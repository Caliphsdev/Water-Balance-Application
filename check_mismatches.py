import json
import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

# Load diagram
with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

# Get all enabled mappings
enabled_mappings = {}
for edge in diagram["edges"]:
    mapping = edge.get("excel_mapping", {})
    if mapping.get("enabled"):
        sheet = mapping.get("sheet")
        column = mapping.get("column")
        if sheet and column:
            if sheet not in enabled_mappings:
                enabled_mappings[sheet] = []
            enabled_mappings[sheet].append(column)

# Load volumes for all sheets
loader = get_flow_volume_loader()
loader.clear_cache()

mismatches = []

for sheet in enabled_mappings.keys():
    area_code = sheet.replace("Flows_", "")
    volumes = loader.get_all_volumes_for_month(area_code, 2025, 12)
    excel_columns = set(volumes.keys())
    
    for mapping_column in enabled_mappings[sheet]:
        if mapping_column not in excel_columns:
            mismatches.append({
                "sheet": sheet,
                "json_column": mapping_column,
                "excel_columns": [c for c in excel_columns if any(word in c for word in mapping_column.split())]
            })

print(f"Found {len(mismatches)} mismatches between JSON mappings and Excel columns:\n")
for i, mismatch in enumerate(mismatches, 1):
    print(f"{i}. Sheet: {mismatch['sheet']}")
    print(f"   JSON has: {mismatch['json_column']}")
    if mismatch['excel_columns']:
        print(f"   Excel similar: {mismatch['excel_columns']}")
    else:
        print(f"   Excel has no similar columns")
    print()
