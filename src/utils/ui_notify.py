"""
UI Notification System
Standardized user notifications with status bar integration
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.app_logger import logger
from utils.error_handler import ErrorSeverity


class NotificationType(Enum):
    """Notification types matching error severities"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class UINotifier:
    """Centralized UI notification system"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize notifier"""
        self._status_bar_callback = None
        self._notification_history = []
        self._max_history = 50
    
    def set_status_bar_callback(self, callback: Callable[[str], None]):
        """
        Set callback for status bar updates
        
        Args:
            callback: Function that takes a message string and updates status bar
        """
        self._status_bar_callback = callback
    
    def info(self, message: str, title: str = "Information",
             show_dialog: bool = False, log: bool = True) -> None:
        """
        Show info notification
        
        Args:
            message: The message to display
            title: Dialog title (if show_dialog=True)
            show_dialog: If True, show messagebox dialog
            log: If True, log the message
        """
        if log:
            logger.info(f"UI Notification: {message}")
        
        self._add_to_history(NotificationType.INFO, message)
        
        if show_dialog:
            messagebox.showinfo(title, message)
        
        self._update_status_bar(f"[i] {message}", NotificationType.INFO)
    
    def success(self, message: str, title: str = "Success",
                show_dialog: bool = False, log: bool = True) -> None:
        """
        Show success notification
        
        Args:
            message: The message to display
            title: Dialog title (if show_dialog=True)
            show_dialog: If True, show messagebox dialog
            log: If True, log the message
        """
        if log:
            logger.info(f"Success: {message}")
        
        self._add_to_history(NotificationType.SUCCESS, message)
        
        if show_dialog:
            messagebox.showinfo(title, message)
        
        self._update_status_bar(f"[OK] {message}", NotificationType.SUCCESS)
    
    def warning(self, message: str, title: str = "Warning",
                show_dialog: bool = True, log: bool = True) -> None:
        """
        Show warning notification
        
        Args:
            message: The message to display
            title: Dialog title (if show_dialog=True)
            show_dialog: If True, show messagebox dialog (default for warnings)
            log: If True, log the message
        """
        if log:
            logger.warning(f"Warning: {message}")
        
        self._add_to_history(NotificationType.WARNING, message)
        
        if show_dialog:
            messagebox.showwarning(title, message)
        
        self._update_status_bar(f"[!] {message}", NotificationType.WARNING)
    
    def error(self, message: str, title: str = "Error",
              technical_details: str = None,
              show_dialog: bool = True, log: bool = True) -> None:
        """
        Show error notification
        
        Args:
            message: User-friendly error message
            title: Dialog title
            technical_details: Optional technical error details (logged but not shown to user)
            show_dialog: If True, show messagebox dialog (default for errors)
            log: If True, log the error
        """
        if log:
            log_msg = f"Error: {message}"
            if technical_details:
                log_msg += f" | Details: {technical_details}"
            logger.error(log_msg)
        
        self._add_to_history(NotificationType.ERROR, message)
        
        if show_dialog:
            messagebox.showerror(title, message)
        
        self._update_status_bar(f"[ERROR] {message}", NotificationType.ERROR)
    
    def confirm(self, message: str, title: str = "Confirm Action") -> bool:
        """
        Show confirmation dialog
        
        Args:
            message: Confirmation message
            title: Dialog title
        
        Returns:
            True if user clicked Yes/OK, False otherwise
        """
        logger.info(f"Confirmation requested: {message}")
        result = messagebox.askyesno(title, message)
        logger.info(f"User confirmed: {result}")
        return result
    
    def ask_ok_cancel(self, message: str, title: str = "Confirm") -> bool:
        """
        Show OK/Cancel dialog
        
        Args:
            message: Message to display
            title: Dialog title
        
        Returns:
            True if user clicked OK, False otherwise
        """
        logger.info(f"OK/Cancel requested: {message}")
        result = messagebox.askokcancel(title, message)
        logger.info(f"User clicked OK: {result}")
        return result
    
    def ask_retry_cancel(self, message: str, title: str = "Retry") -> bool:
        """
        Show Retry/Cancel dialog
        
        Args:
            message: Message to display
            title: Dialog title
        
        Returns:
            True if user clicked Retry, False otherwise
        """
        logger.info(f"Retry/Cancel requested: {message}")
        result = messagebox.askretrycancel(title, message)
        logger.info(f"User clicked Retry: {result}")
        return result
    
    def status(self, message: str, log: bool = False) -> None:
        """
        Update status bar only (no dialog)
        
        Args:
            message: Status message
            log: If True, log at debug level
        """
        if log:
            logger.debug(f"Status: {message}")
        
        self._update_status_bar(message, NotificationType.INFO)
    
    def clear_status(self):
        """Clear status bar"""
        self._update_status_bar("Ready", NotificationType.INFO)
    
    def _update_status_bar(self, message: str, notification_type: NotificationType):
        """Update status bar via callback"""
        if self._status_bar_callback:
            try:
                self._status_bar_callback(message)
            except Exception as e:
                # Don't let status bar update failures break the app
                logger.error(f"Status bar update failed: {e}")
    
    def _add_to_history(self, notification_type: NotificationType, message: str):
        """Add notification to history"""
        from datetime import datetime
        
        entry = {
            'timestamp': datetime.now(),
            'type': notification_type.value,
            'message': message
        }
        
        self._notification_history.append(entry)
        
        # Limit history size
        if len(self._notification_history) > self._max_history:
            self._notification_history = self._notification_history[-self._max_history:]
    
    def get_recent_notifications(self, count: int = 10) -> list:
        """Get recent notifications from history"""
        return self._notification_history[-count:]
    
    def clear_history(self):
        """Clear notification history"""
        self._notification_history.clear()
    
    def notify_from_error(self, severity: ErrorSeverity, user_message: str,
                         technical_message: str = None,
                         show_dialog: bool = None) -> None:
        """
        Create notification from error handler output
        
        Args:
            severity: Error severity level
            user_message: User-friendly message
            technical_message: Technical error details
            show_dialog: Override default dialog behavior
        """
        # Map severity to notification method
        if severity == ErrorSeverity.CRITICAL or severity == ErrorSeverity.ERROR:
            if show_dialog is None:
                show_dialog = True
            self.error(user_message, technical_details=technical_message, show_dialog=show_dialog)
        elif severity == ErrorSeverity.WARNING:
            if show_dialog is None:
                show_dialog = True
            self.warning(user_message, show_dialog=show_dialog)
        else:
            if show_dialog is None:
                show_dialog = False
            self.info(user_message, show_dialog=show_dialog)


# Global notifier instance
notifier = UINotifier()
