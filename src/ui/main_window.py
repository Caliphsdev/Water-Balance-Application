"""
Main Window - Professional UI Layout
Sidebar navigation, content area, toolbar, and status bar
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config
from utils.app_logger import logger
from utils.ui_notify import notifier
from utils.alert_manager import alert_manager
from ui.mousewheel import apply_mousewheel_recursive
from utils.excel_monitor import ExcelFileMonitor
from utils.excel_timeseries_extended import ExcelTimeSeriesExtended
from utils.cache_prewarm import prewarm_latest_month
import threading


class MainWindow:
    """Main application window with professional layout"""
    
    def __init__(self, root):
        """Initialize the main window layout"""
        self.root = root
        self.current_module = None
        self._module_cache = {}
        self._pending_load = None
        
        # Log application start
        logger.info("Main window initializing")
        
        # Set up notification system with status bar callback
        notifier.set_status_bar_callback(self._update_status_message)
        
        # Excel loading will be lazy (on-demand when modules need it)
        self.excel_loaded = False
        self.excel_monitor = None
        
        # Create main container
        self.container = ttk.Frame(self.root)
        self.container.pack(fill='both', expand=True)
        
        # Build UI components
        self._create_toolbar()
        self._create_main_layout()
        self._create_statusbar()
        # Maximize window for better fit across modules
        self._maximize_window()

        # Load default module (Dashboard) - Excel will load on-demand
        self.load_module('dashboard')
    
    def _create_toolbar(self):
        """Create top toolbar with menu and quick actions"""
        toolbar_height = config.get('ui.toolbar_height', 50)
        bg_header = config.get_color('bg_header')
        text_light = config.get_color('text_light')
        
        self.toolbar = tk.Frame(
            self.container,
            bg=bg_header,
            height=toolbar_height
        )
        self.toolbar.pack(side='top', fill='x')
        self.toolbar.pack_propagate(False)
        
        # Application title and logo
        title_frame = tk.Frame(self.toolbar, bg=bg_header)
        title_frame.pack(side='left', padx=20, pady=10)
        
        # Company logo (if available)
        logo_path = config.get_logo_path()
        if logo_path and Path(logo_path).exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                # Resize to fit toolbar height (maintain aspect ratio)
                toolbar_height = config.get('ui.toolbar_height', 50)
                img.thumbnail((int(toolbar_height * 2.5), toolbar_height - 10), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(title_frame, image=self.logo_photo, bg=bg_header)
                logo_label.pack(side='left', padx=(0, 15))
            except Exception as e:
                logger.warning(f"Could not load logo: {e}")
        
        app_title = tk.Label(
            title_frame,
            text=config.app_name,
            font=config.get_font('heading_medium'),
            fg=text_light,
            bg=bg_header
        )
        app_title.pack(side='left')
    
    def _create_main_layout(self):
        """Create sidebar and content area layout"""
        # Main content frame
        self.main_frame = ttk.Frame(self.container)
        self.main_frame.pack(side='top', fill='both', expand=True)
        
        # Sidebar navigation
        self._create_sidebar()
        
        # Content area
        self._create_content_area()
    
    def _create_sidebar(self):
        """Create sidebar with navigation menu"""
        sidebar_width = config.get('ui.sidebar_width', 220)
        bg_sidebar = config.get_color('bg_sidebar')
        text_light = config.get_color('text_light')
        
        self.sidebar = tk.Frame(
            self.main_frame,
            bg=bg_sidebar,
            width=sidebar_width
        )
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = tk.Label(
            self.sidebar,
            text="Navigation",
            font=config.get_font('heading_small'),
            fg=text_light,
            bg=bg_sidebar,
            anchor='w',
            padx=20,
            pady=15
        )
        sidebar_header.pack(fill='x')
        
        # Navigation menu items
        self.nav_buttons = {}
        
        menu_items = [
            ('dashboard', '» Dashboard', 'Water balance overview and KPIs'),
            ('analytics', '» Analytics & Trends', 'Statistical analysis and trend graphs'),
            ('monitoring_data', '» Monitoring Data', 'Environmental and operational monitoring from Excel'),
            ('water_sources', '» Water Sources', 'Manage rivers, boreholes, and underground sources'),
            ('storage', '» Storage Facilities', 'Manage dams and water storage'),
            ('calculations', '» Calculations', 'Water balance calculations and results'),
            ('flow_diagram', '» Flow Diagram', 'Visual water balance flow with inputs/outputs/processes'),
            ('settings', '» Settings', 'System configuration and backups'),
        ]
        
        for module_id, label, tooltip in menu_items:
            self._create_nav_button(module_id, label, tooltip)
        
        # Separator
        separator = tk.Frame(self.sidebar, bg=config.get_color('divider'), height=1)
        separator.pack(fill='x', padx=20, pady=10)
        
        # Help and About at bottom
        help_items = [
            ('help', '? Help', 'User guide and documentation'),
            ('about', 'i About', 'About this application'),
        ]
        
        for module_id, label, tooltip in help_items:
            self._create_nav_button(module_id, label, tooltip)

    def _validate_excel_path_startup(self):
        """On startup, ensure the Application Inputs Excel is a valid .xlsx file.
        If missing/invalid, guide user to Settings → Data Sources.
        """
        try:
            from pathlib import Path
            template_path = config.get('data_sources.template_excel_path', '') or ''
            p = Path(template_path)
            is_valid = p.is_file()
            if not is_valid:
                notifier.warning(
                    "Application Inputs Excel is not configured or invalid.\n" +
                    "Go to Settings → Data Sources to select the .xlsx file.",
                    title="Excel Path Needed",
                    show_dialog=True
                )
                # Navigate to settings and open data sources tab (if supported)
                self.load_module('settings', tab='data_sources')
        except Exception:
            pass
    
    def _create_nav_button(self, module_id, label, tooltip):
        """Create a navigation button in sidebar"""
        bg_sidebar = config.get_color('bg_sidebar')
        text_light = config.get_color('text_light')
        primary_light = config.get_color('primary_light')
        
        btn = tk.Button(
            self.sidebar,
            text=label,
            font=config.get_font('body'),
            fg=text_light,
            bg=bg_sidebar,
            activebackground=primary_light,
            activeforeground='white',
            relief='flat',
            anchor='w',
            padx=20,
            pady=12,
            cursor='hand2',
            command=lambda: self.load_module(module_id)
        )
        btn.pack(fill='x')
        
        # Tooltip (simple version)
        self._bind_tooltip(btn, tooltip)
        
        # Hover effects
        btn.bind('<Enter>', lambda e: btn.config(bg=primary_light))
        btn.bind('<Leave>', lambda e: btn.config(bg=bg_sidebar))
        
        self.nav_buttons[module_id] = btn
    
    def _bind_tooltip(self, widget, text):
        """Simple tooltip binding"""
        def show_tooltip(event):
            # Simple statusbar tooltip
            self.statusbar_label.config(text=text)
        
        def hide_tooltip(event):
            self._update_statusbar()
        
        widget.bind('<Enter>', show_tooltip, add='+')
        widget.bind('<Leave>', hide_tooltip, add='+')
    
    def _create_content_area(self):
        """Create main content display area"""
        bg_main = config.get_color('bg_main')
        
        self.content_area = tk.Frame(self.main_frame, bg=bg_main)
        self.content_area.pack(side='left', fill='both', expand=True)
        
        # Content will be loaded dynamically based on navigation
    
    def _create_statusbar(self):
        """Create bottom status bar"""
        statusbar_height = config.get('ui.statusbar_height', 25)
        bg_secondary = config.get_color('bg_secondary')
        text_secondary = config.get_color('text_secondary')
        
        self.statusbar = tk.Frame(
            self.container,
            bg=bg_secondary,
            height=statusbar_height
        )
        self.statusbar.pack(side='bottom', fill='x')
        self.statusbar.pack_propagate(False)
        
        # Status label
        self.statusbar_label = tk.Label(
            self.statusbar,
            text="Ready",
            font=config.get_font('caption'),
            fg=text_secondary,
            bg=bg_secondary,
            anchor='w',
            padx=10
        )
        self.statusbar_label.pack(side='left', fill='x', expand=True)
        
        # Exit button (red)
        exit_btn = tk.Button(
            self.statusbar,
            text="Exit",
            font=config.get_font('body_bold'),
            fg='white',
            bg='#C62828',
            activebackground='#B71C1C',
            activeforeground='white',
            relief='flat',
            padx=14, pady=4,
            cursor='hand2',
            command=self._request_exit
        )
        exit_btn.pack(side='right', padx=(5, 6), pady=3)
        exit_btn.bind('<Enter>', lambda e: exit_btn.config(bg='#B71C1C'))
        exit_btn.bind('<Leave>', lambda e: exit_btn.config(bg='#C62828'))

        # Version info left of button
        version_label = tk.Label(
            self.statusbar,
            text=f"v{config.app_version}",
            font=config.get_font('caption'),
            fg=text_secondary,
            bg=bg_secondary,
            anchor='e',
            padx=8
        )
        version_label.pack(side='right')

    def _maximize_window(self):
        """Maximize the window to fit the screen without changing layouts."""
        try:
            # Try platform zoom (Windows/macOS)
            self.root.state('zoomed')
        except Exception:
            try:
                # Some X11/wayland builds support '-zoomed' attribute
                self.root.attributes('-zoomed', True)
            except Exception:
                try:
                    # Fallback: set geometry to screen size
                    w = self.root.winfo_screenwidth()
                    h = self.root.winfo_screenheight()
                    self.root.geometry(f"{w}x{h}+0+0")
                except Exception:
                    pass
    
    def load_module(self, module_id, **kwargs):
        """Load a module into the content area
        
        Args:
            module_id: ID of the module to load
            **kwargs: Additional parameters to pass to module loaders
        """
        # Debounce: cancel pending load if user clicks rapidly
        if self._pending_load:
            self.root.after_cancel(self._pending_load)
            self._pending_load = None
        
        # Skip if already on this module (unless kwargs provided)
        if module_id == self.current_module and not kwargs:
            return
        
        def _do_load():
            self._pending_load = None
            try:
                logger.user_action(f"Loading module: {module_id}")
                
                # Clear current content
                for widget in self.content_area.winfo_children():
                    widget.destroy()
                
                # Force update to clear widgets immediately
                self.content_area.update_idletasks()
            
                # Highlight active nav button
                self._highlight_nav_button(module_id)
                
                # Load module based on ID
                self.current_module = module_id
                
                if module_id == 'dashboard':
                    self._load_dashboard()
                elif module_id == 'analytics':
                    self._load_analytics()
                elif module_id == 'monitoring_data':
                    self._load_monitoring_data()
                elif module_id == 'water_sources':
                    self._load_water_sources()
                elif module_id == 'storage':
                    self._load_storage_facilities()
                elif module_id == 'calculations':
                    self._load_calculations()
                elif module_id == 'flow_diagram':
                    self._load_flow_diagram()
                elif module_id == 'settings':
                    self._load_settings(tab=kwargs.get('tab'))
                elif module_id == 'help':
                    from ui.help_documentation import HelpDocumentation
                    help_module = HelpDocumentation(self.content_area)
                    help_module.create_ui()
                elif module_id == 'about':
                    self._load_about()
            
                self._update_statusbar()
                logger.info(f"Module loaded successfully: {module_id}")

                # Apply mousewheel bindings globally within content area after load
                try:
                    apply_mousewheel_recursive(self.content_area)
                except Exception:
                    # Non-critical; ignore failures silently
                    pass
                
            except Exception as e:
                from utils.error_handler import error_handler, ErrorCategory
                tech_msg, user_msg, severity = error_handler.handle(
                    e, 
                    context=f"Loading module: {module_id}",
                    category=ErrorCategory.SYSTEM
                )
                notifier.notify_from_error(severity, user_msg, tech_msg)
                # Visible fallback so window is not blank
                try:
                    for widget in self.content_area.winfo_children():
                        widget.destroy()
                    fallback = tk.Frame(self.content_area, bg=config.get_color('bg_main'))
                    fallback.pack(fill='both', expand=True, padx=30, pady=30)
                    tk.Label(
                        fallback,
                        text=f"Module '{module_id}' failed to load.",
                        font=config.get_font('heading_medium'),
                        fg=config.get_color('primary'),
                        bg=config.get_color('bg_main')
                    ).pack(anchor='w')
                    tk.Label(
                        fallback,
                        text="Check Settings → Data Sources if this depends on Excel data.",
                        font=config.get_font('body'),
                        fg=config.get_color('text_primary'),
                        bg=config.get_color('bg_main'),
                        wraplength=800,
                        justify='left'
                    ).pack(anchor='w', pady=(10,20))
                    tk.Button(
                        fallback,
                        text="Open Settings",
                        command=lambda: self.load_module('settings'),
                        padx=18,
                        pady=8,
                        bg=config.get_color('primary'),
                        fg='white',
                        relief='flat',
                        activebackground=config.get_color('primary_dark')
                    ).pack(anchor='w')
                except Exception:
                    pass
        
        # Schedule load with small delay for debouncing
        self._pending_load = self.root.after(50, _do_load)
    
    def _highlight_nav_button(self, active_id):
        """Highlight the active navigation button"""
        bg_sidebar = config.get_color('bg_sidebar')
        primary = config.get_color('primary')
        
        for module_id, btn in self.nav_buttons.items():
            if module_id == active_id:
                btn.config(bg=primary)
            else:
                btn.config(bg=bg_sidebar)
    
    def _ensure_excel_loaded(self, module_name: str) -> bool:
        """Ensure Excel is loaded before module needs it
        
        Args:
            module_name: Name of module that needs Excel
            
        Returns:
            True if Excel loaded, False if missing
        """
        if self.excel_loaded:
            return True  # Already loaded
        
        from utils.lazy_excel_loader import get_lazy_loader
        from ui.excel_config_dialog import show_excel_config_dialog
        
        loader = get_lazy_loader()
        
        # Try to load Excel
        def on_excel_missing(path):
            """Called if Excel file is missing"""
            result = show_excel_config_dialog(self.root, path)
            if result:
                # User configured a new path, try loading again
                loader.reset()
                loader.load_excel_if_needed()
                self.excel_loaded = True
        
        success = loader.load_excel_if_needed(on_missing=on_excel_missing)
        if success:
            self.excel_loaded = True
            logger.info(f"Excel loaded for module: {module_name}")
            return True
        else:
            logger.warning(f"Excel not available for module: {module_name}")
            return False
    
    def _load_dashboard(self):
        """Load the dashboard module"""
        from ui.dashboard import DashboardModule
        
        dashboard = DashboardModule(self.content_area)
        dashboard.load()

    def _load_analytics(self):
        """Load the analytics & trends module"""
        from ui.analytics_dashboard import AnalyticsDashboard
        
        analytics = AnalyticsDashboard(self.content_area)
        analytics.load()
    
    def _load_monitoring_data(self):
        """Load the monitoring data module"""
        from ui.monitoring_data import MonitoringDataModule
        
        module = MonitoringDataModule(self.content_area)
        module.load()
    
    def _load_water_sources(self):
        """Load the water sources management module"""
        from ui.water_sources import WaterSourcesModule
        
        module = WaterSourcesModule(self.content_area)
        module.load()
    
    def _load_storage_facilities(self):
        """Load the storage facilities management module"""
        from ui.storage_facilities import StorageFacilitiesModule
        
        module = StorageFacilitiesModule(self.content_area)
        module.load()
    
    def _load_calculations(self):
        """Load the calculations module"""
        # Lazy load Excel if needed (calculations may use Excel data)
        self._ensure_excel_loaded('calculations')
        
        from ui.calculations import CalculationsModule
        
        module = CalculationsModule(self.content_area)
        module.load()

    def _load_flow_diagram(self):
        """Load the flow diagram module showing water balance flow"""
        from ui.flow_diagram_dashboard import FlowDiagramDashboard

        module = FlowDiagramDashboard(self.content_area)
        module.load()
    
    def _load_placeholder(self, title, description):
        """Load a placeholder for modules under development"""
        bg_main = config.get_color('bg_main')
        
        container = tk.Frame(self.content_area, bg=bg_main)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            container,
            text=title,
            font=config.get_font('heading_large'),
            fg=config.get_color('primary'),
            bg=bg_main,
            anchor='w'
        )
        title_label.pack(fill='x', pady=(0, 10))
        
        # Description
        desc_label = tk.Label(
            container,
            text=description,
            font=config.get_font('body'),
            fg=config.get_color('text_secondary'),
            bg=bg_main,
            anchor='w'
        )
        desc_label.pack(fill='x', pady=(0, 20))
        
        # Placeholder message
        message = tk.Label(
            container,
            text="🚧 Module under development\n\nThis feature will be implemented soon.",
            font=config.get_font('heading_small'),
            fg=config.get_color('text_secondary'),
            bg=bg_main,
            justify='center'
        )
        message.pack(expand=True)
    
    def _load_about(self):
        """Load the About page"""
        bg_main = config.get_color('bg_main')
        
        container = tk.Frame(self.content_area, bg=bg_main)
        container.pack(fill='both', expand=True)
        
        # Center content frame
        center_frame = tk.Frame(container, bg=bg_main)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Company logo/header
        header = tk.Label(
            center_frame,
            text="🏢 TransAfrica Resources",
            font=('Segoe UI', 24, 'bold'),
            fg='#0066cc',
            bg=bg_main
        )
        header.pack(pady=(0, 10))
        
        # App title
        title = tk.Label(
            center_frame,
            text=f"💧 {config.app_name}",
            font=('Segoe UI', 18, 'bold'),
            fg=config.get_color('text_primary'),
            bg=bg_main
        )
        title.pack(pady=(0, 5))
        
        # Version
        version = tk.Label(
            center_frame,
            text=f"📦 Version {config.app_version}",
            font=('Segoe UI', 12),
            fg=config.get_color('text_secondary'),
            bg=bg_main
        )
        version.pack(pady=(0, 20))
        
        # Description
        desc = tk.Label(
            center_frame,
            text="Professional water balance management system for mining operations",
            font=('Segoe UI', 11),
            fg=config.get_color('text_primary'),
            bg=bg_main,
            wraplength=500
        )
        desc.pack(pady=(0, 30))
        
        # Contact info section
        contact_frame = tk.Frame(center_frame, bg='#f8f9fa', relief='solid', borderwidth=1)
        contact_frame.pack(fill='x', padx=20, pady=10)
        
        contact_title = tk.Label(
            contact_frame,
            text="📞 Contact Information",
            font=('Segoe UI', 12, 'bold'),
            fg='#0066cc',
            bg='#f8f9fa'
        )
        contact_title.pack(pady=(15, 10))
        
        contacts = [
            "📧 caliphs@transafreso.com",
            "📧 kali@transafreso.com",
            "☎️  +27 82 355 8130",
            "☎️  +27 235 76 07"
        ]
        
        for contact in contacts:
            contact_label = tk.Label(
                contact_frame,
                text=contact,
                font=('Segoe UI', 10),
                fg=config.get_color('text_primary'),
                bg='#f8f9fa'
            )
            contact_label.pack(pady=3)
        
        contact_frame.pack_configure(pady=(0, 20))
        
        # Features
        features_label = tk.Label(
            center_frame,
            text="✨ Key Features",
            font=('Segoe UI', 11, 'bold'),
            fg=config.get_color('text_primary'),
            bg=bg_main
        )
        features_label.pack(pady=(10, 8))
        
        features = [
            "• Comprehensive water source tracking",
            "• Storage facility management", 
            "• Real-time water balance calculations",
            "• Professional reporting and exports",
            "• Modern intuitive interface"
        ]
        
        for feature in features:
            feature_label = tk.Label(
                center_frame,
                text=feature,
                font=('Segoe UI', 10),
                fg=config.get_color('text_secondary'),
                bg=bg_main,
                justify='left'
            )
            feature_label.pack(anchor='w', padx=40)
        
        # Copyright
        copyright_label = tk.Label(
            center_frame,
            text=f"© 2025 TransAfrica Resources (Pty) Ltd. All rights reserved.",
            font=('Segoe UI', 9),
            fg=config.get_color('text_secondary'),
            bg=bg_main
        )
        copyright_label.pack(pady=(30, 0))
    
    def _update_statusbar(self):
        """Update status bar with current module info"""
        module_names = {
            'dashboard': 'Dashboard - Water Balance Overview',
            'water_sources': 'Water Sources Management',
            'storage': 'Storage Facilities Management',
            'measurements': 'Measurements Data Entry',
            'calculations': 'Water Balance Calculations',
            'reports': 'Reports Generation',
            'settings': 'Settings & Configuration',
            'import_export': 'Data Import/Export',
            'help': 'Help & Documentation',
        }
        
        status_text = module_names.get(self.current_module, 'Ready')
        self.statusbar_label.config(text=status_text)
    
    def _update_status_message(self, message: str):
        """Update status bar with custom message (used by notifier)"""
        if hasattr(self, 'statusbar_label'):
            self.statusbar_label.config(text=message)

    def _request_exit(self):
        """Handle exit button click with confirmation using notifier."""
        from utils.app_logger import logger as _logger
        _logger.user_action("Application close requested (button)")
        if notifier.confirm("Are you sure you want to exit?", "Confirm Exit"):
            try:
                # Cancel any pending after callbacks
                if hasattr(self, '_alert_badge_after_id') and self._alert_badge_after_id:
                    self.root.after_cancel(self._alert_badge_after_id)
                    self._alert_badge_after_id = None
                
                # Set flag to prevent on_closing double execution
                self.root._closing = True
            except Exception:
                pass
            _logger.info("Application closing - user confirmed via button")
            _logger.info("=" * 60)
            _logger.info("Water Balance Application Stopped")
            _logger.info("=" * 60)
            try:
                self.root.destroy()
            except Exception:
                pass
        else:
            _logger.info("Application close cancelled by user (button)")
    
    # Toolbar action methods removed - use sidebar navigation instead
    
    def _setup_excel_monitor(self):
        """Setup Excel file monitoring for auto-reload (legacy - disabled on startup)"""
        # Excel monitoring is now only done via lazy loader on-demand
        # This method is kept for backwards compatibility
        logger.info("Excel monitoring disabled at startup (lazy loading enabled)")
    
    def _on_excel_changed(self):
        """Called when Excel file changes - reload data"""
        try:
            # Reload Excel data singleton
            excel = ExcelTimeSeriesExtended()
            excel.reload()
            
            # Show notification to user
            self.root.after(0, lambda: notifier.info("📊 Excel data updated automatically"))
            
            # Reload current module if it uses Excel data
            if self.current_module in ['dashboard', 'calculations']:
                logger.info(f"Reloading {self.current_module} after Excel change")
                self.root.after(100, lambda: self.load_module(self.current_module))
                
        except Exception as e:
            logger.error(f"Error handling Excel file change: {e}")

    def _prewarm_cache_background(self):
        """Run cache pre-warm automatically in a background thread to avoid UI blocking."""
        def _task():
            try:
                from database.db_manager import db
                repo = ExcelTimeSeriesExtended()
                ok, total, latest = prewarm_latest_month(db_manager=db, repo=repo)
                if latest:
                    msg = f"Cache pre-warmed: {ok}/{total} facilities for {latest:%Y-%m}"
                else:
                    msg = "Cache pre-warm skipped (no dates)"
                logger.info(msg)
                try:
                    # Silently log - no UI notification for automatic pre-warming
                    pass
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Automatic cache pre-warm error: {e}")
        t = threading.Thread(target=_task, daemon=True)
        t.start()

    def _load_settings(self, tab=None):
        """Load settings module
        
        Args:
            tab: Optional tab to open ('alerts', 'constants', etc.)
        """
        from ui.settings_revamped import SettingsModule
        module = SettingsModule(self.content_area, initial_tab=tab)
        module.load()

    def _load_extended_summary(self):
        """Load extended summary GUI module"""
        from ui.extended_summary_view import ExtendedSummaryView
        view = ExtendedSummaryView(self.content_area)
        view.load()
        view.pack(fill='both', expand=True, padx=15, pady=10)
