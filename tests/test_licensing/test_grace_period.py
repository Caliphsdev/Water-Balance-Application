"""Grace period expiration tests.

Tests the 7-day offline grace period logic:
- Grace period allows offline use
- Grace period expires after 7 days
- Grace period resets on successful online validation
- App blocks access when grace expired
"""

import datetime as dt
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from licensing.license_manager import LicenseManager


class TestGracePeriodExpiration:
    """Test grace period expiration after 7 days offline."""
    
    def test_within_grace_period_allows_access(
        self, mock_db, mock_license_client, create_license_record, 
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test that app allows access within 7-day grace period.
        
        Scenario: User goes offline on Day 1, app started on Day 5.
        Expected: Access allowed (5 < 7 days).
        """
        # Setup: Create license activated today with 7-day grace
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=7)
        
        record = create_license_record(
            last_online_check=now.isoformat(),
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Patch LicenseClient to raise network error (simulate offline)
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        # Test on Day 5 (within grace period)
        test_time = now + dt.timedelta(days=5)
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(test_time)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should allow access (offline grace)
        assert valid is True
        assert "offline mode" in message.lower()
    
    def test_grace_period_expired_blocks_access(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test that app blocks access after 7-day grace period expires.
        
        Scenario: User goes offline on Day 1, app started on Day 8.
        Expected: Access BLOCKED (8 > 7 days).
        """
        # Setup: Create license activated 8 days ago
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        activation_time = now - dt.timedelta(days=8)
        grace_until = activation_time + dt.timedelta(days=7)  # Expired 1 day ago
        
        record = create_license_record(
            last_online_check=activation_time.isoformat(),
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Patch LicenseClient to raise network error (simulate offline)
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        # Test now (grace expired)
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should block access (grace expired)
        assert valid is False
        assert "unable to verify license" in message.lower()
    
    def test_grace_period_exactly_7_days_allows_access(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test edge case: exactly 7 days is still within grace.
        
        Scenario: User goes offline on Day 1, app started exactly 7 days later.
        Expected: Access allowed (boundary condition).
        """
        # Setup: Create license with grace expiring in exactly 1 second
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(seconds=1)  # About to expire
        
        record = create_license_record(
            last_online_check=(now - dt.timedelta(days=7)).isoformat(),
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Patch LicenseClient to raise network error
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        # Test at exact grace period boundary
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should allow (still within grace by 1 second)
        assert valid is True
    
    def test_grace_period_resets_on_successful_online_validation(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test that successful online validation resets grace period to 7 days.
        
        Scenario: User offline for 6 days, reconnects, grace resets.
        Expected: New grace period starts from reconnection time.
        """
        # Setup: Create license with grace about to expire
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        old_grace = now + dt.timedelta(days=1)  # 1 day left
        
        record = create_license_record(
            last_online_check=(now - dt.timedelta(days=6)).isoformat(),
            offline_grace_until=old_grace.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        # Patch LicenseClient to succeed (online validation works)
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.return_value = {
            "valid": True,
            "status": "active",
            "message": "License valid",
            "expiry_date": (dt.date.today() + dt.timedelta(days=365)).isoformat(),
            "has_hw_binding": True,
        }
        
        # Test with online validation succeeding
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should succeed
        assert valid is True
        
        # Check that grace period was reset to 7 days from now
        updated_record = mock_db._stored_records[-1]
        grace_value = updated_record["offline_grace_until"]
        # Handle both string (ISO format) and datetime object
        if isinstance(grace_value, str):
            new_grace = dt.datetime.fromisoformat(grace_value)
        else:
            new_grace = grace_value
        expected_grace = now + dt.timedelta(days=7)
        
        # Allow 1 second tolerance for test execution time
        assert abs((new_grace - expected_grace).total_seconds()) < 1
    
    def test_no_grace_period_blocks_immediately(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that missing grace period blocks access on network failure.
        
        Scenario: License has no offline_grace_until field set.
        Expected: Access blocked immediately on network error.
        """
        # Setup: Create license WITHOUT grace period
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        
        record = create_license_record(
            offline_grace_until=None,  # No grace period!
        )
        mock_db._stored_records.append(record)
        
        # Patch LicenseClient to raise network error
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        # Test with network error
        with patch('licensing.license_manager.dt.datetime') as mock_dt:
            mock_dt.utcnow.return_value = now
            mock_dt.fromisoformat = lambda s: dt.datetime.fromisoformat(s)
            mock_dt.strptime = lambda s, fmt: dt.datetime.strptime(s, fmt)
            mock_dt.combine = lambda d, t: dt.datetime.combine(d, t)
            manager = LicenseManager()
            valid, message, expiry = manager.validate_startup()
        
        # Should block (no grace period available)
        assert valid is False
        assert "unable to verify license" in message.lower()
    
    def test_grace_period_status_reporting(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test is_offline_grace_active() reports correct status.
        
        Scenario: Check grace period status at different times.
        Expected: Correct active/inactive status and days remaining.
        """
        # Setup: Create license with 3 days grace remaining
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=3, hours=6)  # 3.25 days
        
        record = create_license_record(
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        
        # Test grace status
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)):
            manager = LicenseManager()
            active, days_left = manager.is_offline_grace_active()
        
        # Should report active with 4 days left (ceiling of 3.25)
        assert active is True
        assert days_left == 4


class TestGracePeriodEdgeCases:
    """Test edge cases and error conditions for grace period."""
    
    def test_corrupted_grace_date_blocks_access(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test that corrupted grace date is handled safely.
        
        Scenario: offline_grace_until field contains invalid ISO format.
        Expected: Access blocked (fail safe).
        """
        # Setup: Invalid grace date format
        record = create_license_record(
            offline_grace_until="INVALID-DATE-FORMAT",
        )
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        manager = LicenseManager()
        valid, message, expiry = manager.validate_startup()
        
        # Should block (can't parse grace date)
        assert valid is False
    
    def test_grace_period_zero_days_configured(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch
    ):
        """Test grace period disabled (0 days configured).
        
        Scenario: Config sets offline_grace_days to 0.
        Expected: No grace period, immediate block on network error.
        """
        # Setup: License with no grace period (0 days)
        record = create_license_record(
            offline_grace_until=None,
        )
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        # Mock config to return 0 grace days
        with patch('src.licensing.license_manager.config') as mock_config:
            mock_config.get.side_effect = lambda key, default: 0 if "grace" in key else default
            
            manager = LicenseManager()
            manager.offline_grace_days = 0  # Explicitly set to 0
            valid, message, expiry = manager.validate_startup()
        
        # Should block immediately (no grace)
        assert valid is False
    
    def test_multiple_offline_startups_within_grace(
        self, mock_db, mock_license_client, create_license_record,
        mock_current_hardware, monkeypatch, create_datetime_mock
    ):
        """Test multiple app startups within grace period.
        
        Scenario: User starts app 3 times over 5 days (all offline).
        Expected: All startups succeed, grace period not consumed faster.
        """
        # Setup: License with 7-day grace
        now = dt.datetime(2026, 1, 22, 12, 0, 0)
        grace_until = now + dt.timedelta(days=7)
        
        record = create_license_record(
            last_online_check=now.isoformat(),
            offline_grace_until=grace_until.isoformat(),
        )
        mock_db._stored_records.append(record)
        
        monkeypatch.setattr("licensing.license_manager.LicenseClient", lambda: mock_license_client)
        mock_license_client.validate.side_effect = ConnectionError("Network unavailable")
        
        # Test startup at Day 0, 2, 5
        test_days = [0, 2, 5]
        
        for day in test_days:
            test_time = now + dt.timedelta(days=day)
            with patch('licensing.license_manager.dt.datetime', create_datetime_mock(test_time)):
                manager = LicenseManager()
                valid, message, expiry = manager.validate_startup()
                
                # All should succeed
                assert valid is True, f"Startup on day {day} should succeed"
