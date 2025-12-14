import pandas as pd
import json

print("=" * 70)
print("CHECKING INTER-AREA FLOWS IN EXCEL")
print("=" * 70)

# Load master diagram
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

edges = master.get('edges', [])

# Find inter-area flow edges and their mappings
inter_area_flows = []
for i, edge in enumerate(edges):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # Check if this is inter-area
    areas = ['mers', 'ug2s', 'merplant', 'oldtsf', 'ug2plant', 'mern', 'stockpile']
    from_area = None
    to_area = None
    
    for area in areas:
        if area in from_node:
            from_area = area
            break
    
    for area in areas:
        if area in to_node and area != from_area:
            to_area = area
            break
    
    if from_area and to_area:
        mapping = edge.get('excel_mapping', {})
        column = mapping.get('column', '')
        sheet = mapping.get('sheet', '')
        inter_area_flows.append({
            'from': from_node,
            'to': to_node,
            'from_area': from_area,
            'to_area': to_area,
            'column': column,
            'sheet': sheet
        })

print(f"\nFound {len(inter_area_flows)} inter-area flows\n")

# Check if columns exist in mapped sheets
excel_file = 'test_templates/Water_Balance_TimeSeries_Template.xlsx'

print("Verifying inter-area flow columns exist in mapped Excel sheets:\n")

verified = 0
missing = 0

for flow in inter_area_flows[:10]:  # Check first 10
    sheet = flow['sheet']
    column = flow['column']
    
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet, header=2)
        
        if column in df.columns:
            print(f"✅ {flow['from_area']:12} → {flow['to_area']:12}")
            print(f"   Column: {column}")
            print(f"   Sheet: {sheet}")
            print(f"   Value: {df.iloc[0][column]}")
            verified += 1
        else:
            print(f"❌ {flow['from_area']:12} → {flow['to_area']:12}")
            print(f"   Column: {column}")
            print(f"   Sheet: {sheet} - COLUMN NOT FOUND")
            missing += 1
    except Exception as e:
        print(f"❌ {flow['from_area']:12} → {flow['to_area']:12}")
        print(f"   Error reading {sheet}: {e}")
        missing += 1
    
    print()

print("=" * 70)
print(f"Results: {verified} working, {missing} missing")

if missing > 0:
    print("\n⚠️  Some inter-area flows have missing Excel columns")
    print("    They may need to be mapped to source area sheets instead")
else:
    print("\n✅ All inter-area flows found in Excel!")
