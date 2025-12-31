#!/usr/bin/env python3
"""Check UG2 South Decline Area structures in database."""
import sqlite3
from pathlib import Path

db_path = Path('data/water_balance.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all structures in UG2 South Decline Area
cur.execute('''
    SELECT s.structure_id, s.structure_code, s.structure_name, s.structure_type
    FROM wb_structures s
    JOIN wb_areas a ON s.area_id = a.area_id
    WHERE a.area_code = 'UG2S'
    ORDER BY s.structure_code
''')

print('=== UG2 South Decline Area Structures ===')
structures = cur.fetchall()
for sid, code, name, stype in structures:
    print(f'\n{code:15} | {name:30} | {stype}')
    
    # Get inflows
    cur.execute('''
        SELECT source_type, source_code, source_name
        FROM wb_inflow_sources
        WHERE target_structure_id = ?
    ''', (sid,))
    inflows = cur.fetchall()
    if inflows:
        for itype, icode, iname in inflows:
            print(f'  ← {itype:15} | {icode:20} | {iname}')
    
    # Get outflows
    cur.execute('''
        SELECT destination_type, dest_code, dest_name
        FROM wb_outflow_destinations
        WHERE source_structure_id = ?
    ''', (sid,))
    outflows = cur.fetchall()
    if outflows:
        for otype, ocode, oname in outflows:
            print(f'  → {otype:15} | {ocode:20} | {oname}')

conn.close()
