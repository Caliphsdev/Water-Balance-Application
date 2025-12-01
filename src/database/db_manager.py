"""
Database Manager
Handles all database operations with connection pooling and error handling
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import json
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config


class DatabaseManager:
    """Database operations manager with connection handling"""
    
    # Class-level flag to avoid repeated constant checks across instances
    _constants_checked = False
    
    def __init__(self, db_path: str = None):
        """Initialize database manager"""
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            db_path = base_dir / config.get('database.path', 'data/water_balance.db')
        
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
            schema = DatabaseSchema(str(self.db_path))
            schema.create_database()
        # Ensure scenarios tables exist
        self._ensure_scenario_tables()
        # Ensure extended calculation columns (non-destructive migration)
        self._ensure_extended_calculation_columns()
        # Ensure new environmental constants (only check once per process)
        if not DatabaseManager._constants_checked:
            try:
                self._ensure_all_constants()
                DatabaseManager._constants_checked = True
            except Exception:
                pass  # Non-critical
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allow dict-like access
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results as list of dicts"""
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
            logger.performance(f"DB query ({query_preview}..., {len(result)} rows)", elapsed)
            
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
            logger.performance(f"DB update ({query_preview}..., {rowcount} rows affected)", elapsed)
            
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
                total_capacity, working_capacity, dead_storage, surface_area,
                pump_start_level, pump_stop_level, high_level_alarm, low_level_alarm,
                current_volume, minimum_operating_level, maximum_operating_level,
                description, purpose, active, commissioned_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            data.get('working_capacity'), data.get('dead_storage'),
            data.get('surface_area'), pump_start, pump_stop,
            data.get('high_level_alarm', 90.0), data.get('low_level_alarm', 10.0),
            data.get('current_volume', 0),
            data.get('minimum_operating_level', 0),
            data.get('maximum_operating_level', 100),
            data.get('description'),
            data.get('purpose'), data.get('active', 1), data.get('commissioned_date')
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
                high_level_alarm = ?, low_level_alarm = ?,
                minimum_operating_level = ?, maximum_operating_level = ?,
                description = ?, active = ?,
                updated_at = CURRENT_TIMESTAMP
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
            data.get('high_level_alarm', 90.0), data.get('low_level_alarm', 10.0),
            data.get('minimum_operating_level', 0), data.get('maximum_operating_level', 100),
            data.get('description'), data.get('active', 1), facility_id
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
    
    def get_evaporation_rate(self, month: int, zone: str = '4A') -> float:
        """Get evaporation rate for month"""
        query = "SELECT evaporation_mm FROM evaporation_rates WHERE month = ? AND zone = ? AND year IS NULL"
        results = self.execute_query(query, (month, zone))
        return results[0]['evaporation_mm'] if results else 0.0
    
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

    # ==================== SCENARIOS ====================
    def _ensure_scenario_tables(self):
        """Create scenario tables if they do not exist"""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scenario_constants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id INTEGER NOT NULL,
                    constant_key TEXT NOT NULL,
                    constant_value REAL NOT NULL,
                    FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id) ON DELETE CASCADE
                )
            """)
            conn.commit()
        finally:
            conn.close()

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

    def _ensure_all_constants(self):
        """Batch-check and create missing constants (called once per process)"""
        # Get all existing constant keys in one query
        existing_keys = set()
        try:
            rows = self.execute_query("SELECT constant_key FROM system_constants")
            existing_keys = {r['constant_key'] for r in rows}
        except:
            return  # Table doesn't exist yet
        
        # Define all required constants
        required_constants = [
            ('EVAP_PAN_COEFF', 0.70, 'factor', 'Evaporation', 
             'Pan coefficient to scale monthly S-pan evaporation to site conditions', 1, 0.3, 1.2),
            ('DEFAULT_MONTHLY_RAINFALL_MM', 60.0, 'mm', 'Evaporation', 
             'Fallback monthly rainfall (mm) used when no rainfall measurements present for period', 1, 0.0, 500.0),
            ('monthly_ore_processing', 350000.0, 't/month', 'Plant', 
             'Default monthly ore processed tonnage used when no entry provided', 1, 100000.0, 1000000.0),
            ('ore_moisture_percent', 3.4, 'percent', 'Plant', 
             'Average moisture percent of ore feed (used to derive water inflow from wet ore)', 1, 1.0, 8.0),
            ('ore_density', 2.7, 't/m³', 'Plant', 
             'Bulk density of run-of-mine ore used for moisture volume conversion', 1, 2.4, 3.2),
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
    
    def ensure_evap_pan_coefficient(self):
        """Ensure EVAP_PAN_COEFF constant exists with default value and metadata."""
        existing = self.execute_query("SELECT constant_key FROM system_constants WHERE constant_key = 'EVAP_PAN_COEFF'")
        if existing:
            return False
        self.execute_insert(
            """
            INSERT INTO system_constants (constant_key, constant_value, unit, category, description, editable, min_value, max_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('EVAP_PAN_COEFF', 0.70, 'factor', 'Evaporation', 'Pan coefficient to scale monthly S-pan evaporation to site conditions', 1, 0.3, 1.2)
        )
        return True

    def ensure_default_rainfall_constant(self):
        """Ensure DEFAULT_MONTHLY_RAINFALL_MM constant exists (fallback rainfall depth in mm when no measurement rows)."""
        existing = self.execute_query("SELECT constant_key FROM system_constants WHERE constant_key = 'DEFAULT_MONTHLY_RAINFALL_MM'")
        if existing:
            return False
        self.execute_insert(
            """
            INSERT INTO system_constants (constant_key, constant_value, unit, category, description, editable, min_value, max_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('DEFAULT_MONTHLY_RAINFALL_MM', 0.0, 'mm', 'Evaporation', 'Fallback monthly rainfall (mm) used when no rainfall measurements present for period', 1, 0.0, 500.0)
        )
        return True

    def ensure_ore_processing_constants(self):
        """Ensure ore processing related constants exist (monthly ore, moisture %, density)."""
        specs = [
            ('monthly_ore_processing', 350000.0, 't/month', 'Plant', 'Default monthly ore processed tonnage', 1, 100000.0, 1000000.0),
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

    def create_scenario(self, name: str, description: str = '') -> int:
        """Create scenario capturing current constants snapshot"""
        scenario_id = self.execute_insert(
            "INSERT INTO scenarios (name, description) VALUES (?, ?)",
            (name, description)
        )
        constants = self.execute_query("SELECT constant_key, constant_value FROM system_constants")
        for row in constants:
            self.execute_insert(
                "INSERT INTO scenario_constants (scenario_id, constant_key, constant_value) VALUES (?, ?, ?)",
                (scenario_id, row['constant_key'], row['constant_value'])
            )
        self.log_change('scenarios', scenario_id, 'create', new_values={'name': name})
        return scenario_id

    def list_scenarios(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM scenarios ORDER BY created_at DESC")

    def get_scenario_constants(self, scenario_id: int) -> Dict[str, float]:
        rows = self.execute_query(
            "SELECT constant_key, constant_value FROM scenario_constants WHERE scenario_id = ?",
            (scenario_id,)
        )
        return {r['constant_key']: r['constant_value'] for r in rows}

    def delete_scenario(self, scenario_id: int) -> int:
        rows = self.execute_update("DELETE FROM scenarios WHERE scenario_id = ?", (scenario_id,))
        if rows:
            self.log_change('scenarios', scenario_id, 'delete', old_values={'scenario_id': scenario_id})
        return rows

    def rename_scenario(self, scenario_id: int, new_name: str, new_description: str = '') -> int:
        rows = self.execute_update(
            "UPDATE scenarios SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE scenario_id = ?",
            (new_name, new_description, scenario_id)
        )
        if rows:
            self.log_change('scenarios', scenario_id, 'update', new_values={'name': new_name})
        return rows

    def get_scenario_diff(self, scenario_id: int) -> List[Dict[str, Any]]:
        """Return list of differences between base constants and scenario constants."""
        base = self.execute_query("SELECT constant_key, constant_value FROM system_constants")
        scen = self.execute_query(
            "SELECT constant_key, constant_value FROM scenario_constants WHERE scenario_id = ?",
            (scenario_id,)
        )
        base_map = {r['constant_key']: r['constant_value'] for r in base}
        scen_map = {r['constant_key']: r['constant_value'] for r in scen}
        diffs = []
        for key, bval in base_map.items():
            sval = scen_map.get(key, bval)
            if sval != bval:
                diffs.append({
                    'constant_key': key,
                    'base_value': bval,
                    'scenario_value': sval,
                    'delta': sval - bval,
                    'percent_change': ((sval - bval) / bval * 100.0) if bval not in (0, None) else None
                })
        return diffs

    def update_scenario_constant(self, scenario_id: int, constant_key: str, new_value: float) -> int:
        """Update a single constant value inside a scenario snapshot."""
        rows = self.execute_update(
            "UPDATE scenario_constants SET constant_value = ? WHERE scenario_id = ? AND constant_key = ?",
            (new_value, scenario_id, constant_key)
        )
        if rows:
            self.log_change('scenario_constants', scenario_id, 'update', new_values={constant_key: new_value})
        return rows

    def create_scenario_from_existing(self, source_scenario_id: int, name: str, description: str = '') -> int:
        """Clone an existing scenario (including its constant snapshot) under a new name."""
        new_id = self.execute_insert(
            "INSERT INTO scenarios (name, description) VALUES (?, ?)",
            (name, description)
        )
        rows = self.execute_query(
            "SELECT constant_key, constant_value FROM scenario_constants WHERE scenario_id = ?",
            (source_scenario_id,)
        )
        for r in rows:
            self.execute_insert(
                "INSERT INTO scenario_constants (scenario_id, constant_key, constant_value) VALUES (?, ?, ?)",
                (new_id, r['constant_key'], r['constant_value'])
            )
        self.log_change('scenarios', new_id, 'create', new_values={'name': name, 'cloned_from': source_scenario_id})
        return new_id

    def purge_scenarios_by_prefix(self, prefixes: List[str]) -> int:
        """Delete scenarios whose names start with any of the given prefixes. Returns count deleted."""
        if not prefixes:
            return 0
        # Build dynamic OR conditions
        conditions = " OR ".join(["name LIKE ?" for _ in prefixes])
        params = [f"{p}%" for p in prefixes]
        # Get IDs first for audit logging
        rows = self.execute_query(f"SELECT scenario_id FROM scenarios WHERE {conditions}", tuple(params))
        count = 0
        for r in rows:
            self.delete_scenario(r['scenario_id'])
            count += 1
        return count

    # (User management removed to simplify application and reduce clutter)
    
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


# Global database instance
db = DatabaseManager()
