"""Quick script to check database schema for calculation service."""
import sqlite3

conn = sqlite3.connect('data/water_balance.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [t[0] for t in cursor.fetchall()]
print("=== TABLES ===")
for t in tables:
    print(f"  - {t}")

# Show storage_facilities schema
print("\n=== STORAGE_FACILITIES COLUMNS ===")
cursor.execute("PRAGMA table_info(storage_facilities)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

# Check if facility_monthly_parameters exists
if 'facility_monthly_parameters' in tables:
    print("\n=== FACILITY_MONTHLY_PARAMETERS COLUMNS ===")
    cursor.execute("PRAGMA table_info(facility_monthly_parameters)")
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]}")
else:
    print("\n[!] facility_monthly_parameters table NOT FOUND")

# Check for monthly_parameters (alternative name)
if 'monthly_parameters' in tables:
    print("\n=== MONTHLY_PARAMETERS COLUMNS ===")
    cursor.execute("PRAGMA table_info(monthly_parameters)")
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]}")

conn.close()
