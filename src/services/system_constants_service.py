"""
System Constants Service (BUSINESS LOGIC & CACHING).

Provides high-level operations for reading and updating system constants.
Used by Settings UI and calculation services.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

from database.db_manager import DatabaseManager
from database.repositories.system_constants_repository import SystemConstantsRepository
from database.schema import DatabaseSchema
from models.system_constant import SystemConstant


logger = logging.getLogger(__name__)


class SystemConstantsService:
    """System constants service (BUSINESS LOGIC & CACHE).

    Responsibilities:
    - Load constants for UI and calculations
    - Validate updates against optional min/max bounds
    - Maintain in-memory cache to reduce DB reads
    - Provide audit history data
    """

    def __init__(
        self,
        repository: Optional[SystemConstantsRepository] = None,
        db_manager: Optional[DatabaseManager] = None,
    ):
        """Initialize service (CONSTRUCTOR).

        Args:
            repository: Repository instance (dependency injection)
            db_manager: Database manager (passed to repository if created here)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.repository = repository or SystemConstantsRepository(self.db_manager)

        # Ensure constants tables exist for upgraded databases (non-destructive).
        schema = DatabaseSchema(self.db_manager.db_path)
        schema.ensure_system_constants_tables()

        self._constants_cache: Dict[str, SystemConstant] = {}
        self._cache_loaded = False

    def list_constants(self) -> List[SystemConstant]:
        """Return all constants (READ - LIST CONSTANTS).

        Returns:
            List of SystemConstant models
        """
        return self.repository.list_constants()

    def list_categories(self) -> List[str]:
        """Return distinct categories (READ - CATEGORY LIST).

        Returns:
            List of category strings
        """
        return self.repository.list_categories()

    def get_constant_map(self, refresh: bool = False) -> Dict[str, SystemConstant]:
        """Get constants map keyed by constant_key (CACHE ACCESS).

        Args:
            refresh: If True, reload cache from database

        Returns:
            Dict of constant_key -> SystemConstant
        """
        if refresh or not self._cache_loaded:
            constants = self.repository.list_constants()
            self._constants_cache = {c.constant_key: c for c in constants}
            self._cache_loaded = True
        return self._constants_cache

    def get_constant_value(self, key: str, default: float = 0.0) -> float:
        """Get numeric constant value by key (CALCULATION ACCESSOR).

        Args:
            key: Constant identifier
            default: Fallback value if constant missing

        Returns:
            Numeric value
        """
        constant = self.get_constant_map().get(key)
        return constant.constant_value if constant else default

    def create_constant(self, constant: SystemConstant) -> SystemConstant:
        """Create new constant with validation (CREATE - INSERT).

        Args:
            constant: SystemConstant model

        Returns:
            Created SystemConstant
        """
        self._validate_constant_bounds(constant)
        created = self.repository.create(constant)
        self.get_constant_map(refresh=True)
        return created

    def update_constant(self, constant: SystemConstant, updated_by: str = "system") -> SystemConstant:
        """Update existing constant with validation (UPDATE - MODIFY).

        Args:
            constant: SystemConstant model
            updated_by: Username for audit logging

        Returns:
            Updated SystemConstant
        """
        self._validate_constant_bounds(constant)
        updated = self.repository.update(constant, updated_by=updated_by)
        self.get_constant_map(refresh=True)
        return updated

    def delete_constant(self, constant_key: str) -> int:
        """Delete constant by key (DELETE - REMOVE).

        Args:
            constant_key: Key to delete

        Returns:
            Number of rows affected
        """
        count = self.repository.delete(constant_key)
        self.get_constant_map(refresh=True)
        return count

    def list_history(self, limit: int = 200) -> List[dict]:
        """Get constant update history (READ - AUDIT LOG).

        Args:
            limit: Max number of rows

        Returns:
            List of history dicts
        """
        return self.repository.list_history(limit=limit)

    def _validate_constant_bounds(self, constant: SystemConstant) -> None:
        """Validate constant value against optional bounds (INTERNAL - VALIDATION).

        Args:
            constant: SystemConstant model

        Raises:
            ValueError: If value outside min/max bounds
        """
        if constant.min_value is not None and constant.constant_value < constant.min_value:
            raise ValueError(
                f"Value for {constant.constant_key} below minimum ({constant.min_value})"
            )
        if constant.max_value is not None and constant.constant_value > constant.max_value:
            raise ValueError(
                f"Value for {constant.constant_key} above maximum ({constant.max_value})"
            )

    def sync_from_packaged_db(self, packaged_db_path: Path, overwrite: bool = False) -> int:
        """Sync system constants from a packaged database (IMPORT DEFAULTS).

        Inserts missing constants from the packaged DB into the user DB.
        By default, existing constants are preserved.

        Args:
            packaged_db_path: Path to packaged water_balance.db
            overwrite: If True, update existing constants with packaged values

        Returns:
            Number of constants inserted or updated
        """
        if not packaged_db_path.exists():
            return 0

        try:
            if packaged_db_path.resolve() == Path(self.db_manager.db_path).resolve():
                return 0
        except Exception:
            # If resolve fails, fall back to best-effort sync.
            pass

        inserted_or_updated = 0
        try:
            source_conn = sqlite3.connect(str(packaged_db_path))
            source_conn.row_factory = sqlite3.Row
            rows = source_conn.execute(
                """
                SELECT constant_key, constant_value, unit, category, description,
                       editable, min_value, max_value
                FROM system_constants
                ORDER BY category, constant_key
                """
            ).fetchall()
        except sqlite3.Error as exc:
            logger.warning("Failed to read packaged constants: %s", exc)
            return 0
        finally:
            try:
                source_conn.close()
            except Exception:
                pass

        if not rows:
            return 0

        for row in rows:
            constant = SystemConstant(
                constant_key=row["constant_key"],
                constant_value=row["constant_value"],
                unit=row["unit"],
                category=row["category"],
                description=row["description"],
                editable=row["editable"],
                min_value=row["min_value"],
                max_value=row["max_value"],
            )
            existing = self.repository.get_by_key(constant.constant_key)
            if existing is None:
                self.repository.create(constant)
                inserted_or_updated += 1
                continue

            if overwrite:
                updated = constant.copy(update={"id": existing.id})
                self.repository.update(updated, updated_by="system")
                inserted_or_updated += 1

        if inserted_or_updated:
            self.get_constant_map(refresh=True)

        return inserted_or_updated

    def seed_defaults_if_empty(self) -> int:
        """Seed baseline constants into an empty constants table.

        This keeps Settings > Constants usable even when no packaged DB is shipped.
        Values are sourced from runtime constants (config-aware), then persisted.
        """
        if self.repository.list_constants():
            return 0

        defaults = self._build_default_constants_payload()
        inserted = 0
        for item in defaults:
            try:
                self.repository.create(SystemConstant(**item))
                inserted += 1
            except Exception as exc:
                logger.warning("Failed seeding constant %s: %s", item.get("constant_key"), exc)

        if inserted:
            self.get_constant_map(refresh=True)
        return inserted

    def ensure_default_constants(self) -> int:
        """Ensure baseline constants exist; insert any missing keys.

        Use this for upgraded databases where table exists but some keys are absent.
        """
        defaults = self._build_default_constants_payload()
        existing_keys = {c.constant_key for c in self.repository.list_constants()}
        inserted = 0
        for item in defaults:
            key = item.get("constant_key")
            if key in existing_keys:
                continue
            try:
                self.repository.create(SystemConstant(**item))
                inserted += 1
                existing_keys.add(key)
            except Exception as exc:
                logger.warning("Failed inserting missing default constant %s: %s", key, exc)

        if inserted:
            self.get_constant_map(refresh=True)
        return inserted

    def _build_default_constants_payload(self) -> List[Dict[str, Any]]:
        """Create constant rows from calculation defaults/config."""
        from services.calculation.constants import ConstantsLoader

        meta: List[Dict[str, Any]] = [
            {
                "constant_key": "evap_pan_coefficient",
                "attr": "evap_pan_coefficient",
                "unit": "ratio",
                "category": "evaporation",
                "description": "Pan-to-lake evaporation conversion factor",
                "min_value": 0.0,
                "max_value": 2.0,
            },
            {
                "constant_key": "seepage_rate_lined_pct",
                "attr": "seepage_rate_lined_pct",
                "unit": "%",
                "category": "seepage",
                "description": "Monthly seepage loss rate for lined facilities",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "seepage_rate_unlined_pct",
                "attr": "seepage_rate_unlined_pct",
                "unit": "%",
                "category": "seepage",
                "description": "Monthly seepage loss rate for unlined facilities",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "tsf_return_water_pct",
                "attr": "tsf_return_water_pct",
                "unit": "%",
                "category": "recycling",
                "description": "Estimated percentage of process water returned from TSF",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "tailings_moisture_pct",
                "attr": "tailings_moisture_pct",
                "unit": "%",
                "category": "tailings",
                "description": "Fallback moisture retained in tailings",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "tailings_solids_density",
                "attr": "tailings_solids_density",
                "unit": "t/m3",
                "category": "tailings",
                "description": "Tailings solids density used in moisture calculations",
                "min_value": 0.1,
                "max_value": 10.0,
            },
            {
                "constant_key": "ore_moisture_pct",
                "attr": "ore_moisture_pct",
                "unit": "%",
                "category": "plant",
                "description": "Moisture percentage in ore feed",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "product_moisture_pct",
                "attr": "product_moisture_pct",
                "unit": "%",
                "category": "plant",
                "description": "Moisture percentage in final product",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "recovery_rate_pct",
                "attr": "recovery_rate_pct",
                "unit": "%",
                "category": "plant",
                "description": "Ore mass recovery rate used for product assumptions",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "dust_suppression_rate_l_per_t",
                "attr": "dust_suppression_rate_l_per_t",
                "unit": "L/t",
                "category": "plant",
                "description": "Dust suppression water application rate per tonne milled",
                "min_value": 0.0,
                "max_value": 1000.0,
            },
            {
                "constant_key": "mining_water_rate_m3_per_t",
                "attr": "mining_water_rate_m3_per_t",
                "unit": "m3/t",
                "category": "mining",
                "description": "Mining water use rate per tonne mined",
                "min_value": 0.0,
                "max_value": 10.0,
            },
            {
                "constant_key": "domestic_consumption_l_per_person_day",
                "attr": "domestic_consumption_l_per_person_day",
                "unit": "L/person/day",
                "category": "domestic",
                "description": "Domestic water demand per person per day",
                "min_value": 0.0,
                "max_value": 1000.0,
            },
            {
                "constant_key": "pump_start_level_pct",
                "attr": "pump_start_level_pct",
                "unit": "%",
                "category": "storage",
                "description": "Automatic transfer trigger level",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "pump_increment_pct",
                "attr": "pump_increment_pct",
                "unit": "%",
                "category": "storage",
                "description": "Transfer increment when auto-transfer triggers",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "balance_error_threshold_pct",
                "attr": "balance_error_threshold_pct",
                "unit": "%",
                "category": "quality",
                "description": "Target maximum acceptable balance closure error",
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "constant_key": "stale_data_warning_days",
                "attr": "stale_data_warning_days",
                "unit": "days",
                "category": "quality",
                "description": "Warning threshold for stale source data",
                "min_value": 0.0,
                "max_value": 3650.0,
            },
            {
                "constant_key": "runoff_enabled",
                "attr": "runoff_enabled",
                "unit": "0/1",
                "category": "feature_flags",
                "description": "Enable runoff component in inflow calculations",
                "min_value": 0.0,
                "max_value": 1.0,
            },
            {
                "constant_key": "dewatering_enabled",
                "attr": "dewatering_enabled",
                "unit": "0/1",
                "category": "feature_flags",
                "description": "Enable dewatering inflow component",
                "min_value": 0.0,
                "max_value": 1.0,
            },
            {
                "constant_key": "mining_consumption_enabled",
                "attr": "mining_consumption_enabled",
                "unit": "0/1",
                "category": "feature_flags",
                "description": "Enable mining consumption outflow component",
                "min_value": 0.0,
                "max_value": 1.0,
            },
            {
                "constant_key": "domestic_consumption_enabled",
                "attr": "domestic_consumption_enabled",
                "unit": "0/1",
                "category": "feature_flags",
                "description": "Enable domestic consumption outflow component",
                "min_value": 0.0,
                "max_value": 1.0,
            },
        ]

        values = ConstantsLoader().constants
        payload: List[Dict[str, Any]] = []
        for item in meta:
            raw_value = getattr(values, item["attr"], None)
            if raw_value is None:
                continue
            if isinstance(raw_value, bool):
                raw_value = 1.0 if raw_value else 0.0
            payload.append(
                {
                    "constant_key": item["constant_key"],
                    "constant_value": float(raw_value),
                    "unit": item["unit"],
                    "category": item["category"],
                    "description": item["description"],
                    "editable": 1,
                    "min_value": item.get("min_value"),
                    "max_value": item.get("max_value"),
                }
            )
        return payload
