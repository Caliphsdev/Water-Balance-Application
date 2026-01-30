# Water Balance Application - AI Agent Instructions

## 🎯 What This Is
Python/Tkinter desktop app for mine water balance management across 8 mining areas. Professional data management system that:
- **Reads immutable templates** (txt files with inflow/outflow/recirculation codes)
- **Calculates water balances** using TRP formulas (fresh inflows = outflows + storage change + error)
- **Loads Excel operational data** (meter readings, flow measurements)
- **Persists to SQLite** database with 20+ tables
- **Renders dashboards** with interactive flow diagrams, KPI analytics, charts

**Key Distinction:** Single Excel file now (`Water_Balance_TimeSeries_Template.xlsx`) contains only Flow Diagram sheets (`Flows_*` per area). Historical meter readings come from `New Water Balance...xlsx` (configured as `legacy_excel_path`).

---

## 📚 Documentation Reference Structure

**docs/ is organized into subfolders by topic** - Use these for context:

```
docs/
├── 01-SETUP/        ← Installation and release workflows
├── 02-ARCHITECTURE/ ← System design patterns
├── 03-DATABASE/     ← Database documentation
├── 04-OPERATIONS/   ← Admin operations and troubleshooting
└── 05-REFERENCE/    ← Quick reference guides
```

**When you need context:** Check the appropriate folder in `docs/` first before asking for clarification.

---

## ❌ CRITICAL: No Summary .md Files (Unless Explicitly Requested)

**DEFAULT BEHAVIOR:**
- ❌ **DO NOT** create `.md` files after completing work
- ❌ **DO NOT** create progress/summary documentation
- ❌ **DO NOT** create "X is complete" docs automatically
- ✅ **ONLY** create `.md` files when user explicitly says "create a doc" or "document this"

**When User DOES Request Documentation:**
1. Check if content belongs in existing `docs/` subfolder
2. Update existing file instead of creating new one
3. Place in correct folder appropriately
4. Never create `.md` files in project root (only `README.md` allowed)

**Enforcement:** Root folder stays clean - no temporary `.md` files, no summary docs, no progress tracking.

---

## ⚡ CRITICAL: Code Comments on Every Edit (ENFORCED)

**ALWAYS write comprehensive comments when editing ANY Python code.**

**MANDATORY ENFORCEMENT:** See [**Comment Enforcement Rules**](instructions/COMMENT_ENFORCEMENT_RULES.md) for complete requirements.  
**QUICK REFERENCE:** See [**Comment Quick Reference**](COMMENT_QUICK_REFERENCE.md) for 1-page summary.

When you update, add, or fix code, you MUST:
1. ✅ **Every new function/method** gets a full docstring (explain purpose, args, returns, raises)
2. ✅ **Every class** gets a docstring (explain what it does, key methods, state)
3. ✅ **Complex logic** gets inline comments (explain WHY not WHAT)
4. ✅ **Cache/performance code** gets comments (explain strategy, TTL, invalidation)
5. ✅ **Data transformations** get comments (explain source, format, business logic)
6. ✅ **Database queries** get comments (explain sheet/table names, columns, joins)
7. ✅ **Excel operations** get comments (distinguish between Meter Readings vs Flow Diagram Excel)

**ENFORCEMENT:** Code without proper comments will be **REJECTED** on review. No exceptions.

**COMMIT MESSAGE RULE:** Include comment updates in commit message:
```
Fix balance calculation for OLDTSF

- Updated clear_cache() docstring to explain invalidation triggers
- Added inline comments to _validate_facility_flows() for data quality checks
- Clarified difference between METER_READINGS and FLOW_DIAGRAM Excel files
```

**If you update code WITHOUT adding/updating comments, the changes will be rejected by future maintainers.**

See **📝 Code Comments Mandate** section below for full details and examples.

## 🐍 Python Environment (MANDATORY)

