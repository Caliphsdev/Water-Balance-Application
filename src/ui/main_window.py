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

import threading

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget,
    QMessageBox, QProgressDialog, QApplication
)
from PySide6.QtCore import (
    Slot,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QUrl,
    Qt,
    QParallelAnimationGroup,
    QAbstractAnimation,
    QObject,
    Signal,
    QRunnable,
    QThreadPool,
)
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication, QDesktopServices

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
from core.config_manager import ConfigManager, get_resource_path
from services.environmental_data_service import get_environmental_data_service

logger = app_logger
from ui.dashboards.help_dashboard import HelpPage
from ui.dashboards.about_dashboard import AboutPage


class _LicenseValidationSignals(QObject):
    """Signals emitted by background runtime license checks."""

    result = Signal(object, float, str)


class _LicenseValidationWorker(QRunnable):
    """Run license validation off the UI thread."""

    def __init__(self):
        super().__init__()
        self.signals = _LicenseValidationSignals()

    def run(self) -> None:
        from time import perf_counter

        started = perf_counter()
        status = None
        error = ""
        try:
            from services.license_service import get_license_service

            status = get_license_service().validate(try_refresh=True, force_online_check=True)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        elapsed = perf_counter() - started
        self.signals.result.emit(status, elapsed, error)


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
        self._is_closing = False
        self._license_block_dialog_shown = False
        self._license_check_in_flight = False
        self._license_worker = None
        self.splash = splash
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._apply_app_window_icon()
        self._disconnect_designer_sidebar_toggles()
        self._configure_header_elements()
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
        QTimer.singleShot(1500, self._check_for_updates)
        
        # Enable resize event handling for responsive layout updates
        self.setWindowFlags(self.windowFlags())  # Ensure resize events are enabled

    def _apply_app_window_icon(self) -> None:
        """Apply branded app icon to main window (fallback-safe)."""
        icon_path = get_resource_path("src/ui/resources/icons/Water Balance.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            return
        # Fallback to Qt resource icon when filesystem icon is unavailable.
        fallback = QIcon(":/icons/Company logo.png")
        if not fallback.isNull():
            self.setWindowIcon(fallback)

    def _check_for_updates(self) -> None:
        """Check for app updates in the background and prompt if available."""
        if self._is_closing:
            return

        def _worker():
            try:
                if self._is_closing:
                    return
                from services.update_service import get_update_service
                from services.license_service import get_license_service

                service = get_update_service()
                update = service.check_for_updates(force=True)
                if self._is_closing:
                    return
                if not update:
                    status = get_license_service().get_status()
                    if (not self._is_closing) and (not status.is_valid or not status.tier):
                        QTimer.singleShot(5000, self._check_for_updates)
                    return

                if not self._is_closing:
                    QTimer.singleShot(0, self, lambda: self._show_update_dialog(update))
            except Exception as exc:
                logger.warning("Update check failed: %s", exc)

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_dialog(self, update_info) -> None:
        """Prompt the user to download and install the available update."""
        if self._is_closing:
            return
        title = "Update Available"
        version = str(getattr(update_info, "version", "") or "N/A")
        size_mb = str(getattr(update_info, "file_size_mb", "") or "").strip()
        notes = str(getattr(update_info, "release_notes", "") or "").strip()
        notes_html = notes.replace("\n", "<br>") if notes else "No release notes provided."

        info_parts = [f"<b>Version:</b> {version}"]
        if size_mb:
            info_parts.append(f"<b>Size:</b> {size_mb} MB")
        info_parts.append(f"<b>What's new:</b><br>{notes_html}")
        message = "<br>".join(info_parts)

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(title)
        self._style_update_message_box(box)
        box.setText("<b>A new update is available.</b>")
        box.setInformativeText(message)
        download_button = box.addButton("Download and install", QMessageBox.ButtonRole.AcceptRole)
        later_button = box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(download_button)
        box.setEscapeButton(later_button)
        box.exec()

        if box.clickedButton() == download_button:
            self._start_update_download(update_info)

    def _start_update_download(self, update_info) -> None:
        """Start downloading the update with progress feedback."""
        if self._is_closing:
            return
        from services.update_service import get_update_service

        service = get_update_service()
        self._install_prompt_shown = False

        if getattr(self, "_update_download_dialog", None):
            self._update_download_dialog.close()

        self._update_download_dialog = QProgressDialog(
            "Downloading update...",
            "Cancel",
            0,
            100,
            self
        )
        self._update_download_dialog.setWindowTitle("Downloading Update")
        self._update_download_dialog.setWindowIcon(self.windowIcon())
        self._update_download_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._update_download_dialog.setMinimumDuration(0)
        self._update_download_dialog.setValue(0)
        self._update_download_dialog.setMinimumWidth(440)
        self._update_download_dialog.setStyleSheet(
            """
            QProgressDialog QLabel {
                min-width: 360px;
                font-size: 13px;
            }
            QProgressBar {
                min-height: 16px;
                border: 1px solid #B8C4D3;
                border-radius: 6px;
                background: #EEF3FA;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: #1f4fa3;
            }
            QProgressDialog QPushButton {
                min-width: 110px;
                min-height: 30px;
                padding: 4px 10px;
            }
            """
        )
        self._update_download_dialog.canceled.connect(service.cancel_download)
        self._update_download_dialog.show()

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
        if self._is_closing:
            return
        if getattr(self, "_update_download_dialog", None):
            self._update_download_dialog.setLabelText(message)
            self._update_download_dialog.setValue(progress)

        if "ready to install" in message.lower() and not getattr(self, "_install_prompt_shown", False):
            self._install_prompt_shown = True
            self._prompt_install_downloaded_update()

    def _on_update_download_failed(self, error_message: str) -> None:
        """Handle download failures."""
        if self._is_closing:
            return
        if getattr(self, "_update_download_dialog", None):
            self._update_download_dialog.close()
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Update Download Failed")
        self._style_update_message_box(box)
        box.setText("<b>The update could not be downloaded.</b>")
        box.setInformativeText(error_message)
        ok_button = box.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        box.setDefaultButton(ok_button)
        box.setEscapeButton(ok_button)
        box.exec()

    def _prompt_install_downloaded_update(self) -> None:
        """Prompt the user to install the downloaded update."""
        if self._is_closing:
            return
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
        self._style_update_message_box(box)
        box.setText(f"<b>Update {version} is ready to install.</b>")
        box.setInformativeText(
            "The app will close to complete installation and reopen from the updated version."
        )
        install_button = box.addButton("Install now", QMessageBox.ButtonRole.AcceptRole)
        later_button = box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(install_button)
        box.setEscapeButton(later_button)
        box.exec()

        if box.clickedButton() == install_button:
            if service.install_update(installer_path):
                app = QApplication.instance()
                if app:
                    app.quit()

    def _style_update_message_box(self, box: QMessageBox, min_width: int = 440) -> None:
        """Apply consistent styling for update-related modal dialogs."""
        box.setWindowIcon(self.windowIcon())
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setMinimumWidth(min_width)
        box.resize(min_width, box.sizeHint().height())
        box.setStyleSheet(
            """
            QMessageBox QLabel {
                min-width: 340px;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                min-width: 110px;
                min-height: 30px;
                padding: 4px 10px;
            }
            """
        )

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
        if hasattr(self.ui, 'referesh_button') and self.ui.referesh_button.isVisible():
            self.ui.referesh_button.clicked.connect(self._on_refresh_clicked)

    def _configure_header_elements(self) -> None:
        if hasattr(self.ui, "Header_Main"):
            self.ui.Header_Main.setMinimumHeight(58)
            self.ui.Header_Main.setMaximumHeight(58)
            self.ui.Header_Main.setStyleSheet(
                """
                QWidget#Header_Main {
                    background-color: #124a9f;
                    border-bottom: 1px solid #0f3f87;
                }
                QLabel#label_2 {
                    color: #ffffff;
                    font-size: 15px;
                    font-weight: 700;
                    letter-spacing: 0.2px;
                }
                QPushButton#pushButton_19 {
                    border: none;
                    background: transparent;
                }
                """
            )
        if hasattr(self.ui, "horizontalLayout_2"):
            self.ui.horizontalLayout_2.setContentsMargins(10, 4, 10, 4)
            self.ui.horizontalLayout_2.setSpacing(10)
        if hasattr(self.ui, "verticalLayout_5"):
            self.ui.verticalLayout_5.setContentsMargins(2, 2, 2, 2)
            self.ui.verticalLayout_5.setSpacing(2)
        if hasattr(self.ui, "Heade_Submain"):
            self.ui.Heade_Submain.hide()
        if hasattr(self.ui, "referesh_button"):
            self.ui.referesh_button.hide()
        if hasattr(self.ui, "label_4"):
            self.ui.label_4.hide()

    def _setup_animations(self) -> None:
        """Create smooth width animations for sidebar transitions."""
        self._sidebar_compact_width = 60
        self._sidebar_expanded_width = 220

        self.anim_icon_only = QPropertyAnimation(self.ui.icon_only, b"maximumWidth")
        self.anim_icon_only.setDuration(230)
        self.anim_icon_only.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_icon_name = QPropertyAnimation(self.ui.icon_name, b"maximumWidth")
        self.anim_icon_name.setDuration(230)
        self.anim_icon_name.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._sidebar_anim_group = QParallelAnimationGroup(self)
        self._sidebar_anim_group.addAnimation(self.anim_icon_only)
        self._sidebar_anim_group.addAnimation(self.anim_icon_name)

    def _set_initial_state(self) -> None:
        """Set initial sidebar visibility (compact by default).
        
        On startup, show icon-only sidebar and hide the wide one.
        Burger button unchecked state = compact mode.
        
        Uses fixed widths to prevent layout jumping during transitions.
        """
        # Keep both panes in layout; width animations control visible state smoothly.
        self.ui.icon_only.setVisible(True)
        self.ui.icon_name.setVisible(True)
        self.ui.icon_only.setMinimumWidth(0)
        self.ui.icon_name.setMinimumWidth(0)
        self.ui.icon_only.setMaximumWidth(self._sidebar_compact_width)
        self.ui.icon_name.setMaximumWidth(0)
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
            statusbar.setMinimumHeight(30)
            statusbar.setMaximumHeight(30)
            statusbar.setStyleSheet(
                """
                QStatusBar {
                    background: #f7f9fc;
                    border-top: 1px solid #cfddee;
                    color: #27486b;
                }
                QStatusBar::item {
                    border: none;
                }
                QWidget#statusLicenseWidget, QWidget#statusNetworkWidget {
                    background: transparent;
                }
                QLabel#statusLicenseLabel {
                    border-radius: 8px;
                    padding: 1px 7px;
                    font-size: 11px;
                    font-weight: 500;
                    border: 1px solid #bfd2e8;
                    background: #e9f1fb;
                    color: #173b68;
                }
                QLabel#statusLicenseLabel[statusTone="trial"] {
                    border: 1px solid #f2d3a2;
                    background: #fff6e8;
                    color: #9a5b00;
                }
                QLabel#statusLicenseLabel[statusTone="invalid"] {
                    border: 1px solid #efc3c0;
                    background: #fff1f1;
                    color: #b42318;
                }
                QLabel#statusNetworkLabel {
                    font-size: 11px;
                    font-weight: 600;
                    color: #5b6f86;
                    padding-right: 4px;
                }
                QLabel#statusNetworkLabel[statusTone="online"] {
                    color: #1f7a44;
                }
                QLabel#statusNetworkLabel[statusTone="offline"] {
                    color: #b42318;
                }
                QLabel#statusNetworkDot {
                    font-size: 12px;
                    padding: 0px 2px;
                    color: #94a6bc;
                }
                QLabel#statusNetworkDot[statusTone="online"] {
                    color: #24a148;
                }
                QLabel#statusNetworkDot[statusTone="offline"] {
                    color: #d92d20;
                }
                """
            )
            
            # === LEFT SIDE: License Info ===
            license_widget = QWidget()
            license_widget.setObjectName("statusLicenseWidget")
            license_layout = QHBoxLayout(license_widget)
            license_layout.setContentsMargins(4, 1, 4, 1)
            license_layout.setSpacing(6)
            
            # License key icon
            self.license_icon = QLabel()
            license_pixmap = QIcon(":/icons/license-svgrepo-com.svg").pixmap(12, 12)
            self.license_icon.setPixmap(license_pixmap)
            self.license_icon.setToolTip("License Status")
            license_layout.addWidget(self.license_icon)
            
            # License type label
            self.license_label = QLabel("Loading...")
            self.license_label.setObjectName("statusLicenseLabel")
            self.license_label.setProperty("statusTone", "valid")
            license_layout.addWidget(self.license_label)
            
            statusbar.addWidget(license_widget)
            
            # === RIGHT SIDE (Permanent): Network Status ===
            network_widget = QWidget()
            network_widget.setObjectName("statusNetworkWidget")
            network_layout = QHBoxLayout(network_widget)
            network_layout.setContentsMargins(6, 2, 6, 2)
            network_layout.setSpacing(4)

            # Network status dot
            self.network_dot = QLabel("●")
            self.network_dot.setObjectName("statusNetworkDot")
            self.network_dot.setProperty("statusTone", "checking")
            network_layout.addWidget(self.network_dot)
            
            # Network status icon
            self.network_icon = QLabel()
            # Set default icon (will be updated by network check)
            default_pixmap = QIcon(":/icons/network-wireless-svgrepo-com.svg").pixmap(12, 12)
            if not default_pixmap.isNull():
                self.network_icon.setPixmap(default_pixmap)
            else:
                logger.debug("Network icon resource not found")
            self.network_icon.setToolTip("Network Status")
            network_layout.addWidget(self.network_icon)
            
            # Network status label
            self.network_label = QLabel("Checking...")
            self.network_label.setObjectName("statusNetworkLabel")
            self.network_label.setProperty("statusTone", "checking")
            network_layout.addWidget(self.network_label)
            
            statusbar.addPermanentWidget(network_widget)
            
            # Defer status updates to avoid blocking startup
            QTimer.singleShot(500, self._update_license_status)
            QTimer.singleShot(1000, self._update_network_status)
            
            # Set up periodic network check (every 30 seconds)
            self._network_check_timer = QTimer(self)
            self._network_check_timer.timeout.connect(self._update_network_status)
            self._network_check_timer.start(30000)  # 30 seconds

            # Set up periodic runtime license enforcement.
            # This ensures revoked licenses are blocked while the app is open.
            interval_seconds = self._resolve_runtime_license_interval_seconds()
            self._license_check_timer = QTimer(self)
            self._license_check_timer.timeout.connect(self._enforce_runtime_license_status)
            self._license_check_timer.start(interval_seconds * 1000)
            QTimer.singleShot(2000, self._enforce_runtime_license_status)
            logger.info("license_runtime_timer interval_seconds=%s", interval_seconds)
            
            logger.info("Status bar widgets initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup status bar: {e}")

    def _set_license_tone(self, tone: str) -> None:
        """Apply status tone to license pill and refresh style."""
        self.license_label.setProperty("statusTone", tone)
        style = self.license_label.style()
        style.unpolish(self.license_label)
        style.polish(self.license_label)
        self.license_label.update()

    def _set_network_tone(self, tone: str) -> None:
        """Apply status tone to network label/dot and refresh style."""
        self.network_label.setProperty("statusTone", tone)
        self.network_dot.setProperty("statusTone", tone)
        label_style = self.network_label.style()
        label_style.unpolish(self.network_label)
        label_style.polish(self.network_label)
        dot_style = self.network_dot.style()
        dot_style.unpolish(self.network_dot)
        dot_style.polish(self.network_dot)
        self.network_label.update()
        self.network_dot.update()
    
    def _update_license_status(self) -> None:
        """Update license status display in status bar (LICENSE STATUS)."""
        try:
            from services.license_service import get_license_service
            license_service = get_license_service()
            
            license_info = license_service.get_license_info()
            
            if license_info and license_info.get('is_valid'):
                tier = license_info.get('tier', 'unknown').upper()
                status = license_info.get('status', 'active')

                self.license_label.setText(f"{tier} License")
                self._set_license_tone("trial" if tier == "TRIAL" else "valid")
                self.license_label.setToolTip(f"License: {tier}\nStatus: {status}")
            else:
                self.license_label.setText("No License")
                self._set_license_tone("invalid")
                self.license_label.setToolTip("No valid license found")
                
        except Exception as e:
            logger.warning(f"Failed to update license status: {e}")
            self.license_label.setText("License: Unknown")
            self._set_license_tone("invalid")
    
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
                        logger.debug(
                            f"Network icon isNull={icon.isNull()}, sizes={icon.availableSizes()}"
                        )
                        network_pixmap = icon.pixmap(16, 16)
                        logger.debug(
                            f"Network pixmap isNull={network_pixmap.isNull()} "
                            f"width={network_pixmap.width()} height={network_pixmap.height()}"
                        )
                        
                        if not network_pixmap.isNull():
                            self.network_icon.setPixmap(network_pixmap)
                            logger.debug("Network pixmap set successfully")
                        else:
                            # Fallback: Use text if icon fails
                            self.network_icon.setText("🟢")
                            logger.debug("Network icon fallback in use")
                        
                        self.network_label.setText("Online")
                        self._set_network_tone("online")
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
                        self._set_network_tone("offline")
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
            self._set_network_tone("checking")

    def _enforce_runtime_license_status(self) -> None:
        """Revalidate license during runtime and block if revoked/invalid."""
        if self._is_closing or self._license_block_dialog_shown or self._license_check_in_flight:
            return
        self._license_check_in_flight = True
        worker = _LicenseValidationWorker()
        self._license_worker = worker
        worker.signals.result.connect(self._on_runtime_license_result)
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def _resolve_runtime_license_interval_seconds() -> int:
        """Resolve runtime license check interval with safe production bounds."""
        cfg = ConfigManager()
        raw = cfg.get(
            "licensing.runtime_check_interval_seconds",
            cfg.get("licensing.background_check_interval_seconds", 900),
        )
        try:
            interval_seconds = int(raw)
        except Exception:
            interval_seconds = 900
        return max(60, min(interval_seconds, 86400))

    @Slot(object, float, str)
    def _on_runtime_license_result(self, status, elapsed_seconds: float, error: str) -> None:
        """Handle background runtime license validation result in UI thread."""
        self._license_check_in_flight = False
        self._license_worker = None
        if self._is_closing:
            return
        if error:
            logger.warning(
                "license_runtime_check result=error elapsed_ms=%s diagnostics=%s",
                int(elapsed_seconds * 1000),
                error,
            )
            return
        if status is None:
            logger.warning("license_runtime_check result=error elapsed_ms=%s diagnostics=empty_status", int(elapsed_seconds * 1000))
            return

        logger.info(
            "license_runtime_check result=%s should_block=%s elapsed_ms=%s",
            status.status,
            int(status.should_block),
            int(elapsed_seconds * 1000),
        )
        self._update_license_status()
        if not status.should_block:
            return

        self._license_block_dialog_shown = True
        if hasattr(self, "_license_check_timer") and self._license_check_timer is not None:
            self._license_check_timer.stop()

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("License Invalid")
        msg.setText("License access has been blocked.")
        msg.setInformativeText(
            f"Status: {status.status}\n"
            f"{status.message}\n\n"
            "Next step:\n"
            "- Connect to internet and retry if this is a refresh issue.\n"
            "- If blocked persists, contact support with your machine ID.\n\n"
            "The application will close."
        )
        msg.exec()
        self.close()

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
        
        Animates compact and expanded panes in parallel for fluid transitions.
        """
        if self._sidebar_anim_group.state() == QAbstractAnimation.State.Running:
            self._sidebar_anim_group.stop()

        if expanded:
            self.anim_icon_only.setStartValue(self.ui.icon_only.maximumWidth())
            self.anim_icon_only.setEndValue(0)
            self.anim_icon_name.setStartValue(self.ui.icon_name.maximumWidth())
            self.anim_icon_name.setEndValue(self._sidebar_expanded_width)
        else:
            self.anim_icon_only.setStartValue(self.ui.icon_only.maximumWidth())
            self.anim_icon_only.setEndValue(self._sidebar_compact_width)
            self.anim_icon_name.setStartValue(self.ui.icon_name.maximumWidth())
            self.anim_icon_name.setEndValue(0)

        self._sidebar_anim_group.start()

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
            dashboard_data = {}
            
            # Get environmental data (rainfall, evaporation) from database
            try:
                env_service = get_environmental_data_service()
                month = getattr(self.ui.dashboard, "current_month", None)
                year = getattr(self.ui.dashboard, "current_year", None)
                
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
        1. Stop background services/timers.
        2. Request all pages to stop background workers.
        3. Drain thread-pool tasks briefly.
        4. Accept close and continue shutdown.
        """
        from PySide6.QtCore import QThreadPool
        from PySide6.QtWidgets import QApplication

        logger.info("Application close requested - shutting down...")
        self._is_closing = True

        if hasattr(self, "_network_check_timer") and self._network_check_timer is not None:
            try:
                self._network_check_timer.stop()
            except Exception as exc:
                logger.debug(f"Unable to stop network check timer: {exc}")
        if hasattr(self, "_license_check_timer") and self._license_check_timer is not None:
            try:
                self._license_check_timer.stop()
            except Exception as exc:
                logger.debug(f"Unable to stop license check timer: {exc}")

        if getattr(self, "_update_download_dialog", None):
            try:
                self._update_download_dialog.close()
            except Exception:
                pass

        # Stop singleton background services first (timers/workers outside page ownership).
        try:
            from services.notification_service import get_notification_service
            get_notification_service().stop_background_sync()
            logger.info("Notification background sync stopped")
        except Exception as exc:
            logger.warning(f"Unable to stop notification background sync: {exc}")

        try:
            from services.update_service import get_update_service
            get_update_service().cancel_download()
            logger.info("Update download worker stop requested")
        except Exception as exc:
            logger.warning(f"Unable to stop update download worker: {exc}")

        # Build a de-duplicated page list from stacked widget + known references.
        pages = []
        seen = set()

        def _add_page(candidate) -> None:
            if candidate is None:
                return
            key = id(candidate)
            if key in seen:
                return
            seen.add(key)
            pages.append(candidate)

        if getattr(self.ui, "stackedWidget", None):
            for idx in range(self.ui.stackedWidget.count()):
                _add_page(self.ui.stackedWidget.widget(idx))

        for attr in (
            "_dashboard_page",
            "_analytics_page",
            "_monitoring_page",
            "_storage_facilities_page",
            "_settings_page",
            "_help_page",
            "_messages_page",
            "_about_page",
        ):
            _add_page(getattr(self, attr, None))

        # Request all page-owned workers to stop.
        for page in pages:
            if hasattr(page, "stop_background_tasks"):
                try:
                    page.stop_background_tasks()
                except Exception as exc:
                    logger.warning(
                        "Error stopping tasks on page %s: %s",
                        page.__class__.__name__,
                        exc,
                    )

        # Drain queued QRunnable work for a bounded interval.
        try:
            QThreadPool.globalInstance().waitForDone(2500)
        except Exception as exc:
            logger.warning(f"Error while draining global thread pool: {exc}")

        # Give threads time to process queued quit/cancel signals.
        app = QApplication.instance()
        if app:
            for _ in range(3):
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
    def _disconnect_designer_sidebar_toggles(self) -> None:
        """Remove Designer's direct sidebar visibility bindings.

        We manage sidebar state ourselves via width animations.
        """
        try:
            self.ui.pushButton_19.toggled.disconnect(self.ui.icon_name.setVisible)
        except Exception:
            pass
        try:
            self.ui.pushButton_19.toggled.disconnect(self.ui.icon_only.setHidden)
        except Exception:
            pass
