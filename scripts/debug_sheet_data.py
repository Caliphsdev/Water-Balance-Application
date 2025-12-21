"""
Debug sheet data to see what Year/Month values are present.

Usage:
  .venv\Scripts\python scripts\debug_sheet_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.flow_volume_loader import get_flow_volume_loader, reset_flow_volume_loader

reset_flow_volume_loader()
loader = get_flow_volume_loader()

# Check sheets with data
sheets_with_data = ['Flows_UG2N', 'Flows_STOCKPILE', 'Flows_UG2S']

for sheet_name in sheets_with_data:
    print(f"\n{'='*60}")
    print(f"Sheet: {sheet_name}")
    print(f"{'='*60}")
    
    df = loader._load_sheet(sheet_name)
    if df.empty:
        print("  Empty DataFrame")
        continue
    
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)[:8]}")
    
    if 'Year' in df.columns and 'Month' in df.columns:
        print(f"\n  Year/Month data:")
        for idx, row in df.iterrows():
            year = row.get('Year')
            month = row.get('Month')
            print(f"    Row {idx}: Year={year}, Month={month}")
    else:
        print("  ❌ Year/Month columns not found!")
    
    # Show first data row
    print(f"\n  First row sample:")
    if not df.empty:
        first_row = df.iloc[0]
        for col in list(df.columns)[:8]:
            print(f"    {col}: {first_row[col]}")
