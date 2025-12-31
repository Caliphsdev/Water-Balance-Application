"""
Verify Excel columns match the flows shown in the app image.
Compare Excel with JSON diagram nodes and app display.
"""
from openpyxl import load_workbook
import json

print('🔍 VERIFICATION: Excel vs JSON vs App Display')
print('=' * 90)
print()

# Load Excel
wb = load_workbook('test_templates/Water_Balance_TimeSeries_Template_temp.xlsx')
ws_ug2n = wb['Flows_UG2N']

# Get Excel columns
excel_cols = [cell.value for cell in ws_ug2n[1] if cell.value and '__TO__' in str(cell.value)]
print(f'📊 Excel Flows_UG2N: {len(excel_cols)} columns')
for idx, col in enumerate(excel_cols, 1):
    print(f'   {idx:2}. {col}')

# Load JSON
with open('data/diagrams/ug2_north_decline.json') as f:
    diagram = json.load(f)

# Get UG2N nodes from JSON
ug2n_nodes = []
for node in diagram.get('nodes', []):
    node_id = node.get('id')
    if node_id and any(x in node_id for x in ['rainfall', 'bh', 'softening', 'reservoir', 'offices', 'guest', 'septic', 'sewage', 'ndcd', 'north', 'loss', 'dust', 'evaporation', 'spill', 'consumption']):
        ug2n_nodes.append({
            'id': node_id,
            'label': node.get('label', node_id)
        })

print()
print(f'📝 JSON UG2N Nodes: {len(ug2n_nodes)}')
for idx, node in enumerate(sorted(ug2n_nodes, key=lambda x: x['id']), 1):
    print(f'   {node["id"]:30} → {node["label"]}')

# Get UG2N edges from JSON
ug2n_edges = []
for edge in diagram.get('edges', []):
    from_id = edge.get('from')
    to_id = edge.get('to')
    # Include if either endpoint is UG2N-related
    if from_id and to_id:
        if any(x in from_id for x in ['rainfall', 'bh', 'softening', 'reservoir', 'offices', 'guest', 'septic', 'sewage', 'ndcd', 'north', 'loss', 'dust', 'evaporation', 'spill', 'consumption', 'junction']):
            ug2n_edges.append(f'{from_id}__TO__{to_id}')

print()
print(f'📍 JSON UG2N Edges: {len(ug2n_edges)}')
for idx, edge in enumerate(sorted(ug2n_edges), 1):
    print(f'   {idx:2}. {edge}')

# Compare
print()
print('🔄 COMPARISON:')
print('=' * 90)

excel_set = set(excel_cols)
json_set = set(ug2n_edges)

only_in_excel = excel_set - json_set
only_in_json = json_set - excel_set

if only_in_excel:
    print(f'\n✅ In Excel but NOT in JSON ({len(only_in_excel)}):')
    for item in sorted(only_in_excel):
        print(f'   • {item}')

if only_in_json:
    print(f'\n⚠️ In JSON but NOT in Excel ({len(only_in_json)}):')
    for item in sorted(only_in_json):
        print(f'   • {item}')

if not only_in_excel and not only_in_json:
    print(f'\n✅ Perfect match between Excel and JSON!')

# Now check against app display names from the image
print()
print('🎯 MAPPING TO APP DISPLAY NAMES:')
print('=' * 90)
print()

# These are from the image provided
app_flows = [
    'DIRECT RAINFALL → NDCD 1-2 / NDSWD 1',
    'NDCD 1-2 / NDSWD 1 → SPILL',
    'NDCD 1-2 / NDSWD 1 → EVAPORATION',
    'NDCD 1-2 / NDSWD 1 → DUST SUPPRESSION',
    'BOREHOLE ABSTRACTION (NDGWA 1-6) → SOFTENING PLANT',
    'SOFTENING PLANT → RESERVOIR',
    'RESERVOIR → OFFICES',
    'SOFTENING PLANT → GUEST HOUSE',
    'GUEST HOUSE → SEPTIC TANK',
    'GUEST HOUSE → CONSUMPTION',
    'SOFTENING PLANT → LOSSES',
    'OFFICES → CONSUMPTION',
    'OFFICES → SEWAGE TREATMENT',
    'SEWAGE TREATMENT → LOSSES',
    'NORTH DECLINE SHAFT AREA → NDCD 1-2 / NDSWD 1',
    'NORTH DECLINE → NDCD 1-2 / NDSWD 1',
    'NDCD 1-2 / NDSWD 1 → NORTH DECLINE',
    'NDCD 1-2 / NDSWD 1 → NDCD 1-2 / NDSWD 1',
    'SEWAGE TREATMENT → Junction (1208, 365)',
    'NDCD 1-2 / NDSWD 1 → MPRWSD 1'
]

print(f'App shows {len(app_flows)} flows in UG2N:')
for idx, flow in enumerate(app_flows, 1):
    print(f'   {idx:2}. {flow}')

# Try to map app names to Excel column codes
print()
print('📋 MAPPING APP DISPLAY → EXCEL COLUMNS:')
print('-' * 90)

node_mapping = {
    'rainfall': 'rainfall',
    'ndcd': 'ndcd',
    'spill': 'spill',
    'evaporation': 'evaporation',
    'dust_suppression': 'dust_suppression',
    'bh_ndgwa': 'bh_ndgwa',
    'softening': 'softening',
    'reservoir': 'reservoir',
    'offices': 'offices',
    'guest_house': 'guest_house',
    'septic': 'septic',
    'consumption': 'consumption',
    'losses': 'losses',
    'sewage': 'sewage',
    'north_shaft': 'north_shaft',
    'north_decline': 'north_decline',
    'junction': 'junction'
}

for app_flow in app_flows:
    parts = app_flow.split(' → ')
    if len(parts) == 2:
        from_name = parts[0].strip()
        to_name = parts[1].strip()
        
        # Try to find matching Excel column
        matched = False
        for excel_col in excel_cols:
            if from_name.lower() in excel_col.lower() or to_name.lower() in excel_col.lower():
                print(f'✅ {app_flow}')
                print(f'   → {excel_col}')
                matched = True
                break
        
        if not matched:
            print(f'❌ {app_flow}')
            print(f'   → NO MATCH in Excel')

print()
print('=' * 90)
print('SUMMARY:')
print(f'   • Excel has {len(excel_cols)} UG2N flows')
print(f'   • JSON has {len(ug2n_edges)} UG2N edges')
print(f'   • App shows ~{len(app_flows)} flows in image')
print()
print('Note: Column names in Excel use JSON node IDs (e.g., rainfall__TO__ndcd)')
print('      App display uses human-readable names (e.g., DIRECT RAINFALL → NDCD 1-2 / NDSWD 1)')
