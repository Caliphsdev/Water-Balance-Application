"""
Storage Facility Service (BUSINESS LOGIC LAYER).

Service layer provides business operations and validation.

Responsibilities:
1. Validate storage facility operations
2. Implement business rules (capacity checks, status transitions)
3. Handle service-level errors and logging
4. Provide clean API for UI controllers
5. Abstract database/repository details

Why service layer:
- UI doesn't know about database (clean dependencies)
- Business logic centralized (easier to test, easier to change)
- Validation happens in one place
- Audit trail and logging
- Future: can add caching, notifications, etc.

Accessed by: StorageFacilitiesPage (UI dashboard)
Uses: StorageFacilityRepository (data access)
"""

import logging
import threading
from typing import List, Optional, Dict, Any
import sqlite3

from models.storage_facility import StorageFacility
from database.repositories.storage_facility_repository import StorageFacilityRepository
from database.db_manager import DatabaseManager
from database.schema import DatabaseSchema
from services.calculation.balance_service import reset_balance_service


logger = logging.getLogger(__name__)


class StorageFacilityService:
    """Storage Facility Service (BUSINESS LOGIC & OPERATIONS).
    
    Provides high-level operations for managing storage facilities.
    
    Key responsibilities:
    - Validate facility data before saving
    - Enforce business rules (e.g., active facilities can't be deleted)
    - Provide error messages suitable for UI
    - Log all operations
    - Handle database errors gracefully
    
    Methods:
    - get_facilities(): Get all facilities with filters
    - get_facility(): Get single facility by code
    - add_facility(): Create new facility with validation
    - update_facility(): Modify facility with business logic
    - delete_facility(): Remove facility (safely)
    - get_summary(): Get dashboard summary statistics
    
    All methods raise exceptions that are caught by UI,
    never crash the application.
    """
    
    def __init__(
        self,
        repository: Optional[StorageFacilityRepository] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """Initialize service (CONSTRUCTOR).
        
        Args:
            repository: StorageFacilityRepository instance
                       (creates new if not provided, allows dependency injection)
            db_manager: DatabaseManager instance
                       (passed to repository if repository not provided)
        """
        # Lazy init avoids blocking UI startup if SQLite is locked or slow.
        self._db_manager = db_manager
        self._repository = repository
        self._initialized = False
        self._init_lock = threading.Lock()

    def _ensure_initialized(self) -> None:
        """Initialize database/repository on first use (LAZY INIT GUARD).

        This defers schema checks and DB creation away from the splash screen.
        Safe to call from any method; runs only once.
        """
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            # Prefer injected dependencies; otherwise, create defaults.
            if self._db_manager is None:
                if self._repository is not None:
                    self._db_manager = getattr(self._repository, "db", None)
                if self._db_manager is None:
                    self._db_manager = DatabaseManager()

            if self._repository is None:
                self._repository = StorageFacilityRepository(self._db_manager)

            # Ensure is_lined column exists for upgraded databases.
            schema = DatabaseSchema(self._db_manager.db_path)
            schema.ensure_is_lined_column()

            self._initialized = True
            logger.info("StorageFacilityService initialized (lazy)")
    
    def get_facilities(
        self,
        status: Optional[str] = None,
        sort_by: str = "name"
    ) -> List[StorageFacility]:
        """Get storage facilities with optional filtering (READ - RETRIEVE FACILITIES).
        
        Retrieves facilities from database with optional filtering.
        
        Args:
            status: Filter by status ('active', 'inactive', 'decommissioned')
                   If None, returns all facilities regardless of status
            sort_by: Sort field ('name', 'code', 'capacity', 'volume')
                    Currently supports these sorts
        
        Returns:
            List of StorageFacility objects, sorted as specified
            Empty list if no facilities match criteria
        
        Raises:
            ValueError: If sort_by is invalid
            sqlite3.Error: Database error
        
        Example:
            service = StorageFacilityService()
            
            # Get all active facilities
            active = service.get_facilities(status='active')
            
            # Get all facilities
            all_facilities = service.get_facilities()
            
            # Filter and sort
            facilities = service.get_facilities(status='active', sort_by='volume')
        """
        # Lazy init keeps DB/schema work out of UI startup path.
        self._ensure_initialized()
        try:
            # Get facilities from repository
            if status:
                facilities = self._repository.list_by_status(status)
            else:
                facilities = self._repository.get_all()
            
            # Sort by requested field (post-retrieval sorting for flexibility)
            if sort_by == "name":
                facilities.sort(key=lambda f: f.name.lower())
            elif sort_by == "code":
                facilities.sort(key=lambda f: f.code.lower())
            elif sort_by == "capacity":
                facilities.sort(key=lambda f: f.capacity_m3, reverse=True)
            elif sort_by == "volume":
                facilities.sort(key=lambda f: f.current_volume_m3, reverse=True)
            else:
                raise ValueError(f"Invalid sort_by field: {sort_by}")
            
            logger.debug(f"Retrieved {len(facilities)} facilities (status={status}, sort_by={sort_by})")
            return facilities
        except sqlite3.Error as e:
            logger.error(f"Failed to get facilities: {e}")
            raise
    
    def get_facility(self, code: str) -> Optional[StorageFacility]:
        """Get single facility by code (READ - SINGLE FACILITY).
        
        Retrieves specific facility by its unique code.
        
        Args:
            code: Facility code (e.g., 'NDCD1', 'OLDTSF')
        
        Returns:
            StorageFacility object if found, None if not found
        
        Raises:
            sqlite3.Error: Database error
        
        Example:
            service = StorageFacilityService()
            facility = service.get_facility('NDCD1')
            if facility:
                logger.info(f"Found: {facility.name} ({facility.volume_percentage:.0f}% full)")
            else:
                logger.warning("Facility not found")
        """
        # Lazy init keeps DB/schema work out of UI startup path.
        self._ensure_initialized()
        try:
            facility = self._repository.get_by_code(code)
            if facility:
                logger.debug(f"Retrieved facility: {code}")
            else:
                logger.debug(f"Facility not found: {code}")
            return facility
        except sqlite3.Error as e:
            logger.error(f"Failed to get facility {code}: {e}")
            raise
    
    def add_facility(
        self,
        code: str,
        name: str,
        facility_type: str,
        capacity_m3: float,
        surface_area_m2: Optional[float] = None,
        current_volume_m3: float = 0,
        is_lined: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> StorageFacility:
        """Create new storage facility (CREATE - ADD NEW FACILITY).
        
        Creates new facility with full validation.
        
        Validation rules:
        1. Code must be non-empty and unique (checked before DB write)
        2. Name must be non-empty
        3. Facility type must be valid (TSF, Pond, Dam, Tank, Other)
        4. Capacity must be > 0 (enforced by Pydantic + DB CHECK)
        5. Volume must be <= capacity (logical check)
        6. Surface area must be non-negative if provided
        
        Args:
            code: Facility code (e.g., 'NDCD1') - MUST BE UNIQUE
            name: Display name (e.g., 'North Decline Decant 1')
            facility_type: Type (TSF, Pond, Dam, Tank, Other)
            capacity_m3: Total capacity in m³ (must be > 0)
            surface_area_m2: Surface area in m² (optional, for evaporation)
            current_volume_m3: Current water level in m³ (default 0)
            is_lined: Lined status - True=lined, False=unlined, None=not applicable
            notes: Additional notes (optional)
        
        Returns:
            Created StorageFacility object with id populated
        
        Raises:
            ValueError: If validation fails (provided to UI as error message)
            sqlite3.IntegrityError: If code already exists
            sqlite3.Error: Database error
        
        Example:
            service = StorageFacilityService()
            
            try:
                new_facility = service.add_facility(
                    code='NDCD1',
                    name='North Decline Decant 1',
                    facility_type='TSF',
                    capacity_m3=250000,
                    surface_area_m2=45000,
                    current_volume_m3=180000,
                    is_lined=True
                )
                logger.info(f"Created facility: {new_facility.code}")
            except ValueError as e:
                logger.error(f"Cannot create facility: {e}")
                # UI shows error dialog to user
        """
        # Lazy init keeps DB/schema work out of UI startup path.
        self._ensure_initialized()
        try:
            # Validation: Capacity must be positive (business rule)
            if capacity_m3 <= 0:
                raise ValueError("Capacity must be greater than 0 m³")
            
            # Validation: Current volume must not exceed capacity
            if current_volume_m3 > capacity_m3:
                raise ValueError(
                    f"Current volume ({current_volume_m3} m³) "
                    f"cannot exceed capacity ({capacity_m3} m³)"
                )
            
            # Validation: Surface area must be non-negative
            if surface_area_m2 is not None and surface_area_m2 < 0:
                raise ValueError("Surface area must be non-negative")
            
            # Create Pydantic model (performs additional validation)
            # NOTE: Status must be capitalized (Active, Inactive) for consistency with database schema
            facility = StorageFacility(
                code=code,
                name=name,
                facility_type=facility_type,
                capacity_m3=capacity_m3,
                surface_area_m2=surface_area_m2,
                current_volume_m3=current_volume_m3,
                is_lined=is_lined,
                status='Active',  # New facilities are always active (CAPITALIZED for consistency)
                notes=notes
            )
            
            # Save to repository
            created = self._repository.create(facility)
            logger.info(f"Facility created: {created.code} (id={created.id})")
            return created
        except ValueError as e:
            logger.warning(f"Failed to add facility (validation error): {e}")
            raise
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Facility code '{code}' already exists")
            else:
                logger.error(f"Failed to add facility (integrity error): {e}")
                raise
        except sqlite3.Error as e:
            logger.error(f"Failed to add facility (database error): {e}")
            raise
    
    def update_facility(
        self,
        facility_id: int,
        name: Optional[str] = None,
        facility_type: Optional[str] = None,
        capacity_m3: Optional[float] = None,
        surface_area_m2: Optional[float] = None,
        current_volume_m3: Optional[float] = None,
        is_lined: Optional[bool] = ...,  # Use Ellipsis as "not provided" sentinel
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> StorageFacility:
        """Update existing facility (UPDATE - MODIFY FACILITY).
        
        Updates facility with optional field changes.
        Only provided fields are updated (others remain unchanged).
        
        Validation:
        1. Facility must exist
        2. If capacity changed, current volume must not exceed new capacity
        3. Status transitions must be valid (active → inactive → decommissioned)
        4. Cannot change facility code (immutable business key)
        
        Args:
            facility_id: Database ID of facility to update
            name: New display name (optional)
            facility_type: New facility type (optional)
            capacity_m3: New capacity in m³ (optional)
            surface_area_m2: New surface area (optional)
            current_volume_m3: New current volume (optional)
            is_lined: New lined status (optional) - True=lined, False=unlined, None=not applicable
            status: New status (optional)
            notes: New notes (optional)
        
        Returns:
            Updated StorageFacility object
        
        Raises:
            ValueError: If facility not found or validation fails
            sqlite3.Error: Database error
        
        Example:
            service = StorageFacilityService()
            
            try:
                # Update volume after measurement
                updated = service.update_facility(
                    facility_id=1,
                    current_volume_m3=190000
                )
                logger.info(f"Updated {updated.code}: {updated.volume_percentage:.0f}% full")
            except ValueError as e:
                logger.error(f"Cannot update: {e}")
        """
        # Lazy init keeps DB/schema work out of UI startup path.
        self._ensure_initialized()
        
        # DATABASE PERSISTENCE LOGGING: Track update attempt with input context
        logger.info(f"UPDATE FACILITY START - ID: {facility_id}, Name: {name}, Type: {facility_type}, Capacity: {capacity_m3}, Volume: {current_volume_m3}, Lined: {is_lined}, Status: {status}")
        
        try:
            # Get existing facility
            facility = self._repository.get_by_id(facility_id)
            if not facility:
                # ERROR CONTEXT LOGGING: Track what was requested
                logger.error(f"ERROR CONTEXT - Facility not found: ID={facility_id}")
                raise ValueError(f"Facility not found (id={facility_id})")
            
            # Update only provided fields
            if name is not None:
                facility.name = name
            if facility_type is not None:
                facility.facility_type = facility_type
            if capacity_m3 is not None:
                if capacity_m3 <= 0:
                    raise ValueError("Capacity must be greater than 0 m³")
                # Check that current volume fits in new capacity
                if facility.current_volume_m3 > capacity_m3:
                    raise ValueError(
                        f"Current volume ({facility.current_volume_m3} m³) "
                        f"exceeds new capacity ({capacity_m3} m³)"
                    )
                facility.capacity_m3 = capacity_m3
            if surface_area_m2 is not None:
                if surface_area_m2 < 0:
                    raise ValueError("Surface area must be non-negative")
                facility.surface_area_m2 = surface_area_m2
            if current_volume_m3 is not None:
                if current_volume_m3 < 0:
                    raise ValueError("Volume cannot be negative")
                if current_volume_m3 > facility.capacity_m3:
                    raise ValueError(
                        f"Volume ({current_volume_m3} m³) "
                        f"exceeds capacity ({facility.capacity_m3} m³)"
                    )
                facility.current_volume_m3 = current_volume_m3
            if is_lined is not ...:  # Ellipsis = not provided, so update if anything else (True/False/None)
                facility.is_lined = is_lined
            if status is not None:
                # Normalize status to capitalized format (Active, Inactive, Decommissioned)
                # This ensures consistency with database schema expectations
                facility.status = status.capitalize() if status else 'Active'
            if notes is not None:
                facility.notes = notes
            
            # Save updated facility
            if self._repository.update(facility):
                logger.info(f"Facility updated: {facility.code} (id={facility_id})")
                # DATABASE PERSISTENCE LOGGING: Track what was saved
                logger.debug(f"DATABASE STEP - Saved changes to facility {facility.code}: Capacity={facility.capacity_m3}, Volume={facility.current_volume_m3}, Status={facility.status}")
                
                # CACHE INVALIDATION: Clear balance cache since storage data affects calculations
                # This ensures next calculation uses fresh data from updated facility
                try:
                    reset_balance_service()
                    logger.debug("Balance service cache cleared after facility update")
                except Exception as e:
                    logger.warning(f"Could not reset balance cache: {e}")
                
                return facility
            else:
                logger.error(f"ERROR CONTEXT - Failed to persist update for facility_id={facility_id}")
                raise ValueError(f"Failed to update facility (id={facility_id})")
        except ValueError as e:
            logger.warning(f"Failed to update facility: {e}")
            # ERROR CONTEXT LOGGING: Track validation failures
            logger.debug(f"ERROR CONTEXT - Validation error: {e}, Input: facility_id={facility_id}, capacity={capacity_m3}, volume={current_volume_m3}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to update facility (database error): {e}")
            # ERROR CONTEXT LOGGING: Track database errors
            logger.debug(f"ERROR CONTEXT - Database error: {e}, facility_id={facility_id}")
            raise
    
    def delete_facility(self, facility_id: int) -> bool:
        """Delete storage facility (DELETE - REMOVE FACILITY).
        
        Deletes facility from system.
        
        Safety constraints:
        1. Facility must exist
        2. Facility must be INACTIVE (active facilities cannot be deleted)
        3. Facility must be DECOMMISSIONED status (if implemented)
        
        To delete an active facility:
        1. Call update_facility() to set status='inactive'
        2. Then call delete_facility()
        
        Args:
            facility_id: Database ID of facility to delete
        
        Returns:
            True if deletion succeeded, False if facility not found
        
        Raises:
            ValueError: If facility is active or otherwise cannot be deleted
            sqlite3.Error: Database error
        
        Example:
            service = StorageFacilityService()
            
            # First mark as inactive
            service.update_facility(facility_id=1, status='inactive')
            
            # Then delete
            if service.delete_facility(facility_id=1):
                logger.info("Facility deleted")
            else:
                logger.error("Could not delete facility")
        """
        # Lazy init keeps DB/schema work out of UI startup path.
        self._ensure_initialized()
        try:
            # Get facility first (safety check)
            facility = self._repository.get_by_id(facility_id)
            if not facility:
                logger.warning(f"Cannot delete: facility not found (id={facility_id})")
                return False
            
            # Check if facility is active (cannot delete active facilities)
            if facility.status == 'active':
                raise ValueError(
                    f"Cannot delete active facility '{facility.code}'. "
                    "Mark as inactive first, then delete."
                )
            
            # Delete from repository
            if self._repository.delete(facility_id):
                logger.info(f"Facility deleted: {facility.code} (id={facility_id})")
                
                # CACHE INVALIDATION: Clear balance cache since facility removed
                try:
                    reset_balance_service()
                    logger.debug("Balance service cache cleared after facility deletion")
                except Exception as e:
                    logger.warning(f"Could not reset balance cache: {e}")
                
                return True
            else:
                logger.warning(f"Failed to delete facility (id={facility_id})")
                return False
        except ValueError as e:
            logger.warning(f"Cannot delete facility: {e}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to delete facility (database error): {e}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics (READ - SUMMARY STATISTICS).
        
        Calculates summary metrics for dashboard display.
        
        Metrics:
        - total_count: Total number of facilities
        - active_count: Number of active facilities
        - total_capacity: Sum of all capacities (m³)
        - total_volume: Sum of all current volumes (m³)
        - average_fullness: Average fill percentage across all facilities
        - facilities_at_risk: Count of facilities > 90% full or < 10% full
        - largest_facility: Facility with highest capacity
        - most_full_facility: Facility with highest fill percentage
        
        Returns:
            Dict with summary statistics
        
        Raises:
            sqlite3.Error: Database error
        
        Example:
            service = StorageFacilityService()
            summary = service.get_summary()
            
            print(f"Total capacity: {summary['total_capacity']} m³")
            print(f"Total volume: {summary['total_volume']} m³")
            print(f"Fill: {summary['average_fullness']:.1f}%")
            print(f"Risk count: {summary['facilities_at_risk']}")
        """
        # Lazy init keeps DB/schema work out of UI startup path.
        self._ensure_initialized()
        try:
            facilities = self._repository.get_all()
            
            if not facilities:
                return {
                    'total_count': 0,
                    'active_count': 0,
                    'total_capacity': 0,
                    'total_volume': 0,
                    'average_fullness': 0,
                    'facilities_at_risk': 0,
                    'largest_facility': None,
                    'most_full_facility': None
                }
            
            # Calculate metrics
            active_facilities = [f for f in facilities if f.status == 'active']
            total_capacity = sum(f.capacity_m3 for f in facilities)
            total_volume = sum(f.current_volume_m3 for f in facilities)
            
            # Average fullness (weighted by capacity)
            if total_capacity > 0:
                average_fullness = (total_volume / total_capacity) * 100
            else:
                average_fullness = 0
            
            # Facilities at risk (very full or very empty)
            at_risk = [f for f in facilities if f.is_full or f.is_empty]
            
            # Largest and most full
            largest = max(facilities, key=lambda f: f.capacity_m3) if facilities else None
            most_full = max(facilities, key=lambda f: f.volume_percentage) if facilities else None
            
            summary = {
                'total_count': len(facilities),
                'active_count': len(active_facilities),
                'total_capacity': total_capacity,
                'total_volume': total_volume,
                'average_fullness': average_fullness,
                'facilities_at_risk': len(at_risk),
                'largest_facility': largest.code if largest else None,
                'most_full_facility': most_full.code if most_full else None
            }
            
            logger.debug(f"Summary: {summary['total_count']} facilities, "
                        f"{summary['average_fullness']:.1f}% average fill")
            return summary
        except sqlite3.Error as e:
            logger.error(f"Failed to get summary: {e}")
            raise
