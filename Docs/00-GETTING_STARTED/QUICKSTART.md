# PySide6 Migration Quick-Start Guide

Get the PySide6 water balance dashboard up and running quickly.

## Phase 1: Initial Setup (30 minutes)

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd d:\Projects\dashboard_waterbalance

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install PySide6 and core dependencies
pip install -r requirements.txt
```

**requirements.txt (create this):**
```
PySide6>=6.5.0
PySide6-Addons>=6.5.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
PyYAML>=6.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
matplotlib>=3.7.0
reportlab>=4.0.0
gspread>=5.12.0
google-auth>=2.23.0
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

### Step 2: Create Directory Structure

```bash
# Run from project root
mkdir -p src\ui\designer
mkdir -p src\ui\dialogs
mkdir -p src\ui\dashboards
mkdir -p src\ui\components
mkdir -p src\ui\styles
mkdir -p src\core
mkdir -p src\services
mkdir -p src\models
mkdir -p src\database
mkdir -p src\utils
mkdir -p config
mkdir -p data\diagrams
mkdir -p data\templates
mkdir -p tests\test_services
mkdir -p tests\test_ui
mkdir -p tests\test_models
```

### Step 3: Copy Core Files from Tkinter

Copy these files from `../tkinter-legacy/src/` without modification:

```bash
# Database layer (unchanged)
cp ../tkinter-legacy/src/database/schema.py src/database/
cp ../tkinter-legacy/src/database/db_manager.py src/database/

# Logging (unchanged)
cp ../tkinter-legacy/src/utils/app_logger.py src/core/

# Config (copy, will enhance later)
cp ../tkinter-legacy/config/app_config.yaml config/
cp ../tkinter-legacy/src/utils/config_manager.py src/core/config_manager.py

# Create empty __init__ files
touch src/__init__.py
touch src\core\__init__.py
touch src\database\__init__.py
touch src\services\__init__.py
touch src\models\__init__.py
touch src\ui\__init__.py
touch src\ui\dialogs\__init__.py
touch src\ui\dashboards\__init__.py
touch src\ui\components\__init__.py
touch src\ui\styles\__init__.py
```

### Step 4: Create Main Entry Point

**File: `src/main.py`** (minimal bootstrap)

```python
"""Water Balance Dashboard - PySide6 Entry Point.

Minimal bootstrap that:
1. Sets WATERBALANCE_USER_DIR environment variable
2. Validates license
3. Initializes PySide6 application
4. Shows main window
"""

import sys
import os
from pathlib import Path

# CRITICAL: Set WATERBALANCE_USER_DIR BEFORE any imports
# This ensures database, config, and license use correct paths
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    local_appdata = os.getenv('LOCALAPPDATA')
    if local_appdata:
        user_base = Path(local_appdata) / 'WaterBalance'
    else:
        user_base = Path.home() / 'AppData' / 'Local' / 'WaterBalance'
else:
    # Running in development
    user_base = Path(__file__).parent.parent

user_base.mkdir(parents=True, exist_ok=True)
os.environ['WATERBALANCE_USER_DIR'] = str(user_base)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# NOW safe to import PySide6 and app modules
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.app_logger import logger


def main():
    """Launch application."""
    logger.info("Application starting")
    
    # Create QApplication (must be before creating any widgets)
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("Main window displayed")
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
```

**Run it:**
```bash
.venv\Scripts\python src/main.py
```

---

## Phase 2: First Dashboard (2-3 hours)

### Step 1: Create Main Window UI in Qt Designer

**File: `src/ui/designer/main_window.ui`**

Use Qt Designer to create:
1. Main window with menu bar
2. Left sidebar (vertical layout with buttons: Calculations, Flow Diagram, Analytics, Settings)
3. Content area (central widget, will hold dashboards)
4. Status bar

**To generate Python code from .ui file:**
```bash
# Install pyside6 uic command
pip show pyside6 | grep Location

# Generate Python from .ui file
pyside6-uic src\ui\designer\main_window.ui -o src\ui\generated_ui_main_window.py
```

### Step 2: Create Main Window Controller

**File: `src/ui/main_window.py`**

Copy from [PYSIDE6_PATTERNS.md](PYSIDE6_PATTERNS.md) → Section "Signal/Slot Communication"

Replace this section in the template:
```python
# Load first dashboard
self._show_dashboard("calculations")
```

With:
```python
# Load first dashboard
self._show_dashboard("calculations")

# Set window title and size
self.setWindowTitle("Water Balance Dashboard")
self.resize(1200, 800)
```

### Step 3: Create Calculations Dashboard

**File: `src/ui/dashboards/calculations_dashboard.py`**

