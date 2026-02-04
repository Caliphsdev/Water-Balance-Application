# Implementation Checklist - PySide6 Water Balance Dashboard

Use this checklist to track your progress through the migration.

## Phase 1: Foundation Setup ⏱️ 30 minutes

### Environment & Dependencies
- [ ] Install PySide6: `pip install PySide6 PySide6-Addons`
- [ ] Create `requirements.txt` with all dependencies
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify: `python -c "from PySide6.QtWidgets import QApplication; print('OK')"`

### Directory Structure
- [ ] Create `src/ui/designer/` directory
- [ ] Create `src/ui/dialogs/` directory
- [ ] Create `src/ui/dashboards/` directory
- [ ] Create `src/ui/components/` directory
- [ ] Create `src/ui/styles/` directory
- [ ] Create `src/core/` directory
- [ ] Create `src/services/` directory
- [ ] Create `src/models/` directory
- [ ] Create `src/database/` directory
- [ ] Create `config/` directory
- [ ] Create `data/diagrams/` directory
- [ ] Create `tests/` with subdirectories

### Copy from Tkinter
- [ ] Copy `src/database/schema.py` from `../tkinter-legacy/src/database/`
- [ ] Copy `src/database/db_manager.py` from `../tkinter-legacy/src/database/`
- [ ] Copy `src/utils/app_logger.py` from `../tkinter-legacy/` → `src/core/app_logger.py`
- [ ] Copy `config/app_config.yaml` from `../tkinter-legacy/config/`
- [ ] Copy database file: `data/water_balance.db` from `../tkinter-legacy/data/`
- [ ] Copy Excel templates to `data/`

### Core Files Created
- [ ] Create `src/main.py` (entry point, ~50 lines)
- [ ] Create `src/__init__.py` (empty)
- [ ] Create `src/core/__init__.py` (empty)
- [ ] Create `src/database/__init__.py` (empty)
- [ ] Create `src/services/__init__.py` (empty)
- [ ] Create `src/models/__init__.py` (empty)
- [ ] Create `src/ui/__init__.py` (empty)
- [ ] Create `config_manager.py` in `src/core/` (from Tkinter, enhanced)

### Verification
- [ ] Run `python src/main.py` successfully (QApplication starts)
- [ ] No import errors
- [ ] Database loads without errors

---

## Phase 2: First Dashboard ⏱️ 2-3 hours

### UI Design (Qt Designer)
- [ ] Open Qt Designer (comes with PySide6)
- [ ] Create `src/ui/designer/main_window.ui`
  - [ ] Main window (QMainWindow)
  - [ ] Menu bar (File, Edit, Help)
  - [ ] Sidebar (vertical layout with buttons: Calculations, Flow Diagram, Analytics, Settings)
  - [ ] Content area (QWidget, will hold dashboards)
  - [ ] Status bar (shows operation status)
- [ ] Save main_window.ui

### Generate Python from .ui Files
- [ ] Generate: `pyside6-uic src/ui/designer/main_window.ui -o src/ui/generated_ui_main_window.py`
- [ ] Verify file created successfully
- [ ] Check generated code compiles: `python -m py_compile src/ui/generated_ui_main_window.py`

### Main Window Controller
- [ ] Create `src/ui/main_window.py`
- [ ] Load UI from generated file: `self.ui = Ui_MainWindow()`
- [ ] Connect sidebar buttons to slots
- [ ] Implement module caching (avoid reloading dashboards)
- [ ] Test: Window shows with sidebar buttons

### Calculations Dashboard Design
- [ ] Create `src/ui/designer/dialogs/calculations_view.ui` in Designer
  - [ ] Date selector (QDateEdit)
  - [ ] Area selector (QComboBox)
  - [ ] Calculate button (QPushButton)
  - [ ] Result table (QTableWidget)
  - [ ] Status label (QLabel for messages)
- [ ] Generate: `pyside6-uic src/ui/designer/dialogs/calculations_view.ui -o src/ui/generated_ui_calculations_view.py`

### Calculations Dashboard Controller
- [ ] Create `src/ui/dashboards/calculations_dashboard.py`
- [ ] Load UI: `self.ui = Ui_CalculationsView()`
- [ ] Connect button: `self.ui.btnCalculate.clicked.connect(self._on_calculate_clicked)`
- [ ] Implement `_on_calculate_clicked()` stub
- [ ] Implement `_display_results()` to update table
- [ ] Test: Click button, see dummy results in table

### Business Logic Services
- [ ] Create `src/services/calculation_service.py`
  - [ ] Class: `CalculationService`
  - [ ] Method: `calculate_balance(facility_code, date)` → Dict
  - [ ] Implement dummy calculations (hardcoded for now)
  - [ ] Add caching: `self._cache`
  - [ ] Add method: `clear_cache()`
- [ ] Create `src/services/excel_service.py`
  - [ ] Class: `ExcelService`
  - [ ] Method: `load_meter_readings(facility_code, date)` → Dict
  - [ ] Implement dummy data (hardcoded for now)
