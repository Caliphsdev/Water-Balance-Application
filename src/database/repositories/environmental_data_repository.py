"""
Environmental Data Repository (Data Access Layer).

CRUD operations for monthly rainfall and evaporation data.
Includes audit logging for all modifications.
"""

from typing import List, Optional, Tuple
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from database.db_manager import DatabaseManager
from models.environmental_data import EnvironmentalData


class EnvironmentalDataRepository:
    """Repository for environmental data (CRUD + AUDIT LOGGING).
    
    Handles database operations for monthly rainfall and evaporation data.
    All updates are logged to environmental_data_audit table for compliance.
    
    Used by: EnvironmentalDataService
    """
    
    def __init__(self, db: DatabaseManager):
        """Initialize repository (CONSTRUCTOR).
        
        Args:
            db: Database manager instance (injected dependency)
        """
        self.db = db
    
    def get_by_year_month(self, year: int, month: int) -> Optional[EnvironmentalData]:
        """Get environmental data for specific year and month (READ).
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
        
        Returns:
            EnvironmentalData if found, None otherwise
        
        Example:
            data = repo.get_by_year_month(2025, 3)  # March 2025
            if data:
                logger.info("Rainfall: %smm", data.rainfall_mm)
        """
        rows = self.db.execute_query(
            "SELECT * FROM environmental_data WHERE year = ? AND month = ?",
            (year, month)
        )
        
        if rows:
            return EnvironmentalData(**rows[0])
        return None
    
    def list_by_year(self, year: int) -> List[EnvironmentalData]:
        """List all environmental data for a specific year (READ).
        
        Args:
            year: Year to filter by
        
        Returns:
            List of EnvironmentalData, sorted by month
        
        Example:
            data_2025 = repo.list_by_year(2025)  # All 12 months (if entered)
        """
        rows = self.db.execute_query(
            "SELECT * FROM environmental_data WHERE year = ? ORDER BY month",
            (year,)
        )
        return [EnvironmentalData(**row) for row in rows]
    
    def list_all(self) -> List[EnvironmentalData]:
        """List all environmental data (READ).
        
        Returns:
            List of all EnvironmentalData, sorted by year desc, month asc
        
        Used by: UI to display all historical data
        """
        rows = self.db.execute_query(
            "SELECT * FROM environmental_data ORDER BY year DESC, month ASC"
        )
        return [EnvironmentalData(**row) for row in rows]
    
    def get_distinct_years(self) -> List[int]:
        """Get list of distinct years with environmental data (UTILITY).
        
        Returns:
            Sorted list of years (descending, most recent first)
        
        Used by: UI year selector dropdown
        """
        rows = self.db.execute_query(
            "SELECT DISTINCT year FROM environmental_data ORDER BY year DESC"
        )
        return [row['year'] for row in rows]
    
    def create(self, data: EnvironmentalData) -> int:
        """Create new environmental data entry (CREATE).
        
        Args:
            data: EnvironmentalData instance to insert
        
        Returns:
            New record ID
        
        Raises:
            sqlite3.IntegrityError: If (year, month) already exists (UNIQUE constraint)
        
        Example:
            new_data = EnvironmentalData(year=2025, month=3, rainfall_mm=120, evaporation_mm=180)
            new_id = repo.create(new_data)
        """
        query = """
            INSERT INTO environmental_data (year, month, rainfall_mm, evaporation_mm, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        now = datetime.now()
        params = (
            data.year,
            data.month,
            data.rainfall_mm,
            data.evaporation_mm,
            now,
            now
        )
        
        # Use execute_mutation for INSERT operations
        self.db.execute_mutation(query, params)
        
        # Get the last inserted row ID
        result = self.db.execute_query(
            "SELECT last_insert_rowid() as id"
        )
        return result[0]['id'] if result else None
    
    def update(self, data: EnvironmentalData) -> bool:
        """Update existing environmental data entry (UPDATE + AUDIT).
        
        Args:
            data: EnvironmentalData with updated values
        
        Returns:
            True if updated, False if not found
        
        Side effects:
            Logs change to environmental_data_audit table
        
        Example:
            data.rainfall_mm = 150.5  # Update value
            success = repo.update(data)
        """
        # Get old values for audit log
        old_data = self.get_by_year_month(data.year, data.month)
        if not old_data:
            return False
        
        # Update record
        query = """
            UPDATE environmental_data 
            SET rainfall_mm = ?, evaporation_mm = ?, updated_at = ?
            WHERE year = ? AND month = ?
        """
        params = (
            data.rainfall_mm,
            data.evaporation_mm,
            datetime.now(),
            data.year,
            data.month
        )
        
        # Use execute_mutation for UPDATE operations
        self.db.execute_mutation(query, params)
        
        # Log to audit table
        self._log_history(old_data, data)
        
        return True
    
    def delete(self, year: int, month: int) -> bool:
        """Delete environmental data entry (DELETE).
        
        Args:
            year: Year to delete
            month: Month to delete
        
        Returns:
            True if deleted, False if not found
        
        Example:
            repo.delete(2025, 3)  # Remove March 2025 data
        """
        query = "DELETE FROM environmental_data WHERE year = ? AND month = ?"
        # Use execute_mutation for DELETE operations
        affected = self.db.execute_mutation(query, (year, month))
        return affected > 0
    
    def _log_history(self, old_data: EnvironmentalData, new_data: EnvironmentalData) -> None:
        """Log environmental data change to audit table (AUDIT LOGGING).
        
        Args:
            old_data: Previous values
            new_data: New values
        
        Side effects:
            Inserts record into environmental_data_audit table
        
        Why: Compliance requirement - track all environmental data changes
        for auditing and historical analysis.
        """
        query = """
            INSERT INTO environmental_data_audit 
            (year, month, old_rainfall_mm, new_rainfall_mm, old_evaporation_mm, new_evaporation_mm, changed_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            new_data.year,
            new_data.month,
            old_data.rainfall_mm,
            new_data.rainfall_mm,
            old_data.evaporation_mm,
            new_data.evaporation_mm,
            datetime.now(),
            'system'  # TODO: Add user tracking when auth implemented
        )
        
        # Use execute_mutation for audit logging
        self.db.execute_mutation(query, params)
    
    def list_history(self, year: Optional[int] = None, month: Optional[int] = None, limit: int = 100) -> List[dict]:
        """List audit history for environmental data (AUDIT QUERY).
        
        Args:
            year: Optional year filter
            month: Optional month filter
            limit: Maximum records to return (default 100)
        
        Returns:
            List of audit log entries, most recent first
        
        Example:
            history = repo.list_history(year=2025, month=3)  # All changes to March 2025
        """
        query = "SELECT * FROM environmental_data_audit WHERE 1=1"
        params = []
        
        if year is not None:
            query += " AND year = ?"
            params.append(year)
        
        if month is not None:
            query += " AND month = ?"
            params.append(month)
        
        query += " ORDER BY changed_at DESC LIMIT ?"
        params.append(limit)
        
        return self.db.execute_query(query, tuple(params))