Copy from [PYSIDE6_PATTERNS.md](PYSIDE6_PATTERNS.md) → Section "Qt Designer Integration"

### Step 4: Create Calculations Service

**File: `src/services/calculation_service.py`**

Copy from [PYSIDE6_PATTERNS.md](PYSIDE6_PATTERNS.md) → Section "Service Layer Pattern"

Adapt this part for your actual Excel loaders:
```python
def _calculate_inflows(self, facility: Dict, meter_data: Dict) -> float:
    """Calculate total fresh inflows (m³)."""
    # TODO: Implement based on facility inflow sources
    # For now, return dummy data
    return 80000

def _calculate_outflows(self, facility: Dict, meter_data: Dict) -> float:
    """Calculate total outflows (m³)."""
    # TODO: Implement based on facility outflow sinks
    return 80000

def _calculate_storage_change(self, facility: Dict, meter_data: Dict) -> float:
    """Calculate change in storage (m³)."""
    # TODO: Implement storage level calculations
    return 5000
```

### Step 5: Create Excel Service

**File: `src/services/excel_service.py`**

Consolidate Excel loaders from Tkinter:
```python
"""Excel Service - Consolidated data loading from Excel files.

Replaces these Tkinter files:
- flow_volume_loader.py
- excel_timeseries.py
- excel_monthly_reader.py
- lazy_excel_loader.py
"""

from typing import Dict, Optional
from datetime import date
from pathlib import Path
import sys
import openpyxl

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import config
from core.app_logger import logger


class ExcelService:
    """Unified Excel data loading service."""
    
    def __init__(self):
        """Initialize Excel service."""
        self._meter_readings_cache = {}
        self._flow_volumes_cache = {}
    
    def load_meter_readings(self, facility_code: str, calc_date: date) -> Dict:
        """Load meter readings from Excel (Meter Readings file).
        
        Args:
            facility_code: Facility code (e.g., 'UG2N')
            calc_date: Date to load (year-month)
        
        Returns:
            Dict with meter readings (storage_start, storage_end, inflows, outflows)
        
        Raises:
            FileNotFoundError: If Excel file not found
            ValueError: If data missing for facility/date
        """
        # TODO: Implement meter readings loading from legacy_excel_path
        # For now, return dummy data
        return {
            'storage_start': 100000,
            'storage_end': 95000,
            'rainfall': 50000,
            'borehole': 30000,
            'mill_consumption': 60000,
            'evaporation': 20000,
        }
    
    def load_flow_volumes(self, area_code: str) -> Dict:
        """Load flow diagram volumes from Excel (Flow Diagram file).
        
        Args:
            area_code: Area code (e.g., 'UG2')
        
        Returns:
            Dict mapping flow_id -> volume_m3
        """
        # TODO: Implement flow volumes loading from timeseries_excel_path
        return {}
    
    def clear_cache(self):
        """Clear cached Excel data (call after Excel reload)."""
        self._meter_readings_cache.clear()
        self._flow_volumes_cache.clear()
        logger.info("Excel cache cleared")
```

### Step 6: Create Database Service

**File: `src/services/database_service.py`**

Wrap the existing `db_manager.py`:
```python
"""Database Service - Abstraction layer over database operations.

Wraps src/database/db_manager.py to provide clean API for services and UI.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager


class DatabaseService:
    """Database operations abstraction layer."""
    
    def __init__(self):
        """Initialize database service."""
        self.db_manager = DatabaseManager()
    
    def get_facility(self, facility_code: str) -> dict:
        """Get facility by code.
        
        Args:
            facility_code: Facility code (e.g., 'UG2N')
        
        Returns:
            Dict with facility data or None
        """
        # TODO: Implement using db_manager
        return {
            'code': facility_code,
            'name': f'Facility {facility_code}',
            'capacity_m3': 150000,
            'inflow_sources': ['rainfall', 'borehole'],
            'outflow_sinks': ['mill_consumption', 'evaporation'],
        }
    
    def get_all_facilities(self) -> list:
        """Get all facilities.
        
        Returns:
            List of facility dicts
        """
        # TODO: Implement using db_manager
        return []
```

### Step 7: Run and Test

```bash
# Run application
.venv\Scripts\python src/main.py

# Should see:
# - Main window with sidebar
# - Calculations dashboard (button clickable)
# - Dummy results displayed in table
```

---

## Phase 3: Add More Dashboards (1 week)

### For Each Dashboard:

1. **Design UI in Qt Designer**
   - Create `.ui` file in `src/ui/designer/dashboards/`
   - Example: `calculations_view.ui`, `flow_diagram_view.ui`

