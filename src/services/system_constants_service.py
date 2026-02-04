"""
System Constants Service (BUSINESS LOGIC & CACHING).

Provides high-level operations for reading and updating system constants.
Used by Settings UI and calculation services.
"""

import logging
from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from database.repositories.system_constants_repository import SystemConstantsRepository
from database.schema import DatabaseSchema
from models.system_constant import SystemConstant


logger = logging.getLogger(__name__)


class SystemConstantsService:
    """System constants service (BUSINESS LOGIC & CACHE).

    Responsibilities:
    - Load constants for UI and calculations
    - Validate updates against optional min/max bounds
    - Maintain in-memory cache to reduce DB reads
    - Provide audit history data
    """

    def __init__(
        self,
        repository: Optional[SystemConstantsRepository] = None,
        db_manager: Optional[DatabaseManager] = None,
    ):
        """Initialize service (CONSTRUCTOR).

        Args:
            repository: Repository instance (dependency injection)
            db_manager: Database manager (passed to repository if created here)
        """
        self.db_manager = db_manager or DatabaseManager()
        self.repository = repository or SystemConstantsRepository(self.db_manager)

        # Ensure constants tables exist for upgraded databases (non-destructive).
        schema = DatabaseSchema(self.db_manager.db_path)
        schema.ensure_system_constants_tables()

        self._constants_cache: Dict[str, SystemConstant] = {}
        self._cache_loaded = False

    def list_constants(self) -> List[SystemConstant]:
        """Return all constants (READ - LIST CONSTANTS).

        Returns:
            List of SystemConstant models
        """
        return self.repository.list_constants()

    def list_categories(self) -> List[str]:
        """Return distinct categories (READ - CATEGORY LIST).

        Returns:
            List of category strings
        """
        return self.repository.list_categories()

    def get_constant_map(self, refresh: bool = False) -> Dict[str, SystemConstant]:
        """Get constants map keyed by constant_key (CACHE ACCESS).

        Args:
            refresh: If True, reload cache from database

        Returns:
            Dict of constant_key -> SystemConstant
        """
        if refresh or not self._cache_loaded:
            constants = self.repository.list_constants()
            self._constants_cache = {c.constant_key: c for c in constants}
            self._cache_loaded = True
        return self._constants_cache

    def get_constant_value(self, key: str, default: float = 0.0) -> float:
        """Get numeric constant value by key (CALCULATION ACCESSOR).

        Args:
            key: Constant identifier
            default: Fallback value if constant missing

        Returns:
            Numeric value
        """
        constant = self.get_constant_map().get(key)
        return constant.constant_value if constant else default

    def create_constant(self, constant: SystemConstant) -> SystemConstant:
        """Create new constant with validation (CREATE - INSERT).

        Args:
            constant: SystemConstant model

        Returns:
            Created SystemConstant
        """
        self._validate_constant_bounds(constant)
        created = self.repository.create(constant)
        self.get_constant_map(refresh=True)
        return created

    def update_constant(self, constant: SystemConstant, updated_by: str = "system") -> SystemConstant:
        """Update existing constant with validation (UPDATE - MODIFY).

        Args:
            constant: SystemConstant model
            updated_by: Username for audit logging

        Returns:
            Updated SystemConstant
        """
        self._validate_constant_bounds(constant)
        updated = self.repository.update(constant, updated_by=updated_by)
        self.get_constant_map(refresh=True)
        return updated

    def delete_constant(self, constant_key: str) -> int:
        """Delete constant by key (DELETE - REMOVE).

        Args:
            constant_key: Key to delete

        Returns:
            Number of rows affected
        """
        count = self.repository.delete(constant_key)
        self.get_constant_map(refresh=True)
        return count

    def list_history(self, limit: int = 200) -> List[dict]:
        """Get constant update history (READ - AUDIT LOG).

        Args:
            limit: Max number of rows

        Returns:
            List of history dicts
        """
        return self.repository.list_history(limit=limit)

    def _validate_constant_bounds(self, constant: SystemConstant) -> None:
        """Validate constant value against optional bounds (INTERNAL - VALIDATION).

        Args:
            constant: SystemConstant model

        Raises:
            ValueError: If value outside min/max bounds
        """
        if constant.min_value is not None and constant.constant_value < constant.min_value:
            raise ValueError(
                f"Value for {constant.constant_key} below minimum ({constant.min_value})"
            )
        if constant.max_value is not None and constant.constant_value > constant.max_value:
            raise ValueError(
                f"Value for {constant.constant_key} above maximum ({constant.max_value})"
            )
