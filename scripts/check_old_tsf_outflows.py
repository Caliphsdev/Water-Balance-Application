import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Show ALL OLD_TSF outflow destinations
print("=== ALL OLD_TSF OUTFLOW DESTINATIONS ===")
cursor.execute('''
    SELECT DISTINCT od.destination_code, od.destination_type, s.structure_code, s.structure_name, a.area_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF'
    ORDER BY od.destination_type
''')
all_ot = cursor.fetchall()
for row in all_ot:
    print(f"  {row[0]:30} ({row[1]:15}) - {row[2]:15}")

# Check specifically for dust
print("\n=== OLD_TSF DUST SUPPRESSION ===")
cursor.execute('''
    SELECT COUNT(*) as count FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF' AND od.destination_type = 'dust'
''')
dust_count = cursor.fetchone()[0]
print(f"Dust entries: {dust_count}")

# Check for spill
print("\n=== OLD_TSF SPILLAGE ===")
cursor.execute('''
    SELECT COUNT(*) as count FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF' AND od.destination_type = 'spill'
''')
spill_count = cursor.fetchone()[0]
print(f"Spill entries: {spill_count}")

# Check for interstitial
print("\n=== OLD_TSF INTERSTITIAL STORAGE ===")
cursor.execute('''
    SELECT DISTINCT od.destination_code, od.destination_type, od.destination_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'OLD_TSF' AND od.destination_type LIKE '%interstitial%'
''')
interstitial = cursor.fetchall()
print(f"Interstitial entries: {len(interstitial)}")
for row in interstitial:
    print(f"  {row[0]:30} ({row[1]:15}) - {row[2]}")

conn.close()
