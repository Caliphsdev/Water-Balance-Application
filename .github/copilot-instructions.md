# Water Balance Application - AI Agent Instructions

- **What this is**: Python/Tkinter desktop app for mine water balance across 8 areas. Core flows: templates → calculations → optional Excel overlays → SQLite persistence → interactive dashboards.

## Architecture Map
- **Controllers**: [src/main.py](src/main.py) bootstraps `WaterBalanceApp` with fast-startup; [src/ui/main_window.py](src/ui/main_window.py) handles navigation.
- **Calculations**: [src/utils/water_balance_calculator.py](src/utils/water_balance_calculator.py) heavy engine with caches (`_balance_cache`, `_kpi_cache`, `_misc_cache`). Balance check lives in [src/utils/balance_check_engine.py](src/utils/balance_check_engine.py) fed by [src/utils/template_data_parser.py](src/utils/template_data_parser.py).
- **Data loading**: Excel on-demand via [src/utils/flow_volume_loader.py](src/utils/flow_volume_loader.py) (path priority: `data_sources.timeseries_excel_path` → `data_sources.template_excel_path` → fallback). JSON diagrams under `data/diagrams/<area>_flow_diagram.json` rendered by [src/ui/flow_diagram_dashboard.py](src/ui/flow_diagram_dashboard.py).
- **Persistence**: SQLite handled by [src/database/db_manager.py](src/database/db_manager.py) and [src/database/schema.py](src/database/schema.py); auto-creates `data/water_balance.db` if missing.
- **Entry variants**: Standard [src/main.py](src/main.py); fallback [src/main_launcher.py](src/main_launcher.py); experimental [src/main_optimized.py](src/main_optimized.py).

## Core Patterns
- **Singletons everywhere**: Always use getters (`get_flow_volume_loader()`, `get_template_parser()`, `get_balance_check_engine()`, `db`, `config`, `logger`, `error_handler`). Never instantiate classes directly. If settings change a path, call the module `reset_*` (e.g., `reset_flow_volume_loader()`) then re-fetch.
- **Config**: Centralized in [config/app_config.yaml](config/app_config.yaml). Update via `config.set(...)`, persist automatically, `config.load_config()` after external edits. Feature flags under `features.*` (notably `fast_startup`).
- **Import shim**: Every module in `src/` prepends `Path(__file__).parent.parent` to `sys.path`—keep this in new files.
- **Fast startup**: Background DB load via [src/utils/async_loader.py](src/utils/async_loader.py); UI must respect `app.db_loaded` before DB-dependent actions.
- **Error/logging**: Use [src/utils/error_handler.py](src/utils/error_handler.py) (`error_handler.handle(...)` returns tech/user messages + severity). Log with [src/utils/app_logger.py](src/utils/app_logger.py); use `logger.performance()` for timing.

## Repository Hygiene
- Prefer updating existing docs instead of creating new `.md` files; consolidate into existing guides (README, feature docs) when adding notes.
- Avoid adding ad-hoc scripts; extend existing utilities in [scripts](scripts) or `src/` where they logically fit. Delete any temporary script once its purpose is served.
- Keep root directory tidy—store new assets under existing folders (e.g., `docs/`, `scripts/`, `data/`).
- When generating outputs for one-off analysis, write to temporary locations and remove after use to avoid clutter.

## Environment
- Use the existing virtualenv at [.venv](../.venv); run tools via `.venv\Scripts\python` and install via `.venv\Scripts\python -m pip install ...`. Do not create new environments.

## Data Inputs & Flows
- Templates (read-only): [INFLOW_CODES_TEMPLATE.txt](INFLOW_CODES_TEMPLATE.txt), [OUTFLOW_CODES_TEMPLATE_CORRECTED.txt](OUTFLOW_CODES_TEMPLATE_CORRECTED.txt), [DAM_RECIRCULATION_TEMPLATE.txt](DAM_RECIRCULATION_TEMPLATE.txt). Parsed once by `get_template_parser()`.
- Excel overlays: `flow_volume_loader.get_flow_volumes_for_month(...)` resolves paths in priority order; call `clear_cache()` before reloads.
- Diagrams: Flow diagram uses `excel_mapping` on edges (mapped vs unmapped). Waypoints and colors auto-detected (clean/waste/underground) in [src/ui/flow_diagram_dashboard.py](src/ui/flow_diagram_dashboard.py).

## Key Workflows
- Run app: `python src/main.py` (honors fast startup). Alternate: `python src/main_launcher.py` or `python src/main_optimized.py`.
- Tests: `pytest src/database/test_database.py` (schema/connectivity). DB init/reset: `python -c "from database.schema import DatabaseSchema; DatabaseSchema().create_database()"`.
- Balance calc flow: in [src/ui/calculations.py](src/ui/calculations.py) `_calculate_balance()` invokes `WaterBalanceCalculator.calculate_water_balance()` + `BalanceCheckEngine.calculate_balance()`; tabs: Balance Summary, Area Breakdown, legacy Summary/Inflows/Outflows/Storage.
- Flow diagram loading: in `_load_from_excel()` (dashboard) fetch fresh loader, `clear_cache()`, then redraw edges.

## Performance & UX Notes
- Reuse caches in calculator before hitting DB. Avoid blocking UI thread; offload heavy work or respect async loader.
- Log timings for hot paths; keep template files immutable in code.

## Common Pitfalls
- Forgetting singleton reset after config/path changes → stale data (flows, Excel, config).
- Bypassing `config` or `db` singletons → inconsistencies.
- Omitting `sys.path.insert(...)` in new modules under `src/` → import failures.
- Modifying template `.txt` files programmatically → user data loss.
- Ignoring `db_loaded` during startup → UI errors.

## Component Rename System
When renaming a component (e.g., `offices` → `office_building`), use the automated system:
1. Edit `component_rename_config.json` with old/new names and Excel columns
2. Run: `python component_rename_manager.py --dry-run` (preview)
3. Run: `python component_rename_manager.py` (apply)
- **What updates**: JSON node IDs, edge references, mappings, Excel columns across all 8 flow sheets
- **Docs**: [COMPONENT_RENAME_SYSTEM_INDEX.md](COMPONENT_RENAME_SYSTEM_INDEX.md) (start here); [COMPONENT_RENAME_QUICK_REFERENCE.md](COMPONENT_RENAME_QUICK_REFERENCE.md) (quick copy-paste).
- **Key**: Always preview first with `--dry-run`; supports batch renames.

## Pointers for Deep Dives
- Balance check docs: [BALANCE_CHECK_README.md](BALANCE_CHECK_README.md).
- Flow diagram usage: [FLOW_DIAGRAM_GUIDE.md](FLOW_DIAGRAM_GUIDE.md).
- Component rename system: [COMPONENT_RENAME_SYSTEM_INDEX.md](COMPONENT_RENAME_SYSTEM_INDEX.md).
- Style/perf guides: [.github/instructions/python.instructions.md](../.github/instructions/python.instructions.md), [.github/instructions/performance-optimization.instructions.md](../.github/instructions/performance-optimization.instructions.md).
