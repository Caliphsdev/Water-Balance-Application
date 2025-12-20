"""
Final verification - test that all 138 edges can load data from Excel.
"""

import json
import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

# Load diagram
with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

# Load all Excel data
loader = get_flow_volume_loader()
loader.clear_cache()

all_volumes = {}
for sheet in ["Flows_UG2P", "Flows_MERP", "Flows_MERN", "Flows_MERS", "Flows_UG2N", "Flows_UG2S", "Flows_OLDTSF", "Flows_STOCKPILE"]:
    area_code = sheet.replace("Flows_", "")
    try:
        volumes = loader.get_all_volumes_for_month(area_code, 2025, 12)
        all_volumes[sheet] = volumes
    except:
        all_volumes[sheet] = {}

print("="*80)
print("VERIFICATION RESULTS")
print("="*80)

# Test each edge
enabled_count = 0
matched_count = 0
missing_count = 0
missing_edges = []

for edge in diagram["edges"]:
    mapping = edge.get("excel_mapping", {})
    
    if mapping.get("enabled"):
        enabled_count += 1
        
        sheet = mapping.get("sheet", "")
        column = mapping.get("column", "")
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        
        # Check if column exists in Excel
        if sheet in all_volumes and column in all_volumes[sheet]:
            matched_count += 1
        else:
            missing_count += 1
            missing_edges.append({
                "from": from_id,
                "to": to_id,
                "sheet": sheet,
                "column": column
            })

print(f"\n[#] Total edges: {len(diagram['edges'])}")
print(f"[OK] Enabled edges: {enabled_count}")
print(f"[OK] Matched to Excel: {matched_count}")
print(f"[X] Missing in Excel: {missing_count}")

if missing_count > 0:
    print(f"\n[WARNING] {missing_count} edges are enabled but missing Excel columns:\n")
    for item in missing_edges[:10]:
        col_display = item["column"].replace(chr(8594), "->")
        print(f"  {item['from']} -> {item['to']}")
        print(f"    Sheet: {item['sheet']}")
        print(f"    Column: {col_display}\n")
    
    if len(missing_edges) > 10:
        print(f"  ... and {len(missing_edges) - 10} more")
else:
    print(f"\n[SUCCESS] All {enabled_count} enabled edges have matching Excel columns!")
    print(f"[SUCCESS] All {enabled_count} flow labels will display data from Excel!")

print("\n" + "="*80)
print("SUMMARY BY SHEET")
print("="*80)

# Count by sheet
sheet_summary = {}
for edge in diagram["edges"]:
    mapping = edge.get("excel_mapping", {})
    if mapping.get("enabled"):
        sheet = mapping.get("sheet", "Unknown")
        if sheet not in sheet_summary:
            sheet_summary[sheet] = {"total": 0, "matched": 0}
        sheet_summary[sheet]["total"] += 1
        
        column = mapping.get("column", "")
        if sheet in all_volumes and column in all_volumes[sheet]:
            sheet_summary[sheet]["matched"] += 1

for sheet in sorted(sheet_summary.keys()):
    stats = sheet_summary[sheet]
    status = "[OK]" if stats["matched"] == stats["total"] else "[!]"
    print(f"{status} {sheet}: {stats['matched']}/{stats['total']} matched")

print("\n" + "="*80)
