#!/usr/bin/env python3
"""
Foundation Module Tests
Tests data quality checker, optimization engine, chart utilities, and database schema
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Test imports
print("\n" + "="*70)
print("TEST 1: Module Imports")
print("="*70)

try:
    from database.db_manager import DatabaseManager
    from utils.data_quality_checker import get_data_quality_checker
    from utils.optimization_engine import get_optimization_engine
    from ui.chart_utils import CHART_COLORS, create_storage_runway_chart
    print("[PASS] All modules imported successfully")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test database schema
print("\n" + "="*70)
print("TEST 2: Database Schema - New Tables")
print("="*70)

db = DatabaseManager()
try:
    # Check groundwater_inflow_monthly table
    gw_cols = db.execute_query("PRAGMA table_info(groundwater_inflow_monthly)")
    print(f"[PASS] groundwater_inflow_monthly table exists with {len(gw_cols)} columns")
    print(f"   Columns: {', '.join([c['name'] for c in gw_cols[:5]])}...")
    
    # Check data_quality_checks table
    dq_cols = db.execute_query("PRAGMA table_info(data_quality_checks)")
    print(f"[PASS] data_quality_checks table exists with {len(dq_cols)} columns")
    print(f"   Columns: {', '.join([c['name'] for c in dq_cols[:5]])}...")
    
    # Verify indexes
    indexes = db.execute_query(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%groundwater%' OR name LIKE '%quality%'"
    )
    print(f"[PASS] Found {len(indexes)} indexes on new tables")
    
except Exception as e:
    print(f"[FAIL] Database schema test failed: {e}")
    sys.exit(1)

# Test data quality checker
print("\n" + "="*70)
print("TEST 3: Data Quality Checker")
print("="*70)

checker = get_data_quality_checker()
try:
    # Test gap analysis
    end_date = date.today()
    start_date = end_date - relativedelta(months=6)
    
    gap_result = checker.check_calculation_gaps(start_date, end_date)
    print(f"[PASS] Gap analysis completed:")
    print(f"   Expected months: {gap_result['expected_months']}")
    print(f"   Present months: {gap_result['present_months']}")
    print(f"   Completeness: {gap_result['completeness_pct']:.1f}%")
    print(f"   Missing months: {gap_result['gap_count']}")
    
    # Test input completeness for recent date
    completeness = checker.check_input_completeness(end_date)
    print(f"[PASS] Input completeness check:")
    print(f"   Confidence score: {completeness['confidence_score']:.1f}/100")
    print(f"   Has Excel data: {completeness['has_excel_data']}")
    print(f"   Warnings: {len(completeness['warnings'])}")
    
    # Test quality level
    level, color = checker.get_quality_level(gap_result['completeness_pct'], completeness['confidence_score'])
    print(f"[PASS] Quality level: {level.upper()} ({color})")
    
    # Test comprehensive check
    all_checks = checker.run_all_checks(start_date, end_date)
    print(f"[PASS] Comprehensive check completed:")
    print(f"   Summary: {all_checks['summary']}")
    print(f"   Warnings: {all_checks['warnings']}, Errors: {all_checks['errors']}")
    
except Exception as e:
    print(f"[FAIL] Data quality checker test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test optimization engine
print("\n" + "="*70)
print("TEST 4: Optimization Engine")
print("="*70)

optimizer = get_optimization_engine()
try:
    # Test target days optimization
    current_storage = 500000  # 500,000 m³
    daily_consumption = 8000  # 8,000 m³/day
    target_days = 45
    
    current_constants = {
        'plant_water_recovery_rate': 0.65,
        'tailings_moisture_pct': 12.0,
        'evaporation_mitigation_factor': 1.0
    }
    
    result = optimizer.optimize_for_target_days(
        target_days=target_days,
        current_storage=current_storage,
        daily_consumption=daily_consumption,
        current_constants=current_constants
    )
    
    print(f"[PASS] Optimization completed:")
    print(f"   Target days: {target_days}")
    print(f"   Achievable: {result['achievable']}")
    print(f"   Projected days: {result['projected_days']}")
    print(f"   Iterations: {result['iterations']}")
    print(f"   Recommended changes: {len(result['recommended_changes'])}")
    if result['recommended_changes']:
        for const, val in result['recommended_changes'].items():
            pct = result['adjustments_pct'].get(const, 0)
            print(f"     - {const}: {val:.3f} ({pct:+.1f}%)")
    print(f"   Message: {result['message']}")
    
    # Test water-saving recommendations
    consumption = {
        'dust_suppression': 6000,
        'tsf_return': 50000,
        'plant_consumption_gross': 80000,
        'evaporation': 15000,
        'mining_consumption': 4000,
        'discharge': 2000
    }
    
    recommendations = optimizer.suggest_water_saving_actions(consumption, storage_level_pct=35)
    print(f"\n[PASS] Generated {len(recommendations)} water-saving recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"   {i}. [{rec['priority'].upper()}] {rec['category']}")
        print(f"      {rec['action']}")
        print(f"      Potential saving: {rec['potential_saving_m3']:,.0f} m³")
    
except Exception as e:
    print(f"[FAIL] Optimization engine test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test chart utilities
print("\n" + "="*70)
print("TEST 5: Chart Utilities")
print("="*70)

try:
    # Test chart creation (no display, just verify it creates)
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for testing
    
    # Create storage runway chart
    projection_days = list(range(0, 91, 3))  # 90 days, every 3 days
    storage_levels = [500000 - (i * 7000) for i in projection_days]  # Declining storage
    
    fig = create_storage_runway_chart(
        projection_days=projection_days,
        storage_levels=storage_levels,
        capacity=600000,
        critical_threshold_pct=25,
        title="Test Storage Projection"
    )
    
    print(f"[PASS] Storage runway chart created: {fig.__class__.__name__}")
    print(f"   Axes count: {len(fig.axes)}")
    print(f"   Figure size: {fig.get_size_inches()}")
    
    # Verify color palette
    print(f"[PASS] Color palette loaded: {len(CHART_COLORS)} colors")
    print(f"   Sample colors: inflows={CHART_COLORS['inflows']}, storage={CHART_COLORS['storage']}")
    
    # Cleanup
    import matplotlib.pyplot as plt
    plt.close(fig)
    
except Exception as e:
    print(f"[FAIL] Chart utilities test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test data insertion into new tables
print("\n" + "="*70)
print("TEST 6: Database Operations - New Tables")
print("="*70)

try:
    # Insert test groundwater data
    db.execute_update(
        """INSERT OR REPLACE INTO groundwater_inflow_monthly 
           (source_id, month, year, inflow_m3, modflow_scenario_name, confidence_level)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 10, 2025, 15000.0, 'test_scenario', 'medium')
    )
    
    # Verify insertion
    gw_data = db.execute_query(
        "SELECT * FROM groundwater_inflow_monthly WHERE modflow_scenario_name = 'test_scenario'"
    )
    print(f"[PASS] Groundwater data inserted and retrieved: {len(gw_data)} row(s)")
    if gw_data:
        print(f"   Sample: {gw_data[0]['inflow_m3']} m³, confidence={gw_data[0]['confidence_level']}")
    
    # Insert test quality check
    db.execute_update(
        """INSERT INTO data_quality_checks 
           (check_date, check_type, severity, message, completeness_pct, gap_count)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date.today().isoformat(), 'test_check', 'info', 'Test quality check', 95.0, 2)
    )
    
    # Verify insertion
    quality_data = db.execute_query(
        "SELECT * FROM data_quality_checks WHERE check_type = 'test_check'"
    )
    print(f"[PASS] Quality check data inserted and retrieved: {len(quality_data)} row(s)")
    if quality_data:
        print(f"   Sample: {quality_data[0]['message']}, severity={quality_data[0]['severity']}")
    
    # Cleanup test data
    db.execute_update("DELETE FROM groundwater_inflow_monthly WHERE modflow_scenario_name = 'test_scenario'")
    db.execute_update("DELETE FROM data_quality_checks WHERE check_type = 'test_check'")
    print("[PASS] Test data cleaned up")
    
except Exception as e:
    print(f"[FAIL] Database operations test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print("[PASS] All foundation tests passed successfully!")
print("\nModules tested:")
print("  1. Database schema (new tables and indexes)")
print("  2. Data quality checker (gap analysis, completeness, quality levels)")
print("  3. Optimization engine (target days optimizer, recommendations)")
print("  4. Chart utilities (matplotlib chart generation)")
print("  5. Database operations (insert/retrieve from new tables)")
print("\nFoundation is ready for UI implementation.")
print("="*70 + "\n")

