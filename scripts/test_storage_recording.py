#!/usr/bin/env python
r"""Test script to verify storage history recording after balance calculation.

Run with: .venv\Scripts\python scripts/test_storage_recording.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from services.calculation.balance_service import get_balance_service, reset_balance_service
from services.calculation.models import CalculationPeriod
import sqlite3

DB_PATH = Path(__file__).parent.parent / 'data' / 'water_balance.db'


def check_history_before():
    """Show current storage history for September 2025."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT facility_code, opening_volume_m3, closing_volume_m3, data_source, updated_at
        FROM storage_history
        WHERE year = 2025 AND month = 9
        ORDER BY facility_code
    """)
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*60)
    print("STORAGE HISTORY BEFORE CALCULATION (Sep 2025)")
    print("="*60)
    
    if not rows:
        print("  No records found for September 2025")
    else:
        for row in rows:
            print(f"  {row[0]}: Opening={row[1]:,.0f}, Closing={row[2]:,.0f} ({row[3]})")
    
    return len(rows)


def calculate_balance():
    """Run balance calculation for September 2025."""
    print("\n" + "="*60)
    print("RUNNING BALANCE CALCULATION (Sep 2025)")
    print("="*60)
    
    # Reset to get fresh service
    reset_balance_service()
    svc = get_balance_service()
    
    period = CalculationPeriod(month=9, year=2025)
    result = svc.calculate(period, force_recalculate=True)
    
    print(f"  Balance Error: {result.error_pct:.1f}%")
    print(f"  Storage Delta: {result.storage.delta_m3:,.0f} m³")
    print(f"  Opening: {result.storage.opening_m3:,.0f} m³")
    print(f"  Closing: {result.storage.closing_m3:,.0f} m³")
    
    return result


def check_history_after():
    """Show storage history after calculation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT facility_code, opening_volume_m3, closing_volume_m3, data_source, updated_at
        FROM storage_history
        WHERE year = 2025 AND month = 9
        ORDER BY facility_code
    """)
    rows = cursor.fetchall()
    
    print("\n" + "="*60)
    print("STORAGE HISTORY AFTER CALCULATION (Sep 2025)")
    print("="*60)
    
    if not rows:
        print("  No records found - HISTORY RECORDING FAILED!")
    else:
        for row in rows:
            print(f"  {row[0]}: Opening={row[1]:,.0f}, Closing={row[2]:,.0f} ({row[3]})")
            print(f"          Updated: {row[4]}")
    
    # Also check storage_facilities table for synced volumes
    print("\n" + "="*60)
    print("STORAGE FACILITIES TABLE (current_volume_m3)")
    print("="*60)
    
    cursor = conn.execute("""
        SELECT code, name, current_volume_m3, updated_at
        FROM storage_facilities
        WHERE status = 'active'
        ORDER BY code
    """)
    fac_rows = cursor.fetchall()
    
    for row in fac_rows:
        print(f"  {row[0]} ({row[1]}): {row[2]:,.0f} m³")
        print(f"          Updated: {row[3]}")
    
    conn.close()
    
    return len(rows)


if __name__ == '__main__':
    before_count = check_history_before()
    result = calculate_balance()
    after_count = check_history_after()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Records before: {before_count}")
    print(f"  Records after: {after_count}")
    
    if after_count > 0:
        print("  ✓ Storage history recording is WORKING!")
    else:
        print("  ✗ Storage history recording FAILED!")