- [ ] Create `src/services/database_service.py`
  - [ ] Class: `DatabaseService`
  - [ ] Method: `get_facility(facility_code)` → Dict
  - [ ] Method: `get_all_facilities()` → List[Dict]
  - [ ] Implement using `DatabaseManager`

### Integration
- [ ] Import services in `calculations_dashboard.py`
- [ ] Call `CalculationService.calculate_balance()` on button click
- [ ] Display results using `_display_results()`
- [ ] Test: Full flow works (click → calculate → display)

### Testing
- [ ] Create `tests/test_services/test_calculation_service.py`
  - [ ] Test: `test_calculate_balance_basic()`
  - [ ] Test: `test_calculate_balance_caching()`
  - [ ] Test: `test_calculate_balance_facility_not_found()`
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Run: `pytest tests/test_services/ -v`
- [ ] All tests pass

### Verification
- [ ] Run `python src/main.py`
- [ ] Click "Calculations" button
- [ ] Click "Calculate" button
- [ ] See results in table
- [ ] No errors in console

---

## Phase 3: Additional Dashboards ⏱️ 1 week

### Flow Diagram Dashboard

**UI Design (Qt Designer)**
- [ ] Create `src/ui/designer/dashboards/flow_diagram_view.ui`
  - [ ] Canvas/widget for diagram display
  - [ ] Combobox for area selection
  - [ ] Refresh button
  - [ ] Info panel (node details)

**Generate & Controller**
- [ ] Generate Python: `pyside6-uic src/ui/designer/dashboards/flow_diagram_view.ui -o src/ui/generated_ui_flow_diagram_view.py`
- [ ] Create `src/ui/dashboards/flow_diagram_dashboard.py`
- [ ] Load UI
- [ ] Connect area selection to diagram reload
- [ ] Implement `_load_diagram(area_code)`

**Custom Widget**
- [ ] Create `src/ui/components/flow_diagram_renderer.py`
  - [ ] Class: `FlowDiagramWidget(QWidget)`
  - [ ] Method: `load_diagram(json_path)`
  - [ ] Method: `paintEvent()` to render nodes/edges
  - [ ] Handle mouse clicks (select node)

**Services**
- [ ] Create `src/services/flow_service.py`
  - [ ] Method: `load_diagram_json(area_code)` → Dict
  - [ ] Method: `load_flow_volumes(area_code)` → Dict
- [ ] Update `ExcelService`: add `load_flow_volumes()`

**Testing**
- [ ] Create `tests/test_services/test_flow_service.py`
- [ ] Create `tests/test_ui/test_flow_diagram_dashboard.py`
- [ ] Run tests

### Analytics Dashboard

**UI Design**
- [ ] Create `src/ui/designer/dashboards/analytics_view.ui`
  - [ ] KPI cards (error %, efficiency, ratios)
  - [ ] Trend chart (matplotlib)
  - [ ] Comparison table

**Generate & Controller**
- [ ] Generate Python
- [ ] Create `src/ui/dashboards/analytics_dashboard.py`
- [ ] Connect to `CalculationService`

**Custom Widget**
- [ ] Create `src/ui/components/kpi_card_widget.py`
  - [ ] Class: `KPICard(title, value)`
  - [ ] Method: `set_value(value, color)`

**Services**
- [ ] Create `src/services/analytics_service.py`
  - [ ] Method: `calculate_kpis(results)` → Dict
  - [ ] Method: `get_trends(facility_code, months)` → List

### Charts Dashboard

**UI Design**
- [ ] Create `src/ui/designer/dashboards/charts_view.ui`
  - [ ] Matplotlib canvas embedded in PySide6
  - [ ] Chart type selector
  - [ ] Date range picker

**Generate & Controller**
- [ ] Create `src/ui/dashboards/charts_dashboard.py`
- [ ] Embed matplotlib figure in PySide6 canvas

**Custom Widget**
- [ ] Create `src/ui/components/chart_widget.py`
  - [ ] Class: `MatplotlibCanvas(QWidget)`
  - [ ] Integrate matplotlib figure

**Services**
- [ ] Use existing analytics service

### Settings/Configuration Dashboard

**UI Design**
- [ ] Create `src/ui/designer/dialogs/settings_dialog.ui`
  - [ ] Excel path inputs
  - [ ] Feature toggle checkboxes
  - [ ] Database path input
  - [ ] Save/Cancel buttons

**Dialog Controller**
- [ ] Create `src/ui/dialogs/settings_dialog.py`
- [ ] Load current config
- [ ] Save on OK
- [ ] Show error on invalid paths

**Testing**
- [ ] Create test for settings persistence
- [ ] Test validation

### Module Integration

- [ ] Add remaining button clicks to `main_window.py`
- [ ] Register all dashboards in module cache
- [ ] Test switching between all dashboards
- [ ] No memory leaks (monitor with activity monitor)

