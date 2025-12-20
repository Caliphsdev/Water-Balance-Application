import sys
from pathlib import Path
import json
from typing import Dict, List, Tuple

# Ensure src is on path
SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))

from utils.flow_volume_loader import get_flow_volume_loader


def load_diagrams(diagrams_dir: Path) -> List[Tuple[str, Dict]]:
    diagrams = []
    for p in sorted(diagrams_dir.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            diagrams.append((p.name, data))
        except Exception as e:
            print(f"❌ Failed to read {p}: {e}")
    return diagrams


def collect_refs(area_json: Dict) -> List[Tuple[str, str]]:
    refs: List[Tuple[str, str]] = []
    edges = area_json.get('edges', [])
    area_code = area_json.get('area_code', '')
    for e in edges:
        m = e.get('excel_mapping', {})
        if not m or not m.get('enabled'):
            continue
        sheet = m.get('sheet') or (f"Flows_{area_code}" if area_code else None)
        column = m.get('column') or ''
        if sheet:
            refs.append((sheet, column))
    return refs


def main() -> int:
    diagrams_dir = Path('data/diagrams')
    if not diagrams_dir.exists():
        print('❌ diagrams directory not found: data/diagrams')
        return 2

    loader = get_flow_volume_loader()
    print(f"📄 Excel file: {loader.excel_path}")
    sheets = set(loader.list_sheets())
    print(f"📚 Workbook sheets ({len(sheets)}): {sorted(sheets)}")

    diagrams = load_diagrams(diagrams_dir)
    if not diagrams:
        print('⚠️ No diagrams found')
        return 0

    total_missing_sheets = 0
    total_missing_columns = 0

    for name, data in diagrams:
        area_code = data.get('area_code', 'UNKNOWN')
        refs = collect_refs(data)
        if not refs:
            print(f"- {name} ({area_code}): No enabled excel mappings")
            continue

        print(f"- {name} ({area_code}): {len(refs)} enabled mappings")
        # Group by sheet
        by_sheet: Dict[str, List[str]] = {}
        for s, c in refs:
            by_sheet.setdefault(s, []).append(c)

        for sheet, columns in sorted(by_sheet.items()):
            exists = sheet in sheets
            df_cols = loader.list_sheet_columns(sheet) if exists else []
            base_ok = bool(df_cols)  # True if we have at least one data column
            y_m_ok = True  # We can't directly check Year/Month via list_sheet_columns
            # Report
            status = 'OK' if exists and base_ok else ('EMPTY' if exists and not base_ok else 'MISSING')
            print(f"  • Sheet {sheet}: {status} ({len(df_cols)} columns)")
            if not exists:
                total_missing_sheets += 1
            # Check columns
            missing_cols = [c for c in columns if c and c not in df_cols]
            if missing_cols:
                total_missing_columns += len(missing_cols)
                print(f"    ⨯ Missing columns: {missing_cols}")
            present_cols = [c for c in columns if c and c in df_cols]
            if present_cols:
                print(f"    ✓ Present columns: {present_cols[:6]}{' …' if len(present_cols)>6 else ''}")

    # Summary
    print('\n==== Summary ====')
    print(f"Missing sheets: {total_missing_sheets}")
    print(f"Missing columns: {total_missing_columns}")
    if total_missing_sheets == 0 and total_missing_columns == 0:
        print('✅ All referenced sheets and columns look valid')
    else:
        print('⚠️ Some mappings reference missing sheets/columns. Consider:')
        print('   - Fix excel_mapping.sheet to a valid Flows_<AREA> sheet')
        print('   - Fix excel_mapping.column to match an existing column name')
        print('   - Clear cache if the Excel file changed (Settings → or call reset_flow_volume_loader)')
        print('   - Disable excel_mapping.enabled for edges that should not load volumes')

    # Special note: OLD TSF case explanation
    print('\nNote: If OLD TSF sheet is EMPTY but data loads, likely because:')
    print(' - Other referenced sheets contain the same column names and are being loaded')
    print(' - The loader aggregates volumes from all referenced sheets in the diagram')
    print(' - Cached DataFrames may serve stale values; clear cache to force reload')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
