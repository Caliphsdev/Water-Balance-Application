# Qt Designer UI Files - Complete List

**Created:** January 25, 2026  
**Total Files:** 17 .ui files ready for Qt Designer

---

## 📋 DESIGN CHECKLIST

### ✅ Main Window (1 file)
- [ ] **main_window.ui** - Application container
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\main_window.py`
  - **Layout:** Sidebar (left) + Content area (center) + Status bar (bottom)
  - **Components Needed:**
    - QToolBar (top): Menu button, app title, quick actions
    - QListWidget (left sidebar): Module navigation (Dashboard, Calculations, Analytics, etc.)
    - QStackedWidget (center): Dynamic content area for loading dashboards
    - QStatusBar (bottom): License status, operation feedback, progress bar
  - **Estimated Time:** 2-3 hours

---

### 📊 Dashboards (6 files - Main Content Modules)

- [ ] **calculations_dashboard.ui** - Water balance calculations
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\calculations.py` (3499 lines)
  - **Layout:** Month/year selectors (top) + Tabbed results (center)
  - **Components Needed:**
    - QComboBox: Month selector
    - QSpinBox: Year selector
    - QPushButton: "Calculate Balance" button
    - QTabWidget: Results tabs (Summary, Area Breakdown, Legacy)
    - QTableWidget: Balance results display
    - QLabel: KPI cards (closure error %, total inflows, outflows)
  - **Estimated Time:** 3-4 hours

- [ ] **analytics_dashboard.ui** - KPI analytics and trends
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\analytics_dashboard.py`
  - **Layout:** KPI cards (top) + Trend charts (bottom)
  - **Components Needed:**
    - QFrame containers for KPI cards
    - QLabel: Metric values and trends
    - QWidget: Placeholder for matplotlib charts
  - **Estimated Time:** 2-3 hours

- [ ] **flow_diagram_dashboard.ui** - Interactive flow diagrams
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\flow_diagram_dashboard.py`
  - **Layout:** Area selector (top) + Diagram canvas (center) + Controls (right)
  - **Components Needed:**
    - QComboBox: Area selection (UG2N, UG2S, OLDTSF, etc.)
    - QWidget: Custom widget placeholder for flow diagram rendering
    - QPushButton: Reload, Export buttons
  - **Estimated Time:** 2-3 hours

- [ ] **charts_dashboard.ui** - Charts and visualizations
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\charts_dashboard.py`
  - **Layout:** Chart type selector (top) + Chart area (center)
  - **Components Needed:**
    - QComboBox: Chart type selection
    - QWidget: Matplotlib integration placeholder
    - QGroupBox: Chart settings
  - **Estimated Time:** 1-2 hours

- [ ] **kpi_dashboard.ui** - Key performance indicators
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\kpi_dashboard.py`
  - **Layout:** Grid of KPI cards
  - **Components Needed:**
    - QGridLayout: KPI card grid (3x3 or 4x3)
    - QFrame: Individual KPI cards
    - QLabel: KPI values, icons, trends
  - **Estimated Time:** 1-2 hours

- [ ] **monitoring_dashboard.ui** - Real-time monitoring
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\monitoring_dashboard.py`
  - **Layout:** Alert list (left) + Status widgets (right)
  - **Components Needed:**
    - QListWidget: Alert/event list
    - QLabel: Status indicators
    - QPushButton: Acknowledge, Dismiss buttons
  - **Estimated Time:** 2 hours

---

### 🗨️ Dialogs (6 files - Popup Windows)

- [ ] **settings_dialog.ui** - Application configuration
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\settings.py` (1612 lines)
  - **Layout:** Tabbed settings interface
  - **Components Needed:**
    - QTabWidget: Settings categories (General, Excel Paths, Features, Database)
    - QLineEdit: File paths
    - QPushButton: Browse buttons
    - QCheckBox: Feature flags
    - QDialogButtonBox: OK, Cancel, Apply
  - **Estimated Time:** 3-4 hours

- [ ] **license_dialog.ui** - License activation
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\license_dialog.py`
  - **Layout:** License key entry + Status display
  - **Components Needed:**
    - QLineEdit: License key input
    - QPushButton: Activate button
    - QLabel: Status message, license details
    - QDialogButtonBox: Close button
  - **Estimated Time:** 1 hour

- [ ] **data_import_dialog.ui** - Excel data import
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\data_import.py`
  - **Layout:** File selector + Import options + Progress
  - **Components Needed:**
    - QLineEdit: File path
    - QPushButton: Browse, Import buttons
    - QProgressBar: Import progress
    - QTextEdit: Import log/results
  - **Estimated Time:** 2 hours

