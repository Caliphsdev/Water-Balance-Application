# Water Balance Application - AI Agent Instructions

## Project Overview
Mine water balance management system built with Python/Tkinter. Calculates daily water flows across 8 mine areas (Merensky North/South, UG2 North/Plant, TSF, Stockpile) tracking inflows, outflows, recirculation, and storage volumes. Uses SQLite for persistence and Excel templates for time-series data. **Key architecture**: On-demand Excel loading via singletons, reactive UI with fast startup feature, modular calculations with balance checking.

## Architecture & Data Flow

### Core Components
- **src/main.py** — Entry point with `WaterBalanceApp` controller and fast startup orchestration
- **src/utils/water_balance_calculator.py** (2000+ lines) — Core calculation engine implementing TRP formulas with internal caching (`_balance_cache`, `_kpi_cache`, `_misc_cache`)
- **src/utils/flow_volume_loader.py** — On-demand Excel loader (singleton pattern) with dynamic path resolution for diagram flows
- **src/database/db_manager.py** — Database operations with caching and connection pooling (auto-creates DB at data/water_balance.db via schema.py if missing)
- **src/database/schema.py** — SQLite schema for 15+ tables (structures, measurements, calculations, etc.)
- **src/ui/main_window.py** — Module navigation controller and loading orchestration
- **src/ui/flow_diagram_dashboard.py** — Interactive flow diagram with JSON persistence, Excel mapping, and auto-color detection
- **src/ui/** — 25+ Tkinter UI modules organized by feature (calculations, dashboard, monitoring, settings, etc.)

### Data Sources & Templates
**Critical**: System uses `.txt` template files for balance checking:
- `INFLOW_CODES_TEMPLATE.txt` - 34 inflow entries across 8 areas
- `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` - 64 outflow entries
- `DAM_RECIRCULATION_TEMPLATE.txt` - 12 recirculation loops

Parser: `src/utils/template_data_parser.py` (singleton pattern `get_template_parser()`)
Engine: `src/utils/balance_check_engine.py` (singleton pattern `get_balance_check_engine()`)

### Database Tables (Key)
- `wb_structures` - Water sources, dams, plants (110+ entries)
- `wb_flow_connections` - Flow topology between structures
- `wb_calculations` - Stored calculation results
- `system_constants` - Configuration values (evaporation rates, plant ratios, etc.)

## Critical Development Patterns

### 1. Singleton Pattern (Heavy Usage) & Reset Mechanism
**Never** instantiate directly. Always use module-level getters:
```python
from utils.template_data_parser import get_template_parser  # NOT TemplateDataParser()
from utils.balance_check_engine import get_balance_check_engine
from utils.flow_volume_loader import get_flow_volume_loader  # Excel loader
from database.db_manager import db  # Global instance
from utils.config_manager import config
```

**Important**: Some singletons (like `flow_volume_loader`) have **reset functions** to force config reload:
```python
from utils.flow_volume_loader import reset_flow_volume_loader
reset_flow_volume_loader()  # Call after Settings path change to clear cached instance
```
This pattern is used when Settings updates affect singleton behavior. Check if a reset function exists before creating workarounds.

### 2. Async Loading (Fast Startup Feature)
Controlled by `config/app_config.yaml`:
```yaml
features:
  fast_startup: true  # Async DB load (3s UI display)
```
Implementation: `src/utils/async_loader.py` - Background thread loads DB while UI shows loading indicator.
**Important**: Always handle `db_loaded` flag in UI interactions.

### 3. Excel Loading (On-Demand Pattern)
The flow diagram loads Excel data on-demand, NOT automatically. **Path resolution is critical**:

```python
from utils.flow_volume_loader import get_flow_volume_loader
loader = get_flow_volume_loader()

# In flow_diagram_dashboard.py, before loading from Excel:
self.flow_loader = get_flow_volume_loader()  # Get fresh instance (picks up Settings changes)
self.flow_loader.clear_cache()  # Clear cached sheets so edits are visible
volumes = loader.get_flow_volumes_for_month(area_code, year, month)
```

**Path Priority** (in `flow_volume_loader.py`):
1. `data_sources.timeseries_excel_path` (user-configured)
2. `data_sources.template_excel_path` (fallback)
3. Default hardcoded path (last resort)

**When Settings changes Excel path**:
1. Settings calls `config.set()` to update both paths
2. Settings calls `reset_flow_volume_loader()` to clear singleton
3. Next `get_flow_volume_loader()` creates fresh instance with new path
4. Flow diagram re-gets loader before loading (see line ~2505 in `flow_diagram_dashboard.py`)

**Excel Format Support**: Loader handles both Date-based and Year/Month-based column formats automatically.

### 5. Configuration Management
Single source: `config/app_config.yaml` accessed via:
```python
from utils.config_manager import config
value = config.get('path.to.key', default_value)
config.set('path.to.key', new_value)  # Updates and persists to YAML
config.load_config()  # Force reload from disk (used by singletons after Settings changes)
```
DB path: `database.path` (defaults to data/water_balance.db). Feature flags live under `features.*`.

**Important**: After changing config (e.g., in Settings), some singletons won't see the change until reset. Call `config.load_config()` and the corresponding reset function if needed.

### 6. Import Path Pattern
**Every** module uses path insertion for imports:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add src/ to path
```
This pattern is required in all files under `src/` to enable relative imports.

### 7. Error Handling Pattern
Use centralized error handler (singleton):
```python
from utils.error_handler import error_handler, ErrorCategory, ErrorSeverity
tech_msg, user_msg, severity = error_handler.handle(
    exception, context="Operation name", category=ErrorCategory.DATABASE
)
# Returns: (technical message for logs, user-friendly message, severity level)
```

### 8. Logging Pattern
Use singleton logger with performance timing:
```python
from utils.app_logger import logger
logger.info("Operation started")
logger.performance("Query execution", elapsed_ms)  # For timing
logger.error("Error occurred", exc_info=True)  # With stack trace
```

## Running & Testing
- Launch app: `python src/main.py` (fast startup honored); fallback launcher: `python src/main_launcher.py`; experimental: `python src/main_optimized.py`.
- Unit tests: `pytest src/database/test_database.py` (SQLite connectivity + schema checks).
- DB init/reset: `python -c "from database.schema import DatabaseSchema; DatabaseSchema().create_database()"` (writes to data/water_balance.db).
- Debug fast-startup: toggle `features.fast_startup` in `config/app_config.yaml`; blocking load uses `load_database_blocking`.

## Module-Specific Guidance

### Calculations Module (`src/ui/calculations.py`)
6-tab interface:
1. Balance Check Summary - Overall equation
2. Area Balance Breakdown - Per-area tabs (8 areas)
3. Summary (legacy)
4. Inflows (legacy)
5. Outflows (legacy)
6. Storage (legacy)

**Workflow**: User selects month → clicks "Calculate Balance" → `_calculate_balance()` calls both `WaterBalanceCalculator.calculate_water_balance()` and `BalanceCheckEngine.calculate_balance()`

### Flow Diagram (`src/ui/flow_diagram_dashboard.py`)
Interactive canvas with:
- Drag-and-drop components
- Flow connections with auto-color detection (blue=clean, red=wastewater, orange=underground return)
- Waypoints for curved routing (middle-click to add)
- JSON persistence in `data/diagrams/<area>_flow_diagram.json`
- **Key pattern**: Uses `excel_mapping` on edges to link flows to Excel columns (21 mapped, 131 unmapped in UG2N)
- **Loading workflow**: Click "Load from Excel" → `_load_from_excel()` → gets fresh loader instance → clears cache → updates edges → redraws

### Testing
- `pytest` for unit tests (see `src/database/test_database.py`)
- Run calculations: `python src/main.py` → Calculations module
- Fast startup test: Verify 3-second UI load time

### Data Inputs/Outputs
- Templates: root `INFLOW_CODES_TEMPLATE.txt`, `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt`, `DAM_RECIRCULATION_TEMPLATE.txt` (read-only, parsed by template_data_parser).
- Excel time-series: `utils.excel_timeseries` / `excel_timeseries_extended` pull from `test_templates/` paths in config; use lazy loader in `lazy_excel_loader.py`.
- Diagrams: JSON persisted per area at `data/diagrams/<area>_flow_diagram.json`.
- Database: SQLite at `data/water_balance.db`; caches for sources/facilities in db_manager, balance/KPI caches in water_balance_calculator.

## Common Tasks

### Adding New Calculation
1. Add constant to `system_constants` table via `db_manager._ensure_all_constants()`
2. Implement logic in `WaterBalanceCalculator` class methods
3. Update UI in relevant module (`calculations.py`, `dashboard.py`, etc.)
4. Test with real data from Excel templates

### Modifying Flow Topology
1. Update `wb_flow_connections` table (from_structure_id, to_structure_id, flow_type)
2. Regenerate templates if needed (scripts in root: `check_*.py`, `add_*.py`)
3. Update diagrams via Flow Diagram Dashboard UI

### Schema Changes
1. Add migration in `src/database/db_manager.py` → `_ensure_*` methods
2. Run schema creation: `python -c "from database.schema import DatabaseSchema; DatabaseSchema().create_database()"`
3. Verify with `check_db_schema.py` scripts

## Performance Considerations
- **Caching**: `WaterBalanceCalculator` has `_balance_cache`, `_kpi_cache`, `_misc_cache` - check before DB hits
- **Logging**: Use `logger.performance()` for timing (see `utils/app_logger.py`)
- **UI**: Minimize DOM-like operations - batch Tkinter updates with `root.update_idletasks()`

## Key Files for Context
- [BALANCE_CHECK_README.md](../BALANCE_CHECK_README.md) - Balance check feature docs
- [FLOW_DIAGRAM_GUIDE.md](../FLOW_DIAGRAM_GUIDE.md) - Interactive diagram usage
- `.github/instructions/python.instructions.md` - Python style guide (PEP 8)
- `.github/instructions/performance-optimization.instructions.md` - Performance best practices

## Common Pitfalls
1. **Don't** create new instances of singleton classes
2. **Don't** modify template files programmatically - they're user-editable references
3. **Don't** assume DB is loaded immediately (check `app.db_loaded` flag)
4. **Don't** use blocking operations in UI thread (use `threading` or `async_loader`)
5. **Don't** forget `sys.path.insert(0, str(Path(__file__).parent.parent))` in new modules
6. **Always** call `config.set_current_user()` before DB operations requiring user context
7. **Always** use `error_handler.handle()` for exceptions - never bare try/except with print()
8. **Always** call `config.load_config()` in path resolvers after Settings changes (singletons won't pick up config changes automatically)
9. **Always** call the reset function (e.g., `reset_flow_volume_loader()`) when Settings changes paths that singletons depend on

## Singleton Reset Patterns

**When Settings changes configuration that affects singletons:**

1. Call `config.set()` to update YAML
2. Call the singleton's reset function to clear cached instance
3. Next access to singleton getter creates new instance with updated config

**Example (Settings path change):**
```python
# settings_revamped.py
config.set('data_sources.timeseries_excel_path', new_path)
from utils.flow_volume_loader import reset_flow_volume_loader
reset_flow_volume_loader()  # Force new instance on next access
```

**Example (Flow diagram after Settings change):**
```python
# flow_diagram_dashboard.py - before loading from Excel
self.flow_loader = get_flow_volume_loader()  # Gets NEW instance (reset cleared old one)
self.flow_loader.clear_cache()  # Clear any cached sheets
```

**Singletons with reset functions:**
- `flow_volume_loader` → `reset_flow_volume_loader()`
- `excel_timeseries_extended` → `ExcelTimeSeriesExtended._instance = None`

Check implementation for others.

## Utility Singletons Reference
Quick reference for commonly used singletons:
```python
from database.db_manager import db                      # Database operations
from utils.app_logger import logger                     # Logging
from utils.error_handler import error_handler           # Error handling
from utils.template_data_parser import get_template_parser()
from utils.balance_check_engine import get_balance_check_engine()
from utils.flow_volume_loader import get_flow_volume_loader()  # Excel loader for flow diagram
from utils.config_manager import config                 # Configuration
from utils.ui_notify import notifier                    # UI notifications
from utils.alert_manager import alert_manager           # Alert system
```

## Entry Points
- `src/main.py` - Standard launch
- `src/main_launcher.py` - Launcher with error handling
- `src/main_optimized.py` - Experimental optimized startup

## Dependencies
Core: `tkinter`, `ttkthemes`, `sqlite3`, `pandas`, `openpyxl`, `PyYAML`
Full list: [requirements.txt](../requirements.txt)
