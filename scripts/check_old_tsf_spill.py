import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check for spill on specific OLD_TSF dams
print("=== OLD_TSF DAM SPILL ENTRIES ===")
cursor.execute('''
    SELECT od.destination_code, od.destination_type, od.destination_name, s.structure_code, s.structure_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF' AND od.destination_type = 'spill'
    ORDER BY s.structure_code
''')
spill_rows = cursor.fetchall()
print(f"Spill entries found: {len(spill_rows)}")
for row in spill_rows:
    print(f"  {row['destination_code']:30} ({row['destination_type']}) - {row['structure_code']} ({row['structure_name']})")

# Check for seepage
print("\n=== OLD_TSF SEEPAGE ENTRIES ===")
cursor.execute('''
    SELECT od.destination_code, od.destination_type, od.destination_name, s.structure_code, s.structure_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF' AND od.destination_type = 'seepage'
    ORDER BY s.structure_code
''')
seepage_rows = cursor.fetchall()
print(f"Seepage entries found: {len(seepage_rows)}")
for row in seepage_rows:
    print(f"  {row['destination_code']:30} ({row['destination_type']}) - {row['structure_code']} ({row['structure_name']})")

# Check for interstitial
print("\n=== OLD_TSF INTERSTITIAL ENTRIES ===")
cursor.execute('''
    SELECT od.destination_code, od.destination_type, od.destination_name, s.structure_code, s.structure_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF' AND od.destination_type LIKE '%interstitial%'
    ORDER BY s.structure_code
''')
interstitial_rows = cursor.fetchall()
print(f"Interstitial entries found: {len(interstitial_rows)}")
for row in interstitial_rows:
    print(f"  {row['destination_code']:30} ({row['destination_type']}) - {row['structure_code']} ({row['structure_name']})")

# Show ALL OLD_TSF entries by destination type
print("\n=== ALL OLD_TSF DESTINATION TYPES ===")
cursor.execute('''
    SELECT DISTINCT od.destination_type, COUNT(*) as count
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF'
    GROUP BY od.destination_type
    ORDER BY od.destination_type
''')
type_rows = cursor.fetchall()
for row in type_rows:
    print(f"  {row['destination_type']:20} : {row['count']} entries")

conn.close()
