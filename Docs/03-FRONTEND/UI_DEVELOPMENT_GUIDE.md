# UI Development Guide - PySide6 Dashboard Pattern

## Directory Structure

```
src/ui/
├── designer/                    # Qt Designer source files (.ui) - LOCAL ONLY
│   ├── main_window.ui          # Main app shell
│   ├── dashboards/             # Dashboard page designs
│   │   ├── calculations.ui
│   │   ├── flow_diagram.ui
│   │   ├── analytics.ui
│   │   └── settings.ui
│   └── dialogs/                # Pop-up dialog designs
│       ├── data_import.ui
│       ├── settings_advanced.ui
│       └── confirm_action.ui
│
├── dashboards/                  # Dashboard controllers (COMMITTED)
│   ├── __init__.py
│   ├── calculations_dashboard.py
│   ├── flow_diagram_dashboard.py
│   ├── analytics_dashboard.py
│   ├── settings_dashboard.py
│   ├── generated_ui_calculations.py    # Compiled from .ui
│   ├── generated_ui_flow_diagram.py
│   ├── generated_ui_analytics.py
│   └── generated_ui_settings.py
│
├── dialogs/                     # Dialog controllers (COMMITTED)
│   ├── __init__.py
│   ├── data_import_dialog.py
│   ├── settings_advanced_dialog.py
│   ├── confirm_action_dialog.py
│   ├── generated_ui_data_import.py     # Compiled from .ui
│   ├── generated_ui_settings_advanced.py
│   └── generated_ui_confirm_action.py
│
├── components/                  # Reusable widgets (COMMITTED)
│   ├── __init__.py
│   ├── kpi_card_widget.py      # Custom widget (pure Python)
│   ├── chart_widget.py         # Matplotlib integration
│   ├── flow_diagram_renderer.py
│   └── data_table_widget.py
│
├── resources/                   # Assets (COMMITTED)
│   ├── icons/
│   ├── images/
│   ├── fonts/
│   └── resources_rc.py         # Compiled from resources.qrc
│
├── styles/                      # Themes & stylesheets
│   ├── __init__.py
│   ├── theme.py
│   └── dark_theme.qss
│
├── main_window.py              # Main window controller
└── generated_ui_main_window.py # Main window UI
```

---

## Scenarios & Patterns

### Scenario 1: Dashboard with Tabs (e.g., Calculations)
**When:** Page has multiple sections organized as tabs (Summary, Area Breakdown, Legacy)

**Qt Designer Steps:**
1. New Form → "Widget"
2. Add QVBoxLayout to root
3. Drop QTabWidget into layout
4. Add tabs: right-click QTabWidget → Insert Page (or use Object Inspector)
5. For each tab, add layout + controls (QFormLayout, QTableWidget, etc.)
6. Save as `src/ui/designer/dashboards/calculations.ui`

**Compile:**
```bash
pyside6-uic src/ui/designer/dashboards/calculations.ui -o src/ui/dashboards/generated_ui_calculations.py
```

**Controller:**
```python
# src/ui/dashboards/calculations_dashboard.py
from PySide6.QtWidgets import QWidget
from .generated_ui_calculations import Ui_Calculations

class CalculationsDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Calculations()
        self.ui.setupUi(self)
        
        # Access tabs via: self.ui.tab_summary, self.ui.tab_area_breakdown, etc.
        # Bind logic here (e.g., load data, connect signals)
```

**Mount in MainWindow:**
```python
# In main_window.py _mount_pages()
self._calculations = CalculationsDashboard(self.ui.calculations)
self.ui.calculations.setLayout(QVBoxLayout())
self.ui.calculations.layout().addWidget(self._calculations)
```

---

### Scenario 2: Pop-up Dialogs (e.g., Data Import, Settings)
**When:** Need modal/non-modal window that appears on button click

**Qt Designer Steps:**
1. New Form → "Dialog with Buttons Bottom" (or "Dialog without Buttons")
2. Add controls (QLineEdit, QComboBox, QPushButton, etc.)
3. Add OK/Cancel buttons if needed
4. Save as `src/ui/designer/dialogs/data_import.ui`

