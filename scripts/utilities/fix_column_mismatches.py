"""
Fix column name mismatches between JSON mappings and Excel columns.
This script updates the JSON diagram to match the actual Excel column names.
"""

import json
import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

# Known mismatches (found through analysis)
FIXES = {
    "Flows_MERP": {
        "MERPLANT_MPSWD12 → MERPLANT_MPSWD12_SPILL": "MERPLANT_MPSWD12 → MERPLANT_MPSWD12_DUST"
    },
    "Flows_UG2N": {
        "RAINFALL_INFLOW → NDCD": "RAINFALL → NDCD",
        "NDCD → DUST_SUPPRESSION": None,  # Not in Excel, disable
        "SOFTENING → TRP_CLINIC": None,   # Not in Excel, disable
        "TRP_CLINIC → SEPTIC": None,      # Not in Excel, disable
        "TRP_CLINIC → CONSUMPTION": None  # Not in Excel, disable
    },
    "Flows_STOCKPILE": {
        "SPCD1 → JUNCTION_129_1140_1242": None  # Not in Excel, disable
    }
}

def main():
    # Load the diagram
    diagram_path = "data/diagrams/ug2_north_decline.json"
    with open(diagram_path, "r", encoding="utf-8") as f:
        diagram = json.load(f)
    
    fixed_count = 0
    disabled_count = 0
    
    # Apply fixes
    for edge in diagram["edges"]:
        mapping = edge.get("excel_mapping", {})
        if not mapping.get("enabled"):
            continue
        
        sheet = mapping.get("sheet")
        column = mapping.get("column")
        
        if sheet in FIXES and column in FIXES[sheet]:
            new_column = FIXES[sheet][column]
            
            if new_column is None:
                # Disable this mapping
                mapping["enabled"] = False
                disabled_count += 1
                print(f"❌ Disabled: {sheet} / {column}")
            else:
                # Update column name
                mapping["column"] = new_column
                fixed_count += 1
                print(f"✅ Fixed: {sheet} / {column} → {new_column}")
    
    # Save the updated diagram
    with open(diagram_path, "w", encoding="utf-8") as f:
        json.dump(diagram, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fixed {fixed_count} column names")
    print(f"❌ Disabled {disabled_count} invalid mappings")
    print(f"💾 Saved to {diagram_path}")
    
    # Verify the fixes
    print("\n🔍 Verifying fixes...")
    loader = get_flow_volume_loader()
    loader.clear_cache()
    
    remaining_mismatches = 0
    for sheet in FIXES.keys():
        area_code = sheet.replace("Flows_", "")
        volumes = loader.get_all_volumes_for_month(area_code, 2025, 12)
        excel_columns = set(volumes.keys())
        
        for edge in diagram["edges"]:
            mapping = edge.get("excel_mapping", {})
            if mapping.get("enabled") and mapping.get("sheet") == sheet:
                column = mapping.get("column")
                if column not in excel_columns:
                    remaining_mismatches += 1
                    print(f"⚠️  Still missing: {sheet} / {column}")
    
    if remaining_mismatches == 0:
        print("✅ All enabled mappings now match Excel columns!")
    else:
        print(f"⚠️  {remaining_mismatches} mismatches remain")

if __name__ == "__main__":
    main()
