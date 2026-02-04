"""
Recirculation Manager Dialog (UI FOR CONFIGURING RECIRCULATION MAPPING).

Allows users to:
- See all storage/dam components
- Enable/disable recirculation for each
- Select sheet and column from Excel (no typing)
- Save configuration to diagram JSON

Dialog displays as table with columns:
- Component Name
- Has Recirculation? (toggle)
- Excel Sheet Name (dropdown)
- Excel Column Name (dropdown)

Uses centralized ExcelManager for all Excel operations (unified with flow volumes + other systems).
"""

import json
from pathlib import Path
from typing import Dict, List
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

# Use centralized Excel manager (shared with flow volumes, analytics, etc.)
from services.excel_manager import ExcelManager, get_excel_manager

logger = logging.getLogger(__name__)


class RecirculationManagerDialog(QDialog):
    """Dialog to manage recirculation mapping (CONFIGURATION UI).
    
    Attributes:
        diagram_data: Dict with nodes and recirculation config
        diagram_path: Path to save updated diagram
    """
    
    def __init__(self, diagram_data: Dict, diagram_path: str, parent=None):
        """Initialize recirculation manager dialog.
        
        Uses centralized ExcelManager singleton for Excel operations.
        This ensures recirculation loading is coordinated with flow volumes
        and other Excel-dependent systems.
        
        Args:
            diagram_data: Current diagram data (with nodes and recirculation config)
            diagram_path: Path to diagram JSON for saving
            parent: Parent widget
        """
        super().__init__(parent)
        self.diagram_data = diagram_data
        self.diagram_path = Path(diagram_path)
        self.setWindowTitle("Recirculation Manager")
        # Made dialog bigger to accommodate long Excel column names
        self.setGeometry(50, 50, 1200, 600)
        
        # Use centralized ExcelManager (shared resource with flow volumes, analytics, etc.)
        self.excel_manager = get_excel_manager()
        
        # Load available sheets from centralized manager
        # These are the same sheets used for flow volumes, ensuring coordination
        self.available_sheets = self.excel_manager.list_flow_sheets()
        self.available_columns = {}  # Will be populated per sheet (cached)
        
        # Get storage/dam components from diagram
        self.storage_components = self._get_storage_components()
        
        # Build UI
        self._setup_ui()
        
        # Load current configuration
        self._load_configuration()
        
        logger.info(f"RecirculationManagerDialog opened with {len(self.storage_components)} components, {len(self.available_sheets)} sheets (via ExcelManager)")
    
    def _get_storage_components(self) -> List[Dict]:
        """Extract all storage/dam nodes from diagram.
        
        Returns:
            List of node dicts with id, label, type
        """
        nodes = self.diagram_data.get('nodes', [])
        storage = []
        
        for node in nodes:
            node_type = node.get('type', '').lower()
            # Include any component with 'storage', 'dam', 'reservoir', 'tsf' in the type name
            if any(keyword in node_type for keyword in ['storage', 'dam', 'reservoir', 'tsf']):
                storage.append({
                    'id': node.get('id', ''),
                    'label': node.get('label', ''),
                    'type': node_type
                })
        
        return storage
    
    def _load_excel_sheets(self) -> List[str]:
        """Load available sheet names from Flow Diagram Excel via ExcelManager.
        
        This uses the centralized ExcelManager, ensuring coordination with
        flow volumes and other systems that load the same Excel file.
        
        Returns:
            List of sheet names (e.g., ['Flows_UG2N', 'Flows_UG2S', ...])
        """
        try:
            # Use centralized manager's method (same sheets used for flow volumes)
            sheets = self.excel_manager.list_flow_sheets()
            logger.info(f"Loaded {len(sheets)} flow sheets via ExcelManager: {sheets}")
            return sheets
        except Exception as e:
            logger.error(f"Error loading Excel sheets via ExcelManager: {e}")
            return []
    
    def _load_excel_columns(self, sheet_name: str) -> List[str]:
        """Load available column names from specific Excel sheet via ExcelManager.
        
        Uses centralized ExcelManager's list_flow_columns() method.
        This ensures we're using the same column parsing logic as flow volumes.
        
        Args:
            sheet_name: Name of sheet to read columns from
            
        Returns:
            List of column names (header row values, excluding Year/Month/Date)
        """
        try:
            if sheet_name in self.available_columns:
                # Already cached
                return self.available_columns[sheet_name]
            
            # Use centralized manager's method (same parsing as flow volumes)
            columns = self.excel_manager.list_flow_columns(sheet_name)
            
            # Cache for future use
            self.available_columns[sheet_name] = columns
            
            logger.info(f"Loaded {len(columns)} columns from sheet '{sheet_name}' via ExcelManager")
            return columns
            
        except Exception as e:
            logger.error(f"Error loading columns from {sheet_name} via ExcelManager: {e}")
            return []
    
    def _setup_ui(self):
        """Build dialog UI (LAYOUT BUILDER)."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Configure Recirculation Volumes")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Description (get Excel file name from manager)
        excel_path = self.excel_manager.get_flow_diagram_path()
        excel_file = excel_path.name if excel_path else "Excel file"
        desc = QLabel(
            f"Select which components have internal recirculation and map to Excel columns.\n"
            f"Data will be loaded from {excel_file}"
        )
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Component Name",
            "Has Recirculation",
            "Excel Sheet",
            "Excel Column"
        ])
        self.table.setRowCount(len(self.storage_components))
        self.table.setMinimumHeight(450)  # Increased for better viewing
        
        # Populate table rows
        for row, component in enumerate(self.storage_components):
            # Column 0: Component name (read-only)
            name_item = QTableWidgetItem(component['label'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Column 1: Checkbox for enabled
            checkbox_widget = QCheckBox()
            checkbox_widget.stateChanged.connect(lambda state, r=row: self._on_checkbox_changed(r, state))
            self.table.setCellWidget(row, 1, checkbox_widget)
            
            # Column 2: Sheet selector (dropdown)
            sheet_combo = QComboBox()
            sheet_combo.addItem("-- Select Sheet --")  # Placeholder
            sheet_combo.addItems(self.available_sheets)
            sheet_combo.currentTextChanged.connect(lambda text, r=row: self._on_sheet_changed(r, text))
            self.table.setCellWidget(row, 2, sheet_combo)
            
            # Column 3: Column selector (dropdown)
            col_combo = QComboBox()
            col_combo.addItem("-- Select Column --")  # Placeholder
            self.table.setCellWidget(row, 3, col_combo)
        
        # Adjust column widths (wider to show long Excel column names)
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 240)
        self.table.setColumnWidth(3, 420)  # Extra wide for Excel column names
        
        # Enable horizontal scrolling if needed
        self.table.horizontalScrollBar().setEnabled(True)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_configuration)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_checkbox_changed(self, row: int, state):
        """Handle checkbox state change (ENABLE/DISABLE ROW).
        
        Args:
            row: Table row index
            state: New checkbox state
        """
        # Enable/disable dropdowns based on checkbox
        is_checked = state == Qt.CheckState.Checked.value
        
        sheet_combo = self.table.cellWidget(row, 2)
        col_combo = self.table.cellWidget(row, 3)
        
        if sheet_combo:
            sheet_combo.setEnabled(is_checked)
        if col_combo:
            col_combo.setEnabled(is_checked)
    
    def _on_sheet_changed(self, row: int, sheet_name: str):
        """Handle sheet selection change (POPULATE COLUMNS).
        
        When user selects a sheet, populate the column dropdown for that row.
        
        Args:
            row: Table row index
            sheet_name: Selected sheet name
        """
        if sheet_name.startswith("-- "):
            # Placeholder selected, clear columns
            col_combo = self.table.cellWidget(row, 3)
            if col_combo:
                col_combo.clear()
                col_combo.addItem("-- Select Column --")
            return
        
        # Load columns from selected sheet
        columns = self._load_excel_columns(sheet_name)
        
        # Update column dropdown
        col_combo = self.table.cellWidget(row, 3)
        if col_combo:
            col_combo.clear()
            col_combo.addItem("-- Select Column --")
            col_combo.addItems(columns)
    
    def _load_configuration(self):
        """Load current recirculation config from diagram and populate table (INIT).
        
        Reads recirculation[] from diagram JSON and sets:
        - Checkbox state (enabled/disabled)
        - Excel sheet selection
        - Excel column selection
        
        Configures table to reflect saved recirculation mappings.
        """
        recirc_config = self.diagram_data.get('recirculation', [])
        
        # Create lookup by component_id
        config_by_id = {r['component_id']: r for r in recirc_config}
        
        # Populate table from stored config
        for row, component in enumerate(self.storage_components):
            component_id = component['id']
            config = config_by_id.get(component_id, {})
            
            # Set checkbox
            checkbox = self.table.cellWidget(row, 1)
            if checkbox:
                is_enabled = config.get('enabled', False)
                checkbox.setChecked(is_enabled)
                # Enable/disable dropdowns
                self.table.cellWidget(row, 2).setEnabled(is_enabled)
                self.table.cellWidget(row, 3).setEnabled(is_enabled)
            
            # Set sheet selector
            sheet_combo = self.table.cellWidget(row, 2)
            if sheet_combo:
                sheet_name = config.get('excel_sheet', '')
                if sheet_name and sheet_name in self.available_sheets:
                    sheet_combo.setCurrentText(sheet_name)
                    # Load columns for this sheet
                    columns = self._load_excel_columns(sheet_name)
                    col_combo = self.table.cellWidget(row, 3)
                    if col_combo:
                        col_combo.clear()
                        col_combo.addItem("-- Select Column --")
                        col_combo.addItems(columns)
            
            # Set column selector
            col_combo = self.table.cellWidget(row, 3)
            if col_combo:
                col_name = config.get('excel_column', '')
                if col_name:
                    index = col_combo.findText(col_name)
                    if index >= 0:
                        col_combo.setCurrentIndex(index)
    
    def _save_configuration(self):
        """Save recirculation configuration to diagram JSON (PERSISTENCE)."""
        try:
            recirc_list = []
            
            for row, component in enumerate(self.storage_components):
                # Get checkbox state
                checkbox = self.table.cellWidget(row, 1)
                enabled = checkbox.isChecked() if checkbox else False
                
                if not enabled:
                    continue
                
                # Get selected sheet
                sheet_combo = self.table.cellWidget(row, 2)
                sheet_name = sheet_combo.currentText() if sheet_combo else ""
                
                if sheet_name.startswith("-- "):
                    # No sheet selected
                    continue
                
                # Get selected column
                col_combo = self.table.cellWidget(row, 3)
                excel_column = col_combo.currentText() if col_combo else ""
                
                if excel_column.startswith("-- "):
                    # No column selected
                    continue
                
                # Add to list
                recirc_list.append({
                    'component_id': component['id'],
                    'component_name': component['label'],
                    'excel_sheet': sheet_name,
                    'excel_column': excel_column,
                    'enabled': True
                })
            
            # Update diagram data
            self.diagram_data['recirculation'] = recirc_list
            
            # Save to JSON
            with open(self.diagram_path, 'w') as f:
                json.dump(self.diagram_data, f, indent=2)
            
            logger.info(f"Recirculation config saved: {len(recirc_list)} components configured")
            
            # Show confirmation
            if recirc_list:
                msg = f"Recirculation configuration saved for {len(recirc_list)} component(s)"
                logger.info(msg)
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving recirculation config: {e}")
            # Still close dialog
            self.accept()
