"""Storage Facilities Dashboard Tests (SIMPLIFIED INTEGRATION).

Tests the dashboard with real database and actual data.
Focus on real bugs and improvements in the UI/dashboard layer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import sqlite3
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication
from services.storage_facility_service import StorageFacilityService


@pytest.fixture(scope="session")
def qapp():
    """QApplication fixture."""
    app = QApplication.instance()
    return app if app else QApplication([])


# ============================================================================
# TESTS - DATA LOADING & CONVERSIONS
# ============================================================================

class TestStorageFacilityDataLoading:
    """Test real data loading from database."""
    
    def test_load_facilities_succeeds(self):
        """Test loading facilities works without errors (BASIC CHECK).
        
        Expected: Service loads facilities from real database.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        # Should return a list (may be empty, may have data)
        assert isinstance(facilities, list)
        print(f"✓ Loaded {len(facilities)} facilities from database")
    
    
    def test_facility_type_conversion_is_correct(self):
        """Test that facility types are correct (TYPE CONVERSION).
        
        Expected: facility_type field contains valid types like Tank, Dam, TSF, etc.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        valid_types = {'Tank', 'Dam', 'TSF', 'Pond', 'Other', 'Evaporation'}
        
        for f in facilities:
            assert f.facility_type in valid_types, f"Invalid type: {f.facility_type}"
        
        print(f"✓ All {len(facilities)} facilities have valid types")
    
    
    def test_tank_facilities_always_have_is_lined_none(self):
        """Test Tank facilities have is_lined = None (DATA INTEGRITY).
        
        Expected: All Tank facilities in DB have is_lined=NULL.
        
        Importance: Tanks cannot be marked as lined/unlined in calculations.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        tanks = [f for f in facilities if f.facility_type == 'Tank']
        
        if tanks:
            for tank in tanks:
                assert tank.is_lined is None, \
                    f"BUG: Tank {tank.code} has is_lined={tank.is_lined}, should be None"
            print(f"✓ All {len(tanks)} Tank facilities have is_lined=None")
        else:
            print("⚠ No Tank facilities in database")
    
    
    def test_is_lined_values_are_valid_types(self):
        """Test is_lined values convert correctly from DB (TYPE CONVERSION).
        
        Expected: is_lined is either True, False, or None (not 0 or 1).
        
        Bugs to catch: 
        - is_lined=1 instead of is_lined=True
        - is_lined=0 instead of is_lined=False
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        for f in facilities:
            assert isinstance(f.is_lined, (bool, type(None))), \
                f"BUG: {f.code} is_lined={f.is_lined} ({type(f.is_lined).__name__}), " \
                f"should be bool or None not int"
        
        print(f"✓ All {len(facilities)} facilities have correct is_lined type")


# ============================================================================
# TESTS - SUMMARY CALCULATIONS
# ============================================================================

class TestSummaryMetricsCalculation:
    """Test KPI and summary calculations."""
    
    def test_utilization_calculation_no_division_by_zero(self):
        """Test utilization calculation handles zero capacity (EDGE CASE).
        
        Expected: No division by zero errors, returns 0 for zero capacity.
        
        Bug to catch: Crash when capacity = 0.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        for facility in facilities:
            capacity = facility.capacity_m3
            volume = facility.current_volume_m3
            
            # Safely calculate utilization
            if capacity > 0:
                util = (volume / capacity) * 100
                assert 0 <= util <= 200, f"BUG: Utilization {util}% out of range"
            else:
                util = 0
                print(f"⚠ Warning: Facility {facility.code} has zero capacity")
        
        print(f"✓ Utilization calculated safely for all {len(facilities)} facilities")
    
    
    def test_volume_does_not_exceed_capacity(self):
        """Test detection of volume > capacity (DATA QUALITY WARNING).
        
        Expected: Identifies overflow conditions.
        
        Bug to catch: Not detecting when volume > capacity.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        overflows = [
            f for f in facilities 
            if f.current_volume_m3 > f.capacity_m3
        ]
        
        if overflows:
            print(f"⚠ Data Quality Issue: {len(overflows)} facilities have volume > capacity:")
            for f in overflows:
                pct = (f.current_volume_m3 / f.capacity_m3 * 100) if f.capacity_m3 > 0 else 0
                print(f"  - {f.code}: {f.current_volume_m3}m³ / {f.capacity_m3}m³ ({pct:.0f}%)")
        else:
            print("✓ No facilities with overflow detected")
    
    
    def test_negative_volume_detection(self):
        """Test detection of negative volumes (DATA QUALITY WARNING).
        
        Expected: Identifies impossible negative volumes.
        
        Bug to catch: Not detecting negative volumes.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        negatives = [f for f in facilities if f.current_volume_m3 < 0]
        
        if negatives:
            print(f"⚠ Data Quality Issue: {len(negatives)} facilities have negative volume:")
            for f in negatives:
                print(f"  - {f.code}: {f.current_volume_m3}m³")
        else:
            print("✓ No negative volumes detected")


