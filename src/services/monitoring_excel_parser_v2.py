"""
Monitoring Excel Parser V2 - STACKED BLOCKS Structure (COPIED FROM TKINTER)

Handles borehole monitoring Excel files with complex header layout.
Based on proven Tkinter implementation at Water-Balance-Application/src/ui/monitoring_data.py

STRUCTURE:
    Row 0-4: Metadata headers (ignored)
    Row 5: Parameter headers → "Calcium^", "Chloride^", "Static Level", etc.
    Row 6: Units → "mg/l", "mg/l", "m"
    Row 7: Section header → "TWO RIVERS GROUNDWATER MONITORING"
    Row 8: Borehole ID → "TRPGWM 01"
    Row 9+: Data rows → timestamp + values
    Row X: Next borehole ID → "TRPGWM 02"
    Row X+1+: Data rows for next borehole
    
ONLY USED FOR: Borehole Monitoring tab
DOES NOT AFFECT: PCD or Static Levels tabs (separate parsers)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import re
from datetime import datetime
from typing import List, Dict
from core.app_logger import logger


def parse_borehole_stacked_blocks(file_path: str) -> pd.DataFrame:
    """
    Parse BOREHOLE MONITORING Excel (stacked blocks structure).
    
    Algorithm (copied from Tkinter):
        1. Find header row by searching for "Static Level" keyword (rows 0-20)
        2. Extract parameter names from header row
        3. Find borehole name rows using regex (col A after header)
        4. Parse data between borehole blocks
    
    Args:
        file_path: Excel file path
    
    Returns:
        DataFrame with columns: borehole, aquifer, date, calcium, chloride, etc.
    """
    # 1. Read Excel with NO header (raw data)
    try:
        df_raw = pd.read_excel(file_path, header=None, engine='xlrd')
    except Exception:
        df_raw = pd.read_excel(file_path, header=None)
    
    if df_raw.empty:
        logger.warning(f"Empty Excel: {Path(file_path).name}")
        return pd.DataFrame()
    
    # 2. Locate header row by searching for "Static Level" keyword
    header_row = None
    for i in range(min(len(df_raw), 20)):
        row_str = df_raw.iloc[i].astype(str).str.lower()
        if row_str.str.contains('static level').any():
            header_row = i
            break
    
    if header_row is None:
        header_row = 5 if len(df_raw) > 5 else 0  # Default to row 5 as fallback
    
    logger.info(f"Detected header row: {header_row}")
    
    # 3. Extract parameter names from header row
    params = []
    for col_idx, val in enumerate(df_raw.iloc[header_row]):
        if pd.notna(val):
            name = str(val).replace('\xa0', ' ').strip()
            if name:
                # Clean up: remove control chars, superscripts
                name = re.sub(r"[\r\n]+", " ", name).replace('^', '').strip()
                if name and name.lower() != 'monitoring point':
                    params.append((col_idx, name))
    
    logger.info(f"Found {len(params)} parameters: {[p[1] for p in params]}")
    
    # 4. Identify borehole name rows (col A, after header row)
    borehole_pattern = re.compile(r'^[A-Z]{3,}\s*\d+[A-Z]*')  # Matches "TRPGWM 01", "BH 12", etc.
    borehole_rows = []
    for i in range(header_row + 1, len(df_raw)):
        val = df_raw.iat[i, 0]
        if pd.isna(val):
            continue
        s = str(val).replace('\xa0', '').strip()
        if borehole_pattern.match(s):
            borehole_rows.append(i)
    
    if not borehole_rows:
        logger.warning(f"No borehole IDs found in {Path(file_path).name}")
        return pd.DataFrame()
    
    borehole_rows.append(len(df_raw))  # Sentinel to mark end of file
    logger.info(f"Found {len(borehole_rows) - 1} boreholes")
    
    # 5. Parse data rows between borehole blocks
    records = []
    for idx in range(len(borehole_rows) - 1):
        start_row = borehole_rows[idx]
        end_row = borehole_rows[idx + 1]
        borehole_name = str(df_raw.iat[start_row, 0]).replace('\xa0', '').strip()
        
        if not borehole_name:
            continue
        
        # Data rows start immediately after borehole name row
        for data_row_idx in range(start_row + 1, end_row):
            date_cell = df_raw.iat[data_row_idx, 0]
            if pd.isna(date_cell):
                continue
            
            date_str = str(date_cell).replace('\xa0', '').strip()
            
            # Detect aquifer from suffix: (S) = Shallow, (D) = Deep
            aquifer = ''
            if '(S' in date_str.upper():
                aquifer = 'Shallow Aquifer'
            elif '(D' in date_str.upper():
                aquifer = 'Deep Aquifer'
            
            # Remove suffix for date parsing
            if '(' in date_str:
                date_str = date_str.split('(')[0].strip()
            
            # Parse date
            try:
                # Try multiple formats to avoid day/month confusion
                parsed_date = None
                for fmt in ["%Y/%m/%d %I:%M:%S %p", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        parsed_date = pd.to_datetime(date_str, format=fmt)
                        break
                    except:
                        continue
                
                if parsed_date is None:
                    parsed_date = pd.to_datetime(date_str, errors='coerce')
                
                if pd.isna(parsed_date):
                    continue
                
            except Exception:
                continue
            
            # Build record
            record = {
                'borehole': borehole_name,
                'borehole_norm': borehole_name.upper(),
                'date': parsed_date.to_pydatetime() if hasattr(parsed_date, 'to_pydatetime') else parsed_date,
                'aquifer': aquifer
            }
            
            # Extract parameter values
            for col_idx, param_name in params:
                if col_idx >= df_raw.shape[1]:
                    continue
                
                val = df_raw.iat[data_row_idx, col_idx]
                if pd.isna(val):
                    continue
                
                val_str = str(val).strip()
                if not val_str or val_str.upper() == 'NO ACCESS' or '<' in val_str:
                    continue
                
                try:
                    record[param_name] = float(val)
                except Exception:
                    record[param_name] = val_str
            
            records.append(record)
    
    df_result = pd.DataFrame(records)
    if not df_result.empty:
        df_result['source_file'] = Path(file_path).name
        df_result = df_result.sort_values(['borehole', 'date']).reset_index(drop=True)
    
    row_count = len(df_result)
    param_count = len([col for col in df_result.columns if col not in ['borehole', 'borehole_norm', 'date', 'aquifer', 'source_file']])
    logger.info(f"OK Parsed {Path(file_path).name}: {row_count} rows, {param_count} parameters")
    
    return df_result