Always use the single `.venv` environment in the project root:
- **Run app:** `.venv\Scripts\python src/main.py`
- **Install packages:** `.venv\Scripts\python -m pip install <package>`
- **Run tests:** `.venv\Scripts\python -m pytest tests/ -v`
- **Check coverage:** `.venv\Scripts\python -m pytest tests/ --cov=src`

The app automatically sets `WATERBALANCE_USER_DIR` environment variable on startup (before any imports) to ensure config/database/licenses use correct paths.

## 🧪 Testing Requirements (MANDATORY)

Every new function/class must have corresponding tests before or immediately after implementation.

**Quick Setup:**
- Test files: `tests/` (mirror `src/` structure)
- Framework: `pytest` (see `.venv\Scripts\python -m pytest --help`)
- Run: `.venv\Scripts\python -m pytest tests/ -v`
- Coverage target: **>80%** on core logic (utils, database, calculations)

**Test Categories:**
- **Unit Tests:** Individual functions (fast, isolated) → `tests/utils/test_calculator.py`
- **Integration Tests:** Multi-component workflows (DB, Excel, calculations)
- **UI Tests:** Dialog flows, state changes (use mocking to avoid graphics)

**Workflow:**
1. Write test (TDD preferred)
2. Implement feature
3. Verify: `.venv\Scripts\python -m pytest tests/ -v` (green tests required)
4. Commit with test code included

**Pro Tips:**
- Use `pytest fixtures` in `tests/conftest.py` for shared test data
- Use `pytest-mock` for mocking DB/Excel dependencies
- Use `pytest-cov` to identify untested code paths

## 🏗️ Architecture Map (Data Flow)

**Input → Calculation → Storage → UI**

1. **Bootstrap** [src/main.py](src/main.py)
   - Sets `WATERBALANCE_USER_DIR` env var BEFORE imports (enables correct DB/config paths)
   - Starts UI in background while async DB loads (fast startup feature)
   - Validates license before showing UI

2. **Templates** (immutable, read-only)
   - [src/utils/template_data_parser.py](src/utils/template_data_parser.py) reads 3 `.txt` files:
     - `INFLOW_CODES_TEMPLATE.txt`, `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt`, `DAM_RECIRCULATION_TEMPLATE.txt`
   - Parsed on startup, cached, never written back (data integrity)

3. **Calculations** (heavy logic, multi-tier caching)
   - [src/utils/water_balance_calculator.py](src/utils/water_balance_calculator.py) (PRIMARY ENGINE)
     - Reads meter data from **METER READINGS Excel** (`legacy_excel_path`)
     - Applies facility constants, computes balances
     - Caches results by date/facility (session-lifetime)
     - Calls `clear_cache()` when Excel updated
   - [src/utils/balance_check_engine.py](src/utils/balance_check_engine.py) (VALIDATOR)
     - Validates closure error < 5% (data quality indicator)
     - Per-area breakdown, templated metrics
   - [src/utils/pump_transfer_engine.py](src/utils/pump_transfer_engine.py) (AUTO-REDISTRIBUTION)
     - Facility-to-facility transfers when storage level ≥ 70%

4. **Excel Overlays** (flow volumes by area)
   - [src/utils/flow_volume_loader.py](src/utils/flow_volume_loader.py) loads from **FLOW DIAGRAM Excel** (`timeseries_excel_path`)
   - Lazy loads on-demand, cached per session
   - Used by flow diagram dashboard to populate edge volumes

5. **Persistence** (SQLite, 20+ tables)
   - [src/database/schema.py](src/database/schema.py) defines tables: mine_areas, water_sources, storage_facilities, measurements, etc.
   - [src/database/db_manager.py](src/database/db_manager.py) CRUD operations, connection pooling

