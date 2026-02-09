"""
License Admin Service

Provides admin CRUD operations for licenses in Supabase.
All operations use the Supabase service role key.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import mimetypes
import threading
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config_manager import ConfigManager
from core.crypto import generate_license_key, VALID_TIERS
from core.supabase_client import (
    SupabaseClient,
    SupabaseConnectionError,
    SupabaseAPIError,
    SupabaseError,
)


class LicenseAdminService:
    """Service for managing license records in Supabase."""

    VALID_STATUSES = ("active", "expired", "revoked")

    def __init__(self, supabase_client: Optional[SupabaseClient] = None):
        self._supabase = supabase_client
        self._config = ConfigManager()
        self._lock = threading.Lock()

    def _ensure_supabase(self) -> None:
        if self._supabase is not None:
            return
        with self._lock:
            if self._supabase is not None:
                return
            url = self._config.get("supabase.url", "").strip()
            service_key = (
                os.environ.get("SUPABASE_SERVICE_KEY", "")
                or self._config.get("supabase.service_key", "")
                or self._read_admin_service_key()
            ).strip()
            if not url or not service_key:
                raise SupabaseConnectionError(
                    "Supabase admin credentials not configured. "
                    "Set supabase.service_key in config or SUPABASE_SERVICE_KEY env var."
                )
            self._supabase = SupabaseClient(url=url, anon_key=service_key)

    def _read_admin_service_key(self) -> str:
        """Load admin service key from admin_config.yaml if present."""
        candidates = []

        user_dir = os.environ.get("WATERBALANCE_USER_DIR", "")
        if user_dir:
            candidates.append(Path(user_dir) / "config" / "admin_config.yaml")

        candidates.append(Path(__file__).parent.parent.parent / "config" / "admin_config.yaml")

        for path in candidates:
            if not path.exists():
                continue
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                return (data.get("supabase", {}) or {}).get("service_key", "")
            except Exception:
                continue

        return ""

    def list_licenses(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Return latest licenses ordered by creation time (desc)."""
        self._ensure_supabase()
        return self._supabase.select(
            table="licenses",
            order="created_at.desc",
            limit=limit,
        )

    def get_license(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Fetch a single license by key."""
        self._ensure_supabase()
        license_key = license_key.strip().upper()
        if not license_key:
            return None
        return self._supabase.select(
            table="licenses",
            filters={"license_key": license_key},
            single=True,
        )

    def list_feedback(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Return feedback submissions ordered by newest first."""
        self._ensure_supabase()
        return self._supabase.select(
            table="feature_requests",
            order="created_at.desc",
            limit=limit,
        )

    def list_notifications(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Return notifications ordered by newest first."""
        self._ensure_supabase()
        return self._supabase.select(
            table="notifications",
            order="published_at.desc",
            limit=limit,
        )

    def create_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a notification record."""
        self._ensure_supabase()
        payload = dict(data)

        expires_at = payload.get("expires_at")
        if isinstance(expires_at, datetime):
            exp = expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            payload["expires_at"] = exp.isoformat()
        elif expires_at in ("", None):
            payload.pop("expires_at", None)

        result = self._supabase.insert("notifications", payload)
        if not result:
            raise SupabaseAPIError("Failed to create notification")
        return result[0]

    def upload_notification_asset(self, file_path: str) -> str:
        """Upload an image asset for notifications and return public URL."""
        self._ensure_supabase()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {file_path}")

        bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "notification-assets")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        object_name = f"notifications/{timestamp}-{path.name}"
        content_type, _ = mimetypes.guess_type(str(path))
        content_type = content_type or "application/octet-stream"

        data = path.read_bytes()
        self._supabase.upload_storage_object(bucket, object_name, data, content_type)

        return f"{self._supabase.url}/storage/v1/object/public/{bucket}/{object_name}"

    def delete_notification_assets_older_than(self, days: int) -> int:
        """Delete notification images older than the given number of days."""
        self._ensure_supabase()
        bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "notification-assets")
        prefix = "notifications"

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        objects = self._supabase.list_storage_objects(bucket, prefix=prefix)
        if not objects:
            return 0

        to_delete = []
        for obj in objects:
            created = obj.get("created_at")
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    created = None
            if created and created < cutoff:
                to_delete.append(obj.get("name"))

        if not to_delete:
            return 0

        self._supabase.delete_storage_objects(bucket, to_delete)
        return len(to_delete)

    def delete_notification(self, notification_id: str) -> None:
        """Delete a notification by id."""
        self._ensure_supabase()
        notification_id = (notification_id or "").strip()
        if not notification_id:
            raise ValueError("Notification id is required")
        result = self._supabase.delete(
            table="notifications",
            filters={"id": notification_id},
        )
        if result is None:
            raise SupabaseAPIError("Failed to delete notification")

    def update_feedback_status(self, feedback_id: str, status: str) -> Dict[str, Any]:
        """Update feedback status by id."""
        self._ensure_supabase()
        status = (status or "").strip().lower()
        if status not in ("open", "in_progress", "resolved", "closed", "wont_fix"):
            raise ValueError(f"Invalid feedback status: {status}")
        result = self._supabase.update(
            table="feature_requests",
            data={"status": status},
            filters={"id": feedback_id},
        )
        if not result:
            raise SupabaseAPIError("Failed to update feedback status")
        return result[0]

    def create_license(
        self,
        license_key: Optional[str],
        tier: str,
        status: str,
        expires_at: Optional[datetime],
        customer_name: Optional[str],
        customer_email: Optional[str],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new license record and return it."""
        self._ensure_supabase()

        tier = (tier or "").strip().lower()
        status = (status or "").strip().lower()

        if tier not in VALID_TIERS:
            raise ValueError(f"Invalid tier: {tier}")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        license_key = (license_key or "").strip().upper() or generate_license_key()

        data: Dict[str, Any] = {
            "license_key": license_key,
            "tier": tier,
            "status": status,
        }

        if expires_at:
            expires = expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            data["expires_at"] = expires.isoformat()

        if customer_name:
            data["customer_name"] = customer_name.strip()
        if customer_email:
            data["customer_email"] = customer_email.strip()
        if notes:
            data["notes"] = notes.strip()

        result = self._supabase.insert("licenses", data)
        if not result:
            raise SupabaseAPIError("Failed to create license")
        return result[0]

    def update_license(self, license_key: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a license and return the updated record."""
        self._ensure_supabase()
        license_key = license_key.strip().upper()
        if not license_key:
            raise ValueError("License key is required")

        if "tier" in updates and updates["tier"]:
            tier = updates["tier"].strip().lower()
            if tier not in VALID_TIERS:
                raise ValueError(f"Invalid tier: {tier}")
            updates["tier"] = tier

        if "status" in updates and updates["status"]:
            status = updates["status"].strip().lower()
            if status not in self.VALID_STATUSES:
                raise ValueError(f"Invalid status: {status}")
            updates["status"] = status

        if "expires_at" in updates and updates["expires_at"] is None:
            updates["expires_at"] = None
        elif "expires_at" in updates and isinstance(updates["expires_at"], datetime):
            expires = updates["expires_at"]
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            updates["expires_at"] = expires.isoformat()

        if "customer_name" in updates and updates["customer_name"] is not None:
            updates["customer_name"] = updates["customer_name"].strip()
        if "customer_email" in updates and updates["customer_email"] is not None:
            updates["customer_email"] = updates["customer_email"].strip()
        if "notes" in updates and updates["notes"] is not None:
            updates["notes"] = updates["notes"].strip()

        result = self._supabase.update(
            table="licenses",
            data=updates,
            filters={"license_key": license_key},
        )
        if not result:
            raise SupabaseAPIError("Failed to update license")
        return result[0]

    def set_status(self, license_key: str, status: str) -> Dict[str, Any]:
        """Set license status."""
        return self.update_license(license_key, {"status": status})


_admin_service_instance: Optional[LicenseAdminService] = None


def get_license_admin_service() -> LicenseAdminService:
    """Return singleton LicenseAdminService instance."""
    global _admin_service_instance
    if _admin_service_instance is None:
        _admin_service_instance = LicenseAdminService()
    return _admin_service_instance
