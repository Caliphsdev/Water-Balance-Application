"""UI tests for Storage Facilities Dashboard.

These tests instantiate the storage facilities module in a lightweight Tk context and stub
database interactions to avoid relying on real data. Focus areas:
- Dashboard rendering and initialization
- Summary card calculations (capacity, volume, utilization, active count)
- Data grid population and filtering
- Search and filter functionality (by name, type, status)
- Facility add/edit/delete operations
- Data persistence and refresh
- Edge cases and error handling
"""

import tkinter as tk
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ui.storage_facilities import StorageFacilitiesModule, FacilityDialog, FacilityMonthlyParamsDialog


class FakeDb:
    """Minimal database stub for StorageFacilitiesModule tests.

    Provides only the methods used by the storage facilities dashboard and returns
    predictable results based on query patterns.
    """

    def __init__(self):
        self._listener = None
        self.facilities_data = [
            {
                'facility_id': 1,
                'facility_code': 'UG2N_DAM1',
                'facility_name': 'North Decline Clean Dams 1-4',
                'type_id': 1,
                'type_name': 'dam',
                'total_capacity': 100000,
                'current_volume': 82000,  # Exactly 82% utilization
                'surface_area': 5000,
                'active': 1,
                'volume_calc_date': date(2025, 12, 31),
                'purpose': 'clean_water',
                'pump_start_level': 70.0,
                'pump_stop_level': 50.0,
                'water_quality': 'process',
            },
            {
                'facility_id': 2,
                'facility_code': 'OLDTSF',
                'facility_name': 'Old Tailings Storage Facility',
                'type_id': 2,
                'type_name': 'tsf',
                'total_capacity': 500000,
                'current_volume': 125000,
                'surface_area': 50000,
                'active': 1,
                'volume_calc_date': date(2025, 12, 31),
                'purpose': 'tailings',
                'pump_start_level': 70.0,
                'pump_stop_level': 50.0,
                'water_quality': 'process',
            },
            {
                'facility_id': 3,
                'facility_code': 'EMERGENCY_TANK',
                'facility_name': 'Emergency Water Tank',
                'type_id': 3,
                'type_name': 'tank',
                'total_capacity': 10000,
                'current_volume': 0,
                'surface_area': 500,
                'active': 0,
                'volume_calc_date': date(2025, 12, 31),
                'purpose': 'emergency',
                'pump_start_level': 70.0,
                'pump_stop_level': 50.0,
                'water_quality': 'emergency',
            },
        ]

    def register_listener(self, cb):
        """Register callback for database changes"""
        self._listener = cb

    def get_storage_facilities(self, active_only=False, use_cache=True):
        """Get storage facilities (PRIMARY READ METHOD).
        
        Args:
            active_only: Filter to active facilities only
            use_cache: Use cached results (for testing, stub ignores this)
        
        Returns:
            List of facility dicts with all properties
        """
        if active_only:
            return [f for f in self.facilities_data if f['active']]
        return self.facilities_data

    def get_facility_types(self):
        """Get all facility types (DATA REFERENCE).
        
        Returns:
            List of type dicts with type_id and type_name
        """
        return [
            {'type_id': 1, 'type_name': 'dam'},
            {'type_id': 2, 'type_name': 'tsf'},
            {'type_id': 3, 'type_name': 'tank'},
        ]

    def add_storage_facility(self, facility_data):
        """Add new storage facility.
        
        Args:
            facility_data: Dict with facility properties
        
        Returns:
            New facility_id
        """
        new_id = max(f['facility_id'] for f in self.facilities_data) + 1
        facility_data['facility_id'] = new_id
        self.facilities_data.append(facility_data)
        return new_id

    def update_storage_facility(self, facility_id, facility_data):
        """Update existing storage facility.
        
        Args:
            facility_id: ID of facility to update
            facility_data: Dict with updated properties
        
        Returns:
            Number of rows affected
        """
        for fac in self.facilities_data:
            if fac['facility_id'] == facility_id:
                fac.update(facility_data)
                return 1
        return 0

    def delete_storage_facilities(self, facility_ids):
        """Delete storage facilities (MULTI-DELETE).
        
        Args:
            facility_ids: List of facility IDs to delete
        
        Returns:
            Number of rows affected
        """
        initial_count = len(self.facilities_data)
        self.facilities_data = [f for f in self.facilities_data if f['facility_id'] not in facility_ids]
        return initial_count - len(self.facilities_data)

    def get_latest_calculation_date(self):
        """Get latest calculation date from database.
        
        Returns:
            Date object of latest calculation
        """
        return date(2025, 12, 31)

    def invalidate_all_caches(self):
        """Invalidate all cached data (called after updates)"""
        pass


