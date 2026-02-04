# PySide6 Implementation Patterns & Examples

This guide provides concrete examples for common patterns you'll encounter in the PySide6 water balance application.

## Table of Contents
1. [Qt Designer Integration](#qt-designer-integration)
2. [Service Layer Pattern](#service-layer-pattern)
3. [Signal/Slot Communication](#signalslot-communication)
4. [Async Calculations](#async-calculations)
5. [Custom Widgets](#custom-widgets)
6. [Configuration & Dependency Injection](#configuration--dependency-injection)
7. [Testing Patterns](#testing-patterns)

---

## Qt Designer Integration

### Pattern: Load .ui File and Add Logic

**File: `ui/dashboards/calculations_dashboard.py`**
```python
"""Calculations Dashboard - Water balance calculations and results display.

This dashboard:
1. Loads the UI from Qt Designer (.ui file)
2. Connects user interactions to calculation service calls
3. Displays results in a table model
4. Updates when calculations complete
"""

from PySide6.QtWidgets import QWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QThread
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.generated_ui_calculations_view import Ui_CalculationsView
from services.calculation_service import CalculationService
from core.app_logger import logger


class CalculationsDashboard(QWidget):
    """Calculations Dashboard controller.
    
    Responsibilities:
    - Load calculations_view.ui from Qt Designer
    - Manage user interactions (date selection, calculate button)
    - Call calculation_service asynchronously
    - Update table with results
    - Handle errors gracefully
    
    Attributes:
        ui (Ui_CalculationsView): Generated UI from Designer
        calc_service (CalculationService): Business logic for calculations
        _worker_thread (QThread): Background thread for long calculations
    """
    
    def __init__(self, parent=None):
        """Initialize Calculations Dashboard.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Load UI from Designer
        self.ui = Ui_CalculationsView()
        self.ui.setupUi(self)
        
        # Initialize services
        self.calc_service = CalculationService()
        
        # Connect user interactions to slots
        self.ui.btnCalculate.clicked.connect(self._on_calculate_clicked)
        self.ui.dateEdit.dateChanged.connect(self._on_date_changed)
        self.ui.cbArea.currentIndexChanged.connect(self._on_area_changed)
        
        # Setup result table
        self._setup_result_table()
        
        # Async calculation thread (for non-blocking operations)
        self._worker_thread = None
        
        logger.info("Calculations Dashboard initialized")
    
    def _setup_result_table(self):
        """Configure result table columns and headers."""
        headers = [
            "Facility",
            "Inflows (m³)",
            "Outflows (m³)",
            "Storage Change (m³)",
            "Error (m³)",
            "Error %",
            "Status"
        ]
        self.ui.tableResults.setColumnCount(len(headers))
        self.ui.tableResults.setHorizontalHeaderLabels(headers)
    
    def _on_calculate_clicked(self):
        """Handle Calculate button click - start async calculation."""
        # Get inputs from UI
        facility_code = self.ui.cbArea.currentText()
        selected_date = self.ui.dateEdit.date().toPython()
        
        if not facility_code:
            QMessageBox.warning(self, "Input Error", "Please select a facility")
            return
        
        # Show loading state
        self.ui.btnCalculate.setEnabled(False)
        self.ui.btnCalculate.setText("Calculating...")
        
        # Start async calculation
        self._calculate_async(facility_code, selected_date)
    
    def _calculate_async(self, facility_code: str, date):
        """Run calculation in background thread (non-blocking).
        
        Args:
            facility_code: Facility code (e.g., 'UG2N')
            date: Calculation date
        """
        def run_calculation():
            try:
                # Call business logic (blocking, but in background thread)
                result = self.calc_service.calculate_balance(facility_code, date)
                return ("success", result)
            except Exception as e:
                logger.error(f"Calculation failed: {e}")
                return ("error", str(e))
        
        def on_complete(result):
            status, data = result
            if status == "success":
                self._display_results(data)
            else:
                QMessageBox.critical(self, "Calculation Error", data)
            
            # Reset button
            self.ui.btnCalculate.setEnabled(True)
            self.ui.btnCalculate.setText("Calculate")
        
        # Create and run worker thread
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_calculation)
        future.add_done_callback(lambda f: on_complete(f.result()))
    
    def _display_results(self, result: dict):
        """Display calculation results in table.
        
        Args:
            result: Dict with keys: balance_m3, error_pct, inflows, outflows, etc.
        """
        # Clear existing rows
        self.ui.tableResults.setRowCount(0)
        
        # Add result row
        row = 0
        self.ui.tableResults.insertRow(row)
        
        items = [
            result.get('facility_code', ''),
            f"{result.get('inflows', 0):.1f}",
            f"{result.get('outflows', 0):.1f}",
            f"{result.get('storage_change', 0):.1f}",
            f"{result.get('error_m3', 0):.1f}",
            f"{result.get('error_percent', 0):.2f}",
            "✓ Valid" if result.get('error_percent', 999) < 5 else "✗ Invalid"
        ]
        
        for col, item_text in enumerate(items):
            self.ui.tableResults.setItem(row, col, QTableWidgetItem(item_text))
    
    def _on_date_changed(self):
        """Handle date selection change."""
        logger.debug(f"Date changed to {self.ui.dateEdit.date().toPython()}")
    
    def _on_area_changed(self):
        """Handle area selection change."""
        selected_area = self.ui.cbArea.currentText()
        logger.info(f"Area changed to {selected_area}")
```

**Key Patterns:**
1. ✅ Load `.ui` file with `Ui_CalculationsView` (auto-generated by `pyside6-uic`)
2. ✅ Connect button clicks to slots with `clicked.connect(self._on_...)`
3. ✅ Call services asynchronously (don't block UI)
4. ✅ Update UI with results in main thread (use callbacks from worker thread)
5. ✅ Handle errors gracefully with `QMessageBox`

---

## Service Layer Pattern

### Pattern: Business Logic Separated from UI

**File: `src/services/calculation_service.py`**
```python
"""Calculation Service - Core water balance calculation engine.

This service encapsulates all calculation logic (from Tkinter's water_balance_calculator.py).
It has NO Tkinter/PySide6 dependencies - pure business logic.

This makes it:
- Testable (can test without GUI)
- Reusable (can call from CLI, API, etc.)
- Portable (no UI framework lock-in)
"""

from typing import Dict, List, Optional
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.excel_service import ExcelService
from services.database_service import DatabaseService
from core.config_manager import config
from core.app_logger import logger
from models.calculation import CalculationResult


class CalculationService:
    """Core water balance calculation engine (pure business logic).
    
    This service reuses the calculation logic from Tkinter's water_balance_calculator.py
    but with improved architecture:
    - No Tkinter/PySide6 dependencies
    - Type hints on all parameters
    - Clear method names
    - Caching for performance
    - Comprehensive docstrings
    
    Attributes:
        excel_service: Handles Excel file reading
        db_service: Handles database operations
        _cache: Dict of calculated results (facility_code -> date -> result)
    """
    
    def __init__(self):
        """Initialize calculation service with required dependencies."""
        self.excel_service = ExcelService()
        self.db_service = DatabaseService()
        self._cache = {}  # Cache calculations to avoid re-computation
    
    def calculate_balance(
        self,
        facility_code: str,
        calc_date: date
    ) -> Dict:
        """Calculate water balance for facility on date (PRIMARY CALCULATION ENGINE).
        
        Implements the TRP (Total Return to Plant) formula:
            Fresh Inflows = Outflows + ΔStorage + Error
        
        This is the core orchestration that:
        1. Reads meter data from METER READINGS Excel
        2. Retrieves facility constants from database
        3. Computes inflows, outflows, storage changes
        4. Validates closure (error < 5%)
        5. Caches results to avoid re-calculation
        
        Args:
            facility_code: Facility ID (e.g., 'UG2N', 'OLDTSF')
            calc_date: Calculation date (year-month from this date)
        
        Returns:
            Dict with keys:
                - facility_code (str): Input facility
                - date (date): Calculation date
                - fresh_inflows_m3 (float): Fresh water inflows (m³)
                - outflows_m3 (float): Total outflows (m³)
                - storage_change_m3 (float): Change in storage (m³)
                - error_m3 (float): Closure error (m³)
                - error_percent (float): Closure error as % of inflows
                - is_valid (bool): True if error < 5%
                - kpis (dict): Additional KPIs (efficiency, ratios, etc.)
        
        Raises:
            ValueError: If facility not found or date invalid
            ExcelReadError: If meter data missing (check data quality)
        
        Example:
            >>> service = CalculationService()
            >>> result = service.calculate_balance('UG2N', date(2025, 3, 1))
            >>> if result['is_valid']:
            ...     print(f"Balance valid for UG2N (error: {result['error_percent']:.1f}%)")
        """
        # Check cache first (avoid expensive calculations)
        cache_key = (facility_code, calc_date.year, calc_date.month)
        if cache_key in self._cache:
            logger.debug(f"Returning cached result for {facility_code} {calc_date}")
            return self._cache[cache_key]
        
        try:
            # 1. Get facility constants from database
            facility = self.db_service.get_facility(facility_code)
            if not facility:
                raise ValueError(f"Facility '{facility_code}' not found in database")
            
            # 2. Load meter readings from Excel
            meter_data = self.excel_service.load_meter_readings(facility_code, calc_date)
            if not meter_data:
                raise ValueError(f"No meter readings for {facility_code} {calc_date}")
            
            # 3. Perform calculations
            inflows = self._calculate_inflows(facility, meter_data)
            outflows = self._calculate_outflows(facility, meter_data)
            storage_change = self._calculate_storage_change(facility, meter_data)
            
            # 4. Compute closure error
            error_m3 = inflows - outflows - storage_change
            error_percent = (error_m3 / inflows * 100) if inflows > 0 else 0
            
            # 5. Build result object with KPIs
            result = {
                'facility_code': facility_code,
                'date': calc_date,
                'fresh_inflows_m3': inflows,
                'outflows_m3': outflows,
                'storage_change_m3': storage_change,
                'error_m3': error_m3,
                'error_percent': error_percent,
                'is_valid': abs(error_percent) < 5,  # Standard tolerance
                'kpis': self._calculate_kpis(facility, inflows, outflows, storage_change)
            }
            
            # 6. Cache result
            self._cache[cache_key] = result
            
            logger.info(
                f"Calculation complete: {facility_code} {calc_date} "
                f"(error: {error_percent:.2f}%, valid: {result['is_valid']})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Calculation failed for {facility_code}: {e}")
            raise
    
    def _calculate_inflows(self, facility: Dict, meter_data: Dict) -> float:
        """Calculate total fresh inflows (m³).
        
        Sources: rainfall, boreholes, plant recycled water, etc.
        """
        # Implementation: Sum all inflow sources
        inflows = 0
        for source in facility.get('inflow_sources', []):
            inflows += meter_data.get(source, 0)
        return inflows
    
    def _calculate_outflows(self, facility: Dict, meter_data: Dict) -> float:
        """Calculate total outflows (m³).
        
        Destinations: mill consumption, evaporation, seepage, etc.
        """
        outflows = 0
        for sink in facility.get('outflow_sinks', []):
            outflows += meter_data.get(sink, 0)
        return outflows
    
    def _calculate_storage_change(self, facility: Dict, meter_data: Dict) -> float:
        """Calculate change in storage (m³)."""
        # Implementation: Start level - End level
        return meter_data.get('storage_start', 0) - meter_data.get('storage_end', 0)
    
    def _calculate_kpis(
        self,
        facility: Dict,
        inflows: float,
        outflows: float,
        storage_change: float
    ) -> Dict:
        """Calculate key performance indicators.
        
        Returns ratios, efficiency metrics, etc.
        """
        return {
            'efficiency_percent': (inflows / (inflows + storage_change) * 100) if (inflows + storage_change) > 0 else 0,
            'inflow_outflow_ratio': inflows / outflows if outflows > 0 else 0,
        }
    
    def clear_cache(self):
        """Clear calculation cache (call after Excel reload)."""
        self._cache.clear()
        logger.info("Calculation cache cleared")
```

**Key Patterns:**
1. ✅ **No UI imports** - Pure business logic, no Tkinter/PySide6 dependencies
2. ✅ **Dependency injection** - Services passed in (excel_service, db_service)
3. ✅ **Clear contracts** - Type hints on all parameters and returns
4. ✅ **Comprehensive docstrings** - Explain purpose, args, returns, raises, examples
5. ✅ **Caching strategy** - Performance improvement documented
6. ✅ **Error handling** - Informative exceptions with context

---

## Signal/Slot Communication

### Pattern: Connect UI Events to Slots

**File: `ui/main_window.py`**
```python
"""Main Window - Application container with sidebar navigation.

This demonstrates the PySide6 signal/slot pattern:
- User interactions (clicks, selections) emit signals
- Signals are connected to slots (callback methods)
- Slots update UI or call services
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.generated_ui_main_window import Ui_MainWindow
from ui.dashboards.calculations_dashboard import CalculationsDashboard
from ui.dashboards.flow_diagram_dashboard import FlowDiagramDashboard
from core.app_logger import logger


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation.
    
    Responsibilities:
    - Load main_window.ui from Qt Designer
    - Manage sidebar navigation (module selection)
    - Load and cache dashboard modules
    - Coordinate between dashboards
    
    Signal/Slot Pattern:
    - btnCalculations.clicked → _on_calculations_clicked
    - btnFlowDiagram.clicked → _on_flow_diagram_clicked
    - etc.
    """
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Load UI from Designer
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Cache loaded dashboards (avoid re-creating on tab switch)
        self._dashboard_cache = {}
        
        # Connect sidebar buttons to slots
        self.ui.btnCalculations.clicked.connect(self._on_calculations_clicked)
        self.ui.btnFlowDiagram.clicked.connect(self._on_flow_diagram_clicked)
        self.ui.btnAnalytics.clicked.connect(self._on_analytics_clicked)
        self.ui.btnSettings.clicked.connect(self._on_settings_clicked)
        
        # Load first dashboard
        self._show_dashboard("calculations")
        
        logger.info("Main window initialized")
    
    def _on_calculations_clicked(self):
        """Handle Calculations button click."""
        self._show_dashboard("calculations")
    
    def _on_flow_diagram_clicked(self):
        """Handle Flow Diagram button click."""
        self._show_dashboard("flow_diagram")
    
    def _on_analytics_clicked(self):
        """Handle Analytics button click."""
        self._show_dashboard("analytics")
    
    def _on_settings_clicked(self):
        """Handle Settings button click."""
        self._show_dashboard("settings")
    
    def _show_dashboard(self, dashboard_name: str):
        """Load and display dashboard (with caching).
        
        First access: Load and cache dashboard
        Subsequent accesses: Use cached instance
        
        Args:
            dashboard_name: Name of dashboard ('calculations', 'flow_diagram', etc.)
        """
        # Check if already cached
        if dashboard_name in self._dashboard_cache:
            dashboard = self._dashboard_cache[dashboard_name]
        else:
            # Load dashboard on first access
            if dashboard_name == "calculations":
                dashboard = CalculationsDashboard()
            elif dashboard_name == "flow_diagram":
                dashboard = FlowDiagramDashboard()
            else:
                # Load other dashboards...
                dashboard = QWidget()
            
            # Cache for next time
            self._dashboard_cache[dashboard_name] = dashboard
        
        # Clear previous content
        for i in reversed(range(self.ui.contentArea.layout().count())):
            self.ui.contentArea.layout().itemAt(i).widget().setParent(None)
        
        # Show new dashboard
        self.ui.contentArea.layout().addWidget(dashboard)
        
        logger.info(f"Showing dashboard: {dashboard_name}")
```

**Key Patterns:**
1. ✅ **Signal connection** - `.clicked.connect(self._on_...)`
2. ✅ **Slot naming** - `_on_<widget>_<event>` convention
3. ✅ **Caching** - Store loaded dashboards in `_dashboard_cache`
4. ✅ **Lazy loading** - Load dashboards on first access (improves startup)
5. ✅ **Clear separation** - Each dashboard is independent

---

## Async Calculations

### Pattern: Run Long Operations in Background Thread

**Recommendation: Use `QThread` for long-running tasks**

```python
"""Example: Async calculation with progress updates."""

from PySide6.QtCore import QThread, Signal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.calculation_service import CalculationService


class CalculationWorker(QThread):
    """Worker thread for background calculations.
    
    Emits signals to update UI:
    - started: Calculation began
    - progress: Percentage complete
    - completed: Calculation finished (result dict)
    - error: Calculation failed (error message)
    """
    
    # Define signals (must be class attributes)
    started = Signal()
    progress = Signal(int)  # Percentage 0-100
    completed = Signal(dict)  # Result dictionary
    error = Signal(str)  # Error message
    
    def __init__(self, facility_code: str, date):
        """Initialize worker.
        
        Args:
            facility_code: Facility code
            date: Calculation date
        """
        super().__init__()
        self.facility_code = facility_code
        self.date = date
        self.calc_service = CalculationService()
    
    def run(self):
        """Run calculation in background thread.
        
        This method runs in a separate thread, so it can block
        without freezing the UI.
        
        Emit signals to notify UI of progress/completion.
        """
        self.started.emit()
        
        try:
            # This can take seconds without freezing UI
            self.progress.emit(50)
            result = self.calc_service.calculate_balance(self.facility_code, self.date)
            self.progress.emit(100)
            
            # Emit result to UI thread
            self.completed.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


# Usage in Dashboard:
def _on_calculate_clicked(self):
    """Start async calculation."""
    facility_code = self.ui.cbArea.currentText()
    selected_date = self.ui.dateEdit.date().toPython()
    
    # Create worker thread
    self._worker = CalculationWorker(facility_code, selected_date)
    
    # Connect signals to slots
    self._worker.started.connect(self._on_calculation_started)
    self._worker.progress.connect(self._on_calculation_progress)
    self._worker.completed.connect(self._on_calculation_completed)
    self._worker.error.connect(self._on_calculation_error)
    
    # Start thread (non-blocking)
    self._worker.start()

def _on_calculation_started(self):
    """Calculation started."""
    self.ui.btnCalculate.setEnabled(False)
    self.ui.lblStatus.setText("Calculating...")

def _on_calculation_progress(self, percent: int):
    """Update progress bar."""
    self.ui.progressBar.setValue(percent)

def _on_calculation_completed(self, result: dict):
    """Calculation finished - update UI."""
    self._display_results(result)
    self.ui.btnCalculate.setEnabled(True)
    self.ui.lblStatus.setText("Done")

def _on_calculation_error(self, error_msg: str):
    """Calculation failed."""
    QMessageBox.critical(self, "Error", error_msg)
    self.ui.btnCalculate.setEnabled(True)
    self.ui.lblStatus.setText("Error")
```

**Key Patterns:**
1. ✅ **QThread subclass** - Separate business logic from UI
2. ✅ **Custom signals** - Emit progress, completion, errors
3. ✅ **Non-blocking** - `worker.start()` doesn't block
4. ✅ **Signal connections** - Connect signals to UI slots for updates

---

## Custom Widgets

### Pattern: Create Reusable UI Components

**File: `ui/components/kpi_card_widget.py`**
```python
"""KPI Card Widget - Reusable component for displaying key metrics.

Example of a custom widget that can be used in multiple dashboards.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class KPICard(QWidget):
    """Reusable KPI display card.
    
    Shows a metric name and value with optional color coding.
    """
    
    def __init__(self, title: str, value: str, parent=None):
        """Initialize KPI card.
        
        Args:
            title: Metric name (e.g., "Closure Error %")
            value: Metric value (e.g., "2.3%")
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Title label
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        font_title = QFont()
        font_title.setPointSize(10)
        font_title.setBold(True)
        self.lbl_title.setFont(font_title)
        
        # Value label
        self.lbl_value = QLabel(value)
        self.lbl_value.setAlignment(Qt.AlignCenter)
        font_value = QFont()
        font_value.setPointSize(16)
        font_value.setBold(True)
        self.lbl_value.setFont(font_value)
        
        # Add to layout
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            KPICard {
                background-color: #F0F4F8;
                border-radius: 4px;
                padding: 10px;
                border: 1px solid #C5D3E6;
            }
        """)
    
    def set_value(self, value: str, color: str = None):
        """Update displayed value and optionally change color.
        
        Args:
            value: New value to display
            color: Optional text color ("#RRGGBB" format)
        """
        self.lbl_value.setText(value)
        if color:
            self.lbl_value.setStyleSheet(f"color: {color};")
    
    def set_status_color(self, is_valid: bool):
        """Color-code based on validity (green = valid, red = invalid).
        
        Args:
            is_valid: True for green, False for red
        """
        color = "#28A745" if is_valid else "#CC3333"
        self.set_value(self.lbl_value.text(), color)
```

**Usage in Dashboard:**
```python
def _setup_kpi_cards(self):
    """Create KPI cards for metrics display."""
    # Create cards
    self.kpi_error = KPICard("Closure Error %", "0.0%")
    self.kpi_efficiency = KPICard("Efficiency %", "0.0%")
    self.kpi_ratio = KPICard("Inflow/Outflow Ratio", "0.0")
    
    # Add to layout
    self.ui.kpiLayout.addWidget(self.kpi_error)
    self.ui.kpiLayout.addWidget(self.kpi_efficiency)
    self.ui.kpiLayout.addWidget(self.kpi_ratio)

def _display_results(self, result: dict):
    """Update KPI cards with results."""
    error_pct = result['error_percent']
    is_valid = result['is_valid']
    
    self.kpi_error.set_value(f"{error_pct:.2f}%")
    self.kpi_error.set_status_color(is_valid)
    
    self.kpi_efficiency.set_value(f"{result['kpis']['efficiency_percent']:.1f}%")
    self.kpi_ratio.set_value(f"{result['kpis']['inflow_outflow_ratio']:.2f}")
```

**Key Patterns:**
1. ✅ **Reusable components** - KPICard can be used in any dashboard
2. ✅ **Constructor injection** - Pass data as init parameters
3. ✅ **Update methods** - `set_value()`, `set_status_color()` for dynamic updates
4. ✅ **Styling** - Internal stylesheet keeps component self-contained

---

## Configuration & Dependency Injection

### Pattern: Type-Safe Configuration with Pydantic

**File: `src/core/config_manager.py`**
```python
"""Configuration Manager - YAML-based settings with Pydantic validation.

This is an improved version of the Tkinter config_manager.py with:
- Type safety via Pydantic
- Clear config structure
- Validation on load
- Default values
"""

from pydantic import BaseSettings, Field
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.app_logger import logger


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    path: str = Field(default="data/water_balance.db", description="Database file path")


class DataSourcesConfig(BaseSettings):
    """Data source paths and locations."""
    legacy_excel_path: str = Field(default="data/New Water Balance 20250930 Oct.xlsx")
    template_excel_path: str = Field(default="data/Water_Balance_TimeSeries_Template.xlsx")
    timeseries_excel_path: str = Field(default="data/Water_Balance_TimeSeries_Template.xlsx")
    inflow_codes_path: str = Field(default="data/templates/INFLOW_CODES_TEMPLATE.txt")
    outflow_codes_path: str = Field(default="data/templates/OUTFLOW_CODES_TEMPLATE_CORRECTED.txt")
    dam_recirculation_path: str = Field(default="data/templates/DAM_RECIRCULATION_TEMPLATE.txt")


class FeaturesConfig(BaseSettings):
    """Feature flags for experimental/optional features."""
    fast_startup: bool = Field(default=True, description="Load UI while DB loads in background")
    new_calculations: bool = Field(default=False, description="Use new calculation engine")
    auto_apply_pump_transfers: bool = Field(default=True)


class AppConfig(BaseSettings):
    """Complete application configuration (type-safe with defaults)."""
    app_name: str = Field(default="Water Balance System")
    version: str = Field(default="1.0.0")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    data_sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)


class ConfigManager:
    """Configuration manager with YAML loading and Pydantic validation."""
    
    def __init__(self, config_path: str = "config/app_config.yaml"):
        """Initialize config manager.
        
        Args:
            config_path: Path to YAML config file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        logger.info(f"Configuration loaded from {self.config_path}")
    
    def _load_config(self) -> AppConfig:
        """Load and validate YAML config file.
        
        Returns:
            AppConfig: Type-safe configuration object
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config invalid according to Pydantic schema
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return AppConfig()
        
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return AppConfig(**data)
    
    def get(self, key: str, default=None):
        """Get config value by dot-notation key.
        
        Args:
            key: Key path (e.g., 'database.path', 'features.fast_startup')
            default: Default value if key not found
        
        Returns:
            Config value or default
        
        Example:
            >>> config = ConfigManager()
            >>> db_path = config.get('database.path')
            >>> fast_startup = config.get('features.fast_startup')
        """
        try:
            parts = key.split('.')
            obj = self.config
            for part in parts:
                obj = getattr(obj, part)
            return obj
        except (AttributeError, KeyError):
            return default


# Singleton instance (reuse from Tkinter pattern)
_config_instance = None

def get_config() -> ConfigManager:
    """Get singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
```

**Usage:**
```python
from core.config_manager import get_config

# Get singleton config
config = get_config()

# Type-safe access
db_path = config.get('database.path')
fast_startup = config.get('features.fast_startup')
excel_path = config.get('data_sources.legacy_excel_path')

# Works with any nested path
if config.get('features.new_calculations', False):
    # Use new calculation engine
    pass
```

**Key Patterns:**
1. ✅ **Pydantic models** - Type validation on config load
2. ✅ **Nested config** - DataSourcesConfig, FeaturesConfig, etc.
3. ✅ **Defaults** - Field(..., default="value") for sensible defaults
4. ✅ **Dot-notation access** - `config.get('features.fast_startup')`
5. ✅ **Singleton pattern** - Single config instance (like Tkinter)

---

## Testing Patterns

### Pattern: Unit Tests for Services

**File: `tests/test_services/test_calculation_service.py`**
```python
"""Unit tests for calculation service.

These tests are FAST and ISOLATED - they don't use real Excel/DB,
they use mocks and fixtures instead.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date

from services.calculation_service import CalculationService
from services.excel_service import ExcelService
from services.database_service import DatabaseService


@pytest.fixture
def mock_excel_service():
    """Mock Excel service for testing."""
    mock = Mock(spec=ExcelService)
    mock.load_meter_readings.return_value = {
        'storage_start': 100000,
        'storage_end': 95000,
        'rainfall': 50000,
        'borehole': 30000,
        'mill_consumption': 60000,
        'evaporation': 20000,
    }
    return mock


@pytest.fixture
def mock_db_service():
    """Mock database service for testing."""
    mock = Mock(spec=DatabaseService)
    mock.get_facility.return_value = {
        'code': 'UG2N',
        'name': 'Underground 2 North',
        'capacity_m3': 150000,
        'inflow_sources': ['rainfall', 'borehole'],
        'outflow_sinks': ['mill_consumption', 'evaporation'],
    }
    return mock


@pytest.fixture
def calc_service(mock_excel_service, mock_db_service):
    """Create calculation service with mocked dependencies."""
    service = CalculationService()
    service.excel_service = mock_excel_service
    service.db_service = mock_db_service
    return service


def test_calculate_balance_basic(calc_service):
    """Test basic balance calculation.
    
    Given: Known inflows/outflows/storage change
    When: Calculate balance
    Then: Result matches expected formula (inflows = outflows + storage_change + error)
    """
    result = calc_service.calculate_balance('UG2N', date(2025, 3, 1))
    
    # Expected: inflows=80k, outflows=80k, storage=5k → error=5k
    assert result['facility_code'] == 'UG2N'
    assert result['fresh_inflows_m3'] == 80000  # rainfall + borehole
    assert result['outflows_m3'] == 80000  # mill + evaporation
    assert result['storage_change_m3'] == 5000  # 100k - 95k
    assert result['error_m3'] == -5000  # Should be -5k (small error)
    assert result['error_percent'] == pytest.approx(-6.25, rel=1e-2)
    assert result['is_valid'] is False  # error > 5%


def test_calculate_balance_caching(calc_service):
    """Test that results are cached (avoid re-calculation).
    
    Given: Calculate balance twice with same inputs
    When: Second call
    Then: Should return cached result without calling Excel/DB
    """
    # First call - should hit services
    result1 = calc_service.calculate_balance('UG2N', date(2025, 3, 1))
    
    # Second call - should use cache (service calls not increased)
    result2 = calc_service.calculate_balance('UG2N', date(2025, 3, 1))
    
    # Results should be identical
    assert result1 == result2
    
    # Service should be called only once for first call
    # (implementation detail - verify with call counts if needed)


def test_calculate_balance_facility_not_found(calc_service, mock_db_service):
    """Test error handling when facility not found."""
    mock_db_service.get_facility.return_value = None
    
    with pytest.raises(ValueError, match="Facility 'INVALID' not found"):
        calc_service.calculate_balance('INVALID', date(2025, 3, 1))


def test_calculate_balance_excel_error(calc_service, mock_excel_service):
    """Test error handling when Excel data missing."""
    mock_excel_service.load_meter_readings.return_value = None
    
    with pytest.raises(ValueError, match="No meter readings"):
        calc_service.calculate_balance('UG2N', date(2025, 3, 1))


def test_clear_cache(calc_service):
    """Test cache invalidation after Excel reload."""
    # Calculate once (caches result)
    calc_service.calculate_balance('UG2N', date(2025, 3, 1))
    assert len(calc_service._cache) == 1
    
    # Clear cache
    calc_service.clear_cache()
    assert len(calc_service._cache) == 0
```

**Key Patterns:**
1. ✅ **Fixtures** - Reusable mock services
2. ✅ **Unit tests** - Test in isolation (no real Excel/DB)
3. ✅ **Mock objects** - Return known data for consistent tests
4. ✅ **Error cases** - Test exceptions with `pytest.raises`
5. ✅ **Cache verification** - Ensure caching works correctly

### Pattern: UI Tests (Mock Services)

**File: `tests/test_ui/test_calculations_dashboard.py`**
```python
"""Unit tests for Calculations Dashboard.

Tests UI interactions without requiring GUI rendering (headless).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date

# Note: PySide6 GUI tests can be tricky - use headless rendering or mock
# pytest-qt plugin helps: pip install pytest-qt


@pytest.fixture
def mock_calculation_service():
    """Mock calculation service."""
    return Mock()


@pytest.fixture
def dashboard(mock_calculation_service, qtbot):
    """Create dashboard with mocked service.
    
    Note: qtbot is provided by pytest-qt plugin
    """
    with patch('ui.dashboards.calculations_dashboard.CalculationService', 
               return_value=mock_calculation_service):
        from ui.dashboards.calculations_dashboard import CalculationsDashboard
        dashboard = CalculationsDashboard()
        qtbot.addWidget(dashboard)
        return dashboard


def test_calculate_button_click(dashboard, mock_calculation_service, qtbot):
    """Test Calculate button click triggers service call."""
    # Set up mock result
    mock_calculation_service.calculate_balance.return_value = {
        'facility_code': 'UG2N',
        'fresh_inflows_m3': 80000,
        'outflows_m3': 80000,
        'storage_change_m3': 5000,
        'error_m3': -5000,
        'error_percent': -6.25,
        'is_valid': False,
        'kpis': {}
    }
    
    # Simulate clicking Calculate button
    dashboard.ui.btnCalculate.click()
    
    # Give async operation time to complete
    qtbot.wait(100)
    
    # Verify service was called
    mock_calculation_service.calculate_balance.assert_called()
    
    # Verify results displayed in table
    assert dashboard.ui.tableResults.rowCount() > 0
```

---

## Summary

These patterns form the foundation of the PySide6 water balance application:

| Pattern | Usage | Key Benefit |
|---------|-------|------------|
| **Qt Designer Integration** | Load .ui files, connect signals | Separation of UI design from code |
| **Service Layer** | Business logic in services | Reusable, testable, no UI dependencies |
| **Signal/Slot** | UI event communication | Decoupled, clean architecture |
| **Async Calculations** | QThread for long operations | Non-blocking, responsive UI |
| **Custom Widgets** | Reusable UI components | DRY principle, consistency |
| **Configuration** | Pydantic-validated config | Type safety, clear defaults |
| **Testing** | Mocked services, fixtures | Fast, isolated unit tests |

**Next Steps:**
1. Create the directory structure following the proposed layout
2. Copy database and service files from Tkinter
3. Design first dashboard in Qt Designer
4. Implement CalculationsDashboard following the patterns above
5. Add tests as you go

---

**For questions about specific patterns, refer to the corresponding section or consult the PySide6 documentation.**
