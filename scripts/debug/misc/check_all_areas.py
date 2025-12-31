import json

print("=" * 70)
print("CHECK ALL AREAS - EDGE MAPPING STATUS")
print("=" * 70)

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Define all areas and their identifiers
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

# Check each area
for area_code, (identifier, expected_sheet) in areas.items():
    # Find edges for this area
    area_edges = []
    for i, edge in enumerate(edges):
        from_node = edge.get('from', '').lower()
        to_node = edge.get('to', '').lower()
        
        if identifier in from_node or identifier in to_node or area_code.lower() in from_node or area_code.lower() in to_node:
            area_edges.append((i, edge))
    
    if area_edges:
        # Count enabled and check sheets
        enabled = sum(1 for _, e in area_edges if e.get('excel_mapping', {}).get('enabled'))
        correct_sheet = sum(1 for _, e in area_edges if e.get('excel_mapping', {}).get('sheet') == expected_sheet)
        wrong_sheet = sum(1 for _, e in area_edges if e.get('excel_mapping', {}).get('sheet') and e.get('excel_mapping', {}).get('sheet') != expected_sheet)
        
        print(f"\n{area_code:12} ({expected_sheet})")
        print(f"  Edges found: {len(area_edges)}")
        print(f"  ✅ Enabled: {enabled}/{len(area_edges)}")
        print(f"  ✅ Correct sheet: {correct_sheet}/{len(area_edges)}")
        
        if wrong_sheet > 0:
            print(f"  ❌ WRONG SHEET: {wrong_sheet}/{len(area_edges)}")
            # Show which edges have wrong sheet
            for _, edge in area_edges:
                if edge.get('excel_mapping', {}).get('sheet') and edge.get('excel_mapping', {}).get('sheet') != expected_sheet:
                    print(f"     - {edge.get('from')} → {edge.get('to')}: {edge.get('excel_mapping', {}).get('sheet')}")
        
        if enabled < len(area_edges):
            print(f"  ❌ DISABLED: {len(area_edges) - enabled}/{len(area_edges)}")
    else:
        print(f"\n{area_code:12} - ⚠️  NO EDGES FOUND")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nChecking for areas that need fixes...")

areas_to_fix = []
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
        
        if enabled < len(area_edges) or correct_sheet < len(area_edges):
            areas_to_fix.append((area_code, len(area_edges) - enabled, len(area_edges) - correct_sheet))

if areas_to_fix:
    print(f"\n⚠️  AREAS NEEDING FIXES: {len(areas_to_fix)}")
    for area_code, disabled, wrong_sheet in areas_to_fix:
        print(f"  ❌ {area_code}: {disabled} disabled, {wrong_sheet} wrong sheet")
    print("\nRun: python fix_all_area_mappings.py")
else:
    print("\n✅ ALL AREAS HAVE CORRECT MAPPINGS")
    print("✅ No fixes needed!")
