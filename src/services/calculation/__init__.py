"""
Water Balance Calculation Engine (MODULAR SERVICES).

This package implements the refactored calculation engine with:
- Clean separation of concerns (inflows, outflows, storage, KPIs)
- Type-safe data models (Pydantic)
- Interface-based design (testable, mockable)
- Scientific accuracy improvements

Structure:
- models.py: Pydantic data models for calculation I/O
- interfaces.py: Abstract service interfaces
- constants.py: Calculation constants loader
- balance_service.py: Main balance orchestrator
- inflows/: Inflow calculation modules
- outflows/: Outflow calculation modules  
- storage/: Storage and dam calculations
- kpis/: KPI calculations

Master Equation:
    balance_error = fresh_inflows - outflows - delta_storage

Usage:
    from services.calculation import BalanceService
    
    service = BalanceService()
    result = service.calculate(facility_code='UG2N', month=3, year=2026)
    logger.info(result.error_percent)  # < 5% = good balance
"""

from services.calculation.models import (
    CalculationPeriod,
    InflowResult,
    OutflowResult,
    StorageChange,
    BalanceResult,
    KPIResult,
    DataQualityFlags,
)
from services.calculation.interfaces import (
    IInflowsService,
    IOutflowsService,
    IStorageService,
    IKPIService,
    IBalanceEngine,
)
from services.calculation.balance_service import BalanceService, get_balance_service

__all__ = [
    # Data Models
    'CalculationPeriod',
    'InflowResult',
    'OutflowResult',
    'StorageChange',
    'BalanceResult',
    'KPIResult',
    'DataQualityFlags',
    # Interfaces
    'IInflowsService',
    'IOutflowsService',
    'IStorageService',
    'IKPIService',
    'IBalanceEngine',
    # Main Service
    'BalanceService',
    'get_balance_service',
]