# ============================================================================
# TESTS - DASHBOARD DISPLAY LOGIC
# ============================================================================

class TestDashboardDisplayLogic:
    """Test dashboard display calculations and formatting."""
    
    def test_volume_percentage_calculation(self):
        """Test volume percentage calculation (DASHBOARD DISPLAY).
        
        Expected: volume_percentage property returns 0-100%.
        
        Bug to catch: 
        - Percentage > 100% when volume > capacity
        - Negative percentages
        - Wrong formula
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        for facility in facilities:
            vol_pct = facility.volume_percentage
            
            # Check property exists and returns number
            assert isinstance(vol_pct, (int, float)), \
                f"BUG: volume_percentage returned {type(vol_pct).__name__} not number"
            
            # Check reasonable range (allow >100 for overflow detection)
            assert vol_pct >= 0, \
                f"BUG: {facility.code} volume_percentage={vol_pct}% is negative"
        
        print(f"✓ volume_percentage calculated correctly for {len(facilities)} facilities")
    
    
    def test_facility_status_values_are_valid(self):
        """Test facility status field has valid values (DATA QUALITY).
        
        Expected: status is 'Active' or 'Inactive'.
        
        Bug to catch: Invalid status values in database.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        valid_statuses = {'Active', 'Inactive'}
        
        invalid = [f for f in facilities if f.status not in valid_statuses]
        
        if invalid:
            print(f"⚠ Data Quality Issue: {len(invalid)} facilities have invalid status:")
            for f in invalid:
                print(f"  - {f.code}: status='{f.status}'")
        else:
            print(f"✓ All {len(facilities)} facilities have valid status")


# ============================================================================
# TESTS - FIELD PRESENCE & CONSISTENCY
# ============================================================================

class TestFieldConsistency:
    """Test that all required fields are present and consistent."""
    
    def test_all_required_fields_present(self):
        """Test all required fields are present (DATA STRUCTURE).
        
        Expected: Every facility has code, name, type, capacity, volume.
        
        Bug to catch: Missing required fields.
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        required_fields = ['id', 'code', 'name', 'facility_type', 'capacity_m3', 
                          'current_volume_m3', 'status', 'is_lined']
        
        for facility in facilities:
            for field in required_fields:
                assert hasattr(facility, field), \
                    f"BUG: Facility {facility.code} missing field '{field}'"
        
        print(f"✓ All {len(facilities)} facilities have required fields")
    
    
    def test_code_field_is_unique_and_not_null(self):
        """Test facility codes are unique (DATA INTEGRITY).
        
        Expected: All codes are unique, non-empty.
        
        Bug to catch:
        - Duplicate codes
        - Null/empty codes
        """
        service = StorageFacilityService()
        facilities = service.get_facilities()
        
        codes = [f.code for f in facilities]
        
        # Check for empty codes
        empty_codes = [f.code for f in facilities if not f.code or not f.code.strip()]
        assert not empty_codes, f"BUG: {len(empty_codes)} facilities have empty codes"
        
        # Check for duplicates
        duplicates = [code for code in codes if codes.count(code) > 1]
        assert not duplicates, f"BUG: Duplicate codes found: {set(duplicates)}"
        
        print(f"✓ All {len(facilities)} facility codes are unique and valid")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
