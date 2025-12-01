"""
Migration: Add is_lined column to storage_facilities table
"""

import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config

def migrate():
    """Add is_lined column to storage_facilities"""
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / config.get('database.path', 'data/water_balance.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(storage_facilities)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_lined' in columns:
            print("✅ Column 'is_lined' already exists in storage_facilities")
            return True
        
        print("🔧 Adding is_lined column to storage_facilities...")
        
        # Add the column (default 0 for unlined)
        cursor.execute("""
            ALTER TABLE storage_facilities 
            ADD COLUMN is_lined BOOLEAN DEFAULT 0
        """)
        
        # Update specific facilities that are typically lined
        # RWD and Process Water Dams are usually lined
        cursor.execute("""
            UPDATE storage_facilities 
            SET is_lined = 1 
            WHERE facility_code IN ('RWD', 'PWD', 'FWD')
        """)
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT facility_code, facility_name, is_lined FROM storage_facilities")
        facilities = cursor.fetchall()
        
        print("\n✅ Migration completed successfully!")
        print("\n📊 Storage Facilities Lining Status:")
        print("=" * 70)
        for code, name, is_lined in facilities:
            status = "🔵 Lined" if is_lined else "⚫ Unlined"
            print(f"{status:12} | {code:12} | {name}")
        
        return True
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
