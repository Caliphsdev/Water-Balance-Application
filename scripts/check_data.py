"""Check database data for environmental and storage tables."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import DatabaseManager

db = DatabaseManager()
conn = db.get_connection()

# Check environmental_data
cursor = conn.execute('SELECT year, month, rainfall_mm, evaporation_mm FROM environmental_data ORDER BY year, month LIMIT 10')
rows = cursor.fetchall()
print('Environmental Data (first 10):')
for r in rows:
    print(f"  {r['year']}-{r['month']:02d}: rainfall={r['rainfall_mm']}, evap={r['evaporation_mm']}")

# Check storage facilities
cursor = conn.execute('SELECT code, status, current_volume_m3, surface_area_m2 FROM storage_facilities LIMIT 5')
rows = cursor.fetchall()
print('\nStorage Facilities (first 5):')
for r in rows:
    print(f"  {r['code']}: status={r['status']}, volume={r['current_volume_m3']}, area={r['surface_area_m2']}")

conn.close()
