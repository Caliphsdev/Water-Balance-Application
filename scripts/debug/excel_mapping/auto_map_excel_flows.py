#!/usr/bin/env python
"""
EXCEL MAPPING AUTOMATION TOOL
For non-programmers: Run this script to auto-map flows to Excel columns
No coding knowledge required!
"""

import json
import sys
from pathlib import Path
import pandas as pd

def get_excel_columns(excel_file, sheet_name):
    """Get all column names from Excel sheet"""
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=2)
        return list(df.columns)
    except Exception as e:
        print(f"Error reading {sheet_name}: {e}")
        return []

def auto_map_flows(json_file, excel_file):
    """
    Automatically map flows to Excel columns based on naming patterns
    """
    
    # Load JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    edges = data.get('edges', [])
    
    # Get all sheets from Excel
    xl_file = pd.ExcelFile(excel_file)
    sheets = xl_file.sheet_names
    
    # Map area codes to sheet names
    area_to_sheet = {
        'UG2N': 'Flows_UG2N',
        'MERN': 'Flows_MERN',
        'MERS': 'Flows_MERS',
        'MERPLANT': 'Flows_MERP',
        'UG2S': 'Flows_UG2S',
        'UG2PLANT': 'Flows_UG2P',
        'OLDTSF': 'Flows_OLDTSF',
        'STOCKPILE': 'Flows_STOCKPILE'
    }
    
    print("\n" + "="*70)
    print("AUTO-MAPPING FLOWS TO EXCEL COLUMNS")
    print("="*70)
    
    updated = 0
    unmapped = 0
    
    for i, edge in enumerate(edges):
        from_node = edge.get('from', '')
        to_node = edge.get('to', '')
        
        # Determine area
        area = None
        for code, sheet in area_to_sheet.items():
            if code.lower() in from_node.lower():
                area = code
                break
        
        if not area:
            continue
        
        sheet = area_to_sheet[area]
        
        # Skip if sheet doesn't exist in Excel
        if sheet not in sheets:
            continue
        
        # Get Excel columns for this sheet
        excel_cols = get_excel_columns(excel_file, sheet)
        
        # Try to find matching column
        flow_name = f"{from_node}__TO__{to_node}".lower()
        
        found_col = None
        
        # Exact match
        for col in excel_cols:
            if col.lower() == flow_name:
                found_col = col
                break
        
        # Partial match (if exact fails)
        if not found_col:
            from_part = from_node.lower()
            to_part = to_node.lower()
            for col in excel_cols:
                col_lower = col.lower()
                # Check if both parts are in column name
                if from_part in col_lower and to_part in col_lower:
                    found_col = col
                    break
        
        # Create or update mapping
        if found_col:
            if 'excel_mapping' not in edge:
                edge['excel_mapping'] = {}
            
            edge['excel_mapping']['enabled'] = True
            edge['excel_mapping']['sheet'] = sheet
            edge['excel_mapping']['column'] = found_col
            
            updated += 1
            print(f"✅ MAPPED: {from_node[:20]:20} → {to_node[:20]:20}")
            print(f"   Column: {found_col}")
        else:
            unmapped += 1
    
    # Save updated JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print(f"RESULTS: {updated} flows mapped, {unmapped} still unmapped")
    print("="*70)
    print("\n📌 NEXT STEPS:")
    print("1. Close the Flow Diagram app if it's open")
    print("2. Reopen the app")
    print("3. Load flows from Excel")
    print("4. Click 'Load from Excel' to see updated mappings")

def list_unmapped_flows(json_file):
    """Show which flows still need mapping"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    edges = data.get('edges', [])
    
    unmapped = []
    for edge in edges:
        mapping = edge.get('excel_mapping', {})
        if not mapping.get('enabled'):
            unmapped.append(edge)
    
    print(f"\n📋 UNMAPPED FLOWS ({len(unmapped)} total):\n")
    
    for edge in unmapped[:20]:  # Show first 20
        print(f"  • {edge.get('from')} → {edge.get('to')}")
    
    if len(unmapped) > 20:
        print(f"  ... and {len(unmapped) - 20} more")

if __name__ == '__main__':
    json_file = 'data/diagrams/ug2_north_decline.json'
    excel_file = 'test_templates/Water_Balance_TimeSeries_Template.xlsx'
    
    if not Path(json_file).exists():
        print(f"❌ JSON file not found: {json_file}")
        sys.exit(1)
    
    if not Path(excel_file).exists():
        print(f"❌ Excel file not found: {excel_file}")
        sys.exit(1)
    
    # Run auto-mapping
    auto_map_flows(json_file, excel_file)
    
    # Show remaining unmapped
    print("\n")
    list_unmapped_flows(json_file)
