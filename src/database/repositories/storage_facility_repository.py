"""
Storage Facility Repository (DATA ACCESS LAYER - CRUD OPERATIONS).

Repository pattern provides clean interface between services and database.

Responsibilities:
1. Convert StorageFacility models to/from database rows
2. Execute CRUD operations (Create, Read, Update, Delete)
3. Handle database errors and validation
4. Prevent duplicate codes (data integrity)
5. Maintain audit trail (timestamps)

Why repository pattern:
- Services don't know about SQL (cleaner dependencies)
- Database details isolated in one place (easier to test, easier to change DB)
- Consistent error handling across all data access
- Single place to add caching/optimization in future

Database: SQLite (storage_facilities table)
Accessed by: StorageFacilityService
"""

import sqlite3
import logging
from typing import List, Optional
from datetime import datetime

from models.storage_facility import StorageFacility
from database.db_manager import DatabaseManager


logger = logging.getLogger(__name__)


class StorageFacilityRepository:
    """Storage Facility Repository (DATA ACCESS - STORAGE FACILITIES).
    
    Provides CRUD operations for storage facilities.
    
    Methods:
    - get_all(): Retrieve all facilities
    - get_by_id(): Get single facility by primary key
    - get_by_code(): Get single facility by facility code (business key)
    - create(): Insert new facility with validation
    - update(): Modify existing facility
    - delete(): Remove facility (with safety checks)
    - list_by_status(): Get facilities filtered by status
    
    All operations:
    - Use Pydantic models for type safety
    - Validate before database write
    - Handle errors gracefully
    - Log operations
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize repository (CONSTRUCTOR).
        
        Args:
            db_manager: DatabaseManager instance (creates new if not provided)
                       Allows dependency injection for testing
        """
        self.db = db_manager or DatabaseManager()
    
    def get_all(self) -> List[StorageFacility]:
        """Get all storage facilities (READ - ALL RECORDS).
        
        Retrieves all facilities from storage_facilities table.
        Results ordered by name for consistent display.
        
        Returns:
            List of StorageFacility objects (may be empty list if none exist)
        
        Raises:
            sqlite3.Error: Database error during query
        
        Example:
            repo = StorageFacilityRepository()
            facilities = repo.get_all()
            for facility in facilities:
                print(f"{facility.code}: {facility.name} ({facility.volume_percentage:.0f}%)")
        """
        try:
            rows = self.db.execute_query(
                """
                SELECT id, code, name, facility_type, capacity_m3, surface_area_m2,
                       current_volume_m3, is_lined, status, notes, created_at, updated_at
                FROM storage_facilities
                ORDER BY name
                """
            )
            
            # Convert database rows to Pydantic models
            facilities = []
            for row in rows:
                facility = self._row_to_model(row)
                facilities.append(facility)
            
            logger.debug(f"Retrieved {len(facilities)} facilities from database")
            return facilities
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve all facilities: {e}")
            raise
    
    def get_by_id(self, facility_id: int) -> Optional[StorageFacility]:
        """Get facility by database ID (READ - BY PRIMARY KEY).
        
        Fast lookup using database primary key (indexed).
        
        Args:
            facility_id: Database record ID
        
        Returns:
            StorageFacility object if found, None if not found
        
        Raises:
            sqlite3.Error: Database error
        
        Example:
            facility = repo.get_by_id(1)
            if facility:
                print(f"Found: {facility.name}")
            else:
                print("Facility not found")
        """
        try:
            row = self.db.execute_query(
                """
                SELECT id, code, name, facility_type, capacity_m3, surface_area_m2,
                       current_volume_m3, is_lined, status, notes, created_at, updated_at
                FROM storage_facilities
                WHERE id = ?
                """,
                (facility_id,),
                fetch_one=True
            )
            
            if not row:
                logger.debug(f"Facility with id={facility_id} not found")
                return None
            
            facility = self._row_to_model(row)
            logger.debug(f"Retrieved facility: {facility.code}")
            return facility
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve facility by id: {e}")
            raise
    
    def get_by_code(self, code: str) -> Optional[StorageFacility]:
        """Get facility by facility code (READ - BY BUSINESS KEY).
        
        Looks up facility by unique code (e.g., 'NDCD1', 'OLDTSF').
        Uses index (idx_storage_code) for fast lookup.
        
        Args:
            code: Facility code (e.g., 'NDCD1')
        
        Returns:
            StorageFacility object if found, None if not found
        
        Raises:
            sqlite3.Error: Database error
        
        Example:
            facility = repo.get_by_code('NDCD1')
            if facility:
                logger.info(f"Found {facility.name}: {facility.current_volume_m3} m³")
        """
        try:
            row = self.db.execute_query(
                """
                SELECT id, code, name, facility_type, capacity_m3, surface_area_m2,
                       current_volume_m3, is_lined, status, notes, created_at, updated_at
                FROM storage_facilities
                WHERE code = ?
                """,
                (code,),
                fetch_one=True
            )
            
            if not row:
                logger.debug(f"Facility with code='{code}' not found")
                return None
            
            facility = self._row_to_model(row)
            return facility
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve facility by code: {e}")
            raise
    
    def create(self, facility: StorageFacility) -> StorageFacility:
        """Create new storage facility (CREATE - INSERT NEW RECORD).
        
        Inserts new facility into database.
        
        Validation:
        1. Pydantic model validation (already done before calling this)
        2. Check code uniqueness (no duplicates)
        3. Check capacity > 0 (enforced by CHECK constraint)
        
        Args:
            facility: StorageFacility model (code must be unique)
        
        Returns:
            StorageFacility with id field populated (auto-generated)
        
        Raises:
            sqlite3.IntegrityError: Code already exists or constraint violation
            sqlite3.Error: Database error
        
        Example:
            new_facility = StorageFacility(
                code="NDCD1",
                name="North Decline Decant 1",
                facility_type="TSF",
                capacity_m3=250000,
                current_volume_m3=180000
            )
            
            try:
                created = repo.create(new_facility)
                logger.info(f"Created facility with id={created.id}")
            except sqlite3.IntegrityError:
                logger.error(f"Facility code '{new_facility.code}' already exists")
        """
        # Check code uniqueness first (provides better error message than DB constraint)
        existing = self.get_by_code(facility.code)
        if existing:
            raise sqlite3.IntegrityError(
                f"Facility code '{facility.code}' already exists (id={existing.id})"
            )
        
        try:
            # Insert new record
            affected = self.db.execute_mutation(
                """
                INSERT INTO storage_facilities
                (code, name, facility_type, capacity_m3, surface_area_m2,
                 current_volume_m3, is_lined, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    facility.code,
                    facility.name,
                    facility.facility_type,
                    facility.capacity_m3,
                    facility.surface_area_m2,
                    facility.current_volume_m3,
                    1 if facility.is_lined is True else (0 if facility.is_lined is False else None),
                    facility.status,
                    facility.notes,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ),
                create_backup=False  # Don't backup on insert (not critical)
            )
            
            # Retrieve created record (to get auto-generated id)
            created = self.get_by_code(facility.code)
            if created:
                logger.info(f"Created facility: {facility.code} (id={created.id})")
                return created
            else:
                raise RuntimeError(f"Failed to retrieve created facility: {facility.code}")
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create facility (integrity error): {e}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to create facility: {e}")
            raise
    
    def update(self, facility: StorageFacility) -> bool:
        """Update existing storage facility (UPDATE - MODIFY RECORD).
        
        Updates facility record in database.
        
        Validation:
        1. Facility must exist (id required, not None)
        2. Code cannot be changed (business key is immutable)
        3. Pydantic validation already done
        
        Args:
            facility: StorageFacility model with id set
        
        Returns:
            True if update succeeded, False if facility not found
        
        Raises:
            ValueError: If id is None (can't update without id)
            sqlite3.IntegrityError: Constraint violation
            sqlite3.Error: Database error
        
        Example:
            facility = repo.get_by_code('NDCD1')
            facility.current_volume_m3 = 190000
            facility.status = 'active'
            
            if repo.update(facility):
                logger.info(f"Updated {facility.code}")
            else:
                logger.error(f"Facility {facility.code} not found")
        """
        if facility.id is None:
            raise ValueError("Cannot update facility without id (id is None)")
        
        try:
            # Update record
            affected = self.db.execute_mutation(
                """
                UPDATE storage_facilities
                SET name=?, facility_type=?, capacity_m3=?, surface_area_m2=?,
                    current_volume_m3=?, is_lined=?, status=?, notes=?, updated_at=?
                WHERE id=?
                """,
                (
                    facility.name,
                    facility.facility_type,
                    facility.capacity_m3,
                    facility.surface_area_m2,
                    facility.current_volume_m3,
                    1 if facility.is_lined is True else (0 if facility.is_lined is False else None),
                    facility.status,
                    facility.notes,
                    datetime.now().isoformat(),
                    facility.id
                ),
                create_backup=True  # Backup before update (modifying data)
            )
            
            if affected > 0:
                logger.info(f"Updated facility: {facility.code} (id={facility.id})")
                return True
            else:
                logger.warning(f"Facility not found for update: id={facility.id}")
                return False
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to update facility (integrity error): {e}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to update facility: {e}")
            raise
    
    def delete(self, facility_id: int) -> bool:
        """Delete storage facility (DELETE - REMOVE RECORD).
        
        Deletes facility from database.
        
        Safety checks:
        1. Facility must exist
        2. Only inactive facilities can be deleted (safety)
        3. Backup created before delete
        
        Args:
            facility_id: Database record ID to delete
        
        Returns:
            True if delete succeeded, False if facility not found or is active
        
        Raises:
            ValueError: If trying to delete active facility
            sqlite3.Error: Database error
        
        Example:
            # Mark as inactive first
            facility = repo.get_by_id(1)
            facility.status = 'inactive'
            repo.update(facility)
            
            # Then delete
            if repo.delete(1):
                logger.info("Facility deleted")
            else:
                logger.error("Could not delete facility")
        """
        try:
            # Check facility exists and is inactive
            facility = self.get_by_id(facility_id)
            if not facility:
                logger.warning(f"Cannot delete: facility not found (id={facility_id})")
                return False
            
            if facility.status == 'active':
                raise ValueError(
                    f"Cannot delete active facility: {facility.code} (id={facility_id}). "
                    "Mark as inactive first."
                )
            
            # Delete record
            affected = self.db.execute_mutation(
                "DELETE FROM storage_facilities WHERE id=?",
                (facility_id,),
                create_backup=True  # Backup before delete
            )
            
            if affected > 0:
                logger.info(f"Deleted facility: {facility.code} (id={facility_id})")
                return True
            else:
                logger.warning(f"Facility not found for delete: id={facility_id}")
                return False
        except ValueError as e:
            logger.warning(f"Cannot delete facility: {e}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to delete facility: {e}")
            raise
    
    def list_by_status(self, status: str) -> List[StorageFacility]:
        """Get facilities filtered by status (READ - FILTERED LIST).
        
        Retrieves facilities with specific status.
        Uses index (idx_storage_status) for fast filtering.
        
        Args:
            status: Status to filter by ('active', 'inactive', 'decommissioned')
        
        Returns:
            List of StorageFacility objects with matching status
        
        Raises:
            sqlite3.Error: Database error
        
        Example:
            active = repo.list_by_status('active')
            logger.info(f"Active facilities: {len(active)}")
            
            for facility in active:
                if facility.is_full:
                    logger.warning(f"{facility.code} is full ({facility.volume_percentage:.0f}%)")
        """
        try:
            rows = self.db.execute_query(
                """
                SELECT id, code, name, facility_type, capacity_m3, surface_area_m2,
                       current_volume_m3, is_lined, status, notes, created_at, updated_at
                FROM storage_facilities
                WHERE status = ?
                ORDER BY name
                """,
                (status,)
            )
            
            facilities = [self._row_to_model(row) for row in rows]
            logger.debug(f"Retrieved {len(facilities)} facilities with status='{status}'")
            return facilities
        except sqlite3.Error as e:
            logger.error(f"Failed to list facilities by status: {e}")
            raise
    
    @staticmethod
    def _row_to_model(row: dict) -> StorageFacility:
        """Convert database row to StorageFacility model (INTERNAL - CONVERSION).
        
        Transforms dict (from database) to Pydantic model.
        Handles datetime parsing and type conversions.
        
        Args:
            row: Dict from database (result of execute_query with dict_factory)
        
        Returns:
            StorageFacility Pydantic model instance
        
        Raises:
            ValueError: If row data is invalid
        """
        try:
            # Parse ISO datetime strings back to datetime objects
            created_at = row['created_at']
            updated_at = row['updated_at']
            
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            
            # Convert is_lined: SQL INTEGER (0/1/NULL) -> Python bool (False/True/None)
            is_lined_val = row.get('is_lined')
            is_lined = None if is_lined_val is None else bool(is_lined_val)
            
            # Create and return model
            return StorageFacility(
                id=row['id'],
                code=row['code'],
                name=row['name'],
                facility_type=row['facility_type'],
                capacity_m3=row['capacity_m3'],
                surface_area_m2=row['surface_area_m2'],
                current_volume_m3=row['current_volume_m3'],
                is_lined=is_lined,
                status=row['status'],
                notes=row['notes'],
                created_at=created_at,
                updated_at=updated_at
            )
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to convert database row to model: {e}")
            raise
