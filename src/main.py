"""
Water Balance Management System - Main Application
Professional Tkinter application with modern UI/UX for mine water balance management

Author: Water Balance Development Team
Version: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import sys
from pathlib import Path
import threading
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import config
from utils.app_logger import logger
from utils.ui_notify import notifier
from utils.error_handler import error_handler
from ui.main_window import MainWindow
from database.db_manager import db
from utils.flow_volume_loader import get_flow_volume_loader, reset_flow_volume_loader
from ui.loading_screen import LoadingScreen
from licensing.license_manager import LicenseManager
from ui.license_dialog import show_license_dialog

# New: Async loading support (Phase 1: Fast Startup)
from utils.async_loader import get_loader, load_database_blocking


class WaterBalanceApp:
    """Main application controller"""
    
    def __init__(self):
        """Initialize the Water Balance Application"""
        self.root = None
        self.main_window = None
        self.loading_screen = None
        self.db_loaded = False
        self.mainloop_started = False
        self.pending_db_callback = None
        
        # License manager for background checks
        self.license_manager = LicenseManager()
        self.license_check_thread = None
        self.license_check_running = False
        self.last_license_status = True  # Assume valid until proven otherwise
        
    def initialize(self):
        """Initialize the application window and components"""
        try:
            logger.info("Initializing Water Balance Application")
            logger.info(f"Version: {config.app_version}")
            logger.info(f"Python: {sys.version}")
            
            # Set default user
            config.set_current_user('admin')
            logger.info("Default user set: admin")
            
            # Check if fast startup feature is enabled
            fast_startup_enabled = config.get('features.fast_startup', False)
            logger.info(f"Fast startup feature: {'ENABLED' if fast_startup_enabled else 'DISABLED'}")
            
            # Create themed root window FIRST (before loading screen)
            # This prevents multiple tk.Tk() instances which cause window artifacts
            try:
                self.root = ThemedTk(theme=config.theme)
            except Exception as theme_err:
                logger.warning(f"Failed to initialize themed window ({config.theme}): {theme_err}. Falling back to standard Tk.")
                self.root = tk.Tk()
                # Apply basic background so user doesn't see black screen
                self.root.configure(bg=config.get_color('bg_main'))
            
            # IMPORTANT: Keep window completely hidden and off-screen until loading completes
            self.root.withdraw()
            self.root.attributes('-alpha', 0.0)  # Completely transparent - prevent any flashing
            self.root.geometry(f"+9999+9999")  # Move far off-screen
            
            # Now create loading screen using main root as parent
            self.loading_screen = LoadingScreen(root=self.root)
            self.loading_screen.set_status("Initializing application...", 0)
            self.loading_screen.show()
            logger.info("Professional loading screen displayed")
            
            # Set target geometry for later
            self.target_geometry = config.window_geometry
            
            self.root.title(config.window_title)
            logger.info(f"Window created: {config.window_geometry}")
            # Closing state flag to prevent double-confirm/destroy
            self.root._closing = False
            
            # Set minimum window size
            min_width = config.get('window.min_width', 1200)
            min_height = config.get('window.min_height', 700)
            self.root.minsize(min_width, min_height)
            
            # Apply DPI scaling for high-res displays
            self._apply_dpi_scaling()
            
            # Apply custom styles
            self._apply_custom_styles()
            logger.info("Custom styles applied")
            
            # Update loading screen
            self.loading_screen.set_status("Loading configuration...", 30)
            
            # Database loading: ASYNC (new) or BLOCKING (old)
            if fast_startup_enabled:
                # NEW: Async database loading - start in background
                self.loading_screen.set_status("Connecting to database...", 45)
                logger.info("Starting ASYNC database loading (fast startup)")
                self.db_loaded = False
                
                # Start async load (no loading indicator yet)
                loader = get_loader()
                loader.load_database_async(
                    db_path=db.db_path,
                    on_complete=self._on_database_loaded
                )
                
            else:
                # OLD: Blocking database load (traditional approach)
                self.loading_screen.set_status("Loading database...", 50)
                logger.info("Using BLOCKING database load (traditional mode)")
                db.preload_caches()
                logger.info("Database caches preloaded (blocking)")
                self.loading_screen.set_status("Initializing UI components...", 75)
                # Health check in blocking mode
                try:
                    stats = db.get_dashboard_stats()
                    logger.info(
                        f"DB Health: sources={stats.get('total_sources',0)}, facilities={stats.get('total_facilities',0)}, "
                        f"capacity={stats.get('total_capacity',0):.2f} Mm³, current={stats.get('total_current_volume',0):.2f} Mm³"
                    )
                    logger.info(f"Active DB: {db.db_path}")
                except Exception as hc_err:
                    logger.warning(f"DB health check failed: {hc_err}")
                self.db_loaded = True
            
            # Create main window
            try:
                self.loading_screen.set_status("Building interface...", 90)
                self.main_window = MainWindow(self.root)
                logger.info("Main window created successfully")
                self.loading_screen.set_status("Finalizing...", 100)
                    
            except Exception as mw_err:
                logger.exception(f"Main window failed to initialize: {mw_err}")
                # Provide visible fallback UI so user is not left with blank window
                fallback = tk.Frame(self.root, bg=config.get_color('bg_main'))
                fallback.pack(fill='both', expand=True)
                tk.Label(
                    fallback,
                    text="Initialization issue - please check logs.",
                    bg=config.get_color('bg_main'),
                    fg=config.get_color('text_primary'),
                    font=config.get_font('heading_small')
                ).pack(pady=40)
                tk.Button(
                    fallback,
                    text="Exit",
                    command=self.root.destroy,
                    padx=20,
                    pady=10
                ).pack()
                return True
            
            # Center window on screen
            self._center_window()
            
            # Schedule synchronized transition after loading completes
            # Loading screen: 3500ms min display
            # Add time for dashboard/window prep: 1000ms
            # Total: 4500ms for smooth synchronized fade transition
            loading_delay_ms = 4500
            
            def on_loading_complete():
                """Synchronized transition: fade out loading screen while fading in main window."""
                # Step 1: Prepare main window (invisible, off-screen)
                self.root.deiconify()  # Make visible (but still transparent)
                self.root.geometry(self.target_geometry)  # Move to center
                self.root.attributes('-alpha', 0.0)  # Start fully transparent
                
                # Step 2: Maximize window BEFORE dashboard load
                if self.main_window and not self.main_window._window_maximized:
                    logger.info("Maximizing window")
                    self.main_window._maximize_window()
                    self.main_window._window_maximized = True
                
                # Step 3: Load dashboard while main window still invisible
                if self.main_window and not self.main_window._dashboard_loaded:
                    logger.info("Loading dashboard")
                    self.main_window.load_module('dashboard')
                
                # Step 4: Process pending events to ensure UI is fully rendered
                self.root.update()
                import time
                time.sleep(0.05)  # Small delay to ensure all widgets rendered
                
                # Step 5: Synchronized smooth fade transition (300ms total)
                # Loading screen fades out while main window fades in
                try:
                    steps = 15  # More steps for smoother animation
                    step_delay = 20  # milliseconds between steps
                    
                    for i in range(1, steps + 1):
                        alpha_in = min(1.0, (i / steps))  # Main window fades in
                        alpha_out = max(0.0, (1.0 - (i / steps)))  # Loading screen fades out
                        
                        # Update main window opacity
                        try:
                            self.root.attributes('-alpha', alpha_in)
                        except:
                            pass
                        
                        # Update loading screen opacity
                        try:
                            if self.loading_screen:
                                self.loading_screen.root.attributes('-alpha', alpha_out)
                        except:
                            pass
                        
                        # Update display
                        self.root.update_idletasks()
                        
                        # Sleep for smooth animation
                        import time
                        time.sleep(step_delay / 1000.0)
                    
                    # Ensure fully visible
                    self.root.attributes('-alpha', 1.0)
                    
                    # Close loading screen (now invisible)
                    try:
                        self.loading_screen.stop_animation()
                        if self.loading_screen.own_root:
                            self.loading_screen.root.destroy()
                            if self.loading_screen.hidden_root:
                                self.loading_screen.hidden_root.destroy()
                        else:
                            self.loading_screen.root.withdraw()
                        self.loading_screen = None
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"Transition error: {e}")
                    # Fallback: just show window
                    self.root.attributes('-alpha', 1.0)
                    try:
                        if self.loading_screen:
                            self.loading_screen.root.withdraw()
                    except:
                        pass
                
                # Bring main window to front and focus
                try:
                    self.root.lift()
                    self.root.focus_force()
                except:
                    pass
            
            # Schedule to show app after loading screen fully completes
            self.root.after(loading_delay_ms, on_loading_complete)
            
            # Bind window close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Fix minimize/restore issue: ensure window properly restores from minimized state
            def on_map_event(event):
                """Handle window deiconify (restore from minimize)."""
                if event.widget == self.root:
                    self.root.attributes('-alpha', 1.0)  # Ensure fully visible
                    self.root.lift()
                    self.root.focus_force()
            
            self.root.bind("<Map>", on_map_event)
            
            logger.info("Application initialization complete")
            return True
            
        except Exception as e:
            # Close loading screen on error
            if self.loading_screen:
                try:
                    self.loading_screen.close()
                except:
                    pass
            tech_msg, user_msg, severity = error_handler.handle(
                e, 
                context="Application initialization",
                suppress=True
            )
            messagebox.showerror(
                "Initialization Error",
                f"{user_msg}\n\nThe application will now close.\n\nTechnical details:\n{tech_msg}"
            )
            logger.critical("Application initialization failed - exiting")
            return False
    
    def _apply_dpi_scaling(self):
        """Detect and apply DPI scaling for high-resolution displays."""
        try:
            if not config.get('window.auto_scale', True):
                return
            
            # Get screen DPI
            dpi = self.root.winfo_fpixels('1i')
            base_dpi = 96.0  # Standard DPI
            
            # Calculate scale factor
            scale = dpi / base_dpi
            user_scale = config.get('window.scale_factor', 1.0)
            final_scale = scale * user_scale
            
            # Apply scaling if significantly different from 1.0
            if abs(final_scale - 1.0) > 0.1:
                # Tkinter tk scaling
                self.root.tk.call('tk', 'scaling', final_scale * base_dpi / 72.0)
                logger.info(f"Applied DPI scaling: {final_scale:.2f}x (screen DPI: {dpi:.0f})")
        except Exception as e:
            logger.warning(f"Could not apply DPI scaling: {e}")
    
    def _apply_custom_styles(self):
        """Apply custom ttk styles for professional appearance"""
        style = ttk.Style()
        
        # Configure colors from config
        primary = config.get_color('primary')
        primary_dark = config.get_color('primary_dark')
        bg_main = config.get_color('bg_main')
        text_primary = config.get_color('text_primary')
        
        # Custom button style
        style.configure(
            'Primary.TButton',
            background=primary,
            foreground='white',
            borderwidth=0,
            focuscolor='none',
            padding=(12, 6)
        )
        
        style.map(
            'Primary.TButton',
            background=[('active', primary_dark), ('pressed', primary_dark)]
        )
        
        # Custom frame styles
        style.configure('Card.TFrame', background=bg_main, relief='flat', borderwidth=1)
        style.configure('Sidebar.TFrame', background=config.get_color('bg_sidebar'))
        
        # Custom label styles
        style.configure(
            'Heading.TLabel',
            font=config.get_font('heading_large'),
            foreground=text_primary
        )
        
        style.configure(
            'Subheading.TLabel',
            font=config.get_font('heading_medium'),
            foreground=text_primary
        )
        
        style.configure(
            'Body.TLabel',
            font=config.get_font('body'),
            foreground=text_primary
        )
        
        # Treeview (data grid) customization
        style.configure(
            'Treeview',
            font=config.get_font('body'),
            rowheight=28,
            borderwidth=0
        )
        
        style.configure(
            'Treeview.Heading',
            font=config.get_font('body_bold'),
            borderwidth=1,
            relief='flat'
        )
        
        style.map(
            'Treeview',
            background=[('selected', primary)],
            foreground=[('selected', 'white')]
        )
    
    def _on_database_loaded(self, db_manager, error):
        """Callback when async database loading completes (called from worker thread)"""
        # If mainloop hasn't started yet, store the callback data for later
        if not self.mainloop_started:
            self.pending_db_callback = (db_manager, error)
            logger.info("DB loaded, callback deferred until mainloop starts")
            return
            
        # Schedule UI updates on main thread using root.after()
        try:
            if self.root and self.root.winfo_exists():
                self.root.after(0, self._update_ui_after_db_load, db_manager, error)
        except Exception as e:
            logger.error(f"Error scheduling UI update: {e}")
    
    def _update_ui_after_db_load(self, db_manager, error):
        """Update UI after database loaded (runs on main thread)"""
        try:
            if error:
                logger.error(f"Database loading failed: {error}")
                
                # Show error and fallback to blocking load
                if messagebox.askyesno(
                    "Database Error",
                    f"Async database loading failed: {error}\n\nFallback to traditional loading?"
                ):
                    logger.info("Falling back to blocking database load")
                    try:
                        db.preload_caches()
                        self.db_loaded = True
                        logger.info("Fallback successful")
                    except Exception as fallback_error:
                        logger.exception("Fallback also failed")
                        messagebox.showerror(
                            "Critical Error",
                            f"Database cannot be loaded: {fallback_error}"
                        )
                else:
                    logger.info("User cancelled fallback - closing app")
                    self.root.destroy()
            else:
                logger.info("✅ Async database loading completed successfully")
                self.db_loaded = True
                
                # Preload caches now that DB is ready
                db.preload_caches()
                logger.info("Database caches preloaded (async)")
                # Health check: log key counts to confirm DB visibility
                try:
                    stats = db.get_dashboard_stats()
                    logger.info(
                        f"DB Health: sources={stats.get('total_sources',0)}, facilities={stats.get('total_facilities',0)}, "
                        f"capacity={stats.get('total_capacity',0):.2f} Mm³, current={stats.get('total_current_volume',0):.2f} Mm³"
                    )
                    logger.info(f"Active DB: {db.db_path}")
                except Exception as hc_err:
                    logger.warning(f"DB health check failed: {hc_err}")
                
        except Exception as e:
            logger.exception(f"Error in database loaded callback: {e}")
    
    def _center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Get window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f'+{x}+{y}')
    
    def on_closing(self):
        """Handle application close event - fast and clean."""
        # Avoid double invocation if already closing
        if getattr(self.root, '_closing', False):
            return
        
        # Check if window still exists
        try:
            if not self.root.winfo_exists():
                return
        except:
            return
    
    def on_closing(self):
        """Handle application close event."""
        logger.user_action("Application close requested")
        if notifier.confirm("Are you sure you want to exit?", "Confirm Exit"):
            self.root._closing = True
            
            # Stop background license check thread immediately (non-blocking)
            self.license_check_running = False
            if self.license_check_thread and self.license_check_thread.is_alive():
                # Don't wait - let daemon thread exit on its own
                pass
            
            # Clear caches asynchronously (don't block UI closure)
            def cleanup():
                try:
                    loader = get_flow_volume_loader()
                    loader.clear_cache()
                except:
                    pass
                try:
                    reset_flow_volume_loader()
                except:
                    pass
            
            # Schedule cleanup in background (doesn't block closing)
            threading.Thread(target=cleanup, daemon=True).start()
            
            logger.info("Application closing - user confirmed")
            logger.info("=" * 60)
            logger.info("Water Balance Application Stopped")
            logger.info("=" * 60)
            
            # Close immediately without waiting for cleanup
            self.root.destroy()
            self.root.quit()
        else:
            logger.info("Application close cancelled by user")
            self.root._closing = False
    
    def run(self):
        """Start the application main loop"""
        if self.initialize():
            self.mainloop_started = True
            
            # Process any pending database callback
            if self.pending_db_callback:
                db_manager, error = self.pending_db_callback
                self.pending_db_callback = None
                logger.info("Processing deferred DB callback")
                self.root.after(100, self._update_ui_after_db_load, db_manager, error)
            
            # Start background license check thread (professional approach)
            self._start_background_license_check()
            
            self.root.mainloop()
    
    def _start_background_license_check(self):
        """Start background thread for periodic license validation every 1-2 hours"""
        self.license_check_running = True
        self.license_check_thread = threading.Thread(
            target=self._background_license_check_loop,
            daemon=True  # Daemon thread - will exit when main app closes
        )
        self.license_check_thread.start()
        logger.info("Background license check thread started (every 1-2 hours)")
    
    def _background_license_check_loop(self):
        """Periodic license validation loop running in background thread"""
        # Check interval: 1 hour (3600 seconds)
        check_interval = config.get('licensing.background_check_interval_seconds', 3600)
        
        while self.license_check_running:
            try:
                # Wait for the check interval before first check
                time.sleep(check_interval)
                
                # Don't check if app is not fully initialized
                if not self.mainloop_started or not self.root.winfo_exists():
                    continue
                
                logger.debug("Running periodic background license check...")
                is_valid, message, expiry_date = self.license_manager.validate_background()
                
                # Only notify if status changed (license was valid, now invalid)
                if self.last_license_status and not is_valid:
                    self.last_license_status = False
                    logger.warning(f"❌ License status changed: {message}")
                    
                    # Show warning dialog on main thread
                    self.root.after(0, self._show_license_revoked_dialog, message)
                elif not self.last_license_status and is_valid:
                    self.last_license_status = True
                    logger.info("✅ License re-validated successfully")
                    
            except Exception as e:
                logger.debug(f"Background license check error (non-critical): {e}")
    
    def _show_license_revoked_dialog(self, message: str):
        """Show dialog when license is revoked during operation"""
        try:
            if not self.root.winfo_exists():
                return
                
            logger.warning("Showing license revocation dialog to user")
            # Show warning (not error) - gives user chance to save work
            result = messagebox.showwarning(
                "License Status Alert",
                f"Your license status has changed:\n\n{message}\n\nPlease save your work and restart the application.",
                type=messagebox.OKCANCEL
            )
            
            if result == messagebox.OK:
                # User acknowledged - optionally restart
                logger.info("User acknowledged license revocation notice")
        except Exception as e:
            logger.debug(f"Could not show dialog: {e}")


def main():
    """Application entry point"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Water Balance Management System")
        logger.info("=" * 60)

        # Enforce license validation before launching UI
        manager = LicenseManager()
        is_valid, reason, expiry_date = manager.validate_startup()
        if not is_valid:
            logger.warning(f"License check failed: {reason}")
            root = tk.Tk()
            root.withdraw()
            
            # Show informative error message to user based on reason
            if "revoked" in reason.lower():
                messagebox.showerror(
                    "License Revoked",
                    f"🚫 Your license has been revoked.\n\n{reason}\n\nThe application cannot start."
                )
                logger.critical("Application terminated: license revoked")
                root.destroy()
                sys.exit(1)
            elif "Hardware mismatch" in reason:
                # Allow transfer attempt
                success = show_license_dialog(parent=root, mode="transfer")
                root.destroy()
                if not success:
                    messagebox.showerror("License Required", f"{reason}\n\nPlease activate to continue.")
                    logger.critical("Application terminated: license validation failed")
                    sys.exit(1)
            else:
                # Regular activation dialog
                success = show_license_dialog(parent=root, mode="activate")
                root.destroy()
                if not success:
                    messagebox.showerror("License Required", f"{reason}\n\nPlease activate to continue.")
                    logger.critical("Application terminated: license validation failed")
                    sys.exit(1)
            
            # Re-validate after activation/transfer
            is_valid, reason, expiry_date = manager.validate_startup()
            if not is_valid:
                messagebox.showerror("License Invalid", reason)
                logger.critical("Application terminated: license validation failed after activation")
                sys.exit(1)
        
        app = WaterBalanceApp()
        app.run()  # run() already calls initialize()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user (Ctrl+C)")
    except Exception as e:
        logger.exception("Fatal error in main application")
        tech_msg, user_msg, severity = error_handler.handle(
            e,
            context="Main application",
            suppress=True
        )
        try:
            messagebox.showerror(
                "Fatal Error",
                f"{user_msg}\n\nThe application will now close.\n\nTechnical details:\n{tech_msg}"
            )
        except:
            print(f"FATAL ERROR: {user_msg}")
            print(f"Technical: {tech_msg}")
    finally:
        logger.info("Application terminated")
        # Force exit to ensure process terminates
        sys.exit(0)


if __name__ == "__main__":
    main()
