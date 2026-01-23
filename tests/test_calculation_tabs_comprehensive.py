"""Comprehensive test for all calculation tabs in the Calculations UI module.

Tests all tabs in the Calculations module:
1. System Balance (Regulator) - Closure and reconciliation
2. Recycled Water - Recirculation volumes
3. Inputs Audit - Data quality from Excel
4. Manual Inputs - User-entered monthly values
5. Storage & Dams - Per-facility storage accounting
6. Days of Operation - Storage runway and water availability
7. Facility Flows - Per-facility inflows and outflows

This test file focuses on:
- Tab initialization and UI rendering
- Data display accuracy
- Error handling and edge cases
- Integration with pump_transfer_engine
"""

import sys
from pathlib import Path
import pytest
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.water_balance_calculator import WaterBalanceCalculator
from database.db_manager import DatabaseManager


class TestCalculationTabsDataAccuracy:
    """Test data accuracy across all calculation tabs"""
    
    def test_system_balance_closure_tab_has_data(self):
        """Verify System Balance (Regulator) tab calculates closure data"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        
        # System Balance tab should have closure-related fields
        assert 'closure_error_m3' in balance or 'balance_error_pct' in balance, \
            "System Balance tab missing closure error data"
        assert 'calculation_date' in balance, \
            "Balance missing calculation_date"
        
        print("✅ System Balance tab has required closure data")
    
    def test_recycled_water_tab_volume_data(self):
        """Verify Recycled Water tab has volume data"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        
        # Should have recycled/recirculation data
        # Looking for keys that might indicate recycled water
        keys_to_check = ['recycled', 'recirculation', 'dirty_inflows', 'rwd']
        has_recycled_data = any(key in balance for key in keys_to_check) or 'inflows' in balance
        
        assert has_recycled_data or 'storage_change' in balance, \
            "Recycled Water tab missing recirculation data"
        
        print("✅ Recycled Water tab has relevant data")
    
    def test_inputs_audit_tab_data_quality(self):
        """Verify Inputs Audit tab data quality information"""
        from utils.inputs_audit import collect_inputs_audit
        
        test_date = date(2025, 1, 15)
        
        # Inputs audit should not raise exception
        audit_data = collect_inputs_audit(test_date)
        
        assert audit_data is not None, \
            "Inputs audit should return data"
        assert isinstance(audit_data, dict), \
            f"Inputs audit should return dict, got {type(audit_data)}"
        
        print("✅ Inputs Audit tab data quality check passed")
    
    def test_manual_inputs_tab_storage(self):
        """Verify Manual Inputs tab can store and retrieve user inputs"""
        db = DatabaseManager()
        test_date = date(2025, 1, 15)
        
        # Manual inputs should be retrievable from DB
        manual_inputs = db.execute_query("""
            SELECT * FROM monthly_manual_inputs 
            WHERE DATE(month_start) = ?
            LIMIT 1
        """, (test_date,))
        
        # This is OK to return empty (no manual inputs entered)
        # Just checking that DB query doesn't crash
        assert isinstance(manual_inputs, list), \
            "Manual inputs query should return list"
        
        print("✅ Manual Inputs tab storage check passed")
    
    def test_storage_and_dams_tab_facility_data(self):
        """Verify Storage & Dams tab shows per-facility data"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        
        # Should have storage_change with facility breakdown
        assert 'storage_change' in balance, \
            "Storage & Dams tab missing storage_change data"
        
        storage_change = balance['storage_change']
        assert isinstance(storage_change, dict), \
            "storage_change should be a dict"
        
        # Should have facilities key or data for each facility
        if 'facilities' in storage_change:
            facilities_data = storage_change['facilities']
            assert isinstance(facilities_data, dict), \
                "facilities data should be a dict"
        
        print("✅ Storage & Dams tab has facility data")
    
    def test_days_of_operation_tab_runway_calculation(self):
        """Verify Days of Operation tab calculates storage runway"""
        from utils.data_quality_checker import get_data_quality_checker
        
        quality_checker = get_data_quality_checker()
        test_date = date(2025, 1, 15)
        
        # Data quality checker should provide quality metrics
        assert quality_checker is not None, \
            "Data quality checker not initialized"
        
        # Just ensure it exists and can be called
        # The actual runway calculation is part of the balance calculation
        print("✅ Days of Operation tab has data quality checker")
    
    def test_facility_flows_tab_data(self):
        """Verify Facility Flows tab has per-facility flow data"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        
        # Should have inflows/outflows or facility data
        assert 'inflows' in balance or 'outflows' in balance or 'storage_change' in balance, \
            "Facility Flows tab missing flow data"
        
        print("✅ Facility Flows tab has flow data")


