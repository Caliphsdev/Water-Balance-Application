"""Shared pytest fixtures for license testing.

Provides mock database, license records, and utility functions
for testing licensing scenarios without hitting real Google Sheets.
"""

import datetime as dt
import sys
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

# Add src to path so we can import from src
import os
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import after path modification
try:
    from licensing.hardware_id import serialize_components
except ImportError:
    # Fallback to explicit path
    import importlib.util
    hardware_id_path = src_path / "licensing" / "hardware_id.py"
    spec = importlib.util.spec_from_file_location("licensing.hardware_id", hardware_id_path)
    hardware_id = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hardware_id)
    serialize_components = hardware_id.serialize_components


@pytest.fixture
def mock_db(monkeypatch):
    """Mock database manager for license tests.
    
    Returns a mock with methods: execute_query, execute_update, execute_insert.
    Stores license records in memory for testing.
    """
    stored_records = []
    
    def mock_execute_query(sql, params=None):
        """Return stored license records."""
        sql_lower = sql.lower() if sql else ""
        if "license_info" in sql_lower and "order by license_id desc limit 1" in sql_lower:
            return [stored_records[-1]] if stored_records else []
        if "license_validation_log" in sql_lower or "license_audit_log" in sql_lower:
            return []
        return []
    
    def mock_execute_update(sql, params=None):
        """Update license record in memory (simulates real DB UPDATE)."""
        if stored_records and params:
            # Update last record with new values
            record = stored_records[-1]
            # Parse SQL to extract column names from SET clause
            # Example: "UPDATE license_info SET license_status = ?, ... WHERE license_id = ?"
            if "SET" in sql and "WHERE" in sql:
                set_clause = sql.split("SET")[1].split("WHERE")[0]
                # Extract column names (everything before '=')
                columns = [col.strip().split("=")[0].strip() for col in set_clause.split(",")]
                # Update only the columns specified in the SQL
                # Last param is WHERE condition (license_id), so exclude it
                for i, col in enumerate(columns):
                    if i < len(params) - 1:
                        record[col] = params[i]
            elif "SET" in sql:  # No WHERE clause (update all)
                set_clause = sql.split("SET")[1]
                columns = [col.strip().split("=")[0].strip() for col in set_clause.split(",")]
                for i, col in enumerate(columns):
                    if i < len(params):
                        record[col] = params[i]
            else:
                # Fallback: update common fields
                keys = [
                    "license_key", "license_status", "license_tier", "licensee_name",
                    "licensee_email", "hardware_components_json", "hardware_match_threshold",
                    "activated_at", "last_online_check", "offline_grace_until", "expiry_date",
                    "max_users", "transfer_count", "last_transfer_at", 
                    "manual_verification_count", "manual_verification_reset_at",
                    "validation_succeeded"
                ]
                for i, key in enumerate(keys):
                    if i < len(params) - 1:  # Skip last param (license_id)
                        if params[i] is not None:  # Only update non-None values
                            record[key] = params[i]
            return 1
        return 0
    
    def mock_execute_insert(sql, params=None):
        """Insert new license record."""
        if not params:
            return 0
        
        # Skip inserts to audit/log tables - don't store them in main stored_records
        sql_lower = sql.lower() if sql else ""
        if "license_validation_log" in sql_lower or "license_audit_log" in sql_lower:
            # These are logging tables, not license_info. Don't store them.
            return 1  # Return success ID
        
        # Handle license_info INSERT only
        if "license_info" not in sql_lower:
            return 0  # Unknown table
        
        keys = [
            "license_key", "license_status", "license_tier", "licensee_name",
            "licensee_email", "hardware_components_json", "hardware_match_threshold",
            "activated_at", "last_online_check", "offline_grace_until", "expiry_date",
            "max_users", "transfer_count", "last_transfer_at",
            "manual_verification_count", "manual_verification_reset_at",
            "validation_succeeded"
        ]
        record = {"license_id": len(stored_records) + 1}
        for i, key in enumerate(keys):
            if i < len(params):
                record[key] = params[i]
            else:
                record[key] = None
        stored_records.append(record)
        return record["license_id"]
    
    mock = MagicMock()
    mock.execute_query.side_effect = mock_execute_query
    mock.execute_update.side_effect = mock_execute_update
    mock.execute_insert.side_effect = mock_execute_insert
    mock._stored_records = stored_records  # For test inspection
    
    # Patch the db import in license_manager
    monkeypatch.setattr("licensing.license_manager.db", mock)
    
    return mock


