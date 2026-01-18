import sys
from pathlib import Path

# Ensure src on path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from database.db_manager import DatabaseManager
from utils.water_balance_calculator import WaterBalanceCalculator

def main():
    db = DatabaseManager()
    calc = WaterBalanceCalculator()
    facilities = db.get_storage_facilities(active_only=False, use_cache=False)
    lined_rate = calc.get_constant('lined_seepage_rate_pct', 0.1) / 100.0
    unlined_rate = calc.get_constant('unlined_seepage_rate_pct', 0.5) / 100.0
    print(f"Lined rate: {lined_rate*100:.2f}% | Unlined rate: {unlined_rate*100:.2f}%\n")
    for f in facilities:
        lined = f.get('is_lined', 0) == 1
        vol = float(f.get('current_volume') or 0.0)
        rate = lined_rate if lined else unlined_rate
        seepage_loss = vol * rate
        print(f"{f['facility_code']:<12} lined={lined:<5} vol={vol:,.0f} m3  monthly_seepage={seepage_loss:,.0f} m3")

if __name__ == "__main__":
    main()
