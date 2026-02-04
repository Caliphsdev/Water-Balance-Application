# 📍 Tkinter Code Reference Map

**Purpose:** Shows exactly where each piece of Tkinter code is located and where it should go in PySide6

**Source:** c:\PROJECTS\Water-Balance-Application  
**Target:** d:\Projects\dashboard_waterbalance

---

## Business Logic to Migrate (With Improvements)

### 1. Core Water Balance Calculation

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\water_balance_calculator.py`

**What it does:**
- Primary calculation engine
- Reads meter data from Excel
- Applies facility constants
- Computes balances
- Caches results

**Where it goes:** `src/services/calculation_service.py`

**How to improve:**
- Add type hints to all functions
- Create BalanceResult Pydantic model
- Add specific error exceptions
- Document cache key format
- Document cache invalidation triggers
- Add comprehensive docstrings
- Extract pure calculation logic

**Key functions to migrate:**
```python
def calculate_water_balance(area: str, month: int, year: int) -> BalanceResult
def _get_inflows(...)
def _get_outflows(...)
def _calculate_balance(...)
def clear_cache()
```

**Tests needed:**
- `tests/test_services/test_calculation_service.py`
- Test with known data
- Verify results match Tkinter output
- Test cache behavior

---

### 2. Balance Validation Engine

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\balance_check_engine.py`

**What it does:**
- Validates balance (closure error < 5%)
- Calculates per-area metrics
- Checks data quality

**Where it goes:** `src/services/balance_check_service.py`

**How to improve:**
- Add type hints
- Use Pydantic for input/output
- Add specific validation exceptions
- Document validation rules
- Add docstrings

**Key functions to migrate:**
```python
def calculate_balance(facility: str, date: datetime) -> BalanceMetrics
def validate_closure_error(error_percent: float) -> bool
def get_per_area_breakdown(...) -> Dict[str, float]
```

---

### 3. Pump Transfer Engine

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\pump_transfer_engine.py`

**What it does:**
- Automatic water redistribution
- Facility-to-facility transfers
- Triggered by storage level thresholds

**Where it goes:** `src/services/pump_transfer_service.py`

**How to improve:**
- Add type hints
- Create PumpTransfer Pydantic model
- Add transfer logging
- Document transfer strategy
- Add comprehensive docstrings

**Key functions to migrate:**
```python
def calculate_pump_transfers(date: datetime) -> List[PumpTransfer]
def should_transfer(facility: Facility) -> bool
def get_transfer_volume(facility: Facility) -> float
def get_destination_facility(...) -> Optional[Facility]
```

---

### 4. Flow Volume Loader

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\flow_volume_loader.py`

**What it does:**
- Loads flow volumes from "Flow Diagram" Excel sheet
- Lazy loads per-month
- Caches results
- Used by flow diagram dashboard

**Where it goes:** `src/services/flow_volume_loader.py`

**How to improve:**
- Add type hints
- Create FlowVolume Pydantic model
- Add error handling for missing data
- Document cache strategy
- Add comprehensive docstrings
- Separate Excel reading from logic

**Key functions to migrate:**
```python
def get_flow_volume(area: str, month: int, component: str) -> float
def load_month_volumes(area: str, month: int) -> Dict[str, float]
def clear_cache()
def validate_flow_data(...) -> bool
```

---

### 5. Excel Data Loaders (Consolidate)

**Source:** Multiple files:
- `c:\PROJECTS\Water-Balance-Application\src\utils\flow_volume_loader.py`
- `c:\PROJECTS\Water-Balance-Application\src\utils\meter_readings_loader.py` (if exists)
- Other Excel loaders

**What they do:**
- Load meter readings from "Meter Readings" Excel sheet
- Load flow data from "Flow Diagram" Excel sheet
- Parse Excel columns
- Handle missing data

**Where it goes:** `src/services/excel_service.py` (consolidated)

**How to improve:**
- Separate into logical methods:
  - `load_meter_readings(month, year)` - From "Meter Readings" sheet
  - `load_flow_volumes(area, month)` - From "Flow Diagram" sheet
