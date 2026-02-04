"""
Help Dashboard Controller (DOCUMENTATION & SUPPORT).

Purpose:
- Load help.ui (container for help content)
- Display user guides, FAQs, and support info
"""

from PySide6.QtWidgets import QWidget

from ui.dashboards.generated_ui_help import Ui_Form


class HelpPage(QWidget):
    """Help Page (DOCUMENTATION).
    
    Displays help resources including:
    - User guides
    - How-to documentation
    - FAQs
    - Support contact info
    - Version/about info
    """
    
    def __init__(self, parent=None):
        """Initialize Help page.
        
        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        
        # Load compiled UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)
