"""
Area Exclusion Manager - Manage which areas are included in balance calculations
Allows decoupling specific areas from overall balance check
"""

from pathlib import Path
from typing import Set, List
import json
from utils.app_logger import logger


class AreaExclusionManager:
    """Manages area exclusions for balance check calculations"""
    
    CONFIG_FILE = Path(__file__).parent.parent / "config" / "area_exclusions.json"
    
    def __init__(self):
        """Initialize exclusion manager"""
        self.excluded_areas: Set[str] = set()
        self._load_exclusions()
    
    def _load_exclusions(self):
        """Load excluded areas from config file"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.excluded_areas = set(config.get('excluded_areas', []))
                    logger.info(f"✅ Loaded {len(self.excluded_areas)} excluded areas from config")
            else:
                self.excluded_areas = set()
                self._save_exclusions()
        except Exception as e:
            logger.error(f"Error loading area exclusions: {e}")
            self.excluded_areas = set()
    
    def _save_exclusions(self):
        """Save excluded areas to config file"""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({
                    'excluded_areas': sorted(list(self.excluded_areas)),
                    'description': 'Areas excluded from balance check calculations'
                }, f, indent=2)
            logger.info(f"✅ Saved {len(self.excluded_areas)} excluded areas to config")
        except Exception as e:
            logger.error(f"Error saving area exclusions: {e}")
    
    def exclude_area(self, area: str) -> bool:
        """Exclude an area from calculations
        
        Returns:
            True if area was added to exclusions, False if already excluded
        """
        if area in self.excluded_areas:
            logger.info(f"Area {area} already excluded")
            return False
        
        self.excluded_areas.add(area)
        self._save_exclusions()
        logger.info(f"✅ Excluded area: {area}")
        return True
    
    def include_area(self, area: str) -> bool:
        """Re-include an area in calculations
        
        Returns:
            True if area was removed from exclusions, False if not excluded
        """
        if area not in self.excluded_areas:
            logger.info(f"Area {area} not in exclusions")
            return False
        
        self.excluded_areas.remove(area)
        self._save_exclusions()
        logger.info(f"✅ Re-included area: {area}")
        return True
    
    def is_excluded(self, area: str) -> bool:
        """Check if area is excluded"""
        return area in self.excluded_areas
    
    def get_excluded_areas(self) -> List[str]:
        """Get list of excluded areas"""
        return sorted(list(self.excluded_areas))
    
    def get_included_areas(self, all_areas: List[str]) -> List[str]:
        """Get list of areas that are NOT excluded
        
        Args:
            all_areas: List of all available areas
            
        Returns:
            List of areas that are included (not excluded)
        """
        return sorted([a for a in all_areas if not self.is_excluded(a)])
    
    def clear_exclusions(self):
        """Clear all exclusions"""
        self.excluded_areas.clear()
        self._save_exclusions()
        logger.info("✅ Cleared all area exclusions")
    
    def set_exclusions(self, areas: List[str]):
        """Set exclusions to exact list
        
        Args:
            areas: List of areas to exclude
        """
        self.excluded_areas = set(areas)
        self._save_exclusions()
        logger.info(f"✅ Set exclusions to: {sorted(list(self.excluded_areas))}")


# Singleton instance
_exclusion_manager = None


def get_area_exclusion_manager() -> AreaExclusionManager:
    """Get singleton exclusion manager instance"""
    global _exclusion_manager
    if _exclusion_manager is None:
        _exclusion_manager = AreaExclusionManager()
    return _exclusion_manager
