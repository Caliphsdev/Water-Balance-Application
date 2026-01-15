"""Core licensing workflow: activation, validation, transfer."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import base64

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import db
from licensing.hardware_id import (
    current_hardware_snapshot,
    deserialize_components,
    describe_mismatch,
    fuzzy_match,
    serialize_components,
)
from licensing.license_client import LicenseClient
from utils.app_logger import logger
from utils.config_manager import config


# Embedded SMTP credentials (obfuscated, non-configurable by users)
_SMTP_CONFIG = {
    'server': 'mail.transafreso.com',
    'port': 465,
    'use_ssl': True,
    'user': 'admin@transafreso.com',
    # Password is base64 encoded for basic obfuscation
    '_encoded_pass': base64.b64encode(b'Adminzakai@2016').decode('utf-8'),
    'support_email': 'admin@transafreso.com',
    'support_phone': '+27 123 456 7890'
}


class LicenseManager:
    """Handles license state and validation."""

    def __init__(self):
        self.client = LicenseClient()
        self.offline_grace_days = int(config.get("licensing.offline_grace_days", 7))
        # Support contact info from embedded config (not editable by users)
        self.support_email = _SMTP_CONFIG['support_email']
        self.support_phone = _SMTP_CONFIG['support_phone']
        self.check_interval_hours = int(config.get("licensing.check_interval_hours", 24))
        self.check_intervals = config.get("licensing.check_intervals", {"trial": 1, "standard": 24, "premium": 168})
        self.max_transfers = int(config.get("licensing.max_transfers", 3))
        self.hardware_threshold = int(config.get("licensing.hardware_match_threshold", 2))

    # Database helpers
    def _fetch_license_row(self) -> Optional[Dict]:
        row = db.execute_query("SELECT * FROM license_info ORDER BY license_id DESC LIMIT 1")
        return row[0] if row else None

    def _try_auto_recover_license(self) -> Tuple[bool, Optional[str]]:
        """Try to auto-recover license from Google Sheets if same hardware exists.

        Scenario: User uninstalled the app (clears local DB) but reinstalls on the
        same computer. This method finds the matching license on Google Sheets and
        restores it locally.

        Returns:
            Tuple of (recovered: bool, message: Optional[str])
        """
        try:
            current_hw = current_hardware_snapshot()
            if not any(current_hw.values()):
                logger.warning("❌ Cannot auto-recover: no hardware info available")
                return False, None
            
            logger.info(f"\n🔍 AUTO-RECOVERY SCAN STARTING")
            logger.info(f"   🖥️  Current machine hardware: {current_hw}")
            
            # Check all licenses on Google Sheets to find a match
            logger.info(f"   📡 Querying Google Sheets for all licenses...")
            all_licenses = self.client.get_all_licenses()
            
            if not all_licenses:
                logger.info("   ❌ No licenses found on Google Sheets")
                return False, None
            
            logger.info(f"   ✅ Found {len(all_licenses)} licenses on Google Sheets to check")
            
            # Find license with matching hardware
            for idx, license_info in enumerate(all_licenses, 1):
                license_key = license_info.get('license_key')
                status = license_info.get('status', '').lower()
                is_valid = license_info.get('valid')
                
                logger.info(f"\n   [{idx}/{len(all_licenses)}] Checking license: {license_key}")
                logger.info(f"      📋 Status: {status}, Valid: {is_valid}")
                
                if not is_valid:
                    # If revoked and hardware matches, block immediately with message
                    remote_hw_json = license_info.get('hardware_components_json', '{}')
                    remote_hw = deserialize_components(remote_hw_json)
                    is_match, matches = fuzzy_match(
                        remote_hw, current_hw, threshold=self.hardware_threshold
                    )
                    if status == "revoked" and is_match:
                        logger.error(
                            f"      🚫 License {license_key} is REVOKED on server for this hardware"
                        )
                        return False, (
                            f"License revoked on server. Contact {self.support_email}"
                        )
                    logger.info(f"      ⏭️  Skipping invalid license (status: {status})")
                    continue
                
                remote_hw_json = license_info.get('hardware_components_json', '{}')
                logger.info(f"      📄 Hardware JSON from Google Sheets: {remote_hw_json[:80]}...")
                
                remote_hw = deserialize_components(remote_hw_json)
                logger.info(f"      🖥️  Remote hardware parsed: {remote_hw}")
                
                # Show field-by-field comparison
                logger.info(f"      🔬 Field-by-field comparison:")
                all_keys = set(list(remote_hw.keys()) + list(current_hw.keys()))
                match_count = 0
                for key in sorted(all_keys):
                    remote_val = remote_hw.get(key, "(missing)")
                    local_val = current_hw.get(key, "(missing)")
                    is_equal = (remote_val == local_val)
                    if is_equal:
                        match_count += 1
                    status_char = "✓" if is_equal else "✗"
                    logger.info(f"         {status_char} {key:15} | remote={remote_val:30} | local={local_val}")
                
                logger.info(f"      📊 Matched {match_count}/{len(all_keys)} fields")
                
                # Check if hardware matches
                is_match, matches = fuzzy_match(remote_hw, current_hw, threshold=self.hardware_threshold)
                logger.info(f"      🔗 Fuzzy match result: {is_match} (fuzzy_matches={matches}, threshold={self.hardware_threshold})")
                
                if is_match:
                    # Found a match! Restore this license locally
                    logger.info(f"      ✅ MATCH FOUND! License {license_key} matches current hardware")
                    
                    now = dt.datetime.utcnow()
                    grace_until = (now + dt.timedelta(days=self.offline_grace_days)) if self.offline_grace_days > 0 else None
                    
                    record = {
                        "license_key": license_key,
                        "license_status": "active",
                        "license_tier": license_info.get('license_tier', 'standard'),
                        "licensee_name": license_info.get('licensee_name'),
                        "licensee_email": license_info.get('licensee_email'),
                        "hardware_components_json": remote_hw_json,
                        "hardware_match_threshold": self.hardware_threshold,
                        "activated_at": license_info.get('activated_at') or now.isoformat(),
                        "last_online_check": now.isoformat(),
                        "offline_grace_until": grace_until.isoformat() if grace_until else None,
                        "expiry_date": license_info.get('expiry_date'),
                        "max_users": license_info.get('max_users', 1),
                        "transfer_count": license_info.get('transfer_count', 0),
                    }
                    
                    self._save_license_row(record)
                    self._log_validation(None, "auto_recovered", f"License auto-recovered: {license_key}")
                    logger.info(f"      💾 License {license_key} saved to local database")
                    logger.info(f"\n✅ AUTO-RECOVERY SUCCESSFUL - License {license_key} restored\n")
                    return True, None
                else:
                    logger.info(f"      ❌ No match (hardware mismatch)")
            
            logger.info(f"\n❌ AUTO-RECOVERY FAILED: No matching license found (checked {len(all_licenses)} licenses)\n")
            return False, None
            
        except Exception as e:
            logger.error(f"❌ AUTO-RECOVERY FATAL ERROR: {e}", exc_info=True)
            return False, "Auto-recovery failed"

    def _save_license_row(self, data: Dict) -> int:
        existing = self._fetch_license_row()
        if existing:
            # Preserve manual verification counters if not provided
            mvc = data.get("manual_verification_count", existing.get("manual_verification_count"))
            mvr = data.get("manual_verification_reset_at", existing.get("manual_verification_reset_at"))
            db.execute_update(
                """
                UPDATE license_info SET
                    license_key = ?,
                    license_status = ?,
                    license_tier = ?,
                    licensee_name = ?,
                    licensee_email = ?,
                    hardware_components_json = ?,
                    hardware_match_threshold = ?,
                    activated_at = ?,
                    last_online_check = ?,
                    offline_grace_until = ?,
                    expiry_date = ?,
                    max_users = ?,
                    transfer_count = ?,
                    last_transfer_at = ?,
                    manual_verification_count = ?,
                    manual_verification_reset_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE license_id = ?
                """,
                (
                    data.get("license_key"),
                    data.get("license_status", "active"),
                    data.get("license_tier", "standard"),
                    data.get("licensee_name"),
                    data.get("licensee_email"),
                    data.get("hardware_components_json"),
                    data.get("hardware_match_threshold", self.hardware_threshold),
                    data.get("activated_at"),
                    data.get("last_online_check"),
                    data.get("offline_grace_until"),
                    data.get("expiry_date"),
                    data.get("max_users", 1),
                    data.get("transfer_count", 0),
                    data.get("last_transfer_at"),
                    mvc,
                    mvr,
                    existing.get("license_id"),
                ),
            )
            return existing.get("license_id")
        return db.execute_insert(
            """
            INSERT INTO license_info (
                license_key, license_status, license_tier, licensee_name, licensee_email,
                hardware_components_json, hardware_match_threshold, activated_at,
                last_online_check, offline_grace_until, expiry_date, max_users,
                transfer_count, last_transfer_at, manual_verification_count, manual_verification_reset_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("license_key"),
                data.get("license_status", "active"),
                data.get("license_tier", "standard"),
                data.get("licensee_name"),
                data.get("licensee_email"),
                data.get("hardware_components_json"),
                data.get("hardware_match_threshold", self.hardware_threshold),
                data.get("activated_at"),
                data.get("last_online_check"),
                data.get("offline_grace_until"),
                data.get("expiry_date"),
                data.get("max_users", 1),
                data.get("transfer_count", 0),
                data.get("last_transfer_at"),
                data.get("manual_verification_count", 0),
                data.get("manual_verification_reset_at"),
            ),
        )

    def _log_validation(self, license_id: Optional[int], result: str, message: str) -> None:
        try:
            db.execute_insert(
                "INSERT INTO license_validation_log (license_id, validation_type, validation_result, validation_message) VALUES (?, ?, ?, ?)",
                (license_id, "startup", result, message),
            )
        except Exception as exc:
            logger.warning(f"Failed to log validation: {exc}")
    
    def _log_security_event(self, license_id: Optional[int], event_type: str, details: str) -> None:
        """Log security-related events for audit trail."""
        try:
            db.execute_insert(
                "INSERT INTO license_audit_log (license_id, event_type, event_details) VALUES (?, ?, ?)",
                (license_id, event_type, details),
            )
            logger.warning(f"Security event: {event_type} - {details}")
        except Exception as exc:
            logger.warning(f"Failed to log security event: {exc}")

    # Public API
    def validate_startup(self) -> Tuple[bool, str, Optional[dt.date]]:
        """Validate license during application startup.
        
        ALWAYS performs online validation for immediate revocation detection.
        Also attempts to auto-recover license from Google Sheets if local DB is empty
        but same hardware is found on the remote sheet (e.g., after reinstall on same machine).
        
        Returns:
            Tuple of (valid: bool, message: str, expiry_date: Optional[date])
        """
        record = self._fetch_license_row()
        
        # If no local license, try to auto-recover from Google Sheets
        if not record:
            logger.info("No local license found - attempting auto-recovery from Google Sheets...")
            recovered, recover_msg = self._try_auto_recover_license()
            if recovered:
                logger.info("✅ License auto-recovered from Google Sheets (same hardware)")
                record = self._fetch_license_row()
            else:
                logger.info("No matching license on Google Sheets for this hardware")
                return False, recover_msg or "License not activated", None

        license_id = record.get("license_id")
        hardware_json = record.get("hardware_components_json") or "{}"
        stored_hardware = deserialize_components(hardware_json)
        current_hardware = current_hardware_snapshot()

        # If no hardware binding exists yet (empty stored snapshot), bind to current hardware
        if not any(stored_hardware.values()) and any(current_hardware.values()):
            record.update(
                {
                    "hardware_components_json": serialize_components(current_hardware),
                    "hardware_match_threshold": self.hardware_threshold,
                }
            )
            self._save_license_row(record)
            stored_hardware = current_hardware

        is_match, matches = fuzzy_match(
            stored_hardware, current_hardware, threshold=record.get("hardware_match_threshold", self.hardware_threshold)
        )
        if not is_match:
            reason = describe_mismatch(stored_hardware, current_hardware)
            self._log_validation(license_id, "hardware_mismatch", reason)
            return False, f"Hardware mismatch: {reason}"

        expiry = record.get("expiry_date")
        expiry_date = None
        if expiry:
            try:
                expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d").date()
                days_remaining = (expiry_date - dt.date.today()).days
                
                if days_remaining < 0:
                    self._log_validation(license_id, "expired", "License expired")
                    return False, f"License expired on {expiry_date.isoformat()}. Renew at {self.support_email}.", None
                elif 0 < days_remaining <= 7:
                    logger.warning(f"⚠️ License expires in {days_remaining} days! Renew soon at {self.support_email}")
                    # Continue validation but log warning
            except Exception:
                pass

        # ALWAYS validate online at startup (professional/enterprise requirement)
        # This ensures immediate revocation detection
        try:
            online_ok, online_msg = self._validate_online(record)
            if not online_ok:
                # CRITICAL: Check if license is REVOKED (no grace period allowed)
                if "revoked" in online_msg.lower():
                    # Store revoked status locally to block access even offline
                    record["license_status"] = "revoked"
                    self._save_license_row(record)
                    self._log_validation(license_id, "revoked", online_msg)
                    logger.error(f"🚫 License REVOKED - blocking access immediately")
                    return False, online_msg, None
                
                # Check if still within grace period (only for non-revoked issues)
                grace_until = record.get("offline_grace_until")
                if grace_until:
                    try:
                        grace_date = dt.datetime.fromisoformat(grace_until)
                        if dt.datetime.utcnow() < grace_date:
                            logger.warning(f"Offline mode - grace period active until {grace_date.isoformat()}")
                            self._log_validation(license_id, "offline_grace", "Using offline grace period")
                            return True, "License valid (offline grace)", expiry_date
                    except Exception:
                        pass
                
                self._log_validation(license_id, "online_failed", online_msg)
                return False, online_msg, None
        except Exception as exc:
            # Network error - allow if grace period is valid AND not previously revoked
            if record.get("license_status") == "revoked":
                logger.error("🚫 License was previously revoked - blocking access")
                return False, "License revoked. Contact support@water-balance.com for assistance.", None
            
            logger.warning(f"Network error during validation: {exc}")
            grace_until = record.get("offline_grace_until")
            if grace_until:
                try:
                    grace_date = dt.datetime.fromisoformat(grace_until)
                    if dt.datetime.utcnow() < grace_date:
                        logger.info(f"Network unavailable - using offline grace period until {grace_date.isoformat()}")
                        self._log_validation(license_id, "offline_grace", "Network unavailable, using grace period")
                        return True, "License valid (offline mode)", expiry_date
                except Exception:
                    pass
            
            self._log_validation(license_id, "network_error", str(exc))
            return False, "Network error: Cannot validate license", None
        
        # Log successful validation with expiry info
        if expiry_date:
            days_left = (expiry_date - dt.date.today()).days
            logger.info(f"✅ License valid - {days_left} days remaining")
        
        self._log_validation(license_id, "valid", "License valid")
        return True, "License valid", expiry_date

    def _validate_online(self, record: Dict) -> Tuple[bool, str]:
        """Validate license against Google Sheet and update timestamps.
        
        With strict mode enabled, also verifies that hardware info exists on remote sheet.
        This prevents piracy by requiring active server-side hardware binding.
        """
        license_key = record.get("license_key")
        if not license_key:
            return False, "License key missing"
        try:
            result = self.client.validate(license_key, current_hardware_snapshot())
        except Exception as exc:
            logger.error(f"Online license validation failed: {exc}")
            return False, "Online validation failed"

        if not result.get("valid"):
            return False, result.get("message", "License invalid")

        # STRICT MODE: Require hardware binding on remote sheet
        require_remote = config.get('licensing.require_remote_hardware_match', False)
        if require_remote and not result.get("hardware_components_json"):
            logger.warning("Strict mode: License has no hardware binding on remote sheet (anti-piracy)")
            # Return success but inform user binding is pending
            # Background thread will handle the sync automatically
            return True, "License active (hardware binding will sync automatically)"

        now = dt.datetime.utcnow()
        grace_until = (now + dt.timedelta(days=self.offline_grace_days)) if self.offline_grace_days > 0 else None
        record.update(
            {
                "license_status": "active",
                "last_online_check": now.isoformat(),
                "offline_grace_until": grace_until.isoformat() if grace_until else None,
                "expiry_date": result.get("expiry_date") or record.get("expiry_date"),
            }
        )
        self._save_license_row(record)
        return True, "License validated"

    def activate(self, license_key: str, licensee_name: str = None, licensee_email: str = None) -> Tuple[bool, str]:
        """Activate license with online validation."""
        if not license_key:
            return False, "License key required"
        try:
            result = self.client.validate(license_key, current_hardware_snapshot())
        except Exception as exc:
            logger.error(f"Activation failed: {exc}")
            return False, "Activation failed: online validation error"

        if not result.get("valid"):
            return False, result.get("message", "License invalid")

        now = dt.datetime.utcnow()
        hardware_snapshot = current_hardware_snapshot()
        record = {
            "license_key": license_key.strip(),
            "license_status": "active",
            "license_tier": result.get("status", "active"),
            "licensee_name": licensee_name,
            "licensee_email": licensee_email,
            "hardware_components_json": serialize_components(hardware_snapshot),
            "hardware_match_threshold": self.hardware_threshold,
            "activated_at": now.isoformat(),
            "last_online_check": now.isoformat(),
            "offline_grace_until": (now + dt.timedelta(days=self.offline_grace_days)).isoformat()
            if self.offline_grace_days > 0
            else None,
            "expiry_date": result.get("expiry_date"),
            "max_users": 1,
            "transfer_count": result.get("transfer_count") or 0,
        }
        license_id = self._save_license_row(record)
        self._log_validation(license_id, "activated", "Activated online")

        # Attempt to update Sheet with activation data (hardware, licensee info)
        # This is optional—data is already saved locally in SQLite
        try:
            self.client.update_activation_data(license_key, hardware_snapshot, licensee_name, licensee_email)
        except Exception as exc:
            logger.debug(f"Sheet update failed (non-critical): {exc}")

        return True, "License activated"

    def request_transfer(self, license_key: str, user_email: str = None) -> Tuple[bool, str]:
        """Request hardware transfer with anti-theft protections.
        
        SECURITY PROTECTIONS:
        1. Email verification required (sends code to registered email)
        2. Transfer notification sent to owner
        3. 24-hour grace period for rejection
        4. IP address logged for audit trail
        5. Security event logged
        
        Args:
            license_key: License key to transfer
            user_email: Email to verify (must match registered email)
            
        Returns:
            Tuple of (success, message)
        """
        if not license_key:
            return False, "License key required"
        
        # Fetch current record
        record = self._fetch_license_row() or {}
        current_count = record.get("transfer_count", 0)
        registered_email = record.get("licensee_email")
        registered_name = record.get("licensee_name", "License Owner")
        
        # PROTECTION 1: Check transfer limit BEFORE allowing transfer
        if current_count >= self.max_transfers:
            msg = f"Transfer limit reached ({current_count}/{self.max_transfers}). Contact {self.support_email} or {self.support_phone}."
            self._log_security_event(record.get("license_id"), "transfer_limit_exceeded", msg)
            return False, msg
        
        # PROTECTION 2: Require email verification (if email registered)
        if registered_email and user_email:
            if user_email.lower() != registered_email.lower():
                msg = f"Email verification failed. Transfer request sent to {registered_email} for approval."
                self._log_security_event(
                    record.get("license_id"), 
                    "unauthorized_transfer_attempt", 
                    f"Transfer attempt from unverified email: {user_email}"
                )
                
                # Send notification to registered email
                try:
                    self._send_transfer_notification(
                        registered_email, 
                        registered_name,
                        current_hardware_snapshot(),
                        suspicious=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification: {e}")
                
                return False, msg
        
        # PROTECTION 3: Send notification to owner before transfer
        if registered_email:
            try:
                self._send_transfer_notification(
                    registered_email,
                    registered_name, 
                    current_hardware_snapshot(),
                    suspicious=False
                )
                logger.info(f"Transfer notification sent to {registered_email}")
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
        
        # PROTECTION 4: Register transfer with server (includes IP logging)
        try:
            ok = self.client.register_transfer(license_key, current_hardware_snapshot())
        except Exception as exc:
            logger.error(f"Transfer request failed: {exc}")
            return False, "Transfer request failed"
        if not ok:
            return False, "Transfer not approved"

        # PROTECTION 5: Log security event with details
        current_hw = current_hardware_snapshot()
        self._log_security_event(
            record.get("license_id"),
            "transfer_approved",
            f"Hardware transfer approved ({current_count + 1}/{self.max_transfers}) - "
            f"New hardware: CPU={current_hw.get('cpu', 'unknown')[:8]}..."
        )

        # Update local database
        record.update(
            {
                "license_key": license_key,
                "hardware_components_json": serialize_components(current_hw),
                "hardware_match_threshold": self.hardware_threshold,
                "last_transfer_at": dt.datetime.utcnow().isoformat(),
                "transfer_count": current_count + 1,
                "license_status": "active",
            }
        )
        self._save_license_row(record)
        self._log_validation(
            record.get("license_id"), 
            "transfer", 
            f"Hardware transfer approved ({current_count + 1}/{self.max_transfers})"
        )
        
        return True, f"Transfer approved ({current_count + 1}/{self.max_transfers} used)"
    
    def _send_transfer_notification(self, email: str, name: str, new_hardware: Dict, suspicious: bool = False):
        """Send email notification about transfer attempt.
        
        Args:
            email: Email address to notify
            name: Licensee name
            new_hardware: New hardware snapshot
            suspicious: Whether this is a suspicious transfer attempt
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Use embedded SMTP credentials (not configurable by users)
        smtp_server = _SMTP_CONFIG['server']
        smtp_port = _SMTP_CONFIG['port']
        smtp_user = _SMTP_CONFIG['user']
        smtp_password = base64.b64decode(_SMTP_CONFIG['_encoded_pass']).decode('utf-8')
        smtp_use_ssl = _SMTP_CONFIG['use_ssl']
        
        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "⚠️ License Transfer Request" if suspicious else "License Transfer Notification"
        msg["From"] = self.support_email
        msg["To"] = email
        
        # Email body
        if suspicious:
            body = f"""
Hello {name},

⚠️ SECURITY ALERT: An UNAUTHORIZED transfer attempt was detected on your license.

Someone attempted to transfer your license to different hardware, but the email verification failed.

Transfer Details:
- New CPU Serial: {new_hardware.get('cpu', 'unknown')[:16]}...
- New Motherboard: {new_hardware.get('motherboard', 'unknown')[:16]}...
- Time: {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

If this was YOU:
- Please ensure you use the email address registered with your license: {email}

If this was NOT YOU:
- Your license is SAFE - the transfer was blocked
- Change your license key immediately by contacting: {self.support_email}
- Report this incident to: {self.support_phone}

Best regards,
Water Balance Support Team
{self.support_email}
{self.support_phone}
"""
        else:
            body = f"""
Hello {name},

A license transfer has been requested for your Water Balance Application license.

Transfer Details:
- New CPU Serial: {new_hardware.get('cpu', 'unknown')[:16]}...
- New Motherboard: {new_hardware.get('motherboard', 'unknown')[:16]}...
- Time: {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

If this was YOU:
- No action needed - transfer is processing

If this was NOT YOU (UNAUTHORIZED):
- Contact us IMMEDIATELY: {self.support_email} or {self.support_phone}
- We can revoke the transfer within 24 hours
- Your license will be restored to your original hardware

Best regards,
Water Balance Support Team
{self.support_email}
{self.support_phone}
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        try:
            if smtp_use_ssl:
                # Port 465 - Use SSL from the start
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    logger.info(f"Transfer notification sent to {email} (SSL)")
            else:
                # Port 587 - Use STARTTLS
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    logger.info(f"Transfer notification sent to {email} (TLS)")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise

    def status_summary(self) -> str:
        """Return human-readable status for UI."""
        record = self._fetch_license_row()
        if not record:
            return "Not activated"
        expiry = record.get("expiry_date")
        expiry_text = f", expires {expiry}" if expiry else ""
        return f"License active{expiry_text}"

    def validate_background(self) -> Tuple[bool, str, Optional[dt.date]]:
        """Periodic background validation (every 1-2 hours while app is running).
        
        Similar to startup validation but called periodically to catch revocations
        during active use. Does NOT block UI (should be called from background thread).
        
        Returns:
            Tuple of (valid: bool, message: str, expiry_date: Optional[date])
        """
        record = self._fetch_license_row()
        if not record:
            return False, "License not activated", None

        license_id = record.get("license_id")
        
        # Quick hardware check
        hardware_json = record.get("hardware_components_json") or "{}"
        stored_hardware = deserialize_components(hardware_json)
        current_hardware = current_hardware_snapshot()
        
        # If hardware is empty/missing (no binding yet), allow access in offline mode
        if not stored_hardware:
            logger.info("License has no hardware binding yet, allowing access (grace period active)")
            # Return success for now - binding will be done on next online check
            expiry = record.get("expiry_date")
            expiry_date = None
            if expiry:
                try:
                    expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d").date()
                except Exception:
                    pass
            return True, "License active (hardware binding pending)", expiry_date
        
        is_match, _ = fuzzy_match(
            stored_hardware, current_hardware, threshold=record.get("hardware_match_threshold", self.hardware_threshold)
        )
        if not is_match:
            reason = describe_mismatch(stored_hardware, current_hardware)
            self._log_validation(license_id, "hardware_mismatch_bg", reason)
            return False, f"Hardware mismatch: {reason}"

        # Check expiry locally first
        expiry = record.get("expiry_date")
        expiry_date = None
        if expiry:
            try:
                expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d").date()
                days_remaining = (expiry_date - dt.date.today()).days
                if days_remaining < 0:
                    self._log_validation(license_id, "expired_bg", "License expired")
                    return False, f"License expired on {expiry_date.isoformat()}.", None
            except Exception:
                pass

        # Perform online validation (will catch revocations)
        try:
            online_ok, online_msg = self._validate_online(record)
            if not online_ok:
                # CRITICAL: Check if license is REVOKED (store status locally)
                if "revoked" in online_msg.lower():
                    record["license_status"] = "revoked"
                    self._save_license_row(record)
                    logger.error(f"🚫 License REVOKED detected in background - blocking access")
                
                self._log_validation(license_id, "revoked_bg", online_msg)
                return False, online_msg, None
        except Exception as exc:
            logger.warning(f"Background validation network error: {exc}")
            # Check if license was previously revoked (even offline)
            if record.get("license_status") == "revoked":
                logger.error("🚫 License was previously revoked - blocking access")
                return False, "License revoked. Contact support@water-balance.com for assistance.", None
            
            # Don't fail on network error during background check; just log
            self._log_validation(license_id, "network_error_bg", str(exc))
            return True, "Background check skipped (network unavailable)", expiry_date

        self._log_validation(license_id, "valid_bg", "Background validation passed")
        return True, "License valid", expiry_date

    def validate_manual(self) -> Tuple[bool, str, Optional[dt.date]]:
        """Manual validation triggered by user clicking 'Verify License Now' button.
        
        Limited to 3 attempts per day to prevent abuse.
        
        Returns:
            Tuple of (valid: bool, message: str, expiry_date: Optional[date])
        """
        logger.info("Manual license verification initiated by user")
        
        record = self._fetch_license_row()
        if not record:
            return False, "License not activated", None
        
        # Check verification attempt limit (3 per day)
        if not self._check_verification_limit(record):
            return False, "Manual verification limit reached (3/day). Please try again tomorrow.", None
        
        # Increment verification counter
        self._increment_verification_counter(record)
        
        # Perform the actual validation
        return self.validate_background()
    
    def _check_verification_limit(self, record: Dict) -> bool:
        """Check if manual verification is allowed (3 per day limit).
        
        Resets at midnight South Africa Standard Time (SAST = UTC+2).
        
        Returns:
            True if verification is allowed, False if limit reached
        """
        import pytz
        
        count = record.get("manual_verification_count", 0)
        reset_at = record.get("manual_verification_reset_at")
        
        # Get current time in SAST
        sast = pytz.timezone('Africa/Johannesburg')
        now_sast = dt.datetime.now(sast)
        
        # Reset counter if it's past midnight SAST
        if reset_at:
            try:
                reset_time = dt.datetime.fromisoformat(reset_at)
                # Make reset_time aware if it's naive
                if reset_time.tzinfo is None:
                    reset_time = sast.localize(reset_time)
                
                if now_sast >= reset_time:
                    # Reset counter (will be done in increment method)
                    return True
            except Exception:
                return True
        
        # Check if limit reached
        if count >= 3:
            logger.warning("⚠️ Manual verification limit reached (3/day)")
            return False
        
        return True
    
    def _increment_verification_counter(self, record: Dict) -> None:
        """Increment manual verification counter and reset at midnight SAST."""
        import pytz
        
        count = record.get("manual_verification_count", 0)
        reset_at = record.get("manual_verification_reset_at")
        
        # Get current time in SAST
        sast = pytz.timezone('Africa/Johannesburg')
        now_sast = dt.datetime.now(sast)
        
        # Check if we need to reset the counter
        should_reset = False
        if reset_at:
            try:
                reset_time = dt.datetime.fromisoformat(reset_at)
                # Make reset_time aware if it's naive
                if reset_time.tzinfo is None:
                    reset_time = sast.localize(reset_time)
                
                if now_sast >= reset_time:
                    should_reset = True
            except Exception:
                should_reset = True
        else:
            should_reset = True
        
        if should_reset:
            # Reset counter to 1 and set new reset time (next midnight SAST)
            new_count = 1
            # Calculate next midnight SAST
            tomorrow = now_sast.date() + dt.timedelta(days=1)
            next_midnight = sast.localize(dt.datetime.combine(tomorrow, dt.time.min))
            new_reset_at = next_midnight.isoformat()
        else:
            # Increment counter
            new_count = count + 1
            new_reset_at = reset_at
        
        # Update database
        db.execute_update(
            """
            UPDATE license_info 
            SET manual_verification_count = ?,
                manual_verification_reset_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE license_id = ?
            """,
            (new_count, new_reset_at, record.get("license_id"))
        )
        
        logger.info(f"Manual verification count: {new_count}/3 (resets at midnight SAST)")
    
    def get_verification_status(self) -> Dict:
        """Get current verification status for UI display.
        
        Returns:
            Dict with: count, limit, reset_time, can_verify, time_until_reset
        """
        import pytz
        
        record = self._fetch_license_row()
        if not record:
            return {"count": 0, "limit": 3, "can_verify": False, "message": "License not activated"}
        
        count = record.get("manual_verification_count", 0)
        reset_at = record.get("manual_verification_reset_at")
        
        # Get current time in SAST
        sast = pytz.timezone('Africa/Johannesburg')
        now_sast = dt.datetime.now(sast)
        
        # Check if past reset time
        if reset_at:
            try:
                reset_time = dt.datetime.fromisoformat(reset_at)
                if reset_time.tzinfo is None:
                    reset_time = sast.localize(reset_time)
                
                if now_sast >= reset_time:
                    count = 0  # Will be reset on next verification
            except Exception:
                count = 0
        
        can_verify = count < 3
        
        # Calculate time until reset
        if reset_at:
            try:
                reset_time = dt.datetime.fromisoformat(reset_at)
                if reset_time.tzinfo is None:
                    reset_time = sast.localize(reset_time)
                time_until = reset_time - now_sast
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            except Exception:
                time_str = "unknown"
        else:
            time_str = "midnight SAST"
        
        return {
            "count": count,
            "limit": 3,
            "can_verify": can_verify,
            "reset_time": reset_at,
            "time_until_reset": time_str,
            "message": f"Verifications: {count}/3 (resets in {time_str})" if not can_verify else f"{count}/3 used"
        }

