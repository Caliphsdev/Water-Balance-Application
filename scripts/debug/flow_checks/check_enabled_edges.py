import json
from pathlib import Path

# Load the diagram
diagram_file = Path('data/diagrams/ug2_north_decline.json')
with open(diagram_file) as f:
    data = json.load(f)

edges = data.get('edges', [])

# Find edges that have ENABLED=TRUE and are loading data
enabled_edges = [e for e in edges if e.get('excel_mapping', {}).get('enabled')]

print(f"Total edges with enabled=True: {len(enabled_edges)}\n")

# Group by sheet
by_sheet = {}
for edge in enabled_edges:
    sheet = edge.get('excel_mapping', {}).get('sheet', 'Unknown')
    if sheet not in by_sheet:
        by_sheet[sheet] = []
    by_sheet[sheet].append(edge)

for sheet, edges_list in by_sheet.items():
    print(f"\n{sheet}: {len(edges_list)} edges")
    for edge in edges_list[:3]:  # Show first 3
        print(f"  - {edge.get('from')} → {edge.get('to')}")
        print(f"    Column: {edge.get('excel_mapping', {}).get('column')}")
