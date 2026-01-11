"""
Database Schema Definition
Complete SQLite database structure for water balance management
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config


class DatabaseSchema:
    """Database schema manager and initializer"""
    
    def __init__(self, db_path: str = None):
        """Initialize database schema manager"""
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            db_path = base_dir / config.get('database.path', 'data/water_balance.db')
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def create_database(self):
        """Create all database tables with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables in order (respecting foreign key dependencies)
            self._create_mine_areas_table(cursor)
            self._create_water_source_types_table(cursor)
            self._create_water_sources_table(cursor)
            self._create_borehole_details_table(cursor)
            self._create_storage_facilities_table(cursor)
            self._create_evaporation_rates_table(cursor)
            self._create_regional_rainfall_monthly_table(cursor)
            self._create_facility_rainfall_monthly_table(cursor)
            self._create_facility_evaporation_monthly_table(cursor)
            self._create_facility_inflow_monthly_table(cursor)
            self._create_facility_outflow_monthly_table(cursor)
            self._create_facility_abstraction_monthly_table(cursor)
            self._create_tailings_moisture_monthly_table(cursor)
            self._create_monthly_manual_inputs_table(cursor)
            # NOTE: seepage_gain_monthly table removed - seepage now automatic based on facility properties
            self._create_measurements_table(cursor)
            self._create_tsf_return_table(cursor)
            self._create_calculations_table(cursor)
            self._create_operating_rules_table(cursor)
            self._create_constants_table(cursor)
            self._create_alert_rules_table(cursor)
            self._create_alerts_table(cursor)
            self._create_audit_log_table(cursor)

            # Ensure optional wb_* topology tables exist (idempotent)
            try:
                from database.migrate_wb_schema import migrate as migrate_wb
                migrate_wb()
            except Exception as wb_err:
                print(f"⚠️ Warning: wb_* topology migration skipped: {wb_err}")
            self._create_reports_table(cursor)
            
            # Insert initial reference data
            self._insert_initial_data(cursor)
            
            conn.commit()
            print(f"✅ Database created successfully: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"❌ Error creating database: {e}")
            return False
        finally:
            conn.close()

    def migrate_database(self):
        """Apply schema migrations (add new tables to existing databases)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create regional and facility-specific monthly tables if they don't exist
            self._create_regional_rainfall_monthly_table(cursor)
            self._create_facility_rainfall_monthly_table(cursor)
            self._create_facility_evaporation_monthly_table(cursor)
            self._create_facility_inflow_monthly_table(cursor)
            self._create_facility_outflow_monthly_table(cursor)
            self._create_facility_abstraction_monthly_table(cursor)
            self._create_tailings_moisture_monthly_table(cursor)
            self._create_monthly_manual_inputs_table(cursor)
            self._create_tsf_return_table(cursor)
            self._create_groundwater_inflow_table(cursor)
            self._create_data_quality_checks_table(cursor)
            # NOTE: seepage_gain_monthly table removed - seepage now automatic based on facility properties

            # Ensure system_constants has optional min/max columns for UI
            cursor.execute("PRAGMA table_info(system_constants)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'min_value' not in cols:
                cursor.execute("ALTER TABLE system_constants ADD COLUMN min_value REAL")
            if 'max_value' not in cols:
                cursor.execute("ALTER TABLE system_constants ADD COLUMN max_value REAL")

            # Ensure optional wb_* topology tables exist (idempotent)
            try:
                from database.migrate_wb_schema import migrate as migrate_wb
                migrate_wb()
            except Exception as wb_err:
                print(f"⚠️ Warning: wb_* topology migration skipped: {wb_err}")
            
            conn.commit()
            print(f"Database migrated successfully: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"❌ Error migrating database: {e}")
            return False
        finally:
            conn.close()
    
    def _create_mine_areas_table(self, cursor):
        """Mine areas/operations table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mine_areas (
                area_id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_code TEXT NOT NULL UNIQUE,
                area_name TEXT NOT NULL,
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mine_areas_code ON mine_areas(area_code)")
    
    def _create_water_source_types_table(self, cursor):
        """Water source type reference table"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_source_types (
                type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_code TEXT NOT NULL UNIQUE,
                type_name TEXT NOT NULL,
                description TEXT,
                color_code TEXT
            )
        """)
    
    def _create_water_sources_table(self, cursor):
        """Water sources (rivers, boreholes, underground)"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_code TEXT NOT NULL UNIQUE,
                source_name TEXT NOT NULL,
                type_id INTEGER NOT NULL,
                area_id INTEGER,
                description TEXT,
                
                -- Borehole purpose classification (NEW - Borehole Analytics)
                source_purpose TEXT DEFAULT 'ABSTRACTION',  -- 'ABSTRACTION', 'MONITORING', 'STATIC', 'DUAL_PURPOSE'
                
                -- Technical specifications
                authorized_volume REAL,  -- m³/month or m³/annum
                authorization_period TEXT,  -- 'monthly', 'annual'
                max_flow_rate REAL,  -- m³/day
                average_flow_rate REAL,  -- Typical average abstraction/monitoring flow (unit per period)
                flow_units TEXT,  -- Units for average flow (e.g. 'm³/day', 'm³/month')
                reliability_factor REAL DEFAULT 1.0,  -- Confidence factor (1=fully reliable)
                
                -- Location/details
                latitude REAL,
                longitude REAL,
                depth REAL,  -- For boreholes (meters)
                river_name TEXT,  -- For river abstractions
                
                -- Status
                active BOOLEAN DEFAULT 1,
                commissioned_date DATE,
                decommissioned_date DATE,
                
                -- Audit
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                
                FOREIGN KEY (type_id) REFERENCES water_source_types(type_id),
                FOREIGN KEY (area_id) REFERENCES mine_areas(area_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_code ON water_sources(source_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_type ON water_sources(type_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_active ON water_sources(active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_sources_purpose ON water_sources(source_purpose)")
    
    def _create_borehole_details_table(self, cursor):
        """Borehole technical details and specifications"""
        cursor.execute("""
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
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_borehole_details_source ON borehole_details(source_id)")
    
    def _create_storage_facilities_table(self, cursor):
        """Storage facilities (dams, tanks, reservoirs)"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage_facilities (
                facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_code TEXT NOT NULL UNIQUE,
                facility_name TEXT NOT NULL,
                facility_type TEXT NOT NULL,  -- 'dam', 'tank', 'pond', 'reservoir'
                area_id INTEGER,
                
                -- Capacity specifications
                total_capacity REAL NOT NULL,  -- m³
                working_capacity REAL,  -- m³ (usable volume)
                dead_storage REAL,  -- m³ (unusable volume)
                surface_area REAL,  -- m² (for evaporation calculations)
                
                -- Operating levels (as percentages)
                pump_start_level REAL DEFAULT 70.0,  -- Start pumping at 70%
                pump_stop_level REAL DEFAULT 20.0,   -- Stop pumping at 20%
                high_level_alarm REAL DEFAULT 90.0,
                low_level_alarm REAL DEFAULT 10.0,
                
                -- Current status
                current_volume REAL DEFAULT 0,
                current_level_percent REAL DEFAULT 0,
                last_updated TIMESTAMP,
                
                -- Physical characteristics
                max_depth REAL,  -- meters
                siltation_percentage REAL DEFAULT 0,  -- Percentage of capacity lost to silt
                is_lined BOOLEAN DEFAULT 0,  -- 1 for lined facilities (negligible seepage), 0 for unlined
                
                -- Purpose and connections
                purpose TEXT,  -- 'raw_water', 'return_water', 'storm_water', 'clean_water'
                water_quality TEXT,  -- 'potable', 'process', 'contaminated'
                feeds_to TEXT,  -- Comma-separated facility codes
                receives_from TEXT,  -- Comma-separated source codes
                evap_active BOOLEAN DEFAULT 1,  -- whether facility participates in evaporation calculations
                
                -- Status
                active BOOLEAN DEFAULT 1,
                commissioned_date DATE,
                
                -- Audit
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (area_id) REFERENCES mine_areas(area_id),
                
                CHECK (total_capacity > 0),
                CHECK (current_level_percent >= 0 AND current_level_percent <= 100),
                CHECK (pump_start_level > pump_stop_level)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facilities_code ON storage_facilities(facility_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facilities_type ON storage_facilities(facility_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facilities_active ON storage_facilities(active)")
    
    def _create_evaporation_rates_table(self, cursor):
        """Monthly evaporation rates reference data"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaporation_rates (
                rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,  -- 1-12
                evaporation_mm REAL NOT NULL,  -- mm/month
                zone TEXT DEFAULT '4A',  -- Evaporation zone
                year INTEGER,  -- Optional: for actual measurements
                notes TEXT,
                
                UNIQUE(month, zone, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (evaporation_mm >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaporation_rates_month ON evaporation_rates(month)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaporation_rates_zone ON evaporation_rates(zone)")

    def _create_regional_rainfall_monthly_table(self, cursor):
        """Regional monthly rainfall that applies to all facilities in the area.
        This is simpler than per-facility rainfall - one value per month for the entire region.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regional_rainfall_monthly (
                rainfall_id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,  -- 1-12
                year INTEGER,  -- Optional: for multi-year planning
                rainfall_mm REAL NOT NULL,  -- mm/month for entire region
                data_source TEXT DEFAULT 'dashboard',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (rainfall_mm >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_regional_rainfall_month ON regional_rainfall_monthly(month)")

    def _create_facility_rainfall_monthly_table(self, cursor):
        """Per-facility monthly rainfall volumes (user-configurable)
        Allows setting facility-specific rainfall on a monthly basis via UI dashboard.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facility_rainfall_monthly (
                rainfall_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                month INTEGER NOT NULL,  -- 1-12
                year INTEGER,  -- Optional: for multi-year planning
                rainfall_mm REAL NOT NULL,  -- mm/month
                data_source TEXT DEFAULT 'dashboard',  -- 'dashboard', 'excel', 'measurement'
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id) ON DELETE CASCADE,
                UNIQUE(facility_id, month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (rainfall_mm >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_rainfall_facility ON facility_rainfall_monthly(facility_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_rainfall_month ON facility_rainfall_monthly(month)")

    def _create_facility_evaporation_monthly_table(self, cursor):
        """Per-facility monthly evaporation rates (user-configurable)
        Allows setting facility-specific evaporation on a monthly basis via UI dashboard.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facility_evaporation_monthly (
                evap_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                month INTEGER NOT NULL,  -- 1-12
                year INTEGER,  -- Optional: for multi-year planning
                evaporation_mm REAL NOT NULL,  -- mm/month
                data_source TEXT DEFAULT 'dashboard',  -- 'dashboard', 'excel', 'measurement'
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id) ON DELETE CASCADE,
                UNIQUE(facility_id, month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (evaporation_mm >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_evap_facility ON facility_evaporation_monthly(facility_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_evap_month ON facility_evaporation_monthly(month)")

    def _create_facility_inflow_monthly_table(self, cursor):
        """Per-facility monthly inflow volumes (user-configurable)
        Allows setting facility-specific inflow on a monthly basis via UI dashboard.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facility_inflow_monthly (
                inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                month INTEGER NOT NULL,  -- 1-12
                year INTEGER,  -- Optional: for multi-year planning
                inflow_m3 REAL NOT NULL,  -- m³/month
                data_source TEXT DEFAULT 'dashboard',  -- 'dashboard', 'excel', 'measurement'
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id) ON DELETE CASCADE,
                UNIQUE(facility_id, month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (inflow_m3 >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_inflow_facility ON facility_inflow_monthly(facility_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_inflow_month ON facility_inflow_monthly(month)")

    def _create_facility_outflow_monthly_table(self, cursor):
        """Per-facility monthly outflow volumes (user-configurable)
        Allows setting facility-specific outflow on a monthly basis via UI dashboard.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facility_outflow_monthly (
                outflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                month INTEGER NOT NULL,  -- 1-12
                year INTEGER,  -- Optional: for multi-year planning
                outflow_m3 REAL NOT NULL,  -- m³/month
                data_source TEXT DEFAULT 'dashboard',  -- 'dashboard', 'excel', 'measurement'
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id) ON DELETE CASCADE,
                UNIQUE(facility_id, month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (outflow_m3 >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_outflow_facility ON facility_outflow_monthly(facility_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_outflow_month ON facility_outflow_monthly(month)")

    def _create_facility_abstraction_monthly_table(self, cursor):
        """Per-facility monthly abstraction volumes (user-configurable)
        Allows setting facility-specific abstraction on a monthly basis via UI dashboard.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facility_abstraction_monthly (
                abstraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                month INTEGER NOT NULL,  -- 1-12
                year INTEGER,  -- Optional: for multi-year planning
                abstraction_m3 REAL NOT NULL,  -- m³/month
                data_source TEXT DEFAULT 'dashboard',  -- 'dashboard', 'excel', 'measurement'
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id) ON DELETE CASCADE,
                UNIQUE(facility_id, month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (abstraction_m3 >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_abstraction_facility ON facility_abstraction_monthly(facility_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facility_abstraction_month ON facility_abstraction_monthly(month)")

    def _create_tailings_moisture_monthly_table(self, cursor):
        """Monthly tailings moisture percentage (user input).
        Used in System Balance calculation for water retained in tailings.
        Falls back to 0 if no data entered.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tailings_moisture_monthly (
                moisture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                tailings_moisture_pct REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(month, year),
                CHECK (month >= 1 AND month <= 12),
                CHECK (tailings_moisture_pct >= 0 AND tailings_moisture_pct <= 100)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tailings_moisture_month ON tailings_moisture_monthly(month, year)")

    def _create_monthly_manual_inputs_table(self, cursor):
        """Monthly manual inputs for auxiliary/site uses and outflows."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS monthly_manual_inputs (
                month_start DATE PRIMARY KEY,
                dust_suppression_m3 REAL DEFAULT 0,
                mining_consumption_m3 REAL DEFAULT 0,
                domestic_consumption_m3 REAL DEFAULT 0,
                discharge_m3 REAL DEFAULT 0,
                product_moisture_m3 REAL DEFAULT 0,
                tailings_retention_m3 REAL DEFAULT 0,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_inputs_month ON monthly_manual_inputs(month_start)")

    def _create_tsf_return_table(self, cursor):
        """Monthly TSF return water volumes (measured).

        Designed for simple import/export of monthly TSF return data
        without disturbing the main measurements table.
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tsf_return_monthly (
                tsf_id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_start DATE NOT NULL,           -- use first day of month
                tsf_return_m3 REAL NOT NULL,         -- measured TSF return volume for the month
                source TEXT,                         -- optional: 'meter', 'model', etc.
                notes TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(month_start)
            )
            """
        )

    def _create_groundwater_inflow_table(self, cursor):
        """Monthly groundwater inflow from MODFLOW/GMS modeling.

        Stores imported groundwater model results for integration with water balance.
        Maps model wells to database water sources for automated inflow calculation.
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groundwater_inflow_monthly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,          -- link to water_sources table
                month INTEGER NOT NULL,              -- 1-12
                year INTEGER NOT NULL,               -- e.g., 2025
                inflow_m3 REAL NOT NULL,             -- monthly groundwater inflow volume
                model_run_date TEXT,                 -- when MODFLOW model was executed
                modflow_scenario_name TEXT,          -- scenario identifier (e.g., 'base', 'drought', 'wet')
                confidence_level TEXT DEFAULT 'medium', -- 'low', 'medium', 'high'
                notes TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (source_id) REFERENCES water_sources(source_id) ON DELETE CASCADE,
                UNIQUE(source_id, month, year, modflow_scenario_name),
                CHECK (month >= 1 AND month <= 12),
                CHECK (inflow_m3 >= 0),
                CHECK (confidence_level IN ('low', 'medium', 'high'))
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_groundwater_date ON groundwater_inflow_monthly(year, month)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_groundwater_source ON groundwater_inflow_monthly(source_id)")

    def _create_data_quality_checks_table(self, cursor):
        """Data quality check results and validation warnings.

        Tracks data completeness, gaps, and quality issues for dashboard alerts.
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data_quality_checks (
                check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TEXT NOT NULL,            -- ISO date when check was performed
                check_type TEXT NOT NULL,            -- 'missing_months', 'data_gaps', 'low_confidence', 'incomplete_inputs'
                severity TEXT NOT NULL,              -- 'info', 'warning', 'error'
                message TEXT NOT NULL,               -- human-readable description
                affected_dates TEXT,                 -- JSON array of affected dates or NULL
                completeness_pct REAL,               -- optional: data completeness percentage (0-100)
                gap_count INTEGER,                   -- optional: number of gaps detected
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CHECK (severity IN ('info', 'warning', 'error')),
                CHECK (completeness_pct IS NULL OR (completeness_pct >= 0 AND completeness_pct <= 100))
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_check_date ON data_quality_checks(check_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_severity ON data_quality_checks(severity)")
    
    def _create_measurements_table(self, cursor):
        """Daily/monthly water measurements (time-series data).
        Monitoring-specific water level & quality fields removed (scope C)."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                measurement_date DATE NOT NULL,
                measurement_type TEXT NOT NULL,
                source_id INTEGER,
                facility_id INTEGER,
                volume REAL,
                flow_rate REAL,
                level_meters REAL,
                level_percent REAL,
                rainfall_mm REAL,
                measured BOOLEAN DEFAULT 1,
                quality_flag TEXT,
                data_source TEXT,
                notes TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recorded_by TEXT,
                FOREIGN KEY (source_id) REFERENCES water_sources(source_id) ON DELETE CASCADE,
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id) ON DELETE CASCADE,
                CHECK (volume >= 0 OR volume IS NULL),
                CHECK (flow_rate >= 0 OR flow_rate IS NULL),
                CHECK (level_percent >= 0 AND level_percent <= 100 OR level_percent IS NULL)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_date ON measurements(measurement_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_type ON measurements(measurement_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_source ON measurements(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_facility ON measurements(facility_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_type_date ON measurements(measurement_type, measurement_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_source_date ON measurements(source_id, measurement_date)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_unique ON measurements(measurement_date, measurement_type, source_id, facility_id)")
    
    def _create_calculations_table(self, cursor):
        """Water balance calculations results"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                calc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                calc_date DATE NOT NULL,
                calc_type TEXT NOT NULL,  -- 'daily', 'monthly', 'annual'
                
                -- Water balance components (m³)
                total_inflows REAL DEFAULT 0,
                total_outflows REAL DEFAULT 0,
                storage_change REAL DEFAULT 0,
                balance_error REAL DEFAULT 0,
                balance_error_percent REAL DEFAULT 0,
                
                -- Detailed inflows
                river_inflow REAL DEFAULT 0,
                borehole_inflow REAL DEFAULT 0,
                underground_inflow REAL DEFAULT 0,
                rainfall_inflow REAL DEFAULT 0,
                return_water_inflow REAL DEFAULT 0,
                other_inflow REAL DEFAULT 0,
                
                -- Detailed outflows
                plant_consumption REAL DEFAULT 0,
                mining_consumption REAL DEFAULT 0,
                evaporation_loss REAL DEFAULT 0,
                seepage_loss REAL DEFAULT 0,
                discharge_outflow REAL DEFAULT 0,
                dust_suppression REAL DEFAULT 0,
                domestic_consumption REAL DEFAULT 0,
                product_moisture REAL DEFAULT 0,
                other_outflow REAL DEFAULT 0,
                
                -- Specific calculations
                tsf_slurry_volume REAL DEFAULT 0,
                tsf_return_volume REAL DEFAULT 0,
                tsf_return_percent REAL DEFAULT 0,
                plant_makeup_water REAL DEFAULT 0,
                mining_water_requirement REAL DEFAULT 0,
                
                -- Production data
                tonnes_mined REAL DEFAULT 0,
                tonnes_processed REAL DEFAULT 0,
                concentrate_produced REAL DEFAULT 0,
                
                -- Validation
                validated BOOLEAN DEFAULT 0,
                validated_by TEXT,
                validated_at TIMESTAMP,
                
                -- Audit
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                calculated_by TEXT DEFAULT 'system',
                notes TEXT,

                -- Extended breakdown (added in enhancement November 2025)
                surface_water_inflow REAL DEFAULT 0,
                groundwater_inflow REAL DEFAULT 0,
                ore_moisture_inflow REAL DEFAULT 0,
                tsf_return_inflow REAL DEFAULT 0,
                plant_returns_inflow REAL DEFAULT 0,
                returns_to_pit_inflow REAL DEFAULT 0,
                seepage_gain_inflow REAL DEFAULT 0,
                plant_consumption_gross REAL DEFAULT 0,
                plant_consumption_net REAL DEFAULT 0,
                tailings_retention_loss REAL DEFAULT 0,
                closure_error_m3 REAL DEFAULT 0,
                closure_error_percent REAL DEFAULT 0,
                balance_status TEXT,
                calc_quality_flag TEXT,
                estimated_component_count INTEGER DEFAULT 0,
                estimated_volume_fraction REAL DEFAULT 0,
                
                UNIQUE(calc_date, calc_type),
                CHECK (balance_error_percent >= 0)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calculations_date ON calculations(calc_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calculations_type ON calculations(calc_type)")
    
    def _create_operating_rules_table(self, cursor):
        """Operating rules and thresholds"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operating_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER,
                rule_type TEXT NOT NULL,  -- 'pump_control', 'alarm', 'transfer'
                rule_name TEXT NOT NULL,
                
                -- Condition
                trigger_level_percent REAL,
                trigger_volume REAL,
                condition_operator TEXT,  -- '>', '<', '>=', '<=', '='
                
                -- Action
                action_type TEXT NOT NULL,  -- 'start_pump', 'stop_pump', 'alarm', 'transfer'
                action_target TEXT,  -- Target facility or system
                action_value REAL,  -- Flow rate, volume, etc.
                
                -- Priority and status
                priority INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT 1,
                
                -- Audit
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id)
            )
        """)
    
    def _create_constants_table(self, cursor):
        """System constants and configuration values"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_constants (
                constant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                constant_key TEXT NOT NULL UNIQUE,
                constant_value REAL NOT NULL,
                unit TEXT,
                category TEXT,  -- 'calculation', 'threshold', 'conversion'
                description TEXT,
                editable BOOLEAN DEFAULT 1,
                
                -- Optional range limits for UI validation (nullable)
                min_value REAL,
                max_value REAL,
                
                -- Audit
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
        """)
    
    def _create_alert_rules_table(self, cursor):
        """Alert rules configuration"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT NOT NULL UNIQUE,
                rule_name TEXT NOT NULL,
                rule_category TEXT NOT NULL,  -- 'storage', 'consumption', 'compliance', 'level'
                
                -- Condition
                metric_name TEXT NOT NULL,  -- 'days_cover', 'level_percent', 'closure_error', etc.
                condition_operator TEXT NOT NULL,  -- '<', '>', '<=', '>=', '='
                threshold_value REAL NOT NULL,
                threshold_unit TEXT,  -- 'days', '%', 'm3', etc.
                
                -- Alert properties
                severity TEXT NOT NULL,  -- 'info', 'warning', 'critical'
                alert_title TEXT NOT NULL,
                alert_message TEXT NOT NULL,
                
                -- Actions
                show_popup BOOLEAN DEFAULT 1,
                send_email BOOLEAN DEFAULT 0,
                email_recipients TEXT,  -- Comma-separated email addresses
                auto_resolve BOOLEAN DEFAULT 1,  -- Auto-resolve when condition no longer met
                
                -- Status
                active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 1,  -- 1=highest, 5=lowest
                
                -- Metadata
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'system'
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_category ON alert_rules(rule_category)")
    
    def _create_alerts_table(self, cursor):
        """Active and historical alerts"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                
                -- Alert details
                severity TEXT NOT NULL,  -- 'info', 'warning', 'critical'
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                metric_value REAL,  -- Actual value that triggered the alert
                threshold_value REAL,  -- Threshold that was exceeded
                
                -- Context
                calculation_date DATE,
                facility_id INTEGER,
                source_id INTEGER,
                
                -- Status
                status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'acknowledged', 'resolved'
                acknowledged_at TIMESTAMP,
                acknowledged_by TEXT,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                resolution_note TEXT,
                
                -- Timestamps
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (rule_id) REFERENCES alert_rules(rule_id),
                FOREIGN KEY (facility_id) REFERENCES storage_facilities(facility_id),
                FOREIGN KEY (source_id) REFERENCES water_sources(source_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alerts(rule_id)")
    
    def _create_audit_log_table(self, cursor):
        """Audit trail for all data changes"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                action TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
                old_values TEXT,  -- JSON
                new_values TEXT,  -- JSON
                changed_by TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                notes TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_log(changed_at)")
    
    def _create_reports_table(self, cursor):
        """Generated reports tracking"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                report_name TEXT NOT NULL,
                report_period_start DATE,
                report_period_end DATE,
                file_path TEXT,
                file_format TEXT,  -- 'pdf', 'excel', 'csv'
                
                -- Content
                parameters TEXT,  -- JSON of report parameters
                
                -- Status
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generated_by TEXT,
                file_size INTEGER  -- bytes
            )
        """)
    
    def _insert_initial_data(self, cursor):
        """Insert initial reference data"""
        
        # Mine areas
        mine_areas = [
            ('UG2N', 'UG2 North', 'UG2 North Decline mining area'),
            ('UG2S', 'UG2 South', 'UG2 South Decline mining area'),
            ('MERN', 'Merensky North', 'Merensky North Decline mining area'),
            ('MERM', 'Merensky Main', 'Merensky Main Decline mining area'),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO mine_areas (area_code, area_name, description) VALUES (?, ?, ?)",
            mine_areas
        )
        
        # Water source types
        source_types = [
            ('RIVER', 'River Abstraction', 'Surface water from rivers', '#2196F3'),
            ('BH', 'Borehole', 'Groundwater from boreholes', '#4CAF50'),
            ('UG', 'Underground Water', 'Mine dewatering/seepage', '#FF9800'),
            ('RETURN', 'Return Water', 'Recycled water from process', '#9C27B0'),
            ('RAIN', 'Rainfall', 'Direct rainfall collection', '#00BCD4'),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO water_source_types (type_code, type_name, description, color_code) VALUES (?, ?, ?, ?)",
            source_types
        )
        
        # Monthly evaporation rates (S-Pan, Zone 4A)
        evap_rates = [
            (1, 226, '4A', None, 'January'),
            (2, 210, '4A', None, 'February'),
            (3, 210, '4A', None, 'March'),
            (4, 209, '4A', None, 'April'),
            (5, 174, '4A', None, 'May'),
            (6, 165, '4A', None, 'June'),
            (7, 129, '4A', None, 'July'),
            (8, 110, '4A', None, 'August'),
            (9, 91, '4A', None, 'September'),
            (10, 102, '4A', None, 'October'),
            (11, 137, '4A', None, 'November'),
            (12, 187, '4A', None, 'December'),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO evaporation_rates (month, evaporation_mm, zone, year, notes) VALUES (?, ?, ?, ?, ?)",
            evap_rates
        )
        
        # System constants (from our analysis)
        # NOTE: TSF_RETURN_RATE, MEAN_ANNUAL_EVAPORATION, PUMP_START_LEVEL, PUMP_STOP_LEVEL, 
        # BALANCE_ERROR_THRESHOLD, DEFAULT_MISSING_VALUE removed as they are not used by latest calculator
        constants = [
            ('MINING_WATER_RATE', 0.18, 'm³/tonne', 'calculation', 'Mining water requirement per tonne'),
            ('SLURRY_DENSITY', 1.4, 't/m³', 'calculation', 'Tailings slurry density'),
            ('CONCENTRATE_MOISTURE', 0.08, 'fraction', 'calculation', 'Moisture content in concentrate (8%)'),
            # Ore processing related (added Nov 2025 for moisture inflow configurability)
            ('monthly_ore_processing', 350000.0, 't/month', 'Plant', 'Default monthly ore processed tonnage used when no entry provided'),
            ('ore_moisture_percent', 3.4, 'percent', 'Plant', 'Average moisture percent of ore feed (used to derive water inflow from wet ore)'),
            ('ore_density', 2.7, 't/m³', 'Plant', 'Bulk density of run-of-mine ore used for moisture volume conversion'),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO system_constants (constant_key, constant_value, unit, category, description) VALUES (?, ?, ?, ?, ?)",
            constants
        )
        
        # Default alert rules
        alert_rules = [
            ('CRITICAL_STORAGE', 'Critical Storage Level', 'storage', 'days_cover', '<', 3.0, 'days',
             'critical', 'Critical Water Storage', 'Water storage critically low - only {metric_value:.1f} days remaining. Immediate action required!',
             1, 0, None, 1, 1, 1, 'Monitor days of operation cover'),
            
            ('LOW_STORAGE', 'Low Storage Warning', 'storage', 'days_cover', '<', 7.0, 'days',
             'warning', 'Low Water Storage', 'Water storage is low - {metric_value:.1f} days remaining. Plan water procurement.',
             1, 0, None, 1, 1, 2, 'Early warning for storage depletion'),
            
            ('MINIMUM_LEVEL_NEAR', 'Approaching Minimum Level', 'storage', 'days_to_minimum', '<', 5.0, 'days',
             'warning', 'Approaching Minimum Operating Level', 'Storage will reach minimum operating level in {metric_value:.1f} days.',
             1, 0, None, 1, 1, 2, 'Alert before reaching pump stop level'),
            
            ('HIGH_STORAGE', 'High Storage Level', 'level', 'storage_utilization', '>', 90.0, '%',
             'warning', 'High Storage Level', 'Storage utilization at {metric_value:.1f}% - overflow risk during rainfall.',
             1, 0, None, 1, 1, 3, 'Prevent overflow incidents'),
            
            ('LOW_LEVEL_ALARM', 'Low Level Alarm', 'level', 'level_percent', '<', 10.0, '%',
             'critical', 'Storage Level Critical', 'Facility at {metric_value:.1f}% capacity - below low level alarm.',
             1, 0, None, 1, 1, 1, 'Facility-specific low level'),
            
            ('HIGH_CLOSURE_ERROR', 'High Closure Error', 'compliance', 'closure_error_pct', '>', 5.0, '%',
             'warning', 'Water Balance Not Closed', 'Closure error {metric_value:.1f}% exceeds threshold - review measurements.',
             1, 0, None, 1, 1, 3, 'Data quality check'),
            
            ('EXCELLENT_SECURITY', 'Excellent Storage Security', 'storage', 'days_cover', '>', 30.0, 'days',
             'info', 'Excellent Water Security', 'Water storage excellent - {metric_value:.0f} days of operation cover.',
             0, 0, None, 1, 1, 5, 'Positive status notification'),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO alert_rules (
                rule_code, rule_name, rule_category, metric_name, condition_operator,
                threshold_value, threshold_unit, severity, alert_title, alert_message,
                show_popup, send_email, email_recipients, auto_resolve, active, priority, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, alert_rules)
        
        print("✅ Initial reference data inserted")
    
    def verify_database(self):
        """Verify database integrity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'mine_areas', 'water_source_types', 'water_sources',
                'storage_facilities', 'evaporation_rates', 'measurements',
                'calculations', 'operating_rules', 'system_constants',
                'alert_rules', 'alerts', 'audit_log', 'reports',
                'groundwater_inflow_monthly', 'data_quality_checks'
            ]
            
            print("\n📊 Database Verification:")
            print(f"  Tables created: {len(tables)}")
            
            for table in expected_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  ✅ {table}: {count} records")
                else:
                    print(f"  ❌ {table}: MISSING")
            
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Verification error: {e}")
            return False
        finally:
            conn.close()


def main():
    """Initialize database from command line"""
    schema = DatabaseSchema()
    
    if schema.db_path.exists():
        response = input(f"Database already exists at {schema.db_path}. Recreate? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
        schema.db_path.unlink()
    
    print("Creating database schema...")
    if schema.create_database():
        schema.verify_database()
        print(f"\n✅ Database ready: {schema.db_path}")
    else:
        print("\n❌ Database creation failed")


if __name__ == "__main__":
    main()
