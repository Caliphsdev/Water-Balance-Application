# Water Balance Application - AI Agent Instructions

## 🎯 What This Is
Python/Tkinter desktop app for mine water balance across 8 areas. Core flow: read templates → calculate balances → load Excel overlays → persist to SQLite → render dashboards. Scientific basis: **Fresh Inflows = Outflows + ΔStorage + Error** (seepage captured in storage change).

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

**ALWAYS use the virtual environment for all Python operations:**
- **Run application:** `.venv\Scripts\python src/main.py`
- **Install packages:** `.venv\Scripts\python -m pip install <package>`
- **Run scripts:** `.venv\Scripts\python <script_path>`
- **Database operations:** `.venv\Scripts\python -c "<command>"`

**Never use system Python or create new virtual environments.** The project uses a single `.venv` environment configured in the root. If running tests or utilities, always activate: `.venv\Scripts\Activate.ps1` (PowerShell).

## 🧪 Testing Requirements (MANDATORY)

**Every feature must have corresponding tests.**

**Test Creation Rules:**
- Create tests for **every new function, class, and feature** before or immediately after implementation
- Test files go in `tests/` directory, mirroring `src/` structure (e.g., `src/utils/foo.py` → `tests/utils/test_foo.py`)
- Use `pytest` as the testing framework
- Run tests before committing: `.venv\Scripts\python -m pytest tests/ -v`
- Aim for **>80% code coverage** on core logic (utils, database, calculations)
- Use fixtures and mocks to isolate units
- Document non-obvious test cases with comments

**Test Categories:**
- **Unit Tests:** Individual functions/methods (fast, isolated)
- **Integration Tests:** Multi-component workflows (DB, Excel, calculations)
- **UI Tests:** Dialog flows, state changes (use mocking where possible)

**Examples:**
- New calculator function → write unit test in `tests/utils/test_calculator.py`
- New Excel loader → write integration test in `tests/utils/test_excel_loader.py`
- New UI dialog → write UI test in `tests/ui/test_dialog.py`

**Workflow:**
1. Write test (TDD preferred, but post-implementation OK)
2. Implement feature
3. Run: `.venv\Scripts\python -m pytest tests/ -v`
4. Achieve green tests
5. Commit with test code included

**Pro Tips:**
- Use `pytest-cov` to check coverage: `.venv\Scripts\python -m pytest tests/ --cov=src`
- Use `pytest-mock` for mocking external dependencies
- Use fixtures in `tests/conftest.py` for shared test data

## 🏗️ Architecture Map

**Data Flow Layers:**
- **Input Templates** → [src/utils/template_data_parser.py](src/utils/template_data_parser.py) parses 3 immutable `.txt` files (inflow/outflow/recirculation codes)
- **Calculations** → [src/utils/water_balance_calculator.py](src/utils/water_balance_calculator.py) (heavy engine, multi-level caches) + [src/utils/balance_check_engine.py](src/utils/balance_check_engine.py) (validation metrics)
- **Excel Overlays** → [src/utils/flow_volume_loader.py](src/utils/flow_volume_loader.py) loads volumes on-demand (path priority: `timeseries_excel_path` > `template_excel_path` > fallback)
- **Persistence** → [src/database/db_manager.py](src/database/db_manager.py) + [src/database/schema.py](src/database/schema.py) (SQLite, 11 tables, auto-init)
- **UI Rendering** → [src/ui/calculations.py](src/ui/calculations.py) (balance tabs) + [src/ui/flow_diagram_dashboard.py](src/ui/flow_diagram_dashboard.py) (JSON diagrams at `data/diagrams/<area>_flow_diagram.json`)

**Key Components:**
- **Bootstrap** [src/main.py](src/main.py) sets `WATERBALANCE_USER_DIR` env var (app-data path) before all imports; async DB load via [src/utils/async_loader.py](src/utils/async_loader.py)
- **Navigation** [src/ui/main_window.py](src/ui/main_window.py)
- **Config** [config/app_config.yaml](config/app_config.yaml) (centralized; YAML backed)

## 🔧 Core Patterns

**Singleton Mandate:** Never `MyClass()` directly. Always use module-level getters:
- `get_template_parser()`, `get_flow_volume_loader()`, `get_balance_check_engine()`, `get_balance_engine()`
- `db` (DatabaseManager), `config` (ConfigManager), `logger` (AppLogger), `error_handler` (ErrorHandler)
- After config/path changes, call `reset_*()` (e.g., `reset_flow_volume_loader()`) then re-fetch to pick up new state.

**Caching Strategy:** Multi-tier with explicit invalidation:
- `WaterBalanceCalculator._balance_cache`, `._kpi_cache`, `._misc_cache` (dict-keyed by date/area)
- DB Manager has `use_cache=False` option; `invalidate_all_caches()` on schema edits
- Call `.clear_cache()` on loaders before Excel reload
- **Rationale:** Avoid re-parsing Excel/templates; speed up repeated calculations in same session

**Config Pattern:** `config.set(key, value)` auto-persists to YAML. Feature flags: `config.get('features.fast_startup')`.

**Import Shim:** Every module in `src/` starts:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```
Then imports from `utils`, `database`, `ui`, `models`. **Keep this in new files.**

**Fast Startup:** UI thread shows loading screen while [src/utils/async_loader.py](src/utils/async_loader.py) loads DB in background. UI checks `app.db_loaded` before DB-dependent actions.

**Error Handling:** `error_handler.handle(exception)` returns `(tech_msg, user_msg, severity)`. Log with `logger.performance(label)` for timings.

## 📂 Data Inputs & Flows

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

## ⚠️ Common Pitfalls

1. **Stale singletons:** After config/path change, forgot to `reset_*()` → reads old Excel path
2. **Direct instantiation:** `FlowVolumeLoader()` instead of `get_flow_volume_loader()` → new instance, loses cache
3. **Missing sys.path shim:** New module in `src/` without `sys.path.insert(...)` → import errors
4. **Template mutations:** Writing to `.txt` template files → data loss on reload
5. **DB_loaded race:** UI tries balance calc before `app.db_loaded = True` → crashes
6. **Circular imports:** Importing from `ui` in `utils` → typically OK but watch for lazy imports in `__init__.py`
7. **Excel path priority:** Forgot that code checks `timeseries_excel_path` first → old data if not in that path

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

## 🗂️ Repository Hygiene

- **Docs:** Prefer updating existing `.md` guides instead of creating new files. Consolidate into [docs/features/INDEX.md](../../docs/features/INDEX.md).
- **Assets:** New assets go to `logo/`, `data/`, or `docs/` folders; keep root clean.
- **Outputs:** Write one-off analysis to temp locations; remove after use to avoid clutter.
- **virtualenv:** Use [.venv](.venv); run via `.venv\Scripts\python` and install via `.venv\Scripts\python -m pip install ...`. Do not create new environments.
- **Branding:** Centralized logos live in [logo/](../../logo/) (Logo Two rivers.png, Company Logo.png, Water Balance.ico).
