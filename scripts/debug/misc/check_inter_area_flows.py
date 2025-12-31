import json

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Check UG2N edges that don't match
print("UG2N edges assigned to other sheets:")
for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    sheet = edge.get('excel_mapping', {}).get('sheet')
    
    if ('ug2' in from_node or 'ndcd' in from_node) and ('ug2' in to_node or 'ndcd' in to_node):
        if 'ug2s' not in from_node and 'ug2s' not in to_node and 'ug2plant' not in from_node and 'ug2plant' not in to_node:
            if sheet != 'Flows_UG2N':
                print(f"  {from_node} → {to_node}: {sheet}")

print("\nMERS edges with inter-area flows:")
for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    sheet = edge.get('excel_mapping', {}).get('sheet')
    
    if ('mers' in from_node or 'mdcd' in from_node) and ('ug2' in to_node or 'mern' in to_node):
        print(f"  {from_node} → {to_node}: {sheet}")

print("\nMERPLANT edges with inter-area flows:")
for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    sheet = edge.get('excel_mapping', {}).get('sheet')
    
    if 'merplant' in from_node and ('ug2' in to_node or 'oldtsf' in to_node or 'ndcd' in to_node):
        print(f"  {from_node} → {to_node}: {sheet}")