@pytest.fixture
def sample_hardware():
    """Sample hardware snapshot for testing.
    
    Returns dict with keys: mac, cpu, board (motherboard UUID).
    """
    return {
        "mac": "00:11:22:33:44:55",
        "cpu": "BFEBFBFF000906E9",
        "board": "12345678-90AB-CDEF-1234-567890ABCDEF"
    }


@pytest.fixture
def different_hardware():
    """Different hardware snapshot (for mismatch testing).
    
    Completely different machine - all components changed.
    """
    return {
        "mac": "AA:BB:CC:DD:EE:FF",
        "cpu": "DEADBEEF12345678",
        "board": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"
    }


@pytest.fixture
def partially_changed_hardware():
    """Partially changed hardware (e.g., network card replaced).
    
    Same CPU and motherboard, different MAC address.
    Should still match with 60% threshold (CPU 30% + board 40% = 70%).
    """
    return {
        "mac": "AA:BB:CC:DD:EE:FF",  # Changed
        "cpu": "BFEBFBFF000906E9",  # Same
        "board": "12345678-90AB-CDEF-1234-567890ABCDEF"  # Same
    }


@pytest.fixture
def create_license_record(sample_hardware):
    """Factory function to create license records with custom values.
    
    Args:
        Overrides for default license record fields
    
    Returns:
        Function that creates license dict with defaults
    
    Example:
        record = create_license_record(license_status="revoked")
    """
    def _create(**overrides):
        now = dt.datetime.utcnow()
        grace_until = now + dt.timedelta(days=7)
        
        defaults = {
            "license_id": 1,
            "license_key": "TEST-LICENSE-KEY-12345",
            "license_status": "active",
            "license_tier": "standard",
            "licensee_name": "Test User",
            "licensee_email": "test@example.com",
            "hardware_components_json": serialize_components(sample_hardware),
            "hardware_match_threshold": "0.6",
            "activated_at": now.isoformat(),
            "last_online_check": now.isoformat(),
            "offline_grace_until": grace_until.isoformat(),
            "expiry_date": (dt.date.today() + dt.timedelta(days=365)).isoformat(),
            "max_users": 1,
            "transfer_count": 0,
            "last_transfer_at": None,
            "manual_verification_count": 0,
            "manual_verification_reset_at": None,
            "validation_succeeded": True,
        }
        defaults.update(overrides)
        return defaults
    
    return _create


@pytest.fixture
def create_datetime_mock():
    """Create properly configured datetime mock that preserves all real datetime methods.
    
    This ensures that when production code calls dt.datetime.fromisoformat(), strptime(),
    combine(), etc., they get REAL datetime objects back, not MagicMocks.
    
    Also handles now() and now(tz) calls for timezone-aware datetime operations.
    
    Usage in test:
        with patch('licensing.license_manager.dt.datetime', create_datetime_mock(now)) as mock_dt:
            manager = LicenseManager()
    
    Returns:
        Function that takes current_time and returns configured mock
    """
    def _create_mock(current_time):
        """Create mock with current_time as utcnow() return value."""
        mock = MagicMock()
        # Set utcnow to return our test time
        mock.utcnow.return_value = current_time
        
        # Handle now() and now(tz) calls
        # Production code calls dt.datetime.now(sast) to get timezone-aware datetime
        import pytz
        def mock_now(tz=None):
            if tz is None:
                return current_time
            # If timezone is requested, localize the current_time
            if hasattr(tz, 'localize'):
                # It's a pytz timezone object
                return tz.localize(current_time)
            else:
                # It's a tzinfo object, just replace tzinfo
                return current_time.replace(tzinfo=tz)
        mock.now.side_effect = mock_now
        
        # Preserve ALL real datetime class methods by wrapping them
        # These must return REAL datetime objects, not mocks
        # CRITICAL: Use lambda to bind to real datetime class
        real_datetime = dt.datetime
        mock.fromisoformat = lambda s: real_datetime.fromisoformat(s)
        mock.strptime = lambda s, fmt: real_datetime.strptime(s, fmt)
        mock.combine = lambda d, t: real_datetime.combine(d, t)
        mock.timedelta = dt.timedelta
        
        return mock
    
    return _create_mock


