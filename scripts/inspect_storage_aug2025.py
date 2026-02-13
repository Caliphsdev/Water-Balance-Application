import sys
from pathlib import Path
import json
# ensure src on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from database.db_manager import DatabaseManager
from services.calculation.balance_service import get_balance_service

svc = get_balance_service()
res = svc.calculate_for_date(8, 2025, force_recalculate=True)

print('Period:', res.period.period_label)

db = DatabaseManager()
conn = db.get_connection()
py = res.period.year
pm = res.period.month

print('\nStorage history rows for the period:')
cur = conn.execute(
    "SELECT facility_code, year, month, opening_volume_m3, closing_volume_m3 FROM storage_history WHERE year=? AND month=?",
    (py, pm)
)
rows = cur.fetchall()
print(json.dumps(rows, default=str, indent=2))

print('\nSample active storage_facilities current volumes:')
cur = conn.execute("SELECT code, name, current_volume_m3, capacity_m3 FROM storage_facilities WHERE status='active'")
rows = cur.fetchall()
print(json.dumps(rows[:20], default=str, indent=2))

conn.close()
