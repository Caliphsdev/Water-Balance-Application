#!/usr/bin/env python
"""
Test Storage Facilities Backend (INTEGRATION TEST).

Tests all layers: Model → Schema → Manager → Repository → Service
"""
import sys
sys.path.insert(0, str(__file__).split('tests')[0] + 'src')

from database.schema import DatabaseSchema
from database.db_manager import DatabaseManager
from services.storage_facility_service import StorageFacilityService
from models.storage_facility import StorageFacility

print("=" * 60)
print("Testing Storage Facilities Backend")
print("=" * 60)

# Test 1: Create database schema
print("\n[1/5] Creating database schema...")
try:
    schema = DatabaseSchema()
    schema.create_database()
    print("✓ Database schema created")
except Exception as e:
    print(f"✗ Failed to create schema: {e}")
    sys.exit(1)

# Test 2: Initialize database manager
print("[2/5] Initializing database manager...")
try:
    db = DatabaseManager()
    print(f"✓ Database manager initialized")
    print(f"✓ Database file exists at: {db.db_path}")
except Exception as e:
    print(f"✗ Failed to init DB manager: {e}")
    sys.exit(1)

# Test 3: Verify table exists
print("[3/5] Verifying storage_facilities table...")
try:
    if db.table_exists('storage_facilities'):
        count = db.get_row_count('storage_facilities')
        print(f"✓ Table exists (rows: {count})")
    else:
        print("✗ Table not found")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed to verify table: {e}")
    sys.exit(1)

# Test 4: Initialize service
print("[4/5] Initializing StorageFacilityService...")
try:
    service = StorageFacilityService()
    summary = service.get_summary()
    print(f"✓ Service initialized")
    print(f"✓ Summary: {summary['total_count']} facilities")
except Exception as e:
    print(f"✗ Failed to init service: {e}")
    sys.exit(1)

# Test 5: Create or retrieve test facility
print("[5/5] Creating/retrieving test facility...")
try:
    # Try to get existing test facility
    test_facility = service.get_facility('TEST001')
    if test_facility:
        print(f"✓ Test facility already exists (id={test_facility.id})")
        print(f"  Code: {test_facility.code}")
        print(f"  Volume: {test_facility.current_volume_m3} m³ ({test_facility.volume_percentage:.1f}% full)")
    else:
        # Create new test facility
        facility = service.add_facility(
            code='TEST001',
            name='Test Facility',
            facility_type='TSF',
            capacity_m3=100000,
            surface_area_m2=5000,
            current_volume_m3=50000
        )
        print(f"✓ Test facility created (id={facility.id})")
        print(f"  Code: {facility.code}")
        print(f"  Volume: {facility.current_volume_m3} m³ ({facility.volume_percentage:.1f}% full)")
except Exception as e:
    print(f"✗ Failed to create/retrieve facility: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print("\nNext steps:")
print("1. Run the PySide6 app: python src/main.py")
print("2. Navigate to Storage Facilities dashboard")
print("3. Click 'Add' to create a facility")
print("4. Double-click a row to edit")
print("5. Right-click to delete (if available)")
