"""Test Tank facility lined status storage (UNIT TEST).

Verifies that Tank facilities always store is_lined as NULL (None) in database.
This ensures Tanks cannot be marked as lined/unlined (data integrity).
"""

import sqlite3
from pathlib import Path


def test_tank_is_lined_null():
    """Verify Tank facilities have is_lined = NULL in database."""
    # Use relative path from tests/ directory
    db_path = Path(__file__).parent.parent / 'data' / 'water_balance.db'
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get any Tank facility
    c.execute('SELECT code, facility_type, is_lined FROM storage_facilities WHERE facility_type="Tank" LIMIT 1')
    r = c.fetchone()
    
    if r:
        code, facility_type, is_lined = r
        print(f'Tank facility: Code={code}, Type={facility_type}, is_lined={is_lined} (None means NULL)')
        
        # Assert is_lined is NULL for Tank
        assert is_lined is None, f"Tank {code} should have is_lined=NULL, but got {is_lined}"
        print('✓ PASS: is_lined is NULL for Tank')
    else:
        print('⚠ No Tank facilities found in database')


if __name__ == '__main__':
    test_tank_is_lined_null()
