"""
Splash screen component for app initialization.

Displays branding and progress while loading database, pages, and resources.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont


class SplashScreen(QWidget):
    """Professional splash screen with branding and progress indicator.
    
    Shows while app initializes database, loads pages, and prepares resources.
    Auto-closes when loading is complete.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()
        self._center_on_screen()
    
    def _setup_ui(self):
        """Create splash screen layout with logo, title, and progress bar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Container for styling
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #0D47A1;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        # Logo (if available)
        try:
            logo_label = QLabel()
            pixmap = QPixmap(":/icons/water_balance_logo.png")  # Try resource first
            if pixmap.isNull():
                pixmap = QPixmap("logo/Water Balance.ico")  # Fallback to file
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, 
                                              Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                container_layout.addWidget(logo_label)
        except:
            pass  # Skip logo if not found
        
        # Application title
        title_label = QLabel("Water Balance Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #0D47A1; background: transparent; border: none;")
        container_layout.addWidget(title_label)
        
        # Subtitle with version
        from core.config_manager import ConfigManager
        config = ConfigManager()
        app_version = config.get('app.version', '1.0.1')
        subtitle_text = f"PySide6 Edition - v{app_version}"
        subtitle_label = QLabel(subtitle_text)
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666; background: transparent; border: none;")
        container_layout.addWidget(subtitle_label)
        
        # Spacer
        container_layout.addSpacing(20)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        container_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E0E0E0;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #0D47A1;
                border-radius: 3px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        layout.addWidget(container)
        self.setFixedSize(450, 400)
    
    def _center_on_screen(self):
        """Center splash screen on primary screen."""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def update_status(self, message: str, progress: int = None):
        """Update status message and progress.
        
        Args:
            message: Status text to display
            progress: Progress percentage (0-100), None to keep current
        """
        self.status_label.setText(message)
        if progress is not None:
            self.progress_bar.setValue(progress)
    
    def finish(self):
        """Close splash screen with fade effect."""
        # Simple close for now, can add fade animation later
        self.close()
