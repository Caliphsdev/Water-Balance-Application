import sys
from pathlib import Path
import json
import threading
from typing import Optional, Dict, Any

# Ensure src/ is importable per project conventions
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import config  # type: ignore
from utils.app_logger import logger  # type: ignore


_REGISTRY_DEFAULT_PATH = Path("data/excel_flow_links.json")


class _ExcelMappingRegistry:
    _lock = threading.RLock()

    def __init__(self) -> None:
        # Resolve path from config, with fallback to default
        custom_path = config.get("data_sources.column_flow_links_path", None)
        if custom_path:
            self._path = Path(custom_path)
        else:
            self._path = _REGISTRY_DEFAULT_PATH

        self._data: Dict[str, Any] = {"links": {}, "meta": {"version": 1}}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        with self._lock:
            if self._loaded:
                return
            try:
                if self._path.exists():
                    self._data = json.loads(self._path.read_text(encoding="utf-8"))
                    logger.info(f"ExcelMappingRegistry loaded from {self._path}")
                else:
                    # Ensure parent directory exists
                    self._path.parent.mkdir(parents=True, exist_ok=True)
                    self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
                    logger.info(f"ExcelMappingRegistry initialized at {self._path}")
                self._loaded = True
            except Exception as ex:
                logger.error("Failed to load ExcelMappingRegistry", exc_info=True)
                # Keep defaults in memory to avoid breaking callers
                self._loaded = True

    def _save(self) -> None:
        with self._lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
                logger.info("ExcelMappingRegistry saved")
            except Exception:
                logger.error("Failed to save ExcelMappingRegistry", exc_info=True)

    def link_column_to_flow(self, flow_id: str, sheet_name: str, column_name: str) -> None:
        """
        Persist a stable link from a logical flow to a specific Excel column.

        - flow_id: A stable identifier for the flow/edge in the diagram JSON
                   (e.g., an edge UUID or "UG2_NORTH::offices->ndcd")
        - sheet_name: The Excel sheet where the column resides
        - column_name: The exact column header as it appears in Excel
        """
        self._ensure_loaded()
        with self._lock:
            self._data.setdefault("links", {})[flow_id] = {
                "sheet": sheet_name,
                "column": column_name,
            }
            self._save()

    def remove_link(self, flow_id: str) -> None:
        self._ensure_loaded()
        with self._lock:
            if flow_id in self._data.get("links", {}):
                del self._data["links"][flow_id]
                self._save()

    def get_link(self, flow_id: str) -> Optional[Dict[str, str]]:
        """Return {"sheet": ..., "column": ...} if a link exists, else None."""
        self._ensure_loaded()
        return self._data.get("links", {}).get(flow_id)

    def resolve_mapping(self, flow_id: str, existing_mapping: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """
        Provide a final mapping to use for a flow:
        - If a registry link exists, prefer it
        - Else, use the existing edge mapping
        - Else, return None and allow caller to apply heuristics
        """
        link = self.get_link(flow_id)
        if link:
            return link
        return existing_mapping

    def all_links(self) -> Dict[str, Dict[str, str]]:
        self._ensure_loaded()
        return dict(self._data.get("links", {}))


_registry_instance: Optional[_ExcelMappingRegistry] = None


def get_excel_mapping_registry() -> _ExcelMappingRegistry:
    global _registry_instance
    if _registry_instance is None:
        # Ensure latest config from disk in case Settings changed path
        try:
            config.load_config()
        except Exception:
            # Non-fatal; proceed with in-memory config
            pass
        _registry_instance = _ExcelMappingRegistry()
    return _registry_instance


def reset_excel_mapping_registry() -> None:
    global _registry_instance
    _registry_instance = None
