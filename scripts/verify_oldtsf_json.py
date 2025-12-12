import json

try:
    with open('data/diagrams/ug2_north_decline.json', 'r') as f:
        data = json.load(f)
    
    print("✅ JSON file is valid!")
    print(f"\nCanvas size: {data['width']} x {data['height']}")
    print(f"Total zones: {len(data['zone_bg'])}")
    print(f"Total nodes: {len(data['nodes'])}")
    print(f"Total edges: {len(data['edges'])}")
    
    # Count Old TSF nodes
    oldtsf_nodes = [n for n in data['nodes'] if n['id'].startswith('oldtsf_')]
    print(f"\nOld TSF Area nodes: {len(oldtsf_nodes)}")
    
    print("\nOld TSF Components:")
    for node in oldtsf_nodes:
        print(f"  - {node['id']:30s} | {node['label']:30s} | Type: {node['type']}")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
