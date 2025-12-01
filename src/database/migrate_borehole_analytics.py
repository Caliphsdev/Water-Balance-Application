"""
Database Migration: Add Borehole Analytics Support
Adds fields for monitoring boreholes, water levels, and quality parameters
"""

import sqlite3
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.app_logger import logger


class BoreholeAnalyticsMigration:
    """Migrate database to support borehole analytics"""
    
    def __init__(self):
        self.db = DatabaseManager()
        
    def backup_database(self):
        """Create backup before migration"""
        from utils.backup_manager import BackupManager
        backup = BackupManager()
        backup_file = backup.create_backup(f"pre_borehole_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        logger.info(f"Backup created: {backup_file}")
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    
    def migrate(self):
        """Run the migration"""
        print("\n" + "="*60)
        print("Borehole Analytics Migration")
        print("="*60)
        
        # Step 1: Backup
        print("\n📦 Step 1: Creating backup...")
        self.backup_database()
        
        # Step 2: Add source_purpose to water_sources
        print("\n🔧 Step 2: Adding source_purpose field...")
        self._add_source_purpose()
        
        # Step 3: Add quality fields to measurements
        print("\n🔧 Step 3: Adding water quality fields to measurements...")
        self._add_measurement_fields()
        
        # Step 4: Create borehole_details table
        print("\n🔧 Step 4: Creating borehole_details table...")
        self._create_borehole_details_table()
        
        # Step 5: Add indexes
        print("\n🔧 Step 5: Adding performance indexes...")
        self._add_indexes()
        
        # Step 6: Update existing data
        print("\n🔧 Step 6: Updating existing borehole data...")
        self._update_existing_data()
        
        print("\n" + "="*60)
        print("✅ Migration Complete!")
        print("="*60)
        print("\nNew Features Available:")
        print("  • Borehole purpose classification (Abstraction/Monitoring/Static)")
        print("  • Water level measurements")
        print("  • Water quality tracking (pH, conductivity, temperature, turbidity)")
        print("  • Borehole technical details")
        print("\nNext Steps:")
        print("  1. Restart the application")
        print("  2. Access Data Quality in Settings > Data Quality tab")
        print("  3. Import water level/quality data using new templates")
        
    def _add_source_purpose(self):
        """Add source_purpose column to water_sources"""
        try:
            self.db.execute_query(
                "ALTER TABLE water_sources ADD COLUMN source_purpose TEXT DEFAULT 'ABSTRACTION'"
            )
            print("   ✓ Added source_purpose field (default: ABSTRACTION)")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("   ℹ source_purpose field already exists")
            else:
                raise
    
    def _add_measurement_fields(self):
        """Add water quality and level fields to measurements table"""
        fields = [
            ("water_level_m", "REAL", "Water level (meters below ground)"),
            ("static_level_m", "REAL", "Static water level (meters)"),
            ("ph", "REAL", "pH value"),
            ("conductivity", "REAL", "Electrical conductivity (μS/cm)"),
            ("temperature", "REAL", "Temperature (°C)"),
            ("turbidity", "REAL", "Turbidity (NTU)"),
            ("dissolved_oxygen", "REAL", "Dissolved oxygen (mg/L)"),
            ("tds", "REAL", "Total dissolved solids (mg/L)"),
            ("quality_notes", "TEXT", "Water quality notes"),
        ]
        
        for field_name, field_type, description in fields:
            try:
                self.db.execute_query(
                    f"ALTER TABLE measurements ADD COLUMN {field_name} {field_type}"
                )
                print(f"   ✓ Added {field_name} ({description})")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print(f"   ℹ {field_name} already exists")
                else:
                    raise
    
    def _create_borehole_details_table(self):
        """Create table for borehole technical specifications"""
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS borehole_details (
                detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL UNIQUE,
                
                -- Elevation and depth
                collar_elevation REAL,           -- m above sea level
                total_depth REAL,                -- m
                casing_depth REAL,               -- m
                screen_top REAL,                 -- m below ground
                screen_bottom REAL,              -- m below ground
                
                -- Aquifer information
                aquifer_type TEXT,               -- 'Fractured rock', 'Alluvial', 'Confined', 'Unconfined'
                aquifer_description TEXT,
                
                -- Construction details
                installation_date DATE,
                drilling_contractor TEXT,
                borehole_diameter REAL,          -- mm
                casing_material TEXT,            -- 'PVC', 'Steel', etc.
                casing_diameter REAL,            -- mm
                
                -- Pumping information
                pump_type TEXT,                  -- 'Submersible', 'Surface', etc.
                pump_depth REAL,                 -- m
                design_yield REAL,               -- m³/day
                tested_yield REAL,               -- m³/day from pump test
                
                -- Monitoring information
                monitoring_frequency TEXT,        -- 'Weekly', 'Monthly', 'Quarterly'
                monitoring_start_date DATE,
                monitoring_purpose TEXT,          -- 'Water level', 'Water quality', 'Both'
                
                -- Additional info
                coordinates_easting REAL,
                coordinates_northing REAL,
                notes TEXT,
                
                -- Audit
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (source_id) REFERENCES water_sources(source_id) ON DELETE CASCADE
            )
        """
        
        self.db.execute_query(create_table_sql)
        print("   ✓ Created borehole_details table")
    
    def _add_indexes(self):
        """Add indexes for performance"""
        indexes = [
            ("idx_measurements_type_date", "measurements(measurement_type, measurement_date)"),
            ("idx_measurements_source_date", "measurements(source_id, measurement_date)"),
            ("idx_water_sources_purpose", "water_sources(source_purpose)"),
            ("idx_borehole_details_source", "borehole_details(source_id)"),
        ]
        
        for index_name, index_spec in indexes:
            try:
                self.db.execute_query(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_spec}")
                print(f"   ✓ Created index: {index_name}")
            except Exception as e:
                print(f"   ℹ Index {index_name} may already exist: {e}")
    
    def _update_existing_data(self):
        """Update existing boreholes to have ABSTRACTION purpose"""
        result = self.db.execute_query("""
            UPDATE water_sources 
            SET source_purpose = 'ABSTRACTION' 
            WHERE type_id = (
                SELECT type_id FROM water_source_types WHERE type_code = 'BH'
            )
            AND (source_purpose IS NULL OR source_purpose = '')
        """)
        
        # Count boreholes
        bh_count = self.db.execute_query("""
            SELECT COUNT(*) as count FROM water_sources 
            WHERE type_id = (SELECT type_id FROM water_source_types WHERE type_code = 'BH')
        """)
        
        count = bh_count[0]['count'] if bh_count else 0
        print(f"   ✓ Updated {count} existing boreholes to ABSTRACTION purpose")
        
        # Log summary
        summary = self.db.execute_query("""
            SELECT ws.source_purpose, COUNT(*) as count
            FROM water_sources ws
            WHERE ws.type_id = (SELECT type_id FROM water_source_types WHERE type_code = 'BH')
            GROUP BY ws.source_purpose
        """)
        
        if summary:
            print("\n   Borehole Summary:")
            for row in summary:
                purpose = row['source_purpose'] or 'UNCLASSIFIED'
                print(f"     • {purpose}: {row['count']} boreholes")
    
    def rollback(self, backup_file):
        """Rollback to backup if migration fails"""
        print(f"\n⚠️ Rolling back to backup: {backup_file}")
        from utils.backup_manager import BackupManager
        backup = BackupManager()
        backup.restore_backup(backup_file)
        print("✅ Rollback complete")


def main():
    """Run migration"""
    migration = BoreholeAnalyticsMigration()
    
    try:
        # Ask for confirmation
        print("\nThis will modify the database structure to add borehole analytics support.")
        print("A backup will be created automatically before proceeding.")
        
        response = input("\nContinue with migration? [y/N]: ").lower().strip()
        
        if response != 'y':
            print("Migration cancelled.")
            return
        
        # Run migration
        migration.migrate()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        print("\nPlease check the logs and restore from backup if needed.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
