"""Test script to examine actual Excel file structure."""
import pandas as pd
from pathlib import Path

# Read the Excel file without headers to see raw structure
file_path = Path("C:/Users/Caliphs Zvinowanda/OneDrive/Desktop/Monitoring Borehole/Boreholes Q3 2021.xls")

if file_path.exists():
    print(f"\nAnalyzing: {file_path.name}")
    print("=" * 100)
    
    # Read all rows
    df = pd.read_excel(file_path, header=None)
    
    print(f"\nTotal rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    # Show rows 0-10 to understand structure
    print("\n--- ROWS 0-10 (Raw Structure) ---")
    for i in range(min(10, len(df))):
        print(f"\nRow {i}:")
        for j, val in enumerate(df.iloc[i].values):
            print(f"  Col {j}: {repr(val)}")
    
    # Show rows 4-6 specifically
    print("\n--- ROWS 4-6 (Header Detection Zone) ---")
    for i in range(4, min(7, len(df))):
        row = df.iloc[i]
        print(f"\nRow {i}:")
        print(f"  Values: {list(row.values)}")
        print(f"  Str version: {str(row.values)}")
        if "Monitoring Parameter" in str(row.values).lower():
            print(f"  >>> Found 'Monitoring Parameter'!")
    
    # Show row 8 (borehole ID)
    if len(df) > 8:
        print(f"\n--- ROW 8 (Borehole ID) ---")
        print(f"Row 8, Col 0: {repr(df.iloc[8, 0])}")
    
    # Show row 9 onwards (data rows)
    print(f"\n--- ROWS 9-12 (Data Rows) ---")
    for i in range(9, min(13, len(df))):
        print(f"\nRow {i}:")
        for j, val in enumerate(df.iloc[i].values[:5]):  # Just first 5 cols
            print(f"  Col {j}: {repr(val)}")
else:
    print(f"File not found: {file_path}")

print("\n" + "=" * 100)
