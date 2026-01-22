"""Google Sheets backed license validation client (Google Sheets API v4 with service account).

This module provides the LicenseClient class which handles:
1. License validation against a Google Sheet (online check)
2. Hardware binding and component tracking
3. Direct Google Sheets API writes for updating license metadata
4. Webhook fallback for sheet updates (if direct API fails)

License data is read from and written to the "licenses" sheet in Google Sheets,
with columns: license_key, status, expiry_date, hw_component_1/2/3, licensee_name,
licensee_email, license_tier, last_validated, etc.

Hardware components map to: hw_component_1=MAC address, hw_component_2=CPU ID,
hw_component_3=Motherboard/UUID (used for 2/3 fuzzy matching during transfers).

All writes are best-effort (non-blocking) - validation continues even if sync fails.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.app_logger import logger
from utils.config_manager import config

try:
    import requests
except Exception:  # pragma: no cover - optional runtime dependency
    requests = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover - optional runtime dependency
    gspread = None
    Credentials = None

# Support contact information
SUPPORT_EMAIL = "caliphs@transafreso.com"
SUPPORT_PHONE = "+27 82 355 8130"


class LicenseClient:
    """Handles online validation against Google Sheet using Google Sheets API v4.
    
    Uses service account authentication for reliable read/write access.
    Also supports Apps Script webhook for instant updates.
    """

    def __init__(self):
        self.sheet_url = config.get("licensing.sheet_url")
        self.sheet_name = config.get("licensing.sheet_name", "licenses")
        self.webhook_url = config.get("licensing.webhook_url")
        self.timeout = int(config.get("licensing.request_timeout", 10))
        self.api_key = config.get("licensing.api_key", "")
        self.service_account_json = config.get("licensing.service_account_json", "")
        self._client = None
        self._spreadsheet = None

    def _extract_sheet_id(self) -> str:
        """Extract spreadsheet ID from URL."""
        # URL format: https://docs.google.com/spreadsheets/d/{ID}/edit?...
        parts = self.sheet_url.split("/d/")
        if len(parts) > 1:
            sheet_id = parts[1].split("/")[0]
            return sheet_id
        raise ValueError(f"Cannot extract sheet ID from URL: {self.sheet_url}")

    def _get_client(self):
        """Get authenticated gspread client (lazy init, cached)."""
        if self._client:
            return self._client
        
        if not gspread or not Credentials:
            raise RuntimeError("gspread not installed; run: pip install gspread google-auth")
        
        if not self.service_account_json or not Path(self.service_account_json).exists():
            raise RuntimeError(
                f"Service account JSON not found: {self.service_account_json}. "
                "Configure licensing.service_account_json in app_config.yaml"
            )
        
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file"
            ]
            creds = Credentials.from_service_account_file(self.service_account_json, scopes=scopes)
            self._client = gspread.authorize(creds)
            logger.info("Google Sheets API client authenticated")
            return self._client
        except Exception as exc:
            raise RuntimeError(f"Failed to authenticate with service account: {exc}")
    
    def _get_spreadsheet(self):
        """Get spreadsheet object (lazy init, cached)."""
        if self._spreadsheet:
            return self._spreadsheet
        
        client = self._get_client()
        sheet_id = self._extract_sheet_id()
        
        try:
            self._spreadsheet = client.open_by_key(sheet_id)
            logger.debug(f"Opened spreadsheet: {self._spreadsheet.title}")
            self._ensure_required_sheets()
            return self._spreadsheet
        except Exception as exc:
            import traceback
            logger.error(f"Spreadsheet open error details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to open spreadsheet: {type(exc).__name__}: {exc}")
    
    def _ensure_required_sheets(self):
        """Ensure audit_log and usage_stats sheets exist."""
        try:
            spreadsheet = self._spreadsheet
            existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
            
            # Create audit_log if missing
            if "audit_log" not in existing_sheets:
                logger.info("Creating audit_log sheet...")
                audit_sheet = spreadsheet.add_worksheet("audit_log", rows=1000, cols=10)
                audit_sheet.append_row([
                    "timestamp", "license_key", "event_type", "status",
                    "hw1", "hw2", "hw3", "error_message", "user_email"
                ])
            
            # Create usage_stats if missing
            if "usage_stats" not in existing_sheets:
                logger.info("Creating usage_stats sheet...")
                usage_sheet = spreadsheet.add_worksheet("usage_stats", rows=1000, cols=6)
                usage_sheet.append_row([
                    "month", "license_key", "calculations_count",
                    "exports_count", "reported_at"
                ])
        except Exception as exc:
            logger.warning(f"Failed to create required sheets: {exc}")
    
    def _get_records(self) -> List[Dict]:
        """Fetch all records from licenses sheet using Google Sheets API."""
        try:
            spreadsheet = self._get_spreadsheet()
            worksheet = spreadsheet.worksheet(self.sheet_name)
            records = worksheet.get_all_records()
            logger.debug(f"Fetched {len(records)} license records")
            return records
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch license sheet: {exc}")

    def validate(self, license_key: str, hardware_components: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Validate license row against Google Sheet.

        Returns a dict with keys: valid, status, expiry_date, message, transfer_count.
        Raises exceptions for network errors so caller can handle grace period.
        """
        try:
            records = self._get_records()
        except Exception as exc:
            logger.error(f"Failed to fetch records: {exc}")
            # Re-raise network errors so LicenseManager can apply grace period
            raise

        for row in records:
            if str(row.get("license_key", "")).strip() != str(license_key).strip():
                continue
            
            logger.debug(f"License row matched: {row}")

            status = str(row.get("status", "")).lower() or "pending"
            if status == "revoked":
                return {
                    "valid": False,
                    "status": status,
                    "message": f"License revoked. Contact {SUPPORT_EMAIL} or {SUPPORT_PHONE} for assistance."
                }
            elif status == "expired":
                return {
                    "valid": False,
                    "status": status,
                    "message": f"License expired. Renew at {SUPPORT_EMAIL} or {SUPPORT_PHONE}."
                }

            # Optionally enforce hardware match on server by storing hashed components
            # Skip hardware check if all components are empty (first activation, no binding yet)
            has_hw_binding = any(row.get(key) for key in ("hw_component_1", "hw_component_2", "hw_component_3"))
            if has_hw_binding:
                # Use fuzzy matching (2/3 components) to handle MAC address changes gracefully
                # This matches the local fuzzy matching logic in hardware_id.py
                stored_components = {
                    "mac": str(row.get("hw_component_1", "")).strip() or None,
                    "cpu": str(row.get("hw_component_2", "")).strip() or None,
                    "board": str(row.get("hw_component_3", "")).strip() or None,
                }
                
                # Count how many components match between stored (Google Sheets) and current
                match_count = 0
                for key, stored_val in stored_components.items():
                    if stored_val and stored_val in hardware_components.values():
                        match_count += 1
                
                # Require 2 out of 3 components to match (same threshold as local validation)
                if match_count < 2:
                    return {
                        "valid": False,
                        "status": "mismatch",
                        "message": f"Hardware mismatch ({match_count}/3 components matched). "
                                   f"Request a hardware transfer or contact {SUPPORT_EMAIL}."
                    }

            expiry_value = row.get("expiry_date")
            expiry_str = str(expiry_value).strip() if expiry_value else ""
            parsed_expiry = None
            if expiry_str:
                try:
                    parsed_expiry = dt.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                except Exception:
                    # Keep raw string if parsing fails (still show to user)
                    parsed_expiry = None

            if parsed_expiry and parsed_expiry < dt.date.today():
                return {
                    "valid": False,
                    "status": "expired",
                    "message": f"License expired on {parsed_expiry.isoformat()}. Renew at {SUPPORT_EMAIL} or {SUPPORT_PHONE}."
                }

            # Include hardware binding info for strict-mode checks upstream
            return {
                "valid": True,
                "status": status,
                "expiry_date": parsed_expiry.isoformat() if parsed_expiry else (expiry_str or None),
                "expiry_raw": expiry_str or None,
                "message": "License validated",
                "transfer_count": row.get("transfer_count"),
                "has_hw_binding": has_hw_binding,
                "hardware_components_json": (
                    {
                        "mac": str(row.get("hw_component_1", "")) or None,
                        "cpu": str(row.get("hw_component_2", "")) or None,
                        "board": str(row.get("hw_component_3", "")) or None,
                    }
                    if has_hw_binding
                    else None
                ),
            }

        return {"valid": False, "status": "not_found", "message": "License key not found"}

    def sync_activation_to_sheet(
        self,
        license_key: str,
        hardware_components: Dict[str, str],
        licensee_name: Optional[str] = None,
        licensee_email: Optional[str] = None,
        is_transfer: bool = False,
    ) -> bool:
        """Sync activation data to Sheet via direct Google Sheets API or webhook (best-effort, non-blocking).
        
        Attempts direct Google Sheets write first, falls back to webhook if configured.
        
        Args:
            license_key: License key.
            hardware_components: Dict of hardware identifiers (MAC, CPU, board, etc.).
            licensee_name: Optional licensee name.
            licensee_email: Optional licensee email.
            is_transfer: If True, increments transfer_count in Sheet.
            
        Returns:
            True if sync succeeded, False otherwise (soft fail—data saved locally regardless).
        """
        try:
            # Try direct Google Sheets API update first
            logger.info(f"Updating license record in Google Sheet: {license_key}")
            spreadsheet = self._get_spreadsheet()
            worksheet = spreadsheet.worksheet(self.sheet_name)
            records = worksheet.get_all_records()
            
            # Find and update the license row
            hw_values = list(hardware_components.values())
            headers = worksheet.row_values(1)  # Get header row
            header_dict = {h: i+1 for i, h in enumerate(headers)}  # Map header name to column number
            
            for idx, row in enumerate(records, 2):  # +2 because sheet rows are 1-indexed and headers are row 1
                if str(row.get("license_key", "")).strip() == license_key:
                    logger.debug(f"Found license at row {idx}, updating with hardware binding")
                    
                    # Prepare updates: hw_component_1, hw_component_2, hw_component_3, licensee_name, licensee_email, last_validated
                    updates = {
                        "hw_component_1": hw_values[0] if len(hw_values) > 0 else "",
                        "hw_component_2": hw_values[1] if len(hw_values) > 1 else "",
                        "hw_component_3": hw_values[2] if len(hw_values) > 2 else "",
                        "last_validated": dt.datetime.utcnow().isoformat(),
                    }
                    
                    if licensee_name:
                        updates["licensee_name"] = licensee_name
                    if licensee_email:
                        updates["licensee_email"] = licensee_email
                    
                    # Update each field using cell references
                    for col_name, value in updates.items():
                        try:
                            if col_name in header_dict:
                                col_num = header_dict[col_name]
                                worksheet.update_cell(idx, col_num, value)
                                logger.debug(f"Updated {col_name} at row {idx}, col {col_num}")
                        except Exception as e:
                            logger.warning(f"Failed to update {col_name}: {e}")
                    
                    logger.info(f"✅ License record updated in Google Sheet: {license_key}")
                    return True
            
            logger.warning(f"License key {license_key} not found in Sheet to update")
            return False
            
        except Exception as exc:
            logger.debug(f"Direct Sheet update failed: {exc}")
            
            # Fallback to webhook if direct update failed
            if not self.webhook_url or not requests:
                logger.debug("No webhook URL configured or requests not available; skipping webhook fallback")
                return False
            
            try:
                logger.debug("Attempting webhook fallback for Sheet sync")
                # Extract first 3 hardware values
                hw_values = list(hardware_components.values())
                payload = {
                    "license_key": license_key,
                    "status": "active",
                    "hw1": hw_values[0] if len(hw_values) > 0 else "",
                    "hw2": hw_values[1] if len(hw_values) > 1 else "",
                    "hw3": hw_values[2] if len(hw_values) > 2 else "",
                    "licensee_name": licensee_name or "",
                    "licensee_email": licensee_email or "",
                    "license_tier": "standard",
                    "event_type": "transfer" if is_transfer else "activate",
                }
                
                headers = {
                    'Content-Type': 'application/json',
                }
                
                # Add API key to headers if configured
                if self.api_key:
                    headers['X-API-Key'] = self.api_key
                
                response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                if "OK" in response.text:
                    logger.info(f"License data synced to Sheet via webhook: {license_key}")
                    return True
                else:
                    logger.debug(f"Webhook returned: {response.text}")
                    return False
            except Exception as webhook_exc:
                logger.debug(f"Webhook fallback also failed: {webhook_exc}")
                return False

    def register_transfer(self, license_key: str, hardware_components: Dict[str, str]) -> bool:
        """Request transfer and sync to Sheet via webhook."""
        return self.sync_activation_to_sheet(license_key, hardware_components, None, None, is_transfer=True)

    def update_activation_data(
        self,
        license_key: str,
        hardware_components: Dict[str, str],
        licensee_name: Optional[str] = None,
        licensee_email: Optional[str] = None,
    ) -> bool:
        """Update Sheet with activation data (hardware, licensee name, email) via webhook."""
        return self.sync_activation_to_sheet(license_key, hardware_components, licensee_name, licensee_email)

    def get_all_licenses(self) -> list:
        """Get all valid licenses from Google Sheet for auto-recovery.
        
        Returns:
            List of license dicts with keys: license_key, status, licensee_name, licensee_email,
                                           hardware_components_json, license_tier, expiry_date, etc.
        """
        try:
            records = self._get_records()
            result = []
            
            logger.debug(f"Raw Google Sheets records count: {len(records)}")
            if records:
                logger.debug(f"First record keys: {list(records[0].keys())}")
                logger.debug(f"First record: {records[0]}")
            
            for row in records:
                license_key = str(row.get("license_key", "")).strip()
                if not license_key or license_key.lower() in ("license_key", "key"):
                    continue
                
                status = str(row.get("status", "")).lower() or "pending"
                
                # Build hardware components JSON - CRITICAL: field order must match local snapshot
                # Local snapshot returns: {"mac": ..., "cpu": ..., "board": ...}
                # Google Sheets columns hw_component_1, hw_component_2, hw_component_3 map to: mac, cpu, board
                hw_c1 = str(row.get("hw_component_1", "")).strip() or ""  # MAC address
                hw_c2 = str(row.get("hw_component_2", "")).strip() or ""  # CPU ID
                hw_c3 = str(row.get("hw_component_3", "")).strip() or ""  # Motherboard/UUID
                
                logger.debug(f"License {license_key} Google Sheets hw components: hw1={hw_c1[:20] if hw_c1 else '(empty)'}, hw2={hw_c2[:20] if hw_c2 else '(empty)'}, hw3={hw_c3[:20] if hw_c3 else '(empty)'}")
                
                # CRITICAL: Use EXACT field names from local hardware snapshot
                hw_components = {
                    "mac": hw_c1,        # hw_component_1 = MAC address
                    "cpu": hw_c2,        # hw_component_2 = CPU ID
                    "board": hw_c3,      # hw_component_3 = Motherboard/UUID
                }
                
                # Convert to JSON string
                import json
                hardware_json = json.dumps(hw_components)
                logger.debug(f"Built hardware JSON for {license_key}: {hardware_json}")
                
                license_info = {
                    "license_key": license_key,
                    "status": status,
                    "valid": status not in ("revoked", "expired"),
                    "licensee_name": row.get("licensee_name") or "",
                    "licensee_email": row.get("licensee_email") or "",
                    "hardware_components_json": hardware_json,
                    "license_tier": row.get("license_tier") or "standard",
                    "expiry_date": str(row.get("expiry_date")).strip() if row.get("expiry_date") else None,
                    "transfer_count": row.get("transfer_count") or "0",
                    "activated_at": str(row.get("activated_at")).strip() if row.get("activated_at") else None,
                    "max_users": row.get("max_users") or "1",
                }
                
                result.append(license_info)
                logger.debug(f"Added license to results: {license_key}")
            
            logger.info(f"get_all_licenses returning {len(result)} valid licenses")
            return result
        except Exception as exc:
            logger.error(f"Failed to get all licenses: {exc}", exc_info=True)
            return []
    
    def check_instant_revocation(self, license_key: str) -> bool:
        """Quick revocation check (lightweight, no full validation).
        
        Called before critical operations (save calculation, export data).
        
        Returns:
            True if license is still active, False if revoked.
        """
        try:
            records = self._get_records()
            for row in records:
                if str(row.get("license_key", "")).strip() == license_key:
                    status = str(row.get("status", "")).lower()
                    if status == "revoked":
                        logger.warning(f"License {license_key} has been revoked")
                        return False
                    return True
            # License not found, but don't block (might be offline)
            return True
        except Exception as e:
            logger.debug(f"Revocation check failed: {e}")
            return True  # Fail open (grace period handles offline)
    
    def report_usage_stats(self, license_key: str, month: str, calculations_count: int, exports_count: int = 0) -> bool:
        """Report monthly usage statistics to webhook.
        
        Args:
            license_key: License key
            month: Month in format YYYY-MM
            calculations_count: Number of calculations this month
            exports_count: Number of exports this month
            
        Returns:
            True if successfully reported, False otherwise
        """
        if not self.webhook_url or not requests:
            return False
        
        try:
            payload = {
                "action": "report_usage",
                "license_key": license_key,
                "month": month,
                "calculations_count": calculations_count,
                "exports_count": exports_count,
            }
            
            headers = {
                'Content-Type': 'application/json',
            }
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            logger.debug(f"Usage stats reported for {license_key}: {month} ({calculations_count} calcs)")
            return True
        except Exception as e:
            logger.debug(f"Failed to report usage stats: {e}")
            return False
