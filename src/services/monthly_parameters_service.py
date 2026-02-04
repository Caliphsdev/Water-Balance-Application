"""
Monthly Parameters Service (BUSINESS LOGIC LAYER).

Provides validated operations for monthly inflows/outflows per facility.

Responsibilities:
- Validate inputs before persistence
- Ensure database table exists for upgraded deployments
- Provide clean API for UI controllers
- Handle database errors gracefully

Data source: SQLite (facility_monthly_parameters table)
"""

import logging
import sqlite3
from typing import List, Optional

from models.monthly_parameters import MonthlyParameters
from database.db_manager import DatabaseManager
from database.schema import DatabaseSchema
from database.repositories.monthly_parameters_repository import MonthlyParametersRepository


logger = logging.getLogger(__name__)


class MonthlyParametersService:
    """Monthly Parameters Service (BUSINESS LOGIC & VALIDATION).

    Methods:
    - get_history(): Fetch monthly history for a facility
    - create_monthly_parameters(): Insert new monthly totals
    - update_monthly_parameters(): Update existing totals
    - delete_monthly_parameters(): Delete a record

    Ensures schema is present before use (upgrade-safe).
    """

    def __init__(
        self,
        repository: Optional[MonthlyParametersRepository] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """Initialize service and ensure schema exists.

        Args:
            repository: MonthlyParametersRepository instance
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        self.repository = repository or MonthlyParametersRepository(self.db_manager)

        # Ensure table exists for upgraded databases (non-destructive)
        schema = DatabaseSchema(self.db_manager.db_path)
        schema.ensure_monthly_parameters_table()

        logger.info("MonthlyParametersService initialized")

    def get_history(self, facility_id: int, limit: int = 120, offset: int = 0) -> List[MonthlyParameters]:
        """Get monthly history for facility (READ - HISTORY).

        Args:
            facility_id: Storage facility ID (FK)
            limit: Max records to return (default 120)
            offset: Pagination offset

        Returns:
            List of MonthlyParameters sorted by year/month descending
        """
        return self.repository.list_by_facility(facility_id, limit=limit, offset=offset)

    def get_record_by_period(self, facility_id: int, year: int, month: int) -> Optional[MonthlyParameters]:
        """Get a single monthly record by facility and period (READ - BY PERIOD).

        Args:
            facility_id: Storage facility ID (FK)
            year: Calendar year
            month: Month number (1-12)

        Returns:
            MonthlyParameters if found, None otherwise
        """
        return self.repository.get_by_facility_month(facility_id, year, month)

    def create_monthly_parameters(
        self,
        facility_id: int,
        year: int,
        month: int,
        total_inflows_m3: float,
        total_outflows_m3: float
    ) -> MonthlyParameters:
        """Create new monthly parameters record (CREATE).

        Validation:
        - month 1-12
        - year 2000-2100
        - totals >= 0
        - unique (facility_id, year, month)

        Raises:
            ValueError: Validation error
            sqlite3.IntegrityError: Duplicate or FK violation
        """
        self._validate_inputs(year, month, total_inflows_m3, total_outflows_m3)

        record = MonthlyParameters(
            facility_id=facility_id,
            year=year,
            month=month,
            total_inflows_m3=total_inflows_m3,
            total_outflows_m3=total_outflows_m3,
        )

        try:
            created = self.repository.create(record)
            logger.info(
                f"Monthly parameters created for facility_id={facility_id} {year}-{month:02d}"
            )
            return created
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate or invalid monthly record: {e}")
            raise

    def update_monthly_parameters(
        self,
        record_id: int,
        total_inflows_m3: float,
        total_outflows_m3: float
    ) -> MonthlyParameters:
        """Update existing monthly parameters record (UPDATE).

        Args:
            record_id: Record ID to update
            total_inflows_m3: Updated inflows
            total_outflows_m3: Updated outflows

        Raises:
            ValueError: Validation error
        """
        if record_id <= 0:
            raise ValueError("record_id must be a positive integer")

        existing = self.repository.get_by_id(record_id)
        if not existing:
            raise ValueError("Monthly record not found")

        # Validate using existing year/month (period is immutable during update)
        self._validate_inputs(
            year=existing.year,
            month=existing.month,
            total_inflows_m3=total_inflows_m3,
            total_outflows_m3=total_outflows_m3,
        )

        updated_model = MonthlyParameters(
            id=record_id,
            facility_id=existing.facility_id,
            year=existing.year,
            month=existing.month,
            total_inflows_m3=total_inflows_m3,
            total_outflows_m3=total_outflows_m3,
        )

        updated = self.repository.update(updated_model)
        logger.info(f"Monthly parameters updated (id={record_id})")
        return updated

    def delete_monthly_parameters(self, record_id: int) -> int:
        """Delete monthly parameters record (DELETE).

        Args:
            record_id: Record ID to delete

        Returns:
            Number of rows deleted
        """
        if record_id <= 0:
            raise ValueError("record_id must be a positive integer")

        deleted = self.repository.delete(record_id)
        logger.info(f"Monthly parameters deleted (id={record_id})")
        return deleted

    @staticmethod
    def _validate_inputs(year: int, month: int, total_inflows_m3: float, total_outflows_m3: float) -> None:
        """Validate inputs for monthly parameters (VALIDATION).

        Args:
            year: Calendar year
            month: Month number (1-12)
            total_inflows_m3: Monthly inflow total
            total_outflows_m3: Monthly outflow total

        Raises:
            ValueError: If any input is invalid
        """
        if year < 2000 or year > 2100:
            raise ValueError("Year must be between 2000 and 2100")
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if total_inflows_m3 < 0:
            raise ValueError("Total inflows must be non-negative")
        if total_outflows_m3 < 0:
            raise ValueError("Total outflows must be non-negative")
