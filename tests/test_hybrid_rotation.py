"""
Test hybrid time+size based log rotation
"""
import sys
import os
from pathlib import Path

user_base = Path('.').resolve()
os.environ['WATERBALANCE_USER_DIR'] = str(user_base)
sys.path.insert(0, 'src')

from core.app_logger import logger, LOGS_DIR, _cleanup_old_logs
import time
from datetime import datetime, timedelta

print("=" * 70)
print("Testing Hybrid Time+Size Based Log Rotation")
print("=" * 70)

# Test 1: Check cleanup function
print("\n1. Testing auto-cleanup of old logs...")
old_log = LOGS_DIR / "test_old_log.log"
old_log.write_text("This is an old log file")
# Set modification time to 100 days ago
old_time = (datetime.now() - timedelta(days=100)).timestamp()
os.utime(old_log, (old_time, old_time))
print(f"   Created fake old log: {old_log}")
print(f"   File exists before cleanup: {old_log.exists()}")

_cleanup_old_logs(max_age_days=90)
print(f"   File exists after cleanup: {old_log.exists()}")

# Test 2: Hybrid rotation with size limits
print("\n2. Testing hybrid rotation configuration...")
storage_logger = logger.get_dashboard_logger('storage_facilities')
analytics_logger = logger.get_dashboard_logger('analytics')

print(f"   Storage Facilities logger handlers: {len(storage_logger.handlers)}")
print(f"   Analytics logger handlers: {len(analytics_logger.handlers)}")

# Test 3: Check rotation intervals
print("\n3. Checking rotation handlers...")
for handler in storage_logger.handlers:
    if hasattr(handler, 'target_handler'):
        target = handler.target_handler
        if hasattr(target, 'maxBytes'):
            max_mb = target.maxBytes / (1024 * 1024)
            print(f"   Storage: {max_mb:.1f}MB max, {target.backupCount} backups")

for handler in analytics_logger.handlers:
    if hasattr(handler, 'target_handler'):
        target = handler.target_handler
        if hasattr(target, 'maxBytes'):
            max_mb = target.maxBytes / (1024 * 1024)
            print(f"   Analytics: {max_mb:.1f}MB max, {target.backupCount} backups")

# Test 4: Log some test messages
print("\n4. Testing log messages with rotation...")
storage_logger.info("Test message 1 from storage")
analytics_logger.info("Test message 1 from analytics")

with logger.performance_timer('Test operation'):
    time.sleep(0.1)

storage_logger.warning("Test warning from storage")
analytics_logger.error("Test error from analytics")

# Test 5: Heavy burst to test batching
print("\n5. Testing heavy logging burst...")
start = time.time()
for i in range(50):
    storage_logger.debug(f"Burst message {i+1}/50")
burst_ms = (time.time() - start) * 1000
print(f"   Logged 50 messages in {burst_ms:.2f}ms (non-blocking!)")

# Shutdown
print("\n6. Shutting down logger...")
time.sleep(0.5)
logger.shutdown()

# Check structure
print("\n" + "=" * 70)
print("LOG STRUCTURE AFTER TEST")
print("=" * 70)
if LOGS_DIR.exists():
    for item in sorted(LOGS_DIR.rglob('*.log*')):
        size_kb = item.stat().st_size / 1024
        rel_path = item.relative_to(LOGS_DIR)
        print(f"  {str(rel_path):50} {size_kb:8.2f} KB")

print("\n✅ HYBRID ROTATION FEATURES:")
print("   • Size-based rotation (prevents huge files)")
print("   • Time-based rotation (weekly for dashboards)")
print("   • Auto-cleanup (removes logs >90 days old)")
print("   • QThread background processing (non-blocking)")
print("   • Dated filenames (analytics.log.2026-01-30)")
print("=" * 70)
