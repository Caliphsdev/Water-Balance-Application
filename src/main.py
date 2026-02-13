"""
PySide6 Water Balance Application - Entry Point

This is the main entry point for the Water Balance Dashboard application.
Sets up critical environment variables before importing any modules.
"""
import sys
import os
import shutil
import yaml
from pathlib import Path

# CRITICAL: Set WATERBALANCE_USER_DIR BEFORE any imports
# This ensures config/db/license use correct paths (same pattern as Tkinter)
def _get_user_base() -> Path:
    if getattr(sys, "frozen", False):
        local_appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(local_appdata) if local_appdata else (Path.home() / "AppData" / "Local")
        return base / "WaterBalanceDashboard"
    return Path(__file__).parent.parent


def _find_packaged_base() -> Path:
    if getattr(sys, "frozen", False):
        exe_base = Path(sys.executable).parent
        internal = exe_base / "_internal"
        return internal if internal.exists() else exe_base
    return Path(__file__).parent.parent


def _read_config_version(config_path: Path) -> str | None:
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return data.get("app", {}).get("version")
    except Exception:
        return None


def _ensure_user_data(user_base: Path, packaged_base: Path) -> None:
    (user_base / "config").mkdir(parents=True, exist_ok=True)
    (user_base / "data").mkdir(parents=True, exist_ok=True)
    (user_base / "logs").mkdir(parents=True, exist_ok=True)

    user_cfg = user_base / "config" / "app_config.yaml"
    cfg_src = packaged_base / "config" / "app_config.yaml"
    if cfg_src.exists():
        if not user_cfg.exists():
            shutil.copy2(cfg_src, user_cfg)
        else:
            packaged_version = _read_config_version(cfg_src)
            user_version = _read_config_version(user_cfg)
            if packaged_version and user_version and packaged_version != user_version:
                backup = user_cfg.with_suffix(".yaml.bak")
                shutil.copy2(user_cfg, backup)
                shutil.copy2(cfg_src, user_cfg)

    data_dst = user_base / "data"
    if data_dst.exists() and not any(data_dst.iterdir()):
        data_src = packaged_base / "data"
        if data_src.exists():
            # Do not seed monitoring data so the Monitoring tab starts empty.
            shutil.copytree(
                data_src,
                data_dst,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("monitoring"),
            )


def _clear_excel_cache(user_base: Path) -> None:
    """Clear persistent Excel cache so users start fresh each run.

    Removes disk cache under <user_base>/data/.cache.
    Safe to call on every startup.
    """
    try:
        cache_dir = user_base / "data" / ".cache"
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
    except Exception:
        # Never block startup on cache cleanup
        pass


def _run_sqlite_migrations() -> None:
    """Apply pending SQLite migrations before the UI loads."""
    try:
        from database.migration_manager import MigrationManager

        applied = MigrationManager().apply_pending()
        if applied:
            logger.info(f"Applied {len(applied)} SQLite migrations")
    except Exception as exc:
        logger.error("SQLite migrations failed: %s", exc)
        raise


def _sync_packaged_constants() -> None:
    """Sync packaged system constants into the user database."""
    try:
        from services.system_constants_service import SystemConstantsService

        packaged_base = _find_packaged_base()
        packaged_db = packaged_base / "data" / "water_balance.db"

        service = SystemConstantsService()
        inserted = service.sync_from_packaged_db(packaged_db, overwrite=False)
        if inserted:
            logger.info("Imported %s system constants from packaged DB", inserted)

        seeded_empty = service.seed_defaults_if_empty()
        if seeded_empty:
            logger.info("Seeded %s default system constants into empty database", seeded_empty)

        inserted_missing = service.ensure_default_constants()
        if inserted_missing:
            logger.info("Inserted %s missing default system constants", inserted_missing)
    except Exception as exc:
        logger.warning("System constants sync skipped: %s", exc)


user_base = _get_user_base()
os.environ['WATERBALANCE_USER_DIR'] = str(user_base)

if getattr(sys, "frozen", False):
    _ensure_user_data(user_base, _find_packaged_base())
    _clear_excel_cache(user_base)

# Now safe to import PySide6 and app modules
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from ui.components.splash_screen import SplashScreen
from ui.main_window import MainWindow
from core.app_logger import logger
from core.config_manager import get_resource_path


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

        # Check license and show dialogs only when needed.
        # Keep splash visible for valid licenses to avoid flicker/double-splash effect.
        result = check_license_or_activate(None)
        
        if result:
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


def _load_custom_fonts(app: QApplication) -> None:
    """Load bundled fonts and set application-wide family fallback."""
    font_paths = [
        "assets/fonts/Lato-Regular.ttf",
        "assets/fonts/Lato-Bold.ttf",
    ]
    loaded_families: set[str] = set()

    for rel_path in font_paths:
        font_path = get_resource_path(rel_path)
        if not font_path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id < 0:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        loaded_families.update(families)

    if "Lato" in loaded_families:
        app.setFont(QFont("Lato"))
        logger.info("Loaded custom app font: Lato")
    elif loaded_families:
        family = sorted(loaded_families)[0]
        app.setFont(QFont(family))
        logger.info("Loaded custom app font fallback: %s", family)
    else:
        logger.info("Custom font files not found; using system fonts")


def main():
    """Bootstrap PySide6 Water Balance Application.
    
    Shows splash screen while loading database, pages, and resources.
    Creates QApplication instance and shows main window when ready.
    Exits with application return code.
    """
    # Install global exception hook
    import sys
    def excepthook(exc_type, exc_value, exc_tb):
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
    sys.excepthook = excepthook

    # Apply SQLite migrations before app initialization
    _run_sqlite_migrations()
    _sync_packaged_constants()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Water Balance Dashboard")
    app.setOrganizationName("Two Rivers Platinum")
    icon_path = get_resource_path("src/ui/resources/icons/Water Balance.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    _load_custom_fonts(app)

    # Load global theme stylesheet if available
    try:
        theme_path = get_resource_path("config/theme.qss")
        if theme_path.exists():
            app.setStyleSheet(theme_path.read_text(encoding="utf-8"))
            logger.info(f"Theme loaded from {theme_path}")
        else:
            logger.warning(f"Theme file not found at {theme_path}")
    except Exception as e:
        logger.warning(f"Failed to load theme stylesheet: {e}")
    
    
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
