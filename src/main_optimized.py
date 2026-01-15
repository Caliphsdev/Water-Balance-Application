"""
Water Balance Management System - Optimized Launcher
Fast startup with splash screen and lazy module loading

Author: Water Balance Development Team
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add src to path FIRST (before any other imports)
sys.path.insert(0, str(Path(__file__).parent))

# Only import critical modules for loading screen
import tkinter as tk
from ui.loading_screen import LoadingScreen


def initialize_app(set_status):
    """
    Initialize application with progress updates
    Uses lazy imports to speed up initial loading screen display
    
    Args:
        set_status: Function to call with (status_text, progress_percentage)
    """
    
    # Step 1: Load configuration (10%)
    set_status("Loading configuration...", 5)
    from utils.config_manager import config
    from utils.app_logger import logger
    set_status("Loading configuration...", 10)
    
    # Step 2: Initialize logging (20%)
    set_status("Initializing logging...", 15)
    logger.info("=" * 60)
    logger.info("Water Balance Application Started")
    logger.info("=" * 60)
    logger.info(f"Version: {config.app_version}")
    logger.info(f"Python: {sys.version}")
    set_status("Initializing logging...", 20)
    
    # Step 3: Load database (40%)
    set_status("Connecting to database...", 25)
    from database.db_manager import db
    set_status("Connecting to database...", 30)
    
    set_status("Preloading caches...", 35)
    db.preload_caches()
    logger.info("Database caches preloaded")
    set_status("Preloading caches...", 40)
    
    # Step 4: Load utilities (55%)
    set_status("Loading utilities...", 45)
    from utils.ui_notify import notifier
    from utils.error_handler import error_handler
    set_status("Loading utilities...", 50)
    
    set_status("Loading theme engine...", 52)
    from ttkthemes import ThemedTk
    set_status("Loading theme engine...", 55)
    
    # Step 5: Create main window (75%)
    set_status("Creating main window...", 60)
    from tkinter import ttk, messagebox
    
    # Set default user
    config.set_current_user('admin')
    logger.info("Default user set: admin")
    
    # Create themed root window
    root = ThemedTk(theme=config.theme)
    root.withdraw()  # Hide until fully loaded
    root.title(config.window_title)
    root.geometry(config.window_geometry)
    logger.info(f"Window created: {config.window_geometry}")
    root._closing = False
    
    # Set minimum window size
    min_width = config.get('window.min_width', 1200)
    min_height = config.get('window.min_height', 700)
    root.minsize(min_width, min_height)
    
    set_status("Creating main window...", 70)
    
    # Step 6: Apply styles (85%)
    set_status("Applying custom styles...", 75)
    _apply_custom_styles(root, config)
    logger.info("Custom styles applied")
    set_status("Applying custom styles...", 80)
    
    # Step 7: Load main window (95%)
    set_status("Building interface...", 85)
    from ui.main_window import MainWindow
    main_window = MainWindow(root)
    logger.info("Main window initializing")
    set_status("Building interface...", 90)
    
    # Step 8: Final setup (100%)
    set_status("Finalizing...", 95)
    _center_window(root)
    
    # Bind close event
    def on_closing():
        if getattr(root, '_closing', False):
            return
        try:
            if not root.winfo_exists():
                return
        except:
            return
        logger.user_action("Application close requested")
        if notifier.confirm("Are you sure you want to exit?", "Confirm Exit"):
            root._closing = True
            logger.info("Application closing - user confirmed")
            logger.info("=" * 60)
            logger.info("Water Balance Application Stopped")
            logger.info("=" * 60)
            root.destroy()
        else:
            logger.info("Application close cancelled by user")
            root._closing = False
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    set_status("Ready!", 98)
    logger.info("Application initialization complete")
    
    # Show window
    root.deiconify()
    root.lift()
    
    set_status("Complete!", 100)
    
    # Return root for main loop
    return root


def _apply_custom_styles(root, config):
    """Apply custom ttk styles for professional appearance"""
    from tkinter import ttk
    
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


def _center_window(root):
    """Center the window on the screen"""
    root.update_idletasks()
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Get window dimensions
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    
    # Calculate position
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    root.geometry(f'+{x}+{y}')


def main():
    """Application entry point with loading screen"""
    loading_screen = None
    try:
        # Get version early (minimal import)
        from utils.config_manager import config
        app_version = config.app_version
        
        # Show loading screen
        loading_screen = LoadingScreen()
        loading_screen.show()
        
        # Initialize app with progress updates
        root = initialize_app(loading_screen.set_status)
        
        # Close loading screen
        loading_screen.close()
        loading_screen = None
        
        from utils.app_logger import logger
        logger.info("Starting main event loop")
        
        # Start the event loop
        root.mainloop()
        
    except KeyboardInterrupt:
        if loading_screen:
            try:
                loading_screen.close()
            except:
                pass
        try:
            from utils.app_logger import logger
            logger.info("Application interrupted by user (Ctrl+C)")
        except:
            print("Application interrupted by user (Ctrl+C)")
    
    except Exception as e:
        if loading_screen:
            try:
                loading_screen.close()
            except:
                pass
        # Try to use logger and error handler if available
        try:
            from utils.app_logger import logger
            from utils.error_handler import error_handler
            from tkinter import messagebox
            
            logger.exception("Fatal error in main application")
            tech_msg, user_msg, severity = error_handler.handle(
                e,
                context="Main application",
                suppress=True
            )
            messagebox.showerror(
                "Fatal Error",
                f"{user_msg}\n\nThe application will now close.\n\nTechnical details:\n{tech_msg}"
            )
        except:
            # Fallback if utilities not loaded
            print(f"FATAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    finally:
        try:
            from utils.app_logger import logger
            logger.info("Application terminated")
        except:
            print("Application terminated")
        # Force exit to ensure process terminates
        sys.exit(0)


if __name__ == "__main__":
    main()
