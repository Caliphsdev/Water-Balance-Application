# 📁 Complete Directory Structure Guide

**Purpose:** Clear explanation of every folder and subfolder in the project  
**Use:** Reference this when deciding where to place new files during development  
**Date:** January 29, 2026

---

## 📋 Table of Contents

1. [Root Level Folders](#root-level-folders)
2. [src/ - Source Code](#src---source-code)
3. [src/ui/ - User Interface](#srcui---user-interface)
4. [tests/ - Testing](#tests---testing)
5. [Quick Reference Table](#quick-reference-table)

---

## 🌳 Complete Directory Tree

```
dashboard_waterbalance/
│
├── config/                      # Application configuration files
│   └── app_config.yaml         # Main YAML config (database paths, Excel paths, etc.)
│
├── data/                        # Runtime data (Excel files, JSON, diagrams, database)
│   ├── balance_check_config.json
│   ├── excel_flow_links.json
│   ├── water_balance.db        # SQLite database (created at runtime)
│   └── diagrams/               # Flow diagram JSON files
│       └── *.json
│
├── src/                         # All Python source code
│   ├── main.py                 # Application entry point
│   │
│   ├── core/                   # Core infrastructure (logging, config management)
│   ├── database/               # Database layer (SQLite connection, schema, queries)
│   ├── models/                 # Data models (Pydantic classes for validation)
│   ├── services/               # Business logic (calculations, data processing)
│   ├── utils/                  # Utility functions (helpers, formatting, caching)
│   └── ui/                     # User interface (PySide6 widgets, dialogs, dashboards)
│
├── tests/                       # All unit tests and integration tests
│   ├── test_models/
│   ├── test_services/
│   └── test_ui/
│
├── Docs/                        # All documentation (18 files)
│   └── *.md
│
├── .venv/                       # Virtual environment (Python packages)
├── requirements.txt             # Python dependencies
└── README.md                    # Project overview
```

---

## Root Level Folders

### 📁 `config/`
**Purpose:** Application configuration files (settings, preferences, feature flags)

**What Goes Here:**
- `app_config.yaml` - Main configuration file
  - Database paths
  - Excel file paths
  - Feature flags (fast_startup, etc.)
  - UI settings (theme, window size)
  - Logging configuration

**Why Separate Folder:**
- Configuration is external to code (can be edited without recompiling)
- Easy to version control settings
- Can have different configs for dev/test/production

**Examples:**
```yaml
# app_config.yaml
database:
  path: "data/water_balance.db"
  
data_sources:
  excel_path: "data/Water_Balance_Template.xlsx"
  
features:
  fast_startup: true
  enable_analytics: true
```

**Rules:**
- ✅ DO: Store user-configurable settings here
- ✅ DO: Use YAML for human-readable config
- ❌ DON'T: Put code or Python files here
- ❌ DON'T: Store sensitive data (passwords, API keys) - use environment variables

---

### 📁 `data/`
**Purpose:** Runtime data files (Excel, JSON, SQLite database, diagrams)

**What Goes Here:**
- `water_balance.db` - SQLite database (created at runtime)
- `*.json` - Configuration data files
  - `balance_check_config.json` - Balance check settings
  - `excel_flow_links.json` - Excel column mappings
  - `flow_friendly_names.json` - Component display names
- `diagrams/` subfolder - Flow diagram JSON files
  - `ug2_north_decline.json`
  - `test_bidirectional_edge.json`
  - etc.

**Why Separate Folder:**
- Data is separate from code (can be backed up independently)
- Database and Excel files can be large
- Easy to .gitignore the database (don't commit user data)
- Easy to provide sample data vs production data

**Subfolders:**
- `diagrams/` - Flow diagram JSON files (node positions, edge paths, zones)

**Rules:**
- ✅ DO: Store runtime data (database, Excel files, JSON data)
- ✅ DO: Use .gitignore for `*.db` files (user data)
- ✅ DO: Commit JSON templates and example files
- ❌ DON'T: Put source code here
- ❌ DON'T: Put UI resources (icons, fonts) here - use src/ui/resources/

---

### 📁 `Docs/`
**Purpose:** All project documentation (architecture, guides, checklists)

**What Goes Here:**
- Architecture documentation
- Implementation guides
- Design patterns
- Quick start guides
- Progress checklists

**Current Files (18 total):**
- `README_CODE_STRUCTURE_REVIEW.md` - Quick verification
- `ARCHITECTURE_VERIFICATION.md` - Detailed architecture
- `BACKEND_IMPLEMENTATION_ROADMAP.md` - Implementation steps
- `PYSIDE6_PATTERNS.md` - Code examples
- `INDEX.md` - Documentation index
- etc.

**Rules:**
- ✅ DO: Store all .md documentation here
- ✅ DO: Keep README.md in root (project entry point)
- ❌ DON'T: Put code or data files here
- ❌ DON'T: Create .md files in root (except README.md)

---

### 📁 `.venv/`
**Purpose:** Python virtual environment (isolated package installation)

**What's Inside:**
- Python interpreter
- Installed packages (PySide6, pandas, openpyxl, etc.)
- Scripts (activate, pip, python)

**Rules:**
- ✅ DO: Always activate before running code (`.venv\Scripts\activate`)
- ✅ DO: Install packages here (`python -m pip install <package>`)
- ❌ DON'T: Commit to Git (.gitignore this folder)
- ❌ DON'T: Manually edit files inside

---

## src/ - Source Code

**Purpose:** All Python application code (business logic, UI, services)

**Structure:**
```
src/
├── main.py              # Entry point (starts application)
├── core/                # Infrastructure (logging, config, app lifecycle)
├── database/            # Data access (SQLite, queries, schema)
├── models/              # Data models (Pydantic validation classes)
├── services/            # Business logic (calculations, data processing)
├── utils/               # Utilities (helpers, caching, formatting)
└── ui/                  # User interface (PySide6 widgets, dashboards, dialogs)
```

---

### 📁 `src/core/`
**Purpose:** Core infrastructure (logging, configuration, app lifecycle)

**What Goes Here:**
- `app_logger.py` - Structured logging setup
- `config_manager.py` - YAML config loading and management
- `application_manager.py` - App lifecycle (startup, shutdown, singleton)

**Why This Folder:**
- Core services used by ALL other layers
- No dependencies on UI, database, or business logic
- Can be tested independently
- Reusable across different projects

**Examples:**
```python
# core/app_logger.py
import logging

def get_logger(name: str) -> logging.Logger:
    """Get structured logger for module"""
    pass

# core/config_manager.py
class ConfigManager:
    """Load and manage YAML configuration"""
    def get(self, key: str) -> Any:
        pass
    
    def set(self, key: str, value: Any):
        pass
```

**Rules:**
- ✅ DO: Put infrastructure code here (logging, config, lifecycle)
- ✅ DO: Keep code framework-agnostic (no PySide6 imports)
- ❌ DON'T: Put business logic here (use services/)
- ❌ DON'T: Put UI code here (use ui/)

---

### 📁 `src/database/`
**Purpose:** Database access layer (SQLite connection, schema, queries)

**What Goes Here:**
- `db_manager.py` - Database connection pooling, query execution
- `schema.py` - Table definitions, migrations
- `repositories/` (future) - Repository pattern classes
  - `facility_repository.py` - Facility CRUD operations
  - `measurement_repository.py` - Measurement CRUD operations

**Why This Folder:**
- Isolates database access from business logic
- Easy to swap database (SQLite → PostgreSQL)
- Connection pooling and transaction management
- Schema versioning and migrations

**Examples:**
```python
# database/db_manager.py
class DatabaseManager:
    """SQLite connection and query management"""
    def get_connection(self):
        """Get database connection"""
        pass
    
    def execute_query(self, sql: str, params: tuple):
        """Execute SELECT query"""
        pass

# database/repositories/facility_repository.py
class FacilityRepository:
    """Data access for facilities (Repository pattern)"""
    def get_by_code(self, code: str) -> Facility:
        pass
    
    def list_all(self) -> List[Facility]:
        pass
```

**Rules:**
- ✅ DO: Put all database code here (connections, queries, schema)
- ✅ DO: Use Repository pattern for data access
- ✅ DO: Return Pydantic models from repositories (not raw dicts)
- ❌ DON'T: Put business logic here (calculations go in services/)
- ❌ DON'T: Import UI code (database is independent)

---

### 📁 `src/models/`
**Purpose:** Data models (Pydantic classes for type-safe data validation)

**What Goes Here:**
- `facility.py` - Facility model (code, name, capacity, etc.)
- `balance_result.py` - Balance calculation result model
- `measurement.py` - Measurement data model
- `flow_volume.py` - Flow volume model

**Why This Folder:**
- Type safety (validate data at boundaries)
- Serialization (JSON, dict conversion)
- Documentation (models document data structure)
- IDE support (autocomplete, type hints)

**Examples:**
```python
# models/facility.py
from pydantic import BaseModel, Field

class Facility(BaseModel):
    """Water storage facility definition"""
    code: str = Field(..., description="Facility code (e.g., 'UG2N')")
    name: str
    area: str
    capacity_m3: float
    pump_start_level: float = 0.70
    is_active: bool = True

# models/balance_result.py
class BalanceResult(BaseModel):
    """Water balance calculation result"""
    facility: str
    date: date
    fresh_inflows_m3: float
    total_outflows_m3: float
    closure_error_percent: float
    is_balanced: bool  # error < 5%
```

**Rules:**
- ✅ DO: Use Pydantic BaseModel for all data classes
- ✅ DO: Add Field() descriptions and validation
- ✅ DO: Use type hints (str, float, int, Optional[], List[])
- ✅ DO: Include example values in docstrings
- ❌ DON'T: Put business logic here (calculations go in services/)
- ❌ DON'T: Import PySide6 (models are framework-independent)

---

### 📁 `src/services/`
**Purpose:** Business logic (calculations, data processing, orchestration)

**What Goes Here:**
- `calculation_service.py` - Water balance calculations
- `balance_check_service.py` - Balance validation
- `flow_volume_loader.py` - Excel data loading
- `pump_transfer_service.py` - Pump transfer logic

**Why This Folder:**
- Business logic separate from UI (testable without rendering)
- Services can be called from UI, CLI, API, tests
- Easy to mock for unit testing
- Reusable across different interfaces

**Examples:**
```python
# services/calculation_service.py
class WaterBalanceCalculationService:
    """Calculate water balance (IMPROVED vs Tkinter)"""
    
    def __init__(self, db_manager, config_manager):
        self.db = db_manager
        self.config = config_manager
    
    def calculate_balance(self, facility: str, year: int, month: int) -> BalanceResult:
        """Calculate water balance with type-safe inputs/outputs"""
        # Business logic here
        pass

# services/balance_check_service.py
class BalanceCheckService:
    """Validate balance calculations"""
    
    def check_balance(self, result: BalanceResult) -> bool:
        """Check if balance is within acceptable error (<5%)"""
        return abs(result.closure_error_percent) < 5
```

**Rules:**
- ✅ DO: Put all business logic here (calculations, validation, orchestration)
- ✅ DO: Use dependency injection (pass db_manager, config in __init__)
- ✅ DO: Return Pydantic models (type-safe outputs)
- ✅ DO: Make services testable (no UI dependencies)
- ❌ DON'T: Import PySide6 here (services are UI-independent)
- ❌ DON'T: Put database queries here (use repositories)
- ❌ DON'T: Put UI logic here (use ui/dashboards/)

---

### 📁 `src/utils/`
**Purpose:** Utility functions (helpers, caching, formatting, Excel parsing)

**What Goes Here:**
- `caching.py` - Caching decorators
- `excel_helpers.py` - Excel file parsing utilities
- `formatting.py` - Data formatting (dates, numbers, units)
- `validators.py` - Input validation helpers

**Why This Folder:**
- Reusable helper functions
- Cross-cutting concerns (caching, formatting)
- No business logic (just utilities)

**Examples:**
```python
# utils/caching.py
from functools import wraps

def cached(ttl_seconds: int = 3600):
    """Decorator for caching function results with TTL"""
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Caching logic
            pass
        return wrapper
    return decorator

# utils/formatting.py
def format_volume(volume_m3: float) -> str:
    """Format volume in m³ with thousands separator"""
    return f"{volume_m3:,.1f} m³"
```

**Rules:**
- ✅ DO: Put reusable helper functions here
- ✅ DO: Keep functions small and focused
- ✅ DO: Add type hints and docstrings
- ❌ DON'T: Put business logic here (use services/)
- ❌ DON'T: Put database code here (use database/)
- ❌ DON'T: Import PySide6 (utils should be framework-independent)

---

## src/ui/ - User Interface

**Purpose:** All PySide6 user interface code (widgets, dialogs, dashboards, resources)

**Structure:**
```
src/ui/
├── main_window.py           # Main application window controller
├── application.py           # QApplication lifecycle
├── generated_ui_main_window.py  # Auto-generated from main_window.ui
│
├── components/              # Custom widgets (reusable UI components)
├── dashboards/              # Page controllers (9 dashboard pages)
├── designer/                # Qt Designer source files (.ui files)
│   ├── dashboards/          # Dashboard .ui files
│   └── dialogs/             # Dialog .ui files
├── dialogs/                 # Dialog controllers (settings, import, etc.)
├── resources/               # UI resources (icons, fonts, images)
│   ├── fonts/
│   ├── icons/
│   └── images/
└── styles/                  # Qt StyleSheets (CSS-like styling)
```

---

### 📁 `src/ui/components/`
**Purpose:** Custom reusable widgets (components used across multiple pages)

**What Goes Here:**
- `flow_diagram_scene.py` - Custom QGraphicsScene for flow diagrams
- `kpi_card_widget.py` - Reusable KPI display card
- `chart_widget.py` - matplotlib → PySide6 chart integration
- `water_table_widget.py` - Reusable data table widget

**Why This Folder:**
- Reusable UI components (DRY principle)
- Custom widgets not provided by PySide6
- Complex widgets with their own logic

**Examples:**
```python
# ui/components/flow_diagram_scene.py
from PySide6.QtWidgets import QGraphicsScene

class FlowDiagramScene(QGraphicsScene):
    """Custom graphics scene for water flow diagrams"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def load_diagram_json(self, json_path: str):
        """Load diagram from JSON file"""
        pass

# ui/components/kpi_card_widget.py
class KPICardWidget(QWidget):
    """Reusable KPI display card"""
    
    def set_value(self, value: float, unit: str):
        """Update KPI value and unit"""
        pass
```

**Rules:**
- ✅ DO: Create custom widgets for reuse across pages
- ✅ DO: Subclass PySide6 widgets (QWidget, QGraphicsScene, etc.)
- ✅ DO: Emit signals for user interactions
- ❌ DON'T: Put business logic here (use services/)
- ❌ DON'T: Put page-specific code here (use dashboards/)

---

### 📁 `src/ui/dashboards/`
**Purpose:** Page controllers (one controller per dashboard page)

**What Goes Here:**
- `dashboard_dashboard.py` - Dashboard page controller (class: DashboardPage)
- `analytics_dashboard.py` - Analytics page controller (class: AnalyticsPage)
- `flow_diagram_dashboard.py` - Flow Diagram page controller (class: FlowDiagramPage)
- `calculation_dashboard.py` - Calculation page controller (class: CalculationPage)
- `monitoring_dashboard.py` - Monitoring page controller (class: MonitoringPage)
- `storage_facilities_dashboard.py` - Storage Facilities page controller (class: StorageFacilitiesPage)
- `settings_dashboard.py` - Settings page controller (class: SettingsPage)
- `help_dashboard.py` - Help page controller (class: HelpPage)
- `about_dashboard.py` - About page controller (class: AboutPage)
- `generated_ui_*.py` - Auto-generated UI classes (DO NOT EDIT)

**Why This Folder:**
- One file per page (easy to find)
- Controllers separate from generated UI code
- Business logic delegated to services

**Examples:**
```python
# ui/dashboards/calculation_dashboard.py
from PySide6.QtWidgets import QWidget
from ui.dashboards.generated_ui_calculation import Ui_Form
from services.calculation_service import WaterBalanceCalculationService

class CalculationPage(QWidget):
    """Calculation dashboard page controller"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # Inject services
        self.service = WaterBalanceCalculationService(db, config)
        
        # Connect signals
        self.ui.btn_calculate.clicked.connect(self._on_calculate)
    
    def _on_calculate(self):
        """Handle calculate button click"""
        # Get inputs from UI
        facility = self.ui.input_facility.text()
        
        # Call service
        result = self.service.calculate_balance(facility, 2025, 3)
        
        # Update UI with result
        self.ui.label_result.setText(f"{result.closure_error_percent:.2f}%")
```

**File Naming:**
- Controller: `{page}_dashboard.py` (e.g., `calculation_dashboard.py`)
- Generated UI: `generated_ui_{page}.py` (e.g., `generated_ui_calculation.py`)
- Class name: `{Page}Page` (e.g., `CalculationPage`)

**Rules:**
- ✅ DO: Create one controller per page
- ✅ DO: Load generated UI in __init__ (self.ui.setupUi(self))
- ✅ DO: Inject services via __init__ or setters
- ✅ DO: Connect signals in __init__ or separate method
- ✅ DO: Delegate business logic to services
- ❌ DON'T: Put calculations in controllers (use services/)
- ❌ DON'T: Edit generated_ui_*.py files (regenerate from .ui)
- ❌ DON'T: Access database directly (use services/)

---

### 📁 `src/ui/designer/`
**Purpose:** Qt Designer source files (.ui XML files for visual design)

**Structure:**
```
designer/
├── dashboards/              # Dashboard .ui files
│   ├── dashboard.ui
│   ├── analytics.ui
│   ├── calculation.ui
│   └── ...
└── dialogs/                 # Dialog .ui files
    ├── settings.ui
    └── import.ui
```

**What Goes Here:**
- `.ui` files - Qt Designer XML (visual UI layout)
- Created/edited in Qt Designer application
- Compiled to Python: `pyside6-uic file.ui -o generated_ui_file.py`

**Why This Folder:**
- Visual UI design (drag-and-drop)
- Non-programmers can design UI
- Separation: design (.ui) vs logic (controller .py)

**Workflow:**
```bash
# 1. Design UI in Qt Designer → save as dashboards/calculation.ui
# 2. Compile to Python
pyside6-uic src/ui/designer/dashboards/calculation.ui -o src/ui/dashboards/generated_ui_calculation.py

# 3. Fix import in generated file
# Change: import resources_rc
# To:     import ui.resources.resources_rc

# 4. Use in controller
from ui.dashboards.generated_ui_calculation import Ui_Form
```

**Rules:**
- ✅ DO: Design UI here in Qt Designer
- ✅ DO: Organize by dashboards/ and dialogs/
- ✅ DO: Compile to Python after each edit
- ❌ DON'T: Commit .ui files to Git (design-time only)
- ❌ DON'T: Put logic in .ui files (use controllers)
- ❌ DON'T: Edit generated_ui_*.py manually (regenerate instead)

---

### 📁 `src/ui/dialogs/`
**Purpose:** Dialog controllers (settings, import, license, etc.)

**What Goes Here:**
- `settings_dialog.py` - Settings dialog controller
- `import_dialog.py` - Data import dialog controller
- `license_dialog.py` - License activation dialog controller
- `generated_ui_*.py` - Auto-generated from designer/dialogs/*.ui

**Why This Folder:**
- Dialogs are popup windows (not pages in main window)
- Different lifecycle from dashboards (show/exec/close)

**Examples:**
```python
# ui/dialogs/settings_dialog.py
from PySide6.QtWidgets import QDialog
from ui.dialogs.generated_ui_settings import Ui_Dialog

class SettingsDialog(QDialog):
    """Settings dialog controller"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Connect signals
        self.ui.btn_save.clicked.connect(self._on_save)
    
    def _on_save(self):
        """Save settings and close dialog"""
        # Get settings from UI
        # Save to config
        self.accept()  # Close dialog
```

**Rules:**
- ✅ DO: Subclass QDialog (not QWidget)
- ✅ DO: Use .exec() to show modal dialogs
- ✅ DO: Call accept() or reject() to close
- ❌ DON'T: Put business logic here (use services/)
- ❌ DON'T: Mix dialogs with dashboards (different lifecycle)

---

### 📁 `src/ui/resources/`
**Purpose:** UI resources (icons, fonts, images) compiled to Python

**Structure:**
```
resources/
├── fonts/                   # Custom fonts (.ttf, .otf)
├── icons/                   # Icons (.png, .svg)
├── images/                  # Images (.png, .jpg)
├── resources.qrc            # Qt resource collection file (XML)
└── resources_rc.py          # Compiled resource file (Python)
```

**What Goes Here:**
- `fonts/` - Custom fonts for UI
- `icons/` - Icons for buttons, toolbar, sidebar
- `images/` - Images for splash screen, about dialog
- `resources.qrc` - Qt resource file (lists all resources)
- `resources_rc.py` - Compiled Python file (import in main_window.py)

**Why This Folder:**
- Resources embedded in application (no external file dependencies)
- Qt resource system (`:/icons/...` paths)
- Single import to register all resources

**Workflow:**
```bash
# 1. Add icons/fonts/images to folders
# 2. Edit resources.qrc to list all files
# 3. Compile to Python
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py

# 4. Import in main_window.py (once)
import ui.resources.resources_rc  # Registers all resources

# 5. Use in UI files or code
icon = QIcon(":/icons/calculate.png")  # Note: :/ prefix
```

**resources.qrc Example:**
```xml
<RCC>
  <qresource prefix="icons">
    <file>icons/calculate.png</file>
    <file>icons/save.png</file>
  </qresource>
  <qresource prefix="fonts">
    <file>fonts/roboto.ttf</file>
  </qresource>
</RCC>
```

**Rules:**
- ✅ DO: Put all UI resources here (icons, fonts, images)
- ✅ DO: Compile resources.qrc to resources_rc.py
- ✅ DO: Import resources_rc.py in main_window.py
- ✅ DO: Use :/ prefix in paths (e.g., `:/icons/save.png`)
- ❌ DON'T: Put data files here (Excel, JSON → use data/ folder)
- ❌ DON'T: Commit resources_rc.py (regenerate from .qrc)
- ❌ DON'T: Reference external file paths in UI (embed in .qrc)

---

### 📁 `src/ui/styles/`
**Purpose:** Qt StyleSheets (CSS-like styling for consistent UI theme)

**What Goes Here:**
- `theme.py` - Color scheme, stylesheet definitions
- `dark_theme.qss` - Qt StyleSheet file (optional)

**Why This Folder:**
- Centralized styling (consistent colors, fonts, spacing)
- Easy to switch themes (light/dark)
- Separation: styling vs layout vs logic

**Examples:**
```python
# ui/styles/theme.py
STYLESHEET = """
QMainWindow {
    background-color: #F5F6F7;
}

QPushButton {
    background-color: #0066CC;
    color: white;
    border-radius: 4px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #0052A3;
}
"""

# Usage in main.py
from ui.styles.theme import STYLESHEET
app.setStyleSheet(STYLESHEET)
```

**Rules:**
- ✅ DO: Define color scheme here
- ✅ DO: Use Qt StyleSheet syntax (CSS-like)
- ✅ DO: Apply in main.py or main_window.py
- ❌ DON'T: Set styles individually in widgets (use stylesheet)
- ❌ DON'T: Hardcode colors in UI files (use theme)

---

## tests/ - Testing

**Purpose:** All unit tests and integration tests

**Structure:**
```
tests/
├── conftest.py              # pytest fixtures (shared test setup)
├── test_models/             # Tests for Pydantic models
│   └── test_facility.py
├── test_services/           # Tests for business logic services
│   ├── test_calculation_service.py
│   ├── test_balance_check_service.py
│   └── test_flow_volume_loader.py
└── test_ui/                 # Tests for UI components
    └── test_main_window.py
```

**What Goes Here:**
- `conftest.py` - pytest fixtures (mock database, sample data)
- `test_models/` - Test Pydantic model validation
- `test_services/` - Test business logic (most important!)
- `test_ui/` - Test UI interactions (optional, use mocking)

**Why This Folder:**
- Tests mirror src/ structure
- Easy to find tests for each module
- pytest auto-discovery

**Examples:**
```python
# tests/test_services/test_calculation_service.py
import pytest
from services.calculation_service import WaterBalanceCalculationService
from models.balance_result import BalanceResult

@pytest.fixture
def service():
    """Create service with mocked dependencies"""
    mock_db = Mock()
    mock_config = Mock()
    return WaterBalanceCalculationService(mock_db, mock_config)

def test_calculate_balance_ug2n_march_2025(service):
    """Test balance calculation for UG2N, March 2025"""
    result = service.calculate_balance('UG2N', 2025, 3)
    
    assert isinstance(result, BalanceResult)
    assert result.facility == 'UG2N'
    assert result.closure_error_percent < 5  # Good closure

# tests/conftest.py
@pytest.fixture
def sample_facility():
    """Sample facility for tests"""
    return Facility(
        code='UG2N',
        name='UG2 North',
        area='UG2',
        capacity_m3=150000
    )
```

**Rules:**
- ✅ DO: Write tests for all services (most important)
- ✅ DO: Use pytest fixtures for setup (conftest.py)
- ✅ DO: Mock dependencies (databases, files)
- ✅ DO: Test edge cases and error conditions
- ❌ DON'T: Test generated UI code (focus on logic)
- ❌ DON'T: Test framework code (PySide6, pandas)

---

## Quick Reference Table

| Folder | Purpose | What Goes Here | What DOESN'T Go Here |
|--------|---------|----------------|---------------------|
| **config/** | Configuration | YAML config files | Code, data files |
| **data/** | Runtime data | Excel, JSON, SQLite db, diagrams | Source code, UI resources |
| **Docs/** | Documentation | .md files | Code, data |
| **src/core/** | Infrastructure | Logging, config, lifecycle | Business logic, UI |
| **src/database/** | Data access | SQLite, queries, repositories | Business logic, UI |
| **src/models/** | Data models | Pydantic classes | Business logic, UI |
| **src/services/** | Business logic | Calculations, validation | UI code, database queries |
| **src/utils/** | Utilities | Helpers, caching, formatting | Business logic, UI |
| **src/ui/components/** | Custom widgets | Reusable UI components | Page-specific code |
| **src/ui/dashboards/** | Page controllers | Dashboard page classes | Business logic, dialogs |
| **src/ui/designer/** | Qt Designer files | .ui XML files | Python code |
| **src/ui/dialogs/** | Dialog controllers | Popup dialog classes | Dashboard pages |
| **src/ui/resources/** | UI resources | Icons, fonts, images | Data files, Excel |
| **src/ui/styles/** | Styling | Qt StyleSheets, themes | Layout, logic |
| **tests/** | Tests | Unit tests, fixtures | Production code |

---

## Decision Flow: Where Does This File Go?

### "I have a new Python file. Where do I put it?"

**Is it a data model (Pydantic class)?**
→ `src/models/`

**Is it business logic (calculations, validation)?**
→ `src/services/`

**Is it database code (queries, schema)?**
→ `src/database/`

**Is it a UI page/dashboard?**
→ `src/ui/dashboards/`

**Is it a popup dialog?**
→ `src/ui/dialogs/`

**Is it a custom widget (reusable component)?**
→ `src/ui/components/`

**Is it a utility/helper function?**
→ `src/utils/`

**Is it infrastructure (logging, config)?**
→ `src/core/`

**Is it a test?**
→ `tests/test_*`

---

### "I have a data file. Where do I put it?"

**Is it configuration (YAML)?**
→ `config/`

**Is it runtime data (Excel, JSON, database)?**
→ `data/`

**Is it a flow diagram (JSON)?**
→ `data/diagrams/`

**Is it a UI resource (icon, font, image)?**
→ `src/ui/resources/fonts/`, `icons/`, or `images/`

**Is it documentation?**
→ `Docs/`

---

## Common Mistakes to Avoid

❌ **Don't put business logic in UI controllers**
```python
# BAD: Calculation in dashboard controller
class CalculationPage(QWidget):
    def _on_calculate(self):
        result = inflows - outflows - storage_change  # ❌ Logic in UI!
        self.ui.label.setText(f"{result}")

# GOOD: Delegate to service
class CalculationPage(QWidget):
    def _on_calculate(self):
        result = self.service.calculate_balance(facility, month, year)  # ✅
        self.ui.label.setText(f"{result.closure_error_percent}%")
```

❌ **Don't put database queries in services**
```python
# BAD: SQL in service
class CalculationService:
    def calculate(self):
        conn = sqlite3.connect('db.db')  # ❌ Direct database access!
        cursor.execute("SELECT * FROM facilities")

# GOOD: Use repository
class CalculationService:
    def __init__(self, facility_repo):
        self.facility_repo = facility_repo  # ✅ Inject repository
    
    def calculate(self):
        facilities = self.facility_repo.list_all()
```

❌ **Don't put UI resources in data/ folder**
```python
# BAD: Icon in data/ folder
icon = QIcon("data/icons/save.png")  # ❌ Wrong folder!

# GOOD: Icon in resources/
icon = QIcon(":/icons/save.png")  # ✅ Qt resource system
```

❌ **Don't put data files in resources/ folder**
```python
# BAD: Excel in resources/
df = pd.read_excel(":/data/template.xlsx")  # ❌ Resources are for UI!

# GOOD: Excel in data/
df = pd.read_excel("data/template.xlsx")  # ✅ Correct location
```

---

## Best Practices Summary

### ✅ DO
- Keep UI separate from business logic (MVC pattern)
- Use dependency injection (pass services to controllers)
- Return Pydantic models from services (type safety)
- Use Repository pattern for database access
- Write tests for services (most important)
- Organize files by purpose (models/, services/, ui/)

### ❌ DON'T
- Mix UI and business logic in same file
- Put database queries in services (use repositories)
- Put business logic in UI controllers (use services)
- Edit generated_ui_*.py files (regenerate from .ui)
- Hardcode paths (use config/)
- Skip tests for services (critical for correctness)

---

## Verification Checklist

Before creating a new file, ask:

- [ ] **Purpose clear?** (What does this file do?)
- [ ] **Correct folder?** (Check decision flow above)
- [ ] **Dependencies minimal?** (Does it import from correct layers?)
- [ ] **Reusable?** (Can this be used elsewhere?)
- [ ] **Testable?** (Can I write unit tests for this?)
- [ ] **Named correctly?** (Follows naming conventions?)

---

## Summary

Your directory structure is **CORRECT and PRODUCTION-READY**:

✅ **Clear separation of concerns** (UI ≠ Logic ≠ Data)
✅ **Scalable** (Each layer can grow independently)
✅ **Testable** (Services independent of UI)
✅ **Maintainable** (Easy to find and modify code)
✅ **Professional** (Industry-standard organization)

**You're ready to start backend development with confidence!**

When in doubt, refer to:
- This guide for folder purposes
- `BACKEND_IMPLEMENTATION_ROADMAP.md` for implementation steps
- `ARCHITECTURE_VERIFICATION.md` for architecture details

---

**Last Updated:** January 29, 2026  
**Status:** ✅ Structure Verified and Documented
