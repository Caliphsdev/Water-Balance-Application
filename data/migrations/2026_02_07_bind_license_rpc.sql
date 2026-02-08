-- Safe migration: add customer fields + bind_license RPC
-- Run this in Supabase SQL editor (does NOT drop tables).

ALTER TABLE licenses
  ADD COLUMN IF NOT EXISTS customer_name TEXT,
  ADD COLUMN IF NOT EXISTS customer_email TEXT;

CREATE OR REPLACE FUNCTION bind_license(
    p_license_key TEXT,
    p_hwid TEXT,
    p_customer_name TEXT DEFAULT NULL,
    p_customer_email TEXT DEFAULT NULL
)
RETURNS TABLE (
    license_key TEXT,
    hwid TEXT,
    customer_name TEXT,
    customer_email TEXT,
    last_validated TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_record licenses%ROWTYPE;
BEGIN
    SELECT * INTO v_record
    FROM licenses AS l
    WHERE l.license_key = p_license_key;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'License key not found';
    END IF;

    IF v_record.status <> 'active' THEN
        RAISE EXCEPTION 'License is not active';
    END IF;

    IF v_record.expires_at IS NOT NULL AND v_record.expires_at < NOW() THEN
        RAISE EXCEPTION 'License has expired';
    END IF;

    IF v_record.hwid IS NOT NULL AND v_record.hwid <> p_hwid THEN
        RAISE EXCEPTION 'License bound to different machine';
    END IF;

    UPDATE licenses AS l
    SET hwid = COALESCE(l.hwid, p_hwid),
        last_validated = NOW(),
        customer_name = COALESCE(NULLIF(p_customer_name, ''), l.customer_name),
        customer_email = COALESCE(NULLIF(p_customer_email, ''), l.customer_email)
    WHERE l.license_key = p_license_key;

    RETURN QUERY
    SELECT l.license_key, l.hwid, l.customer_name, l.customer_email, l.last_validated
    FROM licenses AS l
    WHERE l.license_key = p_license_key;
END;
$$;

GRANT EXECUTE ON FUNCTION bind_license(TEXT, TEXT, TEXT, TEXT) TO anon, authenticated;
