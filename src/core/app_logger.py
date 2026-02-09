"""
Application Logging Infrastructure
Centralized logging with rotating file handler and console output
Includes QThread-based background logger worker for async logging
Hybrid rotation: TIME-based + SIZE-based + AUTO-CLEANUP
"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime, timedelta
import sys
import time
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Optional
from PySide6.QtCore import QThread, Signal, QObject

from core.config_manager import ConfigManager

# Create logs directory
def _resolve_logs_dir() -> Path:
    """Resolve logs directory with safe, per-user defaults.
    - In EXE mode (PyInstaller), prefer `%LOCALAPPDATA%/WaterBalance/logs`.
      If `WATERBALANCE_USER_DIR` is set, use `<WATERBALANCE_USER_DIR>/logs`.
    - In dev mode, use `<repo>/logs`.
    """
    import os
    # If running as frozen EXE, avoid Program Files and use AppData
    if getattr(sys, 'frozen', False):
        env_dir = os.environ.get('WATERBALANCE_USER_DIR')
        if env_dir:
            return Path(env_dir) / 'logs'
        local_appdata = os.getenv('LOCALAPPDATA')
        if local_appdata:
            return Path(local_appdata) / 'WaterBalance' / 'logs'
        # Fallbacks
        home = Path.home()
        candidate = home / 'AppData' / 'Local' / 'WaterBalance' / 'logs'
        if (home / 'AppData' / 'Local').exists():
            return candidate
        return home / '.waterbalance' / 'logs'
    # Dev mode: repo logs
    return Path(__file__).parent.parent.parent / 'logs'

LOGS_DIR = _resolve_logs_dir()
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / 'water_balance.log'
ERROR_LOG = LOGS_DIR / 'errors.log'


def _cleanup_old_logs(max_age_days: int = 90):
    """Auto-cleanup old log files to prevent disk bloat (MAINTENANCE TASK).
    
    Removes all .log and .log.* files older than max_age_days.
    Runs automatically on app startup to maintain disk hygiene.
    
    Args:
        max_age_days: Delete logs older than this many days (default 90)
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        for log_file in LOGS_DIR.rglob('*.log*'):  # .log and .log.* files
            if log_file.is_file():
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    try:
                        log_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        # Log to stderr if cleanup fails (don't break app)
                        sys.stderr.write(f"Failed to delete old log {log_file}: {e}\n")
        
        if deleted_count > 0:
            sys.stderr.write(
                f"Cleaned up {deleted_count} log files older than {max_age_days} days\n"
            )
    except Exception as e:
        sys.stderr.write(f"Log cleanup error: {e}\n")


class SafeConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            try:
                self.stream.write(msg)
                self.stream.write(self.terminator)
            except UnicodeEncodeError:
                enc = getattr(self.stream, 'encoding', None) or sys.getdefaultencoding()
                safe = msg.encode(enc, errors='replace').decode(enc, errors='replace')
                self.stream.write(safe)
                self.stream.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class HybridRotatingHandler(RotatingFileHandler):
    """Hybrid rotation handler (TIME + SIZE based ROTATION).
    
    Rotates when EITHER condition is met:
    1. File size exceeds maxBytes (size-based)
    2. Time interval expires (time-based)
    
    This gives organized logs (by date) without disk bloat.
    
    Usage:
        handler = HybridRotatingHandler(
            'logs/analytics.log',
            maxBytes=3*1024*1024,  # 3MB
            backupCount=7,         # 7 files
            when='midnight'        # Rotate at midnight (or use 'W0' for Monday)
        )
    """
    
    def __init__(self, filename: str, maxBytes: int, backupCount: int, when: str = 'midnight'):
        """Initialize hybrid handler.
        
        Args:
            filename: Log file path
            maxBytes: Max file size before rotation (e.g., 5*1024*1024 for 5MB)
            backupCount: Number of backup files to keep
            when: Time interval ('midnight', 'W0' for Monday, etc.)
        """
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount)
        self.when = when
        self.last_rotation_date = datetime.now().date()
        
        # Set rotation interval (in days)
        if when == 'midnight':
            self.rotation_interval_days = 1  # Daily
        elif when.startswith('W'):  # W0 = Monday, W1 = Tuesday, etc.
            self.rotation_interval_days = 7  # Weekly
        elif when == 'monthly':
            self.rotation_interval_days = 30  # ~Monthly
        else:
            self.rotation_interval_days = 1  # Default daily
    
    def shouldRollover(self, record) -> bool:
        """Check if rotation needed (size OR time based).
        
        Returns:
            True if rotation needed
        """
        # Check size-based rotation first (fast)
        if super().shouldRollover(record):
            return True
        
        # Check time-based rotation
        today = datetime.now().date()
        days_since_rotation = (today - self.last_rotation_date).days
        
        if days_since_rotation >= self.rotation_interval_days:
            self.last_rotation_date = today
            return True
        
        return False
    
    def doRollover(self):
        """Perform rollover with timestamped filename (HYBRID ROTATION)."""
        # Call parent to do the actual rotation
        super().doRollover()
        
        # Rename backup file with date (water_balance.log.1 → water_balance.log.2026-01-30)
        try:
            backup_index = 1
            while True:
                old_name = f"{self.baseFilename}.{backup_index}"
                if not Path(old_name).exists():
                    break
                
                # Get file modification time
                mtime = Path(old_name).stat().st_mtime
                backup_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                new_name = f"{self.baseFilename}.{backup_date}"
                
                # Rename to dated format (only once)
                if old_name != new_name:
                    try:
                        Path(old_name).rename(new_name)
                    except FileExistsError:
                        pass  # Already named, skip
                break
        except Exception as e:
            self.handleError(None)


