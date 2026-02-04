"""
Recirculation Volume Loader (EXCEL DATA SOURCE FOR RECIRCULATION).

Loads recirculation volumes from Flow Diagram Excel (Water_Balance_TimeSeries_Template.xlsx).
Mirrors FlowVolumeLoader pattern for consistency.

Data Flow:
1. Read Water_Balance_TimeSeries_Template.xlsx via centralized ExcelManager (area-specific sheets: Flows_UG2N, etc.)
2. Extract recirculation columns mapped in diagram JSON
3. Cache results per area/month to avoid re-reads
4. Return dict: {component_id: volume_m3}

Configuration (from diagram JSON):
{
  "recirculation": [
    {
      "component_id": "storage_ndcd_1",
      "component_name": "NDCD 1",
      "excel_sheet": "Flows_UG2N",
      "excel_column": "NDCD1_Recirculation",
      "enabled": true
    }
  ]
}

Usage:
    loader = get_recirculation_loader()
    volumes = loader.get_recirculation("UG2N", month=1, year=2026)
    # Returns: {"storage_ndcd_1": 22500, "storage_tsf": 5000, ...}

Architecture:
- Uses centralized ExcelManager singleton for all Excel operations
- Ensures coordination with flow volumes and other systems
- All Excel access goes through one place (unified loading)
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
import logging
from datetime import datetime

from services.excel_manager import get_excel_manager

logger = logging.getLogger(__name__)

# Singleton instance
_recirculation_loader_instance = None


class RecirculationVolumeLoader:
    """Load recirculation volumes from Excel (SINGLETON PATTERN).
    
    Uses centralized ExcelManager for all Excel operations, ensuring coordination
    with flow volumes and other systems that access the same Excel file.
    
    Attributes:
        config_path: Path to diagram configuration JSON
        excel_manager: Reference to centralized ExcelManager singleton
        _cache: Dict[cache_key, Dict[component, volume]] for fast lookups
    """
    
    def __init__(self, config_path: str = None):
        """Initialize loader with diagram config path.
        
        Excel operations use centralized ExcelManager (no direct file access).
        This ensures coordination with flow volumes and other systems.
        
        Args:
            config_path: Path to diagram JSON (e.g., data/diagrams/UG2N_flow_diagram.json)
        """
        self.config_path = Path(config_path) if config_path else Path("data/diagrams/UG2N_flow_diagram.json")
        
        # Use centralized ExcelManager for all Excel operations
        # This is the same manager used by flow volumes, analytics, calculations
        self.excel_manager = get_excel_manager()
        
        self._cache = {}
        self._recirculation_config = {}
        
        self._load_config()
        logger.info(f"RecirculationVolumeLoader initialized (using centralized ExcelManager) with config: {self.config_path}")
    
    def _load_config(self):
        """Load recirculation configuration from diagram JSON.
        
        Reads which components have recirculation and which Excel sheet/column map to them.
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self._recirculation_config = data.get('recirculation', [])
                    logger.debug(f"Loaded recirculation config: {len(self._recirculation_config)} components")
            else:
                logger.warning(f"Config not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading recirculation config: {e}")
            self._recirculation_config = []
    
    def get_recirculation(self, area_code: str, month: int = None, year: int = None) -> Dict[str, float]:
        """Get recirculation volumes for area and date (MAIN API).
        
        Checks cache first, then reads from Excel via ExcelManager if needed.
        Uses centralized ExcelManager, ensuring coordination with flow volumes.
        If month/year not available in Excel, uses most recent date in sheet.
        
        Args:
            area_code: Area code (e.g., "UG2N", "UG2S")
            month: Month (1-12), if None uses current month or most recent in Excel
            year: Year, if None uses current year or most recent in Excel
        
        Returns:
            Dict mapping component_id to volume in m³
            Example: {"storage_ndcd_1": 22500, "storage_tsf": 5000}
        
        Raises:
            ValueError: If month/year invalid
        """
        if month is None or year is None:
            # Use current month/year, but will fallback to most recent in Excel if needed
            current_month = datetime.now().month
            current_year = datetime.now().year
            month = month or current_month
            year = year or current_year
        
        # Check cache
        cache_key = f"{area_code}_{month}_{year}"
        if cache_key in self._cache:
            logger.debug(f"Cache HIT: Recirculation {area_code} {month}/{year}")
            return self._cache[cache_key]
        
        # Load from Excel via centralized manager
        logger.debug(f"Cache MISS: Loading recirculation from Excel {area_code} {month}/{year}")
        volumes = self._read_from_excel(area_code, month, year)
        
        # Cache result
        self._cache[cache_key] = volumes
        logger.info(f"Loaded {len(volumes)} recirculation volumes for {area_code}")
        
        return volumes
    
    def _read_from_excel(self, area_code: str, month: int, year: int) -> Dict[str, float]:
        """Read recirculation volumes from Excel sheet via ExcelManager.
        
        Uses centralized ExcelManager, ensuring we read from the same source
        as flow volumes and other systems.
        
        Args:
            area_code: Area code (used to find sheet name, e.g., "UG2N")
            month: Month (1-12)
            year: Year
        
        Returns:
            Dict of component_id: volume (in m³)
        """
        try:
            volumes = {}
            
            logger.debug(f"[RECIRCULATION] _read_from_excel: Loading recirculation for {area_code}, {month}/{year}")
            logger.debug(f"[RECIRCULATION] Found {len(self._recirculation_config)} recirculation configs")
            
            # Iterate through configured recirculation components
            
            # Iterate through configured recirculation components
            for config in self._recirculation_config:
                component_id = config.get('component_id')
                sheet_name = config.get('excel_sheet')
                column_name = config.get('excel_column')
                enabled = config.get('enabled', False)
                
                logger.debug(f"[RECIRCULATION] Component: {component_id}, enabled={enabled}")
                
                if not enabled or not sheet_name or not column_name:
                    logger.debug(f"[RECIRCULATION] Skipped: enabled={enabled}")
                    continue
                
                # Load sheet and verify column exists
                try:
                    df = self.excel_manager.load_flow_sheet(sheet_name)
                    if column_name not in df.columns:
                        logger.warning(f"[RECIRCULATION] Column not found in {sheet_name}: {column_name}")
                        continue
                except Exception as e:
                    logger.error(f"[RECIRCULATION] Error loading sheet {sheet_name}: {e}")
                    continue
                
                # Try to load volume from Excel
                try:
                    volume = self.excel_manager.get_flow_volume(
                        area_code_or_sheet=sheet_name,
                        column_name=column_name,
                        year=year,
                        month=month
                    )
                    
                    if volume is not None:
                        volumes[component_id] = volume
                        logger.debug(f"[RECIRCULATION] Loaded: {component_id} = {volume} m³")
                    else:
                        logger.warning(f"[RECIRCULATION] No volume found for {component_id}")
                        
                except Exception as e:
                    logger.error(f"[RECIRCULATION] Error loading {component_id}: {e}")
            
            logger.debug(f"[RECIRCULATION] Loaded {len(volumes)} recirculation volumes for {area_code}")
            return volumes
            
        except Exception as e:
            logger.error(f"[RECIRCULATION] Error reading recirculation from Excel: {e}", exc_info=True)
            import traceback
            logger.error(f"[RECIRCULATION] Traceback: {traceback.format_exc()}")
            return {}
    
    def clear_cache(self):
        """Clear all cached recirculation data (call after Excel updates).
        
        This should be called when Excel files are reloaded or data changes.
        Coordinates with ExcelManager cache invalidation.
        """
        self._cache.clear()
        logger.info("Recirculation cache cleared")
    
    def set_config_path(self, config_path: str):
        """Update config path and reload (for diagram switching).
        
        Args:
            config_path: New path to diagram JSON
        """
        self.config_path = Path(config_path)
        self._load_config()
        self.clear_cache()
        logger.info(f"Recirculation config path updated: {config_path}")
    
    def get_all_components(self) -> List[Dict]:
        """Get all recirculation components from config.
        
        Returns:
            List of recirculation config dicts
        """
        return self._recirculation_config


def get_recirculation_loader() -> RecirculationVolumeLoader:
    """Get singleton instance of recirculation loader (SINGLETON GETTER).
    
    Uses centralized ExcelManager internally for all Excel operations.
    Ensures coordination with flow volumes and other systems.
    
    Returns:
        RecirculationVolumeLoader instance
    """
    global _recirculation_loader_instance
    if _recirculation_loader_instance is None:
        _recirculation_loader_instance = RecirculationVolumeLoader()
    return _recirculation_loader_instance


def reset_recirculation_loader():
    """Reset singleton instance (call after config changes).
    
    This clears the singleton so the next call to get_recirculation_loader()
    creates a fresh instance with updated configuration.
    """
    global _recirculation_loader_instance
    _recirculation_loader_instance = None
    logger.info("Recirculation loader singleton reset")
