# Licensing System - Developer Quick Reference

## Quick Links

| Document | Purpose |
|----------|---------|
| [LICENSING_SYSTEM_COMPLETE_STATUS.md](LICENSING_SYSTEM_COMPLETE_STATUS.md) | Complete feature matrix & deployment readiness |
| [AUTO_RECOVERY_FIX_SUMMARY.md](AUTO_RECOVERY_FIX_SUMMARY.md) | Hardware matching fix & technical details |
| [AUTO_RECOVERY_FEATURE_VERIFICATION.md](AUTO_RECOVERY_FEATURE_VERIFICATION.md) | Test results & verification evidence |
| [docs/LICENSING_SYSTEM_COMPLETE_GUIDE.md](docs/LICENSING_SYSTEM_COMPLETE_GUIDE.md) | User-facing documentation |
| [docs/LICENSING_SECURITY_ARCHITECTURE.md](docs/LICENSING_SECURITY_ARCHITECTURE.md) | Security deep-dive for architects |

## Key Code Locations

### License Validation
```python
# Main entry point - called during app startup
from src.licensing.license_manager import LicenseManager
manager = LicenseManager()
is_valid, message, expiry_date = manager.validate_startup()
```

### Hardware Binding
```python
# Get current machine hardware (hashed)
from src.licensing.hardware_id import current_hardware_snapshot
hw = current_hardware_snapshot()  # Returns: {"mac": hash, "cpu": hash, "board": hash}

# Compare hardware with fuzzy matching
from src.licensing.hardware_id import fuzzy_match
is_match, matches = fuzzy_match(stored_hw, current_hw, threshold=2)
```

### Google Sheets Integration
```python
# Query all licenses from Google Sheets
from src.licensing.license_client import LicenseClient
client = LicenseClient()
all_licenses = client.get_all_licenses()  # Returns list of license dicts

# Validate specific license
is_valid, msg = client.validate("ABC-123-XYZ")
```

### Auto-Recovery
```python
# Automatically restore license from Google Sheets for same hardware
# Called automatically during startup if no local license found
# No manual action needed - handles reinstall scenario transparently
```

### Manual Verification
```python
# User clicks "Verify License" button
from src.licensing.license_manager import LicenseManager
manager = LicenseManager()
result = manager.validate_manual()  # Returns (success, message, expiry)

# Check remaining verifications for the day
status = manager.get_verification_status()  # Returns (remaining_count, resets_at)
```

## Hardware Field Mapping

**CRITICAL**: Hardware components must map consistently across all layers:

```python
# Local detection (src/licensing/hardware_id.py)
collect_components() → {
    "mac": <network adapter MAC hash>,
    "cpu": <CPU serial number hash>,
    "board": <motherboard UUID hash>
}

# Remote storage (Google Sheets)
hw_component_1 → "mac" (network adapter)
hw_component_2 → "cpu" (CPU ID)
hw_component_3 → "board" (motherboard/UUID)

# When loading from remote (src/licensing/license_client.py)
hw_components = {
    "mac": hw_component_1,
    "cpu": hw_component_2,
    "board": hw_component_3
}
```

⚠️ **If you change field names, update ALL THREE locations**

## Database Schema

```sql
-- Main license record
CREATE TABLE license_info (
    license_id INTEGER PRIMARY KEY,
    license_key TEXT UNIQUE NOT NULL,
    license_status TEXT DEFAULT 'pending',  -- 'active', 'revoked', 'expired'
    license_tier TEXT,
    licensee_name TEXT,
    licensee_email TEXT,
    hardware_components_json TEXT,          -- JSON: {"mac": hash, "cpu": hash, "board": hash}
    hardware_match_threshold INTEGER,       -- Number of matching components needed
    expiry_date DATE,
    max_users INTEGER,
    transfer_count INTEGER,
    manual_verification_count INTEGER,
    manual_verification_reset_at TIMESTAMP, -- Midnight SAST
    -- ... other fields
);

-- Audit trails
CREATE TABLE license_validation_log (...)
CREATE TABLE license_audit_log (...)
```

