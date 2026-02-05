"""
Hardware ID (HWID) Generation Module

Generates a unique, stable identifier for the machine based on hardware characteristics.
Used for license binding to prevent key sharing.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import hashlib
import platform
import uuid
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# (HWID GENERATION)

def get_machine_uuid() -> Optional[str]:
    """
    Get machine UUID from system.
    
    On Windows, uses WMIC to get the motherboard UUID.
    Falls back to MAC address if unavailable.
    
    Returns:
        Machine UUID string or None if unavailable.
    """
    if platform.system() == "Windows":
        try:
            # Get motherboard UUID via WMIC
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                machine_uuid = lines[1].strip()
                if machine_uuid and machine_uuid != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
                    return machine_uuid
        except Exception as e:
            logger.debug(f"Could not get machine UUID via WMIC: {e}")
    
    return None


def get_disk_serial() -> Optional[str]:
    """
    Get primary disk serial number.
    
    On Windows, uses WMIC to get the disk serial.
    
    Returns:
        Disk serial string or None if unavailable.
    """
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "SerialNumber"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                serial = lines[1].strip()
                if serial:
                    return serial
        except Exception as e:
            logger.debug(f"Could not get disk serial via WMIC: {e}")
    
    return None


def generate_hwid() -> str:
    """
    Generate a unique hardware identifier for this machine.
    
    Combines multiple hardware characteristics to create a stable,
    unique fingerprint that survives OS reinstalls but changes
    with major hardware changes.
    
    Components used (in order of reliability):
    1. Machine UUID (motherboard)
    2. Disk serial number
    3. MAC address (network adapter)
    4. Computer name + OS info (fallback)
    
    Returns:
        32-character hexadecimal HWID string.
    """
    components = []
    
    # Try to get machine UUID (most reliable)
    machine_uuid = get_machine_uuid()
    if machine_uuid:
        components.append(f"uuid:{machine_uuid}")
    
    # Try to get disk serial
    disk_serial = get_disk_serial()
    if disk_serial:
        components.append(f"disk:{disk_serial}")
    
    # MAC address (can change with network adapter)
    mac = str(uuid.getnode())
    components.append(f"mac:{mac}")
    
    # Computer name and architecture (fallback identifiers)
    components.append(f"node:{platform.node()}")
    components.append(f"arch:{platform.machine()}")
    components.append(f"os:{platform.system()}")
    
    # Combine all components
    raw_string = "|".join(components)
    
    # Hash to create consistent 32-char HWID
    hwid = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()[:32]
    
    logger.debug(f"Generated HWID from {len(components)} components")
    
    return hwid


def get_hwid() -> str:
    """
    Get the hardware ID for this machine.
    
    This is the primary function to call from other modules.
    Caches the result after first generation.
    
    Returns:
        32-character hexadecimal HWID string.
    """
    if not hasattr(get_hwid, '_cached_hwid'):
        get_hwid._cached_hwid = generate_hwid()
    return get_hwid._cached_hwid


def get_hwid_display() -> str:
    """
    Get a display-friendly version of the HWID.
    
    Formats as: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
    
    Returns:
        Formatted HWID string for display to users.
    """
    hwid = get_hwid()
    # Split into groups of 4
    groups = [hwid[i:i+4].upper() for i in range(0, len(hwid), 4)]
    return "-".join(groups)


# (MODULE TEST)

if __name__ == "__main__":
    print("Hardware ID Generation Test")
    print("=" * 50)
    print(f"Raw HWID:     {get_hwid()}")
    print(f"Display HWID: {get_hwid_display()}")
    print(f"Platform:     {platform.system()} {platform.release()}")
    print(f"Node:         {platform.node()}")
    print(f"Machine:      {platform.machine()}")
