# Copilot Instructions - Water Balance Dashboard

## Architecture

**Stack**: PySide6 (Qt6) desktop app with SQLite database, pandas/numpy for data processing.

**Data Flow**: `UI (dashboards/) → Services (services/) → Repositories (database/repositories/) → SQLite`

```
src/
├── ui/dashboards/          # Page controllers (e.g., dashboard_dashboard.py)
│   └── generated_ui_*.py   # Compiled from Qt Designer .ui files
├── services/               # Business logic (e.g., storage_facility_service.py)
├── database/repositories/  # Data access layer
└── core/                   # Logging, config
```

## Critical Patterns

### Service Layer (REQUIRED)
All business logic goes in `services/`. Never put DB queries or calculations in UI controllers.
```python
# ✅ Correct: UI calls service
from services.dashboard_service import get_dashboard_service
kpis = get_dashboard_service().get_dashboard_kpis()

# ❌ Wrong: Direct DB access in UI
cursor.execute("SELECT * FROM facilities")
```

### Import Shim (REQUIRED in every src/ file)
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Qt Designer Workflow
1. Edit `.ui` file in Qt Designer (`src/ui/designer/`)
2. Compile: `pyside6-uic src/ui/designer/dashboards/X.ui -o src/ui/dashboards/generated_ui_X.py`
3. Fix import: Change `import resources_rc` → `import ui.resources.resources_rc`
4. Commit only `generated_ui_*.py` files, NOT `.ui` files

## Key Commands

```powershell
.venv\Scripts\python src/main.py              # Run app
pytest tests/ -v                               # Run tests
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py  # Compile resources
```

## Release Workflow (Windows)

When shipping updates, always follow this order:

1) Bump versions:
- `config/app_config.yaml` → `app.version`
- `scripts/packaging/water_balance.iss` → `#define AppVersion`

2) Build app bundle:
```powershell
.\scripts\packaging\build_windows.ps1
```

3) Build installer:
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" .\scripts\packaging\water_balance.iss
```

4) Compute hash + size:
```powershell
$path = "scripts\packaging\dist\installer\WaterBalanceDashboard-Setup.exe"
Get-FileHash -Algorithm SHA256 $path
(Get-Item $path).Length
```

5) Publish GitHub release:
```powershell
gh release create vX.Y.Z "scripts/packaging/dist/installer/WaterBalanceDashboard-Setup.exe" -t "vX.Y.Z" -n "<release notes>"
```

6) Insert Supabase row in `app_updates`:
```sql
insert into app_updates (version, min_tiers, download_url, release_notes, file_hash, file_size, is_mandatory)
values (
	'X.Y.Z',
	ARRAY['developer'],
	'https://github.com/Caliphsdev/Water-Balance-Application/releases/download/vX.Y.Z/WaterBalanceDashboard-Setup.exe',
	'<release notes>',
	'<SHA256>',
	<file size bytes>,
	false
);
```

## Conventions

- **Controllers**: `{name}_dashboard.py` or `{name}_page.py`
- **Services**: `{entity}_service.py` with singleton pattern via `get_{name}_service()`
- **UI Slots**: `_on_{event}()` (e.g., `_on_refresh_clicked`)
- **Docstrings**: Google style with `(SECTION MARKER)` for navigation

## File Policy

- ❌ Do NOT create `.md` summary files after completing work
- ❌ Do NOT create files in project root (only README.md allowed)
- ✅ Update existing docs in `Docs/` if documentation is needed

## Key Files

| Purpose | File |
|---------|------|
| Main dashboard | `src/ui/dashboards/dashboard_dashboard.py` |
| KPI aggregation | `src/services/dashboard_service.py` |
| Storage CRUD | `src/services/storage_facility_service.py` |
| Flow diagram | `src/ui/dashboards/flow_diagram_page.py` (2400+ lines) |
| PySide6 reference | `Docs/pyside6/create-gui-applications-pyside6.pdf` (730 pages) |

## Reference

- **PySide6 Docs**: https://doc.qt.io/qtforpython-6/
- **GitHub**: https://github.com/Caliphsdev/Water-Balance-Application
