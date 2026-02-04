import sys, os
from pathlib import Path

user_base = Path('.').resolve()
os.environ['WATERBALANCE_USER_DIR'] = str(user_base)
sys.path.insert(0, 'src')

from core.app_logger import logger, LOGS_DIR

print(f"LOGS_DIR: {LOGS_DIR}")
print(f"LOGS_DIR exists: {LOGS_DIR.exists()}")

print("\nGetting storage_facilities logger...")
sl = logger.get_dashboard_logger('storage_facilities')

print(f"Logger name: {sl.name}")
print(f"Logger level: {sl.level}")
print(f"Handlers count: {len(sl.handlers)}")
print(f"Has handlers: {sl.hasHandlers()}")

expected_dir = LOGS_DIR / 'storage_facilities'
print(f"\nExpected dir: {expected_dir}")
print(f"Expected dir exists: {expected_dir.exists()}")

if expected_dir.exists():
    print(f"Contents: {list(expected_dir.iterdir())}")

print("\nLogging test message...")
sl.info("Test message from storage_facilities logger")

import time
time.sleep(0.5)

print("\nShutting down...")
logger.shutdown()

print(f"\nAfter shutdown - folder exists: {expected_dir.exists()}")
if expected_dir.exists():
    print(f"Files: {list(expected_dir.glob('*'))}")
