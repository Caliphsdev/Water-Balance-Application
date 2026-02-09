"""
Messages Dashboard - Professional Redesign

Complete redesign following desktop-design skill principles.
Features: Professional cards, delete functionality, notification badge, styled tabs.

(MODULE OVERVIEW)
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QStackedWidget, QComboBox, QLineEdit,
    QTextEdit, QMessageBox, QGraphicsDropShadowEffect, QSizePolicy,
    QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, QUrl
from PySide6.QtGui import QIcon, QFont, QColor, QDesktopServices

from core.app_logger import logger


# (NOTIFICATION DRAWER COMPONENT)

class NotificationDrawer(QFrame):
    """
    Slide-in drawer panel for viewing full notification details.
    
    Features:
    - Slides in from right edge with smooth animation
    - Shows full notification title, message, and timestamp
    - Close button and semi-transparent backdrop
    - Professional styling with shadows
    """
    
    closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notification_data = None
        self._setup_ui()
        self.hide()
    
    def _setup_ui(self):
        """Build drawer UI."""
        self.setObjectName("notificationDrawer")
        self.setStyleSheet("""
            QFrame#notificationDrawer {
                background-color: white;
                border-left: 1px solid #d0d7de;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Notification Details")
        title.setFont(QFont('Segoe UI Variable', 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #24292f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #57606a;
                font-size: 18px;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #f6f8fa;
            }
        """)
        close_btn.clicked.connect(self.closed.emit)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #d0d7de;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Content area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f6f8fa;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #d0d7de;
                border-radius: 5px;
                min-height: 30px;
            }
        """)
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)
        self.content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(-5)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)
    
    def show_notification(self, notification_data: dict):
        """Display notification in drawer."""
        self.notification_data = notification_data
        
        if not hasattr(self, "title_label"):
            self.title_label = QLabel()
            self.title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.DemiBold))
            self.title_label.setWordWrap(True)
            self.title_label.setStyleSheet("color: #24292f; margin-bottom: 12px;")
            self.content_layout.insertWidget(0, self.title_label)

            self.badge_label = QLabel()
            self.badge_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
            self.badge_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.badge_label.setStyleSheet("""
                QLabel {
                    background-color: #0969da;
                    color: white;
                    padding: 6px 14px;
                    border-radius: 4px;
                }
            """)
            self.content_layout.insertWidget(1, self.badge_label)

            self.message_label = QLabel()
            self.message_label.setFont(QFont('Segoe UI', 12))
            self.message_label.setWordWrap(True)
            self.message_label.setStyleSheet("color: #424242; line-height: 1.6; margin: 16px 0px;")
            self.content_layout.insertWidget(2, self.message_label)

            self.date_label = QLabel()
            self.date_label.setFont(QFont('Segoe UI', 11))
            self.date_label.setStyleSheet("color: #6e7781; margin-top: 16px;")
            self.content_layout.insertWidget(3, self.date_label)

        # Title
        self.title_label.setText(notification_data.get('title', 'Notification'))

        # Priority badge
        priority = notification_data.get('priority', 'info')
        priority_colors = {
            'critical': '#cf222e',
            'high': '#fb8500',
            'info': '#0969da',
            'low': '#1a7f37'
        }
        badge_color = priority_colors.get(priority, priority_colors['info'])
        self.badge_label.setText(priority.upper())
        self.badge_label.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_color};
                color: white;
                padding: 6px 14px;
                border-radius: 4px;
            }}
        """)

        # Message
        message = notification_data.get('message') or notification_data.get('body', '')
        if message:
            self.message_label.setText(message)
            self.message_label.show()
        else:
            self.message_label.hide()

        # Date
        date_text = notification_data.get('created_at', '')
        if date_text:
            self.date_label.setText(f"📅 {self._format_date(date_text)}")
            self.date_label.show()
        else:
            self.date_label.hide()

        self.show()
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            return date_str


# (NOTIFICATION CARD COMPONENT)

class NotificationCard(QFrame):
    """
    Individual notification card with professional design.
    
    Features:
    - Priority color indicator
    - Delete button with hover effect
    - Click to expand
    - Shadow for depth
    - Read/unread styling
    """
    
    deleted = Signal(str)  # Emits notification ID when deleted
    clicked = Signal(dict)  # Emits notification data when clicked
    
    def __init__(self, notification_data: dict, parent=None):
        super().__init__(parent)
        self.notification_data = notification_data
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Build card layout."""
        self.setObjectName("notificationCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Priority indicator (colored dot)
        icon = QLabel()
        icon.setFixedSize(12, 12)
        icon.setStyleSheet(f"""
            QLabel {{
                background-color: {self._get_priority_color()};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title
        title = QLabel(self.notification_data.get('title', 'Notification'))
        title.setFont(QFont('Segoe UI', 12, QFont.Weight.DemiBold))
        title.setWordWrap(True)
        content_layout.addWidget(title)
        
        # Message preview
        message = self.notification_data.get('message', '')
        if message:
            preview = QLabel(message[:100] + ('...' if len(message) > 100 else ''))
            preview.setFont(QFont('Segoe UI', 10))
            preview.setWordWrap(True)
            preview.setStyleSheet("color: #6e7781;")
            content_layout.addWidget(preview)
        
        # Date
        date = self.notification_data.get('created_at', '')
        if date:
            date_label = QLabel(self._format_date(date))
            date_label.setFont(QFont('Segoe UI', 9))
            date_label.setStyleSheet("color: #8b949e;")
            content_layout.addWidget(date_label)
        
        layout.addLayout(content_layout, stretch=1)
        
        # Delete button
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setObjectName("deleteButton")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(delete_btn, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Add shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
    
    def _apply_styling(self):
        """Apply professional card styling."""
        is_read = self.notification_data.get('is_read', False)
        bg_color = "#f6f8fa" if is_read else "#ffffff"
        
        self.setStyleSheet(f"""
            QFrame#notificationCard {{
                background-color: {bg_color};
                border: 1px solid #d0d7de;
                border-radius: 8px;
                padding: 0px;
            }}
            QFrame#notificationCard:hover {{
                background-color: #f3f4f6;
                border-color: #0969da;
            }}
            QPushButton#deleteButton {{
                background-color: transparent;
                border: none;
                color: #57606a;
                font-size: 16px;
                border-radius: 14px;
            }}
            QPushButton#deleteButton:hover {{
                background-color: #ffebe9;
                color: #cf222e;
            }}
        """)
    
    def _get_priority_color(self) -> str:
        """Get color based on priority/type."""
        priority = self.notification_data.get('priority', 'info')
        colors = {
            'critical': '#cf222e',
            'high': '#fb8500',
            'info': '#0969da',
            'low': '#1a7f37'
        }
        return colors.get(priority, colors['info'])
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display (relative time)."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    return f"{diff.seconds // 60}m ago"
                return f"{diff.seconds // 3600}h ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days}d ago"
            else:
                return dt.strftime("%b %d, %Y")
        except:
            return date_str
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        notif_id = self.notification_data.get('id', '')
        if notif_id:
            self.deleted.emit(notif_id)
    
    def mousePressEvent(self, event):
        """Handle card click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.notification_data)
        super().mousePressEvent(event)


