import json
from pathlib import Path

diagram_file = Path('data/diagrams/ug2_north_decline.json')
with open(diagram_file) as f:
    data = json.load(f)

edges = data.get('edges', [])
merensky_edges = [e for e in edges if 'merensky' in e.get('from', '').lower()]

print('Merensky edges with Excel mappings:')
for edge in merensky_edges:
    mapping = edge.get('excel_mapping', {})
    if mapping.get('enabled'):
        print(f"✓ {edge.get('from')} → {edge.get('to')}")
        print(f"  Sheet: {mapping.get('sheet')}")
        print(f"  Column: {mapping.get('column')}")
        print()
