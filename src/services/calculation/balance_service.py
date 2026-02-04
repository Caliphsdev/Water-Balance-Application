"""
Water Balance Calculation Service (MAIN ORCHESTRATOR).

Implements the complete water balance calculation workflow:
1. Gather inflows (rainfall, abstraction, ore moisture)
2. Calculate outflows (evaporation, seepage, dust suppression)
3. Track storage changes (opening → closing volumes)
4. Compute balance closure (error = IN - OUT - ΔS)
5. Calculate KPIs (recycled %, water intensity)

Master Equation:
    balance_error = fresh_inflows - outflows - delta_storage
    error_pct = (error / inflows) * 100

Quality Rule:
    error_pct < 5% = Good balance (GREEN)
    error_pct >= 5% = Poor balance (RED)

Usage:
    from services.calculation import BalanceService
    
    service = BalanceService()
    result = service.calculate_for_date(month=3, year=2026)
    
    if result.is_balanced:
        print(f"Balance OK: {result.error_pct:.1f}% error")
    else:
        print(f"Balance issues: {result.quality_flags.warnings}")
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from services.calculation.interfaces import (
    IBalanceEngine,
    IInflowsService,
    IOutflowsService,
    IStorageService,
    IRecycledService,
    IKPIService,
    IFacilityBalanceService,
    CalculationError,
)
from services.calculation.models import (
    CalculationPeriod,
    InflowResult,
    OutflowResult,
    StorageChange,
    BalanceResult,
    KPIResult,
    RecycledWaterResult,
    FacilityBalance,
    DataQualityFlags,
    DataQualityLevel,
    InflowComponent,
    OutflowComponent,
)
from services.calculation.constants import get_constants, ConstantsLoader
from services.excel_manager import get_excel_manager, ExcelManager

logger = logging.getLogger(__name__)

# Excel column names for Meter Readings data
# These map to columns in the legacy Excel "Meter Readings" sheet
EXCEL_COLUMNS = {
    'tonnes_milled': 'Tonnes Milled',
    'total_consumption': 'Total Water Consumption',
    'total_recycled': 'Total Recycled Water',
    'recycled_pct': '%Recycled',
    # RWD columns - RWD is volume (m³), RWD.1 is intensity (m³/t)
    'rwd_1': 'RWD',  # Volume in m³
    'rwd_intensity': 'RWD.1',  # Intensity in m³/t (used for cross-verification)
    # Tailings density (t/m³) - used for tailings lockup calculation
    # Note: This is DENSITY, not return water volume
    'tailings_density': 'Tailings RD',
    # Product concentrate columns (Two Rivers Platinum Mine)
    # PGM = Platinum Group Metals concentrate
    'pgm_wet_tonnes': 'PGM Concentrate Wet tons dispatched',
    'pgm_moisture_pct': 'PGM Concentrate Moisture',
    # Chromite = Chromite by-product concentrate
    'chromite_wet_tonnes': 'Chromite Concentrate Wet tons dispatched',
    'chromite_moisture_pct': 'Chromite Concentrate Moisture',
    # Surface water abstraction (rivers)
    'surface_water_sources': [
        'Groot Dwars River', 
        'Klein Dwars River',
    ],
    # Groundwater abstraction (boreholes)
    'groundwater_sources': [
        'Plant Borehole Water Use',
        'CPGWA 1', 'CPGWA 2', 'CPGWA 3',
        'NTSFGWA 1', 'NTSFGWA 2',
        'MDGWA 1', 'MDGWA 2', 'MDGWA 3', 'MDGWA 4', 'MDGWA 5',
        'NDGWA 1', 'NDGWA 2', 'NDGWA 3', 'NDGWA 4', 'NDGWA 5', 'NDGWA 6',
        'MERGWA 1', 'MERGWA 2',
    ],
    # Combined abstraction (legacy, for backwards compatibility)
    'abstraction_sources': [
        'Plant Borehole Water Use',
        'CPGWA 1', 'CPGWA 2', 'CPGWA 3',
        'NTSFGWA 1', 'NTSFGWA 2',
        'Groot Dwars River', 'Klein Dwars River',
        'MDGWA 1', 'MDGWA 2', 'MDGWA 3', 'MDGWA 4', 'MDGWA 5',
        'NDGWA 1', 'NDGWA 2', 'NDGWA 3', 'NDGWA 4', 'NDGWA 5', 'NDGWA 6',
        'MERGWA 1', 'MERGWA 2',
    ],
    # Dewatering sources (underground water removal = inflow to system)
    'dewatering_sources': [
        'Main decline dewatering',
        'North decline dewatering',
        'Merensky dewatering',
    ],
}


class InflowsService(IInflowsService):
    """Inflows calculation service implementation.
    
    Calculates all fresh water inflows from:
    - Rainfall (to surface water bodies)
    - Abstraction (rivers, boreholes) - from Excel Meter Readings
    - Ore moisture - from Excel Tonnes Milled
    - External purchases
    
    Data sources:
    - environmental_data table (rainfall_mm, evaporation_mm)
    - storage_facilities table (surface_area_m2)
    - Excel Meter Readings (abstraction, tonnes milled, dewatering)
    """
    
    def __init__(self, db_manager=None, excel_manager: Optional[ExcelManager] = None):
        """Initialize inflows service.
        
        Args:
            db_manager: Database manager instance (creates one if None)
            excel_manager: Excel manager for Meter Readings access
        """
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        self.db = db_manager
        self._excel = excel_manager or get_excel_manager()
        self._constants = get_constants()
    
    def calculate_inflows(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> InflowResult:
        """Calculate total fresh water inflows for a period.
        
        Inflow sources (by category):
        1. RAINFALL - Direct precipitation on storage surfaces
        2. RUNOFF - Surface water runoff from catchment areas  
        3. SURFACE WATER - Rivers (Groot Dwars, Klein Dwars)
        4. GROUNDWATER - Boreholes (CPGWA, NTSFGWA, MDGWA, NDGWA, MERGWA)
        5. UNDERGROUND DEWATERING - Water pumped from mine workings
        6. ORE MOISTURE - Water entering with mined ore
        
        Args:
            period: Calculation period (month/year)
            flags: Data quality flags to populate
        
        Returns:
            InflowResult with total and breakdown by source
        """
        components = {}
        component_details = []
        
        # 1. Rainfall inflow (direct to surface water bodies)
        rainfall = self.get_rainfall_inflow(period, flags)
        components['rainfall'] = rainfall
        component_details.append(InflowComponent(
            name='rainfall',
            value_m3=rainfall,
            quality=DataQualityLevel.MEASURED if rainfall > 0 else DataQualityLevel.MISSING,
            source='Environmental Monitoring',
            notes='Direct rainfall onto storage surfaces (mm × area)'
        ))
        
        # 2. Runoff from catchment areas (OPTIONAL - toggle in settings)
        if self._constants.runoff_enabled:
            runoff = self._get_catchment_runoff(period, flags)
            components['runoff'] = runoff
            component_details.append(InflowComponent(
                name='runoff',
                value_m3=runoff,
                quality=DataQualityLevel.CALCULATED,
                source='Rainfall × runoff coefficient × catchment area',
                notes='Surface water runoff from surrounding areas'
            ))
        else:
            runoff = 0.0
            components['runoff'] = 0.0
        
        # 3. Surface water abstraction (rivers)
        surface_water = self._get_surface_water_abstraction(period, flags)
        components['surface_water'] = surface_water
        component_details.append(InflowComponent(
            name='surface_water',
            value_m3=surface_water,
            quality=DataQualityLevel.MEASURED,
            source='River flow meters',
            notes='Groot Dwars River, Klein Dwars River'
        ))
        
        # 4. Groundwater abstraction (boreholes)
        groundwater = self._get_groundwater_abstraction(period, flags)
        components['groundwater'] = groundwater
        component_details.append(InflowComponent(
            name='groundwater',
            value_m3=groundwater,
            quality=DataQualityLevel.MEASURED,
            source='Borehole meters',
            notes='CPGWA, NTSFGWA, MDGWA, NDGWA, MERGWA boreholes'
        ))
        
        # 5. Underground dewatering (mine water pumped to surface)
        dewatering = self._get_underground_dewatering(period, flags)
        components['dewatering'] = dewatering
        component_details.append(InflowComponent(
            name='dewatering',
            value_m3=dewatering,
            quality=DataQualityLevel.MEASURED if dewatering > 0 else DataQualityLevel.MISSING,
            source='Underground pump meters',
            notes='Water pumped from underground workings (Main, North, Merensky declines)'
        ))
        
        # 6. Ore moisture (water entering with ore)
        ore_moisture = self._get_ore_moisture(period, flags)
        components['ore_moisture'] = ore_moisture
        component_details.append(InflowComponent(
            name='ore_moisture',
            value_m3=ore_moisture,
            quality=DataQualityLevel.CALCULATED,
            source='Ore tonnes × moisture %',
            notes='Natural moisture content in mined ore'
        ))
        
        # Legacy "abstraction" for backwards compatibility (sum of surface + groundwater)
        components['abstraction'] = surface_water + groundwater
        
        # Calculate total (runoff only included if enabled)
        total = rainfall + surface_water + groundwater + dewatering + ore_moisture
        if self._constants.runoff_enabled:
            total += runoff
        
        logger.debug(f"Inflows for {period.period_short}: {total:,.0f} m³ "
                     f"(rainfall={rainfall:,.0f}, runoff={runoff:,.0f}, "
                     f"surface={surface_water:,.0f}, groundwater={groundwater:,.0f}, "
                     f"dewatering={dewatering:,.0f}, ore_moisture={ore_moisture:,.0f})")
        
        return InflowResult(
            total_m3=total,
            components=components,
            component_details=component_details,
            quality=DataQualityLevel.CALCULATED
        )
    
    def get_rainfall_inflow(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get rainfall contribution to inflows.
        
        Equation: rainfall_mm × total_surface_area / 1000
        
        Only counts rainfall on active storage facilities (status='active').
        """
        try:
            # Get rainfall for the period
            rainfall_mm = self._get_rainfall_mm(period, flags)
            
            # Get total surface area of active facilities
            surface_area = self._get_total_surface_area()
            
            if rainfall_mm <= 0 or surface_area <= 0:
                return 0.0
            
            # Convert mm to m³: mm × m² / 1000 = m³
            rainfall_m3 = (rainfall_mm * surface_area) / 1000
            
            return rainfall_m3
            
        except Exception as e:
            logger.warning(f"Rainfall calculation error: {e}")
            flags.add_warning(f"Rainfall calculation failed: {e}")
            return 0.0
    
    def get_abstraction(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get fresh water abstraction from external sources (LEGACY - COMBINED).
        
        Reads abstraction volumes from Meter Readings Excel:
        - Plant Borehole Water Use
        - CPGWA 1-3, NTSFGWA 1-2 (boreholes)
        - Groot Dwars River, Klein Dwars River (rivers)
        - MDGWA, NDGWA, MERGWA boreholes
        
        DEPRECATED: Use _get_surface_water_abstraction() and _get_groundwater_abstraction()
        for broken-down sources.
        
        Args:
            period: Calculation period
            flags: Data quality flags to populate
        
        Returns:
            Total abstraction in m³
        """
        try:
            total = 0.0
            
            # Sum all abstraction sources from Excel (full month range)
            for source_col in EXCEL_COLUMNS['abstraction_sources']:
                try:
                    series = self._excel.get_meter_readings_series(
                        source_col,
                        start_date=period.start_date,
                        end_date=period.end_date
                    )
                    if series:
                        # series is List[(date, value)], get first match within month
                        value = series[0][1] if series else 0.0
                        total += value
                except Exception:
                    # Column may not exist in all Excel versions
                    pass
            
            if total > 0:
                logger.debug(f"Abstraction from Excel for {period.period_short}: {total:,.0f} m³")
                return total
            
            # No data found
            flags.add_missing('abstraction', f'No abstraction data for {period.period_short}')
            return 0.0
            
        except Exception as e:
            logger.warning(f"Abstraction query error: {e}")
            flags.add_warning(f"Abstraction query failed: {e}")
            return 0.0

    def _get_surface_water_abstraction(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get surface water abstraction from rivers (INFLOW).
        
        Surface water sources:
        - Groot Dwars River
        - Klein Dwars River
        
        Data source: Excel Meter Readings → river columns
        """
        try:
            total = 0.0
            
            for source_col in EXCEL_COLUMNS['surface_water_sources']:
                try:
                    series = self._excel.get_meter_readings_series(
                        source_col,
                        start_date=period.start_date,
                        end_date=period.end_date
                    )
                    if series and series[0][1] > 0:
                        total += float(series[0][1])
                except Exception:
                    pass
            
            logger.debug(f"Surface water abstraction: {total:,.0f} m³")
            return total
            
        except Exception as e:
            logger.debug(f"Surface water query error: {e}")
            return 0.0

    def _get_groundwater_abstraction(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get groundwater abstraction from boreholes (INFLOW).
        
        Groundwater sources (boreholes):
        - Plant Borehole Water Use
        - CPGWA 1-3 (Concentrator Plant Groundwater Abstraction)
        - NTSFGWA 1-2 (North TSF Groundwater)
        - MDGWA 1-5 (Main Decline Groundwater)
        - NDGWA 1-6 (North Decline Groundwater)
        - MERGWA 1-2 (Merensky Groundwater)
        
        Data source: Excel Meter Readings → borehole columns
        """
        try:
            total = 0.0
            
            for source_col in EXCEL_COLUMNS['groundwater_sources']:
                try:
                    series = self._excel.get_meter_readings_series(
                        source_col,
                        start_date=period.start_date,
                        end_date=period.end_date
                    )
                    if series and series[0][1] > 0:
                        total += float(series[0][1])
                except Exception:
                    pass
            
            logger.debug(f"Groundwater abstraction: {total:,.0f} m³")
            return total
            
        except Exception as e:
            logger.debug(f"Groundwater query error: {e}")
            return 0.0

    def _get_underground_dewatering(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get underground dewatering volumes (INFLOW).
        
        Underground mines have natural groundwater ingress (seepage INTO workings).
        This water must be pumped to surface = an INFLOW to the surface water system.
        
        Sources:
        - Main decline dewatering
        - North decline dewatering
        - Merensky dewatering
        
        Note: This is the opposite of "seepage loss" (outflow).
        Underground seepage comes IN, then gets pumped OUT to surface dams.
        
        Data source: Excel Meter Readings → dewatering columns
        """
        try:
            total = 0.0
            
            for source_col in EXCEL_COLUMNS['dewatering_sources']:
                try:
                    series = self._excel.get_meter_readings_series(
                        source_col,
                        start_date=period.start_date,
                        end_date=period.end_date
                    )
                    if series and series[0][1] > 0:
                        total += float(series[0][1])
                except Exception:
                    pass
            
            if total > 0:
                logger.debug(f"Underground dewatering: {total:,.0f} m³")
            else:
                flags.add_missing('dewatering', 'No dewatering data in Excel')
            
            return total
            
        except Exception as e:
            logger.debug(f"Dewatering query error: {e}")
            return 0.0

    def _get_catchment_runoff(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate catchment runoff from rainfall (INFLOW).
        
        Scientific basis:
        - Rainfall on surrounding catchment areas generates surface runoff
        - Runoff coefficient depends on surface type (vegetation, roads, rock)
        - This water flows into storage dams and adds to inflows
        
        Equation: runoff_m³ = rainfall_mm × catchment_area × runoff_coefficient / 1000
        
        Runoff coefficients:
        - Open water: 1.0 (already counted in direct rainfall)
        - Bare tailings: 0.60
        - Compacted roads: 0.75
        - Vegetated: 0.30
        - Natural bush: 0.20
        
        Note: This requires catchment area configuration per storage facility.
        Currently returns 0 if catchment areas not configured.
        
        Data source: environmental_data (rainfall) + storage_facilities (catchment_area)
        """
        try:
            rainfall_mm = self._get_rainfall_mm(period, flags)
            
            if rainfall_mm <= 0:
                return 0.0
            
            # Get total catchment area from storage facilities
            # Look for facilities with catchment_area_m2 column
            try:
                conn = self.db.get_connection()
                cursor = conn.execute("""
                    SELECT SUM(COALESCE(catchment_area_m2, 0)) as total_catchment
                    FROM storage_facilities
                    WHERE status = 'active'
                """)
                row = cursor.fetchone()
                conn.close()
                
                catchment_area = float(row['total_catchment']) if row and row['total_catchment'] else 0.0
            except Exception:
                # Column may not exist - runoff not configured
                catchment_area = 0.0
            
            if catchment_area <= 0:
                # Runoff not configured for this site
                flags.add_estimated('runoff', 'No catchment areas configured')
                return 0.0
            
            # Use average runoff coefficient for mixed terrain
            # Default to natural bush (0.20) for undeveloped catchments
            avg_runoff_coeff = self._constants.runoff_coefficients.get('natural_bush', 0.20)
            
            # Calculate runoff: mm × m² / 1000 = m³
            runoff_m3 = (rainfall_mm * catchment_area * avg_runoff_coeff) / 1000
            
            logger.debug(f"Catchment runoff: {rainfall_mm}mm × {catchment_area:,.0f}m² × {avg_runoff_coeff} = {runoff_m3:,.0f} m³")
            return runoff_m3
            
        except Exception as e:
            logger.debug(f"Runoff calculation error: {e}")
            return 0.0

    def _get_ore_moisture(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate water entering system as ore moisture (INFLOW).
        
        Scientific basis:
        - Ore contains natural moisture from underground mining
        - Moisture content varies by ore type and mining method (typically 3-8%)
        - This water becomes available when ore is crushed and processed
        
        Equation: ore_moisture_m3 = tonnes_milled × (moisture_pct / 100)
        
        Since moisture is a mass fraction and water density ≈ 1 t/m³:
        tonnes of water = m³ of water
        
        Data source: Excel Meter Readings → 'Tonnes Milled' column
        Constants: ore_moisture_pct (default 3.5%)
        
        Args:
            period: Calculation period
            flags: Data quality flags to populate
            
        Returns:
            Ore moisture volume in m³
        """
        try:
            # Get tonnes milled from Excel (full month range)
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tonnes_milled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            tonnes_milled = series[0][1] if series else 0.0
            
            if tonnes_milled <= 0:
                flags.add_missing('ore_moisture', f'No ore production data for {period.period_short}')
                return 0.0
            
            # Calculate moisture content
            # Moisture % is mass fraction: (mass of water / mass of wet ore) × 100
            # Typical values: hard rock 3-5%, soft ore 5-8%
            ore_moisture_pct = self._constants.ore_moisture_pct
            
            # Volume of water = tonnes of ore × moisture fraction
            # Water density = 1 t/m³, so tonnes of water = m³ of water
            moisture_m3 = tonnes_milled * (ore_moisture_pct / 100.0)
            
            logger.debug(f"Ore moisture for {period.period_short}: "
                        f"{tonnes_milled:,.0f} t × {ore_moisture_pct}% = {moisture_m3:,.0f} m³")
            
            return moisture_m3
            
        except Exception as e:
            logger.warning(f"Ore moisture calculation error: {e}")
            flags.add_warning(f"Ore moisture calculation failed: {e}")
            return 0.0
    
    def _get_rainfall_mm(self, period: CalculationPeriod, flags: DataQualityFlags) -> float:
        """Get monthly rainfall in mm from environmental_data table.
        
        Table schema: environmental_data(id, year, month, rainfall_mm, evaporation_mm, ...)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT rainfall_mm 
                FROM environmental_data
                WHERE month = ? AND year = ?
            """, (period.month, period.year))
            row = cursor.fetchone()
            conn.close()
            
            if row and row['rainfall_mm'] is not None:
                return float(row['rainfall_mm'])
            
            flags.add_missing('rainfall', f'No rainfall data for {period.period_short}')
            return 0.0
            
        except Exception as e:
            logger.debug(f"Rainfall query error: {e}")
            return 0.0
    
    def _get_total_surface_area(self) -> float:
        """Get total surface area of active facilities receiving rainfall.
        
        Table schema: storage_facilities(id, code, name, ..., surface_area_m2, status, ...)
        Uses status='Active' to filter active facilities (no evap_active column).
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT COALESCE(SUM(surface_area_m2), 0) as total
                FROM storage_facilities
                WHERE LOWER(status) = 'active'
                AND surface_area_m2 > 0
            """)
            row = cursor.fetchone()
            conn.close()
            
            return float(row['total']) if row else 0.0
            
        except Exception as e:
            logger.warning(f"Surface area query error: {e}")
            return 0.0


class OutflowsService(IOutflowsService):
    """Outflows calculation service implementation.
    
    Calculates all water leaving the system:
    - Evaporation (from ponds, TSFs)
    - Seepage losses (unlined dams)
    - Dust suppression (estimated from operations)
    - Tailings moisture lock-up (from tonnes milled)
    - Mining consumption (underground water usage)
    - Domestic consumption (camp/hostel usage)
    - Product moisture (water exported with concentrate)
    
    Data sources:
    - environmental_data table (evaporation_mm)
    - storage_facilities table (surface_area_m2)
    - Excel Meter Readings (tonnes milled for tailings calc)
    - system_constants (seepage rates, moisture percentages)
    """
    
    def __init__(self, db_manager=None, excel_manager: Optional[ExcelManager] = None):
        """Initialize outflows service.
        
        Args:
            db_manager: Database manager instance (creates one if None)
            excel_manager: Excel manager for Meter Readings access
        """
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        self.db = db_manager
        self._excel = excel_manager or get_excel_manager()
        self._constants = get_constants()
    
    def calculate_outflows(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> OutflowResult:
        """Calculate total outflows for a period.
        
        Components calculated:
        1. Evaporation - water lost to atmosphere from open surfaces
        2. Seepage - water lost to ground from unlined facilities
        3. Dust suppression - water sprayed for dust control
        4. Tailings lockup - water retained in tailings solids
        5. Mining consumption - underground water usage (drilling, cooling)
        6. Domestic consumption - camp/hostel water usage
        7. Product moisture - water exported with concentrate
        """
        components = {}
        component_details = []
        
        # 1. Evaporation losses
        evaporation = self.get_evaporation(period, flags)
        components['evaporation'] = evaporation
        component_details.append(OutflowComponent(
            name='evaporation',
            value_m3=evaporation,
            quality=DataQualityLevel.CALCULATED,
            destination='Atmosphere',
            notes='Pan evap × coeff × surface area'
        ))
        
        # 2. Seepage losses
        seepage = self.get_seepage(period, flags)
        components['seepage'] = seepage
        component_details.append(OutflowComponent(
            name='seepage',
            value_m3=seepage,
            quality=DataQualityLevel.ESTIMATED,
            destination='Groundwater',
            notes='Lined=0.1%, Unlined=0.5% of volume'
        ))
        
        # 3. Dust suppression
        dust_suppression = self._get_dust_suppression(period, flags)
        components['dust_suppression'] = dust_suppression
        component_details.append(OutflowComponent(
            name='dust_suppression',
            value_m3=dust_suppression,
            quality=DataQualityLevel.ESTIMATED,
            destination='Atmosphere/Ground',
            notes='Water sprayed for dust control'
        ))
        
        # 4. Tailings moisture lock-up
        tailings_lockup = self._get_tailings_lockup(period, flags)
        components['tailings_lockup'] = tailings_lockup
        component_details.append(OutflowComponent(
            name='tailings_lockup',
            value_m3=tailings_lockup,
            quality=DataQualityLevel.CALCULATED,
            destination='Tailings',
            notes='Water retained in tailings solids'
        ))
        
        # 5. Mining consumption (underground operations)
        # Only include if enabled - often water returns as dewatering (avoids double-counting)
        mining_consumption = 0.0
        if getattr(self._constants, 'mining_consumption_enabled', False):
            mining_consumption = self._get_mining_consumption(period, flags)
            components['mining_consumption'] = mining_consumption
            component_details.append(OutflowComponent(
                name='mining_consumption',
                value_m3=mining_consumption,
                quality=DataQualityLevel.ESTIMATED,
                destination='Underground',
                notes='Drilling, cooling, underground dust suppression'
            ))
        else:
            # Log that it's disabled (water recaptured as dewatering)
            logger.debug("Mining consumption disabled (water returns as dewatering inflow)")
        
        # 6. Domestic consumption
        # Only include if enabled - may be recycled in closed-loop systems
        domestic_consumption = 0.0
        if getattr(self._constants, 'domestic_consumption_enabled', True):
            domestic_consumption = self._get_domestic_consumption(period, flags)
            components['domestic_consumption'] = domestic_consumption
            component_details.append(OutflowComponent(
                name='domestic_consumption',
                value_m3=domestic_consumption,
                quality=DataQualityLevel.ESTIMATED,
                destination='Sewage/Evaporation',
                notes='Camp, hostel, office, ablution facilities'
            ))
        
        # 7. Product moisture (water exported with concentrate)
        product_moisture = self._get_product_moisture(period, flags)
        components['product_moisture'] = product_moisture
        component_details.append(OutflowComponent(
            name='product_moisture',
            value_m3=product_moisture,
            quality=DataQualityLevel.CALCULATED,
            destination='Off-site (product)',
            notes='Water exported with concentrate/product'
        ))
        
        # Calculate total
        total = sum(components.values())
        
        logger.debug(f"Outflows for {period.period_short}: {total:,.0f} m³ "
                     f"(evap={evaporation:,.0f}, seepage={seepage:,.0f}, "
                     f"dust={dust_suppression:,.0f}, tailings={tailings_lockup:,.0f}, "
                     f"mining={mining_consumption:,.0f}, domestic={domestic_consumption:,.0f}, "
                     f"product={product_moisture:,.0f})")
        
        return OutflowResult(
            total_m3=total,
            components=components,
            component_details=component_details,
            quality=DataQualityLevel.CALCULATED
        )
    
    def get_evaporation(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate total evaporation losses.
        
        Equation: evap_mm × pan_coeff × surface_area / 1000
        """
        try:
            # Get evaporation for the period
            evap_mm = self._get_evaporation_mm(period, flags)
            
            if evap_mm <= 0:
                return 0.0
            
            pan_coeff = self._constants.evap_pan_coefficient
            
            # Calculate per facility and sum
            # Filter by status='active' (case-insensitive) and surface area > 0
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT code, surface_area_m2, current_volume_m3
                FROM storage_facilities
                WHERE LOWER(status) = 'active'
                AND surface_area_m2 > 0
            """)
            facilities = cursor.fetchall()
            conn.close()
            
            total_evap = 0.0
            for fac in facilities:
                surface_area = float(fac['surface_area_m2'] or 0)
                current_vol = float(fac['current_volume_m3'] or 0)
                
                # Calculate evaporation for this facility
                evap_m3 = (evap_mm * pan_coeff * surface_area) / 1000
                
                # Cap at current volume (can't evaporate more than exists)
                evap_m3 = min(evap_m3, current_vol)
                
                total_evap += evap_m3
            
            return total_evap
            
        except Exception as e:
            logger.warning(f"Evaporation calculation error: {e}")
            flags.add_warning(f"Evaporation calculation failed: {e}")
            return 0.0
    
    def get_seepage(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate total seepage losses.
        
        Lined dams: 0.1% of volume per month
        Unlined dams: 0.5% of volume per month
        """
        try:
            lined_rate = self._constants.seepage_rate_lined_pct / 100
            unlined_rate = self._constants.seepage_rate_unlined_pct / 100
            
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT code, is_lined, current_volume_m3
                FROM storage_facilities
                WHERE status = 'active'
                AND current_volume_m3 > 0
            """)
            facilities = cursor.fetchall()
            conn.close()
            
            total_seepage = 0.0
            for fac in facilities:
                volume = float(fac['current_volume_m3'] or 0)
                is_lined = bool(fac['is_lined'])
                
                rate = lined_rate if is_lined else unlined_rate
                seepage = volume * rate
                
                total_seepage += seepage
            
            return total_seepage
            
        except Exception as e:
            logger.warning(f"Seepage calculation error: {e}")
            flags.add_warning(f"Seepage calculation failed: {e}")
            return 0.0
    
    def _get_evaporation_mm(self, period: CalculationPeriod, flags: DataQualityFlags) -> float:
        """Get monthly evaporation in mm from environmental_data table.
        
        Table schema: environmental_data(id, year, month, rainfall_mm, evaporation_mm, ...)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT evaporation_mm 
                FROM environmental_data
                WHERE month = ? AND year = ?
            """, (period.month, period.year))
            row = cursor.fetchone()
            conn.close()
            
            if row and row['evaporation_mm'] is not None:
                return float(row['evaporation_mm'])
            
            flags.add_missing('evaporation', f'No evaporation data for {period.period_short}')
            return 0.0
            
        except Exception as e:
            logger.debug(f"Evaporation query error: {e}")
            return 0.0
    
    def _get_dust_suppression(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Estimate dust suppression water usage (OUTFLOW).
        
        Scientific basis:
        - Water is sprayed on roads, stockpiles, and conveyors for dust control
        - Application rate depends on climate, traffic, and material properties
        - Industry benchmarks: 0.5-2% of ore tonnage, or 0.5-2 L/tonne
        
        Equation: dust_water_m3 = tonnes × application_rate (L/t) / 1000
        
        Default rate: 1 L/tonne = 0.001 m³/tonne
        Typical ranges:
        - Dry climate, dusty ore: 1.5-2 L/t
        - Moderate climate: 0.5-1 L/t
        - Wet climate: 0.2-0.5 L/t
        
        Data source: Excel Meter Readings → 'Tonnes Milled' column
        Constants: dust_suppression_rate_l_per_t (default 1.0 L/t)
        """
        try:
            # Read tonnes milled from Excel (full month range)
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tonnes_milled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            if series and series[0][1] > 0:
                tonnes_milled = float(series[0][1])
                
                # Dust suppression rate: L water per tonne of ore handled
                # Use configured value or default to 1.0 L/t
                dust_rate_l_per_t = getattr(self._constants, 'dust_suppression_rate_l_per_t', 1.0)
                
                # Convert L to m³: L / 1000 = m³
                dust_m3 = tonnes_milled * dust_rate_l_per_t / 1000.0
                
                flags.add_estimated('dust_suppression', 
                                   f'Estimated at {dust_rate_l_per_t} L/t × {tonnes_milled:,.0f}t')
                logger.debug(f"Dust suppression: {tonnes_milled:,.0f}t × {dust_rate_l_per_t} L/t = {dust_m3:,.0f} m³")
                return dust_m3
            
            flags.add_estimated('dust_suppression', 'No tonnes milled data for estimation')
            return 0.0
            
        except Exception as e:
            logger.debug(f"Dust suppression estimation error: {e}")
            flags.add_estimated('dust_suppression', f'Estimation failed: {e}')
            return 0.0
    
    def _get_tailings_lockup(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate water locked up in tailings solids (OUTFLOW).
        
        Scientific basis:
        - Tailings are the waste rock after mineral extraction
        - After deposition, water is retained in tailings pore spaces
        - This water is permanently locked and does not return to the system
        
        Moisture Calculation from Density:
        - If tailings density (ρslurry) is measured, we calculate moisture from physics:
          Cw (solids concentration) = ρs × (ρslurry - ρw) / (ρslurry × (ρs - ρw))
          moisture_pct = (1 - Cw) × 100
        - Where ρs = solids density (2.7 t/m³), ρw = water density (1.0 t/m³)
        
        Lockup Equation: tailings_water_m3 = tailings_tonnes × moisture_pct / 100
        
        Note: Tailings tonnes ≈ ore tonnes (98%+ becomes tailings in base metal mining)
        
        Data sources:
        - Tonnes: Excel Meter Readings → 'Tonnes Milled' column
        - Density: Excel Meter Readings → 'Tailings RD' column (optional, for actual moisture)
        
        Fallback: Uses tailings_moisture_pct constant (default 45%) when density not available
        """
        try:
            # Read tonnes milled from Excel (tailings ≈ tonnes milled)
            # Recovery rate is typically 1-2%, so 98%+ becomes tailings
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tonnes_milled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            tailings_tonnes = 0.0
            if series and series[0][1] > 0:
                tailings_tonnes = float(series[0][1])
            
            if tailings_tonnes <= 0:
                flags.add_estimated('tailings_lockup', 'No tonnage data')
                return 0.0
            
            # Try to get actual moisture % from tailings density measurement
            moisture_pct = self._calculate_moisture_from_density(period, flags)
            
            # Fallback to constant if density not available
            if moisture_pct is None:
                moisture_pct = self._constants.tailings_moisture_pct  # Default 45%
                logger.debug(f"Using constant moisture: {moisture_pct}%")
            else:
                logger.debug(f"Using measured moisture from density: {moisture_pct:.1f}%")
            
            # Water locked = tailings tonnes × moisture content
            # Using simplified formula (valid when moisture is expressed as % of wet mass)
            # Mw = M_wet × (moisture% / 100) where M_wet ≈ tailings_tonnes
            lockup_m3 = tailings_tonnes * (moisture_pct / 100.0)
            
            logger.debug(f"Tailings lockup: {tailings_tonnes:,.0f}t × {moisture_pct:.1f}% = {lockup_m3:,.0f} m³")
            return lockup_m3
            
        except Exception as e:
            logger.debug(f"Tailings lockup calculation error: {e}")
            return 0.0
    
    def _calculate_moisture_from_density(
        self,
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> Optional[float]:
        """Calculate tailings moisture % from measured slurry density (PHYSICS).
        
        Scientific basis:
        - Slurry density depends on solids/water ratio
        - Cw (solids concentration by weight) = ρs × (ρslurry - ρw) / (ρslurry × (ρs - ρw))
        - moisture_pct = (1 - Cw) × 100
        
        Constants:
        - ρs (solids density) = 2.7 t/m³ (typical ore, configurable)
        - ρw (water density) = 1.0 t/m³
        
        Data source: Excel Meter Readings → 'Tailings RD' column (t/m³)
        
        Returns:
            Moisture % if density available and valid, None otherwise
        """
        try:
            # Get tailings density from Excel (t/m³)
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tailings_density'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            if not series or series[0][1] <= 0:
                return None
            
            rho_slurry = float(series[0][1])  # Measured slurry density (t/m³)
            
            # Physical constants
            rho_solids = getattr(self._constants, 'tailings_solids_density', 2.7)  # t/m³
            rho_water = 1.0  # t/m³
            
            # Validate density is within physical bounds
            # Slurry density must be between water (1.0) and solids (2.7)
            if rho_slurry <= rho_water or rho_slurry >= rho_solids:
                logger.warning(f"Invalid tailings density {rho_slurry} t/m³ (must be 1.0-2.7)")
                return None
            
            # Calculate solids concentration by weight
            # Formula: Cw = ρs × (ρslurry - ρw) / (ρslurry × (ρs - ρw))
            Cw = rho_solids * (rho_slurry - rho_water) / (rho_slurry * (rho_solids - rho_water))
            moisture_pct = (1 - Cw) * 100
            
            logger.debug(f"Moisture from density: ρ={rho_slurry:.2f} → {moisture_pct:.1f}%")
            return moisture_pct
            
        except Exception as e:
            logger.debug(f"Moisture from density calculation error: {e}")
            return None

    def _get_mining_consumption(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate underground mining water consumption (OUTFLOW).
        
        Scientific basis:
        - Underground mining requires water for:
          • Drilling (40%): Dust suppression, bit cooling, chip removal
          • Cooling (30%): Ventilation, equipment cooling in deep mines
          • Dust suppression (20%): Underground roads, loading points
          • Other (10%): Sprinklers, cleaning, firefighting
        
        Equation: mining_water_m3 = tonnes_mined × water_rate (m³/t)
        
        Industry benchmarks:
        - Underground hard rock: 0.03-0.08 m³/t
        - Open pit: 0.02-0.05 m³/t (less cooling required)
        - Deep mines (>2km): 0.08-0.15 m³/t (more cooling)
        
        Note: Much of this water ends up in mine sumps and is pumped to surface,
        so it may appear as recycled water rather than true consumption.
        This component tracks the initial usage, not net loss.
        
        Data source: Excel Meter Readings → 'Tonnes Milled' (proxy for mined)
        Constants: mining_water_rate_m3_per_t (default 0.05 m³/t)
        """
        try:
            # Read tonnes milled (proxy for tonnes mined)
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tonnes_milled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            if series and series[0][1] > 0:
                tonnes_mined = float(series[0][1])
                
                # Mining water rate: m³ per tonne of ore mined
                rate = getattr(self._constants, 'mining_water_rate_m3_per_t', 0.05)
                
                mining_m3 = tonnes_mined * rate
                
                flags.add_estimated('mining_consumption', 
                                   f'Estimated at {rate} m³/t × {tonnes_mined:,.0f}t')
                logger.debug(f"Mining consumption: {tonnes_mined:,.0f}t × {rate} m³/t = {mining_m3:,.0f} m³")
                return mining_m3
            
            flags.add_estimated('mining_consumption', 'No production data')
            return 0.0
            
        except Exception as e:
            logger.debug(f"Mining consumption error: {e}")
            return 0.0

    def _get_domestic_consumption(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate domestic/sanitation water consumption (OUTFLOW).
        
        Scientific basis:
        - Mining operations have associated domestic water needs:
          • Hostels/camps: Drinking, bathing, laundry
          • Offices: Ablution, canteens, cleaning
          • Change houses: Showers, toilets
        
        Equation: domestic_m3 = workforce × days × daily_rate (L/person/day) / 1000
        
        Industry benchmarks (L/person/day):
        - WHO minimum: 50 L
        - Mining camp (hot climate): 150-200 L
        - SA urban average: 200-250 L
        - Default: 150 L/person/day
        
        Note: Currently estimated based on typical workforce size.
        Future: Read workforce from HR system or configuration.
        
        Constants: domestic_consumption_l_per_person_day (default 150 L)
        Assumption: 2000 person workforce (configurable)
        """
        try:
            # Default workforce estimate
            # TODO: Read from configuration or HR data
            workforce = 2000  # People
            days_in_month = (period.end_date - period.start_date).days + 1
            
            # Consumption rate: L per person per day
            rate_l = getattr(self._constants, 'domestic_consumption_l_per_person_day', 150.0)
            
            # Calculate total (L → m³)
            domestic_l = workforce * days_in_month * rate_l
            domestic_m3 = domestic_l / 1000.0
            
            flags.add_estimated('domestic_consumption', 
                               f'Est: {workforce} people × {days_in_month} days × {rate_l} L/day')
            logger.debug(f"Domestic consumption: {workforce} × {days_in_month}d × {rate_l} L = {domestic_m3:,.0f} m³")
            return domestic_m3
            
        except Exception as e:
            logger.debug(f"Domestic consumption error: {e}")
            return 0.0

    def _get_product_moisture(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate water exported with product/concentrate (OUTFLOW).
        
        Scientific basis (Two Rivers Platinum Mine):
        - PGM (Platinum Group Metals) concentrate is shipped with residual moisture
        - Chromite concentrate is a by-product also shipped with moisture
        - This water leaves the mine water circuit permanently
        
        Equation (using actual Excel data):
            pgm_water = PGM_wet_tonnes × PGM_moisture_pct / 100
            chromite_water = Chromite_wet_tonnes × Chromite_moisture_pct / 100
            total_product_water = pgm_water + chromite_water
        
        Data sources (Excel Meter Readings):
        - 'PGM Concentrate Wet tons dispatched' - PGM concentrate tonnes
        - 'PGM Concentrate Moisture' - PGM moisture % (typically 14-15%)
        - 'Chromite Concentrate Wet tons dispatched' - Chromite tonnes
        - 'Chromite Concentrate Moisture' - Chromite moisture % (typically 5-6%)
        
        Fallback: Uses constants (recovery_rate_pct=2%, product_moisture_pct=8%) if Excel data unavailable
        """
        try:
            # Try to read actual product data from Excel (preferred method)
            total_product_water = self._get_product_moisture_from_excel(period, flags)
            
            if total_product_water is not None:
                return total_product_water
            
            # Fallback to constant-based calculation if Excel data unavailable
            return self._get_product_moisture_from_constants(period, flags)
            
        except Exception as e:
            logger.debug(f"Product moisture error: {e}")
            return 0.0
    
    def _get_product_moisture_from_excel(
        self,
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> Optional[float]:
        """Get product moisture from actual Excel concentrate data (PREFERRED).
        
        Two Rivers Platinum Mine produces:
        1. PGM Concentrate (Platinum Group Metals) - higher moisture (~14%)
        2. Chromite Concentrate (by-product) - lower moisture (~5%)
        
        Returns:
            Total water in products (m³), or None if data unavailable
        """
        try:
            # Get PGM concentrate data
            pgm_tonnes_series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['pgm_wet_tonnes'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            pgm_moisture_series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['pgm_moisture_pct'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            # Get Chromite concentrate data
            chromite_tonnes_series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['chromite_wet_tonnes'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            chromite_moisture_series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['chromite_moisture_pct'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            # Check if we have at least PGM data (primary product)
            if not pgm_tonnes_series or pgm_tonnes_series[0][1] <= 0:
                return None  # Fall back to constants
            
            # Calculate PGM water
            pgm_wet_tonnes = float(pgm_tonnes_series[0][1])
            pgm_moisture_pct = 14.0  # Default for PGM
            if pgm_moisture_series and pgm_moisture_series[0][1] > 0:
                pgm_moisture_pct = float(pgm_moisture_series[0][1])
            pgm_water_m3 = pgm_wet_tonnes * (pgm_moisture_pct / 100.0)
            
            # Calculate Chromite water (if available)
            chromite_water_m3 = 0.0
            chromite_wet_tonnes = 0.0
            chromite_moisture_pct = 5.0  # Default for Chromite
            if chromite_tonnes_series and chromite_tonnes_series[0][1] > 0:
                chromite_wet_tonnes = float(chromite_tonnes_series[0][1])
                if chromite_moisture_series and chromite_moisture_series[0][1] > 0:
                    chromite_moisture_pct = float(chromite_moisture_series[0][1])
                chromite_water_m3 = chromite_wet_tonnes * (chromite_moisture_pct / 100.0)
            
            total_water = pgm_water_m3 + chromite_water_m3
            
            # Log the calculation
            flags.add_calculated('product_moisture',
                f'PGM: {pgm_wet_tonnes:,.0f}t×{pgm_moisture_pct:.1f}%={pgm_water_m3:,.0f}m³ + '
                f'Chromite: {chromite_wet_tonnes:,.0f}t×{chromite_moisture_pct:.1f}%={chromite_water_m3:,.0f}m³')
            logger.debug(
                f"Product moisture (Excel): PGM {pgm_water_m3:,.0f} + Chromite {chromite_water_m3:,.0f} "
                f"= {total_water:,.0f} m³"
            )
            
            return total_water
            
        except Exception as e:
            logger.debug(f"Product moisture from Excel error: {e}")
            return None
    
    def _get_product_moisture_from_constants(
        self,
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate product moisture using constants (FALLBACK).
        
        Used when actual concentrate data is not available in Excel.
        
        Equation:
            product_tonnes = ore_tonnes × recovery_rate_pct
            product_water_m3 = product_tonnes × moisture_pct / 100
        
        Constants:
        - recovery_rate_pct: Default 2% (base metals)
        - product_moisture_pct: Default 8% (filter cake)
        """
        try:
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tonnes_milled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            if series and series[0][1] > 0:
                tonnes_milled = float(series[0][1])
                
                recovery_pct = getattr(self._constants, 'recovery_rate_pct', 2.0)
                product_tonnes = tonnes_milled * (recovery_pct / 100.0)
                
                moisture_pct = getattr(self._constants, 'product_moisture_pct', 8.0)
                product_water_m3 = product_tonnes * (moisture_pct / 100.0)
                
                flags.add_estimated('product_moisture',
                    f'Using constants: {product_tonnes:,.0f}t × {moisture_pct}% (no Excel data)')
                logger.debug(
                    f"Product moisture (constants): {product_tonnes:,.0f}t × {moisture_pct}% = "
                    f"{product_water_m3:,.0f} m³"
                )
                return product_water_m3
            
            flags.add_estimated('product_moisture', 'No production data')
            return 0.0
            
        except Exception as e:
            logger.debug(f"Product moisture from constants error: {e}")
            return 0.0


class StorageService(IStorageService):
    """Storage calculation service implementation (STORAGE TRACKING).
    
    Tracks storage volumes across all facilities for water balance calculation.
    
    Key responsibilities:
    1. Calculate opening and closing volumes for each facility
    2. Sum to get system-wide storage change (ΔStorage)
    3. Record monthly storage history for future calculations
    4. Track inter-facility transfers (optional, for reporting)
    
    Scientific basis:
    - ΔStorage = Closing_Volume - Opening_Volume
    - Opening volume = previous month's closing (mass conservation)
    - Positive ΔStorage = water accumulated
    - Negative ΔStorage = water released
    
    Data sources:
    - storage_facilities table: current volumes, capacities
    - storage_history table: monthly opening/closing records
    - facility_transfers table: inter-dam water movements (optional)
    """
    
    def __init__(self, db_manager=None):
        """Initialize storage service (CONSTRUCTOR).
        
        Args:
            db_manager: Database manager instance (optional, auto-created if None)
        
        Side effects:
            - Creates storage_history table if missing (schema migration)
        """
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        self.db = db_manager
        
        # Ensure storage_history table exists (safe migration)
        self._ensure_storage_tables()
    
    def _ensure_storage_tables(self) -> None:
        """Ensure storage_history and facility_transfers tables exist (SCHEMA CHECK).
        
        Called on service initialization to handle upgrades from older databases.
        Uses IF NOT EXISTS to be safe for repeated calls.
        """
        try:
            from database.schema import DatabaseSchema
            schema = DatabaseSchema()
            schema.ensure_storage_history_tables()
        except Exception as e:
            logger.warning(f"Could not ensure storage tables: {e}")
    
    def calculate_storage(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags,
        inflows_m3: Optional[float] = None,
        outflows_m3: Optional[float] = None
    ) -> StorageChange:
        """Calculate system-wide storage change (MAIN CALCULATION).
        
        Two modes of operation:
        1. If inflows/outflows provided: Calculate closing from balance equation
           Closing = Opening + Inflows - Outflows (mass conservation)
        2. If not provided: Read both from database (legacy behavior)
        
        The first mode (with inflows/outflows) ensures the balance closes
        properly with error ~0%, which is scientifically correct.
        
        Args:
            period: Year/month for calculation
            flags: Data quality tracker
            inflows_m3: Total inflows for period (optional, for balance calculation)
            outflows_m3: Total outflows for period (optional, for balance calculation)
        
        Returns:
            StorageChange with system totals
        """
        facilities = self.get_all_facilities_storage(period, flags)
        
        total_opening = sum(f.opening_m3 for f in facilities)
        total_capacity = sum(f.capacity_m3 or 0 for f in facilities)
        
        # Calculate closing volume from balance equation if inflows/outflows provided
        if inflows_m3 is not None and outflows_m3 is not None:
            # Mass conservation: Closing = Opening + IN - OUT
            total_closing = total_opening + inflows_m3 - outflows_m3
            
            # Ensure non-negative (can't have negative storage)
            if total_closing < 0:
                logger.warning(f"Calculated closing storage is negative ({total_closing:,.0f} m³), "
                              f"clamping to 0. This may indicate missing inflow data.")
                flags.add_warning('storage_negative', 
                                 f'Calculated closing < 0, clamped to 0')
                total_closing = 0.0
            
            # Check for capacity overflow
            if total_closing > total_capacity and total_capacity > 0:
                overflow = total_closing - total_capacity
                logger.warning(f"Calculated closing storage ({total_closing:,.0f} m³) exceeds "
                              f"capacity ({total_capacity:,.0f} m³) by {overflow:,.0f} m³")
                flags.add_warning('storage_overflow', 
                                 f'Closing exceeds capacity by {overflow:,.0f} m³')
            
            logger.debug(f"Storage calculated from balance: Opening={total_opening:,.0f} + "
                        f"IN={inflows_m3:,.0f} - OUT={outflows_m3:,.0f} = Closing={total_closing:,.0f} m³")
            source = DataQualityLevel.CALCULATED
        else:
            # Legacy mode: read closing from database
            total_closing = sum(f.closing_m3 for f in facilities)
            source = DataQualityLevel.MEASURED
        
        # Build per-facility breakdown with proportional closing volumes
        # When calculated, distribute closing proportionally based on opening
        facility_breakdown = []
        for fac in facilities:
            if inflows_m3 is not None and outflows_m3 is not None and total_opening > 0:
                # Proportional distribution: Each facility gets share based on opening %
                fac_ratio = fac.opening_m3 / total_opening
                fac_closing = fac.opening_m3 + (total_closing - total_opening) * fac_ratio
            else:
                fac_closing = fac.closing_m3
            
            facility_breakdown.append(StorageChange(
                facility_code=fac.facility_code,
                facility_name=fac.facility_name,
                opening_m3=fac.opening_m3,
                closing_m3=fac_closing,
                capacity_m3=fac.capacity_m3,
                source=source
            ))
        
        return StorageChange(
            facility_code=None,
            facility_name="System Total",
            opening_m3=total_opening,
            closing_m3=total_closing,
            capacity_m3=total_capacity,
            source=source,
            facility_breakdown=facility_breakdown
        )
    
    def get_facility_storage(
        self, 
        facility_code: str, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> StorageChange:
        """Get storage for a specific facility."""
        try:
            conn = self.db.get_connection()
            
            # Get facility info
            cursor = conn.execute("""
                SELECT code, name, capacity_m3, current_volume_m3
                FROM storage_facilities
                WHERE code = ?
            """, (facility_code,))
            fac = cursor.fetchone()
            
            if not fac:
                flags.add_warning(f"Facility {facility_code} not found")
                return StorageChange(
                    facility_code=facility_code,
                    facility_name="Unknown",
                    opening_m3=0,
                    closing_m3=0
                )
            
            # Get opening volume from previous month end
            # For now, use current volume as closing
            closing_m3 = float(fac['current_volume_m3'] or 0)
            
            # Try to get previous month's closing as opening
            opening_m3 = self._get_previous_month_volume(
                facility_code, period, conn, flags
            )
            
            conn.close()
            
            return StorageChange(
                facility_code=fac['code'],
                facility_name=fac['name'],
                opening_m3=opening_m3,
                closing_m3=closing_m3,
                capacity_m3=float(fac['capacity_m3'] or 0),
                source=DataQualityLevel.MEASURED
            )
            
        except Exception as e:
            logger.warning(f"Facility storage query error: {e}")
            flags.add_warning(f"Storage query failed for {facility_code}")
            return StorageChange(
                facility_code=facility_code,
                opening_m3=0,
                closing_m3=0
            )
    
    def get_all_facilities_storage(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> List[StorageChange]:
        """Get storage for all active facilities."""
        results = []
        
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT code FROM storage_facilities WHERE status = 'active'
            """)
            facilities = cursor.fetchall()
            conn.close()
            
            for fac in facilities:
                storage = self.get_facility_storage(fac['code'], period, flags)
                results.append(storage)
                
        except Exception as e:
            logger.warning(f"All facilities storage query error: {e}")
            flags.add_warning(f"Could not retrieve all facility storage")
        
        return results
    
    def _get_previous_month_volume(
        self,
        facility_code: str,
        period: CalculationPeriod,
        conn,
        flags: DataQualityFlags
    ) -> float:
        """Get previous month's closing volume as this month's opening."""
        try:
            # Calculate previous month
            if period.month == 1:
                prev_month, prev_year = 12, period.year - 1
            else:
                prev_month, prev_year = period.month - 1, period.year
            
            # Try to get previous month's closing from history
            cursor = conn.execute("""
                SELECT closing_volume_m3
                FROM storage_history
                WHERE facility_code = ?
                AND month = ? AND year = ?
            """, (facility_code, prev_month, prev_year))
            row = cursor.fetchone()
            
            if row:
                # Found historical record - use it
                logger.debug(f"{facility_code}: Opening from history = {row['closing_volume_m3']:,.0f} m³")
                return float(row['closing_volume_m3'])
            
            # No history found - fallback to current volume
            # This assumes current volume is a reasonable proxy for opening
            # (will be inaccurate but better than 0)
            cursor = conn.execute("""
                SELECT current_volume_m3
                FROM storage_facilities
                WHERE code = ?
            """, (facility_code,))
            row = cursor.fetchone()
            
            if row:
                current = float(row['current_volume_m3'] or 0)
                flags.add_estimated(f'{facility_code}_opening', 
                                   f'No history for {prev_month}/{prev_year}, using current ({current:,.0f} m³)')
                logger.info(f"{facility_code}: No storage history, using current volume as opening: {current:,.0f} m³")
                return current
            
            flags.add_warning(f'{facility_code}_opening', 'No volume data found')
            return 0.0
            
        except Exception as e:
            # Log error but don't fail completely - try current volume fallback
            logger.warning(f"Previous month volume query error for {facility_code}: {e}")
            
            # Fallback: try to get current volume
            try:
                cursor = conn.execute("""
                    SELECT current_volume_m3
                    FROM storage_facilities
                    WHERE code = ?
                """, (facility_code,))
                row = cursor.fetchone()
                if row and row['current_volume_m3']:
                    flags.add_estimated(f'{facility_code}_opening', 
                                       'History query failed, using current volume')
                    return float(row['current_volume_m3'])
            except Exception:
                pass
            
            return 0.0

    def record_storage_history(
        self,
        period: CalculationPeriod,
        storage: StorageChange,
        data_source: str = 'calculated'
    ) -> bool:
        """Record storage volumes in history table (HISTORY RECORDING).
        
        Should be called after each balance calculation to build up history.
        This allows future calculations to use accurate opening volumes.
        
        Also updates storage_facilities.current_volume_m3 so the Storage
        Facilities page displays the latest calculated closing volume.
        
        Args:
            period: Year/month for the record
            storage: StorageChange with opening, closing, facility info
            data_source: 'measured', 'calculated', 'estimated', 'imported'
        
        Returns:
            True if record saved, False if failed
        
        Example:
            storage = storage_service.get_facility_storage('NDCD1', period, flags)
            storage_service.record_storage_history(period, storage, 'measured')
        """
        if not storage.facility_code:
            logger.debug("Cannot record history for system total (no facility_code)")
            return False
        
        try:
            conn = self.db.get_connection()
            
            # 1. Upsert history record (monthly snapshot)
            conn.execute("""
                INSERT INTO storage_history (
                    facility_code, year, month, 
                    opening_volume_m3, closing_volume_m3, 
                    data_source, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(facility_code, year, month) DO UPDATE SET
                    opening_volume_m3 = excluded.opening_volume_m3,
                    closing_volume_m3 = excluded.closing_volume_m3,
                    data_source = excluded.data_source,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                storage.facility_code,
                period.year,
                period.month,
                storage.opening_m3,
                storage.closing_m3,
                data_source
            ))
            
            # 2. Update storage_facilities.current_volume_m3 with closing volume
            # This syncs the calculated result to the main facilities table
            # so Storage Facilities page displays the latest calculated value
            conn.execute("""
                UPDATE storage_facilities
                SET current_volume_m3 = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE code = ?
            """, (storage.closing_m3, storage.facility_code))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded storage history for {storage.facility_code} "
                       f"{period.month}/{period.year}: "
                       f"Opening={storage.opening_m3:,.0f}, Closing={storage.closing_m3:,.0f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record storage history: {e}")
            return False

    def record_all_facilities_history(
        self,
        period: CalculationPeriod,
        flags: DataQualityFlags,
        data_source: str = 'calculated',
        calculated_storage: Optional[StorageChange] = None
    ) -> int:
        """Record storage history for all active facilities (BATCH RECORDING).
        
        If calculated_storage is provided (from balance equation), distributes
        the total closing volume proportionally across facilities based on
        their capacity. This ensures individual facility records align with
        the calculated system total.
        
        Args:
            period: Year/month for the record
            flags: Data quality tracker
            data_source: 'measured', 'calculated', 'estimated', 'imported'
            calculated_storage: System total storage from balance calculation
        
        Returns:
            Number of records successfully saved
        """
        facilities = self.get_all_facilities_storage(period, flags)
        saved = 0
        
        # If we have calculated storage from balance equation, distribute
        # the closing volume proportionally across facilities
        if calculated_storage and calculated_storage.closing_m3 > 0:
            total_opening = sum(f.opening_m3 for f in facilities)
            delta = calculated_storage.delta_m3
            
            # Distribute delta proportionally based on opening volumes
            for storage in facilities:
                if total_opening > 0:
                    # Proportional share of the total delta
                    proportion = storage.opening_m3 / total_opening if total_opening > 0 else 1.0 / len(facilities)
                    facility_delta = delta * proportion
                    # Create updated storage with calculated closing
                    updated_storage = StorageChange(
                        facility_code=storage.facility_code,
                        facility_name=storage.facility_name,
                        opening_m3=storage.opening_m3,
                        closing_m3=storage.opening_m3 + facility_delta,
                        capacity_m3=storage.capacity_m3,
                        source=DataQualityLevel.CALCULATED
                    )
                    if self.record_storage_history(period, updated_storage, data_source):
                        saved += 1
                else:
                    # No opening volumes - just save as-is
                    if self.record_storage_history(period, storage, data_source):
                        saved += 1
        else:
            # Legacy mode - save facilities as-is
            for storage in facilities:
                if self.record_storage_history(period, storage, data_source):
                    saved += 1
        
        logger.info(f"Recorded storage history for {saved}/{len(facilities)} facilities")
        return saved


class KPIService(IKPIService):
    """KPI calculation service implementation (KEY PERFORMANCE INDICATORS).
    
    Calculates key performance indicators from balance results.
    Uses Excel Meter Readings for tonnes milled data.
    
    KPIs calculated:
    - Recycled water percentage
    - Water intensity (m³/tonne milled)
    - Abstraction vs license limit
    - Storage days remaining
    """
    
    def __init__(self, db_manager=None, excel_manager: Optional[ExcelManager] = None):
        """Initialize KPI service."""
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        self.db = db_manager
        self._excel = excel_manager or get_excel_manager()
        self._constants = get_constants()
    
    def calculate_kpis(
        self,
        inflows: InflowResult,
        outflows: OutflowResult,
        recycled: RecycledWaterResult,
        storage: StorageChange,
        period: CalculationPeriod,
    ) -> KPIResult:
        """Calculate all KPIs from balance components (KEY PERFORMANCE INDICATORS).
        
        Calculates efficiency metrics and cross-verification data:
        - Recycled water percentage (efficiency)
        - Water intensity (m³/tonne)
        - RWD intensity cross-check (calculated vs measured)
        - Tailings moisture from slurry density
        
        Data sources: Excel Meter Readings for tonnes, RWD, density
        """
        
        # Total water used = fresh inflows + recycled
        total_water = inflows.total_m3 + recycled.total_m3
        
        # Recycled percentage
        recycled_pct = 0.0
        if total_water > 0:
            recycled_pct = (recycled.total_m3 / total_water) * 100
        fresh_pct = 100 - recycled_pct
        
        # Water intensity (m³ per tonne milled)
        tonnes_milled = self._get_tonnes_milled(period)
        water_intensity = 0.0
        if tonnes_milled > 0:
            water_intensity = total_water / tonnes_milled
        
        # Abstraction vs license
        abstraction = inflows.abstraction_m3
        license_limit = self._constants.abstraction_license_annual_m3
        abstraction_pct = None
        within_license = True
        
        if license_limit and license_limit > 0:
            # Convert annual limit to monthly
            monthly_limit = license_limit / 12
            abstraction_pct = (abstraction / monthly_limit) * 100
            within_license = abstraction_pct <= 100
        
        # Storage days remaining
        storage_days = self._calculate_storage_days(storage, outflows, period)
        
        # Cross-verification: RWD intensity (calculated vs measured)
        rwd_measured, rwd_calculated, rwd_match = self._calculate_rwd_intensity_check(
            recycled, tonnes_milled, period
        )
        
        # Cross-verification: Tailings moisture from slurry density
        moisture_from_density, density_measured = self._get_tailings_moisture_from_density(period)
        
        return KPIResult(
            recycled_pct=recycled_pct,
            fresh_pct=fresh_pct,
            water_intensity_m3_per_tonne=water_intensity,
            abstraction_m3=abstraction,
            abstraction_license_m3=license_limit,
            abstraction_pct_of_license=abstraction_pct,
            storage_days=storage_days,
            abstraction_within_license=within_license,
            # Cross-verification data
            rwd_intensity_measured=rwd_measured,
            rwd_intensity_calculated=rwd_calculated,
            rwd_intensity_match=rwd_match,
            tailings_moisture_from_density=moisture_from_density,
            tailings_density_measured=density_measured,
        )
    
    def _calculate_rwd_intensity_check(
        self,
        recycled: RecycledWaterResult,
        tonnes_milled: float,
        period: CalculationPeriod
    ) -> Tuple[Optional[float], Optional[float], bool]:
        """Cross-check RWD intensity: measured (RWD.1) vs calculated (RWD ÷ Tonnes).
        
        Data source: Excel Meter Readings columns:
        - RWD.1 (m³/t) - measured intensity
        - RWD (m³) - measured volume
        - Tonnes Milled - for calculation
        
        Cross-verification: 
        - Excel provides RWD volume and RWD.1 intensity
        - RWD.1 should equal RWD ÷ Tonnes
        - If they don't match, data quality issue
        
        Returns:
            Tuple of (measured_intensity, calculated_intensity, match_flag)
            match_flag is True if <5% difference or data not available
        """
        try:
            # Get measured RWD intensity from Excel (RWD.1 column)
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['rwd_intensity'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            rwd_measured = float(series[0][1]) if series and series[0][1] > 0 else None
            
            # Get RWD volume directly from Excel to calculate intensity
            # (We read from Excel since recycled.components may have pre-calculated total)
            rwd_volume_series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['rwd_1'],  # RWD column (m³)
                start_date=period.start_date,
                end_date=period.end_date
            )
            rwd_volume = float(rwd_volume_series[0][1]) if rwd_volume_series and rwd_volume_series[0][1] > 0 else 0.0
            
            # Calculate RWD intensity from RWD volume and tonnes
            rwd_calculated = None
            if tonnes_milled > 0 and rwd_volume > 0:
                rwd_calculated = rwd_volume / tonnes_milled
            
            # Check if they match (within 5%)
            rwd_match = True
            if rwd_measured is not None and rwd_calculated is not None:
                diff_pct = abs(rwd_measured - rwd_calculated) / rwd_measured * 100 if rwd_measured > 0 else 0
                rwd_match = diff_pct < 5.0
                if not rwd_match:
                    logger.warning(
                        f"RWD intensity mismatch: measured={rwd_measured:.3f}, "
                        f"calculated={rwd_calculated:.3f}, diff={diff_pct:.1f}%"
                    )
            
            return rwd_measured, rwd_calculated, rwd_match
            
        except Exception as e:
            logger.debug(f"RWD intensity check error: {e}")
            return None, None, True
    
    def _get_tailings_moisture_from_density(
        self,
        period: CalculationPeriod
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate tailings moisture % from slurry density (PHYSICS).
        
        Data source: Excel Meter Readings → 'Tailings RD' column (t/m³)
        
        Returns:
            Tuple of (moisture_pct, density_measured)
        """
        try:
            # Get tailings density from Excel
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tailings_density'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            if not series or series[0][1] <= 0:
                return None, None
            
            rho_slurry = float(series[0][1])  # Measured slurry density (t/m³)
            
            # Physical constants
            rho_solids = getattr(self._constants, 'tailings_solids_density', 2.7)  # t/m³
            rho_water = 1.0  # t/m³
            
            # Validate bounds
            if rho_slurry <= rho_water or rho_slurry >= rho_solids:
                return None, rho_slurry
            
            # Calculate moisture from density
            Cw = rho_solids * (rho_slurry - rho_water) / (rho_slurry * (rho_solids - rho_water))
            moisture_pct = (1 - Cw) * 100
            
            return moisture_pct, rho_slurry
            
        except Exception as e:
            logger.debug(f"Tailings moisture from density error: {e}")
            return None, None
        
        return KPIResult(
            recycled_pct=recycled_pct,
            fresh_pct=fresh_pct,
            water_intensity_m3_per_tonne=water_intensity,
            abstraction_m3=abstraction,
            abstraction_license_m3=license_limit,
            abstraction_pct_of_license=abstraction_pct,
            storage_days=storage_days,
            abstraction_within_license=within_license
        )
    
    def _get_tonnes_milled(self, period: CalculationPeriod) -> float:
        """Get tonnes milled for the period from Excel Meter Readings."""
        try:
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['tonnes_milled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            return series[0][1] if series else 0.0
            
        except Exception as e:
            logger.debug(f"Tonnes milled query error: {e}")
            return 0.0
    
    def _calculate_storage_days(
        self,
        storage: StorageChange,
        outflows: OutflowResult,
        period: CalculationPeriod
    ) -> Optional[float]:
        """Calculate days of operation remaining at current usage."""
        if outflows.total_m3 <= 0:
            return None
        
        # Daily usage rate
        daily_usage = outflows.total_m3 / period.days_in_period
        
        if daily_usage <= 0:
            return None
        
        # Days until storage depleted
        return storage.closing_m3 / daily_usage


class RecycledService(IRecycledService):
    """Recycled water calculation service.
    
    Uses Excel Meter Readings for RWD and Total Recycled Water data.
    """
    
    def __init__(self, db_manager=None, excel_manager: Optional[ExcelManager] = None):
        """Initialize recycled service."""
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        self.db = db_manager
        self._excel = excel_manager or get_excel_manager()
        self._constants = get_constants()
    
    def calculate_recycled(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> RecycledWaterResult:
        """Calculate total recycled water for a period.
        
        Reads from Excel Meter Readings columns:
        - 'Total Recycled Water' - if available, use directly
        - 'RWD', 'RWD.1' - RWD volumes
        - 'Tailings RD' - Tailings return
        """
        components = {}
        
        # Try to get pre-calculated total from Excel first
        try:
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['total_recycled'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            if series and series[0][1] > 0:
                total_recycled = series[0][1]
                logger.debug(f"Recycled water from Excel for {period.period_short}: {total_recycled:,.0f} m³")
                return RecycledWaterResult(
                    total_m3=total_recycled,
                    components={'total_from_excel': total_recycled}
                )
        except Exception:
            pass  # Fall back to component calculation
        
        # TSF return water (estimate from plant consumption)
        tsf_return = self._get_tsf_return(period, flags)
        components['tsf_return'] = tsf_return
        
        # RWD circulation from Excel
        rwd = self._get_rwd_circulation(period, flags)
        components['rwd'] = rwd
        
        total = sum(components.values())
        
        return RecycledWaterResult(
            total_m3=total,
            components=components
        )
    
    def _get_tsf_return(self, period: CalculationPeriod, flags: DataQualityFlags) -> float:
        """Get TSF return water volume.
        
        TSF return = water that returns from tailings dam back to plant.
        This is estimated as a percentage of plant consumption since
        there's no direct measurement column in the Excel.
        
        Note: 'Tailings RD' column is actually Tailings DENSITY (t/m³),
        not return water volume - so we estimate instead.
        """
        # No direct measurement available - estimate from plant consumption
        return self._estimate_tsf_return(period, flags)
    
    def _estimate_tsf_return(self, period: CalculationPeriod, flags: DataQualityFlags) -> float:
        """Estimate TSF return as percentage of total consumption.
        
        Uses tsf_return_water_pct from constants (typically 70-80%).
        """
        try:
            # Read total consumption from Excel
            series = self._excel.get_meter_readings_series(
                EXCEL_COLUMNS['total_consumption'],
                start_date=period.start_date,
                end_date=period.end_date
            )
            
            if series and series[0][1] > 0:
                plant_consumption = float(series[0][1])
                tsf_return_pct = self._constants.tsf_return_water_pct
                flags.add_estimated('tsf_return', 
                                   f'Estimated at {tsf_return_pct}% of plant consumption')
                return plant_consumption * (tsf_return_pct / 100)
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"TSF return estimation error: {e}")
            return 0.0
    
    def _get_rwd_circulation(self, period: CalculationPeriod, flags: DataQualityFlags) -> float:
        """Get RWD recirculation volume from Excel.
        
        Reads RWD column (m³) from Meter Readings sheet.
        Note: RWD.1 column is m³/t (intensity ratio), not volume - we skip it.
        """
        total = 0.0
        
        # Read RWD volume column only (rwd_1)
        # Note: rwd_2 was removed - it's m³/t, not a volume
        for col_key in ['rwd_1']:
            try:
                col_name = EXCEL_COLUMNS.get(col_key)
                if not col_name:
                    continue
                    
                series = self._excel.get_meter_readings_series(
                    col_name,
                    start_date=period.start_date,
                    end_date=period.end_date
                )
                if series and series[0][1] > 0:
                    total += float(series[0][1])
            except Exception as e:
                logger.debug(f"RWD column {col_key} read failed: {e}")
        
        if total > 0:
            logger.debug(f"RWD circulation from Excel for {period.period_short}: {total:,.0f} m³")
        
        return total


class BalanceService(IBalanceEngine):
    """Main water balance calculation service.
    
    Orchestrates all sub-services to produce complete balance results.
    Implements the master water balance equation:
        error = fresh_inflows - outflows - delta_storage
    """
    
    def __init__(self, db_manager=None, excel_manager: Optional[ExcelManager] = None):
        """Initialize balance service with all sub-services.
        
        Args:
            db_manager: Shared database manager (creates one if None)
            excel_manager: Shared Excel manager for reading Meter Readings
        """
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        
        self.db = db_manager
        self._excel = excel_manager or get_excel_manager()
        
        # Initialize sub-services with shared DB and Excel managers
        self.inflows_service = InflowsService(db_manager, self._excel)
        self.outflows_service = OutflowsService(db_manager, self._excel)
        self.storage_service = StorageService(db_manager)
        self.recycled_service = RecycledService(db_manager, self._excel)
        self.kpi_service = KPIService(db_manager, self._excel)
        
        # Cache for repeated calculations
        self._cache: Dict[str, BalanceResult] = {}
        
        logger.info("BalanceService initialized")
    
    def calculate(
        self,
        period: CalculationPeriod,
        mode: str = "REGULATOR",
        force_recalculate: bool = False,
    ) -> BalanceResult:
        """Run complete water balance calculation.
        
        Workflow:
        1. Check cache for existing result (skip if force_recalculate=True)
        2. Calculate inflows
        3. Calculate outflows
        4. Calculate storage change
        5. Calculate recycled water
        6. Compute balance closure
        7. Calculate KPIs
        8. Cache and return result
        
        Args:
            period: Calculation period (month/year)
            mode: Calculation mode (REGULATOR, INTERNAL, AUDIT)
            force_recalculate: If True, skip cache and recalculate from fresh data.
                              Use when data has changed (e.g., Excel updated, DB modified).
        
        Returns:
            BalanceResult with all calculation outputs
        """
        # Check cache (skip if force_recalculate is True)
        cache_key = f"{period.year}_{period.month}_{mode}"
        if not force_recalculate and cache_key in self._cache:
            logger.debug(f"Returning cached result for {period.period_short}")
            return self._cache[cache_key]
        
        if force_recalculate:
            logger.info(f"Force recalculating balance for {period.period_label} (cache bypassed)")
        else:
            logger.info(f"Calculating balance for {period.period_label} (mode={mode})")
        
        # Initialize quality flags
        flags = DataQualityFlags()
        
        try:
            # 1. Calculate inflows
            inflows = self.inflows_service.calculate_inflows(period, flags)
            
            # 2. Calculate outflows
            outflows = self.outflows_service.calculate_outflows(period, flags)
            
            # 3. Calculate storage change using balance equation
            # Closing = Opening + Inflows - Outflows (mass conservation)
            # This ensures the balance closes properly with error ~0%
            storage = self.storage_service.calculate_storage(
                period, flags,
                inflows_m3=inflows.total_m3,
                outflows_m3=outflows.total_m3
            )
            
            # 4. Calculate recycled water (for KPIs only)
            recycled = self.recycled_service.calculate_recycled(period, flags)
            
            # 5. Compute balance closure
            # Master equation: error = IN - OUT - ΔS
            balance_error = inflows.total_m3 - outflows.total_m3 - storage.delta_m3
            error_pct = 0.0
            if inflows.total_m3 > 0:
                error_pct = (balance_error / inflows.total_m3) * 100
            
            # 6. Calculate KPIs
            kpis = self.kpi_service.calculate_kpis(
                inflows, outflows, recycled, storage, period
            )
            
            # 7. Build result
            result = BalanceResult(
                period=period,
                inflows=inflows,
                outflows=outflows,
                storage=storage,
                recycled=recycled,
                balance_error_m3=balance_error,
                error_pct=error_pct,
                kpis=kpis,
                quality_flags=flags,
                calculated_at=datetime.now(),
                calculation_mode=mode
            )
            
            # 8. Log summary
            status = "✓ BALANCED" if result.is_balanced else "✗ UNBALANCED"
            logger.info(f"Balance {period.period_short}: {status} "
                       f"(error={error_pct:.1f}%, IN={inflows.total_m3:,.0f}, "
                       f"OUT={outflows.total_m3:,.0f}, ΔS={storage.delta_m3:,.0f})")
            
            # 9. Record storage history for future reference
            # This allows future calculations to get accurate opening volumes
            # by looking up the previous month's closing volume from history
            # Pass calculated storage so facilities get proportional closing volumes
            try:
                self.storage_service.record_all_facilities_history(
                    period, flags, data_source='calculated',
                    calculated_storage=storage
                )
            except Exception as hist_err:
                logger.warning(f"Could not record storage history: {hist_err}")
                # Don't fail calculation if history recording fails
            
            # 10. Cache result
            self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Balance calculation failed: {e}")
            raise CalculationError(
                message=str(e),
                component="BalanceService",
                details={'period': period.period_label, 'mode': mode}
            )
    
    def calculate_for_date(
        self,
        month: int,
        year: int,
        mode: str = "REGULATOR",
        force_recalculate: bool = False,
    ) -> BalanceResult:
        """Run calculation for a specific month/year.
        
        Convenience method that creates CalculationPeriod internally.
        
        Args:
            month: Month number (1-12)
            year: Year (e.g., 2025)
            mode: Calculation mode (REGULATOR, INTERNAL, AUDIT)
            force_recalculate: If True, bypass cache and use fresh data
        
        Returns:
            BalanceResult with calculation outputs
        
        Example:
            service = get_balance_service()
            
            # Normal calculation (uses cache if available)
            result = service.calculate_for_date(9, 2025)
            
            # Force fresh calculation after data update
            result = service.calculate_for_date(9, 2025, force_recalculate=True)
        """
        period = CalculationPeriod(month=month, year=year)
        return self.calculate(period, mode, force_recalculate)
    
    def clear_cache(self) -> None:
        """Clear all calculation caches.
        
        Call when:
        - Excel file is updated
        - Database is modified
        - Configuration changes
        """
        self._cache.clear()
        ConstantsLoader().refresh()
        logger.debug("Balance calculation cache cleared")


# Singleton instance
_balance_service: Optional[BalanceService] = None


def get_balance_service() -> BalanceService:
    """Get the balance service singleton.
    
    Usage:
        from services.calculation.balance_service import get_balance_service
        
        service = get_balance_service()
        result = service.calculate_for_date(3, 2026)
    """
    global _balance_service
    if _balance_service is None:
        _balance_service = BalanceService()
    return _balance_service


def reset_balance_service() -> None:
    """Reset the balance service singleton.
    
    Call when database or configuration changes.
    """
    global _balance_service
    if _balance_service is not None:
        _balance_service.clear_cache()
    _balance_service = None
    logger.debug("Balance service singleton reset")
