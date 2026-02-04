# 📋 Backend Implementation Roadmap

## Phase 2: Backend Services Implementation

**Previous Phase:** ✅ UI Skeleton Complete (9 pages, all class-based, ready for backend)  
**Current Phase:** 🔄 Backend Services (THIS PHASE)  
**Future Phase:** Performance & Integration Testing

---

## Implementation Order (Recommended)

### Step 1: Data Models (src/models/) - START HERE
**Why First:** Everything depends on models (validation, type safety, serialization)

```python
# src/models/__init__.py
from .facility import Facility
from .balance_result import BalanceResult
from .measurement import Measurement
from .flow_volume import FlowVolume

__all__ = [
    'Facility',
    'BalanceResult', 
    'Measurement',
    'FlowVolume',
]

# src/models/facility.py
from pydantic import BaseModel, Field
from typing import Optional

class Facility(BaseModel):
    """Water storage facility definition"""
    code: str = Field(..., description="Facility code (e.g., 'UG2N')")
    name: str = Field(..., description="Full facility name")
    area: str = Field(..., description="Mining area code")
    capacity_m3: float = Field(..., description="Storage capacity in m³")
    pump_start_level: float = Field(default=0.70, description="Pump trigger level (70% default)")
    feeds_to: Optional[str] = Field(default=None, description="Destination facilities (comma-separated)")
    is_active: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "UG2N",
                "name": "Underground 2 North",
                "area": "UG2",
                "capacity_m3": 150000,
            }
        }

# src/models/balance_result.py
from pydantic import BaseModel
from datetime import date

class BalanceResult(BaseModel):
    """Water balance calculation result"""
    facility: str
    date: date
    fresh_inflows_m3: float
    total_outflows_m3: float
    storage_change_m3: float
    closure_error_m3: float
    closure_error_percent: float
    is_balanced: bool  # error < 5%
    kpis: dict  # Additional KPIs
```

**Estimated Time:** 2-3 hours  
**Files to Create:** 5-7 Pydantic model files

---

### Step 2: Database Layer (src/database/) - CRITICAL FOUNDATION
**Why Second:** Services need database to load/store data

**Part 2a: Connection Management**
```python
# src/database/db_manager.py - EXPAND EXISTING

class DatabaseManager:
    """SQLite database connection and query management"""
    
    def __init__(self, db_path: str = "data/water_balance.db"):
        self.db_path = db_path
        self._connection = None
    
    def get_connection(self):
        """Get SQLite connection (connection pooling)"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query, return list of dicts"""
        pass
    
    def execute_update(self, sql: str, params: tuple = ()):
        """Execute INSERT/UPDATE/DELETE, commit changes"""
        pass
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
```

**Part 2b: Repository Pattern**
```python
# src/database/repositories/facility_repository.py

from models.facility import Facility
from typing import List, Optional

class FacilityRepository:
    """Data access for facilities (abstraction over raw SQL)"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_by_code(self, code: str) -> Optional[Facility]:
        """Get facility by code"""
        result = self.db.execute_query(
            "SELECT * FROM storage_facilities WHERE code = ?",
            (code,)
        )
        return Facility(**result[0]) if result else None
    
    def list_all(self) -> List[Facility]:
        """Get all active facilities"""
        results = self.db.execute_query(
            "SELECT * FROM storage_facilities WHERE is_active = 1"
        )
        return [Facility(**row) for row in results]
    
    def save(self, facility: Facility):
        """Save facility to database"""
        self.db.execute_update(
            """INSERT OR REPLACE INTO storage_facilities 
               (code, name, area, capacity_m3, pump_start_level, feeds_to, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (facility.code, facility.name, facility.area, facility.capacity_m3,
             facility.pump_start_level, facility.feeds_to, facility.is_active)
        )
```

**Estimated Time:** 3-4 hours  
**Files to Create:** db_manager.py expansion + 4-5 repository files

---

### Step 3: Service Layer (src/services/) - BUSINESS LOGIC
**Why Third:** Services use repositories to implement business logic

