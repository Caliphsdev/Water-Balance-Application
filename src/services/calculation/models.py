"""
Calculation Data Models (TYPE-SAFE I/O).

Pydantic models for water balance calculation inputs and outputs.
All values in cubic meters (m³) unless specified otherwise.

Scientific Basis:
- Water balance equation: IN = OUT + ΔS + Error
- Error < 5% indicates good data quality
- Values should be non-negative (physical constraint)

Usage:
    from services.calculation.models import BalanceResult
    
    result = BalanceResult(
        period=CalculationPeriod(month=3, year=2026),
        inflows=InflowResult(total_m3=45000, ...),
        ...
    )
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import date, datetime
from enum import Enum


class DataQualityLevel(str, Enum):
    """Data quality classification for calculation inputs.
    
    Used to flag whether values are measured (high confidence) or 
    estimated/simulated (lower confidence, needs review).
    """
    MEASURED = "measured"       # From direct measurement (meters, surveys)
    CALCULATED = "calculated"  # Derived from other measured values
    ESTIMATED = "estimated"     # Estimated from historical averages
    SIMULATED = "simulated"     # Simulated/predicted value
    MISSING = "missing"         # Data not available, using default


class DataQualityFlags(BaseModel):
    """Tracks data quality issues for a calculation run.
    
    Used to surface warnings to users about data reliability.
    Helps distinguish measured vs estimated values in audits.
    
    Attributes:
        missing_values: List of input fields that were missing/defaulted
        estimated_values: List of input fields using estimates
        simulated_values: List of input fields using simulation
        warnings: Human-readable warning messages for UI display
        notes: Additional context (e.g., data source, assumptions)
    
    Example:
        flags = DataQualityFlags()
        flags.add_missing('rainfall', 'No rainfall data for March 2026, using 0')
        flags.add_warning('Storage survey is 45 days old - may be inaccurate')
    """
    
    missing_values: List[str] = Field(default_factory=list, description="Fields with missing data")
    estimated_values: List[str] = Field(default_factory=list, description="Fields using estimates")
    simulated_values: List[str] = Field(default_factory=list, description="Fields using simulation")
    warnings: List[str] = Field(default_factory=list, description="Warning messages for UI")
    notes: Dict[str, str] = Field(default_factory=dict, description="Additional context per field")
    
    def add_missing(self, field: str, note: str = "") -> None:
        """Record a missing value flag.
        
        Args:
            field: Name of the missing field (e.g., 'rainfall')
            note: Optional explanation to show in UI
        """
        if field not in self.missing_values:
            self.missing_values.append(field)
        if note:
            self.notes[field] = note
    
    def add_estimated(self, field: str, note: str = "") -> None:
        """Record an estimated value flag.
        
        Args:
            field: Name of the estimated field
            note: Optional explanation (e.g., 'Used 3-month average')
        """
        if field not in self.estimated_values:
            self.estimated_values.append(field)
        if note:
            self.notes[field] = note
    
    def add_simulated(self, field: str, note: str = "") -> None:
        """Record a simulated value flag.
        
        Args:
            field: Name of the simulated field
            note: Optional explanation
        """
        if field not in self.simulated_values:
            self.simulated_values.append(field)
        if note:
            self.notes[field] = note

    def add_calculated(self, field: str, note: str = "") -> None:
        """Record a calculated value (for info/audit, not a quality issue).
        
        This is used for values that are derived from other data,
        not for flagging problems but for audit trail purposes.
        
        Args:
            field: Name of the calculated field
            note: Optional explanation of calculation method
        """
        # Just add to notes - calculated values are not quality issues
        if note:
            self.notes[field] = note
    
    def add_warning(self, message: str) -> None:
        """Add a general warning message for UI display.
        
        Args:
            message: Human-readable warning text
        """
        if message not in self.warnings:
            self.warnings.append(message)
    
    @property
    def has_issues(self) -> bool:
        """Check if any data quality issues exist."""
        return bool(self.missing_values or self.estimated_values or 
                    self.simulated_values or self.warnings)
    
    @property
    def issue_count(self) -> int:
        """Total number of data quality issues."""
        return (len(self.missing_values) + len(self.estimated_values) + 
                len(self.simulated_values) + len(self.warnings))
    
    def as_dict(self) -> Dict[str, any]:
        """Convert to display-friendly dict for UI tooltips."""
        return {
            'missing': self.missing_values,
            'estimated': self.estimated_values,
            'simulated': self.simulated_values,
            'warnings': self.warnings,
            'notes': self.notes,
        }


class CalculationPeriod(BaseModel):
    """Period for calculation (month + year).
    
    Represents a single month period for water balance calculation.
    
    Attributes:
        month: Calendar month (1-12)
        year: Calendar year (e.g., 2026)
        calculation_date: Last day of the period (auto-computed)
        days_in_period: Number of days in month (for daily rates)
    """
    
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., ge=2000, le=2100, description="Year (e.g., 2026)")
    
    @property
    def calculation_date(self) -> date:
        """Get the last day of the calculation period.
        
        Used as the reference date for storage snapshots.
        """
        import calendar
        last_day = calendar.monthrange(self.year, self.month)[1]
        return date(self.year, self.month, last_day)
    
    @property
    def start_date(self) -> date:
        """Get the first day of the calculation period.
        
        Used for Excel range queries that span the full month.
        """
        return date(self.year, self.month, 1)
    
    @property
    def end_date(self) -> date:
        """Get the last day of the calculation period (alias for calculation_date).
        
        Used for Excel range queries that span the full month.
        """
        import calendar
        last_day = calendar.monthrange(self.year, self.month)[1]
        return date(self.year, self.month, last_day)
    
    @property
    def days_in_period(self) -> int:
        """Get number of days in the period.
        
        Used to convert daily rates to monthly volumes.
        """
        import calendar
        return calendar.monthrange(self.year, self.month)[1]
    
    @property
    def period_label(self) -> str:
        """Human-readable period label (e.g., 'March 2026')."""
        import calendar
        return f"{calendar.month_name[self.month]} {self.year}"
    
    @property
    def period_short(self) -> str:
        """Short period label (e.g., 'Mar 2026')."""
        import calendar
        return f"{calendar.month_abbr[self.month]} {self.year}"

class InflowComponent(BaseModel):
    """Single inflow component with source tracking.
    
    Tracks individual inflow sources (rainfall, abstraction, dewatering, etc.)
    with data quality and source information.
    """
    
    name: str = Field(..., description="Component name (e.g., 'rainfall', 'abstraction')")
    value_m3: float = Field(..., ge=0, description="Volume in m³")
    quality: DataQualityLevel = Field(default=DataQualityLevel.MEASURED, description="Data quality level")
    source: str = Field(default="", description="Data source (e.g., 'Excel', 'Database', 'Meter')")
    notes: str = Field(default="", description="Additional notes")


class InflowResult(BaseModel):
    """Complete inflows calculation result.
    
    Contains all fresh water inflows to the system for a period.
    Fresh = water entering from outside the system boundary
    (excludes recycled/recirculated water).
    
    Components typically include:
    - Rainfall direct (to surface water bodies)
    - Abstraction from rivers/boreholes
    - Ore moisture (water entering with mined ore)
    - Underground dewatering (if exiting aquifer boundary)
    - External water purchases
    
    Attributes:
        total_m3: Sum of all inflow components
        components: Breakdown by source
        quality_flags: Data quality issues for inflows
    """
    
    total_m3: float = Field(default=0.0, ge=0, description="Total fresh inflows (m³)")
    components: Dict[str, float] = Field(default_factory=dict, description="Breakdown by source")
    component_details: List[InflowComponent] = Field(default_factory=list, description="Detailed component info")
    quality: DataQualityLevel = Field(default=DataQualityLevel.CALCULATED, description="Overall quality")
    
    @property
    def rainfall_m3(self) -> float:
        """Get rainfall component."""
        return self.components.get('rainfall', 0.0)
    
    @property
    def abstraction_m3(self) -> float:
        """Get abstraction component."""
        return self.components.get('abstraction', 0.0)
    
    @property
    def ore_moisture_m3(self) -> float:
        """Get ore moisture component."""
        return self.components.get('ore_moisture', 0.0)
    
    @property
    def other_m3(self) -> float:
        """Get 'other' inflows component (external purchases, transfers, etc.)."""
        return self.components.get('other', 0.0)


class OutflowComponent(BaseModel):
    """Single outflow component with destination tracking."""
    
    name: str = Field(..., description="Component name (e.g., 'evaporation', 'dust_suppression')")
    value_m3: float = Field(..., ge=0, description="Volume in m³")
    quality: DataQualityLevel = Field(default=DataQualityLevel.MEASURED, description="Data quality level")
    destination: str = Field(default="", description="Where water goes (e.g., 'Atmosphere', 'Tailings')")
    notes: str = Field(default="", description="Additional notes")


class OutflowResult(BaseModel):
    """Complete outflows calculation result.
    
    Contains all water leaving the system for a period.
    
    Components typically include:
    - Evaporation (from ponds, TSFs, open surfaces)
    - Seepage losses (unlined dams, TSFs)
    - Dust suppression (lost to ground/atmosphere)
    - Tailings moisture lock-up (water retained in tailings)
    - Discharge (controlled releases)
    - Plant consumption (process losses, product moisture)
    
    Attributes:
        total_m3: Sum of all outflow components
        components: Breakdown by destination
    """
    
    total_m3: float = Field(default=0.0, ge=0, description="Total outflows (m³)")
    components: Dict[str, float] = Field(default_factory=dict, description="Breakdown by destination")
    component_details: List[OutflowComponent] = Field(default_factory=list, description="Detailed component info")
    quality: DataQualityLevel = Field(default=DataQualityLevel.CALCULATED, description="Overall quality")
    
    @property
    def evaporation_m3(self) -> float:
        """Get evaporation component."""
        return self.components.get('evaporation', 0.0)
    
    @property
    def seepage_m3(self) -> float:
        """Get seepage losses component."""
        return self.components.get('seepage', 0.0)
    
    @property
    def dust_suppression_m3(self) -> float:
        """Get dust suppression component."""
        return self.components.get('dust_suppression', 0.0)
    
    @property
    def tailings_lockup_m3(self) -> float:
        """Get tailings moisture lock-up component."""
        return self.components.get('tailings_lockup', 0.0)
    
    @property
    def other_m3(self) -> float:
        """Get 'other' outflows component (discharge, losses, etc.)."""
        return self.components.get('other', 0.0)


class StorageChange(BaseModel):
    """Storage change for a single facility or system total.
    
    Tracks opening and closing volumes with change (delta).
    For system totals, also includes per-facility breakdown.
    
    Attributes:
        facility_code: Facility identifier (None for system total)
        opening_m3: Opening volume at period start
        closing_m3: Closing volume at period end
        delta_m3: Change = closing - opening (auto-calculated)
        source: Data source (measured/simulated)
        facility_breakdown: Per-facility storage changes (only for system total)
    """
    
    facility_code: Optional[str] = Field(None, description="Facility code (None for system total)")
    facility_name: Optional[str] = Field(None, description="Facility display name")
    opening_m3: float = Field(default=0.0, ge=0, description="Opening volume (m³)")
    closing_m3: float = Field(default=0.0, ge=0, description="Closing volume (m³)")
    capacity_m3: Optional[float] = Field(None, ge=0, description="Facility capacity (m³)")
    source: DataQualityLevel = Field(default=DataQualityLevel.MEASURED, description="Data source quality")
    facility_breakdown: List['StorageChange'] = Field(default_factory=list, description="Per-facility breakdown (for system total)")
    
    @property
    def delta_m3(self) -> float:
        """Calculate storage change (positive = gain, negative = loss)."""
        return self.closing_m3 - self.opening_m3
    
    @property
    def closing_pct(self) -> Optional[float]:
        """Closing volume as percentage of capacity."""
        if self.capacity_m3 and self.capacity_m3 > 0:
            return (self.closing_m3 / self.capacity_m3) * 100
        return None
    
    @property
    def is_overflow(self) -> bool:
        """Check if facility is at/above capacity."""
        if self.capacity_m3:
            return self.closing_m3 >= self.capacity_m3
        return False


class RecycledWaterResult(BaseModel):
    """Recycled water flows (for KPI tracking, not mass balance).
    
    Recycled water is water reused within the system.
    NOT included in mass balance (not crossing boundary)
    but tracked for efficiency KPIs.
    
    Components:
    - TSF return water (decanted back to plant)
    - RWD (Return Water Dam) flows
    - Process water recirculation
    """
    
    total_m3: float = Field(default=0.0, ge=0, description="Total recycled water (m³)")
    components: Dict[str, float] = Field(default_factory=dict, description="Breakdown by source")
    
    @property
    def tsf_return_m3(self) -> float:
        """Get TSF return water component."""
        return self.components.get('tsf_return', 0.0)
    
    @property
    def rwd_m3(self) -> float:
        """Get RWD recirculation component."""
        return self.components.get('rwd', 0.0)


class KPIResult(BaseModel):
    """KPI calculation result for water efficiency metrics.
    
    Key Performance Indicators for water management:
    - Recycled water percentage (higher = better efficiency)
    - Water intensity (m³ per tonne milled)
    - Abstraction vs license usage
    - Storage days remaining
    - Data quality cross-checks
    
    Attributes:
        recycled_pct: % of water that is recycled (0-100)
        water_intensity: m³ water per tonne ore processed
        abstraction_pct_of_license: % of licensed abstraction used
        storage_days: Days of operation at current storage
        rwd_intensity_measured: RWD.1 from Excel (m³/t) for verification
        rwd_intensity_calculated: RWD ÷ Tonnes (m³/t) for cross-check
        tailings_moisture_from_density: Moisture % calculated from slurry density
    """
    
    recycled_pct: float = Field(default=0.0, ge=0, le=100, description="Recycled water percentage")
    fresh_pct: float = Field(default=100.0, ge=0, le=100, description="Fresh water percentage")
    water_intensity_m3_per_tonne: float = Field(default=0.0, ge=0, description="Water per tonne milled")
    abstraction_m3: float = Field(default=0.0, ge=0, description="Fresh water abstraction (m³)")
    abstraction_license_m3: Optional[float] = Field(None, ge=0, description="Licensed abstraction limit (m³)")
    abstraction_pct_of_license: Optional[float] = Field(None, ge=0, description="% of license used")
    storage_days: Optional[float] = Field(None, ge=0, description="Days of operation remaining")
    abstraction_within_license: bool = Field(default=True, description="Whether within license limits")
    
    # Cross-verification KPIs (data quality checks)
    rwd_intensity_measured: Optional[float] = Field(None, ge=0, description="RWD.1 from Excel (m³/t)")
    rwd_intensity_calculated: Optional[float] = Field(None, ge=0, description="RWD ÷ Tonnes calculated (m³/t)")
    rwd_intensity_match: bool = Field(default=True, description="Whether measured matches calculated (<5% diff)")
    tailings_moisture_from_density: Optional[float] = Field(None, ge=0, le=100, description="Moisture % from slurry density")
    tailings_density_measured: Optional[float] = Field(None, ge=0, description="Slurry density from Excel (t/m³)")
    
    @property
    def efficiency_rating(self) -> str:
        """Get efficiency rating based on recycled percentage.
        
        Returns:
            'Excellent' (>80%), 'Good' (60-80%), 'Fair' (40-60%), 'Poor' (<40%)
        """
        if self.recycled_pct >= 80:
            return "Excellent"
        elif self.recycled_pct >= 60:
            return "Good"
        elif self.recycled_pct >= 40:
            return "Fair"
        else:
            return "Poor"


class FacilityBalance(BaseModel):
    """Per-facility water balance result.
    
    Detailed balance for a single storage facility including
    all inflows, outflows, and transfers.
    """
    
    facility_code: str = Field(..., description="Facility code (e.g., 'NDCD1')")
    facility_name: str = Field(..., description="Facility display name")
    facility_type: str = Field(default="Storage", description="Type: TSF, Pond, Dam, etc.")
    
    # Volumes
    opening_m3: float = Field(default=0.0, ge=0, description="Opening volume (m³)")
    closing_m3: float = Field(default=0.0, ge=0, description="Closing volume (m³)")
    capacity_m3: float = Field(..., gt=0, description="Facility capacity (m³)")
    
    # Flows
    inflows_m3: float = Field(default=0.0, ge=0, description="Total inflows (m³)")
    outflows_m3: float = Field(default=0.0, ge=0, description="Total outflows (m³)")
    transfers_in_m3: float = Field(default=0.0, ge=0, description="Transfers in (m³)")
    transfers_out_m3: float = Field(default=0.0, ge=0, description="Transfers out (m³)")
    evaporation_m3: float = Field(default=0.0, ge=0, description="Evaporation (m³)")
    seepage_m3: float = Field(default=0.0, ge=0, description="Seepage (m³)")
    rainfall_m3: float = Field(default=0.0, ge=0, description="Rainfall gain (m³)")
    
    @property
    def delta_m3(self) -> float:
        """Storage change."""
        return self.closing_m3 - self.opening_m3
    
    @property
    def closing_pct(self) -> float:
        """Closing percentage of capacity."""
        if self.capacity_m3 > 0:
            return (self.closing_m3 / self.capacity_m3) * 100
        return 0.0
    
    @property
    def status(self) -> str:
        """Facility status based on fill level."""
        pct = self.closing_pct
        if pct >= 95:
            return "CRITICAL"
        elif pct >= 80:
            return "HIGH"
        elif pct >= 20:
            return "NORMAL"
        else:
            return "LOW"


class BalanceResult(BaseModel):
    """Complete water balance calculation result.
    
    Contains all calculation outputs for a single period including:
    - Inflows, outflows, storage changes
    - Balance closure (error)
    - Data quality flags
    - KPIs
    - Per-facility breakdowns
    
    Master Equation:
        balance_error_m3 = fresh_inflows - outflows - delta_storage
        error_pct = (error / inflows) * 100
    
    Quality Rule:
        error_pct < 5% = Good balance (GREEN)
        error_pct >= 5% = Poor balance (RED) - investigate data quality
    
    Attributes:
        period: Calculation period (month/year)
        inflows: Fresh water inflows result
        outflows: Water outflows result
        storage: System-wide storage change
        recycled: Recycled water flows (KPI only)
        kpis: Key performance indicators
        facilities: Per-facility balance details
        quality_flags: Data quality warnings
    """
    
    period: CalculationPeriod = Field(..., description="Calculation period")
    
    # Main balance components
    inflows: InflowResult = Field(..., description="Fresh water inflows")
    outflows: OutflowResult = Field(..., description="Water outflows")
    storage: StorageChange = Field(..., description="System-wide storage change")
    recycled: Optional[RecycledWaterResult] = Field(None, description="Recycled water (KPI only)")
    
    # Closure calculation
    balance_error_m3: float = Field(default=0.0, description="Balance closure error (m³)")
    error_pct: float = Field(default=0.0, description="Error as % of inflows")
    
    # KPIs and breakdowns
    kpis: Optional[KPIResult] = Field(None, description="Key performance indicators")
    facilities: List[FacilityBalance] = Field(default_factory=list, description="Per-facility balances")
    
    # Data quality
    quality_flags: DataQualityFlags = Field(default_factory=DataQualityFlags, description="Data quality issues")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")
    calculation_mode: str = Field(default="REGULATOR", description="Mode: REGULATOR, INTERNAL, AUDIT")
    
    @property
    def status(self) -> str:
        """Balance status based on error percentage.
        
        Returns:
            'GREEN' if error < 5%, 'RED' otherwise
        """
        return "GREEN" if abs(self.error_pct) < 5 else "RED"
    
    @property
    def is_balanced(self) -> bool:
        """Check if balance is within acceptable tolerance."""
        return abs(self.error_pct) < 5
    
    @property
    def summary_dict(self) -> Dict[str, any]:
        """Get summary for UI display."""
        return {
            'date': self.period.calculation_date,
            'period_label': self.period.period_label,
            'fresh_inflows': self.inflows.total_m3,
            'total_outflows': self.outflows.total_m3,
            'storage_change': self.storage.delta_m3,
            'balance_error': self.balance_error_m3,
            'error_percent': self.error_pct,
            'status': self.status,
            'recycled_pct': self.kpis.recycled_pct if self.kpis else 0,
            'has_warnings': self.quality_flags.has_issues,
            'warning_count': self.quality_flags.issue_count,
        }