## Testing Auto-Recovery

```bash
# Simulate reinstall and recovery
python test_auto_recovery.py

# Expected output:
# [STEP 1] Current machine hardware: ...
# [STEP 2] Clearing local license...
# [STEP 3] Attempting auto-recovery...
# [STEP 4] Verifying license restoration...
# [STEP 5] Testing startup validation...
# SUCCESS - AUTO-RECOVERY FULLY FUNCTIONAL
```

## Common Tasks

### Add a New License
1. Go to Google Sheets (shared link provided)
2. Add row with: license_key, licensee_name, licensee_email, status='active'
3. Set hw_component_1, hw_component_2, hw_component_3 if available
4. License automatically available on next app run

### Revoke a License
1. Open Google Sheets
2. Change status to 'revoked'
3. License will be detected as revoked at next app startup or background check
4. User immediately blocked from access

### Test Transfer Process
1. `src/ui/main_window.py` → "Transfer License" button
2. Opens transfer dialog with email verification
3. Sends verification email to new licensee
4. License migrated after verification

### Monitor Audit Trail
```sql
-- View validation history
SELECT * FROM license_validation_log ORDER BY validation_timestamp DESC LIMIT 10;

-- View security events
SELECT * FROM license_audit_log ORDER BY audit_timestamp DESC LIMIT 10;

-- View specific license history
SELECT * FROM license_validation_log 
WHERE license_id = (SELECT license_id FROM license_info WHERE license_key = 'ABC-123-XYZ')
ORDER BY validation_timestamp DESC;
```

## Logging

All licensing operations logged via `src/utils/app_logger.py`:

```
# Startup validation
16:39:14 | INFO | No local license found - attempting auto-recovery...
16:39:15 | INFO | AUTO-RECOVERY SUCCESSFUL

# Manual verification
16:41:15 | INFO | Manual license verification initiated by user
16:41:15 | INFO | Manual verification count: 1/3 (resets at midnight SAST)

# Security events
16:41:20 | WARNING | Strict mode: License has no hardware binding (anti-piracy)

# Revocation
16:41:28 | CRITICAL | REVOCATION DETECTED: License revoked by administrator
```

## Troubleshooting Checklist

- [ ] Is Google Sheets accessible? (Check network)
- [ ] Is hardware hashing working? (Run `current_hardware_snapshot()`)
- [ ] Are field names consistent? (Check license_client.py line for "mac"/"cpu"/"board")
- [ ] Is SQLite database intact? (Run `sqlite3 data/water_balance.db ".tables"`)
- [ ] Is verification limit reset at midnight SAST? (Check `pytz.timezone('Africa/Johannesburg')`)
- [ ] Are email notifications sending? (Check SMTP config in license_manager.py)
- [ ] Is background thread running? (Check logs for "Background license check thread started")

## Performance Notes

- Hardware hashing: ~50ms (one-time)
- Startup validation: ~500ms (online), <100ms (offline with cache)
- Background check: Async in daemon thread (no UI impact)
- Database queries: Typically <10ms with caching
- Google Sheets query: ~1-2 seconds (network dependent)

## Security Reminders

1. **Never log raw hardware values** - Always use hashed versions
2. **Validate ALL input** from Google Sheets - Don't trust format
3. **Clear sensitive data** - Remove license keys from memory after use
4. **Use HTTPS only** - For any future API calls
5. **Audit access** - Monitor who accesses Google Sheets license list
6. **Update regularly** - Check for security vulnerabilities in dependencies

## Next Steps for Enhancement

1. Add two-factor authentication for transfers
2. Implement geolocation-based anomaly detection
3. Create admin dashboard for license management
4. Add automated testing in CI/CD pipeline
5. Set up monitoring for suspicious activity

---

**Last Updated**: 2024  
**Status**: Production Ready  
**Maintainer**: DevOps Team
