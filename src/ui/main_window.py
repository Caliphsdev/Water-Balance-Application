"""
Main window controller (application shell).

Purpose:
- Load the generated UI for the main window
- Wire up navigation buttons to switch pages in the central QStackedWidget
- Keep business logic out of generated files for maintainability

Notes:
- Generated UI lives in `ui/generated_ui_main_window.py` and should be
  recompiled from `ui/designer/main_window.ui` when the layout changes.
- Resources are compiled to `ui/resources/resources_rc.py` and imported
  once here so `:/icons/...` paths resolve application-wide.
"""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import Slot, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication

# Register compiled Qt resources (icons, images, fonts)
import ui.resources.resources_rc  # noqa: F401

from .generated_ui_main_window import Ui_MainWindow
from ui.dashboards.dashboard_dashboard import DashboardPage
from ui.dashboards.analytics_dashboard import AnalyticsPage
from ui.dashboards.monitoring_dashboard import MonitoringPage
from ui.dashboards.storage_facilities_dashboard import StorageFacilitiesPage
from ui.dashboards.calculation_dashboard import CalculationPage
from ui.dashboards.flow_diagram_page import FlowDiagramPage
from ui.dashboards.settings_dashboard import SettingsPage
from ui.dashboards.messages_dashboard import MessagesPage
from core.app_logger import logger as app_logger
from core.config_manager import ConfigManager
from services.environmental_data_service import get_environmental_data_service

logger = app_logger
from ui.dashboards.help_dashboard import HelpPage
from ui.dashboards.about_dashboard import AboutPage