- Add type hints
- Create ExcelDataSet Pydantic model
- Add validation
- Clear cache invalidation strategy
- Add comprehensive docstrings

**Key functions to consolidate:**
```python
def load_meter_readings(month: int, year: int) -> Dict[str, MeterReading]
def load_flow_volumes(area: str, month: int) -> Dict[str, float]
def validate_excel_file(file_path: str) -> bool
def clear_all_caches()
```

---

### 6. Template Parser

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\template_data_parser.py`

**What it does:**
- Reads template .txt files (inflow, outflow, recirculation codes)
- Parses into structured data
- Cached at startup

**Where it goes:** `src/services/excel_service.py` (consolidate with Excel loaders)

**How to improve:**
- Add type hints
- Create Template Pydantic model
- Add error handling
- Document template format
- Add comprehensive docstrings

**Key functions to migrate:**
```python
def parse_inflow_template() -> Dict[str, str]
def parse_outflow_template() -> Dict[str, str]
def parse_recirculation_template() -> Dict[str, str]
def validate_template_format(...) -> bool
```

---

## Database Layer to Migrate (With Minor Improvements)

### 7. Database Schema

**Source:** `c:\PROJECTS\Water-Balance-Application\src\database\schema.py`

**What it does:**
- Defines SQLite tables
- Mine areas, water sources, storage facilities
- Measurements, calculations, flow volumes
- 20+ tables

**Where it goes:** `src/database/schema.py`

**How to improve:**
- Add SCHEMA_VERSION at top
- Organize schemas by version
- Add comments explaining each table
- Add migration functions
- Keep as-is if well-structured

**Key changes:**
```python
# Before (if no versioning):
CREATE TABLE facilities (...)

# After (versioning for migrations):
SCHEMA_VERSION = 1
SCHEMAS = {
    1: """
        CREATE TABLE facilities (...)
        CREATE TABLE measurements (...)
        ...
    """
}
```

---

### 8. Database Manager

**Source:** `c:\PROJECTS\Water-Balance-Application\src\database\db_manager.py`

**What it does:**
- Connection pooling
- CRUD operations
- Transaction management

**Where it goes:** `src/database/db_manager.py`

**How to improve:**
- Add type hints
- Extract CRUD into repositories
- Add connection retry logic
- Keep transaction handling
- Add comprehensive docstrings

**Key functions to keep:**
```python
def get_connection()
def execute_query(query: str, params: Optional[Tuple]) -> Cursor
def fetch_one(...) -> Optional[Dict]
def fetch_all(...) -> List[Dict]
def execute_many(...)
```

---

### 9. Create Repositories (NEW)

**Create:** `src/database/repositories/`

These are NEW - extract CRUD from db_manager.py

**Files to create:**

```python
# repository/facility_repository.py
class FacilityRepository:
    def get_facility(code: str) -> Facility
    def list_facilities() -> List[Facility]
    def create_facility(facility: Facility) -> int
    def update_facility(facility: Facility) -> bool

# repository/measurement_repository.py
class MeasurementRepository:
    def get_measurements(facility: str, month: int, year: int) -> List[Measurement]
    def create_measurement(measurement: Measurement) -> int
    def update_measurement(measurement: Measurement) -> bool

# repository/balance_repository.py
class BalanceRepository:
    def save_balance_result(result: BalanceResult) -> int
    def get_balance_result(facility: str, date: datetime) -> Optional[BalanceResult]
    def list_balance_results(facility: str) -> List[BalanceResult]
    def get_latest_balance(facility: str) -> Optional[BalanceResult]

# repository/flow_volume_repository.py
class FlowVolumeRepository:
    def save_flow_volume(volume: FlowVolume) -> int
    def get_flow_volumes(area: str, month: int) -> Dict[str, float]
    def list_flow_volumes(area: str) -> List[FlowVolume]
```

---

## Infrastructure to Migrate (No Changes Needed)

### 10. Configuration Manager

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\config_manager.py`

