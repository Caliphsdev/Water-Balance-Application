"""
PySide6 Water Balance Application - Entry Point

This is the main entry point for the Water Balance Dashboard application.
Sets up critical environment variables before importing any modules.
"""
import sys
import os
from pathlib import Path

# CRITICAL: Set WATERBALANCE_USER_DIR BEFORE any imports
# This ensures config/db/license use correct paths (same pattern as Tkinter)
user_base = Path(__file__).parent.parent
os.environ['WATERBALANCE_USER_DIR'] = str(user_base)

# Now safe to import PySide6 and app modules
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.components.splash_screen import SplashScreen
from ui.main_window import MainWindow
from core.app_logger import logger

def main():
    """Bootstrap PySide6 Water Balance Application.
    
    Shows splash screen while loading database, pages, and resources.
    Creates QApplication instance and shows main window when ready.
    Exits with application return code.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Water Balance Dashboard")
    app.setOrganizationName("Two Rivers Platinum")
    
    # Show splash screen immediately
    splash = SplashScreen()
    splash.show()
    app.processEvents()  # Force splash to render
    
    # Create main window in background (loads pages, db, etc.)
    splash.update_status("Loading database...", 20)
    app.processEvents()
    
    window = MainWindow(splash)  # Pass splash to update progress
    
    # Close splash and show main window after short delay
    def finish_loading():
        splash.update_status("Ready!", 100)
        QTimer.singleShot(300, lambda: (splash.finish(), window.show()))
    
    QTimer.singleShot(100, finish_loading)
    
    # Run application and capture exit code
    exit_code = app.exec()
    
    # Shutdown background logger (flush all queued messages)
    logger.shutdown()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
