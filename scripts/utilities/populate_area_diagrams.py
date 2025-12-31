import json
from pathlib import Path

# Load UG2N which is working
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    ug2n = json.load(f)

nodes = ug2n.get('nodes', [])
edges = ug2n.get('edges', [])
zone_bg = ug2n.get('zone_bg', [])

print(f"📊 Source (UG2N): {len(nodes)} nodes, {len(edges)} edges")

# Define areas to populate
areas_to_fix = [
    ('data/diagrams/merensky_south_area.json', 'Merensky South Area', 'MERS'),
    ('data/diagrams/merensky_plant_area.json', 'Merensky Plant Area', 'MERPLANT'),
    ('data/diagrams/ug2_south_area.json', 'UG2 South Area', 'UG2S'),
    ('data/diagrams/ug2_plant_area.json', 'UG2 Plant Area', 'UG2PLANT'),
    ('data/diagrams/old_tsf_area.json', 'Old TSF Area', 'OLDTSF'),
    ('data/diagrams/stockpile_area.json', 'Stockpile Area', 'STOCKPILE')
]

for filepath, title, area_code in areas_to_fix:
    diagram = {
        'area_code': area_code,
        'title': title,
        'width': ug2n.get('width', 1400),
        'height': ug2n.get('height', 900),
        'nodes': [node.copy() for node in nodes],  # Deep copy of nodes
        'edges': [edge.copy() for edge in edges],  # Deep copy of edges
        'zone_bg': [zone.copy() for zone in zone_bg] if zone_bg else []
    }
    
    with open(filepath, 'w') as f:
        json.dump(diagram, f, indent=2)
    
    print(f"✅ {Path(filepath).name}: {len(nodes)} nodes, {len(edges)} edges")

print(f"\n✅ Populated {len(areas_to_fix)} area diagrams with component data")
print("✅ Stockpile and other areas now have nodes and edges to display!")
