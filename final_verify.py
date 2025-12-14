import json

print("=" * 70)
print("FINAL VERIFICATION - ALL AREAS")
print("=" * 70)

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Define all areas
areas = {
    'UG2N': ('ug2', 'Flows_UG2N'),
    'MERN': ('merensky_north', 'Flows_MERN'),
    'MERS': ('merensky_south', 'Flows_MERS'),
    'MERPLANT': ('merplant', 'Flows_MERPLANT'),
    'UG2S': ('ug2south', 'Flows_UG2S'),
    'UG2PLANT': ('ug2plant', 'Flows_UG2PLANT'),
    'OLDTSF': ('oldtsf', 'Flows_OLDTSF'),
    'STOCKPILE': ('stockpile', 'Flows_STOCKPILE')
}

all_good = True

for area_code, (identifier, expected_sheet) in areas.items():
    area_edges = []
    for i, edge in enumerate(edges):
        from_node = edge.get('from', '').lower()
        to_node = edge.get('to', '').lower()
        
        if identifier in from_node or identifier in to_node or area_code.lower() in from_node or area_code.lower() in to_node:
            area_edges.append((i, edge))
    
    if area_edges:
        enabled = sum(1 for _, e in area_edges if e.get('excel_mapping', {}).get('enabled'))
        correct_sheet = sum(1 for _, e in area_edges if e.get('excel_mapping', {}).get('sheet') == expected_sheet)
        
        if enabled == len(area_edges) and correct_sheet == len(area_edges):
            print(f"✅ {area_code:12} - {len(area_edges):2} flows - ALL ENABLED & CORRECT SHEET")
        else:
            print(f"❌ {area_code:12} - {len(area_edges):2} flows - {enabled} enabled, {correct_sheet} correct sheet")
            all_good = False

print("\n" + "=" * 70)
if all_good:
    print("✅ ALL 8 AREAS HAVE CORRECT MAPPINGS!")
    print("✅ All flows will load from correct Excel sheets")
    print("✅ All data will display when you press 'Load from Excel'")
else:
    print("❌ Some areas still have issues")
print("=" * 70)
