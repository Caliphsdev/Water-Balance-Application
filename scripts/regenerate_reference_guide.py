"""
Generate a corrected Reference Guide sheet data from actual diagram definitions.
Replaces the outdated Reference Guide sheet in Excel with current node/label/area info.
"""

import sys
import pathlib
import json
import pandas as pd
from typing import List, Dict, Tuple

# Ensure src is on path
SRC = pathlib.Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))

from utils.flow_volume_loader import get_flow_volume_loader


def extract_nodes_from_diagrams() -> Dict[str, List[Tuple[str, str]]]:
    """
    Extract all nodes from diagram JSON files.
    Returns dict: {area_code: [(node_id, label), ...]}
    """
    diagrams_dir = pathlib.Path('data/diagrams')
    nodes_by_area: Dict[str, List[Tuple[str, str]]] = {}
    
    for p in sorted(diagrams_dir.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            area_code = data.get('area_code')
            if not area_code or area_code == 'UNKNOWN':
                continue
            
            area_nodes = []
            for node in data.get('nodes', []):
                node_id = node.get('id', '')
                label = node.get('label', '')
                if node_id and label:
                    area_nodes.append((node_id, label))
            
            if area_nodes:
                nodes_by_area[area_code] = sorted(area_nodes)
        except Exception as e:
            print(f"⚠️ Failed to read {p}: {e}")
    
    return nodes_by_area


def generate_reference_guide_data(nodes_by_area: Dict[str, List[Tuple[str, str]]]) -> pd.DataFrame:
    """
    Generate reference guide DataFrame with columns: Node ID, Label, Area
    """
    rows = []
    for area in sorted(nodes_by_area.keys()):
        for node_id, label in nodes_by_area[area]:
            rows.append({
                'Node ID': node_id,
                'Label': label,
                'Area': area
            })
    
    return pd.DataFrame(rows)


def main() -> int:
    loader = get_flow_volume_loader()
    excel_path = loader.excel_path
    
    print(f"📄 Excel file: {excel_path}")
    
    # Extract nodes from diagrams
    nodes_by_area = extract_nodes_from_diagrams()
    print(f"📊 Areas found: {', '.join(sorted(nodes_by_area.keys()))}")
    
    total_nodes = sum(len(v) for v in nodes_by_area.values())
    print(f"📋 Total nodes: {total_nodes}\n")
    
    # Generate reference guide data
    df_reference = generate_reference_guide_data(nodes_by_area)
    
    # Read existing workbook to preserve other sheets
    try:
        with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
            existing_sheets = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names if s != 'Reference Guide'}
    except Exception as e:
        print(f"⚠️ Could not read existing sheets: {e}")
        existing_sheets = {}
    
    # Write back with updated Reference Guide
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        # Update Reference Guide
        df_reference.to_excel(writer, sheet_name='Reference Guide', index=False)
        
        # Preserve other sheets (no need to write them in append mode)

    
    print(f"✅ Reference Guide updated with {len(df_reference)} nodes")
    print(f"   Breakdown by area:")
    for area in sorted(nodes_by_area.keys()):
        count = len(nodes_by_area[area])
        print(f"   • {area}: {count} nodes")
    
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