2. **Generate Python from .ui**
   ```bash
   pyside6-uic src\ui\designer\dashboards\calculations_view.ui -o src\ui\generated_ui_calculations_view.py
   ```

3. **Create Dashboard Controller**
   - File: `src/ui/dashboards/<dashboard>_dashboard.py`
   - Load UI: `self.ui = Ui_<DashboardView>()`
   - Connect signals: `self.ui.button.clicked.connect(self._on_clicked)`
   - Call services: `self.service.do_something()`

4. **Add Service Layer If Needed**
   - File: `src/services/<domain>_service.py`
   - Pure business logic, no UI imports

5. **Write Tests**
   - File: `tests/test_ui/test_<dashboard>_dashboard.py`
   - File: `tests/test_services/test_<domain>_service.py`

### Example: Flow Diagram Dashboard

**UI:** Load JSON diagrams, render with PySide6 graphics
**Service:** Parse JSON, provide node/edge data
**Tests:** Mock JSON, verify rendering

---

## Common Commands

### Development
```bash
# Run app
.venv\Scripts\python src/main.py

# Run tests
.venv\Scripts\python -m pytest tests/ -v

# Test coverage
.venv\Scripts\python -m pytest tests/ --cov=src --cov-report=html

# Generate all UI files from Designer
for /r src\ui\designer %%f in (*.ui) do pyside6-uic "%%f" -o "src\generated_ui_%%~nf.py"

# Check for Python errors
.venv\Scripts\python -m py_compile src/**/*.py
```

### Debugging
```bash
# Run with debug logging
.venv\Scripts\python -c "import logging; logging.basicConfig(level=logging.DEBUG); import src.main; src.main.main()"

# Check imports
.venv\Scripts\python -c "from src.ui.main_window import MainWindow; print('Imports OK')"

# List installed packages
.venv\Scripts\pip list
```

---

## Troubleshooting

### ImportError: No module named 'PySide6'
```bash
# Install PySide6
.venv\Scripts\pip install PySide6
```

### ImportError: cannot import name 'Ui_MainWindow'
```bash
# Regenerate .ui file
pyside6-uic src\ui\designer\main_window.ui -o src\ui\generated_ui_main_window.py
```

### ModuleNotFoundError: No module named 'src'
```bash
# Ensure sys.path is set in imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Database not found
```bash
# Copy from Tkinter project
cp ../tkinter-legacy/data/water_balance.db data/
```

### Excel file not found
```bash
# Copy Excel files to data/
cp ../tkinter-legacy/data/*.xlsx data/
```

---

## Next Steps

1. **Complete Phase 2** - Get first dashboard running
2. **Add remaining dashboards** - Flow diagram, analytics, charts
3. **Connect real data** - Replace dummy data with actual Excel/DB
4. **Add dialogs** - Settings, data import, license
5. **Test thoroughly** - Unit tests, integration tests
6. **Build executable** - PyInstaller, create installer
7. **Document** - Update README, user guide

---

## File Checklist (By End of Phase 2)

- [x] Directory structure created
- [x] Database files copied from Tkinter
- [x] `src/main.py` (entry point)
- [x] `src/core/app_logger.py` (logging)
- [x] `src/core/config_manager.py` (configuration)
- [x] `src/ui/main_window.py` (main UI controller)
- [x] `src/ui/designer/main_window.ui` (Qt Designer file)
- [x] `src/ui/generated_ui_main_window.py` (auto-generated)
- [x] `src/ui/dashboards/calculations_dashboard.py` (first dashboard)
- [x] `src/services/calculation_service.py` (calculation logic)
- [x] `src/services/excel_service.py` (Excel I/O)
- [x] `src/services/database_service.py` (DB abstraction)
- [x] `config/app_config.yaml` (app configuration)
- [x] `tests/test_services/test_calculation_service.py` (unit tests)
- [x] `tests/test_ui/test_main_window.py` (UI tests)
- [x] `requirements.txt` (Python dependencies)

---

## Resources

- **PySide6 Docs**: https://doc.qt.io/qtforpython-6/
- **Qt Designer Guide**: https://doc.qt.io/qt-6/qtdesigner-manual.html
- **Tkinter Source**: `../tkinter-legacy/src/` (for business logic reference)
- **Architecture Details**: See [MIGRATION_ANALYSIS.md](MIGRATION_ANALYSIS.md) and [PYSIDE6_PATTERNS.md](PYSIDE6_PATTERNS.md)

---

**Estimated Timeline:**
- Phase 1 (Setup): 30 minutes
- Phase 2 (First Dashboard): 2-3 hours
- Phase 3 (All Dashboards): 1 week
- **Total**: ~10-12 days for feature parity

Good luck! 🚀
