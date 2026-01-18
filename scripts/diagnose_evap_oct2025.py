import sys
from pathlib import Path
from datetime import date

# Ensure src/ is on path
base = Path(__file__).parent.parent
sys.path.insert(0, str(base / 'src'))

from utils.water_balance_calculator import WaterBalanceCalculator
from database.db_manager import DatabaseManager


def main():
    calc_date = date(2025, 10, 1)
    db = DatabaseManager()
    calc = WaterBalanceCalculator()

    facilities = db.get_storage_facilities()
    regional_evap_mm = db.get_regional_evaporation_monthly(calc_date.month, year=calc_date.year)
    print(f"Regional evaporation (mm) for Oct {calc_date.year}: {regional_evap_mm}")
    print("\nPer-facility evaporation diagnostics (m3):")

    storage_change = calc.calculate_storage_change(calc_date, preloaded_facilities=facilities)
    total_evap = 0.0

    for f in facilities:
        fid = f.get('facility_id')
        code = f.get('facility_code')
        name = f.get('facility_name')
        area = float(f.get('surface_area') or 0.0)
        current_vol = float(f.get('current_volume') or 0.0)
        evap_mm_fac = db.get_facility_evaporation_monthly(fid, calc_date.month, year=calc_date.year)
        used_mm = evap_mm_fac if evap_mm_fac and evap_mm_fac > 0 else regional_evap_mm
        raw_evap_m3 = (used_mm / 1000.0) * area if area > 0 else 0.0
        # After patch: clamped to available current volume
        evap_m3 = min(raw_evap_m3, current_vol)
        total_evap += evap_m3

        drivers = storage_change['facilities'].get(code, {}).get('drivers', {})
        computed_evap = drivers.get('evaporation', 0.0)

        print(f"- {code} / {name}: area={area:,.0f} m2, current={current_vol:,.0f} m3, evap_mm={used_mm}, raw_evap={raw_evap_m3:,.0f}, clamped={evap_m3:,.0f}, calc_evap={computed_evap:,.0f}")

    print(f"\nTotal evaporation (Oct 2025): {total_evap:,.0f} m3")


if __name__ == '__main__':
    main()
