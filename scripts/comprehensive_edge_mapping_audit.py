"""
Comprehensive audit: verify that EVERY edge in flow diagrams is connected to an Excel column.
Groups results by area and sheet for clarity.
"""

import sys
from pathlib import Path
import json
from typing import Dict, List, Tuple, Set

# Ensure src is on path
SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))

from utils.flow_volume_loader import get_flow_volume_loader


def load_diagrams(diagrams_dir: Path) -> List[Tuple[str, Dict]]:
    """Load all diagram JSON files."""
    diagrams = []
    for p in sorted(diagrams_dir.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            diagrams.append((p.name, data))
        except Exception as e:
            print(f"❌ Failed to read {p}: {e}")
    return diagrams


def main() -> int:
    diagrams_dir = Path('data/diagrams')
    if not diagrams_dir.exists():
        print('❌ diagrams directory not found: data/diagrams')
        return 2

    loader = get_flow_volume_loader()
    print(f"📄 Excel file: {loader.excel_path}")
    sheets = set(loader.list_sheets())
    print(f"📚 Workbook sheets ({len(sheets)}): {sorted(sheets)}\n")

    diagrams = load_diagrams(diagrams_dir)
    if not diagrams:
        print('⚠️ No diagrams found')
        return 0

    # Global counters
    total_edges = 0
    total_unmapped = 0
    total_missing_refs = 0

    for name, data in diagrams:
        area_code = data.get('area_code', 'UNKNOWN')
        edges = data.get('edges', [])
        
        print(f"\n{'='*70}")
        print(f"Diagram: {name} (Area: {area_code})")
        print(f"{'='*70}")
        print(f"Total edges: {len(edges)}\n")

        # Categorize edges
        unmapped_edges = []
        mapped_edges_by_sheet: Dict[str, List[Dict]] = {}
        
        for edge in edges:
            total_edges += 1
            from_node = edge.get('from', '?')
            to_node = edge.get('to', '?')
            edge_label = f"{from_node} → {to_node}"
            
            excel_mapping = edge.get('excel_mapping', {})
            if not excel_mapping or not excel_mapping.get('enabled'):
                unmapped_edges.append((edge_label, excel_mapping))
                total_unmapped += 1
                continue
            
            sheet = excel_mapping.get('sheet') or f'Flows_{area_code}'
            column = excel_mapping.get('column')
            
            if not column:
                unmapped_edges.append((edge_label, excel_mapping))
                total_unmapped += 1
                continue
            
            # Check if sheet/column exist
            exists = sheet in sheets
            df_cols = loader.list_sheet_columns(sheet) if exists else []
            col_exists = column in df_cols if exists else False
            
            if not (exists and col_exists):
                total_missing_refs += 1
                status = "MISSING" if not exists else "COL_MISSING"
                print(f"  ⨯ {edge_label}")
                print(f"    ↳ Mapping: {sheet} → {column} [{status}]")
                continue
            
            # Valid mapping
            if sheet not in mapped_edges_by_sheet:
                mapped_edges_by_sheet[sheet] = []
            mapped_edges_by_sheet[sheet].append({
                'label': edge_label,
                'column': column
            })
        
        # Report unmapped edges
        if unmapped_edges:
            print(f"❌ UNMAPPED EDGES ({len(unmapped_edges)}):")
            for label, mapping in unmapped_edges:
                if mapping:
                    print(f"  • {label}")
                    print(f"    ↳ Partial mapping: enabled={mapping.get('enabled')}, sheet={mapping.get('sheet')}, column={mapping.get('column')}")
                else:
                    print(f"  • {label} (no excel_mapping)")
        
        # Report valid mapped edges by sheet
        if mapped_edges_by_sheet:
            print(f"\n✅ VALID MAPPINGS BY SHEET:")
            for sheet in sorted(mapped_edges_by_sheet.keys()):
                edges_for_sheet = mapped_edges_by_sheet[sheet]
                print(f"\n  📊 Sheet: {sheet}")
                print(f"     Edges ({len(edges_for_sheet)}):")
                for edge_info in edges_for_sheet[:5]:  # Show first 5
                    print(f"     • {edge_info['label']} → {edge_info['column']}")
                if len(edges_for_sheet) > 5:
                    print(f"     ... and {len(edges_for_sheet) - 5} more")
        
        if not unmapped_edges and not mapped_edges_by_sheet:
            print("⚠️ No edges found or all disabled")

    # Global summary
    print(f"\n\n{'='*70}")
    print("GLOBAL SUMMARY")
    print(f"{'='*70}")
    print(f"Total edges across all diagrams: {total_edges}")
    print(f"Unmapped or incomplete mappings: {total_unmapped}")
    print(f"Mapped to missing sheet/column: {total_missing_refs}")
    print(f"Properly mapped: {total_edges - total_unmapped - total_missing_refs}")
    
    if total_unmapped == 0 and total_missing_refs == 0:
        print("\n✅ ALL EDGES ARE PROPERLY MAPPED TO VALID EXCEL REFERENCES!")
        return 0
    else:
        print("\n⚠️ Some edges need attention. Fix unmapped edges and missing references above.")
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