6. **UI Rendering**
   - [src/ui/main_window.py](src/ui/main_window.py) (APPLICATION CONTAINER) - sidebar + content area
   - [src/ui/calculations.py](src/ui/calculations.py) - balance tabs (Summary, Area Breakdown, Legacy)
   - [src/ui/flow_diagram_dashboard.py](src/ui/flow_diagram_dashboard.py) - interactive flow diagrams with JSON at `data/diagrams/<area>_flow_diagram.json`
   - [src/ui/analytics_dashboard.py](src/ui/analytics_dashboard.py), [charts_dashboard.py](src/ui/charts_dashboard.py), etc.

**Key Pattern:** Every major component is a singleton accessed via `get_*()` getter. Never instantiate directly.

## 🔧 Core Patterns

### Singleton Pattern (MANDATORY)
Every major component is accessed via getter functions, never direct instantiation:
```python
# ✅ CORRECT
from utils.config_manager import config
from utils.app_logger import logger
from utils.error_handler import error_handler
from database.db_manager import db

# ❌ WRONG - Never do this:
# calculator = WaterBalanceCalculator()
# loader = FlowVolumeLoader()
```

**Key Getters:**
- `get_template_parser()`, `get_flow_volume_loader()`, `get_balance_check_engine()`, `get_balance_engine()`
- After config/path changes, call `reset_*()` (e.g., `reset_flow_volume_loader()`) then re-fetch

### Caching Strategy
Multi-tier with explicit invalidation:
- **WaterBalanceCalculator:** `_balance_cache`, `_kpi_cache`, `_misc_cache` (dict keyed by date/area)
- **DB Manager:** `use_cache=False` option; `invalidate_all_caches()` on schema edits
- **Excel Loaders:** Call `.clear_cache()` before Excel reload
- **Why:** Avoid re-parsing Excel/templates; speeds up repeated calculations 10x

### Configuration Pattern
```python
config.set(key, value)  # Auto-persists to YAML
config.get('features.fast_startup')  # Feature flags
```

### Import Shim (Required in Every File in `src/`)
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
# Then: from utils import ..., from database import ...
```

### Fast Startup
UI shows loading screen while [src/utils/async_loader.py](src/utils/async_loader.py) loads DB in background. UI checks `app.db_loaded` before DB-dependent actions.

## � Startup Lifecycle (Key to Understanding App State)

The app startup is **asynchronous and lifecycle-aware**. Understanding this prevents bugs:

1. **main() called** → Sets `WATERBALANCE_USER_DIR` env var (BEFORE any imports!)
2. **Tkinter window created** → Hidden, invisible, off-screen
3. **Loading screen shown** → User sees "Initializing..." message
4. **Database loads** (two modes):
   - **Fast startup enabled:** Async load in background thread (~3-5s) → `_on_database_loaded()` callback
   - **Fast startup disabled:** Blocking load on main thread (legacy)
5. **UI components initialized** → main_window, sidebar, content area
6. **Dashboard loaded** → After window is revealed (improves perceived startup speed)
7. **Window revealed** → Smooth fade transition from loading screen
8. **Mainloop starts** → Event loop running, UI responsive

**Key Gotcha:** Code can run before `db_loaded = True`. Always check:
```python
if hasattr(app, 'db_loaded') and app.db_loaded:
    # Safe to use database
    balance = calculator.calculate_balance(...)
```

**Async Callback Pattern:**
```python
# This gets called from worker thread when DB finishes
def _on_database_loaded(self, db_manager, error):
    # ALWAYS use root.after() to update UI on main thread!
    self.root.after(0, self._update_ui_after_db_load, db_manager, error)
