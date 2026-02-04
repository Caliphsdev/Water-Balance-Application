"""
Test script to verify QThread logger and dashboard logging
"""
import sys
import os
from pathlib import Path

# Set environment variable
user_base = Path(__file__).parent.parent
os.environ['WATERBALANCE_USER_DIR'] = str(user_base)

# Add src to path
sys.path.insert(0, str(user_base / 'src'))

from core.app_logger import logger
import time

print("=" * 60)
print("Testing QThread Background Logger")
print("=" * 60)

# Test 1: Basic logging
print("\n1. Testing basic log levels...")
logger.debug("DEBUG: This is a debug message (file only)")
logger.info("INFO: This is an info message (file only)")
logger.warning("WARNING: This is a warning (console + file)")
logger.error("ERROR: This is an error (console + file)")

# Test 2: Performance timer
print("\n2. Testing performance timer...")
with logger.performance_timer('Test operation 1'):
    time.sleep(0.1)

with logger.performance_timer('Test operation 2'):
    time.sleep(0.05)

# Test 3: Dashboard logger
print("\n3. Testing dashboard logger...")
storage_logger = logger.get_dashboard_logger('storage_facilities')
storage_logger.info("Storage Facility dashboard initialized")
storage_logger.debug("This is a debug message from storage dashboard")

analytics_logger = logger.get_dashboard_logger('analytics')
analytics_logger.info("Analytics dashboard initialized")
analytics_logger.debug("This is a debug message from analytics dashboard")

# Test 4: Heavy logging burst (tests async performance)
print("\n4. Testing heavy logging burst (100 messages)...")
start = time.time()
for i in range(100):
    logger.debug(f"Burst message {i+1}/100")
burst_time = (time.time() - start) * 1000
print(f"   Logged 100 messages in {burst_time:.2f}ms (non-blocking!)")

# Test 5: Performance tracking
print("\n5. Testing performance tracking...")
with logger.performance_timer('Load mock data'):
    time.sleep(0.2)

# Dashboard loggers use logger.performance() directly
storage_logger.info("Simulating storage dashboard operation...")
start = time.time()
time.sleep(0.15)
logger.performance('Storage dashboard operation', (time.time() - start) * 1000)

analytics_logger.info("Simulating analytics chart generation...")
start = time.time()
time.sleep(0.1)
logger.performance('Analytics chart generation', (time.time() - start) * 1000)

print("\n" + "=" * 60)
print("Shutting down logger worker...")
logger.shutdown()

print("\nLog files should be created at:")
logs_dir = Path(__file__).parent.parent / 'logs'
print(f"  System logs: {logs_dir}")
print(f"  Storage logs: {logs_dir / 'storage_facilities'}")
print(f"  Analytics logs: {logs_dir / 'analytics'}")

print("\nCheck log files for all test messages!")
print("=" * 60)
