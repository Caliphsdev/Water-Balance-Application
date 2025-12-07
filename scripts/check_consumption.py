import sqlite3
from pathlib import Path
DB = Path(__file__).parent.parent / 'data' / 'water_balance.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
print('Consumption outflow destinations (joined to structure and area):')
for row in c.execute('''
    SELECT a.area_code, s.structure_code, s.structure_name,
           d.destination_code, d.destination_name, d.destination_type, d.notes
    FROM wb_outflow_destinations d
    JOIN wb_structures s ON d.source_structure_id = s.structure_id
    LEFT JOIN wb_areas a ON s.area_id = a.area_id
    WHERE d.destination_type = 'consumption'
    ORDER BY a.area_code, s.structure_code
'''):
    print(row)

print('\nOther outflow destinations (non-consumption):')
for row in c.execute('''
    SELECT a.area_code, s.structure_code, d.destination_type, d.destination_code, d.destination_name
    FROM wb_outflow_destinations d
    JOIN wb_structures s ON d.source_structure_id = s.structure_id
    LEFT JOIN wb_areas a ON s.area_id = a.area_id
    WHERE d.destination_type <> 'consumption'
    ORDER BY a.area_code, s.structure_code
'''):
    print(row)

print('\nwb_flow_connections with subcategory=consumption:')
for row in c.execute("SELECT from_structure_id, to_structure_id, flow_type, subcategory, notes FROM wb_flow_connections WHERE subcategory='consumption'"):
    print(row)

print('\nwb_measurement_map entries containing consumption:')
for row in c.execute("SELECT excel_series_code, target_type, target_id, notes FROM wb_measurement_map WHERE excel_series_code LIKE '%consum%'"):
    print(row)
conn.close()
