import sys
from pathlib import Path
sys.path.insert(0, str(Path('src')))
from database.db_manager import DatabaseManager

db = DatabaseManager()
# Clear old pump transfer events for test facilities
db.execute_query('DELETE FROM pump_transfer_events WHERE source_code IN ("SRC_TEST", "MDCD5-6") OR dest_code IN ("DST_TEST", "MDSWD3-4")', ())
print('Cleaned pump_transfer_events')
