"""Activate all storage facilities so they contribute to rainfall calculations."""
from pathlib import Path
import sys

sys.path.insert(0, str((Path(__file__).parent.parent / 'src').resolve()))

from database.db_manager import db

# Get all facilities before update
all_facilities = db.get_storage_facilities(active_only=False, use_cache=False)

print("\n=== ACTIVATING ALL STORAGE FACILITIES ===\n")

inactive_facilities = [f for f in all_facilities if f.get('active', 0) == 0]

if inactive_facilities:
    # Update all inactive facilities to active using SQL
    query = "UPDATE storage_facilities SET active = 1, updated_at = CURRENT_TIMESTAMP WHERE active = 0"
    db.execute_update(query)
    
    for f in inactive_facilities:
        code = f.get('facility_code', 'N/A')
        name = f.get('facility_name', 'N/A')
        print(f"ACTIVATED: {code:10} {name}")
else:
    print("All facilities already active!")

print(f"\n{'='*80}")
print(f"Total facilities activated: {len(inactive_facilities)}")

# Clear cache and verify
db._invalidate_facilities_cache()
active_facilities = db.get_storage_facilities(active_only=True, use_cache=False)
total_area = sum(f.get('surface_area', 0) or 0 for f in active_facilities)

print(f"Active facilities after update: {len(active_facilities)}")
print(f"Total active surface area: {total_area:,.0f} m2")
print(f"Expected rainfall (45.2mm): {(45.2/1000)*total_area:,.2f} m3")
print("\nDONE! Restart the application to see the updated rainfall calculation.")
