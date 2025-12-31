import json

# Load and check
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    data = json.load(f)

edges = data['edges']

# Find the flow
matching = [e for e in edges if e.get('from') == 'ug2plant_ug2pcd1' and e.get('to') == 'ug2plant_ug2p_plant']

print(f"✅ Found {len(matching)} matching flow(s)\n")

for edge in matching:
    print(f"Flow: {edge.get('from')} → {edge.get('to')}")
    print(f"Volume: {edge.get('volume')}")
    print(f"Flow Type: {edge.get('flow_type')}")
    
    mapping = edge.get('excel_mapping', {})
    if mapping:
        print(f"\n✅ Excel Mapping EXISTS:")
        print(f"   Enabled: {mapping.get('enabled')}")
        print(f"   Sheet: {mapping.get('sheet')}")
        print(f"   Column: {mapping.get('column')}")
    else:
        print(f"\n❌ NO Excel Mapping found!")
        print(f"   You need to add excel_mapping to this flow")