class BackgroundLoggerWorker(QThread):
    """Background thread for async log processing (NON-BLOCKING LOGGER).
    
    Benefits:
    - UI never freezes during heavy logging
    - File I/O happens asynchronously
    - Thread-safe queue-based message buffering
    - Auto-flushes every 100ms or on 50 message batch
    
    Usage:
        worker = BackgroundLoggerWorker()
        worker.start()
        worker.queue_log_record(record)
        # On shutdown:
        worker.stop()
        worker.wait()
    """
    
    log_error = Signal(str)  # Emit critical logging errors to UI
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._log_queue = Queue(maxsize=1000)  # Max 1000 pending messages
        self._running = True
        self._flush_interval_ms = 100  # Flush every 100ms
        self._batch_size = 50  # Or flush after 50 messages
    
    def queue_log_record(self, record: logging.LogRecord, handler: logging.Handler):
        """Queue log record for async processing (CALLED FROM MAIN THREAD).
        
        Args:
            record: Log record to process
            handler: Handler to emit the record
        """
        try:
            self._log_queue.put((record, handler), block=False)
        except Exception as e:
            # Queue full - emit to stderr immediately (fallback)
            sys.stderr.write(f"LOG QUEUE FULL: {record.getMessage()}\n")
    
    def run(self):
        """Background processing loop (RUNS IN WORKER THREAD)."""
        batch = []
        last_flush_time = time.time()
        
        while self._running:
            try:
                # Try to get a record with short timeout
                try:
                    record, handler = self._log_queue.get(timeout=0.1)
                    batch.append((record, handler))
                except Empty:
                    pass
                
                # Flush batch if size or time threshold reached
                current_time = time.time()
                time_since_flush = (current_time - last_flush_time) * 1000  # Convert to ms
                
                should_flush = (
                    len(batch) >= self._batch_size or
                    (batch and time_since_flush >= self._flush_interval_ms)
                )
                
                if should_flush:
                    self._flush_batch(batch)
                    batch = []
                    last_flush_time = current_time
                    
            except Exception as e:
                self.log_error.emit(f"Logger worker error: {e}")
        
        # Final flush on shutdown
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: list):
        """Write batch of log records to handlers with safe Unicode encoding (FILE I/O HERE).
        
        Safely emits records to handlers, catching UnicodeEncodeError and using
        safe encoding (with 'replace' mode) to prevent crashes on special characters.
        The SafeConsoleHandler already handles this, but we add a safety net here.
        """
        for record, handler in batch:
            try:
                handler.emit(record)
            except UnicodeEncodeError as ue:
                # Unicode error - try again with safe message
                try:
                    # Replace special characters with ASCII equivalents
                    original_msg = record.getMessage()
                    safe_msg = original_msg.encode('utf-8', errors='replace').decode('utf-8')
                    safe_msg = safe_msg.encode('ascii', errors='replace').decode('ascii')
                    
                    # Create new record with safe message
                    safe_record = logging.LogRecord(
                        record.name, record.levelno, record.pathname, record.lineno,
                        safe_msg, record.args, record.exc_info, record.func, record.sinfo
                    )
                    handler.emit(safe_record)
                except Exception as e:
                    # If still fails, print to stderr instead
                    sys.stderr.write(
                        f"LOG FAILED (Unicode): {record.getMessage()[:100]}\n"
                    )
            except Exception as e:
                # Fallback to stderr if handler fails
                sys.stderr.write(f"Handler emit failed: {e}\n")
    
    def stop(self):
        """Signal worker to stop (CALL BEFORE APP EXIT)."""
        self._running = False


