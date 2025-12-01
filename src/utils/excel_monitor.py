"""
Excel File Monitor
Watches Excel template for changes and triggers reload
"""

import os
import time
import threading
from pathlib import Path
from typing import Callable, Optional
from utils.app_logger import logger


class ExcelFileMonitor:
    """Monitor Excel file for changes and trigger reload"""
    
    def __init__(self, file_path: str, callback: Callable, check_interval: float = 2.0):
        """
        Initialize file monitor
        
        Args:
            file_path: Path to Excel file to monitor
            callback: Function to call when file changes
            check_interval: How often to check (seconds)
        """
        self.file_path = Path(file_path)
        self.callback = callback
        self.check_interval = check_interval
        self._last_modified = None
        self._monitoring = False
        self._thread = None
        
    def start(self):
        """Start monitoring in background thread"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._last_modified = self._get_modified_time()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Excel monitor started for {self.file_path.name}")
        
    def stop(self):
        """Stop monitoring"""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Excel monitor stopped")
        
    def _get_modified_time(self) -> Optional[float]:
        """Get file modification time"""
        try:
            if self.file_path.exists():
                return os.path.getmtime(self.file_path)
        except Exception as e:
            logger.error(f"Error getting file mtime: {e}")
        return None
        
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                current_mtime = self._get_modified_time()
                
                if current_mtime and self._last_modified:
                    if current_mtime > self._last_modified:
                        logger.info(f"Excel file changed detected: {self.file_path.name}")
                        self._last_modified = current_mtime
                        
                        # Call callback on main thread (thread-safe)
                        try:
                            self.callback()
                        except Exception as e:
                            logger.error(f"Error in file change callback: {e}")
                
                # Update last modified
                if current_mtime:
                    self._last_modified = current_mtime
                    
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                
            # Sleep
            time.sleep(self.check_interval)
