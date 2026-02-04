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
        
        # Set default selection
        self._set_default_type(default_type)
        
        self.setModal(True)
    
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