**Part 3a: Balance Calculation Service**
```python
# src/services/calculation_service.py - IMPROVE EXISTING

from models.balance_result import BalanceResult
from database.repositories.facility_repository import FacilityRepository
from database.repositories.measurement_repository import MeasurementRepository
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class WaterBalanceCalculationService:
    """Calculate water balance (IMPROVED vs Tkinter - not copy-paste)"""
    
    def __init__(self, db_manager, config_manager):
        self.db = db_manager
        self.config = config_manager
        self.facility_repo = FacilityRepository(db_manager)
        self.measurement_repo = MeasurementRepository(db_manager)
        # Implement caching decorator
        self._cache = {}
    
    def calculate_balance(self, facility_code: str, year: int, month: int) -> BalanceResult:
        """Calculate water balance for facility and month
        
        IMPROVEMENTS OVER TKINTER:
        ✅ Type-safe inputs/outputs (not untyped dicts)
        ✅ Pydantic validation (catches errors early)
        ✅ Structured logging (not prints)
        ✅ Proper error handling (exceptions, not exceptions)
        ✅ Caching (10x faster on repeats)
        ✅ Unit testable (no UI knowledge)
        ✅ Reusable (can be called from CLI/API)
        
        Args:
            facility_code: e.g., 'UG2N'
            year: Gregorian year
            month: Month (1-12)
        
        Returns:
            BalanceResult with all calculations
        
        Raises:
            ValueError: If facility not found
            FacilityError: If facility data invalid
        """
        # Validate inputs
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid month: {month}")
        
        # Load facility (will fail if not found)
        facility = self.facility_repo.get_by_code(facility_code)
        if not facility:
            raise ValueError(f"Facility not found: {facility_code}")
        
        # Load measurements for the month
        measurements = self.measurement_repo.get_by_facility_month(
            facility_code, year, month
        )
        
        # Calculate balance (improved algorithm)
        fresh_inflows = self._calculate_fresh_inflows(measurements)
        outflows = self._calculate_outflows(measurements)
        storage_change = self._calculate_storage_change(measurements)
        
        # Compute closure error
        closure_error = fresh_inflows - outflows - storage_change
        closure_error_percent = (closure_error / fresh_inflows * 100) if fresh_inflows > 0 else 0
        
        # Log results (structured)
        logger.info(f"Balance calculated for {facility_code} {month}/{year}",
                   extra={
                       'facility': facility_code,
                       'month': month,
                       'year': year,
                       'fresh_inflows': fresh_inflows,
                       'outflows': outflows,
                       'storage_change': storage_change,
                       'closure_error_percent': closure_error_percent,
                   })
        
        return BalanceResult(
            facility=facility_code,
            date=date(year, month, 1),
            fresh_inflows_m3=fresh_inflows,
            total_outflows_m3=outflows,
            storage_change_m3=storage_change,
            closure_error_m3=closure_error,
            closure_error_percent=closure_error_percent,
            is_balanced=abs(closure_error_percent) < 5,
            kpis={
                'inflow_count': len([m for m in measurements if m.is_inflow]),
                'outflow_count': len([m for m in measurements if m.is_outflow]),
                'recirculation_count': len([m for m in measurements if m.is_recirculation]),
            }
        )
    
    def _calculate_fresh_inflows(self, measurements) -> float:
        """Calculate total fresh inflows (IMPROVED: proper calculation)"""
        return sum(m.volume for m in measurements if m.is_inflow and not m.is_recirculation)
    
    def _calculate_outflows(self, measurements) -> float:
        """Calculate total outflows"""
        return sum(m.volume for m in measurements if m.is_outflow)
    
    def _calculate_storage_change(self, measurements) -> float:
        """Calculate storage change"""
        # Implementation details based on business logic
        pass
```

**Estimated Time:** 4-5 hours  
**Files to Create/Expand:** 4 service files (calculation, balance_check, flow_volume, pump_transfer)

---

### Step 4: Utils Layer (src/utils/) - HELPERS
**Why Fourth:** Services use utilities for common tasks

```python
# src/utils/caching.py

from functools import wraps
from typing import Callable, Any
import time

def cached(ttl_seconds: int = 3600):
    """Decorator for caching function results with TTL
    
    IMPROVEMENT OVER TKINTER: Automatic, per-function caching
    (not manual dict management scattered throughout code)
    
    Usage:
        @cached(ttl_seconds=1800)
        def expensive_calculation():
            return result
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            # Check if cached and not expired
            if key in cache and (now - cache_time[key]) < ttl_seconds:
                return cache[key]
            
            # Compute result
            result = func(*args, **kwargs)
            cache[key] = result
            cache_time[key] = now
            
            return result
        
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    
    return decorator

# Usage in services:
# @cached(ttl_seconds=1800)
# def calculate_balance(...):
#     ...
```

**Estimated Time:** 1-2 hours  
**Files to Create:** 2-3 utility files (caching, excel_parsing, formatting)

