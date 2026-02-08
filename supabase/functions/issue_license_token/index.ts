// Supabase Edge Function: issue_license_token
// Signs license tokens with Ed25519 using a private key stored in function secrets.

import { createClient } from "npm:@supabase/supabase-js@2";
import nacl from "npm:tweetnacl@1.0.3";

const OFFLINE_TOKEN_VALIDITY_DAYS = 7;
const TOKEN_VERSION = 1;
const VALID_TIERS = new Set(["developer", "premium", "standard", "free_trial"]);

function decodeBase64Url(input: string): Uint8Array {
  const normalized = input.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "===".slice((normalized.length + 3) % 4);
  const raw = atob(padded);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) {
    bytes[i] = raw.charCodeAt(i);
  }
  return bytes;
}

function encodeBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function getSigningKey(): Uint8Array {
  const raw = (Deno.env.get("WATERBALANCE_PRIVATE_KEY") || "").trim();
  if (!raw) {
    throw new Error("Missing WATERBALANCE_PRIVATE_KEY secret");
  }
  const keyBytes = decodeBase64Url(raw);
  if (keyBytes.length === nacl.sign.seedLength) {
    return nacl.sign.keyPair.fromSeed(keyBytes).secretKey;
  }
  if (keyBytes.length !== nacl.sign.secretKeyLength) {
    throw new Error("Invalid private key length");
  }
  return keyBytes;
}

function buildTokenPayload(
  licenseKey: string,
  hwid: string,
  tier: string,
  expiresAt: Date
): string {
  const payload = {
    v: TOKEN_VERSION,
    key: licenseKey,
    hwid,
    tier,
    exp: expiresAt.toISOString(),
    iat: new Date().toISOString(),
  };
  const json = JSON.stringify(payload);
  return encodeBase64Url(new TextEncoder().encode(json));
}

function signToken(payloadB64: string, signingKey: Uint8Array): string {
  const payloadBytes = new TextEncoder().encode(payloadB64);
  const signature = nacl.sign.detached(payloadBytes, signingKey);
  return `${payloadB64}.${encodeBase64Url(signature)}`;
}

function getSupabaseAdminClient() {
  const url = (Deno.env.get("APP_SUPABASE_URL") || "").trim();
  const serviceKey = (Deno.env.get("APP_SUPABASE_SERVICE_ROLE_KEY") || "").trim();
  if (!url || !serviceKey) {
    throw new Error("Missing APP_SUPABASE_URL or APP_SUPABASE_SERVICE_ROLE_KEY secret");
  }
  return createClient(url, serviceKey, { auth: { persistSession: false } });
}

function jsonResponse(status: number, payload: Record<string, unknown>) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return jsonResponse(405, { error: "Method not allowed" });
  }

  try {
    const body = await req.json();
    const licenseKey = String(body?.license_key || "").trim().toUpperCase();
    const hwid = String(body?.hwid || "").trim();

    if (!licenseKey || !hwid) {
      return jsonResponse(400, { error: "license_key and hwid are required" });
    }

    const supabase = getSupabaseAdminClient();
    const { data: license, error } = await supabase
      .from("licenses")
      .select("license_key, hwid, tier, status, expires_at")
      .eq("license_key", licenseKey)
      .maybeSingle();

    if (error) {
      return jsonResponse(500, { error: error.message });
    }
    if (!license) {
      return jsonResponse(404, { error: "License key not found" });
    }
    if ((license.status || "").toLowerCase() !== "active") {
      return jsonResponse(403, { error: "License is not active" });
    }
    if (license.hwid && license.hwid !== hwid) {
      return jsonResponse(403, { error: "License bound to different machine" });
    }

    const tier = (license.tier || "standard").toLowerCase();
    if (!VALID_TIERS.has(tier)) {
      return jsonResponse(400, { error: "Invalid license tier" });
    }

    let expiresAt: Date | null = null;
    if (license.expires_at) {
      expiresAt = new Date(license.expires_at);
      if (Number.isNaN(expiresAt.getTime())) {
        expiresAt = null;
      }
    }

    const offlineExpiry = new Date();
    offlineExpiry.setUTCDate(offlineExpiry.getUTCDate() + OFFLINE_TOKEN_VALIDITY_DAYS);
    const tokenExpiry = expiresAt ? new Date(Math.min(offlineExpiry.getTime(), expiresAt.getTime())) : offlineExpiry;

    if (!license.hwid) {
      await supabase
        .from("licenses")
        .update({ hwid, last_validated: new Date().toISOString() })
        .eq("license_key", licenseKey);
    } else {
      await supabase
        .from("licenses")
        .update({ last_validated: new Date().toISOString() })
        .eq("license_key", licenseKey);
    }

    const signingKey = getSigningKey();
    const payloadB64 = buildTokenPayload(licenseKey, hwid, tier, tokenExpiry);
    const signedToken = signToken(payloadB64, signingKey);

    return jsonResponse(200, { signed_token: signedToken });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unexpected error";
    return jsonResponse(500, { error: message });
  }
});
