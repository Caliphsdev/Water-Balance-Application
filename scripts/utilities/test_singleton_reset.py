"""
Test script to verify singleton reset functionality for flow volume loader.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.flow_volume_loader import get_flow_volume_loader, reset_flow_volume_loader
from utils.config_manager import config

print("=" * 60)
print("Testing Flow Volume Loader Singleton Reset")
print("=" * 60)

# Get initial loader instance
print("\n1️⃣ Getting initial loader instance...")
loader1 = get_flow_volume_loader()
print(f"   Loader instance ID: {id(loader1)}")
print(f"   Excel path: {loader1.excel_path}")

# Get it again (should be same instance)
print("\n2️⃣ Getting loader again (should be same instance)...")
loader2 = get_flow_volume_loader()
print(f"   Loader instance ID: {id(loader2)}")
print(f"   Same instance? {loader1 is loader2}")
print(f"   Excel path: {loader2.excel_path}")

# Simulate Settings path change
print("\n3️⃣ Simulating Settings path change...")
new_path = "test_templates\\Water_Balance_TimeSeries_Template.xlsx"
print(f"   Setting both paths to: {new_path}")
config.set('data_sources.template_excel_path', new_path)
config.set('data_sources.timeseries_excel_path', new_path)

# WITHOUT reset - get loader (should still be old instance)
print("\n4️⃣ Getting loader WITHOUT reset (should be old instance)...")
loader3 = get_flow_volume_loader()
print(f"   Loader instance ID: {id(loader3)}")
print(f"   Same as loader1? {loader1 is loader3}")
print(f"   Excel path: {loader3.excel_path}")
print(f"   ⚠️ Path unchanged because singleton not reset")

# NOW reset the singleton
print("\n5️⃣ Resetting singleton...")
reset_flow_volume_loader()
print("   ✅ Singleton reset called")

# Get loader again (should be NEW instance with new path)
print("\n6️⃣ Getting loader AFTER reset (should be new instance)...")
loader4 = get_flow_volume_loader()
print(f"   Loader instance ID: {id(loader4)}")
print(f"   Same as loader1? {loader1 is loader4}")
print(f"   Excel path: {loader4.excel_path}")

# Verify path changed
print("\n" + "=" * 60)
if loader1 is not loader4:
    print("✅ SUCCESS: Singleton was reset (different instance)")
else:
    print("❌ FAIL: Singleton NOT reset (same instance)")

if str(loader4.excel_path).endswith("Template.xlsx"):
    print("✅ SUCCESS: Path changed to template")
else:
    print("❌ FAIL: Path still pointing to old file")
print("=" * 60)
