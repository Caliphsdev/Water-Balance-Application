import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check all structures where area_name is Stockpile Area
print("=== STOCKPILE AREA - ALL STRUCTURES ===")
cursor.execute('''
    SELECT s.structure_id, s.structure_code, s.structure_name, s.structure_type, a.area_id, a.area_name
    FROM wb_structures s
    LEFT JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_name LIKE '%Stockpile%' OR a.area_name = 'STOCKPILE'
    ORDER BY s.structure_code
''')
rows = cursor.fetchall()
print(f"Found {len(rows)} structures:")
for row in rows:
    print(f"  ID: {row['structure_id']:3} | {row['structure_code']:15} | {row['structure_name']:25} | {row['structure_type']:15} | Area: {row['area_name']}")

# Check by area_id
print("\n=== CHECKING STOCKPILE AREA DETAILS ===")
cursor.execute('''
    SELECT area_id, area_name, area_code
    FROM wb_areas
    WHERE area_name LIKE '%Stockpile%' OR area_code LIKE '%STP%'
''')
areas = cursor.fetchall()
for area in areas:
    print(f"  Area ID: {area['area_id']} | {area['area_name']} ({area['area_code']})")
    
    # Get structures for this area
    cursor.execute('''
        SELECT structure_code, structure_name, structure_type
        FROM wb_structures
        WHERE area_id = ?
        ORDER BY structure_code
    ''', (area['area_id'],))
    structs = cursor.fetchall()
    print(f"    Structures in this area ({len(structs)}):")
    for struct in structs:
        print(f"      {struct['structure_code']:15} ({struct['structure_type']:15}) - {struct['structure_name']}")

conn.close()
