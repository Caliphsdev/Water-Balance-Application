import sqlite3

conn = sqlite3.connect('data/water_balance.db')
cursor = conn.cursor()

# First, get the structure IDs for TRTD and NT RWD
print("=== GETTING STRUCTURE IDs ===")
cursor.execute('''
    SELECT structure_id, structure_code, structure_name 
    FROM wb_structures 
    WHERE structure_code IN ('OT_TRTD', 'OT_NT_RWD')
''')
structures = cursor.fetchall()
struct_map = {row[1]: row[0] for row in structures}
print(f"Structures found: {struct_map}")

# Define new outflow destinations to add
outflows_to_add = [
    # TRTD spill, seepage, interstitial
    (struct_map.get('OT_TRTD'), 'OT_TRTD_spill', 'spill', 'TRTD 1-2 Spillage'),
    (struct_map.get('OT_TRTD'), 'OT_TRTD_seepage', 'seepage', 'TRTD 1-2 Seepage'),
    (struct_map.get('OT_TRTD'), 'OT_TRTD_interstitial', 'interstitial', 'TRTD 1-2 Interstitial Storage'),
    
    # NT RWD spill, seepage, interstitial
    (struct_map.get('OT_NT_RWD'), 'OT_NT_RWD_spill', 'spill', 'NT RWD 1-2 Spillage'),
    (struct_map.get('OT_NT_RWD'), 'OT_NT_RWD_seepage', 'seepage', 'NT RWD 1-2 Seepage'),
    (struct_map.get('OT_NT_RWD'), 'OT_NT_RWD_interstitial', 'interstitial', 'NT RWD 1-2 Interstitial Storage'),
]

print("\n=== ADDING OUTFLOW DESTINATIONS ===")
for source_id, dest_code, dest_type, dest_name in outflows_to_add:
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
