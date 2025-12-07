import sqlite3

conn = sqlite3.connect('data/water_balance.db')
cursor = conn.cursor()

# Get structure IDs for OT_NEW_TSF and OT_OLD_TSF
print("=== GETTING TSF STRUCTURE IDs ===")
cursor.execute('''
    SELECT structure_id, structure_code, structure_name 
    FROM wb_structures 
    WHERE structure_code IN ('OT_NEW_TSF', 'OT_OLD_TSF')
''')
structures = cursor.fetchall()
struct_map = {row[1]: row[0] for row in structures}
print(f"Structures found: {struct_map}")

# Define TSF seepage and interstitial outflows
tsf_outflows = [
    (struct_map.get('OT_NEW_TSF'), 'OT_NEW_TSF_seepage', 'seepage', 'New TSF Seepage'),
    (struct_map.get('OT_NEW_TSF'), 'OT_NEW_TSF_interstitial', 'interstitial', 'New TSF Interstitial Storage'),
    (struct_map.get('OT_OLD_TSF'), 'OT_OLD_TSF_seepage', 'seepage', 'Old TSF Seepage'),
    (struct_map.get('OT_OLD_TSF'), 'OT_OLD_TSF_interstitial', 'interstitial', 'Old TSF Interstitial Storage'),
]

print("\n=== ADDING TSF SEEPAGE/INTERSTITIAL ENTRIES ===")
for source_id, dest_code, dest_type, dest_name in tsf_outflows:
    if source_id:
        cursor.execute('''
            INSERT INTO wb_outflow_destinations (source_structure_id, destination_code, destination_type, destination_name)
            VALUES (?, ?, ?, ?)
        ''', (source_id, dest_code, dest_type, dest_name))
        print(f"✓ Added: {dest_code} ({dest_type}) - {dest_name}")
    else:
        print(f"✗ Skipped: {dest_code} - Structure not found")

conn.commit()
print("\n=== DATABASE UPDATED ===")
conn.close()
