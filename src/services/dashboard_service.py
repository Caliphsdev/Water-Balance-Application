"""
Dashboard Service (KPI AGGREGATION LAYER).

Aggregates data from multiple sources to provide complete dashboard KPIs.
Used by DashboardPage to populate all KPI cards.

Data sources:
- StorageFacilityService: storage facilities count, capacity, volume, utilization
- EnvironmentalDataService: rainfall, evaporation
- FlowDiagramPage: balance data (inflows, outflows, recirculation, error)

This service consolidates all data retrieval for the main dashboard.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.storage_facility_service import StorageFacilityService
from services.environmental_data_service import get_environmental_data_service

logger = logging.getLogger(__name__)


# Singleton instance
_service_instance: Optional['DashboardService'] = None


class DashboardService:
    """Dashboard Service (CENTRAL KPI AGGREGATION).
    
    Provides a single method to fetch all KPIs needed for the main dashboard.
    
    Methods:
    - get_dashboard_kpis(): Get complete set of dashboard data
    - get_storage_kpis(): Get storage-related metrics only
    
    Used by:
    - DashboardPage: populate KPI cards on startup and refresh
    - MainWindow: initial data load
    """
    
    def __init__(self):
        """Initialize service (CONSTRUCTOR).
        
        Initializes connections to dependent services.
        Uses lazy loading for expensive service calls.
        """
        self._storage_service: Optional[StorageFacilityService] = None
        self._env_service = None
    
    def _get_storage_service(self) -> StorageFacilityService:
        """Get storage facility service (LAZY INIT).
        
        Returns:
            StorageFacilityService instance
        """
        if self._storage_service is None:
            self._storage_service = StorageFacilityService()
        return self._storage_service
    
    def _get_env_service(self):
        """Get environmental data service (LAZY INIT).
        
        Returns:
            EnvironmentalDataService instance
        """
        if self._env_service is None:
            self._env_service = get_environmental_data_service()
        return self._env_service
    
    def get_dashboard_kpis(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Get complete dashboard KPI data (MAIN AGGREGATION METHOD).
        
        Fetches data from all sources and returns a single dict suitable for
        DashboardPage.update_data().
        
        Args:
            month: Month (1-12) for environmental data. Defaults to current month.
            year: Year for environmental data. Defaults to current year.
        
        Returns:
            Dict with all dashboard KPIs:
            - water_sources: int (count of active sources - from storage facilities for now)
            - storage_facilities: int (count of dams)
            - total_capacity: float (Mm³)
            - current_volume: float (Mm³)
            - utilization: float (percentage)
            - rainfall: float (mm) or None if not available
            - evaporation: float (mm) or None if not available
            - month: int (1-12)
            - year: int
        
        Example:
            service = get_dashboard_service()
            data = service.get_dashboard_kpis(month=12, year=2025)
            dashboard.update_data(data)
        """
        # Default to current date if not specified
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        
        result = {
            'month': month,
            'year': year,
        }
        
        # Get storage facility KPIs
        try:
            storage_kpis = self.get_storage_kpis()
            result.update(storage_kpis)
        except Exception as e:
            logger.warning(f"Could not load storage KPIs: {e}")
            # Provide defaults
            result.update({
                'storage_facilities': 0,
                'total_capacity': 0.0,
                'current_volume': 0.0,
                'utilization': 0.0,
            })
        
        # Get environmental data
        try:
            env_service = self._get_env_service()
            rainfall = env_service.get_rainfall(year, month, default=None)
            evaporation = env_service.get_evaporation(year, month, default=None)
            
            if rainfall is not None:
                result['rainfall'] = rainfall
            if evaporation is not None:
                result['evaporation'] = evaporation
        except Exception as e:
            logger.warning(f"Could not load environmental data: {e}")
        
        logger.debug(f"Dashboard KPIs loaded: {result}")
        return result
    
    def get_storage_kpis(self) -> Dict[str, Any]:
        """Get storage facility KPIs only (FOCUSED RETRIEVAL).
        
        Returns:
            Dict with storage-related KPIs:
            - storage_facilities: int (count of active facilities)
            - total_capacity: float (Mm³)
            - current_volume: float (Mm³)
            - utilization: float (percentage)
        """
        storage_service = self._get_storage_service()
        summary = storage_service.get_summary()
        
        # Convert from m³ to Mm³ (megaliters = millions of cubic meters)
        total_capacity_m3 = summary.get('total_capacity', 0)
        total_volume_m3 = summary.get('total_volume', 0)
        
        # Convert to Mm³ (divide by 1,000,000)
        total_capacity_mm3 = total_capacity_m3 / 1_000_000
        current_volume_mm3 = total_volume_m3 / 1_000_000
        
        # Calculate utilization percentage
        utilization = summary.get('average_fullness', 0)
        
        # Count active facilities
        active_count = summary.get('active_count', 0)
        
        return {
            'storage_facilities': active_count,
            'total_capacity': total_capacity_mm3,
            'current_volume': current_volume_mm3,
            'utilization': utilization,
        }


def get_dashboard_service() -> DashboardService:
    """Get singleton dashboard service instance (SINGLETON ACCESSOR).
    
    Returns:
        DashboardService instance (created on first call)
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = DashboardService()
    return _service_instance


def reset_dashboard_service() -> None:
    """Reset singleton instance (FOR TESTING/CACHE INVALIDATION).
    
    Forces re-creation of service on next get_dashboard_service() call.
    """
    global _service_instance
    _service_instance = None
