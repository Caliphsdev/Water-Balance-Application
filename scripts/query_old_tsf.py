import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import db
import json

# Query for Old TSF structures - try looking for OLD_TSF explicitly
structures = db.execute_query("""
    SELECT structure_id, structure_name, area_id, structure_type 
    FROM wb_structures 
    WHERE structure_id = 'OLD_TSF'
       OR structure_name LIKE '%Old TSF%'
       OR area_id LIKE '%OLD_TSF%'
    ORDER BY structure_id
""")

print(f'Found {len(structures)} structures for OLD_TSF')
print(json.dumps(structures, indent=2))

# Check all structures to see area_id values
print('\n--- Checking all area_id values ---')
all_areas = db.execute_query("""
    SELECT DISTINCT area_id FROM wb_structures ORDER BY area_id
""")
print('All area_ids:', [a['area_id'] for a in all_areas])

# Check inflow sources for OLD_TSF
inflows = db.execute_query("""
    SELECT i.inflow_id, i.source_code, i.source_name, s.structure_id, s.area_id
    FROM wb_inflow_sources i
    JOIN wb_structures s ON i.target_structure_id = s.structure_id
    WHERE s.structure_id = 'OLD_TSF' 
       OR s.area_id LIKE '%OLD_TSF%'
       OR i.source_name LIKE '%Old TSF%'
    ORDER BY i.source_code
""")

print(f'\nFound {len(inflows)} inflow sources for OLD_TSF')
print(json.dumps(inflows, indent=2))

# Check outflow destinations for OLD_TSF
outflows = db.execute_query("""
    SELECT o.outflow_id, o.destination_code, o.destination_name, s.structure_id, s.area_id
    FROM wb_outflow_destinations o
    JOIN wb_structures s ON o.source_structure_id = s.structure_id
    WHERE s.structure_id = 'OLD_TSF'
       OR s.area_id LIKE '%OLD_TSF%'
       OR o.destination_name LIKE '%Old TSF%'
    ORDER BY o.destination_code
""")

print(f'\nFound {len(outflows)} outflow destinations from OLD_TSF')
print(json.dumps(outflows, indent=2))
