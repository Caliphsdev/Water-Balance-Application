"""
Notification Drawer Component

A sliding drawer panel that displays notifications with cards.
Follows the email drawer pattern from DOCUMENTATION.md.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from typing import Optional, List

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont

from services.notification_service import (
    get_notification_service, 
    Notification,
    NotificationService
)

logger = logging.getLogger(__name__)


# (STYLES)

NOTIFICATION_DRAWER_STYLE = """
QFrame#notificationDrawer {
    background-color: #16213e;
    border-left: 1px solid #30363d;
}

QFrame#drawerHeader {
    background-color: #1a1a2e;
    border-bottom: 1px solid #30363d;
    padding: 12px 16px;
}

QLabel#drawerTitle {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
}

QPushButton#closeButton {
    background-color: transparent;
    border: none;
    color: #8892a0;
    font-size: 18px;
    padding: 4px 8px;
    border-radius: 4px;
}

QPushButton#closeButton:hover {
    background-color: #21262d;
    color: #ffffff;
}

QPushButton#markAllReadButton {
    background-color: transparent;
    border: 1px solid #30363d;
    color: #8892a0;
    font-size: 11px;
    padding: 6px 12px;
    border-radius: 4px;
}

QPushButton#markAllReadButton:hover {
    background-color: #21262d;
    border-color: #8892a0;
}

QScrollArea#notificationScrollArea {
    background-color: transparent;
    border: none;
}

QWidget#notificationList {
    background-color: transparent;
}

QFrame#notificationCard {
    background-color: #0f3460;
    border-radius: 8px;
    padding: 12px;
    margin: 4px 8px;
}

QFrame#notificationCard:hover {
    background-color: #1a4070;
}

QFrame#notificationCard[read="true"] {
    background-color: #0d1117;
}

QFrame#notificationCard[read="true"]:hover {
    background-color: #161b22;
}

QLabel#notificationIcon {
    font-size: 20px;
}

QLabel#notificationTitle {
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#notificationBody {
    font-size: 12px;
    color: #8892a0;
}

QLabel#notificationTime {
    font-size: 10px;
    color: #6e7681;
}

QLabel#newBadge {
    background-color: #238636;
    color: #ffffff;
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
}

