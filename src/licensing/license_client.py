"""Google Sheets backed license validation client (public sheet access with Apps Script webhook for write-back)."""

from __future__ import annotations

import csv
import datetime as dt
import io
import sys
from pathlib import Path
from typing import Dict, Optional

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.app_logger import logger
from utils.config_manager import config

try:
    import requests
except Exception:  # pragma: no cover - optional runtime dependency
    requests = None

# Support contact information
SUPPORT_EMAIL = "support@water-balance.com"
SUPPORT_PHONE = "+27 123 456 7890"


class LicenseClient:
    """Handles online validation against a Google Sheet using public CSV export (no auth needed).
    
    Write-back is via Apps Script webhook (no credentials needed, personal Google account support).
    """

    def __init__(self):
        self.sheet_url = config.get("licensing.sheet_url")
        self.sheet_name = config.get("licensing.sheet_name", "licenses")
        self.webhook_url = config.get("licensing.webhook_url")
        self.timeout = int(config.get("licensing.request_timeout", 10))

    def _extract_sheet_id(self) -> str:
        """Extract spreadsheet ID from URL."""
        # URL format: https://docs.google.com/spreadsheets/d/{ID}/edit?...
        parts = self.sheet_url.split("/d/")
        if len(parts) > 1:
            sheet_id = parts[1].split("/")[0]
            return sheet_id
        raise ValueError(f"Cannot extract sheet ID from URL: {self.sheet_url}")

    def _get_records(self) -> list:
        """Fetch sheet as CSV via public Google Sheets API (no auth required)."""
        if not requests:
            raise RuntimeError("requests not installed; cannot reach license server")
        if not self.sheet_url:
            raise RuntimeError("License sheet URL not configured")

        sheet_id = self._extract_sheet_id()
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={self.sheet_name}"
        
        try:
            response = requests.get(csv_url, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch license sheet: {exc}")

        # Parse CSV
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            return []

        # Parse headers (first line)
        reader = csv.reader(io.StringIO(lines[0]))
        headers = next(reader)
        headers = [h.strip().strip('"') for h in headers if h.strip()]

        # Parse data rows
        records = []
        for line in lines[1:]:
            if not line.strip():
                continue
            reader = csv.reader(io.StringIO(line))
            values = next(reader)
            row = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    val = values[i].strip().strip('"')
                    row[header] = val if val else None
            records.append(row)

        return records

    def validate(self, license_key: str, hardware_components: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Validate license row against Google Sheet.

        Returns a dict with keys: valid, status, expiry_date, message, transfer_count.
        """
        try:
            records = self._get_records()
        except Exception as exc:
            logger.error(f"Failed to fetch records: {exc}")
            return {"valid": False, "status": "error", "message": str(exc)}

        for row in records:
            if str(row.get("license_key", "")).strip() != str(license_key).strip():
                continue
            
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
                    "message": f"License expired. Renew at {SUPPORT_EMAIL}."
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
            expiry_date = None
            if expiry_str:
                try:
                    expiry_date = dt.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                except Exception:
                    pass
            
            if expiry_date and expiry_date < dt.date.today():
                return {
                    "valid": False,
                    "status": "expired",
                    "message": f"License expired on {expiry_date.isoformat()}. Renew at {SUPPORT_EMAIL}."
                }

            return {
                "valid": True,
                "status": status,
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "message": "License validated",
                "transfer_count": row.get("transfer_count"),
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
        """Sync activation data to Sheet via Apps Script webhook (best-effort, non-blocking).
        
        Args:
            license_key: License key.
            hardware_components: Dict of hardware identifiers (MAC, CPU, board, etc.).
            licensee_name: Optional licensee name.
            licensee_email: Optional licensee email.
            is_transfer: If True, increments transfer_count in Sheet.
            
        Returns:
            True if webhook responded successfully, False otherwise (soft fail—data saved locally regardless).
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured; skipping Sheet sync")
            return False

        if not requests:
            logger.debug("requests not available; skipping webhook call")
            return False

        try:
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
                "is_transfer": is_transfer,  # NEW: Flag for transfer_count increment
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            if "OK" in response.text:
                logger.info(f"License data synced to Sheet via webhook: {license_key}")
                return True
            else:
                logger.debug(f"Webhook returned: {response.text}")
                return False
        except Exception as exc:
            logger.debug(f"Failed to sync to Sheet via webhook: {exc}")
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

