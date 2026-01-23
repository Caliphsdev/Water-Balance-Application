"""
Foundational service classes for water balance inputs.

This module provides small, composable services for inflows, outflows,
and storage snapshots. They are intentionally thin and will be wired into
the main balance engine in later steps. Each service returns structured
data classes and will surface data-quality flags (measured vs simulated,
missing data) without performing balance closure here.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional
import sys
from pathlib import Path

# Import shim for src package
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class DataQualityFlags:
    """Tracks data quality for a calculation run.

    Adds helper methods so UI/tests can register ad-hoc flags (e.g., missing
    rainfall) without needing to know the internal storage structure.
    """

    missing_tsf_return: bool = False
    simulated_storage: bool = False
    estimated_inflows: bool = False
    estimated_outflows: bool = False
    notes: Dict[str, str] = field(default_factory=dict)

    def add_flag(self, key: str, message: str) -> None:
        """Record a human-readable data quality flag for later display.

        Args:
            key: Unique flag identifier (e.g., 'missing_rainfall').
            message: Description shown in UI/tests explaining the data issue.
        """
        # NOTE: UI rendering expects flags in `notes`; keep a single source.
        self.notes[key] = message

    def as_dict(self) -> Dict[str, str]:
        """Flatten flags to a display-friendly dict for UI tooltips/cards."""
        info = {}
        if self.missing_tsf_return:
            info["missing_tsf_return"] = "TSF return missing; set to 0"
        if self.simulated_storage:
            info["simulated_storage"] = "Storage uses simulated/database values"
        if self.estimated_inflows:
            info["estimated_inflows"] = "Inflows include estimates"
        if self.estimated_outflows:
            info["estimated_outflows"] = "Outflows include estimates"
        info.update(self.notes)
        return info


@dataclass
class FreshInflows:
    """Fresh water entering the system."""
    total: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


@dataclass
class DirtyInflows:
    """Dirty/recycled water inflows (RWD, underground dewatering)."""
    total: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


@dataclass
class Outflows:
    """Explicit outflows from the system."""
    total: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


@dataclass(init=False)
class StorageSnapshot:
    """Opening/closing storage volumes and their source.

    Tests sometimes supply an explicit `delta` argument; support that via
    `_delta_override` so UI rendering can use provided value without breaking
    the default calculation (closing - opening).
    """

    opening: float = 0.0
    closing: float = 0.0
    source: str = "unknown"  # measured | simulated
    _delta_override: Optional[float] = field(default=None, repr=False)

    def __init__(self, opening: float = 0.0, closing: float = 0.0, source: str = "unknown", delta: Optional[float] = None):
        """Initialize snapshot with optional explicit delta override.

        Args:
            opening: Opening volume for period (m³).
            closing: Closing volume for period (m³).
            source: Data origin (e.g., 'Database', 'Simulated').
            delta: Optional pre-computed delta used when provided; otherwise
                computed as closing - opening.
        """
        # Store raw volumes and any caller-provided delta for UI/testing.
        self.opening = opening
        self.closing = closing
        self.source = source
        self._delta_override = delta

    @property
    def delta(self) -> float:
        # Prefer explicit override (used in tests) to avoid recomputing.
        if self._delta_override is not None:
            return float(self._delta_override)
        return self.closing - self.opening


class InflowsService:
    """Retrieves fresh and dirty inflows for a calculation date."""

    def get_fresh(self, calculation_date: date, flags: DataQualityFlags) -> FreshInflows:
        """Return fresh inflows; to be implemented with measured-first logic."""
        raise NotImplementedError

    def get_dirty(self, calculation_date: date, flags: DataQualityFlags) -> DirtyInflows:
        """Return dirty/recycled inflows (RWD, underground dewatering)."""
        raise NotImplementedError


class OutflowsService:
    """Retrieves explicit outflows for a calculation date."""

    def get_outflows(self, calculation_date: date, flags: DataQualityFlags) -> Outflows:
        """Return outflows; to be implemented with measured-first logic."""
        raise NotImplementedError


class StorageService:
    """Provides storage opening/closing volumes (measured preferred)."""

    def get_storage(self, calculation_date: date, flags: DataQualityFlags) -> StorageSnapshot:
        """Return storage snapshot; simulate only when measured data is unavailable."""
        raise NotImplementedError


class RecycledService:
    """Handler for dirty/recycled water inflows (RWD, underground dewatering)."""

    def __init__(self):
        from database.db_manager import DatabaseManager
        from utils.excel_timeseries import get_default_excel_repo

        self.db = DatabaseManager()
        self._excel_repo = get_default_excel_repo()

    def _get_excel_tsf_return(self, calculation_date: date) -> Optional[float]:
        try:
            val = self._excel_repo.get_monthly_value(calculation_date, "RWD")
            if val and val > 0:
                return float(val)
        except Exception:
            return None
        return None

    def _get_db_tsf_return(self, calculation_date: date) -> Optional[float]:
        try:
            month_start = date(calculation_date.year, calculation_date.month, 1)
            rows = self.db.execute_query(
                """
                SELECT tsf_return_m3
                FROM tsf_return_monthly
                WHERE month_start = ?
                LIMIT 1
                """,
                (month_start,),
            )
            if rows and rows[0].get("tsf_return_m3"):
                return float(rows[0]["tsf_return_m3"])
        except Exception:
            return None
        return None

    def get_recycled(self, calculation_date: date, flags: DataQualityFlags) -> DirtyInflows:
        """Return recycled inflows (RWD and underground dewatering flows).
        
        These are internal water flows that are INCLUDED in balance closure but tracked separately
        to distinguish from fresh water sources.
        
        Components:
        - rwd_inflow: RWD [Return Water Dam] - recycled water supply to mine (from Excel or DB)
        - underground_dewatering: sum of three shafts from Meter Readings
        """
        components: Dict[str, float] = {}

        # RWD inflow (recycled water from Return Water Dam)
        excel_val = self._get_excel_tsf_return(calculation_date)
        db_val = None if excel_val is not None else self._get_db_tsf_return(calculation_date)
        rwd_inflow = excel_val if excel_val is not None else db_val
        if rwd_inflow is None:
            flags.missing_tsf_return = True
            flags.notes["rwd_inflow"] = "Missing RWD inflow; set to 0"
            rwd_inflow = 0.0
        components["rwd_inflow"] = rwd_inflow

        # Underground dewatering (three shafts) from Meter Readings when available
        ug_total = 0.0
        try:
            # Header names as provided in mapping; absent headers yield 0.0
            ug_main = self._excel_repo.get_monthly_value(calculation_date, "Main decline dewatering")
            ug_north = self._excel_repo.get_monthly_value(calculation_date, "North decline dewatering")
            ug_mer = self._excel_repo.get_monthly_value(calculation_date, "Merensky dewatering")
            # Coerce to float and handle None
            ug_total = float(ug_main or 0.0) + float(ug_north or 0.0) + float(ug_mer or 0.0)
        except Exception:
            ug_total = 0.0
        components["underground_dewatering"] = ug_total

        total = rwd_inflow + ug_total

        return DirtyInflows(total=total, components=components)
