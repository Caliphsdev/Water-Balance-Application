import json

print("=" * 70)
print("FIXING MERS AND MERPLANT AREA MAPPINGS")
print("=" * 70)

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

fixed = 0

# Fix MERS - flows that originate from MERS should use Flows_MERS
for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # If flow starts in MERS area, should load from Flows_MERS
    if ('mers' in from_node or 'mdcd' in from_node) and 'merplant' not in from_node and 'ug2plant' not in from_node:
        # Exclude inter-area flows
        if not any(x in to_node for x in ['ug2s', 'ug2plant', 'merplant', 'oldtsf', 'stockpile']):
            edge['excel_mapping'] = {
                'enabled': True,
                'sheet': 'Flows_MERS',
                'column': edge.get('excel_mapping', {}).get('column', '')
            }
            fixed += 1

print(f"✅ Fixed {fixed} MERS flows")

# Fix MERPLANT - flows that originate from MERPLANT should use Flows_MERPLANT
fixed_merplant = 0
for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # If flow starts in MERPLANT area, should load from Flows_MERPLANT
    if 'merplant' in from_node:
        # Even if it goes to other areas, it originates in MERPLANT
        edge['excel_mapping'] = {
            'enabled': True,
            'sheet': 'Flows_MERPLANT',
            'column': edge.get('excel_mapping', {}).get('column', '')
        }
        fixed_merplant += 1

print(f"✅ Fixed {fixed_merplant} MERPLANT flows")

# Save
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"\n✅ Total fixed: {fixed + fixed_merplant} flows")
print("✅ MERS and MERPLANT now load from correct sheets")
