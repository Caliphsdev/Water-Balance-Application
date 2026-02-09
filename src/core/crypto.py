"""
Cryptographic Utilities for License System

Provides Ed25519 digital signature functionality for:
- Signing license tokens (admin tool only, requires private key)
- Verifying license tokens (client app, uses embedded public key)

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import base64
import json
import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


# (CONSTANTS)

def _load_public_key_config() -> str:
    """Load public key from config."""
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        return config.get('license.public_key', '')
    except Exception:
        return ''


def _load_private_key_config() -> str:
    """Load private key from config (admin tooling only)."""
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        return config.get('license.private_key', '')
    except Exception:
        return ''


_NACL_IMPORT_ERROR = ""
try:
    from nacl.signing import SigningKey, VerifyKey
    _HAS_NACL = True
except Exception as e:
    SigningKey = None
    VerifyKey = None
    _HAS_NACL = False
    _NACL_IMPORT_ERROR = str(e)

# Public key for license verification (embedded in app)
# This is safe to distribute - it can only VERIFY signatures, not create them
PUBLIC_KEY_BASE64 = os.environ.get('WATERBALANCE_PUBLIC_KEY', '') or _load_public_key_config()
PRIVATE_KEY_BASE64 = os.environ.get('WATERBALANCE_PRIVATE_KEY', '') or _load_private_key_config()

# Token version for future compatibility
TOKEN_VERSION = 1

# License tiers
VALID_TIERS = ('developer', 'premium', 'standard', 'free_trial')


def generate_ed25519_keypair_base64() -> Tuple[str, str]:
    """
    Generate an Ed25519 key pair and return URL-safe base64 strings.

    Returns:
        Tuple of (public_key_b64, private_key_b64).
    """
    if not _HAS_NACL:
        raise ValueError("PyNaCl is required to generate Ed25519 keys.")

    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    private_b64 = base64.urlsafe_b64encode(signing_key.encode()).decode('utf-8').rstrip('=')
    public_b64 = base64.urlsafe_b64encode(verify_key.encode()).decode('utf-8').rstrip('=')
    return public_b64, private_b64


# (TOKEN STRUCTURE)

class LicenseToken:
    """
    Represents a signed license token.
    
    Token structure (JSON):
    {
        "v": 1,                           # Token version
        "key": "WB-XXXX-XXXX-XXXX",       # License key
        "hwid": "a1b2c3d4...",            # Hardware ID
        "tier": "premium",                 # License tier
        "exp": "2026-03-04T00:00:00Z",    # Expiry timestamp (ISO 8601)
        "iat": "2026-02-04T00:00:00Z"     # Issued at timestamp
    }
    
    The token is Base64-encoded JSON with a signature appended:
    BASE64(json).SIGNATURE
    """
    
    def __init__(
        self,
        license_key: str,
        hwid: str,
        tier: str,
        expires_at: datetime,
        issued_at: Optional[datetime] = None
    ):
        self.version = TOKEN_VERSION
        self.license_key = license_key
        self.hwid = hwid
        self.tier = tier
        self.expires_at = expires_at
        self.issued_at = issued_at or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert token to dictionary for serialization."""
        return {
            "v": self.version,
            "key": self.license_key,
            "hwid": self.hwid,
            "tier": self.tier,
            "exp": self.expires_at.isoformat(),
            "iat": self.issued_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LicenseToken':
        """Create token from dictionary."""
        return cls(
            license_key=data["key"],
            hwid=data["hwid"],
            tier=data["tier"],
            expires_at=datetime.fromisoformat(data["exp"]),
            issued_at=datetime.fromisoformat(data["iat"])
        )
    
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        now = datetime.now(timezone.utc)
        # Ensure expires_at is timezone-aware
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp
    
    def days_until_expiry(self) -> int:
        """Get days until token expires (negative if expired)."""
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        delta = exp - now
        return delta.days


# (ED25519 SIGNING)

def _b64decode_key(value: str) -> bytes:
    """Decode URL-safe base64 key data, handling missing padding."""
    raw = (value or '').strip().encode('utf-8')
    if not raw:
        return b''
    padding = b'=' * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)

def _get_signing_key() -> bytes:
    """Get the Ed25519 private key from environment/config."""
    if not PRIVATE_KEY_BASE64:
        raise ValueError(
            "No signing key configured. "
            "Set WATERBALANCE_PRIVATE_KEY or license.private_key in config."
        )
    if not _HAS_NACL:
        detail = f" PyNaCl import error: {_NACL_IMPORT_ERROR}" if _NACL_IMPORT_ERROR else ""
        raise ValueError(f"PyNaCl is required for Ed25519 signing.{detail}")
    key_bytes = _b64decode_key(PRIVATE_KEY_BASE64)
    if not key_bytes:
        raise ValueError("Invalid private key encoding.")
    return key_bytes


def _get_verification_key() -> bytes:
    """Get the Ed25519 public key from environment/config."""
    if not PUBLIC_KEY_BASE64:
        raise ValueError(
            "No verification key configured. "
            "Set WATERBALANCE_PUBLIC_KEY or license.public_key in config."
        )
    if not _HAS_NACL:
        detail = f" PyNaCl import error: {_NACL_IMPORT_ERROR}" if _NACL_IMPORT_ERROR else ""
        raise ValueError(f"PyNaCl is required for Ed25519 verification.{detail}")
    key_bytes = _b64decode_key(PUBLIC_KEY_BASE64)
    if not key_bytes:
        raise ValueError("Invalid public key encoding.")
    return key_bytes


