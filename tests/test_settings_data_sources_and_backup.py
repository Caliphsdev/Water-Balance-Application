"""Settings-related integration tests (data sources + backup manager).

These tests avoid UI dependencies and focus on persistence and backup flows
used by the Settings dashboard tabs. They specifically cover data-source path
persistence (Meter Readings vs Flow Diagram Excel paths) and backup create/
restore logic.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import yaml

from src.utils.backup_manager import BackupManager
from src.utils.config_manager import config


def _restore_config(
    original_config: Dict[str, Any],
    original_path: Path | None,
    original_text: str | None,
) -> None:
    """Restore global config singleton to its prior state to avoid side effects."""
    # Reinstate in-memory config first so subsequent calls use original values.
    config._config = deepcopy(original_config)  # noqa: SLF001 - test-only state reset
    config._config_path = original_path  # noqa: SLF001 - test-only state reset
    if original_path and original_text is not None:
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_text(original_text, encoding="utf-8")
    elif original_path:
        # If no prior text, ensure file is removed to mirror previous absence.
        try:
            original_path.unlink()
        except FileNotFoundError:
            pass


def test_backup_manager_create_and_restore(tmp_path: Path) -> None:
    """BackupManager should create backups and restore the database file contents."""
    db_path = tmp_path / "water_balance.db"
    db_path.write_text("original-db", encoding="utf-8")
    backup_dir = tmp_path / "backups"

    manager = BackupManager(db_path=db_path, backup_dir=backup_dir)

    backup_file = manager.create_backup(label="integration")
    assert backup_file.exists()
    assert backup_file.parent == backup_dir

    # Mutate the live database to confirm restore overwrites it.
    db_path.write_text("mutated", encoding="utf-8")
    manager.restore_backup(backup_file)

    restored_text = db_path.read_text(encoding="utf-8")
    assert restored_text == "original-db"


def test_data_source_paths_persist_in_config(tmp_path: Path) -> None:
    """Data source path updates should persist via config.set and round-trip to disk."""
    # Snapshot current config so we can restore after the test.
    original_config = deepcopy(config._config)  # noqa: SLF001 - test-only state capture
    original_path = getattr(config, "_config_path", None)
    original_text = None
    if original_path and Path(original_path).exists():
        original_text = Path(original_path).read_text(encoding="utf-8")

    temp_cfg = tmp_path / "app_config.yaml"
    temp_cfg.write_text(
        yaml.safe_dump(
            {
                "data_sources": {
                    # Flow Diagram Excel path: feeds flow diagram dashboard.
                    "template_excel_path": "templates/Water_Balance_TimeSeries_Template.xlsx",
                    # Meter Readings Excel path: operational readings for balance engine.
                    "legacy_excel_path": "data/New Water Balance 20250930 Oct.xlsx",
                }
            }
        ),
        encoding="utf-8",
    )

    try:
        # Load isolated config and update both paths.
        config.load_config(str(temp_cfg))
        config.set("data_sources.template_excel_path", "custom/template.xlsx")
        config.set("data_sources.legacy_excel_path", "custom/legacy.xlsx")

        # Reload from disk to verify persistence.
        persisted = yaml.safe_load(temp_cfg.read_text(encoding="utf-8"))
        assert persisted["data_sources"]["template_excel_path"] == "custom/template.xlsx"
        assert persisted["data_sources"]["legacy_excel_path"] == "custom/legacy.xlsx"

        # Ensure getters return the updated values (used by settings tab status labels).
        assert config.get("data_sources.template_excel_path") == "custom/template.xlsx"
        assert config.get("data_sources.legacy_excel_path") == "custom/legacy.xlsx"
    finally:
        _restore_config(original_config, original_path, original_text)

        # Clean up temp config to avoid accidental reuse.
        if temp_cfg.exists():
            temp_cfg.unlink()
        # Restore original config file if we captured one but it was removed during the test.
        if original_path and original_text and not Path(original_path).exists():
            original_path.parent.mkdir(parents=True, exist_ok=True)
            original_path.write_text(original_text, encoding="utf-8")
