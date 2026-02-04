import json

data = json.load(open('data/diagrams/ug2_north_decline.json'))
node_ids = {n['id'] for n in data['nodes']}
print(f"Total nodes: {len(node_ids)}")

# Find edges with missing nodes
missing_edges = []
for i, edge in enumerate(data['edges']):
    from_id = edge.get('from_id') or edge.get('from')
    to_id = edge.get('to_id') or edge.get('to')
    from_exists = from_id in node_ids
    to_exists = to_id in node_ids
    if not from_exists or not to_exists:
        missing_edges.append((from_id, to_id, from_exists, to_exists))

print(f"Missing nodes in edges: {len(missing_edges)}")
for from_id, to_id, from_exists, to_exists in missing_edges[:5]:
    print(f"  {from_id}({from_exists}) -> {to_id}({to_exists})")
