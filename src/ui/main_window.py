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
from licensing.license_manager import LicenseManager
import threading


class MainWindow:
    """Main application window with professional layout"""
    
    def __init__(self, root):
        """Initialize the main window layout"""
        self.root = root
        self.current_module = None
        self._module_cache = {}
        self._pending_load = None
        self.sidebar_collapsed = False  # Initialize sidebar state
        
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
        
        # Build UI components (statusbar CREATED FIRST so it's packed in correct order)
        self._create_toolbar()
        self._create_statusbar()  # Pack statusbar BEFORE main layout
        self._create_main_layout()
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
        
        # Hamburger menu button (for toggling sidebar) - enhanced styling
        self.menu_btn = tk.Button(
            self.toolbar,
            text='☰',
            font=('Segoe UI', 24, 'bold'),
            bg=bg_header,
            fg=text_light,
            activebackground='#2c3e50',
            activeforeground='#3498db',
            relief='flat',
            bd=0,
            padx=15,
            pady=6,
            cursor='hand2',
            command=self._toggle_sidebar,
            highlightthickness=0,
            overrelief='flat'
        )
        self.menu_btn.pack(side='left', padx=(8, 12))
        
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
    
    def _update_license_status_label(self, is_valid: bool = None, expiry_date = None):
        """Update the license status display in toolbar.
        
        Args:
            is_valid: Optional override for license validity (e.g., from verify button result)
            expiry_date: Optional override for expiry date
        """
        try:
            # If not provided, fetch fresh status
            if is_valid is None:
                from licensing.license_manager import LicenseManager
                manager = LicenseManager()
                is_valid, msg, expiry_date = manager.validate_startup()
            
            if is_valid:
                if expiry_date:
                    from datetime import date
                    days_left = (expiry_date - date.today()).days
                    if days_left <= 7:
                        self.license_status_label.config(
                            text=f"⚠️ {days_left}d left",
                            fg=config.get_color('warning')
                        )
                    else:
                        self.license_status_label.config(
                            text=f"✅ Valid ({days_left}d)",
                            fg='#4caf50'
                        )
                else:
                    self.license_status_label.config(text='✅ Valid', fg='#4caf50')
            else:
                self.license_status_label.config(text='❌ Invalid', fg='#f44336')
        except Exception as e:
            logger.debug(f"Could not update license status label: {e}")
    
    def _verify_license_now(self):
        """Handle manual license verification button click"""
        try:
            from licensing.license_manager import LicenseManager
            from tkinter import messagebox
            
            manager = LicenseManager()
            
            # Check verification status BEFORE attempting
            status = manager.get_verification_status()
            if not status["can_verify"]:
                messagebox.showwarning(
                    "Verification Limit Reached",
                    f"⚠️ You have reached the daily verification limit.\n\n"
                    f"{status['message']}\n\n"
                    f"Resets at midnight (South Africa time)"
                )
                return
            
            self.license_verify_btn.config(state='disabled', text='⏳ Verifying...')
            self.root.update()
            
            is_valid, message, expiry_date = manager.validate_manual()
            
            # Update status label with ACTUAL verification result (not a fresh call)
            self._update_license_status_label(is_valid=is_valid, expiry_date=expiry_date)
            
            # Update button state based on new verification count
            self._update_verify_button_state()
            
            if is_valid:
                messagebox.showinfo(
                    "License Valid",
                    f"✅ Your license is active and valid.\n\n{message}"
                )
                logger.info("Manual license verification passed")
            else:
                # Check if limit was reached
                if "limit reached" in message.lower():
                    messagebox.showwarning(
                        "Verification Limit",
                        f"⚠️ {message}"
                    )
                else:
                    messagebox.showerror(
                        "License Invalid",
                        f"❌ License verification failed:\n\n{message}\n\nPlease contact support@water-balance.com"
                    )
                    logger.warning(f"Manual license verification failed: {message}")
                
        except Exception as e:
            logger.exception(f"License verification error: {e}")
            messagebox.showerror(
                "Verification Error",
                f"Could not verify license:\n{str(e)}\n\nCheck your internet connection."
            )
        finally:
            # Update button state
            self._update_verify_button_state()
    
    def _update_verify_button_state(self):
        """Update verify button state based on verification count."""
        try:
            from licensing.license_manager import LicenseManager
            manager = LicenseManager()
            status = manager.get_verification_status()
            
            if status["can_verify"]:
                self.license_verify_btn.config(
                    state='normal',
                    text=f'🔐 Verify License ({status["count"]}/3)'
                )
            else:
                self.license_verify_btn.config(
                    state='disabled',
                    text=f'⏸️ Limit Reached (resets in {status["time_until_reset"]})'
                )
        except Exception as e:
            logger.debug(f"Could not update verify button state: {e}")
            self.license_verify_btn.config(state='normal', text='🔐 Verify License')
    
    def _create_main_layout(self):
        """Create sidebar and content area layout"""
        # Main content frame (expands to fill available space between toolbar and statusbar)
        self.main_frame = ttk.Frame(self.container)
        self.main_frame.pack(fill='both', expand=True)
        
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
        
        # Sidebar header - Enhanced styling (no hamburger icon, just label)
        header_frame = tk.Frame(self.sidebar, bg='#34495e', height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="Navigation",
            font=('Segoe UI', 13, 'bold'),
            fg='white',
            bg='#34495e',
            anchor='w',
            padx=20,
            pady=18
        ).pack(fill='x')
        
        # Navigation menu items
        self.nav_buttons = {}
        
        menu_items = [
            ('dashboard', '📊 Dashboard', 'Water balance overview and KPIs'),
            ('analytics', '📈 Analytics & Trends', 'Statistical analysis and trend graphs'),
            ('monitoring_data', '🔍 Monitoring Data', 'Environmental and operational monitoring from Excel'),
            ('storage', '💧 Storage Facilities', 'Manage dams and water storage'),
            ('calculations', '⚙️ Calculations', 'Water balance calculations and results'),
            ('flow_diagram', '🌊 Flow Diagram', 'Visual water balance flow with inputs/outputs/processes'),
            ('settings', '⚡ Settings', 'System configuration and backups'),
        ]
        
        for module_id, label, tooltip in menu_items:
            self._create_nav_button(module_id, label, tooltip)
        
        # Separator with better styling
        separator_frame = tk.Frame(self.sidebar, bg=bg_sidebar, height=20)
        separator_frame.pack(fill='x', padx=10, pady=(10, 5))
        separator_line = tk.Frame(separator_frame, bg='#555555', height=1)
        separator_line.pack(fill='x', padx=10, pady=8)
        
        # Help and About at bottom
        help_items = [
            ('help', '❓ Help', 'User guide and documentation'),
            ('about', 'ℹ️ About', 'About this application'),
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
    
    def _toggle_sidebar(self):
        """Toggle sidebar visibility to save screen space"""
        if self.sidebar_collapsed:
            # Expand sidebar
            self.sidebar.pack(side='left', fill='y', before=self.content_area)
            self.sidebar_collapsed = False
            # Update hamburger button to show it's expanded
            self.menu_btn.config(relief='flat', bg=config.get_color('bg_header'))
        else:
            # Collapse sidebar
            self.sidebar.pack_forget()
            self.sidebar_collapsed = True
            # Highlight hamburger button when collapsed
            self.menu_btn.config(relief='solid', bg=config.get_color('primary_light'))
    
    def _create_nav_button(self, module_id, label, tooltip):
        """Create a navigation button in sidebar"""
        bg_sidebar = config.get_color('bg_sidebar')
        text_light = config.get_color('text_light')
        primary_light = config.get_color('primary_light')
        
        btn = tk.Button(
            self.sidebar,
            text=label,
            font=('Segoe UI', 10, 'bold'),
            fg=text_light,
            bg=bg_sidebar,
            activebackground='#3498db',
            activeforeground='white',
            relief='flat',
            anchor='w',
            padx=18,
            pady=14,
            cursor='hand2',
            bd=0,
            command=lambda: self.load_module(module_id)
        )
        btn.pack(fill='x', padx=6, pady=3)
        
        # Store module_id for reference
        btn.module_id = module_id
        
        # Tooltip (simple version)
        self._bind_tooltip(btn, tooltip)
        
        # Enhanced hover effects with smooth transitions
        def on_enter(e):
            btn.config(bg='#3498db', fg='white')
            btn.config(relief='solid', bd=1)
        
        def on_leave(e):
            # Check if this button is active
            if hasattr(btn, 'module_id') and btn.module_id == getattr(self, 'current_module', None):
                btn.config(bg='#2980b9', fg='white', relief='solid', bd=1)
            else:
                btn.config(bg=bg_sidebar, fg=text_light, relief='flat', bd=0)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
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
        """Create bottom status bar with clean styling"""
        statusbar_height = config.get('ui.statusbar_height', 28)
        bg_secondary = '#2c3e50'  # Darker background for contrast
        text_secondary = '#e8eef5'  # Light blue text
        
        self.statusbar = tk.Frame(
            self.container,
            bg=bg_secondary,
            height=statusbar_height,
            relief='flat',
            bd=0,
            highlightthickness=0
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
            padx=15
        )
        self.statusbar_label.pack(side='left', fill='x', expand=True)
        
        # Version info
        version_label = tk.Label(
            self.statusbar,
            text=f"v{config.app_version}",
            font=config.get_font('caption'),
            fg=text_secondary,
            bg=bg_secondary,
            anchor='e',
            padx=10
        )
        version_label.pack(side='right')

        # License status
        license_text = LicenseManager().status_summary()
        self.license_label = tk.Label(
            self.statusbar,
            text=license_text,
            font=config.get_font('caption'),
            fg=text_secondary,
            bg=bg_secondary,
            anchor='e',
            padx=8
        )
        self.license_label.pack(side='right')

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
        
        # Store current module for hover effects
        self.current_module = active_id
        
        for module_id, btn in self.nav_buttons.items():
            if module_id == active_id:
                # Active button: blue background with white text and border
                btn.config(bg='#2980b9', fg='white', relief='solid', bd=1)
            else:
                # Inactive button: default sidebar background
                btn.config(bg=bg_sidebar, fg=config.get_color('text_light'), relief='flat', bd=0)
    
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
        """Load the About page with enhanced styling and information"""
        bg_main = config.get_color('bg_main')
        bg_secondary = config.get_color('bg_secondary')
        text_primary = config.get_color('text_primary')
        text_secondary = config.get_color('text_secondary')
        accent = config.get_color('accent')
        
        container = tk.Frame(self.content_area, bg=bg_main)
        container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Create scrollable canvas
        canvas = tk.Canvas(container, bg=bg_main, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_main)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                # Canvas was destroyed (likely during tab switch), ignore
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Create main frame inside scrollable frame
        main_frame = tk.Frame(scrollable_frame, bg=bg_main)
        main_frame.pack(fill='both', expand=True, padx=40, pady=50)
        
        # HEADER SECTION
        header_frame = tk.Frame(main_frame, bg=bg_main)
        header_frame.pack(fill='x', pady=(0, 40))
        
        company = tk.Label(
            header_frame,
            text="🏢 TransAfrica Resources",
            font=('Segoe UI', 28, 'bold'),
            fg=accent,
            bg=bg_main
        )
        company.pack(pady=(0, 10))
        
        app_title = tk.Label(
            header_frame,
            text=f"💧 {config.app_name}",
            font=('Segoe UI', 22, 'bold'),
            fg=text_primary,
            bg=bg_main
        )
        app_title.pack(pady=(0, 8))
        
        version_text = tk.Label(
            header_frame,
            text=f"Version {config.app_version}",
            font=('Segoe UI', 13),
            fg=text_secondary,
            bg=bg_main
        )
        version_text.pack(pady=(0, 15))
        
        # DIVIDER
        divider = tk.Frame(main_frame, height=2, bg=accent, relief='flat')
        divider.pack(fill='x', pady=(0, 30))
        
        # DESCRIPTION SECTION
        desc_title = tk.Label(
            main_frame,
            text="About This Application",
            font=('Segoe UI', 14, 'bold'),
            fg=text_primary,
            bg=bg_main
        )
        desc_title.pack(anchor='w', pady=(0, 10))
        
        description = tk.Label(
            main_frame,
            text="A comprehensive water balance management system designed for mining operations. "
                 "Tracks all water inflows, outflows, and storage changes to ensure accurate "
                 "water management and regulatory compliance across multiple facilities.",
            font=('Segoe UI', 11),
            fg=text_primary,
            bg=bg_main,
            justify='left',
            wraplength=700
        )
        description.pack(anchor='w', pady=(0, 30))
        
        # KEY CAPABILITIES SECTION
        features_title = tk.Label(
            main_frame,
            text="✨ Core Capabilities",
            font=('Segoe UI', 14, 'bold'),
            fg=text_primary,
            bg=bg_main
        )
        features_title.pack(anchor='w', pady=(0, 12))
        
        features_frame = tk.Frame(main_frame, bg=bg_main)
        features_frame.pack(fill='x', anchor='w', pady=(0, 30))
        
        features = [
            ("📊", "6 Dashboard Views", "Main, KPI, Analytics, Charts, Flow Diagram, Monitoring"),
            ("💧", "Complete Water Tracking", "6 inflow sources + 7 outflow components with detailed breakdown"),
            ("🏗️", "Storage Management", "Track multiple facilities with real-time volume and capacity monitoring"),
            ("📈", "Real-time Calculations", "Advanced water balance engine with closure error validation"),
            ("📋", "Professional Reporting", "Generate compliance reports and export data for analysis"),
            ("⚙️", "Configurable Parameters", "Adjust mining rates, TSF return %, seepage losses, and more"),
            ("🎨", "Modern Interface", "Intuitive user experience with professional styling and navigation"),
            ("📡", "Excel Integration", "Seamless integration with Water_Balance_TimeSeries_Template.xlsx")
        ]
        
        for icon, title, desc in features:
            feature_item = tk.Frame(features_frame, bg=bg_main)
            feature_item.pack(fill='x', pady=8)
            
            icon_label = tk.Label(
                feature_item,
                text=icon,
                font=('Segoe UI', 14),
                fg=accent,
                bg=bg_main,
                width=3
            )
            icon_label.pack(side='left', padx=(0, 12))
            
            text_frame = tk.Frame(feature_item, bg=bg_main)
            text_frame.pack(side='left', fill='x', expand=True)
            
            feature_title_lbl = tk.Label(
                text_frame,
                text=title,
                font=('Segoe UI', 11, 'bold'),
                fg=text_primary,
                bg=bg_main,
                justify='left'
            )
            feature_title_lbl.pack(anchor='w')
            
            feature_desc_lbl = tk.Label(
                text_frame,
                text=desc,
                font=('Segoe UI', 10),
                fg=text_secondary,
                bg=bg_main,
                justify='left',
                wraplength=600
            )
            feature_desc_lbl.pack(anchor='w')
        
        # COMPANY INFORMATION SECTION
        company_title = tk.Label(
            main_frame,
            text="🏢 Company Information",
            font=('Segoe UI', 14, 'bold'),
            fg=text_primary,
            bg=bg_main
        )
        company_title.pack(anchor='w', pady=(30, 12))
        
        company_items = [
            ("Organization", "TransAfrica Resources (Pty) Ltd"),
            ("Industry", "Mining & Water Management"),
            ("Headquarters", "South Africa"),
            ("Focus", "Advanced water balance and environmental compliance"),
            ("Mission", "Provide innovative solutions for sustainable water management in mining operations")
        ]
        
        for label, value in company_items:
            company_row = tk.Frame(main_frame, bg=bg_main)
            company_row.pack(fill='x', pady=4)
            
            label_widget = tk.Label(
                company_row,
                text=label,
                font=('Segoe UI', 10, 'bold'),
                fg=accent,
                bg=bg_main,
                anchor='w',
                width=20
            )
            label_widget.pack(side='left')
            
            value_widget = tk.Label(
                company_row,
                text=value,
                font=('Segoe UI', 10),
                fg=text_primary,
                bg=bg_main,
                justify='left',
                wraplength=550
            )
            value_widget.pack(side='left', fill='x', expand=True)
        
        # CONTACT SECTION
        contact_frame = tk.Frame(main_frame, bg='#f5f5f5', relief='solid', bd=1)
        contact_frame.pack(fill='x', pady=(30, 30), padx=0)
        
        contact_title = tk.Label(
            contact_frame,
            text="📞 Contact Information",
            font=('Segoe UI', 13, 'bold'),
            fg=accent,
            bg='#f5f5f5'
        )
        contact_title.pack(pady=(15, 10), padx=15)
        
        contact_info = [
            ("Email", "caliphs@transafreso.com"),
            ("Email", "kali@transafreso.com"),
            ("Phone", "+27 82 355 8130"),
            ("Phone", "+27 235 76 07")
        ]
        
        for contact_type, contact_value in contact_info:
            contact_item = tk.Frame(contact_frame, bg='#f5f5f5')
            contact_item.pack(fill='x', pady=4, padx=15)
            
            type_label = tk.Label(
                contact_item,
                text=f"{contact_type}:",
                font=('Segoe UI', 10, 'bold'),
                fg='#333333',
                bg='#f5f5f5',
                width=10,
                anchor='w'
            )
            type_label.pack(side='left')
            
            value_label = tk.Label(
                contact_item,
                text=contact_value,
                font=('Segoe UI', 10),
                fg='#666666',
                bg='#f5f5f5'
            )
            value_label.pack(side='left', padx=10)
        
        # DEVELOPER INFORMATION SECTION
        dev_title = tk.Label(
            main_frame,
            text="👨‍💻 Development Team",
            font=('Segoe UI', 14, 'bold'),
            fg=text_primary,
            bg=bg_main
        )
        dev_title.pack(anchor='w', pady=(30, 12))
        
        dev_frame = tk.Frame(main_frame, bg=bg_main)
        dev_frame.pack(fill='x', anchor='w', pady=(0, 30))
        
        developers = [
            {
                "name": "Caliphs Nyamudzanha",
                "role": "Lead Developer & Project Manager",
                "expertise": "Full-stack Python development, UI/UX design, water balance calculations",
                "contact": "caliphs@transafreso.com"
            },
            {
                "name": "Kali Nyamudzanha",
                "role": "Developer & Business Analyst",
                "expertise": "Database design, reporting systems, business process optimization",
                "contact": "kali@transafreso.com"
            }
        ]
        
        for dev in developers:
            dev_item = tk.Frame(dev_frame, bg='#f5f5f5', relief='solid', bd=1)
            dev_item.pack(fill='x', pady=10)
            
            name_label = tk.Label(
                dev_item,
                text=dev["name"],
                font=('Segoe UI', 11, 'bold'),
                fg=accent,
                bg='#f5f5f5'
            )
            name_label.pack(anchor='w', padx=15, pady=(12, 2))
            
            role_label = tk.Label(
                dev_item,
                text=dev["role"],
                font=('Segoe UI', 10, 'bold'),
                fg='#333333',
                bg='#f5f5f5'
            )
            role_label.pack(anchor='w', padx=15, pady=(0, 4))
            
            expertise_label = tk.Label(
                dev_item,
                text=f"Expertise: {dev['expertise']}",
                font=('Segoe UI', 9),
                fg='#666666',
                bg='#f5f5f5',
                justify='left',
                wraplength=650
            )
            expertise_label.pack(anchor='w', padx=15, pady=(0, 4))
            
            email_label = tk.Label(
                dev_item,
                text=f"📧 {dev['contact']}",
                font=('Segoe UI', 9),
                fg='#666666',
                bg='#f5f5f5'
            )
            email_label.pack(anchor='w', padx=15, pady=(0, 12))
        
        # SYSTEM INFO SECTION
        info_title = tk.Label(
            main_frame,
            text="🔧 System Information",
            font=('Segoe UI', 14, 'bold'),
            fg=text_primary,
            bg=bg_main
        )
        info_title.pack(anchor='w', pady=(30, 12))
        
        info_items = [
            ("Default Mining Water Rate:", "1.43 m³/tonne"),
            ("Default TSF Return Rate:", "56%"),
            ("Seepage Loss Rate:", "0.5% per month"),
            ("Closure Error Threshold:", "±5% (Excel standard)"),
            ("Calculation Basis:", "Monthly periods"),
            ("Database:", "SQLite (water_balance.db)"),
            ("Python Version:", "3.11+")
        ]
        
        for label, value in info_items:
            info_row = tk.Frame(main_frame, bg=bg_main)
            info_row.pack(fill='x', pady=4)
            
            label_widget = tk.Label(
                info_row,
                text=label,
                font=('Segoe UI', 10, 'bold'),
                fg=text_primary,
                bg=bg_main,
                anchor='w',
                width=35
            )
            label_widget.pack(side='left')
            
            value_widget = tk.Label(
                info_row,
                text=value,
                font=('Segoe UI', 10),
                fg=text_secondary,
                bg=bg_main
            )
            value_widget.pack(side='left')
        
        # COPYRIGHT
        copyright = tk.Label(
            main_frame,
            text="© 2025 TransAfrica Resources (Pty) Ltd. All rights reserved.",
            font=('Segoe UI', 9),
            fg=text_secondary,
            bg=bg_main
        )
        copyright.pack(pady=(40, 0))
    
    def _update_statusbar(self):
        """Update status bar with current module info"""
        module_names = {
            'dashboard': 'Dashboard - Water Balance Overview',
            'storage': 'Storage Facilities Management',
            'calculations': 'Water Balance Calculations',
            'settings': 'Settings & Configuration',
            'help': 'Help & Documentation',
        }
        
        status_text = module_names.get(self.current_module, 'Ready')
        self.statusbar_label.config(text=status_text)
    
    def _update_status_message(self, message: str):
        """Update status bar with custom message (used by notifier)"""
        if hasattr(self, 'statusbar_label'):
            self.statusbar_label.config(text=message)
    
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
        from ui.settings import SettingsModule
        module = SettingsModule(self.content_area, initial_tab=tab)
        module.load()

    def _load_extended_summary(self):
        """Load extended summary GUI module"""
        from ui.extended_summary_view import ExtendedSummaryView
        view = ExtendedSummaryView(self.content_area)
        view.load()
        view.pack(fill='both', expand=True, padx=15, pady=10)
