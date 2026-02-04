"""
SQLite Database Schema Definition (SCHEMA INITIALIZATION).

Defines the database structure for the PySide6 Water Balance application.
This is a FRESH database design (separate from Tkinter legacy app).

Starting with: storage_facilities table
Future tables: measurements, calculations, alerts, pump_transfers, etc.

Database file: data/water_balance.db
Accessed by: StorageFacilityRepository and related services
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


logger = logging.getLogger(__name__)


class DatabaseSchema:
    """Database schema manager (SCHEMA INITIALIZATION & MIGRATION).
    
    Responsible for:
    1. Creating fresh SQLite database
    2. Defining all table structures
    3. Setting up indexes and constraints
    4. Handling schema migrations (future)
    
    Why separate class: Keeps schema logic isolated, makes it testable,
    allows easy schema updates without touching core DB manager.
    """
    
    # Database location (relative to project root)
    DB_PATH = Path(__file__).parent.parent.parent / "data" / "water_balance.db"
    
    # Schema version (bump on any table/column changes)
    SCHEMA_VERSION = 6  # Added storage_history table
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize schema manager (CONSTRUCTOR).
        
        Args:
            db_path: Override default database path (useful for testing)
        """
        self.db_path = db_path or self.DB_PATH
    
    def create_database(self) -> None:
        """Create fresh database with all tables (INITIALIZATION ENTRY POINT).
        
        This is called once on first app startup or during database reset.
        
        Process:
        1. Create data/ directory if not exists
        2. Connect to SQLite
        3. Create all tables (storage_facilities, etc.)
        4. Set pragmas (performance, integrity)
        5. Verify structure (integrity check)
        
        Side effects: Creates database file on disk
        
        Raises:
            sqlite3.Error: If database creation fails
        
        Example:
            schema = DatabaseSchema()
            schema.create_database()
        """
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect and create schema
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._set_pragmas(conn)
            self._create_storage_facilities_table(conn)
            self._create_monthly_parameters_table(conn)
            self._create_system_constants_table(conn)
            self._create_constants_audit_table(conn)
            self._create_environmental_data_table(conn)
            self._create_environmental_audit_table(conn)
            self._create_storage_history_table(conn)
            self._create_facility_transfers_table(conn)
            # Future: _create_measurements_table, etc.
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to create database schema: {e}") from e
        finally:
            conn.close()
    
    @staticmethod
    def _set_pragmas(conn: sqlite3.Connection) -> None:
        """Set SQLite performance and integrity pragmas (DATABASE TUNING).
        
        Pragmas configured:
        - foreign_keys: ON (enforce referential integrity)
        - journal_mode: WAL (write-ahead logging for concurrency)
        - synchronous: NORMAL (balance safety vs speed)
        - cache_size: -64000 (64MB cache)
        - temp_store: MEMORY (temp tables in RAM, faster)
        
        Why these settings:
        - WAL mode allows concurrent reads while writing
        - Foreign keys prevent orphaned records
        - NORMAL sync prevents corruption while staying reasonably fast
        
        Args:
            conn: SQLite connection object
        """
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")
        conn.execute("PRAGMA temp_store = MEMORY")
    
    def _create_storage_facilities_table(self, conn: sqlite3.Connection) -> None:
        """Create storage_facilities table (CORE TABLE - STORAGE FACILITY RECORDS).
        
        Table structure:
        - id: PRIMARY KEY (auto-increment)
        - code: UNIQUE NOT NULL (facility identifier, e.g., 'NDCD1', 'OLDTSF')
        - name: NOT NULL (display name)
        - facility_type: Enum-like (TSF, Pond, Dam, Tank, Other)
        - capacity_m3: CHECK > 0 (total capacity, must be positive)
        - surface_area_m2: Optional (for evaporation calculations)
        - current_volume_m3: CHECK >= 0 (current water level)
        - status: Default 'active' (active, inactive, decommissioned)
        - notes: Optional text
        - created_at: Timestamp (when record created)
        - updated_at: Timestamp (when record last modified)
        
        Indexes:
        - idx_storage_code: Speed up lookups by facility code
        - idx_storage_status: Speed up filtering by status
        - idx_storage_updated: Speed up time-based queries
        
        Constraints:
        - code must be unique (no duplicates)
        - capacity and volume must be non-negative
        - capacity must be positive (> 0)
        
        Args:
            conn: SQLite connection object
        
        Raises:
            sqlite3.Error: If table creation fails
        """
        # Create main table with all constraints
        conn.execute("""
            CREATE TABLE IF NOT EXISTS storage_facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                facility_type TEXT NOT NULL CHECK(facility_type IN ('TSF', 'Pond', 'Dam', 'Tank', 'Other')),
                capacity_m3 REAL NOT NULL CHECK(capacity_m3 > 0),
                surface_area_m2 REAL,
                current_volume_m3 REAL NOT NULL DEFAULT 0 CHECK(current_volume_m3 >= 0),
                is_lined INTEGER CHECK(is_lined IN (0, 1, NULL)),
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'decommissioned')),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries (performance optimization)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_code ON storage_facilities(code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_status ON storage_facilities(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_updated ON storage_facilities(updated_at)")

    def _create_monthly_parameters_table(self, conn: sqlite3.Connection) -> None:
        """Create facility_monthly_parameters table (MONTHLY TOTALS PER FACILITY).
        
        Table purpose:
        - Stores monthly inflow/outflow totals per facility
        - Enables historical trend view for each facility
        - Supports future analytics and reporting
        
        Table structure:
        - id: PRIMARY KEY (auto-increment)
        - facility_id: FK to storage_facilities.id (enforces integrity)
        - year: INTEGER (e.g., 2026)
        - month: INTEGER (1-12)
        - total_inflows_m3: REAL (>= 0)
        - total_outflows_m3: REAL (>= 0)
        - created_at: Timestamp
        - updated_at: Timestamp
        
        Constraints:
        - UNIQUE(facility_id, year, month) prevents duplicate monthly records
        - CHECK constraints ensure valid month/year and non-negative totals
        
        Indexes (performance):
        - idx_monthly_facility: fast lookup by facility
        - idx_monthly_year_month: fast ordering by time
        - idx_monthly_updated: time-based queries
        
        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facility_monthly_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 2000 AND year <= 2100),
                month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
                total_inflows_m3 REAL NOT NULL DEFAULT 0 CHECK(total_inflows_m3 >= 0),
                total_outflows_m3 REAL NOT NULL DEFAULT 0 CHECK(total_outflows_m3 >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(facility_id, year, month),
                FOREIGN KEY(facility_id) REFERENCES storage_facilities(id) ON DELETE CASCADE
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_monthly_facility ON facility_monthly_parameters(facility_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_monthly_year_month ON facility_monthly_parameters(year, month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_monthly_updated ON facility_monthly_parameters(updated_at)")

    def _create_system_constants_table(self, conn: sqlite3.Connection) -> None:
        """Create system_constants table (CONFIGURATION CONSTANTS).

        Stores configurable calculation parameters used by the app.

        Table structure:
        - id: PRIMARY KEY (auto-increment)
        - constant_key: UNIQUE NOT NULL (identifier used by calculations)
        - constant_value: REAL (numeric value)
        - unit: Optional text (display unit)
        - category: Optional text (UI grouping)
        - description: Optional text (human-readable)
        - editable: 1/0 (lock critical constants)
        - min_value/max_value: Optional bounds for validation
        - created_at/updated_at: Audit timestamps

        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_constants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                constant_key TEXT NOT NULL UNIQUE,
                constant_value REAL NOT NULL,
                unit TEXT,
                category TEXT,
                description TEXT,
                editable INTEGER NOT NULL DEFAULT 1 CHECK(editable IN (0, 1)),
                min_value REAL,
                max_value REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_constants_category ON system_constants(category)")

    def _create_constants_audit_table(self, conn: sqlite3.Connection) -> None:
        """Create constants_audit table (CHANGE HISTORY).

        Logs updates to system constants for audit and troubleshooting.

        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS constants_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                constant_key TEXT NOT NULL,
                old_value REAL,
                new_value REAL,
                updated_by TEXT DEFAULT 'system'
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_constants_audit_key ON constants_audit(constant_key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_constants_audit_time ON constants_audit(changed_at)")

    def _create_environmental_data_table(self, conn: sqlite3.Connection) -> None:
        """Create environmental_data table (MONTHLY RAINFALL & EVAPORATION).

        Stores monthly environmental data for water balance calculations.
        Used by water balance calculator to compute rainfall inflows and evaporation losses.

        Table structure:
        - id: PRIMARY KEY
        - year: Year (e.g., 2025)
        - month: Month (1-12)
        - rainfall_mm: Monthly rainfall in millimeters
        - evaporation_mm: Monthly evaporation in millimeters
        - created_at: Timestamp when created
        - updated_at: Timestamp when last modified
        - UNIQUE(year, month): Prevent duplicate entries for same month

        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS environmental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                rainfall_mm REAL NOT NULL CHECK(rainfall_mm >= 0),
                evaporation_mm REAL NOT NULL CHECK(evaporation_mm >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month)
            )
        """)

        # Indexes for fast lookups by year/month
        conn.execute("CREATE INDEX IF NOT EXISTS idx_environmental_year ON environmental_data(year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_environmental_year_month ON environmental_data(year, month)")

    def _create_environmental_audit_table(self, conn: sqlite3.Connection) -> None:
        """Create environmental_data_audit table (CHANGE HISTORY).

        Logs all changes to environmental data for compliance and troubleshooting.

        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS environmental_data_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                old_rainfall_mm REAL,
                new_rainfall_mm REAL,
                old_evaporation_mm REAL,
                new_evaporation_mm REAL,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT DEFAULT 'system'
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_environmental_audit_year_month ON environmental_data_audit(year, month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_environmental_audit_time ON environmental_data_audit(changed_at)")

    def _create_storage_history_table(self, conn: sqlite3.Connection) -> None:
        """Create storage_history table (MONTHLY STORAGE TRACKING).

        Tracks monthly opening and closing volumes for each storage facility.
        Essential for calculating ΔStorage in water balance equation:
            Balance Error = Inflows - Outflows - ΔStorage
            where ΔStorage = Closing_Volume - Opening_Volume

        Table structure:
        - id: PRIMARY KEY
        - facility_code: FK to storage_facilities.code
        - year: Year (e.g., 2025)
        - month: Month (1-12)
        - opening_volume_m3: Volume at start of month
        - closing_volume_m3: Volume at end of month
        - delta_volume_m3: Change = closing - opening (computed for convenience)
        - data_source: 'measured', 'calculated', 'estimated', 'imported'
        - notes: Optional comments
        - created_at: Timestamp when created
        - updated_at: Timestamp when last modified
        - UNIQUE(facility_code, year, month): Prevent duplicate entries

        Scientific notes:
        - Opening volume should equal previous month's closing (mass conservation)
        - Closing volume comes from physical measurements or calculations
        - Delta is positive if storage increased, negative if decreased

        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS storage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_code TEXT NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 2000 AND year <= 2100),
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                opening_volume_m3 REAL NOT NULL DEFAULT 0 CHECK(opening_volume_m3 >= 0),
                closing_volume_m3 REAL NOT NULL DEFAULT 0 CHECK(closing_volume_m3 >= 0),
                delta_volume_m3 REAL GENERATED ALWAYS AS (closing_volume_m3 - opening_volume_m3) STORED,
                data_source TEXT NOT NULL DEFAULT 'measured' CHECK(data_source IN ('measured', 'calculated', 'estimated', 'imported')),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(facility_code, year, month),
                FOREIGN KEY(facility_code) REFERENCES storage_facilities(code) ON DELETE CASCADE
            )
        """)

        # Indexes for fast lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_history_facility ON storage_history(facility_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_history_year_month ON storage_history(year, month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_history_facility_time ON storage_history(facility_code, year, month)")

    def _create_facility_transfers_table(self, conn: sqlite3.Connection) -> None:
        """Create facility_transfers table (INTER-FACILITY WATER MOVEMENTS).

        Tracks water transfers between storage facilities.
        
        Scientific notes:
        - Transfers are INTERNAL movements - they don't affect system-wide balance
        - Water leaving Facility A appears as inflow to Facility B
        - System total remains constant (mass conservation)
        - Used for facility-level reporting and operational tracking

        Table structure:
        - id: PRIMARY KEY
        - source_facility_code: FK to storage_facilities.code
        - dest_facility_code: FK to storage_facilities.code
        - transfer_date: Date of transfer
        - volume_m3: Volume transferred (must be positive)
        - transfer_method: 'pump', 'gravity', 'spillway', 'other'
        - notes: Optional comments
        - created_at: Timestamp

        Args:
            conn: SQLite connection object
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facility_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_facility_code TEXT NOT NULL,
                dest_facility_code TEXT NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 2000 AND year <= 2100),
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                volume_m3 REAL NOT NULL CHECK(volume_m3 > 0),
                transfer_method TEXT DEFAULT 'pump' CHECK(transfer_method IN ('pump', 'gravity', 'spillway', 'other')),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(source_facility_code) REFERENCES storage_facilities(code) ON DELETE RESTRICT,
                FOREIGN KEY(dest_facility_code) REFERENCES storage_facilities(code) ON DELETE RESTRICT,
                CHECK(source_facility_code != dest_facility_code)
            )
        """)

        # Indexes for fast lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transfers_source ON facility_transfers(source_facility_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transfers_dest ON facility_transfers(dest_facility_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transfers_year_month ON facility_transfers(year, month)")

    def ensure_monthly_parameters_table(self) -> None:
        """Ensure monthly parameters table exists (SAFE SCHEMA UPDATE).
        
        This method is safe to call on existing databases:
        - If table exists, no changes are made
        - If table is missing, it is created with indexes
        
        Why needed:
        - Existing DBs may predate this feature
        - We avoid destructive migrations for production data
        - Keeps app resilient across upgrades
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._set_pragmas(conn)
            self._create_monthly_parameters_table(conn)
            conn.commit()
        finally:
            conn.close()

    def ensure_system_constants_tables(self) -> None:
        """Ensure system constants and audit tables exist (SAFE SCHEMA UPDATE).

        Safe to call on existing databases:
        - Creates system_constants table if missing
        - Creates constants_audit table if missing
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._set_pragmas(conn)
            self._create_system_constants_table(conn)
            self._create_constants_audit_table(conn)
            conn.commit()
        finally:
            conn.close()

    def ensure_environmental_data_tables(self) -> None:
        """Ensure environmental_data and audit tables exist (SAFE SCHEMA UPDATE).

        Safe to call on existing databases:
        - Creates environmental_data table if missing
        - Creates environmental_data_audit table if missing

        Used by: EnvironmentalDataService on first access
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._set_pragmas(conn)
            self._create_environmental_data_table(conn)
            self._create_environmental_audit_table(conn)
            conn.commit()
        finally:
            conn.close()

    def ensure_storage_history_tables(self) -> None:
        """Ensure storage_history and facility_transfers tables exist (SAFE SCHEMA UPDATE).

        Safe to call on existing databases:
        - Creates storage_history table if missing (for ΔStorage tracking)
        - Creates facility_transfers table if missing (for inter-dam flows)

        Why needed:
        - Existing DBs created before v6 don't have these tables
        - Storage history is CRITICAL for accurate water balance
        - Without history, opening volume defaults to 0 → incorrect ΔStorage

        Used by: StorageService.calculate_storage() on first access
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._set_pragmas(conn)
            self._create_storage_history_table(conn)
            self._create_facility_transfers_table(conn)
            conn.commit()
            logger.info("Ensured storage_history and facility_transfers tables exist")
        except sqlite3.Error as e:
            logger.error(f"Failed to create storage history tables: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def ensure_is_lined_column(self) -> None:
        """Ensure is_lined column exists in storage_facilities table (SAFE SCHEMA UPGRADE).
        
        This method is safe to call on existing databases:
        - If column exists, no changes are made
        - If column is missing, it is added with default NULL
        
        Why needed:
        - Existing DBs created before v3 don't have is_lined column
        - We avoid destructive migrations for production data
        - Keeps app resilient across upgrades
        
        Migration:
        - Adds: is_lined INTEGER CHECK(is_lined IN (0, 1, NULL)) DEFAULT NULL
        - NULL = not applicable (tanks, etc.)
        - 0 = unlined dam/TSF
        - 1 = lined dam/TSF
        """
        if not self.db_path.exists():
            return  # Database doesn't exist yet
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            # Check if is_lined column exists
            cursor = conn.execute("PRAGMA table_info(storage_facilities)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_lined' not in columns:
                # Add is_lined column
                conn.execute("""
                    ALTER TABLE storage_facilities 
                    ADD COLUMN is_lined INTEGER CHECK(is_lined IN (0, 1, NULL))
                """)
                conn.commit()
                logger.info("Added is_lined column to storage_facilities table (schema upgrade)")
            else:
                logger.debug("is_lined column already exists in storage_facilities")
        except sqlite3.Error as e:
            logger.error(f"Failed to add is_lined column: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database (UTILITY - TABLE EXISTENCE CHECK).
        
        Useful for verifying schema before operations.
        
        Args:
            table_name: Name of table to check
        
        Returns:
            True if table exists, False otherwise
        
        Example:
            if schema.table_exists('storage_facilities'):
                # Safe to query
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def reset_database(self) -> None:
        """Reset database to fresh state (DESTRUCTIVE - USE WITH CAUTION).
        
        WARNING: This DELETES all data. Used for:
        - Testing (pytest fixtures)
        - Development (clearing test data)
        - Fresh reinstall
        
        Process:
        1. Backup existing database (if exists)
        2. Delete database file
        3. Create fresh database with schema
        
        Side effects: Database file deleted and recreated (data loss!)
        """
        # Backup existing database if it exists
        if self.db_path.exists():
            backup_path = self.db_path.with_suffix('.db.backup')
            self.db_path.rename(backup_path)
        
        # Create fresh database
        self.create_database()
    
    def get_schema_info(self) -> dict:
        """Get information about current schema (UTILITY - SCHEMA INSPECTION).
        
        Returns:
            Dict with tables and their column info
        
        Returns:
            {
                'schema_version': 1,
                'tables': {
                    'storage_facilities': [
                        {'name': 'id', 'type': 'INTEGER', ...},
                        ...
                    ]
                }
            }
        
        Useful for debugging and schema verification.
        """
        if not self.db_path.exists():
            return {'schema_version': 0, 'tables': {}}
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = {
                'schema_version': self.SCHEMA_VERSION,
                'tables': {}
            }
            
            for table in tables:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [
                    {
                        'name': row[1],
                        'type': row[2],
                        'not_null': bool(row[3]),
                        'default': row[4]
                    }
                    for row in cursor.fetchall()
                ]
                schema_info['tables'][table] = columns
            
            return schema_info
        finally:
            conn.close()
