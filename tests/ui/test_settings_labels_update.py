"""Settings UI status label updates.

Validates that changing Excel paths via the Settings UI
updates the displayed path labels and status indicators.
"""
import tkinter as tk
from pathlib import Path
from unittest.mock import patch

import pytest

from ui.settings import SettingsModule


@pytest.mark.ui
def test_template_and_legacy_status_labels_update(tmp_path: Path):
    """Changing paths via the UI updates labels and status indicators.

    Flow:
    - Create temp files to simulate valid Excel files
    - Open Settings UI and navigate Data Sources tab
    - Simulate file selection for template and legacy paths
    - Verify path labels reflect new paths and status shows "Found"
    """
    # Create temp files to simulate existing Excel files
    template_file = tmp_path / "Water_Balance_TimeSeries_Template.xlsx"
    legacy_file = tmp_path / "New Water Balance.xlsx"
    template_file.write_text("dummy")
    legacy_file.write_text("dummy")

    root = tk.Tk()
    try:
        module = SettingsModule(root)
        module.load()

        # Simulate selecting template excel via file dialog
        with patch("tkinter.filedialog.askopenfilename", return_value=str(template_file)), \
             patch("tkinter.messagebox.showinfo"):
            module._select_template_excel()

        # The implementation converts to relative path if inside cwd; accept either
        tpl_label_text = module.template_path_label.cget("text")
        assert Path(tpl_label_text).name == template_file.name
        assert module.template_status_label.cget("text").startswith("✓")

        # Simulate selecting legacy excel via file dialog
        with patch("tkinter.filedialog.askopenfilename", return_value=str(legacy_file)), \
             patch("tkinter.messagebox.showinfo"):
            module._select_legacy_excel()

        legacy_label_text = module.legacy_path_label.cget("text")
        assert Path(legacy_label_text).name == legacy_file.name
        assert module.legacy_status_label.cget("text").startswith("✓")
    finally:
        root.destroy()
