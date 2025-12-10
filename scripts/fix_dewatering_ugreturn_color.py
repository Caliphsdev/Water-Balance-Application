import json

# Load the diagram
with open('data/diagrams/ug2_north_decline.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update color for dewatering and ug_return edges
types_to_red = {'dewatering', 'ug_return'}
for edge in data['edges']:
    if edge.get('flow_type') in types_to_red:
        edge['color'] = '#e74c3c'

with open('data/diagrams/ug2_north_decline.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('? Updated dewatering and ug_return flowlines to red')
