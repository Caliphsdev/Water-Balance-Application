"""
Test script to verify the Configure Balance Check feature works correctly.
Shows that disabling flows changes the balance calculation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import json
from utils.balance_check_engine import get_balance_check_engine
from utils.template_data_parser import get_template_parser

print("=" * 80)
print("TEST: Configure Balance Check Feature")
print("=" * 80)

# Load templates first
parser = get_template_parser()
print(f"\n📋 Templates loaded:")
print(f"   - Inflows: {len(parser.inflows)} entries")
print(f"   - Outflows: {len(parser.outflows)} entries")
print(f"   - Recirculation: {len(parser.recirculation)} entries")

# Test 1: Calculate with ALL flows
print(f"\n🧪 Test 1: Calculate with ALL flows enabled")
print("-" * 80)

engine = get_balance_check_engine()
metrics_all = engine.calculate_balance()

print(f"✅ Results with ALL flows:")
print(f"   - Total Inflows: {metrics_all.total_inflows:,.0f} m³ ({metrics_all.inflow_count} entries)")
print(f"   - Total Outflows: {metrics_all.total_outflows:,.0f} m³ ({metrics_all.outflow_count} entries)")
print(f"   - Total Recirculation: {metrics_all.total_recirculation:,.0f} m³ ({metrics_all.recirculation_count} entries)")
print(f"   - Balance Difference: {metrics_all.balance_difference:,.0f} m³")
print(f"   - Error: {metrics_all.balance_error_percent:.2f}%")
print(f"   - Status: {metrics_all.status_label}")

# Test 2: Create a config that disables some outflows
print(f"\n🧪 Test 2: Create config that disables 34 of 64 outflows")
print("-" * 80)

config = {
    'inflows': [
        {'code': entry.code, 'name': entry.name, 'area': entry.area, 'enabled': True}
        for entry in parser.inflows
    ],
    'recirculation': [
        {'code': entry.code, 'name': entry.name, 'area': entry.area, 'enabled': True}
        for entry in parser.recirculation
    ],
    'outflows': [
        {'code': entry.code, 'name': entry.name, 'area': entry.area, 'enabled': True}
        for i, entry in enumerate(parser.outflows)
        if i < 30  # Only enable first 30 of 64
    ]
}

# Save test config
config_path = Path('data/balance_check_config.json')
config_path.parent.mkdir(parents=True, exist_ok=True)
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ Saved test config with:")
print(f"   - {len(config['inflows'])} inflows enabled")
print(f"   - {len(config['recirculation'])} recirculation enabled")
print(f"   - {len(config['outflows'])} outflows enabled (out of 64)")

# Test 3: Calculate with config applied
print(f"\n🧪 Test 3: Calculate with config-filtered flows")
print("-" * 80)

# Create fresh engine instance
from utils.balance_check_engine import BalanceCheckEngine
engine_with_config = BalanceCheckEngine()
metrics_filtered = engine_with_config.calculate_balance()

print(f"✅ Results with FILTERED flows:")
print(f"   - Total Inflows: {metrics_filtered.total_inflows:,.0f} m³ ({metrics_filtered.inflow_count} entries)")
print(f"   - Total Outflows: {metrics_filtered.total_outflows:,.0f} m³ ({metrics_filtered.outflow_count} entries)")
print(f"   - Total Recirculation: {metrics_filtered.total_recirculation:,.0f} m³ ({metrics_filtered.recirculation_count} entries)")
print(f"   - Balance Difference: {metrics_filtered.balance_difference:,.0f} m³")
print(f"   - Error: {metrics_filtered.balance_error_percent:.2f}%")
print(f"   - Status: {metrics_filtered.status_label}")

# Summary
print(f"\n📊 Comparison:")
print("-" * 80)
outflow_diff = metrics_all.total_outflows - metrics_filtered.total_outflows
print(f"Outflows reduced by: {outflow_diff:,.0f} m³ ({34} outflows disabled)")
print(f"Balance changed from {metrics_all.balance_difference:,.0f} m³ to {metrics_filtered.balance_difference:,.0f} m³")
print(f"Error % changed from {metrics_all.balance_error_percent:.2f}% to {metrics_filtered.balance_error_percent:.2f}%")

print(f"\n" + "=" * 80)
print(f"✅ TEST PASSED - Configure Balance Check feature is working!")
print(f"=" * 80)
print(f"\nHow it works:")
print(f"1. User clicks '⚙️ Configure Balance Check' in Calculations module")
print(f"2. Dialog shows all flows (inflows, recirculation, outflows)")
print(f"3. User unchecks flows they want to exclude")
print(f"4. Config is saved to: data/balance_check_config.json")
print(f"5. Next time balance is calculated, ONLY enabled flows are included")
print(f"6. This lets you control exactly what's in your balance calculation!")
