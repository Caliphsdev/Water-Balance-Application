"""
Edit Flow Dialog Controller

Wrapper around generated_ui_edit_flow_dialog.py that provides:
- Color picker functionality
- Excel sheet/column population
- Auto-mapping of flows to Excel columns
- Data retrieval for saving to JSON
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QDialog,
    QColorDialog,
    QMessageBox,
    QPushButton,
    QLabel,
    QFormLayout,
    QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtGui import QColor, QIcon
from PySide6.QtCore import Qt, QSize
from typing import Dict, Optional

from ui.dialogs.generated_ui_edit_flow_dialog import Ui_EditFlowDialog
from ui.dialogs.add_edit_node_dialog import AddEditNodeDialog
from ui.components.flow_graphics_items import FlowNodeItem
from services.excel_manager import get_excel_manager
from ui.components.excel_preview_widget import ExcelPreviewWidget


class EditFlowDialog(QDialog):
    """
    Edit Flow Line Dialog (FORM WRAPPER).
    
    Purpose:
    - Display source and destination components (read-only)
    - Allow user to select flow type (clean/dirty/evaporation/recirculation)
    - Choose flow line color
    - Map flow to Excel sheet/column for data loading
    - Intelligent auto-mapping of column names
    
    Supports both editing existing edges and creating new edges.
    """
    
    def __init__(self, parent=None, edge_idx: Optional[int] = None, edge_data: Optional[Dict] = None,
                 from_node_data: Optional[Dict] = None, to_node_data: Optional[Dict] = None,
                 is_new_edge: bool = False):
        """
        Initialize dialog.
        
        Args:
            parent: Parent widget (FlowDiagramPage)
            edge_idx: Edge index in diagram_data['edges'] (None for new edges)
            edge_data: Edge data dict {from_id, to_id, flow_type, color, volume, waypoints}
            from_node_data: Source node data dict
            to_node_data: Destination node data dict
            is_new_edge: Whether this is a new edge being created
        """
        super().__init__(parent)
        self.ui = Ui_EditFlowDialog()
        self.ui.setupUi(self)
        
        self.parent_page = parent
        self.edge_idx = edge_idx
        self.edge_data = edge_data or {}
        self.from_node_data = from_node_data
        self.to_node_data = to_node_data
        self.is_new_edge = is_new_edge
        self.selected_color = QColor(self.edge_data.get('color', "#3498DB"))
        self.excel_manager = get_excel_manager()
        self._flowline_only_mode = not self.is_new_edge
        self._mapping_warning_label: Optional[QLabel] = None

        # Setup responsive dialog size (80% of screen, minimum 1000x800)
        self._setup_responsive_size()
        self._apply_dialog_polish()

        # Setup
        self._populate_fields()
        self._populate_excel_options()
        self._setup_excel_create_button()
        self._setup_excel_preview()
        self._setup_endpoint_edit_buttons()
        self._apply_flowline_only_mode()
        self._connect_buttons()
        self._update_color_preview()
        
        self.setModal(True)

    def _apply_dialog_polish(self):
        """Apply a consistent visual style with Add/Edit Component dialogs."""
        self.setWindowTitle("Add Flow Line" if self.is_new_edge else "Edit Flow Line")
        self.ui.btn_ok.setText("Save")

        self.ui.formLayout.setHorizontalSpacing(14)
        self.ui.formLayout.setVerticalSpacing(10)
        self.ui.formLayout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        for widget in (self.ui.combo_flow_type, self.ui.combo_sheet, self.ui.combo_column):
            widget.setMinimumHeight(32)
        self.ui.btn_color_picker.setMinimumHeight(32)
        self.ui.btn_color_picker.setMinimumWidth(110)
        self.ui.label_color_preview.setFixedSize(64, 32)
        self.ui.value_from.setMinimumHeight(32)
        self.ui.value_to.setMinimumHeight(32)
        self.ui.btn_ok.setMinimumHeight(34)
        self.ui.btn_cancel.setMinimumHeight(34)
        self.ui.btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        self.ui.btn_cancel.setIconSize(QSize(14, 14))
        self.ui.btn_auto_map.setMinimumHeight(32)

        # Reduce unused whitespace below the form.
        self.ui.verticalSpacer.changeSize(20, 8, QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Improve label clarity.
        self.ui.label_excel.setText("Excel Mapping:")
        self.ui.groupBox_excel.setTitle("Data Source Mapping")

        self.setStyleSheet(
            """
            QDialog {
                background: #f5f8fc;
            }
            QLabel#value_from, QLabel#value_to {
                background: #ffffff;
                border: 1px solid #b8c9dd;
                border-radius: 6px;
                padding: 6px 8px;
                color: #0f2747;
            }
            QLineEdit, QComboBox, QPlainTextEdit, QSpinBox {
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
            QGroupBox {
                border: 1px solid #c9d8ea;
                border-radius: 8px;
                margin-top: 8px;
                padding: 8px;
                color: #173b68;
                font-weight: 600;
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
            QPushButton#btn_ok {
                background: #1f4f8f;
                border: 1px solid #1f4f8f;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton#btn_ok:hover {
                background: #1a457d;
            }
            """
        )
    
    def _setup_responsive_size(self):
        """Set dialog to responsive size (80% of screen, minimum 1000x800) (RESPONSIVE SIZING).
        
        Makes the dialog larger to show Excel preview better.
        Centers on screen.
        """
        from PySide6.QtGui import QGuiApplication
        
        screen = QGuiApplication.primaryScreen().geometry()
        dialog_width = max(1000, int(screen.width() * 0.85))
        dialog_height = max(800, int(screen.height() * 0.85))
        
        self.resize(dialog_width, dialog_height)
        
        # Center on screen
        x = (screen.width() - dialog_width) // 2
        y = (screen.height() - dialog_height) // 2
        self.move(x, y)
    
    def _populate_fields(self):
        """
        Populate dialog fields from edge data.
        
        Handles both existing edges (from diagram_data) and new edges (from parameters).
        """
        if self.is_new_edge and self.edge_data:
            # New edge - use provided edge_data
            from_node_id = self.edge_data.get('from_id', '???')
            to_node_id = self.edge_data.get('to_id', '???')
            flow_type = self.edge_data.get('flow_type', 'transfer').lower()
            color_hex = self.edge_data.get('color', '#3498DB')
        else:
            # Existing edge - read from diagram_data
            if self.edge_idx is None or not self.parent_page:
                return
            
            edge_data = self.parent_page.diagram_data['edges'][self.edge_idx]
            from_node_id = edge_data.get('from_id', '???')
            to_node_id = edge_data.get('to_id', '???')
            flow_type = edge_data.get('flow_type', 'transfer').lower()
            color_hex = edge_data.get('color', '#3498DB')
        
        # Prefer human-readable labels from node data when available.
        if self.from_node_data and self.from_node_data.get('label'):
            self.ui.value_from.setText(self.from_node_data.get('label'))
        else:
            self.ui.value_from.setText(from_node_id)

        if self.to_node_data and self.to_node_data.get('label'):
            self.ui.value_to.setText(self.to_node_data.get('label'))
        else:
            self.ui.value_to.setText(to_node_id)
        
        # Set flow type
        flow_type_map = {
            'transfer': 0,
            'clean': 0,
            'dirty': 1,
            'evaporation': 2,
            'recirculation': 3
        }
        self.ui.combo_flow_type.setCurrentIndex(flow_type_map.get(flow_type, 0))
        
        # Set color
        self.selected_color = QColor(color_hex)
        
        # NOTE: Volume widget does not exist in UI - it would be loaded from Excel mapping
        # so no need to set volume here
        
        # Set Excel mapping (if controls exist)
        if hasattr(self.ui, 'combo_sheet'):
            excel_mapping = self.edge_data.get('excel_mapping', {})
            sheet = excel_mapping.get('sheet', '')
            column = excel_mapping.get('column', '')
            
            idx = self.ui.combo_sheet.findText(sheet)
            if idx >= 0:
                self.ui.combo_sheet.setCurrentIndex(idx)
            else:
                if sheet:
                    self.ui.combo_sheet.setEditText(sheet)
        
        if hasattr(self.ui, 'combo_column'):
            excel_mapping = self.edge_data.get('excel_mapping', {})
            column = excel_mapping.get('column', '')
            
            idx = self.ui.combo_column.findText(column)
            if idx >= 0:
                self.ui.combo_column.setCurrentIndex(idx)
            else:
                if column:
                    self.ui.combo_column.setEditText(column)
    
    def _populate_excel_options(self):
        """
        Populate Excel sheet and column dropdowns.
        
        Uses ExcelManager to read Flow Diagram Excel sheets and columns.
        """
        sheets = self.excel_manager.list_flow_sheets()
        self.ui.combo_sheet.clear()
        if sheets:
            self.ui.combo_sheet.addItems(sheets)

        # Prefer explicit mapping, else infer from parent page area code
        excel_mapping = self.edge_data.get('excel_mapping', {})
        mapped_sheet = excel_mapping.get('sheet', '').strip()
        area_code = getattr(self.parent_page, 'area_code', '') if self.parent_page else ''
        default_sheet = self.excel_manager.resolve_flow_sheet_name(area_code) if area_code else ''

        if mapped_sheet:
            if self.ui.combo_sheet.findText(mapped_sheet) < 0:
                self.ui.combo_sheet.addItem(mapped_sheet)
            self.ui.combo_sheet.setCurrentText(mapped_sheet)
        elif default_sheet and self.ui.combo_sheet.findText(default_sheet) >= 0:
            self.ui.combo_sheet.setCurrentText(default_sheet)

        # Ensure columns are loaded for the initial sheet selection
        self._on_sheet_changed(self.ui.combo_sheet.currentText())

        # Set mapped column if provided
        mapped_column = excel_mapping.get('column', '').strip()
        if mapped_column:
            if self.ui.combo_column.findText(mapped_column) < 0:
                self.ui.combo_column.addItem(mapped_column)
            self.ui.combo_column.setCurrentText(mapped_column)
    
    def _connect_buttons(self):
        """Connect button signals to slot methods (SIGNAL/SLOT WIRING).
        
        Connects:
        - Color picker button → _on_pick_color()
        - Auto-map button → _on_auto_map()
        - Sheet dropdown → _on_sheet_changed()
        - Column dropdown → _on_column_changed()
        """
        self.ui.btn_color_picker.clicked.connect(self._on_pick_color)
        if self.is_new_edge:
            self.ui.btn_auto_map.clicked.connect(self._on_auto_map)
        self.ui.combo_sheet.currentTextChanged.connect(self._on_sheet_changed)
        self.ui.combo_column.currentTextChanged.connect(self._on_column_changed)

    def _setup_excel_create_button(self):
        """Add an Auto-Create Column button to the Excel mapping group.

        This avoids editing the generated UI file while providing a clear
        workflow for creating new columns in the Flow Diagram Excel file.
        """
        if not hasattr(self.ui, 'formLayout_excel') or not self.is_new_edge:
            return

        self.btn_auto_create_column = QPushButton("Auto-Create Column")
        self.btn_auto_create_column.setObjectName("btn_auto_create_column")
        self.btn_auto_create_column.setMinimumHeight(32)
        self.btn_auto_create_column.setToolTip(
            "Create a new column in the Flow Diagram Excel sheet for this flowline"
        )

        # Place below the auto-map button in the same group box.
        self.ui.formLayout_excel.setWidget(
            3, QFormLayout.ItemRole.SpanningRole, self.btn_auto_create_column
        )
        self.btn_auto_create_column.clicked.connect(self._on_auto_create_column)

    def _setup_excel_preview(self):
        """Add a responsive Excel preview below the mapping controls (EXCEL PREVIEW DISPLAY).
        
        Shows the selected Excel sheet with the mapped column highlighted in yellow.
        Makes the preview larger (300px minimum height) for better data visibility.
        """
        if not hasattr(self.ui, 'formLayout_excel'):
            return

        self._preview_widget = ExcelPreviewWidget(self.ui.groupBox_excel)
        self._preview_widget.setMinimumHeight(300)  # Larger for better visibility

        # Insert below the Auto-Create button.
        self.ui.formLayout_excel.setWidget(
            4, QFormLayout.ItemRole.SpanningRole, self._preview_widget
        )
        
        # Initialize preview with current sheet/column selection.
        sheet_name = self.ui.combo_sheet.currentText().strip()
        if sheet_name:
            self._preview_widget.set_sheet(sheet_name)
            # Auto-highlight the currently selected column
            column_name = self.ui.combo_column.currentText().strip()
            if column_name:
                self._preview_widget.set_highlight_column(column_name)

    def _apply_flowline_only_mode(self):
        """Apply focused edit behavior for existing flowlines."""
        if not hasattr(self.ui, 'formLayout_excel'):
            return

        self._mapping_warning_label = QLabel()
        self._mapping_warning_label.setWordWrap(True)
        self.ui.formLayout_excel.setWidget(
            5, QFormLayout.ItemRole.SpanningRole, self._mapping_warning_label
        )

        if self._flowline_only_mode:
            self.ui.groupBox_excel.setTitle("Flowline Data Mapping")
            self.ui.btn_auto_map.hide()
            self.ui.btn_auto_map.setEnabled(False)
            self.ui.btn_auto_map.setToolTip(
                "Auto-mapping tools are available in new flow setup or Excel Setup."
            )
            if hasattr(self, "btn_auto_create_column"):
                self.btn_auto_create_column.hide()
                self.btn_auto_create_column.setEnabled(False)
            if hasattr(self, "_preview_widget"):
                self._preview_widget.set_add_row_enabled(False)
                self._preview_widget.set_help_text(
                    "<b>Excel Preview</b> - Only selected flowline column is editable below."
                )
        elif hasattr(self, "_preview_widget"):
            self._preview_widget.set_add_row_enabled(True)

        self._sync_preview_column_permissions()

    def _sync_preview_column_permissions(self):
        """Sync preview highlight + editable column lock with current mapping."""
        if not hasattr(self, "_preview_widget"):
            return

        selected_column = self.ui.combo_column.currentText().strip() or None
        self._preview_widget.set_highlight_column(selected_column)
        self._preview_widget.set_editable_column(selected_column if self._flowline_only_mode else None)

        if not self._mapping_warning_label:
            return

        if not self._flowline_only_mode:
            self._mapping_warning_label.hide()
            return

        has_valid_column = self._preview_widget.has_loaded_column(selected_column)
        if has_valid_column:
            self._mapping_warning_label.setText(
                "Only the selected flowline column is editable below."
            )
            self._mapping_warning_label.setStyleSheet("color: #285b2a; font-size: 11px;")
        else:
            self._mapping_warning_label.setText(
                "Mapped column not found in this sheet. No cells are editable until a valid column is selected."
            )
            self._mapping_warning_label.setStyleSheet("color: #8a4b00; font-size: 11px;")
        self._mapping_warning_label.show()

    def _setup_endpoint_edit_buttons(self):
        """Add buttons to edit the From/To component names.

        This lets users rename components without leaving the flow dialog.
        The underlying node IDs remain stable; only labels and metadata update.
        """
        layout = QHBoxLayout()

        self.btn_edit_from = QPushButton("Edit From")
        self.btn_edit_from.setToolTip("Edit the source component details")
        self.btn_edit_to = QPushButton("Edit To")
        self.btn_edit_to.setToolTip("Edit the destination component details")

        layout.addWidget(self.btn_edit_from)
        layout.addWidget(self.btn_edit_to)
        layout.addStretch(1)

        # Insert after the To Component row.
        self.ui.formLayout.insertRow(2, "", layout)

        self.btn_edit_from.clicked.connect(lambda: self._edit_endpoint_node("from"))
        self.btn_edit_to.clicked.connect(lambda: self._edit_endpoint_node("to"))

    def _edit_endpoint_node(self, endpoint: str) -> None:
        """Open the Add/Edit dialog for a flow endpoint node.

        Args:
            endpoint: "from" or "to" indicating which node to edit.
        """
        if not self.parent_page:
            QMessageBox.warning(self, "Edit Component", "Parent page not available.")
            return

        node_id = (
            self.edge_data.get('from_id') if endpoint == "from" else self.edge_data.get('to_id')
        )
        if not node_id:
            QMessageBox.warning(self, "Edit Component", "Component ID missing.")
            return

        # Locate node data in the parent diagram data.
        node_data = next(
            (n for n in self.parent_page.diagram_data.get('nodes', []) if n.get('id') == node_id),
            None
        )
        if not node_data:
            QMessageBox.warning(self, "Edit Component", "Component not found in diagram.")
            return

        dialog = AddEditNodeDialog(self.parent_page, mode="edit", node_id=node_id, node_data=node_data)
        if dialog.exec() != QDialog.Accepted:
            return

        updated_node = node_data.copy()
        updated_node.update(dialog.get_node_data())
        updated_node['x'] = node_data.get('x', 0)
        updated_node['y'] = node_data.get('y', 0)
        updated_node['width'] = node_data.get('width', FlowNodeItem.DEFAULT_WIDTH)
        updated_node['height'] = node_data.get('height', FlowNodeItem.DEFAULT_HEIGHT)

        # Persist updates in the parent diagram data.
        nodes = self.parent_page.diagram_data.get('nodes', [])
        for idx, node in enumerate(nodes):
            if node.get('id') == node_id:
                nodes[idx] = updated_node
                break

        # Update graphics item if present.
        node_item = self.parent_page.node_items.get(node_id)
        if node_item:
            node_item.apply_node_data(updated_node)

        # Update display labels in this dialog.
        label_text = updated_node.get('label', node_id)
        if endpoint == "from":
            self.ui.value_from.setText(label_text)
        else:
            self.ui.value_to.setText(label_text)

    def _on_sheet_changed(self, sheet_name: str):
        """Update column dropdown when sheet selection changes (SLOT).
        
        When user selects a different sheet:
        1. Clears existing column options
        2. Loads columns from selected sheet via ExcelManager
        3. Updates preview widget to show new sheet
        
        Args:
            sheet_name: Selected Excel sheet name (e.g., 'Flows_UG2N')
        """
        self.ui.combo_column.clear()
        if not sheet_name:
            return

        columns = self.excel_manager.list_flow_columns(sheet_name)
        if columns:
            self.ui.combo_column.addItems(columns)
        if hasattr(self, "_preview_widget"):
            # Keep preview sheet and highlight in sync with mapping selection.
            self._preview_widget.set_sheet(sheet_name)
            self._sync_preview_column_permissions()

    def _on_column_changed(self, column_name: str):
        """Highlight the selected column in the preview widget (SLOT).
        
        When user selects a column, updates the Excel preview to highlight
        that column in yellow for visual confirmation.
        
        Args:
            column_name: Selected Excel column name
        """
        if hasattr(self, "_preview_widget"):
            # Ensure preview always follows the current sheet + column selection.
            sheet_name = self.ui.combo_sheet.currentText().strip()
            if sheet_name:
                self._preview_widget.set_sheet(sheet_name)
            self._sync_preview_column_permissions()
    
    def _on_pick_color(self):
        """Open color picker dialog for flow line color (SLOT).
        
        Shows Qt color picker dialog and updates the flow color if user
        selects a valid color. Color is used for edge rendering.
        """
        color = QColorDialog.getColor(
            self.selected_color,
            self,
            "Choose Flow Line Color",
            QColorDialog.ShowAlphaChannel
        )
        
        if color.isValid():
            self.selected_color = color
            self._update_color_preview()
    
    def _update_color_preview(self):
        """Update color preview label with current selected color (UI UPDATE).
        
        Sets the background color of the preview label to show the user
        what color the flow line will be rendered as.
        """
        self.ui.label_color_preview.setStyleSheet(
            f"background-color: {self.selected_color.name()}; border: 1px solid #556b84; border-radius: 4px;"
        )
    
    def _on_auto_map(self):
        """
        Intelligent auto-mapping of flow to Excel column.
        
        Algorithm:
        1. Get source and destination node IDs
        2. Extract readable names (e.g., "BH" from "bh_ndgwa")
        3. Search Excel columns for matching names
        4. Suggest closest match
        
        Uses ExcelManager to search for matching column names.
        """
        from_id = self.edge_data.get('from_id') or (self.from_node_data or {}).get('id', '')
        to_id = self.edge_data.get('to_id') or (self.to_node_data or {}).get('id', '')
        sheet_name = self.ui.combo_sheet.currentText().strip()

        mapping = self.excel_manager.auto_map_flow_column(
            from_id=from_id,
            to_id=to_id,
            area_code_or_sheet=sheet_name or None,
        )

        if not mapping:
            QMessageBox.information(
                self,
                "Auto-Mapping",
                "No matching Excel column found for this flow.\n"
                "You can choose a column manually or create a new one."
            )
            return

        mapped_sheet = mapping.get('sheet', '')
        mapped_column = mapping.get('column', '')

        if mapped_sheet:
            if self.ui.combo_sheet.findText(mapped_sheet) < 0:
                self.ui.combo_sheet.addItem(mapped_sheet)
            self.ui.combo_sheet.setCurrentText(mapped_sheet)

        if mapped_column:
            if self.ui.combo_column.findText(mapped_column) < 0:
                self.ui.combo_column.addItem(mapped_column)
            self.ui.combo_column.setCurrentText(mapped_column)

    def _on_auto_create_column(self):
        """Create a new Excel column for this flowline and select it.

        This writes to the Flow Diagram Excel file (timeseries_excel_path),
        not the Meter Readings Excel file. It ensures the column exists so
        users can enter flow volumes without leaving the app.
        """
        from_id = self.edge_data.get('from_id') or (self.from_node_data or {}).get('id', '')
        to_id = self.edge_data.get('to_id') or (self.to_node_data or {}).get('id', '')

        if not from_id or not to_id:
            QMessageBox.warning(self, "Missing Data", "Flow endpoints are missing.")
            return

        # Suggest a standardized column name based on flow endpoints.
        suggested_name = self.excel_manager.suggest_flow_column_name(from_id, to_id)
        if not suggested_name:
            QMessageBox.warning(self, "Auto-Create", "Unable to suggest a column name.")
            return

        sheet_name = self.ui.combo_sheet.currentText().strip()
        if not sheet_name:
            QMessageBox.warning(self, "Auto-Create", "Please select a sheet first.")
            return

        confirm = QMessageBox.question(
            self,
            "Create Excel Column",
            f"Create column '{suggested_name}' in '{sheet_name}'?\n\n"
            "This will modify the Flow Diagram Excel file.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # Prevent duplicates: if column already exists, inform user and select it.
        existing_columns = self.excel_manager.list_flow_columns(sheet_name)
        if suggested_name in existing_columns:
            self._on_sheet_changed(sheet_name)
            self.ui.combo_column.setCurrentText(suggested_name)
            QMessageBox.information(
                self,
                "Auto-Create",
                f"Column '{suggested_name}' already exists. It has been selected for you."
            )
            return

        created = self.excel_manager.create_flow_column(sheet_name, suggested_name)
        if not created:
            QMessageBox.warning(
                self,
                "Auto-Create",
                "Failed to create column. Ensure the Excel file is not open and try again."
            )
            return

        # Refresh the column list and select the newly created column.
        self._on_sheet_changed(sheet_name)
        if self.ui.combo_column.findText(suggested_name) < 0:
            self.ui.combo_column.addItem(suggested_name)
        self.ui.combo_column.setCurrentText(suggested_name)

        QMessageBox.information(
            self,
            "Auto-Create",
            f"Column '{suggested_name}' created and selected."
        )
    
    def get_flow_data(self) -> Dict:
        """
        Retrieve form data as dictionary for saving to edge_data.
        
        For new edges, returns complete edge_data with waypoints.
        For existing edges, returns updated fields.
        
        Returns:
            Dict with keys: from_id, to_id, flow_type, color, volume, waypoints
            Example:
            {
                'from_id': 'BH_NDGWA',
                'to_id': 'SUMP_1',
                'flow_type': 'transfer',
                'color': '#3498DB',
                'volume': 0.0,
                'waypoints': [QPointF(...), QPointF(...), ...],
                'excel_mapping': {'sheet': '', 'column': ''}
            }
        """
        flow_type_map = {
            0: 'transfer',
            1: 'clean',
            2: 'dirty',
            3: 'evaporation',
            4: 'recirculation'
        }
        
        # Base fields that always get updated
        updated_data = {
            'flow_type': flow_type_map.get(self.ui.combo_flow_type.currentIndex(), 'transfer'),
            'color': self.selected_color.name(),
            'volume': 0.0,  # Volume loaded from Excel mapping, not from user input
            'excel_mapping': {
                'sheet': self.ui.combo_sheet.currentText() if hasattr(self.ui, 'combo_sheet') else '',
                'column': self.ui.combo_column.currentText() if hasattr(self.ui, 'combo_column') else ''
            }
        }
        
        # For new edges, include waypoints and node IDs
        if self.is_new_edge:
            updated_data.update({
                'from_id': self.edge_data.get('from_id'),
                'to_id': self.edge_data.get('to_id'),
                'waypoints': self.edge_data.get('waypoints', [])
            })
        
        return updated_data
    
    def accept(self):
        """Override accept to validate before closing."""
        sheet = self.ui.combo_sheet.currentText().strip()
        column = self.ui.combo_column.currentText().strip()
        
        if not sheet or not column:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select or enter both sheet name and column name"
            )
            return
        
        super().accept()
