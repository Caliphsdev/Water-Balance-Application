"""
Calculations Dashboard Controller (CALCULATION ENGINE UI).

Purpose:
- Load the compiled calculation.ui file
- Handle user inputs (month/year selection)
- Display water balance calculation results in 4 essential tabs
- Connect Calculate button to calculation engine

Data Flow:
1. User selects month/year and clicks "Calculate Balance"
2. calculate_btn.clicked → _on_calculate()
3. _on_calculate() → calls BalanceService.calculate_for_date()
4. Results returned as BalanceResult with all balance data
5. _populate_tabs() distributes data to each tab
6. UI displays results with KPI cards and status indicators

Tab Structure (Streamlined):
- Tab 0: System Balance - main balance results with KPI cards
- Tab 1: Recycled Water - recycled water metrics and efficiency
- Tab 2: Data Quality - validation results and warnings
- Tab 3: Days of Operation - water runway analysis with projections

Removed Tabs (now on dedicated pages):
- Inputs Audit (low value)
- Manual Inputs (not implemented)
- Storage & Dams (duplicates Storage Facilities page)
- Facility Flows (duplicates Flow Diagram page)

Dependencies:
- services.calculation.balance_service: Main calculation orchestrator
- services.calculation.days_of_operation_service: Water runway analysis
- services.calculation.models: BalanceResult, CalculationPeriod, etc.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem, QProgressBar,
    QGraphicsDropShadowEffect, QFileDialog, QLineEdit, QPushButton, QToolTip
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from ui.dashboards.generated_ui_calculation import Ui_Form
import calendar
from datetime import date, datetime
import logging

# Import calculation services
from services.calculation.balance_service import get_balance_service, BalanceService, EXCEL_COLUMNS
from services.calculation.days_of_operation_service import get_days_of_operation_service
from services.calculation.models import BalanceResult, CalculationPeriod, DataQualityFlags

logger = logging.getLogger(__name__)

PALETTE = {
    "text": "#0f172a",
    "muted": "#64748b",
    "muted_light": "#94a3b8",
    "border": "#e2e8f0",
    "surface": "#ffffff",
    "surface_alt": "#f8fafc",
    "surface_soft": "#f1f5f9",
    "accent": "#1d4ed8",
    "success": "#16a34a",
    "success_bg": "#ecfdf5",
    "info": "#2563eb",
    "info_bg": "#eff6ff",
    "warning": "#d97706",
    "warning_bg": "#fffbeb",
    "danger": "#dc2626",
    "danger_bg": "#fef2f2",
}

STATUS_THEMES = {
    "healthy": {"color": PALETTE["success"], "gradient": ("stop:0 #14532d", "stop:1 #16a34a")},
    "moderate": {"color": PALETTE["info"], "gradient": ("stop:0 #1e3a8a", "stop:1 #2563eb")},
    "warning": {"color": PALETTE["warning"], "gradient": ("stop:0 #92400e", "stop:1 #d97706")},
    "critical": {"color": PALETTE["danger"], "gradient": ("stop:0 #991b1b", "stop:1 #dc2626")},
}


class CalculationPage(QWidget):
    """Water Balance Calculations Dashboard (MAIN CALCULATION UI).
    
    This controller loads the calculation.ui and manages:
    - Date selection (month/year comboboxes)
    - Calculate button action
    - Tab population with calculation results
    - Data display formatting
    
    Tabs (Streamlined - 4 essential tabs):
    1. System Balance - main results with KPI cards and balance summary
    2. Recycled Water - recycled water metrics and efficiency ratios
    3. Data Quality - validation checks, warnings, and data source flags
    4. Days of Operation - water runway analysis with depletion projections
    
    Attributes:
        balance_service: BalanceService singleton for calculations
        days_service: DaysOfOperationService for runway analysis
        current_results: Latest BalanceResult from calculation
    """
    
    def __init__(self, parent=None):
        """Initialize Calculations Dashboard.
        
        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        
        # Load the compiled UI file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._apply_layout_refresh()
        
        # Get the calculation service singleton
        self._balance_service: BalanceService = None  # Lazy-loaded
        
        # Store current calculation results
        self.current_results: BalanceResult = None
        
        # Track if tabs are set up
        self._tabs_initialized = False
        
        # Connect signals to slots
        self._connect_signals()

        # Add direct Meter Readings Excel selector to this page
        self._setup_excel_loader_controls()
        
        # Initialize tabs with placeholder content
        self._setup_tabs()
        
        logger.info("CalculationPage initialized")

    def _apply_layout_refresh(self) -> None:
        """Apply compact, consistent page structure without changing logic."""
        if hasattr(self.ui, "gridLayout"):
            self.ui.gridLayout.setContentsMargins(12, 10, 12, 10)
            self.ui.gridLayout.setVerticalSpacing(8)

        # Page title/subtitle consistency with other dashboards
        if hasattr(self.ui, "label_2"):
            self.ui.label_2.setObjectName("label_title")
        if hasattr(self.ui, "label_3"):
            self.ui.label_3.setObjectName("label_subtitle")
        if hasattr(self.ui, "header_frame"):
            self.ui.header_frame.setObjectName("calc_page_header")
            self.ui.header_frame.setMinimumHeight(84)
            self.ui.header_frame.setMaximumHeight(96)
        if hasattr(self.ui, "verticalLayout"):
            self.ui.verticalLayout.setContentsMargins(10, 6, 10, 6)
            self.ui.verticalLayout.setSpacing(4)

        # Compact control bar
        if hasattr(self.ui, "frame"):
            self.ui.frame.setObjectName("calc_control_bar")
            # Two rows now exist (Excel selector + month/year controls), so keep enough height.
            self.ui.frame.setMinimumHeight(112)
            self.ui.frame.setMaximumHeight(132)
        if hasattr(self.ui, "verticalLayout_2"):
            self.ui.verticalLayout_2.setContentsMargins(10, 8, 10, 8)
            self.ui.verticalLayout_2.setSpacing(8)
        if hasattr(self.ui, "label_5"):
            self.ui.label_5.setObjectName("calc_control_section")
        if hasattr(self.ui, "comboBox"):
            self.ui.comboBox.setMinimumWidth(88)
        if hasattr(self.ui, "comboBox_2"):
            self.ui.comboBox_2.setMinimumWidth(88)
        if hasattr(self.ui, "pushButton"):
            self.ui.pushButton.setText("Calculate Balance")
            self.ui.pushButton.setObjectName("primaryButton")
            self.ui.pushButton.setMinimumHeight(29)
            self.ui.pushButton.setMaximumHeight(31)
            self.ui.pushButton.setMinimumWidth(148)
            # Force readable style regardless of inherited/generated object-name rules.
            self.ui.pushButton.setStyleSheet(
                "background-color:#1f3a5f; color:#ffffff; border:1px solid #1f3a5f; "
                "border-radius:8px; padding:4px 12px; font-weight:700;"
            )

        # Tabs polish
        if hasattr(self.ui, "tabWidget"):
            self.ui.tabWidget.setObjectName("calc_tab_widget")
    
    @property
    def balance_service(self) -> BalanceService:
        """Lazy-load the balance service singleton.
        
        Returns:
            BalanceService instance for calculations
        """
        if self._balance_service is None:
            self._balance_service = get_balance_service()
        return self._balance_service
    
    def _connect_signals(self):
        """Connect UI signals to slot methods (SIGNAL/SLOT PATTERN).
        
        Connects:
        - Calculate button (pushButton) → _on_calculate()
        - Year combobox changes → update calculation date
        - Month combobox changes → update calculation date
        """
        # Connect Calculate button
        if hasattr(self.ui, 'pushButton'):
            self.ui.pushButton.clicked.connect(self._on_calculate)
        
        # Connect date selectors (update when user changes month/year)
        if hasattr(self.ui, 'comboBox'):  # Year combobox
            self.ui.comboBox.currentTextChanged.connect(self._on_date_changed)
        
        if hasattr(self.ui, 'comboBox_2'):  # Month combobox
            self.ui.comboBox_2.currentTextChanged.connect(self._on_date_changed)

    def _setup_excel_loader_controls(self) -> None:
        """Add Meter Readings Excel path selector inside calculations control bar."""
        if not hasattr(self.ui, "verticalLayout_2"):
            return

        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel("Meter Readings Excel:")
        label.setObjectName("calc_excel_label")
        row.addWidget(label)

        self.calc_excel_path_edit = QLineEdit()
        self.calc_excel_path_edit.setObjectName("calc_excel_path_edit")
        self.calc_excel_path_edit.setReadOnly(True)
        self.calc_excel_path_edit.setPlaceholderText("No file selected")
        self.calc_excel_path_edit.setMinimumHeight(28)
        row.addWidget(self.calc_excel_path_edit, 1)

        self.calc_excel_select_btn = QPushButton("Select File")
        self.calc_excel_select_btn.setObjectName("secondaryButton")
        self.calc_excel_select_btn.setMinimumHeight(28)
        self.calc_excel_select_btn.setMaximumHeight(30)
        self.calc_excel_select_btn.clicked.connect(self._on_select_meter_excel)
        row.addWidget(self.calc_excel_select_btn)

        self.ui.verticalLayout_2.insertLayout(1, row)
        self._refresh_meter_excel_path_display()

    def _refresh_meter_excel_path_display(self) -> None:
        """Refresh the on-page Meter Readings Excel path display."""
        if not hasattr(self, "calc_excel_path_edit"):
            return

        try:
            from services.excel_manager import get_excel_manager
            excel_mgr = get_excel_manager()
            path = excel_mgr.get_meter_readings_path() or ""
            path_text = str(path) if path else ""
            self.calc_excel_path_edit.setText(path_text)
            self.calc_excel_path_edit.setToolTip(path_text)
        except Exception as exc:
            logger.warning(f"Unable to read meter readings path: {exc}")
            self.calc_excel_path_edit.setText("")
            self.calc_excel_path_edit.setToolTip("")

    def _on_select_meter_excel(self) -> None:
        """Let user select Meter Readings Excel file used by calculations."""
        try:
            current_dir = ""
            if hasattr(self, "calc_excel_path_edit") and self.calc_excel_path_edit.text():
                current_dir = self.calc_excel_path_edit.text()

            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Meter Readings Excel File",
                current_dir,
                "Excel Files (*.xlsx *.xls *.xlsm);;All Files (*.*)"
            )
            if not file_path:
                return

            from services.excel_manager import get_excel_manager
            excel_mgr = get_excel_manager()
            excel_mgr.set_meter_readings_path(file_path)
            # Backward-compatible cache clear across ExcelManager versions.
            if hasattr(excel_mgr, "clear_meter_cache"):
                excel_mgr.clear_meter_cache()
            elif hasattr(excel_mgr, "clear_meter_readings_cache"):
                excel_mgr.clear_meter_readings_cache()
            elif hasattr(excel_mgr, "clear_all_caches"):
                excel_mgr.clear_all_caches()
            self._refresh_meter_excel_path_display()

            QMessageBox.information(
                self,
                "Excel File Updated",
                "Meter Readings Excel file updated successfully.\n"
                "You can now run Calculate Balance using this file."
            )
            logger.info(f"Meter Readings Excel updated from Calculations page: {file_path}")
        except Exception as exc:
            logger.error(f"Failed to set Meter Readings Excel from Calculations page: {exc}", exc_info=True)
            QMessageBox.critical(
                self,
                "Excel Selection Error",
                f"Failed to set Meter Readings Excel file:\n\n{exc}"
            )
    
    def _on_date_changed(self):
        """Handle date selection change (SLOT).
        
        Called when user changes month or year combobox.
        Clears previous results to indicate recalculation needed.
        """
        # Clear previous results display to show recalculation is needed
        if self.current_results is not None:
            # Could add visual indicator that results are stale
            pass
    
    def _on_calculate(self):
        """Handle Calculate Balance button click (MAIN ACTION).
        
        Workflow:
        1. Get selected month/year from comboboxes
        2. Validate input
        3. CHECK DATA QUALITY & REQUIRED FILES (NEW)
        4. Call BalanceService.calculate_for_date()
        5. Populate tabs with BalanceResult
        6. Show success/error message
        """
        # Get selected month and year
        try:
            year_str = self.ui.comboBox.currentText()  # e.g., "2025"
            month_str = self.ui.comboBox_2.currentText()  # e.g., "Jan"
            
            # Validate inputs
            if not year_str or not month_str:
                QMessageBox.warning(self, "Input Required", 
                    "Please select both month and year.")
                return
            
            # Convert month abbreviation to number
            try:
                month = list(calendar.month_abbr).index(month_str)
            except ValueError:
                QMessageBox.warning(self, "Invalid Month", 
                    f"Invalid month selected: {month_str}")
                return
            
            year = int(year_str)
            
            # VALIDATE DATA QUALITY BEFORE CALCULATION (NEW)
            data_check = self._validate_data_completeness()
            if not data_check['is_complete']:
                # Show warning with missing items
                missing_list = "\n".join([f"  • {item}" for item in data_check['missing']])
                response = QMessageBox.warning(
                    self, 
                    "⚠ Missing Data",
                    f"The following required data is missing or incomplete:\n\n{missing_list}\n\n"
                    f"This will result in INCORRECT calculation results.\n\n"
                    f"Do you want to continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if response != QMessageBox.Yes:
                    logger.warning(f"User cancelled calculation due to missing data")
                    return
            
            # Log the calculation request
            logger.info(f"User requested balance calculation for {month_str} {year}")
            
            # Disable button during calculation
            if hasattr(self.ui, 'pushButton'):
                self.ui.pushButton.setEnabled(False)
                self.ui.pushButton.setText("Calculating...")
            
            try:
                # Call the balance service
                result = self.balance_service.calculate_for_date(
                    month=month,
                    year=year,
                    mode="REGULATOR"
                )
                
                # Store result for other tabs
                self.current_results = result
                
                # Populate tabs with real data
                self._populate_tabs_from_result(result)
                
                # Show success message with summary (updated to include data quality warnings)
                status_icon = "✓" if result.is_balanced else "⚠"
                summary_msg = (
                    f"{status_icon} Water Balance for {result.period.period_label}\n\n"
                    f"Fresh Inflows:  {result.inflows.total_m3:,.0f} m³\n"
                    f"Total Outflows: {result.outflows.total_m3:,.0f} m³\n"
                    f"Storage Change: {result.storage.delta_m3:,.0f} m³\n"
                    f"Balance Error:  {result.error_pct:.2f}%\n\n"
                    f"Status: {result.status}"
                )
                
                # Add quality warnings if present
                if result.quality_flags and result.quality_flags.warnings:
                    summary_msg += (
                        f"\n\n⚠ Data Quality Warnings ({len(result.quality_flags.warnings)}):\n"
                        + "\n".join([f"  • {w}" for w in list(result.quality_flags.warnings)[:5]])
                    )
                    if len(result.quality_flags.warnings) > 5:
                        summary_msg += f"\n  ... and {len(result.quality_flags.warnings) - 5} more"
                
                QMessageBox.information(self, "Calculation Complete", summary_msg)

                
                logger.info(f"Balance calculation complete: {result.status} "
                           f"(error={result.error_pct:.1f}%)")
                
            finally:
                # Re-enable button
                if hasattr(self.ui, 'pushButton'):
                    self.ui.pushButton.setEnabled(True)
                    self.ui.pushButton.setText("Calculate Balance")
            
        except Exception as e:
            logger.error(f"Balance calculation failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Calculation Error", 
                f"Balance calculation failed:\n\n{str(e)}\n\n"
                f"Check the logs for details.")
            
            # Re-enable button on error
            if hasattr(self.ui, 'pushButton'):
                self.ui.pushButton.setEnabled(True)
                self.ui.pushButton.setText("Calculate Balance")
    
    def _validate_data_completeness(self) -> dict:
        """Validate that all required data sources are available (DATA QUALITY CHECK).
        
        Checks:
        1. Excel file loaded with Meter Readings data
        2. Environmental data (rainfall, evaporation) exists
        3. Storage facilities configured
        4. At least one inflow source available
        5. At least one outflow calculation possible
        
        Returns:
            Dict with 'is_complete' bool and 'missing' list of missing items
        """
        missing = []
        
        try:
            from services.excel_manager import get_excel_manager
            from database.db_manager import DatabaseManager
            
            excel_mgr = get_excel_manager()
            db = DatabaseManager()
            
            # Check 1: Excel Meter Readings loaded
            try:
                # First check if file exists
                if not excel_mgr.meter_readings_exists():
                    missing.append("Excel Meter Readings file not found")
                else:
                    # Load and validate data
                    meter_data = excel_mgr.load_meter_readings()
                    if meter_data is None or meter_data.empty:
                        missing.append("Excel Meter Readings data (tonnes milled, water consumption, etc.) is empty")
                    else:
                        # Check that key columns exist
                        required_cols = ['Tonnes Milled', 'Total Water Consumption', 'Total Recycled Water']
                        for col in required_cols:
                            if col not in meter_data.columns:
                                missing.append(f"Excel Meter Readings column missing: {col}")
            except Exception as e:
                missing.append(f"Excel file access error: {str(e)}")
            
            # Check 2: Environmental data
            try:
                conn = db.get_connection()
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM environmental_data LIMIT 1")
                count = cursor.fetchone()['cnt']
                conn.close()
                if count == 0:
                    missing.append("Environmental data (rainfall, evaporation) - Add via Monitoring page")
            except Exception as e:
                missing.append(f"Environmental data access: {str(e)}")
            
            # Check 3: Storage facilities
            try:
                conn = db.get_connection()
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM storage_facilities WHERE status='active'")
                count = cursor.fetchone()['cnt']
                conn.close()
                if count == 0:
                    missing.append("Storage facilities configured - Create facilities in Storage page")
            except Exception as e:
                missing.append(f"Storage facilities access: {str(e)}")
            
            return {
                'is_complete': len(missing) == 0,
                'missing': missing
            }
            
        except Exception as e:
            logger.warning(f"Data validation check error: {e}")
            return {
                'is_complete': False,
                'missing': [f"Data validation error: {str(e)}"]
            }

    
    def _setup_tabs(self):
        """Initialize 4 essential tabs with placeholder content (INITIALIZATION).
        
        Creates tab structure and adds placeholder labels/tables.
        Each tab will be populated with real data in _populate_tabs().
        
        Tab Mapping (UI has 8 tabs, we hide 4):
        - Tab 0: System Balance ✓ KEEP
        - Tab 1: Recycled Water ✓ KEEP
        - Tab 2: Data Quality ✓ KEEP
        - Tab 3: Inputs Audit → HIDE (low value)
        - Tab 4: Manual Inputs → HIDE (not implemented)
        - Tab 5: Storage & Dams → HIDE (duplicates Storage Facilities page)
        - Tab 6: Days of Operation ✓ KEEP (move to position 3)
        - Tab 7: Facility Flows → HIDE (duplicates Flow Diagram page)
        """
        # Remove tabs we don't need (remove from end to preserve indices)
        # After removal, Days of Operation (originally tab 6) becomes tab 3
        tabs_to_remove = [7, 5, 4, 3]  # Facility Flows, Storage & Dams, Manual Inputs, Inputs Audit
        for tab_index in tabs_to_remove:
            if self.ui.tabWidget.count() > tab_index:
                self.ui.tabWidget.removeTab(tab_index)
        
        # Rename remaining tabs (now 0, 1, 2, 3)
        tab_names = [
            "System Balance",
            "Recycled Water", 
            "Data Quality",
            "Days of Operation"
        ]
        for i, name in enumerate(tab_names):
            if i < self.ui.tabWidget.count():
                self.ui.tabWidget.setTabText(i, name)
        
        # Setup remaining tabs
        # Tab 0: System Balance
        self._setup_system_balance_tab()
        
        # Tab 1: Recycled Water
        self._setup_recycled_water_tab()
        
        # Tab 2: Data Quality
        self._setup_data_quality_tab()
        
        # Tab 3: Days of Operation (was tab 6)
        self._setup_days_of_operation_tab()
    
    def _setup_system_balance_tab(self):
        """Setup System Balance (Regulator) tab - Main balance results (TAB 0).
        
        Display:
        - Fresh Inflows (m³)
        - Total Outflows (m³)
        - ΔStorage (m³)
        - Balance Error (m³)
        - Error % 
        - Status (GREEN/RED)
        """
        tab = self.ui.tabWidget.widget(0)
        if not tab:
            return
        
        layout = QVBoxLayout(tab)
        
        # Add placeholder labels (will update in _populate_tabs)
        label = QLabel("System Balance Results\n(Click Calculate to populate)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("")
        layout.addWidget(label)
        
        tab.setLayout(layout)
    
    def _setup_recycled_water_tab(self):
        """Setup Recycled Water tab - RWD and recycled water metrics (TAB 1)."""
        tab = self.ui.tabWidget.widget(1)
        if not tab:
            return
        
        layout = QVBoxLayout(tab)
        label = QLabel("Recycled Water Information\n(Data will appear here)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("")
        layout.addWidget(label)
        
        tab.setLayout(layout)
    
    def _setup_data_quality_tab(self):
        """Setup Data Quality tab - Validation and quality checks (TAB 2)."""
        tab = self.ui.tabWidget.widget(2)
        if not tab:
            return
        
        layout = QVBoxLayout(tab)
        label = QLabel("Data Quality Checks\n(Validation results will appear here)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("")
        layout.addWidget(label)
        
        tab.setLayout(layout)
    
    def _setup_days_of_operation_tab(self):
        """Setup Days of Operation tab - Water runway analysis (TAB 3).
        
        Now at index 3 after removing unused tabs.
        Shows water runway projections with depletion timeline.
        """
        tab = self.ui.tabWidget.widget(3)
        if not tab:
            return
        
        layout = QVBoxLayout(tab)
        label = QLabel("Days of Operation Analysis\n(How long water will last at current usage)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("")
        layout.addWidget(label)
        
        tab.setLayout(layout)
    
    def _populate_tabs_from_result(self, result: 'BalanceResult'):
        """Populate all tabs with calculation results (MAIN UPDATE METHOD).
        
        Called after successful balance calculation.
        Updates each tab with relevant data from BalanceResult model.
        
        Args:
            result: BalanceResult Pydantic model containing:
                - period: CalculationPeriod with month/year/date
                - inflows: InflowResult with component breakdown
                - outflows: OutflowResult with component breakdown
                - storage: StorageChange with delta_m3
                - balance_error_m3: closure error
                - error_pct: closure error percentage
                - status: 'GREEN' or 'RED'
                - kpis: KPIResult with efficiency metrics
                - quality: DataQualityFlags for data validation
                
        Note:
            Stores result in self.current_result for export/reuse.
            Each _update_* method handles its own tab.
        """
        # Store result for potential export/reuse
        self.current_results = result
        
        # Update Tab 0: System Balance - main summary with KPIs
        self._update_system_balance(result)
        
        # Update Tab 1: Recycled Water - efficiency metrics
        self._update_recycled_water(result)
        
        # Update Tab 2: Data Quality - validation flags and warnings
        self._update_data_quality(result)
        
        # Update Tab 3: Days of Operation - water runway
        self._update_days_of_operation(result)
    
    def _update_system_balance(self, result: 'BalanceResult'):
        """Update System Balance tab with modern card-based layout (TAB 0 UPDATE).
        
        Creates a professional horizontal layout with:
        - Hero header with period and status
        - Three-column card layout (Inflows | Outflows | Storage)
        - Bottom closure summary with status indicator
        - Color-coded cards with shadow effects
        
        Args:
            result: BalanceResult model with all calculation outputs
        """
        tab = self.ui.tabWidget.widget(0)
        if not tab or not tab.layout():
            return
        
        # Clear old content
        while tab.layout().count():
            item = tab.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create scroll area for responsive layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("")
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Determine status
        is_balanced = result.error_pct <= 5.0
        status_color = PALETTE["success"] if is_balanced else PALETTE["danger"]
        status_text = "✓ BALANCED" if is_balanced else "✗ UNBALANCED"
        status_bg = PALETTE["success_bg"] if is_balanced else PALETTE["danger_bg"]
        
        # ═══════════════════════════════════════════════════════════════════
        # HERO HEADER
        # ═══════════════════════════════════════════════════════════════════
        header = QFrame()
        header.setObjectName("calc_balance_header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(10)
        
        # Left: structured title + period (cleaner than stacked single text block)
        title_wrap = QWidget(header)
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        balance_title = QLabel("System Balance")
        balance_title.setObjectName("calc_balance_title")
        period_label = QLabel(result.period.period_label.upper())
        period_label.setObjectName("calc_balance_period")
        title_layout.addWidget(balance_title)
        title_layout.addWidget(period_label)
        header_layout.addWidget(title_wrap)
        
        header_layout.addStretch()
        
        # Right: Status badge
        status_badge = QLabel(f"  {status_text}  ")
        status_badge.setObjectName("calc_status_badge")
        header_layout.addWidget(status_badge)
        
        # Error badge
        error_badge = QLabel(f"  Error: {result.error_pct:.1f}%  ")
        error_badge.setObjectName("calc_error_badge")
        header_layout.addWidget(error_badge)
        
        main_layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════════════
        # THREE-COLUMN CARDS ROW
        # ═══════════════════════════════════════════════════════════════════
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        
        # --- INFLOWS CARD ---
        # Get abstraction breakdown: surface_water (rivers) + groundwater (boreholes)
        surface_water = result.inflows.components.get('surface_water', 0.0)
        groundwater = result.inflows.components.get('groundwater', 0.0)
        dewatering = result.inflows.components.get('dewatering', 0.0)
        
        inflows_card = self._create_balance_card(
            title="💧 FRESH INFLOWS",
            subtitle="Natural Water Entering System",
            items=[
                ("🌧️ Rainfall", result.inflows.rainfall_m3, PALETTE["accent"]),
                ("🏞️ Rivers", surface_water, PALETTE["info"]),
                ("🕳️ Boreholes", groundwater, PALETTE["info"]),
                ("⛏️ Dewatering", dewatering, PALETTE["info"]),
                ("⛏️ Ore Moisture", result.inflows.ore_moisture_m3, PALETTE["info"]),
                ("📥 Other Sources", result.inflows.other_m3, PALETTE["muted"]),
            ],
            total=result.inflows.total_m3,
            accent_color=PALETTE["accent"],
            bg_gradient=("from surface to surface", PALETTE["surface"], PALETTE["surface"]),
            card_object_name="calc_card_inflows",
        )
        cards_row.addWidget(inflows_card)
        
        # --- OUTFLOWS CARD ---
        outflows_card = self._create_balance_card(
            title="🔥 OUTFLOWS",
            subtitle="Water Leaving System",
            items=[
                ("☀️ Evaporation", result.outflows.evaporation_m3, PALETTE["warning"]),
                ("💧 Seepage", result.outflows.seepage_m3, PALETTE["danger"]),
                ("🌫️ Dust Suppression", result.outflows.dust_suppression_m3, PALETTE["muted"]),
                ("🏭 Tailings Lockup", result.outflows.tailings_lockup_m3, PALETTE["info"]),
                ("📤 Other Losses", result.outflows.other_m3, PALETTE["muted"]),
            ],
            total=result.outflows.total_m3,
            accent_color=PALETTE["warning"],
            bg_gradient=("from surface to surface", PALETTE["surface"], PALETTE["surface"]),
            card_object_name="calc_card_outflows",
        )
        cards_row.addWidget(outflows_card)
        
        # --- STORAGE CARD ---
        delta = result.storage.delta_m3
        delta_icon = "📈" if delta >= 0 else "📉"
        delta_color = PALETTE["success"] if delta >= 0 else PALETTE["danger"]
        
        # Build storage items including system totals
        storage_items = [
            ("📂 Opening Storage", result.storage.opening_m3, PALETTE["muted"]),
            ("📁 Closing Storage", result.storage.closing_m3, PALETTE["success"]),
        ]
        
        # Build facility breakdown for expandable section
        facility_breakdown = []
        if result.storage.facility_breakdown:
            for fac in result.storage.facility_breakdown:
                fac_delta_icon = "▲" if fac.delta_m3 >= 0 else "▼"
                fac_color = PALETTE["success"] if fac.delta_m3 >= 0 else PALETTE["danger"]
                facility_breakdown.append({
                    'name': fac.facility_name or fac.facility_code,
                    'delta': fac.delta_m3,
                    'color': fac_color,
                    'icon': fac_delta_icon
                })
        
        storage_card = self._create_storage_card(
            title="🏊 STORAGE CHANGE",
            subtitle="System Water Reserves",
            items=storage_items,
            total=delta,
            total_label=f"{delta_icon} Delta (ΔS)",
            facility_breakdown=facility_breakdown,
            accent_color=PALETTE["success"],
            bg_gradient=("from surface to surface", PALETTE["surface"], PALETTE["surface"]),
            card_object_name="calc_card_storage",
        )
        cards_row.addWidget(storage_card)
        
        main_layout.addLayout(cards_row)
        
        # ═══════════════════════════════════════════════════════════════════
        # CLOSURE EQUATION FOOTER
        # ═══════════════════════════════════════════════════════════════════
        footer = QFrame()
        footer.setObjectName("calc_equation_strip")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 10, 12, 10)
        footer_layout.setSpacing(10)
        
        # Equation visualization
        eq_parts = [
            (f"{result.inflows.total_m3:,.0f}", "Fresh IN", PALETTE["accent"]),
            ("−", "", PALETTE["muted"]),
            (f"{result.outflows.total_m3:,.0f}", "Outflows", PALETTE["warning"]),
            ("−", "", PALETTE["muted"]),
            (f"{result.storage.delta_m3:+,.0f}", "ΔStorage", PALETTE["success"]),
            ("=", "", PALETTE["muted"]),
            (f"{result.balance_error_m3:+,.0f}", "Error", status_color),
        ]
        
        for value, label, color in eq_parts:
            part_widget = QLabel(
                f"<div style='text-align:center;'>"
                f"<span style='font-size:18px;font-weight:700;line-height:1.2;color:{color};'>{value}</span><br/>"
                f"<span style='font-size:11px;line-height:1.2;color:{PALETTE['muted']};'>{label}</span></div>"
            )
            part_widget.setObjectName("calc_equation_part")
            part_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            part_widget.setMinimumHeight(58)
            footer_layout.addWidget(part_widget)
        
        main_layout.addWidget(footer)
        
        # Quality note
        note = QLabel("💡 <i>Error &lt; 5% indicates good data quality. Higher errors suggest measurement issues or missing data.</i>")
        note.setObjectName("calc_quality_note")
        note.setWordWrap(True)
        main_layout.addWidget(note)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        tab.layout().addWidget(scroll)
        
        logger.info(f"Balance calculated for {result.period.period_label}: Error={result.error_pct:.2f}%")
    
    def _create_balance_card(self, title: str, subtitle: str, items: list, 
                              total: float, accent_color: str, bg_gradient: tuple,
                              total_label: str = "TOTAL", show_delta: bool = False,
                              card_object_name: str = "calc_balance_card") -> QFrame:
        """Create a styled balance card with items and total (UI HELPER).
        
        Args:
            title: Card title with emoji
            subtitle: Subtitle description
            items: List of (name, value, color) tuples
            total: Total value to display
            accent_color: Primary accent color
            bg_gradient: Tuple of (desc, start_color, end_color)
            total_label: Label for total row
            show_delta: If True, format total with +/- sign
        
        Returns:
            QFrame: Styled card widget
        """
        card = QFrame()
        card.setObjectName(card_object_name)
        card.setProperty("calcCard", True)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("calc_card_title")
        layout.addWidget(title_label)
        
        # Subtitle
        sub_label = QLabel(subtitle)
        sub_label.setObjectName("calc_card_subtitle")
        layout.addWidget(sub_label)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("calc_card_divider")
        layout.addWidget(divider)
        
        # Items
        for name, value, color in items:
            item_row = QHBoxLayout()
            item_row.setSpacing(6)
            item_name = QLabel(name)
            item_name.setObjectName("calc_card_item_name")
            item_value = QLabel(f"{value:,.0f} m³")
            item_value.setObjectName("calc_card_item_value")
            item_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            item_row.addWidget(item_name)
            item_row.addWidget(item_value)
            layout.addLayout(item_row)
        
        # Total divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setObjectName("calc_card_divider")
        layout.addWidget(divider2)
        
        # Total row
        total_row = QHBoxLayout()
        total_name = QLabel(total_label)
        total_name.setObjectName("calc_card_total_name")
        
        if show_delta:
            total_val = QLabel(f"{total:+,.0f} m³")
        else:
            total_val = QLabel(f"{total:,.0f} m³")
        total_val.setObjectName("calc_card_total_value")
        total_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_row.addWidget(total_name)
        total_row.addWidget(total_val)
        layout.addLayout(total_row)
        
        return card
    
    def _create_storage_card(self, title: str, subtitle: str, items: list, 
                              total: float, total_label: str, 
                              facility_breakdown: list, accent_color: str, 
                              bg_gradient: tuple,
                              card_object_name: str = "calc_card_storage") -> QFrame:
        """Create storage card with facility breakdown section (UI HELPER).
        
        Similar to _create_balance_card but includes expandable facility breakdown
        showing per-facility storage changes (where the delta comes from).
        
        Args:
            title: Card title with emoji
            subtitle: Subtitle description
            items: List of (name, value, color) tuples for system totals
            total: Total delta value to display
            total_label: Label for total row (e.g., "📈 Delta (ΔS)")
            facility_breakdown: List of dicts with 'name', 'delta', 'color', 'icon'
            accent_color: Primary accent color
            bg_gradient: Tuple of (desc, start_color, end_color)
        
        Returns:
            QFrame: Styled storage card widget with breakdown
        """
        card = QFrame()
        card.setObjectName(card_object_name)
        card.setProperty("calcCard", True)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("calc_card_title")
        layout.addWidget(title_label)
        
        # Subtitle
        sub_label = QLabel(subtitle)
        sub_label.setObjectName("calc_card_subtitle")
        layout.addWidget(sub_label)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("calc_card_divider")
        layout.addWidget(divider)
        
        # System totals (Opening/Closing)
        for name, value, color in items:
            item_row = QHBoxLayout()
            item_row.setSpacing(6)
            item_name = QLabel(name)
            item_name.setObjectName("calc_card_item_name")
            item_value = QLabel(f"{value:,.0f} m³")
            item_value.setObjectName("calc_card_item_value")
            item_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            item_row.addWidget(item_name)
            item_row.addWidget(item_value)
            layout.addLayout(item_row)
        
        # Total divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setObjectName("calc_card_divider")
        layout.addWidget(divider2)
        
        # Total (Delta) row with large value
        total_row = QHBoxLayout()
        total_name = QLabel(total_label)
        total_name.setObjectName("calc_card_total_name")
        
        delta_color = PALETTE["success"] if total >= 0 else PALETTE["danger"]
        total_val = QLabel(f"{total:+,.0f} m³")
        total_val.setObjectName("calc_card_total_value")
        total_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_row.addWidget(total_name)
        total_row.addWidget(total_val)
        layout.addLayout(total_row)
        
        # --- FACILITY BREAKDOWN SECTION ---
        if facility_breakdown:
            # Small divider before breakdown
            divider3 = QFrame()
            divider3.setFrameShape(QFrame.Shape.HLine)
            divider3.setObjectName("calc_card_divider")
            layout.addWidget(divider3)
            
            # Breakdown header
            breakdown_header = QLabel("📊 By Facility:")
            breakdown_header.setObjectName("calc_card_breakdown_header")
            layout.addWidget(breakdown_header)
            
            # Per-facility rows
            for fac in facility_breakdown:
                fac_row = QHBoxLayout()
                fac_row.setSpacing(4)
                
                # Facility name with icon
                fac_name = QLabel(f"  {fac['icon']} {fac['name']}")
                fac_name.setObjectName("calc_card_item_name")
                
                # Delta value with color
                fac_delta = QLabel(f"{fac['delta']:+,.0f} m³")
                fac_delta.setObjectName("calc_card_item_value")
                fac_delta.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                fac_row.addWidget(fac_name)
                fac_row.addWidget(fac_delta)
                layout.addLayout(fac_row)
        
        return card
    
    def _update_recycled_water(self, result: 'BalanceResult'):
        """Update Recycled Water tab with efficiency metrics (TAB 1 UPDATE).
        
        Displays recycled water KPIs in modern card layout:
        - Gauge-style efficiency display
        - Three metric cards (Recycled %, Intensity, Storage Days)
        - Pie chart showing water source breakdown
        - Color-coded status indicators
        
        Args:
            result: BalanceResult with kpis.recycled_pct, etc.
        """
        tab = self.ui.tabWidget.widget(1)
        if not tab or not tab.layout():
            return
        
        # Clear old content
        while tab.layout().count():
            item = tab.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Extract recycled water metrics from result
        kpis = result.kpis if result.kpis else None
        
        if kpis:
            recycled_pct = kpis.recycled_pct
            water_intensity = kpis.water_intensity_m3_per_tonne
            storage_days = kpis.storage_days
        else:
            recycled_pct = 0.0
            water_intensity = 0.0
            storage_days = 0.0
        
        # Determine status based on recycled %
        if recycled_pct >= 60:
            status_text = "EXCELLENT"
            status_emoji = "🌟"
            theme = STATUS_THEMES["healthy"]
        elif recycled_pct >= 40:
            status_text = "GOOD"
            status_emoji = "✅"
            theme = STATUS_THEMES["warning"]
        else:
            status_text = "NEEDS IMPROVEMENT"
            status_emoji = "⚠️"
            theme = STATUS_THEMES["critical"]

        status_color = theme["color"]
        
        # Create scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # ═══════════════════════════════════════════════════════════════════
        # HERO HEADER - Big efficiency gauge (Compact -20%)
        # ═══════════════════════════════════════════════════════════════════
        header = QFrame()
        header.setObjectName("calc_metric_header")
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(4)
        
        # Title
        title = QLabel("Water Recycling Efficiency")
        title.setObjectName("calc_metric_header_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Big percentage display (reduced from 48px to 38px)
        pct_display = QLabel(f"{recycled_pct:.1f}%")
        pct_display.setObjectName("calc_metric_header_value")
        pct_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(pct_display)
        
        # Status badge (compact)
        badge = QLabel(f"{status_emoji} {status_text}")
        badge.setObjectName("calc_metric_header_badge")
        badge.setProperty("metricState", status_text.lower().replace(" ", "_"))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(160)
        
        badge_container = QWidget()
        badge_layout = QHBoxLayout(badge_container)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(badge)
        header_layout.addWidget(badge_container)
        
        # Period subtitle (compact)
        period = QLabel(f"{result.period.period_label}")
        period.setObjectName("calc_metric_header_period")
        period.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(period)
        
        main_layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════════════
        # THREE METRIC CARDS
        # ═══════════════════════════════════════════════════════════════════
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        
        # Card 1: Water Intensity
        intensity_card = self._create_metric_card(
            emoji="💧",
            title="Water Intensity",
            value=f"{water_intensity:.3f}",
            unit="m³/tonne ore",
            subtitle="Lower is better",
            color=PALETTE["accent"],
            bg_color=PALETTE["surface"]
        )
        cards_row.addWidget(intensity_card)
        
        # Card 2: Total Water Consumption (more relevant than storage days here)
        total_consumption = result.outflows.total_m3 if result.outflows else 0
        consumption_card = self._create_metric_card(
            emoji="📊",
            title="Total Consumption",
            value=f"{total_consumption/1000:,.0f}",
            unit="thousand m³",
            subtitle="This period",
            color=PALETTE["info"],
            bg_color=PALETTE["surface"]
        )
        cards_row.addWidget(consumption_card)
        
        # Card 3: Fresh vs Recycled
        fresh_pct = 100 - recycled_pct
        ratio_card = self._create_metric_card(
            emoji="⚖️",
            title="Fresh Water Used",
            value=f"{fresh_pct:.1f}",
            unit="% of total",
            subtitle="Target: < 40%",
            color=PALETTE["success"] if fresh_pct < 40 else PALETTE["warning"],
            bg_color=PALETTE["surface"]
        )
        cards_row.addWidget(ratio_card)
        
        cards_widget = QWidget()
        cards_widget.setLayout(cards_row)
        main_layout.addWidget(cards_widget)
        
        # ═══════════════════════════════════════════════════════════════════
        # WATER SOURCE PIE CHART
        # ═══════════════════════════════════════════════════════════════════
        chart_frame = QFrame()
        chart_frame.setObjectName("calc_chart_frame")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        
        chart_title = QLabel("Water Source Breakdown")
        chart_title.setObjectName("calc_chart_title")
        chart_layout.addWidget(chart_title)
        
        # Create pie chart (donut style) with edge-case handling for 0%/100%.
        series = QPieSeries()
        series.setHoleSize(0.52)
        series.setPieSize(0.86)

        fresh_pct = max(0.0, 100.0 - recycled_pct)
        if recycled_pct <= 0.01:
            fresh_slice = series.append("Fresh Water", 100.0)
            fresh_slice.setBrush(QColor(PALETTE["accent"]))
        elif fresh_pct <= 0.01:
            recycled_slice = series.append("Recycled Water", 100.0)
            recycled_slice.setBrush(QColor(PALETTE["success"]))
        else:
            recycled_slice = series.append("Recycled Water", recycled_pct)
            fresh_slice = series.append("Fresh Water", fresh_pct)
            recycled_slice.setBrush(QColor(PALETTE["success"]))
            fresh_slice.setBrush(QColor(PALETTE["accent"]))

        # Keep the visual clean: no callout labels on slices, rely on legend.
        for slice in series.slices():
            slice.setLabelVisible(False)
            slice.setBorderColor(QColor("#ffffff"))
            slice.setBorderWidth(1)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundVisible(False)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(250)
        chart_layout.addWidget(chart_view)
        
        main_layout.addWidget(chart_frame)
        
        # ═══════════════════════════════════════════════════════════════════
        # INTERPRETATION FOOTER
        # ═══════════════════════════════════════════════════════════════════
        footer = QLabel(f"""
        💡 <b>Performance Guide:</b><br/>
        <span style="color:{PALETTE['success']};">● > 60%</span> Excellent recycling | 
        <span style="color:{PALETTE['warning']};">● 40-60%</span> Good, room for improvement | 
        <span style="color:{PALETTE['danger']};">● < 40%</span> Process optimization needed
        """)
        footer.setObjectName("calc_section_footer")
        footer.setWordWrap(True)
        main_layout.addWidget(footer)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        tab.layout().addWidget(scroll)
    
    def _create_metric_card(self, emoji: str, title: str, value: str,
                            unit: str, subtitle: str, color: str, bg_color: str) -> QFrame:
        """Create a compact metric card for KPI display (UI HELPER).
        
        Args:
            emoji: Icon emoji for card
            title: Metric name
            value: Main value to display
            unit: Unit label
            subtitle: Helper text
            color: Accent color
            bg_color: Background color
        
        Returns:
            QFrame: Styled metric card widget
        """
        tone = "neutral"
        if color == PALETTE["success"]:
            tone = "success"
        elif color == PALETTE["warning"]:
            tone = "warning"
        elif color == PALETTE["danger"]:
            tone = "danger"
        elif color in (PALETTE["accent"], PALETTE["info"]):
            tone = "info"

        card = QFrame()
        card.setObjectName("calc_metric_card")
        card.setProperty("metricTone", tone)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Emoji
        emoji_label = QLabel(emoji)
        emoji_label.setObjectName("calc_metric_icon")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(emoji_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("calc_metric_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("calc_metric_value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Unit
        unit_label = QLabel(unit)
        unit_label.setObjectName("calc_metric_unit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit_label)
        
        # Subtitle
        sub_label = QLabel(subtitle)
        sub_label.setObjectName("calc_metric_subtitle")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_label)
        
        return card
    
    def _update_data_quality(self, result: 'BalanceResult'):
        """Update Data Quality tab with validation flags (TAB 2 UPDATE).
        
        Displays data quality assessment in modern card layout:
        - Quality score gauge
        - Status cards for each quality dimension
        - Issue list with visual indicators
        - Recommendations
        
        Args:
            result: BalanceResult with quality_flags attributes
        """
        tab = self.ui.tabWidget.widget(2)
        if not tab or not tab.layout():
            return
        
        # Clear old content
        while tab.layout().count():
            item = tab.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Extract quality flags
        quality = result.quality_flags if result.quality_flags else None
        
        if quality:
            has_missing = len(quality.missing_values) > 0
            has_estimated = len(quality.estimated_values) > 0
            has_simulated = len(quality.simulated_values) > 0
            missing_fields = quality.missing_values or []
            estimated_fields = quality.estimated_values or []
            simulated_fields = quality.simulated_values or []
            warnings = quality.warnings or []
        else:
            has_missing = False
            has_estimated = False
            has_simulated = False
            missing_fields = []
            estimated_fields = []
            simulated_fields = []
            warnings = []
        
        # Calculate quality score (0-100) using issue counts with guard rails.
        # This reflects how many variables are impacted instead of a single yes/no flag.
        score = 100
        score -= min(len(missing_fields) * 8, 40)
        score -= min(len(estimated_fields) * 4, 20)
        score -= min(len(simulated_fields) * 3, 15)
        score -= min(len(warnings) * 3, 15)
        score = max(score, 0)
        
        # Determine status
        if score >= 90:
            status_text = "EXCELLENT"
            status_emoji = "🌟"
            theme = STATUS_THEMES["healthy"]
        elif score >= 70:
            status_text = "GOOD"
            status_emoji = "✅"
            theme = STATUS_THEMES["moderate"]
        elif score >= 50:
            status_text = "FAIR"
            status_emoji = "⚠️"
            theme = STATUS_THEMES["warning"]
        else:
            status_text = "POOR"
            status_emoji = "❌"
            theme = STATUS_THEMES["critical"]

        # Create scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Quality score header
        header = QFrame()
        header.setObjectName("calc_quality_header")
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(3)
        
        title = QLabel("Data Quality Assessment")
        title.setObjectName("calc_quality_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        score_display = QLabel(f"{score}")
        score_display.setObjectName("calc_quality_score")
        score_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(score_display)
        
        score_label = QLabel("Quality Score")
        score_label.setObjectName("calc_quality_score_label")
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(score_label)
        
        badge = QLabel(f"{status_emoji} {status_text}")
        badge.setObjectName("calc_quality_badge")
        badge.setProperty("qualityLevel", status_text.lower())
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(130)
        
        badge_container = QWidget()
        badge_layout = QHBoxLayout(badge_container)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(badge)
        header_layout.addWidget(badge_container)
        
        main_layout.addWidget(header)
        
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        
        # Missing Data Card
        missing_card = self._create_status_card(
            title="Missing Data",
            status="YES" if has_missing else "NO",
            count=len(missing_fields),
            is_good=not has_missing,
            icon="📊"
        )
        cards_row.addWidget(missing_card)
        
        # Estimated Values Card
        estimated_card = self._create_status_card(
            title="Estimated Values",
            status="YES" if has_estimated else "NO",
            count=len(estimated_fields),
            is_good=not has_estimated,
            icon="📈"
        )
        cards_row.addWidget(estimated_card)
        
        # Simulated Values Card
        simulated_card = self._create_status_card(
            title="Simulated Values",
            status="YES" if has_simulated else "NO",
            count=len(simulated_fields),
            is_good=not has_simulated,
            icon="🔬"
        )
        cards_row.addWidget(simulated_card)
        
        # Warnings Card
        warnings_card = self._create_status_card(
            title="Warnings",
            status=str(len(warnings)) if warnings else "0",
            count=len(warnings),
            is_good=len(warnings) == 0,
            icon="⚠️"
        )
        cards_row.addWidget(warnings_card)
        
        cards_widget = QWidget()
        cards_widget.setLayout(cards_row)
        main_layout.addWidget(cards_widget)
        
        # Details section
        if missing_fields or estimated_fields or warnings:
            details_row = QHBoxLayout()
            details_row.setSpacing(12)

            issues_frame = QFrame()
            issues_frame.setObjectName("calc_quality_issues")
            issues_layout = QVBoxLayout(issues_frame)
            issues_layout.setContentsMargins(14, 12, 14, 12)
            issues_layout.setSpacing(6)
            
            issues_title = QLabel("Issues Found")
            issues_title.setObjectName("calc_quality_issues_title")
            issues_layout.addWidget(issues_title)
            
            for field in missing_fields[:5]:
                item = QLabel(f"• Missing: {field}")
                item.setObjectName("calc_quality_issue_item")
                issues_layout.addWidget(item)
            
            if len(missing_fields) > 5:
                more = QLabel(f"... and {len(missing_fields) - 5} more missing fields")
                more.setObjectName("calc_quality_issue_more")
                issues_layout.addWidget(more)
            
            for field in estimated_fields[:3]:
                item = QLabel(f"• Estimated: {field}")
                item.setObjectName("calc_quality_issue_item")
                issues_layout.addWidget(item)

            for field in simulated_fields[:3]:
                item = QLabel(f"• Simulated: {field}")
                item.setObjectName("calc_quality_issue_item")
                issues_layout.addWidget(item)
            
            for warning in warnings[:3]:
                item = QLabel(f"• Warning: {warning}")
                item.setObjectName("calc_quality_issue_item")
                item.setWordWrap(True)
                issues_layout.addWidget(item)

            details_row.addWidget(issues_frame, 2)

            scoring_frame = QFrame()
            scoring_frame.setObjectName("calc_quality_scoring")
            scoring_layout = QVBoxLayout(scoring_frame)
            scoring_layout.setContentsMargins(14, 12, 14, 12)
            scoring_layout.setSpacing(6)
            scoring_title = QLabel("Scoring Rules")
            scoring_title.setObjectName("calc_quality_issues_title")
            scoring_layout.addWidget(scoring_title)
            for line in [
                "• Missing values: -8 each (max -40)",
                "• Estimated values: -4 each (max -20)",
                "• Simulated values: -3 each (max -15)",
                "• Warnings: -3 each (max -15)",
            ]:
                lbl = QLabel(line)
                lbl.setObjectName("calc_quality_rule_item")
                scoring_layout.addWidget(lbl)
            scoring_layout.addStretch(1)
            details_row.addWidget(scoring_frame, 1)

            main_layout.addLayout(details_row)
        else:
            good_frame = QFrame()
            good_frame.setObjectName("calc_quality_issues")
            good_layout = QVBoxLayout(good_frame)
            good_layout.setContentsMargins(18, 16, 18, 16)
            good_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            good_label = QLabel("All data quality checks passed.\nNo issues detected in the selected period.")
            good_label.setObjectName("calc_quality_good")
            good_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            good_layout.addWidget(good_label)
            
            main_layout.addWidget(good_frame)
        
        footer = QLabel("Tip: target score >= 90 for reliable monthly balance reporting.")
        footer.setObjectName("calc_quality_footer")
        footer.setWordWrap(True)
        main_layout.addWidget(footer)

        trace_frame = QFrame()
        trace_frame.setObjectName("calc_quality_issues")
        trace_layout = QVBoxLayout(trace_frame)
        trace_layout.setContentsMargins(14, 12, 14, 12)
        trace_layout.setSpacing(6)

        trace_title = QLabel("Calculation Trace (Selected Month)")
        trace_title.setObjectName("calc_quality_issues_title")
        trace_layout.addWidget(trace_title)

        for line in self._build_calc_trace_lines(result):
            trace_item = QLabel(f"• {line}")
            trace_item.setObjectName("calc_quality_issue_item")
            trace_item.setWordWrap(True)
            trace_layout.addWidget(trace_item)

        main_layout.addWidget(trace_frame)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        tab.layout().addWidget(scroll)

    def _build_calc_trace_lines(self, result: 'BalanceResult') -> list[str]:
        """Build business-readable trace lines for key estimated outflows."""
        lines: list[str] = []
        try:
            service = get_balance_service()
            constants = getattr(service, "_constants", None)
            excel = getattr(service, "_excel", None)

            tonnes_milled = 0.0
            if excel:
                series = excel.get_meter_readings_series(
                    EXCEL_COLUMNS["tonnes_milled"],
                    start_date=result.period.start_date,
                    end_date=result.period.end_date
                )
                if series and series[0][1] is not None:
                    tonnes_milled = float(series[0][1])

            dust_rate_l_per_t = float(getattr(constants, "dust_suppression_rate_l_per_t", 1.0))
            dust_m3 = float(result.outflows.components.get("dust_suppression", 0.0))
            lines.append(
                f"Dust Suppression = Tonnes Milled ({tonnes_milled:,.0f} t) x Dust Rate ({dust_rate_l_per_t:g} L/t) / 1000 = {dust_m3:,.0f} m3"
            )

            tailings_m3 = float(result.outflows.components.get("tailings_lockup", 0.0))
            moisture_from_density = (
                result.kpis.tailings_moisture_from_density
                if result.kpis else None
            )
            if moisture_from_density is not None:
                moisture_pct = float(moisture_from_density)
                moisture_source = "Tailings RD from Excel"
            else:
                moisture_pct = float(getattr(constants, "tailings_moisture_pct", 45.0))
                moisture_source = "Configured fallback constant"

            lines.append(
                f"Tailings Lockup = Tailings Tonnes (~{tonnes_milled:,.0f} t) x Moisture ({moisture_pct:.1f}% from {moisture_source}) = {tailings_m3:,.0f} m3"
            )
        except Exception as exc:
            lines.append(f"Trace unavailable: {exc}")

        return lines
    
    def _create_status_card(self, title: str, status: str, count: int, 
                            is_good: bool, icon: str) -> QFrame:
        """Create a status indicator card (UI HELPER).
        
        Args:
            title: Card title
            status: Status text (YES/NO or count)
            count: Issue count
            is_good: True if status is good (no issues)
            icon: Emoji icon
        
        Returns:
            QFrame: Styled status card
        """
        card = QFrame()
        card.setObjectName("calc_quality_status_card")
        card.setProperty("qualityState", "good" if is_good else "bad")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("calc_quality_status_icon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("calc_quality_status_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        status_label = QLabel(status)
        status_label.setObjectName("calc_quality_status_value")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        if count > 0:
            count_label = QLabel(f"({count} items)")
            count_label.setObjectName("calc_quality_status_count")
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(count_label)
        
        return card
    
    def _update_days_of_operation(self, result: 'BalanceResult'):
        """Update Days of Operation tab with water runway analysis (TAB 3 UPDATE).
        
        Uses DaysOfOperationService to calculate:
        - System-wide water runway with visual gauge
        - Bar chart of per-facility runway days
        - Pie chart of storage distribution
        - Facility cards with color-coded status
        
        Args:
            result: BalanceResult with period information
        """
        tab = self.ui.tabWidget.widget(3)
        if not tab or not tab.layout():
            return
        
        # Clear old content
        while tab.layout().count():
            item = tab.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get runway analysis from service (ICMM-aligned calculation)
        # Pass balance_result for accurate outflow-based consumption
        try:
            days_service = get_days_of_operation_service()
            runway = days_service.calculate_runway(
                month=result.period.month,
                year=result.period.year,
                projection_months=12,
                balance_result=result  # NEW: Pass balance result for outflows
            )
        except Exception as e:
            logger.error(f"Days of operation calculation failed: {e}")
            error_label = QLabel(f"❌ Error calculating runway: {e}")
            error_label.setStyleSheet("")
            tab.layout().addWidget(error_label)
            return
        
        # ICMM-Standard Runway Calculation:
        # Days = Usable_Storage / Daily_Net_Fresh_Demand
        # Where:
        #   Usable_Storage = Current - 10% reserve
        #   Net_Fresh_Demand = Outflows - Recycled_Water
        
        # Use the service's calculated values (now industry-standard)
        daily_consumption = runway.daily_net_fresh_demand_m3
        gross_daily_consumption = 0.0
        if runway.total_outflows_m3 > 0:
            gross_daily_consumption = runway.total_outflows_m3 / 30
        display_daily_consumption = daily_consumption
        combined_days = runway.combined_days_remaining
        
        # Log data quality for debugging
        logger.info(f"Runway using {runway.consumption_source}: "
                   f"demand={daily_consumption:,.0f} m³/day, days={combined_days}")
        
        # Use combined days for main display
        days = combined_days
        
        if days >= 180:
            status_text = "HEALTHY"
            status_emoji = "🟢"
            theme = STATUS_THEMES["healthy"]
        elif days >= 90:
            status_text = "MODERATE"
            status_emoji = "🔵"
            theme = STATUS_THEMES["moderate"]
        elif days >= 30:
            status_text = "WARNING"
            status_emoji = "🟡"
            theme = STATUS_THEMES["warning"]
        else:
            status_text = "CRITICAL"
            status_emoji = "🔴"
            theme = STATUS_THEMES["critical"]

        status_color = theme["color"]
        header_gradient = theme["gradient"]
        
        # Create scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("")
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # ═══════════════════════════════════════════════════════════════════
        # HERO HEADER - System Runway (User-friendly display)
        # ═══════════════════════════════════════════════════════════════════
        header = QFrame()
        header.setObjectName("calc_days_header")
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(2)
        
        # Title - simple and clear
        title = QLabel("How Long Will Our Water Last?")
        title.setObjectName("calc_days_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Big days display
        days_display = QLabel(f"{days}")
        days_display.setObjectName("calc_days_value")
        days_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(days_display)
        
        # Plain English explanation
        days_label = QLabel("DAYS OF WATER REMAINING AT CURRENT USAGE")
        days_label.setObjectName("calc_days_subtitle")
        days_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(days_label)
        
        # Status row - just show the status, no confusing secondary number
        status_row = QHBoxLayout()
        status_row.setSpacing(16)
        status_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status badge
        badge = QLabel(f"{status_emoji} {status_text}")
        badge.setObjectName("calc_days_badge")
        badge.setProperty("runwayState", status_text.lower())
        status_row.addWidget(badge)
        
        # Show monthly usage with exact formula context.
        monthly_usage = display_daily_consumption * 30
        usage_info = QLabel(f"📊 Using {monthly_usage/1000:,.0f}k m³/month")
        usage_info.setObjectName("calc_days_usage")
        if daily_consumption > 0:
            usage_info.setToolTip(
                "Net demand = outflows - recycled\n"
                f"Net demand: {daily_consumption:,.0f} m3/day"
            )
        else:
            usage_info.setToolTip(
                "Net demand is 0 (recycled >= outflows)\n"
                f"Gross outflows: {gross_daily_consumption:,.0f} m3/day"
            )
        status_row.addWidget(usage_info)
        
        status_container = QWidget()
        status_container.setLayout(status_row)
        header_layout.addWidget(status_container)
        
        main_layout.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════════════
        # SYSTEM TOTALS CARDS (Plain English)
        # ═══════════════════════════════════════════════════════════════════
        totals_row = QHBoxLayout()
        totals_row.setSpacing(12)
        
        # Available Water (what we can actually use)
        QToolTip.setStyleSheet(
            "QToolTip {"
            "background-color: #0f172a;"
            "color: #f8fafc;"
            "border: 1px solid #334155;"
            "padding: 6px;"
            "border-radius: 6px;"
            "max-width: 220px;"
            "}"
        )

        storage_card = self._create_metric_card(
            emoji="🏊",
            title="Available Water",
            value=f"{runway.usable_storage_m3/1000:,.0f}",
            unit="thousand m³",
            subtitle=f"(We keep 10% as safety buffer)",
            color=PALETTE["info"],
            bg_color=PALETTE["surface"]
        )
        storage_card.setToolTip("Usable storage = total - 10% reserve")
        totals_row.addWidget(storage_card)
        
        # Daily Water Usage
        consumption_card = self._create_metric_card(
            emoji="💧",
            title="Daily Usage",
            value=f"{daily_consumption:,.0f}",
            unit="m³ per day",
            subtitle="How much we use daily",
            color=PALETTE["success"],
            bg_color=PALETTE["surface"]
        )
        if daily_consumption > 0:
            consumption_card.setToolTip("Net demand per day (outflows - recycled)")
        else:
            consumption_card.setToolTip("Net demand is 0; showing gross outflows")
        totals_row.addWidget(consumption_card)
        
        # Water Lost to Environment (can't control)
        env_losses = runway.evaporation_loss_m3 + runway.seepage_loss_m3
        env_card = self._create_metric_card(
            emoji="☀️",
            title="Lost to Evaporation",
            value=f"{env_losses/1000:,.1f}",
            unit="thousand m³/month",
            subtitle="Evaporation + ground seepage",
            color=PALETTE["warning"],
            bg_color=PALETTE["surface"]
        )
        env_card.setToolTip("Evaporation + seepage losses from outflows")
        totals_row.addWidget(env_card)
        
        # Recycled Water (good news!)
        recycled_card = self._create_metric_card(
            emoji="♻️",
            title="Water Recycled",
            value=f"{runway.recycled_water_m3/1000:,.1f}",
            unit="thousand m³/month",
            subtitle="Reused instead of wasted",
            color=PALETTE["success"],
            bg_color=PALETTE["surface"]
        )
        recycled_card.setToolTip("Used in net demand (outflows - recycled)")
        totals_row.addWidget(recycled_card)
        
        totals_widget = QWidget()
        totals_widget.setLayout(totals_row)
        main_layout.addWidget(totals_widget)
        
        # ═══════════════════════════════════════════════════════════════════
        # CHARTS ROW - Bar chart + Pie chart side by side
        # ═══════════════════════════════════════════════════════════════════
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)
        
        # Bar Chart - Runway by Facility
        bar_frame = QFrame()
        bar_frame.setObjectName("calc_chart_frame")
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(16, 16, 16, 16)
        
        bar_title = QLabel("Runway by Facility (Days)")
        bar_title.setObjectName("calc_chart_title")
        bar_layout.addWidget(bar_title)
        
        # Create bar chart
        bar_set = QBarSet("Days Remaining")
        bar_set.setColor(QColor(PALETTE["accent"]))
        categories = []
        
        for f in runway.facilities[:8]:  # Limit to 8 for readability
            bar_set.append(f.days_remaining_conservative)
            categories.append(f.facility_code[:6])  # Truncate long codes
        
        bar_series = QBarSeries()
        bar_series.append(bar_set)
        
        bar_chart = QChart()
        bar_chart.addSeries(bar_series)
        bar_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        bar_chart.legend().setVisible(False)
        bar_chart.setBackgroundVisible(False)
        
        # Category axis
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        bar_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        # Value axis
        axis_y = QValueAxis()
        max_days = max(f.days_remaining_conservative for f in runway.facilities) if runway.facilities else 100
        axis_y.setRange(0, max_days * 1.1)
        axis_y.setLabelFormat("%d")
        bar_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        bar_view = QChartView(bar_chart)
        bar_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        bar_view.setMinimumHeight(200)
        bar_layout.addWidget(bar_view)
        
        charts_row.addWidget(bar_frame, stretch=3)
        
        # Pie Chart - Storage Distribution
        pie_frame = QFrame()
        pie_frame.setObjectName("calc_chart_frame")
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(16, 16, 16, 16)
        
        pie_title = QLabel("Storage Distribution")
        pie_title.setObjectName("calc_chart_title")
        pie_layout.addWidget(pie_title)
        
        # Create pie chart with percentage labels (on slices AND legend)
        pie_series = QPieSeries()
        colors = [
            PALETTE["accent"],
            PALETTE["info"],
            PALETTE["success"],
            PALETTE["warning"],
            "#0ea5e9",
            "#14b8a6",
            "#64748b",
            "#94a3b8",
        ]
        
        # Calculate total for percentage
        total_volume = sum(f.current_volume_m3 for f in runway.facilities[:6])
        
        for i, f in enumerate(runway.facilities[:6]):  # Top 6 facilities
            pct = (f.current_volume_m3 / total_volume * 100) if total_volume > 0 else 0
            # Use short label for slice, full label for legend
            slice = pie_series.append(f"{f.facility_code}: {pct:.1f}%", f.current_volume_m3)
            slice.setBrush(QColor(colors[i % len(colors)]))
            # Keep slice labels off (legend shows percentage), looks cleaner
            slice.setLabelVisible(False)
            if i == 0:  # Explode largest
                slice.setExploded(True)
                slice.setExplodeDistanceFactor(0.05)
        
        pie_chart = QChart()
        pie_chart.addSeries(pie_series)
        pie_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        pie_chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        pie_chart.legend().setVisible(True)
        pie_chart.setBackgroundVisible(False)
        
        pie_view = QChartView(pie_chart)
        pie_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        pie_view.setMinimumHeight(200)
        pie_layout.addWidget(pie_view)
        
        charts_row.addWidget(pie_frame, stretch=2)
        
        charts_widget = QWidget()
        charts_widget.setLayout(charts_row)
        main_layout.addWidget(charts_widget)
        
        # ═══════════════════════════════════════════════════════════════════
        # FACILITY STATUS CARDS (Compact - 50% reduced)
        # ═══════════════════════════════════════════════════════════════════
        facilities_frame = QFrame()
        facilities_frame.setObjectName("calc_facilities_frame")
        facilities_layout = QVBoxLayout(facilities_frame)
        facilities_layout.setContentsMargins(10, 8, 10, 8)
        facilities_layout.setSpacing(4)
        
        facilities_title = QLabel("Facility Status Details")
        facilities_title.setObjectName("calc_facilities_title")
        facilities_layout.addWidget(facilities_title)
        
        # Facility grid - compact spacing (reduced 50%)
        facility_grid = QGridLayout()
        facility_grid.setSpacing(6)
        facility_grid.setContentsMargins(4, 4, 4, 4)
        
        for i, f in enumerate(runway.facilities[:12]):  # Max 12 facilities
            # Determine color based on days
            if f.days_remaining_conservative >= 180:
                f_state = "healthy"
            elif f.days_remaining_conservative >= 90:
                f_state = "moderate"
            elif f.days_remaining_conservative >= 30:
                f_state = "warning"
            else:
                f_state = "critical"
            
            f_card = QFrame()
            f_card.setObjectName("calc_facility_card")
            f_card.setProperty("runwayState", f_state)
            f_card.setMinimumHeight(55)
            f_layout = QVBoxLayout(f_card)
            f_layout.setContentsMargins(6, 4, 6, 4)
            f_layout.setSpacing(2)
            
            # Facility code (compact)
            code_label = QLabel(f.facility_code)
            code_label.setObjectName("calc_facility_code")
            f_layout.addWidget(code_label)

            # Per-facility source badge:
            # - outflows: measured system outflow source used
            # - storage_history: proxy from storage history delta if available
            # - estimated: 5% of capacity fallback
            estimated_monthly = f.capacity_m3 * 0.05
            if runway.consumption_source == "outflows":
                source_text = "Measured"
                source_tip = (
                    "Uses balance outflows source at system level.\n"
                    "Facility card is scaled from facility projection context."
                )
            elif runway.consumption_source == "storage_history":
                if abs(f.monthly_consumption_m3 - estimated_monthly) <= 0.5:
                    source_text = "Estimated"
                    source_tip = "No storage-history proxy found for this facility in selected period.\nUsing fallback 5% of capacity/month."
                else:
                    source_text = "History Proxy"
                    source_tip = "Uses storage_history delta proxy for this facility in selected period."
            else:
                source_text = "Estimated"
                source_tip = "Uses fallback estimate of 5% of facility capacity per month."

            source_label = QLabel(source_text)
            source_label.setObjectName("calc_facility_source")
            source_label.setToolTip(source_tip)
            source_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            source_label.setMaximumWidth(115)
            if source_text == "Measured":
                source_label.setStyleSheet(
                    "background:#ecfdf5; color:#166534; border:1px solid #86efac; "
                    "border-radius:10px; padding:1px 8px; font-size:10px; font-weight:700;"
                )
            elif source_text == "History Proxy":
                source_label.setStyleSheet(
                    "background:#eff6ff; color:#1d4ed8; border:1px solid #93c5fd; "
                    "border-radius:10px; padding:1px 8px; font-size:10px; font-weight:700;"
                )
            else:
                source_label.setStyleSheet(
                    "background:#fffbeb; color:#92400e; border:1px solid #fcd34d; "
                    "border-radius:10px; padding:1px 8px; font-size:10px; font-weight:700;"
                )
            f_layout.addWidget(source_label)

            # Days remaining (reduced from 20px to 13px)
            days_label = QLabel(f"{f.days_remaining_conservative}d")
            days_label.setObjectName("calc_facility_days")
            f_layout.addWidget(days_label)
            
            # Volume - single line compact
            vol_label = QLabel(f"{f.current_volume_m3/1000:,.0f}k ({f.utilization_pct:.0f}%)")
            vol_label.setObjectName("calc_facility_volume")
            f_layout.addWidget(vol_label)
            
            # Utilization bar (thinner)
            util_bar = QFrame()
            util_bar.setFixedHeight(3)
            util_bar.setObjectName("calc_facility_bar")
            util_bar.setProperty("runwayState", f_state)
            f_layout.addWidget(util_bar)
            
            row = i // 4
            col = i % 4
            facility_grid.addWidget(f_card, row, col)
        
        facilities_layout.addLayout(facility_grid)
        main_layout.addWidget(facilities_frame)
        
        # ═══════════════════════════════════════════════════════════════════
        # ENVIRONMENTAL FACTORS FOOTER
        # ═══════════════════════════════════════════════════════════════════
        footer = QLabel("""
        🌍 <b>Environmental Factors (Burgersfort Region):</b> 
        Evaporation 75-180 mm/month | Rainfall 5-110 mm/month | Min reserve: 10% capacity
        """)
        footer.setObjectName("calc_section_footer")
        footer.setWordWrap(True)
        main_layout.addWidget(footer)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        tab.layout().addWidget(scroll)



