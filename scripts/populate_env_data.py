"""Populate 2025 environmental data for testing.

Adds monthly rainfall and evaporation data for 2025 (Jan-Dec).
Uses typical South African Highveld seasonal patterns.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import DatabaseManager

# Typical monthly values for SA Highveld mining region
# Rainfall: wet season Nov-Mar, dry Apr-Oct
# Evaporation: higher in summer, lower in winter
MONTHLY_DATA_2025 = [
    # (month, rainfall_mm, evaporation_mm)
    (1, 120, 180),   # Jan - wet summer
    (2, 110, 170),   # Feb - wet summer
    (3, 80, 160),    # Mar - late summer
    (4, 40, 140),    # Apr - autumn
    (5, 15, 120),    # May - dry
    (6, 5, 100),     # Jun - dry winter
    (7, 5, 100),     # Jul - dry winter
    (8, 10, 120),    # Aug - late winter
    (9, 25, 150),    # Sep - spring
    (10, 60, 170),   # Oct - spring
    (11, 90, 180),   # Nov - early summer
    (12, 100, 185),  # Dec - summer
]


def main():
    db = DatabaseManager()
    conn = db.get_connection()
    
    # Check existing data for 2025
    cursor = conn.execute('SELECT COUNT(*) as cnt FROM environmental_data WHERE year = 2025')
    row = cursor.fetchone()
    existing = row['cnt'] if row else 0
    
    if existing > 0:
        print(f'2025 data already exists ({existing} rows). Skipping insert.')
        conn.close()
        return
    
    # Check table structure first
    cursor = conn.execute('PRAGMA table_info(environmental_data)')
    cols = cursor.fetchall()
    col_names = [c['name'] for c in cols]
    print(f'Table columns: {col_names}')
    
    # Insert 2025 data
    print('\nInserting 2025 environmental data...')
    
    for month, rainfall, evap in MONTHLY_DATA_2025:
        try:
            conn.execute('''
                INSERT INTO environmental_data (year, month, rainfall_mm, evaporation_mm)
                VALUES (?, ?, ?, ?)
            ''', (2025, month, rainfall, evap))
            print(f'  2025-{month:02d}: rainfall={rainfall}mm, evap={evap}mm')
        except Exception as e:
            print(f'  2025-{month:02d}: Error - {e}')
    
    conn.commit()
    conn.close()
    
    print('\nDone! 2025 environmental data populated.')


if __name__ == '__main__':
    main()
