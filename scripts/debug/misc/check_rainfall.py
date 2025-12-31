#!/usr/bin/env python
"""Check rainfall inflows for Stockpile Area"""
from src.database.db_manager import DatabaseManager

db = DatabaseManager()

# Get all inflows for Stockpile structures
query = '''
SELECT DISTINCT
    s.structure_code,
    s.structure_name,
    w.source_type,
    w.source_code,
    w.source_name
FROM wb_inflow_sources w
JOIN wb_structures s ON w.target_structure_id = s.structure_id
WHERE s.structure_code LIKE "STP_%"
ORDER BY s.structure_code, w.source_type, w.source_code
'''
results = db.execute_query(query)

print('=== All Inflows for Stockpile Area Structures ===\n')
for row in results:
    code = row.get('structure_code') or row[0]
    name = row.get('structure_name') or row[1]
    source_type = row.get('source_type') or row[2]
    source_code = row.get('source_code') or row[3]
    source_name = row.get('source_name') or row[4]
    print(f'{code:20} | {source_type:15} | {source_code:25} | {source_name}')

rainfall_count = len([r for r in results if (r.get('source_type') or r[2]) == 'rainfall'])
print(f'\nTotal rainfall inflows: {rainfall_count}')