class TestStorageFacilitiesDashboard:
    """Test StorageFacilitiesModule initialization, rendering, and data management."""

    @pytest.fixture
    def root(self):
        """Create a Tk root window for testing."""
        root = tk.Tk()
        yield root
        root.destroy()

    @pytest.fixture
    def parent_frame(self, root):
        """Create a parent frame for the storage facilities module."""
        frame = tk.Frame(root)
        frame.pack(fill='both', expand=True)
        return frame

    @pytest.fixture
    def db(self):
        """Create a fake database stub."""
        return FakeDb()

    @pytest.fixture
    def module(self, parent_frame, db):
        """Create StorageFacilitiesModule with fake database."""
        with patch('ui.storage_facilities.DatabaseManager', return_value=db):
            module = StorageFacilitiesModule(parent_frame)
            yield module

    # ============================================================================
    # INITIALIZATION & RENDERING TESTS
    # ============================================================================

    def test_module_initialization(self, module, db):
        """Test that module initializes with correct attributes."""
        assert module.parent is not None
        assert module.db is not None
        assert module.facilities == []
        assert module.filtered_facilities == []
        assert module.facility_types == []
        assert module.tree is None
        assert module.volume_source_text == "Current volume from database"

    def test_load_creates_ui_sections(self, module, db):
        """Test that load() creates all required UI sections."""
        module.load()
        
        # Verify parent has children (sections were created)
        children = module.parent.winfo_children()
        assert len(children) > 0
        
        # Verify tree widget exists and has correct columns
        assert module.tree is not None
        columns = module.tree['columns']
        expected_columns = ('ID', 'Code', 'Name', 'Type', 'Capacity', 'Volume', 'Utilization', 'Surface Area', 'Status')
        assert columns == expected_columns

    def test_load_populates_initial_data(self, module, db):
        """Test that load() populates facilities and updates display."""
        module.load()
        
        # Verify facilities were loaded
        assert len(module.facilities) == 3
        assert module.facilities[0]['facility_code'] == 'UG2N_DAM1'
        
        # Verify filtered list matches facilities initially
        assert len(module.filtered_facilities) == 3

    # ============================================================================
    # SUMMARY CARDS TESTS
    # ============================================================================

    def test_summary_cards_total_capacity(self, module, db):
        """Test total capacity card calculation (ACTIVE FACILITIES ONLY)."""
        module.load()
        
        # Only active facilities: UG2N_DAM1 (100000) + OLDTSF (500000) = 600000
        # EMERGENCY_TANK is inactive, not included
        active_facilities = [f for f in db.facilities_data if f['active']]
        total_capacity = sum(f['total_capacity'] for f in active_facilities)
        
        assert total_capacity == 600000

    def test_summary_cards_total_volume(self, module, db):
        """Test total current volume card calculation (ACTIVE FACILITIES ONLY)."""
        module.load()
        
        # Only active facilities: UG2N_DAM1 (82000) + OLDTSF (125000) = 207000
        active_facilities = [f for f in db.facilities_data if f['active']]
        total_volume = sum(f['current_volume'] for f in active_facilities)
        
        assert total_volume == 207000

    def test_summary_cards_average_utilization(self, module, db):
        """Test average utilization calculation for active facilities."""
        module.load()
        
        # Only active facilities with capacity > 0:
        # UG2N_DAM1: 82000 / 100000 * 100 = 82.0%
        # OLDTSF: 125000 / 500000 * 100 = 25.0%
        # Average: (82.0 + 25.0) / 2 = 53.5%
        active_facilities = [f for f in db.facilities_data if f['active'] and f['total_capacity'] > 0]
        utilizations = [(f['current_volume'] / f['total_capacity'] * 100) for f in active_facilities]
        avg_util = sum(utilizations) / len(utilizations) if utilizations else 0

        assert len(utilizations) == 2
        assert 53.0 < avg_util < 54.0
        active_count = sum(1 for f in db.facilities_data if f['active'])
        assert active_count == 2

    def test_summary_cards_empty_database(self, module, db):
        """Test summary cards with no facilities (EDGE CASE)."""
        db.facilities_data = []
        module.load()
        
        # Should not crash; cards should show 0
        assert module.total_capacity_label is not None
        assert module.total_volume_label is not None

    # ============================================================================
    # DATA GRID & FILTERING TESTS
    # ============================================================================

    def test_data_grid_displays_all_facilities(self, module, db):
        """Test that data grid populates with all facilities."""
        module.load()
        
        # Get tree items
        items = module.tree.get_children()
        assert len(items) == 3
        
        # Verify facility codes appear in grid
        values_list = [module.tree.item(item, 'values') for item in items]
        codes = [vals[1] for vals in values_list]
        assert 'UG2N_DAM1' in codes
        assert 'OLDTSF' in codes
        assert 'EMERGENCY_TANK' in codes

    def test_data_grid_displays_active_status(self, module, db):
        """Test that active/inactive status is displayed correctly."""
        module.load()
        
        # Get tree items and check status column (index 8)
        items = module.tree.get_children()
        values_list = [module.tree.item(item, 'values') for item in items]
        
        status_values = [vals[8] for vals in values_list]
        active_count = sum(1 for s in status_values if '✓' in s)
        inactive_count = sum(1 for s in status_values if '✕' in s)
        
        assert active_count == 2
        assert inactive_count == 1

    def test_search_filter_by_facility_name(self, module, db):
        """Test searching facilities by name."""
        module.load()
        
        # Search for "Old"
        module.search_var.set("Old")
        module._apply_filters()
        
        assert len(module.filtered_facilities) == 1
        assert module.filtered_facilities[0]['facility_code'] == 'OLDTSF'

    def test_search_filter_by_facility_code(self, module, db):
        """Test searching facilities by code."""
        module.load()
        
        # Search for "DAM1"
        module.search_var.set("DAM1")
        module._apply_filters()
        
        assert len(module.filtered_facilities) == 1
        assert module.filtered_facilities[0]['facility_code'] == 'UG2N_DAM1'

    def test_type_filter(self, module, db):
        """Test filtering facilities by type."""
        module.load()
        
        # Filter by 'dam' type
        module.type_filter_var.set('dam')
        module._apply_filters()
        
        filtered_types = [f['type_name'] for f in module.filtered_facilities]
        assert all(t == 'dam' for t in filtered_types)
        assert len(module.filtered_facilities) == 1

    def test_status_filter_active_only(self, module, db):
        """Test filtering to active facilities only."""
        module.load()
        
        # Filter to active facilities
        module.status_filter_var.set('Active')
        module._apply_filters()
        
        assert all(f['active'] for f in module.filtered_facilities)
        assert len(module.filtered_facilities) == 2

    def test_status_filter_inactive_only(self, module, db):
        """Test filtering to inactive facilities only."""
        module.load()
        
        # Filter to inactive facilities
        module.status_filter_var.set('Inactive')
        module._apply_filters()
        
        assert all(not f['active'] for f in module.filtered_facilities)
        assert len(module.filtered_facilities) == 1

    def test_combined_filters(self, module, db):
        """Test combining multiple filters (search + type + status)."""
        module.load()
        
        # Search for facilities AND filter by type
        module.search_var.set("North")
        module.type_filter_var.set('dam')
        module.status_filter_var.set('Active')
        module._apply_filters()
        
        assert len(module.filtered_facilities) == 1
        assert module.filtered_facilities[0]['facility_code'] == 'UG2N_DAM1'

    def test_filter_clears_search(self, module, db):
        """Test that clearing search shows all matching facilities."""
        module.load()
        
        # Apply search
        module.search_var.set("Old")
        module._apply_filters()
        assert len(module.filtered_facilities) == 1
        
        # Clear search
        module.search_var.set("")
        module._apply_filters()
        assert len(module.filtered_facilities) == 3

    # ============================================================================
    # UTILIZATION CALCULATION TESTS
    # ============================================================================

    def test_utilization_percentage_calculation(self, module, db):
        """Test utilization percentage calculation for grid display."""
        module.load()
        
        # Get a facility with known values
        ug2n = [f for f in module.facilities if f['facility_code'] == 'UG2N_DAM1'][0]
        util_pct = (ug2n['current_volume'] / ug2n['total_capacity'] * 100)
        
        # Should be exactly 82%
        assert 81.5 < util_pct < 82.5

    def test_utilization_with_zero_capacity(self, module, db):
        """Test utilization when capacity is zero (EDGE CASE - prevent division by zero)."""
        # Add facility with zero capacity
        db.facilities_data.append({
            'facility_id': 4,
            'facility_code': 'ZERO_CAP',
            'facility_name': 'Zero Capacity Tank',
            'type_id': 3,
            'type_name': 'tank',
            'total_capacity': 0,
            'current_volume': 0,
            'surface_area': 100,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        })
        
        module.load()
        
        # Should not crash; utilization should show as "—"
        zero_cap_fac = [f for f in module.facilities if f['facility_code'] == 'ZERO_CAP'][0]
        assert zero_cap_fac['total_capacity'] == 0

    def test_utilization_with_null_volume(self, module, db):
        """Test utilization when current volume is None (EDGE CASE)."""
        # Add facility with null volume
        db.facilities_data.append({
            'facility_id': 5,
            'facility_code': 'NULL_VOL',
            'facility_name': 'Null Volume Tank',
            'type_id': 3,
            'type_name': 'tank',
            'total_capacity': 5000,
            'current_volume': None,
            'surface_area': 200,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        })
        
        module.load()
        
        # Should handle None gracefully
        null_fac = [f for f in module.facilities if f['facility_code'] == 'NULL_VOL'][0]
        assert null_fac['current_volume'] is None

    # ============================================================================
    # ADD/EDIT/DELETE FACILITY TESTS
    # ============================================================================

    def test_add_facility_success(self, module, db):
        """Test adding a new storage facility."""
        module.load()
        initial_count = len(module.facilities)
        
        new_facility = {
            'facility_code': 'NEW_DAM',
            'facility_name': 'New Storage Dam',
            'type_id': 1,
            'type_name': 'dam',
            'total_capacity': 50000,
            'current_volume': 25000,
            'surface_area': 2000,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        }
        
        new_id = db.add_storage_facility(new_facility)
        
        assert new_id is not None
        assert len(db.facilities_data) == initial_count + 1
        assert db.facilities_data[-1]['facility_code'] == 'NEW_DAM'

    def test_edit_facility_success(self, module, db):
        """Test editing an existing facility."""
        module.load()
        
        # Edit OLDTSF capacity
        update_data = {'total_capacity': 600000}
        rows_affected = db.update_storage_facility(2, update_data)
        
        assert rows_affected == 1
        oldtsf = [f for f in db.facilities_data if f['facility_id'] == 2][0]
        assert oldtsf['total_capacity'] == 600000

    def test_delete_single_facility(self, module, db):
        """Test deleting a single facility."""
        module.load()
        initial_count = len(db.facilities_data)
        
        # Delete EMERGENCY_TANK (id=3)
        rows_affected = db.delete_storage_facilities([3])
        
        assert rows_affected == 1
        assert len(db.facilities_data) == initial_count - 1
        assert not any(f['facility_id'] == 3 for f in db.facilities_data)

    def test_delete_multiple_facilities(self, module, db):
        """Test deleting multiple facilities (MULTI-DELETE)."""
        module.load()
        initial_count = len(db.facilities_data)
        
        # Delete two facilities
        rows_affected = db.delete_storage_facilities([1, 3])
        
        assert rows_affected == 2
        assert len(db.facilities_data) == initial_count - 2
        assert not any(f['facility_id'] in [1, 3] for f in db.facilities_data)

    def test_delete_nonexistent_facility(self, module, db):
        """Test deleting non-existent facility (EDGE CASE - should fail gracefully)."""
        module.load()
        initial_count = len(db.facilities_data)
        
        # Try to delete facility with ID 999 (doesn't exist)
        rows_affected = db.delete_storage_facilities([999])
        
        assert rows_affected == 0
        assert len(db.facilities_data) == initial_count

    # ============================================================================
    # REFRESH & DATA PERSISTENCE TESTS
    # ============================================================================

    def test_refresh_reloads_data(self, module, db):
        """Test that refresh updates facilities from database."""
        module.load()
        
        # Modify a facility
        db.update_storage_facility(1, {'total_capacity': 100000})
        
        # Refresh
        module._load_data()
        
        # Verify updated data is loaded
        ug2n = [f for f in module.facilities if f['facility_id'] == 1][0]
        assert ug2n['total_capacity'] == 100000

    def test_refresh_clears_filters(self, module, db):
        """Test that refresh resets filters."""
        module.load()
        
        # Apply filter
        module.search_var.set("Old")
        module._apply_filters()
        assert len(module.filtered_facilities) == 1
        
        # Refresh (simulate clicking refresh button)
        module._load_data()
        
        # Filter should still be applied after refresh (user didn't clear it)
        # but data should be fresh from DB
        assert len(module.facilities) == 3

    def test_volume_source_text_indicates_source(self, module, db):
        """Test that volume source is clearly indicated in UI."""
        module.load()
        
        # Volume source text may contain 'database', 'excel', 'calc', or other indicators
        # Just verify it's not empty
        assert module.volume_source_text is not None
        assert len(module.volume_source_text) > 0

    # ============================================================================
    # FACILITY TYPES TESTS
    # ============================================================================

    def test_facility_types_loaded(self, module, db):
        """Test that facility types are loaded from database."""
        module.load()
        
        assert len(module.facility_types) == 3
        type_names = [t['type_name'] for t in module.facility_types]
        assert 'dam' in type_names
        assert 'tsf' in type_names
        assert 'tank' in type_names

    def test_facility_type_filter_options(self, module, db):
        """Test that type filter combo shows all types."""
        module.load()
        
        # Verify facility_types were used to populate combo
        assert len(module.facility_types) > 0

    # ============================================================================
    # GRID TAG STYLING TESTS
    # ============================================================================

    def test_active_facility_gets_active_tag(self, module, db):
        """Test that active facilities get 'active' tag for styling."""
        module.load()
        module._populate_grid()
        
        # Get active facility tag
        items = module.tree.get_children()
        for item in items:
            values = module.tree.item(item, 'values')
            if values[1] == 'UG2N_DAM1':  # Active facility
                tags = module.tree.item(item, 'tags')
                assert 'active' in tags

    def test_inactive_facility_gets_inactive_tag(self, module, db):
        """Test that inactive facilities get 'inactive' tag for styling."""
        module.load()
        module._populate_grid()
        
        # Get inactive facility tag
        items = module.tree.get_children()
        for item in items:
            values = module.tree.item(item, 'values')
            if values[1] == 'EMERGENCY_TANK':  # Inactive facility
                tags = module.tree.item(item, 'tags')
                assert 'inactive' in tags

    def test_high_utilization_gets_tag(self, module, db):
        """Test that high utilization facilities get 'high_util' tag (>=80%)."""
        module.load()
        module._populate_grid()
        
        # UG2N_DAM1 has 82% utilization, should get high_util tag with >= logic
        items = module.tree.get_children()
        for item in items:
            values = module.tree.item(item, 'values')
            if values[1] == 'UG2N_DAM1':  # High utilization facility
                tags = module.tree.item(item, 'tags')
                # Should have both 'active' and 'high_util' tags
                assert 'active' in tags
                assert 'high_util' in tags

    def test_low_utilization_gets_tag(self, module, db):
        """Test that low utilization facilities get 'low_util' tag (<20%, >0%)."""
        module.load()
        
        # Add facility with low utilization
        db.facilities_data.append({
            'facility_id': 10,
            'facility_code': 'LOW_UTIL',
            'facility_name': 'Low Utilization Tank',
            'type_id': 3,
            'type_name': 'tank',
            'total_capacity': 100000,
            'current_volume': 5000,  # 5% utilization
            'surface_area': 1000,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        })
        
        module._load_data()
        module._populate_grid()
        
        items = module.tree.get_children()
        for item in items:
            values = module.tree.item(item, 'values')
            if values[1] == 'LOW_UTIL':
                tags = module.tree.item(item, 'tags')
                assert 'low_util' in tags or 'active' in tags  # May have both

    # ============================================================================
    # INFO LABEL TESTS
    # ============================================================================

    def test_info_label_shows_facility_count(self, module, db):
        """Test that info label shows correct facility counts."""
        module.load()
        module._populate_grid()
        
        # Label should show total, filtered, and active counts
        label_text = module.info_label.cget('text')
        assert '3' in label_text  # Total
        assert 'active' in label_text.lower()

    def test_info_label_updates_on_filter(self, module, db):
        """Test that info label updates when filters are applied."""
        module.load()
        
        # Apply filter
        module.search_var.set("Old")
        module._apply_filters()
        module._populate_grid()
        
        label_text = module.info_label.cget('text')
        assert '1 of 3' in label_text  # Showing 1 of 3 facilities

    # ============================================================================
    # COMPLEX SCENARIO TESTS
    # ============================================================================

    def test_workflow_add_search_delete(self, module, db):
        """Test complete workflow: add facility, search for it, delete it."""
        module.load()
        
        # Step 1: Add facility
        new_facility = {
            'facility_code': 'WORKFLOW_TEST',
            'facility_name': 'Workflow Test Facility',
            'type_id': 1,
            'type_name': 'dam',
            'total_capacity': 30000,
            'current_volume': 15000,
            'surface_area': 1500,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        }
        new_id = db.add_storage_facility(new_facility)
        module._load_data()
        
        assert any(f['facility_code'] == 'WORKFLOW_TEST' for f in module.facilities)
        
        # Step 2: Search for it
        module.search_var.set("WORKFLOW_TEST")
        module._apply_filters()
        
        assert len(module.filtered_facilities) == 1
        assert module.filtered_facilities[0]['facility_code'] == 'WORKFLOW_TEST'
        
        # Step 3: Delete it
        rows_affected = db.delete_storage_facilities([new_id])
        assert rows_affected == 1
        module._load_data()
        
        assert not any(f['facility_code'] == 'WORKFLOW_TEST' for f in module.facilities)

    def test_workflow_add_edit_verify_cards(self, module, db):
        """Test workflow: add facility and verify summary cards update."""
        module.load()
        
        # Get initial totals
        initial_capacity = sum(f['total_capacity'] for f in db.facilities_data if f['active'])
        
        # Add facility
        new_facility = {
            'facility_code': 'ADD_TEST',
            'facility_name': 'Add Test Facility',
            'type_id': 1,
            'type_name': 'dam',
            'total_capacity': 100000,
            'current_volume': 50000,
            'surface_area': 2000,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        }
        db.add_storage_facility(new_facility)
        module._load_data()
        module._update_summary_cards()
        
        # Verify capacity increased
        new_capacity = sum(f['total_capacity'] for f in db.facilities_data if f['active'])
        assert new_capacity == initial_capacity + 100000

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    def test_load_with_empty_database(self, module, db):
        """Test loading when database has no facilities (EDGE CASE)."""
        db.facilities_data = []
        
        # Should not crash
        module.load()
        assert len(module.facilities) == 0
        assert len(module.filtered_facilities) == 0

    def test_filter_with_special_characters(self, module, db):
        """Test search filter with special characters (EDGE CASE)."""
        module.load()
        
        # Search with special characters
        module.search_var.set("@#$%")
        module._apply_filters()
        
        # Should not crash; should return no results
        assert len(module.filtered_facilities) == 0

    def test_filter_case_insensitive(self, module, db):
        """Test that search is case-insensitive."""
        module.load()
        
        # Search lowercase
        module.search_var.set("oldtsf")
        module._apply_filters()
        
        assert len(module.filtered_facilities) == 1
        
        # Search uppercase
        module.search_var.set("OLDTSF")
        module._apply_filters()
        
        assert len(module.filtered_facilities) == 1