**Compile:**
```bash
pyside6-uic src/ui/designer/dialogs/data_import.ui -o src/ui/dialogs/generated_ui_data_import.py
```

**Controller:**
```python
# src/ui/dialogs/data_import_dialog.py
from PySide6.QtWidgets import QDialog
from .generated_ui_data_import import Ui_DataImportDialog

class DataImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DataImportDialog()
        self.ui.setupUi(self)
        
        # Connect OK/Cancel
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
    
    def get_selected_file(self):
        return self.ui.file_path_input.text()
```

**Show Dialog:**
```python
# From dashboard or main window
from ui.dialogs.data_import_dialog import DataImportDialog

def _on_import_clicked(self):
    dialog = DataImportDialog(self)
    if dialog.exec() == QDialog.Accepted:
        file_path = dialog.get_selected_file()
        # Process import
```

---

### Scenario 3: Dynamic Show/Hide Sections (e.g., Advanced Options)
**When:** Parts of UI appear/disappear based on user actions

**Qt Designer Steps:**
1. Create the expandable section as a QWidget or QGroupBox
2. Give it a clear `objectName` (e.g., `advanced_options_panel`)
3. Design both states (shown and hidden) but leave visible by default

**Controller:**
```python
# Hide initially
self.ui.advanced_options_panel.setVisible(False)

# Toggle on button click
def _on_show_advanced_clicked(self, checked):
    self.ui.advanced_options_panel.setVisible(checked)
    
# Connect to checkbox/button
self.ui.show_advanced_checkbox.toggled.connect(self._on_show_advanced_clicked)
```

**Alternative (Animated):**
```python
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

def _toggle_advanced(self, show):
    self.anim = QPropertyAnimation(self.ui.advanced_options_panel, b"maximumHeight")
    self.anim.setDuration(200)
    self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    if show:
        self.ui.advanced_options_panel.setVisible(True)
        self.anim.setStartValue(0)
        self.anim.setEndValue(300)  # Final height
    else:
        self.anim.setStartValue(300)
        self.anim.setEndValue(0)
        self.anim.finished.connect(lambda: self.ui.advanced_options_panel.setVisible(False))
    self.anim.start()
```

---

### Scenario 4: Switching Views in Same Page (e.g., Chart vs Table)
**When:** Same dashboard space shows different content based on selection

**Qt Designer Steps:**
1. Drop QStackedWidget into dashboard
2. Add pages: Insert Page → each page is a different view
3. Design each page (Page 0 = chart, Page 1 = table, etc.)
4. Name pages clearly: `chart_view`, `table_view`

**Controller:**
```python
# Switch views
def _on_view_changed(self, index):
    self.ui.content_stack.setCurrentIndex(index)

# Connect to combo/radio buttons
self.ui.view_selector.currentIndexChanged.connect(self._on_view_changed)
```

---

### Scenario 5: Nested Tabs (e.g., Settings with subtabs)
**When:** Tab has its own sub-tabs

**Qt Designer Steps:**
1. Main QTabWidget with tabs: General, Data Paths, Licensing
2. Inside "Data Paths" tab, drop another QTabWidget
3. Add sub-tabs: Excel Paths, Database, Templates

**Controller:**
```python
# Access nested tabs
self.ui.main_tabs.setCurrentIndex(1)  # Data Paths tab
self.ui.data_paths_subtabs.setCurrentIndex(0)  # Excel Paths sub-tab
```

---

### Scenario 6: Reusable Custom Widgets (e.g., KPI Card)
**When:** Same widget type used in multiple places

**Create Custom Widget:**
```python
# src/ui/components/kpi_card_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class KPICardWidget(QWidget):
    def __init__(self, title="", value="", unit="", parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.set_title(title)
        self.set_value(value, unit)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.title_label = QLabel()
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setStyleSheet("border: 1px solid #ccc; border-radius: 8px; padding: 10px;")
    
    def set_title(self, title):
        self.title_label.setText(title)
    
    def set_value(self, value, unit=""):
        self.value_label.setText(f"{value} {unit}")
```

