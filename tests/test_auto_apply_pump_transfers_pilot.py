import pytest
from datetime import date

from src.database.db_manager import DatabaseManager
from src.utils.water_balance_calculator import WaterBalanceCalculator
from src.utils.config_manager import config


@pytest.mark.integration
def test_pilot_area_gating_applies_only_to_configured_area():
    """Pilot rollout: ensure auto-apply only affects facilities in pilot areas.

    Steps:
    1) Enable auto-apply and set scope to 'pilot-area' with pilot area 'UG2N'.
    2) Create a pair of facilities in UG2N and verify transfers apply.
    3) Create a pair of facilities in MERM and verify transfers are skipped.
    """
    # Configure feature flag and pilot areas (persisted)
    config.set('features.auto_apply_pump_transfers', True)
    config.set('features.auto_apply_pump_transfers_scope', 'pilot-area')
    config.set('features.auto_apply_pump_transfers_pilot_areas', ['UG2N'])

    db = DatabaseManager()
    
    # CRITICAL: Clean up ALL pump_transfer_events for test date BEFORE test starts
    # This prevents idempotency blocking from previous test runs (all facilities, not just test ones)
    test_date = date(2024, 11, 20)
    db.execute_update("DELETE FROM pump_transfer_events WHERE calc_date = ?", (test_date,))

    # Helper: get area_id by area_code from seeded schema
    def area_id(area_code: str) -> int:
        rows = db.execute_query("SELECT area_id FROM mine_areas WHERE area_code = ?", (area_code,))
        assert rows, f"Area code {area_code} not found in mine_areas"
        return rows[0]['area_id']

    # Facilities in pilot area UG2N
    dst_ug2n_id = db.add_storage_facility(
        facility_code='DST_UG2N',
        facility_name='Dest UG2N',
        facility_type='dam',
        area_id=area_id('UG2N'),
        total_capacity=100000.0,
        working_capacity=None,
        surface_area=0.0,
        pump_start_level=70.0,
        pump_stop_level=20.0,
        high_level_alarm=90.0,
        max_depth=None,
        purpose='raw_water',
        water_quality='process',
        current_volume=60000.0,
        description='Pilot dest dam UG2N',
        active=1,
        commissioned_date=None,
        feeds_to=None,
        evap_active=1,
        is_lined=0,
    )

    src_ug2n_id = db.add_storage_facility(
        facility_code='SRC_UG2N',
        facility_name='Src UG2N',
        facility_type='dam',
        area_id=area_id('UG2N'),
        total_capacity=100000.0,
        working_capacity=None,
        surface_area=0.0,
        pump_start_level=70.0,
        pump_stop_level=20.0,
        high_level_alarm=90.0,
        max_depth=None,
        purpose='raw_water',
        water_quality='process',
        current_volume=80000.0,
        description='Pilot src dam UG2N',
        active=1,
        commissioned_date=None,
        feeds_to='DST_UG2N',
        evap_active=1,
        is_lined=0,
    )

    # Facilities in non-pilot area MERM
    dst_merm_id = db.add_storage_facility(
        facility_code='DST_MERM',
        facility_name='Dest MERM',
        facility_type='dam',
        area_id=area_id('MERM'),
        total_capacity=100000.0,
        working_capacity=None,
        surface_area=0.0,
        pump_start_level=70.0,
        pump_stop_level=20.0,
        high_level_alarm=90.0,
        max_depth=None,
        purpose='raw_water',
        water_quality='process',
        current_volume=60000.0,
        description='Pilot dest dam MERM',
        active=1,
        commissioned_date=None,
        feeds_to=None,
        evap_active=1,
        is_lined=0,
    )

    src_merm_id = db.add_storage_facility(
        facility_code='SRC_MERM',
        facility_name='Src MERM',
        facility_type='dam',
        area_id=area_id('MERM'),
        total_capacity=100000.0,
        working_capacity=None,
        surface_area=0.0,
        pump_start_level=70.0,
        pump_stop_level=20.0,
        high_level_alarm=90.0,
        max_depth=None,
        purpose='raw_water',
        water_quality='process',
        current_volume=80000.0,
        description='Pilot src dam MERM',
        active=1,
        commissioned_date=None,
        feeds_to='DST_MERM',
        evap_active=1,
        is_lined=0,
    )

    try:
        calc = WaterBalanceCalculator()
        # Apply calculation for a given month (engine-only volumes drive transfers)
        # Use unique date per test run to avoid idempotency conflicts (defined at top)
        calc.calculate_water_balance(test_date)

        # Verify UG2N facilities updated (5% of capacity = 5000m3)
        rows = db.execute_query(
            "SELECT facility_code, current_volume FROM storage_facilities WHERE facility_code IN ('SRC_UG2N','DST_UG2N') ORDER BY facility_code"
        )
        vols = {r['facility_code']: float(r['current_volume'] or 0.0) for r in rows}
        assert 75000.0 == pytest.approx(vols['SRC_UG2N'], rel=0, abs=1.0)
        assert 65000.0 == pytest.approx(vols['DST_UG2N'], rel=0, abs=1.0)

        # Verify MERM facilities untouched (pilot gating skips non-pilot area)
        rows2 = db.execute_query(
            "SELECT facility_code, current_volume FROM storage_facilities WHERE facility_code IN ('SRC_MERM','DST_MERM') ORDER BY facility_code"
        )
        vols2 = {r['facility_code']: float(r['current_volume'] or 0.0) for r in rows2}
        # MERM facilities should remain unchanged (80k and 60k) because they're not in pilot area
        assert 80000.0 == pytest.approx(vols2['SRC_MERM'], rel=0, abs=1.0)
        assert 60000.0 == pytest.approx(vols2['DST_MERM'], rel=0, abs=1.0)
    finally:
        # Cleanup test facilities
        db.hard_delete_storage_facility(src_ug2n_id)
        db.hard_delete_storage_facility(dst_ug2n_id)
        db.hard_delete_storage_facility(src_merm_id)
        db.hard_delete_storage_facility(dst_merm_id)
