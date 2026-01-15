"""Simple encryption helpers for license payloads."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

from cryptography.fernet import Fernet

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))


def _derive_key(seed: str) -> bytes:
    """Derive a deterministic key from provided seed."""
    digest = hashlib.sha256(seed.encode("utf-8", errors="ignore")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_payload(payload: Dict, seed: str) -> str:
    """Encrypt a dict payload using the provided seed."""
    key = _derive_key(seed)
    cipher = Fernet(key)
    token = cipher.encrypt(json.dumps(payload, sort_keys=True).encode("utf-8"))
    return token.decode("utf-8")


def decrypt_payload(token: str, seed: str) -> Dict:
    """Decrypt payload using the provided seed."""
    key = _derive_key(seed)
    cipher = Fernet(key)
    plaintext = cipher.decrypt(token.encode("utf-8"))
    return json.loads(plaintext.decode("utf-8"))
