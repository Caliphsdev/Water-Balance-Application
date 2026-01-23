"""
Database Manager
Handles all database operations with connection pooling and error handling
"""

import sqlite3
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import json
import sys
import time
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config
from utils.app_logger import logger


class DatabaseManager:
    """Database operations manager with connection handling"""
    
    # Class-level flag to avoid repeated constant checks across instances
    _constants_checked = False
    # Class-level flag for one-time unused constants cleanup
    _unused_cleanup_done = False
    # One-time sqlite adapter initialization
    _sqlite_adapters_initialized = False
    
    def __init__(self, db_path: str = None):
        """Initialize database manager
        Resolves a single, canonical database path in this order:
        1) Explicit `db_path` argument
        2) `config.get('database.path')` if set
        3) `WATERBALANCE_USER_DIR` env var → `<user_dir>/data/water_balance.db`
        4) Fallback to project `<repo>/data/water_balance.db`
        """
        if db_path is None:
            # Project base directory (may point to Program Files when frozen)
            base_dir = Path(__file__).parent.parent.parent

            # If launcher set a user data directory, prefer it for any relative path
            import os
            user_dir = os.environ.get('WATERBALANCE_USER_DIR')

            cfg_path = config.get('database.path', None)

            if cfg_path:
                cfg_path = Path(cfg_path)
                if cfg_path.is_absolute():
                    db_path = cfg_path
                else:
                    # Relative path → place under user data dir when available, otherwise under base_dir
                    if user_dir:
                        db_path = Path(user_dir) / cfg_path
                    else:
                        db_path = base_dir / cfg_path
            else:
                # No configured path: default to user data dir if available
                if user_dir:
                    db_path = Path(user_dir) / 'data' / 'water_balance.db'
                else:
                    # Development fallback: repo-local path
                    db_path = base_dir / 'data' / 'water_balance.db'

        self.db_path = Path(db_path)
        
        # Performance optimization: cache for frequently accessed static data
        self._sources_cache = None
        self._facilities_cache = None
        self._cache_timestamp = None
        # Event listeners (simple pub/sub for UI cache invalidation)
        self._listeners = []
        
        # Ensure database exists
        if not self.db_path.exists():
            from database.schema import DatabaseSchema
            from utils.app_logger import logger
            
            # Create the directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to seed from bundled database (in PyInstaller _internal folder or dev repo)
            bundled_db = Path(__file__).parent.parent.parent / '_internal' / 'data' / 'water_balance.db'
            if not bundled_db.exists():
                # Dev fallback
                bundled_db = Path(__file__).parent.parent.parent / 'data' / 'water_balance.db'
            
            if bundled_db.exists() and bundled_db != self.db_path:
                try:
                    # Copy bundled database (has all the water sources and reference data)
                    shutil.copy2(bundled_db, self.db_path)
                    logger.info(f"Database seeded from bundled copy: {bundled_db}")
                except Exception as e:
                    logger.warning(f"Failed to seed database from {bundled_db}, creating empty schema: {e}")
                    # Fall back to creating empty database
                    schema = DatabaseSchema(str(self.db_path))
                    schema.create_database()
            else:
                # No bundled database, create fresh schema
                schema = DatabaseSchema(str(self.db_path))
                schema.create_database()
        else:
            # Perform non-destructive schema migration on existing databases.
            # WHY: New tables like pump_transfer_events may be added over time;
            # running migrate here ensures idempotent creation without data loss.
            try:
                from database.schema import DatabaseSchema
                schema = DatabaseSchema(str(self.db_path))
                schema.migrate_database()
            except Exception:
                # If migration fails, continue; callers will surface specific errors as needed.
                pass
        
        # Log resolved DB path (DEBUG level - not shown on console)
        try:
            from utils.app_logger import logger
            logger.debug(f"Database connected: {self.db_path}")
        except Exception:
            pass

        # Ensure extended calculation columns (non-destructive migration)
        self._ensure_extended_calculation_columns()
        # Ensure storage facilities table has newer columns (evap_active, is_lined)
        self._ensure_storage_facility_columns()
        # Ensure required system constants exist (idempotent)
        try:
            self._ensure_all_constants()
            DatabaseManager._constants_checked = True
        except Exception:
            pass  # Non-critical
        # Auto-remove constants not used by the latest calculation engine (once per process)
        if not DatabaseManager._unused_cleanup_done:
            try:
                self._auto_remove_constants_not_used_in_calculator()
                DatabaseManager._unused_cleanup_done = True
            except Exception:
                pass

        # One-time sqlite adapter registration to silence default adapter warnings
        if not DatabaseManager._sqlite_adapters_initialized:
            try:
                self._initialize_sqlite_adapters()
                DatabaseManager._sqlite_adapters_initialized = True
            except Exception:
                # Non-critical; continue without custom adapters
                pass
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory and foreign key enforcement.
        
        Returns a SQLite connection configured for this application:
        - Row factory: Enables dict-like column access (rows["column_name"])
        - Foreign keys: Enforces referential integrity (ON cascading deletes)
        
        Returns:
            sqlite3.Connection: Configured database connection ready for queries
            
        Note: Connections should be closed after use. Context managers recommended.
        """
        conn = sqlite3.connect(self.db_path)
        # Enable dict-like access to columns (easier than index-based access)
        conn.row_factory = sqlite3.Row
        # Enforce foreign key constraints (data integrity and referential consistency)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _initialize_sqlite_adapters() -> None:
        """Register adapters to suppress deprecated SQLite date/datetime warnings.
        
        SQLite 3.42+ changed default date handling to issue deprecation warnings.
        This method configures explicit adapters to:
        1. Serialize Python date/datetime to ISO 8601 strings (TEXT columns)
        2. Suppress deprecation warnings that would clutter logs
        
        This is a one-time setup (called during __init__ on first DatabaseManager instantiation).
        
        Note: Converters are registered but optional; they're used only if detect_types is enabled.
        """
        # Serialize date/datetime to ISO strings explicitly (TEXT columns in database)
        sqlite3.register_adapter(date, lambda d: d.isoformat())
        sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())

        # Converters optional; keep behavior consistent if enabled via detect_types
        sqlite3.register_converter("DATE", lambda s: date.fromisoformat(s.decode()))
        sqlite3.register_converter("TIMESTAMP", lambda s: datetime.fromisoformat(s.decode()))

        # Proactively silence deprecation warnings to keep logs clean
        warnings.filterwarnings(
            "ignore",
            message="The default date adapter is deprecated",
            category=DeprecationWarning,
            module="sqlite3",
        )
        warnings.filterwarnings(
            "ignore",
            message="The default datetime adapter is deprecated",
            category=DeprecationWarning,
            module="sqlite3",
        )
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results as list of dicts (MAIN READ METHOD).
        
        This is the PRIMARY read interface for dashboard and UI queries.
        
        Args:
            query: SQL SELECT statement (can include ? placeholders for params)
            params: Optional tuple of parameters to bind (SQL injection prevention)
        
        Returns:
            List of dicts where each dict is a row (columns accessible by name)
            Empty list if no results
        
        Raises:
            sqlite3.OperationalError: If query is malformed or database unreachable
            sqlite3.DatabaseError: If database is corrupted
        
        Example:
            results = db.execute_query(
                "SELECT facility_code, capacity FROM storage_facilities WHERE active = ?",
                (True,)
            )
            for row in results:
                print(f"Facility: {row['facility_code']}, Capacity: {row['capacity']} m³")
        
        Performance Note: Results are fetched into memory. For large result sets (>10k rows),
        consider using execute_query_generator() to stream results instead.
        """
        start_time = time.perf_counter()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
            elapsed = (time.perf_counter() - start_time) * 1000
            from utils.app_logger import logger
            query_preview = query[:50].replace('\n', ' ')
            if elapsed > 100:
                logger.info(f"⚠️  SLOW query ({elapsed:.0f}ms): {query_preview}... ({len(result)} rows)")
            else:
                logger.debug(f"PERF: DB query ({query_preview}..., {len(result)} rows) in {elapsed:.2f}ms")
            
            return result
        finally:
            conn.close()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        start_time = time.perf_counter()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            rowcount = cursor.rowcount
            
            elapsed = (time.perf_counter() - start_time) * 1000
            from utils.app_logger import logger
            query_preview = query[:50].replace('\n', ' ')
            if elapsed > 100:
                logger.info(f"⚠️  SLOW update ({elapsed:.0f}ms): {query_preview}... ({rowcount} rows affected)")
            else:
                logger.debug(f"PERF: DB update ({query_preview}..., {rowcount} rows affected) in {elapsed:.2f}ms")
            
            return rowcount
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute INSERT and return last inserted ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def apply_pump_transfers(self, calculation_date: date, transfers_report: Dict[str, Dict], user: str = 'system') -> int:
        """Apply pump transfers transactionally and log audit events (IDEMPOTENT).

        This method updates `storage_facilities.current_volume` for both source and
        destination facilities according to the computed `transfers_report`, then
        records each application in `pump_transfer_events`. It enforces idempotency
        by checking for existing events for the given date and source/destination
        pair and will skip re-applying to avoid double-counting.

        Args:
            calculation_date: The date of the balance calculation (month-level is acceptable).
            transfers_report: The structure returned by `PumpTransferEngine.calculate_pump_transfers()`.
            user: Username performing the operation (for audit trail).

        Returns:
            Number of transfer rows applied (inserted into `pump_transfer_events`).

        Raises:
            sqlite3.Error: On database failures; transaction is rolled back.

        Example:
            applied = db.apply_pump_transfers(date(2025, 10, 1), pump_transfers, user='admin')
        """
        if not transfers_report:
            return 0

        conn = self.get_connection()
        applied_count = 0
        try:
            cur = conn.cursor()
            # Begin atomic operation
            cur.execute("BEGIN")

            # Helper: lookup facility by code → row
            def _lookup_facility(code: str) -> Optional[sqlite3.Row]:
                cur.execute("SELECT * FROM storage_facilities WHERE UPPER(facility_code) = UPPER(?) LIMIT 1", (code,))
                row = cur.fetchone()
                return row

            # Pilot gating configuration (rollout control):
            # - scope 'global' applies to all facilities
            # - scope 'pilot-area' applies only when the source facility's area_code is in the configured list
            # WHY: Enable safe staged rollout by constraining auto-apply to selected mining areas first.
            scope = (config.get('features.auto_apply_pump_transfers_scope', 'global') or 'global').lower()
            pilot_areas = set([a.upper() for a in (config.get('features.auto_apply_pump_transfers_pilot_areas', []) or [])])

            def _get_area_code(area_id: Optional[int]) -> Optional[str]:
                """Resolve area_code from area_id (local helper for pilot gating).
                Returns None when area_id is null or lookup fails.
                """
                if not area_id:
                    return None
                try:
                    cur.execute("SELECT area_code FROM mine_areas WHERE area_id = ? LIMIT 1", (area_id,))
                    row = cur.fetchone()
                    return row[0] if row else None
                except Exception:
                    return None

            for source_code, payload in transfers_report.items():
                transfers = payload.get('transfers') or []
                if not transfers:
                    # No eligible destination; still track that evaluation happened via audit_log
                    continue

                source_row = _lookup_facility(source_code)
                if not source_row:
                    continue

                # Pilot-area gating: skip application if source facility's area is not in pilot list
                # (Only enforced when scope == 'pilot-area').
                if scope == 'pilot-area':
                    src_area_code = _get_area_code(source_row['area_id'])
                    if pilot_areas and (src_area_code is None or src_area_code.upper() not in pilot_areas):
                        # Skip applying transfers for non-pilot areas
                        continue

                source_current = float(source_row['current_volume'] or 0.0)
                for t in transfers:
                    dest_code = t.get('destination')
                    vol = float(t.get('volume_m3') or 0.0)
                    if vol <= 0:
                        continue

                    # Idempotency check: existing event for (date, source, dest)
                    cur.execute(
                        "SELECT 1 FROM pump_transfer_events WHERE calc_date = ? AND source_code = ? AND dest_code = ? LIMIT 1",
                        (calculation_date, source_code, dest_code)
                    )
                    if cur.fetchone():
                        # Already applied; skip to prevent double application
                        continue

                    dest_row = _lookup_facility(dest_code)
                    if not dest_row:
                        continue

                    dest_current = float(dest_row['current_volume'] or 0.0)
                    # Compute new volumes (clamp at 0 for source; destination safe due to engine checks)
                    new_source = max(0.0, source_current - vol)
                    new_dest = dest_current + vol

                    # Update source and destination current volumes + level percent
                    # Inline to keep single transaction and minimal round-trips
                    def _level_percent(volume: float, capacity: float) -> float:
                        return (volume / capacity * 100.0) if capacity and capacity > 0 else 0.0

                    source_capacity = float(source_row['total_capacity'] or 0.0)
                    dest_capacity = float(dest_row['total_capacity'] or 0.0)

                    cur.execute(
                        """
                        UPDATE storage_facilities
                        SET current_volume = ?, current_level_percent = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE facility_id = ?
                        """,
                        (new_source, _level_percent(new_source, source_capacity), source_row['facility_id'])
                    )

                    cur.execute(
                        """
                        UPDATE storage_facilities
                        SET current_volume = ?, current_level_percent = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE facility_id = ?
                        """,
                        (new_dest, _level_percent(new_dest, dest_capacity), dest_row['facility_id'])
                    )

                    # Insert audit event (destination level before/after included)
                    cur.execute(
                        """
                        INSERT INTO pump_transfer_events (
                            calc_date, source_code, dest_code, volume_m3,
                            destination_level_before, destination_level_after, reason,
                            applied_by, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'applied')
                        """,
                        (
                            calculation_date, source_code, dest_code, vol,
                            float(t.get('destination_level_before') or 0.0),
                            float(t.get('destination_level_after') or 0.0),
                            t.get('reason') or 'Automatic pump transfer',
                            user,
                        )
                    )

                    # Update source_current for chained transfers from same source (if any)
                    source_current = new_source
                    applied_count += 1

            # Commit atomic changes and notify caches
            conn.commit()
            self.invalidate_all_caches()
            return applied_count
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ==================== WATER SOURCES ====================
    
    def get_water_sources(self, active_only: bool = True, use_cache: bool = True) -> List[Dict]:
        """Get all water sources
        
        Args:
            active_only: Return only active sources
            use_cache: Use cached data if available (default True)
        """
        # Check cache (performance optimization)
        if use_cache and self._sources_cache is not None:
            if active_only:
                return [s for s in self._sources_cache if s.get('active', 0) == 1]
            return self._sources_cache
        
        query = """
            SELECT ws.*, wst.type_name, wst.type_code, wst.color_code,
                   ma.area_name, ma.area_code
            FROM water_sources ws
            LEFT JOIN water_source_types wst ON ws.type_id = wst.type_id
            LEFT JOIN mine_areas ma ON ws.area_id = ma.area_id
            ORDER BY ws.source_code
        """
        
        result = self.execute_query(query)
        
        # Always cache all sources, filter active_only on retrieval
        if use_cache:
            self._sources_cache = result
        
        # Filter after caching
        if active_only:
            result = [s for s in result if s.get('active', 0) == 1]
        
        return result
    
    def get_water_source(self, source_id: int) -> Optional[Dict]:
        """Get single water source by ID"""
        query = """
            SELECT ws.*, wst.type_name, wst.type_code,
                   ma.area_name, ma.area_code
            FROM water_sources ws
            LEFT JOIN water_source_types wst ON ws.type_id = wst.type_id
            LEFT JOIN mine_areas ma ON ws.area_id = ma.area_id
            WHERE ws.source_id = ?
        """
        results = self.execute_query(query, (source_id,))
        return results[0] if results else None
    
    def add_water_source(self, **data) -> int:
        """Add new water source"""
        query = """
            INSERT INTO water_sources (
                source_code, source_name, type_id, area_id, description, source_purpose,
                authorized_volume, authorization_period, max_flow_rate,
                average_flow_rate, flow_units, reliability_factor,
                latitude, longitude, depth, river_name, active,
                commissioned_date, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['source_code'], data['source_name'], data['type_id'],
            data.get('area_id'), data.get('description'), data.get('source_purpose','ABSTRACTION'),
            data.get('authorized_volume'), data.get('authorization_period'),
            data.get('max_flow_rate'),
            data.get('average_flow_rate'), data.get('flow_units', 'm³/month'),
            data.get('reliability_factor', 1.0),
            data.get('latitude'), data.get('longitude'),
            data.get('depth'), data.get('river_name'), data.get('active', 1),
            data.get('commissioned_date'), data.get('created_by', 'system')
        )
        result = self.execute_insert(query, params)
        self._invalidate_sources_cache()
        return result
    
    def update_water_source(self, source_id: int, **data) -> int:
        """Update water source"""
        query = """
            UPDATE water_sources SET
                source_code = ?, source_name = ?, type_id = ?, source_purpose = ?,
                average_flow_rate = ?, flow_units = ?, reliability_factor = ?,
                description = ?, active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE source_id = ?
        """
        params = (
            data['source_code'], data['source_name'], data['type_id'], data.get('source_purpose','ABSTRACTION'),
            data.get('average_flow_rate'), data.get('flow_units', 'm³/month'),
            data.get('reliability_factor', 1.0),
            data.get('description'), data.get('active', 1), source_id
        )
        result = self.execute_update(query, params)
        self._invalidate_sources_cache()
        return result

    def classify_source_purposes(self) -> int:
        """Classify source_purpose using abstraction measurements only (monitoring removed)."""
        abstraction_types = {'source_flow'}
        rows = self.execute_query("SELECT source_id, source_purpose FROM water_sources")
        updated = 0
        for r in rows:
            sid = r['source_id']
            m_rows = self.execute_query(
                "SELECT measurement_type, COUNT(*) as cnt FROM measurements WHERE source_id = ? GROUP BY measurement_type",
                (sid,)
            )
            if not m_rows:
                continue
            has_abstraction = any(m['measurement_type'] in abstraction_types for m in m_rows)
            new_purpose = 'ABSTRACTION' if has_abstraction else (r['source_purpose'] or 'ABSTRACTION')
            if new_purpose != r['source_purpose']:
                self.execute_update("UPDATE water_sources SET source_purpose = ?, updated_at = CURRENT_TIMESTAMP WHERE source_id = ?", (new_purpose, sid))
                updated += 1
        if updated:
            self._invalidate_sources_cache()
        return updated
    
    def activate_water_source(self, source_id: int) -> int:
        """Activate (restore) a water source"""
        query = "UPDATE water_sources SET active = 1, updated_at = CURRENT_TIMESTAMP WHERE source_id = ?"
        result = self.execute_update(query, (source_id,))
        self._invalidate_sources_cache()
        return result
    
    def delete_water_source(self, source_id: int) -> int:
        """Soft delete water source"""
        query = "UPDATE water_sources SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE source_id = ?"
        result = self.execute_update(query, (source_id,))
        self._invalidate_sources_cache()
        return result

    def delete_water_source_cascade(self, source_id: int, hard: bool = True) -> int:
        """Delete a water source and cascade remove its dependent records.
        Args:
            source_id: ID of the water source to remove.
            hard: If True perform hard DELETE (FK cascades will remove measurements,
                  borehole_details, alerts). If False performs soft delete but also
                  explicitly deletes measurements for integrity.
        Returns:
            Number of water_sources rows affected (0 or 1).
        """
        # Fetch existing for logging/audit (if exists)
        existing = self.get_water_source(source_id)
        if not existing:
            return 0
        if hard:
            # Hard delete (FK ON DELETE CASCADE in schema handles dependent rows)
            rows = self.execute_update("DELETE FROM water_sources WHERE source_id = ?", (source_id,))
            if rows:
                self.log_change('water_sources', source_id, 'delete', old_values={'source_code': existing.get('source_code')})
        else:
            # Soft delete + explicit measurement removal to avoid residual inflows
            rows = self.delete_water_source(source_id)
            if rows:
                self.execute_update("DELETE FROM measurements WHERE source_id = ?", (source_id,))
                self.execute_update("DELETE FROM borehole_details WHERE source_id = ?", (source_id,))
                self.execute_update("DELETE FROM alerts WHERE source_id = ?", (source_id,))
        self._invalidate_sources_cache()
        return rows

    def delete_water_source_by_code_cascade(self, source_code: str, hard: bool = True) -> int:
        """Convenience method: cascade delete by source_code.
        Args:
            source_code: unique code of the source to remove.
            hard: pass-through to delete_water_source_cascade.
        Returns:
            Rows affected (0 or 1).
        """
        rows = self.execute_query("SELECT source_id FROM water_sources WHERE source_code = ?", (source_code,))
        if not rows:
            return 0
        return self.delete_water_source_cascade(rows[0]['source_id'], hard=hard)
    
    # ==================== STORAGE FACILITIES ====================
    
    def get_storage_facilities(self, active_only: bool = True, use_cache: bool = True) -> List[Dict]:
        """Get all storage facilities with type information
        
        Args:
            active_only: Return only active facilities
            use_cache: Use cached data if available (default True)
        """
        # Check cache (performance optimization)
        if use_cache and self._facilities_cache is not None:
            if active_only:
                return [f for f in self._facilities_cache if f.get('active', 0) == 1]
            return self._facilities_cache
        
        query = """
            SELECT sf.*, sf.facility_type as type_name,
                   ma.area_name, ma.area_code
            FROM storage_facilities sf
            LEFT JOIN mine_areas ma ON sf.area_id = ma.area_id
            ORDER BY sf.facility_code
        """
        
        result = self.execute_query(query)
        
        # Always cache all facilities, filter active_only on retrieval
        if use_cache:
            self._facilities_cache = result
        
        # Filter after caching
        if active_only:
            result = [f for f in result if f.get('active', 0) == 1]
        
        return result
    
    def get_storage_facility(self, facility_id: int) -> Optional[Dict]:
        """Get single storage facility by ID"""
        query = """
            SELECT sf.*, ma.area_name, ma.area_code
            FROM storage_facilities sf
            LEFT JOIN mine_areas ma ON sf.area_id = ma.area_id
            WHERE sf.facility_id = ?
        """
        results = self.execute_query(query, (facility_id,))
        return results[0] if results else None
    
    def add_storage_facility(self, **data) -> int:
        """Add new storage facility"""
        query = """
            INSERT INTO storage_facilities (
                facility_code, facility_name, facility_type, area_id,
                total_capacity, working_capacity, surface_area,
                pump_start_level, pump_stop_level, high_level_alarm,
                max_depth, purpose, water_quality,
                current_volume, description, active, commissioned_date, feeds_to,
                evap_active, is_lined
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Ensure pump_start > pump_stop for constraint
        pump_start = data.get('pump_start_level', 70.0)
        pump_stop = data.get('pump_stop_level', 20.0)
        if pump_start <= pump_stop:
            pump_start = 70.0
            pump_stop = 20.0
        
        params = (
            data['facility_code'], data['facility_name'], data['facility_type'],
            data.get('area_id'), data.get('total_capacity'),
            data.get('working_capacity'),
            data.get('surface_area'), pump_start, pump_stop,
            data.get('high_level_alarm', 90.0),
            data.get('max_depth'),
            data.get('purpose', 'raw_water'), data.get('water_quality', 'process'),
            data.get('current_volume', 0),
            data.get('description'),
            data.get('active', 1), data.get('commissioned_date'),
            data.get('feeds_to'),
            data.get('evap_active', 1), data.get('is_lined', 0)
        )
        result = self.execute_insert(query, params)
        self._invalidate_facilities_cache()
        return result
    
    def update_storage_facility(self, facility_id: int, **data) -> int:
        """Update storage facility"""
        query = """
            UPDATE storage_facilities SET
                facility_code = ?, facility_name = ?, facility_type = ?,
                total_capacity = ?, current_volume = ?, surface_area = ?,
                pump_start_level = ?, pump_stop_level = ?,
                high_level_alarm = ?,
                max_depth = ?,
                description = ?, active = ?, purpose = ?, water_quality = ?,
                feeds_to = ?, evap_active = ?, is_lined = ?, updated_at = CURRENT_TIMESTAMP
            WHERE facility_id = ?
        """
        # Ensure pump_start > pump_stop
        pump_start = data.get('pump_start_level', 70.0)
        pump_stop = data.get('pump_stop_level', 20.0)
        if pump_start <= pump_stop:
            pump_start = 70.0
            pump_stop = 20.0
        
        params = (
            data['facility_code'], data['facility_name'], data.get('facility_type'),
            data.get('total_capacity'),
            data.get('current_volume', 0), data.get('surface_area'),
            pump_start, pump_stop,
            data.get('high_level_alarm', 90.0),
            data.get('max_depth'),
            data.get('description'), data.get('active', 1), data.get('purpose', 'raw_water'),
            data.get('water_quality', 'process'), data.get('feeds_to'),
            data.get('evap_active', 1), data.get('is_lined', 0), facility_id
        )
        result = self.execute_update(query, params)
        self._invalidate_facilities_cache()
        return result
    
    def update_facility_level(self, facility_id: int, volume: float) -> int:
        """Update current volume and calculate level percentage"""
        # First get capacity
        facility = self.get_storage_facility(facility_id)
        if not facility:
            raise ValueError(f"Facility {facility_id} not found")
        
        level_percent = (volume / facility['total_capacity']) * 100 if facility['total_capacity'] > 0 else 0
        
        query = """
            UPDATE storage_facilities SET
                current_volume = ?, current_level_percent = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE facility_id = ?
        """
        return self.execute_update(query, (volume, level_percent, facility_id))
    
    def delete_storage_facility(self, facility_id: int) -> int:
        """Soft delete storage facility"""
        query = "UPDATE storage_facilities SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE facility_id = ?"
        result = self.execute_update(query, (facility_id,))
        self._invalidate_facilities_cache()
        return result

    def delete_storage_facilities(self, facility_ids: List[int]) -> int:
        """Bulk hard delete storage facilities by IDs.
        Args:
            facility_ids: list of facility_id integers.
        Returns:
            Number of rows deleted.
        """
        if not facility_ids:
            return 0
        placeholders = ",".join(["?"] * len(facility_ids))
        query = f"DELETE FROM storage_facilities WHERE facility_id IN ({placeholders})"
        result = self.execute_update(query, tuple(facility_ids))
        self._invalidate_facilities_cache()
        return result

    def hard_delete_storage_facility(self, facility_id: int) -> int:
        """Hard delete a storage facility and cascade delete dependent records.
        Removes rows in related tables that reference the facility to satisfy
        foreign key constraints, then deletes the facility itself.

        Returns:
            1 if the facility row was deleted, otherwise 0.
        """
        # Fetch existing for audit context
        existing = self.get_storage_facility(facility_id)
        if not existing:
            return 0

        # Delete explicit dependents first where ON DELETE CASCADE isn't defined
        # Measurements and monthly configs have CASCADE, but alerts and operating_rules do not.
        try:
            # Alerts referencing facility
            self.execute_update("DELETE FROM alerts WHERE facility_id = ?", (facility_id,))
            # Operating rules for this facility
            self.execute_update("DELETE FROM operating_rules WHERE facility_id = ?", (facility_id,))
            # Measurements (also covered by FK CASCADE, kept for clarity)
            self.execute_update("DELETE FROM measurements WHERE facility_id = ?", (facility_id,))
            # Monthly rainfall/evap/flow rows (FK CASCADE exists; explicit for completeness)
            self.execute_update("DELETE FROM facility_rainfall_monthly WHERE facility_id = ?", (facility_id,))
            self.execute_update("DELETE FROM facility_evaporation_monthly WHERE facility_id = ?", (facility_id,))
            self.execute_update("DELETE FROM facility_inflow_monthly WHERE facility_id = ?", (facility_id,))
            self.execute_update("DELETE FROM facility_outflow_monthly WHERE facility_id = ?", (facility_id,))
            self.execute_update("DELETE FROM facility_abstraction_monthly WHERE facility_id = ?", (facility_id,))
            # Finally delete the facility
            rows = self.execute_update("DELETE FROM storage_facilities WHERE facility_id = ?", (facility_id,))
            if rows:
                self.log_change('storage_facilities', facility_id, 'delete', old_values={'facility_code': existing.get('facility_code')})
            self._invalidate_facilities_cache()
            return rows
        except sqlite3.Error:
            # If anything fails, propagate to caller for test visibility
            raise
    
    # ==================== MEASUREMENTS ====================
    
    def add_measurement(self, data: Dict) -> int:
        """Add new measurement (monitoring-specific fields removed)."""
        query = """
            INSERT INTO measurements (
                measurement_date, measurement_type, source_id, facility_id,
                volume, flow_rate, level_meters, level_percent, rainfall_mm,
                measured, quality_flag, data_source, notes, recorded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['measurement_date'], data['measurement_type'],
            data.get('source_id'), data.get('facility_id'),
            data.get('volume'), data.get('flow_rate'),
            data.get('level_meters'), data.get('level_percent'),
            data.get('rainfall_mm'),
            data.get('measured', 1), data.get('quality_flag', 'good'),
            data.get('data_source', 'manual'), data.get('notes'),
            data.get('recorded_by', 'system')
        )
        new_id = self.execute_insert(query, params)
        self._notify('measurement_added', {
            'measurement_id': new_id,
            'measurement_type': data.get('measurement_type'),
            'source_id': data.get('source_id'),
            'facility_id': data.get('facility_id'),
            'measurement_date': data.get('measurement_date')
        })
        return new_id
    
    def get_measurements(self, start_date: date, end_date: date,
                        measurement_type: str = None) -> List[Dict]:
        """Get measurements for date range"""
        query = """
            SELECT m.*, ws.source_code, ws.source_name,
                   sf.facility_code, sf.facility_name
            FROM measurements m
            LEFT JOIN water_sources ws ON m.source_id = ws.source_id
            LEFT JOIN storage_facilities sf ON m.facility_id = sf.facility_id
            WHERE m.measurement_date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        
        if measurement_type:
            query += " AND m.measurement_type = ?"
            params.append(measurement_type)
        
        query += " ORDER BY m.measurement_date DESC, m.measurement_type"
        
        return self.execute_query(query, tuple(params))

    def delete_measurements(self, measurement_ids: List[int]) -> int:
        """Bulk delete measurements by IDs.
        Args:
            measurement_ids: list of measurement_id integers.
        Returns:
            Number of rows deleted.
        """
        if not measurement_ids:
            return 0
        # Build placeholders safely
        placeholders = ",".join(["?"] * len(measurement_ids))
        query = f"DELETE FROM measurements WHERE measurement_id IN ({placeholders})"
        return self.execute_update(query, tuple(measurement_ids))

    # ==================== MONTHLY MANUAL INPUTS ====================

    def upsert_monthly_manual_inputs(self, month_start: date, values: Dict) -> None:
        """Insert or replace monthly manual inputs for auxiliary/outflow categories."""
        record = {
            'month_start': month_start,
            'dust_suppression_m3': float(values.get('dust_suppression_m3', 0) or 0),
            'mining_consumption_m3': float(values.get('mining_consumption_m3', 0) or 0),
            'domestic_consumption_m3': float(values.get('domestic_consumption_m3', 0) or 0),
            'discharge_m3': float(values.get('discharge_m3', 0) or 0),
            'product_moisture_m3': float(values.get('product_moisture_m3', 0) or 0),
            'tailings_retention_m3': float(values.get('tailings_retention_m3', 0) or 0),
            'notes': values.get('notes'),
        }
        self.execute_update(
            """
            INSERT INTO monthly_manual_inputs (
                month_start, dust_suppression_m3, mining_consumption_m3, domestic_consumption_m3,
                discharge_m3, product_moisture_m3, tailings_retention_m3, notes, updated_at
            ) VALUES (:month_start, :dust_suppression_m3, :mining_consumption_m3, :domestic_consumption_m3,
                      :discharge_m3, :product_moisture_m3, :tailings_retention_m3, :notes, CURRENT_TIMESTAMP)
            ON CONFLICT(month_start) DO UPDATE SET
                dust_suppression_m3=excluded.dust_suppression_m3,
                mining_consumption_m3=excluded.mining_consumption_m3,
                domestic_consumption_m3=excluded.domestic_consumption_m3,
                discharge_m3=excluded.discharge_m3,
                product_moisture_m3=excluded.product_moisture_m3,
                tailings_retention_m3=excluded.tailings_retention_m3,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            """,
            record
        )

    def get_monthly_manual_inputs(self, month_start: date) -> Dict:
        """Return monthly manual inputs; defaults to zeroed structure when missing."""
        try:
            row = self.execute_query(
                "SELECT * FROM monthly_manual_inputs WHERE month_start = ? LIMIT 1",
                (month_start,)
            )
            if row:
                return row[0]
        except Exception:
            pass  # Table may not exist yet; caller will see zero defaults
        return {
            'month_start': month_start,
            'dust_suppression_m3': 0.0,
            'mining_consumption_m3': 0.0,
            'domestic_consumption_m3': 0.0,
            'discharge_m3': 0.0,
            'product_moisture_m3': 0.0,
            'tailings_retention_m3': 0.0,
            'notes': None,
        }

    # ==================== METADATA HELPERS ====================

    def get_latest_data_date(self) -> Optional[date]:
        """Return the latest date present in calculations, measurements, or manual inputs."""
        candidates: List[date] = []
        try:
            calc_row = self.execute_query("SELECT MAX(calc_date) as d FROM calculations")
            if calc_row and calc_row[0].get('d'):
                candidates.append(datetime.strptime(calc_row[0]['d'], "%Y-%m-%d").date())
        except Exception:
            pass
        try:
            meas_row = self.execute_query("SELECT MAX(measurement_date) as d FROM measurements")
            if meas_row and meas_row[0].get('d'):
                candidates.append(datetime.strptime(meas_row[0]['d'], "%Y-%m-%d").date())
        except Exception:
            pass
        try:
            manual_row = self.execute_query("SELECT MAX(month_start) as d FROM monthly_manual_inputs")
            if manual_row and manual_row[0].get('d'):
                candidates.append(datetime.strptime(manual_row[0]['d'], "%Y-%m-%d").date())
        except Exception:
            pass
        if not candidates:
            return None
        return max(candidates)
    
    # ==================== CALCULATIONS ====================
    
    def save_calculation(self, data: Dict) -> int:
        """Save water balance calculation"""
        # Derive quality metrics if not provided
        if 'calc_quality_flag' not in data or 'estimated_component_count' not in data:
            qflag, est_count, est_fraction = self._derive_calc_quality(data['calc_date'])
            data.setdefault('calc_quality_flag', qflag)
            data.setdefault('estimated_component_count', est_count)
            data.setdefault('estimated_volume_fraction', est_fraction)
        query = """
            INSERT OR REPLACE INTO calculations (
                calc_date, calc_type, total_inflows, total_outflows,
                storage_change, balance_error, balance_error_percent,
                river_inflow, borehole_inflow, underground_inflow,
                rainfall_inflow, return_water_inflow,
                plant_consumption, mining_consumption, evaporation_loss,
                seepage_loss, dust_suppression, domestic_consumption,
                product_moisture, tsf_slurry_volume, tsf_return_volume,
                tsf_return_percent, plant_makeup_water, mining_water_requirement,
                tonnes_mined, tonnes_processed, concentrate_produced,
                calculated_by, notes,
                surface_water_inflow, groundwater_inflow, ore_moisture_inflow,
                tsf_return_inflow, plant_returns_inflow, returns_to_pit_inflow,
                seepage_gain_inflow, plant_consumption_gross, plant_consumption_net,
                tailings_retention_loss, closure_error_m3, closure_error_percent,
                balance_status, calc_quality_flag, estimated_component_count,
                estimated_volume_fraction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['calc_date'], data.get('calc_type', 'daily'),
            data.get('total_inflows', 0), data.get('total_outflows', 0),
            data.get('storage_change', 0), data.get('balance_error', 0),
            data.get('balance_error_percent', 0),
            data.get('river_inflow', 0), data.get('borehole_inflow', 0),
            data.get('underground_inflow', 0), data.get('rainfall_inflow', 0),
            data.get('return_water_inflow', 0),
            data.get('plant_consumption', 0), data.get('mining_consumption', 0),
            data.get('evaporation_loss', 0), data.get('seepage_loss', 0),
            data.get('dust_suppression', 0), data.get('domestic_consumption', 0),
            data.get('product_moisture', 0), data.get('tsf_slurry_volume', 0),
            data.get('tsf_return_volume', 0), data.get('tsf_return_percent', 0),
            data.get('plant_makeup_water', 0), data.get('mining_water_requirement', 0),
            data.get('tonnes_mined', 0), data.get('tonnes_processed', 0),
            data.get('concentrate_produced', 0),
            data.get('calculated_by', 'system'), data.get('notes'),
            data.get('surface_water_inflow', 0), data.get('groundwater_inflow', 0),
            data.get('ore_moisture_inflow', 0), data.get('tsf_return_inflow', 0),
            data.get('plant_returns_inflow', 0), data.get('returns_to_pit_inflow', 0),
            data.get('seepage_gain_inflow', 0), data.get('plant_consumption_gross', 0),
            data.get('plant_consumption_net', 0), data.get('tailings_retention_loss', 0),
            data.get('closure_error_m3', data.get('balance_error', 0)),
            data.get('closure_error_percent', data.get('balance_error_percent', 0)),
            data.get('balance_status', None), data.get('calc_quality_flag', 'good'),
            data.get('estimated_component_count', 0),
            data.get('estimated_volume_fraction', 0.0)
        )
        return self.execute_insert(query, params)
    
    def get_calculations(self, start_date: date, end_date: date,
                        calc_type: str = None) -> List[Dict]:
        """Get calculations for date range"""
        query = "SELECT * FROM calculations WHERE calc_date BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if calc_type:
            query += " AND calc_type = ?"
            params.append(calc_type)
        
        query += " ORDER BY calc_date DESC"
        
        return self.execute_query(query, tuple(params))

    def get_closure_error_trend(self, days: int = 90) -> List[Dict]:
        """Return list of recent closure error values for trend chart.
        Args:
            days: Number of most recent days to include.
        Returns:
            List of dicts sorted by ascending date: [{calc_date, closure_error_m3, closure_error_percent}]
        """
        if days <= 0:
            return []
        rows = self.execute_query(
            "SELECT calc_date, closure_error_m3, closure_error_percent FROM calculations ORDER BY calc_date DESC LIMIT ?",
            (days,)
        )
        # Reverse to chronological order (oldest first)
        return list(reversed(rows))
    
    # ==================== REFERENCE DATA ====================
    
    def get_mine_areas(self) -> List[Dict]:
        """Get all mine areas"""
        return self.execute_query("SELECT * FROM mine_areas WHERE active = 1 ORDER BY area_code")
    
    def get_water_source_types(self) -> List[Dict]:
        """Get all water source types"""
        return self.execute_query("SELECT * FROM water_source_types ORDER BY type_name")
    
    def get_source_types(self) -> List[Dict]:
        """Alias for get_water_source_types for backward compatibility"""
        return self.get_water_source_types()
    
    def get_facility_types(self) -> List[Dict]:
        """Get distinct facility types from storage_facilities"""
        # Since facility_type is just a text field, get unique values
        query = """
            SELECT DISTINCT facility_type as type_name, facility_type as type_id
            FROM storage_facilities 
            WHERE active = 1
            ORDER BY facility_type
        """
        return self.execute_query(query)
    
    def get_evaporation_rate(self, month: int, zone: str = None) -> float:
        """Get evaporation rate for month"""
        if zone is None:
            from utils.config_manager import config
            zone = config.get('environmental.evaporation_zone', '4A')
        query = "SELECT evaporation_mm FROM evaporation_rates WHERE month = ? AND zone = ? AND year IS NULL"
        results = self.execute_query(query, (month, zone))
        return results[0]['evaporation_mm'] if results else 0.0

    def get_regional_rainfall_monthly(self, month: int, year: int = None) -> float:
        """Get regional rainfall for month (applies to all facilities in the area).
        Two-tier fallback: year-specific → baseline (year=NULL) → 0.
        """
        if year is None:
            query = "SELECT rainfall_mm FROM regional_rainfall_monthly WHERE month = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (month,))
        else:
            # Try year-specific first
            query = "SELECT rainfall_mm FROM regional_rainfall_monthly WHERE month = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (month, year))
            # Fallback to baseline if year-specific not found
            if not results:
                query = "SELECT rainfall_mm FROM regional_rainfall_monthly WHERE month = ? AND year IS NULL LIMIT 1"
                results = self.execute_query(query, (month,))
        return results[0]['rainfall_mm'] if results else 0.0

    def get_regional_evaporation_monthly(self, month: int, zone: str = None, year: int = None) -> float:
        """Get regional evaporation for month (applies to all facilities).
        Uses evaporation_rates table. Two-tier fallback: year-specific → baseline (year=NULL) → 0.
        """
        if zone is None:
            from utils.config_manager import config
            zone = config.get('environmental.evaporation_zone', '4A')
        if year is None:
            query = "SELECT evaporation_mm FROM evaporation_rates WHERE month = ? AND zone = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (month, zone))
        else:
            # Try year-specific first
            query = "SELECT evaporation_mm FROM evaporation_rates WHERE month = ? AND zone = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (month, zone, year))
            # Fallback to baseline if year-specific not found
            if not results:
                query = "SELECT evaporation_mm FROM evaporation_rates WHERE month = ? AND zone = ? AND year IS NULL LIMIT 1"
                results = self.execute_query(query, (month, zone))
        return results[0]['evaporation_mm'] if results else 0.0

    def get_facility_rainfall_monthly(self, facility_id: int, month: int, year: int = None) -> float:
        """Get per-facility rainfall for month (from dashboard).
        Falls back to 0 if not set in dashboard.
        """
        if year is None:
            query = "SELECT rainfall_mm FROM facility_rainfall_monthly WHERE facility_id = ? AND month = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (facility_id, month))
        else:
            query = "SELECT rainfall_mm FROM facility_rainfall_monthly WHERE facility_id = ? AND month = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (facility_id, month, year))
        return results[0]['rainfall_mm'] if results else 0.0

    def get_facility_evaporation_monthly(self, facility_id: int, month: int, year: int = None) -> float:
        """Get per-facility evaporation for month (from dashboard).
        Falls back to 0 if not set in dashboard.
        """
        if year is None:
            query = "SELECT evaporation_mm FROM facility_evaporation_monthly WHERE facility_id = ? AND month = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (facility_id, month))
        else:
            query = "SELECT evaporation_mm FROM facility_evaporation_monthly WHERE facility_id = ? AND month = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (facility_id, month, year))
        return results[0]['evaporation_mm'] if results else 0.0

    def get_facility_inflow_monthly(self, facility_id_or_code, month: int, year: int = None) -> float:
        """Get per-facility inflow for month (from dashboard).
        Falls back to 0 if not set in dashboard.
        Accepts either facility_id (int) or facility_code (str).
        """
        # Handle facility_code -> facility_id lookup
        if isinstance(facility_id_or_code, str):
            lookup_query = "SELECT facility_id FROM storage_facilities WHERE facility_code = ? LIMIT 1"
            lookup_results = self.execute_query(lookup_query, (facility_id_or_code,))
            if not lookup_results:
                return 0.0
            facility_id = lookup_results[0]['facility_id']
        else:
            facility_id = facility_id_or_code
        
        if year is None:
            query = "SELECT inflow_m3 FROM facility_inflow_monthly WHERE facility_id = ? AND month = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (facility_id, month))
        else:
            query = "SELECT inflow_m3 FROM facility_inflow_monthly WHERE facility_id = ? AND month = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (facility_id, month, year))
        return results[0]['inflow_m3'] if results else 0.0

    def get_facility_outflow_monthly(self, facility_id_or_code, month: int, year: int = None) -> float:
        """Get per-facility outflow for month (from dashboard).
        Falls back to 0 if not set in dashboard.
        Accepts either facility_id (int) or facility_code (str).
        """
        # Handle facility_code -> facility_id lookup
        if isinstance(facility_id_or_code, str):
            lookup_query = "SELECT facility_id FROM storage_facilities WHERE facility_code = ? LIMIT 1"
            lookup_results = self.execute_query(lookup_query, (facility_id_or_code,))
            if not lookup_results:
                return 0.0
            facility_id = lookup_results[0]['facility_id']
        else:
            facility_id = facility_id_or_code
        
        if year is None:
            query = "SELECT outflow_m3 FROM facility_outflow_monthly WHERE facility_id = ? AND month = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (facility_id, month))
        else:
            query = "SELECT outflow_m3 FROM facility_outflow_monthly WHERE facility_id = ? AND month = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (facility_id, month, year))
        return results[0]['outflow_m3'] if results else 0.0

    def get_facility_abstraction_monthly(self, facility_id_or_code, month: int, year: int = None) -> float:
        """Get per-facility abstraction for month (from dashboard).
        Falls back to 0 if not set in dashboard.
        Accepts either facility_id (int) or facility_code (str).
        """
        # Handle facility_code -> facility_id lookup
        if isinstance(facility_id_or_code, str):
            lookup_query = "SELECT facility_id FROM storage_facilities WHERE facility_code = ? LIMIT 1"
            lookup_results = self.execute_query(lookup_query, (facility_id_or_code,))
            if not lookup_results:
                return 0.0
            facility_id = lookup_results[0]['facility_id']
        else:
            facility_id = facility_id_or_code
        
        if year is None:
            query = "SELECT abstraction_m3 FROM facility_abstraction_monthly WHERE facility_id = ? AND month = ? AND year IS NULL LIMIT 1"
            results = self.execute_query(query, (facility_id, month))
        else:
            query = "SELECT abstraction_m3 FROM facility_abstraction_monthly WHERE facility_id = ? AND month = ? AND year = ? LIMIT 1"
            results = self.execute_query(query, (facility_id, month, year))
        return results[0]['abstraction_m3'] if results else 0.0

    def get_facility_rainfall_all_months(self, facility_id: int, year: int = None) -> Dict[int, float]:
        """Get all 12 months of rainfall for facility"""
        if year is None:
            query = "SELECT month, rainfall_mm FROM facility_rainfall_monthly WHERE facility_id = ? AND year IS NULL ORDER BY month"
            results = self.execute_query(query, (facility_id,))
        else:
            query = "SELECT month, rainfall_mm FROM facility_rainfall_monthly WHERE facility_id = ? AND year = ? ORDER BY month"
            results = self.execute_query(query, (facility_id, year))
        return {row['month']: row['rainfall_mm'] for row in results}

    def get_facility_evaporation_all_months(self, facility_id: int, year: int = None) -> Dict[int, float]:
        """Get all 12 months of evaporation for facility"""
        if year is None:
            query = "SELECT month, evaporation_mm FROM facility_evaporation_monthly WHERE facility_id = ? AND year IS NULL ORDER BY month"
            results = self.execute_query(query, (facility_id,))
        else:
            query = "SELECT month, evaporation_mm FROM facility_evaporation_monthly WHERE facility_id = ? AND year = ? ORDER BY month"
            results = self.execute_query(query, (facility_id, year))
        return {row['month']: row['evaporation_mm'] for row in results}

    def get_facility_inflow_all_months(self, facility_id: int, year: int = None) -> Dict[int, float]:
        """Get all 12 months of inflow for facility"""
        if year is None:
            query = "SELECT month, inflow_m3 FROM facility_inflow_monthly WHERE facility_id = ? AND year IS NULL ORDER BY month"
            results = self.execute_query(query, (facility_id,))
        else:
            query = "SELECT month, inflow_m3 FROM facility_inflow_monthly WHERE facility_id = ? AND year = ? ORDER BY month"
            results = self.execute_query(query, (facility_id, year))
        return {row['month']: row['inflow_m3'] for row in results}

    def get_facility_outflow_all_months(self, facility_id: int, year: int = None) -> Dict[int, float]:
        """Get all 12 months of outflow for facility"""
        if year is None:
            query = "SELECT month, outflow_m3 FROM facility_outflow_monthly WHERE facility_id = ? AND year IS NULL ORDER BY month"
            results = self.execute_query(query, (facility_id,))
        else:
            query = "SELECT month, outflow_m3 FROM facility_outflow_monthly WHERE facility_id = ? AND year = ? ORDER BY month"
            results = self.execute_query(query, (facility_id, year))
        return {row['month']: row['outflow_m3'] for row in results}

    def get_facility_abstraction_all_months(self, facility_id: int, year: int = None) -> Dict[int, float]:
        """Get all 12 months of abstraction for facility"""
        if year is None:
            query = "SELECT month, abstraction_m3 FROM facility_abstraction_monthly WHERE facility_id = ? AND year IS NULL ORDER BY month"
            results = self.execute_query(query, (facility_id,))
        else:
            query = "SELECT month, abstraction_m3 FROM facility_abstraction_monthly WHERE facility_id = ? AND year = ? ORDER BY month"
            results = self.execute_query(query, (facility_id, year))
        return {row['month']: row['abstraction_m3'] for row in results}

    def get_regional_rainfall_all_months(self, year: int = None) -> Dict[int, float]:
        """Get all 12 months of regional rainfall"""
        if year is None:
            query = "SELECT month, rainfall_mm FROM regional_rainfall_monthly WHERE year IS NULL ORDER BY month"
            results = self.execute_query(query)
        else:
            query = "SELECT month, rainfall_mm FROM regional_rainfall_monthly WHERE year = ? ORDER BY month"
            results = self.execute_query(query, (year,))
        return {row['month']: row['rainfall_mm'] for row in results}

    def get_regional_evaporation_all_months(self, zone: str = None, year: int = None) -> Dict[int, float]:
        """Get all 12 months of regional evaporation"""
        if zone is None:
            from utils.config_manager import config
            zone = config.get('environmental.evaporation_zone', '4A')
        if year is None:
            query = "SELECT month, evaporation_mm FROM evaporation_rates WHERE zone = ? AND year IS NULL ORDER BY month"
            results = self.execute_query(query, (zone,))
        else:
            query = "SELECT month, evaporation_mm FROM evaporation_rates WHERE zone = ? AND year = ? ORDER BY month"
            results = self.execute_query(query, (zone, year))
        return {row['month']: row['evaporation_mm'] for row in results}

    def set_facility_rainfall_monthly(self, facility_id: int, month: int, rainfall_mm: float, year: int = None, user: str = 'dashboard') -> int:
        """Set per-facility rainfall for a month"""
        query = """
            INSERT OR REPLACE INTO facility_rainfall_monthly (facility_id, month, year, rainfall_mm, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute_update(query, (facility_id, month, year, rainfall_mm, user))

    def set_facility_evaporation_monthly(self, facility_id: int, month: int, evaporation_mm: float, year: int = None, user: str = 'dashboard') -> int:
        """Set per-facility evaporation for a month"""
        query = """
            INSERT OR REPLACE INTO facility_evaporation_monthly (facility_id, month, year, evaporation_mm, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute_update(query, (facility_id, month, year, evaporation_mm, user))

    def set_facility_inflow_monthly(self, facility_id: int, month: int, inflow_m3: float, year: int = None, user: str = 'dashboard') -> int:
        """Set per-facility inflow for a month"""
        # Auto-capture current year if not provided for historical tracking
        if year is None:
            from datetime import datetime
            year = datetime.now().year
        query = """
            INSERT OR REPLACE INTO facility_inflow_monthly (facility_id, month, year, inflow_m3, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute_update(query, (facility_id, month, year, inflow_m3, user))

    def set_facility_outflow_monthly(self, facility_id: int, month: int, outflow_m3: float, year: int = None, user: str = 'dashboard') -> int:
        """Set per-facility outflow for a month"""
        # Auto-capture current year if not provided for historical tracking
        if year is None:
            from datetime import datetime
            year = datetime.now().year
        query = """
            INSERT OR REPLACE INTO facility_outflow_monthly (facility_id, month, year, outflow_m3, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute_update(query, (facility_id, month, year, outflow_m3, user))

    def set_facility_abstraction_monthly(self, facility_id: int, month: int, abstraction_m3: float, year: int = None, user: str = 'dashboard') -> int:
        """Set per-facility abstraction for a month"""
        # Auto-capture current year if not provided for historical tracking
        if year is None:
            from datetime import datetime
            year = datetime.now().year
        query = """
            INSERT OR REPLACE INTO facility_abstraction_monthly (facility_id, month, year, abstraction_m3, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute_update(query, (facility_id, month, year, abstraction_m3, user))

    def set_regional_rainfall_monthly(self, month: int, rainfall_mm: float, year: int = None, user: str = 'dashboard') -> int:
        """Set regional rainfall for a month (applies to all facilities)"""
        query = """
            INSERT OR REPLACE INTO regional_rainfall_monthly (month, year, rainfall_mm, data_source, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        return self.execute_update(query, (month, year, rainfall_mm, user))

    def set_regional_evaporation_monthly(self, month: int, evaporation_mm: float, zone: str = None, year: int = None, user: str = 'dashboard') -> int:
        """Set regional evaporation for a month (applies to all facilities)"""
        if zone is None:
            from utils.config_manager import config
            zone = config.get('environmental.evaporation_zone', '4A')
        query = """
            INSERT OR REPLACE INTO evaporation_rates (month, zone, year, evaporation_mm, notes)
            VALUES (?, ?, ?, ?, ?)
        """
        notes = f"Set via dashboard by {user}"
        return self.execute_update(query, (month, zone, year, evaporation_mm, notes))

    def delete_facility_inflow(self, facility_id: int, month: int, year: int = None) -> int:
        """Delete facility inflow entry for a month"""
        if year is None:
            query = "DELETE FROM facility_inflow_monthly WHERE facility_id = ? AND month = ? AND year IS NULL"
            return self.execute_update(query, (facility_id, month))
        else:
            query = "DELETE FROM facility_inflow_monthly WHERE facility_id = ? AND month = ? AND year = ?"
            return self.execute_update(query, (facility_id, month, year))

    def delete_facility_outflow(self, facility_id: int, month: int, year: int = None) -> int:
        """Delete facility outflow entry for a month"""
        if year is None:
            query = "DELETE FROM facility_outflow_monthly WHERE facility_id = ? AND month = ? AND year IS NULL"
            return self.execute_update(query, (facility_id, month))
        else:
            query = "DELETE FROM facility_outflow_monthly WHERE facility_id = ? AND month = ? AND year = ?"
            return self.execute_update(query, (facility_id, month, year))

    def delete_facility_abstraction(self, facility_id: int, month: int, year: int = None) -> int:
        """Delete facility abstraction entry for a month"""
        if year is None:
            query = "DELETE FROM facility_abstraction_monthly WHERE facility_id = ? AND month = ? AND year IS NULL"
            return self.execute_update(query, (facility_id, month))
        else:
            query = "DELETE FROM facility_abstraction_monthly WHERE facility_id = ? AND month = ? AND year = ?"
            return self.execute_update(query, (facility_id, month, year))

    def list_facility_flows(self, facility_id: int = None, month: int = None, year: int = None) -> List[Dict]:
        """List facility flows with optional filtering by facility/month/year"""
        query = """
            SELECT 
                f.facility_id, f.facility_code, f.facility_name,
                COALESCE(i.month, o.month) as month,
                COALESCE(i.year, o.year) as year,
                COALESCE(i.inflow_m3, 0) as inflow_m3,
                COALESCE(o.outflow_m3, 0) as outflow_m3,
                (COALESCE(i.inflow_m3, 0) - COALESCE(o.outflow_m3, 0)) as net_flow_m3
            FROM storage_facilities f
            LEFT JOIN facility_inflow_monthly i ON f.facility_id = i.facility_id
            LEFT JOIN facility_outflow_monthly o ON f.facility_id = o.facility_id
            WHERE 1=1
        """
        params = []
        
        if facility_id:
            query += " AND f.facility_id = ?"
            params.append(facility_id)
        if month:
            query += " AND COALESCE(i.month, o.month) = ?"
            params.append(month)
        if year:
            query += " AND COALESCE(i.year, o.year) = ?"
            params.append(year)
        
        query += " ORDER BY f.facility_code, COALESCE(i.month, o.month)"
        
        try:
            return self.execute_query(query, tuple(params) if params else ())
        except Exception as e:
            logger.error(f"Error listing facility flows: {e}")
            return []

    def auto_generate_facility_flows_from_balance(self, facility_id: int, calculation_date, closing_volume: float, 
                                                   opening_volume: float, rainfall_volume: float, 
                                                   evaporation_volume: float, seepage_volume: float) -> Dict[str, float]:
        """Auto-generate inflow/outflow/abstraction from calculated balance changes.
        
        This method calculates the implied flows based on observed volume changes
        and regional environmental factors (rainfall, evap, seepage).
        
        Formula: closing = opening + inflows - outflows - abstraction
        Therefore: inflows = (closing - opening) + outflows + abstraction + evap + seepage - rainfall
        
        Returns dict with inflow_m3, outflow_m3, abstraction_m3
        """
        from datetime import datetime
        
        # Calculate net change
        net_change = closing_volume - opening_volume
        
        # Environmental impacts already accounted for
        environmental_gain = rainfall_volume
        environmental_loss = evaporation_volume + seepage_volume
        
        # Estimate flows (simplified: assume no abstraction, balance is inflow - outflow)
        # net_change = inflow - outflow - abstraction + rainfall - evap - seepage
        # If net_change > 0 after accounting for environmental: implies net inflow
        # If net_change < 0: implies net outflow
        
        adjusted_change = net_change + environmental_loss - environmental_gain
        
        if adjusted_change > 0:
            # Net positive: assume inflow, minimal outflow
            inflow_m3 = adjusted_change
            outflow_m3 = 0.0
            abstraction_m3 = 0.0
        else:
            # Net negative: assume outflow or abstraction
            inflow_m3 = 0.0
            outflow_m3 = abs(adjusted_change) * 0.7  # 70% as outflow
            abstraction_m3 = abs(adjusted_change) * 0.3  # 30% as abstraction
        
        # Store in DB with current year and month
        month = calculation_date.month
        year = calculation_date.year
        
        self.set_facility_inflow_monthly(facility_id, month, inflow_m3, year, user='auto-generated')
        self.set_facility_outflow_monthly(facility_id, month, outflow_m3, year, user='auto-generated')
        self.set_facility_abstraction_monthly(facility_id, month, abstraction_m3, year, user='auto-generated')
        
        return {
            'inflow_m3': inflow_m3,
            'outflow_m3': outflow_m3,
            'abstraction_m3': abstraction_m3,
            'method': 'auto-generated from balance'
        }

    def get_constant(self, key: str) -> Optional[float]:
        """Get system constant value"""
        query = "SELECT constant_value FROM system_constants WHERE constant_key = ?"
        results = self.execute_query(query, (key,))
        return results[0]['constant_value'] if results else None
    
    def get_all_constants(self) -> Dict[str, float]:
        """Get all system constants as dictionary"""
        results = self.execute_query("SELECT constant_key, constant_value FROM system_constants")
        return {row['constant_key']: row['constant_value'] for row in results}

    def update_constant(self, key: str, value: float, user: str = 'system') -> int:
        """Update a system constant value and log change"""
        old_val = self.get_constant(key)
        rows = self.execute_update(
            "UPDATE system_constants SET constant_value = ?, updated_at = CURRENT_TIMESTAMP WHERE constant_key = ?",
            (value, key)
        )
        if rows:
            self.log_change('system_constants', 0, 'update',
                            old_values={key: old_val}, new_values={key: value}, user=user)
        return rows
    
    # ==================== AUDIT & LOGGING ====================
    
    def log_change(self, table_name: str, record_id: int, action: str,
                   old_values: Dict = None, new_values: Dict = None,
                   user: str = 'system') -> int:
        """Log data change to audit trail"""
        query = """
            INSERT INTO audit_log (
                table_name, record_id, action, old_values, new_values, changed_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            table_name, record_id, action,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            user
        )
        return self.execute_insert(query, params)
    
    # ==================== STATISTICS & SUMMARY ====================
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics (optimized)"""
        stats = {}
        
        # Fetch once, reuse (performance optimization)
        sources = self.get_water_sources(active_only=True)
        # Only count ABSTRACTION and DUAL_PURPOSE sources for dashboard
        sources_counted = [s for s in sources if s.get('source_purpose','ABSTRACTION') in ('ABSTRACTION','DUAL_PURPOSE')]
        facilities = self.get_storage_facilities(active_only=True)

        stats['total_sources'] = len(sources_counted)
        stats['total_facilities'] = len(facilities)

        # Calculate totals from fetched data (no additional queries)
        stats['total_capacity'] = sum(f['total_capacity'] for f in facilities)
        stats['total_current_volume'] = sum(f.get('current_volume', 0) for f in facilities)
        stats['total_utilization_percent'] = (
            (stats['total_current_volume'] / stats['total_capacity'] * 100)
            if stats['total_capacity'] > 0 else 0
        )

        # Latest calculation
        latest_calc = self.execute_query(
            "SELECT * FROM calculations ORDER BY calc_date DESC LIMIT 1"
        )
        if latest_calc:
            stats['latest_calculation'] = latest_calc[0]

        return stats

    def _ensure_extended_calculation_columns(self):
        """Non-destructive migration: add extended calculation columns if missing."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(calculations)")
            existing = {row[1] for row in cur.fetchall()}
            # Map of column name to ALTER TABLE statement
            new_columns = {
                'surface_water_inflow': "ALTER TABLE calculations ADD COLUMN surface_water_inflow REAL DEFAULT 0",
                'groundwater_inflow': "ALTER TABLE calculations ADD COLUMN groundwater_inflow REAL DEFAULT 0",
                'ore_moisture_inflow': "ALTER TABLE calculations ADD COLUMN ore_moisture_inflow REAL DEFAULT 0",
                'tsf_return_inflow': "ALTER TABLE calculations ADD COLUMN tsf_return_inflow REAL DEFAULT 0",
                'plant_returns_inflow': "ALTER TABLE calculations ADD COLUMN plant_returns_inflow REAL DEFAULT 0",
                'returns_to_pit_inflow': "ALTER TABLE calculations ADD COLUMN returns_to_pit_inflow REAL DEFAULT 0",
                'seepage_gain_inflow': "ALTER TABLE calculations ADD COLUMN seepage_gain_inflow REAL DEFAULT 0",
                'plant_consumption_gross': "ALTER TABLE calculations ADD COLUMN plant_consumption_gross REAL DEFAULT 0",
                'plant_consumption_net': "ALTER TABLE calculations ADD COLUMN plant_consumption_net REAL DEFAULT 0",
                'tailings_retention_loss': "ALTER TABLE calculations ADD COLUMN tailings_retention_loss REAL DEFAULT 0",
                'closure_error_m3': "ALTER TABLE calculations ADD COLUMN closure_error_m3 REAL DEFAULT 0",
                'closure_error_percent': "ALTER TABLE calculations ADD COLUMN closure_error_percent REAL DEFAULT 0",
                'balance_status': "ALTER TABLE calculations ADD COLUMN balance_status TEXT",
                'calc_quality_flag': "ALTER TABLE calculations ADD COLUMN calc_quality_flag TEXT DEFAULT 'good'",
                'estimated_component_count': "ALTER TABLE calculations ADD COLUMN estimated_component_count INTEGER DEFAULT 0",
                'estimated_volume_fraction': "ALTER TABLE calculations ADD COLUMN estimated_volume_fraction REAL DEFAULT 0"
            }
            for col, stmt in new_columns.items():
                if col not in existing:
                    cur.execute(stmt)
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            # Silent fail; will be retried on next startup
        finally:
            conn.close()

    def _ensure_storage_facility_columns(self):
        """Non-destructive migration: add newer storage_facilities columns if missing."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(storage_facilities)")
            existing = {row[1] for row in cur.fetchall()}
            migrations = {
                'evap_active': "ALTER TABLE storage_facilities ADD COLUMN evap_active BOOLEAN DEFAULT 1",
                'is_lined': "ALTER TABLE storage_facilities ADD COLUMN is_lined BOOLEAN DEFAULT 0",
                'volume_calc_date': "ALTER TABLE storage_facilities ADD COLUMN volume_calc_date DATE",
            }
            for col, stmt in migrations.items():
                if col not in existing:
                    cur.execute(stmt)
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            # Silent fail; will retry on next startup
        finally:
            conn.close()

    def _ensure_all_constants(self):
        """Ensure required system constants exist (idempotent)."""
        # Get all existing constant keys in one query
        existing_keys = set()
        try:
            rows = self.execute_query("SELECT constant_key FROM system_constants")
            existing_keys = {r['constant_key'] for r in rows}
        except:
            return  # Table doesn't exist yet
        
        # Define all required constants
        required_constants = [
            # Core calculation constants used by the app (kept stable across builds)
            ('tailings_moisture_pct', 20.0, '%', 'Optimization',
             'Tailings retained moisture percent used in retention loss', 1, 0.0, 100.0),
            ('dust_suppression_rate', 0.2, 'm³/t', 'Plant',
             'Dust suppression water requirement per tonne of ore processed', 1, 0.01, 0.50),
            ('ore_density', 2.7, 't/m³', 'Plant',
             'Bulk density of run-of-mine ore used for moisture volume conversion', 1, 2.4, 3.2),
            ('ore_moisture_percent', 5.0, 'percent', 'Plant',
             'Average moisture percent of ore feed (used to derive water inflow from wet ore)', 1, 1.0, 8.0),
            ('lined_seepage_rate_pct', 0.1, '%', 'Seepage',
             'Monthly seepage loss rate for lined facilities', 1, 0.0, 1.0),
            ('unlined_seepage_rate_pct', 0.5, '%', 'Seepage',
             'Monthly seepage loss rate for unlined facilities', 1, 0.0, 2.0),
            # Legacy constant retained for backwards compatibility; may be unused
            ('EVAP_PAN_COEFF', 0.70, 'factor', 'Evaporation',
             'Pan coefficient to scale monthly S-pan evaporation to site conditions', 1, 0.3, 1.2),
        ]
        
        # Insert only missing constants
        for key, val, unit, cat, desc, editable, min_v, max_v in required_constants:
            if key not in existing_keys:
                try:
                    self.execute_insert(
                        """
                        INSERT INTO system_constants (constant_key, constant_value, unit, category, description, editable, min_value, max_value)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (key, val, unit, cat, desc, editable, min_v, max_v)
                    )
                except:
                    pass  # Constant might have been added by another process
    
    # Deprecated methods: ensure_evap_pan_coefficient, ensure_default_rainfall_constant, ensure_ore_processing_constants
    # These methods are no longer called. Constants not used by the calculator are auto-removed at startup.
    
    def _auto_remove_constants_not_used_in_calculator(self) -> int:
        """
        Remove constants not referenced by the latest balance calculation engine
        (restricted to utils/water_balance_calculator.py and utils/balance_check_engine.py).
        Preserves Optimization-category constants.
        """
        # Fetch keys with categories
        rows = self.execute_query("SELECT constant_key, category FROM system_constants")
        if not rows:
            return 0
        keys = [r['constant_key'] for r in rows]
        categories = {r['constant_key']: (r.get('category') or '') for r in rows}

        # Compute usage by scanning calculator files only
        base_dir = Path(__file__).parent.parent.parent
        calc_files = [
            base_dir / 'src' / 'utils' / 'water_balance_calculator.py',
            base_dir / 'src' / 'utils' / 'balance_check_engine.py'
        ]
        usage = {k: 0 for k in keys}
        for path in calc_files:
            try:
                if not path.exists():
                    continue
                text = path.read_text(encoding='utf-8', errors='ignore')
                for k in keys:
                    cnt = text.count(k)
                    if cnt:
                        usage[k] += cnt
            except Exception:
                continue

        # Build removal list: zero usage in calculator, and not Optimization category
        # Protect required categories and specific keys from deletion
        protected_cats = {'optimization', 'plant', 'seepage'}
        protected_keys = {
            'tailings_moisture_pct',
            'dust_suppression_rate',
            'ore_density',
            'ore_moisture_percent',
            'lined_seepage_rate_pct',
            'unlined_seepage_rate_pct',
        }
        removable = [
            k for k in keys
            if (usage.get(k, 0) == 0)
            and (categories.get(k, '').lower() not in protected_cats)
            and (k not in protected_keys)
        ]
        if not removable:
            return 0

        deleted = 0
        for k in removable:
            try:
                old_val = self.get_constant(k)
                rows = self.execute_update("DELETE FROM system_constants WHERE constant_key = ?", (k,))
                if rows:
                    self.log_change('system_constants', 0, 'delete', old_values={k: old_val}, user='system')
                    deleted += 1
            except Exception:
                continue

        # Log summary
        try:
            from utils.app_logger import logger
            if deleted > 0:
                preview = ", ".join(removable[:5])
                logger.info(f"♻️  Cleaned up {deleted}/{len(keys)} unused constants: {preview}{'...' if len(removable) > 5 else ''}")
            else:
                logger.debug(f"All {len(keys)} system constants are in use by calculator")
        except Exception:
            pass
        return deleted

    def ensure_ore_processing_constants(self):
        """Ensure ore processing related constants exist (monthly ore, moisture %, density)."""
        specs = [
            ('ore_moisture_percent', 3.4, 'percent', 'Plant', 'Ore feed moisture percent', 1, 1.0, 8.0),
            ('ore_density', 2.7, 't/m³', 'Plant', 'Bulk ore density for moisture volume conversion', 1, 2.4, 3.2),
        ]
        for key, val, unit, cat, desc, editable, min_v, max_v in specs:
            existing = self.execute_query("SELECT constant_key FROM system_constants WHERE constant_key = ?", (key,))
            if existing:
                continue
            self.execute_insert(
                """
                INSERT INTO system_constants (constant_key, constant_value, unit, category, description, editable, min_value, max_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (key, val, unit, cat, desc, editable, min_v, max_v)
            )
        return True

    def _derive_calc_quality(self, calc_date: str) -> Tuple[str, int, float]:
        """Assess measurement quality for a calculation date.
        Returns (quality_flag, estimated_component_count, estimated_volume_fraction)."""
        # Fetch measurements for date
        rows = self.execute_query(
            """
            SELECT measured, quality_flag, COALESCE(volume,0) as volume
            FROM measurements WHERE measurement_date = ?
            """,
            (calc_date,)
        )
        if not rows:
            return ('no_data', 0, 0.0)
        total_vol = sum(r['volume'] for r in rows)
        estim_keys = {'estimated','interpolated','historical_average','default'}
        estimated_rows = [r for r in rows if (not r['measured']) or (r['quality_flag'] in estim_keys)]
        est_count = len(estimated_rows)
        est_vol = sum(r['volume'] for r in estimated_rows)
        fraction = (est_vol / total_vol) if total_vol > 0 else 0.0
        if est_count == 0:
            flag = 'good'
        elif fraction > 0.7:
            flag = 'low_confidence'
        elif fraction > 0.3:
            flag = 'mixed'
        else:
            flag = 'mostly_measured'
        return (flag, est_count, fraction)

    def backfill_extended_calculation_columns(self, max_rows: int = None) -> int:
        """Recompute and populate extended calculation columns for existing rows.
        Args:
            max_rows: Optional limit on number of rows to backfill (most recent first).
        Returns:
            Number of rows updated.
        """
        # Lazy import to avoid circular dependency at module load
        from utils.water_balance_calculator import WaterBalanceCalculator
        calc_engine = WaterBalanceCalculator()
        conn = self.get_connection()
        updated = 0
        try:
            cur = conn.cursor()
            order_clause = "ORDER BY calc_date DESC"
            limit_clause = f"LIMIT {int(max_rows)}" if max_rows else ""
            cur.execute(f"SELECT calc_id, calc_date, calc_type FROM calculations {order_clause} {limit_clause}")
            rows = cur.fetchall()
            for r in rows:
                calc_id = r[0]
                calc_date_str = r[1]
                # Parse date
                try:
                    from datetime import datetime
                    calc_date = datetime.strptime(calc_date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                balance = calc_engine.calculate_water_balance(calc_date)
                infl = balance['inflows']
                out = balance['outflows']
                closure_err_m3 = balance['closure_error_m3']
                closure_err_pct = balance['closure_error_percent']
                status = balance['balance_status']
                # Prepare update; only update extended fields
                update_sql = """
                    UPDATE calculations SET
                        surface_water_inflow = ?, groundwater_inflow = ?, ore_moisture_inflow = ?,
                        tsf_return_inflow = ?, plant_returns_inflow = ?, returns_to_pit_inflow = ?,
                        seepage_gain_inflow = ?, plant_consumption_gross = ?, plant_consumption_net = ?,
                        tailings_retention_loss = ?, closure_error_m3 = ?, closure_error_percent = ?,
                        balance_status = ?, calc_quality_flag = ?, estimated_component_count = ?,
                        estimated_volume_fraction = ?
                    WHERE calc_id = ?
                """
                params = (
                    infl.get('surface_water', 0), infl.get('groundwater', 0), infl.get('ore_moisture', 0),
                    infl.get('tsf_return', 0), infl.get('plant_returns', 0), infl.get('returns_to_pit', 0),
                    infl.get('seepage_gain', 0), out.get('plant_consumption_gross', 0), out.get('plant_consumption_net', 0),
                    out.get('tailings_retention', 0), closure_err_m3, closure_err_pct,
                    status, 'good', 0, 0.0, calc_id
                )
                cur.execute(update_sql, params)
                updated += 1
            conn.commit()
            return updated
        except Exception:
            conn.rollback()
            return updated
        finally:
            conn.close()

    # ==================== CACHE MANAGEMENT ====================
    
    def _invalidate_sources_cache(self):
        """Invalidate sources cache after add/update/delete"""
        self._sources_cache = None
    
    def _invalidate_facilities_cache(self):
        """Invalidate facilities cache after add/update/delete"""
        self._facilities_cache = None
    
    def invalidate_all_caches(self):
        """Clear all caches (call after bulk operations)"""
        self._sources_cache = None
        self._facilities_cache = None
    
    def preload_caches(self):
        """Preload sources and facilities caches for optimal startup performance
        
        Call this early in application startup to avoid repeated queries
        when multiple modules initialize.
        """
        if self._sources_cache is None:
            self.get_water_sources(active_only=False, use_cache=True)
        if self._facilities_cache is None:
            self.get_storage_facilities(active_only=False, use_cache=True)
    
    # ==================== EVENT SYSTEM ====================
    def register_listener(self, listener):
        """Register a callback(listener(event_type, payload))."""
        if callable(listener) and listener not in self._listeners:
            self._listeners.append(listener)

    def unregister_listener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify(self, event_type: str, payload: Dict):
        """Notify listeners of an event (errors are swallowed)."""
        for fn in list(self._listeners):
            try:
                fn(event_type, payload)
            except Exception:
                continue

    # ==================== TAILINGS MOISTURE ====================
    
    def get_tailings_moisture_monthly(self, month: int, year: int = 2025) -> Optional[float]:
        """Get tailings moisture percentage for a specific month.
        Returns None if no entry exists (caller should use fallback to 0).
        """
        try:
            result = self.execute_query(
                "SELECT tailings_moisture_pct FROM tailings_moisture_monthly WHERE month = ? AND year = ?",
                (month, year)
            )
            return float(result[0]['tailings_moisture_pct']) if result else None
        except Exception as e:
            from utils.app_logger import logger
            logger.error(f"Error getting tailings moisture: {e}")
            return None
    
    def set_tailings_moisture_monthly(self, month: int, year: int = 2025, 
                                     tailings_moisture_pct: float = None, 
                                     notes: str = None) -> bool:
        """Set or update tailings moisture percentage for a month."""
        try:
            self.execute_update(
                """INSERT OR REPLACE INTO tailings_moisture_monthly 
                   (month, year, tailings_moisture_pct, notes, updated_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (month, year, tailings_moisture_pct, notes)
            )
            from utils.app_logger import logger
            logger.info(f"Set tailings moisture for {month}/{year}: {tailings_moisture_pct}%")
            return True
        except Exception as e:
            from utils.app_logger import logger
            logger.error(f"Error setting tailings moisture: {e}")
            return False
    
    def get_tailings_moisture_all_months(self, year: int = 2025) -> Dict[int, float]:
        """Get tailings moisture for all months in a year.
        Returns dict: {month: moisture_pct}
        """
        try:
            results = self.execute_query(
                "SELECT month, tailings_moisture_pct FROM tailings_moisture_monthly WHERE year = ? ORDER BY month",
                (year,)
            )
            return {r['month']: float(r['tailings_moisture_pct']) for r in results}
        except Exception as e:
            from utils.app_logger import logger
            logger.error(f"Error getting tailings moisture for year: {e}")
            return {}

    # NOTE: Seepage gain/loss calculation is now automatic based on facility properties
    # (aquifer_gain_rate_pct, is_lined flag) and does not require manual database entries.
    # Methods get_seepage_gain_monthly(), set_seepage_gain_monthly(), and
    # get_seepage_gain_all_months() have been removed as part of facility-level seepage refactoring.


# Global database instance
db = DatabaseManager()
