#!/usr/bin/env python
"""
Quick demo of the new mapping features.
Shows how Manual Mapper and Edit All Mappings work together.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.flow_volume_loader import get_flow_volume_loader

print("=" * 70)
print("EXCEL MAPPING MANAGEMENT - FEATURE DEMONSTRATION")
print("=" * 70)

# Load diagram
diagram_file = Path("data/diagrams/ug2_north_decline.json")
with open(diagram_file) as f:
    diagram = json.load(f)

# Get Excel columns
loader = get_flow_volume_loader()
area_sheets = {
    'Flows_UG2N', 'Flows_MERN', 'Flows_MERS', 'Flows_MERP',
    'Flows_UG2S', 'Flows_UG2P', 'Flows_OLDTSF', 'Flows_STOCKPILE'
}

sheet_columns = {}
for sheet in area_sheets:
    df = loader._load_sheet(sheet)
    if df is not None and not df.empty:
        cols = [str(c).strip() for c in df.columns if str(c).strip() not in {'Date', 'Year', 'Month'}]
        sheet_columns[sheet] = cols
    else:
        sheet_columns[sheet] = []

# Analyze all flows
edges = diagram.get('edges', [])
manual_mapper_list = []
edit_all_list = []
valid_list = []

for idx, edge in enumerate(edges):
    mapping = edge.get('excel_mapping', {}) or {}
    sheet = mapping.get('sheet', '')
    column = mapping.get('column', '')
    enabled = mapping.get('enabled', False)
    
    flow_id = f"{edge.get('from', '?')} → {edge.get('to', '?')}"
    
    # Categorize
    if not sheet or not column or not enabled:
        manual_mapper_list.append((idx, flow_id, sheet, column, "unmapped"))
    else:
        cols = sheet_columns.get(sheet, [])
        if column not in cols:
            manual_mapper_list.append((idx, flow_id, sheet, column, "invalid"))
        else:
            valid_list.append((idx, flow_id, sheet, column))

print("\n📊 MAPPING STATUS OVERVIEW")
print("-" * 70)
print(f"✅ Valid mappings (correct Excel column):        {len(valid_list):3d}")
print(f"⚠️  Needs attention (invalid or missing):         {len(manual_mapper_list):3d}")
print(f"   - Unmapped (no sheet/column):                 {sum(1 for x in manual_mapper_list if x[4]=='unmapped'):3d}")
print(f"   - Invalid (column not in Excel):              {sum(1 for x in manual_mapper_list if x[4]=='invalid'):3d}")
print(f"📋 TOTAL FLOWS:                                   {len(edges):3d}")

print("\n" + "=" * 70)
print("FEATURE 1: [MANUAL MAPPER]")
print("=" * 70)
print(f"🎯 Purpose: Fix flows with invalid/missing Excel mappings")
print(f"📈 Flows to fix: {len(manual_mapper_list)}")
print(f"\n✨ How it works:")
print(f"   1. Shows one flow at a time")
print(f"   2. Choose Sheet from dropdown")
print(f"   3. Choose Column from sheet")
print(f"   4. Preview mapping before saving")
print(f"   5. Optionally save as alias for future auto-maps")
print(f"\n📌 Flows that need fixing:")
for idx, (idx_val, flow_id, sheet, col, status) in enumerate(manual_mapper_list[:5]):
    print(f"   {idx+1}. [{status:7s}] {flow_id}")
    print(f"      Current: {sheet}.{col}")
if len(manual_mapper_list) > 5:
    print(f"   ... and {len(manual_mapper_list) - 5} more")

print("\n" + "=" * 70)
print("FEATURE 2: [EDIT ALL MAPPINGS]")
print("=" * 70)
print(f"🎯 Purpose: Review and fix ALL 152 flows at once")
print(f"📈 Total flows shown: {len(edges)}")
print(f"\n✨ How it works:")
print(f"   1. See all flows in searchable table")
print(f"   2. ✅ = valid, ⚠️ = needs fixing")
print(f"   3. Search by flow name or column name")
print(f"   4. Click any flow to edit its mapping")
print(f"   5. Changes saved immediately")
print(f"\n📌 Quick stats from table view:")
print(f"   Valid flows (✅):   {len(valid_list)}/152")
print(f"   Invalid flows (⚠️): {len(manual_mapper_list)}/152")
print(f"\n📌 Example flows in table:")
for idx, (idx_val, flow_id, sheet, col) in enumerate(valid_list[:3]):
    print(f"   ✅ {flow_id}")
    print(f"      → {sheet}: {col}")
for idx, (idx_val, flow_id, sheet, col, status) in enumerate(manual_mapper_list[:2]):
    print(f"   ⚠️  {flow_id}")
    print(f"      → {sheet}: {col} [INVALID]")

print("\n" + "=" * 70)
print("WORKFLOW COMPARISON")
print("=" * 70)
print(f"""
SCENARIO 1: Auto-map got some mappings wrong
→ Use [Edit All Mappings]:
   1. Search for the problematic flow
   2. Click it to edit
   3. Select correct column
   4. Done! (saves immediately)

SCENARIO 2: Want to fix all broken mappings
→ Use [Manual Mapper]:
   1. Shows only the {len(manual_mapper_list)} broken flows
   2. Step-by-step fixing with preview
   3. Optionally save as alias
   4. Auto-map learns for next time

SCENARIO 3: Need to verify specific mappings
→ Use [Edit All Mappings]:
   1. Search by flow name: "sewage", "borehole", etc
   2. See current mapping
   3. Edit if needed
   4. All in one table view

SCENARIO 4: Want auto-map to be smarter
→ When fixing mappings:
   1. Check "Save as alias" when using Manual Mapper
   2. Auto-map will remember for future runs
   3. Aliases stored in data/column_aliases.json
""")

print("=" * 70)
print("✅ READY TO USE!")
print("=" * 70)
print("""
Launch the app:
    python src/main.py

Then:
    1. Open Flow Diagram Dashboard
    2. Click [🔗 Edit Mappings]
    3. Choose [Manual Mapper] or [Edit All Mappings]
    4. Fix your mappings!

Both features work together to give you complete control over Excel mappings.
""")
