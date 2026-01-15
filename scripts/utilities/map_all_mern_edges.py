import json
from pathlib import Path
import pandas as pd

# Load the diagram
diagram_file = Path('data/diagrams/ug2_north_decline.json')
with open(diagram_file) as f:
    data = json.load(f)

# Load Excel to get available columns
excel_file = Path('test_templates/Water_Balance_TimeSeries_Template.xlsx')
df = pd.read_excel(excel_file, sheet_name='Flows_MERN', header=2)
flow_cols = set([c for c in df.columns if c not in ['Date', 'Year', 'Month']])

print(f"Found {len(flow_cols)} flow columns in Flows_MERN")
print()

# Find and update Merensky edges
edges = data.get('edges', [])
updated = 0
already_mapped = 0
no_match = 0

for edge in edges:
    from_id = edge.get('from', '')
    to_id = edge.get('to', '')
    
    # Skip if not a Merensky edge
    if 'merensky' not in from_id.lower() and 'merensky' not in to_id.lower():
        continue
    
    # Check current mapping
    mapping = edge.get('excel_mapping', {})
    
    if mapping.get('enabled'):
        already_mapped += 1
        continue
    
    # Try to find matching column in Excel
    # Pattern: from_id__TO__to_id
    potential_col = f"{from_id}__TO__{to_id}"
    
    if potential_col in flow_cols:
        edge['excel_mapping'] = {
            'enabled': True,
            'column': potential_col,
            'sheet': 'Flows_Merensky North'
        }
        print(f"✓ Mapped: {from_id} → {to_id}")
        print(f"  Column: {potential_col}")
        updated += 1
    else:
        print(f"❌ No match: {from_id} → {to_id} (looking for: {potential_col})")
        no_match += 1
    
    print()

# Save updated diagram
with open(diagram_file, 'w') as f:
    json.dump(data, f, indent=2)

print("="*80)
print(f"Summary:")
print(f"  Already mapped: {already_mapped}")
print(f"  Newly mapped: {updated}")
print(f"  No Excel match: {no_match}")
print(f"\n✅ Diagram updated and saved!")
