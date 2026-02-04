# Copilot Instructions - PySide6 Water Balance Dashboard

## 🎯 Project Context

**Dashboard Waterbalance** is a professional PySide6 water balance management application with interactive flow diagram editing, real-time data visualization, and comprehensive facility management.

**Current Status**: Phase 4 Complete (80% done) - Flow diagram drawing mode implemented with orthogonal routing and real-time edge creation

**Architecture**: Clean MVC separation with service layer, custom QGraphicsItems, lazy-loaded models, and Qt Designer integration

---

## 📚 Key Architecture Patterns

### Service Layer (Business Logic)
**Pattern**: UI → Service → Repository → Database
```python
# services/storage_facility_service.py
class StorageFacilityService:
    """Business logic layer with validation, error handling, logging"""
    def get_facilities(self, filters=None) -> List[Dict]:
        # Validate → Call Repository → Transform data → Return
```
**All business logic goes in services/** Never in UI controllers.

### Lazy Loading Models
**Pattern**: QAbstractTableModel with on-demand data()
```python
# ui/models/storage_facilities_model.py
class StorageFacilitiesModel(QAbstractTableModel):
    """Lazy loads 500+ facilities - only visible cells rendered"""
    def data(self, index, role):  # Called ONLY for visible cells
        return self._facilities_data[index.row()][self._column_keys[index.column()]]
```
**Performance**: 500ms → 50ms for 500 facilities

### Custom QGraphicsItems
**Pattern**: Node/Edge items with 17 anchor points for flow diagrams
```python
# ui/components/graphics/node_graphics_item.py
class NodeGraphicsItem(QGraphicsEllipseItem):
    """Water component nodes with 17 snapping points"""
    def get_anchor_positions(self) -> List[QPointF]:
        # Returns N, NE, E, SE, S, SW, W, NW, + intermediates
```
**See**: `flow_diagram_page.py` (2,463 lines) for complete implementation

---

## ❌ CRITICAL: No Summary .md Files (Unless Explicitly Requested)

**DEFAULT BEHAVIOR:**
- ❌ **DO NOT** create `.md` files after completing work
- ❌ **DO NOT** create progress/summary documentation
- ❌ **DO NOT** create "X is complete" docs automatically
- ✅ **ONLY** create `.md` files when user explicitly says "create a doc" or "document this"

**When User DOES Request Documentation:**
1. Check if content belongs in existing `Docs/` subfolder
2. Update existing file instead of creating new one
3. Place in correct folder: Features→`04-FEATURES/`, Architecture→`01-ARCHITECTURE/`, etc.
4. Never create `.md` files in project root (only `README.md` allowed)

**Enforcement:** Root folder is PRISTINE - only `.github/`, `src/`, `tests/`, `config/`, `data/`, `Docs/`, `logs/`, `.venv/`, and config files allowed.

---

## 🚀 Critical Developer Workflows

### UI Compilation (Qt Designer → Python)
**Always compile .ui files after editing in Qt Designer**:
```powershell
# Single file
pyside6-uic src/ui/designer/dashboards/analytics.ui -o src/ui/dashboards/generated_ui_analytics.py

# All dashboards at once (use scripts/compile_ui.ps1)
Get-ChildItem src/ui/designer/dashboards/*.ui | ForEach-Object {
    pyside6-uic $_.FullName -o "src/ui/dashboards/generated_ui_$($_.BaseName).py"
}

# Fix imports: Change "import resources_rc" → "import ui.resources.resources_rc"
```
**Never commit .ui files** - only commit generated .py files

### Running Tests
```powershell
# Phase 4 drawing mode tests
python tests/test_phase4_drawing_mode.py

# All tests with coverage
pytest tests/ -v --cov=src

# Specific test
pytest tests/test_storage_facilities_backend.py -v
```

### Key Commands
```powershell
# Run app
.venv\Scripts\python src/main.py

# Compile resources (icons, images)
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py

# Check diagram JSON structure
python scripts/check_diagram.py data/diagrams/ug2_north_decline.json
```

---

## 🏗️ Project Structure & Conventions

```
src/
├── ui/                           # All PySide6 UI code
│   ├── dashboards/              # Page controllers (dashboard_dashboard.py, flow_diagram_page.py)
│   │   └── generated_ui_*.py   # Compiled from .ui files (COMMIT THESE)
│   ├── dialogs/                 # Modal dialogs (add_edit_node_dialog.py, etc.)
│   ├── components/              # Reusable widgets (splash_screen.py, kpi_card.py)
│   │   └── graphics/           # Custom QGraphicsItems (node_graphics_item.py, edge_graphics_item.py)
│   ├── models/                  # QAbstractTableModel subclasses (lazy loading)
│   ├── designer/                # Qt Designer .ui files (DO NOT COMMIT)
│   └── resources/               # Icons, images, compiled resources_rc.py
├── services/                    # Business logic layer
│   ├── storage_facility_service.py
│   ├── monthly_parameters_service.py
│   └── recirculation_loader.py
├── database/                    # SQLite database access
│   └── repositories/           # Data access layer
├── models/                      # Pydantic data models
└── core/                        # App infrastructure (logging, config)

data/diagrams/                   # Flow diagram JSON files
scripts/                         # Utility scripts (compile_ui.ps1, check_diagram.py)
tests/                           # pytest tests
```

### Naming Conventions
- **Controllers**: `{name}_dashboard.py` or `{name}_page.py` (e.g., `flow_diagram_page.py`)
- **Generated UI**: `generated_ui_{name}.py` (e.g., `generated_ui_analytics.py`)
- **Services**: `{entity}_service.py` (e.g., `storage_facility_service.py`)
- **Models**: `{entity}_model.py` (lazy table models) or just `{entity}.py` (Pydantic)
- **Dialogs**: `{action}_{entity}_dialog.py` (e.g., `add_edit_node_dialog.py`)

### Import Pattern (CRITICAL)
Every file in `src/` must add parent to path:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
# Then: from ui.models import ..., from services import ...
```

---

## 📋 Adding a New Dashboard Page (Recipe)

Follow this 5-step workflow:

### 1. Design UI (Qt Designer - optional)
If using Qt Designer, create `.ui` file in `src/ui/designer/dashboards/analytics.ui`
**OR skip to step 2 if building UI programmatically**

### 2. Create Controller
```python
# src/ui/dashboards/analytics_dashboard.py
from PySide6.QtWidgets import QWidget, QVBoxLayout
from ui.dashboards.generated_ui_analytics import Ui_Form  # If using Designer

class AnalyticsPage(QWidget):
    """Analytics & Trends page (KPI CHARTS & TRENDS)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()  # If using Designer
        self.ui.setupUi(self)
        # OR build layout programmatically if no .ui file
```

### 3. Compile UI (if using Designer)
```powershell
pyside6-uic src/ui/designer/dashboards/analytics.ui -o src/ui/dashboards/generated_ui_analytics.py
# Fix import: Change "import resources_rc" → "import ui.resources.resources_rc"
```

### 4. Wire Business Logic
```python
from services.storage_facility_service import StorageFacilityService

class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.service = StorageFacilityService()  # Inject service
        self._load_data()
    
    def _load_data(self):
        facilities = self.service.get_facilities()
        # Update UI with data
```

### 5. Mount in MainWindow
Edit `src/ui/main_window.py`, add to `_mount_pages()`:
```python
from ui.dashboards.analytics_dashboard import AnalyticsPage

analytics_page = AnalyticsPage()
self.ui.stackedWidget.addWidget(analytics_page)
self.ui.analytics_trends = analytics_page  # Store reference
```

### 6. Connect Navigation
In `main_window.py`, wire button to page:
```python
self.ui.analytics_1.clicked.connect(lambda: self._show_page(self.ui.analytics_trends))
```

---

## 🧩 PySide6 Modules Quick Reference

**Currently Using:**
- ✅ **QtCore** - Signals/slots, timers, animations
- ✅ **QtWidgets** - All UI components
- ✅ **QtGui** - Graphics, fonts, painters

**Available (Phase 5+):**
- 🎨 **QtCharts** - Native charts (replace matplotlib) → See [PYSIDE6_MODULES_GUIDE.md](../Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md#priority-1-qtcharts-phase-5---analytics-dashboard)
- 🖼️ **QtSvg/QtSvgWidgets** - Scalable flow diagrams → See [PYSIDE6_MODULES_GUIDE.md](../Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md#priority-2-qtsvg--qtsvgwidgets-phase-5---flow-diagram-enhancement)
- 🖨️ **QtPrintSupport** - PDF export → See [PYSIDE6_MODULES_GUIDE.md](../Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md#priority-3-qtprintsupport-phase-6---reporting)
- 🗄️ **QtSql** - Database models → See [PYSIDE6_MODULES_GUIDE.md](../Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md#priority-4-qtsql-phase-7---database-layer-upgrade)

**Not Needed:** QtQml, QtQuick, QtDesigner (design-time only), QtDBus (Linux), QtOpenGL

**→ Full guide:** [Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md](../Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md)

---

## 🔧 Common Patterns & Solutions

### Signal/Slot Connection
```python
# Connect button click to method
self.ui.btn_save.clicked.connect(self._on_save_clicked)

# Emit signal from service
class FacilityService(QObject):
    data_changed = Signal()
    
    def update_facility(self, code):
        # ... update logic ...
        self.data_changed.emit()  # Notify listeners
```

### Loading Data from Service
```python
from services.storage_facility_service import StorageFacilityService

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = StorageFacilityService()
        self._load_data()
    
    def _load_data(self):
        try:
            facilities = self.service.get_facilities()
            self._populate_table(facilities)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
```

### Lazy Model for Large Tables
```python
from ui.models.storage_facilities_model import StorageFacilitiesModel

# Create model
model = StorageFacilitiesModel()
model.setFacilitiesData(facilities_list)

# Set on view (auto-renders only visible cells)
self.ui.table_facilities.setModel(model)
```

### Custom Graphics Items (Flow Diagrams)
```python
from ui.components.graphics.node_graphics_item import NodeGraphicsItem

# Create node
node = NodeGraphicsItem(node_id="UG2N", label="Underground 2 North", rect=QRectF(0, 0, 100, 60))
scene.addItem(node)

# Get anchor points for edge connections
anchors = node.get_anchor_positions()  # 17 snapping points
```

---

## ⚠️ Common Pitfalls

1. **Forgetting sys.path shim**: Add parent to path in every `src/` file
2. **Importing .ui files**: Never import .ui directly - compile to .py first
3. **resource_rc import**: Fix to `import ui.resources.resources_rc` after compilation
4. **Direct business logic in UI**: Use services layer instead
5. **Blocking UI thread**: Use QThread or signals for long operations
6. **Not committing generated_ui_*.py**: These ARE source files (commit them)
7. **Committing .ui files**: Design-time only (DO NOT commit)
8. **Missing data() implementation**: Lazy models need proper data() method

---

## 📚 Documentation Structure

```
Docs/
├── 00-GETTING_STARTED/          ← Quick starts, phase briefs
├── 01-ARCHITECTURE/             ← System design, patterns
├── 02-BACKEND/                  ← Services, repositories
├── 03-FRONTEND/                 ← UI components, widgets
├── 04-FEATURES/                 ← Feature implementations
│   ├── Excel_Integration/
│   └── Flow_Diagram/
├── 05-SETUP_AND_OPERATIONS/     ← Installation, admin
├── 06-REFERENCE/                ← Style guides, conventions
│   └── PYSIDE6_MODULES_GUIDE.md ← QtCharts, QtSvg, etc.
└── 07-ANALYSIS_AND_PLANNING/    ← Roadmaps, analysis
    └── Phase_Completions/
```

**When you need context:** Check the appropriate folder first before asking.

---

## 🗂️ Repository Hygiene (STRICT)

### 📝 Markdown File Policy - MINIMIZE DURING DEVELOPMENT

**CRITICAL RULE**: Do NOT create new `.md` files casually. Check existing documentation first.

**Before Creating Any New `.md` File:**
1. ✅ Search existing `Docs/` folder for related topics
2. ✅ Check if content can be added to existing files
3. ✅ Review [Docs/INDEX.md](Docs/INDEX.md) or [Docs/DOCUMENTATION_INDEX.md](Docs/DOCUMENTATION_INDEX.md) for consolidated docs
4. ✅ Ask: "Does this NEED a new file, or should it update an existing one?"

**What NOT to Do:**
- ❌ Create one `.md` file per feature (consolidate into feature index)
- ❌ Create analysis/summary `.md` files during development (write to `Docs/` only if persistent value)
- ❌ Create `.md` files for temporary outputs or verification (use temp locations, delete after)
- ❌ Create duplicate documentation (update existing instead)
- ❌ Create `.md` files in project root (only: README.md, PHASE_*.md, START_*.md for critical milestones)

**What TO Do:**
- ✅ Update existing documentation files
- ✅ Add to [Docs/INDEX.md](Docs/INDEX.md) for new features
- ✅ Consolidate related docs into single files
- ✅ Keep `.md` files concise and focused
- ✅ Use existing `.md` structure and naming conventions

**Guideline:**
- **During active development**: Inline comments + code documentation (NO new `.md` files)
- **After feature completion**: One consolidated `.md` in `Docs/` folder if persistent value
- **For temporary analysis**: Use temp locations, delete after use to avoid clutter
- **For persistent knowledge**: Add to existing guides or [Docs/INDEX.md](Docs/INDEX.md)

**Root Folder Policy**:
- Keep root clean - only essential files
- Only: `.github/`, `src/`, `tests/`, `config/`, `data/`, `Docs/`, `logs/`, `.venv/`, config files
- No temporary `.md` files in root

---

## 📝 Code Style & Conventions

1. **Imports**: Group stdlib, third-party, local
2. **Type hints**: Use on all function signatures
3. **Docstrings**: Module, class, and public method docstrings (Google style)
4. **Naming**:
   - Classes: `PascalCase` (e.g., `CalculationService`)
   - Functions: `snake_case` (e.g., `calculate_balance`)
   - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
   - UI slots: `_on_<event>` (e.g., `_on_calculate_clicked`)
5. **Qt Conventions**:
   - Use `Qt.CursorShape.WaitCursor` for blocking operations
   - Emit signals for long operations (avoid freezing UI)
   - Use layouts instead of manual positioning

---

## � PySide6 Reference Documentation (CRITICAL)

### **Comprehensive PySide6 Book (730 Pages)**
**Location**: `Docs/pyside6/create-gui-applications-pyside6.pdf`  
**Skill Reference**: `.github/skills/pyside6/SKILL.md`

When developing ANY PySide6 feature, reference the appropriate chapter:

| Topic | Chapter | Pages |
|-------|---------|-------|
| **Widgets** (QLabel, QComboBox, QListWidget, etc.) | 2.3 | 28-55 |
| **Layouts** (QVBoxLayout, QGridLayout, QStackedLayout) | 2.4 | 56-85 |
| **Signals & Slots** | 2.2 | 18-27 |
| **Dialogs** (QMessageBox, file dialogs) | 2.6 | 107-149 |
| **Qt Designer** (.ui files, resources) | 3 | 168-199 |
| **Theming & QSS** (styling, dark mode, icons) | 4 | 200-265 |
| **Model View Controller** (QTableView, QAbstractTableModel) | 5 | 266-357 |
| **Custom Widgets** (QPainter, paintEvent) | 6 | 358-422 |
| **Threading** (QThread, QRunnable, QThreadPool) | 7 | 423-522 |
| **Plotting** (PyQtGraph, Matplotlib) | 8 | 523-558 |
| **Timers & Advanced Features** | 9 | 559-603 |
| **Packaging** (PyInstaller, installers) | 10 | 605-652 |

**To read specific pages from PDF:**
```python
import pdfplumber
with pdfplumber.open('Docs/pyside6/create-gui-applications-pyside6.pdf') as pdf:
    text = pdf.pages[99].extract_text()  # Page 100 (0-indexed)
```

---

## 🔗 References

### **Core Documentation**
- **PySide6 Book (PDF)**: `Docs/pyside6/create-gui-applications-pyside6.pdf` - **PRIMARY REFERENCE** (730 pages of examples and best practices)
- **PySide6 Skill**: `.github/skills/pyside6/SKILL.md` - Table of contents and quick reference
- **PySide6 Official Docs**: https://doc.qt.io/qtforpython-6/
- **Qt Designer Guide**: https://doc.qt.io/qt-6/qtdesigner-manual.html
- **Pydantic Docs**: https://docs.pydantic.dev/latest/
- **Tkinter Source**: `../tkinter-legacy/` (for business logic reference)

### **Project-Specific Guides**
- **PySide6 Modules Guide**: [Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md](../Docs/06-REFERENCE/PYSIDE6_MODULES_GUIDE.md) - Comprehensive reference for QtCharts, QtSvg, QtPrintSupport, QtSql integration (Phase 5+)
- **Python Style**: [.github/instructions/python.instructions.md](instructions/python.instructions.md) - PEP 8, type hints, docstrings
- **Performance**: [.github/instructions/performance-optimization.instructions.md](instructions/performance-optimization.instructions.md) - Frontend/backend optimization

### **GitHub Skills (AI Assistant Reference)**
- **PDF Skill**: `.github/skills/pdf/SKILL.md` - How to read/extract from PDF documentation
- **PySide6 Skill**: `.github/skills/pyside6/SKILL.md` - Full table of contents for the 730-page PySide6 book
- **Frontend Design Skill**: `.github/skills/frontend-design/SKILL.md` - UI/UX design best practices

---

**Last updated**: February 2, 2026  
**Status**: Phase 4 complete, Phase 5 ready (Analytics Dashboard + QtCharts integration)
