"""
Populate UG2N Excel template with flow values from the diagram image.
Creates a new Excel file with the flow data filled in.
"""
import pandas as pd
from pathlib import Path
from datetime import date

# Flow values from the UG2 North Decline Area diagram
# Column names MUST match exactly what's in the Excel template
ug2n_flow_values = {
    # Main flows from diagram
    'bh_ndgwa__TO__softening': 71530,              # Borehole → Softening
    'softening__TO__reservoir': 47485,             # Softening → Reservoir
    'softening__TO__guest_house': 3706,            # Softening → Guest House (inflow)
    'softening__TO__losses': 2594,                 # Softening losses
    'reservoir__TO__offices': 47485,               # Reservoir → Offices
    'guest_house__TO__consumption': 3706,          # Guest House consumption
    'guest_house__TO__septic': 2594,               # Guest House → Septic/Losses
    'offices__TO__consumption2': 33240,            # Offices consumption
    'offices__TO__sewage': 33240,                  # Offices → Sewage Treatment
    'sewage__TO__junction_127_1208_365': 46425,    # Sewage → Junction (to NDCD)
    'sewage__TO__losses2': 14132,                  # Sewage → North Decline/Losses
    'north_shaft__TO__ndcd': 33240,                # North Shaft → NDCD
    'ndcd__TO__north_decline': 187761,             # NDCD → North Decline
    'north_decline__TO__ndcd': 245572,             # North Decline → NDCD (return)
    'rainfall__TO__ndcd': 5363,                    # Rainfall → NDCD
    'ndcd__TO__spill': 5923,                       # NDCD spillage
    'ndcd__TO__dust_suppression': 1112,            # NDCD → Dust suppression
    'ndcd__TO__evaporation': 14759,                # NDCD evaporation
    'ndcd__TO__ndcd': 14246,                       # NDCD internal recirculation
}

# Path to Excel file
excel_file = Path('test_templates/Water_Balance_TimeSeries_Template.xlsx')
output_file = Path('test_templates/Water_Balance_TimeSeries_Template_POPULATED.xlsx')

print(f'📊 Populating Excel template from diagram values...')
print(f'Reading: {excel_file}')

# Read the existing Excel file with all sheets
with pd.ExcelFile(excel_file, engine='openpyxl') as xls:
    # Create a dictionary to store all sheets
    all_sheets = {}
    
    for sheet_name in xls.sheet_names:
        if sheet_name.startswith('Flows_UG2N'):
            # Read UG2N sheet with header in row 3 (index 2)
            df = pd.read_excel(xls, sheet_name=sheet_name, header=2, engine='openpyxl')
            
            print(f'\n✅ Processing sheet: {sheet_name}')
            print(f'   Rows: {len(df)}')
            print(f'   Columns: {len(df.columns)}')
            
            # Update the first data row (December 2025)
            if len(df) > 0:
                # Set Date, Year, Month
                df.loc[0, 'Date'] = 1  # Day of month
                df.loc[0, 'Year'] = 2025
                df.loc[0, 'Month'] = 12
                
                # Update flow values
                updated_count = 0
                for flow_id, value in ug2n_flow_values.items():
                    if flow_id in df.columns:
                        df.loc[0, flow_id] = value
                        updated_count += 1
                        print(f'   ✓ {flow_id}: {value:,.0f} m³')
                    else:
                        print(f'   ⚠ Column not found: {flow_id}')
                
                print(f'\n   📝 Updated {updated_count} flows')
                
                # Add more months if needed (copy December values)
                if len(df) == 1:
                    # Add November and October with same values
                    nov_row = df.iloc[0].copy()
                    nov_row['Month'] = 11
                    oct_row = df.iloc[0].copy()
                    oct_row['Month'] = 10
                    
                    df = pd.concat([df, pd.DataFrame([nov_row]), pd.DataFrame([oct_row])], ignore_index=True)
                    print(f'   ➕ Added November and October rows (same values)')
            
            all_sheets[sheet_name] = df
        else:
            # Keep other sheets unchanged
            all_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)

# Write to new Excel file
print(f'\n💾 Saving to: {output_file}')
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, df in all_sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f'\n✅ Done! Excel template populated successfully')
print(f'📂 Output: {output_file}')
print(f'\n💡 Next steps:')
print(f'   1. Open the Excel file and verify the values')
print(f'   2. Update Settings > Data Sources to point to this file')
print(f'   3. Load flows in the Flow Diagram module')