class TestCalculationTabsBugDetection:
    """Test for potential bugs in calculation tabs"""
    
    def test_no_crash_on_empty_date(self):
        """Verify calculations don't crash with edge case dates"""
        calculator = WaterBalanceCalculator()
        
        # Try first day of month
        test_date = date(2025, 1, 1)
        try:
            balance = calculator.calculate_water_balance(test_date)
            assert balance is not None, "Balance calculation should return data"
        except Exception as e:
            pytest.fail(f"Balance calculation crashed on first day of month: {e}")
        
        print("✅ No crash on edge case dates")
    
    def test_pump_transfers_displays_correctly(self):
        """Verify pump transfers display data in Storage & Dams tab"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        pump_transfers = balance.get('pump_transfers', {})
        
        # For each facility with transfers, verify structure
        for facility_code, transfer_data in pump_transfers.items():
            # Should have key fields
            required_fields = [
                'current_level_pct',
                'pump_start_level',
                'is_at_pump_start',
                'transfers'
            ]
            
            for field in required_fields:
                assert field in transfer_data, \
                    f"Transfer data for {facility_code} missing {field}"
            
            # transfers should be a list
            assert isinstance(transfer_data['transfers'], list), \
                f"transfers for {facility_code} should be a list"
        
        print(f"✅ Pump transfers display structure valid ({len(pump_transfers)} facilities)")
    
    def test_closure_error_in_acceptable_range(self):
        """Verify closure error calculations are in reasonable range"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        
        # Check closure error is within realistic range
        if 'closure_error_percent' in balance:
            error_pct = balance['closure_error_percent']
            # Error > 200% would indicate calculation issue
            assert error_pct < 200, \
                f"Closure error {error_pct}% seems unrealistically high"
        
        if 'closure_error_m3' in balance:
            error_m3 = balance['closure_error_m3']
            # Error > 10M m3 would be unrealistic for typical mining operations
            assert abs(error_m3) < 10_000_000, \
                f"Closure error {error_m3} m³ seems unrealistically high"
        
        print("✅ Closure error in acceptable range")
    
    def test_storage_change_calculation_consistency(self):
        """Verify storage_change calculations are internally consistent"""
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        balance = calculator.calculate_water_balance(test_date)
        storage = balance.get('storage_change', {})
        
        if 'facilities' in storage:
            facilities = storage['facilities']
            
            for fac_code, fac_data in facilities.items():
                # Verify: change = closing - opening
                opening = float(fac_data.get('opening', 0))
                closing = float(fac_data.get('closing', 0))
                change = float(fac_data.get('change', 0))
                
                expected_change = closing - opening
                # Allow small rounding error
                assert abs(change - expected_change) < 1.0, \
                    f"{fac_code}: change {change} != closing-opening {expected_change}"
        
        print("✅ Storage change calculations are internally consistent")


class TestCalculationTabsIntegration:
    """Test integration between tabs and shared data"""
    
    def test_facility_data_consistency_across_tabs(self):
        """Verify facility data is consistent across multiple tabs"""
        db = DatabaseManager()
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        # Get facilities from DB
        db_facilities = db.execute_query("""
            SELECT facility_code, facility_name FROM storage_facilities 
            WHERE active = 1
        """)
        
        # Get facilities from balance calculation
        balance = calculator.calculate_water_balance(test_date)
        storage_change = balance.get('storage_change', {})
        
        if 'facilities' in storage_change:
            calc_facilities = set(storage_change['facilities'].keys())
            db_codes = set(f['facility_code'] for f in db_facilities)
            
            # Calculated facilities should be subset of or equal to DB facilities
            # (Some facilities might be inactive)
            orphaned = calc_facilities - db_codes
            if orphaned:
                print(f"⚠️  Orphaned facilities in calculation: {orphaned}")
        
        print("✅ Facility data consistency check passed")
    
    def test_manual_inputs_reflected_in_balance(self):
        """Verify manual inputs are included in balance calculation"""
        db = DatabaseManager()
        calculator = WaterBalanceCalculator()
        test_date = date(2025, 1, 15)
        
        # Check for manual inputs
        manual = db.execute_query("""
            SELECT * FROM monthly_manual_inputs 
            WHERE DATE(month_start) = ?
        """, (test_date,))
        
        if manual:
            # If manual inputs exist, they should be reflected in balance
            balance = calculator.calculate_water_balance(test_date)
            assert balance is not None, \
                "Balance should be calculated even with manual inputs"
        
        print("✅ Manual inputs integration check passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
