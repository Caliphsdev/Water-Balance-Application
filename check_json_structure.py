import json
with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)
print(f"Type of 'nodes': {type(diagram.get('nodes'))}")
print(f"First 3 nodes: {list(diagram.get('nodes', [])[:3]) if isinstance(diagram.get('nodes'), list) else list(diagram.get('nodes', {}).items())[:3]}")
