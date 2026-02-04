#!/usr/bin/env python
"""Check storage database schema and data for balance calculation debugging.

This script analyzes the storage_facilities and storage_history tables
to identify issues with storage tracking in balance calculations.

Data Source: SQLite database at data/water_balance.db
Output: Schema details, sample data, and potential issues
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlite3

def main():
    """Analyze storage schema and data."""
    conn = sqlite3.connect("data/water_balance.db")
    cursor = conn.cursor()
    
    print("=" * 60)
    print("STORAGE SCHEMA ANALYSIS")
    print("=" * 60)
    
    # Check storage_facilities table
    print("\n=== storage_facilities columns ===")
    cursor.execute("PRAGMA table_info(storage_facilities)")
    for row in cursor.fetchall():
        print(f"  {row[1]}: {row[2]}")
    
    # Check if storage_history exists
    print("\n=== storage_history table ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='storage_history'")
    exists = cursor.fetchone()
    print(f"  Exists: {bool(exists)}")
    
    if exists:
        cursor.execute("PRAGMA table_info(storage_history)")
        for row in cursor.fetchall():
            print(f"  {row[1]}: {row[2]}")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM storage_history")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count}")
        
        if count > 0:
            print("\n  Sample data:")
            cursor.execute("SELECT * FROM storage_history LIMIT 5")
            for row in cursor.fetchall():
                print(f"    {row}")
    
    # Sample facilities data
    print("\n=== storage_facilities data ===")
    cursor.execute("SELECT code, name, capacity_m3, current_volume_m3, status FROM storage_facilities")
    facilities = cursor.fetchall()
    print(f"  Total facilities: {len(facilities)}")
    for row in facilities[:10]:
        code, name, capacity, current, status = row
        fill_pct = (current / capacity * 100) if capacity else 0
        print(f"  {code}: {name[:30]:<30} Capacity: {capacity:>12,.0f} m³  Current: {current:>12,.0f} m³ ({fill_pct:.1f}%)")
    
    # Calculate totals
    total_capacity = sum(r[2] or 0 for r in facilities)
    total_current = sum(r[3] or 0 for r in facilities)
    print(f"\n  TOTAL capacity: {total_capacity:,.0f} m³")
    print(f"  TOTAL current:  {total_current:,.0f} m³")
    
    # Check for transfers table
    print("\n=== transfers table ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transfers'")
    if cursor.fetchone():
        print("  Exists: True")
        cursor.execute("PRAGMA table_info(transfers)")
        for row in cursor.fetchall():
            print(f"  {row[1]}: {row[2]}")
        cursor.execute("SELECT COUNT(*) FROM transfers")
        print(f"  Row count: {cursor.fetchone()[0]}")
    else:
        print("  Exists: False")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
