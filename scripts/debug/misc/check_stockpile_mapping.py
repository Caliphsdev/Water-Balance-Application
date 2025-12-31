import pandas as pd
import json

print("=" * 70)
print("STOCKPILE AREA - EXCEL TEMPLATE CHECK")
print("=" * 70)

# Check Flows_STOCKPILE sheet
try:
    df = pd.read_excel('test_templates/Water_Balance_TimeSeries_Template.xlsx', 
                       sheet_name='Flows_STOCKPILE', header=2)
    print(f"\n✅ Flows_STOCKPILE sheet found")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print(f"\n   Column names:")
    for i, col in enumerate(df.columns):
        print(f"      {i}: {col}")
    print(f"\n   First row data:")
    row = df.iloc[0]
    for col in df.columns:
        val = row[col]
        if pd.notna(val):
            print(f"      {col}: {val}")
except Exception as e:
    print(f"\n❌ Error reading Flows_STOCKPILE: {e}")
    df = None

# Check master diagram edges that should map to Stockpile
print("\n" + "=" * 70)
print("MASTER DIAGRAM - STOCKPILE FLOW MAPPINGS")
print("=" * 70)

with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    master = json.load(f)

# Look for edges that might be Stockpile flows
stockpile_edges = []
for i, edge in enumerate(master.get('edges', [])):
    from_node = edge.get('from', '').lower()
    to_node = edge.get('to', '').lower()
    
    # Check if edge mentions stockpile or spcd (stockpile code)
    if 'stockpile' in from_node or 'stockpile' in to_node or 'spcd' in from_node or 'spcd' in to_node:
        stockpile_edges.append((i, edge))

print(f"\nFound {len(stockpile_edges)} edges mentioning Stockpile/SPCD:")
for idx, (edge_idx, edge) in enumerate(stockpile_edges[:10]):
    print(f"\n  Edge {edge_idx}:")
    print(f"    From: {edge.get('from')}")
    print(f"    To: {edge.get('to')}")
    mapping = edge.get('excel_mapping', {})
    if mapping:
        print(f"    Excel Mapping enabled: {mapping.get('enabled', False)}")
        print(f"    Excel Column: {mapping.get('column', 'NOT SET')}")
        print(f"    Excel Sheet: {mapping.get('sheet', 'NOT SET')}")
    else:
        print(f"    Excel Mapping: NONE")

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

if stockpile_edges:
    # Check if mappings exist
    mapped = sum(1 for _, e in stockpile_edges if e.get('excel_mapping', {}).get('enabled'))
    print(f"\n✅ Stockpile edges found: {len(stockpile_edges)}")
    print(f"   With Excel mappings: {mapped}/{len(stockpile_edges)}")
    
    # Check if columns match
    if df is not None:
        df_cols = set(df.columns)
        print(f"\n✅ Flows_STOCKPILE has {len(df_cols)} columns")
        
        # Check if any edge columns exist in Excel
        found_cols = 0
        for _, edge in stockpile_edges:
            mapping = edge.get('excel_mapping', {})
            col = mapping.get('column')
            if col and col in df_cols:
                found_cols += 1
        
        print(f"   Columns matching edge mappings: {found_cols}/{len(stockpile_edges)}")
else:
    print(f"\n⚠️ NO Stockpile-related edges found in master diagram!")
    print("   This is the problem - edges need to reference Stockpile nodes")
