"""
Monitoring Data Dashboard - PySide6 Controller

Orchestrates loading, parsing, and displaying monitoring data.

Architecture:
1. Load YAML source definitions from config
2. Create tabs for each enabled source
3. Each tab:
   - Load button triggers async data loader
   - Data table displays parsed records
   - Chart shows time series trends
   - Error display shows validation issues
4. Background threading keeps UI responsive

REUSE:
- Async loading from monitoring_data_loader.py (REUSE AsyncDatabaseLoader pattern)
- Chart embedding from existing chart utilities (if available)
- Pydantic models for type safety
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QGroupBox, QTextEdit,
    QProgressBar, QMessageBox, QHeaderView, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot
from PySide6.QtGui import QColor, QFont
from pathlib import Path
import logging
import os
import yaml
import pandas as pd

from models.monitoring_data import DataSourceDefinition, StructureType
from services.monitoring_data_loader import MonitoringDataLoader
from core.config_manager import get_resource_path


logger = logging.getLogger(__name__)


# ============================================================================
# WORKER THREAD (for async loading)
# ============================================================================

class DataLoaderWorker(QThread):
    """Worker thread for loading data in background"""
    
    # Signals
    loading_started = Signal()
    loading_progress = Signal(str)  # Progress message
    loading_completed = Signal(object, object)  # (loader, result)
    loading_error = Signal(str)  # Error message
    
    def __init__(self, loader: MonitoringDataLoader):
        super().__init__()
        self.loader = loader
    
    def run(self):
        """Run in background thread"""
        try:
            self.loading_started.emit()
            self.loading_progress.emit(f"Loading {self.loader.source_def.name}...")
            
            result = self.loader.load()
            
            self.loading_completed.emit(self.loader, result)
        
        except Exception as e:
            self.loading_error.emit(str(e))


# ============================================================================
# MONITORING DATA SOURCE TAB
# ============================================================================

class MonitoringSourceTab(QWidget):
    """Single monitoring data source tab"""
    
    def __init__(self, source_def: DataSourceDefinition, parent=None):
        super().__init__(parent)
        self.source_def = source_def
        self.loader: MonitoringDataLoader = None
        self.worker_thread: DataLoaderWorker = None
        self.data: pd.DataFrame = None
        
        self._create_widgets()
        self._connect_signals()
    
    def _create_widgets(self):
        """Create UI components"""
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # ===== HEADER (buttons, status) =====
        header = QHBoxLayout()
        
        # Load button
        self.btn_load = QPushButton(f"Load {self.source_def.name}")
        self.btn_load.clicked.connect(self._on_load_clicked)
        header.addWidget(self.btn_load)
        
        # Status label
        self.lbl_status = QLabel("Ready")
        header.addWidget(self.lbl_status)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(20)
        self.progress.setVisible(False)
        header.addWidget(self.progress)
        
        header.addStretch()
        layout.addLayout(header)
        
        # ===== PANED WINDOW (table + chart area) =====
        splitter = QSplitter(Qt.Horizontal)
        
        # ----- TABLE FRAME -----
        table_group = QGroupBox("Data")
        table_layout = QVBoxLayout()
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter table rows...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_box)
        table_layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.table)
        
        table_group.setLayout(table_layout)
        splitter.addWidget(table_group)
        
        # ----- CHART FRAME -----
        chart_group = QGroupBox("Chart")
        chart_layout = QVBoxLayout()
        self.chart_label = QLabel("Chart will display here once data is loaded")
        self.chart_label.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(self.chart_label)
        chart_group.setLayout(chart_layout)
        splitter.addWidget(chart_group)
        
        splitter.setSizes([600, 600])
        layout.addWidget(splitter)
        
        # ===== ERROR FRAME =====
        error_group = QGroupBox("Errors & Warnings")
        error_layout = QVBoxLayout()
        
        self.text_errors = QTextEdit()
        self.text_errors.setReadOnly(True)
        self.text_errors.setMaximumHeight(80)
        error_layout.addWidget(self.text_errors)
        
        error_group.setLayout(error_layout)
        layout.addWidget(error_group)
    
    def _connect_signals(self):
        """Connect signals"""
        pass
    
    def _on_load_clicked(self):
        """Load data (async)"""
        
        self.btn_load.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.lbl_status.setText("Loading...")
        self.text_errors.clear()
        
        # Create loader
        self.loader = MonitoringDataLoader(self.source_def)
        
        # Create worker thread
        self.worker_thread = DataLoaderWorker(self.loader)
        self.worker_thread.loading_completed.connect(self._on_load_completed)
        self.worker_thread.loading_error.connect(self._on_load_error)
        
        # Start thread
        self.worker_thread.start()
    
    @Slot(object, object)
    def _on_load_completed(self, loader: MonitoringDataLoader, result):
        """Called when async load completes"""
        
        self.progress.setVisible(False)
        self.btn_load.setEnabled(True)
        
        # Get data
        self.data = loader.get_dataframe()
        stats = loader.get_statistics()
        
        self.lbl_status.setText(
            f"{stats['total_records']} records from {stats['files_scanned']} files "
            f"({stats['total_time_ms']})"
        )
        
        # Display table
        self._display_table()
        
        # Display errors (if any)
        if result.total_errors > 0:
            errors_text = f"Found {result.total_errors} errors:\n\n"
            for file_result in result.file_results:
                if file_result.errors:
                    errors_text += f"{Path(file_result.file_path).name}:\n"
                    for error_msg in file_result.errors[:3]:  # Show first 3
                        errors_text += f"  - {error_msg}\n"
            
            self.text_errors.setText(errors_text)
    
    @Slot(str)
    def _on_load_error(self, error: str):
        """Called when load fails"""
        
        self.progress.setVisible(False)
        self.btn_load.setEnabled(True)
        self.lbl_status.setText(f"Error: {error}")
        self.text_errors.setText(f"Load Error:\n{error}")
        
        QMessageBox.critical(self, "Load Error", error)
    
    def _display_table(self):
        """Populate table with data"""
        
        if self.data is None or len(self.data) == 0:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        
        # Set columns
        columns = list(self.data.columns)
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Add rows
        self.table.setRowCount(len(self.data))
        for row_idx, (idx, row) in enumerate(self.data.iterrows()):
            for col_idx, col in enumerate(columns):
                value = str(row[col])
                item = QTableWidgetItem(value)
                self.table.setItem(row_idx, col_idx, item)
    
    def _on_search_changed(self, text: str):
        """Filter table based on search text"""
        
        if not self.data or len(self.data) == 0:
            return
        
        if not text:
            # Show all
            self._display_table()
            return
        
        # Filter data
        text_lower = text.lower()
        mask = self.data.astype(str).apply(
            lambda x: x.str.contains(text_lower, case=False, na=False)
        ).any(axis=1)
        
        filtered = self.data[mask]
        
        # Display filtered
        columns = list(self.data.columns)
        self.table.setRowCount(len(filtered))
        
        for row_idx, (idx, row) in enumerate(filtered.iterrows()):
            for col_idx, col in enumerate(columns):
                value = str(row[col])
                item = QTableWidgetItem(value)
                self.table.setItem(row_idx, col_idx, item)


# ============================================================================
# MONITORING DASHBOARD (MAIN WIDGET)
# ============================================================================

class MonitoringDataDashboard(QWidget):
    """
    Main monitoring data dashboard with tabs per source.
    
    Features:
    - Multiple tabs (one per enabled monitoring source)
    - Each tab: data table + chart + errors
    - Search/filter per tab
    - Async loading from Excel directories
    - Background threading (non-blocking)
    
    Usage:
        dashboard = MonitoringDataDashboard()
        # Add to main window or dialog
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.tabs = {}
        self.notebook = QTabWidget()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.notebook)
        self.setLayout(layout)
        
        # Load sources from config
        self._load_sources()
    
    def _load_sources(self):
        """Load monitoring sources from YAML config"""
        
        try:
            user_dir = os.environ.get("WATERBALANCE_USER_DIR", "")
            if user_dir:
                config_path = Path(user_dir) / "config" / "monitoring_data_sources.yaml"
            else:
                config_path = get_resource_path("config/monitoring_data_sources.yaml")

            if not config_path.exists():
                config_path = get_resource_path("config/monitoring_data_sources.yaml")

            if not config_path.exists():
                self.notebook.addTab(
                    QLabel("Config file not found: config/monitoring_data_sources.yaml"),
                    "Error"
                )
                return
            
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            
            sources = config_data.get('monitoring_data_sources', [])
            
            if not sources:
                self.notebook.addTab(
                    QLabel("No monitoring sources configured"),
                    "Empty"
                )
                return
            
            for source_dict in sources:
                # Create source definition
                source_def = DataSourceDefinition(**source_dict)
                
                # Skip disabled sources
                if not source_dict.get('enabled', True):
                    continue
                
                # Create tab
                tab = MonitoringSourceTab(source_def)
                self.notebook.addTab(tab, source_def.name)
                self.tabs[source_def.id] = tab
        
        except Exception as e:
            error_label = QLabel(f"Error loading sources: {e}")
            error_label.setAlignment(Qt.AlignCenter)
            self.notebook.addTab(error_label, "Error")


if __name__ == "__main__":
    """Test dashboard"""
    
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dashboard = MonitoringDataDashboard()
    dashboard.setWindowTitle("Monitoring Data Dashboard - Test")
    dashboard.resize(1200, 800)
    dashboard.show()
    
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("✅ Dashboard UI ready for testing")
    logger.info("Click 'Load' buttons to parse Excel files\n")
    
    sys.exit(app.exec())
