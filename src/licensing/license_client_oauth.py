"""Google Sheets backed license validation client using OAuth (user credentials)."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Dict, Optional

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.app_logger import logger
from utils.config_manager import config

try:
    import gspread
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover - optional runtime dependency
    gspread = None
    Credentials = None


class LicenseClientOAuth:
    """Handles online validation against a Google Sheet using OAuth (user credentials)."""

    def __init__(self):
        self.sheet_url = config.get("licensing.sheet_url")
        self.sheet_name = config.get("licensing.sheet_name", "licenses")
        self.credentials_path = config.get("licensing.service_account_json")
        self.timeout = int(config.get("licensing.request_timeout", 10))

    def _get_sheet(self):
        """Open sheet using user credentials (token.json) if available, else service account."""
        if not gspread or not Credentials:
            raise RuntimeError("gspread not installed; cannot reach license server")
        if not self.sheet_url:
            raise RuntimeError("License sheet URL not configured")

        # Try user OAuth first (token.json)
        token_path = Path("token.json")
        if token_path.exists():
            try:
                from google.oauth2.credentials import Credentials as UserCredentials
                creds = UserCredentials.from_authorized_user_file("token.json")
                if creds and creds.valid:
                    client = gspread.authorize(creds)
                    spreadsheet = client.open_by_url(self.sheet_url)
                    return spreadsheet.worksheet(self.sheet_name)
            except Exception as e:
                logger.warning(f"User OAuth failed: {e}; falling back to service account")

        # Fall back to service account
        if not self.credentials_path:
            raise RuntimeError("License credentials not configured")

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_url(self.sheet_url)
        return spreadsheet.worksheet(self.sheet_name)

    def validate(self, license_key: str, hardware_components: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Validate license row against Google Sheet.

        Returns a dict with keys: valid, status, expiry_date, message, transfer_count.
        """
        sheet = self._get_sheet()
        records = sheet.get_all_records()
        for row in records:
            if str(row.get("license_key", "")).strip() != str(license_key).strip():
                continue
            status = str(row.get("status", "")).lower() or "pending"
            if status in {"revoked", "expired"}:
                return {"valid": False, "status": status, "message": f"License {status}"}

            # Optionally enforce hardware match on server by storing hashed components
            for key in ("hw_component_1", "hw_component_2", "hw_component_3"):
                expected = str(row.get(key, "")).strip()
                if expected and expected not in hardware_components.values():
                    return {"valid": False, "status": "mismatch", "message": "Hardware mismatch"}

            expiry_value = row.get("expiry_date")
            expiry_str = str(expiry_value).strip() if expiry_value else ""
            expiry_date = None
            if expiry_str:
                try:
                    expiry_date = dt.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                except Exception:
                    pass
            if expiry_date and expiry_date < dt.date.today():
                return {"valid": False, "status": "expired", "message": "License expired"}

            return {
                "valid": True,
                "status": status,
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "message": "License validated",
                "transfer_count": row.get("transfer_count"),
            }

        return {"valid": False, "status": "not_found", "message": "License key not found"}

    def register_transfer(self, license_key: str, hardware_components: Dict[str, str]) -> bool:
        """Auto-approve transfer by updating hardware component columns."""
        sheet = self._get_sheet()
        records = sheet.get_all_records()
        headers = sheet.row_values(1)
        for idx, row in enumerate(records, start=2):  # gspread rows start at 1; row 1 header
            if str(row.get("license_key", "")).strip() != str(license_key).strip():
                continue
            try:
                values_list = list(hardware_components.values())
                hw1 = headers.index("hw_component_1") + 1 if "hw_component_1" in headers else None
                hw2 = headers.index("hw_component_2") + 1 if "hw_component_2" in headers else None
                hw3 = headers.index("hw_component_3") + 1 if "hw_component_3" in headers else None
                transfer_col = headers.index("transfer_count") + 1 if "transfer_count" in headers else None
                status_col = headers.index("status") + 1 if "status" in headers else None
                if hw1:
                    sheet.update_cell(idx, hw1, values_list[0] if len(values_list) > 0 else "")
                if hw2:
                    sheet.update_cell(idx, hw2, values_list[1] if len(values_list) > 1 else "")
                if hw3:
                    sheet.update_cell(idx, hw3, values_list[2] if len(values_list) > 2 else "")
                if transfer_col:
                    sheet.update_cell(idx, transfer_col, int(row.get("transfer_count", 0)) + 1)
                if status_col:
                    sheet.update_cell(idx, status_col, "active")
                return True
            except Exception as exc:  # pragma: no cover - runtime update errors
                logger.error(f"Failed to update transfer: {exc}")
                return False
        return False
