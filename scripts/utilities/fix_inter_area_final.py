import json

# Load master diagram
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

area_map = {
    'mern': 'Flows_Merensky North',
    'mers': 'Flows_MERS',
    'merplant': 'Flows_MERPLANT',
    'ug2n': 'Flows_UG2N',
    'ug2s': 'Flows_UG2S',
    'ug2plant': 'Flows_UG2PLANT',
    'oldtsf': 'Flows_OLDTSF',
    'stockpile': 'Flows_STOCKPILE'
}

updated = 0

for edge in edges:
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # Identify source area from "from_node"
    source_area = None
    for area in area_map.keys():
        if area in from_node:
            source_area = area
            break
    
    # Identify destination area from "to_node"
    dest_area = None
    for area in area_map.keys():
        if area in to_node:
            dest_area = area
            break
    
    # If inter-area flow with wrong sheet mapping
    if source_area and dest_area and source_area != dest_area:
        mapping = edge.get('excel_mapping', {})
        current_sheet = mapping.get('sheet', '')
        
        # Check if it's mapped to destination sheet (wrong)
        if current_sheet == area_map[dest_area]:
            # Change to source sheet (correct)
            edge['excel_mapping']['sheet'] = area_map[source_area]
            updated += 1
            print(f"✅ Fixed: {from_node[:20]:20} → {to_node[:20]:20}")
            print(f"   Changed: {current_sheet} → {area_map[source_area]}")

# Save
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"\n{'='*70}")
print(f"Fixed {updated} inter-area flow mappings")
print(f"{'='*70}")
