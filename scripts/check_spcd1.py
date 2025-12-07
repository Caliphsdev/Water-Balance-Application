import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check Stockpile area structures
print("=== STOCKPILE AREA STRUCTURES ===")
cursor.execute('''
    SELECT s.structure_id, s.structure_code, s.structure_name, s.structure_type
    FROM wb_structures s
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'STOCKPILE'
    ORDER BY s.structure_code
''')
structures = cursor.fetchall()
for row in structures:
    print(f"  {row['structure_code']:15} ({row['structure_type']:15}) - {row['structure_name']}")

# Check if SPCD1 has evaporation in calculations or elsewhere
print("\n=== SPCD1 EVAPORATION IN DATABASE ===")
cursor.execute('''
    SELECT DISTINCT od.destination_code, od.destination_type, od.destination_name, s.structure_code
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    WHERE s.structure_code = 'STP_SPCD1'
''')
spcd1_rows = cursor.fetchall()
print(f"SPCD1 outflows found: {len(spcd1_rows)}")
for row in spcd1_rows:
    print(f"  {row['destination_code']:30} ({row['destination_type']})")

# Check calculations table for evaporation
print("\n=== CALCULATIONS TABLE - EVAPORATION ===")
cursor.execute('''
    SELECT DISTINCT c.area_id, a.area_name, c.evaporation_mm, c.dam_surface_area
    FROM calculations c
    JOIN wb_areas a ON c.area_id = a.area_id
    WHERE a.area_name = 'STOCKPILE'
''')
calc_rows = cursor.fetchall()
for row in calc_rows:
    print(f"  Area: {row['area_name']}, Evap MM: {row['evaporation_mm']}, Surface: {row['dam_surface_area']}")

conn.close()
