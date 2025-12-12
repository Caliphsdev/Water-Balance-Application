import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import db
import json

# Get all structures in area_id 5 (OLD_TSF area)
print("=" * 60)
print("STRUCTURES IN OLD TSF AREA (area_id=5)")
print("=" * 60)
structures = db.execute_query("""
    SELECT structure_id, structure_code, structure_name, structure_type 
    FROM wb_structures 
    WHERE area_id = 5
    ORDER BY structure_id
""")
print(f'Found {len(structures)} structures')
for s in structures:
    print(f"  {s['structure_id']:3d} | {s['structure_code']:20s} | {s['structure_name']:40s} | {s['structure_type']}")

# Get all inflow sources for OLD_TSF area structures
print("\n" + "=" * 60)
print("INFLOW SOURCES TO OLD TSF AREA")
print("=" * 60)
inflows = db.execute_query("""
    SELECT i.inflow_id, i.source_code, i.source_name, i.source_type, s.structure_name
    FROM wb_inflow_sources i
    JOIN wb_structures s ON i.target_structure_id = s.structure_id
    WHERE s.area_id = 5
    ORDER BY i.source_code
""")
print(f'Found {len(inflows)} inflow sources')
for inf in inflows:
    print(f"  {inf['source_code']:30s} | {inf['source_name']:40s} | Type: {inf['source_type']:10s} | To: {inf['structure_name']}")

# Get all outflow destinations from OLD_TSF area structures
print("\n" + "=" * 60)
print("OUTFLOW DESTINATIONS FROM OLD TSF AREA")
print("=" * 60)
outflows = db.execute_query("""
    SELECT o.outflow_id, o.destination_code, o.destination_name, s.structure_name as from_structure
    FROM wb_outflow_destinations o
    JOIN wb_structures s ON o.source_structure_id = s.structure_id
    WHERE s.area_id = 5
    ORDER BY o.destination_code
""")
print(f'Found {len(outflows)} outflow destinations')
for out in outflows:
    print(f"  {out['destination_code']:30s} | {out['destination_name']:40s} | From: {out['from_structure']}")

# Check for TRTD and NT RWD structures (might be in different area or need searching)
print("\n" + "=" * 60)
print("SEARCHING FOR TRTD AND NEW TSF COMPONENTS")
print("=" * 60)
trtd_search = db.execute_query("""
    SELECT structure_id, structure_code, structure_name, structure_type, area_id
    FROM wb_structures 
    WHERE structure_code LIKE '%TRTD%' 
       OR structure_name LIKE '%TRTD%'
       OR structure_code LIKE '%NT_%'
       OR structure_name LIKE '%New Tailings%'
       OR structure_name LIKE '%NEW TSF%'
    ORDER BY structure_id
""")
print(f'Found {len(trtd_search)} related structures')
for s in trtd_search:
    print(f"  {s['structure_id']:3d} | Area: {s['area_id']} | {s['structure_code']:20s} | {s['structure_name']}")
