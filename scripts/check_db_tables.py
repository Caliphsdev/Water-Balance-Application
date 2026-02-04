"""Check database tables and storage_history status."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row

# List all tables
print("=" * 60)
print("DATABASE TABLES")
print("=" * 60)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
for t in tables:
    print(f"  - {t}")

# Check storage_history
print()
print("=" * 60)
print("STORAGE_HISTORY TABLE")
print("=" * 60)

if 'storage_history' in tables:
    print("Status: EXISTS")
    print()
    print("Schema:")
    cursor = conn.execute("PRAGMA table_info(storage_history)")
    for col in cursor.fetchall():
        print(f"  {col['name']} ({col['type']})")
    print()
    print("Records:")
    cursor = conn.execute("SELECT COUNT(*) as cnt FROM storage_history")
    print(f"  {cursor.fetchone()['cnt']} records")
    
    # Show sample
    cursor = conn.execute("SELECT * FROM storage_history LIMIT 5")
    rows = cursor.fetchall()
    if rows:
        print()
        print("Sample data:")
        for row in rows:
            print(f"  {row['facility_code']} {row['year']}/{row['month']:02d}: "
                  f"open={row['opening_volume_m3']:,.0f}, close={row['closing_volume_m3']:,.0f}")
else:
    print("Status: DOES NOT EXIST")
    print()
    print("Creating table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS storage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_code TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            opening_volume_m3 REAL NOT NULL DEFAULT 0,
            closing_volume_m3 REAL NOT NULL DEFAULT 0,
            data_source TEXT DEFAULT 'calculated',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(facility_code, year, month)
        )
    """)
    conn.commit()
    print("Table created successfully!")

conn.close()
