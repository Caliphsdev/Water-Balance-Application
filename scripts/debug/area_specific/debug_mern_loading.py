import json
from pathlib import Path
import pandas as pd

# Load the diagram
diagram_file = Path('data/diagrams/ug2_north_decline.json')
with open(diagram_file) as f:
    data = json.load(f)

# Load the Excel data
excel_file = Path('test_templates/Water_Balance_TimeSeries_Template.xlsx')
df = pd.read_excel(excel_file, sheet_name='Flows_MERN', header=2)

print("Available MERN flows in Excel:")
flow_cols = [c for c in df.columns if c not in ['Date', 'Year', 'Month']]
for col in flow_cols:
    val = df.iloc[0][col] if len(df) > 0 else 'N/A'
    print(f"  {col}: {val}")

print("\n" + "="*80 + "\n")

# Find all Merensky edges
edges = data.get('edges', [])
merensky_edges = [e for e in edges if 'merensky' in e.get('from', '').lower() or 'merensky' in e.get('to', '').lower()]

print(f"Found {len(merensky_edges)} Merensky edges in diagram:\n")

for i, edge in enumerate(merensky_edges, 1):
    from_id = edge.get('from', '')
    to_id = edge.get('to', '')
    mapping = edge.get('excel_mapping', {})
    
    print(f"{i}. {from_id} → {to_id}")
    
    if mapping.get('enabled'):
        col = mapping.get('column', '')
        sheet = mapping.get('sheet', '')
        print(f"   ✓ Mapped to: {sheet}/{col}")
        
        # Check if column exists in Excel
        if col in flow_cols:
            val = df.iloc[0][col] if len(df) > 0 else 'N/A'
            print(f"   ✓ Excel value: {val}")
        else:
            print(f"   ❌ Column NOT FOUND in Excel!")
    else:
        print(f"   ❌ NOT MAPPED")
    
    print()