---

## Phase 4: Dialogs & Features ⏱️ 3-4 days

### Data Import Dialog
- [ ] Create `src/ui/dialogs/data_import_dialog.py`
- [ ] Browse & select Excel file
- [ ] Preview data
- [ ] Import to database

### License Dialog
- [ ] Copy from Tkinter: `src/ui/license_dialog.py`
- [ ] Adapt to PySide6
- [ ] Test activation flow

### Help & Documentation
- [ ] Create `src/ui/help_documentation.py`
- [ ] Show user guides
- [ ] Link to external docs

### Notifications & Alerts
- [ ] Create `src/utils/ui_notify.py` (PySide6 version)
- [ ] Show toasts/notifications
- [ ] Error message handling

---

## Phase 5: Testing & Polish ⏱️ 3-4 days

### Unit Tests

**Services**
- [ ] `test_calculation_service.py` - 100% coverage
- [ ] `test_balance_check_service.py`
- [ ] `test_pump_transfer_service.py`
- [ ] `test_excel_service.py`
- [ ] `test_database_service.py`

**Models**
- [ ] Pydantic model validation tests
- [ ] Data conversion tests

**Utilities**
- [ ] Config manager tests
- [ ] Logger tests
- [ ] Error handler tests

### UI Tests
- [ ] `test_main_window.py`
- [ ] `test_calculations_dashboard.py`
- [ ] `test_flow_diagram_dashboard.py`
- [ ] Dialog tests

### Integration Tests
- [ ] Database + Service integration
- [ ] Excel + Service integration
- [ ] Full workflow tests (user scenario)

### Code Quality
- [ ] Run `mypy src/ --strict` (no errors)
- [ ] Run `pylint src/` (score > 8.0)
- [ ] Run `pytest --cov=src --cov-report=html` (>80% coverage)
- [ ] Check for dead code

### Performance
- [ ] Measure startup time (< 5 seconds)
- [ ] Measure calculation time (< 2 seconds for typical)
- [ ] Profile memory usage
- [ ] Check for memory leaks

### UI Polish
- [ ] Apply theme/stylesheet
- [ ] Center dialogs on parent window
- [ ] Test responsive layout (different screen sizes)
- [ ] Test dark mode (if using stylesheet)

### Documentation
- [ ] Update README.md
- [ ] Add architecture diagrams
- [ ] Document API for services
- [ ] Create user guide

---

## Phase 6: Build & Deploy ⏱️ 2-3 days

### Executable Build
- [ ] Create `build.ps1` (PyInstaller script)
- [ ] Build executable: `python build.ps1`
- [ ] Test executable on clean machine
- [ ] Verify: Database loads, calculations work

### Installer
- [ ] Create Inno Setup script (`.iss`)
- [ ] Configure installer (logo, welcome screen, license)
- [ ] Build installer: `iscc installer.iss`
- [ ] Test installer: Install, run, uninstall cleanly

### Distribution
- [ ] Create installer with version number
- [ ] Create installer directory: `dist/`
- [ ] Create README for distribution
- [ ] Create release notes

---

## Final Checklist ✅

### Feature Completeness
- [ ] All Tkinter dashboards migrated
- [ ] All dialogs functional
- [ ] All settings configurable
- [ ] License system working

### Code Quality
- [ ] Type hints: 100% coverage
- [ ] Docstrings: All public methods
- [ ] Tests: >80% coverage
- [ ] No linting errors

### Performance
- [ ] Startup < 5 seconds
- [ ] Calculations < 2 seconds
- [ ] No memory leaks
- [ ] Responsive to user input

### User Experience
- [ ] Responsive layout (all screen sizes)
- [ ] Professional styling
- [ ] Clear error messages
- [ ] Intuitive navigation

### Documentation
- [ ] README.md complete
- [ ] Architecture documented
- [ ] API documented
- [ ] User guide available

### Deployment
- [ ] Windows executable works
- [ ] Installer works
- [ ] Uninstall clean
- [ ] License validation works

---

## Time Tracking

Record actual time spent in each phase:

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| 1 | 30 min | _____ | |
| 2 | 2-3 hrs | _____ | |
| 3 | 1 week | _____ | |
| 4 | 3-4 days | _____ | |
| 5 | 3-4 days | _____ | |
| 6 | 2-3 days | _____ | |
| **Total** | **~12 days** | **_____** | |

---

## Issues Found

Document any issues discovered during implementation:

```
Issue #1: [Date]
- Description: ...
- Resolution: ...
- Lessons learned: ...

Issue #2: [Date]
- Description: ...
- Resolution: ...
- Lessons learned: ...
```

---

## Sign-Off

- [ ] All phases complete
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation reviewed
- [ ] Ready for production

**Completed by**: _______________  
**Date**: _______________  
**Sign-off**: _______________

---

**Print this document and check off each item as you complete it!**
