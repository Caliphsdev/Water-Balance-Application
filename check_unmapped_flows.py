#!/usr/bin/env python
"""Check which flows are unmapped or have invalid Excel mappings."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.flow_volume_loader import get_flow_volume_loader
import pandas as pd

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

print(f"Available sheets in Excel:")
for sheet in sheet_columns:
    cols = sheet_columns[sheet]
    print(f"  {sheet}: {len(cols)} columns")
    if cols:
        print(f"    First 3: {cols[:3]}")

# Check edges
edges = diagram.get('edges', [])
print(f"\nTotal edges: {len(edges)}")

unmapped = []
invalid = []
mapped = []

for idx, edge in enumerate(edges):
    mapping = edge.get('excel_mapping', {}) or {}
    sheet = mapping.get('sheet', '')
    column = mapping.get('column', '')
    enabled = mapping.get('enabled', False)
    
    flow_id = f"{edge.get('from')} → {edge.get('to')}"
    
    # Check if unmapped
    if not sheet or not column:
        unmapped.append((idx, flow_id, sheet, column))
    elif not enabled:
        unmapped.append((idx, flow_id, sheet, column))
    else:
        # Check if column exists in sheet
        cols = sheet_columns.get(sheet, [])
        if column not in cols:
            invalid.append((idx, flow_id, sheet, column))
        else:
            mapped.append((idx, flow_id, sheet, column))

print(f"\n✓ Mapped (valid column exists): {len(mapped)}")
if mapped[:3]:
    for idx, flow_id, sheet, col in mapped[:3]:
        print(f"  {flow_id} → {sheet}: {col}")

print(f"\n✗ Unmapped (no sheet/column): {len(unmapped)}")
if unmapped:
    for idx, flow_id, sheet, column in unmapped[:5]:
        print(f"  {flow_id} → sheet={sheet}, col={column}")

print(f"\n⚠ Invalid (column not in sheet): {len(invalid)}")
if invalid:
    for idx, flow_id, sheet, column in invalid[:5]:
        cols = sheet_columns.get(sheet, [])
        print(f"  {flow_id} → {sheet}.{column}")
        print(f"    Available cols: {cols[:2]}...")
