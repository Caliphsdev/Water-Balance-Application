"""
Extract real connections from database and regenerate Excel with actual flows.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.db_manager import DatabaseManager

db = DatabaseManager()

# Get all structures
query = 'SELECT structure_id, structure_name, structure_code FROM wb_structures ORDER BY structure_code'
structures = db.execute_query(query)
print('=== STRUCTURES ===')
for s in structures[:20]:
    struct_code = s.get('structure_code') or s[2]
    struct_name = s.get('structure_name') or s[1]
    print(f'{struct_code}: {struct_name}')

print(f'\nTotal structures: {len(structures)}\n')

# Get all connections
query = '''
SELECT 
    fs.structure_code as from_code,
    fs.structure_name as from_name,
    ts.structure_code as to_code,
    ts.structure_name as to_name
FROM wb_flow_connections fc
JOIN wb_structures fs ON fc.from_structure_id = fs.structure_id
JOIN wb_structures ts ON fc.to_structure_id = ts.structure_id
ORDER BY from_code, to_code
'''
connections = db.execute_query(query)
print(f'=== CONNECTIONS ({len(connections)} total) ===')
for c in connections:
    from_code = c.get('from_code') or c[0]
    from_name = c.get('from_name') or c[1]
    to_code = c.get('to_code') or c[2]
    to_name = c.get('to_name') or c[3]
    print(f'{from_code:12} -> {to_code:12} ({from_name:30} -> {to_name})')