QLabel#emptyLabel {
    color: #6e7681;
    font-size: 13px;
}
"""


# (NOTIFICATION CARD)

class NotificationCard(QFrame):
    """
    Card widget displaying a single notification.
    
    Shows icon, title, body preview, time, and NEW badge if unread.
    """
    
    clicked = Signal(str)  # notification_id
    
    def __init__(self, notification: Notification, parent=None):
        super().__init__(parent)
        self.notification = notification
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the card UI."""
        self.setObjectName("notificationCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("read", "true" if self.notification.is_read else "false")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(self.notification.type_icon)
        icon_label.setObjectName("notificationIcon")
        icon_label.setFixedWidth(28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        
        title_label = QLabel(self.notification.title)
        title_label.setObjectName("notificationTitle")
        title_label.setWordWrap(True)
        title_row.addWidget(title_label, 1)
        
        # NEW badge
        if self.notification.is_new:
            self.new_badge = QLabel("NEW")
            self.new_badge.setObjectName("newBadge")
            title_row.addWidget(self.new_badge)
        else:
            self.new_badge = None
        
        content_layout.addLayout(title_row)
        
        # Body preview (truncated)
        body_text = self.notification.body
        if len(body_text) > 100:
            body_text = body_text[:100] + "..."
        
        body_label = QLabel(body_text)
        body_label.setObjectName("notificationBody")
        body_label.setWordWrap(True)
        content_layout.addWidget(body_label)
        
        # Time
        time_label = QLabel(self.notification.age_display)
        time_label.setObjectName("notificationTime")
        content_layout.addWidget(time_label)
        
        layout.addLayout(content_layout, 1)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.notification.id)
        super().mousePressEvent(event)
    
    def mark_as_read(self):
        """Update visual state to read."""
        self.setProperty("read", "true")
        self.style().unpolish(self)
        self.style().polish(self)
        
        if self.new_badge:
            self.new_badge.hide()


# (NOTIFICATION DRAWER)

class NotificationDrawer(QFrame):
    """
    Sliding drawer panel for notifications.
    
    Features:
    - Animated slide-in/out from right
    - Scrollable notification list
    - Mark all as read button
    - Auto-sync with NotificationService
    """
    
    close_requested = Signal()
    notification_selected = Signal(str)  # notification_id
    
    # Drawer dimensions
    DRAWER_WIDTH = 380
    ANIMATION_DURATION = 300
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._service: Optional[NotificationService] = None
        self._cards: dict = {}  # id -> NotificationCard
        self._is_open = False
        
        self._setup_ui()
        self._setup_animations()
        self._connect_service()
    
    def _setup_ui(self):
        """Set up the drawer UI."""
        self.setObjectName("notificationDrawer")
        self.setStyleSheet(NOTIFICATION_DRAWER_STYLE)
        self.setFixedWidth(0)  # Start collapsed
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setObjectName("drawerHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 12, 12)
        
        title = QLabel("Notifications")
        title.setObjectName("drawerTitle")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Mark all read button
        self.mark_all_btn = QPushButton("Mark all read")
        self.mark_all_btn.setObjectName("markAllReadButton")
        self.mark_all_btn.clicked.connect(self._on_mark_all_read)
        header_layout.addWidget(self.mark_all_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setObjectName("notificationScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Notification list container
        self.list_widget = QWidget()
        self.list_widget.setObjectName("notificationList")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        
        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)
        
        # Empty state
        self.empty_label = QLabel("No notifications")
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        self.list_layout.insertWidget(0, self.empty_label)
    
    def _setup_animations(self):
        """Set up slide animations."""
        self._min_animation = QPropertyAnimation(self, b"minimumWidth")
        self._min_animation.setDuration(self.ANIMATION_DURATION)
        self._min_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._max_animation = QPropertyAnimation(self, b"maximumWidth")
        self._max_animation.setDuration(self.ANIMATION_DURATION)
        self._max_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _connect_service(self):
        """Connect to notification service."""
        self._service = get_notification_service()
        self._service.notifications_updated.connect(self._on_notifications_updated)
        self._service.new_notification.connect(self._on_new_notification)
    
    # (ANIMATION)
    
    def open(self):
        """Open the drawer with animation."""
        if self._is_open:
            return
        
        self._is_open = True
        
        self._min_animation.setStartValue(0)
        self._min_animation.setEndValue(self.DRAWER_WIDTH)
        
        self._max_animation.setStartValue(0)
        self._max_animation.setEndValue(self.DRAWER_WIDTH)
        
        self._min_animation.start()
        self._max_animation.start()
        
        # Refresh notifications
        self._refresh_list()
    
    def close(self):
        """Close the drawer with animation."""
        if not self._is_open:
            return
        
        self._is_open = False
        
        self._min_animation.setStartValue(self.DRAWER_WIDTH)
        self._min_animation.setEndValue(0)
        
        self._max_animation.setStartValue(self.DRAWER_WIDTH)
        self._max_animation.setEndValue(0)
        
        self._min_animation.start()
        self._max_animation.start()
    
    def toggle(self):
        """Toggle drawer open/close."""
        if self._is_open:
            self.close()
        else:
            self.open()
    
    @property
    def is_open(self) -> bool:
        """Check if drawer is open."""
        return self._is_open
    
    # (CONTENT)
    
    def _refresh_list(self):
        """Refresh the notification list."""
        # Clear existing cards
        for card in self._cards.values():
            card.deleteLater()
        self._cards.clear()
        
        # Remove all widgets except empty label and stretch
        while self.list_layout.count() > 2:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get notifications
        notifications = self._service.notifications if self._service else []
        
        # Show empty state if no notifications
        if not notifications:
            self.empty_label.show()
            self.mark_all_btn.setEnabled(False)
            return
        
        self.empty_label.hide()
        self.mark_all_btn.setEnabled(self._service.unread_count > 0 if self._service else False)
        
        # Add notification cards
        for i, notif in enumerate(notifications):
            card = NotificationCard(notif)
            card.clicked.connect(self._on_card_clicked)
            
            self._cards[notif.id] = card
            self.list_layout.insertWidget(i, card)
    
    def _on_notifications_updated(self, notifications: List[Notification]):
        """Handle notifications update."""
        if self._is_open:
            self._refresh_list()
    
    def _on_new_notification(self, notification: Notification):
        """Handle new notification received."""
        # Could show a subtle indicator or auto-refresh
        if self._is_open:
            self._refresh_list()
    
    # (ACTIONS)
    
    def _on_close(self):
        """Handle close button click."""
        self.close()
        self.close_requested.emit()
    
    def _on_card_clicked(self, notification_id: str):
        """Handle notification card click."""
        # Mark as read
        if self._service:
            self._service.mark_as_read(notification_id)
        
        # Update card visual
        if notification_id in self._cards:
            self._cards[notification_id].mark_as_read()
        
        # Update mark all button
        self.mark_all_btn.setEnabled(self._service.unread_count > 0 if self._service else False)
        
        self.notification_selected.emit(notification_id)
    
    def _on_mark_all_read(self):
        """Handle mark all as read."""
        if self._service:
            self._service.mark_all_as_read()
            
            # Update all cards
            for card in self._cards.values():
                card.mark_as_read()
            
            self.mark_all_btn.setEnabled(False)


# (NOTIFICATION BADGE)

class NotificationBadge(QLabel):
    """
    Badge showing unread notification count.
    
    Displays as a small red circle with white number.
    Hides automatically when count is 0.
    """
    
    BADGE_STYLE = """
    QLabel#notificationBadge {
        background-color: #f85149;
        color: #ffffff;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 5px;
        border-radius: 8px;
        min-width: 16px;
    }
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notificationBadge")
        self.setStyleSheet(self.BADGE_STYLE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        
        # Connect to service
        self._service = get_notification_service()
        self._service.unread_count_changed.connect(self.set_count)
        
        # Initial count
        self.set_count(self._service.unread_count)
    
    def set_count(self, count: int):
        """
        Set the badge count.
        
        Args:
            count: Number to display. Hidden if 0.
        """
        if count <= 0:
            self.hide()
        else:
            self.setText(str(min(count, 99)) if count < 100 else "99+")
            self.show()


# (MODULE TEST)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Create test window
    window = QMainWindow()
    window.setWindowTitle("Notification Drawer Test")
    window.resize(1000, 600)
    
    central = QWidget()
    layout = QHBoxLayout(central)
    
    # Main content
    content = QLabel("Main Content Area")
    content.setStyleSheet("background-color: #1a1a2e; color: white; font-size: 24px;")
    content.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(content, 1)
    
    # Drawer
    drawer = NotificationDrawer()
    layout.addWidget(drawer)
    
    window.setCentralWidget(central)
    
    # Toggle button in toolbar
    toolbar = window.addToolBar("Test")
    toggle_action = toolbar.addAction("🔔 Toggle Drawer")
    toggle_action.triggered.connect(drawer.toggle)
    
    window.show()
    
    sys.exit(app.exec())
