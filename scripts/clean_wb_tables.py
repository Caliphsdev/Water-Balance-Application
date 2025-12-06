"""Clean migration: Drop all wb_* tables and recreate from scratch."""

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'water_balance.db'


def clean_wb_tables(db_path: Path = DB_PATH):
    """Drop all wb_* tables to start fresh."""
    conn = sqlite3.connect(str(db_path))
    conn.execute('PRAGMA foreign_keys=OFF')  # Temporarily disable to allow drops
    try:
        cur = conn.cursor()
        
        # Drop tables in reverse dependency order
        tables = [
            'wb_measurement_map',
            'wb_inter_area_transfers',
            'wb_outflow_destinations',
            'wb_inflow_sources',
            'wb_flow_connections',
            'wb_structures',
            'wb_areas',
        ]
        
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped {table}")
        
        conn.commit()
        print("\n✅ All wb_* tables dropped successfully.")
        
    finally:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.close()


if __name__ == '__main__':
    clean_wb_tables()
