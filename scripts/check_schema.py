import sqlite3

conn = sqlite3.connect('data/water_balance.db')
cursor = conn.cursor()

# Check wb_outflow_destinations columns
print("=== wb_outflow_destinations SCHEMA ===")
cursor.execute("PRAGMA table_info(wb_outflow_destinations)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]:20} {col[2]}")

conn.close()
