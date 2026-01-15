import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3

conn = sqlite3.connect('data/water_balance.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find Drought_2026 scenario
cur.execute("SELECT scenario_id, name FROM scenarios WHERE name = 'Drought_2026'")
scenario = cur.fetchone()
if scenario:
    sid = scenario['scenario_id']
    print(f'[SCENARIO] Found Drought_2026 with ID: {sid}\n')
    
    # Check inflow adjustments
    cur.execute('SELECT * FROM scenario_inflow_adjustments WHERE scenario_id = ?', (sid,))
    inflows = cur.fetchall()
    print(f'[INFLOWS] Count: {len(inflows)}')
    for inf in inflows:
        print(f'  {dict(inf)}')
    
    print()
    
    # Check outflow adjustments
    cur.execute('SELECT * FROM scenario_outflow_adjustments WHERE scenario_id = ?', (sid,))
    outflows = cur.fetchall()
    print(f'[OUTFLOWS] Count: {len(outflows)}')
    for out in outflows:
        print(f'  {dict(out)}')
    
    print()
    
    # Check environmental adjustments
    cur.execute('SELECT * FROM scenario_environmental_adjustments WHERE scenario_id = ?', (sid,))
    envs = cur.fetchall()
    print(f'[ENVIRONMENTAL] Count: {len(envs)}')
    for env in envs:
        print(f'  {dict(env)}')
else:
    print('Drought_2026 scenario not found')
    print('Available scenarios:')
    cur.execute('SELECT scenario_id, name FROM scenarios')
    for row in cur.fetchall():
        print(f'  ID {row[0]}: {row[1]}')

conn.close()
