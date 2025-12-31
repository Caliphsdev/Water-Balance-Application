import sqlite3
from pathlib import Path

db_path = 'data/water_balance.db'
if Path(db_path).exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check available tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print('Available tables:')
    for table in tables:
        print(f'  - {table[0]}')
    
    # Check water_sources structure
    cursor.execute("PRAGMA table_info(water_sources)")
    cols = cursor.fetchall()
    print('\nWater Sources columns:')
    for col in cols:
        print(f'  {col[1]}: {col[2]}')
    
    # Check storage_facilities structure  
    cursor.execute("PRAGMA table_info(storage_facilities)")
    cols = cursor.fetchall()
    print('\nStorage Facilities columns:')
    for col in cols[:20]:
        print(f'  {col[1]}: {col[2]}')
    
    # Check if there are any records
    cursor.execute("SELECT COUNT(*) FROM water_sources")
    print(f'\nWater sources count: {cursor.fetchone()[0]}')
    
    cursor.execute("SELECT COUNT(*) FROM storage_facilities")
    print(f'Storage facilities count: {cursor.fetchone()[0]}')
    
    if cursor.execute("SELECT COUNT(*) FROM water_sources").fetchone()[0] > 0:
        cursor.execute("SELECT source_code, source_name, area_id FROM water_sources LIMIT 5")
        print('\nSample sources:')
        for row in cursor.fetchall():
            print(f'  {row}')
    
    conn.close()
else:
    print('Database not found')
