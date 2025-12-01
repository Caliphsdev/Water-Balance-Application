"""
Database Schema Migration Script
Adds missing columns to existing tables
"""

import sqlite3
from pathlib import Path

def migrate_database():
    """Add missing columns to water_sources and storage_facilities tables"""
    
    # Get database path
    db_path = Path(__file__).parent.parent.parent / 'data' / 'water_balance.db'
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("Starting database migration...")
        
        # Check and add missing columns to water_sources
        cursor.execute("PRAGMA table_info(water_sources)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'average_flow_rate' not in columns:
            print("Adding average_flow_rate to water_sources...")
            cursor.execute("ALTER TABLE water_sources ADD COLUMN average_flow_rate REAL")
        
        if 'flow_units' not in columns:
            print("Adding flow_units to water_sources...")
            cursor.execute("ALTER TABLE water_sources ADD COLUMN flow_units TEXT DEFAULT 'm³/month'")
        
        if 'reliability_factor' not in columns:
            print("Adding reliability_factor to water_sources...")
            cursor.execute("ALTER TABLE water_sources ADD COLUMN reliability_factor REAL DEFAULT 1.0")
        
        # Check and add missing columns to storage_facilities
        cursor.execute("PRAGMA table_info(storage_facilities)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'description' not in columns:
            print("Adding description to storage_facilities...")
            cursor.execute("ALTER TABLE storage_facilities ADD COLUMN description TEXT")
        
        if 'minimum_operating_level' not in columns:
            print("Adding minimum_operating_level to storage_facilities...")
            cursor.execute("ALTER TABLE storage_facilities ADD COLUMN minimum_operating_level REAL DEFAULT 0")
        
        if 'maximum_operating_level' not in columns:
            print("Adding maximum_operating_level to storage_facilities...")
            cursor.execute("ALTER TABLE storage_facilities ADD COLUMN maximum_operating_level REAL DEFAULT 100")
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Display updated schema
        print("\nUpdated water_sources columns:")
        cursor.execute("PRAGMA table_info(water_sources)")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
        print("\nUpdated storage_facilities columns:")
        cursor.execute("PRAGMA table_info(storage_facilities)")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
