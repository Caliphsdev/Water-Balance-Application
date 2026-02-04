"""
Excel Setup Dialog Controller (FLOW DIAGRAM EXCEL CONFIGURATION).

Wrapper around generated_ui_excel_setup_dialog.py that provides:
- Excel file selection and validation
- Flow-to-column mapping configuration
- Auto-mapping of flows to Excel columns
- Column management (add/rename/delete) via ColumnEditorDialog
- Persistence of mappings to data/excel_flow_links.json
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QTableWidgetItem,
    QMessageBox,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from typing import Dict, Optional
import json

from ui.dialogs.generated_ui_excel_setup_dialog import Ui_ExcelSetupDialog
from ui.dialogs.column_editor_dialog import ColumnEditorDialog
from services.excel_manager import get_excel_manager
from ui.components.excel_preview_widget import ExcelPreviewWidget


class ExcelSetupDialog(QDialog):
    """
    Excel Setup/Mapping Dialog (CONFIGURATION).
    
    Purpose:
    - Browse and select Excel file containing flow volume data
    - Validate Excel file structure (sheet names, columns)
    - Create/edit mappings from flows (From→To) to Excel columns
    - Auto-discover matching columns using intelligent naming
    - Persist mappings to data/excel_flow_links.json for reuse
    
    Data Sources:
    - Excel file path: timeseries_excel_path (from config)
    - Flow diagram: diagram_data['edges'] from parent
    - Mappings: data/excel_flow_links.json
    
    Expected Excel Structure:
    - Sheets named "Flows_*" for each mining area
    - Column A: Month/Date
    - Column B+: Flow volumes (e.g., "BH_to_Sump", "Sump_to_Plant")
    """
    
    def __init__(self, parent=None):
        """
        Initialize dialog.
        
        Args:
            parent: Parent widget (FlowDiagramPage)
        """
        super().__init__(parent)
        self.ui = Ui_ExcelSetupDialog()
        self.ui.setupUi(self)
        
        # Clear any lingering placeholder texts that might have been set
        self.ui.input_file_path.clear()
        self.ui.input_file_path.setPlaceholderText("")
        self.ui.value_status.setText("")
        
        self.parent_page = parent
        self.excel_path = None
        self.excel_file = None  # openpyxl Workbook object
        self.mappings_file = "data/excel_flow_links.json"
        self.flow_mappings = {}  # {flow_key: {sheet, column}}
        self.excel_manager = get_excel_manager()
        
        # Setup
        self._load_excel_mappings()
        self._connect_buttons()
        self._setup_preview_panel()
        
        # Load existing Excel path from config if it exists
        existing_path = self.excel_manager.get_flow_diagram_path()
        if existing_path.exists():
            self.excel_path = str(existing_path)
            self.ui.input_file_path.setText(self.excel_path)
            flow_sheets = self.excel_manager.list_flow_sheets()
            if flow_sheets:
                self.ui.value_status.setText(f"Loaded: {len(flow_sheets)} flow sheets")
                self.ui.value_status.setStyleSheet("color: #22AA22;")
                # Populate table now that Excel is already loaded
                self._populate_mapping_table()
                # Preview the first sheet
                if hasattr(self, "_preview_widget"):
                    self._preview_widget.set_sheet(flow_sheets[0])
            else:
                self.ui.value_status.setText("No Excel file configured")
        else:
            self.ui.value_status.setText("No Excel file configured")
        
        # Always show grid and alternating colors for better visibility
        self.ui.table_mapping.setShowGrid(True)
        self.ui.table_mapping.setAlternatingRowColors(True)
        
        self.setModal(True)
        
        # Dynamic sizing based on screen dimensions (80% of screen)
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        dialog_width = int(screen.width() * 0.8)
        dialog_height = int(screen.height() * 0.8)
        self.resize(dialog_width, dialog_height)
        
        # Center on screen
        self.move(
            (screen.width() - dialog_width) // 2,
            (screen.height() - dialog_height) // 2
        )
    
    def _connect_buttons(self):
        """Connect button signals (EVENT CONNECTIONS).
        
        Connects UI buttons to their handler methods:
        - Browse: Open file browser
        - Auto-map: Auto-map flows to columns
        - Clear mapping: Reset all mappings
        - Manage columns: Open column editor
        - Selection changed: Update preview
        """
        self.ui.btn_browse.clicked.connect(self._on_browse_excel)
        self.ui.btn_auto_map_all.clicked.connect(self._on_auto_map_all)
        self.ui.btn_clear_mapping.clicked.connect(self._on_clear_mapping)
        self.ui.table_mapping.itemSelectionChanged.connect(self._on_mapping_selection_changed)
        
        # Add column manager button if it exists in UI
        if hasattr(self.ui, "btn_manage_columns"):
            self.ui.btn_manage_columns.clicked.connect(self._on_manage_columns)

    def _setup_preview_panel(self):
        """Add Excel preview panel next to the mapping table.

        The preview shows the selected sheet contents so users can verify
        mappings without leaving the app.
        """
        if not hasattr(self.ui, "verticalLayout_table"):
            return

        # Remove the table widget from its current layout position.
        table_item = self.ui.verticalLayout_table.takeAt(0)
        if table_item is None:
            return

        # Create a horizontal layout to hold table + preview.
        self._preview_layout = QHBoxLayout()
        self._preview_widget = ExcelPreviewWidget(self.ui.groupBox_mapping)

        # Re-add the existing table widget and the preview widget.
        self._preview_layout.addWidget(self.ui.table_mapping, stretch=2)
        self._preview_layout.addWidget(self._preview_widget, stretch=1)

        # Insert the horizontal layout at the top of the mapping group.
        self.ui.verticalLayout_table.insertLayout(0, self._preview_layout)
    
    def _on_browse_excel(self):
        """
        Open file browser to select Excel file.
        
        Validates Excel structure after selection:
        - File must be .xlsx format
        - Must contain "Flows_*" sheets
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.excel_path = file_path
        self.ui.input_file_path.setText(file_path)

        # Persist path in ExcelManager and config (CRITICAL - must save to config!)
        self.excel_manager.set_flow_diagram_path(file_path)
        
        # Clear cache to force reload from new file
        self.excel_manager.clear_flow_cache()
        
        # Validate flow sheets exist
        flow_sheets = self.excel_manager.list_flow_sheets()
        if flow_sheets:
            self.ui.value_status.setText(f"Loaded: {len(flow_sheets)} flow sheets")
            self.ui.value_status.setStyleSheet("color: #22AA22;")
            # Show the mapping table now that Excel is loaded
            self._populate_mapping_table()
            self.ui.groupBox_mapping.show()
            # Preview the first sheet for quick feedback
            if hasattr(self, "_preview_widget"):
                self._preview_widget.set_sheet(flow_sheets[0])
        else:
            self.ui.value_status.setText("Error: No 'Flows_*' sheets found")
            self.ui.value_status.setStyleSheet("color: #E74C3C;")

    def _on_mapping_selection_changed(self):
        """Update preview when the mapping table selection changes."""
        if not hasattr(self, "_preview_widget"):
            return

        selected_items = self.ui.table_mapping.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        sheet_item = self.ui.table_mapping.item(row, 1)
        column_item = self.ui.table_mapping.item(row, 2)

        sheet_name = sheet_item.text().strip() if sheet_item else ""
        column_name = column_item.text().strip() if column_item else ""

        if not sheet_name:
            # Fallback to area sheet if mapping is empty.
            sheet_name = self.excel_manager.resolve_flow_sheet_name(
                getattr(self.parent_page, 'area_code', '')
            )

        if sheet_name:
            self._preview_widget.set_sheet(sheet_name)
            self._preview_widget.set_highlight_column(column_name or None)
    
    def _load_excel_mappings(self):
        """Load existing flow-to-column mappings from JSON file."""
        try:
            with open(self.mappings_file, 'r') as f:
                self.flow_mappings = json.load(f)
        except FileNotFoundError:
            self.flow_mappings = {}
    
    def _populate_mapping_table(self):
        """
        Populate table with flows from diagram and their Excel mappings.
        
        Table columns: From→To | Sheet | Column | Status
        
        Status: ✓ (mapped), ✗ (unmapped)
        
        Reads mappings from TWO sources (in priority order):
        1. edge.excel_mapping (saved by Edit Flow dialog)
        2. data/excel_flow_links.json (saved by Excel Setup dialog)
        """
        if not self.parent_page or not self.parent_page.diagram_data:
            return
        
        edges = self.parent_page.diagram_data.get('edges', [])
        self.ui.table_mapping.setRowCount(len(edges))
        
        for row, edge in enumerate(edges):
            from_id = edge.get('from_id') or edge.get('from', '???')
            to_id = edge.get('to_id') or edge.get('to', '???')
            flow_key = f"{self.parent_page.area_code}::{from_id}->{to_id}"
            
            # From→To column
            flow_label = f"{from_id} -> {to_id}"
            self.ui.table_mapping.setItem(row, 0, QTableWidgetItem(flow_label))
            
            # Get mapping from EDGE FIRST (Edit Flow dialog), then fallback to excel_flow_links.json
            edge_mapping = edge.get('excel_mapping', {})
            if edge_mapping and edge_mapping.get('sheet') and edge_mapping.get('column'):
                # Use mapping from edge data (saved by Edit Flow dialog)
                mapping = edge_mapping
            else:
                # Fallback to excel_flow_links.json (saved by Excel Setup dialog)
                mapping = self.flow_mappings.get(flow_key, {})
            
            sheet = mapping.get('sheet', '')
            column = mapping.get('column', '')
            
            # Sheet column - show empty or mapped value
            sheet_display = sheet if sheet else ""
            sheet_item = QTableWidgetItem(sheet_display)
            if not sheet:
                sheet_item.setForeground(Qt.gray)
            self.ui.table_mapping.setItem(row, 1, sheet_item)
            
            # Column name - show empty or mapped value
            column_display = column if column else ""
            column_item = QTableWidgetItem(column_display)
            if not column:
                column_item.setForeground(Qt.gray)
            self.ui.table_mapping.setItem(row, 2, column_item)
            
            # Status column
            status = "✓" if sheet and column else "✗"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.green if sheet and column else Qt.red)
            self.ui.table_mapping.setItem(row, 3, status_item)
    
    def _on_auto_map_all(self):
        """
        Automatically map all flows to Excel columns using intelligent matching.
        
        Algorithm:
        1. For each flow (From→To):
           - Extract component names (e.g., "BH" from "bh_ndgwa")
           - Search Excel columns for containing these names
           - Suggest closest match
        
        Uses ExcelManager auto-mapping heuristics to find best matches.
        """
        flow_sheets = self.excel_manager.list_flow_sheets()
        if not flow_sheets:
            QMessageBox.warning(
                self,
                "Excel File Not Configured",
                "Please click 'Browse...' to select the Flow Diagram Excel file first."
            )
            return

        if not self.parent_page or not self.parent_page.diagram_data:
            return

        default_sheet = self.excel_manager.resolve_flow_sheet_name(
            getattr(self.parent_page, 'area_code', '')
        )

        edges = self.parent_page.diagram_data.get('edges', [])
        for row, edge in enumerate(edges):
            from_id = edge.get('from_id') or edge.get('from', '')
            to_id = edge.get('to_id') or edge.get('to', '')

            mapping = self.excel_manager.auto_map_flow_column(
                from_id=from_id,
                to_id=to_id,
                area_code_or_sheet=default_sheet,
            )

            if mapping:
                sheet = mapping.get('sheet', '')
                column = mapping.get('column', '')

                self.ui.table_mapping.setItem(row, 1, QTableWidgetItem(sheet))
                self.ui.table_mapping.setItem(row, 2, QTableWidgetItem(column))

                status_item = QTableWidgetItem("✓")
                status_item.setForeground(Qt.green)
                self.ui.table_mapping.setItem(row, 3, status_item)

                flow_key = f"{self.parent_page.area_code}::{from_id}->{to_id}"
                self.flow_mappings[flow_key] = {'sheet': sheet, 'column': column}
            else:
                status_item = QTableWidgetItem("✗")
                status_item.setForeground(Qt.red)
                self.ui.table_mapping.setItem(row, 3, status_item)
    
    def _on_clear_mapping(self):
        """Clear all mappings."""
        reply = QMessageBox.question(
            self,
            "Clear All Mappings",
            "Clear all flow-to-column mappings?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.flow_mappings = {}
            self._populate_mapping_table()
    
    def accept(self):
        """Override accept to save mappings before closing.
        
        Saves to BOTH locations:
        1. edge.excel_mapping in diagram JSON (for Edit Flow dialog)
        2. data/excel_flow_links.json (for Excel Setup dialog)
        """
        try:
            # Collect current mappings from table
            if self.parent_page and self.parent_page.diagram_data:
                edges = self.parent_page.diagram_data.get('edges', [])
                for row, edge in enumerate(edges):
                    from_id = edge.get('from_id') or edge.get('from', '???')
                    to_id = edge.get('to_id') or edge.get('to', '???')
                    flow_key = f"{self.parent_page.area_code}::{from_id}->{to_id}"
                    
                    sheet = self.ui.table_mapping.item(row, 1).text() if self.ui.table_mapping.item(row, 1) else ""
                    column = self.ui.table_mapping.item(row, 2).text() if self.ui.table_mapping.item(row, 2) else ""
                    
                    if sheet and column:
                        # Save to excel_flow_links.json
                        self.flow_mappings[flow_key] = {'sheet': sheet, 'column': column}
                        
                        # ALSO save to edge data in diagram JSON (for Edit Flow dialog)
                        edge['excel_mapping'] = {'sheet': sheet, 'column': column}
            
            # Save to file
            with open(self.mappings_file, 'w') as f:
                json.dump(self.flow_mappings, f, indent=2)
            
            # Save diagram JSON with updated edge mappings
            if self.parent_page and self.parent_page.diagram_path:
                with open(self.parent_page.diagram_path, 'w') as f:
                    json.dump(self.parent_page.diagram_data, f, indent=2)
            
            super().accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mappings: {e}")    
    def _on_manage_columns(self):
        """Open Column Editor dialog for managing Excel columns (USER ACTION).
        
        Purpose:
        - Allow user to add/rename/delete columns in Flow Diagram Excel
        - Dialog handles all Excel operations programmatically
        - Updates mappings if columns are renamed
        """
        if not self.excel_manager.flow_diagram_exists():
            QMessageBox.warning(
                self,
                "Excel File Not Configured",
                "Please browse to select the Flow Diagram Excel file first.",
            )
            return
        
        # Determine area code from parent if available
        area_code = "UG2N"
        if self.parent_page and hasattr(self.parent_page, "area_code"):
            area_code = self.parent_page.area_code
        
        # Open column editor dialog
        dialog = ColumnEditorDialog(self, area_code=area_code)
        if dialog.exec() == QDialog.Accepted:
            # Reload mapping table since columns may have changed
            self._populate_mapping_table()
            QMessageBox.information(
                self, "Columns Updated", "Column changes applied. Mappings reloaded."
            )