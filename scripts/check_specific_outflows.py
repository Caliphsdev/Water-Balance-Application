import sqlite3
from pathlib import Path
DB = Path(__file__).parent.parent / 'data' / 'water_balance.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

print('=== MPRWSD1 in structures ===')
for row in c.execute("SELECT structure_code, structure_name FROM wb_structures WHERE structure_code='MPRWSD1'"):
    print(row)

print('\n=== All MER_PLANT structures ===')
for row in c.execute("SELECT s.structure_code, s.structure_name FROM wb_structures s JOIN wb_areas a ON s.area_id=a.area_id WHERE a.area_code='MER_PLANT' ORDER BY s.structure_code"):
    print(row)

print('\n=== Outflow destinations for STP losses (all areas) ===')
for row in c.execute("SELECT a.area_code, s.structure_code, d.destination_code, d.destination_name FROM wb_outflow_destinations d JOIN wb_structures s ON d.source_structure_id=s.structure_id LEFT JOIN wb_areas a ON s.area_id=a.area_id WHERE d.destination_type='losses' AND s.structure_code LIKE '%STP%' ORDER BY a.area_code"):
    print(row)

print('\n=== Product_bound (water in concentrate) outflows ===')
for row in c.execute("SELECT a.area_code, s.structure_code, d.destination_code, d.destination_name FROM wb_outflow_destinations d JOIN wb_structures s ON d.source_structure_id=s.structure_id LEFT JOIN wb_areas a ON s.area_id=a.area_id WHERE d.destination_type='product_bound' ORDER BY a.area_code"):
    print(row)

conn.close()
