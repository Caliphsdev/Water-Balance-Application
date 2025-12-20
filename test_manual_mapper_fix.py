#!/usr/bin/env python
"""Test the updated manual mapper detection logic."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.flow_volume_loader import get_flow_volume_loader

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

# Updated detection logic (as in fixed manual_mapper)
edges = diagram.get('edges', [])
unmapped = []

for idx, edge in enumerate(edges):
    mapping = edge.get('excel_mapping', {}) or {}
    sheet = mapping.get('sheet', '')
    column = mapping.get('column', '')
    enabled = mapping.get('enabled', False)
    
    # Include if: unmapped (no sheet/column), disabled, OR invalid (column not in sheet)
    if not sheet or not column or not enabled:
        unmapped.append((idx, edge, "unmapped"))
    else:
        cols = sheet_columns.get(sheet, [])
        if column not in cols:
            unmapped.append((idx, edge, "invalid"))

print(f"✓ Manual Mapper Detection Results")
print(f"=" * 60)
print(f"Total edges: {len(edges)}")
print(f"Flows needing attention: {len(unmapped)}")
print(f"\n📋 Breakdown:")
unmapped_count = sum(1 for _, _, s in unmapped if s == "unmapped")
invalid_count = sum(1 for _, _, s in unmapped if s == "invalid")
print(f"  Unmapped (no sheet/column): {unmapped_count}")
print(f"  Invalid (column not in Excel): {invalid_count}")

if unmapped:
    print(f"\n🎯 Flows to fix (first 10):")
    for i, (idx, edge, status) in enumerate(unmapped[:10]):
        from_id = edge.get('from', '?')
        to_id = edge.get('to', '?')
        mapping = edge.get('excel_mapping', {})
        sheet = mapping.get('sheet', '?')
        column = mapping.get('column', '?')
        print(f"  {i+1}. [{status}] {from_id} → {to_id}")
        print(f"     Current: {sheet}.{column}")
        if status == "invalid":
            cols = sheet_columns.get(sheet, [])
            print(f"     Available in {sheet}: {cols[:2]}...")
else:
    print(f"\n✅ All flows have valid Excel mappings!")
