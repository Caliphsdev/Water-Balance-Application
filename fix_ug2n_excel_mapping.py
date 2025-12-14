"""
Fix excel_mapping for UG2N edges to match Excel column names.
The Excel columns use a different naming format.
"""
import json
from pathlib import Path

# Excel column names from the populated file
excel_columns = {
    'bh_ndgwa__softening': 'bh_ndgwa__TO__softening',
    'softening__reservoir': 'softening__TO__reservoir',
    'softening__guest_house': 'softening__TO__guest_house',
    'softening__losses': 'softening__TO__losses',
    'reservoir__offices': 'reservoir__TO__offices',
    'guest_house__consumption': 'guest_house__TO__consumption',
    'guest_house__septic': 'guest_house__TO__septic',
    'offices__consumption2': 'offices__TO__consumption2',
    'offices__sewage': 'offices__TO__sewage',
    'sewage__junction_127_1208_365': 'sewage__TO__junction_127_1208_365',
    'sewage__losses2': 'sewage__TO__losses2',
    'north_shaft__ndcd': 'north_shaft__TO__ndcd',
    'ndcd__north_decline': 'ndcd__TO__north_decline',
    'north_decline__ndcd': 'north_decline__TO__ndcd',
    'rainfall__ndcd': 'rainfall__TO__ndcd',
    'ndcd__spill': 'ndcd__TO__spill',
    'ndcd__dust_suppression': 'ndcd__TO__dust_suppression',
    'ndcd__evaporation': 'ndcd__TO__evaporation',
    'ndcd__ndcd': 'ndcd__TO__ndcd',
}

json_file = Path('data/diagrams/ug2_north_decline.json')

with open(json_file, 'r') as f:
    data = json.load(f)

edges = data.get('edges', [])
print(f'📊 Checking {len(edges)} edges for UG2N matches...\n')

matched_count = 0
unmatched_count = 0

for edge in edges:
    from_id = edge.get('from', '')
    to_id = edge.get('to', '')
    
    # Generate expected column name
    expected_column = f"{from_id}__TO__{to_id}"
    
    # Check if this matches any Excel column (with or without __TO__)
    # Try matching without area prefix
    from_simple = from_id.split('__')[-1] if '__' in from_id else from_id
    to_simple = to_id.split('__')[-1] if '__' in to_id else to_id
    simple_key = f"{from_simple}__{to_simple}"
    
    # Check if there's an Excel column that matches
    excel_column = None
    for key, val in excel_columns.items():
        if key == simple_key or val in expected_column or expected_column.endswith(val):
            excel_column = val
            break
    
    if excel_column:
        edge['excel_mapping'] = {
            'enabled': True,
            'column': excel_column,
            'sheet': 'Flows_UG2N'
        }
        matched_count += 1
        if matched_count <= 5:
            print(f'✓ Matched: {from_id} → {to_id}')
            print(f'  Excel column: {excel_column}\n')
    else:
        # Keep the auto-generated mapping but disable it
        edge['excel_mapping'] = {
            'enabled': False,
            'column': expected_column,
            'sheet': 'Flows_UG2N'
        }
        unmatched_count += 1

print(f'\n✅ Matched: {matched_count} edges to Excel columns')
print(f'⏭️  Unmatched: {unmatched_count} edges (disabled)')

# Save
with open(json_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f'\n💾 Saved to: {json_file}')
