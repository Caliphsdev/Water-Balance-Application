"""
Async Database Loader for Fast Startup
Loads database in background while UI displays loading state
Fallback to blocking load if any issues occur
"""

import threading
import time
from typing import Callable, Optional
from utils.app_logger import logger


class AsyncDatabaseLoader:
    """Handles asynchronous database connection and initialization"""
    
    def __init__(self):
        self.db_manager = None
        self.loading = True
        self.error = None
        self.load_thread = None
        self.callbacks = []
        
    def load_database_async(self, db_path: str, on_complete: Optional[Callable] = None):
        """
        Start loading database in background thread
        
        Args:
            db_path: Path to SQLite database
            on_complete: Callback to execute when loading completes (success or failure)
        """
        if on_complete:
            self.callbacks.append(on_complete)
            
        self.load_thread = threading.Thread(
            target=self._load_database_worker,
            args=(db_path,),
            daemon=True
        )
        self.load_thread.start()
        logger.info("🚀 Database loading started in background thread")
        
    def _load_database_worker(self, db_path: str):
        """Worker thread that loads the database"""
        try:
            from database.db_manager import DatabaseManager
            
            logger.info(f"Connecting to database: {db_path}")
            start_time = time.time()
            
            # Initialize database connection
            self.db_manager = DatabaseManager(db_path)
            
            # Test connection by running a simple query
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            # Prefer wb_structures if present (topology schema); otherwise use storage_facilities
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wb_structures'")
            has_wb_structures = cursor.fetchone() is not None
            if has_wb_structures:
                cursor.execute("SELECT COUNT(*) FROM wb_structures")
                count = cursor.fetchone()[0]
                summary = f"{count} structures"
            else:
                cursor.execute("SELECT COUNT(*) FROM storage_facilities")
                count = cursor.fetchone()[0]
                summary = f"{count} facilities"
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Database loaded successfully in {elapsed:.2f}s ({summary})")
            
            self.loading = False
            self.error = None
            
        except Exception as e:
            logger.error(f"❌ Database loading failed: {e}", exc_info=True)
            self.loading = False
            self.error = str(e)
            self.db_manager = None
            
        finally:
            # Execute all callbacks
            for callback in self.callbacks:
                try:
                    callback(self.db_manager, self.error)
                except Exception as cb_error:
                    logger.error(f"Callback error: {cb_error}", exc_info=True)
                    
    def is_loading(self) -> bool:
        """Check if database is still loading"""
        return self.loading
        
    def get_database(self):
        """Get database manager (may be None if still loading or failed)"""
        return self.db_manager
        
    def get_error(self) -> Optional[str]:
        """Get error message if loading failed"""
        return self.error
        
    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """
        Block until database loading completes or timeout
        
        Args:
            timeout: Maximum seconds to wait
            
        Returns:
            True if completed successfully, False if timeout or error
        """
        if self.load_thread:
            self.load_thread.join(timeout=timeout)
            
        return not self.loading and self.error is None


# Global singleton instance
_loader_instance = None


def get_loader() -> AsyncDatabaseLoader:
    """Get global async loader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = AsyncDatabaseLoader()
    return _loader_instance


def load_database_blocking(db_path: str):
    """
    FALLBACK: Traditional blocking database load
    Used when async loading is disabled or fails
    """
    from database.db_manager import DatabaseManager
    logger.info(f"Loading database (blocking mode): {db_path}")
    start_time = time.time()
    
    db_manager = DatabaseManager(db_path)
    
    elapsed = time.time() - start_time
    logger.info(f"✅ Database loaded in {elapsed:.2f}s (blocking mode)")
    
    return db_manager
