# Water Balance Application - AI Agent Instructions

## 🎯 What This Is
Python/Tkinter desktop app for mine water balance across 8 areas. Core flow: read templates → calculate balances → load Excel overlays → persist to SQLite → render dashboards. Scientific basis: **Fresh Inflows = Outflows + ΔStorage + Error** (seepage captured in storage change).

## 🐍 Python Environment (MANDATORY)

**ALWAYS use the virtual environment for all Python operations:**
- **Run application:** `.venv\Scripts\python src/main.py`
- **Install packages:** `.venv\Scripts\python -m pip install <package>`
- **Run scripts:** `.venv\Scripts\python <script_path>`
- **Database operations:** `.venv\Scripts\python -c "<command>"`

**Never use system Python or create new virtual environments.** The project uses a single `.venv` environment configured in the root. If running tests or utilities, always activate: `.venv\Scripts\Activate.ps1` (PowerShell).

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

**Excel Sheets** (two separate files):
- **Meter Readings** (`legacy_excel_path`): "Meter Readings" sheet → used by `src/ui/calculations.py` for water balance
- **Flow Diagrams** (`timeseries_excel_path`): "Flows_*" sheets (8 areas) → used by `src/ui/flow_diagram_dashboard.py`

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

## 📚 Deep Dive Resources

- **Balance Check Logic:** [docs/BALANCE_CHECK_README.md](../../docs/BALANCE_CHECK_README.md)
- **Flow Diagram System:** [docs/FLOW_DIAGRAM_GUIDE.md](../../docs/FLOW_DIAGRAM_GUIDE.md)
- **Component Rename:** [docs/features/COMPONENT_RENAME_SYSTEM_INDEX.md](../../docs/features/COMPONENT_RENAME_SYSTEM_INDEX.md)
- **Excel Integration:** [docs/features/EXCEL_INTEGRATION_SUMMARY.md](../../docs/features/EXCEL_INTEGRATION_SUMMARY.md)
- **Code Style:** [.github/instructions/python.instructions.md](./../instructions/python.instructions.md) (PEP 8, type hints, docstrings)

## 🗂️ Repository Hygiene

- **Docs:** Prefer updating existing `.md` guides instead of creating new files. Consolidate into [docs/features/INDEX.md](../../docs/features/INDEX.md).
- **Assets:** New assets go to `logo/`, `data/`, or `docs/` folders; keep root clean.
- **Outputs:** Write one-off analysis to temp locations; remove after use to avoid clutter.
- **virtualenv:** Use [.venv](.venv); run via `.venv\Scripts\python` and install via `.venv\Scripts\python -m pip install ...`. Do not create new environments.
- **Branding:** Centralized logos live in [logo/](../../logo/) (Logo Two rivers.png, Company Logo.png, Water Balance.ico).
