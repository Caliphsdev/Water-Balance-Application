import sqlite3

conn = sqlite3.connect('data/water_balance.db')
cursor = conn.cursor()

# Remove the incorrect seepage and interstitial entries from dams
print("=== REMOVING SEEPAGE/INTERSTITIAL FROM DAMS ===")

entries_to_remove = [
    'OT_TRTD_seepage',
    'OT_TRTD_interstitial',
    'OT_NT_RWD_seepage',
    'OT_NT_RWD_interstitial'
]

for dest_code in entries_to_remove:
    cursor.execute('DELETE FROM wb_outflow_destinations WHERE destination_code = ?', (dest_code,))
    print(f"✓ Removed: {dest_code}")

conn.commit()
print("\n=== DATABASE UPDATED ===")
conn.close()
