"""
Flow Type Selection Dialog Controller

Wrapper around generated_ui_flow_type_selection_dialog.py that provides:
- Radio button selection for flow types
- Data retrieval for flow type
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from ui.dialogs.generated_ui_flow_type_selection_dialog import Ui_FlowTypeSelectionDialog


class FlowTypeSelectionDialog(QDialog):
    """
    Flow Type Selection Dialog (QUICK PICKER).
    
    Purpose:
    - Simple radio button selection for flow type when drawing new flows
    - Used immediately after user finishes drawing a line
    - Default: Clean water
    """
    
    def __init__(self, parent=None, default_type: str = "clean"):
        """
        Initialize dialog.
        
        Args:
            parent: Parent widget (FlowDiagramPage)
            default_type: Default selected flow type ('clean', 'dirty', 'evaporation', 'recirculation')
        """
        super().__init__(parent)
        self.ui = Ui_FlowTypeSelectionDialog()
        self.ui.setupUi(self)
        self._apply_dialog_polish()
        self._normalize_option_labels()
        
        # Set default selection
        self._set_default_type(default_type)
        
        self.setModal(True)

    def _apply_dialog_polish(self) -> None:
        """Apply consistent popup style for flow dialogs."""
        self.setMinimumSize(460, 280)
        self.resize(500, 300)
        self.ui.btn_ok.setText("Save")
        self.ui.btn_ok.setMinimumHeight(34)
        self.ui.btn_cancel.setMinimumHeight(34)
        self.ui.btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        self.ui.btn_cancel.setIconSize(QSize(14, 14))
        self.ui.label_instruction.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.setStyleSheet(
            """
            QDialog {
                background: #f5f8fc;
            }
            QLabel#label_instruction {
                color: #153e72;
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            QRadioButton {
                spacing: 10px;
                color: #122a4b;
                font-size: 13px;
                padding: 4px 0;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
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

    def _normalize_option_labels(self) -> None:
        """Use clear business-facing labels."""
        self.ui.label_instruction.setText("Select water flow type for this line:")
        self.ui.radio_clean.setText("Clean Water (Blue) - fresh water source")
        self.ui.radio_dirty.setText("Dirty/Waste Water (Red) - wastewater or effluent")
        self.ui.radio_evaporation.setText("Evaporation Loss (Black) - atmospheric loss")
        self.ui.radio_recirculation.setText("Recirculation (Purple) - recycled return flow")
    
    def _set_default_type(self, flow_type: str):
        """
        Set default selected radio button.
        
        Args:
            flow_type: 'clean', 'dirty', 'evaporation', or 'recirculation'
        """
        type_map = {
            'clean': self.ui.radio_clean,
            'dirty': self.ui.radio_dirty,
            'evaporation': self.ui.radio_evaporation,
            'recirculation': self.ui.radio_recirculation
        }
        
        radio = type_map.get(flow_type.lower(), self.ui.radio_clean)
        radio.setChecked(True)
    
    def get_flow_type(self) -> str:
        """
        Get selected flow type.
        
        Returns:
            'clean', 'dirty', 'evaporation', or 'recirculation'
        """
        if self.ui.radio_dirty.isChecked():
            return 'dirty'
        elif self.ui.radio_evaporation.isChecked():
            return 'evaporation'
        elif self.ui.radio_recirculation.isChecked():
            return 'recirculation'
        else:
            return 'clean'
    
    def get_flow_color(self) -> str:
        """
        Get color for selected flow type.
        
        Returns:
            Hex color code: '#3498DB' (clean), '#E74C3C' (dirty),
            '#2C3E50' (evaporation), '#9B59B6' (recirculation)
        """
        flow_type = self.get_flow_type()
        color_map = {
            'clean': '#3498DB',          # Blue
            'dirty': '#E74C3C',          # Red
            'evaporation': '#2C3E50',    # Black/Gray
            'recirculation': '#9B59B6'   # Purple
        }
        return color_map.get(flow_type, '#3498DB')
