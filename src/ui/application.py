"""
Water Balance Application Main Window (PySide6)

Minimal stub for initial setup verification.
Will be replaced with Qt Designer-based UI in Phase 2.
"""
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class WaterBalanceApp(QMainWindow):
    """Main application window (STUB - will expand with Qt Designer).
    
    This is a temporary "Hello World" implementation to verify:
    1. PySide6 installation working
    2. Environment setup correct
    3. Window creation successful
    
    Next: Replace with Qt Designer .ui file + controller pattern.
    """
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._create_stub_ui()
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("Water Balance Dashboard - PySide6 Migration")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 800)
    
    def _create_stub_ui(self):
        """Create temporary placeholder UI.
        
        Shows success message to confirm PySide6 setup working.
        This will be completely replaced in Phase 2.
        """
        central = QWidget()
        layout = QVBoxLayout()
        
        # Success message
        label = QLabel(
            "✅ PySide6 Setup Working!\n\n"
            "Environment: WATERBALANCE_USER_DIR configured\n"
            "Database: Schema and manager copied\n"
            "Services: Business logic ready for adaptation\n"
            "Data: Configuration and diagrams loaded\n\n"
            "📋 Next Steps:\n"
            "1. Install Qt Designer\n"
            "2. Design main window UI (sidebar + content)\n"
            "3. Compile .ui to Python\n"
            "4. Build first dashboard (Calculations)\n\n"
            "See QUICKSTART.md Phase 2 for details"
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 50px;
                background-color: #f0f8ff;
                border: 2px solid #0066cc;
                border-radius: 10px;
            }
        """)
        
        layout.addWidget(label)
        central.setLayout(layout)
        self.setCentralWidget(central)
