import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

loader = get_flow_volume_loader()
loader.clear_cache()

# Check OLDTSF for the 2 disabled edges
oldtsf_volumes = loader.get_all_volumes_for_month("OLDTSF", 2025, 12)
print("OLDTSF Excel columns containing NEW_TSF and NT_RWD:\n")
for col in sorted(oldtsf_volumes.keys()):
    if "NEW_TSF" in col and "NT_RWD" in col:
        print(f"  {col}")

print("\nOLDTSF Excel columns containing OLD_TSF and TRTD:\n")
for col in sorted(oldtsf_volumes.keys()):
    if "OLD_TSF" in col and "TRTD" in col:
        print(f"  {col}")

# Check STOCKPILE for the disabled edge
stockpile_volumes = loader.get_all_volumes_for_month("STOCKPILE", 2025, 12)
print("\nSTOCKPILE Excel columns containing STOCKPILE_AREA and SPCD1:\n")
for col in sorted(stockpile_volumes.keys()):
    if "STOCKPILE_AREA" in col and "SPCD1" in col:
        print(f"  {col}")