@pytest.fixture
def mock_license_client():
    """Mock LicenseClient for testing without hitting Google Sheets.
    
    Returns mock with methods: validate, get_all_licenses, update_activation_data.
    """
    mock = MagicMock()
    
    # Default validate response (success)
    mock.validate.return_value = {
        "valid": True,
        "status": "active",
        "message": "License valid",
        "expiry_date": (dt.date.today() + dt.timedelta(days=365)).isoformat(),
        "has_hw_binding": True,
    }
    
    # Default get_all_licenses response
    mock.get_all_licenses.return_value = []
    
    # Default update_activation_data response
    mock.update_activation_data.return_value = True
    
    return mock


@pytest.fixture
def freeze_time():
    """Utility to freeze datetime.utcnow() for testing time-based logic.
    
    Returns function that sets a fixed time for all datetime.utcnow() calls.
    
    Example:
        freeze_time(dt.datetime(2026, 1, 22, 12, 0, 0))
        # Now all datetime.utcnow() calls return 2026-01-22 12:00:00
    """
    patches = []
    
    def _freeze(frozen_time: dt.datetime):
        """Set fixed time for datetime.utcnow()."""
        # Patch datetime module in license_manager
        patcher = patch('licensing.license_manager.dt.datetime')
        mock_datetime = patcher.start()
        mock_datetime.utcnow.return_value = frozen_time
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        mock_datetime.strptime = dt.datetime.strptime
        mock_datetime.combine = dt.datetime.combine  # For SAST timezone fixes
        mock_datetime.date = dt.date  # Preserve date class
        mock_datetime.time = dt.time  # Preserve time class
        mock_datetime.timedelta = dt.timedelta  # Preserve timedelta
        # Make the mock callable to return datetime instances
        mock_datetime.side_effect = lambda *args, **kwargs: dt.datetime(*args, **kwargs)
        patches.append(patcher)
        return mock_datetime
    
    yield _freeze
    
    # Cleanup
    for p in patches:
        p.stop()


@pytest.fixture
def freeze_time_complete():
    """Complete datetime mock that preserves ALL datetime functionality.
    
    Use this for tests that need full datetime compatibility (constructors,
    fromisoformat, strptime, comparisons, etc.).
    
    Returns context manager that patches datetime and preserves real methods.
    """
    from unittest.mock import MagicMock
    
    class DatetimeMock:
        """Mock that delegates to real datetime but allows utcnow override."""
        
        def __init__(self, frozen_time=None):
            self.frozen_time = frozen_time
            # Preserve all real datetime class methods
            for attr in dir(dt.datetime):
                if not attr.startswith('_') and attr != 'utcnow':
                    setattr(self, attr, getattr(dt.datetime, attr))
        
        def utcnow(self):
            return self.frozen_time if self.frozen_time else dt.datetime.utcnow()
        
        def __call__(self, *args, **kwargs):
            """Allow datetime() constructor to work."""
            return dt.datetime(*args, **kwargs)
    
    def _context(frozen_time):
        """Return context manager for patching."""
        mock = DatetimeMock(frozen_time)
        return patch('licensing.license_manager.dt.datetime', mock)
    
    return _context


@pytest.fixture
def mock_current_hardware(monkeypatch, sample_hardware):
    """Mock current_hardware_snapshot to return fixed hardware.
    
    By default returns sample_hardware, can be overridden in tests.
    """
    def _set_hardware(hw: Dict):
        """Change the mocked hardware snapshot."""
        monkeypatch.setattr(
            "licensing.license_manager.current_hardware_snapshot",
            lambda: hw
        )
    
    # Default to sample_hardware
    _set_hardware(sample_hardware)
    
    # Return function to change hardware mid-test
    return _set_hardware
