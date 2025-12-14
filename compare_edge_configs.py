import json
from pathlib import Path

# Load the diagram
diagram_file = Path('data/diagrams/ug2_north_decline.json')
with open(diagram_file) as f:
    data = json.load(f)

edges = data.get('edges', [])

# Compare UG2 edges vs Merensky edges
ug2_edges = [e for e in edges if 'ug2' in e.get('from', '').lower() or 'north_shaft' in e.get('from', '').lower() or 'north_decline' in e.get('from', '').lower()]
ug2_edges = [e for e in ug2_edges if 'merensky' not in e.get('from', '').lower() and 'merensky' not in e.get('to', '').lower()]

merensky_edges = [e for e in edges if 'merensky' in e.get('from', '').lower() or 'merensky' in e.get('to', '').lower()]

print("="*80)
print("UG2 NORTH EDGES (that work):")
print("="*80)
for i, edge in enumerate(ug2_edges[:5], 1):  # Show first 5
    from_id = edge.get('from', '')
    to_id = edge.get('to', '')
    mapping = edge.get('excel_mapping', {})
    
    print(f"\n{i}. {from_id} → {to_id}")
    print(f"   Enabled: {mapping.get('enabled')}")
    print(f"   Sheet: {mapping.get('sheet')}")
    print(f"   Column: {mapping.get('column')}")

print("\n" + "="*80)
print("MERENSKY EDGES (not displaying):")
print("="*80)
for i, edge in enumerate(merensky_edges[:5], 1):  # Show first 5
    from_id = edge.get('from', '')
    to_id = edge.get('to', '')
    mapping = edge.get('excel_mapping', {})
    
    print(f"\n{i}. {from_id} → {to_id}")
    print(f"   Enabled: {mapping.get('enabled')}")
    print(f"   Sheet: {mapping.get('sheet')}")
    print(f"   Column: {mapping.get('column')}")

print("\n" + "="*80)
print(f"Total UG2 edges with mappings: {sum(1 for e in ug2_edges if e.get('excel_mapping', {}).get('enabled'))}")
print(f"Total Merensky edges with mappings: {sum(1 for e in merensky_edges if e.get('excel_mapping', {}).get('enabled'))}")
