"""
Add/Edit Node Dialog Controller

Wrapper around generated_ui_add_edit_node_dialog.py that provides:
- Color picker functionality
- Form data validation
- Data retrieval for saving to JSON
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QDialog, QColorDialog, QSpinBox, QLabel, QSizePolicy,
    QWidget, QHBoxLayout, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QGuiApplication
from typing import Dict, Optional

from ui.dialogs.generated_ui_add_edit_node_dialog import Ui_AddEditNodeDialog


class AddEditNodeDialog(QDialog):
    """
    Add or Edit Component Dialog (FORM WRAPPER).
    
    Purpose:
    - Collect component properties from user (ID, label, type, shape, color)
    - Validate input data
    - Provide data retrieval for saving to JSON
    
    Mode:
    - "add": New component (ID field editable)
    - "edit": Existing component (ID field read-only, pre-populate fields)
    """
    
    def __init__(self, parent=None, mode: str = "add", node_id: Optional[str] = None,
                 node_data: Optional[Dict] = None):
        """
        Initialize dialog.
        
        Args:
            parent: Parent widget (FlowDiagramPage)
            mode: "add" or "edit"
            node_id: Node ID (required if mode="edit", optional if mode="add")
            node_data: Optional node data (pre-populates fields for edit mode)
        """
        super().__init__(parent)
        self.ui = Ui_AddEditNodeDialog()
        self.ui.setupUi(self)
        
        self.mode = mode
        self.node_id = node_id
        self.node_data = node_data or {}
        self.selected_color = QColor("#DFE6ED")  # Default color
        self.selected_outline = QColor("#2C3E50")  # Default border color

        self._setup_responsive_size()

        # Add custom controls not present in UI file.
        self._insert_section_rows()
        self._add_custom_controls()
        self._enable_scrollable_form()
        self._apply_layout_polish()
        self._populate_shape_options()
        
        # Setup
        self._setup_mode()
        self._connect_buttons()
        self._update_color_preview()
        self._update_outline_preview()
        
        self.setModal(True)

    def _setup_responsive_size(self):
        """Set responsive dialog size with a safer minimum height."""
        screen = QGuiApplication.primaryScreen().geometry()
        dialog_width = max(640, int(screen.width() * 0.42))
        dialog_height = max(580, int(screen.height() * 0.76))
        self.resize(dialog_width, dialog_height)
        self.setMinimumSize(620, 560)

        # Center on screen
        x = (screen.width() - dialog_width) // 2
        y = (screen.height() - dialog_height) // 2
        self.move(x, y)

    def _enable_scrollable_form(self):
        """Wrap form rows into a scroll area; keep action buttons fixed."""
        remove_indices = []
        for idx in range(self.ui.verticalLayout.count()):
            item = self.ui.verticalLayout.itemAt(idx)
            if item and (item.layout() is self.ui.formLayout or item.spacerItem() is self.ui.verticalSpacer):
                remove_indices.append(idx)

        for idx in sorted(remove_indices, reverse=True):
            self.ui.verticalLayout.takeAt(idx)

        form_container = QWidget(self)
        form_container.setLayout(self.ui.formLayout)

        self._form_scroll = QScrollArea(self)
        self._form_scroll.setObjectName("component_form_scroll")
        self._form_scroll.setWidgetResizable(True)
        self._form_scroll.setFrameShape(QFrame.NoFrame)
        self._form_scroll.setWidget(form_container)
        self._form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._form_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.ui.verticalLayout.insertWidget(0, self._form_scroll, 1)
    
    def _setup_mode(self):
        """Setup UI based on mode - add vs edit (MODE CONFIGURATION).
        
        In edit mode:
        - Sets window title to 'Edit Component'
        - Loads existing node data into fields
        - Allows ID editing for renaming
        
        In add mode:
        - Sets window title to 'Add Component'
        - Focuses ID input for immediate entry
        """
        if self.mode == "edit":
            self.setWindowTitle("Edit Component")
            # Allow ID editing (user can change component identifier)
            self.ui.input_id.setReadOnly(False)
            self.ui.input_id.setText(self.node_id)
            self._load_node_data()
        else:
            self.setWindowTitle("Add Component")
            self.ui.input_id.setReadOnly(False)
            self.ui.input_id.setFocus()

    def _add_custom_controls(self):
        """Add border color, width, height, and font size controls."""
        # Insert custom rows right before "Behavior" section so they remain
        # grouped under Appearance and never overlap existing generated rows.
        custom_start_row = 8

        # Border color row
        self.label_outline_color = QLabel("Border Color:")
        outline_row = QWidget(self)
        outline_layout = QHBoxLayout(outline_row)
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.setSpacing(4)
        outline_row.setMinimumHeight(36)
        self.btn_outline_picker = QPushButton("Choose Color", outline_row)
        self.btn_outline_picker.setObjectName("btn_outline_picker")
        self.label_outline_preview = QLabel(outline_row)
        self.label_outline_preview.setFixedSize(64, 32)
        outline_layout.addWidget(self.btn_outline_picker)
        outline_layout.addWidget(self.label_outline_preview)
        outline_layout.addStretch(1)
        self.ui.formLayout.insertRow(custom_start_row, self.label_outline_color, outline_row)

        # Width row
        self.label_width = QLabel("Width:")
        self.spin_width = QSpinBox(self)
        self.spin_width.setRange(60, 220)
        self.spin_width.setValue(100)
        self.spin_width.setAlignment(Qt.AlignCenter)
        self.spin_width.setMinimumWidth(92)
        self.spin_width.setMaximumWidth(120)
        self.spin_width.setMinimumHeight(32)
        self.ui.formLayout.insertRow(custom_start_row + 1, self.label_width, self.spin_width)

        # Height row
        self.label_height = QLabel("Height:")
        self.spin_height = QSpinBox(self)
        self.spin_height.setRange(50, 170)
        self.spin_height.setValue(80)
        self.spin_height.setAlignment(Qt.AlignCenter)
        self.spin_height.setMinimumWidth(92)
        self.spin_height.setMaximumWidth(120)
        self.spin_height.setMinimumHeight(32)
        self.ui.formLayout.insertRow(custom_start_row + 2, self.label_height, self.spin_height)

        # Font size row
        self.label_font_size = QLabel("Font Size:")
        self.spin_font_size = QSpinBox(self)
        self.spin_font_size.setRange(6, 20)
        self.spin_font_size.setValue(9)
        self.spin_font_size.setAlignment(Qt.AlignCenter)
        self.spin_font_size.setMinimumWidth(92)
        self.spin_font_size.setMaximumWidth(120)
        self.spin_font_size.setMinimumHeight(32)
        self.spin_font_size.setButtonSymbols(QSpinBox.PlusMinus)
        self.ui.formLayout.insertRow(custom_start_row + 3, self.label_font_size, self.spin_font_size)

    def _insert_section_rows(self):
        """Insert visual section headers to improve scanability."""
        appearance = QLabel("Appearance")
        appearance.setObjectName("dialogSectionHeader")
        identity = QLabel("Identity")
        identity.setObjectName("dialogSectionHeader")

        # Base generated rows are:
        # 0 ID, 1 Label, 2 Type, 3 Shape, 4 Fill Color, 5 Lock
        # Insert headers in deterministic positions to avoid row collisions.
        self.ui.formLayout.insertRow(0, identity)
        self.ui.formLayout.insertRow(4, appearance)

    def _apply_layout_polish(self):
        """Apply spacing, sizing, and styles for a cleaner dialog layout."""
        self.setMinimumSize(620, 560)

        self.ui.formLayout.setHorizontalSpacing(14)
        self.ui.formLayout.setVerticalSpacing(12)
        self.ui.formLayout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.ui.label_label.setText("Label:")
        self.ui.label_lock.setText("Lock Component:")
        self.ui.checkbox_lock.setText("Prevent dragging")

        # Normalize control heights for visual consistency.
        for widget in (self.ui.input_id, self.ui.combo_type, self.ui.combo_shape):
            widget.setMinimumHeight(32)
        self.ui.input_label.setMinimumHeight(64)
        self.ui.input_label.setMaximumHeight(72)
        self.ui.btn_color_picker.setMinimumHeight(32)
        self.ui.btn_color_picker.setMinimumWidth(110)
        self.btn_outline_picker.setMinimumHeight(32)
        self.btn_outline_picker.setMinimumWidth(110)
        self.ui.label_color_preview.setFixedSize(64, 32)
        self.label_outline_preview.setFixedSize(64, 32)

        # Reduce excessive bottom gap.
        self.ui.verticalSpacer.changeSize(20, 8, QSizePolicy.Minimum, QSizePolicy.Fixed)
        if hasattr(self, "_form_scroll"):
            self._form_scroll.setMinimumHeight(420)

        # Button hierarchy: primary OK, secondary Cancel.
        self.ui.btn_ok.setText("Save")
        self.ui.btn_ok.setMinimumHeight(34)
        self.ui.btn_cancel.setMinimumHeight(34)
        self.ui.btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        self.ui.btn_cancel.setIconSize(QSize(14, 14))

        self.setStyleSheet(
            """
            QDialog {
                background: #f5f8fc;
            }
            QLabel#dialogSectionHeader {
                font-size: 12px;
                font-weight: 700;
                color: #1d4f91;
                margin-top: 6px;
                padding-top: 2px;
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
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
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
            QScrollArea#component_form_scroll {
                background: transparent;
            }
            QScrollBar:vertical {
                background: #eef3f9;
                width: 10px;
                margin: 2px 2px 2px 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #b9c9de;
                min-height: 28px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9eb4d0;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            """
        )

    def _populate_shape_options(self):
        """Populate shape combo box with all supported shapes (SHAPE OPTIONS).
        
        Available shapes:
        - Rectangle: Standard rectangular node (default)
        - Oval/Circle: For tanks, dams, and circular structures
        - Trapezoid: For processing facilities
        - Office/Building: For administrative buildings
        - Hexagon: For special-purpose nodes
        """
        self.shape_options = [
            "Rectangle",
            "Oval/Circle",
            "Trapezoid",
            "Office Building",
            "Hexagon",
        ]
        self.ui.combo_shape.clear()
        self.ui.combo_shape.addItems(self.shape_options)

    def _load_node_data(self):
        """Load node data into the form fields for edit mode (DATA BINDING).
        
        Populates form fields from self.node_data:
        - Label (multi-line text)
        - Type (dropdown: water_source, storage, process, etc.)
        - Shape (rect, oval, trapezoid, etc.)
        - Locked state (checkbox)
        - Font size (spinbox)
        - Fill color (color preview)
        
        Falls back to parent diagram_data if node_data not provided.
        """
        if not self.node_data and self.parent() is not None:
            parent_data = getattr(self.parent(), "diagram_data", {})
            for node in parent_data.get("nodes", []):
                if node.get("id") == self.node_id:
                    self.node_data = node
                    break

        if not self.node_data:
            return

        self.ui.input_label.setPlainText(self.node_data.get("label", ""))
        self.ui.combo_type.setCurrentText(
            self.node_data.get("type", "").replace("_", " ").title()
        )
        shape_value = self.node_data.get("shape", "rect")
        shape_label = {
            "rect": "Rectangle",
            "oval": "Oval/Circle",
            "trapezoid": "Trapezoid",
            "office": "Office Building",
            "hexagon": "Hexagon",
        }.get(shape_value, "Rectangle")
        if shape_label in self.shape_options:
            self.ui.combo_shape.setCurrentText(shape_label)
        self.ui.checkbox_lock.setChecked(self.node_data.get("locked", False))
        self.spin_font_size.setValue(int(self.node_data.get("font_size", 9)))
        self.spin_width.setValue(int(self.node_data.get("width", 100)))
        self.spin_height.setValue(int(self.node_data.get("height", 80)))

        fill_color = self.node_data.get("fill", "#DFE6ED")
        self.selected_color = QColor(fill_color)
        self._update_color_preview()
        outline_color = self.node_data.get("outline", "#2C3E50")
        self.selected_outline = QColor(outline_color)
        self._update_outline_preview()
    
    def _connect_buttons(self):
        """Connect button signals to slot methods (SIGNAL/SLOT WIRING).
        
        Connects color picker button to _on_pick_color() for fill color selection.
        """
        self.ui.btn_color_picker.clicked.connect(self._on_pick_color)
        self.btn_outline_picker.clicked.connect(self._on_pick_outline_color)
    
    def _on_pick_color(self):
        """Open color picker dialog for component fill color (SLOT).
        
        Shows Qt color picker dialog. If user selects valid color,
        updates selected_color and refreshes preview label.
        """
        color = QColorDialog.getColor(
            self.selected_color,
            self,
            "Choose Component Color",
            QColorDialog.ShowAlphaChannel
        )
        
        if color.isValid():
            self.selected_color = color
            self._update_color_preview()

    def _on_pick_outline_color(self):
        """Open color picker dialog for component border color."""
        color = QColorDialog.getColor(
            self.selected_outline,
            self,
            "Choose Border Color",
            QColorDialog.ShowAlphaChannel
        )

        if color.isValid():
            self.selected_outline = color
            self._update_outline_preview()
    
    def _update_color_preview(self):
        """Update color preview label with current selected color (UI UPDATE).
        
        Sets background color of preview label to show user what fill
        color the component will be rendered with.
        """
        self.ui.label_color_preview.setStyleSheet(
            f"background-color: {self.selected_color.name()}; border: 1px solid #556b84; border-radius: 4px;"
        )

    def _update_outline_preview(self):
        """Update border color preview swatch."""
        self.label_outline_preview.setStyleSheet(
            f"background-color: {self.selected_outline.name()}; border: 1px solid #556b84; border-radius: 4px;"
        )
    
    def get_node_data(self) -> Dict:
        """
        Retrieve form data as dictionary.
        
        Returns:
            Dict with keys: id, label, type, shape, fill, locked
            Example:
            {
                'id': 'bh_ndgwa',
                'label': 'Borehole\nNDGWA',
                'type': 'water_source',
                'shape': 'rect',
                'fill': '#DFE6ED',
                'locked': False
            }
        """
        shape_label = self.ui.combo_shape.currentText()
        shape_value = {
            "Rectangle": "rect",
            "Oval/Circle": "oval",
            "Trapezoid": "trapezoid",
            "Office Building": "office",
            "Hexagon": "hexagon",
        }.get(shape_label, "rect")

        return {
            'id': self.ui.input_id.text().strip(),
            'label': self.ui.input_label.toPlainText().strip(),
            'type': self.ui.combo_type.currentText().lower().replace(' ', '_'),
            'shape': shape_value,
            'fill': self.selected_color.name(),
            'outline': self.selected_outline.name(),
            'locked': self.ui.checkbox_lock.isChecked(),
            'font_size': self.spin_font_size.value(),
            'width': self.spin_width.value(),
            'height': self.spin_height.value(),
        }
    
    def validate(self) -> bool:
        """
        Validate form data.
        
        Returns:
            True if valid, False otherwise
        """
        node_id = self.ui.input_id.text().strip()
        label = self.ui.input_label.toPlainText().strip()
        
        # Validate ID
        if not node_id:
            return False, "Component ID is required"
        
        if len(node_id) > 50:
            return False, "Component ID is too long (max 50 chars)"
        
        if not all(c.isalnum() or c == '_' for c in node_id):
            return False, "Component ID can only contain letters, numbers, and underscores"
        
        # Validate label
        if not label:
            return False, "Label is required"
        
        if len(label) > 100:
            return False, "Label is too long (max 100 chars)"
        
        return True, ""
    
    def accept(self):
        """Override accept to validate before closing."""
        valid, message = self.validate()
        if not valid:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", message)
            return
        
        super().accept()