class MainWindow(QMainWindow):
    """Main application window controller (UI shell).

    This controller owns high-level navigation and delegates
    to per-dashboard controllers/widgets loaded into the
    central `QStackedWidget`.

    Design guidelines:
    - Keep this class focused on navigation, window state, and status bar
    - Implement each dashboard/page as its own controller (e.g.,
      `ui/dashboards/calculations_dashboard.py`) and set them as pages
      of `self.ui.stackedWidget`
    - Do not modify generated UI classes directly
    """

    def __init__(self, splash=None, parent=None) -> None:
        super().__init__(parent)
        self.splash = splash
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._storage_facilities_page = None
        self._messages_page = None
        self._apply_window_sizing()
        self._setup_animations()
        self._set_initial_state()
        
        # Load all pages upfront (splash screen shows during this)
        self._mount_pages()
        self._connect_navigation()
        self._setup_notification_drawer()
        self._setup_status_bar()  # Setup status bar with license/network info
        self._set_default_page()  # Set Dashboard as the startup page
        
        # Enable resize event handling for responsive layout updates
        self.setWindowFlags(self.windowFlags())  # Ensure resize events are enabled

    def _connect_navigation(self) -> None:
        """Wire sidebar buttons to stacked widget pages.

        Assumes the generated UI contains `QPushButton`s with names
        matching navigation targets and a central `QStackedWidget`
        with corresponding page widgets created in Designer.
        """
        # Map buttons (icon-only and text+icon) to target page widgets
        nav_pairs = [
            (self.ui.dashboard_1, self.ui.dashboard),
            (self.ui.dashboard_2, self.ui.dashboard),
            (self.ui.analytics_1, self.ui.analytics_trends),
            (self.ui.analytics_2, self.ui.analytics_trends),
            (self.ui.monitoring_data_1, self.ui.monitoring_data),
            (self.ui.monitoring_data_2, self.ui.monitoring_data),
            (self.ui.storage_facilities_1, self.ui.storge_facilitites),
            (self.ui.storage_facilites_2, self.ui.storge_facilitites),
            (self.ui.calculations_1, self.ui.calculations),
            (self.ui.calculations_2, self.ui.calculations),
            (self.ui.flow_diagram_1, self.ui.flow_diagram),
            (self.ui.flow_diagram_2, self.ui.flow_diagram),
            (self.ui.settings_1, self.ui.settings),
            (self.ui.settings_2, self.ui.settings),
            (self.ui.help_1, self.ui.help),
            (self.ui.help_2, self.ui.help),
            (self.ui.about_1, self.ui.about),
            (self.ui.about_2, self.ui.about),
        ]

        for button, page in nav_pairs:
            button.clicked.connect(lambda _checked=False, p=page: self._show_page(p))

        # Messages page navigation (icon-only and text+icon buttons)
        if hasattr(self.ui, 'pushButton_messageicon') and self._messages_page:
            self.ui.pushButton_messageicon.clicked.connect(
                lambda: self._show_page(self._messages_page)
            )
        if hasattr(self.ui, 'message_iconandwords') and self._messages_page:
            self.ui.message_iconandwords.clicked.connect(
                lambda: self._show_page(self._messages_page)
            )

        # Menu (burger) toggles wide vs compact sidebar
        self.ui.pushButton_19.toggled.connect(self._toggle_sidebar)
        
        # Refresh button (in header) triggers current page refresh
        if hasattr(self.ui, 'referesh_button'):
            self.ui.referesh_button.clicked.connect(self._on_refresh_clicked)

    def _setup_animations(self) -> None:
        """Create smooth width animations for sidebar transitions."""
        # Animation for icon-only sidebar
        self.anim_icon_only = QPropertyAnimation(self.ui.icon_only, b"maximumWidth")
        self.anim_icon_only.setDuration(200)
        self.anim_icon_only.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Animation for icon+name sidebar
        self.anim_icon_name = QPropertyAnimation(self.ui.icon_name, b"maximumWidth")
        self.anim_icon_name.setDuration(200)
        self.anim_icon_name.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def _set_initial_state(self) -> None:
        """Set initial sidebar visibility (compact by default).
        
        On startup, show icon-only sidebar and hide the wide one.
        Burger button unchecked state = compact mode.
        
        Uses fixed widths to prevent layout jumping during transitions.
        """
        # Set fixed widths to prevent layout recalculation jumps
        self.ui.icon_only.setMaximumWidth(60)
        self.ui.icon_name.setMaximumWidth(220)
        
        # Start in compact mode
        self.ui.icon_only.setVisible(True)
        self.ui.icon_name.setVisible(False)
        self.ui.pushButton_19.setChecked(False)

    def _apply_window_sizing(self) -> None:
        """Apply responsive window sizing based on screen and config."""
        config = ConfigManager()
        geometry = config.get('window.geometry', '1400x900')
        min_width = int(config.get('window.min_width', 1200))
        min_height = int(config.get('window.min_height', 700))

        try:
            width_str, height_str = geometry.lower().split('x')
            width = int(width_str.strip())
            height = int(height_str.strip())
        except Exception:
            width, height = 1400, 900

        screen = QGuiApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            max_width = int(avail.width() * 0.95)
            max_height = int(avail.height() * 0.95)
            min_width = min(min_width, max_width)
            min_height = min(min_height, max_height)
            width = max(min(width, max_width), min_width)
            height = max(min(height, max_height), min_height)

        self.setMinimumSize(min_width, min_height)
        self.resize(width, height)

    def _setup_notification_drawer(self) -> None:
        """Set up notification drawer and bell button in header.
        
        Adds a notification bell button to the header toolbar that toggles
        a sliding notification drawer panel.
        """
        # TEMPORARILY DISABLED - investigating freeze issue
        logger.info("Notification drawer setup skipped (debugging)")
        self.notification_drawer = None
        return
        
        logger.info("Setting up notification drawer...")
        try:
            from ui.components.notification_drawer import NotificationDrawer, NotificationBadge
            logger.debug("Imported notification drawer components")
            
            # Create notification drawer (sliding panel)
            self.notification_drawer = NotificationDrawer(self)
            logger.debug("Created notification drawer")
            
            # Add drawer to the main layout (right side of central widget)
            # Find the main horizontal layout and add drawer
            central_layout = self.ui.centralwidget.layout()
            if central_layout:
                central_layout.addWidget(self.notification_drawer)
            
            # Create bell button for header
            self.notification_btn = QPushButton("🔔")
            self.notification_btn.setObjectName("notificationButton")
            self.notification_btn.setToolTip("Notifications")
            self.notification_btn.setFixedSize(36, 36)
            self.notification_btn.setStyleSheet("""
                QPushButton#notificationButton {
                    background-color: transparent;
                    border: none;
                    font-size: 18px;
                    border-radius: 4px;
                }
                QPushButton#notificationButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
            self.notification_btn.clicked.connect(self.notification_drawer.toggle)
            
            # Create badge overlay
            self.notification_badge = NotificationBadge(self.notification_btn)
            self.notification_badge.move(20, 0)
            
            # Add button to header (after refresh button)
            if hasattr(self.ui, 'horizontalLayout'):
                self.ui.horizontalLayout.addWidget(self.notification_btn)
            
            # Add feedback button to header
            self.feedback_btn = QPushButton("💬")
            self.feedback_btn.setObjectName("feedbackButton")
            self.feedback_btn.setToolTip("Send Feedback")
            self.feedback_btn.setFixedSize(36, 36)
            self.feedback_btn.setStyleSheet("""
                QPushButton#feedbackButton {
                    background-color: transparent;
                    border: none;
                    font-size: 18px;
                    border-radius: 4px;
                }
                QPushButton#feedbackButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
            self.feedback_btn.clicked.connect(self._show_feedback_dialog)
            
            if hasattr(self.ui, 'horizontalLayout'):
                self.ui.horizontalLayout.addWidget(self.feedback_btn)
            
            logger.info("Notification drawer initialized")
            
        except ImportError as e:
            logger.warning(f"Notification drawer not available: {e}")
            self.notification_drawer = None
        except Exception as e:
            logger.error(f"Failed to setup notification drawer: {e}")
            self.notification_drawer = None

    def _setup_status_bar(self) -> None:
        """Set up status bar with license info and network status (STATUS BAR SETUP).
        
        Adds the following widgets to the status bar:
        - License key icon + license type label (left side)
        - Network status icon (right side, permanent)
        
        The status bar cannot have widgets added via Qt Designer, so we add them programmatically.
        """
        logger.info("Setting up status bar widgets...")
        
        try:
            statusbar = self.ui.statusbar
            
            # === LEFT SIDE: License Info ===
            license_widget = QWidget()
            license_layout = QHBoxLayout(license_widget)
            license_layout.setContentsMargins(8, 2, 8, 2)
            license_layout.setSpacing(6)
            
            # License key icon
            self.license_icon = QLabel()
            license_pixmap = QIcon(":/icons/license-svgrepo-com.svg").pixmap(16, 16)
            self.license_icon.setPixmap(license_pixmap)
            self.license_icon.setToolTip("License Status")
            license_layout.addWidget(self.license_icon)
            
            # License type label
            self.license_label = QLabel("Loading...")
            self.license_label.setStyleSheet("""
                QLabel {
                    color: #424242;
                    font-size: 12px;
                    padding: 2px 4px;
                }
            """)
            license_layout.addWidget(self.license_label)
            
            statusbar.addWidget(license_widget)
            
            # === RIGHT SIDE (Permanent): Network Status ===
            network_widget = QWidget()
            network_layout = QHBoxLayout(network_widget)
            network_layout.setContentsMargins(8, 2, 8, 2)
            network_layout.setSpacing(4)
            
            # Network status icon
            self.network_icon = QLabel()
            # Set default icon (will be updated by network check)
            default_pixmap = QIcon(":/icons/network-wireless-svgrepo-com.svg").pixmap(16, 16)
            if not default_pixmap.isNull():
                self.network_icon.setPixmap(default_pixmap)
            else:
                logger.debug("Network icon resource not found")
            self.network_icon.setToolTip("Network Status")
            network_layout.addWidget(self.network_icon)
            
            # Network status label
            self.network_label = QLabel("Checking...")
            self.network_label.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-size: 11px;
                }
            """)
            network_layout.addWidget(self.network_label)
            
            statusbar.addPermanentWidget(network_widget)
            
            # Defer status updates to avoid blocking startup
            QTimer.singleShot(500, self._update_license_status)
            QTimer.singleShot(1000, self._update_network_status)
            
            # Set up periodic network check (every 30 seconds)
            self._network_check_timer = QTimer(self)
            self._network_check_timer.timeout.connect(self._update_network_status)
            self._network_check_timer.start(30000)  # 30 seconds
            
            logger.info("Status bar widgets initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup status bar: {e}")
    
    def _update_license_status(self) -> None:
        """Update license status display in status bar (LICENSE STATUS)."""
        try:
            from services.license_service import get_license_service
            license_service = get_license_service()
            
            license_info = license_service.get_license_info()
            
            if license_info and license_info.get('is_valid'):
                tier = license_info.get('tier', 'unknown').upper()
                status = license_info.get('status', 'active')
                
                # Color-code by tier
                tier_colors = {
                    'PROFESSIONAL': '#4CAF50',  # Green
                    'ENTERPRISE': '#2196F3',     # Blue  
                    'TRIAL': '#ff9800',          # Orange
                    'BASIC': '#9e9e9e',          # Gray
                }
                color = tier_colors.get(tier, '#757575')
                
                self.license_label.setText(f"{tier} License")
                self.license_label.setStyleSheet(f"""
                    QLabel {{
                        color: {color};
                        font-size: 12px;
                        font-weight: bold;
                        padding: 2px 6px;
                        background-color: {color}22;
                        border-radius: 4px;
                    }}
                """)
                self.license_label.setToolTip(f"License: {tier}\nStatus: {status}")
            else:
                self.license_label.setText("No License")
                self.license_label.setStyleSheet("""
                    QLabel {
                        color: #f44336;
                        font-size: 12px;
                        padding: 2px 4px;
                    }
                """)
                self.license_label.setToolTip("No valid license found")
                
        except Exception as e:
            logger.warning(f"Failed to update license status: {e}")
            self.license_label.setText("License: Unknown")
    
    def _update_network_status(self) -> None:
        """Update network status display in status bar (NETWORK STATUS).
        
        Uses QRunnable to avoid blocking the UI thread during network check.
        """
        logger.debug("Network status check requested")
        try:
            from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject
            
            class WorkerSignals(QObject):
                """Signals for worker thread."""
                result = Signal(bool)
            
            class NetworkCheckWorker(QRunnable):
                def __init__(self):
                    super().__init__()
                    self.signals = WorkerSignals()
                    
                def run(self):
                    import socket
                    try:
                        logger.debug("Network check: connecting to 8.8.8.8:53")
                        socket.create_connection(("8.8.8.8", 53), timeout=2)
                        is_online = True
                        logger.debug("Network check: online")
                    except (socket.timeout, socket.error, OSError) as e:
                        is_online = False
                        logger.debug(f"Network check: offline ({e})")
                    logger.debug(f"Network check: emitting result is_online={is_online}")
                    self.signals.result.emit(is_online)
            
            def update_ui(is_online):
                logger.debug(f"Network status UI update is_online={is_online}")
                try:
                    if is_online:
                        icon = QIcon(":/icons/network-wireless-svgrepo-com.svg")
                        logger.debug(f"Network icon isNull={icon.isNull()}, sizes={icon.availableSizes()}")
                        network_pixmap = icon.pixmap(16, 16)
                        logger.debug(
                            "Network pixmap isNull=%s width=%s height=%s",
                            network_pixmap.isNull(),
                            network_pixmap.width(),
                            network_pixmap.height(),
                        )
                        
                        if not network_pixmap.isNull():
                            self.network_icon.setPixmap(network_pixmap)
                            logger.debug("Network pixmap set successfully")
                        else:
                            # Fallback: Use text if icon fails
                            self.network_icon.setText("🟢")
                            logger.debug("Network icon fallback in use")
                        
                        self.network_label.setText("Online")
                        self.network_label.setStyleSheet("""
                            QLabel {
                                color: #4CAF50;
                                font-size: 11px;
                            }
                        """)
                        self.network_icon.setToolTip("Connected to network")
                        logger.debug("Network status updated to Online")
                    else:
                        icon = QIcon(":/icons/network-wireless-disabled-svgrepo-com.svg")
                        network_pixmap = icon.pixmap(16, 16)
                        
                        if not network_pixmap.isNull():
                            self.network_icon.setPixmap(network_pixmap)
                        else:
                            self.network_icon.setText("🔴")
                        
                        self.network_label.setText("Offline")
                        self.network_label.setStyleSheet("""
                            QLabel {
                                color: #f44336;
                                font-size: 11px;
                            }
                        """)
                        self.network_icon.setToolTip("No network connection")
                except Exception as ui_error:
                    logger.warning(f"Error updating network UI: {ui_error}")
            
            # Keep reference to worker to prevent garbage collection
            self._network_worker = NetworkCheckWorker()
            self._network_worker.signals.result.connect(update_ui)
            QThreadPool.globalInstance().start(self._network_worker)
                
        except Exception as e:
            logger.warning(f"Failed to check network status: {e}")
            self.network_label.setText("Unknown")

    def _set_default_page(self) -> None:
        """Set Dashboard page as the default startup page.
        
        Called after all pages are mounted to show Dashboard on app launch.
        """
        dashboard_index = self.ui.stackedWidget.indexOf(self.ui.dashboard)
        if dashboard_index >= 0:
            self.ui.stackedWidget.setCurrentIndex(dashboard_index)

    def _update_splash(self, message: str, progress: int):
        """Update splash screen status (HELPER)."""
        if self.splash:
            self.splash.update_status(message, progress)
            from PySide6.QtWidgets import QApplication
            QApplication.instance().processEvents()

    def _mount_pages(self) -> None:
        """Load dashboard controllers into stacked widget pages (DASHBOARD INITIALIZATION).
        
        Replaces Designer placeholder pages with live controller widgets.
        Called once during __init__ to populate all navigable pages.
        Updates splash screen progress as each page loads.
        
        Pattern:
        1. Create dashboard controller (e.g., DashboardPage())
        2. Find placeholder page in stacked widget by object name
        3. Replace placeholder's layout with controller
        
        This keeps business logic out of Designer and makes controllers reusable.
        """
        # Dashboard page (Water Balance KPIs overview)
        self._update_splash("Loading Dashboard...", 30)
        dashboard_page = DashboardPage()
        
        # Find the placeholder page from Designer by object name
        placeholder_index = self.ui.stackedWidget.indexOf(self.ui.dashboard)
        
        if placeholder_index >= 0:
            # Replace the placeholder page with our controller
            self.ui.stackedWidget.removeWidget(self.ui.dashboard)
            self.ui.stackedWidget.insertWidget(placeholder_index, dashboard_page)
            self.ui.dashboard = dashboard_page  # Update reference
            
            # Connect dashboard refresh signal to re-sync balance data
            dashboard_page.refresh_requested.connect(self._init_dashboard_data)
            
            # Initialize dashboard with current data (if flow diagram loads after)
            self._init_dashboard_data()
        
        # Analytics & Trends page
        self._update_splash("Loading Analytics...", 40)
        analytics_page = AnalyticsPage()
        analytics_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.analytics_trends)
        if analytics_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.analytics_trends)
            self.ui.stackedWidget.insertWidget(analytics_placeholder_index, analytics_page)
            self.ui.analytics_trends = analytics_page

        # Monitoring Data page
        self._update_splash("Loading Monitoring...", 50)
        monitoring_page = MonitoringPage()
        monitoring_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.monitoring_data)
        if monitoring_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.monitoring_data)
            self.ui.stackedWidget.insertWidget(monitoring_placeholder_index, monitoring_page)
            self.ui.monitoring_data = monitoring_page

        # Storage Facilities page (deferred to avoid startup stalls)
        self._update_splash("Loading Storage (deferred)...", 60)

        # Calculations page
        self._update_splash("Loading Calculations...", 70)
        calculations_page = CalculationPage()
        calculations_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.calculations)
        if calculations_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.calculations)
            self.ui.stackedWidget.insertWidget(calculations_placeholder_index, calculations_page)
            self.ui.calculations = calculations_page

        # Flow Diagram page
        self._update_splash("Loading Flow Diagram...", 80)
        flow_diagram_page = FlowDiagramPage()
        flow_diagram_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.flow_diagram)
        if flow_diagram_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.flow_diagram)
            self.ui.stackedWidget.insertWidget(flow_diagram_placeholder_index, flow_diagram_page)
            self.ui.flow_diagram = flow_diagram_page
            
            # Connect balance data updates to dashboard (REAL-TIME SYNC)
            flow_diagram_page.balance_data_updated.connect(self._on_balance_data_updated)
            
            # After all pages mounted, sync initial data to dashboard
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self._init_dashboard_data)

        # Settings page
        self._update_splash("Loading Settings...", 85)
        settings_page = SettingsPage()
        settings_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.settings)
        if settings_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.settings)
            self.ui.stackedWidget.insertWidget(settings_placeholder_index, settings_page)
            self.ui.settings = settings_page

        # Help page
        self._update_splash("Loading Help...", 90)
        help_page = HelpPage()
        help_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.help)
        if help_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.help)
            self.ui.stackedWidget.insertWidget(help_placeholder_index, help_page)
            self.ui.help = help_page

        # About page
        self._update_splash("Finalizing...", 95)
        about_page = AboutPage()
        about_placeholder_index = self.ui.stackedWidget.indexOf(self.ui.about)
        if about_placeholder_index >= 0:
            self.ui.stackedWidget.removeWidget(self.ui.about)
            self.ui.stackedWidget.insertWidget(about_placeholder_index, about_page)
            self.ui.about = about_page

        # Messages page (Inbox, Notifications, Feedback)
        # No placeholder in Designer - add dynamically to stacked widget
        self._update_splash("Loading Messages...", 98)
        self._messages_page = MessagesPage()
        self.ui.stackedWidget.addWidget(self._messages_page)
        self._update_splash("Pages loaded!", 99)
        logger.info("Messages page added to navigation")

    @Slot()
    def _toggle_sidebar(self, expanded: bool) -> None:
        """Animate sidebar transitions smoothly.
        
        Uses QPropertyAnimation on maximumWidth for fluid transitions.
        """
        if expanded:
            # Animate to wide mode
            self.ui.icon_only.setVisible(False)
            self.ui.icon_name.setVisible(True)
            self.anim_icon_name.setStartValue(0)
            self.anim_icon_name.setEndValue(220)
            self.anim_icon_name.start()
        else:
            # Animate to compact mode
            self.ui.icon_name.setVisible(False)
            self.ui.icon_only.setVisible(True)
            self.anim_icon_only.setStartValue(0)
            self.anim_icon_only.setEndValue(60)
            self.anim_icon_only.start()

    @Slot()
    def _show_page(self, page_widget) -> None:
        """Switch to the given page on the central stacked widget.
        
        All pages are pre-loaded during startup, so navigation is instant.
        """
        if page_widget == self.ui.storge_facilitites:
            page_widget = self._ensure_storage_facilities_page()
        elif page_widget is not None and getattr(page_widget, "objectName", lambda: "")() == "storge_facilitites":
            page_widget = self._ensure_storage_facilities_page()

        index = self.ui.stackedWidget.indexOf(page_widget)
        if index < 0 and self._storage_facilities_page is not None:
            if page_widget is not None and getattr(page_widget, "objectName", lambda: "")() == "storge_facilitites":
                page_widget = self._storage_facilities_page
                index = self.ui.stackedWidget.indexOf(page_widget)
        if index >= 0:
            self.ui.stackedWidget.setCurrentIndex(index)
    
    @Slot()
    def _show_feedback_dialog(self):
        """Show the feedback dialog for bug reports and feature requests."""
        try:
            from ui.dialogs.feedback_dialog import FeedbackDialog
            from core.config_manager import ConfigManager
            
            config = ConfigManager()
            app_version = config.get('app.version', '1.0.0')
            
            dialog = FeedbackDialog(self, app_version=app_version)
            dialog.exec()
        except ImportError as e:
            logger.warning(f"Feedback dialog not available: {e}")
        except Exception as e:
            logger.error(f"Failed to show feedback dialog: {e}")
    
    @Slot()
    def _on_refresh_clicked(self):
        """Handle Refresh button click (GLOBAL REFRESH ACTION).
        
        Refreshes the current page based on what's visible:
        - Dashboard: Reload all KPIs from database
        - Storage Facilities: Reload facilities list
        - Monitoring: Reload data from Excel
        - etc.
        
        Also re-syncs dashboard with flow diagram balance data.
        """
        current_page = self.ui.stackedWidget.currentWidget()
        
        # Refresh the current page if it has a refresh method
        if hasattr(current_page, 'refresh'):
            logger.info(f"Refreshing current page: {current_page.__class__.__name__}")
            current_page.refresh()
        
        # Always refresh dashboard KPIs if it's the current page
        if current_page == self.ui.dashboard:
            self._init_dashboard_data()  # Also sync balance data from flow diagram
        
        logger.debug("Global refresh completed")
    
    def _init_dashboard_data(self):
        """Initialize dashboard with data from flow diagram and database (STARTUP DATA SYNC).
        
        Pulls initial balance data from flow diagram and environmental data from database.
        Called after flow diagram page is loaded and connected.
        """
        try:
            # Get balance data from flow diagram if available
            dashboard_data = {}
            
            if hasattr(self.ui, 'flow_diagram') and hasattr(self.ui.flow_diagram, 'get_balance_summary'):
                balance_data = self.ui.flow_diagram.get_balance_summary()
                dashboard_data.update(balance_data)
            
            # Get environmental data (rainfall, evaporation) from database
            try:
                env_service = get_environmental_data_service()
                month = dashboard_data.get('month')
                year = dashboard_data.get('year')
                
                if month and year:
                    # get_rainfall/get_evaporation return default 0.0 if not found
                    rainfall = env_service.get_rainfall(year, month, default=None)
                    evaporation = env_service.get_evaporation(year, month, default=None)
                    
                    # Only add to dashboard if data exists (not None)
                    if rainfall is not None:
                        dashboard_data['rainfall'] = rainfall
                        logger.debug(f"Rainfall loaded: {rainfall:.1f}mm")
                    else:
                        logger.debug(f"No rainfall data for {year}-{month:02d}")
                    
                    if evaporation is not None:
                        dashboard_data['evaporation'] = evaporation
                        logger.debug(f"Evaporation loaded: {evaporation:.1f}mm")
                    else:
                        logger.debug(f"No evaporation data for {year}-{month:02d}")
            except Exception as e:
                logger.warning(f"Could not load environmental data: {e}")
            
            # Update dashboard with all data
            if hasattr(self.ui, 'dashboard') and hasattr(self.ui.dashboard, 'update_data'):
                self.ui.dashboard.update_data(dashboard_data)
                logger.debug(f"Dashboard initialized with data: {dashboard_data}")
        except Exception as e:
            logger.error(f"Error initializing dashboard data: {e}", exc_info=True)
    
    def _on_balance_data_updated(self, balance_data: dict):
        """Handle balance data updates from flow diagram (CROSS-PAGE SYNC).
        
        Updates the main dashboard with latest balance calculations and environmental data.
        Called when flow diagram recalculates balance (after Load Excel, Balance Check, etc.)
        
        Args:
            balance_data: Dict with keys: total_inflows, total_outflows, recirculation, balance_error, month, year
        """
        try:
            # Start with balance data
            dashboard_data = balance_data.copy()
            
            # Get environmental data for the selected month/year
            try:
                env_service = get_environmental_data_service()
                month = balance_data.get('month')
                year = balance_data.get('year')
                
                if month and year:
                    # Get rainfall and evaporation - will return None if not found in database
                    rainfall = env_service.get_rainfall(year, month, default=None)
                    evaporation = env_service.get_evaporation(year, month, default=None)
                    
                    # Only add to dashboard if data exists
                    if rainfall is not None:
                        dashboard_data['rainfall'] = rainfall
                    if evaporation is not None:
                        dashboard_data['evaporation'] = evaporation
                    
                    logger.debug(f"Environmental data: Rainfall={rainfall}, Evaporation={evaporation}")
            except Exception as e:
                logger.warning(f"Could not load environmental data: {e}")
            
            # Update dashboard with combined data
            if hasattr(self.ui, 'dashboard') and hasattr(self.ui.dashboard, 'update_data'):
                self.ui.dashboard.update_data(dashboard_data)
                logger.debug(f"Dashboard updated with balance data: {dashboard_data}")
        except Exception as e:
            logger.error(f"Error updating dashboard with balance data: {e}", exc_info=True)

    def _ensure_storage_facilities_page(self):
        """Lazily initialize Storage Facilities page on first navigation.

        This avoids blocking the splash screen during startup when the
        storage facilities service performs schema checks or DB access.

        Returns:
            QWidget: Live StorageFacilitiesPage instance or the placeholder
            widget if initialization fails.
        """
        if self._storage_facilities_page is not None:
            return self._storage_facilities_page

        try:
            storage_facilities_page = StorageFacilitiesPage()
            placeholder_index = self.ui.stackedWidget.indexOf(
                self.ui.storge_facilitites
            )
            if placeholder_index >= 0:
                self.ui.stackedWidget.removeWidget(self.ui.storge_facilitites)
                self.ui.stackedWidget.insertWidget(
                    placeholder_index, storage_facilities_page
                )
                self.ui.storge_facilitites = storage_facilities_page
            self._storage_facilities_page = storage_facilities_page
            return storage_facilities_page
        except Exception as exc:
            logger.error(
                "Failed to load Storage Facilities page on demand",
                exc_info=True,
            )
            return self.ui.storge_facilitites

    def closeEvent(self, event) -> None:
        """Handle window close - always shut down the application.

        The close button (X) always closes the app completely.
        
        Close sequence:
        1. Call stop_background_tasks() on each dashboard (requests cancellation)
        2. Process events to allow threads to finish gracefully
        3. Accept the close event and exit
        """
        from PySide6.QtWidgets import QApplication
        
        logger.info("Application close requested - shutting down...")
        
        # Full shutdown - stop background workers
        pages = [
            getattr(self.ui, "monitoring_data", None),
            getattr(self.ui, "analytics_trends", None),
            getattr(self.ui, "storge_facilitites", None),
        ]

        # Request all threads to stop
        for page in pages:
            if page and hasattr(page, "stop_background_tasks"):
                try:
                    page.stop_background_tasks()
                except Exception as e:
                    logger.warning(f"Error stopping tasks on page: {e}")

        # Give threads time to finish gracefully
        app = QApplication.instance()
        if app:
            app.processEvents()

        # Accept the close event to allow the application to shut down
        event.accept()
    
    def resizeEvent(self, event) -> None:
        """Handle window resize events (RESPONSIVE LAYOUT).
        
        Triggers font rescaling in dashboard page when window is resized
        to ensure fonts remain proportional at all window sizes.
        """
        super().resizeEvent(event)
        
        # Trigger font rescaling on the current dashboard page if it supports it
        if self.ui.stackedWidget:
            current_page = self.ui.stackedWidget.currentWidget()
            if current_page and hasattr(current_page, '_apply_dynamic_font_scaling'):
                # Use QTimer to defer rescaling to next event loop (prevents resize lag)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(50, current_page._apply_dynamic_font_scaling)
    
    def changeEvent(self, event) -> None:
        """Handle window state changes (WINDOW STATE HANDLING).
        
        Currently just passes through - close button always closes the app.
        """
        from PySide6.QtCore import Qt
        
        # Don't minimize to tray - let the close button work normally
        super().changeEvent(event)
