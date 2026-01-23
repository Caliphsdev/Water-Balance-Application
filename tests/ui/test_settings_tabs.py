"""UI smoke tests for Settings module tabs.

These tests ensure the Settings notebook builds correctly and that data source
labels reflect config values (without exercising file dialogs).
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import tkinter as tk
import yaml

from ui.settings import SettingsModule
from utils.config_manager import config


def _restore_config(original_config: Dict[str, Any], original_path: Path | None, original_text: str | None) -> None:
    """Restore global config singleton to its prior state to avoid side effects."""
    # Direct assignment is safe in tests to avoid polluting global config state.
    config._config = deepcopy(original_config)  # noqa: SLF001 - test-only reset
    config._config_path = original_path  # noqa: SLF001 - test-only reset
    if original_path and original_text is not None:
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_text(original_text, encoding="utf-8")


def test_settings_tabs_render_without_error():
    """Settings notebook should create all expected tabs and expose notebook handle."""
    root = tk.Tk()
    root.withdraw()
    try:
        module = SettingsModule(root)
        module.load()
        root.update_idletasks()

        assert module.notebook is not None
        tab_titles = [
            module.notebook.tab(tab_id, option="text").strip()
            for tab_id in module.notebook.tabs()
        ]
        assert any("Constants" in title for title in tab_titles)
        assert any("Environmental" in title for title in tab_titles)
        assert any("Data Sources" in title for title in tab_titles)
        assert any("Backup" in title for title in tab_titles)
    finally:
        root.destroy()


def test_data_sources_labels_follow_config(tmp_path: Path):
    """Data source labels should reflect config paths loaded from disk."""
    original_config = deepcopy(config._config or {})  # noqa: SLF001 - test-only snapshot
    original_path = getattr(config, "_config_path", None)
    original_text = None
    if original_path and Path(original_path).exists():
        original_text = Path(original_path).read_text(encoding="utf-8")

    temp_cfg = tmp_path / "app_config.yaml"
    config_data: Dict[str, Any] = deepcopy(original_config)
    data_sources = config_data.setdefault("data_sources", {})
    data_sources["template_excel_path"] = "custom/flows.xlsx"
    data_sources["legacy_excel_path"] = "custom/meter.xlsx"

    temp_cfg.write_text(yaml.safe_dump(config_data), encoding="utf-8")

    try:
        config.load_config(str(temp_cfg))
        root = tk.Tk()
        root.withdraw()
        try:
            module = SettingsModule(root)
            module.load()
            root.update_idletasks()

            assert "custom/flows.xlsx" in module.template_path_label.cget("text")
            assert "custom/meter.xlsx" in module.legacy_path_label.cget("text")
        finally:
            root.destroy()
    finally:
        _restore_config(original_config, original_path, original_text)