**What it does:**
- Loads YAML config
- Manages app settings
- Feature flags

**Where it goes:** `src/core/config_manager.py`

**How to improve:** ✅ No changes - excellent as-is

**Keep as:**
```python
def get(key: str)
def set(key: str, value: Any)
def reload_config()
```

---

### 11. Application Logger

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\app_logger.py`

**What it does:**
- Structured logging
- File and console output
- Performance logging

**Where it goes:** `src/core/app_logger.py`

**How to improve:** ✅ No changes - excellent as-is

**Keep as:**
```python
def info(msg: str)
def error(msg: str, exc_info: bool = False)
def warning(msg: str)
def debug(msg: str)
def performance(label: str)
```

---

## UI to Rewrite (Don't Migrate - Pure PySide6)

### 12. Calculation Dashboard

**Source:** `c:\PROJECTS\Water-Balance-Application\src\ui\calculations.py`

**What it does:**
- Displays balance results
- Shows area breakdown
- Shows legacy summary

**Where it goes:** `src/ui/dashboards/calculations_page.py` ✅ Already exists

**What to do:**
- ✅ DON'T copy Tkinter UI code
- ✅ Already rewritten in PySide6 properly
- ✅ Just wire to calculation_service
- ✅ Update to call services instead of calculating directly

**Changes needed:**
```python
# Before (Tkinter - mixed concerns):
def calculate_balance(self):
    balance = calculate_water_balance(...)  # Direct call
    self.display_results(balance)

# After (PySide6 - separated concerns):
def __init__(self):
    self.calc_service = CalculationService()

def calculate_balance(self):
    try:
        balance = self.calc_service.calculate_balance(facility, month, year)
        self.display_results(balance)
    except ValueError as e:
        self.show_error_dialog(str(e))
