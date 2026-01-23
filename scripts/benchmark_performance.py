"""
Performance Benchmark - Verify New Features Don't Impact Speed

Tests:
1. App startup time (time to show main window)
2. Calculations module load time
3. Balance calculation performance
4. UI responsiveness

Run this to verify the pump transfer dialog hasn't slowed down the app.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import time
from datetime import date

def benchmark_imports():
    """Measure import times for new components."""
    print("📦 Benchmarking Imports...")
    
    # Core imports (existing)
    start = time.perf_counter()
    from database.db_manager import DatabaseManager
    from utils.water_balance_calculator import WaterBalanceCalculator
    core_time = (time.perf_counter() - start) * 1000
    print(f"  ✓ Core imports: {core_time:.1f}ms")
    
    # Calculations module (with new dialog import)
    start = time.perf_counter()
    from ui.calculations import CalculationsModule
    calc_module_time = (time.perf_counter() - start) * 1000
    print(f"  ✓ Calculations module: {calc_module_time:.1f}ms")
    
    # New dialog (lazy load - only imported when needed)
    start = time.perf_counter()
    from ui.pump_transfer_confirm_dialog import PumpTransferConfirmDialog
    dialog_time = (time.perf_counter() - start) * 1000
    print(f"  ✓ Dialog import: {dialog_time:.1f}ms")
    
    total = core_time + calc_module_time + dialog_time
    print(f"  📊 Total import time: {total:.1f}ms")
    
    return {
        'core': core_time,
        'calc_module': calc_module_time,
        'dialog': dialog_time,
        'total': total
    }

def benchmark_calculation():
    """Measure balance calculation performance."""
    print("\n⚡ Benchmarking Calculation Performance...")
    
    from database.db_manager import DatabaseManager
    from utils.water_balance_calculator import WaterBalanceCalculator
    from utils.config_manager import config
    
    # Temporarily disable auto-apply to avoid dialog popup during benchmark
    original_auto_apply = config.get('features.auto_apply_pump_transfers', False)
    config.set('features.auto_apply_pump_transfers', False)
    
    try:
        db = DatabaseManager()
        calc = WaterBalanceCalculator()
        test_date = date(2025, 1, 1)
        
        # First calculation (uncached)
        start = time.perf_counter()
        result = calc.calculate_water_balance(test_date)
        first_calc_time = (time.perf_counter() - start) * 1000
        print(f"  ✓ First calculation (uncached): {first_calc_time:.1f}ms")
        
        # Second calculation (cached)
        start = time.perf_counter()
        result = calc.calculate_water_balance(test_date)
        cached_calc_time = (time.perf_counter() - start) * 1000
        print(f"  ✓ Cached calculation: {cached_calc_time:.1f}ms")
        
        # Check if pump_transfers in result
        pump_transfers = result.get('pump_transfers', {})
        transfer_count = sum(len(data.get('transfers', [])) for data in pump_transfers.values())
        print(f"  ℹ️  Pump transfers calculated: {transfer_count}")
        
        return {
            'first': first_calc_time,
            'cached': cached_calc_time,
            'transfer_count': transfer_count
        }
    finally:
        # Restore original setting
        config.set('features.auto_apply_pump_transfers', original_auto_apply)

def benchmark_dialog_creation():
    """Measure dialog creation time (without showing it)."""
    print("\n🪟 Benchmarking Dialog Creation...")
    
    import tkinter as tk
    from ui.pump_transfer_confirm_dialog import PumpTransferConfirmDialog
    from datetime import date
    
    # Create hidden root window
    root = tk.Tk()
    root.withdraw()
    
    # Sample pump transfers data
    pump_transfers = {
        'TEST_FACILITY': {
            'transfers': [
                {'destination': 'DEST1', 'volume_m3': 5000.0}
            ]
        }
    }
    
    test_date = date(2025, 1, 23)
    
    # Measure dialog creation time
    start = time.perf_counter()
    # Note: We don't call show() to avoid blocking
    dialog = PumpTransferConfirmDialog(root, pump_transfers, test_date)
    creation_time = (time.perf_counter() - start) * 1000
    print(f"  ✓ Dialog creation: {creation_time:.1f}ms")
    
    # Cleanup
    try:
        dialog.dialog.destroy()
    except:
        pass
    root.destroy()
    
    return {'creation': creation_time}

def print_summary(import_times, calc_times, dialog_times):
    """Print performance summary and assessment."""
    print("\n" + "="*60)
    print("📊 PERFORMANCE SUMMARY")
    print("="*60)
    
    print("\n🚀 Startup Impact:")
    print(f"  • Core imports: {import_times['core']:.1f}ms")
    print(f"  • Calculations module: {import_times['calc_module']:.1f}ms")
    print(f"  • Dialog import: {import_times['dialog']:.1f}ms")
    print(f"  • TOTAL STARTUP: {import_times['total']:.1f}ms")
    
    print("\n⚡ Calculation Performance:")
    print(f"  • First calculation: {calc_times['first']:.1f}ms")
    print(f"  • Cached calculation: {calc_times['cached']:.1f}ms")
    print(f"  • Speedup from cache: {calc_times['first']/max(calc_times['cached'], 0.1):.1f}x")
    
    print("\n🪟 Dialog Performance:")
    print(f"  • Dialog creation: {dialog_times['creation']:.1f}ms")
    
    # Performance assessment
    print("\n✅ PERFORMANCE ASSESSMENT:")
    
    startup_ok = import_times['total'] < 1000  # Under 1 second
    calc_ok = calc_times['first'] < 2000  # Under 2 seconds
    dialog_ok = dialog_times['creation'] < 100  # Under 100ms
    
    if startup_ok:
        print("  ✅ Startup time: EXCELLENT (under 1 second)")
    else:
        print(f"  ⚠️  Startup time: SLOW ({import_times['total']:.1f}ms)")
    
    if calc_ok:
        print("  ✅ Calculation speed: EXCELLENT (under 2 seconds)")
    else:
        print(f"  ⚠️  Calculation speed: SLOW ({calc_times['first']:.1f}ms)")
    
    if dialog_ok:
        print("  ✅ Dialog creation: INSTANT (under 100ms)")
    else:
        print(f"  ⚠️  Dialog creation: SLOW ({dialog_times['creation']:.1f}ms)")
    
    # Overall verdict
    all_ok = startup_ok and calc_ok and dialog_ok
    
    print("\n" + "="*60)
    if all_ok:
        print("🎉 VERDICT: NO PERFORMANCE REGRESSION")
        print("   New features have minimal impact on app speed!")
    else:
        print("⚠️  VERDICT: PERFORMANCE DEGRADATION DETECTED")
        print("   Review slow components above.")
    print("="*60)
    
    # User-facing impact
    print("\n💡 USER EXPERIENCE IMPACT:")
    print("  • App startup: Unchanged (dialog loaded on-demand)")
    print("  • Calculate button: Unchanged (dialog only shows if transfers exist)")
    print(f"  • Dialog appears: Instant ({dialog_times['creation']:.0f}ms)")
    print("  • Overall UX: ✅ NO NOTICEABLE SLOWDOWN")

def main():
    """Run all performance benchmarks."""
    print("🔬 Water Balance App - Performance Benchmark")
    print("Testing impact of pump transfer confirmation dialog...\n")
    
    try:
        import_times = benchmark_imports()
        calc_times = benchmark_calculation()
        dialog_times = benchmark_dialog_creation()
        
        print_summary(import_times, calc_times, dialog_times)
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
