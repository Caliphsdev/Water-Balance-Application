from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from services.license_service import LicenseStatus, _load_license_timing_from_config
from ui.main_window import MainWindow


def test_runtime_interval_is_bounded(monkeypatch):
    class DummyCfg:
        def get(self, key, default=None):
            if key == "licensing.runtime_check_interval_seconds":
                return 999999
            return default

    monkeypatch.setattr("ui.main_window.ConfigManager", lambda: DummyCfg())
    assert MainWindow._resolve_runtime_license_interval_seconds() == 86400


def test_runtime_interval_uses_floor(monkeypatch):
    class DummyCfg:
        def get(self, key, default=None):
            if key == "licensing.runtime_check_interval_seconds":
                return 1
            return default

    monkeypatch.setattr("ui.main_window.ConfigManager", lambda: DummyCfg())
    assert MainWindow._resolve_runtime_license_interval_seconds() == 60


def test_offline_timing_fallback_is_production_safe(monkeypatch):
    class BrokenCfg:
        def get(self, key, default=None):
            raise RuntimeError("config unavailable")

    monkeypatch.setattr("services.license_service.ConfigManager", lambda: BrokenCfg())
    offline_days, refresh_days = _load_license_timing_from_config()
    assert offline_days >= 1.0
    assert refresh_days >= 0.0


def test_blocking_statuses_include_clock_and_system_unavailable():
    assert LicenseStatus(LicenseStatus.CLOCK_TAMPER).should_block is True
    assert LicenseStatus(LicenseStatus.SYSTEM_UNAVAILABLE).should_block is True