# (NOTIFICATION BADGE COMPONENT)

class NotificationBadge(QLabel):
    """Badge showing unread notification count."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notificationBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(20, 20)
        self.hide()  # Hidden by default
        
        self.setStyleSheet("""
            QLabel#notificationBadge {
                background-color: #cf222e;
                color: white;
                font-size: 10px;
                font-weight: bold;
                border-radius: 10px;
                padding: 2px;
            }
        """)
    
    def set_count(self, count: int):
        """Update badge count and visibility."""
        if count > 0:
            self.setText(str(min(count, 99)))  # Cap at 99
            self.show()
        else:
            self.hide()


# (MESSAGES PAGE MAIN CLASS)

class MessagesPage(QWidget):
    """
    Messages & Notifications Dashboard - Professional Redesign
    
    Features:
    - Card-based notification list with delete functionality
    - Notification count badge
    - Styled updates tab
    - Enhanced feedback form
    - Professional typography and spacing
    - Smooth interactions and hover effects
    
    (CLASS OVERVIEW)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("messagesPage")
        self._notifications = []
        self._unread_count = 0
        self._drawer_width = 440
        self._setup_ui()
        
        # Defer notification loading to avoid blocking startup
        QTimer.singleShot(100, self._load_notifications)
        
    def _setup_ui(self):
        """Build main UI with professional layout."""
        self.setStyleSheet("""
            QWidget#messagesPage {
                background-color: #f6f8fa;
            }
            QToolTip {
                background-color: #111827;
                color: #f8fafc;
                border: 1px solid #334155;
                padding: 8px 10px;
                border-radius: 6px;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header with badge
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab bar
        tab_bar = self._create_tab_bar()
        main_layout.addWidget(tab_bar)
        
        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: transparent;")
        
        # Tab 0: Notifications
        self.notifications_tab = self._create_notifications_tab()
        self.content_stack.addWidget(self.notifications_tab)
        
        # Tab 1: Updates
        self.updates_tab = self._create_updates_tab()
        self.content_stack.addWidget(self.updates_tab)
        
        # Tab 2: Feedback
        self.feedback_tab = self._create_feedback_tab()
        self.content_stack.addWidget(self.feedback_tab)
        
        # Content row: stack + drawer
        content_row = QWidget()
        content_row_layout = QHBoxLayout(content_row)
        content_row_layout.setContentsMargins(0, 0, 0, 0)
        content_row_layout.setSpacing(16)

        content_row_layout.addWidget(self.content_stack, 1)

        self.notification_drawer = NotificationDrawer(self)
        self.notification_drawer.closed.connect(self._close_drawer)
        self.notification_drawer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.notification_drawer.setMinimumWidth(0)
        self.notification_drawer.setMaximumWidth(0)
        content_row_layout.addWidget(self.notification_drawer)

        # Drawer animation (smooth slide effect)
        self._drawer_animation = QPropertyAnimation(self.notification_drawer, b"minimumWidth")
        self._drawer_animation.setDuration(280)
        self._drawer_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._drawer_max_animation = QPropertyAnimation(self.notification_drawer, b"maximumWidth")
        self._drawer_max_animation.setDuration(280)
        self._drawer_max_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        main_layout.addWidget(content_row, 1)
        
    def _open_drawer(self):
        """Animate drawer open (smooth width expansion)."""
        self._drawer_animation.stop()
        self._drawer_max_animation.stop()

        self._drawer_animation.setStartValue(self.notification_drawer.minimumWidth())
        self._drawer_animation.setEndValue(self._drawer_width)

        self._drawer_max_animation.setStartValue(self.notification_drawer.maximumWidth())
        self._drawer_max_animation.setEndValue(self._drawer_width)

        self._drawer_animation.start()
        self._drawer_max_animation.start()

    def _close_drawer(self):
        """Animate drawer closed."""
        self._drawer_animation.stop()
        self._drawer_max_animation.stop()

        self._drawer_animation.setStartValue(self.notification_drawer.minimumWidth())
        self._drawer_animation.setEndValue(0)

        self._drawer_max_animation.setStartValue(self.notification_drawer.maximumWidth())
        self._drawer_max_animation.setEndValue(0)

        self._drawer_animation.start()
        self._drawer_max_animation.start()
        
    def _create_header(self) -> QWidget:
        """Create page header with badge (HEADER SECTION)."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Icon + Title + Badge container
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(":/icons/message.svg").pixmap(32, 32))
        title_layout.addWidget(icon_label)
        
        # Title
        title = QLabel("Messages & Notifications")
        title.setFont(QFont('Segoe UI Variable', 24, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #24292f;")
        title_layout.addWidget(title)
        
        # Badge
        self.header_badge = NotificationBadge()
        title_layout.addWidget(self.header_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(title_container)
        layout.addStretch()
        
        return header
        
    def _create_tab_bar(self) -> QWidget:
        """Create professional tab navigation (TAB BAR SECTION)."""
        tab_bar = QWidget()
        layout = QHBoxLayout(tab_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.tab_buttons = []
        tabs = [
            ("🔔 Notifications", 0),
            ("📦 Updates", 1),
            ("💬 Feedback", 2),
        ]
        
        for text, index in tabs:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFont(QFont('Segoe UI', 12, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    padding: 8px 16px;
                    color: #57606a;
                }
                QPushButton:hover {
                    color: #24292f;
                    background-color: #f6f8fa;
                    border-radius: 6px 6px 0px 0px;
                }
                QPushButton:checked {
                    color: #0969da;
                    border-bottom-color: #0969da;
                    background-color: transparent;
                }
            """)
            btn.clicked.connect(lambda checked, idx=index: self.content_stack.setCurrentIndex(idx))
            layout.addWidget(btn)
            self.tab_buttons.append(btn)
        
        # Select first tab
        self.tab_buttons[0].setChecked(True)
        
        layout.addStretch()
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #d0d7de;")
        separator.setFixedHeight(1)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(tab_bar)
        container_layout.addWidget(separator)
        
        return container
        
    def _create_notifications_tab(self) -> QWidget:
        """Create notifications list with cards (NOTIFICATIONS TAB)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        
        # Scroll area with custom scrollbar styling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f6f8fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #d0d7de;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #afb8c1;
            }
        """)
        
        # Container for notification cards
        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(12)
        self.notifications_layout.addStretch()
        
        scroll.setWidget(self.notifications_container)
        # Card container for list
        card = QFrame()
        card.setObjectName("notificationsCard")
        card.setStyleSheet("""
            QFrame#notificationsCard {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(0)
        card_layout.addWidget(scroll)

        layout.addWidget(card)
        
        return tab
        
    def _create_updates_tab(self) -> QWidget:
        """Create updates info tab with professional styling (UPDATES TAB)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        
        self.update_toast_label = QLabel("Update found")
        self.update_toast_label.setVisible(False)
        self.update_toast_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.update_toast_label.setFont(QFont('Segoe UI', 11, QFont.Weight.DemiBold))
        self.update_toast_label.setStyleSheet("""
            QLabel {
                background-color: #1f2937;
                color: #f9fafb;
                padding: 8px 12px;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.update_toast_label)

        # Current version card
        version_card = QFrame()
        version_card.setObjectName("versionCard")
        version_card.setStyleSheet("""
            QFrame#versionCard {
                background-color: #dafbe1;
                border: 1px solid #4ac26b;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        version_layout = QVBoxLayout(version_card)
        
        version_title = QLabel("✅ Current Version")
        version_title.setFont(QFont('Segoe UI', 14, QFont.Weight.DemiBold))
        version_title.setStyleSheet("color: #1a7f37;")
        version_layout.addWidget(version_title)
        
        from core.config_manager import ConfigManager
        config = ConfigManager()
        current_version = config.get('app.version', '1.0.0')
        
        version_label = QLabel(f"Water Balance Dashboard v{current_version}")
        version_label.setFont(QFont('Segoe UI', 16))
        version_label.setStyleSheet("color: #0d1117;")
        version_layout.addWidget(version_label)
        
        layout.addWidget(version_card)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 6, 0, 0)
        controls_layout.setSpacing(10)

        self.update_check_button = QPushButton("Check for updates")
        self.update_check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_check_button.setMinimumHeight(30)
        self.update_check_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self.update_check_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: 1px solid #1d4ed8;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                border-color: #94a3b8;
                color: #f1f5f9;
            }
        """)
        self.update_check_button.clicked.connect(self._on_check_updates_clicked)
        controls_layout.addWidget(self.update_check_button)

        self.update_download_button = QPushButton("Download update")
        self.update_download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_download_button.setMinimumHeight(30)
        self.update_download_button.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self.update_download_button.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: #ffffff;
                border: 1px solid #15803d;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                border-color: #94a3b8;
                color: #f1f5f9;
            }
        """)
        self.update_download_button.setVisible(False)
        self.update_download_button.clicked.connect(self._open_update_download)
        controls_layout.addWidget(self.update_download_button)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Updates placeholder
        self.update_status_label = QLabel("🔍 No updates available")
        self.update_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_status_label.setFont(QFont('Segoe UI', 13))
        self.update_status_label.setStyleSheet("""
            QLabel {
                color: #6e7781;
                padding: 60px 20px;
                background-color: #f6f8fa;
                border-radius: 8px;
            }
        """)
        self.update_status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self.update_status_label, 1)

        self._pending_update_url = None
        self._pending_update_info = None
        self._download_dialog = None
        self._install_prompt_shown = False
        self._update_toast_timer = QTimer(self)
        self._update_toast_timer.setSingleShot(True)
        self._update_toast_timer.timeout.connect(self.update_toast_label.hide)

        self._update_check_timeout = QTimer(self)
        self._update_check_timeout.setSingleShot(True)
        self._update_check_timeout.timeout.connect(self._on_update_check_timeout)
        
        return tab

    def _on_check_updates_clicked(self) -> None:
        """Run an on-demand update check and report results in the Updates tab."""
        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(False)
        if hasattr(self, "update_status_label"):
            self.update_status_label.setText("Checking for updates...")
        if hasattr(self, "update_download_button"):
            self.update_download_button.setVisible(False)
        self._pending_update_url = None
        if hasattr(self, "_update_check_timeout"):
            self._update_check_timeout.start(30000)

        def _worker():
            try:
                from services.update_service import get_update_service
                update = get_update_service().check_for_updates(force=True)
                QTimer.singleShot(0, self, lambda: self._on_update_check_finished(update))
            except Exception as exc:
                QTimer.singleShot(0, self, lambda: self._on_update_check_error(str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_check_finished(self, update_info) -> None:
        """Handle update check completion and refresh UI state."""
        if hasattr(self, "_update_check_timeout"):
            self._update_check_timeout.stop()
        if update_info:
            size_text = ""
            if update_info.file_size_mb:
                size_text = f" ({update_info.file_size_mb} MB)"
            self.update_status_label.setText(
                f"Update available: v{update_info.version}{size_text}"
            )
            self._pending_update_info = update_info
            self._pending_update_url = update_info.download_url
            self.update_download_button.setVisible(True)
            self._show_update_toast(f"Update available: v{update_info.version}")
        else:
            self.update_status_label.setText("🔍 No updates available")
            self._show_update_toast("No updates available")
            self._pending_update_info = None
            self._pending_update_url = None

        self.update_check_button.setEnabled(True)

    def _on_update_check_error(self, error_message: str) -> None:
        """Handle update check errors and restore UI state."""
        if hasattr(self, "_update_check_timeout"):
            self._update_check_timeout.stop()
        logger.warning("Update check failed: %s", error_message)
        self.update_status_label.setText("Update check failed. Try again.")
        self._show_update_toast("Update check failed", is_error=True)
        self.update_check_button.setEnabled(True)

    def _on_update_check_timeout(self) -> None:
        """Handle update checks that exceed the timeout window."""
        self.update_status_label.setText("Update check timed out. Try again.")
        self._show_update_toast("Update check timed out", is_error=True)
        self.update_check_button.setEnabled(True)

    def _open_update_download(self) -> None:
        """Download the available update and prompt to install."""
        if self._pending_update_info:
            self._start_update_download(self._pending_update_info)
            return
        if self._pending_update_url:
            QDesktopServices.openUrl(QUrl(self._pending_update_url))

    def _start_update_download(self, update_info) -> None:
        """Start downloading the update with progress feedback."""
        from services.update_service import get_update_service

        service = get_update_service()
        self._install_prompt_shown = False

        if self._download_dialog:
            self._download_dialog.close()

        self._download_dialog = QProgressDialog(
            "Downloading update...",
            "Cancel",
            0,
            100,
            self
        )
        self._download_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._download_dialog.setMinimumDuration(0)
        self._download_dialog.setValue(0)
        self._download_dialog.canceled.connect(service.cancel_download)
        self._download_dialog.show()

        try:
            service.update_progress.disconnect(self._on_update_download_progress)
        except Exception:
            pass
        try:
            service.update_failed.disconnect(self._on_update_download_failed)
        except Exception:
            pass

        service.update_progress.connect(self._on_update_download_progress)
        service.update_failed.connect(self._on_update_download_failed)
        service.download_update(update_info)

    def _on_update_download_progress(self, progress: int, message: str) -> None:
        """Update the progress dialog and prompt for install when ready."""
        if self._download_dialog:
            self._download_dialog.setLabelText(message)
            self._download_dialog.setValue(progress)

        if "ready to install" in message.lower() and not self._install_prompt_shown:
            self._install_prompt_shown = True
            self._prompt_install_downloaded_update()

    def _on_update_download_failed(self, error_message: str) -> None:
        """Handle download failures."""
        if self._download_dialog:
            self._download_dialog.close()
        QMessageBox.warning(self, "Update Download Failed", error_message)

    def _prompt_install_downloaded_update(self) -> None:
        """Prompt the user to install the downloaded update."""
        from services.update_service import get_update_service

        service = get_update_service()
        pending = service.check_pending_update()
        if not pending:
            return

        version = pending.get("version", "")
        installer_path = pending.get("installer_path", "")

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Update Ready")
        box.setText(f"Update {version} is ready to install.")
        box.setInformativeText("The app will close to complete the installation.")
        install_button = box.addButton("Install now", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        if box.clickedButton() == install_button:
            if service.install_update(installer_path):
                app = QApplication.instance()
                if app:
                    app.quit()

    def _show_update_toast(self, message: str, is_error: bool = False) -> None:
        """Show a transient toast-like notice in the Updates tab."""
        if is_error:
            self.update_toast_label.setStyleSheet("""
                QLabel {
                    background-color: #b91c1c;
                    color: #fff7ed;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
            """)
        else:
            self.update_toast_label.setStyleSheet("""
                QLabel {
                    background-color: #1f2937;
                    color: #f9fafb;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
            """)

        self.update_toast_label.setText(message)
        self.update_toast_label.setVisible(True)
        self._update_toast_timer.start(4000)
        
    def _create_feedback_tab(self) -> QWidget:
        """Create feedback submission tab with professional form (FEEDBACK TAB)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)
        
        # Form container card
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setStyleSheet("""
            QFrame#formCard {
                background-color: white;
                border: 1px solid #d0d7de;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(10)
        
        # Feedback type
        type_label = QLabel("Type")
        type_label.setFont(QFont('Segoe UI', 9, QFont.Weight.DemiBold))
        form_layout.addWidget(type_label)
        
        self.feedback_type = QComboBox()
        self.feedback_type.addItems(["🐛 Bug Report", "💡 Feature Request", "📝 General Feedback"])
        self.feedback_type.setFont(QFont('Segoe UI', 10))
        self.feedback_type.setFixedHeight(34)
        self.feedback_type.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #f6f8fa;
            }
            QComboBox:hover {
                border-color: #0969da;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        form_layout.addWidget(self.feedback_type)

        # Contact row
        contact_title = QLabel("Contact (optional)")
        contact_title.setFont(QFont('Segoe UI', 9, QFont.Weight.DemiBold))
        form_layout.addWidget(contact_title)

        contact_row = QHBoxLayout()
        contact_row.setSpacing(12)

        name_col = QVBoxLayout()
        name_label = QLabel("Name")
        name_label.setFont(QFont('Segoe UI', 8, QFont.Weight.DemiBold))
        name_label.setStyleSheet("color: #475569;")
        name_col.addWidget(name_label)

        self.feedback_name = QLineEdit()
        self.feedback_name.setPlaceholderText("Your name or company")
        self.feedback_name.setFont(QFont('Segoe UI', 9))
        self.feedback_name.setFixedHeight(32)
        self.feedback_name.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0969da;
                outline: none;
            }
        """)
        name_col.addWidget(self.feedback_name)

        email_col = QVBoxLayout()
        email_label = QLabel("Email")
        email_label.setFont(QFont('Segoe UI', 8, QFont.Weight.DemiBold))
        email_label.setStyleSheet("color: #475569;")
        email_col.addWidget(email_label)

        self.feedback_email = QLineEdit()
        self.feedback_email.setPlaceholderText("you@example.com")
        self.feedback_email.setFont(QFont('Segoe UI', 9))
        self.feedback_email.setFixedHeight(32)
        self.feedback_email.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0969da;
                outline: none;
            }
        """)
        email_col.addWidget(self.feedback_email)

        contact_row.addLayout(name_col, 1)
        contact_row.addLayout(email_col, 1)
        form_layout.addLayout(contact_row)

        # Title
        title_label = QLabel("Title")
        title_label.setFont(QFont('Segoe UI', 9, QFont.Weight.DemiBold))
        form_layout.addWidget(title_label)
        
        self.feedback_title = QLineEdit()
        self.feedback_title.setPlaceholderText("Brief summary of your feedback...")
        self.feedback_title.setFont(QFont('Segoe UI', 9))
        self.feedback_title.setFixedHeight(32)
        self.feedback_title.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0969da;
                outline: none;
            }
        """)
        form_layout.addWidget(self.feedback_title)

        # Description
        desc_label = QLabel("Description")
        desc_label.setFont(QFont('Segoe UI', 9, QFont.Weight.DemiBold))
        form_layout.addWidget(desc_label)
        
        self.feedback_body = QTextEdit()
        self.feedback_body.setPlaceholderText(
            "Please provide details about your feedback...\n\n"
            "• For bugs: Steps to reproduce, expected vs actual behavior\n"
            "• For features: Describe the feature and why it would be useful"
        )
        self.feedback_body.setFont(QFont('Segoe UI', 9))
        self.feedback_body.setMinimumHeight(96)
        self.feedback_body.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #0969da;
            }
        """)
        form_layout.addWidget(self.feedback_body, 1)

        # Submit button
        submit_row = QHBoxLayout()
        submit_row.addStretch()
        
        self.submit_btn = QPushButton("📤 Submit Feedback")
        self.submit_btn.setFont(QFont('Segoe UI', 9, QFont.Weight.DemiBold))
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setFixedHeight(30)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7f37;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #138636;
            }
            QPushButton:pressed {
                background-color: #0f6d2e;
            }
            QPushButton:disabled {
                background-color: #8c959f;
            }
        """)
        self.submit_btn.clicked.connect(self._submit_feedback)
        submit_row.addWidget(self.submit_btn)
        
        form_layout.addLayout(submit_row)

        content_row.addWidget(form_card, 1)

        layout.addLayout(content_row)
        layout.addStretch()
        
        return tab
        
    def _load_notifications(self):
        """Load notifications from service (DATA LOADING)."""
        logger.info("Loading notifications...")
        
        # Clear existing
        while self.notifications_layout.count() > 1:  # Keep stretch
            item = self.notifications_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            from services.notification_service import get_notification_service
            service = get_notification_service()
            
            # Get notifications
            notifications = service.get_cached_notifications()
            
            if not notifications:
                # Show professional placeholder
                placeholder = QLabel("📭 No notifications yet")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setFont(QFont('Segoe UI', 14))
                placeholder.setStyleSheet("""
                    QLabel {
                        color: #6e7781;
                        padding: 60px 20px;
                        background-color: #f6f8fa;
                        border-radius: 8px;
                    }
                """)
                self.notifications_layout.insertWidget(0, placeholder)
                self._unread_count = 0
                self.header_badge.set_count(0)
                return
            
            # Add notification cards
            unread_count = 0
            for notif_data in notifications:
                card = NotificationCard(notif_data)
                card.deleted.connect(self._on_notification_deleted)
                card.clicked.connect(self._on_notification_clicked)
                self.notifications_layout.insertWidget(self.notifications_layout.count() - 1, card)
                
                if not notif_data.get('is_read', False):
                    unread_count += 1
            
            self._unread_count = unread_count
            self.header_badge.set_count(unread_count)
            
            logger.info(f"Loaded {len(notifications)} notifications ({unread_count} unread)")
            
        except Exception as e:
            logger.exception(f"Failed to load notifications: {e}")
            error_label = QLabel(f"⚠️ Error loading notifications: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #cf222e; padding: 20px;")
            self.notifications_layout.insertWidget(0, error_label)
    
    def _on_notification_deleted(self, notification_id: str):
        """Handle notification deletion (DELETE ACTION)."""
        try:
            from services.notification_service import get_notification_service
            service = get_notification_service()
            
            # Hide locally for this device
            service.mark_as_deleted(notification_id)
            
            # Reload notifications
            self._load_notifications()
            
            logger.info(f"Notification {notification_id} deleted")
            
        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            QMessageBox.warning(self, "Delete Failed", "Could not delete notification.")
    
    def _on_notification_clicked(self, notification_data: dict):
        """Handle notification click (CLICK ACTION) - Opens drawer."""
        try:
            from services.notification_service import get_notification_service
            service = get_notification_service()
            
            # Mark as read
            notif_id = notification_data.get('id', '')
            if notif_id:
                service.mark_as_read(notif_id)
                self._load_notifications()  # Refresh to show as read
            
            # Show notification in drawer (slide-in panel)
            self.notification_drawer.show_notification(notification_data)
            self._open_drawer()
            
        except Exception as e:
            logger.error(f"Failed to handle notification click: {e}")
    
    def _submit_feedback(self):
        """Submit user feedback to Supabase (FEEDBACK SUBMISSION)."""
        feedback_type = self.feedback_type.currentText()
        title = self.feedback_title.text().strip()
        body = self.feedback_body.toPlainText().strip()
        customer_name = self.feedback_name.text().strip()
        email = self.feedback_email.text().strip() or None

        if email and not self._is_valid_email(email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a title for your feedback.")
            return
            
        if not body:
            QMessageBox.warning(self, "Missing Description", "Please describe your feedback.")
            return
        
        # Map display text to type code
        type_map = {
            "🐛 Bug Report": "bug",
            "💡 Feature Request": "feature",
            "📝 General Feedback": "general"
        }
        feedback_code = type_map.get(feedback_type, "general")
        
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Submitting...")
        
        try:
            from services.feedback_service import get_feedback_service
            service = get_feedback_service()
            
            success = service.submit_feedback(
                feedback_type=feedback_code,
                title=title,
                description=body,
                email=email,
                customer_name=customer_name
            )
            
            if success:
                QMessageBox.information(
                    self, 
                    "Feedback Submitted",
                    "Thank you for your feedback! We appreciate you taking the time to help improve the application."
                )
                self.feedback_title.clear()
                self.feedback_body.clear()
                self.feedback_type.setCurrentIndex(0)
                self.feedback_name.clear()
                self.feedback_email.clear()
            else:
                error_message = service.last_error or (
                    "Failed to submit feedback. Please check your internet connection and try again."
                )
                QMessageBox.warning(
                    self,
                    "Submission Failed",
                    error_message
                )
                
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while submitting feedback:\n{str(e)}"
            )
        finally:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("📤 Submit Feedback")
            
    def refresh(self):
        """Refresh the messages page (PUBLIC REFRESH METHOD)."""
        self._load_notifications()

    def _is_valid_email(self, email: str) -> bool:
        import re

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return bool(re.match(pattern, email))
