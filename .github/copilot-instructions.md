# Water Balance Application - AI Agent Instructions

## Project Overview
Mine water balance management system built with Python/Tkinter. Calculates daily water flows across 8 mine areas (Merensky North/South, UG2 North/Plant, TSF, Stockpile) tracking inflows, outflows, recirculation, and storage volumes. Uses SQLite for persistence and Excel templates for time-series data.

## Architecture & Data Flow

### Core Components
- **src/main.py** - Entry point with `WaterBalanceApp` controller
- **src/utils/water_balance_calculator.py** (2000+ lines) - Core calculation engine implementing TRP formulas
- **src/database/db_manager.py** - Database operations with caching and connection pooling
- **src/database/schema.py** - SQLite schema for 15+ tables (structures, measurements, calculations, etc.)
- **src/ui/** - Tkinter UI modules (dashboard, calculations, monitoring, flow diagrams, settings)

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

### 1. Singleton Pattern (Heavy Usage)
**Never** instantiate directly. Always use module-level getters:
```python
from utils.template_data_parser import get_template_parser  # NOT TemplateDataParser()
from utils.balance_check_engine import get_balance_check_engine
from database.db_manager import db  # Global instance
```

### 2. Async Loading (Fast Startup Feature)
Controlled by `config/app_config.yaml`:
```yaml
features:
  fast_startup: true  # Async DB load (3s UI display)
```
Implementation: `src/utils/async_loader.py` - Background thread loads DB while UI shows loading indicator.
**Important**: Always handle `db_loaded` flag in UI interactions.

### 3. Database Operations
- Use `db.execute_query()` for SELECT (returns `List[Dict]`)
- Use `db.execute_update()` for INSERT/UPDATE/DELETE
- Preload data with `db.get_all_sources(force_reload=False)` and `db.get_all_facilities()` (cached)
- **Never** write directly to flow/balance data from templates - templates are read-only data sources

### 4. Configuration Management
Single source: `config/app_config.yaml` accessed via:
```python
from utils.config_manager import config
value = config.get('path.to.key', default_value)
```

### 5. Import Path Pattern
**Every** module uses path insertion for imports:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add src/ to path
```
This pattern is required in all files under `src/` to enable relative imports.

### 6. Error Handling Pattern
Use centralized error handler (singleton):
```python
from utils.error_handler import error_handler, ErrorCategory, ErrorSeverity
tech_msg, user_msg, severity = error_handler.handle(
    exception, context="Operation name", category=ErrorCategory.DATABASE
)
# Returns: (technical message for logs, user-friendly message, severity level)
```

### 7. Logging Pattern
Use singleton logger with performance timing:
```python
from utils.app_logger import logger
logger.info("Operation started")
logger.performance("Query execution", elapsed_ms)  # For timing
logger.error("Error occurred", exc_info=True)  # With stack trace
```

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

### Testing
- `pytest` for unit tests (see `src/database/test_database.py`)
- Run calculations: `python src/main.py` → Calculations module
- Fast startup test: Verify 3-second UI load time

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

## Utility Singletons Reference
Quick reference for commonly used singletons:
```python
from database.db_manager import db                      # Database operations
from utils.app_logger import logger                     # Logging
from utils.error_handler import error_handler           # Error handling
from utils.template_data_parser import get_template_parser()
from utils.balance_check_engine import get_balance_check_engine()
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
