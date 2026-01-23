# Remaining Test Failures - Root Causes and Solutions

## Current Status
- **18 PASSED** ✅
- **17 FAILED** ❌

## Root Causes Identified

### 1. **Timezone Recursion (FIXED)**
- ✅ **Fix Applied**: Save `real_combine = dt.datetime.combine` BEFORE patching
- ✅ **Result**: No more "maximum recursion depth exceeded" in naive_combine

### 2. **Grace Period Tests Failing - datetime.fromisoformat() Recursion**
- **Issue**: Production code calls `dt.datetime.fromisoformat()` on grace period dates
- **Cause**: Mock still has recursion somewhere in fromisoformat
- **Solution**: Check production code for direct `dt.datetime()` constructor calls during grace period check

### 3. **Database Mock - manual_verification_count Not Persisting**
- **Issue**: Test sets `manual_verification_count=3`, production code reads `0`
- **Cause**: `mock_execute_update` not properly updating the field
- **Solution**: Enhance SQL parsing to handle all column names including `manual_verification_count`

### 4. **Database Mock - license_status Not Persisting**
- **Issue**: Revocation tests set `license_status="revoked"`, production code reads `"startup"`
- **Cause**: Same as #3 - SQL parsing not capturing the column
- **Solution**: Verify SET clause parsing handles all column names

### 5. **Status Summary - Expected "offline" but got "license active"**
- **Issue**: Test expects status to show "offline" mode
- **Possible Bug**: Production code `status_summary()` might not detect offline mode correctly
- **Solution**: Check production logic for status detection

### 6. **Activation Test - Wrong Record Index**
- **Issue**: `assert record["license_key"] == "TEST-LICENSE-KEY"` but `record = 1`
- **Cause**: Test reads wrong index or mock returns wrong value
- **Solution**: Use `stored_records[-1]` (most recent) instead of index 0

## Comprehensive Fix Strategy

### Phase 1: Fix All Datetime Mocking (HIGH PRIORITY)
```python
# Standard pattern for ALL datetime mocks:
real_combine = dt.datetime.combine  # BEFORE patch
real_fromisoformat = dt.datetime.fromisoformat  # BEFORE patch

with patch('licensing.license_manager.dt.datetime') as mock_dt:
    mock_dt.utcnow.return_value = test_time
    mock_dt.fromisoformat = lambda s: real_fromisoformat(s)
    mock_dt.strptime = lambda s, fmt: dt.datetime.strptime(s, fmt)
    mock_dt.combine = lambda d, t: real_combine(d, t)
    mock_dt.timedelta = dt.timedelta
    # NO side_effect - already removed
```

### Phase 2: Fix Database Mock SQL Parsing
**conftest.py** - Enhance `mock_execute_update`:
```python
# Current columns handled:
# - offline_grace_until, last_online_check, license_status, validation_succeeded
# MISSING: manual_verification_count, manual_verification_reset_at

# Add to SET clause parsing:
columns = ["offline_grace_until", "last_online_check", "license_status", 
           "manual_verification_count", "manual_verification_reset_at",
           "validation_succeeded", "transfer_count", "last_transfer_at"]
```

### Phase 3: Fix List Manipulation
**All tests** that use `mock_db._stored_records`:
```python
# ❌ WRONG:
mock_db._stored_records = [record]

# ✅ CORRECT:
mock_db._stored_records.clear()
mock_db._stored_records.append(record)
```

### Phase 4: Fix Timezone-Aware Mocks
**Manual verification tests**:
```python
# Mock dt.datetime.now() to return timezone-aware datetime
import pytz
sast = pytz.timezone('Africa/Johannesburg')
now_sast = sast.localize(now)
mock_dt.now.return_value = now_sast  # Not naive `now`
```

## Test-by-Test Action Plan

### Grace Period Tests (5 failures)
1. `test_within_grace_period_allows_access` - Fix datetime mocking
2. `test_grace_period_exactly_7_days_allows_access` - Fix datetime mocking
3. `test_grace_period_resets_on_successful_online_validation` - Fix grace_value isinstance check
4. `test_grace_period_status_reporting` - Fix status detection
5. `test_multiple_offline_startups_within_grace` - Fix datetime mocking

### Manual Verification Tests (3 failures)
1. `test_manual_verification_increments_counter` - Fix SQL parsing for counter column
2. `test_manual_verification_limit_3_per_day` - Fix timezone-aware now() + SQL parsing
3. `test_manual_verification_counter_resets_at_midnight_sast` - Same as above

### Revocation Tests (3 failures)
1. `test_revoked_status_persisted_locally` - Fix SQL parsing for license_status column
2. `test_offline_allows_access_even_if_revoked_on_server` - Fix datetime mocking
3. `test_background_validation_detects_revocation` - Fix SQL parsing for license_status

### Time Tampering Tests (4 failures)
1. `test_time_skew_tolerance_allows_minor_drift` - Fix datetime mocking
2. `test_time_moved_forward_is_allowed` - Fix datetime mocking
3. `test_no_last_check_time_allows_access` - Fix datetime mocking
4. `test_audit_log_entry_on_time_tamper` - Fix audit log mock

### Other Tests (2 failures)
1. `test_successful_activation_saves_license` - Use `stored_records[-1]` not `[0]`
2. `test_status_summary_shows_offline_with_days_left` - Check production code logic

## Next Steps
1. Apply comprehensive datetime mock pattern to ALL tests
2. Enhance mock_execute_update SQL parsing
3. Fix all list manipulations to use clear/append
4. Verify production code for potential bugs (status detection)
5. Run full test suite and verify 35/35 passing

## Files to Edit
- **tests/test_licensing/conftest.py** - Enhanced SQL parsing
- **tests/test_licensing/test_grace_period.py** - Datetime mocks, list manipulation
- **tests/test_licensing/test_license_manager.py** - Timezone-aware mocks, list manipulation, record index
- **tests/test_licensing/test_time_tampering.py** - Datetime mocks
- **tests/test_licensing/test_revocation.py** - Datetime mocks, list manipulation

## Production Code Bugs to Investigate
- **status_summary()** - Does it correctly detect offline mode when `last_online_check` is old?
- Any other logic issues revealed by tests

---
**Created**: 2026-01-22
**Status**: Analysis Complete, Ready for Batch Fixes
