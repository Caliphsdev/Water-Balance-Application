import sqlite3
from pathlib import Path

db_path = 'data/water_balance.db'
if Path(db_path).exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check flow connection tables
    for table_name in ['wb_flow_connections', 'wb_inflow_sources', 'wb_outflow_destinations', 'wb_areas']:
        print(f'\n{table_name} columns:')
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        for col in cols:
            print(f'  {col[1]}: {col[2]}')
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f'  Records: {count}')
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            print(f'  Sample:')
            for row in cursor.fetchall():
                print(f'    {row[:8]}...')
    
    # Check UG2N area specifically
    print('\n\n=== UG2N AREA DATA ===')
    cursor.execute("SELECT * FROM wb_areas WHERE area_code = 'UG2N'")
    area = cursor.fetchone()
    if area:
        print(f'Area: {area}')
        
        # Get flows for UG2N
        cursor.execute("SELECT * FROM wb_flow_connections WHERE source_area = 'UG2N' OR dest_area = 'UG2N' LIMIT 10")
        flows = cursor.fetchall()
        print(f'\nFlows for UG2N (count: {len(flows)}):')
        for flow in flows:
            print(f'  {flow[:10]}')
    
    conn.close()
else:
    print('Database not found')
