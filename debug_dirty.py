#!/usr/bin/env python3
"""Debug: Show what balance_services_legacy returns."""

import sys
from pathlib import Path
from datetime import datetime, date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Disable logging noise
import logging
logging.disable(logging.CRITICAL)

from src.utils.balance_services_legacy import LegacyBalanceServices
from src.utils.balance_services import DataQualityFlags

test_date = date(2025, 10, 31)
flags = DataQualityFlags()

legacy = LegacyBalanceServices()
dirty = legacy.get_dirty(test_date, flags)

print(f"\nDirty Inflows:")
print(f"  Total: {dirty.total}")
print(f"  Components: {dirty.components}")
