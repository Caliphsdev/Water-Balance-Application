"""
Column alias resolver for renamed/non-standard Excel headers.

Maps renamed column names (e.g., "OLDTSF_to_TRTDs(return)") to their
corresponding diagram flow targets (e.g., "oldtsf_trtd__TO__oldtsf_old_tsf").

Used by auto-map when direct column matching fails.
"""

import sys
from pathlib import Path
import json
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.app_logger import logger
from utils.config_manager import config


_ALIASES_DEFAULT_PATH = Path("data/column_aliases.json")


class _ColumnAliasResolver:
    """Singleton resolver for column aliases."""

    def __init__(self) -> None:
        # Resolve path from config or use default
        custom_path = config.get("data_sources.column_aliases_path", None)
        if custom_path:
            self._path = Path(custom_path)
        else:
            self._path = _ALIASES_DEFAULT_PATH

        self._aliases: Dict[str, str] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load aliases from file if not already loaded."""
        if self._loaded:
            return

        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._aliases = data.get("aliases", {})
                logger.info(f"ColumnAliasResolver loaded {len(self._aliases)} aliases from {self._path}")
            else:
                logger.debug(f"ColumnAliasResolver: no aliases file at {self._path}")
                self._aliases = {}
            self._loaded = True
        except Exception as ex:
            logger.error(f"Failed to load column aliases: {ex}", exc_info=True)
            self._aliases = {}
            self._loaded = True

    def resolve(self, column_name: str) -> Optional[str]:
        """
        Resolve a column name to its target flow.

        Args:
            column_name: The Excel column header (possibly renamed)

        Returns:
            The target flow identifier (from__TO__to), or None if no alias found
        """
        self._ensure_loaded()
        return self._aliases.get(column_name)

    def add_alias(self, column_name: str, target_flow: str) -> None:
        """
        Register or update an alias for a renamed column.

        Args:
            column_name: The Excel column header
            target_flow: The target flow identifier (from__TO__to)
        """
        self._ensure_loaded()
        self._aliases[column_name] = target_flow
        self._save()

    def remove_alias(self, column_name: str) -> None:
        """Remove an alias."""
        self._ensure_loaded()
        if column_name in self._aliases:
            del self._aliases[column_name]
            self._save()

    def all_aliases(self) -> Dict[str, str]:
        """Return all registered aliases."""
        self._ensure_loaded()
        return dict(self._aliases)

    def _save(self) -> None:
        """Persist aliases to file."""
        try:
            data = {
                "comment": "Column aliases for renamed/non-standard Excel headers",
                "aliases": self._aliases,
                "metadata": {
                    "version": 1,
                    "description": "Maps renamed column headers to diagram flow targets"
                }
            }
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info("ColumnAliasResolver saved")
        except Exception:
            logger.error("Failed to save column aliases", exc_info=True)


_resolver_instance: Optional[_ColumnAliasResolver] = None


def get_column_alias_resolver() -> _ColumnAliasResolver:
    """Get or create the singleton alias resolver."""
    global _resolver_instance
    if _resolver_instance is None:
        try:
            config.load_config()
        except Exception:
            pass
        _resolver_instance = _ColumnAliasResolver()
    return _resolver_instance


def reset_column_alias_resolver() -> None:
    """Reset the singleton (call when aliases file is updated externally)."""
    global _resolver_instance
    _resolver_instance = None
