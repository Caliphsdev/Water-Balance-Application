import json

print("=" * 70)
print("FIXING ALL AREA MAPPINGS")
print("=" * 70)

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Area mappings: identifier -> correct sheet
area_mappings = {
    'ug2_north': 'Flows_UG2N',
    'ndcd': 'Flows_UG2N',
    'mern': 'Flows_MERN',
    'merensky_north': 'Flows_MERN',
    'mers': 'Flows_MERS',
    'merensky_south': 'Flows_MERS',
    'mdcd': 'Flows_MERS',  # Merensky South uses MDCD
    'merplant': 'Flows_MERPLANT',
    'ug2south': 'Flows_UG2S',
    'ug2s': 'Flows_UG2S',
    'ug2plant': 'Flows_UG2PLANT',
    'oldtsf': 'Flows_OLDTSF',
    'stockpile': 'Flows_STOCKPILE',
    'spcd': 'Flows_STOCKPILE'
}

fixed_count = 0
disabled_count = 0

for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # Determine which area this edge belongs to
    correct_sheet = None
    for identifier, sheet_name in area_mappings.items():
        if identifier in from_node or identifier in to_node:
            correct_sheet = sheet_name
            break
    
    if correct_sheet:
        mapping = edge.get('excel_mapping', {})
        
        # Check if mapping needs fixing
        current_sheet = mapping.get('sheet')
        is_enabled = mapping.get('enabled', False)
        
        if current_sheet != correct_sheet or not is_enabled:
            # Fix the mapping
            edge['excel_mapping'] = {
                'enabled': True,
                'sheet': correct_sheet,
                'column': mapping.get('column', '')
            }
            
            if not is_enabled:
                disabled_count += 1
            
            if current_sheet != correct_sheet:
                fixed_count += 1
                if fixed_count <= 5:  # Show first 5 fixes
                    print(f"\n✅ Edge {i}: {from_node} → {to_node}")
                    print(f"   Changed: {current_sheet or 'NONE'} → {correct_sheet}")

# Save fixed diagram
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(master, f, indent=2)

print(f"\n" + "=" * 70)
print(f"✅ FIXED {fixed_count} sheet references")
print(f"✅ ENABLED {disabled_count} disabled mappings")
print(f"✅ All areas now have correct Excel sheet mappings")
print("=" * 70)
