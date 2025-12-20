import sys
import json
from pathlib import Path
import openpyxl

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from utils.flow_volume_loader import get_flow_volume_loader

loader = get_flow_volume_loader()

# Build column map for all sheets using workbook directly
excel_path = loader._resolve_excel_path(None)
wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)

sheet_columns = {}
for sheet_name in wb.sheetnames:
    # Use loader to keep header logic consistent
    df = loader._load_sheet(sheet_name)
    if df is not None and not df.empty:
        cols = [str(c).strip() for c in df.columns if str(c).strip() not in {'Date', 'Year', 'Month'}]
        sheet_columns[sheet_name] = cols
    else:
        sheet_columns[sheet_name] = []

print("Loaded sheets:")
for k,v in sheet_columns.items():
    print(f"  {k}: {len(v)} cols")

# Scan all diagram JSONs
base = Path('data/diagrams')
diagram_files = sorted(base.glob('*.json'))
print(f"\nScanning {len(diagram_files)} diagrams...\n")

for dfile in diagram_files:
    data = json.load(open(dfile, encoding='utf-8'))
    edges = data.get('edges', [])
    unmapped = []
    invalid = []
    for idx, edge in enumerate(edges):
        mapping = edge.get('excel_mapping', {}) or {}
        sheet = mapping.get('sheet', '')
        column = mapping.get('column', '')
        enabled = mapping.get('enabled', False)
        if not sheet or not column or not enabled:
            unmapped.append((idx, edge))
            continue
        cols = sheet_columns.get(sheet, [])
        if column not in cols:
            invalid.append((idx, edge))
    if unmapped or invalid:
        area = data.get('area_code', dfile.stem)
        print(f"{dfile.name} (area {area}): {len(invalid)} invalid, {len(unmapped)} unmapped")
        if invalid:
            for i,(idx,e) in enumerate(invalid[:30]):
                m=e.get('excel_mapping',{})
                print(f"  ⚠ invalid #{idx}: {e.get('from')}→{e.get('to')}  map {m.get('sheet')}.{m.get('column')}")
        if unmapped:
            for i,(idx,e) in enumerate(unmapped[:3]):
                print(f"  ✗ unmapped #{idx}: {e.get('from')}→{e.get('to')}")
        print()
