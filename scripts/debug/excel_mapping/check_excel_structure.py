"""Check and display the Excel template structure."""
import pandas as pd

excel_file = 'test_templates/Water_Balance_TimeSeries_Template.xlsx'

# Read with row 2 as header (row 1 contains column names)
df = pd.read_excel(excel_file, sheet_name='Flows_UG2N', header=2, engine='openpyxl')

print('📊 Flows_UG2N Sheet Structure:')
print('='*70)
print(f'Total Rows: {len(df)}')
print(f'Total Columns: {len(df.columns)}')
print()
print('Columns:')
for i, col in enumerate(df.columns, 1):
    print(f'  {i:2d}. {col}')
print()
print('Data Sample:')
print(df.head())
print()
print('Column Types:')
print(df.dtypes)
