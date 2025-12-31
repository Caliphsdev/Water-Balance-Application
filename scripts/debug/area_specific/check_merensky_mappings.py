import json
from pathlib import Path

diagram_file = Path('data/diagrams/ug2_north_decline.json')
with open(diagram_file) as f:
    data = json.load(f)

edges = data.get('edges', [])
merensky_edges = [e for e in edges if 'merensky' in e.get('from', '').lower() or 'merensky' in e.get('to', '').lower()]

issues = []
for edge in merensky_edges:
    mapping = edge.get('excel_mapping', {})
    if mapping.get('enabled'):
        sheet = mapping.get('sheet', '')
        col = mapping.get('column', '')
        if 'UG2' in sheet:
            issues.append(f"{edge.get('from')} -> {edge.get('to')} maps to {sheet}/{col}")

if issues:
    print('Found cross-area mapping issues:')
    for issue in issues:
        print(f'  ❌ {issue}')
else:
    print('No cross-area mapping issues found')
