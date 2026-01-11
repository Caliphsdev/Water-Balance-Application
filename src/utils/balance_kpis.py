"""
KPI layer for operations mode.

Calculates recycled %, storage utilization, and intensity metrics without
affecting the closure equation. Recycled water remains excluded from closure.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class KpiResult:
    recycled_percent: float
    recycled_volume: float
    fresh_volume: float
    storage_utilization_pct: float
    storage_open: float
    storage_close: float
    intensity_m3_per_tonne: float


class KpiCalculator:
    """Computes KPI overlays for operations mode."""

    def compute(
        self,
        fresh_in_m3: float,
        recycled_m3: float,
        total_outflows_m3: float,
        ore_tonnes: float,
        storage_open: float,
        storage_close: float,
    ) -> KpiResult:
        total_water = fresh_in_m3 + recycled_m3
        recycled_pct = (recycled_m3 / total_water * 100.0) if total_water > 0 else 0.0
        intensity = (total_outflows_m3 / ore_tonnes) if ore_tonnes and ore_tonnes > 0 else 0.0
        storage_util = (storage_close / storage_close) * 100.0 if storage_close > 0 else 0.0

        return KpiResult(
            recycled_percent=recycled_pct,
            recycled_volume=recycled_m3,
            fresh_volume=fresh_in_m3,
            storage_utilization_pct=storage_util,
            storage_open=storage_open,
            storage_close=storage_close,
            intensity_m3_per_tonne=intensity,
        )