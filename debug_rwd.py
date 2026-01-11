#!/usr/bin/env python3
"""Debug: Show what's in the inflows dict."""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Disable logging noise
import logging
logging.disable(logging.CRITICAL)

from src.utils.water_balance_calculator import WaterBalanceCalculator

calc = WaterBalanceCalculator()

# Test getting inflows dict
test_date = datetime(2025, 10, 31)

inflows = calc.calculate_total_inflows(test_date, ore_tonnes=1000)
print("\nInflowsDict Keys:")
for key in sorted(inflows.keys()):
    print(f"  {key}: {inflows[key]}")

# Specifically check rwd_inflow
rwd = inflows.get('rwd_inflow', 'NOT FOUND')
print(f"\nrwd_inflow value: {rwd}")
