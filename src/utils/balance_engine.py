"""
Balance engine orchestrator and closure calculator.

This module wires the fresh inflow, outflow, storage, and recycled services
and applies the single master water balance equation:
    balance_error = fresh_in - outflows - delta_storage
Recycled water is KPI-only and excluded from closure.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import sys
from pathlib import Path

# Import shim
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.balance_services import (
    DataQualityFlags,
    FreshInflows,
    DirtyInflows,
    Outflows,
    StorageSnapshot,
    InflowsService,
    OutflowsService,
    StorageService,
    RecycledService,
)
from utils.balance_kpis import KpiCalculator, KpiResult


@dataclass
class BalanceResult:
    """Output bundle for a balance calculation run."""

    fresh_in: FreshInflows
    outflows: Outflows
    storage: StorageSnapshot
    recycled: DirtyInflows
    error_m3: float
    error_pct: float
    flags: DataQualityFlags
    mode: str
    kpis: Optional[dict] = field(default=None)


class BalanceCalculator:
    """Applies the master water balance equation."""

    @staticmethod
    def compute_closure(total_inflows_m3: float, outflows_m3: float, delta_storage_m3: float) -> tuple[float, float]:
        """Compute closure error.
        
        Args:
            total_inflows_m3: Total inflows (fresh + dirty water)
            outflows_m3: Total outflows
            delta_storage_m3: Change in storage
        """
        error = total_inflows_m3 - outflows_m3 - delta_storage_m3
        pct = (error / total_inflows_m3 * 100.0) if total_inflows_m3 > 0 else 0.0
        return error, pct


class BalanceEngine:
    """Coordinates services to produce a balance result."""

    def __init__(
        self,
        inflows_service: InflowsService,
        outflows_service: OutflowsService,
        storage_service: StorageService,
        recycled_service: Optional[RecycledService] = None,
        mode: str = "REGULATOR",
    ):
        self.inflows_service = inflows_service
        self.outflows_service = outflows_service
        self.storage_service = storage_service
        self.recycled_service = recycled_service or RecycledService()
        self.mode = mode.upper()
        self.kpi_calculator = KpiCalculator()

    def run(self, calculation_date: date) -> BalanceResult:
        flags = DataQualityFlags()

        fresh_in = self.inflows_service.get_fresh(calculation_date, flags)
        # Try to get dirty inflows; if method doesn't exist, fall back to recycled
        if hasattr(self.inflows_service, 'get_dirty'):
            dirty = self.inflows_service.get_dirty(calculation_date, flags)
        else:
            # Fallback for services that only have get_recycled
            dirty = DirtyInflows(total=0, components={})
        
        outflows = self.outflows_service.get_outflows(calculation_date, flags)
        storage = self.storage_service.get_storage(calculation_date, flags)

        # Closure uses FRESH inflows only (recycled/dirty water excluded from mass balance)
        # Scientific principle: Fresh IN = Outflows + ΔStorage + Error
        # Recycled water is accounted for in storage change (returns to TSF)
        fresh_inflows_only = fresh_in.total  # Excludes RWD and dirty sources
        
        error_m3, error_pct = BalanceCalculator.compute_closure(
            fresh_inflows_only,  # Use FRESH only, not total
            outflows.total,
            storage.delta,
        )
        
        # Total inflows = Fresh + Dirty (used for KPI reporting only, not for closure)
        total_inflows = fresh_in.total + dirty.total

        kpis = None
        if self.mode == "OPERATIONS":
            ore_tonnes = 0.0
            # Pull ore tonnes if the inflow service exposes it (legacy adapter does)
            if hasattr(self.inflows_service, "get_ore_tonnes"):
                try:
                    ore_tonnes = float(self.inflows_service.get_ore_tonnes(calculation_date) or 0.0)
                except Exception:
                    ore_tonnes = 0.0

            kpis = self.kpi_calculator.compute(
                fresh_in_m3=fresh_in.total,
                recycled_m3=dirty.total,
                total_outflows_m3=outflows.total,
                ore_tonnes=ore_tonnes,
                storage_open=storage.opening,
                storage_close=storage.closing,
            ).__dict__

        return BalanceResult(
            fresh_in=fresh_in,
            outflows=outflows,
            storage=storage,
            recycled=dirty,
            error_m3=error_m3,
            error_pct=error_pct,
            flags=flags,
            mode=self.mode,
            kpis=kpis,
        )