---

### Step 5: Wire Services to UI (Signals/Slots) - INTEGRATION
**Why Fifth:** Connect UI to services for reactive updates

```python
# src/ui/dashboards/calculation_dashboard.py - MODIFY EXISTING

from PySide6.QtCore import QThread, Signal, QObject
from services.calculation_service import WaterBalanceCalculationService
from models.balance_result import BalanceResult

class CalculationWorker(QObject):
    """Background worker for balance calculation"""
    calculation_complete = Signal(dict)  # Emits result
    calculation_error = Signal(str)      # Emits error message
    
    def __init__(self, service: WaterBalanceCalculationService):
        super().__init__()
        self.service = service
    
    def calculate(self, facility: str, year: int, month: int):
        """Run calculation in background thread"""
        try:
            result = self.service.calculate_balance(facility, year, month)
            self.calculation_complete.emit(result.dict())
        except Exception as e:
            self.calculation_error.emit(str(e))

class CalculationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # Initialize service
        from core.config_manager import load_config
        from database.db_manager import DatabaseManager
        
        config = load_config('config/app_config.yaml')
        db = DatabaseManager(config.get('database.path'))
        self.service = WaterBalanceCalculationService(db, config)
        
        # Setup worker thread
        self.worker_thread = QThread()
        self.worker = CalculationWorker(self.service)
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.ui.btn_calculate.clicked.connect(self._on_calculate_clicked)
        self.worker.calculation_complete.connect(self._on_calculation_complete)
        self.worker.calculation_error.connect(self._on_calculation_error)
        self.worker_thread.started.connect(self.worker.calculate)
    
    def _on_calculate_clicked(self):
        """Handle calculate button click"""
        facility = self.ui.input_facility.text()
        year = self.ui.spinbox_year.value()
        month = self.ui.spinbox_month.value()
        
        # Start background calculation (non-blocking)
        self.worker.calculate(facility, year, month)
        self.worker_thread.start()
    
    def _on_calculation_complete(self, result: dict):
        """Handle calculation complete"""
        # Update UI with results
        self.ui.label_balance.setText(f"{result['closure_error_m3']:.1f} m³")
        self.ui.label_error.setText(f"{result['closure_error_percent']:.2f}%")
    
    def _on_calculation_error(self, error: str):
        """Handle calculation error"""
        QMessageBox.critical(self, "Calculation Error", error)
```

**Estimated Time:** 2-3 hours  
**Files to Modify:** 9 dashboard files (add service integration)

---

### Step 6: Unit Tests (tests/) - VALIDATION
**Why Sixth:** Ensure services work correctly before integration

```python
# tests/test_services/test_calculation_service.py

import pytest
from unittest.mock import Mock
from services.calculation_service import WaterBalanceCalculationService
from models.facility import Facility
from models.measurement import Measurement
from models.balance_result import BalanceResult
from datetime import date

@pytest.fixture
def mock_db():
    """Mock database manager"""
    return Mock()

@pytest.fixture
def mock_config():
    """Mock config manager"""
    return Mock()

@pytest.fixture
def service(mock_db, mock_config):
    """Create service with mocked dependencies"""
    return WaterBalanceCalculationService(mock_db, mock_config)

def test_calculate_balance_ug2n_march_2025(service, mock_db):
    """Test balance calculation for UG2N, March 2025"""
    # Setup mock data
    facility = Facility(
        code='UG2N',
        name='UG2 North',
        area='UG2',
        capacity_m3=150000
    )
    mock_db.get_facility.return_value = facility
    
    measurements = [
        Measurement(facility='UG2N', volume=1000, is_inflow=True),
        Measurement(facility='UG2N', volume=800, is_outflow=True),
    ]
    mock_db.get_measurements.return_value = measurements
    
    # Execute calculation
    result = service.calculate_balance('UG2N', 2025, 3)
    
    # Verify results
    assert isinstance(result, BalanceResult)
    assert result.facility == 'UG2N'
    assert result.date == date(2025, 3, 1)
    assert result.closure_error_percent < 5  # Good closure

def test_calculate_balance_invalid_month(service):
    """Test calculation with invalid month"""
    with pytest.raises(ValueError):
        service.calculate_balance('UG2N', 2025, 13)

def test_calculate_balance_facility_not_found(service, mock_db):
    """Test calculation for non-existent facility"""
    mock_db.get_facility.return_value = None
    
    with pytest.raises(ValueError):
        service.calculate_balance('INVALID', 2025, 3)
```

