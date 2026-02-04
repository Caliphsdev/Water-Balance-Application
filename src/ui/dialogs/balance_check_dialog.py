"""
Balance Check Dialog Controller

Wrapper around generated_ui_balance_check_dialog.py that provides:
- Water balance calculation
- Flow categorization (inflow/outflow/recirculation/ignore)
- Category persistence to JSON
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QDialog, QTableWidgetItem, QComboBox, QMessageBox
from PySide6.QtCore import Qt
from typing import Dict, List, Tuple
import json

from ui.dialogs.generated_ui_balance_check_dialog import Ui_BalanceCheckDialog


class BalanceCheckDialog(QDialog):
    """
    Water Balance Check Dialog (ANALYSIS).
    
    Purpose:
    - Calculate and display water balance for current diagram
    - Allow user to categorize flows as inflow/outflow/recirculation/ignore
    - Validate closure error < 5% (good data quality indicator)
    - Display summary metrics (total inflows, outflows, balance error)
    - Save categorizations to data/balance_check_flow_categories.json
    
    Balance Equation:
    balance_error_pct = (Inflows - Outflows - Recirculation) / Inflows × 100
    
    Good balance: < 5% error (indicates measurement accuracy)
    """
    
    def __init__(self, parent=None, area_code: str = "UG2N"):
        """
        Initialize dialog.
        
        Args:
            parent: Parent widget (FlowDiagramPage)
            area_code: Mining area code for context
        """
        super().__init__(parent)
        self.ui = Ui_BalanceCheckDialog()
        self.ui.setupUi(self)
        
        self.parent_page = parent
        self.area_code = area_code
        self.categories_file = "data/balance_check_flow_categories.json"
        self.flow_categories = {}  # {edge_idx: category}
        
        # Configure dialog size and responsiveness (LARGE & DYNAMIC)
        self._configure_dialog_size()
        
        # Setup
        self.ui.value_area.setText(area_code)
        self._load_categorizations()
        self._populate_flows_table()
        self._configure_table_columns()  # Configure columns AFTER population
        self._connect_buttons()
        self._calculate_balance()
        
        self.setModal(True)
    
    def _configure_dialog_size(self):
        """Configure dialog size to be large and responsive (RESPONSIVE UI).
        
        - Makes dialog 1200x800 (80% of typical screen)
        - Allows resizing to adapt to different screen sizes
        - Table stretches to fill available space
        """
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QScreen
        
        # Get primary screen dimensions
        if self.parent():
            screen = self.parent().screen()
        else:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        
        if screen:
            screen_geometry = screen.geometry()
            # Use 80% of screen width and 85% of screen height
            width = int(screen_geometry.width() * 0.80)
            height = int(screen_geometry.height() * 0.85)
            # But keep minimum size reasonable
            width = max(width, 1000)
            height = max(height, 700)
        else:
            width = 1200
            height = 800
        
        self.resize(width, height)
        
        # Allow resizing
        self.setMinimumSize(QSize(900, 600))
        self.setMaximumSize(QSize(2560, 1600))  # Support 4K screens
    
    def _configure_table_columns(self):
        """Configure table columns to display Excel names in full (DYNAMIC COLUMN SIZING).
        
        - Column 0 (Excel Column Name): Auto-fit to content + stretch
        - Column 1 (Destination): 200px minimum
        - Column 2 (Volume): 100px
        - Column 3 (Category): 120px (dropdown needs space)
        
        Uses ResizeToContents combined with stretch for responsiveness.
        """
        from PySide6.QtWidgets import QHeaderView
        
        header = self.ui.table_flows.horizontalHeader()
        header.setStretchLastSection(False)
        
        # Column 0: Excel Column Name - STRETCH and fit to content (most important)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # Column 1: Destination - Interactive (manual resize)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        self.ui.table_flows.setColumnWidth(1, 200)
        
        # Column 2: Volume - Interactive (manual resize)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        self.ui.table_flows.setColumnWidth(2, 100)
        
        # Column 3: Category - Stretch to fill remaining space
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.ui.table_flows.setColumnWidth(3, 120)
        
        # Set row height to be taller for better readability
        self.ui.table_flows.verticalHeader().setDefaultSectionSize(28)
        
        # After short delay, adjust columns again (ensures dialog is rendered)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._adjust_column_widths_final)
    
    def _adjust_column_widths_final(self):
        """Final column width adjustment after dialog is fully rendered (RESPONSIVE SIZING).
        
        Called via QTimer to ensure dialog has proper size before calculating proportions.
        """
        table_width = self.ui.table_flows.width()
        
        # Set column widths based on actual dialog width (4 columns)
        self.ui.table_flows.setColumnWidth(0, int(table_width * 0.40))  # Excel column name (widest)
        self.ui.table_flows.setColumnWidth(1, int(table_width * 0.22))  # Destination
        self.ui.table_flows.setColumnWidth(2, int(table_width * 0.13))  # Volume
        self.ui.table_flows.setColumnWidth(3, int(table_width * 0.25))  # Category
    
    def _load_categorizations(self):
        """Load saved flow categorizations from JSON file (PERSISTENCE).
        
        Reads data/balance_check_flow_categories.json and extracts
        the categorizations for current area_code. If file doesn't exist,
        initializes with empty dict (all flows uncategorized).
        
        Categories: Inflow, Outflow, Recirculation, Ignore
        """
        try:
            with open(self.categories_file, 'r') as f:
                categories_data = json.load(f)
                self.flow_categories = categories_data.get(self.area_code, {})
        except FileNotFoundError:
            self.flow_categories = {}
    
    def _populate_flows_table(self):
        """
        Populate table with flows from diagram, GROUPED BY SHEET.
        
        Includes:
        - Edges (standard flow lines from diagram_data['edges'])
        - Recirculation entries (diagram_data['recirculation'])
        
        Table columns: From | To | Volume (m³) | Category (dropdown)
        
        Flows are grouped with sheet header rows to organize long lists.
        
        Category options:
        - Inflow: Fresh water entering system
        - Outflow: Water leaving system
        - Recirculation: Internal recycling
        - Ignore: Excluded from balance calculation
        """
        if not self.parent_page or not self.parent_page.diagram_data:
            return
        
        edges = self.parent_page.diagram_data.get('edges', [])
        recirculation_entries = self.parent_page.diagram_data.get('recirculation', [])
        node_lookup = {
            node.get('id'): node for node in self.parent_page.diagram_data.get('nodes', [])
        }
        
        # Group edges and recirculation entries by sheet name
        sheet_groups = {}
        for row, edge in enumerate(edges):
            excel_mapping = edge.get('excel_mapping', {})
            sheet_name = excel_mapping.get('sheet', 'Unmapped')
            
            if sheet_name not in sheet_groups:
                sheet_groups[sheet_name] = []
            sheet_groups[sheet_name].append(("edge", row, edge))
        
        for recirc_entry in recirculation_entries:
            sheet_name = recirc_entry.get('excel_sheet', 'Unmapped')
            if sheet_name not in sheet_groups:
                sheet_groups[sheet_name] = []
            sheet_groups[sheet_name].append(("recirc", None, recirc_entry))
        
        # Calculate total rows: flows + group headers
        total_rows = sum(len(items) for items in sheet_groups.values()) + len(sheet_groups)
        self.ui.table_flows.setRowCount(total_rows)
        
        # Store flow_key to table row mapping for category persistence
        self.edge_row_map = {}  # {flow_key: table_row}
        
        table_row = 0
        # Iterate through sheets in sorted order
        for sheet_name in sorted(sheet_groups.keys()):
            # Add GROUP HEADER ROW
            header_item = QTableWidgetItem(f"📊 {sheet_name}")
            header_item.setFont(self.ui.table_flows.font())
            self.ui.table_flows.setItem(table_row, 0, header_item)
            
            # Create items for all columns in header row (so we can style them)
            from PySide6.QtGui import QColor, QBrush
            brush = QBrush(QColor(240, 240, 240))
            
            # Column 0 already has the header item
            header_item.setBackground(brush)
            header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable)
            
            # Create and style columns 1-3
            for col in range(1, 4):
                col_item = QTableWidgetItem("")
                col_item.setBackground(brush)
                col_item.setFlags(col_item.flags() & ~Qt.ItemIsSelectable)
                self.ui.table_flows.setItem(table_row, col, col_item)
            
            table_row += 1
            
            # Add flows for this sheet
            for entry_type, edge_idx, entry in sheet_groups[sheet_name]:
                if entry_type == "edge":
                    from_id = entry.get('from', '???')
                    to_id = entry.get('to', '???')
                    volume_str = entry.get('volume', '0')
                    
                    # Get Excel column name if available, otherwise use component ID (USER-FRIENDLY DISPLAY)
                    excel_mapping = entry.get('excel_mapping', {})
                    column_name = excel_mapping.get('column', from_id)
                    # Keep legacy edge key format for backward-compatible category storage
                    flow_key = str(edge_idx)
                    default_category = self.flow_categories.get(flow_key, "Ignore")
                else:
                    component_id = entry.get('component_id', '')
                    excel_column = entry.get('excel_column', '')
                    column_name = excel_column or entry.get('component_name', 'Recirculation')
                    flow_key = f"recirc::{component_id}"
                    default_category = self.flow_categories.get(flow_key, "Recirculation")
                    
                    # Recirculation entries are self-loops; derive To from column if possible
                    from_id = column_name
                    to_id = column_name
                    if "→" in column_name:
                        parts = [p.strip() for p in column_name.split("→", 1)]
                        from_id = parts[0]
                        to_id = parts[1] if len(parts) > 1 else parts[0]
                    
                    # Use node-level recirculation volume if available
                    node_data = node_lookup.get(component_id, {})
                    volume_str = node_data.get('recirculation_volume', 0)
                
                self.edge_row_map[flow_key] = table_row
                
                # From column (show Excel column name for clarity)
                self.ui.table_flows.setItem(table_row, 0, QTableWidgetItem(f"  {column_name}"))
                
                # To column (show destination component - helps understand flow direction)
                self.ui.table_flows.setItem(table_row, 1, QTableWidgetItem(to_id))
                
                # Volume column
                self.ui.table_flows.setItem(table_row, 2, QTableWidgetItem(str(volume_str)))
                
                # Category dropdown (column 3)
                category_combo = QComboBox()
                category_combo.addItems(["Inflow", "Outflow", "Recirculation", "Ignore"])
                
                idx = category_combo.findText(default_category)
                if idx >= 0:
                    category_combo.setCurrentIndex(idx)
                
                # Connect to recalculate on change
                category_combo.currentTextChanged.connect(self._calculate_balance)
                
                # Store flow metadata for later retrieval
                category_combo.flow_key = flow_key
                category_combo.flow_volume = volume_str
                
                self.ui.table_flows.setCellWidget(table_row, 3, category_combo)
                table_row += 1
    
    def _connect_buttons(self):
        """Connect button signals to slot methods (SIGNAL/SLOT WIRING).
        
        Connects save button to _on_save_categories() for persisting
        flow categorizations to JSON file.
        """
        self.ui.btn_save_categories.clicked.connect(self._on_save_categories)
    
    def _calculate_balance(self):
        """
        Calculate water balance from categorized flows.
        
        Balance Equation:
        net_flow = inflows - outflows - recirculation
        balance_error_pct = abs(net_flow) / inflows × 100
        
        Updates UI labels with results.
        
        Note: Iterates through table rows but skips header rows (which have no combo widget).
        """
        if not self.parent_page or not self.parent_page.diagram_data:
            return
        
        edges = self.parent_page.diagram_data.get('edges', [])
        inflows = 0.0
        outflows = 0.0
        recirculation = 0.0
        
        # Iterate through table rows
        for table_row in range(self.ui.table_flows.rowCount()):
            category_combo = self.ui.table_flows.cellWidget(table_row, 3)  # Category column
            if not category_combo or not isinstance(category_combo, QComboBox):
                # Skip header rows (they don't have combo boxes)
                continue
            
            # Get the stored volume for this row
            if not hasattr(category_combo, 'flow_volume'):
                continue
            category = category_combo.currentText()
            volume_str = category_combo.flow_volume
            
            try:
                volume = float(str(volume_str).replace(',', ''))
            except ValueError:
                volume = 0.0
            
            if category == "Inflow":
                inflows += volume
            elif category == "Outflow":
                outflows += volume
            elif category == "Recirculation":
                recirculation += volume
        
        # Calculate balance
        balance_numerator = inflows - outflows - recirculation
        balance_error_pct = (abs(balance_numerator) / inflows * 100) if inflows > 0 else 0
        
        # Update UI
        self.ui.value_inflows.setText(f"{inflows:,.1f} m³")
        self.ui.value_outflows.setText(f"{outflows:,.1f} m³")
        self.ui.value_recirculation.setText(f"{recirculation:,.1f} m³")
        self.ui.value_error_pct.setText(f"{balance_error_pct:.2f} %")
        self.ui.value_balance.setText(f"{balance_error_pct:.2f} %")
        
        # Color code error status
        if balance_error_pct < 5:
            self.ui.value_error_pct.setStyleSheet("color: #22AA22; font-weight: bold;")  # Green
        else:
            self.ui.value_error_pct.setStyleSheet("color: #E74C3C; font-weight: bold;")  # Red
    
    def _on_save_categories(self):
        """Save flow categorizations to JSON file.
        
        Iterates through table rows, skips header rows, saves edge_idx -> category mapping.
        """
        try:
            # Collect current categorizations
            self.flow_categories = {}
            for table_row in range(self.ui.table_flows.rowCount()):
                category_combo = self.ui.table_flows.cellWidget(table_row, 3)  # Category column
                if not category_combo or not isinstance(category_combo, QComboBox):
                    # Skip header rows
                    continue
                
                # Get the flow_key from the combo box
                if hasattr(category_combo, 'flow_key'):
                    flow_key = category_combo.flow_key
                    self.flow_categories[str(flow_key)] = category_combo.currentText()
            
            # Load existing file
            try:
                with open(self.categories_file, 'r') as f:
                    categories_data = json.load(f)
            except FileNotFoundError:
                categories_data = {}
            
            # Update with current area's categories
            categories_data[self.area_code] = self.flow_categories
            
            # Save
            with open(self.categories_file, 'w') as f:
                json.dump(categories_data, f, indent=2)
            
            QMessageBox.information(self, "Success", "Flow categories saved successfully")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save categories: {e}")
