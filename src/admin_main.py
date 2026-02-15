"""
PySide6 License Manager - Entry Point

Launches the standalone admin GUI for managing Supabase licenses.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import shutil
import yaml

from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle
from PySide6.QtGui import QIcon

from ui.admin.license_manager_window import LicenseManagerWindow
from core.config_manager import get_resource_path


class _FastTooltipStyle(QProxyStyle):
    """Reduce tooltip wake-up delay for faster hover feedback."""

    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay:
            return 120
        if hint == QStyle.StyleHint.SH_ToolTip_FallAsleepDelay:
            return 2000
        return super().styleHint(hint, option, widget, returnData)


def _apply_fast_tooltips(app: QApplication) -> None:
    try:
        app.setStyle(_FastTooltipStyle(app.style()))
    except Exception:
        pass


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


def _read_config_version(config_path: Path) -> str | None:
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return data.get("app", {}).get("version")
    except Exception:
        return None


def _ensure_user_data(user_base: Path, packaged_base: Path) -> None:
    (user_base / "config").mkdir(parents=True, exist_ok=True)
    (user_base / "data").mkdir(parents=True, exist_ok=True)
    (user_base / "logs").mkdir(parents=True, exist_ok=True)

    user_cfg = user_base / "config" / "app_config.yaml"
    cfg_src = packaged_base / "config" / "app_config.yaml"
    if cfg_src.exists():
        if not user_cfg.exists():
            shutil.copy2(cfg_src, user_cfg)
        else:
            packaged_version = _read_config_version(cfg_src)
            user_version = _read_config_version(user_cfg)
            if packaged_version and user_version and packaged_version != user_version:
                backup = user_cfg.with_suffix(".yaml.bak")
                shutil.copy2(user_cfg, backup)
                shutil.copy2(cfg_src, user_cfg)


def main() -> None:
    user_base = _get_user_base()
    os.environ["WATERBALANCE_USER_DIR"] = str(user_base)

    if getattr(sys, "frozen", False):
        _ensure_user_data(user_base, _find_packaged_base())

    app = QApplication(sys.argv)
    app.setApplicationName("Water Balance License Manager")
    app.setOrganizationName("Two Rivers Platinum")
    _apply_fast_tooltips(app)
    icon_path = get_resource_path("src/ui/resources/icons/Water Balance.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = LicenseManagerWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
