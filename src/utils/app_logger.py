"""
Application Logging Infrastructure
Centralized logging with rotating file handler and console output
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import sys

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / 'water_balance.log'
ERROR_LOG = LOGS_DIR / 'errors.log'


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
        """Initialize logging configuration"""
        if self._initialized:
            return
        
        self._initialized = True
        
        # Create loggers
        self.app_logger = logging.getLogger('water_balance')
        self.error_logger = logging.getLogger('water_balance.errors')
        
        # Set levels
        self.app_logger.setLevel(logging.DEBUG)
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
        
        # Main app file handler (rotating, 5MB max, keep 5 backups)
        app_file_handler = RotatingFileHandler(
            APP_LOG,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        app_file_handler.setLevel(logging.DEBUG)
        app_file_handler.setFormatter(detailed_formatter)
        
        # Error file handler (rotating, 10MB max, keep 10 backups)
        error_file_handler = RotatingFileHandler(
            ERROR_LOG,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        
        # Console handler (INFO and above) with safe Unicode fallback
        console_handler = SafeConsoleHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.app_logger.addHandler(app_file_handler)
        self.app_logger.addHandler(console_handler)
        
        self.error_logger.addHandler(error_file_handler)
        self.error_logger.addHandler(console_handler)
        
        # Initial log entry
        self.app_logger.info("=" * 60)
        self.app_logger.info("Water Balance Application Started")
        self.app_logger.info("=" * 60)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.app_logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.app_logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.app_logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info=False, **kwargs):
        """Log error message"""
        self.app_logger.error(message, exc_info=exc_info, **kwargs)
        self.error_logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info=False, **kwargs):
        """Log critical message"""
        self.app_logger.critical(message, exc_info=exc_info, **kwargs)
        self.error_logger.critical(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.app_logger.exception(message, **kwargs)
        self.error_logger.exception(message, **kwargs)
    
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


# Global logger instance
logger = AppLogger()
