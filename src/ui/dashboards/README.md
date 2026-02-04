# Dashboard Files Overview

## ✅ Active Dashboard Pages (Loaded by MainWindow)

These files are imported and used in `src/ui/main_window.py`:

| File | Page Name | Generated UI | Purpose |
|------|-----------|--------------|---------|
| **dashboard_dashboard.py** | DashboardPage | generated_ui_dashboard.py | Main Dashboard with KPI cards |
| **analytics_dashboard.py** | AnalyticsPage | generated_ui_analytics.py | Analytics & Trends |
| **monitoring_dashboard.py** | MonitoringPage | generated_ui_monitoring.py | Monitoring Data |
| **storage_facilities_dashboard.py** | StorageFacilitiesPage | generated_ui_storage_facilities.py | Storage Facilities |
| **calculation_dashboard.py** | CalculationPage | generated_ui_calculation.py | Calculations |
| **flow_diagram_page.py** | FlowDiagramPage | generated_ui_flow_diagram.py | ⭐ Flow Diagram Editor (Main) |
| **settings_dashboard.py** | SettingsPage | generated_ui_settings.py | Settings |
| **help_dashboard.py** | HelpPage | generated_ui_help.py | Help |
| **about_dashboard.py** | AboutPage | generated_ui_about.py | About |

## 🔧 Generated UI Files (Auto-compiled from Qt Designer)

These are auto-generated from `.ui` files using `pyside6-uic`:

- **generated_ui_*.py** - ⚠️ Never edit these directly! Edit the `.ui` file in `src/ui/designer/` and run `compile_ui.ps1` to regenerate.

## ❌ Unused/Legacy Files

Files with `_UNUSED_` prefix are not currently used in the application:

- **_UNUSED_flow_diagram_dashboard.py.bak** - Old duplicate of flow_diagram_page.py, kept for reference only. Safe to delete.

## 📝 Adding a Button Handler

**Example: Adding a "Load Excel" button handler to Flow Diagram page**

1. ✅ Edit `flow_diagram_page.py` (NOT _UNUSED_flow_diagram_dashboard.py.bak)
2. ✅ Connect button in `_connect_toolbar_buttons()` method:
   ```python
   self.ui.load_excel_button.clicked.connect(self._on_load_excel_clicked)
   ```
3. ✅ Add handler method:
   ```python
   def _on_load_excel_clicked(self):
       """Handle Load Excel button click."""
       # Your code here
   ```

## 🔍 How to Find the Right File

**Rule of thumb:** If the page is listed in the sidebar navigation, it has a `*_dashboard.py` or `*_page.py` file in this folder.

**Quick check:** Search `src/ui/main_window.py` for `from ui.dashboards.` to see exactly which files are being imported.

---

**Last Updated:** February 1, 2026  
**Purpose:** Prevent confusion about duplicate/unused files
