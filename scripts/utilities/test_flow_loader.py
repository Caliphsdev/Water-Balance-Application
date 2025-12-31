from openpyxl import load_workbook
import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

# Get loader
loader = get_flow_volume_loader()
loader.clear_cache()

# Try to load volumes for December 2025
print("Testing flow volume loading for UG2P, December 2025\n")
volumes = loader.get_all_volumes_for_month("UG2P", 2025, 12)

print(f"Loaded {len(volumes)} volumes")
print("\nFirst 10 volumes:")
for i, (key, value) in enumerate(volumes.items()):
    if i >= 10:
        break
    print(f"  {key}: {value:,.0f} m³")
