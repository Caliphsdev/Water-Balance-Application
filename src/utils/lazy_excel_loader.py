"""
Lazy Excel Loader - On-Demand Excel Loading
Loads Excel files only when needed, with graceful error handling
"""

from pathlib import Path
from typing import Optional, Callable
from utils.app_logger import logger
from utils.config_manager import config


class LazyExcelLoader:
    """Handles lazy loading of Excel files on-demand"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize lazy loader"""
        if self._initialized:
            return
        
        self._initialized = True
        self._excel_instance = None
        self._is_loading = False
        self._excel_path = None
        self._has_warned_user = False
        self._update_excel_path()
    
    def _update_excel_path(self):
        """Get Excel file path from config"""
        template_path = config.get('data_sources.template_excel_path', 
                                   'test_templates/Water_Balance_TimeSeries_Template.xlsx')
        base_dir = Path(__file__).parent.parent.parent
        self._excel_path = base_dir / template_path if not Path(template_path).is_absolute() else Path(template_path)
    
    def excel_file_exists(self) -> bool:
        """Check if Excel file exists"""
        self._update_excel_path()
        return self._excel_path.exists() and self._excel_path.is_file()
    
    def get_excel_path(self) -> Optional[Path]:
        """Get configured Excel file path"""
        self._update_excel_path()
        return self._excel_path if self._excel_path.exists() else None
    
    def load_excel_if_needed(self, on_missing: Optional[Callable] = None) -> bool:
        """
        Load Excel file on-demand if not already loaded
        
        Args:
            on_missing: Callback function if Excel file is missing
            
        Returns:
            True if Excel loaded successfully, False otherwise
        """
        if self._excel_instance is not None:
            return True  # Already loaded
        
        if self._is_loading:
            logger.info("Excel loading already in progress...")
            return False
        
        self._update_excel_path()
        
        # Check if file exists
        if not self.excel_file_exists():
            logger.warning(f"Excel file not found: {self._excel_path}")
            
            # Call callback if provided
            if on_missing and not self._has_warned_user:
                self._has_warned_user = True
                on_missing(str(self._excel_path))
            
            return False
        
        # Load Excel
        try:
            self._is_loading = True
            logger.info(f"Lazy loading Excel file: {self._excel_path.name}")
            
            from utils.excel_timeseries_extended import ExcelTimeSeriesExtended
            self._excel_instance = ExcelTimeSeriesExtended(str(self._excel_path))
            
            logger.info("✅ Excel file loaded successfully (lazy)")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}", exc_info=True)
            self._excel_instance = None
            return False
        finally:
            self._is_loading = False
    
    def get_excel_instance(self):
        """Get loaded Excel instance (returns None if not loaded)"""
        return self._excel_instance
    
    def is_excel_loaded(self) -> bool:
        """Check if Excel is already loaded"""
        return self._excel_instance is not None
    
    def reset(self):
        """Reset loader (for testing or reconfiguration)"""
        self._excel_instance = None
        self._is_loading = False
        self._has_warned_user = False
        logger.info("Excel loader reset")


def get_lazy_loader() -> LazyExcelLoader:
    """Get singleton lazy loader instance"""
    return LazyExcelLoader()
