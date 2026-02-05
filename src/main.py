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


def check_license(app: QApplication, splash: SplashScreen) -> bool:
    """
    Check license validity on startup.
    
    Returns True if license is valid, False if app should exit.
    Shows activation dialog if not activated.
    Shows blocked dialog if license is expired/revoked.
    """
    try:
        from ui.dialogs.license_dialog import check_license_or_activate
        
        splash.update_status("Checking license...", 10)
        app.processEvents()
        
        # Hide splash during license dialogs
        splash.hide()
        
        # Check license and show dialogs if needed
        result = check_license_or_activate(None)
        
        if result:
            splash.show()
            logger.info("License check passed")
            return True
        else:
            return False
            
    except ImportError:
        # License modules not available - skip check (dev mode)
        logger.warning("License modules not available, skipping license check")
        return True
    except Exception as e:
        logger.error(f"License check error: {e}")
        # On error, allow app to run (graceful degradation)
        return True
def start_background_services() -> None:
    """Start background services after main window is shown."""
    try:
        # Start notification sync (uses QTimer internally)
        from services.notification_service import get_notification_service
        service = get_notification_service()
        service.start_background_sync()
        logger.info("Notification background sync scheduled")
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Failed to start background services: {e}")


def main():
    """Bootstrap PySide6 Water Balance Application.
    
    Shows splash screen while loading database, pages, and resources.
    Creates QApplication instance and shows main window when ready.
    Exits with application return code.
    """
    # Install global exception hook
    import sys
    def excepthook(exc_type, exc_value, exc_tb):
        import traceback
        print("[EXCEPTION] Uncaught exception:", flush=True)
        traceback.print_exception(exc_type, exc_value, exc_tb)
    sys.excepthook = excepthook
    
    app = QApplication(sys.argv)
    app.setApplicationName("Water Balance Dashboard")
    app.setOrganizationName("Two Rivers Platinum")
    
    
    # Show splash screen immediately
    splash = SplashScreen()
    splash.show()
    app.processEvents()  # Force splash to render
    
    # Check license before loading main app
    if not check_license(app, splash):
        logger.info("License check failed, exiting")
        sys.exit(1)
    
    # Create main window in background (loads pages, db, etc.)
    splash.update_status("Loading database...", 20)
    app.processEvents()
    
    window = MainWindow(splash)  # Pass splash to update progress
    
    # Close splash and show main window after short delay
    def finish_loading():
        """Close splash screen and display main window."""
        splash.update_status("Ready!", 100)
        def show_window():
            splash.finish()
            window.show()
            window.raise_()
            window.activateWindow()
        QTimer.singleShot(300, show_window)
        # Start background services after window is shown
        QTimer.singleShot(1000, start_background_services)
    
    # IMPORTANT: Store reference to timer to prevent garbage collection
    # Give timer a parent (app) for proper Qt object lifecycle
    finish_timer = QTimer(app)
    finish_timer.setSingleShot(True)
    finish_timer.timeout.connect(finish_loading)
    finish_timer.start(100)
    
    # Run application and capture exit code
    exit_code = app.exec()
    
    # Shutdown background logger (flush all queued messages)
    logger.shutdown()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
