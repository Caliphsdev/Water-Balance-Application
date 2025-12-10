import json

with open('data/diagrams/ug2_north_decline.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for edge in data['edges']:
    if edge.get('flow_type') == 'stormwater':
        edge['color'] = '#e74c3c'

with open('data/diagrams/ug2_north_decline.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('? Updated stormwater flowlines to red')
