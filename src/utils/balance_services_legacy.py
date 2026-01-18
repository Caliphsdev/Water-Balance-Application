"""
Legacy-backed implementations of the balance services using WaterBalanceCalculator.

These adapters reuse the existing calculator to populate the new service interfaces
without changing legacy calculations yet. They ensure fresh inflows exclude recycled
water and avoid TSF inference (TSF handled separately by RecycledService).
"""

from datetime import date
from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.water_balance_calculator import WaterBalanceCalculator
from utils.balance_services import (
    DataQualityFlags,
    FreshInflows,
    DirtyInflows,
    Outflows,
    StorageSnapshot,
    InflowsService,
    OutflowsService,
    StorageService,
)


class LegacyBalanceServices(InflowsService, OutflowsService, StorageService):
    """Adapter over WaterBalanceCalculator to feed the new engine."""

    def __init__(self, ore_tonnes: Optional[float] = None):
        self.calculator = WaterBalanceCalculator()
        self.ore_tonnes = ore_tonnes
        self._balance_cache: Dict[tuple, Dict] = {}

    def _get_balance(self, calculation_date: date) -> Dict:
        key = (calculation_date, self.ore_tonnes)
        if key not in self._balance_cache:
            self._balance_cache[key] = self.calculator.calculate_water_balance(
                calculation_date, self.ore_tonnes
            )
        return self._balance_cache[key]

    def get_fresh(self, calculation_date: date, flags: DataQualityFlags) -> FreshInflows:
        """Return fresh inflows for closure.
        
        Default behavior: includes underground dewatering as fresh (configurable).
        This aligns the regulator view with scientific classification where
        underground pump-out adds new water to the surface system.
        """
        bal = self._get_balance(calculation_date)
        inflows = bal.get("inflows", {}) or {}

        # Config toggle: classify underground as fresh (default True)
        try:
            from utils.config_manager import config
            classify_ug_as_fresh = bool(config.get('features.classify_underground_as_fresh', True))
        except Exception:
            classify_ug_as_fresh = True

        components = {}
        keys = [
            "surface_water",
            "groundwater",
            "rainfall",
            "ore_moisture",
            # NOTE: seepage_gain is NOT included here - it's a facility-level phenomenon
            # calculated automatically based on dam properties and aquifer conditions
        ]
        if classify_ug_as_fresh:
            keys.append("underground")

        for key in keys:
            components[key] = inflows.get(key, 0.0) or 0.0

        if not classify_ug_as_fresh:
            flags.notes["underground_classification"] = (
                "Underground excluded from fresh (classified as recycled for analysis)"
            )

        fresh_total = sum(components.values())
        # plant_returns and returns_to_pit are internal/recycled; exclude from closure
        return FreshInflows(total=fresh_total, components=components)

    def get_dirty(self, calculation_date: date, flags: DataQualityFlags) -> DirtyInflows:
        """Return dirty/recycled water inflows (RWD, underground dewatering).
        
        RWD (Return Water Dam) and underground dewatering are tracked separately
        as "dirty water" to distinguish from fresh water sources.
        """
        bal = self._get_balance(calculation_date)
        inflows = bal.get("inflows", {}) or {}

        # Config toggle: classify underground as fresh (default True)
        try:
            from utils.config_manager import config
            classify_ug_as_fresh = bool(config.get('features.classify_underground_as_fresh', True))
        except Exception:
            classify_ug_as_fresh = True

        components = {}
        
        # RWD (Return Water Dam) - always dirty water
        rwd_val = inflows.get("rwd_inflow", 0.0) or 0.0
        components["rwd_inflow"] = rwd_val

        # Underground dewatering - dirty if not classified as fresh
        if not classify_ug_as_fresh:
            ug_val = inflows.get("underground", 0.0) or 0.0
            components["underground_dewatering"] = ug_val
        else:
            components["underground_dewatering"] = 0.0

        dirty_total = sum(components.values())
        return DirtyInflows(total=dirty_total, components=components)

    def get_outflows(self, calculation_date: date, flags: DataQualityFlags) -> Outflows:
        bal = self._get_balance(calculation_date)
        out = bal.get("outflows", {})
        # System outflows: water permanently leaving the site
        # EXCLUDED from outflows (to avoid double-counting):
        #   • Evaporation: already in ΔStorage (reduces closing volume)
        #   • Seepage Loss: already in ΔStorage (reduces closing volume)
        #   • Plant Consumption: superseded by detailed water usage breakdown below
        components = {
            "mining_consumption": out.get("mining_consumption", 0.0) or 0.0,
            "domestic_consumption": out.get("domestic_consumption", 0.0) or 0.0,
            "product_moisture": out.get("product_moisture", 0.0) or 0.0,
            "tailings_retention": out.get("tailings_retention", 0.0) or 0.0,
            "dust_suppression": out.get("dust_suppression", 0.0) or 0.0,
            "discharge": out.get("discharge", 0.0) or 0.0,
        }
        # Measured-first override: Meter Readings (PGM/Chromite) → Production sheet (fallback)
        try:
            from utils.config_manager import config
            use_prod = config.get('features.use_production_sheet_for_outflows', True)
        except Exception:
            use_prod = True

        if use_prod:
            try:
                from utils.excel_timeseries import get_default_excel_repo
                from utils.excel_timeseries_extended import get_extended_excel_repo
                
                legacy_repo = get_default_excel_repo()
                extended_repo = get_extended_excel_repo()
                
                # PRIORITY 1: Meter Readings (PGM + Chromite wet tons and moisture)
                # Note: Column headers may have trailing spaces
                pgm_wet = legacy_repo.get_monthly_value(calculation_date, "PGM Concentrate Wet tons dispatched")
                # Try with and without trailing space
                pgm_moist = legacy_repo.get_monthly_value(calculation_date, "PGM Concentrate Moisture")
                if not pgm_moist:
                    pgm_moist = legacy_repo.get_monthly_value(calculation_date, "PGM Concentrate Moisture ")
                
                chr_wet = legacy_repo.get_monthly_value(calculation_date, "Chromite Concentrate Wet tons dispatched")
                # Try with and without trailing space
                chr_moist = legacy_repo.get_monthly_value(calculation_date, "Chromite Concentrate Moisture")
                if not chr_moist:
                    chr_moist = legacy_repo.get_monthly_value(calculation_date, "Chromite Concentrate Moisture ")
                
                # Total concentrate tonnage (PGM + Chromite)
                conc_t = None
                if pgm_wet and chr_wet:
                    conc_t = float(pgm_wet) + float(chr_wet)
                
                # Weighted average moisture percent
                conc_moist_pct = None
                if pgm_wet and pgm_moist and chr_wet and chr_moist:
                    total_wet = float(pgm_wet) + float(chr_wet)
                    if total_wet > 0:
                        weighted_moist = (float(pgm_wet) * float(pgm_moist) + float(chr_wet) * float(chr_moist)) / total_wet
                        conc_moist_pct = weighted_moist
                
                # PRIORITY 2: Production sheet (fallback for concentrate if Meter Readings missing, primary for tailings)
                if conc_t is None:
                    conc_t = extended_repo.get_concentrate_produced(calculation_date)
                if conc_moist_pct is None:
                    conc_moist_pct = extended_repo.get_concentrate_moisture(calculation_date)
                
                # Tailings moisture always from Production sheet (not in Meter Readings)
                tails_moist_pct = extended_repo.get_tailings_moisture(calculation_date)
                
                # Get ore tonnes for tailings calculation
                ore_t = 0.0
                try:
                    ore_t = float(self.get_ore_tonnes(calculation_date) or 0.0)
                except Exception:
                    ore_t = 0.0
                
                # Compute product moisture (water shipped off-site in concentrate)
                # Note: Excel stores percentages as values (8.5 for 8.5%), not 0.085
                if conc_t is not None and conc_moist_pct is not None:
                    prod_moist_m3 = max(0.0, float(conc_t) * float(conc_moist_pct) / 100.0)
                    components["product_moisture"] = prod_moist_m3
                    source = "Meter Readings (PGM + Chromite)" if (pgm_wet and chr_wet) else "Production sheet"
                    flags.notes["product_moisture_source"] = source
                
                # Compute tailings retention (water locked in tailings solids)
                # Note: Excel stores percentages as values (32.5 for 32.5%), not 0.325
                if ore_t > 0 and conc_t is not None and tails_moist_pct is not None:
                    tails_solid_t = max(0.0, float(ore_t) - float(conc_t))
                    tails_ret_m3 = max(0.0, tails_solid_t * float(tails_moist_pct) / 100.0)
                    components["tailings_retention"] = tails_ret_m3
                    flags.notes["tailings_retention_source"] = "Production sheet (Tailings Moisture)"
            except Exception:
                # Silently ignore and keep legacy components
                pass

        # Total outflows = sum of all water leaving the system
        total = sum(components.values())
        return Outflows(total=total, components=components)

    def get_storage(self, calculation_date: date, flags: DataQualityFlags) -> StorageSnapshot:
        bal = self._get_balance(calculation_date)
        storage_change = bal.get("storage_change", {})
        opening = storage_change.get("total_opening_volume", 0.0) or 0.0
        closing = storage_change.get("total_closing_volume", 0.0) or 0.0
        facilities = storage_change.get("facilities", {})
        # If any facility used Database source, mark simulated_storage
        if any(v.get("source") == "Database" for v in facilities.values()):
            flags.simulated_storage = True
            flags.notes["storage"] = "Facility volumes include simulated/database values"
        return StorageSnapshot(opening=opening, closing=closing, source="mixed")

    def get_ore_tonnes(self, calculation_date: date) -> float:
        """Expose ore tonnes for KPI intensity; uses the same calculator path."""
        bal = self._get_balance(calculation_date)
        return bal.get("ore_processed", 0.0) or 0.0
