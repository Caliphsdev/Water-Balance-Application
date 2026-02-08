"""
License Service

Handles license validation, activation, and offline token management.
Implements strict blocking when license expires offline.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import os
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any

from core.hwid import get_hwid, get_hwid_display
from core.crypto import (
    LicenseToken, 
    sign_token, 
    verify_token, 
    verify_token_hwid,
    VALID_TIERS
)
from core.supabase_client import (
    get_supabase_client, 
    SupabaseClient,
    SupabaseError,
    SupabaseConnectionError,
    SupabaseAPIError
)

logger = logging.getLogger(__name__)


# (CONSTANTS)

# License token validity period (days) for offline use
OFFLINE_TOKEN_VALIDITY_DAYS = 7

# How many days before expiry to refresh online
REFRESH_INTERVAL_DAYS = 1

# License file location
LICENSE_FILENAME = "license.dat"

# Clock tamper guard
CLOCK_GUARD_FILENAME = "license_clock.json"
CLOCK_SKEW_TOLERANCE_SECONDS = 600


# (LICENSE STATUS)

class LicenseStatus:
    """Represents the current license status."""
    
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_ACTIVATED = "not_activated"
    HWID_MISMATCH = "hwid_mismatch"
    REVOKED = "revoked"
    NETWORK_ERROR = "network_error"
    
    def __init__(
        self,
        status: str,
        tier: Optional[str] = None,
        message: str = "",
        days_remaining: Optional[int] = None,
        needs_online_refresh: bool = False
    ):
        self.status = status
        self.tier = tier
        self.message = message
        self.days_remaining = days_remaining
        self.needs_online_refresh = needs_online_refresh
    
    @property
    def is_valid(self) -> bool:
        """Check if license is valid and app should run."""
        return self.status == self.VALID
    
    @property
    def should_block(self) -> bool:
        """Check if app should be blocked from running."""
        return self.status in (
            self.EXPIRED, 
            self.INVALID, 
            self.NOT_ACTIVATED,
            self.HWID_MISMATCH,
            self.REVOKED
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status,
            "tier": self.tier,
            "message": self.message,
            "days_remaining": self.days_remaining,
            "needs_online_refresh": self.needs_online_refresh
        }


# (LICENSE SERVICE)

class LicenseService:
    """
    Service for managing license validation and activation.
    
    Implements:
    - Online license activation with HWID binding
    - Offline token validation with strict expiry blocking
    - Automatic token refresh when online
    - License tier information
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        supabase_client: Optional[SupabaseClient] = None
    ):
        """
        Initialize license service.
        
        Args:
            data_dir: Directory for license.dat file.
            supabase_client: Supabase client instance (for testing).
        """
        self._data_dir = data_dir
        self._supabase = supabase_client
        self._current_token: Optional[LicenseToken] = None
        self._license_status: Optional[LicenseStatus] = None
        self._init_lock = threading.Lock()
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """Ensure service is initialized."""
        if self._initialized:
            return
        
        with self._init_lock:
            if self._initialized:
                return
            
            # Set up data directory
            if self._data_dir is None:
                user_dir = os.environ.get('WATERBALANCE_USER_DIR', '')
                if user_dir:
                    self._data_dir = Path(user_dir) / "data"
                else:
                    self._data_dir = Path(__file__).parent.parent.parent / "data"
            
            self._data_dir.mkdir(parents=True, exist_ok=True)
            
            # Set up Supabase client
            if self._supabase is None:
                self._supabase = get_supabase_client()
            
            self._initialized = True
            logger.debug(f"License service initialized, data dir: {self._data_dir}")
    
    @property
    def license_file_path(self) -> Path:
        """Get path to license.dat file."""
        self._ensure_initialized()
        return self._data_dir / LICENSE_FILENAME
    
    @property
    def hwid(self) -> str:
        """Get this machine's hardware ID."""
        return get_hwid()
    
    @property
    def hwid_display(self) -> str:
        """Get formatted HWID for display."""
        return get_hwid_display()

    @property
    def _clock_guard_path(self) -> Path:
        self._ensure_initialized()
        return self._data_dir / CLOCK_GUARD_FILENAME
    
    # (LICENSE FILE OPERATIONS)
    
    def _load_license_file(self) -> Optional[str]:
        """
        Load license token from file.
        
        Returns:
            Signed token string or None if file doesn't exist.
        """
        self._ensure_initialized()
        
        if not self.license_file_path.exists():
            logger.debug("No license file found")
            return None
        
        try:
            with open(self.license_file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read license file: {e}")
            return None
    
    def _save_license_file(self, signed_token: str) -> bool:
        """
        Save license token to file.
        
        Args:
            signed_token: The signed token string to save.
            
        Returns:
            True if saved successfully.
        """
        self._ensure_initialized()
        
        try:
            with open(self.license_file_path, 'w', encoding='utf-8') as f:
                f.write(signed_token)
            logger.debug("License file saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save license file: {e}")
            return False
    
    def _delete_license_file(self) -> bool:
        """
        Delete the license file.
        
        Returns:
            True if deleted or didn't exist.
        """
        try:
            if self.license_file_path.exists():
                self.license_file_path.unlink()
                logger.info("License file deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete license file: {e}")
            return False

    # (CLOCK GUARD)

    def _load_clock_guard(self) -> Optional[datetime]:
        """Load last seen timestamp used to detect clock rollback."""
        try:
            if not self._clock_guard_path.exists():
                return None
            raw = self._clock_guard_path.read_text(encoding='utf-8')
            data = json.loads(raw)
            last_seen = data.get("last_seen")
            if not last_seen:
                return None
            return datetime.fromisoformat(last_seen)
        except Exception as e:
            logger.debug(f"Failed to read clock guard: {e}")
            return None

    def _save_clock_guard(self, timestamp: datetime) -> None:
        """Persist last seen timestamp."""
        try:
            payload = {"last_seen": timestamp.isoformat()}
            self._clock_guard_path.write_text(json.dumps(payload), encoding='utf-8')
        except Exception as e:
            logger.debug(f"Failed to write clock guard: {e}")

    def _check_clock_tamper(self) -> Tuple[bool, str]:
        """Detect if system clock moved backward beyond tolerance."""
        last_seen = self._load_clock_guard()
        if not last_seen:
            return True, ""
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now < last_seen - timedelta(seconds=CLOCK_SKEW_TOLERANCE_SECONDS):
            return False, "System time appears to have been changed. Please reconnect and re-activate."
        return True, ""
    
    # (ONLINE VALIDATION)
    
    def _validate_license_online(
        self,
        license_key: str
    ) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate license key against Supabase.
        
        Args:
            license_key: The license key to validate.
            
        Returns:
            Tuple of (is_valid, license_data, error_message).
        """
        try:
            # Query license from Supabase
            result = self._supabase.select(
                table="licenses",
                filters={"license_key": license_key},
                single=True
            )
            
            if not result:
                return False, None, "License key not found"
            
            # Check status (active, expired, revoked)
            status = result.get("status", "").lower()
            if status == "revoked":
                return False, None, "License has been revoked"
            elif status == "expired":
                return False, None, "License has expired"
            elif status != "active":
                return False, None, f"Invalid license status: {status}"
            
            # Check if already bound to different HWID
            existing_hwid = result.get("hwid")
            if existing_hwid and existing_hwid != self.hwid:
                return False, None, "License is bound to a different machine"
            
            # Check expiry (if set)
            expires_at = result.get("expires_at")
            if expires_at:
                exp_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > exp_dt:
                    return False, None, "License has expired"
            
            return True, result, ""
            
        except SupabaseConnectionError as e:
            logger.warning(f"Cannot connect to license server: {e}")
            return False, None, f"Cannot connect to license server: {e}"
        except SupabaseAPIError as e:
            logger.error(f"License server error: {e}")
            return False, None, f"License server error: {e.details or e}"
        except Exception as e:
            logger.error(f"License validation failed: {e}")
            return False, None, f"Validation error: {e}"
    
    def _bind_hwid_online(
        self,
        license_key: str,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Bind this machine's HWID to a license key.
        
        Args:
            license_key: The license key to bind.
            
        Returns:
            True if bound successfully.
        """
        try:
            params = {
                "p_license_key": license_key,
                "p_hwid": self.hwid,
                "p_customer_name": customer_name,
                "p_customer_email": customer_email,
            }
            self._supabase.rpc("bind_license", params=params)
            logger.info(f"HWID bound to license {license_key[:12]} via RPC")
            return True, ""
        except SupabaseAPIError as e:
            details = e.details or str(e)
            logger.error(f"Failed to bind HWID via RPC: {details}")
            if "bind_license" in details and ("does not exist" in details or "not found" in details):
                return False, "bind_license RPC missing. Run the Supabase migration SQL."
            return False, f"Supabase RPC error: {details}"
        except Exception as e:
            logger.error(f"Failed to bind HWID: {e}")
            return False, f"Bind failed: {e}"
    
    def _update_last_validated(self, license_key: str) -> bool:
        """
        Update last_validated timestamp for a license.
        
        Args:
            license_key: The license key to update.
            
        Returns:
            True if updated successfully.
        """
        try:
            self._supabase.update(
                table="licenses",
                data={"last_validated": datetime.now(timezone.utc).isoformat()},
                filters={"license_key": license_key}
            )
            return True
        except Exception as e:
            logger.debug(f"Failed to update last_validated: {e}")
            return False
    
    # (TOKEN OPERATIONS)
    
    def _create_offline_token(
        self,
        license_key: str,
        tier: str,
        server_expiry: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Create a signed offline token.
        
        Args:
            license_key: The license key.
            tier: License tier.
            server_expiry: Server-side expiry (if any).
            
        Returns:
            Signed token string or None if signing fails.
        """
        # Calculate token expiry (minimum of server expiry and offline validity)
        offline_expiry = datetime.now(timezone.utc) + timedelta(days=OFFLINE_TOKEN_VALIDITY_DAYS)
        
        if server_expiry:
            if server_expiry.tzinfo is None:
                server_expiry = server_expiry.replace(tzinfo=timezone.utc)
            expiry = min(offline_expiry, server_expiry)
        else:
            expiry = offline_expiry
        
        token = LicenseToken(
            license_key=license_key,
            hwid=self.hwid,
            tier=tier,
            expires_at=expiry
        )
        
        try:
            return sign_token(token)
        except Exception as e:
            logger.error(f"Failed to create offline token: {e}")
            return None
    
    # (PUBLIC API)
    
    def activate(
        self,
        license_key: str,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> LicenseStatus:
        """
        Activate a license key (requires internet).
        
        This is the primary method for first-time activation.
        Validates online, binds HWID, and creates offline token.
        
        Args:
            license_key: The license key to activate.
            customer_name: Optional customer name for first activation.
            customer_email: Optional customer email for first activation.
            
        Returns:
            LicenseStatus indicating result.
        """
        self._ensure_initialized()
        license_key = license_key.strip().upper()
        customer_name = customer_name.strip() if customer_name else None
        customer_email = customer_email.strip() if customer_email else None
        
        logger.info(f"Activating license {license_key[:12]}...")
        
        # Validate online
        is_valid, license_data, error = self._validate_license_online(license_key)
        
        if not is_valid:
            logger.warning(f"License activation failed: {error}")
            
            if "Cannot connect" in error:
                return LicenseStatus(
                    LicenseStatus.NETWORK_ERROR,
                    message="Internet connection required for activation"
                )
            elif "different machine" in error:
                return LicenseStatus(
                    LicenseStatus.HWID_MISMATCH,
                    message=error
                )
            elif "revoked" in error.lower():
                return LicenseStatus(
                    LicenseStatus.REVOKED,
                    message=error
                )
            else:
                return LicenseStatus(
                    LicenseStatus.INVALID,
                    message=error
                )
        
        # Require customer details on first activation
        missing_customer = not (license_data.get("customer_name") and license_data.get("customer_email"))
        if not license_data.get("hwid") and missing_customer:
            if not (customer_name and customer_email):
                return LicenseStatus(
                    LicenseStatus.INVALID,
                    message="Name and email are required for first activation"
                )

        # Bind HWID or fill missing customer info
        needs_customer_update = missing_customer and customer_name and customer_email
        if not license_data.get("hwid") or needs_customer_update:
            bind_name = customer_name if not license_data.get("customer_name") else None
            bind_email = customer_email if not license_data.get("customer_email") else None
            ok, bind_error = self._bind_hwid_online(license_key, bind_name, bind_email)
            if not ok:
                return LicenseStatus(
                    LicenseStatus.NETWORK_ERROR,
                    message=bind_error or "Failed to bind license to this machine"
                )
        
        # Create and save offline token
        tier = license_data.get("tier", "standard")
        server_expiry = None
        if license_data.get("expires_at"):
            server_expiry = datetime.fromisoformat(
                license_data["expires_at"].replace('Z', '+00:00')
            )
        
        signed_token = self._create_offline_token(license_key, tier, server_expiry)
        
        if not signed_token:
            return LicenseStatus(
                LicenseStatus.INVALID,
                message="Failed to create license token"
            )
        
        if not self._save_license_file(signed_token):
            return LicenseStatus(
                LicenseStatus.INVALID,
                message="Failed to save license file"
            )
        
        # Verify the saved token
        is_valid, token, _ = verify_token_hwid(signed_token, self.hwid)
        if is_valid:
            self._current_token = token
            self._license_status = LicenseStatus(
                LicenseStatus.VALID,
                tier=tier,
                message="License activated successfully",
                days_remaining=token.days_until_expiry()
            )
            self._save_clock_guard(datetime.now(timezone.utc))
        
        logger.info(f"License activated: tier={tier}")
        return self._license_status
    
    def validate(self, try_refresh: bool = True) -> LicenseStatus:
        """
        Validate the current license.
        
        Checks offline token first, optionally tries online refresh.
        STRICT BLOCKING: If token is expired, app will not run.
        
        Args:
            try_refresh: Whether to attempt online refresh if needed.
            
        Returns:
            LicenseStatus indicating current state.
        """
        self._ensure_initialized()
        
        # Load license file
        signed_token = self._load_license_file()
        
        if not signed_token:
            self._license_status = LicenseStatus(
                LicenseStatus.NOT_ACTIVATED,
                message="No license found. Please activate."
            )
            return self._license_status
        
        # Verify signature and HWID
        is_valid, token, error = verify_token_hwid(signed_token, self.hwid)
        
        if not is_valid:
            logger.warning(f"License validation failed: {error}")
            self._delete_license_file()
            
            if "Hardware ID mismatch" in error:
                self._license_status = LicenseStatus(
                    LicenseStatus.HWID_MISMATCH,
                    message="License bound to different machine"
                )
            else:
                self._license_status = LicenseStatus(
                    LicenseStatus.INVALID,
                    message=f"Invalid license: {error}"
                )
            return self._license_status
        
        # Check expiry - STRICT BLOCKING
        if token.is_expired():
            logger.warning("License token expired")
            
            # Try online refresh if allowed
            if try_refresh:
                refresh_status = self._try_online_refresh(token.license_key)
                if refresh_status.is_valid:
                    return refresh_status
            
            # STRICT BLOCK - expired and couldn't refresh
            self._license_status = LicenseStatus(
                LicenseStatus.EXPIRED,
                tier=token.tier,
                message="License expired. Connect to internet to renew.",
                days_remaining=token.days_until_expiry()
            )
            return self._license_status

        # Detect clock tampering
        clock_ok, clock_error = self._check_clock_tamper()
        if not clock_ok:
            self._license_status = LicenseStatus(
                LicenseStatus.INVALID,
                tier=token.tier,
                message=clock_error,
                days_remaining=token.days_until_expiry()
            )
            return self._license_status
        
        # Token is valid
        self._current_token = token
        
        # Check if refresh is due
        needs_refresh = token.days_until_expiry() <= REFRESH_INTERVAL_DAYS
        
        if needs_refresh and try_refresh:
            # Try background refresh (non-blocking)
            self._try_online_refresh(token.license_key)
        
        self._license_status = LicenseStatus(
            LicenseStatus.VALID,
            tier=token.tier,
            message="License valid",
            days_remaining=token.days_until_expiry(),
            needs_online_refresh=needs_refresh
        )

        self._save_clock_guard(datetime.now(timezone.utc))
        
        return self._license_status
    
    def _try_online_refresh(self, license_key: str) -> LicenseStatus:
        """
        Try to refresh license token online.
        
        Args:
            license_key: The license key to refresh.
            
        Returns:
            Updated LicenseStatus.
        """
        logger.debug("Attempting online license refresh...")
        
        is_valid, license_data, error = self._validate_license_online(license_key)
        
        if not is_valid:
            if "Cannot connect" in error:
                # Network error - keep existing token
                return LicenseStatus(
                    LicenseStatus.NETWORK_ERROR,
                    message="Could not refresh license (offline)"
                )
            else:
                # License revoked or invalid
                self._delete_license_file()
                return LicenseStatus(
                    LicenseStatus.REVOKED if "revoked" in error.lower() else LicenseStatus.INVALID,
                    message=error
                )
        
        # Update last validated
        self._update_last_validated(license_key)
        
        # Create new token
        tier = license_data.get("tier", "standard")
        server_expiry = None
        if license_data.get("expires_at"):
            server_expiry = datetime.fromisoformat(
                license_data["expires_at"].replace('Z', '+00:00')
            )
        
        signed_token = self._create_offline_token(license_key, tier, server_expiry)
        
        if signed_token and self._save_license_file(signed_token):
            is_valid, token, _ = verify_token_hwid(signed_token, self.hwid)
            if is_valid:
                self._current_token = token
                logger.info("License refreshed successfully")
                self._save_clock_guard(datetime.now(timezone.utc))
                return LicenseStatus(
                    LicenseStatus.VALID,
                    tier=tier,
                    message="License refreshed",
                    days_remaining=token.days_until_expiry()
                )
        
        return LicenseStatus(
            LicenseStatus.INVALID,
            message="Failed to refresh license"
        )
    
    def deactivate(self) -> bool:
        """
        Deactivate license on this machine.
        
        Removes local license file. Does NOT unbind HWID server-side.
        
        Returns:
            True if deactivated successfully.
        """
        self._current_token = None
        self._license_status = None
        return self._delete_license_file()
    
    def get_status(self) -> LicenseStatus:
        """
        Get current license status without re-validating.
        
        Returns:
            Current LicenseStatus or NOT_ACTIVATED if not validated yet.
        """
        if self._license_status is None:
            return self.validate(try_refresh=False)
        return self._license_status
    
    def get_tier(self) -> Optional[str]:
        """
        Get current license tier.
        
        Returns:
            Tier string ('developer', 'premium', 'standard', 'free_trial') or None.
        """
        status = self.get_status()
        return status.tier
    
    def is_licensed(self) -> bool:
        """
        Quick check if app is licensed.
        
        Returns:
            True if license is valid.
        """
        return self.get_status().is_valid
    
    def get_license_info(self) -> Dict[str, Any]:
        """
        Get detailed license information.
        
        Returns:
            Dictionary with license details.
        """
        status = self.get_status()
        return {
            "status": status.status,
            "is_valid": status.is_valid,
            "tier": status.tier,
            "message": status.message,
            "days_remaining": status.days_remaining,
            "hwid": self.hwid_display,
            "license_key": self._current_token.license_key if self._current_token else None
        }


# (SINGLETON)

_service_instance: Optional[LicenseService] = None


def get_license_service() -> LicenseService:
    """
    Get the singleton LicenseService instance.
    
    Returns:
        LicenseService instance.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = LicenseService()
    return _service_instance


# (MODULE TEST)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("License Service Test")
    logger.info("=" * 50)
    
    service = get_license_service()
    
    logger.info("HWID: %s", service.hwid_display)
    logger.info("License file: %s", service.license_file_path)
    
    logger.info("")
    logger.info("Validating license...")
    status = service.validate(try_refresh=False)
    
    logger.info("Status: %s", status.status)
    logger.info("Tier: %s", status.tier)
    logger.info("Message: %s", status.message)
    logger.info("Days remaining: %s", status.days_remaining)
    logger.info("Should block: %s", status.should_block)
