# PySide6 Water Balance Dashboard - Quick Start Guide

Get the PySide6 water balance dashboard up and running quickly.

---

## Prerequisites

- Python 3.10 or higher
- Git
- Windows 10/11

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/Caliphsdev/Water-Balance-Application.git
cd Water-Balance-Application
```

### Step 2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Command Prompt)
.venv\Scripts\activate.bat
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
.venv\Scripts\python src/main.py
```

The main dashboard window will open with:
- Left sidebar with navigation buttons
- Dashboard page with KPI cards
- Storage Facilities management
- Flow Diagram editor
- Analytics views

---

## Project Structure

```
src/
├── main.py                 # Application entry point
├── core/                   # Infrastructure (logging, config)
│   ├── app_logger.py       # Logging configuration
│   └── config_manager.py   # YAML config loading
├── database/               # Database access layer
│   └── repositories/       # Data access classes
├── models/                 # Pydantic data models
├── services/               # Business logic layer
│   ├── dashboard_service.py        # KPI aggregation
│   ├── storage_facility_service.py # Facility operations
│   └── ...
└── ui/                     # PySide6 UI layer
    ├── main_window.py      # Main window controller
    ├── dashboards/         # Page controllers
    ├── dialogs/            # Modal dialogs
    ├── components/         # Reusable widgets
    │   └── graphics/       # Custom QGraphicsItems
    ├── models/             # Qt table models
    └── resources/          # Icons, styles
```

---

## Key Components

### Services (Business Logic)

| Service | Purpose |
|---------|---------|
| `DashboardService` | Aggregates KPI data for dashboard cards |
| `StorageFacilityService` | CRUD for storage facilities |
| `CalculationService` | Water balance calculations |
| `ExcelService` | Excel file import/export |

### Dashboard Pages

| Page | Description |
|------|-------------|
| `dashboard_dashboard.py` | Main dashboard with KPI cards |
| `storage_facilities_dashboard.py` | Facility management table |
| `flow_diagram_page.py` | Interactive flow diagram editor |
| `analytics_dashboard.py` | Analytics and trends |

### Custom Graphics

| Component | Description |
|-----------|-------------|
| `NodeGraphicsItem` | Flow diagram node with 17 anchor points |
| `EdgeGraphicsItem` | Connection edge with orthogonal routing |

---

## Common Commands

### Development

```powershell
# Run application
.venv\Scripts\python src/main.py

# Run all tests
.venv\Scripts\python -m pytest tests/ -v

# Run specific test
.venv\Scripts\python -m pytest tests/test_storage_facilities_backend.py -v

# Test coverage
.venv\Scripts\python -m pytest tests/ --cov=src --cov-report=html
```

### UI Compilation (Qt Designer)

```powershell
# Compile single .ui file
pyside6-uic src/ui/designer/dashboards/analytics.ui -o src/ui/dashboards/generated_ui_analytics.py

# Compile resources
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py
```

---

## Configuration

### Application Config

**File:** `config/app_config.yaml`

```yaml
database:
  path: data/water_balance.db

excel:
  legacy_path: data/legacy_excel.xlsx
  timeseries_path: data/timeseries.xlsx

ui:
  theme: dark
  font_size: 10
```

### Logging

Logs are written to `logs/app.log` with automatic rotation.

---

## Troubleshooting

### ImportError: No module named 'PySide6'

```bash
pip install PySide6 PySide6-Addons
```

### Database not found

The database file should be at `data/water_balance.db`. If missing, run the application once to create it.

### ModuleNotFoundError: No module named 'src'

Ensure you're running from the project root:

```bash
cd d:\Projects\dashboard_waterbalance
.venv\Scripts\python src/main.py
```

---

## Next Steps

1. **Explore the UI** - Click through dashboard pages
2. **Read Architecture** - See [01-ARCHITECTURE/](../01-ARCHITECTURE/) for patterns
3. **Backend Development** - See [02-BACKEND/](../02-BACKEND/) for services
4. **Frontend Development** - See [03-FRONTEND/](../03-FRONTEND/) for UI components

---

## Resources

- **PySide6 Docs**: https://doc.qt.io/qtforpython-6/
- **Qt Designer Guide**: https://doc.qt.io/qt-6/qtdesigner-manual.html
- **Project GitHub**: https://github.com/Caliphsdev/Water-Balance-Application

---

**Time to complete:** 15-20 minutes  
**Next:** Run the app and explore the dashboard!
