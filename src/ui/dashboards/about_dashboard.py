"""
About Dashboard Controller (APPLICATION INFO).

Purpose:
- Load about.ui (container for about content)
- Display application version, licensing, and credits
"""

from PySide6.QtWidgets import QWidget

from ui.dashboards.generated_ui_about import Ui_Form


class AboutPage(QWidget):
    """About Page (APPLICATION INFORMATION).
    
    Displays application information including:
    - Version info
    - License details
    - Credits
    - Build info
    - Developer contact
    """
    
    def __init__(self, parent=None):
        """Initialize About page.
        
        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        
        # Load compiled UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)
