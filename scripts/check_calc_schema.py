import sqlite3

conn = sqlite3.connect('data/water_balance.db')
cursor = conn.cursor()

# Check calculations table schema
print("=== CALCULATIONS TABLE SCHEMA ===")
cursor.execute("PRAGMA table_info(calculations)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]:25} {col[2]}")

conn.close()