- [ ] **excel_config_dialog.ui** - Excel file path configuration
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\excel_config_dialog.py`
  - **Layout:** File path inputs + Validation
  - **Components Needed:**
    - QLineEdit: Multiple file paths
    - QPushButton: Browse buttons
    - QLabel: Validation status
    - QDialogButtonBox: Save, Cancel
  - **Estimated Time:** 1 hour

- [ ] **pump_transfer_confirm_dialog.ui** - Pump transfer confirmation
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\pump_transfer_confirm_dialog.py`
  - **Layout:** Transfer details + Confirmation buttons
  - **Components Needed:**
    - QLabel: Source/destination facility names
    - QLabel: Transfer volume
    - QDialogButtonBox: Confirm, Cancel
  - **Estimated Time:** 30 minutes

- [ ] **area_exclusion_dialog.ui** - Area exclusion settings
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\area_exclusion_dialog.py`
  - **Layout:** Area checklist
  - **Components Needed:**
    - QListWidget with checkboxes: Mining areas
    - QDialogButtonBox: Save, Cancel
  - **Estimated Time:** 30 minutes

---

### 📄 Specialized Views (4 files)

- [ ] **measurements_view.ui** - Measurement data entry
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\measurements.py`
  - **Layout:** Data grid for measurements
  - **Components Needed:**
    - QTableWidget: Measurement data grid
    - QPushButton: Add, Edit, Delete
    - QDateEdit: Date selector
  - **Estimated Time:** 2 hours

- [ ] **storage_facilities_view.ui** - Storage facility management
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\storage_facilities.py`
  - **Layout:** Facility list + Details panel
  - **Components Needed:**
    - QListWidget: Facilities
    - QFormLayout: Facility details (capacity, type, etc.)
    - QPushButton: Add, Edit, Delete
  - **Estimated Time:** 2 hours

- [ ] **reports_view.ui** - Report generation
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\reports.py`
  - **Layout:** Report options + Preview
  - **Components Needed:**
    - QComboBox: Report type selection
    - QDateEdit: Date range selectors
    - QPushButton: Generate, Export buttons
    - QTextEdit: Report preview
  - **Estimated Time:** 1-2 hours

- [ ] **help_view.ui** - Help and documentation
  - **Tkinter Source:** `C:\PROJECTS\Water-Balance-Application\src\ui\help_documentation.py`
  - **Layout:** Help topics + Content area
  - **Components Needed:**
    - QTreeWidget: Help topics navigation
    - QTextBrowser: Help content display
  - **Estimated Time:** 1 hour

---

## 🚀 WORKFLOW FOR EACH .UI FILE

### Step 1: Open in Qt Designer
```bash
# Option 1: Standalone Qt Designer (recommended)
designer src\ui\designer\main_window.ui

# Option 2: Qt Creator
# File > Open File > Select .ui file
```

### Step 2: Design the UI
- Drag widgets from Widget Box (left panel)
- Arrange layout with Layout tools (toolbar)
- Set properties (right panel)
- Connect signals/slots if needed (F4)

### Step 3: Save & Compile to Python
```bash
# After saving .ui file, compile to Python:
pyside6-uic src\ui\designer\main_window.ui -o src\ui\generated_ui_main_window.py
```

### Step 4: Import in Controller
```python
# src/ui/main_window.py
from ui.generated_ui_main_window import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
```

---

## 📊 DESIGN PRIORITY ORDER

**Phase 1 (Critical - Week 1):**
1. ✅ main_window.ui - Application shell
2. ✅ calculations_dashboard.ui - Core feature
3. ✅ settings_dialog.ui - Configuration

**Phase 2 (Important - Week 2):**
4. flow_diagram_dashboard.ui - Visual feature
5. analytics_dashboard.ui - KPI display
6. license_dialog.ui - Critical for deployment

**Phase 3 (Nice to Have - Week 3):**
7-17. Remaining dashboards, dialogs, views

---

## 🎯 ESTIMATED TOTAL DESIGN TIME

- **Main Window:** 2-3 hours
- **Dashboards (6):** 10-15 hours
- **Dialogs (6):** 8-10 hours
- **Views (4):** 6-8 hours

**Total: 26-36 hours** (3-5 days of focused UI design work)

---

## 📝 DESIGN TIPS

1. **Use Layouts:** Always use layouts (QVBoxLayout, QHBoxLayout, QGridLayout) - never absolute positioning
2. **Responsive Design:** Set minimum/maximum sizes on widgets to ensure responsiveness
3. **Naming Convention:** Use descriptive object names (btnCalculate, comboMonth, tableResults)
4. **Stylesheets:** Add basic styles in Designer, refine in Python code
5. **Placeholders:** Use QWidget placeholders for custom components (flow diagrams, charts)

---

## ✅ SUCCESS CRITERIA

Each .ui file is complete when:
- [ ] All widgets added and properly named
- [ ] Layouts applied (no absolute positioning)
- [ ] Compiles to Python without errors
- [ ] Controller can load and display the UI
- [ ] Responsive (resizes properly)

---

**Next Step:** Open Qt Designer and start with `main_window.ui`!
