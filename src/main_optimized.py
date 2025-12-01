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

# Only import critical modules for splash screen
import tkinter as tk
from ui.splash_screen import show_splash_and_load


def initialize_app(progress_callback):
    """
    Initialize application with progress updates
    Uses lazy imports to speed up initial splash display
    
    Args:
        progress_callback: Function to call with (value, status, detail)
    """
    
    # Step 1: Load configuration (10%)
    progress_callback(5, "Loading configuration...", "Reading config files")
    from utils.config_manager import config
    from utils.app_logger import logger
    progress_callback(10, "Configuration loaded", "")
    
    # Step 2: Initialize logging (20%)
    progress_callback(15, "Initializing logging...", "Setting up log handlers")
    logger.info("=" * 60)
    logger.info("Water Balance Application Started")
    logger.info("=" * 60)
    logger.info(f"Version: {config.app_version}")
    logger.info(f"Python: {sys.version}")
    progress_callback(20, "Logging initialized", "")
    
    # Step 3: Load database (40%)
    progress_callback(25, "Connecting to database...", "Opening SQLite connection")
    from database.db_manager import db
    progress_callback(30, "Database connected", "")
    
    progress_callback(35, "Preloading caches...", "Loading frequently used data")
    db.preload_caches()
    logger.info("Database caches preloaded")
    progress_callback(40, "Database ready", "")
    
    # Step 4: Load utilities (55%)
    progress_callback(45, "Loading utilities...", "Error handlers and notifications")
    from utils.ui_notify import notifier
    from utils.error_handler import error_handler
    progress_callback(50, "Utilities loaded", "")
    
    progress_callback(52, "Loading theme engine...", "Applying visual styles")
    from ttkthemes import ThemedTk
    progress_callback(55, "Theme loaded", "")
    
    # Step 5: Create main window (75%)
    progress_callback(60, "Creating main window...", "Initializing UI framework")
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
    
    progress_callback(70, "Window created", "")
    
    # Step 6: Apply styles (85%)
    progress_callback(75, "Applying custom styles...", "Configuring theme colors")
    _apply_custom_styles(root, config)
    logger.info("Custom styles applied")
    progress_callback(80, "Styles applied", "")
    
    # Step 7: Load main window (95%)
    progress_callback(85, "Building interface...", "Loading main application window")
    from ui.main_window import MainWindow
    main_window = MainWindow(root)
    logger.info("Main window initializing")
    progress_callback(90, "Interface built", "")
    
    # Step 8: Final setup (100%)
    progress_callback(95, "Finalizing...", "Positioning window")
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
    
    progress_callback(98, "Ready!", "Starting application...")
    logger.info("Application initialization complete")
    
    # Show window
    root.deiconify()
    root.lift()
    
    progress_callback(100, "Complete!", "")
    
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
    """Application entry point with splash screen"""
    try:
        # Get version early (minimal import)
        from utils.config_manager import config
        app_version = config.app_version
        
        # Show splash and initialize app
        show_splash_and_load(app_version, initialize_app)
        
        # Get root window and start main loop
        # Note: root is created inside initialize_app and is already visible
        # We just need to start the event loop
        from utils.app_logger import logger
        logger.info("Starting main event loop")
        
        # The root window is already created and visible, just keep it running
        tk.mainloop()
        
    except KeyboardInterrupt:
        try:
            from utils.app_logger import logger
            logger.info("Application interrupted by user (Ctrl+C)")
        except:
            print("Application interrupted by user (Ctrl+C)")
    
    except Exception as e:
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


if __name__ == "__main__":
    main()
