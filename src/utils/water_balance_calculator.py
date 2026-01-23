"""
Water Balance Calculation Engine
Core calculations for mine water balance based on TRP formulas

Implements formulas from Excel analysis:
- Plant makeup water requirements
- TSF return water calculations
- Evaporation losses
- Water balance equations
- Storage level changes
- Automatic pump transfers between facilities
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.historical_averaging import HistoricalAveraging
from utils.excel_timeseries import get_default_excel_repo
from utils.app_logger import logger
from utils.alert_manager import alert_manager
from utils.pump_transfer_engine import PumpTransferEngine
from utils.config_manager import config


class WaterBalanceCalculator:
    """Water balance calculation engine"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.constants = self._load_constants()
        self.historical_avg = HistoricalAveraging(self.db)
        # Excel repositories - initialized lazily on first use
        self._excel_repo = None
        self._excel_repo_path = None  # Track Meter Readings path for config change detection
        self._flow_repo = None  # Flow diagram Excel repo (initialized lazily)
        self._flow_repo_path = None  # Track Flow Diagram path for config change detection
        # Pump transfer engine
        self.pump_transfer_engine = PumpTransferEngine(self.db, self)
        # Performance optimization: cache for balance calculations
        self._balance_cache = {}
        self._kpi_cache = {}
        # Miscellaneous per-date caches (dust suppression, facility measurements, etc.)
        self._misc_cache: Dict[str, Dict] = {}
        # Capacity warnings tracker - cleared at start of each calculation
        self._capacity_warnings = []
        # Cache invalidation listeners (for observer pattern)
        self._cache_listeners = []
    
    def _get_excel_repo(self):
        r"""Lazy-load Excel repository on first access, detecting config changes.
        
        Loads METER READINGS Excel (legacy_excel_path: data\New Water Balance...xlsx)
        which contains "Meter Readings" sheet with tonnes milled, RWD, dewatering, etc.
        
        NOT the Flow Diagram Excel (timeseries_excel_path) which has Flows_* sheets.
        
        Detects Excel path changes: if user changes legacy_excel_path in Settings,
        automatically reloads from the new path on next access.
        """
        from utils.config_manager import config
        
        current_path = config.get('data_sources.legacy_excel_path')
        
        # Path changed or first access: reload Excel repo
        if self._excel_repo is None or self._excel_repo_path != current_path:
            self._excel_repo = get_default_excel_repo()
            self._excel_repo_path = current_path
            if self._excel_repo_path != current_path:
                logger.debug(f"Excel (Meter Readings) path changed from {self._excel_repo_path} to {current_path}, reloading")
        
        return self._excel_repo
    
    def register_cache_listener(self, callback) -> None:
        """Register a callback to be notified when caches are invalidated.
        
        Usage:
            def on_cache_clear():
                # Respond to cache invalidation (e.g., refresh UI)
                pass
            calculator.register_cache_listener(on_cache_clear)
        
        Args:
            callback: Callable that takes no arguments
        """
        if callback and callable(callback):
            self._cache_listeners.append(callback)
            logger.debug(f"Cache listener registered: {callback}")
    
    def _notify_cache_listeners(self) -> None:
        """Notify all registered listeners that cache has been cleared."""
        for listener in self._cache_listeners:
            try:
                listener()
            except Exception as e:
                logger.error(f"Cache listener error: {e}")
    
    def clear_cache(self) -> None:
        """Clear all calculation and Excel data caches (Critical for data consistency).
        
        MANDATORY: Call this method when:
        1. User updates Excel file externally (new measurements, meter readings)
        2. Configuration changes (Excel path updated, facility definitions modified)
        3. Database is manually edited (water sources, storage facilities)
        4. Monthly calculations are re-run (force fresh Excel read)
        
        Cache Architecture:
        - _balance_cache: {date_key: {facility: balance_result}} - water balance for each facility
        - _kpi_cache: {date_key: kpi_metrics} - key performance indicators
        - _misc_cache: {date_key: misc_metrics} - miscellaneous calculations
        - _excel_repo: File I/O cache for measurements and operational data
        
        Without clearing, stale Excel data will be reused, producing incorrect results
        and cascading errors through downstream dashboards.
        
        After clearing, notifies all registered cache listeners so dependent systems
        (UI dashboards, etc.) can refresh their displays.
        """
        self._balance_cache.clear()
        self._kpi_cache.clear()
        self._misc_cache.clear()
        # Propagate cache clear to Excel repository if it's been initialized
        if self._excel_repo is not None:
            self._excel_repo.clear_cache()
            logger.debug("Excel (Meter Readings) repository cache cleared")
        if self._flow_repo is not None:
            self._flow_repo.clear_cache()
            logger.debug("Excel (Flow Diagram) repository cache cleared")
        
        # Notify all observers that cache has been invalidated
        self._notify_cache_listeners()
    
    def _validate_facility_flows(self, facility_code: str, capacity: float,
                                inflow_total: float, outflow_total: float,
                                opening_volume: float) -> None:
        """Validate that flows don't exceed dam capacity.
        
        Args:
            facility_code: Facility identifier
            capacity: Total capacity in m³
            inflow_total: Total inflows (manual + rain) in m³
            outflow_total: Total outflows (manual + evap + abstraction) in m³
            opening_volume: Opening volume in m³
        
        Logs warnings if:
        - Projected closing > capacity (overflow risk)
        - Single inflow/outflow > capacity (data entry error likely)
        - Opening volume > capacity (data inconsistency)
        """
        if not capacity or capacity <= 0:
            return  # Skip validation for facilities without capacity
        
        warnings = []
        projected_closing = opening_volume + inflow_total - outflow_total
        
        # Check opening volume
        if opening_volume > capacity:
            warnings.append(
                f"{facility_code}: Opening volume ({opening_volume:,.0f} m³) exceeds capacity ({capacity:,.0f} m³)"
            )
        
        # Check single inflow exceeds capacity (likely data error)
        if inflow_total > capacity * 1.5:  # Allow 1.5x for multi-month accumulation
            warnings.append(
                f"{facility_code}: Inflow ({inflow_total:,.0f} m³) exceeds 150% capacity ({capacity:,.0f} m³) - check data entry"
            )
        
        # Check single outflow exceeds capacity
        if outflow_total > capacity * 1.5:
            warnings.append(
                f"{facility_code}: Outflow ({outflow_total:,.0f} m³) exceeds 150% capacity ({capacity:,.0f} m³) - check data entry"
            )
        
        # Check projected overflow
        if projected_closing > capacity:
            overflow = projected_closing - capacity
            warnings.append(
                f"{facility_code}: Projected closing ({projected_closing:,.0f} m³) exceeds capacity by {overflow:,.0f} m³ - will be clamped"
            )
        
        # Log all warnings
        for warning in warnings:
            logger.warning(warning)
            alert_manager.add_alert('warning', f'Capacity Validation: {warning}', 'storage_validation')
            self._capacity_warnings.append(warning)
    
    def get_capacity_warnings(self) -> List[str]:
        """Return list of capacity validation warnings from last calculation."""
        return self._capacity_warnings.copy()
    
    def clear_capacity_warnings(self) -> None:
        """Clear capacity warnings list."""
        self._capacity_warnings.clear()
    
    def _load_constants(self) -> Dict:
        """Load system constants from database"""
        constants_data = self.db.execute_query("SELECT * FROM system_constants")
        
        constants = {}
        for const in constants_data:
            # Map constant keys to standardized names
            key = const['constant_key'].lower().replace('_', '')
            constants[key] = float(const['constant_value'])
            
            # Also store with friendly names
            if 'TSF' in const['constant_key']:
                constants['tsf_return_percentage'] = float(const['constant_value']) * 100
        
        return constants
    
    def get_constant(self, name: str, default: float = 0.0) -> float:
        """Get a system constant value"""
        # Direct lookup first (for friendly keys like 'mining_water_per_tonne')
        if name in self.constants:
            return self.constants.get(name, default)
        # Normalize: lower + remove underscores for raw DB keys
        norm = name.lower().replace('_', '')
        # Map common raw forms to friendly storage keys
        alias_map = {
            'tsfreturnrate': 'tsf_return_percentage'
        }
        mapped = alias_map.get(norm, norm)
        return self.constants.get(mapped, default)
    
    # ==================== INFLOWS ====================
    
    def calculate_source_inflow(self, source_id: int, calculation_date: date,
                                use_historical_avg: bool = True,
                                preloaded: Optional[Dict[int, Dict]] = None,
                                preloaded_sources: Optional[Dict[int, Dict]] = None) -> float:
        """
        Calculate inflow from a water source (Excel-only: borehole/river measurements)
        Priority: Excel value > source default
        
        Args:
            source_id: Water source ID
            calculation_date: Date of calculation
            use_historical_avg: Deprecated (kept for API compatibility)
            preloaded: Deprecated (kept for API compatibility)
        """
        # Get source metadata
        source = None
        if preloaded_sources and source_id in preloaded_sources:
            source = preloaded_sources[source_id]
        else:
            source = self.db.get_water_source(source_id)

        if not source:
            return 0.0

        # Try to get value from Excel time-series
        header_name = self._get_excel_header_for_source(source)
        if header_name:
            try:
                val = self._get_excel_repo().get_monthly_value(calculation_date, header_name)
                # Accept explicit zeros from Excel; only fall back when truly missing (None)
                if val is not None:
                    return float(val)
            except Exception:
                pass
        # If Excel provided no value, force zero defaults for specified categories
        # per user request: Groundwater (boreholes), Underground (dewatering),
        # and Rivers/Transfers (surface water, river/stream/dam, transfer/portal/plant).
        stype = (source.get('type_name', '') or '').lower()
        if (
            'borehole' in stype or 'groundwater' in stype or
            'underground' in stype or 'dewater' in stype or
            'surface' in stype or 'river' in stype or 'stream' in stype or 'dam' in stype or
            'transfer' in stype or 'portal' in stype or 'plant' in stype
        ):
            return 0.0
        
        # Fallback to source default from metadata
        avg_flow = source.get('average_flow_rate', 0.0) or 0.0
        reliability_raw = source.get('reliability_factor', 0.85)
        if reliability_raw > 1:  # treat as percent
            reliability = reliability_raw / 100.0
        else:
            reliability = reliability_raw
        
        return avg_flow * reliability

    def _get_excel_header_for_source(self, source: Dict) -> Optional[str]:
        """Map a water source row to an Excel column header.

        For now we use simple rules based on source_code and source_name.
        This is deliberately conservative so that only clearly-mapped
        sources are driven from Excel; others still use DB defaults.
        """
        code = (source.get("source_code") or "").strip()
        name = (source.get("source_name") or "").strip()

        # Explicit mappings between source_code and Excel column headers
        mapping = {
            # Rivers
            "Groot Dwars": "Groot Dwars River",
            "Klein Dwars": "Klein Dwars River",
            # Transfers / plant-related
            "PTN": "Plant to North",
            # In DB the source_code is WTP(M) but the Excel header
            # is "Water to Portal(Main)".
            "WTP(M)": "Water to Portal(Main)",
            # Underground dewatering
            "SDUGW": "Main decline dewatering",
            # NDUGW is the code in DB for North Decline Underground
            # water, mapped to the Excel "North decline dewatering".
            "NDUGW": "North decline dewatering",
            "MNUGW": "Merensky dewatering",
            # Borehole groups and summaries (where you want direct
            # use of the Excel totals instead of individual boreholes)
            "CPGWA 1": "CPGWA 1",
            "CPGWA 2": "CPGWA 2",
            "CPGWA 3": "CPGWA 3",
            "NTSFGWA 1": "NTSFGWA 1",
            "NTSFGWA 2": "NTSFGWA 2",
            "MDGWA 1": "MDGWA 1",
            # Note: Excel has a space in "MDGWA 2 "
            "MDGWA 2": "MDGWA 2 ",
            "MDGWA 3": "MDGWA 3",
            "MDGWA 4": "MDGWA 4",
            "MDGWA 5": "MDGWA 5",
            "NDGWA 1": "NDGWA 1",
            "NDGWA 2": "NDGWA 2",
            "NDGWA 3": "NDGWA 3",
            "NDGWA 4": "NDGWA 4",
            "NDGWA 5": "NDGWA 5",
            "NDGWA 6": "NDGWA 6",
            "MERGWA 1": "MERGWA 1",
            "MERGWA 2": "MERGWA 2",
        }

        if code in mapping:
            return mapping[code]

        # For boreholes where the Excel column header is the same as
        # the registered source name, we can fall back to name matching.
        df = getattr(self._get_excel_repo(), "_df", None)
        if df is not None and name in df.columns:
            return name

        return None

    def calculate_total_inflows(self,
                                calculation_date: date,
                                ore_tonnes: float = None,
                                skip_measurements: bool = False,
                                preloaded_sources: Optional[List[Dict]] = None,
                                preloaded_facilities: Optional[List[Dict]] = None) -> Dict[str, float]:
        """
        Calculate total inflows from all active sources (FULL EXCEL PARITY)
        Returns breakdown by source type matching legacy model
        """
        sources = preloaded_sources if preloaded_sources is not None else self.db.get_water_sources(active_only=True)
        # Build source map to avoid repeated per-source fetches for fallback defaults
        source_map = {s['source_id']: s for s in sources}
        
        inflows = {
            'surface_water': 0.0,
            'groundwater': 0.0,
            'underground': 0.0,
            'rainfall': 0.0,
            'ore_moisture': 0.0,
            'tsf_return': 0.0,
            'plant_returns': 0.0,
            'returns_to_pit': 0.0,
            'seepage_gain': 0.0,
            'total': 0.0  # Legacy total (core components only for tests when ore_tonnes is None)
        }

        for source in sources:
            flow = self.calculate_source_inflow(
                source['source_id'], calculation_date,
                preloaded_sources=source_map
            )
            
            # Get source type name
            source_type_name = source.get('type_name', '').lower()
            
            # Categorize by source type (Excel granularity)
            if ('surface' in source_type_name or 'river' in source_type_name or 
                'stream' in source_type_name or 'dam' in source_type_name):
                inflows['surface_water'] += flow
                inflows['total'] += flow
            elif 'borehole' in source_type_name or 'groundwater' in source_type_name:
                inflows['groundwater'] += flow
                inflows['total'] += flow
            elif 'underground' in source_type_name or 'dewater' in source_type_name:
                inflows['underground'] += flow
                inflows['total'] += flow
        
        # Add rainfall (from measurements if available)
        # Always attempt rainfall (uses fallback constant if no measurements); skip_measurements only affects querying overhead.
        rainfall = self._get_rainfall_inflow(calculation_date, preloaded_facilities=preloaded_facilities) if not skip_measurements else self._get_rainfall_inflow(calculation_date, preloaded_facilities=preloaded_facilities)
        inflows['rainfall'] = rainfall
        inflows['total'] += rainfall
        
        # Ore moisture water (Excel: FROM WET ORE)
        # Include ore moisture only when explicit ore_tonnes provided (align tests)
        # Ore moisture water: allow stored measurement (measurement_type='ore_processed') when ore_tonnes not passed
        ore_moisture, ore_source_present = self.calculate_ore_moisture_water(ore_tonnes, calculation_date)
        inflows['ore_moisture'] = ore_moisture
        # Add to total if explicit ore tonnage provided OR measurement present (keeps legacy tests excluding only when no source at all)
        if ore_source_present:
            inflows['total'] += ore_moisture
        
        # RWD (Return Water Dam) - Excel column AO
        # - When Excel RWD exists for the month, display as dirty water inflow
        #   do NOT use it to reduce plant consumption (net = gross).
        # - When no Excel RWD, TSF is calculated automatically in outflows.
        if not skip_measurements and calculation_date is not None:
            try:
                excel_rwd = self._get_excel_repo().get_monthly_value(calculation_date, "RWD")
                if excel_rwd and excel_rwd > 0:
                    inflows['rwd_inflow'] = float(excel_rwd)
                    inflows['total'] += inflows['rwd_inflow']
            except Exception:
                pass
        
        # Extended inflow categories: exclude from legacy 'total' when ore_tonnes is None (legacy test expectation)
        if not skip_measurements:
            plant_returns = self.calculate_plant_returns(calculation_date)
            inflows['plant_returns'] = plant_returns
            if ore_tonnes is not None:
                inflows['total'] += plant_returns

            returns_to_pit = self.calculate_returns_to_pit(calculation_date)
            inflows['returns_to_pit'] = returns_to_pit
            if ore_tonnes is not None:
                inflows['total'] += returns_to_pit
        
        # NOTE: Seepage gain is NOT included in mine-level inflows
        # It is handled at the facility level (storage balance) as an automatic calculation
        # based on dam properties (lining, geology, aquifer conditions)
        
        return inflows
    
    def _get_rainfall_inflow(self, calculation_date: date, preloaded_facilities: Optional[List[Dict]] = None) -> float:
        """Calculate rainfall contribution to storage using database regional rainfall.
        Uses year-aware monthly value and applies only to facilities with evaporation enabled.
        """
        # Use database regional rainfall (per-facility calculation handles this now)
        # Sum up all facility rainfall from calculate_facility_balance
        facilities = preloaded_facilities if preloaded_facilities is not None else self.db.get_storage_facilities()
        
        month = calculation_date.month
        year = calculation_date.year
        total_rainfall_volume = 0.0
        
        for f in facilities:
            # Get regional rainfall for this month (year-aware)
            regional_rainfall_mm = self.db.get_regional_rainfall_monthly(month, year)
            if regional_rainfall_mm is None or regional_rainfall_mm <= 0:
                continue
                
            # Check if evaporation is active for this facility
            evap_flag = f.get('evap_active', 1)
            if evap_flag in (None, ''):
                evap_flag = 1
            if int(evap_flag) != 1:
                continue
                
            # Calculate rainfall volume for this facility
            surface_area = f.get('surface_area', 0) or 0.0
            if surface_area > 0:
                facility_rainfall_volume = (regional_rainfall_mm / 1000.0) * surface_area
                total_rainfall_volume += facility_rainfall_volume
        
        return total_rainfall_volume
    
    def calculate_ore_moisture_water(self, ore_tonnes: float = None, calculation_date: date = None) -> tuple:
        """Calculate water from ore moisture.
        Priority order for ore tonnage source:
          1. Excel monthly value 'Tonnes Milled' (by year+month)
          2. Explicit ore_tonnes argument (only if > 0)
        
        Returns: (ore_moisture_water_m3, source_present_bool)
        source_present_bool True only if data came from Excel or explicit positive tonnage.
        """
        source_present = False
        
        # Priority 1: Try Excel monthly tonnes milled
        if calculation_date is not None:
            try:
                excel_tonnes = self._get_excel_repo().get_monthly_value(calculation_date, "Tonnes Milled")
                if excel_tonnes and excel_tonnes > 0:
                    ore_tonnes = float(excel_tonnes)
                    source_present = True
            except Exception:
                pass
        
        # Priority 2: Use explicit ore_tonnes only if > 0
        if ore_tonnes is None or ore_tonnes <= 0:
            # No data from Excel or explicit positive tonnage → default to zero
            ore_tonnes = 0.0
            source_present = False

        ore_moisture_pct = self.get_constant('ore_moisture_percent', 3.4)
        ore_density = self.get_constant('ore_density', 2.7)
        ore_moisture_water = (ore_tonnes * (ore_moisture_pct / 100.0)) / ore_density
        return (ore_moisture_water, source_present)
    
    def calculate_tailings_retention(self, plant_consumption: float, calculation_date: date = None,
                                     manual_inputs: Optional[Dict] = None) -> float:
        """Water locked in tailings solids.
        Always auto-calculated: (Ore - Concentrate) × Tailings Moisture %.
        Uses TRP Excel ore/concentrate + DB tailings moisture, else zero.
        """
        if not calculation_date:
            return 0.0

        # Source ore tonnage from TRP Excel only; no synthetic constants
        try:
            ore_tonnes = self._get_excel_repo().get_monthly_value(calculation_date, "Tonnes Milled") or 0.0
        except Exception:
            ore_tonnes = 0.0

        # Concentrate tonnage from TRP Excel meter readings (PGM + Chromite)
        concentrate_tonnes = 0.0
        try:
            pgm_wet = self._get_excel_repo().get_monthly_value(calculation_date, "PGM Concentrate Wet tons dispatched") or 0
            chr_wet = self._get_excel_repo().get_monthly_value(calculation_date, "Chromite Concentrate Wet tons dispatched") or 0
            concentrate_tonnes = float(pgm_wet) + float(chr_wet)
        except Exception:
            concentrate_tonnes = 0.0

        tailings_dry_mass = max(ore_tonnes - concentrate_tonnes, 0.0)

        # Tailings moisture: Priority 1) DB monthly data, 2) Constant fallback
        tailings_moisture_pct = 0.0
        try:
            db_moisture = self.db.get_tailings_moisture_monthly(calculation_date.month, calculation_date.year)
            if db_moisture is not None:
                tailings_moisture_pct = max(float(db_moisture), 0.0) / 100.0
            else:
                # Fallback to constant if no DB data
                const_moisture = self.db.get_constant('tailings_moisture_pct')
                if const_moisture:
                    tailings_moisture_pct = max(float(const_moisture), 0.0) / 100.0
        except Exception:
            # Final fallback to constant
            try:
                const_moisture = self.db.get_constant('tailings_moisture_pct')
                if const_moisture:
                    tailings_moisture_pct = max(float(const_moisture), 0.0) / 100.0
            except Exception:
                tailings_moisture_pct = 0.0

        return tailings_dry_mass * tailings_moisture_pct
    
    def calculate_seepage_losses(self, calculation_date: date, skip_measurements: bool = False, preloaded_facilities: Optional[List[Dict]] = None) -> Tuple[float, float]:
        """Calculate seepage gains and losses at FACILITY LEVEL.
        
        NOTE: This is maintained for backward compatibility but seepage is now calculated
        per-facility in calculate_facility_balance() based on dam lining status and aquifer properties.
        Mine-level balance does NOT include seepage as an inflow source.
        
        Priority: 1) Database per-facility monthly input, 2) Zero fallback
        Returns: (seepage_gain, seepage_loss)
        """
        # Seepage methods were removed as seepage is now calculated automatically
        # based on facility properties (aquifer_gain_rate_pct, is_lined flag)
        # For backward compatibility, return zero for mine-level seepage
        return (0.0, 0.0)
    
    def calculate_returns_to_pit(self, calculation_date: date) -> float:
        """Calculate water returned to pit.
        Currently not tracked; default to zero.
        """
        return 0.0

    def calculate_plant_returns(self, calculation_date: date) -> float:
        """Calculate direct plant returns (internal plant recirculation).
        Typically netted within plant consumption; default to zero to avoid double-counting.
        """
        return 0.0
    
    def calculate_pump_transfers(self, calculation_date: date) -> Dict[str, float]:
        """Calculate inter-facility pump transfers (not in Excel - always empty)"""
        return {}
    
    def calculate_dust_suppression(self, calculation_date: date, ore_tonnes: float = None,
                                   manual_inputs: Optional[Dict] = None) -> float:
        """Dust suppression water use.
        Always auto-calculated: Ore Tonnes × Dust Suppression Rate (from settings).
        Priority: 1) Measurements (DB), 2) Ore tonnage estimate (TRP Excel or parameter).
        """
        # Measurements (daily/monthly) by type
        dust_water = self.db.execute_query(
            """
            SELECT SUM(volume) as total FROM measurements
            WHERE measurement_date = ? AND measurement_type = 'dust_suppression'
            """,
            (calculation_date,)
        )
        if dust_water and dust_water[0]['total']:
            return float(dust_water[0]['total'])

        # Auto-calculate from ore tonnage and dust suppression rate
        ore_val = 0.0
        if ore_tonnes is not None and ore_tonnes > 0:
            ore_val = ore_tonnes
        else:
            try:
                excel_ore = self._get_excel_repo().get_monthly_value(calculation_date, "Tonnes Milled")
                ore_val = float(excel_ore or 0.0)
            except Exception:
                ore_val = 0.0

        dust_rate = self.get_constant('dust_suppression_rate', 0.02)
        return ore_val * dust_rate
    
    # ==================== OUTFLOWS ====================
    
    def calculate_plant_consumption(self, ore_tonnes: float = None, calculation_date: date = None,
                                   fresh_water_available: float = None, tsf_return: float = None) -> float:
        """
        Calculate plant water consumption (gross water circulating through plant).
        
        SCIENTIFICALLY CORRECT APPROACH:
        ================================
        When actual water measurements exist:
            Gross Plant = Fresh Water Available + TSF Return
            
        Fresh water available includes:
            • Surface water, groundwater, underground dewatering
            • Rainfall, ore moisture, seepage gain
            • Minus: auxiliary uses (dust, mining, domestic)
            • Minus: environmental losses (evap from facilities, discharge)
        
        When no measurements exist (projections/estimates):
            Gross Plant = Ore tonnes × Water per tonne
            
        The water_per_tonne constant represents the total water:ore ratio
        needed for processing, which INCLUDES recycling. It's only used
        when actual water measurements are unavailable.
        
        Returns: Gross plant consumption (m³) - total water circulating in plant
        """
        # If we have actual water measurements, use mass balance approach
        if fresh_water_available is not None and tsf_return is not None:
            # Gross = Fresh makeup + Recycled water
            return fresh_water_available + tsf_return
        
        # Fallback: estimate from ore tonnage (for projections/when no measurements)
        if ore_tonnes is None:
            ore_tonnes = 0.0
        
        water_per_tonne = self.get_constant('mining_water_per_tonne', 0.0)
        consumption = ore_tonnes * water_per_tonne
        
        return consumption
    
    def calculate_tsf_return(self, plant_consumption: float, calculation_date: date = None) -> float:
        """Calculate TSF return water (recycled water from tailings back to plant).

        Priority:
        1) DB monthly entry (tsf_return_monthly)
        2) Estimated % of plant consumption
        """
        if calculation_date is not None:
            try:
                month_start = date(calculation_date.year, calculation_date.month, 1)
                rows = self.db.execute_query(
                    """
                    SELECT tsf_return_m3
                    FROM tsf_return_monthly
                    WHERE month_start = ?
                    LIMIT 1
                    """,
                    (month_start,)
                )
                if rows and rows[0].get('tsf_return_m3'):
                    return float(rows[0]['tsf_return_m3'])
            except Exception:
                pass

        return_percentage = self.get_constant('tsf_return_percentage', 36.0) / 100.0
        return plant_consumption * return_percentage

    def _get_measured_tailings_density(self, calculation_date: date) -> Optional[float]:
        """Return measured tailings/slurry density (not in Excel - always None)"""
        return None
    
    def calculate_evaporation_loss(self, calculation_date: date, preloaded_facilities: Optional[List[Dict]] = None) -> float:
        """Calculate evaporation losses using monthly rate.
        Priority: 1) Per-facility DB dashboard entries, 2) Global evaporation_rates table (year-aware), 3) Extended Excel
        Caps per-facility evaporation so it cannot exceed available volume.
        """
        month = calculation_date.month
        year = calculation_date.year
        
        # Get surface area of all storage facilities
        facilities = preloaded_facilities if preloaded_facilities is not None else self.db.get_storage_facilities()
        total_evap_volume = 0.0
        
        for f in facilities:
            facility_id = f.get('facility_id')
            surface_area = f.get('surface_area', 0) or 0.0
            current_vol = f.get('current_volume', 0.0) or 0.0
            evap_flag = f.get('evap_active', 1)
            
            if evap_flag in (None, ''):
                evap_flag = 1
            if int(evap_flag) != 1 or surface_area <= 0:
                continue
            
            # Priority 1: Per-facility DB dashboard entry
            facility_evap_mm = self.db.get_facility_evaporation_monthly(facility_id, month, year)
            
            if facility_evap_mm > 0:
                evap_volume = (facility_evap_mm / 1000.0) * surface_area
                # Clamp evaporation to available water volume in the facility
                total_evap_volume += min(evap_volume, current_vol)
            else:
                # Priority 2: Global evaporation_rates table (zone-based, year-aware)
                evap_mm = self.db.get_regional_evaporation_monthly(month, year=year)
                if evap_mm and evap_mm > 0:
                    evap_volume = (evap_mm / 1000.0) * surface_area
                    total_evap_volume += min(evap_volume, current_vol)
        
        return total_evap_volume
    
    def calculate_discharge(self, calculation_date: date, manual_inputs: Optional[Dict] = None) -> float:
        """Controlled discharge/releases.
        Priority: 1) Manual monthly input, 2) Measurements, 3) Zero.
        """
        month_start = date(calculation_date.year, calculation_date.month, 1)
        if manual_inputs is None:
            manual_inputs = self.db.get_monthly_manual_inputs(month_start)

        manual_val = manual_inputs.get('discharge_m3') if manual_inputs else None
        if manual_val is not None:
            return float(manual_val or 0.0)

        discharge_rows = self.db.execute_query(
            """
            SELECT SUM(volume) as total FROM measurements
            WHERE measurement_date = ? AND measurement_type = 'discharge'
            """,
            (calculation_date,)
        )
        if discharge_rows and discharge_rows[0]['total']:
            return float(discharge_rows[0]['total'])

        return 0.0
    
    def calculate_total_outflows(self, calculation_date: date,
                                 ore_tonnes: float = None,
                                 skip_measurements: bool = False,
                                 preloaded_facilities: Optional[List[Dict]] = None,
                                 fresh_water_to_plant: float = None) -> Dict[str, float]:
        """
        Calculate total outflows with extended Excel support.
        
        WATER FLOW EXPLANATION:
        ═══════════════════════
        
        Plant Consumption (Gross): Total water circulating through plant processes
          ├─ Includes: Fresh water + Recycled water (TSF return)
          ├─ Used for: Ore grinding, flotation, concentrate filtering
          └─ Calculation: When actual measurements exist:
                           Gross = Fresh water to plant + TSF return
                         When estimating (projections):
                           Gross = Ore tonnes × Water per tonne
        
        Plant Consumption (Net): Fresh water actually consumed by plant
          ├─ Formula: Gross - TSF Return
          └─ This is the \"new\" water the plant needs
        
        COMPONENT RELATIONSHIPS:
        ────────────────────────
        
        Components INCLUDED in Plant Consumption:
          • Dust suppression (included in plant operations)
          • Mining consumption (included in plant operations)
          • Domestic consumption (included in overall site water use)
          • Product moisture (water locked in concentrate - part of plant output)
          • Tailings retention (water locked in tailings - part of plant output)
        
        Components SEPARATE from Plant Consumption:
          • Evaporation (environmental loss from storage facilities)
          • Discharge (controlled release to environment)
          • Seepage loss (shown separately but affects storage change, not total outflows)
        
        TOTAL OUTFLOWS:
        ───────────────
        Total = Net Plant + Evaporation + Discharge
        
        Note on Seepage:
          Seepage loss is NOT included in total outflows because it's already
          captured in the storage change calculation. When facilities lose water
          to seepage, their volumes decrease, which is reflected in storage change.
          Including seepage in both total outflows AND storage change would
          double-count this loss.
        
        Why net instead of gross?
          • Gross includes recycled water (TSF return)
          • TSF return is counted as INFLOW
          • Using gross would double-count the recycled water
          • Net represents actual fresh water consumption
        
        Returns breakdown by category matching legacy model
        """
        month_start = date(calculation_date.year, calculation_date.month, 1)
        manual_inputs = self.db.get_monthly_manual_inputs(month_start)

        # Calculate TSF return FIRST (needed for plant consumption calculation)
        # Use ore-based estimate for initial calculation
        plant_consumption_estimate = self.calculate_plant_consumption(ore_tonnes=ore_tonnes)
        tsf_return = self.calculate_tsf_return(plant_consumption_estimate, calculation_date)
        
        # Calculate plant consumption (gross water circulation)
        # If we have fresh_water_to_plant, use mass balance approach
        # Abstraction to plant not tracked without extended Excel; assume 0
        abstraction_to_plant = 0.0

        if fresh_water_to_plant is not None:
            # Gross = fresh_to_plant + TSF return
            plant_consumption = fresh_water_to_plant + tsf_return
        else:
            # Fallback to ore-based calculation (gross estimated from tonnes)
            # Add TSF return to reflect operational feed
            plant_consumption = plant_consumption_estimate + tsf_return
        
        # Calculate environmental losses from storage facilities
        evaporation = self.calculate_evaporation_loss(calculation_date, preloaded_facilities=preloaded_facilities)

        # Discharge from manual inputs or measurements
        discharge = self.calculate_discharge(calculation_date, manual_inputs=manual_inputs)

        # Additional categories (for detailed reporting - included in plant consumption)
        tailings_retention = self.calculate_tailings_retention(plant_consumption, calculation_date, manual_inputs=manual_inputs)
        _, seepage_loss = self.calculate_seepage_losses(calculation_date,
                                skip_measurements=skip_measurements,
                                preloaded_facilities=preloaded_facilities)

        # Dust suppression - check Excel first (part of plant operations)
        dust_suppression = self.calculate_dust_suppression(calculation_date, ore_tonnes=ore_tonnes, manual_inputs=manual_inputs)

        # Mining & domestic consumption - manual inputs or measurements; zero if missing
        mining_use = float(manual_inputs.get('mining_consumption_m3', 0.0) or 0.0)
        domestic_use = float(manual_inputs.get('domestic_consumption_m3', 0.0) or 0.0)

        if mining_use == 0.0:
            mining_rows = self.db.execute_query(
                """
                SELECT SUM(volume) as total FROM measurements
                WHERE measurement_date = ? AND measurement_type = 'mining_consumption'
                """,
                (calculation_date,)
            )
            if mining_rows and mining_rows[0]['total']:
                mining_use = float(mining_rows[0]['total'])

        if domestic_use == 0.0:
            domestic_rows = self.db.execute_query(
                """
                SELECT SUM(volume) as total FROM measurements
                WHERE measurement_date = ? AND measurement_type = 'domestic_consumption'
                """,
                (calculation_date,)
            )
            if domestic_rows and domestic_rows[0]['total']:
                domestic_use = float(domestic_rows[0]['total'])

        # Product moisture (concentrate moisture) - PRIORITY: Meter Readings → Production sheet
        concentrate_tonnes = None
        concentrate_moisture_pct = None
        
        try:
            # PRIORITY 1: Meter Readings (PGM + Chromite)
            # Note: Column headers may have trailing spaces
            pgm_wet = self._get_excel_repo().get_monthly_value(calculation_date, "PGM Concentrate Wet tons dispatched")
            # Try with and without trailing space
            pgm_moist = self._get_excel_repo().get_monthly_value(calculation_date, "PGM Concentrate Moisture")
            if not pgm_moist:
                pgm_moist = self._get_excel_repo().get_monthly_value(calculation_date, "PGM Concentrate Moisture ")
            
            chr_wet = self._get_excel_repo().get_monthly_value(calculation_date, "Chromite Concentrate Wet tons dispatched")
            # Try with and without trailing space
            chr_moist = self._get_excel_repo().get_monthly_value(calculation_date, "Chromite Concentrate Moisture")
            if not chr_moist:
                chr_moist = self._get_excel_repo().get_monthly_value(calculation_date, "Chromite Concentrate Moisture ")
            
            if pgm_wet and chr_wet:
                concentrate_tonnes = float(pgm_wet) + float(chr_wet)
            
            if pgm_wet and pgm_moist and chr_wet and chr_moist:
                total_wet = float(pgm_wet) + float(chr_wet)
                if total_wet > 0:
                    weighted_moist = (float(pgm_wet) * float(pgm_moist) + float(chr_wet) * float(chr_moist)) / total_wet
                    concentrate_moisture_pct = weighted_moist / 100.0  # Excel stores as %, convert to decimal
        except Exception:
            pass
        
        # No extended Excel fallback; default to zero when missing
        if concentrate_tonnes is None:
            concentrate_tonnes = 0.0
        if concentrate_moisture_pct is None:
            concentrate_moisture_pct = 0.0

        # Product moisture calculation (wet basis):
        # Water (tonnes) = Wet mass (tonnes) × (moisture% / 100)
        # Water (m³) = Water (tonnes) / water_density (t/m³)
        # Assuming water density = 1.0 t/m³ for moisture content
        water_density = 1.0  # tonnes per m³
        product_moisture_tonnes = (concentrate_tonnes * concentrate_moisture_pct) if concentrate_tonnes > 0 else 0.0
        product_moisture = product_moisture_tonnes / water_density  # Convert to m³

        # Net plant consumption (fresh water actually consumed by main plant)
        # Net = Fresh_to_plant (do not count abstraction or TSF as fresh)
        net_plant_consumption = fresh_water_to_plant if fresh_water_to_plant is not None else max(0.0, plant_consumption - tsf_return - abstraction_to_plant)

        # TOTAL OUTFLOWS: Only actual water losses leaving the mine site
        # ═════════════════════════════════════════════════════════════════
        # 
        # Components INCLUDED in total (water permanently leaving site):
        #   • Mining Consumption: Water used in underground operations
        #   • Domestic Consumption: Personnel and site water use
        #   • Dust Suppression: Ore handling dust control
        #   • Discharge: Water released to environment
        #   • Product Moisture: Water shipped off-site with concentrate
        #   • Tailings Retention: Water locked in tailings solids
        # 
        # Components EXCLUDED from total (not external losses):
        #   • Evaporation: Captured in storage change (dam volume decrease)
        #   • Seepage Loss: Captured in storage change (dam volume decrease)
        #   • Plant Consumption Gross: Superseded by detailed components above
        #   • Plant Consumption Net: OLD metric, replaced by detailed breakdown
        #   • Abstraction to Plant: Internal transfer (not fresh water loss)
        # 
        # WHY exclude evaporation & seepage from outflows total?
        #   When water evaporates from a dam or seeps through lining:
        #   1. Dam volume decreases → Captured in storage change (ΔStorage)
        #   2. If we ALSO count it in outflows, we double-count the loss
        #   3. Mass balance: Fresh IN = Outflows + ΔStorage + Error
        #   4. Storage change already includes evaporation/seepage effects
        # 
        # MASS BALANCE EQUATION:
        #   Fresh Inflows - (Mining + Domestic + Dust + Discharge + 
        #   Product Moisture + Tailings) - ΔStorage = Balance Error
        # 
        # Note: ΔStorage is calculated per-facility and includes evaporation
        # and seepage effects automatically through measured volume changes
        total = mining_use + domestic_use + dust_suppression + discharge + product_moisture + tailings_retention

        outflows = {
            'plant_consumption_gross': plant_consumption,
            'plant_consumption_net': net_plant_consumption,
            'evaporation': evaporation,
            'discharge': discharge,
            'tailings_retention': tailings_retention,  # Detail component (part of net plant)
            'seepage_loss': seepage_loss,  # Environmental loss (affects storage, not in total)
            'dust_suppression': dust_suppression,  # Auxiliary use (added to total)
            'mining_consumption': mining_use,  # Auxiliary use (added to total)
            'domestic_consumption': domestic_use,  # Auxiliary use (added to total)
            'product_moisture': product_moisture,  # Detail component (part of net plant)
            'abstraction_to_plant': abstraction_to_plant,  # Operational feed from storage (not fresh)
            'total': total  # Net plant + aux uses + evap + discharge (no double-counting)
        }
        return outflows
    
    # ==================== WATER BALANCE ====================
    
    def calculate_storage_change(self, calculation_date: date,
                                 skip_measurements: bool = False,
                                 preloaded_facilities: Optional[List[Dict]] = None) -> Dict[str, float]:
        """Calculate storage change across all facilities.
        Uses DB measurements/inputs; no extended Excel dependency.
        Returns opening volumes, closing volumes, and net change
        """
        facilities = preloaded_facilities if preloaded_facilities is not None else self.db.get_storage_facilities()
        
        total_opening = 0.0
        total_closing = 0.0
        facility_changes = {}
        
        # Preload rainfall_mm and evaporation_mm once (used per facility)
        month = calculation_date.month
        evap_rate_rows = self.db.execute_query(
            "SELECT evaporation_mm FROM evaporation_rates WHERE month = ?",
            (month,)
        )
        preloaded_evap_mm = evap_rate_rows[0]['evaporation_mm'] if evap_rate_rows else 0.0
        
        rainfall_rows = self.db.execute_query(
            "SELECT rainfall_mm FROM measurements WHERE measurement_date = ? AND measurement_type = 'rainfall'",
            (calculation_date,)
        )
        if rainfall_rows:
            total_rainfall_mm = sum(r['rainfall_mm'] for r in rainfall_rows if r.get('rainfall_mm'))
        else:
            # Fallback to zero when no measurement rows
            total_rainfall_mm = 0.0

        facility_measurements_map = {}
        
        for facility in facilities:
            facility_id = facility['facility_id']
            facility_code = facility['facility_code']
            facility_capacity = facility.get('total_capacity', 0)
            facility_surface_area = facility.get('surface_area', 0)

            # Database-driven path only
            opening_vol = facility.get('current_volume', 0.0)

            facility_balance = self.calculate_facility_balance(
                facility_id, calculation_date,
                preloaded_facility=facility,
                preloaded_rainfall_mm=total_rainfall_mm,
                preloaded_evap_mm=preloaded_evap_mm,
                preloaded_facility_measurements=facility_measurements_map if not skip_measurements else {}
            )
            closing_vol = facility_balance['closing_volume'] if facility_balance else opening_vol
            
            inflow_manual = float(facility_balance.get('facility_inflow_m3', 0.0) or 0.0) if facility_balance else 0.0
            outflow_manual = float(facility_balance.get('facility_outflow_m3', 0.0) or 0.0) if facility_balance else 0.0
            rain = float(facility_balance.get('rainfall_volume', 0.0) or 0.0) if facility_balance else 0.0
            evap = float(facility_balance.get('evaporation', 0.0) or 0.0) if facility_balance else 0.0
            abstr = float(facility_balance.get('facility_abstraction_m3', 0.0) or 0.0) if facility_balance else 0.0
            
            data_source = 'Database'
            
            change = closing_vol - opening_vol
            
            total_opening += opening_vol
            total_closing += closing_vol
            
            # Record details for transparency
            facility_changes[facility_code] = {
                'opening': opening_vol,
                'closing': closing_vol,
                'change': change,
                'source': data_source,
                'drivers': {
                    'inflow_manual': inflow_manual,
                    'outflow_manual': outflow_manual,
                    'rainfall': rain,
                    'evaporation': evap,
                    'abstraction': abstr,
                    # Automatic seepage factors (facility-level only)
                    'seepage_gain': float(facility_balance.get('seepage_gain', 0.0) or 0.0) if facility_balance else 0.0,
                    'seepage_loss': float(facility_balance.get('seepage_loss', 0.0) or 0.0) if facility_balance else 0.0
                }
            }
        
        net_change = total_closing - total_opening
        
        return {
            'total_opening_volume': total_opening,
            'total_closing_volume': total_closing,
            'net_storage_change': net_change,
            'facilities': facility_changes
        }
    
    def calculate_closure_error(self, inflows: float, outflows: float, 
                               storage_change: float) -> Tuple[float, float]:
        """Calculate water balance closure error (scientifically correct).
        
        Formula: Error = Fresh Inflows - Outflows - ΔStorage
        
        IMPORTANT: 'inflows' should be FRESH water only, excluding recycled water (TSF return).
        This represents the mass balance of new water entering vs leaving/stored.
        
        Error should be close to zero for a well-balanced system.
        Typical acceptable range: < 10% of fresh inflows
        
        Returns: (absolute_error, percent_error)
        """
        # Water balance formula: Fresh IN = OUT + ΔStorage + Error
        # Therefore: Error = Fresh IN - OUT - ΔStorage
        absolute_error = inflows - outflows - storage_change
        
        # Percentage error relative to fresh inflows
        percent_error = (abs(absolute_error) / inflows * 100.0) if inflows > 0 else 0.0
        
        return (absolute_error, percent_error)
    
    def calculate_water_balance(self, calculation_date: date, 
                                ore_tonnes: float = None) -> Dict:
        """
        Calculate complete water balance for a date (FULL EXCEL PARITY)
        Returns all components, closure error, and net balance
        """
        # CRITICAL: Clear capacity warnings at start of calculation
        # Prevents warnings from previous calculations accumulating in the list
        # Each calculation starts fresh with its own validation warnings
        self.clear_capacity_warnings()
        
        start_time = time.perf_counter()
        
        # Check cache first (performance optimization)
        ore_key = ore_tonnes if ore_tonnes is not None else 0.0
        cache_key = (calculation_date, ore_key)
        if cache_key in self._balance_cache:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.performance(f"calculate_water_balance (cached) for {calculation_date}", elapsed)
            return self._balance_cache[cache_key].copy()
        
        # No longer optimize for empty days - we now use Excel time-series
        # which always has data, not DB measurements
        empty_day = False

        # If ore_tonnes not explicitly provided, prefer Excel Tonnes Milled
        # for this month before falling back to zero (no synthetic defaults).
        ore_val = ore_tonnes
        if ore_val is None and calculation_date is not None:
            try:
                excel_tonnes = self._get_excel_repo().get_monthly_value(calculation_date, "Tonnes Milled")
            except Exception:
                excel_tonnes = 0.0
            if excel_tonnes and excel_tonnes > 0:
                ore_val = float(excel_tonnes)

        # Final fallback to zero when no explicit or Excel tonnes provided
        # (aligns with user preference for zero-defaults when data is missing)
        if ore_val is None:
            ore_val = 0.0

        # Calculate all components (skip measurement queries if empty day)
        # Prefetch static datasets once per calculation to avoid repeated queries
        preloaded_facilities = self.db.get_storage_facilities()
        preloaded_sources = self.db.get_water_sources(active_only=True)

        inflows_raw = self.calculate_total_inflows(
            calculation_date,
            ore_val,
            skip_measurements=empty_day,
            preloaded_sources=preloaded_sources,
            preloaded_facilities=preloaded_facilities
        )
        
        # Calculate fresh water available to plant
        # This is all inflows EXCEPT TSF return (which is recycled)
        fresh_water_total = (
            inflows_raw.get('surface_water', 0) +
            inflows_raw.get('groundwater', 0) +
            inflows_raw.get('underground', 0) +
            inflows_raw.get('rainfall', 0) +
            inflows_raw.get('ore_moisture', 0) +
            inflows_raw.get('seepage_gain', 0)
        )
        
        # Subtract auxiliary uses (dust, mining, domestic) from fresh water
        # These are separate from main plant processing
        # We need to get these values first
        month_start = date(calculation_date.year, calculation_date.month, 1)
        manual_inputs = self.db.get_monthly_manual_inputs(month_start)

        dust_suppression_prelim = self.calculate_dust_suppression(calculation_date, ore_tonnes=ore_val, manual_inputs=manual_inputs) or 0.0

        mining_use_prelim = float(manual_inputs.get('mining_consumption_m3', 0.0) or 0.0)
        domestic_use_prelim = float(manual_inputs.get('domestic_consumption_m3', 0.0) or 0.0)

        if mining_use_prelim == 0.0:
            mining_rows = self.db.execute_query(
                """
                SELECT SUM(volume) as total FROM measurements
                WHERE measurement_date = ? AND measurement_type = 'mining_consumption'
                """,
                (calculation_date,)
            )
            if mining_rows and mining_rows[0]['total']:
                mining_use_prelim = float(mining_rows[0]['total'])

        if domestic_use_prelim == 0.0:
            domestic_rows = self.db.execute_query(
                """
                SELECT SUM(volume) as total FROM measurements
                WHERE measurement_date = ? AND measurement_type = 'domestic_consumption'
                """,
                (calculation_date,)
            )
            if domestic_rows and domestic_rows[0]['total']:
                domestic_use_prelim = float(domestic_rows[0]['total'])

        auxiliary_uses = dust_suppression_prelim + mining_use_prelim + domestic_use_prelim
        fresh_water_to_plant = fresh_water_total - auxiliary_uses
        
        # Calculate automatic pump transfers between facilities
        pump_transfers = self.pump_transfer_engine.calculate_pump_transfers(calculation_date)
        # Auto-apply to database if feature flag enabled (transactional, idempotent)
        # WHY here? Applying before outflows/storage ensures evaporation caps
        # and facility-level balances use the updated opening volumes.
        try:
            if config.get('features.auto_apply_pump_transfers', False):
                applied = self.db.apply_pump_transfers(
                    calculation_date,
                    pump_transfers,
                    user=config.get_current_user()
                )
                if applied > 0:
                    # Refresh preloaded facilities so subsequent calculations use updated volumes
                    preloaded_facilities = self.db.get_storage_facilities(use_cache=False)
                    logger.info(f"Auto-applied {applied} pump transfer(s) for {calculation_date}")
        except Exception as e:
            # Safety: do not fail balance if transfer application encounters an issue
            logger.error(f"Auto-apply pump transfers failed: {e}")
        
        outflows = self.calculate_total_outflows(
            calculation_date,
            ore_val,
            skip_measurements=empty_day,
            preloaded_facilities=preloaded_facilities,
            fresh_water_to_plant=fresh_water_to_plant
        )

        # Build inflows including TSF:
        # - If a monthly TSF override exists, calculate_total_inflows has
        #   already populated inflows_raw['tsf_return'] with that value.
        # - If no monthly override exists, we derive TSF as the difference
        #   between gross and net plant consumption so that recycling is
        #   still credited as an inflow.
        inflows = inflows_raw.copy()
        if inflows.get('tsf_return', 0.0) <= 0.0:
            tsf_return_auto = max(
                0.0,
                outflows.get('plant_consumption_gross', 0.0) - outflows.get('plant_consumption_net', 0.0)
            )
            inflows['tsf_return'] = tsf_return_auto
            inflows['total'] += tsf_return_auto
        
        # Calculate storage change
        storage_change_data = self.calculate_storage_change(
            calculation_date,
            skip_measurements=empty_day,
            preloaded_facilities=preloaded_facilities
        )
        net_storage_change = storage_change_data['net_storage_change']
        
        # Calculate fresh inflows (excluding recycled TSF return)
        fresh_inflows = inflows['total'] - inflows.get('tsf_return', 0.0)
        
        # DATA QUALITY: Flag when fresh inflows are very low
        # When fresh_inflows < 100 m³, the closure error % becomes unreliable
        # (e.g., 10 m³ error out of 50 m³ inflows = 20% error, but in absolute terms is minor)
        # This flag helps UI/alerts distinguish measurement noise from real issues
        has_low_fresh_inflows = fresh_inflows < 100.0
        
        # Calculate closure error using FRESH inflows only (scientifically correct)
        # TSF return is recycled water, not new water entering the system
        # Water Balance: Fresh IN = Outflows + Storage Change + Closure Error
        closure_error_abs, closure_error_pct = self.calculate_closure_error(
            fresh_inflows, outflows['total'], net_storage_change
        )
        
        # Net balance (for operational planning) - uses total inflows including recycling
        net_balance = inflows['total'] - outflows['total']
        
        # Get current storage levels (using Excel volumes for this date if available)
        storage_stats = self._get_storage_statistics(preloaded_facilities=preloaded_facilities, calculation_date=calculation_date)
        
        # Add closing volume to storage stats (critical for Days of Operation)
        storage_stats['closing'] = storage_change_data.get('total_closing_volume', storage_stats['current_volume'])
        storage_stats['capacity'] = storage_stats['total_capacity']  # Alias for compatibility
        
        balance = {
            'calculation_date': calculation_date,
            'inflows': inflows,
            'outflows': outflows,
            'net_balance': net_balance,
            'storage_change': storage_change_data,
            'closure_error_m3': closure_error_abs,
            'closure_error_percent': closure_error_pct,
            'has_low_fresh_inflows': has_low_fresh_inflows,  # Data quality indicator: True if fresh_inflows < 100 m³
            'storage': storage_stats,
            'ore_processed': ore_val,
            'balance_status': 'CLOSED' if closure_error_pct < 5.0 else 'OPEN',
            'pump_transfers': pump_transfers
        }
        
        # Cache the result (performance optimization)
        self._balance_cache[cache_key] = balance.copy()
        
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.performance(f"calculate_water_balance (computed) for {calculation_date}", elapsed)
        
        return balance

    def _is_empty_day(self, calculation_date: date) -> bool:
        """Return True if there are zero measurement rows for the date."""
        rows = self.db.execute_query(
            "SELECT 1 FROM measurements WHERE measurement_date = ? LIMIT 1",
            (calculation_date,)
        )
        return len(rows) == 0
    
    def _get_storage_statistics(self, preloaded_facilities: Optional[List[Dict]] = None, calculation_date: Optional[date] = None) -> Dict:
        """Get current storage statistics using database values only."""
        facilities = preloaded_facilities if preloaded_facilities is not None else self.db.get_storage_facilities()
        
        total_capacity = sum(f.get('total_capacity', 0) for f in facilities)
        current_volume = sum(f.get('current_volume', 0) for f in facilities)
        
        utilization = (current_volume / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            'total_capacity': total_capacity,
            'current_volume': current_volume,  # Opening balance
            'opening': current_volume,  # Alias for clarity
            'available_capacity': total_capacity - current_volume,
            'utilization_percent': utilization
        }
    
    def calculate_facility_balance(self, facility_id: int,
                                   calculation_date: date,
                                   preloaded_facility: Optional[Dict] = None,
                                   preloaded_rainfall_mm: Optional[float] = None,
                                   preloaded_evap_mm: Optional[float] = None,
                                   preloaded_facility_measurements: Optional[Dict[int, Dict[str, float]]] = None) -> Dict:
        """
        Calculate water balance for a specific storage facility (EXCEL PARITY)
        Includes per-facility rainfall and evaporation
        """
        # Use preloaded facility metadata if supplied to reduce query count
        facility = preloaded_facility if preloaded_facility is not None else self.db.get_storage_facility(facility_id)
        if not facility:
            return None
        
        # Per-facility monthly inflows/outflows/abstraction from dashboard DB
        month = calculation_date.month
        year = calculation_date.year
        facility_inflow_m3 = self.db.get_facility_inflow_monthly(facility_id, month, year)
        facility_outflow_m3 = self.db.get_facility_outflow_monthly(facility_id, month, year)
        facility_abstraction_m3 = self.db.get_facility_abstraction_monthly(facility_id, month, year)
        
        inflows = facility_inflow_m3
        outflows = facility_outflow_m3 + facility_abstraction_m3
        
        # Optionally add legacy measurements (if preloaded or from DB)
        if preloaded_facility_measurements and facility_id in preloaded_facility_measurements:
            mtypes = preloaded_facility_measurements[facility_id]
            inflows += sum(mtypes.get(mt, 0.0) for mt in ['facility_inflow','pump_inflow','transfer_in'])
            outflows += sum(mtypes.get(mt, 0.0) for mt in ['facility_outflow','pump_outflow','transfer_out','discharge'])
        else:
            measurements = self.db.execute_query(
                """
                SELECT measurement_type, SUM(volume) as total_volume
                FROM measurements
                WHERE facility_id = ? AND measurement_date = ?
                GROUP BY measurement_type
                """,
                (facility_id, calculation_date)
            )
            for m in measurements:
                if m['measurement_type'] in ['facility_inflow', 'pump_inflow', 'transfer_in']:
                    inflows += m['total_volume'] or 0
                elif m['measurement_type'] in ['facility_outflow', 'pump_outflow', 'transfer_out', 'discharge']:
                    outflows += m['total_volume'] or 0
        
        # Regional rainfall and evaporation (apply to all facilities in the area)
        # Guard against None to avoid float * NoneType errors when applying rainfall/evap
        # IMPORTANT: If surface_area is 0.0 (from DB or None), rainfall/evaporation calculations
        # will result in 0 volume, which is expected—some facilities don't have measured surface area.
        # This is NOT an error and should NOT block calculation; it just means no rainfall/evap applied.
        surface_area = facility.get('surface_area')
        if surface_area is None:
            surface_area = 0.0
        # Respect evap_active flag: if disabled, skip rainfall/evap for this facility
        evap_flag = facility.get('evap_active', 1)
        if evap_flag in (None, ''):
            evap_flag = 1
        evap_enabled = int(evap_flag) == 1
        
        # Use regional rainfall (applies to all facilities, year-aware)
        rainfall_mm = self.db.get_regional_rainfall_monthly(month, calculation_date.year)
        if not rainfall_mm or rainfall_mm < 0:
            rainfall_mm = 0.0
        
        # Rainfall volume on this facility
        rainfall_volume = (rainfall_mm / 1000.0) * surface_area if evap_enabled else 0.0
        inflows += rainfall_volume
        
        # Regional evaporation (applies to all facilities)
        evap_loss = 0.0
        
        if evap_enabled and surface_area > 0:
            # Use year-aware regional evaporation
            regional_evap_mm = self.db.get_regional_evaporation_monthly(month, year=calculation_date.year)
            if regional_evap_mm and regional_evap_mm > 0:
                evap_loss = (regional_evap_mm / 1000.0) * surface_area
                # Cap evaporation so it cannot exceed current available volume
                current_vol = facility.get('current_volume', 0.0) or 0.0
                evap_loss = min(evap_loss, current_vol)
        
        outflows += evap_loss
        
        # Per-facility seepage loss (Excel: seepage as % of volume)
        # Loss rate depends on dam lining status:
        # - Lined dams: 0.1% per month (minimal loss)
        # - Unlined dams: 0.5% per month (natural seepage)
        is_lined = facility.get('is_lined', 0)
        if is_lined:
            seepage_loss_rate_pct = self.get_constant('lined_seepage_rate_pct', 0.1) / 100.0
        else:
            seepage_loss_rate_pct = self.get_constant('unlined_seepage_rate_pct', 0.5) / 100.0
        
        current_vol = facility.get('current_volume', 0)
        facility_seepage_loss = current_vol * seepage_loss_rate_pct
        outflows += facility_seepage_loss
        
        # Per-facility seepage gain (water seeping INTO dam from aquifer)
        # Automatic calculation based on facility aquifer properties
        aquifer_gain_rate_pct = facility.get('aquifer_gain_rate_pct', 0.0)
        facility_seepage_gain = current_vol * aquifer_gain_rate_pct / 100.0
        inflows += facility_seepage_gain
        
        # Calculate balance (pre-clamp)
        net_balance_pre = inflows - outflows
        new_volume = current_vol + net_balance_pre
        
        # Ensure within capacity bounds
        capacity = facility.get('total_capacity', 0)
        if new_volume > capacity:
            overflow = new_volume - capacity
            new_volume = capacity
        else:
            overflow = 0.0
        
        if new_volume < 0:
            deficit = abs(new_volume)
            new_volume = 0.0
        else:
            deficit = 0.0
        # Recompute net balance after clamping so closing = opening + net_balance
        net_balance = new_volume - current_vol
        
        return {
            'facility_code': facility['facility_code'],
            'facility_name': facility['facility_name'],
            'calculation_date': calculation_date,
            'opening_volume': current_vol,
            'inflows': inflows,
            'outflows': outflows,
            'rainfall_volume': rainfall_volume,
            'evaporation': evap_loss,
            'seepage_gain': facility_seepage_gain,
            'seepage_loss': facility_seepage_loss,
            'facility_inflow_m3': facility_inflow_m3,
            'facility_outflow_m3': facility_outflow_m3,
            'facility_abstraction_m3': facility_abstraction_m3,
            'net_balance': net_balance,
            'closing_volume': new_volume,
            'capacity': capacity,
            'utilization_percent': (new_volume / capacity * 100) if capacity > 0 else 0,
            'overflow': overflow,
            'deficit': deficit
        }
    
    # ==================== PROJECTIONS ====================
    
    def calculate_monthly_projection(self, start_date: date, 
                                     months: int = 12,
                                     ore_tonnes_per_month: float = None) -> List[Dict]:
        """Project water balance for future months.
        Returns list of monthly balance snapshots (minimal keys required by tests).
        """
        projections: List[Dict] = []
        current_date = start_date
        ore_val = ore_tonnes_per_month if ore_tonnes_per_month is not None else 0.0
        for _ in range(months):
            # Use first day of month for projection consistency
            projection_date = date(current_date.year, current_date.month, 1)
            balance = self.calculate_water_balance(projection_date, ore_val)
            projections.append({
                'calculation_date': projection_date,
                'inflows': balance['inflows'],
                'outflows': balance['outflows'],
                'net_balance': balance['net_balance'],
                'storage': balance['storage']
            })
            # Advance one month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        return projections

    def calculate_deficit_surplus(self, calculation_date: date, ore_tonnes: float = None) -> Dict[str, float]:
        """Assess deficit/surplus status for a given date.
        Returns status, message, and key storage metrics.
        """
        balance = self.calculate_water_balance(calculation_date, ore_tonnes)
        net_balance = balance['net_balance']
        storage_available = balance['storage']['available_capacity']
        current_volume = balance['storage']['current_volume']
        if net_balance > 0:
            if net_balance > storage_available:
                status = 'overflow_risk'
                message = f"Surplus of {net_balance:,.0f} m³ exceeds available storage capacity"
            else:
                status = 'surplus'
                message = f"Surplus of {net_balance:,.0f} m³ can be stored"
        else:
            deficit = abs(net_balance)
            if deficit > current_volume:
                status = 'critical_deficit'
                message = f"Deficit of {deficit:,.0f} m³ exceeds current storage"
            else:
                status = 'deficit'
                message = f"Deficit of {deficit:,.0f} m³ within acceptable range"
        return {
            'status': status,
            'message': message,
            'net_balance': net_balance,
            'current_storage': current_volume,
            'available_capacity': storage_available
        }
    
    # ==================== KPI CALCULATIONS ====================
    
    def calculate_water_use_efficiency(self, calculation_date: date, 
                                       ore_tonnes: float = None) -> Dict[str, float]:
        """Calculate water use efficiency KPIs (Excel Dashboard metrics)
        Returns m³ water per tonne milled for various consumption categories
        """
        if ore_tonnes is None:
            ore_tonnes = 0.0
        
        if ore_tonnes == 0:
            return {
                'total_efficiency': 0.0,
                'plant_efficiency': 0.0,
                'mining_efficiency': 0.0,
                'overall_efficiency': 0.0
            }
        
        balance = self.calculate_water_balance(calculation_date, ore_tonnes)
        outflows = balance['outflows']
        
        # Total water consumed per tonne (Excel: Total Consumption / Tonnes Milled)
        total_consumption = (outflows.get('plant_consumption_net', 0) + 
                           outflows.get('mining_consumption', 0) + 
                           outflows.get('dust_suppression', 0))
        total_efficiency = total_consumption / ore_tonnes
        
        # Plant-specific efficiency
        plant_efficiency = outflows.get('plant_consumption_net', 0) / ore_tonnes
        
        # Mining-specific efficiency
        mining_efficiency = (outflows.get('mining_consumption', 0) + 
                           outflows.get('dust_suppression', 0)) / ore_tonnes
        
        # Overall efficiency (all outflows except returns)
        overall_consumption = outflows['total']
        overall_efficiency = overall_consumption / ore_tonnes
        
        return {
            'total_efficiency': total_efficiency,  # m³/tonne
            'plant_efficiency': plant_efficiency,  # m³/tonne
            'mining_efficiency': mining_efficiency,  # m³/tonne
            'overall_efficiency': overall_efficiency,  # m³/tonne
            'ore_tonnes': ore_tonnes,
            'total_consumption_m3': total_consumption
        }
    
    def calculate_recycling_ratio(self, calculation_date: date) -> Dict[str, float]:
        """Calculate water recycling ratios (Excel: TSF Return % + other recycling)
        Returns percentage of water recycled vs fresh water intake
        """
        balance = self.calculate_water_balance(calculation_date)
        
        inflows = balance['inflows']
        total_inflows = inflows['total']
        
        if total_inflows == 0:
            return {
                'tsf_recycling_ratio': 0.0,
                'total_recycling_ratio': 0.0,
                'fresh_water_ratio': 100.0
            }
        
        # TSF return recycling (Excel: TSF Return / Total Inflows)
        tsf_return = inflows.get('tsf_return', 0)
        tsf_recycling_ratio = (tsf_return / total_inflows) * 100.0
        
        # Total recycling (TSF + plant returns + returns to pit)
        total_recycled = (tsf_return + 
                         inflows.get('plant_returns', 0) + 
                         inflows.get('returns_to_pit', 0))
        total_recycling_ratio = (total_recycled / total_inflows) * 100.0
        
        # Fresh water ratio (surface + groundwater + underground)
        fresh_water = (inflows.get('surface_water', 0) + 
                      inflows.get('groundwater', 0) + 
                      inflows.get('underground', 0))
        fresh_water_ratio = (fresh_water / total_inflows) * 100.0
        
        return {
            'tsf_recycling_ratio': tsf_recycling_ratio,  # %
            'total_recycling_ratio': total_recycling_ratio,  # %
            'fresh_water_ratio': fresh_water_ratio,  # %
            'tsf_return_m3': tsf_return,
            'total_recycled_m3': total_recycled,
            'fresh_water_m3': fresh_water,
            'total_inflows_m3': total_inflows
        }
    
    def calculate_source_dependency(self, calculation_date: date) -> Dict[str, float]:
        """Calculate dependency on each water source type (Excel: Source Breakdown)
        Returns percentage breakdown of water sources
        """
        balance = self.calculate_water_balance(calculation_date)
        inflows = balance['inflows']
        total = inflows['total']
        
        if total == 0:
            return {
                'surface_water_pct': 0.0,
                'groundwater_pct': 0.0,
                'underground_pct': 0.0,
                'rainfall_pct': 0.0,
                'recycled_pct': 0.0,
                'other_pct': 0.0
            }
        
        # Calculate percentage for each source type
        surface_water_pct = (inflows.get('surface_water', 0) / total) * 100.0
        groundwater_pct = (inflows.get('groundwater', 0) / total) * 100.0
        underground_pct = (inflows.get('underground', 0) / total) * 100.0
        rainfall_pct = (inflows.get('rainfall', 0) / total) * 100.0
        
        recycled = (inflows.get('tsf_return', 0) + 
                   inflows.get('plant_returns', 0) + 
                   inflows.get('returns_to_pit', 0))
        recycled_pct = (recycled / total) * 100.0
        
        other = (inflows.get('ore_moisture', 0) + 
                inflows.get('seepage_gain', 0))
        other_pct = (other / total) * 100.0
        
        return {
            'surface_water_pct': surface_water_pct,
            'groundwater_pct': groundwater_pct,
            'underground_pct': underground_pct,
            'rainfall_pct': rainfall_pct,
            'recycled_pct': recycled_pct,
            'other_pct': other_pct,
            'total_inflows_m3': total,
            # Absolute values
            'surface_water_m3': inflows.get('surface_water', 0),
            'groundwater_m3': inflows.get('groundwater', 0),
            'underground_m3': inflows.get('underground', 0),
            'rainfall_m3': inflows.get('rainfall', 0),
            'recycled_m3': recycled,
            'other_m3': other
        }
    
    def calculate_storage_security(self, calculation_date: date) -> Dict[str, float]:
        """Calculate storage security metrics (Excel: Days Cover / Reserve)
        Returns days of operation covered by current storage
        """
        balance = self.calculate_water_balance(calculation_date)
        
        current_storage = balance['storage']['current_volume']
        total_outflows = balance['outflows']['total']
        
        # Assume monthly calculation, convert to daily
        days_in_month = 30  # Average
        daily_consumption = total_outflows / days_in_month if days_in_month > 0 else 0
        
        # Days of operation cover
        if daily_consumption > 0:
            days_cover = current_storage / daily_consumption
        else:
            days_cover = 999  # Effectively infinite if no consumption
        
        # Minimum operating level days
        facilities = self.db.get_storage_facilities()
        total_capacity = sum(f.get('total_capacity', 0) for f in facilities)
        min_operating_level_pct = self.get_constant('pump_stop_level', 20.0) / 100.0
        min_operating_volume = total_capacity * min_operating_level_pct
        
        if daily_consumption > 0:
            days_to_minimum = (current_storage - min_operating_volume) / daily_consumption
        else:
            days_to_minimum = 999
        
        # IMPORTANT: days_to_minimum can be negative if current_storage < min_operating_volume
        # Negative value indicates facility is ALREADY BELOW MINIMUM OPERATING LEVEL
        # The clamping to max(0, ...) in return dict hides the actual deficit
        # For alerts: check if calculated value was negative before clamping
        
        # Security status
        if days_cover >= 30:
            security_status = 'excellent'
        elif days_cover >= 14:
            security_status = 'good'
        elif days_cover >= 7:
            security_status = 'adequate'
        elif days_cover >= 3:
            security_status = 'low'
        else:
            security_status = 'critical'
        
        return {
            'days_cover': days_cover,
            'days_to_minimum': max(0, days_to_minimum),
            'is_below_minimum': days_to_minimum < 0,  # CRITICAL: Flag when already below minimum operating level
            'current_storage_m3': current_storage,
            'daily_consumption_m3': daily_consumption,
            'monthly_consumption_m3': total_outflows,
            'min_operating_volume_m3': min_operating_volume,
            'security_status': security_status,
            'storage_utilization_pct': balance['storage']['utilization_percent']
        }
    
    def calculate_compliance_metrics(self, calculation_date: date, preloaded_sources: Optional[List[Dict]] = None) -> Dict[str, any]:
        """Calculate compliance metrics (Excel: Authorized vs Actual abstractions)
        Checks water use against authorized limits
        """
        balance = self.calculate_water_balance(calculation_date)
        inflows = balance['inflows']
        
        # Get all active sources with authorized volumes
        sources = preloaded_sources if preloaded_sources is not None else self.db.get_water_sources(active_only=True)
        
        compliance_data = []
        total_authorized = 0.0
        total_actual = 0.0
        violations = 0
        
        source_rows = self.db.execute_query(
            """
            SELECT source_id, SUM(volume) as total
            FROM measurements
            WHERE measurement_date = ? AND measurement_type = 'inflow'
            GROUP BY source_id
            """,
            (calculation_date,)
        )
        source_actual_map = {r['source_id']: (r['total'] or 0.0) for r in source_rows}

        for source in sources:
            authorized_vol = source.get('authorized_volume', 0) or 0
            actual_vol = source_actual_map.get(source['source_id'], 0.0)
            
            # Compliance check
            if authorized_vol > 0:
                utilization_pct = (actual_vol / authorized_vol) * 100.0
                compliant = actual_vol <= authorized_vol
                
                if not compliant:
                    violations += 1
                
                compliance_data.append({
                    'source_code': source['source_code'],
                    'source_name': source['source_name'],
                    'authorized_m3': authorized_vol,
                    'actual_m3': actual_vol,
                    'utilization_pct': utilization_pct,
                    'compliant': compliant,
                    'variance_m3': actual_vol - authorized_vol
                })
                
                total_authorized += authorized_vol
                total_actual += actual_vol
        
        # Overall compliance
        if total_authorized > 0:
            overall_utilization = (total_actual / total_authorized) * 100.0
            overall_compliant = total_actual <= total_authorized
        else:
            overall_utilization = 0.0
            overall_compliant = True
        
        # Closure error compliance (should be < 5%)
        closure_error_pct = balance['closure_error_percent']
        closure_compliant = closure_error_pct < 5.0
        
        return {
            'overall_compliant': overall_compliant and closure_compliant,
            'total_authorized_m3': total_authorized,
            'total_actual_m3': total_actual,
            'overall_utilization_pct': overall_utilization,
            'violations_count': violations,
            'sources_checked': len(compliance_data),
            'closure_error_pct': closure_error_pct,
            'closure_compliant': closure_compliant,
            'source_details': compliance_data
        }
    
    def calculate_all_kpis(self, calculation_date: date, 
                          ore_tonnes: float = None) -> Dict:
        """Calculate all KPIs in one call (Excel: Dashboard aggregation)
        Returns comprehensive KPI dashboard data
        OPTIMIZED: Single balance calculation, all metrics derived from it
        """
        # Check KPI cache first
        ore_key = ore_tonnes if ore_tonnes is not None else 0.0
        cache_key = (calculation_date, ore_key)
        if cache_key in self._kpi_cache:
            return self._kpi_cache[cache_key].copy()
        
        # Calculate balance ONCE (previous version called it 6 times!)
        balance = self.calculate_water_balance(calculation_date, ore_tonnes)
        
        # Derive all metrics from the single balance calculation
        inflows = balance['inflows']
        outflows = balance['outflows']
        ore_processed = balance['ore_processed']
        
        # Water use efficiency (inline calculation)
        total_consumption = (outflows.get('plant_consumption_net', 0) + 
                           outflows.get('mining_consumption', 0) + 
                           outflows.get('dust_suppression', 0))
        efficiency = {
            'total_efficiency': total_consumption / ore_processed if ore_processed > 0 else 0,
            'plant_efficiency': outflows.get('plant_consumption_net', 0) / ore_processed if ore_processed > 0 else 0,
            'mining_efficiency': (outflows.get('mining_consumption', 0) + outflows.get('dust_suppression', 0)) / ore_processed if ore_processed > 0 else 0,
            'overall_efficiency': outflows['total'] / ore_processed if ore_processed > 0 else 0,
            'ore_tonnes': ore_processed,
            'total_consumption_m3': total_consumption
        }
        
        # Recycling ratio (inline calculation)
        total_inflows = inflows['total']
        tsf_return = inflows.get('tsf_return', 0)
        total_recycled = (tsf_return + inflows.get('plant_returns', 0) + inflows.get('returns_to_pit', 0))
        fresh_water = (inflows.get('surface_water', 0) + inflows.get('groundwater', 0) + inflows.get('underground', 0))
        recycling = {
            'tsf_recycling_ratio': (tsf_return / total_inflows * 100.0) if total_inflows > 0 else 0,
            'total_recycling_ratio': (total_recycled / total_inflows * 100.0) if total_inflows > 0 else 0,
            'fresh_water_ratio': (fresh_water / total_inflows * 100.0) if total_inflows > 0 else 0,
            'tsf_return_m3': tsf_return,
            'total_recycled_m3': total_recycled,
            'fresh_water_m3': fresh_water,
            'total_inflows_m3': total_inflows
        }
        
        # Source dependency (inline calculation)
        recycled_total = (inflows.get('tsf_return', 0) + inflows.get('plant_returns', 0) + inflows.get('returns_to_pit', 0))
        other = (inflows.get('ore_moisture', 0) + inflows.get('seepage_gain', 0))
        dependency = {
            'surface_water_pct': (inflows.get('surface_water', 0) / total_inflows * 100.0) if total_inflows > 0 else 0,
            'groundwater_pct': (inflows.get('groundwater', 0) / total_inflows * 100.0) if total_inflows > 0 else 0,
            'underground_pct': (inflows.get('underground', 0) / total_inflows * 100.0) if total_inflows > 0 else 0,
            'rainfall_pct': (inflows.get('rainfall', 0) / total_inflows * 100.0) if total_inflows > 0 else 0,
            'recycled_pct': (recycled_total / total_inflows * 100.0) if total_inflows > 0 else 0,
            'other_pct': (other / total_inflows * 100.0) if total_inflows > 0 else 0,
            'total_inflows_m3': total_inflows,
            'surface_water_m3': inflows.get('surface_water', 0),
            'groundwater_m3': inflows.get('groundwater', 0),
            'underground_m3': inflows.get('underground', 0),
            'rainfall_m3': inflows.get('rainfall', 0),
            'recycled_m3': recycled_total,
            'other_m3': other
        }
        
        # Storage security (inline calculation)
        current_storage = balance['storage']['current_volume']
        total_outflows_val = outflows['total']
        days_in_month = 30
        daily_consumption = total_outflows_val / days_in_month if days_in_month > 0 else 0
        days_cover = current_storage / daily_consumption if daily_consumption > 0 else 999
        
        facilities = self.db.get_storage_facilities()
        total_capacity = sum(f.get('total_capacity', 0) for f in facilities)
        min_operating_level_pct = self.get_constant('pump_stop_level', 20.0) / 100.0
        min_operating_volume = total_capacity * min_operating_level_pct
        days_to_minimum = ((current_storage - min_operating_volume) / daily_consumption) if daily_consumption > 0 else 999
        
        if days_cover >= 30:
            security_status = 'excellent'
        elif days_cover >= 14:
            security_status = 'good'
        elif days_cover >= 7:
            security_status = 'adequate'
        elif days_cover >= 3:
            security_status = 'low'
        else:
            security_status = 'critical'
        
        security = {
            'days_cover': days_cover,
            'days_to_minimum': max(0, days_to_minimum),
            'current_storage_m3': current_storage,
            'daily_consumption_m3': daily_consumption,
            'monthly_consumption_m3': total_outflows_val,
            'min_operating_volume_m3': min_operating_volume,
            'security_status': security_status,
            'storage_utilization_pct': balance['storage']['utilization_percent']
        }
        
        # Compliance metrics (still need source-level data, keep existing call)
        compliance = self.calculate_compliance_metrics(calculation_date)
        
        result = {
            'calculation_date': calculation_date,
            'water_efficiency': efficiency,
            'recycling': recycling,
            'source_dependency': dependency,
            'storage_security': security,
            'compliance': compliance,
            'closure_error': {
                'error_m3': balance['closure_error_m3'],
                'error_pct': balance['closure_error_percent'],
                'status': balance['balance_status']
            },
            'summary': {
                'total_inflows_m3': total_inflows,
                'total_outflows_m3': outflows['total'],
                'net_balance_m3': balance['net_balance'],
                'ore_processed_tonnes': ore_processed
            }
        }
        
        # Cache the result
        self._kpi_cache[cache_key] = result.copy()
        
        return result
    
    # ==================== SAVE CALCULATIONS ====================
    
    def persist_storage_volumes(self, calculation_date: date) -> bool:
        """Persist calculated closing volumes to storage facilities (Excel: update storage)
        Updates current_volume for each facility based on calculated balance.
        
        Logic:
        - If calculating a new date: update volumes to new date's closing values
        - If recalculating same date: replace old volumes with latest calculated values
        - Tracks which calculation date the volumes correspond to via volume_calc_date
        """
        try:
            facilities = self.db.get_storage_facilities(use_cache=False)
            
            # Preload shared rainfall/evap data for persist step
            month = calculation_date.month
            evap_rate_rows = self.db.execute_query(
                "SELECT evaporation_mm FROM evaporation_rates WHERE month = ?",
                (month,)
            )
            preloaded_evap_mm = evap_rate_rows[0]['evaporation_mm'] if evap_rate_rows else 0.0
            rainfall_rows = self.db.execute_query(
                "SELECT rainfall_mm FROM measurements WHERE measurement_date = ? AND measurement_type = 'rainfall'",
                (calculation_date,)
            )
            if rainfall_rows:
                total_rainfall_mm = sum(r['rainfall_mm'] for r in rainfall_rows if r.get('rainfall_mm'))
            else:
                total_rainfall_mm = 0.0

            # Facility measurements map is now always empty (no DB time-series)
            facility_measurements_map = {}
            
            updated_count = 0
            for facility in facilities:
                facility_id = facility['facility_id']
                facility_balance = self.calculate_facility_balance(
                    facility_id, calculation_date,
                    preloaded_facility=facility,
                    preloaded_rainfall_mm=None,
                    preloaded_evap_mm=None,
                    preloaded_facility_measurements=facility_measurements_map
                )
                
                if facility_balance:
                    closing_volume = facility_balance['closing_volume']
                    utilization = facility_balance['utilization_percent']
                    
                    # Update facility current volume with calculation date tracking
                    update_query = """
                        UPDATE storage_facilities 
                        SET current_volume = ?,
                            current_level_percent = ?,
                            volume_calc_date = ?,
                            last_updated = ?
                        WHERE facility_id = ?
                    """
                    self.db.execute_update(
                        update_query,
                        (closing_volume, utilization, calculation_date, datetime.now(), facility_id)
                    )
                    updated_count += 1
            
            # Invalidate cache so dashboard shows updated volumes
            self.db.invalidate_all_caches()
            
            logger.info(f"✅ Updated {updated_count} facility volumes for {calculation_date}")
            return True
        except Exception as e:
            logger.error(f"Error persisting storage volumes: {e}")
            return False
    
    def save_calculation(self, calculation_date: date, 
                        ore_tonnes: float = None,
                        notes: str = None,
                        persist_storage: bool = True) -> int:
        """
        Save water balance calculation to database (FULL EXCEL PARITY)
        Saves all components and optionally persists storage volumes
        Returns existing calc_id if duplicate found, or new calc_id if saved
        """
        # Resolve ore tonnes first (use Excel if not provided)
        # This ensures duplicate detection uses the same value as the calculation
        resolved_ore_tonnes = ore_tonnes
        if resolved_ore_tonnes is None:
            try:
                excel_tonnes = self._get_excel_repo().get_monthly_value(calculation_date, "Tonnes Milled")
                if excel_tonnes and excel_tonnes > 0:
                    resolved_ore_tonnes = float(excel_tonnes)
                else:
                    resolved_ore_tonnes = 0.0
            except Exception:
                resolved_ore_tonnes = 0.0
        
        # Check for duplicate calculation FIRST (before any calculations)
        existing_id = self._check_duplicate_calculation(calculation_date, resolved_ore_tonnes)
        previous_closing_volumes = None

        if existing_id:
            # Capture current (closing) volumes before any snapshot restore so we can
            # compare against the newly calculated closings and restore if needed.
            facilities_current = self.db.get_storage_facilities(use_cache=False)
            previous_closing_volumes = {
                f['facility_code']: f.get('current_volume', 0.0) or 0.0
                for f in facilities_current
            }
            try:
                restored = self._restore_opening_from_snapshot(existing_id)
                if not restored:
                    logger.info("No opening snapshot found; using current volumes as openings")
            except Exception as e:
                logger.error(f"Error restoring opening snapshot for existing calculation: {e}")
                # Continue anyway - we'll use current volumes as fallback
                raise

        # Ensure we have an opening snapshot for this calculation date to keep
        # repeated calculations idempotent.
        if not self._has_opening_snapshot(calculation_date):
            facilities_for_snapshot = self.db.get_storage_facilities(use_cache=False)
            opening_snapshot = {
                f['facility_code']: f.get('current_volume', 0.0) or 0.0
                for f in facilities_for_snapshot
            }
            self._save_opening_snapshot(calculation_date, opening_snapshot)
        
        # Calculate water balance (will use current volumes from DB as opening)
        balance = self.calculate_water_balance(calculation_date, ore_tonnes)
        
        if existing_id:
            # Duplicate found - check if results changed (user may have updated inputs)
            # Compare calculated storage change with previous calculation's storage change
            volumes_changed = self._check_if_volumes_changed(
                balance, calculation_date, existing_id, previous_closing_volumes
            )
            
            try:
                if volumes_changed:
                    # Inputs changed (e.g., surface water, manual inputs) - update volumes
                    logger.info(f"Duplicate calculation found for {calculation_date} (calc_id={existing_id}) - volumes changed, updating")
                    # Delete old calculation
                    self.db.execute_update("DELETE FROM calculations WHERE calc_id = ?", (existing_id,))
                    # persist_storage stays True - we need to update volumes
                else:
                    # True duplicate (same inputs, same results) - don't update volumes
                    logger.info(f"Duplicate calculation found for {calculation_date} (calc_id={existing_id}) - identical results, keeping current volumes")
                    self.db.execute_update("DELETE FROM calculations WHERE calc_id = ?", (existing_id,))
                    # Don't persist storage volumes - they're already correct
                    persist_storage = False
                    # Restore closing volumes if we temporarily reverted to openings
                    if previous_closing_volumes:
                        for code, vol in previous_closing_volumes.items():
                            self.db.execute_update(
                                "UPDATE storage_facilities SET current_volume = ? WHERE facility_code = ?",
                                (vol, code),
                            )
                        self.db.invalidate_all_caches()
            except Exception as e:
                logger.error(f"Error handling duplicate calculation for {calculation_date}: {e}")
                # Explicit cleanup: restore closing volumes if duplicate handling failed
                if previous_closing_volumes:
                    try:
                        for code, vol in previous_closing_volumes.items():
                            self.db.execute_update(
                                "UPDATE storage_facilities SET current_volume = ? WHERE facility_code = ?",
                                (vol, code),
                            )
                        self.db.invalidate_all_caches()
                    except Exception as cleanup_error:
                        logger.error(f"Cleanup failed while restoring volumes: {cleanup_error}")
                raise
        
        # Persist storage volumes for NEW calculations or changed duplicates
        if persist_storage:
            self.persist_storage_volumes(calculation_date)
        
        # Enhanced query with ALL Excel categories
        query = """
            INSERT OR REPLACE INTO calculations (
                calc_date, calc_type,
                total_inflows, total_outflows, storage_change, 
                balance_error, balance_error_percent,
                river_inflow, borehole_inflow, underground_inflow, 
                rainfall_inflow, return_water_inflow, other_inflow,
                plant_consumption, mining_consumption, evaporation_loss, 
                seepage_loss, discharge_outflow, dust_suppression, 
                domestic_consumption, product_moisture, other_outflow,
                tsf_slurry_volume, tsf_return_volume, tsf_return_percent,
                tonnes_processed, validated, calculated_by, notes
            ) VALUES (
                ?, 'monthly',
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, 0, 'system', ?
            )
        """
        
        inflows = balance['inflows']
        outflows = balance['outflows']
        storage_change = balance['storage_change']['net_storage_change']
        
        # Calculate TSF slurry volume
        plant_gross = outflows['plant_consumption_gross']
        measured_density = self._get_measured_tailings_density(calculation_date)
        slurry_density = measured_density if measured_density is not None else self.get_constant('slurry_density', 1.4)
        tsf_slurry = plant_gross / slurry_density if slurry_density > 0 else 0
        
        params = (
            calculation_date,
            # Totals
            inflows['total'],
            outflows['total'],
            storage_change,
            balance['closure_error_m3'],
            balance['closure_error_percent'],
            # Inflows detail
            inflows.get('surface_water', 0),
            inflows.get('groundwater', 0),
            inflows.get('underground', 0),
            inflows.get('rainfall', 0),
            inflows.get('tsf_return', 0) + inflows.get('plant_returns', 0) + inflows.get('returns_to_pit', 0),
            inflows.get('ore_moisture', 0) + inflows.get('seepage_gain', 0),
            # Outflows detail
            outflows.get('plant_consumption_net', 0),
            outflows.get('mining_consumption', 0),
            outflows.get('evaporation', 0),
            outflows.get('seepage_loss', 0),
            outflows.get('discharge', 0),
            outflows.get('dust_suppression', 0),
            outflows.get('domestic_consumption', 0),
            outflows.get('product_moisture', 0) + outflows.get('tailings_retention', 0),
            0,  # other_outflow
            # TSF specifics
            tsf_slurry,
            outflows.get('tsf_return', 0),
            self.get_constant('tsf_return_percentage', 56.0),
            # Production
            balance['ore_processed'],
            # Notes
            notes
        )
        
        calc_id = self.db.execute_insert(query, params)
        
        # Trigger alert checking after calculation is saved
        try:
            self._check_alerts(calculation_date, balance)
        except Exception as e:
            logger.error(f"Alert checking failed: {e}")
            # Don't fail the calculation if alerts fail
        
        return calc_id
    
    def _check_if_volumes_changed(
        self,
        balance: Dict,
        calc_date: date,
        existing_calc_id: int,
        previous_facility_volumes: Optional[Dict[str, float]] = None,
    ) -> bool:
        """
        Check if calculated closing volumes differ from the previously saved calculation.
        Returns True if any volume changed (net or per-facility), False if identical.
        """
        try:
            # Get the previous calculation's storage change data
            prev_calc_query = """
                SELECT storage_change FROM calculations 
                WHERE calc_id = ?
            """
            prev_result = self.db.execute_query(prev_calc_query, (existing_calc_id,))
            
            if not prev_result or not prev_result[0].get('storage_change'):
                logger.info("No previous calculation storage data - assuming volumes changed")
                return True
            
            prev_storage_change = float(prev_result[0]['storage_change'])
            
            if 'storage_change' not in balance:
                logger.warning("No storage_change in current balance - assuming volumes changed")
                return True
            
            current_storage_change = balance['storage_change'].get('net_storage_change', 0)
            diff = abs(current_storage_change - prev_storage_change)
            if diff > 0.1:
                logger.info(f"Storage change differs: Previous={prev_storage_change:.0f}, Current={current_storage_change:.0f}, Diff={diff:.0f} m³")
                return True

            # Net matches; compare per-facility closing volumes with current DB volumes
            facilities_balance = balance['storage_change'].get('facilities', {}) or {}
            if facilities_balance:
                current_facilities = previous_facility_volumes or {
                    f['facility_code']: f.get('current_volume', 0.0)
                    for f in self.db.get_storage_facilities(use_cache=False)
                }
                for code, values in facilities_balance.items():
                    closing = values.get('closing')
                    current_vol = current_facilities.get(code)
                    if closing is None or current_vol is None:
                        continue
                    if abs(closing - current_vol) > 0.1:
                        logger.info(
                            f"Closing volume differs for {code}: current={current_vol:.1f}, closing={closing:.1f}"
                        )
                        return True

            logger.info(f"Storage change matches ({current_storage_change:.0f} m³) and per-facility closings match - true duplicate")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check volume changes: {e}")
            return True  # safer to update on error
    
    def _check_duplicate_calculation(self, calc_date: date, ore_tonnes: float) -> Optional[int]:
        """
        Check if a calculation with the same date and ore tonnes already exists
        
        Args:
            calc_date: Calculation date
            ore_tonnes: Tonnes processed
            
        Returns:
            calc_id if duplicate found, None otherwise
        """
        query = """
            SELECT calc_id FROM calculations
            WHERE calc_date = ? AND ABS(tonnes_processed - ?) < 0.01
            ORDER BY calc_id DESC
            LIMIT 1
        """
        
        result = self.db.execute_query(query, (calc_date, ore_tonnes))
        if result:
            return result[0]['calc_id']
        return None

    def _has_opening_snapshot(self, calc_date: date) -> bool:
        """Return True if an opening snapshot already exists for the date."""
        try:
            result = self.db.execute_query(
                "SELECT 1 FROM opening_volume_snapshots WHERE calc_date = ? LIMIT 1",
                (calc_date,),
            )
            return bool(result)
        except Exception:
            # Table may not exist yet; treat as missing snapshot
            return False
    
    def _save_opening_snapshot(self, calc_date: date, snapshot: Dict[str, float]) -> None:
        """
        Save opening volume snapshot for a calculation date
        This allows us to restore exact opening values when handling duplicates
        """
        try:
            # Store in a simple table: calc_date, facility_code, opening_volume
            for facility_code, opening_volume in snapshot.items():
                query = """
                    INSERT OR REPLACE INTO opening_volume_snapshots 
                    (calc_date, facility_code, opening_volume)
                    VALUES (?, ?, ?)
                """
                self.db.execute_update(query, (calc_date, facility_code, opening_volume))
            
            logger.info(f"Saved opening snapshot for {calc_date} ({len(snapshot)} facilities)")
            
        except Exception as e:
            # If table doesn't exist, create it
            if "no such table" in str(e).lower():
                logger.info("Creating opening_volume_snapshots table...")
                create_query = """
                    CREATE TABLE IF NOT EXISTS opening_volume_snapshots (
                        calc_date DATE NOT NULL,
                        facility_code TEXT NOT NULL,
                        opening_volume REAL NOT NULL,
                        PRIMARY KEY (calc_date, facility_code)
                    )
                """
                self.db.execute_update(create_query)
                # Retry the insert
                for facility_code, opening_volume in snapshot.items():
                    query = """
                        INSERT OR REPLACE INTO opening_volume_snapshots 
                        (calc_date, facility_code, opening_volume)
                        VALUES (?, ?, ?)
                    """
                    self.db.execute_update(query, (calc_date, facility_code, opening_volume))
                logger.info(f"Saved opening snapshot for {calc_date} ({len(snapshot)} facilities)")
            else:
                logger.error(f"Failed to save opening snapshot: {e}")
    
    def _restore_opening_from_snapshot(self, calc_id: int) -> bool:
        """
        Restore opening volumes from saved snapshot for the calculation's date
        Returns True if successful, False otherwise
        """
        try:
            # Get calc_date from calc_id
            calc_query = "SELECT calc_date FROM calculations WHERE calc_id = ?"
            calc_result = self.db.execute_query(calc_query, (calc_id,))
            
            if not calc_result:
                logger.warning(f"No calculation found with calc_id={calc_id}")
                return False
            
            calc_date = calc_result[0]['calc_date']
            
            # Retrieve snapshot
            snapshot_query = """
                SELECT facility_code, opening_volume 
                FROM opening_volume_snapshots 
                WHERE calc_date = ?
            """
            snapshot = self.db.execute_query(snapshot_query, (calc_date,))
            
            if not snapshot:
                logger.warning(f"No opening snapshot found for {calc_date}")
                return False
            
            # Restore volumes to database
            for row in snapshot:
                facility_code = row['facility_code']
                opening_volume = row['opening_volume']
                
                update_query = """
                    UPDATE storage_facilities 
                    SET current_volume = ? 
                    WHERE facility_code = ?
                """
                self.db.execute_update(update_query, (opening_volume, facility_code))
            
            logger.info(f"Restored {len(snapshot)} facility volumes from snapshot")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from snapshot: {e}")
            return False
    
    def get_calculation_history(self, start_date: date, 
                                end_date: date) -> List[Dict]:
        """
        Retrieve historical calculations
        """
        query = """
            SELECT * FROM water_balance_calculations
            WHERE calculation_date BETWEEN ? AND ?
            ORDER BY calculation_date DESC
        """
        
        return self.db.execute_query(query, (start_date, end_date))
    
    def _check_alerts(self, calculation_date: date, balance: Dict):
        """
        Check for alert conditions after calculation
        
        Args:
            calculation_date: Date of calculation
            balance: Water balance result dict
        """
        # Check storage security alerts
        security = balance.get('storage', {})
        if security:
            security_metrics = {
                'days_cover': balance.get('storage_security', {}).get('days_cover', 0),
                'days_to_minimum': balance.get('storage_security', {}).get('days_to_minimum', 0),
                'storage_utilization_pct': security.get('utilization_percent', 0),
                'current_storage_m3': security.get('current_volume', 0),
            }
            
            # If storage_security not in balance, calculate it
            if not balance.get('storage_security'):
                try:
                    sec_calc = self.calculate_storage_security(calculation_date)
                    security_metrics.update(sec_calc)
                except Exception as e:
                    logger.warning(f"Could not calculate storage security for alerts: {e}")
            
            alert_manager.check_storage_security(calculation_date, security_metrics)
        
        # Check compliance alerts
        compliance = balance.get('compliance', {})
        if not compliance:
            # Calculate compliance if not in balance
            try:
                compliance = self.calculate_compliance_metrics(calculation_date)
            except Exception as e:
                logger.warning(f"Could not calculate compliance for alerts: {e}")
        
        if compliance:
            compliance_metrics = {
                'closure_error_pct': balance.get('closure_error_percent', 0),
                'violations_count': compliance.get('violations_count', 0),
                'overall_utilization_pct': compliance.get('overall_utilization_pct', 0),
            }
            alert_manager.check_compliance(calculation_date, compliance_metrics)
        
        # Check facility-level alerts
        facilities = self.db.get_storage_facilities()
        for facility in facilities:
            level_percent = facility.get('current_level_percent', 0)
            volume = facility.get('current_volume', 0)
            
            if level_percent > 0 or volume > 0:
                alert_manager.check_facility_level(
                    calculation_date,
                    facility['facility_id'],
                    level_percent,
                    volume
                )
        
        # Auto-resolve alerts where conditions no longer met
        alert_manager.auto_resolve_alerts(calculation_date)
        
        logger.info(f"Alert checking completed for {calculation_date}")
    
    # ==================== CACHE MANAGEMENT ====================
    
    def invalidate_cache(self, calculation_date: date = None):
        """Invalidate calculation caches
        Call after measurements updated, constants changed, or storage persisted
        
        Args:
            calculation_date: Invalidate only this date, or None for full cache clear
        """
        if calculation_date is None:
            # Full cache clear
            self._balance_cache.clear()
            self._kpi_cache.clear()
        else:
            # Selective invalidation by date
            keys_to_remove = [k for k in self._balance_cache.keys() if k[0] == calculation_date]
            for key in keys_to_remove:
                self._balance_cache.pop(key, None)
                self._kpi_cache.pop(key, None)
    
    def reload_constants(self):
        """Reload constants and clear cache
        Call after constant update
        """
        self.constants = self._load_constants()
        self.invalidate_cache()  # Clear all since constants affect all dates