```

---

### 13. Flow Diagram Dashboard

**Source:** `c:\PROJECTS\Water-Balance-Application\src\ui\flow_diagram_dashboard.py`

**What it does:**
- Displays flow diagram
- Updates volumes from Excel
- Shows KPIs

**Where it goes:** `src/ui/dashboards/flow_diagram_page.py` ✅ Already exists

**What to do:**
- ✅ DON'T copy Tkinter rendering code
- ✅ Already rewritten in PySide6 with QGraphicsScene
- ✅ Just wire to flow_volume_loader
- ✅ Update to call services instead of reading Excel directly

---

## Optional Future Components (Phase 2B)

### 14. Licensing System

**Source:** `c:\PROJECTS\Water-Balance-Application\src\licensing\license_manager.py`

**What it does:**
- License validation
- Hardware binding
- Online/offline checks

**Where it goes:** `src/services/license_service.py` (Phase 2B)

**When:** Only if implementing Phase 2B (commercial features)

**Reference:** ADMIN_OPERATIONS.md + ARCHITECTURE.md in DOCUMENTATION folder

---

### 15. Excel Mapping Registry

**Source:** `c:\PROJECTS\Water-Balance-Application\src\utils\excel_mapping_registry.py`

**What it does:**
- Maps logical flow IDs to Excel columns
- Persists to JSON
- Enables component renaming

**Where it goes:** Can integrate into `src/services/excel_service.py`

**When:** Consider for Phase 2B (component rename system)

**Status:** Optional enhancement

---

## Summary: What to Move Where

### Copy As-Is (Minor improvements):
```
Tkinter                                  →  PySide6
src/utils/config_manager.py              →  src/core/config_manager.py
src/utils/app_logger.py                  →  src/core/app_logger.py
src/database/schema.py                   →  src/database/schema.py
```

### Refactor with Improvements:
```
Tkinter                                  →  PySide6 (Improve!)
src/utils/water_balance_calculator.py    →  src/services/calculation_service.py
src/utils/balance_check_engine.py        →  src/services/balance_check_service.py
src/utils/pump_transfer_engine.py        →  src/services/pump_transfer_service.py
src/utils/flow_volume_loader.py          →  src/services/flow_volume_loader.py
src/utils/*_loader.py (multiple)         →  src/services/excel_service.py
src/database/db_manager.py               →  src/database/db_manager.py (add repos)
```

### Create New (Data models):
```
NEW (from analysis)
→  src/models/facility.py
→  src/models/balance_result.py
→  src/models/measurement.py
→  src/models/flow_volume.py
→  src/models/pump_transfer.py
```

### Create New (Utilities):
```
NEW (helpers)
→  src/utils/caching.py
→  src/utils/validators.py
→  src/utils/formatters.py
→  src/utils/error_handler.py
```

### Rewrite in PySide6 (Don't migrate):
```
Tkinter UI (don't use)          ✅ Already rewritten
src/ui/calculations.py          →  src/ui/dashboards/calculations_page.py
src/ui/flow_diagram_dashboard.py→  src/ui/dashboards/flow_diagram_page.py
src/ui/main_window.py           →  src/ui/main_window.py (already done)
```

### Skip for Now:
```
Licensing system (Phase 2B when needed)
Auto-update system (Phase 2B when needed)
Admin operations (Phase 2B when needed)
```

---

## Next Steps

1. **Review this map** - Understand what goes where
2. **Review QUICK_ACTION_PLAN.md** - 5-day implementation schedule
3. **Review INTEGRATION_ANALYSIS_AND_RECOMMENDATIONS.md** - Full analysis
4. **Open Tkinter code** - Reference while migrating
5. **Start Day 1** - Create Pydantic models in src/models/

---

## File Locations (Quick Ref)

**Tkinter source:**
```
c:\PROJECTS\Water-Balance-Application\
├── src\
│   ├── utils\
│   │   ├── water_balance_calculator.py
│   │   ├── balance_check_engine.py
│   │   ├── pump_transfer_engine.py
│   │   ├── flow_volume_loader.py
│   │   ├── config_manager.py
│   │   ├── app_logger.py
│   │   ├── template_data_parser.py
│   │   ├── excel_mapping_registry.py
│   │   └── ... (other utilities)
│   ├── database\
│   │   ├── schema.py
│   │   └── db_manager.py
│   ├── ui\
│   │   ├── calculations.py
│   │   ├── flow_diagram_dashboard.py
│   │   └── main_window.py
│   └── licensing\
│       └── license_manager.py
└── config\
    └── app_config.yaml
```

**PySide6 target:**
```
d:\Projects\dashboard_waterbalance\
├── src\
│   ├── models\                ← NEW
│   │   ├── facility.py
│   │   ├── balance_result.py
│   │   ├── measurement.py
│   │   ├── flow_volume.py
│   │   └── pump_transfer.py
│   ├── services\              ← MOVED & IMPROVED
│   │   ├── calculation_service.py
│   │   ├── balance_check_service.py
│   │   ├── pump_transfer_service.py
│   │   ├── flow_volume_loader.py
│   │   └── excel_service.py
│   ├── database\              ← MOVED & IMPROVED
│   │   ├── schema.py
│   │   ├── db_manager.py
│   │   ├── migrations.py
│   │   └── repositories\
│   │       ├── facility_repository.py
│   │       ├── measurement_repository.py
│   │       ├── balance_repository.py
│   │       └── flow_volume_repository.py
│   ├── utils\                 ← NEW
│   │   ├── caching.py
│   │   ├── validators.py
│   │   ├── formatters.py
│   │   └── error_handler.py
│   ├── core\                  ← COPIED
│   │   ├── app_logger.py
│   │   └── config_manager.py
│   └── ui\
│       └── dashboards\        ← WIRED TO SERVICES
│           ├── calculations_page.py
│           ├── flow_diagram_page.py
│           └── ... (7 other pages)
├── tests\
│   ├── test_models\
│   ├── test_services\
│   └── test_ui\
└── config\
    └── app_config.yaml
```

---

**Ready to migrate? Start with Day 1: Create Pydantic models!** 🚀

