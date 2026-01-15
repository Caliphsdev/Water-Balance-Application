"""Hardware fingerprint utilities for license binding."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))


def _run_command(command: List[str]) -> str:
    """Run a subprocess command and return stripped output."""
    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL, shell=False)
        return output.decode(errors="ignore").strip()
    except Exception:
        return ""


def _get_mac_address() -> str:
    """Return MAC address; fallback to uuid node if unavailable."""
    try:
        mac = platform.node()  # name as weak fallback for stability
        import uuid

        node = uuid.getnode()
        if (node >> 40) % 2:
            return mac or ""
        return f"{node:012x}"
    except Exception:
        return ""


def _get_cpu_id() -> str:
    """Return CPU identifier using platform-specific commands."""
    system = platform.system().lower()
    if system == "windows":
        return _run_command(["wmic", "cpu", "get", "ProcessorId", "/value"]).split("=")[-1]
    if system == "linux":
        return _run_command(["cat", "/proc/cpuinfo"]).split("Serial")[-1].strip()
    if system == "darwin":
        return _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
    return ""


def _get_board_serial() -> str:
    """Return baseboard/UUID identifier."""
    system = platform.system().lower()
    if system == "windows":
        uuid_value = _run_command(["wmic", "csproduct", "get", "uuid", "/value"]).split("=")[-1]
        if uuid_value:
            return uuid_value
        return _run_command(["wmic", "baseboard", "get", "SerialNumber", "/value"]).split("=")[-1]
    if system == "linux":
        paths = [
            "/sys/class/dmi/id/board_serial",
            "/sys/class/dmi/id/product_uuid",
        ]
        for p in paths:
            try:
                if os.path.exists(p):
                    return Path(p).read_text().strip()
            except Exception:
                continue
    if system == "darwin":
        return _run_command(["ioreg", "-l"]).split("IOPlatformUUID")[-1].strip().strip("\" ")
    return ""


def collect_components() -> Dict[str, str]:
    """Collect raw hardware component identifiers."""
    fallback = platform.node() or os.environ.get("COMPUTERNAME", "") or "fallback-node"
    return {
        "mac": _get_mac_address() or fallback,
        "cpu": _get_cpu_id() or fallback,
        "board": _get_board_serial() or fallback,
    }


def fingerprint_components(components: Dict[str, str]) -> Dict[str, str]:
    """Hash hardware components for storage without exposing raw values."""
    hashed = {}
    for key, value in components.items():
        digest = hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest() if value else ""
        hashed[key] = digest
    return hashed


def fuzzy_match(stored: Dict[str, str], current: Dict[str, str], threshold: int = 2) -> Tuple[bool, int]:
    """Return whether current hardware matches stored hashes under fuzzy threshold."""
    match_count = 0
    for key in ("mac", "cpu", "board"):
        if stored.get(key) and current.get(key) and stored[key] == current[key]:
            match_count += 1
    return match_count >= threshold, match_count


def serialize_components(hashed_components: Dict[str, str]) -> str:
    """Serialize hashed components to JSON."""
    return json.dumps(hashed_components, sort_keys=True)


def deserialize_components(serialized: str) -> Dict[str, str]:
    """Deserialize hashed components JSON."""
    try:
        return json.loads(serialized or "{}")
    except Exception:
        return {}


def current_hardware_snapshot() -> Dict[str, str]:
    """Convenience helper returning hashed snapshot."""
    return fingerprint_components(collect_components())


def describe_mismatch(stored: Dict[str, str], current: Dict[str, str]) -> str:
    """Produce human-friendly mismatch explanation."""
    messages: List[str] = []
    for key, label in [("mac", "Network adapter"), ("cpu", "CPU"), ("board", "Motherboard")]:
        if stored.get(key) and current.get(key) and stored[key] != current[key]:
            messages.append(f"{label} changed")
    return ", ".join(messages) if messages else "No mismatch details available"
