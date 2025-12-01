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

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import config
from utils.app_logger import logger
from utils.ui_notify import notifier
from utils.error_handler import error_handler
from ui.main_window import MainWindow
from database.db_manager import db


class WaterBalanceApp:
    """Main application controller"""
    
    def __init__(self):
        """Initialize the Water Balance Application"""
        self.root = None
        self.main_window = None
        
    def initialize(self):
        """Initialize the application window and components"""
        try:
            logger.info("Initializing Water Balance Application")
            logger.info(f"Version: {config.app_version}")
            logger.info(f"Python: {sys.version}")
            
            # Set default user
            config.set_current_user('admin')
            logger.info("Default user set: admin")
            
            # Preload database caches to avoid repeated queries during module initialization
            logger.info("Preloading database caches...")
            db.preload_caches()
            logger.info("Database caches preloaded")
            
            # Create themed root window with safe fallback
            try:
                self.root = ThemedTk(theme=config.theme)
            except Exception as theme_err:
                logger.warning(f"Failed to initialize themed window ({config.theme}): {theme_err}. Falling back to standard Tk.")
                self.root = tk.Tk()
                # Apply basic background so user doesn't see black screen
                self.root.configure(bg=config.get_color('bg_main'))
            self.root.title(config.window_title)
            self.root.geometry(config.window_geometry)
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
            
            # Create main window
            try:
                self.main_window = MainWindow(self.root)
                logger.info("Main window created successfully")
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
            
            # Bind window close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            logger.info("Application initialization complete")
            return True
            
        except Exception as e:
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
        """Handle application close event"""
        # Avoid double invocation if already closing
        if getattr(self.root, '_closing', False):
            return
        
        # Check if window still exists before showing dialog
        try:
            if not self.root.winfo_exists():
                return
        except:
            return
            
        logger.user_action("Application close requested")
        if notifier.confirm("Are you sure you want to exit?", "Confirm Exit"):
            self.root._closing = True
            logger.info("Application closing - user confirmed")
            logger.info("=" * 60)
            logger.info("Water Balance Application Stopped")
            logger.info("=" * 60)
            self.root.destroy()
        else:
            logger.info("Application close cancelled by user")
            self.root._closing = False
    
    def run(self):
        """Start the application main loop"""
        if self.initialize():
            self.root.mainloop()


def main():
    """Application entry point"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Water Balance Management System")
        logger.info("=" * 60)
        
        app = WaterBalanceApp()
        try:
            app.initialize()
            app.run()
        except Exception as e:
            try:
                # Try to use error handler and logger first
                error_handler.handle(e)
            except Exception:
                # Failsafe: Write error directly to log file
                import traceback
                log_path = Path(__file__).parent.parent / 'logs' / 'water_balance.log'
                log_path.parent.mkdir(exist_ok=True)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n[CRITICAL ERROR] {datetime.now()}\n{traceback.format_exc()}\n")
                print(f"Critical error written to {log_path}")
        
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


if __name__ == "__main__":
    main()
