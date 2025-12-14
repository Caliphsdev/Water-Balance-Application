import json
import pandas as pd

# Check Merensky North JSON
print("=" * 60)
print("MERENSKY NORTH AREA JSON")
print("=" * 60)
with open('data/diagrams/merensky_north_area.json', 'r') as f:
    mern = json.load(f)

print(f"Area Code: {mern.get('area_code')}")
print(f"Title: {mern.get('title')}")
print(f"Nodes: {len(mern.get('nodes', []))}")
print(f"Edges: {len(mern.get('edges', []))}")
print(f"Zone BG: {len(mern.get('zone_bg', []))}")
if mern.get('nodes'):
    print(f"First node: {mern['nodes'][0]}")
if mern.get('edges'):
    print(f"First edge keys: {list(mern['edges'][0].keys())}")

# Check Stockpile JSON
print("\n" + "=" * 60)
print("STOCKPILE AREA JSON")
print("=" * 60)
with open('data/diagrams/stockpile_area.json', 'r') as f:
    spcd = json.load(f)

print(f"Area Code: {spcd.get('area_code')}")
print(f"Title: {spcd.get('title')}")
print(f"Nodes: {len(spcd.get('nodes', []))}")
print(f"Edges: {len(spcd.get('edges', []))}")
print(f"Zone BG: {len(spcd.get('zone_bg', []))}")
if spcd.get('nodes'):
    print(f"First node: {spcd['nodes'][0]}")
if spcd.get('edges'):
    print(f"First edge keys: {list(spcd['edges'][0].keys())}")

# Check Excel sheets
print("\n" + "=" * 60)
print("EXCEL SHEET STRUCTURE")
print("=" * 60)

# Check Merensky North
try:
    df_mern = pd.read_excel('test_templates/Water_Balance_TimeSeries_Template.xlsx', 
                            sheet_name='Flows_MERN', header=2)
    print(f"✅ Flows_MERN: {len(df_mern)} rows, {len(df_mern.columns)} columns")
    print(f"   Columns: {df_mern.columns.tolist()[:5]}...")
except Exception as e:
    print(f"❌ Flows_MERN: {e}")

# Check Stockpile
try:
    df_spcd = pd.read_excel('test_templates/Water_Balance_TimeSeries_Template.xlsx', 
                            sheet_name='Flows_STOCKPILE', header=2)
    print(f"\n✅ Flows_STOCKPILE: {len(df_spcd)} rows, {len(df_spcd.columns)} columns")
    print(f"   Columns: {df_spcd.columns.tolist()[:5]}...")
except Exception as e:
    print(f"❌ Flows_STOCKPILE: {e}")

# Compare
print("\n" + "=" * 60)
print("COMPARISON")
print("=" * 60)
print(f"Merensky North nodes = Stockpile nodes? {len(mern.get('nodes', [])) == len(spcd.get('nodes', []))}")
print(f"Merensky North edges = Stockpile edges? {len(mern.get('edges', [])) == len(spcd.get('edges', []))}")

# Check if they're actually the same (deep comparison)
if mern.get('nodes') and spcd.get('nodes'):
    same_nodes = mern.get('nodes') == spcd.get('nodes')
    print(f"Merensky North nodes identical to Stockpile? {same_nodes}")
    if same_nodes:
        print("  ⚠️ Both have identical node data - this is the issue!")
        print("  Stockpile needs its OWN nodes, not copies of UG2N")

if mern.get('edges') and spcd.get('edges'):
    same_edges = mern.get('edges') == spcd.get('edges')
    print(f"Merensky North edges identical to Stockpile? {same_edges}")
    if same_edges:
        print("  ⚠️ Both have identical edge data")
