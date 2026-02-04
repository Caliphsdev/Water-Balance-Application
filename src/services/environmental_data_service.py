"""
Environmental Data Service (Business Logic + Caching).

Provides API for accessing rainfall and evaporation data.
Used by water balance calculator and Settings UI.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from database.repositories.environmental_data_repository import EnvironmentalDataRepository
from models.environmental_data import EnvironmentalData


# Singleton instance
_service_instance = None


class EnvironmentalDataService:
    """Service for environmental data (BUSINESS LOGIC + CACHING).
    
    Provides:
    1. Simple API for calculations: get_rainfall(), get_evaporation()
    2. CRUD operations for Settings UI
    3. In-memory caching for fast repeated access
    4. Data validation and business rules
    
    Used by:
    - WaterBalanceCalculator (get rainfall/evaporation for calculations)
    - SettingsPage (manage environmental data via UI)
    """
    
    def __init__(self):
        """Initialize service (CONSTRUCTOR).
        
        Initializes database connection and empty cache.
        Cache is loaded lazily on first access.
        """
        self.db = DatabaseManager()
        self.repository = EnvironmentalDataRepository(self.db)
        self._cache: Dict[Tuple[int, int], EnvironmentalData] = {}  # {(year, month): data}
        self._cache_loaded = False
    
    def _ensure_cache_loaded(self) -> None:
        """Load cache if not already loaded (LAZY LOADING).
        
        Why lazy: Avoid loading all data at app startup if not needed.
        Cache is loaded on first access to any method.
        """
        if not self._cache_loaded:
            self.refresh_cache()
    
    def refresh_cache(self) -> None:
        """Reload cache from database (CACHE MANAGEMENT).
        
        Call this after:
        - Creating/updating/deleting environmental data
        - Importing bulk data
        - Database changes outside the service
        
        Performance: Fast (<100ms) for typical dataset (few years of data).
        """
        all_data = self.repository.list_all()
        self._cache = {(d.year, d.month): d for d in all_data}
        self._cache_loaded = True
    
    def clear_cache(self) -> None:
        """Clear cache (CACHE MANAGEMENT).
        
        Forces reload on next access.
        Use when: Database modified externally.
        """
        self._cache.clear()
        self._cache_loaded = False
    
    # ==================== API FOR CALCULATIONS ====================
    
    def get_rainfall(self, year: int, month: int, default: float = 0.0) -> float:
        """Get rainfall for year/month (CALCULATION API).
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            default: Default value if not found (default 0.0)
        
        Returns:
            Rainfall in mm
        
        Example (in WaterBalanceCalculator):
            rainfall_mm = service.get_rainfall(2025, 3, default=0.0)
            rainfall_volume_m3 = (rainfall_mm / 1000) * surface_area_m2
        
        Performance: Cached, so repeated calls are instant.
        """
        self._ensure_cache_loaded()
        data = self._cache.get((year, month))
        return data.rainfall_mm if data else default
    
    def get_evaporation(self, year: int, month: int, default: float = 0.0) -> float:
        """Get evaporation for year/month (CALCULATION API).
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            default: Default value if not found (default 0.0)
        
        Returns:
            Evaporation in mm
        
        Example (in WaterBalanceCalculator):
            evap_mm = service.get_evaporation(2025, 3, default=0.0)
            evap_loss_m3 = (evap_mm / 1000) * surface_area_m2
        
        Performance: Cached, so repeated calls are instant.
        """
        self._ensure_cache_loaded()
        data = self._cache.get((year, month))
        return data.evaporation_mm if data else default
    
    # ==================== CRUD FOR UI ====================
    
    def get_entry(self, year: int, month: int) -> Optional[EnvironmentalData]:
        """Get environmental data entry (READ).
        
        Args:
            year: Year
            month: Month (1-12)
        
        Returns:
            EnvironmentalData if exists, None otherwise
        
        Used by: UI to check if data exists before creating
        """
        self._ensure_cache_loaded()
        return self._cache.get((year, month))
    
    def list_entries(self, year: Optional[int] = None) -> List[EnvironmentalData]:
        """List environmental data entries (READ).
        
        Args:
            year: Optional year filter (None = all years)
        
        Returns:
            List of EnvironmentalData, sorted by year desc, month asc
        
        Used by: UI to populate form for selected year
        """
        self._ensure_cache_loaded()
        
        if year is None:
            return sorted(self._cache.values(), key=lambda d: (d.year, d.month))
        
        return [
            data for (y, m), data in sorted(self._cache.items())
            if y == year
        ]
    
    def get_available_years(self) -> List[int]:
        """Get list of years with environmental data (UTILITY).
        
        Returns:
            Sorted list of years (most recent first)
        
        Used by: UI year selector dropdown
        """
        return self.repository.get_distinct_years()
    
    def create_or_update_entry(
        self, 
        year: int, 
        month: int, 
        rainfall_mm: float, 
        evaporation_mm: float
    ) -> EnvironmentalData:
        """Create or update environmental data entry (UPSERT).
        
        Args:
            year: Year
            month: Month (1-12)
            rainfall_mm: Rainfall in mm
            evaporation_mm: Evaporation in mm
        
        Returns:
            Created or updated EnvironmentalData
        
        Raises:
            ValueError: If validation fails (negative values, extremes)
        
        Used by: UI Save button - simplifies logic (no need to check if exists)
        """
        # Validate via Pydantic model
        data = EnvironmentalData(
            year=year,
            month=month,
            rainfall_mm=rainfall_mm,
            evaporation_mm=evaporation_mm
        )
        
        # Check if exists
        existing = self.repository.get_by_year_month(year, month)
        
        if existing:
            # Update existing
            data.id = existing.id
            self.repository.update(data)
        else:
            # Create new
            data.id = self.repository.create(data)
        
        # Refresh cache
        self.refresh_cache()
        
        return data
    
    def delete_entry(self, year: int, month: int) -> bool:
        """Delete environmental data entry (DELETE).
        
        Args:
            year: Year
            month: Month
        
        Returns:
            True if deleted, False if not found
        
        Used by: UI delete/clear functionality
        """
        success = self.repository.delete(year, month)
        if success:
            self.refresh_cache()
        return success
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_import(self, entries: List[Tuple[int, int, float, float]]) -> int:
        """Bulk import environmental data (BULK CREATE/UPDATE).
        
        Args:
            entries: List of (year, month, rainfall_mm, evaporation_mm) tuples
        
        Returns:
            Number of entries successfully imported
        
        Example:
            entries = [
                (2025, 1, 120.5, 180.0),
                (2025, 2, 95.3, 165.2),
                ...
            ]
            count = service.bulk_import(entries)
        
        Used by: Future Excel import feature
        """
        count = 0
        for year, month, rainfall, evaporation in entries:
            try:
                self.create_or_update_entry(year, month, rainfall, evaporation)
                count += 1
            except ValueError as e:
                # Log validation error but continue with other entries
                print(f"Skipping ({year}, {month}): {e}")
        
        return count
    
    def export_to_dict(self, year: Optional[int] = None) -> Dict:
        """Export environmental data to dictionary (EXPORT).
        
        Args:
            year: Optional year filter (None = all years)
        
        Returns:
            Dictionary with structure suitable for JSON/Excel export
        
        Example output:
            {
                "2025": {
                    "1": {"rainfall_mm": 120.5, "evaporation_mm": 180.0},
                    "2": {"rainfall_mm": 95.3, "evaporation_mm": 165.2},
                    ...
                }
            }
        
        Used by: Future Excel export feature
        """
        entries = self.list_entries(year)
        
        result = {}
        for entry in entries:
            year_key = str(entry.year)
            if year_key not in result:
                result[year_key] = {}
            
            result[year_key][str(entry.month)] = {
                "rainfall_mm": entry.rainfall_mm,
                "evaporation_mm": entry.evaporation_mm
            }
        
        return result
    
    def get_history(self, year: Optional[int] = None, month: Optional[int] = None) -> List[dict]:
        """Get audit history for environmental data (AUDIT QUERY).
        
        Args:
            year: Optional year filter
            month: Optional month filter
        
        Returns:
            List of audit log entries, most recent first
        
        Used by: Future audit/history UI feature
        """
        return self.repository.list_history(year, month)


def get_environmental_data_service() -> EnvironmentalDataService:
    """Get singleton instance of environmental data service (FACTORY).
    
    Returns:
        Shared EnvironmentalDataService instance
    
    Why singleton: Share cache across application, avoid duplicate DB queries.
    
    Example:
        service = get_environmental_data_service()
        rainfall = service.get_rainfall(2025, 3)
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = EnvironmentalDataService()
    return _service_instance


def reset_environmental_data_service() -> None:
    """Reset singleton instance (TESTING UTILITY).
    
    Forces creation of new service instance on next get_environmental_data_service() call.
    Use when: Database path changes, testing, or config updates.
    """
    global _service_instance
    _service_instance = None
