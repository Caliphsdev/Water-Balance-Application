"""
Messages Dashboard - Professional Redesign

Complete redesign following desktop-design skill principles.
Features: Professional cards, delete functionality, notification badge, styled tabs.

(MODULE OVERVIEW)
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QStackedWidget, QComboBox, QLineEdit,
    QTextEdit, QMessageBox, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont, QColor

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
        message = notification_data.get('message', '')
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
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)
        
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
        
        # Updates placeholder
        placeholder = QLabel("🔍 No updates available")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(QFont('Segoe UI', 13))
        placeholder.setStyleSheet("""
            QLabel {
                color: #6e7781;
                padding: 60px 20px;
                background-color: #f6f8fa;
                border-radius: 8px;
            }
        """)
        layout.addWidget(placeholder, 1)
        
        return tab
        
    def _create_feedback_tab(self) -> QWidget:
        """Create feedback submission tab with professional form (FEEDBACK TAB)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)

        header_card = QFrame()
        header_card.setObjectName("feedbackHeader")
        header_card.setStyleSheet("""
            QFrame#feedbackHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 10px;
                padding: 18px 22px;
            }
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 16, 20, 16)

        header_stack = QVBoxLayout()
        header_stack.setSpacing(4)
        header_title = QLabel("Feedback & Requests")
        header_title.setFont(QFont('Segoe UI Variable', 18, QFont.Weight.DemiBold))
        header_title.setStyleSheet("color: #f8fafc;")
        header_stack.addWidget(header_title)

        header_subtitle = QLabel("Help us improve Water Balance with clear, actionable feedback.")
        header_subtitle.setFont(QFont('Segoe UI', 11))
        header_subtitle.setStyleSheet("color: #cbd5f5;")
        header_stack.addWidget(header_subtitle)
        header_layout.addLayout(header_stack)
        header_layout.addStretch()

        header_note = QLabel("Typical response: 1-2 business days")
        header_note.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        header_note.setStyleSheet(
            "color: #e2e8f0; border: 1px solid #475569; padding: 6px 10px; border-radius: 6px;"
        )
        header_layout.addWidget(header_note)

        layout.addWidget(header_card)

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
                padding: 24px;
            }
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(16)
        
        # Feedback type
        type_label = QLabel("Feedback Type")
        type_label.setFont(QFont('Segoe UI', 11, QFont.Weight.DemiBold))
        form_layout.addWidget(type_label)
        
        self.feedback_type = QComboBox()
        self.feedback_type.addItems(["🐛 Bug Report", "💡 Feature Request", "📝 General Feedback"])
        self.feedback_type.setFont(QFont('Segoe UI', 11))
        self.feedback_type.setFixedHeight(36)
        self.feedback_type.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
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

        type_hint = QLabel("Choose the category that best matches your request.")
        type_hint.setFont(QFont('Segoe UI', 9))
        type_hint.setStyleSheet("color: #6e7781;")
        form_layout.addWidget(type_hint)

        # Contact row
        contact_title = QLabel("Contact (optional)")
        contact_title.setFont(QFont('Segoe UI', 11, QFont.Weight.DemiBold))
        form_layout.addWidget(contact_title)

        contact_row = QHBoxLayout()
        contact_row.setSpacing(12)

        name_col = QVBoxLayout()
        name_label = QLabel("Customer Name")
        name_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        name_col.addWidget(name_label)

        self.feedback_name = QLineEdit()
        self.feedback_name.setPlaceholderText("Your name or company")
        self.feedback_name.setFont(QFont('Segoe UI', 11))
        self.feedback_name.setFixedHeight(36)
        self.feedback_name.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
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
        email_label = QLabel("Email (optional)")
        email_label.setFont(QFont('Segoe UI', 10, QFont.Weight.DemiBold))
        email_col.addWidget(email_label)

        self.feedback_email = QLineEdit()
        self.feedback_email.setPlaceholderText("you@example.com")
        self.feedback_email.setFont(QFont('Segoe UI', 11))
        self.feedback_email.setFixedHeight(36)
        self.feedback_email.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
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

        contact_hint = QLabel("Include an email if you want updates or follow-ups.")
        contact_hint.setFont(QFont('Segoe UI', 9))
        contact_hint.setStyleSheet("color: #6e7781;")
        form_layout.addWidget(contact_hint)
        
        # Title
        title_label = QLabel("Title")
        title_label.setFont(QFont('Segoe UI', 11, QFont.Weight.DemiBold))
        form_layout.addWidget(title_label)
        
        self.feedback_title = QLineEdit()
        self.feedback_title.setPlaceholderText("Brief summary of your feedback...")
        self.feedback_title.setFont(QFont('Segoe UI', 11))
        self.feedback_title.setFixedHeight(36)
        self.feedback_title.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
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

        title_hint = QLabel("Keep it short. Example: \"Flow chart export freezes\"")
        title_hint.setFont(QFont('Segoe UI', 9))
        title_hint.setStyleSheet("color: #6e7781;")
        form_layout.addWidget(title_hint)
        
        # Description
        desc_label = QLabel("Description")
        desc_label.setFont(QFont('Segoe UI', 11, QFont.Weight.DemiBold))
        form_layout.addWidget(desc_label)
        
        self.feedback_body = QTextEdit()
        self.feedback_body.setPlaceholderText(
            "Please provide details about your feedback...\n\n"
            "• For bugs: Steps to reproduce, expected vs actual behavior\n"
            "• For features: Describe the feature and why it would be useful"
        )
        self.feedback_body.setFont(QFont('Segoe UI', 11))
        self.feedback_body.setMinimumHeight(150)
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

        body_hint = QLabel("Attach key steps, expected result, and actual result where possible.")
        body_hint.setFont(QFont('Segoe UI', 9))
        body_hint.setStyleSheet("color: #6e7781;")
        form_layout.addWidget(body_hint)
        
        # Submit button
        submit_row = QHBoxLayout()
        submit_row.addStretch()
        
        self.submit_btn = QPushButton("📤 Submit Feedback")
        self.submit_btn.setFont(QFont('Segoe UI', 11, QFont.Weight.DemiBold))
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setFixedHeight(40)
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

        # Drawer panel
        drawer = QFrame()
        drawer.setObjectName("feedbackDrawer")
        drawer.setFixedWidth(260)
        drawer.setStyleSheet("""
            QFrame#feedbackDrawer {
                background-color: #0f172a;
                border-radius: 10px;
                padding: 18px;
            }
        """)
        drawer_layout = QVBoxLayout(drawer)
        drawer_layout.setSpacing(14)

        drawer_header = QHBoxLayout()
        drawer_header.setContentsMargins(0, 0, 0, 0)

        drawer_title = QLabel("Feedback Guide")
        drawer_title.setFont(QFont('Segoe UI', 12, QFont.Weight.DemiBold))
        drawer_title.setStyleSheet("color: #e2e8f0;")
        drawer_header.addWidget(drawer_title)
        drawer_header.addStretch()

        self.drawer_toggle = QPushButton("Hide")
        self.drawer_toggle.setFixedHeight(26)
        self.drawer_toggle.setStyleSheet("""
            QPushButton {
                color: #cbd5f5;
                background-color: transparent;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 2px 10px;
            }
            QPushButton:hover {
                border-color: #93c5fd;
                color: #e2e8f0;
            }
        """)
        drawer_header.addWidget(self.drawer_toggle)
        drawer_layout.addLayout(drawer_header)

        drawer_body = QLabel(
            "• Describe the issue clearly\n"
            "• Include steps to reproduce\n"
            "• Add expected vs actual results\n"
            "• Mention data or screen name"
        )
        drawer_body.setStyleSheet("color: #cbd5f5; line-height: 1.4;")
        drawer_body.setWordWrap(True)
        drawer_layout.addWidget(drawer_body)

        drawer_note = QLabel("Support replies go to the email you provide.")
        drawer_note.setStyleSheet("color: #94a3b8; font-size: 10px;")
        drawer_note.setWordWrap(True)
        drawer_layout.addWidget(drawer_note)

        drawer_layout.addStretch()

        content_row.addWidget(form_card, 3)
        content_row.addWidget(drawer, 1)

        self._feedback_drawer = drawer
        self.drawer_toggle.clicked.connect(self._toggle_feedback_drawer)

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
                QMessageBox.warning(
                    self,
                    "Submission Failed",
                    "Failed to submit feedback. Please check your internet connection and try again."
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

    def _toggle_feedback_drawer(self) -> None:
        if not hasattr(self, "_feedback_drawer"):
            return
        is_visible = self._feedback_drawer.isVisible()
        self._feedback_drawer.setVisible(not is_visible)
        self.drawer_toggle.setText("Show" if is_visible else "Hide")

    def _is_valid_email(self, email: str) -> bool:
        import re

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return bool(re.match(pattern, email))
