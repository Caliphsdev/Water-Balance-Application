import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check SPCD1 structure details
print("=== SPCD1 STRUCTURE DETAILS ===")
cursor.execute('''
    SELECT s.structure_id, s.structure_code, s.structure_name, s.structure_type, a.area_name
    FROM wb_structures s
    LEFT JOIN wb_areas a ON s.area_id = a.area_id
    WHERE s.structure_code = 'STP_SPCD1'
''')
spcd1 = cursor.fetchone()
if spcd1:
    print(f"  Code: {spcd1['structure_code']}")
    print(f"  Name: {spcd1['structure_name']}")
    print(f"  Type: {spcd1['structure_type']}")
    print(f"  Area: {spcd1['area_name']}")
else:
    print("  SPCD1 not found")

# Check all structures in Stockpile area
print("\n=== ALL STRUCTURES IN STOCKPILE AREA ===")
cursor.execute('''
    SELECT s.structure_code, s.structure_name, s.structure_type
    FROM wb_structures s
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name = 'STOCKPILE'
    ORDER BY s.structure_code
''')
stockpile_structs = cursor.fetchall()
print(f"Found {len(stockpile_structs)} structures:")
for row in stockpile_structs:
    print(f"  {row['structure_code']:15} ({row['structure_type']:15}) - {row['structure_name']}")

# Check SPCD1 outflows
print("\n=== SPCD1 OUTFLOW DESTINATIONS ===")
cursor.execute('''
    SELECT od.destination_code, od.destination_type, od.destination_name
    FROM wb_outflow_destinations od
    JOIN wb_structures s ON od.source_structure_id = s.structure_id
    WHERE s.structure_code = 'STP_SPCD1'
''')
spcd1_outflows = cursor.fetchall()
for row in spcd1_outflows:
    print(f"  {row['destination_code']:30} ({row['destination_type']})")

conn.close()