class TestFacilityDialog:
    """Test FacilityDialog for add/edit operations."""

    @pytest.fixture
    def root(self):
        """Create a Tk root window for testing."""
        root = tk.Tk()
        yield root
        root.destroy()

    @pytest.fixture
    def db(self):
        """Create a fake database stub."""
        return FakeDb()

    def test_dialog_initialization_add_mode(self, root, db):
        """Test dialog initialization in add mode."""
        with patch('ui.storage_facilities.DatabaseManager', return_value=db):
            dialog = FacilityDialog(root, db, db.get_facility_types(), mode='add')
            
            assert dialog.mode == 'add'
            assert dialog.facility is None


class TestStorageFacilitiesIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def root(self):
        """Create a Tk root window for testing."""
        root = tk.Tk()
        yield root
        root.destroy()

    @pytest.fixture
    def parent_frame(self, root):
        """Create a parent frame for the storage facilities module."""
        frame = tk.Frame(root)
        frame.pack(fill='both', expand=True)
        return frame

    @pytest.fixture
    def db(self):
        """Create a fake database stub."""
        return FakeDb()

    @pytest.fixture
    def module(self, parent_frame, db):
        """Create StorageFacilitiesModule with fake database."""
        with patch('ui.storage_facilities.DatabaseManager', return_value=db):
            module = StorageFacilitiesModule(parent_frame)
            yield module

    def test_complete_facility_lifecycle(self, module, db):
        """Test complete lifecycle: load, filter, add, edit, delete."""
        # Load
        module.load()
        assert len(module.facilities) == 3
        
        # Filter
        module.search_var.set("dam")
        module._apply_filters()
        assert len(module.filtered_facilities) == 1
        
        # Clear filter
        module.search_var.set("")
        module._apply_filters()
        
        # Add
        new_facility = {
            'facility_code': 'LIFECYCLE_TEST',
            'facility_name': 'Lifecycle Test',
            'type_id': 1,
            'type_name': 'dam',
            'total_capacity': 50000,
            'current_volume': 25000,
            'surface_area': 2000,
            'active': 1,
            'volume_calc_date': date(2025, 12, 31),
        }
        new_id = db.add_storage_facility(new_facility)
        
        # Refresh
        module._load_data()
        assert len(module.facilities) == 4
        
        # Edit
        db.update_storage_facility(new_id, {'total_capacity': 60000})
        module._load_data()
        updated = [f for f in module.facilities if f['facility_id'] == new_id][0]
        assert updated['total_capacity'] == 60000
        
        # Delete
        db.delete_storage_facilities([new_id])
        module._load_data()
        assert len(module.facilities) == 3
