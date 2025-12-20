import json
from pathlib import Path

d = json.loads(Path('data/diagrams/ug2_north_decline.json').read_text())
edges = d.get('edges', [])
unmapped = [e for e in edges if not e.get('excel_mapping', {}).get('sheet')]

print(f'Total edges: {len(edges)}')
print(f'Unmapped (no sheet): {len(unmapped)}')

if unmapped:
    print(f'\nSample unmapped edge:')
    print(json.dumps(unmapped[0], indent=2))
    
print(f'\nEdges with mapping:')
mapped = [e for e in edges if e.get('excel_mapping', {}).get('sheet')]
print(f'Mapped: {len(mapped)}')
print(f'Sample mapped:')
print(json.dumps(mapped[0], indent=2))
