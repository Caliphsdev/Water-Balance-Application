"""
System Constants Repository (DATA ACCESS LAYER - CRUD OPERATIONS).

Provides SQLite access to system_constants and constants_audit tables.
Used by SystemConstantsService and Settings UI.
"""

import logging
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any

from database.db_manager import DatabaseManager
from models.system_constant import SystemConstant


logger = logging.getLogger(__name__)


class SystemConstantsRepository:
    """System constants repository (DATA ACCESS - CONSTANTS).

    Provides CRUD operations and history logging.
    Uses parameterized queries for safety.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize repository (CONSTRUCTOR).

        Args:
            db_manager: DatabaseManager instance (creates new if not provided)
        """
        self.db = db_manager or DatabaseManager()

    def list_constants(self) -> List[SystemConstant]:
        """List all constants sorted by category/key (READ - LIST CONSTANTS).

        Returns:
            List of SystemConstant models
        """
        rows = self.db.execute_query(
            """
            SELECT id, constant_key, constant_value, unit, category, description,
                   editable, min_value, max_value, created_at, updated_at
            FROM system_constants
            ORDER BY category, constant_key
            """
        )
        return [self._row_to_model(row) for row in rows]

    def get_by_key(self, constant_key: str) -> Optional[SystemConstant]:
        """Get constant by key (READ - BY KEY).

        Args:
            constant_key: Unique constant identifier

        Returns:
            SystemConstant if found, else None
        """
        row = self.db.execute_query(
            """
            SELECT id, constant_key, constant_value, unit, category, description,
                   editable, min_value, max_value, created_at, updated_at
            FROM system_constants
            WHERE constant_key = ?
            """,
            (constant_key,),
            fetch_one=True
        )
        return self._row_to_model(row) if row else None

    def create(self, constant: SystemConstant) -> SystemConstant:
        """Insert a new constant (CREATE - INSERT RECORD).

        Args:
            constant: SystemConstant model

        Returns:
            Created SystemConstant (with ID populated)

        Raises:
            sqlite3.IntegrityError: Duplicate key or constraint violation
        """
        self.db.execute_mutation(
            """
            INSERT INTO system_constants (
                constant_key, constant_value, unit, category, description,
                editable, min_value, max_value, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                constant.constant_key,
                constant.constant_value,
                constant.unit,
                constant.category,
                constant.description,
                constant.editable,
                constant.min_value,
                constant.max_value,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
            create_backup=False
        )

        created = self.get_by_key(constant.constant_key)
        if not created:
            raise sqlite3.Error("Failed to retrieve created system constant")
        return created

    def update(self, constant: SystemConstant, updated_by: str = "system") -> SystemConstant:
        """Update a constant and log history (UPDATE - MODIFY RECORD).

        Args:
            constant: SystemConstant model (must include constant_key)
            updated_by: Username for audit trail

        Returns:
            Updated SystemConstant
        """
        existing = self.get_by_key(constant.constant_key)
        if not existing:
            raise ValueError(f"Constant not found: {constant.constant_key}")

        self.db.execute_mutation(
            """
            UPDATE system_constants
            SET constant_value = ?, unit = ?, category = ?, description = ?,
                editable = ?, min_value = ?, max_value = ?, updated_at = ?
            WHERE constant_key = ?
            """,
            (
                constant.constant_value,
                constant.unit,
                constant.category,
                constant.description,
                constant.editable,
                constant.min_value,
                constant.max_value,
                datetime.now().isoformat(),
                constant.constant_key,
            ),
            create_backup=False
        )

        # Audit log (old vs new) for History tab.
        self._log_history(
            constant_key=constant.constant_key,
            old_value=existing.constant_value,
            new_value=constant.constant_value,
            updated_by=updated_by,
        )

        updated = self.get_by_key(constant.constant_key)
        if not updated:
            raise sqlite3.Error("Failed to retrieve updated system constant")
        return updated

    def delete(self, constant_key: str) -> int:
        """Delete constant by key (DELETE - REMOVE RECORD).

        Args:
            constant_key: Key to delete

        Returns:
            Number of rows affected
        """
        return self.db.execute_mutation(
            "DELETE FROM system_constants WHERE constant_key = ?",
            (constant_key,),
            create_backup=False
        )

    def list_categories(self) -> List[str]:
        """Get distinct categories (READ - CATEGORY LIST).

        Returns:
            List of category names (sorted)
        """
        rows = self.db.execute_query(
            """
            SELECT DISTINCT category
            FROM system_constants
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
            """
        )
        return [row["category"] for row in rows if row.get("category")]

    def list_history(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Get recent constant change history (READ - AUDIT LOG).

        Args:
            limit: Max number of audit rows

        Returns:
            List of audit rows as dicts
        """
        return self.db.execute_query(
            """
            SELECT changed_at, constant_key, old_value, new_value, updated_by
            FROM constants_audit
            ORDER BY changed_at DESC
            LIMIT ?
            """,
            (limit,)
        )

    def _log_history(
        self,
        constant_key: str,
        old_value: float,
        new_value: float,
        updated_by: str
    ) -> None:
        """Insert audit record for constant changes (INTERNAL - AUDIT LOG).

        Args:
            constant_key: Constant identifier
            old_value: Previous value
            new_value: Updated value
            updated_by: User or process name
        """
        try:
            self.db.execute_mutation(
                """
                INSERT INTO constants_audit (changed_at, constant_key, old_value, new_value, updated_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    constant_key,
                    old_value,
                    new_value,
                    updated_by,
                ),
                create_backup=False
            )
        except sqlite3.Error as e:
            logger.warning(f"Failed to log constant history: {e}")

    @staticmethod
    def _row_to_model(row: Dict[str, Any]) -> SystemConstant:
        """Convert DB row to SystemConstant model (INTERNAL - MAPPER).

        Args:
            row: Dict-like DB row

        Returns:
            SystemConstant model
        """
        return SystemConstant(**row)
