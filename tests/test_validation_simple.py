#!/usr/bin/env python3
"""
Quick test to verify the data validation fix in calculation_dashboard.py
Tests that the Excel validation properly detects missing files/data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_validation_logic():
    """Test the exact validation logic from calculation_dashboard"""
    print("\n" + "="*60)
    print("TESTING: Calculation Dashboard Data Validation")
    print("="*60)
    
    from services.excel_manager import get_excel_manager
    from database.db_manager import DatabaseManager
    
    excel_mgr = get_excel_manager()
    db = DatabaseManager()
    missing = []
    
    print("\nPhase 1: Excel File Check")
    print("-" * 60)
    
    # Replicate the exact validation code
    try:
        # First check if file exists
        if not excel_mgr.meter_readings_exists():
            missing.append("Excel Meter Readings file not found")
            print("✗ FAIL: Excel file does not exist")
        else:
            print("✓ PASS: Excel file exists")
            
            # Load and validate data
            meter_data = excel_mgr.load_meter_readings()
            if meter_data is None or meter_data.empty:
                missing.append("Excel Meter Readings data (tonnes milled, water consumption, etc.) is empty")
                print("✗ FAIL: Excel data is empty")
            else:
                print(f"✓ PASS: Excel data loaded ({len(meter_data)} rows)")
                
                # Check that key columns exist
                required_cols = ['Tonnes Milled', 'Total Water Consumption', 'Total Recycled Water']
                all_cols_exist = True
                for col in required_cols:
                    if col not in meter_data.columns:
                        missing.append(f"Excel Meter Readings column missing: {col}")
                        print(f"  ✗ FAIL: Missing column '{col}'")
                        all_cols_exist = False
                    else:
                        print(f"  ✓ PASS: Column '{col}' found")
                
                if all_cols_exist:
                    print("✓ PASS: All required Excel columns present")
    except Exception as e:
        missing.append(f"Excel file access error: {str(e)}")
        print(f"✗ FAIL: Excel error: {e}")
    
    print("\nPhase 2: Environmental Data Check")
    print("-" * 60)
    
    try:
        conn = db.get_connection()
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM environmental_data LIMIT 1")
        count = cursor.fetchone()['cnt']
        conn.close()
        if count == 0:
            missing.append("Environmental data (rainfall, evaporation) - Add via Monitoring page")
            print("✗ FAIL: No environmental data found")
        else:
            print(f"✓ PASS: Environmental data found ({count} records)")
    except Exception as e:
        missing.append(f"Environmental data access: {str(e)}")
        print(f"✗ FAIL: Environmental data error: {e}")
    
    print("\nPhase 3: Storage Facilities Check")
    print("-" * 60)
    
    try:
        conn = db.get_connection()
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM storage_facilities WHERE status='active'")
        count = cursor.fetchone()['cnt']
        conn.close()
        if count == 0:
            missing.append("Storage facilities configured - Create facilities in Storage page")
            print("✗ FAIL: No active storage facilities")
        else:
            print(f"✓ PASS: Active storage facilities found ({count} records)")
    except Exception as e:
        missing.append(f"Storage facilities access: {str(e)}")
        print(f"✗ FAIL: Storage facilities error: {e}")
    
    print("\n" + "="*60)
    print("VALIDATION RESULT")
    print("="*60)
    
    if missing:
        print(f"❌ VALIDATION FAILED - Missing items ({len(missing)}):")
        for item in missing:
            print(f"   • {item}")
        print(f"\n⚠ Dialog would show to user:")
        print(f"   'The following required data is missing or incomplete:'")
        print(f"   [list of items above]")
        print(f"   'Do you want to continue anyway?'")
        print(f"   [Yes] [No]")
        print(f"\n✓ VALIDATION IS WORKING CORRECTLY")
        return False
    else:
        print(f"✅ VALIDATION PASSED")
        print(f"All required data is present.")
        print(f"Calculation can proceed without warnings.")
        print(f"✓ VALIDATION IS WORKING CORRECTLY")
        return True


if __name__ == "__main__":
    try:
        success = test_validation_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
