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

from PySide6.QtWidgets import QDialog, QColorDialog, QSpinBox, QLabel
from PySide6.QtGui import QColor
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

        # Add font size control (not present in UI file)
        self._add_font_size_control()
        self._populate_shape_options()
        
        # Setup
        self._setup_mode()
        self._connect_buttons()
        self._update_color_preview()
        
        self.setModal(True)
    
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

    def _add_font_size_control(self):
        """Add font size spin box to form layout (UI enhancement)."""
        self.label_font_size = QLabel("Font Size:")
        self.spin_font_size = QSpinBox(self)
        self.spin_font_size.setRange(6, 20)
        self.spin_font_size.setValue(9)
        self.ui.formLayout.insertRow(5, self.label_font_size, self.spin_font_size)

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
            "Office/Building",
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
            "office": "Office/Building",
            "hexagon": "Hexagon",
        }.get(shape_value, "Rectangle")
        if shape_label in self.shape_options:
            self.ui.combo_shape.setCurrentText(shape_label)
        self.ui.checkbox_lock.setChecked(self.node_data.get("locked", False))
        self.spin_font_size.setValue(int(self.node_data.get("font_size", 9)))

        fill_color = self.node_data.get("fill", "#DFE6ED")
        self.selected_color = QColor(fill_color)
        self._update_color_preview()
    
    def _connect_buttons(self):
        """Connect button signals to slot methods (SIGNAL/SLOT WIRING).
        
        Connects color picker button to _on_pick_color() for fill color selection.
        """
        self.ui.btn_color_picker.clicked.connect(self._on_pick_color)
    
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
    
    def _update_color_preview(self):
        """Update color preview label with current selected color (UI UPDATE).
        
        Sets background color of preview label to show user what fill
        color the component will be rendered with.
        """
        self.ui.label_color_preview.setStyleSheet(
            f"background-color: {self.selected_color.name()}; border: 1px solid #333;"
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
        base_outline = self.node_data.get("outline", "#2C3E50")
        shape_label = self.ui.combo_shape.currentText()
        shape_value = {
            "Rectangle": "rect",
            "Oval/Circle": "oval",
            "Trapezoid": "trapezoid",
            "Office/Building": "office",
            "Hexagon": "hexagon",
        }.get(shape_label, "rect")

        return {
            'id': self.ui.input_id.text().strip(),
            'label': self.ui.input_label.toPlainText().strip(),
            'type': self.ui.combo_type.currentText().lower().replace(' ', '_'),
            'shape': shape_value,
            'fill': self.selected_color.name(),
            'outline': base_outline,
            'locked': self.ui.checkbox_lock.isChecked(),
            'font_size': self.spin_font_size.value()
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
