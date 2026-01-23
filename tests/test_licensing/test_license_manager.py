"""Core license manager tests.

Tests basic functionality:
- License activation
- Hardware matching (weighted similarity)
- Online/offline validation
- Manual verification limits
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


class TestHardwareMatching:
    """Test hardware similarity matching logic."""
    
    def test_identical_hardware_matches(
        self, mock_db, mock_license_client, create_license_record,
        sample_hardware, monkeypatch
    ):
        """Test that identical hardware matches 100%.
        
        Scenario: Same MAC, CPU, motherboard.
        Expected: Similarity = 1.0 (100%), match = True.
        """
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        monkeypatch.setattr("licensing.license_manager.current_hardware_snapshot", lambda: sample_hardware)
        
        manager = LicenseManager()
        
        # Test similarity calculation
        is_match, similarity = manager._is_hardware_match(sample_hardware, sample_hardware)
        
        assert is_match is True
        assert similarity == 1.0
    
    def test_completely_different_hardware_fails(
        self, mock_db, mock_license_client, sample_hardware, different_hardware,
        monkeypatch
    ):
        """Test that completely different hardware fails matching.
        
        Scenario: All components different (MAC, CPU, motherboard).
        Expected: Similarity = 0.0 (0%), match = False.
        """
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        manager = LicenseManager()
        
        # Test similarity
        is_match, similarity = manager._is_hardware_match(sample_hardware, different_hardware)
        
        assert is_match is False
        assert similarity == 0.0
    
    def test_partial_hardware_change_matches_above_threshold(
        self, mock_db, mock_license_client, sample_hardware, 
        partially_changed_hardware, monkeypatch
    ):
        """Test that partial hardware change still matches.
        
        Scenario: Same CPU (30%) + same motherboard (40%) = 70% similarity.
        Expected: Similarity = 0.70, match = True (above 60% threshold).
        """
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        manager = LicenseManager()
        
        # Test similarity (MAC changed, CPU and board same)
        is_match, similarity = manager._is_hardware_match(
            sample_hardware, partially_changed_hardware
        )
        
        assert is_match is True
        assert similarity == 0.70  # CPU 30% + board 40%
    
    def test_only_motherboard_match_is_not_enough(
        self, mock_db, mock_license_client, sample_hardware, monkeypatch
    ):
        """Test that only motherboard match (40%) fails threshold.
        
        Scenario: Same motherboard, different CPU and MAC.
        Expected: Similarity = 0.40, match = False (below 60%).
        """
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        only_board_matches = {
            "mac": "AA:BB:CC:DD:EE:FF",  # Different
            "cpu": "DEADBEEF12345678",   # Different
            "board": sample_hardware["board"],  # Same
        }
        
        manager = LicenseManager()
        is_match, similarity = manager._is_hardware_match(sample_hardware, only_board_matches)
        
        assert is_match is False
        assert similarity == 0.40  # Only board 40%


class TestLicenseActivation:
    """Test license activation workflow."""
    
    def test_successful_activation_saves_license(
        self, mock_db, mock_license_client, sample_hardware, monkeypatch
    ):
        """Test that successful activation saves license to database.
        
        Scenario: Valid license key, online validation succeeds.
        Expected: License saved with hardware binding.
        """
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        monkeypatch.setattr("licensing.license_manager.current_hardware_snapshot", lambda: sample_hardware)
        
        # Mock successful validation
        mock_license_client.validate.return_value = {
            "valid": True,
            "status": "active",
            "message": "License valid",
            "expiry_date": (dt.date.today() + dt.timedelta(days=365)).isoformat(),
            "has_hw_binding": True,
        }
        
        manager = LicenseManager()
        success, message = manager.activate(
            "TEST-LICENSE-KEY",
            licensee_name="Test User",
            licensee_email="test@example.com"
        )
        
        # Should succeed
        assert success is True
        assert "activated" in message.lower()
        
        # Check license saved to DB (activation adds new record)
        assert len(mock_db._stored_records) >= 1
        # Get the last inserted record (activation creates new one)
        record = mock_db._stored_records[-1]
        assert record["license_key"] == "TEST-LICENSE-KEY"
        assert record["licensee_name"] == "Test User"
        assert record["license_status"] == "active"
    
    def test_activation_with_invalid_key_fails(
        self, mock_db, mock_license_client, monkeypatch
    ):
        """Test that invalid license key fails activation.
        
        Scenario: License key not found on server.
        Expected: Activation fails with error message.
        """
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        # Mock validation failure
        mock_license_client.validate.return_value = {
            "valid": False,
            "status": "invalid",
            "message": "License key not found",
            "has_hw_binding": False,
        }
        
        manager = LicenseManager()
        success, message = manager.activate("INVALID-KEY")
        
        # Should fail
        assert success is False
        assert "invalid" in message.lower() or "not found" in message.lower()


class TestManualVerification:
    """Test manual 'Verify License Now' functionality."""
    
    def test_manual_verification_increments_counter(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that manual verification increments attempt counter.
        
        Scenario: User clicks 'Verify License Now' button.
        Expected: Counter incremented from 0 to 1.
        """
        # Setup: Fresh license with 0 attempts
        record = create_license_record(manual_verification_count=0)
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_manual()
        
        # Check counter incremented
        updated_record = mock_db._stored_records[-1]
        assert updated_record["manual_verification_count"] == 1
    
    def test_manual_verification_limit_3_per_day(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test that manual verification is limited to 3 attempts per day.
        
        Scenario: User already verified 3 times today.
        Expected: 4th attempt blocked with error message.
        """
        # Setup: License with 3 attempts already used
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        
        # Set reset time to tomorrow midnight SAST
        import pytz
        real_combine = dt.datetime.combine
        sast = pytz.timezone('Africa/Johannesburg')
        tomorrow = now.date() + dt.timedelta(days=1)
        reset_at = sast.localize(real_combine(tomorrow, dt.time.min))
        
        record = create_license_record(
            manual_verification_count=3,  # Already used 3/3
            manual_verification_reset_at=reset_at.isoformat(),
        )
        mock_db._stored_records.clear()  # Clear list (don't create new one)
        mock_db._stored_records.append(record)  # Append to same list
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_manual()
        
        # Should block (limit reached)
        assert valid is False
        assert "limit reached" in message.lower()
        assert "3/day" in message.lower()
    
    def test_manual_verification_counter_resets_at_midnight_sast(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test that verification counter resets at midnight SAST.
        
        Scenario: User used 3 attempts yesterday, tries again today.
        Expected: Counter reset, verification allowed.
        """
        # Setup: License with 3 attempts, reset time was yesterday
        import pytz
        real_combine = dt.datetime.combine
        sast = pytz.timezone('Africa/Johannesburg')
        
        # Current time: Jan 23, 2026 01:00 UTC (naive)
        # Will be localized to SAST by create_datetime_mock
        now_naive = dt.datetime(2026, 1, 23, 1, 0, 0)
        
        # Reset time was yesterday midnight SAST (Jan 23 00:00 SAST)
        reset_at = sast.localize(real_combine(dt.date(2026, 1, 23), dt.time.min))
        
        record = create_license_record(
            manual_verification_count=3,  # Used all attempts yesterday
            manual_verification_reset_at=reset_at.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now_naive)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_manual()
        
        # Should allow (counter reset)
        assert valid is True
        
        # Counter should be reset to 1
        updated_record = mock_db._stored_records[-1]
        assert updated_record["manual_verification_count"] == 1


class TestStatusReporting:
    """Test license status display for UI."""
    
    def test_status_summary_shows_online_mode(
        self, mock_db, create_license_record, monkeypatch
    ):
        """Test that status shows 'Online' after successful validation."""
        # Setup: License with successful validation flag
        record = create_license_record(validation_succeeded=True)
        mock_db._stored_records.append(record)
        
        from licensing.license_manager import LicenseClient
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: LicenseClient)
        
        manager = LicenseManager()
        status = manager.status_summary()
        
        assert "online" in status.lower()
    
    def test_status_summary_shows_offline_with_days_left(
        self, mock_db, create_license_record, monkeypatch, create_datetime_mock
    ):
        """Test that status shows offline mode with days remaining."""
        # Setup: License in offline mode with 5 days grace
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=5)
        
        record = create_license_record(
            validation_succeeded=False,  # Offline mode
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        from licensing.license_manager import LicenseClient
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: LicenseClient)
        
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            status = manager.status_summary()
        
        assert "offline" in status.lower()
        assert "5d" in status or "5 d" in status.lower()
