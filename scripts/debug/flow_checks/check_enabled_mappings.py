import json

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    data = json.load(f)

edges = data.get('edges', [])
enabled = [e for e in edges if e.get('excel_mapping', {}).get('enabled')]

print(f'Total edges: {len(edges)}')
print(f'Enabled mappings: {len(enabled)}')
print(f'\nFirst 10 enabled mappings:')
for e in enabled[:10]:
    mapping = e.get('excel_mapping', {})
    print(f"  {e.get('from')} → {e.get('to')}")
    print(f"    Sheet: {mapping.get('sheet')}, Column: {mapping.get('column')}")
