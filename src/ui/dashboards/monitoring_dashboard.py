"""
Monitoring Data Dashboard controller (PySide6).

Purpose:
- Load the compiled Designer UI from generated_ui_monitoring.py
- Handle folder selection for monitoring Excel files
- Preview data from Excel files in tables
- Generate charts from monitoring data using QtCharts (optional)
- Keep all logic out of the generated UI for maintainability

Structure:
- 3 main tabs: Borehole Static Levels | Borehole Monitoring | PCD Monitoring
- Each main tab has 2 sub-tabs: Upload & Preview | Visualize
- Upload & Preview: Folder selection + data table
- Visualize: Chart options + chart rendering
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict
import os
from PySide6.QtCore import Qt, QDateTime, QDate, QTimer, QSizeF, QRect
from PySide6.QtGui import QStandardItem, QStandardItemModel, QPainter, QPdfWriter, QPageSize
from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QMessageBox,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QAbstractItemView,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QComboBox,
)

import pandas as pd
# Use ExcelManager for centralized Excel access (matches Analytics dashboard)
from services.excel_manager import get_excel_manager

# Import directory loader for background Excel loading (QThread-based, non-blocking UI)
from services.directory_loader import DirectoryLoaderThread

# Import config manager for directory persistence
from core.config_manager import ConfigManager
config = ConfigManager()

# QtCharts is optional; import conditionally
try:
    from PySide6.QtCharts import (
        QChart,
        QChartView,
        QLineSeries,
        QScatterSeries,
        QBarSeries,
        QBarSet,
        QBarCategoryAxis,
        QDateTimeAxis,
        QValueAxis,
    )
    HAS_QTCHARTS = True
except Exception:
    QChart = QChartView = QLineSeries = QScatterSeries = None
    QBarSeries = QBarSet = QBarCategoryAxis = None
    HAS_QTCHARTS = False

# QtSvg is optional; only needed for SVG export
try:
    from PySide6.QtSvg import QSvgGenerator
    HAS_QTSVG = True
except Exception:
    QSvgGenerator = None
    HAS_QTSVG = False

from .generated_ui_monitoring import Ui_Form
from core.app_logger import logger as app_logger
logger = app_logger  # Alias for convenience in cache methods
# Note: monitoring parsers/models are not used in this dashboard yet.


class MonitoringPage(QWidget):
    """Monitoring Data Dashboard (environmental & operational data visualization).

    Responsibilities:
    - Own the page widget and runtime behavior
    - Provide folder selection UX for Excel monitoring data
    - Preview data from Excel files in tables
    - Generate charts when requested

    UI Structure:
    - mainTabWidget: 3 main tabs (Static Levels, Monitoring, PCD)
      - Each main tab contains sub-tabs (Upload & Preview, Visualize)
      - Upload & Preview: folder path, filters, data table
      - Visualize: chart type selector, generate button, chart viewport

    Data Flow:
    1. User clicks folder button → file dialog
    2. Folder path displayed in text field
    3. Data auto-loads and shows in table
    4. User can filter (Aquifer, Monitoring Point)
    5. Switch to Visualize tab → click Generate
    6. Chart renders in chart viewport
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Initialize ExcelManager singleton for all Excel data access (centralized, cached)
        self._excel_manager = get_excel_manager()
        
        # Initialize QThread workers for background directory loading (non-blocking UI)
        # Each dashboard tab gets its own worker for parallel/independent loading
        self._static_loader_thread: Optional[DirectoryLoaderThread] = None
        self._monitoring_loader_thread: Optional[DirectoryLoaderThread] = None
        self._pcd_loader_thread: Optional[DirectoryLoaderThread] = None
        
        # Store folder paths for specialized parsing (e.g., static boreholes unique structure)
        self._static_folder_path: Optional[Path] = None
        
        # Dashboard-specific logger for monitoring data
        self._logger = app_logger.get_dashboard_logger("monitoring.dashboard")

        # Initialize monitoring date range controls with wide defaults
        # so charts include all data unless user narrows the range.
        # Initialize month/year combos for Monitoring tab (match Static tab pattern)
        # Replace complex date pickers with simple month/year dropdowns for better UX
        if hasattr(self.ui, "date_monitoring_from") and hasattr(self.ui, "date_monitoring_to"):
            # Hide the old date pickers; they'll be replaced with combo boxes
            self.ui.date_monitoring_from.setVisible(False)
            self.ui.date_monitoring_to.setVisible(False)
        
        # Initialize month/year combo boxes for Monitoring tab (SIMPLIFIED DATE PICKER)
        current_year = QDate.currentDate().year()
        years = [str(y) for y in range(2020, 2031)]
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        
        # Remove old date pickers from layout and hide them
        if hasattr(self.ui, 'horizontalLayout_monitoring_options'):
            if hasattr(self.ui, 'date_monitoring_from'):
                self.ui.horizontalLayout_monitoring_options.removeWidget(self.ui.date_monitoring_from)
                self.ui.date_monitoring_from.setVisible(False)
            if hasattr(self.ui, 'date_monitoring_to'):
                self.ui.horizontalLayout_monitoring_options.removeWidget(self.ui.date_monitoring_to)
                self.ui.date_monitoring_to.setVisible(False)
            if hasattr(self.ui, 'label_monitoring_date_from'):
                # Keep the labels, just hide date pickers
                pass
            if hasattr(self.ui, 'label_monitoring_date_to'):
                # Keep the labels, just hide date pickers
                pass
        
        # Create combo boxes dynamically for Monitoring tab
        if not hasattr(self.ui, 'combo_year_from_monitoring'):
            self.ui.combo_year_from_monitoring = QComboBox()
            self.ui.combo_year_from_monitoring.addItems(years)
            self.ui.combo_year_from_monitoring.setCurrentText(str(current_year - 1))
            self.ui.combo_year_from_monitoring.setMinimumWidth(70)
            # Insert after "From:" label
            if hasattr(self.ui, 'horizontalLayout_monitoring_options'):
                # Find index of label_monitoring_date_from and insert after it
                layout = self.ui.horizontalLayout_monitoring_options
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.label_monitoring_date_from:
                        layout.insertWidget(i + 1, self.ui.combo_year_from_monitoring)
                        break
        
        if not hasattr(self.ui, 'combo_month_from_monitoring'):
            self.ui.combo_month_from_monitoring = QComboBox()
            self.ui.combo_month_from_monitoring.addItems(months)
            self.ui.combo_month_from_monitoring.setCurrentIndex(0)
            self.ui.combo_month_from_monitoring.setMinimumWidth(100)
            # Insert after year combo
            if hasattr(self.ui, 'horizontalLayout_monitoring_options'):
                layout = self.ui.horizontalLayout_monitoring_options
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.combo_year_from_monitoring:
                        layout.insertWidget(i + 1, self.ui.combo_month_from_monitoring)
                        break
        
        if not hasattr(self.ui, 'combo_year_to_monitoring'):
            self.ui.combo_year_to_monitoring = QComboBox()
            self.ui.combo_year_to_monitoring.addItems(years)
            self.ui.combo_year_to_monitoring.setCurrentText(str(current_year))
            self.ui.combo_year_to_monitoring.setMinimumWidth(70)
            # Insert after "To:" label
            if hasattr(self.ui, 'horizontalLayout_monitoring_options'):
                layout = self.ui.horizontalLayout_monitoring_options
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.label_monitoring_date_to:
                        layout.insertWidget(i + 1, self.ui.combo_year_to_monitoring)
                        break
        
        if not hasattr(self.ui, 'combo_month_to_monitoring'):
            self.ui.combo_month_to_monitoring = QComboBox()
            self.ui.combo_month_to_monitoring.addItems(months)
            self.ui.combo_month_to_monitoring.setCurrentIndex(11)  # December
            self.ui.combo_month_to_monitoring.setMinimumWidth(100)
            # Insert after year to combo
            if hasattr(self.ui, 'horizontalLayout_monitoring_options'):
                layout = self.ui.horizontalLayout_monitoring_options
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.combo_year_to_monitoring:
                        layout.insertWidget(i + 1, self.ui.combo_month_to_monitoring)
                        break
        
        # Initialize month/year combos for PCD tab (SIMPLIFIED DATE PICKER)
        if hasattr(self.ui, 'horizontalLayout_pcd_options'):
            if hasattr(self.ui, 'date_pcd_from'):
                self.ui.horizontalLayout_pcd_options.removeWidget(self.ui.date_pcd_from)
                self.ui.date_pcd_from.setVisible(False)
            if hasattr(self.ui, 'date_pcd_to'):
                self.ui.horizontalLayout_pcd_options.removeWidget(self.ui.date_pcd_to)
                self.ui.date_pcd_to.setVisible(False)
        
        # Create "From:" label if it doesn't exist (PCD tab may not have it)
        if not hasattr(self.ui, 'label_pcd_date_from'):
            from PySide6.QtWidgets import QLabel
            self.ui.label_pcd_date_from = QLabel()
            self.ui.label_pcd_date_from.setText("From:")
            self.ui.label_pcd_date_from.setObjectName("label_pcd_date_from")
        
        # Create "To:" label if it doesn't exist (PCD tab may not have it)
        if not hasattr(self.ui, 'label_pcd_date_to'):
            from PySide6.QtWidgets import QLabel
            self.ui.label_pcd_date_to = QLabel()
            self.ui.label_pcd_date_to.setText("To:")
            self.ui.label_pcd_date_to.setObjectName("label_pcd_date_to")
        
        if not hasattr(self.ui, 'combo_year_from_pcd'):
            self.ui.combo_year_from_pcd = QComboBox()
            self.ui.combo_year_from_pcd.addItems(years)
            self.ui.combo_year_from_pcd.setCurrentText(str(current_year - 1))
            self.ui.combo_year_from_pcd.setMinimumWidth(70)
            if hasattr(self.ui, 'horizontalLayout_pcd_options'):
                layout = self.ui.horizontalLayout_pcd_options
                # Add "From:" label first if not already in layout
                from_label_exists = False
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.label_pcd_date_from:
                        from_label_exists = True
                        layout.insertWidget(i + 1, self.ui.combo_year_from_pcd)
                        break
                if not from_label_exists:
                    # Add label and combo at the end before Generate/Save buttons
                    layout.insertWidget(layout.count() - 2, self.ui.label_pcd_date_from)
                    layout.insertWidget(layout.count() - 2, self.ui.combo_year_from_pcd)
        
        if not hasattr(self.ui, 'combo_month_from_pcd'):
            self.ui.combo_month_from_pcd = QComboBox()
            self.ui.combo_month_from_pcd.addItems(months)
            self.ui.combo_month_from_pcd.setCurrentIndex(0)
            self.ui.combo_month_from_pcd.setMinimumWidth(100)
            if hasattr(self.ui, 'horizontalLayout_pcd_options'):
                layout = self.ui.horizontalLayout_pcd_options
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.combo_year_from_pcd:
                        layout.insertWidget(i + 1, self.ui.combo_month_from_pcd)
                        break
        
        if not hasattr(self.ui, 'combo_year_to_pcd'):
            self.ui.combo_year_to_pcd = QComboBox()
            self.ui.combo_year_to_pcd.addItems(years)
            self.ui.combo_year_to_pcd.setCurrentText(str(current_year))
            self.ui.combo_year_to_pcd.setMinimumWidth(70)
            if hasattr(self.ui, 'horizontalLayout_pcd_options'):
                layout = self.ui.horizontalLayout_pcd_options
                # Add "To:" label first if not already in layout
                to_label_exists = False
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.label_pcd_date_to:
                        to_label_exists = True
                        layout.insertWidget(i + 1, self.ui.combo_year_to_pcd)
                        break
                if not to_label_exists:
                    # Add label and combo at the end before Generate/Save buttons
                    layout.insertWidget(layout.count() - 2, self.ui.label_pcd_date_to)
                    layout.insertWidget(layout.count() - 2, self.ui.combo_year_to_pcd)
        
        if not hasattr(self.ui, 'combo_month_to_pcd'):
            self.ui.combo_month_to_pcd = QComboBox()
            self.ui.combo_month_to_pcd.addItems(months)
            self.ui.combo_month_to_pcd.setCurrentIndex(11)  # December
            self.ui.combo_month_to_pcd.setMinimumWidth(100)
            if hasattr(self.ui, 'horizontalLayout_pcd_options'):
                layout = self.ui.horizontalLayout_pcd_options
                for i in range(layout.count()):
                    if layout.itemAt(i).widget() == self.ui.combo_year_to_pcd:
                        layout.insertWidget(i + 1, self.ui.combo_month_to_pcd)
                        break
        
        # Initialize static tab month/year combos (like Analytics dashboard)
        self._init_year_month_combos()
        
        # Track selected boreholes for multi-select (like Analytics multi-source)
        self._selected_boreholes: list = []
        
        # Track which aliases we've already logged (avoid spam)
        self._logged_aliases: set = set()

        # Preview row cap for large datasets (keeps table responsive on big imports)
        # Note: Full DataFrame is kept in memory for filters/visualizations.
        self._table_preview_max_rows: int = 5000
        
        # Cache infrastructure (HYBRID: memory + disk persistence)
        # Use user data directory for packaged builds
        user_dir = os.environ.get('WATERBALANCE_USER_DIR')
        if user_dir:
            self._cache_dir = Path(user_dir) / 'data' / '.cache' / 'monitoring'
        else:
            self._cache_dir = Path(config.get('data_sources.base_path', 'data')) / '.cache' / 'monitoring'
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, Dict] = {}  # {file_path: {mtime, dataframe, rows}}
        self._cache_enabled: bool = True  # Toggle for troubleshooting
        
        # Multi-select state tracking for charts
        self._selected_boreholes: list = []  # For static levels (already exists)
        self._selected_monitoring_boreholes: list = []  # For borehole monitoring
        self._selected_pcd_points: list = []  # For PCD monitoring

        # Chart view references (created at runtime)
        self._static_chart_view: Optional[QChartView] = None
        self._monitoring_chart_view: Optional[QChartView] = None
        self._pcd_chart_view: Optional[QChartView] = None

        # Data cache (will be populated when folders are selected)
        self._static_data = None
        self._monitoring_data = None
        self._pcd_data = None

        # Wire up folder selection buttons
        self.ui.pushButton_6.clicked.connect(self._on_static_choose_folder)
        self.ui.pushButton_3.clicked.connect(self._on_monitoring_choose_folder)
        self.ui.pushButton_7.clicked.connect(self._on_pcd_choose_folder)
        
        # Restore previously selected folders from config (auto-load on startup)
        self._restore_folder_paths()

        # Wire up generate buttons
        self.ui.pushButton_4.clicked.connect(self._on_static_generate)
        self.ui.pushButton_2.clicked.connect(self._on_monitoring_generate)
        if hasattr(self.ui, "pushButton_8"):
            self.ui.pushButton_8.clicked.connect(self._on_pcd_generate)

        # Wire up Save Chart buttons (SAVE FUNCTIONALITY)
        self.ui.pushButton_5.clicked.connect(self._on_static_save_chart)
        self.ui.pushButton.clicked.connect(self._on_monitoring_save_chart)
        self.ui.pushButton_9.clicked.connect(self._on_pcd_save_chart)

        # Wire up filter changes (to refresh table display when combo boxes change)
        # These are the PREVIEW tab filters (Upload & Preview), not Visualize tab
        # monitoring_aquifer_filter = Aquifer filter (Borehole Monitoring Preview tab)
        if hasattr(self.ui, 'monitoring_aquifer_filter'):
            self.ui.monitoring_aquifer_filter.currentTextChanged.connect(self._on_monitoring_aquifer_changed)
        
        # pcd_point_filter = Monitoring Point filter (PCD Preview tab)
        if hasattr(self.ui, 'pcd_point_filter'):
            self.ui.pcd_point_filter.currentTextChanged.connect(self._on_pcd_point_changed)

        # Set up QTableView models + headers for all preview tables
        self._setup_static_table_model()
        self._setup_monitoring_table_model()
        self._setup_pcd_table_model()
        
        # Add multi-select buttons for Monitoring and PCD tabs
        self._add_monitoring_multi_select_button()
        self._add_pcd_multi_select_button()
        self._reflow_pcd_options_layout()
        
        # Auto-load previously saved directories on startup (user-friendly persistence)
        self._load_saved_directories()

    # ==================== FILTER HANDLERS ====================
    
    def _on_monitoring_aquifer_changed(self, aquifer_value: str) -> None:
        """Handle aquifer filter change - update table to show only selected aquifer."""
        self._logger.debug(f"[FILTER] Monitoring aquifer changed to: '{aquifer_value}'")
        
        # Early exit if data not loaded yet or table model not initialized
        if self._monitoring_data is None or self._monitoring_data.empty:
            self._logger.debug("[FILTER] No monitoring data - skipping filter")
            return
        
        if not hasattr(self, '_monitoring_table_model') or self._monitoring_table_model is None:
            self._logger.debug("[FILTER] Table model not initialized - skipping filter")
            return
        
        # Filter data by aquifer
        if aquifer_value and aquifer_value.strip() and aquifer_value != "All":
            if 'Aquifer' in self._monitoring_data.columns:
                filtered_df = self._monitoring_data[self._monitoring_data['Aquifer'] == aquifer_value]
                self._logger.info(f"[FILTER] Filtered to aquifer '{aquifer_value}': {len(filtered_df)} rows (from {len(self._monitoring_data)})")
            else:
                filtered_df = self._monitoring_data
                self._logger.warning("[FILTER] 'Aquifer' column not found - showing all data")
        else:
            filtered_df = self._monitoring_data
            self._logger.info(f"[FILTER] Showing all data: {len(filtered_df)} rows")
        
        # Repopulate table with filtered data
        headers = [
            "Borehole", "Aquifer", "Date", "Calcium", "Chloride", "Magnesium",
            "Nitrate (No3)", "Potassium", "Sulphate", "Total Desolved solid",
            "Static Level", "Sodium"
        ]
        num_boreholes = filtered_df['Borehole'].nunique() if 'Borehole' in filtered_df.columns else 0
        detail = f"{num_boreholes} boreholes"
        self._populate_table_model(
            self._monitoring_table_model,
            filtered_df,
            headers,
            status_label=None,
            context="Monitoring",
            detail=detail,
        )
        self._logger.debug(f"[FILTER] Table updated with {len(filtered_df)} rows")
    
    def _on_pcd_point_changed(self, point_value: str) -> None:
        """Handle PCD monitoring point filter change - update table to show only selected point."""
        self._logger.debug(f"[FILTER] PCD point changed to: '{point_value}'")
        
        # Early exit if data not loaded yet or table model not initialized
        if self._pcd_data is None or self._pcd_data.empty:
            self._logger.debug("[FILTER] No PCD data - skipping filter")
            return
        
        if not hasattr(self, '_pcd_table_model') or self._pcd_table_model is None:
            self._logger.debug("[FILTER] PCD table model not initialized - skipping filter")
            return
        
        # Find point column (might be 'Point', 'Monitoring Point', etc.)
        point_col = None
        for col in self._pcd_data.columns:
            if 'point' in col.lower():
                point_col = col
                break
        
        self._logger.debug(f"[FILTER] Found point column: {point_col}")
        
        # Filter data by monitoring point (skip if "All" is selected)
        if point_value and point_value.strip() and point_value != "All" and point_col and point_col in self._pcd_data.columns:
            filtered_df = self._pcd_data[self._pcd_data[point_col] == point_value]
            self._logger.info(f"[FILTER] Filtered to point '{point_value}': {len(filtered_df)} rows (from {len(self._pcd_data)})")
        else:
            filtered_df = self._pcd_data
            self._logger.info(f"[FILTER] Showing all PCD data: {len(filtered_df)} rows")
        
        # Repopulate table with filtered data
        headers = [
            "Monitoring Point", "Date", "Aluminium as AL", "Total Hardness as CaCO3",
            "Iron as Fe", "Total Alkalinity as CaCO3", "pH", "Electrical Conductivity",
            "Total dissolved solids", "Chloride", "Fluoride", "Nitrate (NO3)",
            "Sulphate", "Total inorganic nitrogen", "Calcium", "Magnesium",
            "Sodium", "Potassium", "Manganese", "Chrome hexavalent",
            "Chrome total", "Cadmium", "Vanadium", "Lead", "Copper"
        ]
        num_points = filtered_df[point_col].nunique() if point_col and point_col in filtered_df.columns else 0
        detail = f"{num_points} point(s)"
        self._populate_table_model(
            self._pcd_table_model,
            filtered_df,
            headers,
            status_label=None,
            context="PCD",
            detail=detail,
        )
    
    # ==================== MULTI-SELECT IMPLEMENTATION ====================
    
    def _add_monitoring_multi_select_button(self) -> None:
        """Add Multi-Select button for Borehole Monitoring tab."""
        if not hasattr(self.ui, 'horizontalLayout_monitoring_options'):
            return
        
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton("🔽 Multi-Select Boreholes")
        btn.setToolTip("Select multiple boreholes to compare on chart")
        btn.clicked.connect(self._show_monitoring_multi_select_dialog)
        
        # Insert before Generate button (usually at index -2 before Save button)
        layout = self.ui.horizontalLayout_monitoring_options
        layout.insertWidget(layout.count() - 2, btn)
    
    def _add_pcd_multi_select_button(self) -> None:
        """Add Multi-Select button for PCD Monitoring tab."""
        if not hasattr(self.ui, 'horizontalLayout_pcd_options'):
            return
        
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton("🔽 Multi-Select Points")
        btn.setToolTip("Select multiple monitoring points to compare on chart")
        btn.clicked.connect(self._show_pcd_multi_select_dialog)
        self._pcd_multi_select_button = btn
        
        # Insert before Generate button
        layout = self.ui.horizontalLayout_pcd_options
        layout.insertWidget(layout.count() - 2, btn)

    def _reflow_pcd_options_layout(self) -> None:
        if not hasattr(self.ui, "frame_pcd_options"):
            return

        frame = self.ui.frame_pcd_options
        old_layout = frame.layout()
        if old_layout is None:
            return

        widgets: list = []
        while old_layout.count():
            item = old_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(frame)
                widgets.append(widget)

        old_layout.setContentsMargins(0, 0, 0, 0)
        old_layout.setSpacing(0)

        container = QWidget(frame)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 6, 8, 6)
        container_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        for name in [
            "label_pcd_chart_type",
            "pcd_chart_type",
            "label_4",
            "comboBox_5",
            "label_5",
            "comboBox_6",
        ]:
            if hasattr(self.ui, name):
                top_row.addWidget(getattr(self.ui, name))

        if hasattr(self, "_pcd_multi_select_button"):
            top_row.addWidget(self._pcd_multi_select_button)

        top_row.addStretch(1)

        if hasattr(self.ui, "pushButton_8"):
            top_row.addWidget(self.ui.pushButton_8)
        if hasattr(self.ui, "pushButton_9"):
            top_row.addWidget(self.ui.pushButton_9)

        for name in [
            "label_pcd_date_from",
            "combo_year_from_pcd",
            "combo_month_from_pcd",
            "label_pcd_date_to",
            "combo_year_to_pcd",
            "combo_month_to_pcd",
        ]:
            if hasattr(self.ui, name):
                bottom_row.addWidget(getattr(self.ui, name))

        bottom_row.addStretch(1)

        container_layout.addLayout(top_row)
        container_layout.addLayout(bottom_row)
        old_layout.addWidget(container)

        for widget in widgets:
            widget.setVisible(True)

        frame.setMinimumHeight(84)
        frame.setMaximumHeight(90)
    
    def _show_monitoring_multi_select_dialog(self) -> None:
        """Show dialog to select multiple boreholes for Monitoring chart."""
        if self._monitoring_data is None or self._monitoring_data.empty:
            QMessageBox.information(self, "No Data", "Load monitoring data first")
            return
        
        if 'Borehole' not in self._monitoring_data.columns:
            QMessageBox.warning(self, "Missing Column", "Borehole column not found in data")
            return
        
        # Get unique boreholes
        boreholes = sorted(self._monitoring_data['Borehole'].dropna().unique().tolist())
        if not boreholes:
            QMessageBox.information(self, "No Boreholes", "No boreholes found in data")
            return
        
        # Show dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLabel, QScrollArea, QWidget
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Boreholes for Comparison Chart")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select up to 10 boreholes to compare:"))
        
        # Scrollable checkbox area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        checkboxes = []
        for bh in boreholes:
            cb = QCheckBox(bh)
            if bh in self._selected_monitoring_boreholes:
                cb.setChecked(True)
            checkboxes.append(cb)
            scroll_layout.addWidget(cb)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = [cb.text() for cb in checkboxes if cb.isChecked()]
            if len(selected) > 10:
                QMessageBox.warning(self, "Too Many", "Maximum 10 boreholes for chart clarity")
                selected = selected[:10]
            self._selected_monitoring_boreholes = selected
            
            # Update UI feedback
            if selected:
                info = f"{len(selected)} borehole(s) selected"
                QMessageBox.information(self, "Selection Updated", info)
    
    def _show_pcd_multi_select_dialog(self) -> None:
        """Show dialog to select multiple PCD points for chart."""
        if self._pcd_data is None or self._pcd_data.empty:
            QMessageBox.information(self, "No Data", "Load PCD data first")
            return
        
        # Find point column (might be 'Point', 'Monitoring Point', etc.)
        point_col = None
        for col in self._pcd_data.columns:
            if 'point' in col.lower():
                point_col = col
                break
        
        if not point_col:
            QMessageBox.warning(self, "Missing Column", "Point/Monitoring Point column not found")
            return
        
        # Get unique points
        points = sorted(self._pcd_data[point_col].dropna().unique().tolist())
        if not points:
            QMessageBox.information(self, "No Points", "No monitoring points found")
            return
        
        # Show dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLabel, QScrollArea, QWidget
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Monitoring Points for Comparison Chart")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select up to 10 points to compare:"))
        
        # Scrollable checkbox area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        checkboxes = []
        for pt in points:
            cb = QCheckBox(str(pt))
            if str(pt) in self._selected_pcd_points:
                cb.setChecked(True)
            checkboxes.append(cb)
            scroll_layout.addWidget(cb)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = [cb.text() for cb in checkboxes if cb.isChecked()]
            if len(selected) > 10:
                QMessageBox.warning(self, "Too Many", "Maximum 10 points for chart clarity")
                selected = selected[:10]
            self._selected_pcd_points = selected
            
            # Update UI feedback
            if selected:
                info = f"{len(selected)} point(s) selected"
                QMessageBox.information(self, "Selection Updated", info)
    
    # ==================== CACHE MANAGEMENT ====================
    
    def _load_from_cache(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache if file unchanged (CACHE LOADER).
        
        Checks both memory cache and disk cache.
        Returns cached DataFrame if file mtime matches cached mtime.
        
        Args:
            file_path: Full path to Excel file
        
        Returns:
            Cached DataFrame if valid, None if cache miss or file changed
        """
        if not self._cache_enabled:
            return None
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return None
        
        current_mtime = file_path_obj.stat().st_mtime
        cache_key = file_path_obj.stem  # Use filename without extension
        
        # Check memory cache first (fastest)
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if cached['mtime'] == current_mtime:
                logger.debug(f"Memory cache HIT: {file_path_obj.name}")
                return cached['dataframe']
            else:
                logger.debug(f"Memory cache STALE: {file_path_obj.name} (file modified)")
        
        # Check disk cache (persistent across sessions)
        disk_cache_file = self._cache_dir / f"{cache_key}.pkl"
        if disk_cache_file.exists():
            try:
                import pickle
                with open(disk_cache_file, 'rb') as f:
                    cached = pickle.load(f)
                
                if cached['mtime'] == current_mtime:
                    # Load into memory cache for next access
                    self._memory_cache[cache_key] = cached
                    logger.debug(f"Disk cache HIT: {file_path_obj.name}")
                    return cached['dataframe']
                else:
                    logger.debug(f"Disk cache STALE: {file_path_obj.name} (file modified)")
            except Exception as e:
                logger.warning(f"Failed to load disk cache for {file_path_obj.name}: {e}")
        
        return None  # Cache miss
    
    def _save_to_cache(self, file_path: str, dataframe: pd.DataFrame):
        """Save DataFrame to both memory and disk cache (CACHE SAVER).
        
        Args:
            file_path: Full path to Excel file
            dataframe: Parsed DataFrame to cache
        """
        if not self._cache_enabled or dataframe is None or dataframe.empty:
            return
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return
        
        current_mtime = file_path_obj.stat().st_mtime
        cache_key = file_path_obj.stem
        
        cache_entry = {
            'mtime': current_mtime,
            'dataframe': dataframe,
            'rows': len(dataframe),
            'file_path': str(file_path_obj)
        }
        
        # Save to memory cache
        self._memory_cache[cache_key] = cache_entry
        
        # Save to disk cache (async to avoid blocking)
        try:
            import pickle
            disk_cache_file = self._cache_dir / f"{cache_key}.pkl"
            with open(disk_cache_file, 'wb') as f:
                pickle.dump(cache_entry, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(f"Cached to disk: {file_path_obj.name} ({len(dataframe)} rows)")
        except Exception as e:
            logger.warning(f"Failed to save disk cache for {file_path_obj.name}: {e}")
    
    def clear_cache(self, cache_type: str = 'both'):
        """Clear memory and/or disk cache (CACHE INVALIDATOR).
        
        Args:
            cache_type: 'memory', 'disk', or 'both' (default)
        """
        if cache_type in ('memory', 'both'):
            count = len(self._memory_cache)
            self._memory_cache.clear()
            logger.info(f"Cleared memory cache ({count} entries)")
        
        if cache_type in ('disk', 'both'):
            try:
                import shutil
                if self._cache_dir.exists():
                    shutil.rmtree(self._cache_dir)
                    self._cache_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("Cleared disk cache")
            except Exception as e:
                logger.warning(f"Failed to clear disk cache: {e}")

    # ==================== INITIALIZATION HELPERS ====================

    def _load_saved_directories(self) -> None:
        """Auto-load previously saved directory paths from config (user-friendly persistence).
        
        This remembers the user's folder selections across app restarts,
        so they don't have to re-select folders every time.
        """
        # Load Static Levels directory
        static_dir = config.get('monitoring.static_borehole_directory')
        if static_dir and Path(static_dir).exists():
            self.ui.static_folder_path.setText(static_dir)
            self._load_static_data(static_dir)
        
        # Load Borehole Monitoring directory
        monitoring_dir = config.get('monitoring.borehole_monitoring_directory')
        if monitoring_dir and Path(monitoring_dir).exists():
            self.ui.monitoring_folder_path.setText(monitoring_dir)
            self._load_monitoring_data(monitoring_dir)
        
        # Load PCD Monitoring directory
        pcd_dir = config.get('monitoring.pcd_monitoring_directory')
        self._logger.info(f"[_load_saved_directories] PCD dir from config: {pcd_dir}")
        if pcd_dir:
            self._logger.info(f"[_load_saved_directories] PCD path exists: {Path(pcd_dir).exists()}")
            if Path(pcd_dir).exists():
                self.ui.pcd_folder_path.setText(pcd_dir)
                self._logger.info(f"[_load_saved_directories] Calling _load_pcd_data({pcd_dir})")
                self._load_pcd_data(pcd_dir)
            else:
                self._logger.warning(f"[_load_saved_directories] PCD path does not exist: {pcd_dir}")
        else:
            self._logger.info(f"[_load_saved_directories] No PCD dir configured")

    def _init_year_month_combos(self) -> None:
        """Initialize year and month combo boxes for date range filtering (like Analytics)."""
        current_year = QDate.currentDate().year()
        
        # Populate years (2020-2030 range)
        years = [str(y) for y in range(2020, 2031)]
        if hasattr(self.ui, 'combo_year_from'):
            self.ui.combo_year_from.addItems(years)
            self.ui.combo_year_from.setCurrentText(str(current_year - 1))
        if hasattr(self.ui, 'combo_year_to'):
            self.ui.combo_year_to.addItems(years)
            self.ui.combo_year_to.setCurrentText(str(current_year))
        
        # Populate months
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if hasattr(self.ui, 'combo_month_from'):
            self.ui.combo_month_from.addItems(months)
            self.ui.combo_month_from.setCurrentIndex(0)  # January
        if hasattr(self.ui, 'combo_month_to'):
            self.ui.combo_month_to.addItems(months)
            self.ui.combo_month_to.setCurrentIndex(11)  # December

    def _add_multi_select_button(self) -> None:
        """Add Multi-select and Clear Selection buttons next to borehole dropdown (like Analytics pattern)."""
        # Multi-select button
        button = QPushButton("Multi-select")
        button.setObjectName("btn_multi_select_boreholes")
        button.setMinimumWidth(100)
        button.clicked.connect(self._open_multi_select_dialog)
        
        # Clear selection button (reset to single dropdown mode)
        clear_button = QPushButton("Clear Selection")
        clear_button.setObjectName("btn_clear_selection")
        clear_button.setMinimumWidth(100)
        clear_button.clicked.connect(self._clear_multi_select)
        
        # Insert buttons into the static options horizontal layout
        if hasattr(self.ui, 'horizontalLayout_static_options'):
            layout = self.ui.horizontalLayout_static_options
            # Find combo position and insert after it
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() and hasattr(item.widget(), 'objectName'):
                    if item.widget().objectName() == 'combo_static_borehole':
                        layout.insertWidget(i + 1, button)
                        layout.insertWidget(i + 2, clear_button)
                        break

    def _open_multi_select_dialog(self) -> None:
        """Open dialog to select multiple boreholes (like Analytics multi-source pattern)."""
        if self._static_data is None or self._static_data.empty:
            QMessageBox.information(
                self,
                "No Data",
                "Load static data first before selecting boreholes.",
            )
            return
        
        boreholes = sorted(self._static_data['Borehole'].unique().tolist())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Boreholes")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)
        
        list_widget = QListWidget(dialog)
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        for borehole in boreholes:
            item = QListWidgetItem(borehole)
            list_widget.addItem(item)
            # Pre-select current selections
            if borehole in self._selected_boreholes:
                item.setSelected(True)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select boreholes to display:"))
        layout.addWidget(list_widget)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._selected_boreholes = [item.text() for item in list_widget.selectedItems()]
            self._on_static_generate()  # Regenerate chart with new selection

    def _clear_multi_select(self) -> None:
        """Clear multi-select and reset to single borehole mode (dropdown only)."""
        self._selected_boreholes = []
        # Regenerate chart with just the dropdown selection
        self._on_static_generate()
        for bh in boreholes:
            item = QListWidgetItem(bh)
            if bh in self._selected_boreholes:
                item.setSelected(True)
            list_widget.addItem(item)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(dialog)
        layout.addWidget(list_widget)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        selected = [item.text() for item in list_widget.selectedItems()]
        self._selected_boreholes = selected
        
        # Update combo to show "Custom Selection" when multi-select is active
        if len(selected) > 1:
            self.ui.combo_static_borehole.setEditText(f"Custom ({len(selected)} selected)")
        elif len(selected) == 1:
            self.ui.combo_static_borehole.setCurrentText(selected[0])
        else:
            self._selected_boreholes = []

    def _setup_static_table_model(self) -> None:
        """Initialize Static Levels QTableView model and column headers.

        QTableView columns are defined by the model (not in Designer).
        This sets the headers so Excel data can populate rows later.
        """
        headers = ["Date", "Borehole", "Static Level"]

        self._static_table_model = QStandardItemModel(0, len(headers), self)
        self._static_table_model.setHorizontalHeaderLabels(headers)
        self.ui.tableView_2.setModel(self._static_table_model)
        # Distribute columns evenly with Stretch
        self.ui.tableView_2.horizontalHeader().setStretchLastSection(False)
        self.ui.tableView_2.horizontalHeader().setSectionResizeMode(
            0, self.ui.tableView_2.horizontalHeader().ResizeMode.Stretch
        )
        self.ui.tableView_2.horizontalHeader().setSectionResizeMode(
            1, self.ui.tableView_2.horizontalHeader().ResizeMode.Stretch
        )
        self.ui.tableView_2.horizontalHeader().setSectionResizeMode(
            2, self.ui.tableView_2.horizontalHeader().ResizeMode.Stretch
        )

    def _setup_monitoring_table_model(self) -> None:
        """Initialize Borehole Monitoring QTableView model and column headers.

        QTableView columns are defined by the model (not in Designer).
        This sets the headers so Excel data can populate rows later.
        
        NOTE: Column name "Total Desolved solid" matches Excel (typo preserved for data integrity).
        """
        headers = [
            "Borehole",
            "Aquifer",
            "Date",
            "Calcium",
            "Chloride",
            "Magnesium",
            "Nitrate (No3)",
            "Potassium",
            "Sulphate",
            "Total Desolved solid",  # Match Excel column name exactly (typo in source data)
            "Static Level",
            "Sodium"
        ]

        self._monitoring_table_model = QStandardItemModel(0, len(headers), self)
        self._monitoring_table_model.setHorizontalHeaderLabels(headers)
        self.ui.tableView.setModel(self._monitoring_table_model)
        
        # Stretch across full width (user preference - was fine before)
        self.ui.tableView.horizontalHeader().setStretchLastSection(False)
        for i in range(len(headers)):
            self.ui.tableView.horizontalHeader().setSectionResizeMode(
                i, self.ui.tableView.horizontalHeader().ResizeMode.Stretch
            )

    def _setup_pcd_table_model(self) -> None:
        """Initialize PCD Monitoring QTableView model and column headers.

        QTableView columns are defined by the model (not in Designer).
        This sets the headers so Excel data can populate rows later.
        """
        headers = ["Monitoring Point",
                    "Date",
                      "Aluminium as AL",
                      "Total Hardness as CaCO3",
                      "Iron as Fe",
                      "Total Alkalinity as CaCO3",
                      "pH",
                      "Electrical Conductivity",
                      "Total dissolved solids",
                      "Chloride",
                      "Fluoride",
                      "Nitrate (NO3)",
                      "Sulphate",
                      "Total inorganic nitrogen",
                      "Calcium",
                      "Magnesium",
                      "Sodium",
                      "Potassium",
                      "Manganese",
                      "Chrome hexavalent",
                      "Chrome total",
                      "Cadmium",
                      "Vanadium",
                      "Lead",
                      "Copper",
                        ]

        self._pcd_table_model = QStandardItemModel(0, len(headers), self)
        self._pcd_table_model.setHorizontalHeaderLabels(headers)
        self.ui.tableView_3.setModel(self._pcd_table_model)
        
        # Enable horizontal scrolling (CRITICAL for 25+ columns to prevent squashing)
        from PySide6.QtCore import Qt
        self.ui.tableView_3.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ui.tableView_3.horizontalHeader().setStretchLastSection(False)
        
        # Set intelligent column sizing: prevent squashing with many columns
        for i in range(len(headers)):
            if i == 0:  # Monitoring Point - wider
                self.ui.tableView_3.setColumnWidth(i, 150)
            elif i == 1:  # Date - fixed width
                self.ui.tableView_3.setColumnWidth(i, 120)
            else:  # Chemical parameters - auto-size to content
                self.ui.tableView_3.horizontalHeader().setSectionResizeMode(
                    i, self.ui.tableView_3.horizontalHeader().ResizeMode.ResizeToContents
                )

    # ==================== TABLE POPULATION HELPER ====================

    def _update_preview_status(
        self,
        label: Optional[QLabel],
        total_rows: int,
        shown_rows: int,
        context: str,
        detail: Optional[str] = None,
    ) -> None:
        """Update a status label with preview row counts.

        Args:
            label: QLabel to update (safe to pass None).
            total_rows: Total rows available in the dataset.
            shown_rows: Rows rendered in the table preview.
            context: Short context label (e.g., "PCD", "Monitoring", "Static").
        """
        if label is None:
            return

        if total_rows <= shown_rows:
            message = f"Loaded {total_rows} rows ({context})"
        else:
            message = (
                f"Loaded {total_rows} rows ({context}) - showing first {shown_rows} rows"
            )

        if detail:
            message = f"{message} - {detail}"

        label.setText(message)

    def _populate_table_model(
        self,
        model: QStandardItemModel,
        data: pd.DataFrame,
        headers: list,
        status_label: Optional[QLabel] = None,
        context: str = "Data",
        detail: Optional[str] = None,
    ) -> None:
        """Populate QTableView model with DataFrame rows (GENERIC TABLE POPULATION).
        
        This method takes Excel data and populates the QStandardItemModel so it displays
        in the QTableView. Each row from the DataFrame becomes a row in the table.
        
        Optimization: Batches inserts and allows UI repaints every 10 rows to prevent freezing.
        
        Args:
            model: QStandardItemModel to populate (from QTableView.model()).
            data: DataFrame with data to display (may have extra columns beyond headers).
            headers: List of column names to display (in order).
            status_label: Optional QLabel to show preview status.
            context: Context label for status text (tab name).
            detail: Optional detail suffix (e.g., "5 boreholes").
        
        Returns:
            None (modifies model in-place)
        """
        from PySide6.QtWidgets import QApplication
        
        # Debug logging for troubleshooting empty tables
        self._logger.info(f"_populate_table_model START: {len(data)} rows x {len(headers)} columns")
        self._logger.info(f"  DataFrame columns: {list(data.columns)}")
        
        # Limit preview rows for large datasets to keep UI responsive
        max_rows = self._table_preview_max_rows
        preview_df = data.head(max_rows) if len(data) > max_rows else data

        model.setRowCount(len(preview_df))
        
        # Column name mapping: handle cases where parser uses different column names
        column_aliases = {
            'Monitoring Point': 'Point',  # PCD table: header says 'Monitoring Point' but DataFrame has 'Point'
        }
        
        # Pre-compute column index mapping to avoid repeated lookups
        col_indices = {}
        for col_name in headers:
            if col_name in data.columns:
                col_indices[col_name] = col_name
            elif col_name in column_aliases and column_aliases[col_name] in data.columns:
                col_indices[col_name] = column_aliases[col_name]
                if col_name not in self._logged_aliases:
                    self._logger.info(f"  Using alias: '{col_name}' -> '{column_aliases[col_name]}'")
                    self._logged_aliases.add(col_name)
            else:
                col_indices[col_name] = None
        self._logger.info(f"  Column index mapping: {col_indices}")
        
        # Populate rows
        for row_idx, (_, row_data) in enumerate(preview_df.iterrows()):
            # Allow UI to repaint every 10 rows (prevents freezing on large datasets)
            if row_idx > 0 and row_idx % 10 == 0:
                QApplication.processEvents()
            
            for col_idx, col_name in enumerate(headers):
                actual_col = col_indices.get(col_name)
                
                # Get value from DataFrame
                if actual_col and actual_col in data.columns:
                    value = row_data[actual_col]
                else:
                    value = None
                
                # Format cell value
                if pd.isna(value) or value is None:
                    display_text = ""
                elif isinstance(value, float):
                    display_text = f"{value:.2f}" if not pd.isna(value) else ""
                else:
                    display_text = str(value)
                
                # Create and insert item into model
                item = QStandardItem(display_text)
                model.setItem(row_idx, col_idx, item)
        
        self._update_preview_status(
            label=status_label,
            total_rows=len(data),
            shown_rows=len(preview_df),
            context=context,
            detail=detail,
        )
        self._logger.info(
            f"_populate_table_model END: populated {len(preview_df)} rows"
        )

    # ==================== BOREHOLE STATIC LEVELS ====================
    
    def _restore_folder_paths(self) -> None:
        """Restore previously selected folder paths from config and auto-load data."""
        # Restore static boreholes folder
        static_folder = config.get('monitoring.static_borehole_directory')
        if static_folder and Path(static_folder).exists():
            self.ui.static_folder_path.setText(static_folder)
            self._static_folder_path = Path(static_folder)
            # Defer auto-load until after __init__ completes (table models must be initialized first)
            QTimer.singleShot(100, lambda: self._load_static_data_async(static_folder))

    def _on_static_choose_folder(self) -> None:
        """Open file dialog for static borehole Excel files."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Static Borehole Excel Files",
            ""
        )
        if not folder:
            return

        self.ui.static_folder_path.setText(folder)
        # Save directory to config for persistence (remembers across app restarts)
        config.set('monitoring.static_borehole_directory', folder)
        # Save folder path for later use in parsing
        self._static_folder_path = Path(folder)
        # Load data in background thread (non-blocking UI)
        self._load_static_data_async(folder)

    def _load_static_data_async(self, folder_path: str) -> None:
        """Load static borehole data in background thread (non-blocking UI).
        
        Args:
            folder_path: Path to folder containing Excel files
        """
        # Clear existing data
        self._static_table_model.setRowCount(0)
        self._static_data = None
        # Status label removed
        
        # Wait for previous thread to finish (if running)
        if self._static_loader_thread is not None and self._static_loader_thread.isRunning():
            self._static_loader_thread.cancel()
            self._static_loader_thread.wait(2000)  # Wait up to 2 seconds
        
        # Create NEW thread each time (QThreads can't be restarted)
        self._static_loader_thread = DirectoryLoaderThread("static_boreholes")
        self._static_loader_thread.set_cache_functions(self._load_from_cache, self._save_to_cache)
        self._static_loader_thread.progress.connect(self._on_static_progress)
        self._static_loader_thread.error.connect(self._on_static_error)
        self._static_loader_thread.complete.connect(self._on_static_complete)
        self._static_loader_thread.cache_stats.connect(self._on_cache_stats)
        
        # Load directory in background
        self._static_loader_thread.load_directory(folder_path)
        self._static_loader_thread.start()
        self._logger.info(f"Started background load for static borehole data from {folder_path}")
    
    def _on_static_progress(self, current: int, total: int, file_name: str) -> None:
        """Handle static borehole progress update (called from worker thread)."""
        # Status label removed
    
    def _on_static_error(self, file_name: str, error_reason: str) -> None:
        """Handle static borehole load error (called from worker thread)."""
        self._logger.warning(f"Failed to load {file_name}: {error_reason}")
    
    def _on_static_complete(self, data: pd.DataFrame, error_summary: dict) -> None:
        """Handle static borehole load completion (called from worker thread)."""
        if data.empty:
            msg = error_summary.get("error") or error_summary.get("warning") or "No data loaded"
            QMessageBox.warning(self, "Load Failed", msg)
        # Status label removed
            return
        
        try:
            # Parse each file using the specialized static levels parser
            # (Excel files have unique structure: borehole name with date/level columns below)
            all_parsed = []
            
            # Get list of files from the source_file column
            if 'source_file' not in data.columns:
        # Status label removed
                return
            
            file_names = data['source_file'].unique()
            
            # Safety check: ensure we have the folder path saved
            if not self._static_folder_path:
                self._logger.error("Static folder path not set - this should not happen")
        # Status label removed
                return
            
            for file_name in file_names:
                if not file_name:
                    continue
                    
                file_path = self._static_folder_path / file_name
                try:
                    parsed = self._parse_static_levels_excel(str(file_path))
                    if not parsed.empty:
                        all_parsed.append(parsed)
                except Exception as e:
                    self._logger.warning(f"Failed to parse {file_name}: {e}")
                    continue
            
            if not all_parsed:
        # Status label removed
                self._static_data = pd.DataFrame()  # Set to empty DataFrame instead of leaving as None
                return
            
            # Combine all parsed data
            combined_df = pd.concat(all_parsed, ignore_index=True)
            combined_df = combined_df.sort_values(['borehole', 'date']).reset_index(drop=True)
            
            # Build standardized view for display
            self._static_data = pd.DataFrame({
                "Date": combined_df['date'],
                "Borehole": combined_df['borehole'],
                "Static Level": combined_df['level']
            })
            
            # Verify we have data before proceeding
            if self._static_data.empty:
        # Status label removed
                return

            # Populate table model with standard columns (cap rows for performance)
            headers = ["Date", "Borehole", "Static Level"]
            num_boreholes = combined_df['borehole'].nunique()
            detail = f"{num_boreholes} boreholes"
            self._populate_table_model(
                self._static_table_model,
                self._static_data,
                headers,
                status_label=None,
                context="Static",
                detail=detail,
            )
            
            # Populate borehole dropdown (safety check: ensure data exists)
            if self._static_data is None or self._static_data.empty or 'Borehole' not in self._static_data.columns:
                self._logger.warning("Cannot populate borehole dropdown: data is None, empty, or missing 'Borehole' column")
                return
            
            boreholes = sorted(self._static_data['Borehole'].unique().tolist())
            if hasattr(self.ui, "combo_static_borehole"):
                self.ui.combo_static_borehole.clear()
                self.ui.combo_static_borehole.addItems(boreholes)
            
            status_msg = (
                f"Loaded {len(combined_df)} records from "
                f"{error_summary.get('loaded_files', 0)} file(s)"
            )
            if error_summary.get('failed_files', 0) > 0:
                status_msg += f" - {error_summary['failed_files']} file(s) failed"
            self._logger.info(
                f"Static borehole load complete: {status_msg}, {num_boreholes} boreholes"
            )
        
        except Exception as e:
            error_msg = f"Error processing static borehole data: {str(e)}"
            self._logger.exception(error_msg)
            QMessageBox.critical(self, "Parse Error", error_msg)
        # Status label removed
    
    def _find_column(self, df: pd.DataFrame, candidates: list) -> str:
        """Find first matching column name from candidates (case-insensitive).
        
        Args:
            df: DataFrame to search
            candidates: List of column name candidates to try
        
        Returns:
            Matching column name, or None if not found
        """
        df_cols = df.columns.str.lower().tolist()
        for candidate in candidates:
            if candidate.lower() in df_cols:
                # Return actual column name from df (preserves case)
                idx = df_cols.index(candidate.lower())
                return df.columns[idx]
        return None
    
    def _parse_static_levels_row(self, row: pd.Series) -> pd.DataFrame:
        """Parse a single row from combined DataFrame to extract date, borehole, level (COLUMN DETECTION).
        
        The Excel files may have different column names, so this method tries to detect the right columns.
        Expected columns (in any order):
        - Date column: 'Date', 'date', 'DATE'
        - Borehole column: 'Borehole', 'borehole', 'BH', 'ID', 'Hole'
        - Level column: 'Static Level', 'Static_Level', 'Level', 'Level (m)'
        
        Returns:
            DataFrame with columns ['date', 'borehole', 'level'] or empty if parsing fails
        """
        try:
            # Create a copy to avoid SettingWithCopyWarning
            row_dict = row.to_dict()
            
            # Debug: Log available columns on first call
            if not hasattr(self, '_logged_columns'):
                self._logger.info(f"Available columns in Excel data: {list(row_dict.keys())}")
                self._logged_columns = True
            
            # Find date column (try various names)
            date_val = None
            date_candidates = ['Date', 'date', 'DATE', 'measurement_date', 'Measurement Date']
            for col in date_candidates:
                if col in row_dict:
                    date_val = row_dict[col]
                    if pd.notna(date_val):
                        break
            
            # Find borehole column (try various names)
            borehole_val = None
            borehole_candidates = ['Borehole', 'borehole', 'BH', 'ID', 'Hole', 'Hole_ID', 'Well']
            for col in borehole_candidates:
                if col in row_dict:
                    borehole_val = row_dict[col]
                    if pd.notna(borehole_val):
                        break
            
            # Find level column (try various names)
            level_val = None
            level_candidates = ['Static Level', 'Static_Level', 'Level', 'Level (m)', 'Static', 'Depth']
            for col in level_candidates:
                if col in row_dict:
                    level_val = row_dict[col]
                    if pd.notna(level_val):
                        break
            
            # If any value is missing, return empty DataFrame
            if date_val is None or borehole_val is None or level_val is None:
                return pd.DataFrame()
            
            # Create standardized output
            return pd.DataFrame({
                'date': [pd.to_datetime(date_val)],
                'borehole': [str(borehole_val)],
                'level': [float(level_val)]
            })
        
        except Exception as e:
            # Log the error for debugging
            self._logger.debug(f"Failed to parse row: {str(e)}")
            # Silently skip rows that can't be parsed
            return pd.DataFrame()
    
    def _load_static_data(self, folder_path: str) -> None:
        """Legacy method - kept for backward compatibility. Use _load_static_data_async instead."""
        self._load_static_data_async(folder_path)

    # ==================== BOREHOLE MONITORING ====================

    def _on_monitoring_choose_folder(self) -> None:
        """Open file dialog for monitoring borehole Excel files."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Monitoring Borehole Excel Files",
            ""
        )
        if not folder:
            return

        self.ui.monitoring_folder_path.setText(folder)
        # Save directory to config for persistence (remembers across app restarts)
        config.set('monitoring.borehole_monitoring_directory', folder)
        # Load data in background thread (non-blocking UI)
        self._load_monitoring_data_async(folder)

    def _load_monitoring_data_async(self, folder_path: str) -> None:
        """Load monitoring borehole data in background thread (non-blocking UI).
        
        Args:
            folder_path: Path to folder containing Excel files
        """
        # Clear existing data
        self._monitoring_table_model.setRowCount(0)
        self._monitoring_data = None
        self.ui.monitoring_status_label.setText("Loading monitoring borehole data...")
        
        # Wait for previous thread to finish (if running)
        if self._monitoring_loader_thread is not None and self._monitoring_loader_thread.isRunning():
            self._monitoring_loader_thread.cancel()
            self._monitoring_loader_thread.wait(2000)  # Wait up to 2 seconds
        
        # Create NEW thread each time (QThreads can't be restarted)
        self._monitoring_loader_thread = DirectoryLoaderThread("borehole_monitoring")
        self._monitoring_loader_thread.set_cache_functions(self._load_from_cache, self._save_to_cache)
        self._monitoring_loader_thread.progress.connect(self._on_monitoring_progress)
        self._monitoring_loader_thread.error.connect(self._on_monitoring_error)
        self._monitoring_loader_thread.complete.connect(self._on_monitoring_complete)
        self._monitoring_loader_thread.cache_stats.connect(self._on_cache_stats)
        
        # Load directory in background
        self._monitoring_loader_thread.load_directory(folder_path)
        self._monitoring_loader_thread.start()
        self._logger.info(f"Started background load for monitoring borehole data from {folder_path}")
    
    def _on_cache_stats(self, stats: dict):
        """Handle cache statistics from loader thread (CACHE PERFORMANCE TRACKER).
        
        Args:
            stats: Dictionary with files_cached, files_parsed, total_files
        """
        cached = stats.get('files_cached', 0)
        parsed = stats.get('files_parsed', 0)
        total = stats.get('total_files', 0)
        
        if total > 0:
            cache_rate = (cached / total) * 100 if total > 0 else 0
            logger.info(
                f"Cache performance: {cached}/{total} files from cache "
                f"({cache_rate:.1f}% hit rate), {parsed} files parsed"
            )
    
    def _on_monitoring_progress(self, current: int, total: int, file_name: str) -> None:
        """Handle monitoring borehole progress update (called from worker thread)."""
        self.ui.monitoring_status_label.setText(f"Loading {file_name}... ({current}/{total})")
    
    def _on_monitoring_error(self, file_name: str, error_reason: str) -> None:
        """Handle monitoring borehole load error (called from worker thread)."""
        self._logger.warning(f"Failed to load {file_name}: {error_reason}")
    
    def _on_monitoring_complete(self, data: pd.DataFrame, error_summary: dict) -> None:
        """Handle monitoring borehole load completion (called from worker thread).
        
        Processes raw Excel data, normalizes columns, and displays in table.
        """
        self._logger.info(f"_on_monitoring_complete: Received {len(data)} rows. Errors: {error_summary}")
        
        if data.empty:
            msg = error_summary.get("error") or error_summary.get("warning") or "No data loaded"
            self.ui.monitoring_status_label.setText(msg)
            self._monitoring_table_model.setRowCount(0)
            self._logger.warning(f"Monitoring data is empty. Message: {msg}")
            return
        
        try:
            self._logger.info(f"Monitoring data columns: {list(data.columns)}")
            self._logger.info(f"Monitoring data shape: {data.shape}")
            
            # Normalize key columns
            date_col = self._find_column(data, ["date", "measurement date", "sample date"])
            borehole_col = self._find_column(data, ["borehole", "borehole id", "bh", "site id"])
            aquifer_col = self._find_column(data, ["aquifer", "aquifer type"])

            self._logger.debug(f"Column matches: date={date_col}, borehole={borehole_col}, aquifer={aquifer_col}")

            if date_col:
                data[date_col] = pd.to_datetime(data[date_col], errors="coerce")

            # Build standardized view for charting and preview
            self._monitoring_data = data.copy()
            if date_col and date_col != "Date":
                self._monitoring_data["Date"] = self._monitoring_data[date_col]
            if borehole_col and borehole_col != "Borehole":
                self._monitoring_data["Borehole"] = self._monitoring_data[borehole_col]
            if aquifer_col and aquifer_col != "Aquifer":
                self._monitoring_data["Aquifer"] = self._monitoring_data[aquifer_col]

            self._logger.debug(f"Standardized data ready: {self._monitoring_data.shape}")

            # Update preview table (cap rows for performance on large datasets)
            headers = [self._monitoring_table_model.horizontalHeaderItem(i).text()
                       for i in range(self._monitoring_table_model.columnCount())]
            self._logger.info(
                f"Calling populate_table_model with {len(self._monitoring_data)} rows and headers: {headers}"
            )

            record_count = len(data)
            unique_boreholes = data[borehole_col].nunique() if borehole_col else 0
            detail = f"{unique_boreholes} boreholes"

            self._populate_table_model(
                self._monitoring_table_model,
                self._monitoring_data,
                headers,
                status_label=self.ui.monitoring_status_label,
                context="Monitoring",
                detail=detail,
            )

            # Populate visualize controls
            numeric_cols = self._monitoring_data.select_dtypes(include="number").columns.tolist()
            numeric_cols = [c for c in numeric_cols if c not in {"Date"}]

            self.ui.comboBox_2.clear()
            self.ui.comboBox_2.addItems(numeric_cols)

            if "Aquifer" in self._monitoring_data.columns:
                aquifers = sorted(self._monitoring_data["Aquifer"].dropna().unique().tolist())
                # Populate Visualize tab aquifer dropdown (comboBox_4)
                self.ui.comboBox_4.clear()
                self.ui.comboBox_4.addItems(["All"] + aquifers)
                # Populate Preview tab aquifer filter (monitoring_aquifer_filter)
                if hasattr(self.ui, 'monitoring_aquifer_filter'):
                    self.ui.monitoring_aquifer_filter.clear()
                    self.ui.monitoring_aquifer_filter.addItems(["All"] + aquifers)
            else:
                self.ui.comboBox_4.clear()
                self.ui.comboBox_4.addItems(["All"])
                if hasattr(self.ui, 'monitoring_aquifer_filter'):
                    self.ui.monitoring_aquifer_filter.clear()
                    self.ui.monitoring_aquifer_filter.addItems(["All"])

            if "Borehole" in self._monitoring_data.columns:
                boreholes = sorted(self._monitoring_data["Borehole"].dropna().unique().tolist())
                self.ui.comboBox_3.clear()
                self.ui.comboBox_3.addItems(boreholes)

            # Status label is updated by _populate_table_model to include preview limits.
            
            # Show error summary if any files failed
            if error_summary.get('errors'):
                self._show_error_summary("Borehole Monitoring", error_summary)
            
            self._logger.info(f"Monitoring borehole load complete: {len(self._monitoring_data)} records, {error_summary.get('failed_files', 0)} errors")
        
        except Exception as e:
            error_msg = f"Error processing monitoring borehole data: {str(e)}"
            self._logger.exception(error_msg)
            self.ui.monitoring_status_label.setText(error_msg)
    
    def _load_monitoring_data(self, folder_path: str) -> None:
        """Legacy method - kept for backward compatibility. Use _load_monitoring_data_async instead."""
        self._load_monitoring_data_async(folder_path)

    def _on_monitoring_filter_changed(self) -> None:
        """Handle aquifer filter change - refresh table."""
        # TODO: Implement filter logic to refresh table
        pass

    # ==================== PCD MONITORING ====================

    def _on_pcd_choose_folder(self) -> None:
        """Open file dialog for PCD monitoring Excel files."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with PCD Monitoring Excel Files",
            ""
        )
        if not folder:
            return

        self.ui.pcd_folder_path.setText(folder)
        # Save directory to config for persistence (remembers across app restarts)
        config.set('monitoring.pcd_monitoring_directory', folder)
        # Load data in background thread (non-blocking UI)
        self._load_pcd_data_async(folder)
    
    def _load_pcd_data(self, folder_path: str) -> None:
        """Wrapper for _load_pcd_data_async - maintained for backward compatibility with auto-load code.
        
        Args:
            folder_path: Path to directory containing PCD Excel files
        """
        self._load_pcd_data_async(folder_path)

    def _load_pcd_data_async(self, folder_path: str) -> None:
        """Load PCD monitoring data in background thread (non-blocking UI).
        
        Args:
            folder_path: Path to folder containing Excel files
        """
        # Clear existing data
        self._pcd_table_model.setRowCount(0)
        self._pcd_data = None
        # Status label removed
        
        # Wait for previous thread to finish (if running)
        if self._pcd_loader_thread is not None and self._pcd_loader_thread.isRunning():
            self._pcd_loader_thread.cancel()
            self._pcd_loader_thread.wait(2000)  # Wait up to 2 seconds
        
        # Create NEW thread each time (QThreads can't be restarted)
        self._pcd_loader_thread = DirectoryLoaderThread("pcd_monitoring")
        self._pcd_loader_thread.set_cache_functions(self._load_from_cache, self._save_to_cache)
        self._pcd_loader_thread.progress.connect(self._on_pcd_progress)
        self._pcd_loader_thread.error.connect(self._on_pcd_error)
        self._pcd_loader_thread.complete.connect(self._on_pcd_complete)
        self._pcd_loader_thread.cache_stats.connect(self._on_cache_stats)
        
        # Load directory in background
        self._pcd_loader_thread.load_directory(folder_path)
        self._pcd_loader_thread.start()
        self._logger.info(f"Started background load for PCD monitoring data from {folder_path}")
    
    def _on_pcd_progress(self, current: int, total: int, file_name: str) -> None:
        """Handle PCD monitoring progress update (called from worker thread)."""
        # Status label removed
    
    def _on_pcd_error(self, file_name: str, error_reason: str) -> None:
        """Handle PCD monitoring load error (called from worker thread)."""
        self._logger.warning(f"Failed to load {file_name}: {error_reason}")
    
    def _on_pcd_complete(self, data: pd.DataFrame, error_summary: dict) -> None:
        """Handle PCD monitoring load completion (called from worker thread)."""
        self._logger.info(f"_on_pcd_complete CALLED with {len(data) if data is not None else 'None'} rows")
        
        if data.empty:
            msg = error_summary.get("error") or error_summary.get("warning") or "No data loaded"
        # Status label removed
            self._pcd_table_model.setRowCount(0)
            return
        
        try:
            self._logger.info(f"PCD data loaded: columns = {list(data.columns)}")
            
            # Normalize key columns
            date_col = self._find_column(data, ["date", "sample date", "measurement date"])
            point_col = self._find_column(data, ["monitoring point", "point", "location", "site", "borehole"])
            self._logger.info(f"PCD: date_col={date_col}, point_col={point_col}")

            if date_col:
                data[date_col] = pd.to_datetime(data[date_col], errors="coerce")

            self._pcd_data = data.copy()
            if date_col and date_col != "Date":
                self._pcd_data["Date"] = self._pcd_data[date_col]
            
            # Ensure we always have a "Point" column for filtering/charting
            if point_col:
                if point_col != "Point":
                    self._logger.info(f"  Creating 'Point' column from '{point_col}' (type: {type(self._pcd_data[point_col])})")
                    self._pcd_data["Point"] = self._pcd_data[point_col]
                    self._logger.info(f"  First 3 Point values: {self._pcd_data['Point'].head(3).tolist()}")
                else:
                    self._logger.info(f"  'Point' column already exists")
            else:
                self._logger.warning(f"  No point column found - filter may not work")
            
            self._logger.info(f"  PCD DataFrame after normalization: columns = {list(self._pcd_data.columns)}")
            self._logger.info(f"  DataFrame shape: {self._pcd_data.shape}")
            self._logger.info(f"  First row: {dict(self._pcd_data.iloc[0]) if len(self._pcd_data) > 0 else 'empty'}")

            headers = [self._pcd_table_model.horizontalHeaderItem(i).text()
                       for i in range(self._pcd_table_model.columnCount())]
            self._logger.info(f"  Table headers: {headers}")
            self._logger.info(f"  Starting populate_table_model...")
            self._populate_table_model(
                self._pcd_table_model,
                self._pcd_data,
                headers,
                status_label=None,
                context="PCD",
            )
            self._logger.info(f"  populate_table_model completed!")

            # Populate visualize controls
            numeric_cols = self._pcd_data.select_dtypes(include="number").columns.tolist()
            numeric_cols = [c for c in numeric_cols if c not in {"Date"}]

            self.ui.comboBox_5.clear()
            self.ui.comboBox_5.addItems(numeric_cols)

            if "Point" in self._pcd_data.columns:
                points = sorted(self._pcd_data["Point"].dropna().unique().tolist())
                self._logger.info(f"  Populating comboBox_6 with {len(points)} points: {points[:5]}...")
                # Populate Visualize tab point dropdown (comboBox_6)
                self.ui.comboBox_6.clear()
                self.ui.comboBox_6.addItems(["All"] + points)
                self._logger.info(f"  comboBox_6 now has {self.ui.comboBox_6.count()} items")
                # Populate Preview tab point filter (pcd_point_filter)
                if hasattr(self.ui, 'pcd_point_filter'):
                    self.ui.pcd_point_filter.clear()
                    self.ui.pcd_point_filter.addItems(["All"] + points)
            else:
                self._logger.warning(f"  'Point' column not found in PCD data - cannot populate filter dropdown")

            # Status label is updated by _populate_table_model to include preview limits.
            status_msg = (
                f"Loaded {len(self._pcd_data)} records from "
                f"{error_summary.get('loaded_files', 0)} file(s)"
            )
            if error_summary.get('failed_files', 0) > 0:
                status_msg += f" - {error_summary['failed_files']} file(s) failed"
            self._logger.info(f"PCD Monitoring: {status_msg}")
            
            # Show error summary if any files failed
            if error_summary.get('errors'):
                self._show_error_summary("PCD Monitoring", error_summary)
            
            self._logger.info(f"PCD monitoring load complete: {len(self._pcd_data)} records, {error_summary.get('failed_files', 0)} errors")
        
        except Exception as e:
            error_msg = f"Error processing PCD monitoring data: {str(e)}"
            self._logger.exception(error_msg)
        # Status label removed
    
    def _load_pcd_data(self, folder_path: str) -> None:
        """Legacy method - kept for backward compatibility. Use _load_pcd_data_async instead."""
        self._load_pcd_data_async(folder_path)
    
    def _show_error_summary(self, tab_name: str, error_summary: dict) -> None:
        """Show a dialog summarizing which files failed to load (ERROR REPORTING).
        
        Args:
            tab_name: Name of the tab (e.g., "Static Boreholes", "Borehole Monitoring")
            error_summary: Dict with 'errors' key containing {filename: error_reason} pairs
        """
        errors = error_summary.get('errors', {})
        if not errors:
            return
        
        error_text = "\\n".join([
            f"• {file_name}: {reason}"
            for file_name, reason in errors.items()
        ])
        
        msg = f"{tab_name}: {len(errors)} file(s) failed to load:\\n\\n{error_text}"
        QMessageBox.warning(self, "Load Errors", msg)

    def _on_pcd_filter_changed(self) -> None:
        """Handle monitoring point filter change - refresh table."""
        # TODO: Implement filter logic to refresh table
        pass

    def stop_background_tasks(self) -> None:
        """Stop any active directory loader threads (SHUTDOWN SAFETY).

        This method is called by the main window during app exit to avoid
        background loaders attempting to update UI widgets after teardown.
        """
        loaders = [
            ("static_boreholes", self._static_loader_thread),
            ("borehole_monitoring", self._monitoring_loader_thread),
            ("pcd_monitoring", self._pcd_loader_thread),
        ]

        for name, loader in loaders:
            if loader and loader.isRunning():
                # Request cancellation and wait briefly for shutdown
                self._logger.info(f"Stopping {name} loader on exit")
                loader.cancel()
                loader.quit()
                loader.wait(2000)

    # ExcelManager now handles all Excel data access for monitoring and PCD tabs. This method is deprecated and removed.

    def _find_column(self, df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
        """Find a column in df that matches one of the candidate names.

        Args:
            df: DataFrame to search.
            candidates: List of candidate column names (case-insensitive).

        Returns:
            The matching DataFrame column name, or None if no match found.
        """
        normalized = {str(col).strip().lower(): col for col in df.columns}
        for name in candidates:
            key = name.strip().lower()
            if key in normalized:
                return normalized[key]
        return None

    # ==================== CHART GENERATION ====================

    def _on_static_generate(self) -> None:
        """Generate chart for static borehole data (month/year filter, multi-select, bar chart support)."""
        if not HAS_QTCHARTS:
            self.ui.static_chart_placeholder.setText(
                "QtCharts not available. Install PySide6-Addons to enable charts."
            )
            return

        if self._static_data is None or self._static_data.empty:
            self.ui.static_chart_placeholder.setText("Load files first to generate charts")
            return

        # Get selected chart type
        chart_type = self.ui.static_chart_type.currentText()

        # Determine selected boreholes (from multi-select or dropdown)
        selected_boreholes = self._selected_boreholes.copy() if len(self._selected_boreholes) > 0 else []
        
        # If no multi-select, use dropdown value
        if not selected_boreholes and hasattr(self.ui, 'combo_static_borehole'):
            bh = self.ui.combo_static_borehole.currentText().strip()
            if bh and not bh.startswith("Custom"):
                selected_boreholes = [bh]
        
        if not selected_boreholes:
            self.ui.static_chart_placeholder.setText(
                "Select a borehole or use Multi-select button"
            )
            self.ui.static_chart_placeholder.setVisible(True)
            return

        # Apply month/year date range filter
        df_filtered = self._static_data.copy()
        filter_from_str = "All dates"
        filter_to_str = "All dates"
        
        if (hasattr(self.ui, 'combo_year_from') and hasattr(self.ui, 'combo_month_from') and
            hasattr(self.ui, 'combo_year_to') and hasattr(self.ui, 'combo_month_to')):
            
            year_from = int(self.ui.combo_year_from.currentText())
            month_from = self.ui.combo_month_from.currentIndex() + 1  # 0-indexed
            year_to = int(self.ui.combo_year_to.currentText())
            month_to = self.ui.combo_month_to.currentIndex() + 1
            
            date_from = pd.Timestamp(year=year_from, month=month_from, day=1)
            # Last day of month
            import calendar
            last_day = calendar.monthrange(year_to, month_to)[1]
            date_to = pd.Timestamp(year=year_to, month=month_to, day=last_day)
            
            filter_from_str = date_from.strftime('%b %Y')
            filter_to_str = date_to.strftime('%b %Y')
            
            # Filter by date range
            if 'Date' in df_filtered.columns:
                df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
                df_filtered = df_filtered[
                    (df_filtered['Date'] >= date_from) &
                    (df_filtered['Date'] <= date_to)
                ]
        
        if df_filtered.empty:
            self.ui.static_chart_placeholder.setText(
                "No data in selected date range\\nAdjust date filters"
            )
            self.ui.static_chart_placeholder.setVisible(True)
            return

        # Limit to 10 boreholes for clarity
        display_limit = 10
        if len(selected_boreholes) > display_limit:
            self.ui.static_chart_placeholder.setText(
                f"Too many boreholes ({len(selected_boreholes)})\\nLimit to {display_limit} for clarity"
            )
            self.ui.static_chart_placeholder.setVisible(True)
            return

        # Create chart with clear, report-ready title
        chart = QChart()
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # Build automated title showing all active filters
        if len(selected_boreholes) == 1:
            title = f"Static Water Level: {selected_boreholes[0]}"
        elif len(selected_boreholes) <= 3:
            title = f"Static Water Level: {', '.join(selected_boreholes)}"
        else:
            title = f"Static Water Level: {len(selected_boreholes)} Boreholes"
        
        # IMPORTANT: Get actual data range from filtered data (not filter range)
        # This shows what data is actually displayed, not what user selected
        if 'Date' in df_filtered.columns:
            df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
            actual_min_date = df_filtered['Date'].min()
            actual_max_date = df_filtered['Date'].max()
            actual_from_str = actual_min_date.strftime('%b %Y')
            actual_to_str = actual_max_date.strftime('%b %Y')
            title += f"  |  {actual_from_str} to {actual_to_str}"

        # Create chart based on type
        if chart_type == "Bar":
            # Bar chart implementation
            bar_series = QBarSeries()
            
            for borehole_name in selected_boreholes:
                df_bh = df_filtered[df_filtered['Borehole'] == borehole_name].copy()
                if df_bh.empty:
                    continue
                
                df_bh = df_bh.sort_values('Date')
                bar_set = QBarSet(borehole_name)
                
                # Track min/max for Y-axis scaling
                values = []
                for _, row in df_bh.iterrows():
                    try:
                        level = float(row.get('Static Level', row.get('Static_Level', 0)))
                        bar_set.append(level)
                        values.append(level)
                    except (ValueError, TypeError):
                        continue
                
                if bar_set.count() > 0:
                    bar_series.append(bar_set)
            
            if bar_series.count() == 0:
                self.ui.static_chart_placeholder.setText("No valid data for bar chart")
                self.ui.static_chart_placeholder.setVisible(True)
                return
            
            chart.addSeries(bar_series)
            
            # Bar chart uses category axis
            categories = []
            all_dates = []
            for bh_name in selected_boreholes:
                df_bh = df_filtered[df_filtered['Borehole'] == bh_name].copy()
                for _, row in df_bh.iterrows():
                    try:
                        dt = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
                        if dt not in all_dates:
                            all_dates.append(dt)
                    except:
                        continue
            
            # Limit to 20 categories for readability
            categories = sorted(all_dates)[:20]
            
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setTitleText("Date")
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            bar_series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            axis_y.setTitleText("Static Level (m)")
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            bar_series.attachAxis(axis_y)
            
            # Auto-scale Y-axis to fit data
            all_levels = []
            for borehole_name in selected_boreholes:
                df_bh = df_filtered[df_filtered['Borehole'] == borehole_name].copy()
                for _, row in df_bh.iterrows():
                    try:
                        level = float(row.get('Static Level', row.get('Static_Level', 0)))
                        all_levels.append(level)
                    except:
                        continue
            
            if all_levels:
                min_val = min(all_levels)
                max_val = max(all_levels)
                margin = (max_val - min_val) * 0.1  # 10% margin
                axis_y.setRange(max(0, min_val - margin), max_val + margin)
            
        else:
            # Line/Scatter chart implementation
            series_list = []
            all_levels = []  # Track all Y values for auto-scaling
            
            for borehole_name in selected_boreholes:
                df_bh = df_filtered[df_filtered['Borehole'] == borehole_name].copy()
                if df_bh.empty:
                    continue
                
                df_bh = df_bh.sort_values('Date')
                
                # Create series based on chart type
                if chart_type == "Scatter":
                    series = QScatterSeries()
                    series.setMarkerSize(8)
                else:  # Line (default)
                    series = QLineSeries()
                
                series.setName(borehole_name)
                
                # Add data points
                for _, row in df_bh.iterrows():
                    try:
                        date_val = pd.to_datetime(row['Date'])
                        timestamp_ms = int(date_val.timestamp() * 1000)
                        level = float(row.get('Static Level', row.get('Static_Level', 0)))
                        series.append(timestamp_ms, level)
                        all_levels.append(level)
                    except (ValueError, TypeError):
                        continue
                
                if series.count() > 0:
                    series_list.append(series)
            
            if not series_list:
                self.ui.static_chart_placeholder.setText("No valid data for selected boreholes")
                self.ui.static_chart_placeholder.setVisible(True)
                return
            
            # Add all series to chart
            for series in series_list:
                chart.addSeries(series)
            
            # Setup axes with proper date formatting
            axis_x = QDateTimeAxis()
            axis_x.setFormat("yyyy-MM-dd")
            axis_x.setTitleText("Date")
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            
            axis_y = QValueAxis()
            axis_y.setTitleText("Static Level (m)")
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            
            # Attach axes to all series (only once per axis)
            for series in series_list:
                series.attachAxis(axis_x)
                series.attachAxis(axis_y)
            
            # Auto-scale Y-axis to fit all data with 10% margin
            if all_levels:
                min_val = min(all_levels)
                max_val = max(all_levels)
                margin = (max_val - min_val) * 0.1  # 10% margin
                axis_y.setRange(max(0, min_val - margin), max_val + margin)
        
        # Set title with larger, bold font for better visibility
        title_font = chart.titleFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setTitle(title)
        
        # Enable legend for all charts (helpful reference even for single borehole)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Remove existing chart if present
        if self._static_chart_view is not None:
            self.ui.staticChartLayout.removeWidget(self._static_chart_view)
            self._static_chart_view.deleteLater()

        # Create and add new chart view
        self._static_chart_view = QChartView(chart)
        self._static_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.ui.staticChartLayout.insertWidget(0, self._static_chart_view)
        
        # Hide placeholder text
        self.ui.static_chart_placeholder.setVisible(False)

    def _on_monitoring_generate(self) -> None:
        """Generate chart for monitoring data."""
        if not HAS_QTCHARTS:
            self.ui.monitoring_chart_placeholder.setText(
                "QtCharts not available. Install PySide6-Addons to enable charts."
            )
            return

        if self._monitoring_data is None or self._monitoring_data.empty:
            self.ui.monitoring_chart_placeholder.setText("Load files first to generate charts")
            return

        parameter = self.ui.comboBox_2.currentText().strip()
        if not parameter:
            self.ui.monitoring_chart_placeholder.setText("Select a parameter to chart")
            return

        chart = QChart()
        # Automated, report-ready title with filters and date range
        title_parts = [f"Monitoring Trend: {parameter}"]
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        df_filtered = self._monitoring_data.copy()

        borehole_value = self.ui.comboBox_3.currentText().strip()
        # Apply date range filter using month/year combos (SIMPLIFIED DATE PICKER)
        if (hasattr(self.ui, 'combo_year_from_monitoring') and hasattr(self.ui, 'combo_month_from_monitoring') and
            hasattr(self.ui, 'combo_year_to_monitoring') and hasattr(self.ui, 'combo_month_to_monitoring')):
            
            year_from = int(self.ui.combo_year_from_monitoring.currentText())
            month_from = self.ui.combo_month_from_monitoring.currentIndex() + 1  # 0-indexed
            year_to = int(self.ui.combo_year_to_monitoring.currentText())
            month_to = self.ui.combo_month_to_monitoring.currentIndex() + 1
            
            date_from = pd.Timestamp(year=year_from, month=month_from, day=1)
            # Last day of month
            import calendar
            last_day = calendar.monthrange(year_to, month_to)[1]
            date_to = pd.Timestamp(year=year_to, month=month_to, day=last_day)
            
            # Filter by date range
            if 'Date' in df_filtered.columns:
                df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
                df_filtered = df_filtered[
                    (df_filtered['Date'] >= date_from) &
                    (df_filtered['Date'] <= date_to)
                ]
                title_parts.append(f"Range: {date_from.strftime('%b %Y')} to {date_to.strftime('%b %Y')}")
        elif hasattr(self.ui, "date_monitoring_from") and hasattr(self.ui, "date_monitoring_to"):
            # Fallback to old date pickers if combos not available (backward compatibility)
            start_date = self.ui.date_monitoring_from.date().toPython()
            end_date = self.ui.date_monitoring_to.date().toPython()
            if start_date and end_date and start_date <= end_date:
                df_filtered = df_filtered[
                    (pd.to_datetime(df_filtered["Date"]) >= pd.Timestamp(start_date))
                    & (pd.to_datetime(df_filtered["Date"]) <= pd.Timestamp(end_date))
                ]
                title_parts.append(f"Range: {start_date} to {end_date}")

        if df_filtered.empty or parameter not in df_filtered.columns:
            self.ui.monitoring_chart_placeholder.setText("No data available for selected filters")
            return

        # Determine chart type (Line, Scatter, Bar, Area)
        chart_type = self.ui.monitoring_chart_type.currentText().strip()
        
        # Determine which boreholes to display (multi-select takes precedence over dropdown)
        # CRITICAL: Check multi-select FIRST, only use dropdown if multi-select is empty
        selected_items = self._selected_monitoring_boreholes.copy() if self._selected_monitoring_boreholes else []
        
        # If no multi-select, use dropdown value
        if not selected_items and borehole_value:
            selected_items = [borehole_value]
            title_parts.append(f"BH: {borehole_value}")
        elif selected_items:
            # Multi-select is active - show which boreholes are selected
            title_parts.append(f"BH: {', '.join(selected_items[:5])}" + ("..." if len(selected_items) > 5 else ""))
        
        if not selected_items:
            self.ui.monitoring_chart_placeholder.setText("Select boreholes using Multi-Select button or dropdown")
            return
        
        # Limit to 10 for clarity
        if len(selected_items) > 10:
            selected_items = selected_items[:10]
        
        # Filter df_filtered to ONLY include selected boreholes
        if 'Borehole' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Borehole'].isin(selected_items)]
        
        if df_filtered.empty:
            self.ui.monitoring_chart_placeholder.setText(f"No data for selected boreholes: {', '.join(selected_items)}")
            return
        
        # Build title showing all active filters (IMPROVED TITLE)
        # Add actual data date range (not filter range) to show what's really displayed
        if 'Date' in df_filtered.columns:
            df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
            actual_min_date = df_filtered['Date'].min()
            actual_max_date = df_filtered['Date'].max()
            if pd.notna(actual_min_date) and pd.notna(actual_max_date):
                title_parts.append(f"Data: {actual_min_date.strftime('%b %Y')} to {actual_max_date.strftime('%b %Y')}")
        
        # Set title with bold formatting (matching Static Levels tab)
        title_font = chart.titleFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setTitle(" | ".join(title_parts))

        # Plot each borehole as a separate series (limit to 10 for clarity)
        group_key = "Borehole" if "Borehole" in df_filtered.columns else None
        series_groups = (
            df_filtered.groupby(group_key) if group_key else [(parameter, df_filtered)]
        )

        # Choose series type based on chart type selection (supports Line, Scatter, Bar, Area, Threshold)
        if chart_type == "Bar":
            from PySide6.QtCharts import QBarSet, QBarSeries, QBarCategoryAxis
            bar_series = QBarSeries()
            all_values = []  # Track all values for Y-axis scaling
            
            # For bar charts, use categorical X-axis (selected boreholes)
            for bh_name in selected_items:
                bh_data = df_filtered[df_filtered['Borehole'] == bh_name] if group_key else df_filtered
                if bh_data.empty:
                    continue
                
                bar_set = QBarSet(str(bh_name))
                bh_data = bh_data.sort_values("Date")
                avg_value = bh_data[parameter].mean() if len(bh_data) > 0 else 0
                bar_set.append(avg_value)
                all_values.append(avg_value)
                bar_series.append(bar_set)
            
            chart.addSeries(bar_series)
            
            # Categorical X-axis for bar chart
            axis_x = QBarCategoryAxis()
            axis_x.append([str(bh) for bh in selected_items])
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            bar_series.attachAxis(axis_x)
            
            # Value Y-axis with auto-scaling
            value_axis = QValueAxis()
            value_axis.setTitleText(parameter)
            chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)
            bar_series.attachAxis(value_axis)
            
            # Auto-scale Y-axis to fit data
            if all_values:
                min_val = min(all_values)
                max_val = max(all_values)
                margin = (max_val - min_val) * 0.1 if max_val != min_val else max_val * 0.1
                value_axis.setRange(max(0, min_val - margin), max_val + margin)
        
        else:
            # Line or Scatter chart (existing logic with multi-select)
            series_class = QLineSeries
            if chart_type == "Scatter":
                series_class = QScatterSeries
            
            all_values = []  # Track all values for Y-axis scaling
            
            for bh_name in selected_items:
                bh_data = df_filtered[df_filtered['Borehole'] == bh_name] if group_key else df_filtered
                if bh_data.empty:
                    continue
                
                series = series_class()
                series.setName(str(bh_name))
                bh_data = bh_data.sort_values("Date")
                
                for _, row in bh_data.iterrows():
                    try:
                        x_val = int(pd.to_datetime(row["Date"]).timestamp() * 1000)
                        y_val = float(row[parameter])
                        series.append(x_val, y_val)
                        all_values.append(y_val)
                    except Exception:
                        continue
                
                if series.count() > 0:
                    chart.addSeries(series)

            # Date axis
            date_axis = QDateTimeAxis()
            date_axis.setFormat("yyyy-MM-dd")
            date_axis.setTitleText("Date")
            chart.addAxis(date_axis, Qt.AlignmentFlag.AlignBottom)

            value_axis = QValueAxis()
            value_axis.setTitleText(parameter)
            chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)

            date_values = df_filtered["Date"].dropna()
            if not date_values.empty:
                min_dt = pd.to_datetime(date_values.min())
                max_dt = pd.to_datetime(date_values.max())
                date_axis.setRange(
                    QDateTime.fromMSecsSinceEpoch(int(min_dt.timestamp() * 1000)),
                    QDateTime.fromMSecsSinceEpoch(int(max_dt.timestamp() * 1000)),
                )

            for series in chart.series():
                series.attachAxis(date_axis)
                series.attachAxis(value_axis)
            
            # Auto-scale Y-axis to fit all data (FIX Y-AXIS SCALING)
            if all_values:
                min_val = min(all_values)
                max_val = max(all_values)
                margin = (max_val - min_val) * 0.1 if max_val != min_val else max_val * 0.1
                value_axis.setRange(max(0, min_val - margin), max_val + margin)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        if self._monitoring_chart_view is not None:
            self.ui.monitoringChartLayout.removeWidget(self._monitoring_chart_view)
            self._monitoring_chart_view.deleteLater()

        self._monitoring_chart_view = QChartView(chart)
        self._monitoring_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.ui.monitoringChartLayout.insertWidget(0, self._monitoring_chart_view)
        self.ui.monitoring_chart_placeholder.setVisible(False)

    def _on_pcd_generate(self) -> None:
        """Generate chart for PCD monitoring data."""
        if not HAS_QTCHARTS:
            self.ui.pcd_chart_placeholder.setText(
                "QtCharts not available. Install PySide6-Addons to enable charts."
            )
            return

        if self._pcd_data is None or self._pcd_data.empty:
            self.ui.pcd_chart_placeholder.setText("Load files first to generate charts")
            return

        parameter = self.ui.comboBox_5.currentText().strip()
        if not parameter:
            self.ui.pcd_chart_placeholder.setText("Select a parameter to chart")
            return

        chart = QChart()
        # Automated, report-ready title with filters and date range
        title_parts = [f"PCD Trend: {parameter}"]
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        df_filtered = self._pcd_data.copy()
        
        # Apply date range filter using month/year combos (SIMPLIFIED DATE PICKER)
        if (hasattr(self.ui, 'combo_year_from_pcd') and hasattr(self.ui, 'combo_month_from_pcd') and
            hasattr(self.ui, 'combo_year_to_pcd') and hasattr(self.ui, 'combo_month_to_pcd')):
            
            year_from = int(self.ui.combo_year_from_pcd.currentText())
            month_from = self.ui.combo_month_from_pcd.currentIndex() + 1  # 0-indexed
            year_to = int(self.ui.combo_year_to_pcd.currentText())
            month_to = self.ui.combo_month_to_pcd.currentIndex() + 1
            
            date_from = pd.Timestamp(year=year_from, month=month_from, day=1)
            # Last day of month
            import calendar
            last_day = calendar.monthrange(year_to, month_to)[1]
            date_to = pd.Timestamp(year=year_to, month=month_to, day=last_day)
            
            # Filter by date range
            if 'Date' in df_filtered.columns:
                df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
                df_filtered = df_filtered[
                    (df_filtered['Date'] >= date_from) &
                    (df_filtered['Date'] <= date_to)
                ]
                title_parts.append(f"Range: {date_from.strftime('%b %Y')} to {date_to.strftime('%b %Y')}")

        if df_filtered.empty or parameter not in df_filtered.columns:
            self.ui.pcd_chart_placeholder.setText("No data available for selected filters")
            return

        # Determine chart type (Line, Scatter, Bar, Area)
        chart_type = self.ui.pcd_chart_type.currentText().strip()
        
        # Get monitoring point from dropdown (comboBox_6 is the PCD monitoring point selector)
        point_value = self.ui.comboBox_6.currentText().strip() if hasattr(self.ui, 'comboBox_6') else None
        
        # Determine which points to display (multi-select takes precedence over dropdown)
        # CRITICAL: Check multi-select FIRST, only use dropdown if multi-select is empty
        selected_points = self._selected_pcd_points.copy() if self._selected_pcd_points else []
        
        # If no multi-select, use dropdown value
        if not selected_points and point_value:
            selected_points = [point_value]
            title_parts.append(f"Point: {point_value}")
        elif selected_points:
            # Multi-select is active - show which points are selected
            title_parts.append(f"Point: {', '.join(selected_points[:5])}" + ("..." if len(selected_points) > 5 else ""))
        
        if not selected_points:
            self.ui.pcd_chart_placeholder.setText("Select points using Multi-Select button or dropdown")
            return
        
        # Limit to 10 for clarity
        if len(selected_points) > 10:
            selected_points = selected_points[:10]
        
        # Filter df_filtered to ONLY include selected points
        if 'Point' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Point'].isin(selected_points)]
        
        if df_filtered.empty:
            self.ui.pcd_chart_placeholder.setText(f"No data for selected points: {', '.join(selected_points)}")
            return
        
        # Build title showing all active filters (IMPROVED TITLE)
        if 'Date' in df_filtered.columns:
            df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
            actual_min_date = df_filtered['Date'].min()
            actual_max_date = df_filtered['Date'].max()
            if pd.notna(actual_min_date) and pd.notna(actual_max_date):
                title_parts.append(f"Data: {actual_min_date.strftime('%b %Y')} to {actual_max_date.strftime('%b %Y')}")
        
        # Set title with bold formatting (matching Static Levels tab)
        title_font = chart.titleFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        chart.setTitleFont(title_font)
        chart.setTitle(" | ".join(title_parts))

        # Choose series type based on chart type selection
        all_values = []  # Track all values for Y-axis scaling
        
        if chart_type == "Bar":
            from PySide6.QtCharts import QBarSet, QBarSeries, QBarCategoryAxis
            bar_series = QBarSeries()
            
            # For bar charts, create bar per selected point
            for pt_name in selected_points:
                pt_data = df_filtered[df_filtered['Point'] == pt_name] if 'Point' in df_filtered.columns else df_filtered
                if pt_data.empty:
                    continue
                
                bar_set = QBarSet(str(pt_name))
                pt_data = pt_data.sort_values("Date")
                avg_value = pt_data[parameter].mean() if len(pt_data) > 0 else 0
                bar_set.append(avg_value)
                all_values.append(avg_value)
                bar_series.append(bar_set)
            
            chart.addSeries(bar_series)
            
            # Categorical X-axis for bar chart
            axis_x = QBarCategoryAxis()
            axis_x.append([str(pt) for pt in selected_points])
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            bar_series.attachAxis(axis_x)
            
            # Value Y-axis
            value_axis = QValueAxis()
            value_axis.setTitleText(parameter)
            chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)
            bar_series.attachAxis(value_axis)
            
            # Auto-scale Y-axis
            if all_values:
                min_val = min(all_values)
                max_val = max(all_values)
                margin = (max_val - min_val) * 0.1 if max_val != min_val else max_val * 0.1
                value_axis.setRange(max(0, min_val - margin), max_val + margin)
        
        else:
            # Line or Scatter chart with multi-select support
            series_class = QLineSeries
            if chart_type == "Scatter":
                series_class = QScatterSeries

            # Loop through all selected points to create multiple series
            for pt_name in selected_points:
                pt_data = df_filtered[df_filtered['Point'] == pt_name] if 'Point' in df_filtered.columns else df_filtered
                if pt_data.empty:
                    continue
                
                series = series_class()
                series.setName(str(pt_name))
                pt_data = pt_data.sort_values("Date")
                
                for _, row in pt_data.iterrows():
                    try:
                        x_val = int(pd.to_datetime(row["Date"]).timestamp() * 1000)
                        y_val = float(row[parameter])
                        series.append(x_val, y_val)
                        all_values.append(y_val)  # Track for scaling
                    except Exception:
                        continue

                if series.count() > 0:
                    chart.addSeries(series)

            date_axis = QDateTimeAxis()
            date_axis.setFormat("yyyy-MM-dd")
            date_axis.setTitleText("Date")
            chart.addAxis(date_axis, Qt.AlignmentFlag.AlignBottom)

            value_axis = QValueAxis()
            value_axis.setTitleText(parameter)
            chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)

            date_values = df_filtered["Date"].dropna()
            if not date_values.empty:
                min_dt = pd.to_datetime(date_values.min())
                max_dt = pd.to_datetime(date_values.max())
                date_axis.setRange(
                    QDateTime.fromMSecsSinceEpoch(int(min_dt.timestamp() * 1000)),
                    QDateTime.fromMSecsSinceEpoch(int(max_dt.timestamp() * 1000)),
                )

            for series in chart.series():
                series.attachAxis(date_axis)
                series.attachAxis(value_axis)
            
            # Auto-scale Y-axis to fit all data
            if all_values:
                min_val = min(all_values)
                max_val = max(all_values)
                margin = (max_val - min_val) * 0.1 if max_val != min_val else max_val * 0.1
                value_axis.setRange(max(0, min_val - margin), max_val + margin)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        if self._pcd_chart_view is not None:
            self.ui.pcdChartLayout.removeWidget(self._pcd_chart_view)
            self._pcd_chart_view.deleteLater()

        self._pcd_chart_view = QChartView(chart)
        self._pcd_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.ui.pcdChartLayout.insertWidget(0, self._pcd_chart_view)
        self.ui.pcd_chart_placeholder.setVisible(False)

    def _create_demo_chart(self, layout, placeholder_label, chart_attr, title: str) -> None:
        """Create and display a demo chart (placeholder implementation).
        
        Args:
            layout: QVBoxLayout to add chart to
            placeholder_label: Label to hide when chart renders
            chart_attr: Attribute name to store chart view reference
            title: Chart title
        """
        if not HAS_QTCHARTS:
            return

        # Create simple line series with demo data
        series = QLineSeries()
        series.setName("Data Trend")
        
        demo_points = [
            (1, 100), (2, 110), (3, 105), (4, 120), (5, 115),
            (6, 130), (7, 125), (8, 140), (9, 135), (10, 150)
        ]
        
        for x, y in demo_points:
            series.append(x, y)

        # Create chart
        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setTitle(title)
        chart.legend().setVisible(True)

        # Remove existing chart if present
        existing_view = getattr(self, chart_attr, None)
        if existing_view is not None:
            layout.removeWidget(existing_view)
            existing_view.deleteLater()

        # Create and add new chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.insertWidget(0, chart_view)
        
        # Update stored reference
        setattr(self, chart_attr, chart_view)
        
        # Hide placeholder text
        placeholder_label.setVisible(False)    
    def _parse_static_levels_excel(self, filepath: str) -> pd.DataFrame:
        """Parse static level sheet with robust detection of shifted rows/columns.
        
        Heuristic detection:
        - Treat any non-empty text cell as a potential borehole name cell (r,c).
        - Validate block below it: rows r+1.. (2-6 rows), same column c must be dates,
          adjacent column c+1 must be numeric levels. Stop at first failure.
        - Collect all valid blocks across all columns/rows. De-duplicate rows.
        
        Returns:
            DataFrame with columns: borehole, date, level, borehole_norm
        """
        # Load with best-effort engine fallback
        try:
            sheet = pd.read_excel(filepath, header=None)
        except Exception as e:
            try:
                sheet = pd.read_excel(filepath, header=None, engine='openpyxl')
            except Exception:
                raise e

        nrows, ncols = sheet.shape

        def try_parse_date(val):
            if pd.isna(val):
                return None
            v = val
            if isinstance(v, str):
                v = v.replace('\xa0', '').strip()
                if not v:
                    return None
            # Direct datetime parse (round to ms to avoid nanosecond warnings)
            try:
                ts = pd.to_datetime(v)
                if pd.isna(ts):
                    return None
                return ts.round("ms").to_pydatetime()
            except Exception:
                pass
            # Excel serial fallback
            try:
                return pd.to_datetime("1899-12-30") + pd.to_timedelta(float(v), unit='D')
            except Exception:
                return None

        def is_number(val):
            if pd.isna(val):
                return False
            try:
                float(val)
                return True
            except Exception:
                return False

        results = []
        seen = set()  # (name, date)
        # Scan all cells for potential name headers
        for r0 in range(nrows):
            for c0 in range(ncols):
                name_val = sheet.iat[r0, c0]
                if pd.isna(name_val):
                    continue
                # A name is a short-to-medium string; skip obvious non-text
                if not isinstance(name_val, str):
                    # Accept non-string only if it looks like a code when casted
                    try:
                        name_str = str(name_val).strip()
                    except Exception:
                        continue
                else:
                    name_str = name_val.strip()
                if not name_str:
                    continue
                # Skip if this cell itself looks like a date or a number (likely a data row, not header)
                if try_parse_date(name_val) is not None:
                    continue
                if is_number(name_val):
                    continue
                # Validate that below we have date/level columns (c0 is date, c0+1 is level)
                if c0 + 1 >= ncols:
                    continue
                # Accumulate 2..6 rows as a block, commit only if >=2
                local = []
                local_keys = set()
                collected = 0
                for rr in range(r0 + 1, min(r0 + 1 + 6, nrows)):
                    dval = sheet.iat[rr, c0]
                    lval = sheet.iat[rr, c0 + 1]
                    d = try_parse_date(dval)
                    if d is None or not is_number(lval):
                        break
                    level = float(lval)
                    key = (name_str, d)
                    if key in seen or key in local_keys:
                        continue
                    local_keys.add(key)
                    local.append({
                        'borehole': name_str,
                        'date': d,
                        'level': level,
                        'borehole_norm': name_str.upper()
                    })
                    collected += 1
                if collected >= 2:
                    results.extend(local)
                    seen.update(local_keys)

        parsed = pd.DataFrame(results)
        if parsed.empty:
            return parsed
        # Clean and sort
        parsed = parsed.sort_values(['borehole', 'date']).reset_index(drop=True)
        return parsed

    # ==================== CHART SAVE METHODS (EXPORT FUNCTIONALITY) ====================

    def _on_static_save_chart(self) -> None:
        """Save the Static Levels chart as an image file.
        
        Supports PNG, JPEG, PDF, and SVG formats. Uses QChartView.grab() for
        raster formats and QSvgGenerator for vector format.
        """
        if self._static_chart_view is None:
            QMessageBox.information(self, "No Chart", "Generate a chart first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Static Levels Chart",
            "static_levels_chart.png",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;PDF Document (*.pdf);;SVG Vector (*.svg);;All Files (*.*)",
        )
        if not path:
            return
        
        if not self._save_chart(self._static_chart_view, path):
            QMessageBox.warning(self, "Save Failed", "Unable to save chart.")

    def _on_monitoring_save_chart(self) -> None:
        """Save the Borehole Monitoring chart as an image file.
        
        Supports PNG, JPEG, PDF, and SVG formats.
        """
        if self._monitoring_chart_view is None:
            QMessageBox.information(self, "No Chart", "Generate a chart first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Borehole Monitoring Chart",
            "monitoring_chart.png",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;PDF Document (*.pdf);;SVG Vector (*.svg);;All Files (*.*)",
        )
        if not path:
            return
        
        if not self._save_chart(self._monitoring_chart_view, path):
            QMessageBox.warning(self, "Save Failed", "Unable to save chart.")

    def _on_pcd_save_chart(self) -> None:
        """Save the PCD Monitoring chart as an image file.
        
        Supports PNG, JPEG, PDF, and SVG formats.
        """
        if self._pcd_chart_view is None:
            QMessageBox.information(self, "No Chart", "Generate a chart first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PCD Monitoring Chart",
            "pcd_chart.png",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;PDF Document (*.pdf);;SVG Vector (*.svg);;All Files (*.*)",
        )
        if not path:
            return
        
        if not self._save_chart(self._pcd_chart_view, path):
            QMessageBox.warning(self, "Save Failed", "Unable to save chart.")

    def _save_chart(self, chart_view: QChartView, path: str) -> bool:
        """Generic save method for all chart views (delegates to format-specific handlers).
        
        Args:
            chart_view: The QChartView widget to save
            path: File path for saving (format determined by extension)
        
        Returns:
            True if save successful, False otherwise
        """
        suffix = Path(path).suffix.lower()
        
        if suffix == ".pdf":
            return self._export_chart_to_pdf(chart_view, path)
        elif suffix == ".svg":
            return self._export_chart_to_svg(chart_view, path)
        else:
            # Default image export (PNG/JPEG)
            try:
                pixmap = chart_view.grab()
                if pixmap.save(path):
                    QMessageBox.information(self, "Saved", f"Chart saved to:\n{path}")
                    return True
            except Exception:
                pass
            return False

    def _export_chart_to_pdf(self, chart_view: QChartView, path: str) -> bool:
        """Export chart to PDF for report-ready output.
        
        Uses QPdfWriter and QPainter to render the chart view at high resolution.
        """
        try:
            size = chart_view.size()
            pdf = QPdfWriter(path)
            pdf.setPageSize(
                QPageSize(QSizeF(size.width(), size.height()), QPageSize.Unit.Point)
            )
            pdf.setResolution(300)
            
            painter = QPainter(pdf)
            chart_view.render(painter)
            painter.end()
            
            QMessageBox.information(self, "Saved", f"Chart saved to:\n{path}")
            return True
        except Exception:
            return False

    def _export_chart_to_svg(self, chart_view: QChartView, path: str) -> bool:
        """Export chart to SVG (vector) for scalable report usage.
        
        Returns False if QtSvg addon is unavailable.
        """
        if not HAS_QTSVG or QSvgGenerator is None:
            QMessageBox.information(
                self,
                "SVG Not Available",
                "QtSvg is not available. Install PySide6-Addons to enable SVG export.",
            )
            return False
        
        try:
            size = chart_view.size()
            generator = QSvgGenerator()
            generator.setFileName(path)
            generator.setSize(size)
            generator.setViewBox(QRect(0, 0, size.width(), size.height()))
            
            painter = QPainter(generator)
            chart_view.render(painter)
            painter.end()
            
            QMessageBox.information(self, "Saved", f"Chart saved to:\n{path}")
            return True
        except Exception:
            return False
