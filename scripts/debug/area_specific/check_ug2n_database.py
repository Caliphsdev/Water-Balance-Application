"""Check all UG2N connections in database vs JSON diagram."""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.db_manager import DatabaseManager

# Check database for ALL UG2N flows
db = DatabaseManager()
query = '''
SELECT 
    fs.structure_code as from_code,
    fs.structure_name as from_name,
    ts.structure_code as to_code,
    ts.structure_name as to_name
FROM wb_flow_connections fc
JOIN wb_structures fs ON fc.from_structure_id = fs.structure_id
JOIN wb_structures ts ON fc.to_structure_id = ts.structure_id
WHERE fs.structure_code LIKE 'UG2N%' OR ts.structure_code LIKE 'UG2N%'
ORDER BY from_code, to_code
'''

connections = db.execute_query(query)
print(f'DATABASE: UG2N Connections ({len(connections)} total)')
print('=' * 80)
db_connections = set()
for c in connections:
    from_code = c.get("from_code")
    to_code = c.get("to_code")
    db_connections.add(f'{from_code}__TO__{to_code}')
    print(f'{from_code:15} -> {to_code:15}')

# Check JSON diagram
json_path = Path(__file__).parent / 'data' / 'diagrams' / 'UG2_NORTH_flow_diagram.json'
if json_path.exists():
    print(f'\nJSON DIAGRAM: {json_path}')
    print('=' * 80)
    with open(json_path) as f:
        diagram = json.load(f)
    
    json_edges = set()
    for edge in diagram.get('edges', []):
        from_node = edge.get('from')
        to_node = edge.get('to')
        json_edges.add(f'{from_node}__TO__{to_node}')
        print(f'{from_node:15} -> {to_node:15}')
    
    print(f'\nCOMPARISON:')
    print('=' * 80)
    print(f'Database connections: {len(db_connections)}')
    print(f'JSON diagram edges: {len(json_edges)}')
    
    # Find differences
    only_in_db = db_connections - json_edges
    only_in_json = json_edges - db_connections
    
    if only_in_db:
        print(f'\n✅ In Database but NOT in JSON:')
        for conn in sorted(only_in_db):
            print(f'   {conn}')
    
    if only_in_json:
        print(f'\n❌ In JSON but NOT in Database:')
        for conn in sorted(only_in_json):
            print(f'   {conn}')
    
    if not only_in_db and not only_in_json:
        print(f'\n✅ Perfect match - Database and JSON are in sync!')
else:
    print(f'⚠️ JSON diagram not found: {json_path}')
