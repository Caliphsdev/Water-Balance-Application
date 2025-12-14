import pandas as pd
from pathlib import Path

excel_file = Path('test_templates/Water_Balance_TimeSeries_Template_POPULATED.xlsx')
if excel_file.exists():
    df = pd.read_excel(excel_file, sheet_name='Flows_MERN', header=0)
    
    # Show all columns
    print('All columns in Flows_MERN:')
    for col in df.columns:
        if col not in ['Date', 'Year', 'Month']:
            print(f'  - {col}')