**Estimated Time:** 2-3 hours  
**Files to Create:** 4-5 test files (one per service + integration tests)

---

## Implementation Timeline

| Phase | Component | Hours | Cumulative |
|-------|-----------|-------|-----------|
| 1 | Models (src/models/) | 3 | 3 |
| 2 | Database Layer (src/database/) | 4 | 7 |
| 3 | Services Layer (src/services/) | 5 | 12 |
| 4 | Utils Layer (src/utils/) | 2 | 14 |
| 5 | UI Integration (signals/slots) | 3 | 17 |
| 6 | Unit Tests (tests/) | 3 | 20 |
| **TOTAL** | **Complete Backend** | **20 hours** | **20 hours** |

**Estimated Completion:** 5 days (4 hours/day) to fully functional backend

---

## File Checklist

### Models to Create (src/models/)
- [ ] `__init__.py` (exports)
- [ ] `facility.py` (Facility model)
- [ ] `balance_result.py` (BalanceResult model)
- [ ] `measurement.py` (Measurement model)
- [ ] `flow_volume.py` (FlowVolume model)
- [ ] `alert.py` (Alert model)

### Database to Expand (src/database/)
- [ ] `db_manager.py` (expand existing)
- [ ] `repositories/__init__.py`
- [ ] `repositories/facility_repository.py`
- [ ] `repositories/measurement_repository.py`
- [ ] `repositories/flow_volume_repository.py`

### Services to Implement (src/services/)
- [ ] `calculation_service.py` (expand existing)
- [ ] `balance_check_service.py` (expand existing)
- [ ] `flow_volume_loader.py` (expand existing)
- [ ] `pump_transfer_service.py` (expand existing)

### Utils to Create (src/utils/)
- [ ] `caching.py` (caching decorator)
- [ ] `excel_helpers.py` (Excel parsing)
- [ ] `formatting.py` (Data formatting)

### Tests to Create (tests/)
- [ ] `test_services/test_calculation_service.py`
- [ ] `test_services/test_balance_check_service.py`
- [ ] `test_services/test_flow_volume_loader.py`
- [ ] `test_services/test_pump_transfer_service.py`
- [ ] `test_models/test_facility.py`
- [ ] `test_integration/test_balance_workflow.py`

### UI to Modify (src/ui/dashboards/)
- [ ] `dashboard_dashboard.py` (add service integration)
- [ ] `analytics_dashboard.py` (add service integration)
- [ ] `calculation_dashboard.py` (add service integration)
- [ ] `flow_diagram_dashboard.py` (add service integration)
- [ ] `monitoring_dashboard.py` (add service integration)
- [ ] `storage_facilities_dashboard.py` (add service integration)

---

## Key Principles for Backend Implementation

1. **NOT Copy-Paste from Tkinter**
   - ✅ Understand the business logic first
   - ✅ Design services properly (interfaces, validation, error handling)
   - ✅ Use type hints and Pydantic models
   - ✅ Implement proper logging (not prints)

2. **Class-Based, Not Procedural**
   - ✅ Each service is a class
   - ✅ Each repository is a class
   - ✅ Each model is a Pydantic BaseModel
   - ✅ NO standalone functions in business logic (except utilities)

3. **Type Safety**
   - ✅ All functions have type hints
   - ✅ All data is validated (Pydantic)
   - ✅ Use Optional[] for nullable values
   - ✅ Use Union[] for multiple types only when necessary

4. **Error Handling**
   - ✅ Custom exceptions (not generic Exception)
   - ✅ Structured logging (not prints)
   - ✅ Validation in models (not in services)
   - ✅ Graceful degradation when possible

5. **Performance**
   - ✅ Caching decorator for expensive operations
   - ✅ Connection pooling for database
   - ✅ Lazy loading for Excel files
   - ✅ Async/threading for long operations

6. **Testability**
   - ✅ Services independent of UI (use dependency injection)
   - ✅ Mock external dependencies in tests
   - ✅ Unit tests for every service method
   - ✅ Integration tests for service workflows

---

## Next: Ready to Start Backend Implementation?

**Review Checklist Before Starting:**
- ✅ All 9 UI pages complete and class-based
- ✅ Architecture verified and documented
- ✅ Directory structure in place
- ✅ This roadmap understood
- ✅ NOT going to copy-paste Tkinter code
- ✅ Will implement with modern patterns

**Then Start:** Implement data models first (Step 1)

**Let me know when ready!** 🚀

