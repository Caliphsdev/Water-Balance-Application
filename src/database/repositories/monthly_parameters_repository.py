"""
Monthly Parameters Repository (DATA ACCESS LAYER - CRUD OPERATIONS).

Repository for facility_monthly_parameters table with:
- Create, read, update, delete operations
- History listing by facility with pagination
- Data conversion between DB rows and Pydantic models

Database: SQLite (facility_monthly_parameters table)
Accessed by: MonthlyParametersService
"""

import sqlite3
import logging
from typing import List, Optional
from datetime import datetime

from models.monthly_parameters import MonthlyParameters
from database.db_manager import DatabaseManager


logger = logging.getLogger(__name__)


class MonthlyParametersRepository:
    """Monthly Parameters Repository (DATA ACCESS - MONTHLY TOTALS).

    Provides CRUD operations for monthly inflow/outflow records.

    Methods:
    - get_by_id(): Retrieve a single record by ID
    - get_by_facility_month(): Retrieve record for facility/year/month
    - list_by_facility(): Get history list with pagination
    - create(): Insert new monthly record
    - update(): Update existing record
    - delete(): Delete record by ID

    All operations:
    - Use Pydantic model for validation
    - Use parameterized queries (safe SQL)
    - Log operations for audit/debug
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize repository (CONSTRUCTOR).

        Args:
            db_manager: DatabaseManager instance (creates new if not provided)
        """
        self.db = db_manager or DatabaseManager()

    def get_by_id(self, record_id: int) -> Optional[MonthlyParameters]:
        """Get monthly record by primary key (READ - BY ID).

        Args:
            record_id: Database record ID

        Returns:
            MonthlyParameters if found, None otherwise
        """
        row = self.db.execute_query(
            """
            SELECT id, facility_id, year, month, total_inflows_m3, total_outflows_m3,
                   created_at, updated_at
            FROM facility_monthly_parameters
            WHERE id = ?
            """,
            (record_id,),
            fetch_one=True
        )

        return self._row_to_model(row) if row else None

    def get_by_facility_month(
        self,
        facility_id: int,
        year: int,
        month: int
    ) -> Optional[MonthlyParameters]:
        """Get monthly record for facility and period (READ - BY FACILITY+MONTH).

        Args:
            facility_id: Storage facility ID (FK)
            year: Calendar year (e.g., 2026)
            month: Month number (1-12)

        Returns:
            MonthlyParameters if found, None otherwise
        """
        row = self.db.execute_query(
            """
            SELECT id, facility_id, year, month, total_inflows_m3, total_outflows_m3,
                   created_at, updated_at
            FROM facility_monthly_parameters
            WHERE facility_id = ? AND year = ? AND month = ?
            """,
            (facility_id, year, month),
            fetch_one=True
        )

        return self._row_to_model(row) if row else None

    def list_by_facility(
        self,
        facility_id: int,
        limit: int = 120,
        offset: int = 0
    ) -> List[MonthlyParameters]:
        """List monthly records for facility (READ - HISTORY LIST WITH PAGINATION).

        Args:
            facility_id: Storage facility ID (FK)
            limit: Max number of records to return (default 120 ~ 10 years)
            offset: Offset for pagination

        Returns:
            List of MonthlyParameters sorted by year/month descending

        Performance:
            Uses indexed columns (facility_id, year, month) for fast retrieval.
        """
        rows = self.db.execute_query(
            """
            SELECT id, facility_id, year, month, total_inflows_m3, total_outflows_m3,
                   created_at, updated_at
            FROM facility_monthly_parameters
            WHERE facility_id = ?
            ORDER BY year DESC, month DESC
            LIMIT ? OFFSET ?
            """,
            (facility_id, limit, offset)
        )

        return [self._row_to_model(row) for row in rows]

    def create(self, record: MonthlyParameters) -> MonthlyParameters:
        """Create new monthly record (CREATE - INSERT RECORD).

        Args:
            record: MonthlyParameters model

        Returns:
            Created MonthlyParameters with ID populated

        Raises:
            sqlite3.IntegrityError: Duplicate (facility_id, year, month) or FK issues
        """
        self.db.execute_mutation(
            """
            INSERT INTO facility_monthly_parameters
            (facility_id, year, month, total_inflows_m3, total_outflows_m3, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.facility_id,
                record.year,
                record.month,
                record.total_inflows_m3,
                record.total_outflows_m3,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
            create_backup=False
        )

        created = self.get_by_facility_month(record.facility_id, record.year, record.month)
        if not created:
            raise sqlite3.Error("Failed to retrieve created monthly record")
        return created

    def update(self, record: MonthlyParameters) -> MonthlyParameters:
        """Update existing monthly record (UPDATE - MODIFY RECORD).

        Args:
            record: MonthlyParameters model (must include id)

        Returns:
            Updated MonthlyParameters
        """
        if not record.id:
            raise ValueError("MonthlyParameters.id is required for update")

        self.db.execute_mutation(
            """
            UPDATE facility_monthly_parameters
            SET total_inflows_m3 = ?,
                total_outflows_m3 = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                record.total_inflows_m3,
                record.total_outflows_m3,
                datetime.now().isoformat(),
                record.id,
            ),
            create_backup=False
        )

        updated = self.get_by_id(record.id)
        if not updated:
            raise sqlite3.Error("Failed to retrieve updated monthly record")
        return updated

    def delete(self, record_id: int) -> int:
        """Delete monthly record by ID (DELETE - REMOVE RECORD).

        Args:
            record_id: Record ID to delete

        Returns:
            Number of rows deleted (0 or 1)
        """
        return self.db.execute_mutation(
            "DELETE FROM facility_monthly_parameters WHERE id = ?",
            (record_id,),
            create_backup=True
        )

    @staticmethod
    def _row_to_model(row: dict) -> MonthlyParameters:
        """Convert database row dict to MonthlyParameters model (ROW MAPPER).

        Args:
            row: Dict from sqlite row factory

        Returns:
            MonthlyParameters model with validated fields
        """
        return MonthlyParameters(
            id=row.get("id"),
            facility_id=row.get("facility_id"),
            year=row.get("year"),
            month=row.get("month"),
            total_inflows_m3=row.get("total_inflows_m3", 0),
            total_outflows_m3=row.get("total_outflows_m3", 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
