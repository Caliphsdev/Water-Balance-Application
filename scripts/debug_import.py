import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from licensing.license_manager import LicenseManager
    print("SUCCESS: Imported LicenseManager")
except Exception as e:
    import traceback
    print(f"FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
