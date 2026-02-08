"""
PySide6 License Manager - Entry Point

Launches the standalone admin GUI for managing Supabase licenses.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import shutil

from PySide6.QtWidgets import QApplication

from ui.admin.license_manager_window import LicenseManagerWindow


def _get_user_base() -> Path:
    if getattr(sys, "frozen", False):
        local_appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(local_appdata) if local_appdata else (Path.home() / "AppData" / "Local")
        return base / "WaterBalanceDashboard"
    return Path(__file__).parent.parent


def _find_packaged_base() -> Path:
    if getattr(sys, "frozen", False):
        exe_base = Path(sys.executable).parent
        internal = exe_base / "_internal"
        return internal if internal.exists() else exe_base
    return Path(__file__).parent.parent


def _ensure_user_data(user_base: Path, packaged_base: Path) -> None:
    (user_base / "config").mkdir(parents=True, exist_ok=True)
    (user_base / "data").mkdir(parents=True, exist_ok=True)
    (user_base / "logs").mkdir(parents=True, exist_ok=True)

    user_cfg = user_base / "config" / "app_config.yaml"
    if not user_cfg.exists():
        for cfg_src in [packaged_base / "config" / "app_config.yaml"]:
            if cfg_src.exists():
                shutil.copy2(cfg_src, user_cfg)
                break


def main() -> None:
    user_base = _get_user_base()
    os.environ["WATERBALANCE_USER_DIR"] = str(user_base)

    if getattr(sys, "frozen", False):
        _ensure_user_data(user_base, _find_packaged_base())

    app = QApplication(sys.argv)
    app.setApplicationName("Water Balance License Manager")
    app.setOrganizationName("Two Rivers Platinum")

    window = LicenseManagerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
