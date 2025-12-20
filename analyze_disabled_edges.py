"""
Analyze all disabled edges and categorize them by:
1. Which sheet they belong to
2. What their source→target flow is
3. Whether similar columns exist in Excel
"""

import json
import sys
sys.path.insert(0, "src")

from utils.flow_volume_loader import get_flow_volume_loader

# Load diagram
with open("data/diagrams/ug2_north_decline.json", "r", encoding="utf-8") as f:
    diagram = json.load(f)

# Get all disabled edges
disabled_edges = []
for edge in diagram["edges"]:
    mapping = edge.get("excel_mapping", {})
    if not mapping.get("enabled"):
        disabled_edges.append({
            "from": edge.get("from", ""),
            "to": edge.get("to", ""),
            "sheet": mapping.get("sheet", ""),
            "column": mapping.get("column", ""),
            "edge": edge
        })

print(f"Found {len(disabled_edges)} disabled edges\n")

# Load all Excel columns by sheet
loader = get_flow_volume_loader()
loader.clear_cache()

excel_columns_by_sheet = {}
for sheet in ["Flows_UG2P", "Flows_MERP", "Flows_MERN", "Flows_UG2N", "Flows_UG2S", "Flows_OLDTSF", "Flows_STOCKPILE"]:
    area_code = sheet.replace("Flows_", "")
    try:
        volumes = loader.get_all_volumes_for_month(area_code, 2025, 12)
        excel_columns_by_sheet[sheet] = set(volumes.keys())
    except:
        excel_columns_by_sheet[sheet] = set()

# Categorize disabled edges
categorized = {
    "can_map": [],  # Has similar existing column
    "needs_column": [],  # Needs new Excel column
    "invalid": []  # Invalid/old format
}

for disabled in disabled_edges:
    from_id = disabled["from"]
    to_id = disabled["to"]
    sheet = disabled["sheet"]
    old_column = disabled["column"]
    
    # Build expected column name
    expected_column = f"{from_id.upper()} → {to_id.upper()}"
    
    # Check if it's in Excel
    excel_cols = excel_columns_by_sheet.get(sheet, set())
    
    if expected_column in excel_cols:
        categorized["can_map"].append({
            **disabled,
            "expected_column": expected_column,
            "reason": "Exact match in Excel"
        })
    elif old_column in ["", "OLDTSF Water Balance Template", "UG2S Water Balance Template", 
                        "MERS Water Balance Template", "STOCKPILE Water Balance Template",
                        "UG2N Water Balance Template", "UG2P Water Balance Template",
                        "MERP Water Balance Template", "MERN Water Balance Template"]:
        # Check if expected column exists
        if expected_column in excel_cols:
            categorized["can_map"].append({
                **disabled,
                "expected_column": expected_column,
                "reason": "Sheet title removed, column exists"
            })
        else:
            categorized["needs_column"].append({
                **disabled,
                "expected_column": expected_column,
                "reason": "Sheet title, needs column"
            })
    elif "__TO__" in old_column or "_TO_" in old_column:
        categorized["invalid"].append({
            **disabled,
            "expected_column": expected_column,
            "reason": "Old format"
        })
    else:
        # Check for similar columns
        similar = [col for col in excel_cols if from_id.upper() in col and to_id.upper() in col]
        if similar:
            categorized["can_map"].append({
                **disabled,
                "expected_column": similar[0],
                "reason": f"Similar column: {similar[0]}"
            })
        else:
            categorized["needs_column"].append({
                **disabled,
                "expected_column": expected_column,
                "reason": "No similar column found"
            })

# Print summary
print("="*80)
print("ANALYSIS SUMMARY")
print("="*80)
print(f"\n✅ Can map to existing columns: {len(categorized['can_map'])}")
print(f"➕ Need new Excel columns: {len(categorized['needs_column'])}")
print(f"❌ Invalid/old format: {len(categorized['invalid'])}")

# Print details
print("\n" + "="*80)
print("✅ CAN MAP TO EXISTING COLUMNS")
print("="*80)
for item in categorized["can_map"][:20]:
    print(f"\n{item['sheet']}")
    print(f"  Edge: {item['from']} → {item['to']}")
    print(f"  Map to: {item['expected_column']}")
    print(f"  Reason: {item['reason']}")
if len(categorized["can_map"]) > 20:
    print(f"\n  ... and {len(categorized['can_map']) - 20} more")

print("\n" + "="*80)
print("➕ NEED NEW EXCEL COLUMNS")
print("="*80)
for item in categorized["needs_column"][:20]:
    print(f"\n{item['sheet']}")
    print(f"  Edge: {item['from']} → {item['to']}")
    print(f"  Add column: {item['expected_column']}")
    print(f"  Reason: {item['reason']}")
if len(categorized["needs_column"]) > 20:
    print(f"\n  ... and {len(categorized['needs_column']) - 20} more")

print("\n" + "="*80)
print("❌ INVALID/OLD FORMAT")
print("="*80)
for item in categorized["invalid"][:10]:
    print(f"\n{item['sheet']}")
    print(f"  Edge: {item['from']} → {item['to']}")
    print(f"  Old column: {item['column']}")
    print(f"  Should be: {item['expected_column']}")
if len(categorized["invalid"]) > 10:
    print(f"\n  ... and {len(categorized['invalid']) - 10} more")

# Save categorization for the next script
with open("disabled_edges_categorized.json", "w", encoding="utf-8") as f:
    json.dump(categorized, f, indent=2, ensure_ascii=False)

print("\n" + "="*80)
print(f"💾 Saved categorization to disabled_edges_categorized.json")
print("="*80)
