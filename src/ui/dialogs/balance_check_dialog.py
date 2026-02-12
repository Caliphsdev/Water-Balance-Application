"""
Balance Check Dialog Controller

Wrapper around generated_ui_balance_check_dialog.py that provides:
- Water balance calculation
- Flow categorization (inflow/outflow/recirculation/ignore)
- Category persistence to JSON
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QDialog,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from typing import Dict, List, Tuple
import json

from ui.dialogs.generated_ui_balance_check_dialog import Ui_BalanceCheckDialog
from core.config_manager import get_resource_path


class NoWheelComboBox(QComboBox):
    """ComboBox that ignores mouse wheel unless it has focus."""

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


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
        self.categories_file = self._get_categories_file()
        self.flow_categories = {}  # {edge_idx: category}
        
        # Configure dialog size and responsiveness (LARGE & DYNAMIC)
        self._configure_dialog_size()
        self._apply_dialog_polish()
        self._modernize_header()
        self._modernize_summary_section()
        
        # Setup
        self.ui.value_area.setText(area_code)
        self._load_categorizations()
        self._populate_flows_table()
        self._configure_table_columns()  # Configure columns AFTER population
        self._connect_buttons()
        self._calculate_balance()
        
        self.setModal(True)

    def _apply_dialog_polish(self) -> None:
        """Apply consistent styling and control sizing for balance popup."""
        self.ui.btn_save_categories.setMinimumHeight(34)
        self.ui.btn_close.setMinimumHeight(34)
        self.ui.btn_save_categories.setText("Save Categories")
        self.ui.table_flows.setAlternatingRowColors(True)
        self.ui.table_flows.setSelectionBehavior(self.ui.table_flows.SelectionBehavior.SelectRows)
        self.ui.table_flows.setSelectionMode(self.ui.table_flows.SelectionMode.SingleSelection)
        self.ui.table_flows.verticalHeader().setVisible(False)

        self.setStyleSheet(
            """
            QDialog {
                background: #f5f8fc;
            }
            QGroupBox {
                border: 1px solid #c9d8ea;
                border-radius: 10px;
                margin-top: 8px;
                padding: 10px;
                color: #173b68;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #173b68;
                font-size: 14px;
                font-weight: 800;
            }
            QLabel#bc_closure_title {
                color: #163a66;
                font-weight: 700;
            }
            QLabel#bc_closure_value {
                font-size: 31px;
                font-weight: 800;
            }
            QTableWidget {
                background: #ffffff;
                border: 1px solid #c8d8ea;
                border-radius: 8px;
                alternate-background-color: #f8fbff;
                gridline-color: #d9e3f0;
            }
            QHeaderView::section {
                background: #e6eef8;
                color: #173b68;
                border: 1px solid #c8d8ea;
                padding: 6px;
                font-weight: 700;
            }
            QComboBox {
                background: #ffffff;
                border: 1px solid #b8c9dd;
                border-radius: 6px;
                padding: 4px 8px;
                color: #0f2747;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QPushButton {
                min-width: 100px;
                border: 1px solid #b7c7db;
                border-radius: 8px;
                padding: 6px 12px;
                background: #f8fbff;
                color: #173b68;
            }
            QPushButton:hover {
                background: #eef4fb;
            }
            QPushButton#btn_save_categories {
                background: #1f4f8f;
                border: 1px solid #1f4f8f;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton#btn_save_categories:hover {
                background: #1a457d;
            }
            QFrame#bc_summary_card {
                background: #ffffff;
                border: 1px solid #cad9ea;
                border-radius: 10px;
            }
            QLabel#bc_summary_title {
                color: #35557d;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#bc_summary_value {
                color: #0f2747;
                font-size: 22px;
                font-weight: 800;
            }
            QLabel#bc_summary_note {
                color: #486286;
                font-size: 12px;
            }
            """
        )

    def _modernize_header(self) -> None:
        """Polish header row and remove redundant area label/value."""
        for widget in (self.ui.label_area, self.ui.value_area):
            self.ui.horizontalLayout_header.removeWidget(widget)
            widget.hide()
            widget.setParent(None)

        self.ui.label_balance_title.setText("Balance Closure:")
        self.ui.label_balance_title.setObjectName("bc_closure_title")
        self.ui.value_balance.setObjectName("bc_closure_value")

    def _modernize_summary_section(self) -> None:
        """Replace form-style summary with compact KPI cards."""
        group = self.ui.groupBox_summary
        group.setObjectName("bc_summary_group")
        group.setTitle("Balance Summary")
        group.setMinimumHeight(168)

        # Keep references to value labels (used by _calculate_balance updates).
        value_labels = {
            "inflows": self.ui.value_inflows,
            "outflows": self.ui.value_outflows,
            "recirculation": self.ui.value_recirculation,
            "error": self.ui.value_error_pct,
        }

        # Clear generated form layout safely.
        old_layout = group.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    # Drop old row-title labels; values are reused as card values.
                    if w not in value_labels.values():
                        w.deleteLater()
            # Detach old layout from group before assigning a new one.
            layout_holder = QWidget()
            layout_holder.setLayout(old_layout)
            layout_holder.deleteLater()

        root = QVBoxLayout()
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        group.setLayout(root)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self._summary_cards = {}

        def _card(card_key: str, title: str, value_widget: QLabel, tone: str) -> QFrame:
            card = QFrame(group)
            card.setObjectName("bc_summary_card")
            card.setProperty("tone", tone)
            card.setMinimumHeight(72)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(10, 8, 10, 8)
            layout.setSpacing(2)

            title_lbl = QLabel(title, card)
            title_lbl.setObjectName("bc_summary_title")
            value_widget.setParent(card)
            value_widget.setObjectName("bc_summary_value")
            value_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            layout.addWidget(title_lbl)
            layout.addWidget(value_widget)
            self._summary_cards[card_key] = card
            return card

        cards_row.addWidget(_card("inflows", "Inflows", self.ui.value_inflows, "inflow"))
        cards_row.addWidget(_card("outflows", "Outflows", self.ui.value_outflows, "outflow"))
        cards_row.addWidget(_card("recirculation", "Recirculation", self.ui.value_recirculation, "recirc"))
        cards_row.addWidget(_card("closure_error", "Closure Error", self.ui.value_error_pct, "error_bad"))

        root.addLayout(cards_row)

        note = QLabel("Target closure error: < 5%. Higher values indicate categorization/data issues.", group)
        note.setObjectName("bc_summary_note")
        note.setWordWrap(True)
        root.addWidget(note)

    def _set_error_card_tone(self, tone: str) -> None:
        """Update closure error summary card border tone dynamically."""
        if not hasattr(self, "_summary_cards"):
            return
        card = self._summary_cards.get("closure_error")
        if card is None:
            return
        if card.property("tone") == tone:
            return
        card.setProperty("tone", tone)
        card.style().unpolish(card)
        card.style().polish(card)
        card.update()

    def _get_categories_file(self) -> Path:
        """Resolve categories file path with user-dir preference."""
        user_dir = os.environ.get('WATERBALANCE_USER_DIR')
        if user_dir:
            return Path(user_dir) / "data" / "balance_check_flow_categories.json"
        return get_resource_path("data/balance_check_flow_categories.json")
    
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
        
        use_live_volumes = bool(getattr(self.parent_page, "_excel_data_loaded_for_session", False))

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
            header_item = QTableWidgetItem(f"Sheet: {sheet_name}")
            header_font = QFont(self.ui.table_flows.font())
            header_font.setBold(True)
            header_font.setPointSize(max(10, header_font.pointSize()))
            header_item.setFont(header_font)
            self.ui.table_flows.setItem(table_row, 0, header_item)
            
            # Create items for all columns in header row (so we can style them)
            from PySide6.QtGui import QColor, QBrush
            brush = QBrush(QColor(240, 240, 240))
            text_brush = QBrush(QColor(25, 55, 96))
            
            # Column 0 already has the header item
            header_item.setBackground(brush)
            header_item.setForeground(text_brush)
            header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable)
            
            # Create and style columns 1-3
            for col in range(1, 4):
                col_item = QTableWidgetItem("")
                col_item.setBackground(brush)
                col_item.setForeground(text_brush)
                col_item.setFlags(col_item.flags() & ~Qt.ItemIsSelectable)
                self.ui.table_flows.setItem(table_row, col, col_item)
            
            table_row += 1
            
            # Add flows for this sheet
            for entry_type, edge_idx, entry in sheet_groups[sheet_name]:
                if entry_type == "edge":
                    from_id = entry.get('from', '???')
                    to_id = entry.get('to', '???')
                    volume_str = entry.get('volume', '0') if use_live_volumes else 0
                    
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
                    volume_str = node_data.get('recirculation_volume', 0) if use_live_volumes else 0
                
                self.edge_row_map[flow_key] = table_row
                
                # From column (show Excel column name for clarity)
                self.ui.table_flows.setItem(table_row, 0, QTableWidgetItem(f"  {column_name}"))
                
                # To column (show destination component - helps understand flow direction)
                self.ui.table_flows.setItem(table_row, 1, QTableWidgetItem(to_id))
                
                # Volume column
                self.ui.table_flows.setItem(table_row, 2, QTableWidgetItem(str(volume_str)))
                
                # Category dropdown (column 3)
                category_combo = NoWheelComboBox()
                category_combo.addItems(["Inflow", "Outflow", "Recirculation", "Ignore"])
                category_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                category_combo.setMinimumHeight(28)
                
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
        closure_text = f"{balance_error_pct:.2f}%"
        self.ui.value_error_pct.setText(closure_text)
        self.ui.value_balance.setText(closure_text)

        # Keep top and bottom closure status color consistent.
        if balance_error_pct < 5:
            color = "#16a34a"  # good
            error_tone = "error_good"
        elif balance_error_pct < 10:
            color = "#d97706"  # caution
            error_tone = "error_warn"
        else:
            color = "#dc2626"  # bad
            error_tone = "error_bad"

        value_style = f"color: {color}; font-weight: 800;"
        self.ui.value_error_pct.setStyleSheet(value_style)
        self.ui.value_balance.setStyleSheet(value_style)
        self._set_error_card_tone(error_tone)
    
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
            Path(self.categories_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.categories_file, 'w') as f:
                json.dump(categories_data, f, indent=2)
            
            QMessageBox.information(self, "Success", "Flow categories saved successfully")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save categories: {e}")
