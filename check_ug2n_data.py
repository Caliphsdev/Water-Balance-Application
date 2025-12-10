import sqlite3
from pathlib import Path

db_path = 'data/water_balance.db'
if Path(db_path).exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get UG2N structures with correct columns
    print('=== UG2N AREA STRUCTURES ===')
    cursor.execute("""
        SELECT structure_id, structure_code, structure_name, structure_type, area_id
        FROM wb_structures
        WHERE area_id IN (
            SELECT area_id FROM wb_areas WHERE area_code LIKE '%UG2%'
        )
        ORDER BY structure_code
    """)
    
    structures = cursor.fetchall()
    print(f'Found {len(structures)} structures:')
    struct_map = {}
    for s in structures:
        struct_map[s[0]] = s[1]
        print(f'  {s[1]}: {s[2]} ({s[3]})')
    
    # Get connections for these structures
    print('\n\n=== CONNECTIONS ===')
    structure_ids = [s[0] for s in structures]
    if structure_ids:
        placeholders = ','.join('?' * len(structure_ids))
        cursor.execute(f"""
            SELECT c.connection_id, c.from_structure_id, c.to_structure_id, 
                   c.flow_type, c.subcategory, c.is_bidirectional
            FROM wb_flow_connections c
            WHERE c.from_structure_id IN ({placeholders}) OR c.to_structure_id IN ({placeholders})
            ORDER BY c.from_structure_id, c.to_structure_id
        """, structure_ids + structure_ids)
        
        connections = cursor.fetchall()
        print(f'Found {len(connections)} connections:')
        for conn_row in connections:
            from_code = struct_map.get(conn_row[1], f"ID:{conn_row[1]}")
            to_code = struct_map.get(conn_row[2], f"ID:{conn_row[2]}")
            bidirectional = " <->" if conn_row[5] else " ->"
            print(f'  {from_code} {bidirectional} {to_code} ({conn_row[3]}/{conn_row[4]})')
    
    conn.close()
else:
    print('Database not found')
