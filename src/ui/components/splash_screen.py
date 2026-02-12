"""
Splash screen component for app initialization.

Displays branding and progress while loading database, pages, and resources.
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor


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
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(0)

        container = QFrame()
        container.setObjectName("splashCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(14, 42, 79, 55))
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(34, 30, 34, 28)
        container_layout.setSpacing(12)

        self.setStyleSheet(
            """
            QFrame#splashCard {
                background: #fdfefe;
                border-radius: 14px;
                border: 1px solid #c9d8ea;
            }
            QLabel#companyName {
                color: #173b68;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#appTitle {
                color: #103e7a;
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#appVersion {
                color: #476488;
                font-size: 11px;
                font-weight: 500;
            }
            QLabel#statusLabel {
                color: #1f3556;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#statusHint {
                color: #6f87a5;
                font-size: 10px;
                font-weight: 500;
            }
            QProgressBar {
                background: #e6eef7;
                border: 1px solid #d4e0ee;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background: #1f4f8f;
                border-radius: 5px;
            }
            """
        )

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedHeight(64)
        logo_pixmap = self._load_company_logo()
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    210,
                    58,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo_label.setText("TransAfrica Resources")
            logo_label.setObjectName("companyName")
        container_layout.addWidget(logo_label)

        title_label = QLabel("Water Balance Dashboard")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)

        from core.config_manager import ConfigManager
        config = ConfigManager()
        app_version = config.get('app.version', '1.0.1')
        subtitle_text = f"Version {app_version}  |  TransAfrica Resources"
        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setObjectName("appVersion")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(subtitle_label)

        container_layout.addSpacing(12)

        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)

        self.status_hint_label = QLabel("Loading modules and validating configuration")
        self.status_hint_label.setObjectName("statusHint")
        self.status_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_hint_label)

        container_layout.addSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        container_layout.addWidget(self.progress_bar)

        root_layout.addWidget(container)
        self.setFixedSize(560, 420)

    def _load_company_logo(self) -> QPixmap:
        """Load company logo from resources or project file fallback."""
        pixmap = QPixmap(":/icons/Company logo.png")
        if not pixmap.isNull():
            return pixmap

        project_logo = (
            Path(__file__).resolve().parents[1]
            / "resources"
            / "icons"
            / "Company logo.png"
        )
        if project_logo.exists():
            return QPixmap(str(project_logo))

        return QPixmap()
    
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
        self.status_hint_label.setText("Please wait while the dashboard starts...")
        if progress is not None:
            self.progress_bar.setValue(progress)
    
    def finish(self):
        """Close splash screen with fade effect."""
        # Simple close for now, can add fade animation later
        self.close()
