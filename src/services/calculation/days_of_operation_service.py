"""
Days of Operation Service (WATER RUNWAY ANALYSIS).

Purpose:
- Calculate how many days water storage will last at current usage
- Project storage depletion using monthly consumption rates
- Account for seasonal rainfall and evaporation variability
- Provide early warning indicators for water scarcity

Scientific Approach:
1. Convert monthly usage data to daily rates
2. Apply seasonal factors for rainfall/evaporation
3. Project month-by-month until storage depleted
4. Provide conservative and optimistic scenarios

Key Equations:
    Net_Daily_Consumption = (Monthly_Usage / days_in_month)
                          - (Monthly_Rainfall × Catchment_Area / days_in_month)
                          + (Monthly_Evaporation × Surface_Area / days_in_month)
    
    Days_Remaining = Available_Storage / Net_Daily_Consumption
    
    Available_Storage = Current_Volume - Minimum_Reserve
                        (can't run facilities to zero)

Data Sources:
    - storage_facilities table: current volumes, capacities, surface areas
    - storage_history table: monthly closing volumes (for trend analysis)
    - environmental_data table: monthly evaporation/rainfall by region
    - Balance calculation: monthly consumption rates (outflows)

Dependencies:
    - StorageService: for facility data
    - EnvironmentalService: for evaporation/rainfall
    - BalanceService: for consumption rates
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from calendar import monthrange
from pydantic import BaseModel, Field

from database.db_manager import DatabaseManager
from services.calculation.constants import get_constants

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class MonthlyProjection(BaseModel):
    """Projection data for a single month (MONTHLY PROJECTION).
    
    Used in the storage depletion curve - each month has:
    - Expected consumption, rainfall gain, evaporation loss
    - Resulting volume at month end
    - Remaining days if volume goes negative this month
    """
    month: int = Field(..., ge=1, le=12, description="Month number (1-12)")
    year: int = Field(..., description="Year")
    month_name: str = Field(..., description="Month name (e.g., 'March 2026')")
    days_in_month: int = Field(..., description="Days in this month")
    
    # Daily rates (m³/day)
    daily_consumption: float = Field(default=0.0, description="Daily water usage rate")
    daily_rainfall_gain: float = Field(default=0.0, description="Daily rainfall gain")
    daily_evaporation_loss: float = Field(default=0.0, description="Daily evaporation loss")
    net_daily_rate: float = Field(default=0.0, description="Net daily consumption (consumption - rain + evap)")
    
    # Monthly totals (m³)
    monthly_consumption: float = Field(default=0.0, description="Total consumption this month")
    monthly_rainfall_gain: float = Field(default=0.0, description="Total rainfall gain this month")
    monthly_evaporation_loss: float = Field(default=0.0, description="Total evaporation loss this month")
    net_monthly_change: float = Field(default=0.0, description="Net storage change this month")
    
    # Volumes (m³)
    opening_volume: float = Field(default=0.0, description="Storage at start of month")
    closing_volume: float = Field(default=0.0, description="Storage at end of month")
    
    # Status
    depleted: bool = Field(default=False, description="True if storage depleted this month")
    days_until_depletion: Optional[int] = Field(None, description="Days until depletion (if this month)")


class FacilityRunway(BaseModel):
    """Days of operation analysis for a single facility (FACILITY RUNWAY).
    
    Contains:
    - Current status (volume, capacity, utilization)
    - Consumption rates (daily/monthly)
    - Environmental factors (evaporation, rainfall gains)
    - Runway projection (days remaining, depletion date)
    """
    facility_code: str = Field(..., description="Facility code (e.g., 'NDCD1')")
    facility_name: str = Field(..., description="Facility display name")
    
    # Current status
    current_volume_m3: float = Field(default=0.0, description="Current storage volume")
    capacity_m3: float = Field(default=0.0, description="Maximum capacity")
    utilization_pct: float = Field(default=0.0, description="Current utilization percentage")
    surface_area_m2: float = Field(default=0.0, description="Water surface area for evaporation")
    
    # Consumption rates (from latest balance calculation)
    monthly_consumption_m3: float = Field(default=0.0, description="Monthly consumption rate")
    daily_consumption_m3: float = Field(default=0.0, description="Daily consumption rate")
    
    # Environmental factors
    monthly_evaporation_m3: float = Field(default=0.0, description="Monthly evaporation loss")
    monthly_rainfall_gain_m3: float = Field(default=0.0, description="Monthly rainfall gain")
    
    # Net rates
    net_daily_consumption_m3: float = Field(default=0.0, description="Net daily consumption (after environmental)")
    
    # Runway analysis
    minimum_reserve_m3: float = Field(default=0.0, description="Minimum reserve (can't go below)")
    available_storage_m3: float = Field(default=0.0, description="Usable storage above minimum")
    
    # Results - Conservative scenario (dry season rates)
    days_remaining_conservative: int = Field(default=0, description="Days remaining (worst case)")
    depletion_date_conservative: Optional[date] = Field(None, description="Expected depletion date (worst case)")
    
    # Results - Optimistic scenario (with average rainfall)
    days_remaining_optimistic: int = Field(default=0, description="Days remaining (best case)")
    depletion_date_optimistic: Optional[date] = Field(None, description="Expected depletion date (best case)")
    
    # Monthly projections (for charts)
    monthly_projections: List[MonthlyProjection] = Field(default_factory=list, description="Month-by-month projection")
    
    # Status indicators
    status: str = Field(default="UNKNOWN", description="Status: CRITICAL (<30d), WARNING (30-90d), OK (>90d)")
    status_color: str = Field(default="#999999", description="Color code for status display")


class SystemRunway(BaseModel):
    """System-wide days of operation analysis (SYSTEM RUNWAY).
    
    Industry-Standard Water Runway Calculation (ICMM/AMIRA P754 aligned):
    
    Equations:
        Usable_Storage = Current_Volume - Dead_Storage (10% reserve)
        Net_Fresh_Demand = Process_Outflows - Recycled_Water_Recovery
        Gross_Floor_Demand = Gross_Outflows × Floor_Pct
        Runway_Daily_Demand = max(Net_Fresh_Demand, Gross_Floor_Demand)
        Days_Remaining = Usable_Storage / Runway_Daily_Demand
    
    The limiting factor is the facility that runs out first.
    """
    calculation_date: datetime = Field(default_factory=datetime.now, description="When analysis was run")
    analysis_period: str = Field(..., description="Period analyzed (e.g., 'September 2025')")
    
    # System totals
    total_current_volume_m3: float = Field(default=0.0, description="Total system storage")
    total_capacity_m3: float = Field(default=0.0, description="Total system capacity")
    system_utilization_pct: float = Field(default=0.0, description="System-wide utilization")
    
    # ICMM-aligned consumption metrics (Industry Standard)
    total_daily_consumption_m3: float = Field(default=0.0, description="Total daily consumption (legacy)")
    total_monthly_consumption_m3: float = Field(default=0.0, description="Total monthly consumption")
    
    # NEW: Industry-standard demand metrics
    total_outflows_m3: float = Field(default=0.0, description="Monthly outflows (water leaving system)")
    recycled_water_m3: float = Field(default=0.0, description="Monthly recycled water recovered")
    net_fresh_demand_m3: float = Field(default=0.0, description="Net fresh water demand (outflows - recycled)")
    daily_net_fresh_demand_m3: float = Field(default=0.0, description="Daily net fresh water demand")
    net_fresh_daily_demand_m3: float = Field(default=0.0, description="Daily net fresh demand (same as daily_net_fresh_demand_m3)")
    gross_outflow_daily_m3: float = Field(default=0.0, description="Daily gross outflows")
    gross_floor_daily_m3: float = Field(default=0.0, description="Daily gross outflow floor demand")
    runway_daily_demand_m3: float = Field(default=0.0, description="Selected daily demand for runway calculation")
    runway_demand_method: str = Field(default="zero", description="Method used: 'net', 'floor', or 'zero'")
    
    # Environmental losses (tracked separately per ICMM)
    evaporation_loss_m3: float = Field(default=0.0, description="Monthly evaporation loss")
    seepage_loss_m3: float = Field(default=0.0, description="Monthly seepage loss")
    
    # Usable storage (excludes 10% dead storage)
    usable_storage_m3: float = Field(default=0.0, description="Storage above minimum reserve")
    minimum_reserve_m3: float = Field(default=0.0, description="Dead storage (10% of capacity)")
    
    # System runway (limited by first facility to deplete)
    system_days_remaining: int = Field(default=0, description="Days until first facility depletes")
    combined_days_remaining: Optional[int] = Field(default=None, description="Days for combined system (usable storage / selected daily demand)")
    limiting_facility: str = Field(default="", description="Facility that will deplete first")
    
    # Per-facility breakdown
    facilities: List[FacilityRunway] = Field(default_factory=list, description="Per-facility analysis")
    
    # Quality flags
    data_quality_notes: List[str] = Field(default_factory=list, description="Data quality warnings")
    consumption_source: str = Field(default="estimated", description="Source: 'measured', 'outflows', 'estimated'")


# =============================================================================
# SERVICE IMPLEMENTATION
# =============================================================================

class DaysOfOperationService:
    """Days of Operation calculation service (WATER RUNWAY ENGINE).
    
    Calculates how many days water storage will last based on:
    1. Current storage volumes
    2. Recent consumption rates (from balance calculations)
    3. Seasonal rainfall and evaporation forecasts
    4. Minimum reserve requirements
    
    Provides two scenarios:
    - CONSERVATIVE: Uses dry season rates (minimal rainfall, high evaporation)
    - OPTIMISTIC: Uses historical average rates
    
    Usage:
        service = DaysOfOperationService()
        result = service.calculate_runway(month=9, year=2025)
        logger.info("System runway: %s days", result.system_days_remaining)
        
        for facility in result.facilities:
            logger.info(
                "%s: %s days",
                facility.facility_name,
                facility.days_remaining_conservative
            )
    """
    
    # Minimum reserve as percentage of capacity (can't run to zero)
    MINIMUM_RESERVE_PCT = 0.10  # 10% reserve
    
    # Burgersfort region environmental data (monthly averages)
    # Source: South African Weather Service historical data
    # Units: mm/month for evaporation and rainfall
    REGIONAL_EVAPORATION_MM = {
        1: 180,   # January (summer - high evap)
        2: 160,   # February
        3: 150,   # March (autumn)
        4: 120,   # April
        5: 90,    # May (winter - low evap)
        6: 75,    # June
        7: 80,    # July
        8: 100,   # August
        9: 130,   # September (spring)
        10: 150,  # October
        11: 165,  # November
        12: 175,  # December
    }
    
    REGIONAL_RAINFALL_MM = {
        1: 110,   # January (wet season)
        2: 95,    # February
        3: 70,    # March
        4: 35,    # April (transition)
        5: 10,    # May (dry season)
        6: 5,     # June
        7: 5,     # July
        8: 5,     # August
        9: 15,    # September (transition)
        10: 55,   # October
        11: 90,   # November
        12: 105,  # December (wet season)
    }
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize Days of Operation service.
        
        Args:
            db_manager: Database manager for facility data access
        """
        if db_manager is None:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
        
        self.db = db_manager
        self._constants = get_constants()
        logger.info("DaysOfOperationService initialized")
    
    def calculate_runway(
        self,
        month: int,
        year: int,
        projection_months: int = 12,
        balance_result: Optional[Any] = None
    ) -> SystemRunway:
        """Calculate system-wide water runway (INDUSTRY-STANDARD CALCULATION).
        
        ICMM/AMIRA P754 Aligned Methodology:
        
        Equations:
            Usable_Storage = Current_Volume - Dead_Storage (10% minimum reserve)
            Net_Fresh_Demand = Total_Outflows - Recycled_Water_Recovery
            Gross_Floor_Demand = Gross_Outflows × Floor_Pct
            Runway_Daily_Demand = max(Net_Fresh_Demand, Gross_Floor_Demand)
            Days_Remaining = Usable_Storage / Runway_Daily_Demand
        
        Data Sources (priority order):
            1. balance_result.outflows (BEST - actual measured/calculated outflows)
            2. storage_history delta (GOOD - opening - closing volumes)
            3. Estimated 5% of capacity (FALLBACK - when no data available)
        
        Args:
            month: Reference month for consumption rates (1-12)
            year: Reference year
            projection_months: How many months to project forward (default 12)
            balance_result: Optional BalanceResult with outflows data (preferred source)
        
        Returns:
            SystemRunway with industry-standard metrics:
            - usable_storage_m3: Storage above minimum reserve
            - runway_daily_demand_m3: Selected daily demand for runway
            - combined_days_remaining: Usable storage / selected daily demand
            - system_days_remaining: First facility to deplete (limiting factor)
        
        Example:
            runway = service.calculate_runway(9, 2025, balance_result=result)
            logger.info("Combined runway: %s days", runway.combined_days_remaining)
            logger.info(
                "Limiting facility: %s (%sd)",
                runway.limiting_facility,
                runway.system_days_remaining
            )
        """
        logger.info(f"Calculating runway for {month}/{year} ({projection_months} months projection)")
        
        # Initialize result
        period_label = f"{self._get_month_name(month)} {year}"
        result = SystemRunway(analysis_period=period_label)
        
        # 1. Get facility data
        facilities = self._get_facilities_data()
        if not facilities:
            result.data_quality_notes.append("No active storage facilities found")
            logger.warning("No facilities found for runway calculation")
            return result
        
        # 2. Get consumption rates - PRIORITY: balance_result outflows > storage_history > estimate
        consumption_rates = {}
        monthly_outflows = 0.0
        recycled_water = 0.0
        evaporation = 0.0
        seepage = 0.0
        
        if balance_result is not None and hasattr(balance_result, 'outflows'):
            # BEST SOURCE: Use actual outflows from balance calculation
            outflows = balance_result.outflows
            monthly_outflows = outflows.total_m3 if outflows else 0.0
            evaporation = getattr(outflows, 'evaporation_m3', 0.0) if outflows else 0.0
            seepage = getattr(outflows, 'seepage_m3', 0.0) if outflows else 0.0
            
            # Get recycled water from balance result (use BalanceResult.recycled)
            if hasattr(balance_result, 'recycled') and balance_result.recycled:
                recycled_water = getattr(balance_result.recycled, 'total_m3', 0.0)
                if recycled_water <= 0 and hasattr(balance_result.recycled, 'components'):
                    # Fall back to specific component if available
                    recycled_water = balance_result.recycled.components.get('rwd', 0.0)
            
            result.consumption_source = "outflows"
            result.data_quality_notes.append("Using measured outflows from balance calculation")
            logger.info(f"Using balance outflows: {monthly_outflows:,.0f} m³/month")
        else:
            # FALLBACK: Try storage_history
            consumption_rates = self._get_consumption_rates(month, year)
            if consumption_rates:
                result.consumption_source = "storage_history"
                result.data_quality_notes.append("Using storage history delta for consumption")
            else:
                result.consumption_source = "estimated"
                result.data_quality_notes.append("Using estimated consumption (5% of capacity)")
        
        # 3. Calculate runway for each facility
        min_days = float('inf')
        limiting_facility = ""
        
        for fac in facilities:
            facility_runway = self._calculate_facility_runway(
                fac, 
                month, 
                year,
                consumption_rates,
                projection_months
            )
            result.facilities.append(facility_runway)
            
            # Track totals
            result.total_current_volume_m3 += facility_runway.current_volume_m3
            result.total_capacity_m3 += facility_runway.capacity_m3
            result.total_daily_consumption_m3 += facility_runway.net_daily_consumption_m3
            
            # Find limiting facility (first to deplete)
            if facility_runway.days_remaining_conservative < min_days:
                min_days = facility_runway.days_remaining_conservative
                limiting_facility = facility_runway.facility_code
        
        # 4. Calculate ICMM-aligned system metrics
        result.minimum_reserve_m3 = result.total_capacity_m3 * self.MINIMUM_RESERVE_PCT
        result.usable_storage_m3 = max(0, result.total_current_volume_m3 - result.minimum_reserve_m3)
        
        # Store outflow components
        result.total_outflows_m3 = monthly_outflows
        result.recycled_water_m3 = recycled_water
        result.evaporation_loss_m3 = evaporation
        result.seepage_loss_m3 = seepage
        
        days_in_selected_month = monthrange(year, month)[1]

        # Hybrid runway demand:
        # - Preserve recycling benefit via net fresh demand
        # - Apply gross outflow floor so demand doesn't collapse to zero while process still runs
        floor_pct = float(getattr(self._constants, 'runway_gross_floor_pct', 0.25) or 0.25)
        if monthly_outflows > 0:
            result.net_fresh_demand_m3 = max(0, monthly_outflows - recycled_water)
            result.daily_net_fresh_demand_m3 = result.net_fresh_demand_m3 / days_in_selected_month
            result.net_fresh_daily_demand_m3 = result.daily_net_fresh_demand_m3
            result.gross_outflow_daily_m3 = monthly_outflows / days_in_selected_month
            result.gross_floor_daily_m3 = result.gross_outflow_daily_m3 * floor_pct
            result.runway_daily_demand_m3 = max(result.net_fresh_daily_demand_m3, result.gross_floor_daily_m3)
            result.runway_demand_method = "net" if result.net_fresh_daily_demand_m3 >= result.gross_floor_daily_m3 else "floor"
        else:
            # Fallback to facility-based consumption
            result.net_fresh_demand_m3 = result.total_daily_consumption_m3 * days_in_selected_month
            result.daily_net_fresh_demand_m3 = result.total_daily_consumption_m3
            result.net_fresh_daily_demand_m3 = result.daily_net_fresh_demand_m3
            result.gross_outflow_daily_m3 = 0.0
            result.gross_floor_daily_m3 = 0.0
            result.runway_daily_demand_m3 = 0.0
            result.runway_demand_method = "zero"
        
        result.total_monthly_consumption_m3 = result.net_fresh_demand_m3
        
        # Calculate combined system days using selected runway demand
        if result.runway_daily_demand_m3 > 0:
            result.combined_days_remaining = int(result.usable_storage_m3 / result.runway_daily_demand_m3)
        else:
            result.combined_days_remaining = None
            result.runway_demand_method = "zero"
        
        if result.total_capacity_m3 > 0:
            result.system_utilization_pct = (result.total_current_volume_m3 / result.total_capacity_m3) * 100
        
        result.system_days_remaining = int(min_days) if min_days != float('inf') else 0
        result.limiting_facility = limiting_facility
        
        logger.info(f"Runway calculated (ICMM method): combined={result.combined_days_remaining}, "
                   f"limiting={limiting_facility} ({result.system_days_remaining}d), "
                   f"daily_demand={result.runway_daily_demand_m3:,.0f} m³/day ({result.runway_demand_method})")
        
        return result
    
    def _get_facilities_data(self) -> List[Dict[str, Any]]:
        """Get active storage facilities from database (DATA RETRIEVAL).
        
        Returns list of dicts with:
            - code, name, capacity_m3, current_volume_m3, surface_area_m2
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.execute("""
                SELECT code, name, capacity_m3, current_volume_m3, 
                       surface_area_m2, status
                FROM storage_facilities
                WHERE status = 'active'
                ORDER BY code
            """)
            
            facilities = []
            for row in cursor:
                facilities.append({
                    'code': row['code'],
                    'name': row['name'],
                    'capacity_m3': float(row['capacity_m3'] or 0),
                    'current_volume_m3': float(row['current_volume_m3'] or 0),
                    'surface_area_m2': float(row['surface_area_m2'] or 0),
                })
            
            conn.close()
            logger.debug(f"Retrieved {len(facilities)} active facilities")
            return facilities
            
        except Exception as e:
            logger.error(f"Failed to get facilities data: {e}")
            return []
    
    def _get_consumption_rates(self, month: int, year: int) -> Dict[str, float]:
        """Get monthly consumption rates from balance calculations.
        
        Attempts to get actual rates from storage_history, falls back to
        estimated rates based on facility capacity.
        
        Args:
            month: Reference month
            year: Reference year
        
        Returns:
            Dict mapping facility_code to monthly consumption (m³)
        """
        rates = {}
        
        try:
            conn = self.db.get_connection()
            
            # Try to get actual consumption from storage history
            # Consumption = opening - closing + inflows
            # Simplified: use delta as proxy
            cursor = conn.execute("""
                SELECT facility_code, 
                       opening_volume_m3,
                       closing_volume_m3,
                       (opening_volume_m3 - closing_volume_m3) as consumption_proxy
                FROM storage_history
                WHERE year = ? AND month = ?
            """, (year, month))
            
            for row in cursor:
                code = row['facility_code']
                # If closing > opening, water was added, so consumption = 0 (or negative)
                # Use absolute value as rough consumption estimate
                consumption = abs(float(row['consumption_proxy'] or 0))
                rates[code] = consumption
                logger.debug(f"{code}: estimated consumption = {consumption:,.0f} m³/month")
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not get consumption rates: {e}")
        
        return rates
    
    def _calculate_facility_runway(
        self,
        facility: Dict[str, Any],
        month: int,
        year: int,
        consumption_rates: Dict[str, float],
        projection_months: int
    ) -> FacilityRunway:
        """Calculate runway for a single facility (FACILITY CALCULATION).
        
        Projects storage depletion month by month, accounting for:
        - Monthly consumption (from balance history or estimated)
        - Evaporation losses (surface area × evaporation rate)
        - Rainfall gains (catchment area × rainfall - simplified)
        - Minimum reserve requirement
        
        Args:
            facility: Dict with code, name, capacity, current_volume, surface_area
            month: Starting month
            year: Starting year
            consumption_rates: Dict of facility_code to monthly consumption
            projection_months: Number of months to project
        
        Returns:
            FacilityRunway with days remaining and monthly projections
        """
        code = facility['code']
        
        # Initialize facility runway
        runway = FacilityRunway(
            facility_code=code,
            facility_name=facility['name'],
            current_volume_m3=facility['current_volume_m3'],
            capacity_m3=facility['capacity_m3'],
            surface_area_m2=facility['surface_area_m2'],
        )
        
        # Calculate utilization
        if runway.capacity_m3 > 0:
            runway.utilization_pct = (runway.current_volume_m3 / runway.capacity_m3) * 100
        
        # Get consumption rate (or estimate)
        if code in consumption_rates:
            runway.monthly_consumption_m3 = consumption_rates[code]
        else:
            # Fallback: estimate as 5% of capacity per month
            runway.monthly_consumption_m3 = runway.capacity_m3 * 0.05
            logger.debug(f"{code}: using estimated consumption (5% of capacity)")
        
        # Calculate minimum reserve
        runway.minimum_reserve_m3 = runway.capacity_m3 * self.MINIMUM_RESERVE_PCT
        runway.available_storage_m3 = max(0, runway.current_volume_m3 - runway.minimum_reserve_m3)
        
        # Project month by month
        current_volume = runway.current_volume_m3
        current_month = month
        current_year = year
        days_total = 0
        depleted = False
        
        for i in range(projection_months):
            # Calculate days in this month
            days_in_month = monthrange(current_year, current_month)[1]
            
            # Get environmental rates for this month
            evap_mm = self.REGIONAL_EVAPORATION_MM.get(current_month, 150)
            rain_mm = self.REGIONAL_RAINFALL_MM.get(current_month, 50)
            
            # Convert to m³ (mm × m² / 1000 = m³)
            monthly_evap_m3 = (evap_mm / 1000) * runway.surface_area_m2
            
            # Rainfall gain: simplified - assume 10% of rainfall is captured
            # (real model would need catchment area data)
            catchment_factor = 0.10  # 10% of rainfall captured
            monthly_rain_m3 = (rain_mm / 1000) * runway.surface_area_m2 * catchment_factor
            
            # Net monthly change
            net_change = (runway.monthly_consumption_m3 - monthly_rain_m3 + monthly_evap_m3)
            
            # Calculate daily rate
            daily_rate = net_change / days_in_month
            
            # Create projection record
            proj = MonthlyProjection(
                month=current_month,
                year=current_year,
                month_name=f"{self._get_month_name(current_month)} {current_year}",
                days_in_month=days_in_month,
                daily_consumption=runway.monthly_consumption_m3 / days_in_month,
                daily_rainfall_gain=monthly_rain_m3 / days_in_month,
                daily_evaporation_loss=monthly_evap_m3 / days_in_month,
                net_daily_rate=daily_rate,
                monthly_consumption=runway.monthly_consumption_m3,
                monthly_rainfall_gain=monthly_rain_m3,
                monthly_evaporation_loss=monthly_evap_m3,
                net_monthly_change=-net_change,  # Negative = losing water
                opening_volume=current_volume,
            )
            
            # Project volume at end of month
            closing_volume = current_volume - net_change
            proj.closing_volume = closing_volume
            
            # Check if depleted this month
            if closing_volume <= runway.minimum_reserve_m3 and not depleted:
                depleted = True
                proj.depleted = True
                
                # Calculate exactly how many days until reserve reached
                available = current_volume - runway.minimum_reserve_m3
                if daily_rate > 0:
                    days_until = int(available / daily_rate)
                    proj.days_until_depletion = days_until
                    days_total += days_until
                else:
                    proj.days_until_depletion = days_in_month
                    days_total += days_in_month
            elif not depleted:
                days_total += days_in_month
            
            runway.monthly_projections.append(proj)
            
            # Move to next month
            current_volume = max(0, closing_volume)
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        # Set runway results
        runway.days_remaining_conservative = days_total
        days_in_selected_month = monthrange(year, month)[1]
        runway.net_daily_consumption_m3 = runway.monthly_consumption_m3 / days_in_selected_month
        
        # Calculate depletion date
        if days_total > 0 and days_total < projection_months * 31:
            from datetime import timedelta
            runway.depletion_date_conservative = date.today() + timedelta(days=days_total)
        
        # Optimistic scenario: reduce net consumption by 20% (more rainfall)
        if runway.net_daily_consumption_m3 > 0:
            optimistic_daily = runway.net_daily_consumption_m3 * 0.8
            if optimistic_daily > 0:
                runway.days_remaining_optimistic = int(runway.available_storage_m3 / optimistic_daily)
            else:
                runway.days_remaining_optimistic = projection_months * 31
        else:
            runway.days_remaining_optimistic = projection_months * 31
        
        # Set status based on conservative days remaining
        runway.status, runway.status_color = self._get_status(runway.days_remaining_conservative)
        
        logger.debug(f"{code}: {runway.days_remaining_conservative} days remaining (conservative)")
        
        return runway
    
    def _get_status(self, days_remaining: int) -> tuple:
        """Determine status category based on days remaining.
        
        Returns:
            Tuple of (status_text, color_code)
        """
        if days_remaining <= 30:
            return "CRITICAL", "#FF0000"  # Red
        elif days_remaining <= 90:
            return "WARNING", "#FFA500"   # Orange
        elif days_remaining <= 180:
            return "MODERATE", "#FFD700"  # Gold
        else:
            return "OK", "#228B22"        # Green
    
    def _get_month_name(self, month: int) -> str:
        """Get month name from number."""
        import calendar
        return calendar.month_name[month]


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_days_of_operation_service: Optional[DaysOfOperationService] = None


def get_days_of_operation_service() -> DaysOfOperationService:
    """Get or create the DaysOfOperationService singleton.
    
    Returns:
        DaysOfOperationService instance
    """
    global _days_of_operation_service
    if _days_of_operation_service is None:
        _days_of_operation_service = DaysOfOperationService()
    return _days_of_operation_service


def reset_days_of_operation_service() -> None:
    """Reset the singleton (for testing or after data changes)."""
    global _days_of_operation_service
    _days_of_operation_service = None
    logger.debug("DaysOfOperationService singleton reset")
