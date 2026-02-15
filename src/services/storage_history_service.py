import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from database.db_manager import DatabaseManager
from database.schema import DatabaseSchema
from models.storage_history import StorageHistoryRecord


logger = logging.getLogger(__name__)


class StorageHistoryService:
    """Service for storage history CRUD and monthly volume updates."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db_manager = db_manager or DatabaseManager()
        schema = DatabaseSchema(self.db_manager.db_path)
        schema.ensure_storage_history_tables()

    def get_history(
        self, facility_code: str, limit: int = 120, offset: int = 0
    ) -> List[StorageHistoryRecord]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, facility_code, year, month, opening_volume_m3, closing_volume_m3, "
                "data_source, notes, created_at, updated_at "
                "FROM storage_history "
                "WHERE facility_code = ? "
                "ORDER BY year DESC, month DESC "
                "LIMIT ? OFFSET ?",
                (facility_code, limit, offset),
            )
            rows = cursor.fetchall()
            return [StorageHistoryRecord(**row) for row in rows]
        finally:
            conn.close()

    def get_previous_closing(
        self, facility_code: str, year: int, month: int
    ) -> Optional[float]:
        prev_month, prev_year = self._previous_period(year, month)
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT closing_volume_m3 FROM storage_history "
                "WHERE facility_code = ? AND year = ? AND month = ?",
                (facility_code, prev_year, prev_month),
            )
            row = cursor.fetchone()
            if row:
                return float(row["closing_volume_m3"])
            return None
        finally:
            conn.close()

    def get_current_volume(self, facility_code: str) -> Optional[float]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT current_volume_m3 FROM storage_facilities WHERE code = ?",
                (facility_code,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return float(row["current_volume_m3"] or 0.0)
        finally:
            conn.close()

    def get_opening_for_period(
        self, facility_code: str, year: int, month: int
    ) -> Tuple[float, str]:
        prev = self.get_previous_closing(facility_code, year, month)
        if prev is not None:
            return prev, "previous month closing"

        current = self.get_current_volume(facility_code)
        if current is not None:
            return current, "current facility volume (no prior history)"

        return 0.0, "defaulted to 0 (no prior history or facility volume)"

    def upsert_monthly_storage(
        self,
        facility_code: str,
        year: int,
        month: int,
        closing_volume_m3: float,
        data_source: str = "measured",
        notes: Optional[str] = None,
    ) -> StorageHistoryRecord:
        opening_volume_m3, opening_note = self.get_opening_for_period(
            facility_code, year, month
        )
        combined_notes = notes or opening_note

        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "INSERT INTO storage_history (facility_code, year, month, opening_volume_m3, closing_volume_m3, data_source, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(facility_code, year, month) DO UPDATE SET "
                "opening_volume_m3 = excluded.opening_volume_m3, "
                "closing_volume_m3 = excluded.closing_volume_m3, "
                "data_source = excluded.data_source, "
                "notes = excluded.notes, "
                "updated_at = CURRENT_TIMESTAMP",
                (
                    facility_code,
                    year,
                    month,
                    opening_volume_m3,
                    closing_volume_m3,
                    data_source,
                    combined_notes,
                ),
            )

            # Keep current snapshot stable: only update current_volume_m3 when
            # saving the latest/newer month. Historical edits remain in history.
            if self._should_update_current_volume(conn, year, month):
                conn.execute(
                    "UPDATE storage_facilities SET current_volume_m3 = ?, updated_at = CURRENT_TIMESTAMP WHERE code = ?",
                    (closing_volume_m3, facility_code),
                )
            else:
                logger.info(
                    "Skipped current volume update for historical period %s %04d-%02d",
                    facility_code,
                    year,
                    month,
                )
            conn.commit()
        finally:
            conn.close()

        logger.info(
            "Saved storage history %s %04d-%02d: opening=%.2f closing=%.2f",
            facility_code,
            year,
            month,
            opening_volume_m3,
            closing_volume_m3,
        )

        # Return the saved record
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, facility_code, year, month, opening_volume_m3, closing_volume_m3, data_source, notes, created_at, updated_at "
                "FROM storage_history WHERE facility_code = ? AND year = ? AND month = ?",
                (facility_code, year, month),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Storage history record not found after save")
            return StorageHistoryRecord(**row)
        finally:
            conn.close()

    @staticmethod
    def _previous_period(year: int, month: int) -> Tuple[int, int]:
        if month == 1:
            return 12, year - 1
        return month - 1, year

    def _should_update_current_volume(self, conn, year: int, month: int) -> bool:
        """Return True when this save is latest/newer than existing history."""
        cursor = conn.execute(
            "SELECT year, month FROM storage_history ORDER BY year DESC, month DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            return True
        latest_year = int(row["year"])
        latest_month = int(row["month"])
        return (year, month) >= (latest_year, latest_month)
