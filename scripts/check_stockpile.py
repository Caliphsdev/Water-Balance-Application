import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check for STP_SEPTIC_effluent
print("=== CHECKING STP_SEPTIC_effluent ===")
cursor.execute('''
    SELECT DISTINCT od.destination_code, od.destination_type, od.destination_name
    FROM wb_outflow_destinations od
    WHERE od.destination_code LIKE '%STP_SEPTIC%' OR od.destination_code LIKE '%SEPTIC_effluent%'
''')
rows = cursor.fetchall()
print(f"STP_SEPTIC entries found: {len(rows)}")
for row in rows:
    print(f"  {row[0]:30} ({row[1]:15}) - {row[2]}")

# Check for STOCKPILE evaporation
print("\n=== CHECKING STOCKPILE EVAPORATION ===")
cursor.execute('''
    SELECT DISTINCT od.destination_code, od.destination_type, s.structure_code, s.structure_name, a.area_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'STOCKPILE' AND od.destination_type = 'evaporation'
''')
evap_rows = cursor.fetchall()
print(f"Stockpile evaporation entries: {len(evap_rows)}")
for row in evap_rows:
    print(f"  {row[0]:30} ({row[1]:15}) - {row[2]} ({row[3]})")

# Show ALL STOCKPILE outflow destinations
print("\n=== ALL STOCKPILE OUTFLOW DESTINATIONS ===")
cursor.execute('''
    SELECT DISTINCT od.destination_code, od.destination_type, s.structure_code, s.structure_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'STOCKPILE'
    ORDER BY od.destination_type
''')
all_stp = cursor.fetchall()
for row in all_stp:
    print(f"  {row[0]:30} ({row[1]:15}) - {row[2]}")

conn.close()
