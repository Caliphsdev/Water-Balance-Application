import json

print("=" * 70)
print("FIXING FINAL INTER-AREA FLOWS")
print("=" * 70)

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# These are inter-area flows that should load from the ORIGINATING area:
# MERS to UG2S flows - should load from Flows_UG2S (because they originate there)
# MERPLANT to OLDTSF flows - should load from Flows_OLDTSF (because they originate there, in MERPLANT but go TO OLDTSF)

fixed = 0

for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # These specific inter-area flows should load from the source area
    
    # UG2S flows that MERS sends to UG2S
    if ('mers' in from_node or 'mdcd' in from_node) and ('ug2s' in to_node or 'ug2s_mdcdg' in to_node):
        edge['excel_mapping'] = {
            'enabled': True,
            'sheet': 'Flows_UG2S',  # They arrive at UG2S, so load from there
            'column': edge.get('excel_mapping', {}).get('column', '')
        }
        fixed += 1
        print(f"✅ {from_node} → {to_node}: Flows_UG2S")
    
    # OLDTSF flows that MERPLANT sends to OLDTSF
    elif 'merplant' in from_node and 'oldtsf' in to_node:
        edge['excel_mapping'] = {
            'enabled': True,
            'sheet': 'Flows_OLDTSF',  # They arrive at OLDTSF, so load from there
            'column': edge.get('excel_mapping', {}).get('column', '')
        }
        fixed += 1
        print(f"✅ {from_node} → {to_node}: Flows_OLDTSF")

# Save
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"\n✅ Fixed {fixed} inter-area flows")
