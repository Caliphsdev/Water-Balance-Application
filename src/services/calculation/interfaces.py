"""
Calculation Service Interfaces (ABSTRACT BASE CLASSES).

Defines the contracts for all calculation services.
Enables dependency injection and testability.

Implementation classes must inherit from these interfaces.
UI code should depend on interfaces, not implementations.

Why interfaces:
1. Testability: Mock implementations for unit tests
2. Flexibility: Swap implementations without changing UI
3. Documentation: Clear API contracts
4. Dependency injection: Services injected, not instantiated
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List

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
)


class IInflowsService(ABC):
    """Interface for inflow calculations.
    
    Responsible for calculating all fresh water inflows:
    - Rainfall (direct to surface water)
    - Abstraction (rivers, boreholes)
    - Ore moisture
    - Underground dewatering
    - External water purchases
    
    Implementations must prioritize measured data over estimates.
    """
    
    @abstractmethod
    def calculate_inflows(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> InflowResult:
        """Calculate total fresh water inflows for a period.
        
        Args:
            period: Calculation period (month/year)
            flags: Data quality flags to populate
        
        Returns:
            InflowResult with total and component breakdown
        
        Raises:
            CalculationError: If required data is missing
        """
        pass
    
    @abstractmethod
    def get_rainfall_inflow(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get rainfall contribution to inflows.
        
        Calculates: rainfall_mm × surface_area / 1000
        
        Args:
            period: Calculation period
            flags: Quality flags to update
        
        Returns:
            Rainfall volume in m³
        """
        pass
    
    @abstractmethod
    def get_abstraction(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Get fresh water abstraction from external sources.
        
        Includes:
        - River abstraction
        - Borehole abstraction
        - Municipal supply
        
        Args:
            period: Calculation period
            flags: Quality flags to update
        
        Returns:
            Abstraction volume in m³
        """
        pass


class IOutflowsService(ABC):
    """Interface for outflow calculations.
    
    Responsible for calculating all water leaving the system:
    - Evaporation
    - Seepage losses
    - Dust suppression
    - Tailings moisture lock-up
    - Discharge
    - Product moisture
    
    Implementations must prioritize measured data over estimates.
    """
    
    @abstractmethod
    def calculate_outflows(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> OutflowResult:
        """Calculate total outflows for a period.
        
        Args:
            period: Calculation period (month/year)
            flags: Data quality flags to populate
        
        Returns:
            OutflowResult with total and component breakdown
        """
        pass
    
    @abstractmethod
    def get_evaporation(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate total evaporation losses.
        
        Calculates for each facility:
            evap_mm × pan_coeff × surface_area / 1000
        
        Args:
            period: Calculation period
            flags: Quality flags to update
        
        Returns:
            Total evaporation volume in m³
        """
        pass
    
    @abstractmethod
    def get_seepage(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> float:
        """Calculate total seepage losses.
        
        Uses:
        - Lined dams: 0.1% of volume
        - Unlined dams: 0.5% of volume
        
        Args:
            period: Calculation period
            flags: Quality flags to update
        
        Returns:
            Total seepage volume in m³
        """
        pass


class IStorageService(ABC):
    """Interface for storage calculations.
    
    Responsible for tracking storage volumes:
    - Opening/closing volumes per facility
    - System-wide storage totals
    - Storage changes (delta)
    
    Should prefer measured data (surveys) over simulated.
    """
    
    @abstractmethod
    def calculate_storage(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> StorageChange:
        """Calculate system-wide storage change.
        
        Args:
            period: Calculation period (month/year)
            flags: Data quality flags to populate
        
        Returns:
            StorageChange with opening, closing, and delta
        """
        pass
    
    @abstractmethod
    def get_facility_storage(
        self, 
        facility_code: str, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> StorageChange:
        """Get storage for a specific facility.
        
        Args:
            facility_code: Facility identifier
            period: Calculation period
            flags: Quality flags to update
        
        Returns:
            StorageChange for the facility
        """
        pass
    
    @abstractmethod
    def get_all_facilities_storage(
        self, 
        period: CalculationPeriod,
        flags: DataQualityFlags
    ) -> List[StorageChange]:
        """Get storage for all active facilities.
        
        Args:
            period: Calculation period
            flags: Quality flags to update
        
        Returns:
            List of StorageChange for each facility
        """
        pass


class IRecycledService(ABC):
    """Interface for recycled water calculations.
    
    Recycled water is reused within the system:
    - TSF return water
    - RWD circulation
    - Process water recirculation
    
    NOT included in mass balance (not crossing boundary)
    but tracked for efficiency KPIs.
    """
    
    @abstractmethod
    def calculate_recycled(
        self, 
        period: CalculationPeriod, 
        flags: DataQualityFlags
    ) -> RecycledWaterResult:
        """Calculate total recycled water for a period.
        
        Args:
            period: Calculation period (month/year)
            flags: Data quality flags to populate
        
        Returns:
            RecycledWaterResult with total and component breakdown
        """
        pass


class IKPIService(ABC):
    """Interface for KPI calculations.
    
    Calculates key performance indicators:
    - Recycled water percentage
    - Water intensity (m³/tonne)
    - Abstraction vs license
    - Storage days remaining
    """
    
    @abstractmethod
    def calculate_kpis(
        self,
        inflows: InflowResult,
        outflows: OutflowResult,
        recycled: RecycledWaterResult,
        storage: StorageChange,
        period: CalculationPeriod,
    ) -> KPIResult:
        """Calculate all KPIs from balance components.
        
        Args:
            inflows: Fresh water inflows
            outflows: Total outflows
            recycled: Recycled water flows
            storage: Storage change
            period: Calculation period
        
        Returns:
            KPIResult with all KPI values
        """
        pass


class IFacilityBalanceService(ABC):
    """Interface for per-facility balance calculations.
    
    Calculates detailed water balance for each storage facility:
    - Inflows (rainfall, transfers in)
    - Outflows (evaporation, seepage, transfers out)
    - Opening/closing volumes
    """
    
    @abstractmethod
    def calculate_facility_balance(
        self,
        facility_code: str,
        period: CalculationPeriod,
        flags: DataQualityFlags,
    ) -> FacilityBalance:
        """Calculate balance for a single facility.
        
        Args:
            facility_code: Facility identifier
            period: Calculation period
            flags: Data quality flags
        
        Returns:
            FacilityBalance with all flow details
        """
        pass
    
    @abstractmethod
    def calculate_all_facilities(
        self,
        period: CalculationPeriod,
        flags: DataQualityFlags,
    ) -> List[FacilityBalance]:
        """Calculate balance for all active facilities.
        
        Args:
            period: Calculation period
            flags: Data quality flags
        
        Returns:
            List of FacilityBalance for each facility
        """
        pass


class IBalanceEngine(ABC):
    """Main calculation engine interface.
    
    Orchestrates all calculation services to produce
    a complete water balance result.
    
    Master Equation:
        error = fresh_inflows - outflows - delta_storage
    """
    
    @abstractmethod
    def calculate(
        self,
        period: CalculationPeriod,
        mode: str = "REGULATOR",
    ) -> BalanceResult:
        """Run complete water balance calculation.
        
        Args:
            period: Calculation period (month/year)
            mode: Calculation mode (REGULATOR, INTERNAL, AUDIT)
        
        Returns:
            BalanceResult with all calculation outputs
        
        Raises:
            CalculationError: If calculation fails
        """
        pass
    
    @abstractmethod
    def calculate_for_date(
        self,
        month: int,
        year: int,
        mode: str = "REGULATOR",
    ) -> BalanceResult:
        """Run calculation for a specific month/year.
        
        Convenience method that creates CalculationPeriod internally.
        
        Args:
            month: Calendar month (1-12)
            year: Calendar year
            mode: Calculation mode
        
        Returns:
            BalanceResult with all calculation outputs
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear all calculation caches.
        
        Call when:
        - Excel file is updated
        - Database is modified
        - Configuration changes
        """
        pass


class CalculationError(Exception):
    """Exception raised when calculation fails.
    
    Provides context about what went wrong and where.
    """
    
    def __init__(self, message: str, component: str = None, details: dict = None):
        """Initialize calculation error.
        
        Args:
            message: Human-readable error message
            component: Which component failed (e.g., 'inflows', 'storage')
            details: Additional error context
        """
        super().__init__(message)
        self.component = component
        self.details = details or {}
