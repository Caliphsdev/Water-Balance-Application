"""
Centralized Error Handler
Classifies, logs, and formats user-friendly error messages
"""

import traceback
from typing import Optional, Dict, Any, Tuple
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.app_logger import logger


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    DATABASE = "database"
    CALCULATION = "calculation"
    VALIDATION = "validation"
    FILE_IO = "file_io"
    NETWORK = "network"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class AppError(Exception):
    """Base application error with metadata"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 user_message: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.details = details or {}
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly message from technical message"""
        # Default user-friendly messages by category
        category_messages = {
            ErrorCategory.DATABASE: "A database error occurred. Please try again or contact support.",
            ErrorCategory.CALCULATION: "Unable to complete the calculation. Please check your input data.",
            ErrorCategory.VALIDATION: "The data provided is invalid. Please review and correct.",
            ErrorCategory.FILE_IO: "Unable to access the file. Please check file permissions.",
            ErrorCategory.NETWORK: "Network connection failed. Please check your connection.",
            ErrorCategory.PERMISSION: "Permission denied. You may not have access to this resource.",
            ErrorCategory.CONFIGURATION: "Configuration error. Please check application settings.",
            ErrorCategory.USER_INPUT: "Invalid input provided. Please review your entries.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
        }
        return category_messages.get(self.category, "An error occurred.")


class ErrorHandler:
    """Centralized error handling and reporting"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize error handler"""
        self.error_history = []
        self.max_history = 100
    
    def handle(self, error: Exception, context: str = None,
               category: ErrorCategory = None,
               severity: ErrorSeverity = None,
               suppress: bool = False) -> Tuple[str, str, ErrorSeverity]:
        """
        Handle an error with logging and user message generation
        
        Args:
            error: The exception that occurred
            context: Additional context about where/when error occurred
            category: Error category (auto-detected if None)
            severity: Error severity (auto-detected if None)
            suppress: If True, don't re-raise the error
        
        Returns:
            Tuple of (technical_message, user_message, severity)
        """
        # Auto-detect category and severity if not provided
        if isinstance(error, AppError):
            category = error.category
            severity = error.severity
            user_message = error.user_message
            technical_message = error.message
        else:
            category = category or self._classify_error(error)
            severity = severity or self._assess_severity(error, category)
            technical_message = str(error)
            user_message = self._generate_user_message(error, category)
        
        # Build full context
        full_context = f"{context} | " if context else ""
        full_context += f"{category.value} | {technical_message}"
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(full_context, exc_info=True)
        elif severity == ErrorSeverity.ERROR:
            logger.error(full_context, exc_info=True)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(full_context)
        else:
            logger.info(full_context)

        # Ensure errors are visible in the terminal for fast debugging
        if severity in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL):
            tb_snippet = traceback.format_exc(limit=1).strip()
            sys.stderr.write(f"ERROR: {full_context}\n")
            if tb_snippet and tb_snippet != 'NoneType: None':
                sys.stderr.write(f"TRACE: {tb_snippet}\n")
            sys.stderr.flush()
        
        # Store in history
        self._add_to_history(error, context, category, severity, user_message)
        
        # Re-raise if not suppressed and critical
        if not suppress and severity == ErrorSeverity.CRITICAL:
            raise
        
        return technical_message, user_message, severity
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error by type and message"""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # Database errors
        if 'sqlite' in error_type.lower() or 'database' in error_msg:
            return ErrorCategory.DATABASE
        
        # File I/O errors
        if any(x in error_type.lower() for x in ['ioerror', 'oserror', 'filenotfound']):
            return ErrorCategory.FILE_IO
        
        # Permission errors
        if 'permission' in error_msg or error_type == 'PermissionError':
            return ErrorCategory.PERMISSION
        
        # Validation errors
        if any(x in error_type.lower() for x in ['value', 'type', 'key', 'attribute']):
            return ErrorCategory.VALIDATION
        
        # Calculation errors
        if any(x in error_msg for x in ['calculation', 'balance', 'formula', 'divide by zero']):
            return ErrorCategory.CALCULATION
        
        # Network errors
        if any(x in error_type.lower() for x in ['connection', 'timeout', 'network']):
            return ErrorCategory.NETWORK
        
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess error severity"""
        error_type = type(error).__name__
        
        # Critical errors that prevent app operation
        if error_type in ['SystemExit', 'KeyboardInterrupt', 'MemoryError']:
            return ErrorSeverity.CRITICAL
        
        # Critical for database corruption
        if category == ErrorCategory.DATABASE and 'corrupt' in str(error).lower():
            return ErrorSeverity.CRITICAL
        
        # Warnings for validation issues
        if category == ErrorCategory.VALIDATION:
            return ErrorSeverity.WARNING
        
        # Warnings for user input
        if category == ErrorCategory.USER_INPUT:
            return ErrorSeverity.WARNING
        
        # Default to ERROR
        return ErrorSeverity.ERROR
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        # Specific messages based on error type
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        if category == ErrorCategory.DATABASE:
            if 'locked' in error_msg:
                return "The database is currently locked. Please wait a moment and try again."
            elif 'not found' in error_msg:
                return "Database file not found. The application may need to be reinstalled."
            elif 'corrupt' in error_msg:
                return "Database corruption detected. Please restore from backup or contact support."
            else:
                return "A database error occurred. Your changes may not have been saved."
        
        elif category == ErrorCategory.FILE_IO:
            if 'not found' in error_msg:
                return "The requested file was not found. Please check the file path."
            elif 'permission' in error_msg:
                return "Unable to access the file due to permission restrictions."
            else:
                return "An error occurred while accessing the file."
        
        elif category == ErrorCategory.CALCULATION:
            if 'divide' in error_msg or 'zero' in error_msg:
                return "Calculation failed due to invalid values (division by zero)."
            else:
                return "Unable to complete the calculation. Please verify your input data."
        
        elif category == ErrorCategory.VALIDATION:
            return f"Invalid data: {error_msg}"
        
        elif category == ErrorCategory.USER_INPUT:
            return "Please check your input and try again."
        
        # Default generic message
        return "An unexpected error occurred. Please try again or contact support if the issue persists."
    
    def _add_to_history(self, error: Exception, context: str,
                       category: ErrorCategory, severity: ErrorSeverity,
                       user_message: str):
        """Add error to history with size limit"""
        from datetime import datetime
        
        entry = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'category': category.value,
            'severity': severity.value,
            'user_message': user_message
        }
        
        self.error_history.append(entry)
        
        # Limit history size
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def get_recent_errors(self, count: int = 10) -> list:
        """Get recent errors from history"""
        return self.error_history[-count:]
    
    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
    
    def wrap(self, func):
        """Decorator to wrap function with error handling"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = f"Function: {func.__name__}"
                self.handle(e, context=context, suppress=False)
        return wrapper


# Global error handler instance
error_handler = ErrorHandler()