**Use in Dashboard:**
```python
from ui.components.kpi_card_widget import KPICardWidget

# In dashboard __init__
self.kpi_balance = KPICardWidget("Water Balance", "1234.5", "m³", self)
self.ui.kpi_container.layout().addWidget(self.kpi_balance)
```

**Or Promote in Designer:**
1. Drop QWidget placeholder
2. Right-click → Promote to...
3. Base class: QWidget
4. Promoted class: KPICardWidget
5. Header file: ui.components.kpi_card_widget.h (leave as-is, PySide ignores)
6. Click Add → Promote

---

## Compilation Workflow

**Single file:**
```bash
pyside6-uic src/ui/designer/dashboards/calculations.ui -o src/ui/dashboards/generated_ui_calculations.py
```

**Batch compile all dashboards:**
```bash
# PowerShell
Get-ChildItem src/ui/designer/dashboards/*.ui | ForEach-Object {
    $name = $_.BaseName
    pyside6-uic $_.FullName -o "src/ui/dashboards/generated_ui_$name.py"
}
```

**Batch compile all dialogs:**
```bash
Get-ChildItem src/ui/designer/dialogs/*.ui | ForEach-Object {
    $name = $_.BaseName
    pyside6-uic $_.FullName -o "src/ui/dialogs/generated_ui_$name.py"
}
```

**Resources (icons/images):**
```bash
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py
```

---

## Quick Decision Guide

| UI Need | Pattern | Location |
|---------|---------|----------|
| Main app shell (sidebar, header, status) | Main Window template | `designer/main_window.ui` |
| Full-page dashboard | Widget template + mount in MainWindow | `designer/dashboards/` |
| Multiple sections on page | QTabWidget inside dashboard | Same .ui file |
| Pop-up window | Dialog template | `designer/dialogs/` |
| Show/hide section | setVisible() on QWidget/QGroupBox | Controller logic |
| Switch views in place | QStackedWidget | In dashboard .ui |
| Reusable component | Custom QWidget subclass | `components/` (pure Python) |
| Chart/plot | Custom widget with matplotlib | `components/chart_widget.py` |

---

## Best Practices

1. **One .ui per logical page/dialog** - don't cram everything into main_window.ui
2. **Always set layouts** - right-click empty space → Lay Out (Vertically/Horizontally)
3. **Name widgets clearly** - use objectName like `calculate_button`, not `pushButton_3`
4. **Don't edit generated files** - always recompile from .ui
5. **Keep .ui local** - .gitignore excludes them; only commit generated .py
6. **Test incrementally** - design → compile → wire → test before adding more
7. **Use spacers** - QSpacerItem for flexible layouts
8. **Promote custom widgets** - integrate your components into Designer
9. **Modal vs Modeless**:
   - Modal (blocks parent): `dialog.exec()`
   - Modeless (non-blocking): `dialog.show()`

---

## Common Pitfalls

- **Missing layout on root widget** → controls won't resize
- **Forgetting to compile .ui** → old UI, changes not reflected
- **Editing generated_ui_*.py** → lost on next compile
- **Not checking objectName** → can't access widget in controller
- **Hardcoded sizes** → use sizePolicy and layouts instead
- **Mixing Designer and manual code** → keep generated separate from logic

---

## Summary

| Scenario | File to Create |
|----------|----------------|
| Dashboard page | `designer/dashboards/X.ui` → `dashboards/generated_ui_X.py` + `dashboards/X_dashboard.py` |
| Pop-up dialog | `designer/dialogs/Y.ui` → `dialogs/generated_ui_Y.py` + `dialogs/Y_dialog.py` |
| Reusable widget | `components/Z_widget.py` (pure Python, no .ui) |
| Tab inside page | Add QTabWidget in the dashboard's .ui |
| Dynamic section | Design visible, toggle with setVisible() in controller |
| View switcher | QStackedWidget in .ui, setCurrentIndex() in controller |

Now you know exactly where to put each piece and how to wire it up. Start with one dashboard (e.g., Calculations), design it, compile, test, then move to the next.
