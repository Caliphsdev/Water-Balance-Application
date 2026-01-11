#!/usr/bin/env python3
"""Check what RWD value the calculator retrieves."""

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

# Test getting RWD for different dates
test_dates = [
    datetime(2025, 10, 31),
    datetime(2025, 9, 30),
    datetime(2025, 8, 31),
]

for test_date in test_dates:
    try:
        result = calc.calculate_water_balance(test_date, ore_tonnes=1000)
        rwd_val = result.get('inflows', {}).get('rwd_inflow', 0)
        print(f"[{test_date.strftime('%Y-%m-%d')}] RWD = {rwd_val} m³")
    except Exception as e:
        print(f"[{test_date.strftime('%Y-%m-%d')}] Error: {e}")
