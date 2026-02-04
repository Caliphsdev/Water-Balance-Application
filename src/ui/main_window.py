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

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel
from PySide6.QtCore import Slot, QSize, QPropertyAnimation, QEasingCurve

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
from core.app_logger import logger as app_logger
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
        self._setup_animations()
        self._set_initial_state()
        
        # Load all pages upfront (splash screen shows during this)
        self._mount_pages()
        self._connect_navigation()
        self._set_default_page()  # Set Dashboard as the startup page

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
        index = self.ui.stackedWidget.indexOf(page_widget)
        if index >= 0:
            self.ui.stackedWidget.setCurrentIndex(index)
    
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
        """Handle application shutdown to stop background workers safely (SHUTDOWN ORCHESTRATION).

        This ensures QThread workers in dashboards are stopped before
        widgets are destroyed, preventing late signal emissions.
        
        Process:
        1. Call stop_background_tasks() on each dashboard (requests cancellation)
        2. Process events to allow threads to finish gracefully
        3. Accept the close event
        
        This prevents "QThread: Destroyed while thread running" warnings during shutdown.
        """
        from PySide6.QtWidgets import QApplication
        
        pages = [
            getattr(self.ui, "monitoring_data", None),
            getattr(self.ui, "analytics_trends", None),
            getattr(self.ui, "storge_facilitites", None),
        ]

        # Request all threads to stop
        for page in pages:
            if page and hasattr(page, "stop_background_tasks"):
                page.stop_background_tasks()

        # Give threads time to finish gracefully
        app = QApplication.instance()
        if app:
            app.processEvents()

        super().closeEvent(event)
