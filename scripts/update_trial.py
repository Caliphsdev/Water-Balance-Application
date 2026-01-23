import sys
sys.path.insert(0, 'src')
from database.db_manager import db

db.execute_update("UPDATE license_info SET license_tier='trial', max_calculations=10, calculation_count=0")
print("License updated to trial with 10 calculation limit")
