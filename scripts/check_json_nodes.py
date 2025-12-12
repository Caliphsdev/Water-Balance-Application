import json

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    data = json.load(f)

print(f'Total nodes: {len(data["nodes"])}')
print(f'\nLast 3 nodes:')
for node in data['nodes'][-3:]:
    print(f"  ID: {node['id']}, Label: {node['label']}")
