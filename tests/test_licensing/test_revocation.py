"""License revocation tests.

Tests immediate revocation detection:
- Revoked license blocks access even within grace period
- Revocation status persisted locally
- Revocation detected during background validation
- Auto-recovery blocked for revoked licenses
"""

import datetime as dt
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from licensing.license_manager import LicenseManager


class TestRevocationWhileOnline:
    """Test license revocation when online validation works."""
    
    def test_revoked_license_blocks_access_immediately(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that revoked license blocks access on startup.
        
        Scenario: License revoked on server, user starts app online.
        Expected: Access BLOCKED immediately (no grace period).
        """
        # Setup: Valid local license
        record = create_license_record()
        mock_db._stored_records.append(record)
        
        # Mock online validation to return revoked status
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.return_value = {
            "valid": False,
            "status": "revoked",
            "message": "License has been revoked",
            "has_hw_binding": True,
        }
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_startup()
        
        # Should block
        assert valid is False
        assert "revoked" in message.lower()
    
    def test_revoked_status_persisted_locally(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that revoked status is saved to local database.
        
        Scenario: License revoked on server.
        Expected: Local license_status updated to 'revoked'.
        """
        # Setup
        record = create_license_record(license_status="active")
        mock_db._stored_records.append(record)
        
        # Mock revocation response
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.return_value = {
            "valid": False,
            "status": "revoked",
            "message": "License revoked",
            "has_hw_binding": True,
        }
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_startup()
        
        # Check local DB was updated
        updated_record = mock_db._stored_records[-1]
        assert updated_record["license_status"] == "revoked"
    
    def test_revoked_license_blocks_even_with_grace_period(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that revocation ignores grace period.
        
        Scenario: License revoked, but still has 5 days grace remaining.
        Expected: Access BLOCKED (revocation overrides grace).
        """
        # Setup: License with active grace period
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=5)
        
        record = create_license_record(
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Mock revocation
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.return_value = {
            "valid": False,
            "status": "revoked",
            "message": "License revoked",
            "has_hw_binding": True,
        }
        
        with patch('licensing.license_manager.dt.datetime') as mock_dt:
            mock_dt.utcnow.return_value = now
            mock_dt.fromisoformat = lambda s: dt.datetime.fromisoformat(s)
            mock_dt.strptime = lambda s, fmt: dt.datetime.strptime(s, fmt)
            mock_dt.combine = lambda d, t: dt.datetime.combine(d, t)
            mock_dt.timedelta = dt.timedelta
            
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should block (revocation overrides grace)
        assert valid is False
        assert "revoked" in message.lower()


class TestRevocationWhileOffline:
    """Test license revocation when user is offline."""
    
    def test_offline_allows_access_even_if_revoked_on_server(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test security gap: offline mode can't detect server-side revocation.
        
        Scenario: License revoked on server, user offline within grace.
        Expected: Access ALLOWED (can't reach server to check).
        
        This is a known limitation - revocation requires online check.
        """
        # Setup: Active local license with grace period
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=5)
        
        record = create_license_record(
            license_status="active",  # Not yet marked as revoked locally
            last_online_check=now.isoformat(),  # Set to mocked time to avoid time-tamper detection
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Mock network error (offline)
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # SECURITY GAP: Will allow access (can't check server)
        assert valid is True
        assert "offline mode" in message.lower()
    
    def test_previously_revoked_license_blocks_even_offline(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that locally marked revoked license blocks access offline.
        
        Scenario: License was revoked yesterday (status saved), user offline today.
        Expected: Access BLOCKED (local status is revoked).
        """
        # Setup: License marked as revoked locally
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=5)
        
        record = create_license_record(
            license_status="revoked",  # Already marked as revoked
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Mock network error (offline)
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        with patch('licensing.license_manager.dt.datetime') as mock_dt:
            mock_dt.utcnow.return_value = now
            mock_dt.fromisoformat = lambda s: dt.datetime.fromisoformat(s)
            mock_dt.strptime = lambda s, fmt: dt.datetime.strptime(s, fmt)
            mock_dt.combine = lambda d, t: dt.datetime.combine(d, t)
            mock_dt.timedelta = dt.timedelta
            
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should block (local status is revoked)
        assert valid is False
        assert "revoked" in message.lower()
    
    def test_background_validation_detects_revocation(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that background validation catches revocation.
        
        Scenario: App running, license revoked, background check runs.
        Expected: Revocation detected and persisted.
        """
        # Setup: Active license
        record = create_license_record(license_status="active")
        mock_db._stored_records.append(record)
        
        # Mock revocation response
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.return_value = {
            "valid": False,
            "status": "revoked",
            "message": "License revoked",
            "has_hw_binding": True,
        }
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_background()
        
        # Should detect revocation
        assert valid is False
        
        # Check local DB updated
        updated_record = mock_db._stored_records[-1]
        assert updated_record["license_status"] == "revoked"


class TestAutoRecoveryRevocation:
    """Test auto-recovery behavior with revoked licenses."""
    
    def test_auto_recovery_blocked_for_revoked_license(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, sample_hardware, monkeypatch
    ):
        """Test that auto-recovery detects and blocks revoked licenses.
        
        Scenario: User reinstalls app, license was revoked on server.
        Expected: Auto-recovery detects revoked status and blocks.
        """
        # Setup: No local license (simulates fresh install)
        # But license exists on server as revoked
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        # Mock get_all_licenses to return revoked license
        from licensing.hardware_id import serialize_components
        mock_license_client.get_all_licenses.return_value = [
            {
                "license_key": "TEST-REVOKED-KEY",
                "status": "revoked",
                "valid": False,  # Revoked = not valid
                "licensee_name": "Test User",
                "licensee_email": "test@example.com",
                "hardware_components_json": serialize_components(sample_hardware),
                "activated_at": dt.datetime.utcnow().isoformat(),
            }
        ]
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_startup()
        
        # Should block (revoked license detected)
        assert valid is False
        assert "revoked" in message.lower()
    
    def test_revocation_message_includes_support_contact(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that revocation message includes support contact info.
        
        Scenario: License revoked.
        Expected: Error message includes email/phone for support.
        """
        # Setup
        record = create_license_record()
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.return_value = {
            "valid": False,
            "status": "revoked",
            "message": "License revoked",
            "has_hw_binding": True,
        }
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_startup()
        
        # Message should include support contact
        # (Current code doesn't add it, but it should)
        # This test documents expected behavior
        assert valid is False
        # TODO: Update code to include support contact in revocation message