def sign_token(token: LicenseToken) -> str:
    """
    Sign a license token and return the complete signed token string.
    
    Format: BASE64(json_payload).SIGNATURE
    
    Args:
        token: The LicenseToken to sign.
        
    Returns:
        Signed token string.
        
    Raises:
        ValueError: If signing key is not configured.
    """
    try:
        # Serialize token to JSON
        payload_json = json.dumps(token.to_dict(), separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')
        
        # Sign with Ed25519
        key = _get_signing_key()
        signing_key = SigningKey(key)
        signed = signing_key.sign(payload_b64.encode('utf-8'))
        signature = base64.urlsafe_b64encode(signed.signature).decode('utf-8')
        
        # Combine payload and signature
        signed_token = f"{payload_b64}.{signature}"
        
        logger.debug(f"Signed token for license {token.license_key}")
        return signed_token
        
    except Exception as e:
        logger.error(f"Failed to sign token: {e}")
        raise


def verify_token(signed_token: str) -> Tuple[bool, Optional[LicenseToken], str]:
    """
    Verify a signed license token.
    
    Args:
        signed_token: The signed token string (payload.signature format).
        
    Returns:
        Tuple of (is_valid, token_or_none, error_message).
    """
    try:
        # Split into payload and signature
        parts = signed_token.split('.')
        if len(parts) != 2:
            return False, None, "Invalid token format"
        
        payload_b64, signature = parts
        
        # Verify signature
        key = _get_verification_key()
        verify_key = VerifyKey(key)
        signature_bytes = _b64decode_key(signature)
        try:
            verify_key.verify(payload_b64.encode('utf-8'), signature_bytes)
        except Exception:
            return False, None, "Invalid signature"
        
        # Decode payload
        payload_json = _b64decode_key(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Check version
        if payload.get('v', 0) > TOKEN_VERSION:
            return False, None, f"Unsupported token version: {payload.get('v')}"
        
        # Validate tier
        if payload.get('tier') not in VALID_TIERS:
            return False, None, f"Invalid tier: {payload.get('tier')}"
        
        # Parse token
        token = LicenseToken.from_dict(payload)
        
        logger.debug(f"Token verified for license {token.license_key}")
        return True, token, ""
        
    except json.JSONDecodeError as e:
        return False, None, f"Invalid token payload: {e}"
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return False, None, f"Verification error: {e}"


def verify_token_hwid(signed_token: str, expected_hwid: str) -> Tuple[bool, Optional[LicenseToken], str]:
    """
    Verify a signed token AND check that HWID matches.
    
    Args:
        signed_token: The signed token string.
        expected_hwid: The HWID that should match the token.
        
    Returns:
        Tuple of (is_valid, token_or_none, error_message).
    """
    is_valid, token, error = verify_token(signed_token)
    
    if not is_valid:
        return False, None, error
    
    if token.hwid != expected_hwid:
        return False, None, "Hardware ID mismatch - license bound to different machine"
    
    return True, token, ""


# (UTILITY FUNCTIONS)

def generate_license_key(prefix: str = "WB") -> str:
    """
    Generate a new license key.
    
    Format: WB-XXXX-XXXX-XXXX (16 random chars + prefix)
    
    Args:
        prefix: Key prefix (default "WB" for Water Balance).
        
    Returns:
        New license key string.
    """
    import secrets
    
    # Generate 12 random bytes and encode as hex
    random_hex = secrets.token_hex(6).upper()  # 12 hex chars
    
    # Format as XXXX-XXXX-XXXX
    parts = [random_hex[i:i+4] for i in range(0, 12, 4)]
    
    return f"{prefix}-{'-'.join(parts)}"


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2-SHA256.
    
    Args:
        password: The password to hash.
        salt: Optional salt bytes. Generated if not provided.
        
    Returns:
        Tuple of (hashed_password_hex, salt_hex).
    """
    import secrets
    
    if salt is None:
        salt = secrets.token_bytes(16)
    
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000
    )
    
    return hashed.hex(), salt.hex()


def verify_password(password: str, hashed_hex: str, salt_hex: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: The password to verify.
        hashed_hex: The stored hash (hex string).
        salt_hex: The stored salt (hex string).
        
    Returns:
        True if password matches, False otherwise.
    """
    salt = bytes.fromhex(salt_hex)
    expected_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(expected_hash, hashed_hex)


# (MODULE TEST)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Crypto Module Test")
    logger.info("=" * 50)
    
    # Generate test key
    test_key = generate_license_key()
    logger.info("Generated license key: %s", test_key)
    
    # Create test token (requires WATERBALANCE_PRIVATE_KEY to be set)
    if os.environ.get('WATERBALANCE_PRIVATE_KEY'):
        from datetime import timedelta
        
        token = LicenseToken(
            license_key=test_key,
            hwid="test_hwid_12345678",
            tier="premium",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        logger.info("\nToken payload: %s", token.to_dict())
        
        signed = sign_token(token)
        logger.info("\nSigned token: %s...", signed[:50])
        
        is_valid, verified_token, error = verify_token(signed)
        status = "✓ Valid" if is_valid else f"✗ Invalid: {error}"
        logger.info("\nVerification: %s", status)
        
        if verified_token:
            logger.info("Days until expiry: %s", verified_token.days_until_expiry())
    else:
        logger.info("\nNote: Set WATERBALANCE_PRIVATE_KEY to test signing/verification")
