import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('=== MINE AREAS ===')
cur.execute('SELECT * FROM mine_areas ORDER BY area_code')
for row in cur.fetchall():
    print(f"{row['area_code']}: {row['area_name']}")

print('\n=== STORAGE FACILITIES (ALL) ===')
cur.execute('SELECT facility_code, facility_name, facility_type, purpose, water_quality, area_id FROM storage_facilities ORDER BY area_id')
for row in cur.fetchall():
    print(f"{row['facility_code']}: {row['facility_name']} ({row['facility_type']}) - purpose:{row['purpose']} quality:{row['water_quality']} area:{row['area_id']}")

print('\n=== WATER SOURCES (sample 30) ===')
cur.execute('SELECT source_code, source_name, type_id, area_id FROM water_sources LIMIT 30')
for row in cur.fetchall():
    print(f"{row['source_code']}: {row['source_name']} (type:{row['type_id']}) area:{row['area_id']}")

print('\n=== WATER SOURCE TYPES ===')
cur.execute('SELECT type_id, type_code, type_name FROM water_source_types')
for row in cur.fetchall():
    print(f"{row['type_code']}: {row['type_name']}")

conn.close()