```

## �📂 Data Inputs & Flows

**Immutable Templates** (read-only, never modify programmatically):
- `INFLOW_CODES_TEMPLATE.txt` (loaded/created by [src/utils/template_data_parser.py](src/utils/template_data_parser.py))
- `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` (output template)
- `DAM_RECIRCULATION_TEMPLATE.txt` (recirculation template)
- Created dynamically from config at [src/utils/create_templates.py](src/utils/create_templates.py)

**Excel Sheets** (configured in [config/app_config.yaml](config/app_config.yaml)):
- **Primary Template** (`data/Water_Balance_TimeSeries_Template.xlsx`): Master template for flow data
  - Used as `template_excel_path` and `timeseries_excel_path` (configured in `app_config.yaml`)
  - Contains "Flows_*" sheets for 8 areas
- **Meter Readings** (`data/New Water Balance 20250930 Oct.xlsx`): Historical meter readings
  - Used by `src/ui/calculations.py` for water balance calculations via `legacy_excel_path`

**JSON Diagrams:** Node IDs map to component names; edges link flows with values. Colors auto-detected: `#228B22` (clean), `#FF6347` (waste), `#696969` (underground).

## 🚀 Key Workflows

**Run app:** `.venv\Scripts\python src/main.py` (respects `features.fast_startup` config). See [🐍 Python Environment](#-python-environment-mandatory) section above.

**DB operations:**
- **Init/Reset:** `.venv\Scripts\python -c "from src.database.schema import DatabaseSchema; DatabaseSchema().create_database()"`
- **Backup:** `db.create_backup()` saves to `data/water_balance_dist.db.bak-<timestamp>`

**Balance calculation** (invoked from [src/ui/calculations.py](src/ui/calculations.py)):
1. `WaterBalanceCalculator.calculate_water_balance(area, month, year)` → dict with balance + KPIs
2. `BalanceCheckEngine.calculate_balance(...)` → metrics (inflows/outflows/error %)
3. `BalanceEngine` → advanced (fresh vs recycled inflows, pump transfers)
4. Results shown in tabs: Balance Summary, Area Breakdown, legacy Summary/Inflows/Outflows/Storage

**Flow diagram reload:** In dashboard `_load_from_excel()` → fetch fresh `FlowVolumeLoader` → `loader.clear_cache()` → redraw JSON edges with new volumes.

**Component rename workflow:**
- Component management handled via [src/utils/excel_mapping_registry.py](src/utils/excel_mapping_registry.py)
- Rename tracked in [data/excel_flow_links.json](data/excel_flow_links.json)
- Updates flow IDs without modifying Python logic (decoupled design)

## ⚡ Performance & UX

**Cache reuse:** Always check calculator caches before hitting DB. Avoid blocking UI with heavy Excel reads; use async_loader.

**Log hot paths:** Use `logger.performance('label')` to track slow calculations. Performance instructions: [.github/instructions/performance-optimization.instructions.md](../.github/instructions/performance-optimization.instructions.md).

## 🚰 Pump Transfer System

Automatic facility-to-facility water redistribution controlled by [src/utils/pump_transfer_engine.py](src/utils/pump_transfer_engine.py):

**Trigger & Thresholds:**
- Runs post-calculation when facility level reaches `pump_start_level` (default 70%)
- Applies 5% incremental transfers via `TRANSFER_INCREMENT`
- Uses facility `feeds_to` config (comma-separated destination codes in priority order)

**Configuration:**
- Each facility's `pump_start_level`, `feeds_to`, `active` status stored in DB
- Destination priority determined by order in `feeds_to`
- Destination must have capacity available (not above its own `pump_start_level`)

**Example Flow:**
```
Source (NDCD1): level=75% → triggers pump (≥70%)
  ↓ (5% transfer)
Destination 1 (PLANT_RWD): priority=1
  ↓ (if full, try next)
Destination 2 (AUXILIARY): priority=2
```

**Workflow:** In [src/ui/calculations.py](src/ui/calculations.py), after `WaterBalanceCalculator.calculate_water_balance()`, call `pump_transfer_engine.calculate_pump_transfers(date)` to populate transfer volumes in dashboard.

## 📊 Excel Mapping Registry

Persistent mapping layer in [src/utils/excel_mapping_registry.py](src/utils/excel_mapping_registry.py):

**Purpose:** Links logical flow IDs to Excel column locations across sheets, enabling safe refactoring without breaking calculations.

**Singleton Pattern:**
- Use `get_excel_mapping_registry()` singleton getter
- Call `reset_excel_mapping_registry()` after Excel file changes
- Data persisted to `data/excel_flow_links.json` (configurable via `data_sources.column_flow_links_path`)

**API:**
- `link_column_to_flow(flow_id, sheet_name, column_name)` → maps logical flow to physical column
- `get_column_for_flow(flow_id, sheet_name)` → retrieves mapped column (or None if unmapped)
- Thread-safe with RLock; auto-creates directories

**Example:** Flow "Plant_Consumption" → sheet "Flows_UG2North" → column "PlantConsumption_m3" (stored in JSON).

**Why:** Decouples Excel column renaming from code; enables component rename system to update only JSON + Excel without touching Python logic.

## 🔐 Licensing System

License activation, validation, and enforcement via [src/licensing/license_manager.py](src/licensing/license_manager.py) and [src/licensing/](src/licensing/).

**Startup Validation:**
- `LicenseManager.validate_startup()` called in [src/main.py](src/main.py) before UI renders
- Performs **online check** to Google Sheets (immediate revocation detection)
- Falls back to **offline grace** (default 7 days) if network fails
- Auto-recovers license if reinstalled on same hardware

**License Tiers & Check Intervals:**
- **trial**: 1-hour check interval (active monitoring)
- **standard**: 24-hour check interval (daily validation)
- **premium**: 168-hour check interval (weekly validation)
- Configured in `app_config.yaml` under `licensing.check_intervals`

**States & Flows:**
1. **No License** → `validate_startup()` prompts activation dialog (show [src/ui/license_dialog.py](src/ui/license_dialog.py))
2. **License Found** → online validation; if success → set `offline_grace_until` timestamp
3. **Online Fails** → check grace period; if within grace → allow offline use; if expired → show error
4. **Hardware Mismatch** → if ≥2 components differ, requires manual verification (email support)

**Transfer Tracking:**
- Max transfers per hardware: `licensing.max_transfers` (default 3)
- Logged in `license_info` table with `transfer_count` and `last_transfer_at`
- Auto-recovery attempts count as transfers; exceeded → manual intervention required

**Config (app_config.yaml):**
```yaml
licensing:
  offline_grace_days: 7
  check_interval_hours: 24
  check_intervals: { trial: 1, standard: 24, premium: 168 }
  max_transfers: 3
  hardware_match_threshold: 2
  require_remote_hardware_match: true
  sheet_url: https://docs.google.com/spreadsheets/d/...
```

**Workflow for Agents:**
- **Adding license logic:** Import `get_license_manager()` singleton; call `.validate_startup()` early in bootstrap
- **Debugging validation:** Check `license_validation_log` and `license_audit_log` tables
- **Testing offline:** Rename/delete `license_info` table, run app within 7-day grace window

## 🔗 External Dependencies & Integrations

**Critical External Services:**
- **Google Sheets API** ([src/licensing/license_manager.py](src/licensing/license_manager.py))
  - License validation pulls from Google Sheets (`licensing.sheet_url` in config)
  - Webhook at `licensing.webhook_url` triggers on license changes
  - Offline grace period: 7 days if network unavailable (configured in `app_config.yaml`)
  
- **Excel Files** (two separate files with different purposes)
  - **Meter Readings Excel** (`legacy_excel_path`): Historical meter data, tonnes milled, RWD volumes
    - Used by `WaterBalanceCalculator` to read operational metrics
    - File: `data/New Water Balance 20250930 Oct.xlsx` (or similar)
  - **Flow Diagram Excel** (`timeseries_excel_path`): Flow diagram data with `Flows_*` sheets
    - Used by `FlowVolume

Loader` to populate flow diagram edges
    - File: `data/Water_Balance_TimeSeries_Template.xlsx`
  - **Key Distinction:** Never mix these files - code explicitly checks which path to use

**Monitoring & Logging:**
- **File Watcher** ([src/utils/excel_monitor.py](src/utils/excel_monitor.py)): Detects Excel file changes in background
- **Structured Logging** ([src/utils/app_logger.py](src/utils/app_logger.py)): All output goes to `logs/` directory + console
- **Alert System** ([src/utils/alert_manager.py](src/utils/alert_manager.py)): Defines alert rules, trigger conditions

**Database Connection:**
- **SQLite** (no external service, local file at `data/water_balance.db`)
- **Connection pooling** in [src/database/db_manager.py](src/database/db_manager.py)
- **Auto-backup** before major operations

## 🚀 Key Developer Workflows

### Running & Building
```bash
# Development
.venv\Scripts\python src/main.py

# Test Suite
.venv\Scripts\python -m pytest tests/ -v

# Code Coverage
.venv\Scripts\python -m pytest tests/ --cov=src --cov-report=html

# Database Reset
.venv\Scripts\python -c "from src.database.schema import DatabaseSchema; DatabaseSchema().create_database()"

# Build EXE (Windows)
build.ps1  # Runs PyInstaller with water_balance.spec

# Create Installer
Build → run installer.iss (Inno Setup)
```

### Debugging
- **Logs:** Check `logs/` directory (structured JSON + console)
- **Database inspection:** Use `scripts/debug/` tools (organized by purpose)
- **License issues:** Check `license_validation_log` and `license_audit_log` tables
- **Excel issues:** Enable file monitor logging in `config/app_config.yaml`

### Configuration
- **Main config:** `config/app_config.yaml` (YAML-based, auto-reloaded)
- **Feature flags:** `features.*` in config (e.g., `features.fast_startup`)
- **Data paths:** `data_sources.*` in config (Excel paths, templates, DB path)
- **Licensing:** `licensing.*` in config (check intervals, grace periods, sheet URL)

## ⚠️ Common Pitfalls

1. **Stale singletons:** After config/path change, forgot to `reset_*()` → reads old Excel path
2. **Direct instantiation:** `FlowVolumeLoader()` instead of `get_flow_volume_loader()` → new instance, loses cache
3. **Missing sys.path shim:** New module in `src/` without `sys.path.insert(...)` → import errors
4. **Template mutations:** Writing to `.txt` template files → data loss on reload
5. **DB_loaded race:** UI tries balance calc before `app.db_loaded = True` → crashes
6. **Circular imports:** Importing from `ui` in `utils` → typically OK but watch for lazy imports in `__init__.py`
7. **Excel path priority:** Forgot that code checks `timeseries_excel_path` first → old data if not in that path
8. **Cache not cleared:** After Excel update, calculations use stale cached data → wrong results
9. **Missing UI thread dispatch:** Update Tkinter from non-main thread → crashes; use `root.after()`
10. **License check failures:** Network error during startup → app blocks; handled gracefully but watch logs

## � Code Comments Mandate (ENFORCED)

**Every function, class, and significant code block MUST have comments.** This is non-negotiable for maintainability.

### Comment Requirements (Enforce When Editing)
1. **Module Docstring:** Every file starts with a docstring explaining purpose, data sources, and dependencies
2. **Class Docstring:** Explain class purpose, key methods, and state management
3. **Function/Method Docstring:** Document parameters, return values, and side effects (use triple quotes)
4. **Inline Comments:** Explain WHY not WHAT; use for complex logic, non-obvious decisions, and data flows
5. **Data Quality Comments:** Explain where data comes from and any transformations applied
6. **Cache Comments:** Document all caching strategies, invalidation triggers, and performance implications
7. **XML/Deprecated Code:** Mark obsolete sections clearly with dates and reasons

### Example Comment Structure (Copy & Use)
```python
def calculate_balance(facility_code: str, month: int, year: int) -> Dict:
    """Calculate water balance for facility and month (PRIMARY CALCULATION ENGINE).
    
    This is the core orchestrator that coordinates:
    1. Reading meter data from Excel (Meter Readings sheet)
    2. Applying facility-specific constants (capacity, evaporation rates)
    3. Computing inflows, outflows, storage changes
    4. Validating closure (error < 5%)
    5. Caching results to avoid re-calculation
    
    Args:
        facility_code: Facility ID (e.g., 'UG2N', 'OLDTSF')
        month: Month (1-12)
        year: Gregorian year
    
    Returns:
        Dict with keys: balance_m3, error_pct, inflows, outflows, storage_change, kpis
        All values in m³ except error_pct (percentage)
    
    Raises:
        ValueError: If facility not found or month invalid
        ExcelReadError: If meter data missing (check data quality)
    
    Example:
        result = calc.calculate_balance('UG2N', 3, 2025)
        if result['error_pct'] > 5:
            logger.warning(f"High closure error for UG2N Mar2025: {result['error_pct']:.1f}%")
    """
    # Validate inputs first (fail fast on bad data)
    # ...
```

### Where Comments Go (Decision Tree)
| Scenario | Action |
|----------|--------|
| New function added | Add full docstring + inline comments for complex logic |
| Editing existing code | Add/update docstring if changed signature; add inline comments if logic changed |
| Removing dead code | Mark with `# DEPRECATED: [date] - [reason] - remove after [future date]` before deleting |
| Cache involved | Comment the cache key format, TTL, and invalidation trigger |
| Excel/DB query | Comment the sheet name, column names, and data transformations |
| Loop with >3 iterations | Add comment explaining iteration logic |
| Conditional branch | Comment WHY the branch exists (business rule, data validation, edge case) |

### Anti-Patterns (REMOVE If Found)
```python
# BAD: Obvious comments that just repeat code
volume = volume * 1000  # Multiply volume by 1000
column = row[0]  # Get the first column

# GOOD: Explain WHY and data context
volume_m3 = volume_ml * 1000  # Convert from mL (meter readings) to m³ for calculation engine
facility_code = row[0]  # Facility code from Excel "Meter Readings" A column (e.g., UG2N)
```

### Git Commit Message Requirement
Include comment rationale in commit message:
```
Add balance_check_engine.calculate_balance() method

- Implements core water balance equation: Fresh IN = Outflows + ΔStorage + Error
- Validates inflows/outflows don't exceed facility capacity (data quality)
- Caches results keyed by (date, facility) to avoid re-reads from Excel
- Called from UI calculations.py on user request; results shown in Balance tab

Updated comments for clarity on data sources (Meter Readings Excel vs Flow Diagram Excel).
```

## 📚 Deep Dive Resources

### **COMMENT ENFORCEMENT (MANDATORY)**
- **Enforcement Rules:** [.github/instructions/COMMENT_ENFORCEMENT_RULES.md](instructions/COMMENT_ENFORCEMENT_RULES.md) - **STRICT mandatory rules for all code changes**
- **Quick Reference:** [.github/COMMENT_QUICK_REFERENCE.md](COMMENT_QUICK_REFERENCE.md) - **1-page summary for quick lookup**
- **Implementation Summary:** [docs/COMMENT_UPDATES_SUMMARY.md](../docs/COMMENT_UPDATES_SUMMARY.md) - **Overview of standards established**

### Architecture & Feature Documentation
- **Balance Check Logic:** [docs/BALANCE_CHECK_README.md](../docs/BALANCE_CHECK_README.md)
- **Flow Diagram System:** [docs/FLOW_DIAGRAM_GUIDE.md](../docs/FLOW_DIAGRAM_GUIDE.md)
- **Component Rename:** [docs/features/COMPONENT_RENAME_SYSTEM_INDEX.md](../docs/features/COMPONENT_RENAME_SYSTEM_INDEX.md)
- **Excel Integration:** [docs/features/EXCEL_INTEGRATION_SUMMARY.md](../docs/features/EXCEL_INTEGRATION_SUMMARY.md)
- **Code Style:** [.github/instructions/python.instructions.md](instructions/python.instructions.md) (PEP 8, type hints, docstrings)

## ✅ ENFORCEMENT CHECKPOINT

**Before submitting ANY code change, verify:**
1. ✅ All functions/methods have docstrings
2. ✅ All parameters are documented with types
3. ✅ Complex logic has inline comments
4. ✅ Cache usage is documented (key, TTL, invalidation)
5. ✅ Data sources are clear (which Excel/DB, tables, columns)
6. ✅ Excel files are distinguished (Meter Readings vs Flow Diagram)
7. ✅ Examples provided for non-obvious functions
8. ✅ Commit message mentions comment updates

**See:** [.github/instructions/COMMENT_ENFORCEMENT_RULES.md](instructions/COMMENT_ENFORCEMENT_RULES.md) for complete checklist and rejection criteria.

## 🗂️ Repository Hygiene (STRICT)

### 📝 Markdown File Policy - ABSOLUTELY MINIMAL

**CRITICAL RULE - DO NOT CREATE SUMMARY .MD FILES** unless explicitly requested by user.

**Default Behavior:**
- ❌ **DO NOT** create summary files after completing work
- ❌ **DO NOT** create progress documentation automatically
- ❌ **DO NOT** create explanation files without user request
- ✅ **ONLY** create `.md` files when user explicitly says "create a doc" or "document this"

**When User DOES Ask for Documentation:**

Before creating ANY new `.md` file:
1. ✅ Search existing `docs/` subfolders for related topics
2. ✅ Check if content can be added to existing files instead
3. ✅ Review [docs/INDEX.md](../../docs/INDEX.md) and category README files
4. ✅ Ask yourself: "Does this NEED a new file, or should it update an existing one?"

**Placement Rules (When Creating):**
- **Operations/Admin** → `docs/04-OPERATIONS/`
- **Setup/Installation** → `docs/01-SETUP/`
- **Architecture/Design** → `docs/02-ARCHITECTURE/`
- **Database** → `docs/03-DATABASE/`
- **References** → `docs/05-REFERENCE/`
- **Never** → Project root (only README.md allowed)

**What NOT to Do (ENFORCED):**
- ❌ Create summary docs after every task
- ❌ Create progress tracking `.md` files
- ❌ Create "X is complete" documentation
- ❌ Create analysis files without explicit user request
- ❌ Create duplicate documentation (update existing instead)
- ❌ Create `.md` files in project root (except README.md)

**Root Folder Policy**:
- Keep root **PRISTINE** - only essential files
- Only allowed: `.github/`, `src/`, `tests/`, `config/`, `data/`, `docs/`, `logs/`, `.venv/`, config files (`requirements.txt`, `README.md`, workspace file)
- **Zero tolerance** for temporary or clutter `.md` files

### Other Repository Rules

- **Assets:** New assets go to `logo/`, `data/`, or `docs/` folders; keep root clean.
- **Outputs:** Write one-off analysis to temp locations; remove after use to avoid clutter.
- **virtualenv:** Use [.venv](.venv); run via `.venv\Scripts\python` and install via `.venv\Scripts\python -m pip install ...`. Do not create new environments.
- **Branding:** Centralized logos live in [logo/](../../logo/) (Logo Two rivers.png, Company Logo.png, Water Balance.ico).
- **Root Folder:** Keep clean. Only essential: `.github/`, `src/`, `tests/`, `config/`, `data/`, `docs/`, `.venv/`, `.gitignore`, `README.md`, `requirements.txt`