from typing import Optional


class QueueHandler(logging.Handler):
    """Logging handler that queues records to BackgroundLoggerWorker.
    
    This handler is added to loggers; it pushes records to the worker thread
    instead of writing directly to files/console (non-blocking).
    """
    
    def __init__(self, worker: BackgroundLoggerWorker, target_handler: logging.Handler):
        super().__init__()
        self.worker = worker
        self.target_handler = target_handler
        # Copy level and formatter from target
        self.setLevel(target_handler.level)
        self.setFormatter(target_handler.formatter)
    
    def emit(self, record: logging.LogRecord):
        """Queue record to background worker (FAST, NON-BLOCKING)."""
        self.worker.queue_log_record(record, self.target_handler)


class AppLogger:
    """Centralized application logger"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logging configuration with hybrid rotation and background worker"""
        if self._initialized:
            return
        
        self._initialized = True
        
        # Run cleanup on startup (removes logs >90 days old)
        _cleanup_old_logs(max_age_days=90)
        
        # Create background logging worker (async I/O)
        self.log_worker = BackgroundLoggerWorker()
        self.log_worker.log_error.connect(self._on_worker_error)
        self.log_worker.start()
        
        # Create loggers
        self.app_logger = logging.getLogger('water_balance')
        self.error_logger = logging.getLogger('water_balance.errors')
        
        config = ConfigManager()
        configured_level = self._resolve_log_level(config.get('logging.level', 'INFO'))

        # Set levels
        self.app_logger.setLevel(configured_level)
        self.error_logger.setLevel(logging.ERROR)
        
        # Prevent propagation to avoid duplicate logs
        self.error_logger.propagate = False
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Main app file handler (HYBRID: 10MB max + monthly rotation)
        app_file_handler = HybridRotatingHandler(
            str(APP_LOG),
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=12,         # Keep 12 files (~1 year of monthly)
            when='midnight'         # Also rotate at midnight if size not hit
        )
        app_file_handler.setLevel(configured_level)
        app_file_handler.setFormatter(detailed_formatter)
        
        # Error file handler (HYBRID: 10MB max + monthly rotation)
        error_file_handler = HybridRotatingHandler(
            str(ERROR_LOG),
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=12,         # Keep 12 files (~1 year)
            when='midnight'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        
        # Console handler (WARNING and above only - cleaner system output)
        console_handler = SafeConsoleHandler(sys.stdout)
        console_handler.setLevel(max(configured_level, logging.WARNING))
        console_handler.setFormatter(simple_formatter)
        
        # Wrap file handlers with async queue handlers (non-blocking I/O)
        app_file_queue = QueueHandler(self.log_worker, app_file_handler)
        error_file_queue = QueueHandler(self.log_worker, error_file_handler)
        
        # Add handlers (files go through worker, console is direct)
        self.app_logger.addHandler(app_file_queue)
        self.app_logger.addHandler(console_handler)  # Console direct (for immediate feedback)
        
        self.error_logger.addHandler(error_file_queue)
        self.error_logger.addHandler(console_handler)
        
        # Initial log entry (to file only, not console - keeps startup clean)
        self.app_logger.log(configured_level, "=" * 60)
        self.app_logger.log(configured_level, "Water Balance Application Started")
        self.app_logger.log(configured_level, "=" * 60)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.app_logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.app_logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.app_logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, exc_info=False, **kwargs):
        """Log error message"""
        self.app_logger.error(message, *args, exc_info=exc_info, **kwargs)
        self.error_logger.error(message, *args, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, *args, exc_info=False, **kwargs):
        """Log critical message"""
        self.app_logger.critical(message, *args, exc_info=exc_info, **kwargs)
        self.error_logger.critical(message, *args, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        self.app_logger.exception(message, *args, **kwargs)
        self.error_logger.exception(message, *args, **kwargs)
    
    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metric"""
        self.app_logger.info(f"PERF: {operation} completed in {duration_ms:.2f}ms", **kwargs)
    
    def user_action(self, action: str, details: str = None, **kwargs):
        """Log user action"""
        msg = f"USER: {action}"
        if details:
            msg += f" | {details}"
        self.app_logger.info(msg, **kwargs)
    
    def database(self, operation: str, affected_rows: int = None, **kwargs):
        """Log database operation"""
        msg = f"DB: {operation}"
        if affected_rows is not None:
            msg += f" | {affected_rows} row(s)"
        self.app_logger.debug(msg, **kwargs)
    
    def calculation(self, calc_type: str, date: str, result: str = None, **kwargs):
        """Log calculation"""
        msg = f"CALC: {calc_type} for {date}"
        if result:
            msg += f" | {result}"
        self.app_logger.debug(msg, **kwargs)
    
    def _on_worker_error(self, error_msg: str):
        """Handle background worker errors (SIGNAL SLOT)."""
        # Fallback to stderr since worker failed
        sys.stderr.write(f"LOGGER WORKER ERROR: {error_msg}\n")
    
    def shutdown(self):
        """Shutdown background logger worker (CALL ON APP EXIT).
        
        Ensures all queued log messages are written before app closes.
        """
        if hasattr(self, 'log_worker'):
            self.app_logger.info("Shutting down background logger...")
            self.log_worker.stop()
            self.log_worker.wait(5000)  # Wait max 5 seconds for flush
            if self.log_worker.isRunning():
                self.app_logger.warning("Logger worker did not stop cleanly")
    
    @contextmanager
    def performance_timer(self, operation: str):
        """Context manager for performance tracking (HELPER).
        
        Usage:
            with logger.performance_timer('Load facilities from DB'):
                facilities = db.get_all_facilities()
            # Logs: "PERF: Load facilities from DB completed in 45.23ms"
        
        Args:
            operation: Description of operation being timed
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.performance(operation, duration_ms)
    
    def get_dashboard_logger(self, dashboard_name: str) -> logging.Logger:
        """Get a dedicated logger for a specific dashboard page.
        
        Creates logs in subfolder: logs/<dashboard_name>/
        Prevents large monolithic log files, easier debugging.
        
        Args:
            dashboard_name: Name of dashboard (e.g., 'analytics', 'flow_diagram')
        
        Returns:
            Configured logger instance for that dashboard
        """
        logger_name = f"water_balance.{dashboard_name}"
        dash_logger = logging.getLogger(logger_name)
        
        # Only configure once (check own handlers, not parent handlers)
        if len(dash_logger.handlers) > 0:
            return dash_logger
        
        config = ConfigManager()
        configured_level = self._resolve_log_level(config.get('logging.level', 'INFO'))
        dash_logger.setLevel(configured_level)
        dash_logger.propagate = False  # Don't send to parent loggers
        
        # Create dashboard-specific log folder
        dash_log_dir = LOGS_DIR / dashboard_name
        dash_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Dashboard-specific log files
        dash_log_file = dash_log_dir / f"{dashboard_name}.log"
        dash_error_file = dash_log_dir / f"{dashboard_name}_errors.log"
        
        # Detailed formatter
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Dashboard file handler (HYBRID: 3MB max + weekly rotation)
        dash_file_handler = HybridRotatingHandler(
            str(dash_log_file),
            maxBytes=3*1024*1024,  # 3 MB
            backupCount=8,         # Keep 8 files (~2 months of weekly)
            when='W0'              # Rotate every Monday + size limit
        )
        dash_file_handler.setLevel(configured_level)
        dash_file_handler.setFormatter(detailed_formatter)
        
        # Dashboard error handler (HYBRID: 5MB max + weekly rotation)
        dash_error_handler = HybridRotatingHandler(
            str(dash_error_file),
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=8,         # Keep 8 files
            when='W0'
        )
        dash_error_handler.setLevel(logging.ERROR)
        dash_error_handler.setFormatter(detailed_formatter)
        
        # Wrap file handlers with async queue handlers (non-blocking dashboard logging)
        dash_file_queue = QueueHandler(self.log_worker, dash_file_handler)
        dash_error_queue = QueueHandler(self.log_worker, dash_error_handler)
        
        dash_logger.addHandler(dash_file_queue)
        dash_logger.addHandler(dash_error_queue)
        
        # Console handler for all levels with SafeConsoleHandler (DEBUG level set to DEBUG, not ERROR)
        # Set to DEBUG level (not ERROR) so that all messages including DEBUG-level logs get proper
        # Unicode encoding protection via SafeConsoleHandler. This prevents UnicodeEncodeError when
        # special characters (arrows, etc.) in log messages are written to Windows console with cp1252 encoding.
        console_handler = SafeConsoleHandler(sys.stdout)
        console_handler.setLevel(configured_level)
        console_handler.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
        dash_logger.addHandler(console_handler)
        
        dash_logger.log(configured_level, f"=== {dashboard_name.upper()} Dashboard Logger Initialized ===")
        return dash_logger

    @staticmethod
    def _resolve_log_level(level_value: str) -> int:
        """Resolve log level from config string with safe fallback."""
        if not isinstance(level_value, str):
            return logging.INFO
        normalized = level_value.strip().upper()
        return {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'WARN': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
        }.get(normalized, logging.INFO)


# Global logger instance
logger = AppLogger()
