# Calculation Engine Refactoring Implementation Plan

**Status:** Development Phase - Sprint 0 Ready  
**Created:** February 2, 2026  
**Priority:** High  
**Estimated Effort:** 4-5 Sprints (scientific improvements added)

---

## 📋 Executive Summary

The current calculation engine in the Tkinter legacy application (`c:\PROJECTS\Water-Balance-Application\src\utils\`) consists of multiple tightly-coupled modules that handle water balance calculations, KPIs, pump transfers, and storage management. This document outlines a comprehensive plan to:

1. Migrate and refactor the engine for the new PySide6 dashboard
2. Implement modular, API-like architecture for easy maintenance
3. Fix scientific accuracy issues (dam overflow, pump transfer logic)
4. Add database persistence for calculation results
5. Create clean separation between UI and business logic

---

## 🏗️ Current Architecture Analysis

### Legacy Engine Components (Tkinter)

| File | Lines | Purpose | Coupling Level |
|------|-------|---------|----------------|
| `water_balance_calculator.py` | 2,477 | Main calculation engine (inflows, outflows, storage, KPIs) | **HIGH** - Monolithic |
| `balance_engine.py` | ~200 | Service orchestrator (uses service pattern) | MEDIUM |
| `balance_services.py` | ~400 | Service interfaces + dataclasses | LOW - Clean abstractions |
| `balance_kpis.py` | ~150 | KPI calculations (recycled %, efficiency) | MEDIUM |
| `pump_transfer_engine.py` | 252 | Auto pump transfers between facilities | **HIGH** - Hardcoded logic |
| `balance_check_engine.py` | 248 | Balance validation from templates | LOW |

### Key Issues Identified

1. **Monolithic Calculator**: `WaterBalanceCalculator` has 2,477 lines doing too much
2. **Duplicate Logic**: Both `water_balance_calculator.py` and `balance_engine.py` calculate balances
3. **Scientific Inaccuracies**: Pump transfer logic when dams are full doesn't match real physics
4. **Tight Excel Coupling**: Calculator reads directly from Excel via `get_monthly_value()`
5. **No Result Persistence**: Calculations aren't saved to database
6. **Mixed Concerns**: UI formatting mixed with calculation logic

---

## 🎯 Target Architecture

### Design Principles

1. **Single Responsibility**: Each module does ONE thing well
2. **Dependency Injection**: Services injected, not instantiated internally
3. **Interface-Based**: All services implement abstract interfaces
4. **Testable**: Every calculation unit testable in isolation
5. **Configurable**: Equations and constants in config, not hardcoded
6. **Auditable**: All calculations logged with inputs and outputs

### New Module Structure

```
src/
└── services/
    └── calculation/
        ├── __init__.py
        ├── interfaces.py         # Abstract base classes for all services
        ├── models.py            # Pydantic dataclasses for inputs/outputs
        ├── constants.py         # System constants loader
        │
        ├── inflows/
        │   ├── __init__.py
        │   ├── inflows_service.py    # Orchestrates all inflow calculations
        │   ├── surface_water.py      # Surface water inflow calculator
        │   ├── groundwater.py        # Groundwater inflow calculator
        │   ├── rainfall.py           # Rainfall contribution calculator
        │   └── recycled.py           # RWD and recycled water calculator
        │
        ├── outflows/
        │   ├── __init__.py
        │   ├── outflows_service.py   # Orchestrates all outflow calculations
        │   ├── plant_consumption.py  # Plant water consumption
        │   ├── evaporation.py        # Pan evaporation model
        │   └── discharge.py          # Discharge/seepage calculations
        │
        ├── storage/
        │   ├── __init__.py
        │   ├── storage_service.py    # Storage change calculations
        │   ├── facility_balance.py   # Per-facility balance logic
        │   └── pump_transfers.py     # FIXED pump transfer logic
        │
        ├── kpis/
        │   ├── __init__.py
        │   ├── kpi_service.py        # KPI orchestrator
        │   ├── efficiency.py         # Water efficiency metrics
        │   ├── recycling.py          # Recycling ratios
        │   └── compliance.py         # Regulatory compliance checks
        │
        ├── engine.py            # Main orchestrator (BalanceEngine)
        └── repository.py        # Database persistence layer
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              UI LAYER                                    │
│  (PySide6 Dashboards: calculations_page.py, analytics_page.py)          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CALCULATION ENGINE                               │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   Inflows    │    │   Outflows   │    │   Storage    │              │
│  │   Service    │    │   Service    │    │   Service    │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             ▼                                            │
│                    ┌──────────────┐                                      │
│                    │    Balance   │◄────── Master Equation              │
│                    │    Engine    │        error = IN - OUT - ΔS        │
│                    └──────┬───────┘                                      │
│                           │                                              │
│                    ┌──────▼───────┐                                      │
│                    │     KPI      │                                      │
│                    │   Service    │                                      │
│                    └──────────────┘                                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │    SQLite    │    │    Excel     │    │   Config     │              │
│  │  Repository  │    │   Loaders    │    │   (YAML)     │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Core Data Models

### Pydantic Models (Type-Safe Calculation I/O)

```python
# services/calculation/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import date

class CalculationPeriod(BaseModel):
    """Period for calculation (month + year)."""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)
    
    @property
    def date(self) -> date:
        return date(self.year, self.month, 1)

class InflowResult(BaseModel):
    """Result from inflows calculation."""
    surface_water_m3: float = 0.0
    groundwater_m3: float = 0.0
    underground_dewatering_m3: float = 0.0
    rainfall_m3: float = 0.0
    ore_moisture_m3: float = 0.0
    tsf_return_m3: float = 0.0
    rwd_inflow_m3: float = 0.0
    
    @property
    def total_fresh_m3(self) -> float:
        """Fresh water only (excludes recycled/RWD)."""
        return (
            self.surface_water_m3 +
            self.groundwater_m3 +
            self.underground_dewatering_m3 +
            self.rainfall_m3 +
            self.ore_moisture_m3
        )
    
    @property
    def total_all_m3(self) -> float:
        """All water including recycled."""
        return self.total_fresh_m3 + self.rwd_inflow_m3 + self.tsf_return_m3

class OutflowResult(BaseModel):
    """Result from outflows calculation."""
    plant_consumption_m3: float = 0.0
    evaporation_m3: float = 0.0
    discharge_m3: float = 0.0
    seepage_m3: float = 0.0
    dust_suppression_m3: float = 0.0
    mining_consumption_m3: float = 0.0
    domestic_consumption_m3: float = 0.0
    product_moisture_m3: float = 0.0
    tailings_retention_m3: float = 0.0
    
    @property
    def total_m3(self) -> float:
        return sum([
            self.plant_consumption_m3,
            self.evaporation_m3,
            self.discharge_m3,
            self.seepage_m3,
            self.dust_suppression_m3,
            self.mining_consumption_m3,
            self.domestic_consumption_m3,
            self.product_moisture_m3,
            self.tailings_retention_m3
        ])

class StorageChange(BaseModel):
    """Storage change for a facility."""
    facility_code: str
    facility_name: str
    opening_volume_m3: float
    closing_volume_m3: float
    rainfall_gain_m3: float = 0.0
    evaporation_loss_m3: float = 0.0
    seepage_loss_m3: float = 0.0
    transfers_in_m3: float = 0.0
    transfers_out_m3: float = 0.0
    
    @property
    def delta_m3(self) -> float:
        """Net storage change."""
        return self.closing_volume_m3 - self.opening_volume_m3
    
    @property
    def level_percent(self) -> float:
        """Current fill level (requires capacity)."""
        # Will be calculated with capacity from constants
        pass

class BalanceResult(BaseModel):
    """Complete water balance calculation result."""
    period: CalculationPeriod
    inflows: InflowResult
    outflows: OutflowResult
    storage_changes: List[StorageChange]
    
    # Derived metrics
    total_inflows_m3: float
    total_outflows_m3: float
    total_storage_change_m3: float
    closure_error_m3: float
    closure_error_percent: float
    
    # Quality flags
    is_valid: bool = True
    warnings: List[str] = []
    errors: List[str] = []
    
    @property
    def closure_status(self) -> str:
        """GREEN (<5%), YELLOW (5-10%), RED (>10%)."""
        if abs(self.closure_error_percent) < 5:
            return "GREEN"
        elif abs(self.closure_error_percent) < 10:
            return "YELLOW"
        return "RED"

class KPIResult(BaseModel):
    """KPI calculation result."""
    period: CalculationPeriod
    
    # Efficiency metrics
    water_intensity_m3_per_tonne: float
    specific_consumption_m3_per_tonne: float
    process_efficiency_percent: float
    
    # Recycling metrics
    recycled_water_percent: float
    fresh_water_dependency_percent: float
    rwd_utilization_percent: float
    
    # Storage metrics
    total_storage_m3: float
    total_capacity_m3: float
    storage_utilization_percent: float
    days_of_cover: float
    
    # Compliance
    discharge_within_limit: bool = True
    abstraction_within_license: bool = True
```

---

## 🔧 Service Interfaces

### Abstract Base Classes

```python
# services/calculation/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional
from .models import (
    CalculationPeriod, InflowResult, OutflowResult,
    StorageChange, BalanceResult, KPIResult
)

class IInflowsService(ABC):
    """Interface for inflows calculation."""
    
    @abstractmethod
    def calculate(self, period: CalculationPeriod) -> InflowResult:
        """Calculate all inflows for the given period."""
        pass
    
    @abstractmethod
    def get_surface_water(self, period: CalculationPeriod) -> float:
        """Calculate surface water inflow (m³)."""
        pass
    
    @abstractmethod
    def get_groundwater(self, period: CalculationPeriod) -> float:
        """Calculate groundwater inflow (m³)."""
        pass

class IOutflowsService(ABC):
    """Interface for outflows calculation."""
    
    @abstractmethod
    def calculate(self, period: CalculationPeriod) -> OutflowResult:
        """Calculate all outflows for the given period."""
        pass
    
    @abstractmethod
    def get_plant_consumption(self, period: CalculationPeriod) -> float:
        """Calculate plant consumption (m³)."""
        pass

class IStorageService(ABC):
    """Interface for storage calculations."""
    
    @abstractmethod
    def calculate_changes(self, period: CalculationPeriod) -> list[StorageChange]:
        """Calculate storage changes for all facilities."""
        pass
    
    @abstractmethod
    def get_facility_balance(
        self, 
        facility_code: str, 
        period: CalculationPeriod
    ) -> StorageChange:
        """Calculate balance for single facility."""
        pass
    
    @abstractmethod
    def calculate_transfers(
        self, 
        period: CalculationPeriod
    ) -> dict[str, dict]:
        """Calculate pump transfers based on current levels."""
        pass

class IKPIService(ABC):
    """Interface for KPI calculations."""
    
    @abstractmethod
    def calculate(self, balance: BalanceResult) -> KPIResult:
        """Calculate all KPIs from a balance result."""
        pass

class IBalanceEngine(ABC):
    """Main calculation engine interface."""
    
    @abstractmethod
    def calculate_balance(self, period: CalculationPeriod) -> BalanceResult:
        """Execute full water balance calculation."""
        pass
    
    @abstractmethod
    def calculate_kpis(self, period: CalculationPeriod) -> KPIResult:
        """Calculate KPIs for period (runs balance internally)."""
        pass
    
    @abstractmethod
    def persist_result(self, result: BalanceResult) -> bool:
        """Save calculation result to database."""
        pass
```

---

## 🔬 Scientific Fixes Required

### Issue 1: Pump Transfer Logic

**Current (Flawed) Logic:**
```python
# When facility level >= 70%, transfer 5% to downstream
if level >= pump_start_level:
    transfer_volume = current_volume * 0.05
    transfer(transfer_volume)
```

**Problems:**
1. Doesn't check if downstream has capacity
2. Doesn't handle cascade (A→B→C overflow scenario)
3. 5% increment is arbitrary, not based on pump capacity
4. Doesn't account for real pump flow rates (m³/hour × hours)

**Fixed Logic:**
```python
# services/calculation/storage/pump_transfers.py
class PumpTransferCalculator:
    """Physically-accurate pump transfer calculations.
    
    Key Improvements:
    - Uses actual pump capacity (m³/day from constants)
    - Respects downstream facility capacity limits
    - Handles cascade transfers (multi-hop)
    - Time-based: days_running × pump_rate
    """
    
    def calculate_transfer(
        self,
        source: FacilityState,
        destination: FacilityState,
        period_days: int
    ) -> TransferResult:
        """Calculate realistic pump transfer volume.
        
        Physics:
        1. Transfer only possible if source level > pump_start_level
        2. Transfer volume = min(
               pump_capacity_m3_day * period_days,
               source_volume - source_dead_storage,
               destination_remaining_capacity
           )
        3. Destination can't exceed 100% (prevents overflow)
        """
        # Check if source can pump
        if source.level_percent < source.pump_start_level:
            return TransferResult(volume_m3=0, reason="Source below pump start level")
        
        # Available to transfer (above dead storage)
        available = source.current_volume - source.dead_storage_m3
        
        # Destination capacity
        destination_headroom = destination.capacity_m3 - destination.current_volume
        
        # Pump physical limit
        pump_max = source.pump_capacity_m3_day * period_days
        
        # Take minimum of all constraints
        transfer_volume = min(available, destination_headroom, pump_max)
        
        return TransferResult(
            volume_m3=max(0, transfer_volume),
            source_code=source.code,
            destination_code=destination.code,
            reason="Calculated transfer"
        )
```

### Issue 2: Dam Overflow Handling

**Current Issue:** No handling when storage exceeds 100%

**Fixed Logic:**
```python
class FacilityBalanceCalculator:
    """Calculate facility balance with overflow protection.
    
    Scientific Basis:
    - Storage cannot exceed physical capacity (100%)
    - Overflow is treated as DISCHARGE (uncontrolled outflow)
    - Overflow logged as data quality warning
    """
    
    def calculate_closing_volume(
        self,
        opening_volume: float,
        inflows: float,
        outflows: float,
        capacity: float
    ) -> tuple[float, float]:
        """Calculate closing volume with overflow handling.
        
        Returns:
            (closing_volume, overflow_volume)
        """
        theoretical_closing = opening_volume + inflows - outflows
        
        if theoretical_closing > capacity:
            # Overflow occurred
            overflow = theoretical_closing - capacity
            closing_volume = capacity
            return closing_volume, overflow
        elif theoretical_closing < 0:
            # Impossible - indicates measurement error
            return 0, 0  # Flag as data quality issue
        else:
            return theoretical_closing, 0
```

### Issue 3: Evaporation Model

**Current:** Uses simple pan evaporation × area  
**Improved:** Use Penman-Monteith or Meyer formula with weather data

```python
class EvaporationCalculator:
    """Evaporation calculation using Meyer formula.
    
    Scientific Basis:
    E = C × (es - ea) × (1 + W/16)
    
    Where:
    - E: evaporation (mm/day)
    - C: pan coefficient (0.7 for Class A pan)
    - es: saturated vapor pressure at water surface temp
    - ea: actual vapor pressure of air
    - W: wind speed (km/day)
    """
    
    def calculate_evaporation_m3(
        self,
        surface_area_m2: float,
        pan_evaporation_mm: float,
        pan_coefficient: float = 0.7
    ) -> float:
        """Calculate evaporation loss.
        
        Args:
            surface_area_m2: Water surface area
            pan_evaporation_mm: Measured pan evaporation
            pan_coefficient: Pan to lake conversion (default 0.7)
        
        Returns:
            Evaporation volume in m³
        """
        evaporation_mm = pan_evaporation_mm * pan_coefficient
        evaporation_m = evaporation_mm / 1000
        return surface_area_m2 * evaporation_m
```

---

## 🔬 Scientific Review & Industry Validation

This section reviews each equation against mining industry standards, academic literature, and regulatory frameworks. Each item is rated for scientific defensibility and includes improvement recommendations.

### Overview: Mining Water Balance Standards

The mining industry follows water balance frameworks established by:
- **ICMM** (International Council on Mining and Metals) - Water Stewardship Framework
- **GISTM** (Global Industry Standard on Tailings Management) - 2020
- **Australian ANCOLD** Guidelines for Tailings Dams
- **MEND** (Mine Environment Neutral Drainage) - Canadian standards
- **DWS** (Department of Water and Sanitation) - South African regulations

**Master Equation (Currently Correct):**
```
ΔS = I - O - E ± G

Where:
  ΔS = Change in storage
  I  = Total inflows (fresh + recycled)
  O  = Total outflows (consumption + discharge)
  E  = Evaporation losses
  G  = Groundwater interaction (+ gain, - loss)
```

---

### 📊 Equation Review Summary

| Component | Current Status | Industry Standard | Recommendation |
|-----------|---------------|-------------------|----------------|
| **Master Balance Equation** | ✅ Correct | ICMM compliant | Minor: Add uncertainty quantification |
| **Evaporation** | ⚠️ Simplified | Penman-Monteith preferred | **IMPROVE**: Add temperature/wind factors |
| **Seepage (Lined/Unlined)** | ⚠️ Oversimplified | Darcy's Law preferred | **IMPROVE**: Use hydraulic conductivity |
| **Seepage Gain (Aquifer)** | ⚠️ Linear % | Darcy's Law preferred | **IMPROVE**: Use head difference |
| **Rainfall** | ✅ Correct | Standard practice | Minor: Add runoff coefficient |
| **TSF Return Water** | ⚠️ Fixed % | Mass balance | **IMPROVE**: Calculate from slurry density |
| **Tailings Retention** | ✅ Reasonable | Industry standard | Minor: Add void ratio |
| **Ore Moisture** | ✅ Correct | Standard practice | None |
| **Plant Consumption** | ⚠️ Ore-based estimate | Flow metering preferred | **IMPROVE**: Use actual measurements |
| **Pump Transfers** | ❌ Unphysical | Pump curves required | **CRITICAL**: Complete redesign |
| **Closure Error** | ✅ Correct | Standard practice | Minor: Add confidence intervals |

---

### 🔴 CRITICAL IMPROVEMENT: Seepage Equations

**Current Approach (Oversimplified):**
```python
seepage_loss = current_volume * seepage_rate_pct  # 0.1% lined, 0.5% unlined
```

**Problem:** This assumes seepage is proportional to volume, not head (water level). In reality, seepage is driven by **hydraulic head** (water depth) and **hydraulic conductivity** of the liner/soil.

**Industry Standard: Darcy's Law**
```
Q = K × i × A

Where:
  Q = Seepage flow rate (m³/s)
  K = Hydraulic conductivity (m/s)
  i = Hydraulic gradient (dimensionless) = Δh / L
  A = Cross-sectional area (m²)
```

**Improved Seepage Equation:**
```python
class SeepageCalculator:
    """Darcy's Law-based seepage calculation.
    
    Academic Reference:
    - Fell et al. (2015) "Geotechnical Engineering of Dams" - Chapter 12
    - ANCOLD Guidelines for Design of Dams and Appurtenant Structures (2019)
    """
    
    # Typical hydraulic conductivity values (m/s)
    CONDUCTIVITY = {
        'hdpe_liner': 1e-12,      # HDPE geomembrane (practically impermeable)
        'clay_liner': 1e-9,       # Compacted clay (600mm)
        'sandy_clay': 1e-7,       # Sandy clay (unlined)
        'silty_sand': 1e-5,       # Silty sand (unlined, poor)
        'fractured_rock': 1e-6,   # Fractured bedrock
    }
    
    def calculate_seepage_m3_month(
        self,
        water_depth_m: float,           # Head driving seepage
        base_area_m2: float,            # Dam base area
        liner_type: str,                # 'hdpe_liner', 'clay_liner', 'sandy_clay', etc.
        liner_thickness_m: float = 1.0  # Seepage path length
    ) -> float:
        """Calculate monthly seepage using Darcy's Law.
        
        Formula: Q = K × A × (h / L) × t
        """
        K = self.CONDUCTIVITY.get(liner_type, 1e-7)  # Default: sandy clay
        i = water_depth_m / liner_thickness_m
        Q_per_second = K * i * base_area_m2
        seconds_per_month = 30 * 24 * 3600
        return Q_per_second * seconds_per_month
```

**Database Changes Required:**
```sql
ALTER TABLE storage_facilities ADD COLUMN liner_type TEXT DEFAULT 'sandy_clay';
ALTER TABLE storage_facilities ADD COLUMN liner_thickness_m REAL DEFAULT 1.0;
ALTER TABLE storage_facilities ADD COLUMN base_area_m2 REAL DEFAULT 0;
```

**Comparison:**
| Dam | Current (% of vol) | Darcy (head-based) | Difference |
|-----|-------------------|-------------------|------------|
| TSF (100,000 m³, 10m deep, unlined) | 500 m³/month | 2,600 m³/month | -80% underestimate |
| RWD (50,000 m³, 5m deep, HDPE lined) | 50 m³/month | ~0 m³/month | Overestimate |

---

### 🟡 RECOMMENDED IMPROVEMENT: Evaporation Model

**Current Approach:**
```python
evap_volume = pan_evap_mm * pan_coefficient * surface_area / 1000
```

**Issue:** Pan coefficient (0.7) doesn't account for wind speed, temperature, humidity, altitude.

**Industry Standard: Penman-Monteith Equation (FAO-56)** - Preferred but requires weather station data.

**Simplified Alternative (Linacre's Formula):**
```python
class ImprovedEvaporationCalculator:
    """Linacre (1977) simplified evaporation model.
    
    Reference: Journal of Hydrology, 34(3-4), pp.255-271
    """
    
    def calculate_evaporation_mm_day(
        self,
        mean_temp_c: float,
        latitude_deg: float,
        altitude_m: float = 0
    ) -> float:
        E = (500 * mean_temp_c / (100 - abs(latitude_deg)) + 15 * 5) / (80 - mean_temp_c)
        altitude_factor = 1 - (altitude_m / 50000)
        return max(0, E * altitude_factor)
```

**Recommendation:** Current pan method is acceptable with temperature adjustment:
```python
temp_factor = 0.95 + (mean_temp_c / 500)  # ~1.0 at 25°C
adjusted_coeff = pan_coefficient * temp_factor
```

---

### 🟡 RECOMMENDED IMPROVEMENT: TSF Return Water

**Current Approach:**
```python
tsf_return = plant_consumption * 0.36  # Fixed 36%
```

**Problem:** TSF return depends on slurry density, beach consolidation, pond size, mineralogy.

**Industry Standard: Mass Balance Calculation**
```
TSF_Return = Slurry_Water - Interstitial_Water - Evap_from_Beach - Seepage
```

**Simplified Alternative (If Data Limited):**
```python
def estimate_tsf_return_percent(slurry_solids_percent: float) -> float:
    """Estimate TSF return as % of slurry water.
    
    Typical ranges by tailings type.
    """
    if slurry_solids_percent <= 35:
        return 0.55  # 55% return (conventional tailings)
    elif slurry_solids_percent <= 55:
        return 0.36  # 36% return (thickened tailings) ← Current default
    elif slurry_solids_percent <= 70:
        return 0.20  # 20% return (paste tailings)
    else:
        return 0.10  # 10% return (filtered tailings)
```

---

### 🟡 RECOMMENDED IMPROVEMENT: Rainfall Runoff

**Current Approach:**
```python
rainfall_volume = rainfall_mm * surface_area / 1000  # 100% captured
```

**Problem:** Ignores catchment runoff and surface type coefficients.

**Industry Standard: Runoff Coefficient**
```python
RUNOFF_COEFFICIENTS = {
    'open_water': 1.0,
    'bare_rock': 0.85,
    'tailings_beach': 0.40,
    'grassed': 0.25,
    'natural_bush': 0.20,
}
```

**Database Changes:**
```sql
CREATE TABLE facility_catchment (
    facility_id INTEGER REFERENCES storage_facilities(id),
    surface_type TEXT NOT NULL,
    area_m2 REAL NOT NULL,
    PRIMARY KEY (facility_id, surface_type)
);
```

---

### 🟢 VALIDATED: Tailings Moisture Retention

**Current Approach:**
```python
tailings_retention = (ore_tonnes - concentrate_tonnes) * tailings_moisture_pct
```

**Assessment:** Scientifically correct for water locked in tailings solids.

**Reference:** Das (2016) "Principles of Geotechnical Engineering" - Soil mechanics fundamentals.

---

### 🟢 VALIDATED: Ore Moisture Inflow

**Current Approach:**
```python
ore_moisture_water = (ore_tonnes * ore_moisture_pct / 100) / ore_density
```

**Assessment:** Correct - water enters system with wet ore. Division by ore_density converts mass to volume.

---

### 🔴 CRITICAL: Pump Transfer Physics

**Current Approach:**
```python
if level >= 70%:
    transfer_volume = current_volume * 0.05  # 5% of volume
```

**Problems:**
1. Ignores pump physical capacity (m³/hr)
2. Ignores operating hours
3. Ignores pipe friction and head losses
4. Ignores destination capacity

**Industry Standard: Pump Curve + System Curve**
```
Q = f(H_pump - H_system)

Where:
  H_pump = Pump head at flow Q (from pump curve)
  H_system = Static head + friction losses
```

**Improved Approach:**
```python
class PumpTransferCalculator:
    """Physically-accurate pump transfer calculations.
    
    Reference: Karassik et al. (2008) "Pump Handbook" 4th Ed.
    """
    
    def calculate_transfer(
        self,
        pump_capacity_m3_hr: float,
        operating_hours_month: float,
        destination_headroom_m3: float
    ) -> float:
        max_pump_volume = pump_capacity_m3_hr * operating_hours_month
        return min(max_pump_volume, destination_headroom_m3)
```

**Database Changes:**
```sql
ALTER TABLE storage_facilities ADD COLUMN pump_capacity_m3_hr REAL DEFAULT 0;
ALTER TABLE storage_facilities ADD COLUMN pump_head_m REAL DEFAULT 0;
ALTER TABLE storage_facilities ADD COLUMN typical_operating_hours_month REAL DEFAULT 0;
```

---

### 🟡 RECOMMENDED: Uncertainty Quantification

**Current:** Single point estimates with no uncertainty bands.

**Industry Standard:** Water balances should include confidence intervals (ICMM, ISO 14046).

**Typical Measurement Uncertainties:**
| Source | Uncertainty |
|--------|------------|
| Flow meter (calibrated) | ±5% |
| Rain gauge | ±10% |
| Evaporation pan | ±15% |
| Storage survey (bathymetric) | ±5% |
| Estimated values | ±30% |

**Implementation:**
```python
class UncertaintyQuantifier:
    """Add uncertainty bands to water balance.
    
    Uses root-sum-square for independent uncertainties.
    """
    
    def calculate_balance_with_uncertainty(self, inflows, outflows, storage_change):
        # Calculate 95% confidence interval
        ci_95 = 1.96 * total_uncertainty
        return {
            'closure_error_m3': closure_error,
            'uncertainty_m3': ci_95,
            'is_significant': abs(closure_error) > ci_95
        }
```

---

### 📋 Summary: Recommended Changes

| Priority | Component | Change | Effort | Impact |
|----------|-----------|--------|--------|--------|
| 🔴 CRITICAL | Pump Transfers | Replace % with pump curve physics | HIGH | High accuracy |
| 🔴 CRITICAL | Seepage | Replace % with Darcy's Law | MEDIUM | Major improvement |
| 🟡 RECOMMENDED | Evaporation | Add temperature factor | LOW | 10-20% accuracy |
| 🟡 RECOMMENDED | TSF Return | Calculate from slurry density | MEDIUM | Site-specific |
| 🟡 RECOMMENDED | Rainfall | Add runoff coefficient | LOW | Better catchment tracking |
| 🟢 OPTIONAL | Uncertainty | Add confidence intervals | MEDIUM | Regulatory compliance |
| 🟢 VALIDATED | Tailings Retention | Current method correct | NONE | N/A |
| 🟢 VALIDATED | Ore Moisture | Current method correct | NONE | N/A |
| 🟢 VALIDATED | Master Equation | Current method correct | NONE | N/A |

---

### 📚 Academic References

1. **Fell, R., MacGregor, P., Stapledon, D., Bell, G., & Foster, M. (2015)**. *Geotechnical Engineering of Dams* (2nd ed.). CRC Press. ISBN: 978-1138000087
   - Chapter 12: Seepage analysis and control

2. **Jewell, R.J., & Fourie, A.B. (2015)**. *Paste and Thickened Tailings – A Guide* (3rd ed.). Australian Centre for Geomechanics.
   - Chapters 4-6: Water balance in tailings systems

3. **Allen, R.G., Pereira, L.S., Raes, D., & Smith, M. (1998)**. *Crop Evapotranspiration - Guidelines for Computing Crop Water Requirements*. FAO Irrigation and Drainage Paper 56. 
   - Penman-Monteith equation

4. **ICMM (2017)**. *A Practical Guide to Consistent Water Reporting*. International Council on Mining and Metals.
   - Industry standard water accounting

5. **ANCOLD (2019)**. *Guidelines on Tailings Dams*. Australian National Committee on Large Dams.
   - Australian regulatory framework

6. **Linacre, E.T. (1977)**. "A simple formula for estimating evaporation rates in various climates using temperature data alone". *Journal of Hydrology*, 34(3-4), pp.255-271.
   - Simplified evaporation model

7. **Das, B.M. (2016)**. *Principles of Geotechnical Engineering* (9th ed.). Cengage Learning.
   - Soil mechanics fundamentals

8. **Karassik, I.J., Messina, J.P., Cooper, P., & Heald, C.C. (2008)**. *Pump Handbook* (4th ed.). McGraw-Hill.
   - Pump hydraulics

---

## 💧 Storage Facility Science (Dam Equations)

This section documents the scientific basis for per-facility water balance calculations, including how lined vs unlined dams behave, seepage equations, and how rainfall/evaporation contribute to storage.

### Facility Balance Equation

Each storage facility (dam, TSF, RWD) follows this water balance:

```
Closing_Volume = Opening_Volume + Inflows - Outflows

Where:
  Inflows = facility_inflow + rainfall_gain + seepage_gain + transfers_in
  Outflows = facility_outflow + evaporation_loss + seepage_loss + transfers_out + abstraction
```

### Dam Lining and Seepage

**Scientific Basis:** Dams/facilities can be **lined** (HDPE, clay) or **unlined** (natural soil). Lining significantly affects seepage rates.

| Dam Type | Typical Seepage Rate | Legacy Constant |
|----------|---------------------|-----------------|
| **Lined** (HDPE, clay) | 0.1% of volume/month | `lined_seepage_rate_pct = 0.1` |
| **Unlined** (natural) | 0.5% of volume/month | `unlined_seepage_rate_pct = 0.5` |

**Legacy Code (Currently Correct):**
```python
# c:\PROJECTS\Water-Balance-Application\src\utils\water_balance_calculator.py lines 1410-1422

is_lined = facility.get('is_lined', 0)  # DB field: 1=lined, 0=unlined
if is_lined:
    seepage_loss_rate_pct = self.get_constant('lined_seepage_rate_pct', 0.1) / 100.0
else:
    seepage_loss_rate_pct = self.get_constant('unlined_seepage_rate_pct', 0.5) / 100.0

current_vol = facility.get('current_volume', 0)
facility_seepage_loss = current_vol * seepage_loss_rate_pct
outflows += facility_seepage_loss
```

**Seepage Loss Equation:**
```
Seepage_Loss (m³) = Current_Volume (m³) × Seepage_Rate (%)

Where:
  - Lined dams:   Seepage_Rate = 0.1% = 0.001
  - Unlined dams: Seepage_Rate = 0.5% = 0.005
```

**Seepage Gain (Aquifer Contribution):**
Some facilities receive groundwater seepage INTO the dam from underlying aquifers.

```python
# Legacy code:
aquifer_gain_rate_pct = facility.get('aquifer_gain_rate_pct', 0.0)
facility_seepage_gain = current_vol * aquifer_gain_rate_pct / 100.0
inflows += facility_seepage_gain
```

**Seepage Gain Equation:**
```
Seepage_Gain (m³) = Current_Volume (m³) × Aquifer_Gain_Rate (%)

Notes:
  - Aquifer gain rate is per-facility (from DB field)
  - Default = 0.0% (no aquifer contribution)
  - Some TSFs may have positive aquifer gain (underground water seeping in)
```

### Rainfall Contribution to Storage

**Scientific Basis:** Rainfall falling directly on the water surface adds volume to storage.

**Legacy Code:**
```python
# Regional rainfall applies to all facilities (from environmental data)
rainfall_mm = self.db.get_regional_rainfall_monthly(month, year)

# Only apply if facility has evaporation enabled (surface area > 0)
if evap_enabled and surface_area > 0:
    rainfall_volume = (rainfall_mm / 1000.0) * surface_area
    inflows += rainfall_volume
```

**Rainfall Volume Equation:**
```
Rainfall_Volume (m³) = Rainfall (mm) × (1m / 1000mm) × Surface_Area (m²)

Simplified:
Rainfall_Volume = Rainfall_mm × Surface_Area_m² / 1000

Example:
  Rainfall: 50 mm/month
  Surface Area: 10,000 m²
  Volume: 50 × 10,000 / 1000 = 500 m³
```

**Key Notes:**
- Only facilities with `evap_active = 1` receive rainfall
- Surface area of 0 = no rainfall contribution
- Regional rainfall (mm) comes from environmental monitoring data

### Evaporation Loss from Storage

**Scientific Basis:** Water evaporates from open water surfaces. Rate depends on pan evaporation (measured) and pan coefficient (0.7 typical).

**Legacy Code:**
```python
if evap_enabled and surface_area > 0:
    regional_evap_mm = self.db.get_regional_evaporation_monthly(month, year)
    if regional_evap_mm and regional_evap_mm > 0:
        evap_loss = (regional_evap_mm / 1000.0) * surface_area
        # Cap evaporation so it cannot exceed current available volume
        evap_loss = min(evap_loss, current_vol)
    outflows += evap_loss
```

**Evaporation Volume Equation:**
```
Evap_Volume (m³) = Pan_Evap (mm) × Pan_Coefficient × Surface_Area (m²) / 1000

Standard Pan Coefficient: 0.7 (Class A pan to lake conversion)

Capping Rule:
  Evap_Volume = min(Evap_Volume, Current_Volume)
  # Can't evaporate more water than exists!

Example:
  Pan Evap: 150 mm/month (summer)
  Pan Coefficient: 0.7
  Surface Area: 10,000 m²
  Volume: 150 × 0.7 × 10,000 / 1000 = 1,050 m³
```

**Key Constants:**
| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `EVAP_PAN_COEFF` | 0.7 | factor | Pan to lake evaporation conversion |

### Complete Facility Balance Calculator

**New Modular Implementation:**
```python
# services/calculation/storage/facility_balance.py

class FacilityBalanceCalculator:
    """Per-facility water balance with scientific accuracy.
    
    Handles:
    - Lined vs unlined seepage rates
    - Aquifer seepage gain
    - Rainfall contribution (area-based)
    - Evaporation loss (area-based, capped)
    - Overflow protection
    - Deficit tracking
    """
    
    def __init__(self, constants: ConstantsService):
        self.constants = constants
    
    def calculate(
        self,
        facility: FacilityState,
        period: CalculationPeriod,
        environmental: EnvironmentalData
    ) -> FacilityBalanceResult:
        """Calculate complete facility balance.
        
        Args:
            facility: Current facility state (from DB)
            period: Month/year for calculation
            environmental: Rainfall and evaporation data
        
        Returns:
            FacilityBalanceResult with all components
        """
        # --- SEEPAGE LOSS ---
        if facility.is_lined:
            seepage_rate = self.constants.get('lined_seepage_rate_pct', 0.1) / 100
        else:
            seepage_rate = self.constants.get('unlined_seepage_rate_pct', 0.5) / 100
        
        seepage_loss = facility.current_volume * seepage_rate
        
        # --- SEEPAGE GAIN (aquifer) ---
        aquifer_rate = facility.aquifer_gain_rate_pct / 100
        seepage_gain = facility.current_volume * aquifer_rate
        
        # --- RAINFALL GAIN ---
        rainfall_gain = 0.0
        if facility.evap_active and facility.surface_area > 0:
            rainfall_gain = (environmental.rainfall_mm / 1000) * facility.surface_area
        
        # --- EVAPORATION LOSS ---
        evap_loss = 0.0
        if facility.evap_active and facility.surface_area > 0:
            pan_coeff = self.constants.get('EVAP_PAN_COEFF', 0.7)
            evap_loss = (environmental.pan_evap_mm * pan_coeff / 1000) * facility.surface_area
            # Cap: can't evaporate more than exists
            evap_loss = min(evap_loss, facility.current_volume)
        
        # --- TOTAL INFLOWS/OUTFLOWS ---
        total_inflows = (
            facility.inflow_m3 +
            rainfall_gain +
            seepage_gain +
            facility.transfers_in
        )
        
        total_outflows = (
            facility.outflow_m3 +
            evap_loss +
            seepage_loss +
            facility.transfers_out +
            facility.abstraction_m3
        )
        
        # --- CLOSING VOLUME ---
        net_change = total_inflows - total_outflows
        theoretical_closing = facility.current_volume + net_change
        
        # Handle overflow (can't exceed capacity)
        if theoretical_closing > facility.capacity:
            overflow = theoretical_closing - facility.capacity
            closing_volume = facility.capacity
        else:
            overflow = 0.0
            closing_volume = max(0, theoretical_closing)
        
        # Handle deficit (shouldn't go negative)
        deficit = abs(min(0, theoretical_closing))
        
        return FacilityBalanceResult(
            facility_code=facility.code,
            facility_name=facility.name,
            opening_volume=facility.current_volume,
            closing_volume=closing_volume,
            
            # Inflow components
            rainfall_gain=rainfall_gain,
            seepage_gain=seepage_gain,
            transfers_in=facility.transfers_in,
            facility_inflow=facility.inflow_m3,
            
            # Outflow components
            evaporation_loss=evap_loss,
            seepage_loss=seepage_loss,
            transfers_out=facility.transfers_out,
            facility_outflow=facility.outflow_m3,
            abstraction=facility.abstraction_m3,
            
            # Derived
            net_change=closing_volume - facility.current_volume,
            overflow=overflow,
            deficit=deficit,
            utilization_pct=(closing_volume / facility.capacity * 100) if facility.capacity > 0 else 0,
            
            # Flags
            is_lined=facility.is_lined,
            evap_active=facility.evap_active
        )
```

### Database Fields Required

```sql
-- storage_facilities table fields for dam science:
CREATE TABLE storage_facilities (
    id INTEGER PRIMARY KEY,
    facility_code TEXT UNIQUE NOT NULL,
    facility_name TEXT,
    
    -- Capacity
    total_capacity REAL DEFAULT 0,
    current_volume REAL DEFAULT 0,
    
    -- Surface properties (for rainfall/evap)
    surface_area REAL DEFAULT 0,  -- m² (0 = no rainfall/evap applied)
    evap_active INTEGER DEFAULT 1,  -- 1=enabled, 0=disabled
    
    -- Lining status (for seepage)
    is_lined INTEGER DEFAULT 0,  -- 1=lined (HDPE/clay), 0=unlined
    
    -- Aquifer contribution
    aquifer_gain_rate_pct REAL DEFAULT 0,  -- % per month
    
    -- Other fields...
    FOREIGN KEY (area_code) REFERENCES mine_areas(code)
);
```

### Summary of Dam Science Equations

| Component | Equation | Units |
|-----------|----------|-------|
| **Seepage Loss (Lined)** | `V × 0.001` | m³/month |
| **Seepage Loss (Unlined)** | `V × 0.005` | m³/month |
| **Seepage Gain (Aquifer)** | `V × aquifer_rate / 100` | m³/month |
| **Rainfall Gain** | `rainfall_mm × area / 1000` | m³/month |
| **Evaporation Loss** | `min(evap_mm × 0.7 × area / 1000, V)` | m³/month |
| **Overflow** | `max(0, closing - capacity)` | m³ |
| **Closing Volume** | `opening + inflows - outflows` (capped) | m³ |

---

## �📅 Implementation Phases

### Phase 1: Foundation (Sprint 1)
**Goal:** Create base structure and data models

| Task | Description | Est. Hours |
|------|-------------|------------|
| 1.1 | Create `services/calculation/` folder structure | 2 |
| 1.2 | Implement Pydantic models (`models.py`) | 4 |
| 1.3 | Define interfaces (`interfaces.py`) | 3 |
| 1.4 | Create constants loader (`constants.py`) | 4 |
| 1.5 | Set up unit test structure | 3 |
| 1.6 | Create mock data for testing | 4 |

**Deliverables:**
- [ ] All data models with validation
- [ ] Abstract interfaces defined
- [ ] Constants loading from DB/config
- [ ] Test fixtures ready

### Phase 2: Inflows Module (Sprint 1-2)
**Goal:** Implement all inflow calculations

| Task | Description | Est. Hours |
|------|-------------|------------|
| 2.1 | Implement `surface_water.py` calculator | 4 |
| 2.2 | Implement `groundwater.py` calculator | 4 |
| 2.3 | Implement `rainfall.py` calculator | 3 |
| 2.4 | Implement `recycled.py` (RWD/TSF return) | 4 |
| 2.5 | Create `inflows_service.py` orchestrator | 3 |
| 2.6 | Unit tests for inflows (90% coverage) | 6 |

**Deliverables:**
- [ ] All inflow calculators working
- [ ] Inflows service aggregating results
- [ ] Excel/DB data loading abstracted
- [ ] Unit tests passing

### Phase 3: Outflows Module (Sprint 2)
**Goal:** Implement all outflow calculations

| Task | Description | Est. Hours |
|------|-------------|------------|
| 3.1 | Implement `plant_consumption.py` | 4 |
| 3.2 | Implement `evaporation.py` with Meyer formula | 6 |
| 3.3 | Implement `discharge.py` (seepage, discharge) | 4 |
| 3.4 | Create `outflows_service.py` orchestrator | 3 |
| 3.5 | Unit tests for outflows (90% coverage) | 6 |

**Deliverables:**
- [ ] All outflow calculators working
- [ ] Improved evaporation model
- [ ] Unit tests passing

### Phase 4: Storage Module (Sprint 2-3)
**Goal:** Implement storage and pump transfers

| Task | Description | Est. Hours |
|------|-------------|------------|
| 4.1 | Implement `facility_balance.py` | 6 |
| 4.2 | Implement `pump_transfers.py` with fixes | 8 |
| 4.3 | Add overflow handling logic | 4 |
| 4.4 | Create `storage_service.py` orchestrator | 4 |
| 4.5 | Unit tests with edge cases | 8 |

**Deliverables:**
- [ ] Per-facility balance calculations
- [ ] Scientifically-accurate pump transfers
- [ ] Overflow handling with warnings
- [ ] Unit tests for edge cases

### Phase 5: Balance Engine (Sprint 3)
**Goal:** Integrate all services into main engine

| Task | Description | Est. Hours |
|------|-------------|------------|
| 5.1 | Implement `engine.py` orchestrator | 6 |
| 5.2 | Implement closure error calculation | 4 |
| 5.3 | Add data quality validation | 4 |
| 5.4 | Integration tests | 8 |
| 5.5 | Performance optimization (caching) | 4 |

**Deliverables:**
- [ ] Full balance calculation working
- [ ] Closure error tracking
- [ ] Data quality flags
- [ ] Integration tests passing

### Phase 6: KPIs & Persistence (Sprint 3-4)
**Goal:** Add KPIs and database storage

| Task | Description | Est. Hours |
|------|-------------|------------|
| 6.1 | Implement KPI calculators | 6 |
| 6.2 | Create database repository | 6 |
| 6.3 | Design calculation results table | 4 |
| 6.4 | Implement result persistence | 4 |
| 6.5 | Add historical comparison queries | 4 |

**Deliverables:**
- [ ] All KPIs calculated
- [ ] Results saved to database
- [ ] Historical data queryable
- [ ] Audit trail for calculations

### Phase 7: UI Integration (Sprint 4)
**Goal:** Connect engine to PySide6 dashboards

| Task | Description | Est. Hours |
|------|-------------|------------|
| 7.1 | Create service facade for UI | 4 |
| 7.2 | Update calculations_page.py | 8 |
| 7.3 | Update analytics_page.py | 6 |
| 7.4 | Add loading/error states | 4 |
| 7.5 | End-to-end testing | 8 |

**Deliverables:**
- [ ] UI fully connected to new engine
- [ ] Loading states for calculations
- [ ] Error handling and display
- [ ] E2E tests passing

---

## 🗄️ Database Schema Updates

### New Table: calculation_results

```sql
CREATE TABLE IF NOT EXISTS calculation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Period
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year INTEGER NOT NULL CHECK(year >= 2020),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Inflows (all in m³)
    surface_water_m3 REAL NOT NULL DEFAULT 0,
    groundwater_m3 REAL NOT NULL DEFAULT 0,
    underground_dewatering_m3 REAL NOT NULL DEFAULT 0,
    rainfall_m3 REAL NOT NULL DEFAULT 0,
    ore_moisture_m3 REAL NOT NULL DEFAULT 0,
    tsf_return_m3 REAL NOT NULL DEFAULT 0,
    rwd_inflow_m3 REAL NOT NULL DEFAULT 0,
    total_inflows_m3 REAL NOT NULL DEFAULT 0,
    
    -- Outflows
    plant_consumption_m3 REAL NOT NULL DEFAULT 0,
    evaporation_m3 REAL NOT NULL DEFAULT 0,
    discharge_m3 REAL NOT NULL DEFAULT 0,
    seepage_m3 REAL NOT NULL DEFAULT 0,
    dust_suppression_m3 REAL NOT NULL DEFAULT 0,
    mining_consumption_m3 REAL NOT NULL DEFAULT 0,
    domestic_consumption_m3 REAL NOT NULL DEFAULT 0,
    product_moisture_m3 REAL NOT NULL DEFAULT 0,
    tailings_retention_m3 REAL NOT NULL DEFAULT 0,
    total_outflows_m3 REAL NOT NULL DEFAULT 0,
    
    -- Storage
    total_storage_change_m3 REAL NOT NULL DEFAULT 0,
    
    -- Closure
    closure_error_m3 REAL NOT NULL DEFAULT 0,
    closure_error_percent REAL NOT NULL DEFAULT 0,
    closure_status TEXT CHECK(closure_status IN ('GREEN', 'YELLOW', 'RED')),
    
    -- Quality
    is_valid BOOLEAN DEFAULT 1,
    warnings TEXT,  -- JSON array
    errors TEXT,    -- JSON array
    
    -- Metadata
    created_by TEXT DEFAULT 'system',
    notes TEXT,
    
    UNIQUE(month, year)
);

-- Index for quick period lookups
CREATE INDEX IF NOT EXISTS idx_calc_results_period 
ON calculation_results(year, month);
```

### New Table: facility_storage_history

```sql
CREATE TABLE IF NOT EXISTS facility_storage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id INTEGER REFERENCES calculation_results(id),
    
    facility_code TEXT NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    
    opening_volume_m3 REAL NOT NULL DEFAULT 0,
    closing_volume_m3 REAL NOT NULL DEFAULT 0,
    rainfall_gain_m3 REAL NOT NULL DEFAULT 0,
    evaporation_loss_m3 REAL NOT NULL DEFAULT 0,
    seepage_loss_m3 REAL NOT NULL DEFAULT 0,
    transfers_in_m3 REAL NOT NULL DEFAULT 0,
    transfers_out_m3 REAL NOT NULL DEFAULT 0,
    overflow_m3 REAL NOT NULL DEFAULT 0,
    
    level_percent REAL,
    
    FOREIGN KEY (facility_code) REFERENCES storage_facilities(code)
);
```

---

## ⚙️ Configuration Schema

### New: calculation_config.yaml

```yaml
calculation:
  # Closure error thresholds
  closure_thresholds:
    green_max_percent: 5.0
    yellow_max_percent: 10.0
    # Above 10% = RED
  
  # Evaporation model settings
  evaporation:
    model: "meyer"  # Options: "simple", "meyer", "penman"
    pan_coefficient: 0.7
    default_pan_evap_mm_day: 5.0
  
  # Pump transfer settings
  pump_transfers:
    enabled: true
    default_start_level_percent: 70
    cascade_enabled: true  # Allow A→B→C transfers
    max_cascade_depth: 3
  
  # Data quality settings
  data_quality:
    max_allowed_overflow_percent: 5.0
    warn_on_negative_storage: true
    require_all_facilities: true
  
  # Caching
  cache:
    enabled: true
    ttl_seconds: 3600
    invalidate_on_excel_update: true
```

---

## ✅ Acceptance Criteria

### Functional Requirements

- [ ] Calculate complete water balance for any month/year
- [ ] All inflow components calculated correctly
- [ ] All outflow components calculated correctly
- [ ] Per-facility storage changes tracked
- [ ] Pump transfers use physically-accurate logic
- [ ] Overflow handling prevents >100% storage
- [ ] Closure error calculated: `error = fresh_in - out - ΔS`
- [ ] All KPIs computed (efficiency, recycling, storage)
- [ ] Results persisted to database
- [ ] Historical results queryable
- [ ] UI displays calculation results
- [ ] Manual inputs saveable per month

### Non-Functional Requirements

- [ ] Calculation completes in <2 seconds
- [ ] Unit test coverage >85%
- [ ] All services injectable (DI-ready)
- [ ] No direct Excel access from services (abstracted)
- [ ] Configuration-driven (no hardcoded constants)
- [ ] Logging on all calculation steps
- [ ] Error handling with user-friendly messages

### Quality Gates

- [ ] All tests pass
- [ ] No lint errors
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Performance benchmarks met

---

## � Development Phase: Scientific Improvements Implementation

Based on the Scientific Review, these are the prioritized improvements to implement. Each task includes database changes, service code, and tests.

### Sprint 0: Foundation (Pre-requisites)

**Objective:** Set up the modular service architecture before implementing scientific improvements.

#### Task 0.1: Create Calculation Services Directory Structure
```
src/services/calculation/
├── __init__.py
├── interfaces.py           # Abstract base classes
├── models.py              # Pydantic data models
├── constants.py           # Constants loader from DB
├── seepage_calculator.py  # NEW: Darcy's Law implementation
├── evaporation_calculator.py  # NEW: Temperature-adjusted
├── rainfall_calculator.py     # NEW: Runoff coefficients
├── tsf_return_calculator.py   # NEW: Variable % by slurry
├── pump_transfer_calculator.py # NEW: Pump curve physics
└── uncertainty_calculator.py   # NEW: Confidence intervals
```

#### Task 0.2: Database Migration Script
```sql
-- File: src/database/migrations/001_scientific_improvements.sql

-- Seepage improvements (Darcy's Law)
ALTER TABLE storage_facilities ADD COLUMN liner_type TEXT DEFAULT 'sandy_clay';
ALTER TABLE storage_facilities ADD COLUMN liner_thickness_m REAL DEFAULT 1.0;
ALTER TABLE storage_facilities ADD COLUMN base_area_m2 REAL DEFAULT 0;
ALTER TABLE storage_facilities ADD COLUMN water_depth_m REAL DEFAULT 0;

-- Pump transfer improvements
ALTER TABLE storage_facilities ADD COLUMN pump_capacity_m3_hr REAL DEFAULT 0;
ALTER TABLE storage_facilities ADD COLUMN pump_head_m REAL DEFAULT 0;
ALTER TABLE storage_facilities ADD COLUMN operating_hours_month REAL DEFAULT 720;

-- TSF return improvements
ALTER TABLE system_constants ADD COLUMN IF NOT EXISTS slurry_solids_percent REAL DEFAULT 50;

-- Catchment tracking for rainfall runoff
CREATE TABLE IF NOT EXISTS facility_catchment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER NOT NULL REFERENCES storage_facilities(id),
    surface_type TEXT NOT NULL,  -- 'open_water', 'bare_rock', 'tailings_beach', 'grassed', 'natural_bush'
    area_m2 REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(facility_id, surface_type)
);

-- Monthly weather data for improved evaporation
CREATE TABLE IF NOT EXISTS monthly_weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    mean_temp_c REAL,
    pan_evaporation_mm REAL,
    rainfall_mm REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month)
);
```

---

### Sprint 1: Critical - Seepage & Pump Transfers (HIGH Priority)

#### Task 1.1: Implement Darcy's Law Seepage Calculator
**File:** `src/services/calculation/seepage_calculator.py`

```python
"""Darcy's Law-based seepage calculation service.

Scientific Reference:
- Fell et al. (2015) "Geotechnical Engineering of Dams" - Chapter 12
- ANCOLD Guidelines (2019)

Replaces: Legacy % of volume approach (0.1%/0.5%)
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class SeepageResult:
    """Result of seepage calculation."""
    seepage_m3_month: float
    liner_type: str
    hydraulic_conductivity: float
    hydraulic_gradient: float
    method: str = "darcy_law"

class SeepageCalculator:
    """Calculate seepage using Darcy's Law: Q = K × i × A."""
    
    # Hydraulic conductivity values (m/s) from geotechnical literature
    CONDUCTIVITY = {
        'hdpe_liner': 1e-12,      # HDPE geomembrane
        'clay_liner': 1e-9,       # Compacted clay (600mm)
        'sandy_clay': 1e-7,       # Sandy clay (unlined)
        'silty_sand': 1e-5,       # Silty sand (poor)
        'fractured_rock': 1e-6,   # Fractured bedrock
    }
    
    SECONDS_PER_MONTH = 30 * 24 * 3600  # 2,592,000
    
    def calculate(
        self,
        water_depth_m: float,
        base_area_m2: float,
        liner_type: str = 'sandy_clay',
        liner_thickness_m: float = 1.0
    ) -> SeepageResult:
        """Calculate monthly seepage volume using Darcy's Law.
        
        Args:
            water_depth_m: Current water depth (hydraulic head driver)
            base_area_m2: Dam base/footprint area
            liner_type: Type of liner or soil
            liner_thickness_m: Seepage path length
        
        Returns:
            SeepageResult with volume and calculation details
        """
        K = self.CONDUCTIVITY.get(liner_type, 1e-7)
        i = water_depth_m / liner_thickness_m  # Hydraulic gradient
        Q_per_second = K * i * base_area_m2
        seepage_m3 = Q_per_second * self.SECONDS_PER_MONTH
        
        return SeepageResult(
            seepage_m3_month=seepage_m3,
            liner_type=liner_type,
            hydraulic_conductivity=K,
            hydraulic_gradient=i
        )
    
    def calculate_legacy(
        self,
        current_volume_m3: float,
        is_lined: bool
    ) -> float:
        """Legacy calculation for backward compatibility.
        
        DEPRECATED: Use calculate() with Darcy's Law instead.
        """
        rate = 0.001 if is_lined else 0.005  # 0.1% or 0.5%
        return current_volume_m3 * rate
```

**Tests:** `tests/services/calculation/test_seepage_calculator.py`
- [ ] Test HDPE liner gives near-zero seepage
- [ ] Test unlined dam gives higher seepage than lined
- [ ] Test seepage increases with water depth
- [ ] Test legacy method matches old behavior
- [ ] Compare Darcy vs legacy for typical scenarios

---

#### Task 1.2: Implement Physics-Based Pump Transfer Calculator
**File:** `src/services/calculation/pump_transfer_calculator.py`

```python
"""Physics-based pump transfer calculation.

Scientific Reference:
- Karassik et al. (2008) "Pump Handbook" - Pump curves and system curves

Replaces: Legacy 5% of volume when level > 70%
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class PumpTransferResult:
    """Result of pump transfer calculation."""
    transfer_volume_m3: float
    limited_by: str  # 'pump_capacity', 'destination_full', 'source_empty', 'none'
    pump_operating_hours: float
    actual_flow_rate_m3_hr: float

class PumpTransferCalculator:
    """Calculate pump transfers based on pump capacity and constraints."""
    
    MINIMUM_SOURCE_LEVEL_PCT = 10  # NPSH protection - stop pumping at 10%
    
    def calculate(
        self,
        pump_capacity_m3_hr: float,
        operating_hours: float,
        source_volume_m3: float,
        source_capacity_m3: float,
        destination_volume_m3: float,
        destination_capacity_m3: float,
        trigger_level_pct: float = 70.0
    ) -> PumpTransferResult:
        """Calculate realistic pump transfer volume.
        
        Args:
            pump_capacity_m3_hr: Rated pump capacity
            operating_hours: Hours pump runs this month
            source_volume_m3: Current volume in source
            source_capacity_m3: Max capacity of source
            destination_volume_m3: Current volume in destination
            destination_capacity_m3: Max capacity of destination
            trigger_level_pct: Level % at which pumping starts
        
        Returns:
            PumpTransferResult with volume and limiting factor
        """
        source_level_pct = (source_volume_m3 / source_capacity_m3) * 100
        
        # Check if transfer is triggered
        if source_level_pct < trigger_level_pct:
            return PumpTransferResult(
                transfer_volume_m3=0,
                limited_by='below_trigger',
                pump_operating_hours=0,
                actual_flow_rate_m3_hr=0
            )
        
        # Maximum theoretical transfer
        max_pump_volume = pump_capacity_m3_hr * operating_hours
        
        # Limit by destination headroom
        destination_headroom = destination_capacity_m3 - destination_volume_m3
        
        # Limit by source availability (above minimum level)
        min_source_volume = source_capacity_m3 * (self.MINIMUM_SOURCE_LEVEL_PCT / 100)
        available_source = max(0, source_volume_m3 - min_source_volume)
        
        # Apply constraints
        transfer_volume = min(max_pump_volume, destination_headroom, available_source)
        
        # Determine limiting factor
        if transfer_volume == 0:
            limited_by = 'source_empty' if available_source == 0 else 'destination_full'
        elif transfer_volume < max_pump_volume:
            if transfer_volume == destination_headroom:
                limited_by = 'destination_full'
            else:
                limited_by = 'source_empty'
        else:
            limited_by = 'pump_capacity'
        
        # Calculate actual operating hours
        actual_hours = transfer_volume / pump_capacity_m3_hr if pump_capacity_m3_hr > 0 else 0
        
        return PumpTransferResult(
            transfer_volume_m3=transfer_volume,
            limited_by=limited_by,
            pump_operating_hours=actual_hours,
            actual_flow_rate_m3_hr=pump_capacity_m3_hr
        )
    
    def calculate_legacy(
        self,
        current_volume_m3: float,
        level_pct: float,
        trigger_level_pct: float = 70.0
    ) -> float:
        """Legacy calculation for backward compatibility.
        
        DEPRECATED: Use calculate() with pump physics instead.
        """
        if level_pct >= trigger_level_pct:
            return current_volume_m3 * 0.05  # 5% of volume
        return 0.0
```

**Tests:** `tests/services/calculation/test_pump_transfer_calculator.py`
- [ ] Test no transfer below trigger level
- [ ] Test transfer limited by pump capacity
- [ ] Test transfer limited by destination headroom
- [ ] Test source doesn't go below 10% (NPSH protection)
- [ ] Test legacy method matches old behavior

---

### Sprint 2: Recommended - Evaporation & TSF Return (MEDIUM Priority)

#### Task 2.1: Implement Temperature-Adjusted Evaporation
**File:** `src/services/calculation/evaporation_calculator.py`

```python
"""Temperature-adjusted evaporation calculation.

Scientific Reference:
- Linacre (1977) Journal of Hydrology
- Australian Bureau of Meteorology Technical Report No. 76

Enhancement: Adds temperature factor to pan evaporation coefficient.
"""
from dataclasses import dataclass

@dataclass
class EvaporationResult:
    """Result of evaporation calculation."""
    evaporation_m3: float
    pan_coefficient: float
    temperature_factor: float
    adjusted_coefficient: float
    method: str

class EvaporationCalculator:
    """Calculate evaporation with temperature adjustment."""
    
    DEFAULT_PAN_COEFFICIENT = 0.7  # Class A pan to lake conversion
    
    def calculate_with_temperature(
        self,
        surface_area_m2: float,
        pan_evap_mm: float,
        mean_temp_c: float,
        pan_coefficient: float = 0.7
    ) -> EvaporationResult:
        """Calculate evaporation with temperature adjustment.
        
        Temperature factor: Higher temps = higher actual evap relative to pan.
        Range: 0.9 (cold, <10°C) to 1.1 (hot, >35°C)
        """
        # Temperature adjustment factor
        temp_factor = 0.95 + (mean_temp_c / 500)  # ~1.0 at 25°C
        temp_factor = max(0.85, min(1.15, temp_factor))  # Clamp to reasonable range
        
        adjusted_coeff = pan_coefficient * temp_factor
        evap_m = (pan_evap_mm * adjusted_coeff) / 1000
        evap_m3 = surface_area_m2 * evap_m
        
        return EvaporationResult(
            evaporation_m3=evap_m3,
            pan_coefficient=pan_coefficient,
            temperature_factor=temp_factor,
            adjusted_coefficient=adjusted_coeff,
            method='pan_temperature_adjusted'
        )
    
    def calculate_linacre(
        self,
        surface_area_m2: float,
        mean_temp_c: float,
        latitude_deg: float,
        days_in_month: int = 30
    ) -> EvaporationResult:
        """Calculate evaporation using Linacre (1977) formula.
        
        Use when pan evaporation data is unavailable.
        """
        # Linacre simplified formula
        E_mm_day = (500 * mean_temp_c / (100 - abs(latitude_deg)) + 75) / (80 - mean_temp_c)
        E_mm_day = max(0, E_mm_day)
        
        monthly_mm = E_mm_day * days_in_month
        evap_m3 = (monthly_mm / 1000) * surface_area_m2
        
        return EvaporationResult(
            evaporation_m3=evap_m3,
            pan_coefficient=0,
            temperature_factor=1.0,
            adjusted_coefficient=0,
            method='linacre_formula'
        )
    
    def calculate_legacy(
        self,
        surface_area_m2: float,
        pan_evap_mm: float,
        pan_coefficient: float = 0.7
    ) -> float:
        """Legacy calculation for backward compatibility."""
        evap_m = (pan_evap_mm * pan_coefficient) / 1000
        return surface_area_m2 * evap_m
```

---

#### Task 2.2: Implement Variable TSF Return Calculator
**File:** `src/services/calculation/tsf_return_calculator.py`

```python
"""Variable TSF return water calculation based on slurry density.

Scientific Reference:
- Jewell & Fourie (2015) "Paste and Thickened Tailings - A Guide"
- Wates (2015) "Tailings Storage Facilities" - SAIMM Handbook

Replaces: Fixed 36% constant
"""
from dataclasses import dataclass
from enum import Enum

class TailingsType(Enum):
    """Classification of tailings by solids content."""
    CONVENTIONAL = "conventional"      # ≤35% solids
    THICKENED = "thickened"           # 35-55% solids
    PASTE = "paste"                   # 55-70% solids
    FILTERED = "filtered"             # >70% solids

@dataclass
class TSFReturnResult:
    """Result of TSF return calculation."""
    return_water_m3: float
    return_percentage: float
    tailings_type: TailingsType
    slurry_solids_pct: float
    method: str

class TSFReturnCalculator:
    """Calculate TSF return water based on slurry properties."""
    
    # Return percentages by tailings type (% of slurry water that returns)
    RETURN_PERCENTAGES = {
        TailingsType.CONVENTIONAL: 0.55,  # 55% return
        TailingsType.THICKENED: 0.36,     # 36% return (current default)
        TailingsType.PASTE: 0.20,         # 20% return
        TailingsType.FILTERED: 0.10,      # 10% return
    }
    
    def classify_tailings(self, slurry_solids_pct: float) -> TailingsType:
        """Classify tailings type by solids content."""
        if slurry_solids_pct <= 35:
            return TailingsType.CONVENTIONAL
        elif slurry_solids_pct <= 55:
            return TailingsType.THICKENED
        elif slurry_solids_pct <= 70:
            return TailingsType.PASTE
        else:
            return TailingsType.FILTERED
    
    def calculate(
        self,
        plant_consumption_m3: float,
        slurry_solids_pct: float
    ) -> TSFReturnResult:
        """Calculate TSF return water based on slurry density.
        
        Args:
            plant_consumption_m3: Total water consumed by plant
            slurry_solids_pct: % solids in tailings slurry (by weight)
        
        Returns:
            TSFReturnResult with return volume and classification
        """
        tailings_type = self.classify_tailings(slurry_solids_pct)
        return_pct = self.RETURN_PERCENTAGES[tailings_type]
        
        return_water = plant_consumption_m3 * return_pct
        
        return TSFReturnResult(
            return_water_m3=return_water,
            return_percentage=return_pct,
            tailings_type=tailings_type,
            slurry_solids_pct=slurry_solids_pct,
            method='slurry_density_based'
        )
    
    def calculate_legacy(
        self,
        plant_consumption_m3: float,
        return_percentage: float = 0.36
    ) -> float:
        """Legacy calculation for backward compatibility."""
        return plant_consumption_m3 * return_percentage
```

---

### Sprint 3: Recommended - Rainfall Runoff (LOW Priority)

#### Task 3.1: Implement Rainfall Runoff Calculator
**File:** `src/services/calculation/rainfall_calculator.py`

```python
"""Rainfall runoff calculation with catchment coefficients.

Scientific Reference:
- Australian Rainfall and Runoff (ARR) Guidelines 2019
- Mays (2010) "Water Resources Engineering"

Enhancement: Adds catchment areas with runoff coefficients.
"""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class RainfallResult:
    """Result of rainfall calculation."""
    total_inflow_m3: float
    direct_rainfall_m3: float
    catchment_runoff_m3: float
    catchment_breakdown: Dict[str, float]

class RainfallCalculator:
    """Calculate rainfall contribution including catchment runoff."""
    
    # Runoff coefficients by surface type
    RUNOFF_COEFFICIENTS = {
        'open_water': 1.0,       # All rainfall captured
        'bare_rock': 0.85,       # High runoff
        'tailings_beach': 0.40,  # Moderate (some infiltration)
        'grassed': 0.25,         # Low runoff
        'natural_bush': 0.20,    # Lowest (high interception)
        'paved': 0.90,           # Nearly impervious
        'gravel': 0.50,          # Moderate
    }
    
    def calculate(
        self,
        rainfall_mm: float,
        water_surface_area_m2: float,
        catchment_areas: Optional[Dict[str, float]] = None
    ) -> RainfallResult:
        """Calculate total rainfall inflow including catchment runoff.
        
        Args:
            rainfall_mm: Monthly rainfall
            water_surface_area_m2: Dam water surface area
            catchment_areas: Dict of {surface_type: area_m2}
        
        Returns:
            RainfallResult with direct and catchment components
        """
        # Direct rainfall on water surface (100% captured)
        direct_rainfall_m3 = (rainfall_mm / 1000) * water_surface_area_m2
        
        # Runoff from catchment areas
        catchment_runoff_m3 = 0.0
        breakdown = {}
        
        if catchment_areas:
            for surface_type, area in catchment_areas.items():
                C = self.RUNOFF_COEFFICIENTS.get(surface_type, 0.3)
                runoff = (rainfall_mm / 1000) * area * C
                catchment_runoff_m3 += runoff
                breakdown[surface_type] = runoff
        
        return RainfallResult(
            total_inflow_m3=direct_rainfall_m3 + catchment_runoff_m3,
            direct_rainfall_m3=direct_rainfall_m3,
            catchment_runoff_m3=catchment_runoff_m3,
            catchment_breakdown=breakdown
        )
    
    def calculate_legacy(
        self,
        rainfall_mm: float,
        surface_area_m2: float
    ) -> float:
        """Legacy calculation (100% capture on surface only)."""
        return (rainfall_mm / 1000) * surface_area_m2
```

---

### Sprint 4: Optional - Uncertainty Quantification

#### Task 4.1: Implement Uncertainty Calculator
**File:** `src/services/calculation/uncertainty_calculator.py`

```python
"""Uncertainty quantification for water balance calculations.

Scientific Reference:
- ICMM (2017) Water Stewardship Framework
- ISO 14046: Water Footprint Assessment

Provides 95% confidence intervals for closure error.
"""
from dataclasses import dataclass
from typing import Dict, Tuple
import math

@dataclass
class UncertaintyResult:
    """Result of uncertainty calculation."""
    closure_error_m3: float
    uncertainty_m3: float
    confidence_interval_low: float
    confidence_interval_high: float
    is_statistically_significant: bool
    confidence_level: float = 0.95

class UncertaintyCalculator:
    """Calculate uncertainty bands for water balance."""
    
    # Typical measurement uncertainties (± %)
    UNCERTAINTIES = {
        'flow_meter': 0.05,           # ±5% (calibrated)
        'ultrasonic_meter': 0.03,     # ±3% (high accuracy)
        'rain_gauge': 0.10,           # ±10%
        'evaporation_pan': 0.15,      # ±15%
        'storage_survey': 0.05,       # ±5% (bathymetric)
        'level_sensor': 0.02,         # ±2% (pressure transducer)
        'estimated': 0.30,            # ±30% (no measurement)
        'calculated': 0.20,           # ±20% (derived values)
    }
    
    def calculate(
        self,
        inflows: Dict[str, Tuple[float, str]],    # {name: (value, measurement_type)}
        outflows: Dict[str, Tuple[float, str]],
        storage_change: Tuple[float, str]
    ) -> UncertaintyResult:
        """Calculate closure error with 95% confidence interval.
        
        Uses root-sum-square (RSS) for independent uncertainties.
        """
        # Calculate variances
        inflow_variance = sum(
            (val * self.UNCERTAINTIES.get(mtype, 0.3)) ** 2
            for val, mtype in inflows.values()
        )
        
        outflow_variance = sum(
            (val * self.UNCERTAINTIES.get(mtype, 0.3)) ** 2
            for val, mtype in outflows.values()
        )
        
        storage_variance = (
            storage_change[0] * self.UNCERTAINTIES.get(storage_change[1], 0.3)
        ) ** 2
        
        # Total uncertainty (RSS)
        total_uncertainty = math.sqrt(inflow_variance + outflow_variance + storage_variance)
        
        # 95% confidence = 1.96 × standard error
        ci_95 = 1.96 * total_uncertainty
        
        # Calculate closure error
        total_inflows = sum(v[0] for v in inflows.values())
        total_outflows = sum(v[0] for v in outflows.values())
        closure_error = total_inflows - total_outflows - storage_change[0]
        
        return UncertaintyResult(
            closure_error_m3=closure_error,
            uncertainty_m3=ci_95,
            confidence_interval_low=closure_error - ci_95,
            confidence_interval_high=closure_error + ci_95,
            is_statistically_significant=abs(closure_error) > ci_95
        )
```

---

### Implementation Checklist

#### Sprint 0: Foundation
- [ ] Create `src/services/calculation/` directory structure
- [ ] Create `interfaces.py` with abstract base classes
- [ ] Create `models.py` with Pydantic dataclasses
- [ ] Run database migration `001_scientific_improvements.sql`
- [ ] Update `storage_facilities` table with new columns
- [ ] Create `facility_catchment` table
- [ ] Create `monthly_weather` table

#### Sprint 1: Critical Improvements
- [ ] Implement `SeepageCalculator` with Darcy's Law
- [ ] Write tests for seepage (5 test cases)
- [ ] Implement `PumpTransferCalculator` with pump physics
- [ ] Write tests for pump transfers (5 test cases)
- [ ] Update facility management UI to edit new fields
- [ ] Populate liner_type for existing facilities
- [ ] Populate pump_capacity for facilities with pumps

#### Sprint 2: Recommended Improvements
- [ ] Implement `EvaporationCalculator` with temperature adjustment
- [ ] Write tests for evaporation (3 test cases)
- [ ] Implement `TSFReturnCalculator` with slurry density
- [ ] Write tests for TSF return (4 test cases)
- [ ] Add slurry_solids_percent to system constants UI
- [ ] Update calculation UI to show adjusted evaporation

#### Sprint 3: Rainfall Runoff
- [ ] Implement `RainfallCalculator` with runoff coefficients
- [ ] Write tests for rainfall (3 test cases)
- [ ] Create UI for managing facility catchment areas
- [ ] Populate catchment data for key facilities

#### Sprint 4: Uncertainty
- [ ] Implement `UncertaintyCalculator`
- [ ] Write tests for uncertainty (3 test cases)
- [ ] Update calculation UI to show confidence intervals
- [ ] Add uncertainty bands to balance summary display

---

### Integration with Existing Engine

**Strategy:** Gradual replacement with feature flags.

```python
# config/app_config.yaml
calculation_engine:
  use_darcy_seepage: true       # Sprint 1
  use_pump_physics: true        # Sprint 1
  use_temp_evaporation: false   # Sprint 2 (after testing)
  use_variable_tsf_return: false  # Sprint 2
  use_catchment_runoff: false   # Sprint 3
  show_uncertainty: false       # Sprint 4
```

**Facade Pattern:**
```python
# src/services/calculation/calculation_facade.py
class CalculationFacade:
    """Unified interface for all calculation services."""
    
    def __init__(self, config: dict):
        self.seepage = SeepageCalculator()
        self.pump = PumpTransferCalculator()
        self.evaporation = EvaporationCalculator()
        self.tsf_return = TSFReturnCalculator()
        self.rainfall = RainfallCalculator()
        self.uncertainty = UncertaintyCalculator()
        self.config = config
    
    def calculate_seepage(self, facility: dict) -> float:
        if self.config.get('use_darcy_seepage', False):
            result = self.seepage.calculate(
                water_depth_m=facility['water_depth_m'],
                base_area_m2=facility['base_area_m2'],
                liner_type=facility.get('liner_type', 'sandy_clay')
            )
            return result.seepage_m3_month
        else:
            return self.seepage.calculate_legacy(
                current_volume_m3=facility['current_volume'],
                is_lined=facility.get('is_lined', 0)
            )
```

---

## �📚 References

### Legacy Files to Reference
- `c:\PROJECTS\Water-Balance-Application\src\utils\water_balance_calculator.py` (2,477 lines)
- `c:\PROJECTS\Water-Balance-Application\src\utils\balance_engine.py` (~200 lines)
- `c:\PROJECTS\Water-Balance-Application\src\utils\balance_services.py` (~400 lines)
- `c:\PROJECTS\Water-Balance-Application\src\utils\pump_transfer_engine.py` (252 lines)
- `c:\PROJECTS\Water-Balance-Application\src\utils\balance_kpis.py` (~150 lines)

### Database Schema
- `c:\PROJECTS\Water-Balance-Application\src\database\schema.py`

### Equations Reference
- Master equation: `balance_error = fresh_inflows - total_outflows - storage_change`
- Fresh inflows exclude: RWD, recycled water
- Storage change: `Σ(closing - opening)` for all facilities

---

## 📝 Notes

1. **Backward Compatibility**: Old Tkinter app continues working during migration
2. **Testing Strategy**: Test new engine against old engine for same inputs
3. **Rollback Plan**: Feature flag to switch between old/new engines
4. **Data Migration**: Historical results can be re-calculated with new engine

---

**Last Updated:** February 2, 2026  
**Next Review:** Sprint 1 planning  
**Owner:** Development Team
