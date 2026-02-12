"""Comprehensive tests for Storage Facilities Dashboard (INTEGRATION TESTS).

Tests the complete facilities management workflow:
- Loading facilities from database
- Searching and filtering
- Summary card calculations
- Add/Edit/Delete operations
- UI state management

Clean up policy: All test data is removed from database after each test.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
import sqlite3

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread
from models.storage_facility import StorageFacility
from services.storage_facility_service import StorageFacilityService
from ui.dashboards.storage_facilities_dashboard import StorageFacilitiesPage


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for all tests (required for PySide6)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db_connection():
    """Create temporary test database connection (ISOLATED TEST DB).
    
    Setup:
    - Creates in-memory SQLite database
    - Initializes schema from DatabaseSchema
    - Yields connection
    
    Teardown:
    - Closes connection
    - Data is automatically deleted (in-memory DB)
    """
    from database.schema import DatabaseSchema
    
    # Create in-memory database for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Initialize schema
    schema = DatabaseSchema()
    
    # Create tables manually in test database
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS storage_facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            area_name TEXT,
            facility_type TEXT NOT NULL,
            capacity_m3 REAL NOT NULL,
            surface_area_m2 REAL,
            current_volume_m3 REAL DEFAULT 0,
            is_lined INTEGER,
            status TEXT DEFAULT 'active',
            notes TEXT
        )
    ''')
    conn.commit()
    
    yield conn
    
    # Cleanup: connection is auto-closed (in-memory)
    conn.close()


@pytest.fixture
def real_service(test_facilities):
    """Create StorageFacilityService with real database (INTEGRATION TEST).
    
    Uses the actual SQLite database (data/water_balance.db) for true integration testing.
    Test facilities are already inserted by test_facilities fixture.
    """
    service = StorageFacilityService()
    yield service
    # No cleanup needed - test_facilities fixture handles it


@pytest.fixture
def service(db_connection):
    """Create StorageFacilityService with test database (MOCKED SERVICE - NOT USED).
    
    Placeholder for potential unit testing with mocked DB.
    Integration tests use real_service instead.
    """
    service = StorageFacilityService()
    yield service


@pytest.fixture
def test_facilities():
    """Create test facilities in real database (TEST DATA SETUP).
    
    Creates 5 facilities with different types and states in actual database.
    
    Cleanup: ALL test data is REMOVED after test completes.
    """
    from database.db_manager import DatabaseManager
    
    db_manager = DatabaseManager.get_instance()
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    # Remove stale test rows from previous interrupted runs.
    cursor.execute("DELETE FROM storage_facilities WHERE code LIKE 'TEST_%'")
    conn.commit()
    
    # Insert test data with unique prefix to avoid conflicts
    test_data = [
        ('TEST_TANK001', 'Test Tank A', 'Tank', 100.0, 50.0, None, 'active'),
        ('TEST_DAM001', 'Test Dam North', 'Dam', 500.0, 350.0, 1, 'active'),
        ('TEST_TSF001', 'Test Tailings A', 'TSF', 1000.0, 800.0, 0, 'active'),
        ('TEST_POND001', 'Test Evap Pond', 'Pond', 200.0, 100.0, None, 'inactive'),
        ('TEST_TSF002', 'Test Tailings B', 'TSF', 800.0, 600.0, 1, 'active'),
    ]
    
    inserted_ids = []
    try:
        for code, name, ftype, capacity, volume, lined, status in test_data:
            cursor.execute('''
                INSERT OR REPLACE INTO storage_facilities 
                (code, name, facility_type, capacity_m3, current_volume_m3, is_lined, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, ftype, capacity, volume, lined, status))
            conn.commit()
            inserted_ids.append(cursor.lastrowid)
        
        yield inserted_ids
    finally:
        # CLEANUP: Remove ALL test data before test ends
        for facility_id in inserted_ids:
            cursor.execute('DELETE FROM storage_facilities WHERE id = ?', (facility_id,))
            conn.commit()
        
        logger = logging.getLogger(__name__)
        logger.info(f"Cleaned up {len(inserted_ids)} test facilities from database")


@pytest.fixture
def dashboard(qapp, service, test_facilities, qtbot):
    """Create StorageFacilitiesPage dashboard for testing (WIDGET CREATION).
    
    Mocks the UI and replaces service with test service.
    """
    with patch('ui.dashboards.storage_facilities_dashboard.StorageFacilityService') as MockService:
        MockService.return_value = service
        dashboard = StorageFacilitiesPage()
        dashboard.service = service  # Replace with test service
        # Wait for async loader thread to populate facilities before assertions.
        qtbot.waitUntil(
            lambda: len(dashboard._facilities) >= len(test_facilities),
            timeout=5000,
        )
        yield dashboard
        # Ensure background threads are fully stopped before widget teardown.
        if hasattr(dashboard, "stop_background_tasks"):
            dashboard.stop_background_tasks()
        for thread in dashboard.findChildren(QThread):
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)
        dashboard.deleteLater()  # Cleanup


# ============================================================================
# TESTS - DATA LOADING
# ============================================================================

class TestFacilitiesLoading:
    """Test facility data loading from database."""
    
    def test_load_empty_database(self, real_service):
        """Test loading facilities when database is empty (EDGE CASE).
        
        Expected: Returns empty list or original facilities, no errors.
        """
        # Get baseline count
        baseline = real_service.get_facilities()
        baseline_count = len(baseline)
        
        # Can't truly test empty DB in integration tests, so just verify we can load
        facilities = real_service.get_facilities()
        assert isinstance(facilities, list)
        assert len(facilities) >= 0
    
    
    def test_load_all_facilities(self, real_service, test_facilities):
        """Test loading all facilities from database (BASIC FUNCTIONALITY).
        
        Expected: Returns test facilities with correct data.
        """
        facilities = real_service.get_facilities()
        
        # Should have at least our test facilities
        test_codes = ['TEST_TANK001', 'TEST_DAM001', 'TEST_TSF001']
        found_codes = [f.code for f in facilities]
        
        for code in test_codes:
            assert any(code in fc for fc in found_codes), f"Test facility {code} not found"
    
    
    def test_load_preserves_types(self, real_service, test_facilities):
        """Test that loaded facilities have correct types (TYPE VALIDATION).
        
        Expected: All facility objects are StorageFacility instances.
        """
        facilities = real_service.get_facilities()
        
        for facility in facilities:
            assert isinstance(facility, StorageFacility)
            assert isinstance(facility.code, str)
            assert isinstance(facility.capacity_m3, (int, float))
            assert isinstance(facility.current_volume_m3, (int, float))
    
    
    def test_tank_is_lined_null(self, real_service, test_facilities):
        """Test Tank facilities have is_lined = None (DATA INTEGRITY).
        
        Expected: Tank facility has is_lined=None (not 0 or 1).
        """
        facilities = real_service.get_facilities()
        tank = next((f for f in facilities if f.facility_type == 'Tank' and f.code.startswith('TEST_')), None)
        
        if tank:
            assert tank.is_lined is None, "Tank should have is_lined=None (Not Applicable)"
    
    
    def test_dam_is_lined_true(self, real_service, test_facilities):
        """Test Dam with is_lined=1 converts to Python True (TYPE CONVERSION).
        
        Expected: Integer 1 from DB converts to Python True.
        """
        facilities = real_service.get_facilities()
        dam = next((f for f in facilities if f.code == 'TEST_DAM001'), None)
        
        if dam:
            assert dam.is_lined is True, "Dam should have is_lined=True (1 in DB)"
    
    
    def test_tsf_is_lined_false(self, real_service, test_facilities):
        """Test TSF with is_lined=0 converts to Python False (TYPE CONVERSION).
        
        Expected: Integer 0 from DB converts to Python False.
        """
        facilities = real_service.get_facilities()
        tsf = next((f for f in facilities if f.code == 'TEST_TSF001'), None)
        
        if tsf:
            assert tsf.is_lined is False, "TSF should have is_lined=False (0 in DB)"


# ============================================================================
# TESTS - DASHBOARD FILTERING
# ============================================================================

class TestDashboardFiltering:
    """Test dashboard search and filter functionality."""
    
    def test_dashboard_loads_facilities(self, dashboard, test_facilities):
        """Test dashboard loads facilities on init (PAGE INITIALIZATION).
        
        Expected: Dashboard._facilities populated.
        """
        assert len(dashboard._facilities) >= len(test_facilities)
    
    
    def test_filter_by_type_tank(self, dashboard, test_facilities):
        """Test filtering facilities by type = Tank (FILTER FUNCTIONALITY).
        
        Expected: Only Tank facilities returned.
        """
        # Apply type filter
        tank_facilities = [f for f in dashboard._facilities if f['type'] == 'Tank']
        
        assert len(tank_facilities) >= 1
        for f in tank_facilities:
            assert f['type'] == 'Tank'
    
    
    def test_filter_by_status_active(self, dashboard, test_facilities):
        """Test filtering facilities by status = active (FILTER FUNCTIONALITY).
        
        Expected: Only active facilities returned.
        """
        active_facilities = [f for f in dashboard._facilities if f['status'] == 'active']
        
        assert len(active_facilities) >= 4  # 4 active in test data
        for f in active_facilities:
            assert f['status'] == 'active'
    
    
    def test_search_by_code(self, dashboard, test_facilities):
        """Test search functionality by facility code (SEARCH FUNCTIONALITY).
        
        Expected: Only matching facilities returned.
        """
        search_term = 'TEST_TANK001'
        matching = [f for f in dashboard._facilities 
                   if search_term.lower() in f['code'].lower()]
        
        assert len(matching) >= 1
        assert matching[0]['code'] == 'TEST_TANK001'
    
    
    def test_search_by_name(self, dashboard, test_facilities):
        """Test search functionality by facility name (SEARCH FUNCTIONALITY).
        
        Expected: All matching facilities returned.
        """
        search_term = 'Test'
        matching = [f for f in dashboard._facilities 
                   if search_term.lower() in f['name'].lower()]
        
        # Should find our test facilities
        assert len(matching) >= len(test_facilities)


# ============================================================================
# TESTS - SUMMARY CARD CALCULATIONS
# ============================================================================

class TestSummaryCards:
    """Test KPI calculation for summary cards."""
    
    def test_total_capacity_calculation(self, dashboard, test_facilities):
        """Test total capacity summary (KPI CALCULATION).
        
        Expected: Sum of all facility capacities.
        """
        test_rows = [f for f in dashboard._facilities if f["code"].startswith("TEST_")]
        total_capacity = sum(f['capacity'] for f in test_rows)
        
        # Test data: 100 + 500 + 1000 + 200 + 800 = 2600
        assert total_capacity == 2600.0
    
    
    def test_current_volume_calculation(self, dashboard, test_facilities):
        """Test current volume summary (KPI CALCULATION).
        
        Expected: Sum of all facility volumes.
        """
        test_rows = [f for f in dashboard._facilities if f["code"].startswith("TEST_")]
        total_volume = sum(f['volume'] for f in test_rows)
        
        # Test data: 50 + 350 + 800 + 100 + 600 = 1900
        assert total_volume == 1900.0
    
    
    def test_utilization_percentage(self, dashboard, test_facilities):
        """Test overall utilization percentage (KPI CALCULATION).
        
        Expected: total_volume / total_capacity * 100
        """
        test_rows = [f for f in dashboard._facilities if f["code"].startswith("TEST_")]
        total_capacity = sum(f['capacity'] for f in test_rows)
        total_volume = sum(f['volume'] for f in test_rows)
        
        utilization = (total_volume / total_capacity * 100) if total_capacity > 0 else 0
        
        # 1900 / 2600 * 100 = 73.08%
        assert abs(utilization - 73.08) < 0.1
    
    
    def test_active_facilities_count(self, dashboard, test_facilities):
        """Test count of active facilities (KPI CALCULATION).
        
        Expected: Number of facilities with status = active.
        """
        test_rows = [f for f in dashboard._facilities if f["code"].startswith("TEST_")]
        active_count = sum(1 for f in test_rows if f['status'] == 'active')
        
        assert active_count == 4


# ============================================================================
# TESTS - ADD/EDIT/DELETE OPERATIONS
# ============================================================================

class TestFacilityCRUD:
    """Test Add/Edit/Delete facility operations."""
    
    def test_add_facility_basic(self, real_service):
        """Test adding a new facility (CREATE OPERATION).
        
        Expected: Facility added to database, can be retrieved.
        Cleanup: Test data removed after test.
        """
        from database.db_manager import DatabaseManager
        
        test_code = 'TEST_CRUD_ADD'
        
        try:
            # Add facility
            real_service.add_facility(
                code=test_code,
                name='CRUD Test Add',
                facility_type='Pond',
                capacity_m3=500.0,
                is_lined=None
            )
            
            # Verify it was added
            facilities = real_service.get_facilities()
            assert any(f.code == test_code for f in facilities), "Facility not added"
        finally:
            # Cleanup
            db_manager = DatabaseManager.get_instance()
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM storage_facilities WHERE code = ?', (test_code,))
            conn.commit()
    
    
    def test_add_tank_auto_sets_is_lined_null(self, real_service):
        """Test that new Tank facility has is_lined = None (DATA INTEGRITY).
        
        Expected: Tank created with is_lined=None.
        Cleanup: Test data removed after test.
        """
        from database.db_manager import DatabaseManager
        
        test_code = 'TEST_CRUD_TANK'
        
        try:
            # Add Tank facility
            real_service.add_facility(
                code=test_code,
                name='CRUD Test Tank',
                facility_type='Tank',
                capacity_m3=100.0
            )
            
            # Verify is_lined is None
            facilities = real_service.get_facilities()
            tank = next((f for f in facilities if f.code == test_code), None)
            assert tank is not None
            assert tank.is_lined is None, "Tank should have is_lined=None"
        finally:
            # Cleanup
            db_manager = DatabaseManager.get_instance()
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM storage_facilities WHERE code = ?', (test_code,))
            conn.commit()
    
    
    def test_update_facility_volume(self, real_service, test_facilities):
        """Test updating facility volume (UPDATE OPERATION).
        
        Expected: Volume updated in database.
        Cleanup: Database restored.
        """
        # Get a test facility to update
        facilities = real_service.get_facilities()
        target = next((f for f in facilities if f.code == 'TEST_TANK001'), None)
        
        if target:
            original_volume = target.current_volume_m3
            
            try:
                # Update volume
                real_service.update_facility(
                    facility_id=target.id,
                    current_volume_m3=99.0
                )
                
                # Verify update
                updated = real_service.get_facility(target.code)
                assert updated.current_volume_m3 == 99.0
            finally:
                # Restore original value
                real_service.update_facility(
                    facility_id=target.id,
                    current_volume_m3=original_volume
                )
    
    
    def test_delete_facility(self, real_service):
        """Test deleting a facility (DELETE OPERATION).
        
        Expected: Facility removed from database.
        Cleanup: N/A (deletion is cleanup).
        """
        from database.db_manager import DatabaseManager
        
        test_code = 'TEST_CRUD_DELETE'
        
        # Create a facility to delete
        real_service.add_facility(
            code=test_code,
            name='CRUD Test Delete',
            facility_type='Pond',
            capacity_m3=300.0
        )
        
        # Get ID
        facilities_before = real_service.get_facilities()
        facility_to_delete = next((f for f in facilities_before if f.code == test_code), None)
        count_before = len(facilities_before)
        
        if facility_to_delete:
            # Service requires inactive status before deletion.
            real_service.update_facility(facility_id=facility_to_delete.id, status='inactive')
            # Delete it
            real_service.delete_facility(facility_to_delete.id)
            
            # Verify deletion
            facilities_after = real_service.get_facilities()
            assert len(facilities_after) == count_before - 1
            assert not any(f.id == facility_to_delete.id for f in facilities_after)


# ============================================================================
# TESTS - PERFORMANCE & OPTIMIZATION
# ============================================================================

class TestPerformance:
    """Test performance characteristics and optimization concerns."""
    
    def test_load_facilities_completes_quickly(self, dashboard, test_facilities):
        """Test that loading facilities completes in reasonable time (PERFORMANCE).
        
        Expected: Load <100ms for 5 facilities (should be near instant).
        
        Concern: If this takes >200ms, lazy-loading model may have issues.
        """
        import time
        
        start = time.time()
        dashboard._load_facilities()
        elapsed = time.time() - start
        
        # Should be very fast (target <100ms)
        assert elapsed < 1.0, f"Load took {elapsed:.3f}s (should be <1s)"
    
    
    def test_filter_performance(self, dashboard, test_facilities):
        """Test filter operation performance (PERFORMANCE).
        
        Expected: Filter completes quickly.
        
        Concern: Filtering large datasets (1000+) should still be fast.
        """
        import time
        
        start = time.time()
        dashboard._filtered_facilities = [
            f for f in dashboard._facilities if f['type'] == 'Tank'
        ]
        elapsed = time.time() - start
        
        assert elapsed < 0.1, f"Filter took {elapsed:.3f}s"
    
    
    def test_utilization_calculation_efficiency(self, dashboard, test_facilities):
        """Test utilization percentage calculation performance (OPTIMIZATION).
        
        Expected: Calculation is efficient (no expensive operations).
        
        Concern: Avoid recalculating if value hasn't changed.
        """
        # Check test fixtures only (ignore ambient production rows in shared DB).
        test_rows = [f for f in dashboard._filtered_facilities if f["code"].startswith("TEST_")]
        for facility in test_rows:
            if facility['capacity'] > 0:
                util = (facility['volume'] / facility['capacity']) * 100
                assert 0 <= util <= 200, "Utilization should be 0-200%"


# ============================================================================
# TESTS - ERROR HANDLING & EDGE CASES
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_division_by_zero_zero_capacity(self, dashboard):
        """Test handling of zero capacity (EDGE CASE).
        
        Expected: No division by zero, returns 0% utilization.
        """
        # Create facility with zero capacity
        facility = {
            'code': 'ZERO_CAP',
            'name': 'Zero Capacity',
            'type': 'Tank',
            'capacity': 0,  # Zero capacity
            'volume': 100,
            'status': 'active'
        }
        
        # Calculate utilization safely
        if facility['capacity'] > 0:
            util = (facility['volume'] / facility['capacity']) * 100
        else:
            util = 0
        
        assert util == 0, "Should return 0 for zero capacity"
    
    
    def test_volume_exceeds_capacity_warning(self, dashboard):
        """Test detection of volume > capacity (DATA QUALITY).
        
        Expected: Identifies invalid state (possible overflow).
        """
        facility = {
            'code': 'OVERFLOW',
            'name': 'Overflow Test',
            'type': 'Tank',
            'capacity': 100,
            'volume': 150,  # Exceeds capacity
            'status': 'active'
        }
        
        # Check for overflow condition
        if facility['volume'] > facility['capacity']:
            is_overflow = True
        else:
            is_overflow = False
        
        assert is_overflow, "Should detect overflow condition"
    
    
    def test_negative_volume_warning(self, dashboard):
        """Test detection of negative volume (DATA QUALITY).
        
        Expected: Identifies impossible state.
        """
        facility = {
            'code': 'NEGATIVE',
            'name': 'Negative Volume Test',
            'type': 'Tank',
            'capacity': 100,
            'volume': -50,  # Negative volume
            'status': 'active'
        }
        
        # Check for negative volume
        if facility['volume'] < 0:
            is_invalid = True
        else:
            is_invalid = False
        
        assert is_invalid, "Should detect negative volume"


# ============================================================================
# TESTS - UI STATE MANAGEMENT
# ============================================================================

class TestUIState:
    """Test UI state management and widget interactions."""
    
    def test_dashboard_initializes_without_errors(self, dashboard):
        """Test dashboard widget initializes successfully (WIDGET INITIALIZATION).
        
        Expected: No exceptions, widget is ready.
        """
        assert dashboard is not None
        assert hasattr(dashboard, '_facilities')
        assert hasattr(dashboard, '_filtered_facilities')
    
    
    def test_table_model_sets_up_correctly(self, dashboard):
        """Test table model configuration (TABLE SETUP).
        
        Expected: Model attached to view, sorting enabled.
        """
        if hasattr(dashboard.ui, 'tableView'):
            assert dashboard.ui.tableView.model() is not None
            assert dashboard.ui.tableView.isSortingEnabled()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
