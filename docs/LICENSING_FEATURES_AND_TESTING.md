# Licensing System - Complete Features & Testing Guide

**Version**: 1.0.0  
**Last Updated**: January 14, 2026  
**Mode**: **STRICT** (Anti-Piracy Enabled)

---

## 🔒 Licensing Architecture Overview

The Water Balance Application uses a **multi-layer hybrid licensing system** with:
1. **Online validation** (Google Sheets - immediate revocation detection)
2. **Local validation** (SQLite - offline support)
3. **Background checks** (hourly periodic validation)
4. **Hardware binding** (prevent hardware ID theft)
5. **Offline grace period** (7 days - work without internet)

---

## 📋 Core Features

### Feature 1: Startup Validation (Immediate Revocation Detection)
**Purpose**: Catch license revocation on first launch  
**Trigger**: App starts (`python src/main.py`)  
**Behavior**: 
- ✅ **Always** validates against Google Sheets (no interval waiting)
- ✅ Checks hardware binding (CPU + Motherboard must match)
- ✅ Verifies license key is marked `valid` in sheet
- ✅ **STRICT MODE**: Requires hardware data on remote sheet
- ✅ Falls back to 7-day offline grace if network fails

**Location**: [src/main.py](../src/main.py#L450) → `validate_startup()`

#### Test Case 1.1: Valid License at Startup
```bash
# Prerequisite: License is activated and valid in Google Sheets
.venv\Scripts\python src\main.py

# Expected Result:
# ✅ License valid - 351 days remaining
# App launches normally
# Status: PASS
```

#### Test Case 1.2: Revoked License Detection
```bash
# Step 1: Revoke license in Google Sheets
#   - Find license key row
#   - Set status = "revoked"
#   - Clear hardware info (triggers strict mode check)

# Step 2: Restart app
.venv\Scripts\python src\main.py

# Expected Result:
# ❌ License validation failed: License hardware binding missing
# License activation dialog appears
# User must re-activate
# Status: PASS
```

#### Test Case 1.3: Hardware Mismatch Detection
```bash
# Step 1: Activate license on Computer A
# Step 2: Move license to Computer B (different hardware)
# Step 3: Try to run app on Computer B without transferring

.venv\Scripts\python src\main.py

# Expected Result:
# ❌ Hardware mismatch: CPU changed, Motherboard changed
# Shows "Confirm Transfer" dialog
# Offers 3 total transfers (config: max_transfers: 3)
# Status: PASS
```

#### Test Case 1.4: Offline Grace Period
```bash
# Prerequisite: License last validated successfully
# Step 1: Disconnect internet / block license server
# Step 2: Restart app
.venv\Scripts\python src\main.py

# Expected Result:
# ✅ License valid (offline grace) - 351 days remaining
# App launches normally (grace period up to 7 days)
# Status: PASS

# Step 3: After 7 days of offline, restart again
# Expected Result:
# ❌ Network error: Cannot validate license
# App blocks access
# Status: PASS
```

---

### Feature 2: Background Periodic Validation
**Purpose**: Catch revocations while app is running  
**Trigger**: Every 1 hour (after app launches)  
**Behavior**:
- ✅ Runs in background daemon thread (doesn't block UI)
- ✅ Validates every 1 hour (configurable)
- ✅ Only shows dialog if status changed (valid → invalid)
- ✅ Non-intrusive warning (doesn't force exit)
- ✅ Gracefully handles network errors

**Location**: [src/main.py](../src/main.py#L468) → `_background_license_check_loop()`  
**Config**: `licensing.background_check_interval_seconds` (default: 3600 = 1 hour)

#### Test Case 2.1: Background Check Catches Revocation
```bash
# Step 1: Start app (license is valid)
.venv\Scripts\python src\main.py

# Step 2: Keep app running
# Step 3: Revoke license in Google Sheets (while app is open)
# Step 4: Wait 60+ seconds for background check to run

# Expected Result:
# ⚠️ License Status Alert dialog appears
# Message: "Your license status has changed: License was revoked"
# User can save work before exiting
# Status: PASS
```

#### Test Case 2.2: No False Alarms on Network Error
```bash
# Step 1: Start app
# Step 2: Disconnect internet while app is running
# Step 3: Wait 60+ seconds for background check

# Expected Result:
# ✅ NO dialog appears (gracefully handles network error)
# App continues working (within grace period)
# Status: PASS
```

#### Test Case 2.3: Re-validation After Transfer
```bash
# Step 1: Transfer license to new hardware (using dialog)
# Step 2: Wait 60+ seconds
# Step 3: Background thread validates against new hardware

# Expected Result:
# ✅ Background validation passes
# No warnings shown (license is valid on new hardware)
# Status: PASS
```

---

### Feature 3: Manual License Verification Button
**Purpose**: User can verify license on-demand  
**Trigger**: Click "🔐 Verify License" button in toolbar  
**Behavior**:
- ✅ Checks license immediately (no waiting)
- ✅ Shows result dialog (valid/invalid)
- ✅ Updates status indicator in toolbar
- ✅ Non-blocking (button grayed during check)
- ✅ Handles network errors gracefully

**Location**: [src/ui/main_window.py](../src/ui/main_window.py#L153) → `_verify_license_now()`

#### Test Case 3.1: Manual Verification - Valid License
```bash
# Step 1: App is running with valid license
# Step 2: Click "🔐 Verify License" button (top right toolbar)

# Expected Result:
# Button shows "⏳ Checking..." temporarily
# Dialog: "✅ Your license is active and valid"
# Status label updates to "✅ Valid (351d)"
# Status: PASS
```

#### Test Case 3.2: Manual Verification - Revoked License
```bash
# Step 1: Revoke license in Google Sheets
# Step 2: Click "🔐 Verify License" button

# Expected Result:
# Dialog: "❌ License verification failed: [reason]"
# Status label updates to "❌ Invalid"
# Status: PASS
```

#### Test Case 3.3: Manual Verification - Network Error
```bash
# Step 1: Disconnect internet
# Step 2: Click "🔐 Verify License" button

# Expected Result:
# Dialog: "Could not verify license: [network error]"
# Status label doesn't change (still shows last valid state)
# Status: PASS
```

---

### Feature 4: License Status Indicator (Toolbar)
**Purpose**: Visual display of license expiry and status  
**Location**: Toolbar top-right corner  
**Display Options**:
- `✅ Valid (351d)` - License is valid, 351 days remaining
- `⚠️ 7d left` - License expires in 7 days or less (warning color)
- `❌ Invalid` - License is revoked or expired

**Location**: [src/ui/main_window.py](../src/ui/main_window.py#L134) → `_update_license_status_label()`

#### Test Case 4.1: Status Display on Startup
```bash
.venv\Scripts\python src\main.py

# Expected Result:
# Toolbar shows "✅ Valid (351d)"
# Status: PASS
```

#### Test Case 4.2: Warning Display (< 7 days)
```bash
# Prerequisite: Manually edit expiry_date in SQLite to 5 days from now
# OR wait until license is within 7 days of expiry

.venv\Scripts\python src\main.py

# Expected Result:
# Toolbar shows "⚠️ 5d left" in warning color (orange)
# Status: PASS
```

---

### Feature 5: Hardware Binding (Anti-Piracy)
**Purpose**: Prevent license key sharing between computers  
**Mechanism**: Unique CPU + Motherboard serial combination  
**Threshold**: 2 out of 3 components must match (configurable)

**Location**: [src/licensing/hardware_id.py](../src/licensing/hardware_id.py)  
**Config**: `licensing.hardware_match_threshold: 2`

#### Test Case 5.1: Hardware Auto-Binding on First Activation
```bash
# Step 1: Fresh install, no license
# Step 2: Activate with valid license key
.venv\Scripts\python src\main.py
# > Click "License > Activate" or use license dialog

# Expected Result:
# Current hardware (CPU, Motherboard, Disk) captured
# Stored in local SQLite: license_info.hardware_components_json
# Status: PASS
```

#### Test Case 5.2: Hardware Mismatch on Different PC
```bash
# Step 1: Export license.db from Computer A
# Step 2: Import on Computer B (different hardware)
# Step 3: Run app on Computer B

.venv\Scripts\python src\main.py

# Expected Result:
# ❌ Hardware mismatch: CPU changed, Motherboard changed
# Transfer dialog appears
# User offered to transfer (uses 1 of 3 transfers)
# Status: PASS
```

---

### Feature 6: Hardware Transfer (Up to 3 Transfers)
**Purpose**: Allow legitimate hardware upgrades / migration  
**Limits**: Max 3 transfers per license (config: `max_transfers: 3`)  
**Behavior**:
- ✅ First transfer: 1/3 used
- ✅ Second transfer: 2/3 used
- ✅ Third transfer: 3/3 used (last transfer)
- ✅ Fourth transfer: DENIED (contact support)

**Location**: [src/licensing/license_manager.py](../src/licensing/license_manager.py#L319) → `request_transfer()`

#### Test Case 6.1: First Hardware Transfer
```bash
# Prerequisite: License activated on Computer A
# Step 1: Move to Computer B (different hardware)
# Step 2: Run app on Computer B
.venv\Scripts\python src\main.py

# Expected Result:
# Dialog: "Hardware mismatch... Would you like to transfer? (1/3)"
# Click "Transfer"
# Database updated: transfer_count = 1
# Status: PASS
```

#### Test Case 6.2: Second Hardware Transfer
```bash
# Prerequisite: Already transferred once
# Step 1: Move to Computer C (different hardware)
.venv\Scripts\python src\main.py

# Expected Result:
# Dialog: "Hardware mismatch... (2/3 transfers used)"
# Transfer succeeds
# Database updated: transfer_count = 2
# Status: PASS
```

#### Test Case 6.3: Transfer Limit Exceeded
```bash
# Prerequisite: Already transferred 3 times
# Step 1: Move to Computer D
.venv\Scripts\python src\main.py

# Expected Result:
# ❌ "Transfer limit reached (3/3)"
# Message: "Contact support@water-balance.com or +27 123 456 7890"
# License is BLOCKED (cannot proceed)
# Status: PASS
```

---

### Feature 7: Tier-Based Check Intervals (Premium vs Standard vs Trial)
**Purpose**: Different update frequencies by license tier  
**Config**:
```yaml
licensing:
  check_intervals:
    trial: 1      # Check every 1 hour
    standard: 24  # Check every 24 hours
    premium: 168  # Check every 7 days
```

**Location**: [src/licensing/license_manager.py](../src/licensing/license_manager.py#L105)

#### Test Case 7.1: Trial Tier (Hourly Checks)
```bash
# Prerequisite: License tier = "trial"
# Step 1: Start app
# Step 2: Wait 61 minutes
# Step 3: Background check triggers

# Expected Result:
# ✅ Background validation runs hourly (more frequent = less trust)
# Status: PASS
```

#### Test Case 7.2: Premium Tier (Weekly Checks)
```bash
# Prerequisite: License tier = "premium"
# Step 1: Start app
# Step 2: Restart within 7 days without internet

# Expected Result:
# ✅ App launches (doesn't require online validation)
# Can work offline for up to 7 days
# Status: PASS
```

---

### Feature 8: Offline Grace Period (7 Days)
**Purpose**: Allow work during internet outage  
**Duration**: 7 days (configurable: `offline_grace_days: 7`)  
**Behavior**:
- ✅ Set on successful online validation
- ✅ Extends by 7 days on each successful check
- ✅ After 7 days offline: license is BLOCKED

**Location**: [src/licensing/license_manager.py](../src/licensing/license_manager.py#L248)

#### Test Case 8.1: Offline Work (First 3 Days)
```bash
# Step 1: Successfully validate license online
# Step 2: Disconnect internet
# Step 3: Restart app (day 1, 2, 3)
.venv\Scripts\python src\main.py

# Expected Result:
# ✅ App launches without internet
# Status: "License valid (offline grace)"
# Status: PASS
```

#### Test Case 8.2: Offline Work (After 7 Days)
```bash
# Step 1: Last online validation: Day 0
# Step 2: No internet for 8 days
# Step 3: Restart app on Day 8
.venv\Scripts\python src\main.py

# Expected Result:
# ❌ Network error: Cannot validate license
# Grace period expired
# App blocks access
# Status: PASS
```

#### Test Case 8.3: Grace Period Reset on Re-connection
```bash
# Step 1: Offline for 3 days
# Step 2: Reconnect internet
# Step 3: Restart app
.venv\Scripts\python src\main.py

# Expected Result:
# ✅ Successful online validation
# offline_grace_until updated to NOW + 7 days
# User can work offline again for 7 more days
# Status: PASS
```

---

### Feature 9: Audit Logging & Security Events
**Purpose**: Track all license-related actions  
**Tables**:
- `license_validation_log` - All validation attempts
- `license_audit_log` - Security events (transfers, revocations)

**Location**: [src/database/schema.py](../src/database/schema.py)

#### Test Case 9.1: Validation Log Entry
```bash
# Step 1: Start app
# Step 2: Query database
sqlite3 data/water_balance.db
SELECT * FROM license_validation_log ORDER BY validation_timestamp DESC LIMIT 5;

# Expected Result:
# Rows show: startup | valid | [datetime]
# Background checks show up as: background | valid
# Revocations show: online_failed | [reason]
# Status: PASS
```

#### Test Case 9.2: Security Audit Log
```bash
sqlite3 data/water_balance.db
SELECT * FROM license_audit_log ORDER BY event_timestamp DESC LIMIT 5;

# Expected Result:
# Transfer events: "Hardware transfer approved (1/3)"
# Revocation alerts: "License was revoked"
# Status: PASS
```

---

## 🚨 Anti-Piracy Measures (Strict Mode)

### Enabled Features:
1. **Strict Hardware Matching** ✅
   - CPU + Motherboard serial comparison
   - Threshold: 2/3 components match
   - Prevents simple USB key sharing

2. **Remote Hardware Binding** ✅
   - Hardware info must exist on Google Sheets
   - Deleting hardware info invalidates license
   - Requires server-side cooperation

3. **Transfer Limits** ✅
   - Only 3 transfers per license
   - After 3: must contact support
   - Prevents unlimited device sharing

4. **Immediate Revocation** ✅
   - Any startup validates online
   - Revocations detected within 1 app start
   - No "trial period" after revocation

5. **Background Monitoring** ✅
   - Hourly checks during app usage
   - Catches mid-session revocations
   - Prevents week-long exploitation

6. **Audit Trail** ✅
   - Every validation logged
   - Every transfer logged
   - Every security event logged
   - Cannot be modified locally

---

## 🧪 Full Test Scenario (Integration Test)

### Scenario: Legitimate User Workflow
```bash
# Day 1: Fresh Install
.venv\Scripts\python src\main.py
# > License activation dialog
# > Enter license key: ABC-123-DEF-456
# > Click "Activate"
# > Hardware binding stored (CPU + MB serial)
# > Offline grace period: TODAY + 7 days
# ✅ PASS

# Day 2-7: Regular Usage (Online)
.venv\Scripts\python src\main.py
# > Background check every hour
# > Status shows "✅ Valid (350d)"
# ✅ PASS

# Day 8: Offline (Internet Down)
.venv\Scripts\python src\main.py
# > Offline grace period still valid
# > Status shows "✅ Valid (offline grace)"
# ✅ PASS

# Day 15: Still Offline
.venv\Scripts\python src\main.py
# > Offline grace period EXPIRED (7 days passed)
# ❌ "Network error: Cannot validate license"
# ✅ PASS (correctly blocks access)

# Day 15: Internet Back Up
.venv\Scripts\python src\main.py
# > Successful online validation
# > Offline grace period reset to NOW + 7 days
# > Status shows "✅ Valid (350d)"
# ✅ PASS

# Day 30: Hardware Upgrade (New CPU)
.venv\Scripts\python src\main.py
# > Hardware mismatch detected
# > Dialog: "Transfer to new hardware? (1/3 transfers)"
# > Click "Transfer"
# > New hardware binding stored
# > transfer_count = 1
# ✅ PASS

# Day 120: License Revoked (Admin action)
# Admin deletes hardware info from Google Sheets
.venv\Scripts\python src\main.py
# > Strict mode: "License hardware binding missing"
# ❌ License activation dialog
# ✅ PASS (pirate attempt blocked!)
```

---

## 📊 Testing Checklist

| Feature | Test Case | Status |
|---------|-----------|--------|
| Startup Validation | Valid License | ⬜ |
| Startup Validation | Revoked License | ⬜ |
| Startup Validation | Hardware Mismatch | ⬜ |
| Startup Validation | Offline Grace | ⬜ |
| Background Check | Catches Revocation | ⬜ |
| Background Check | Network Error Handling | ⬜ |
| Manual Verification | Valid License | ⬜ |
| Manual Verification | Revoked License | ⬜ |
| Manual Verification | Network Error | ⬜ |
| Status Indicator | Valid Display | ⬜ |
| Status Indicator | Warning Display | ⬜ |
| Hardware Binding | Auto-Binding | ⬜ |
| Hardware Transfer | First Transfer (1/3) | ⬜ |
| Hardware Transfer | Second Transfer (2/3) | ⬜ |
| Hardware Transfer | Limit Exceeded (3/3) | ⬜ |
| Tier-Based Intervals | Trial (1h) | ⬜ |
| Tier-Based Intervals | Premium (7d) | ⬜ |
| Offline Grace | First 3 Days | ⬜ |
| Offline Grace | After 7 Days | ⬜ |
| Offline Grace | Grace Period Reset | ⬜ |
| Audit Logging | Validation Log | ⬜ |
| Audit Logging | Security Audit Log | ⬜ |

---

## 🔧 Configuration Reference

```yaml
licensing:
  # Anti-Piracy Settings
  require_remote_hardware_match: true    # STRICT MODE
  hardware_match_threshold: 2             # 2 of 3 components
  max_transfers: 3                        # Only 3 transfers allowed
  
  # Check Timing
  background_check_interval_seconds: 3600  # 1 hour background checks
  offline_grace_days: 7                   # 7 days offline allowed
  
  # Tier-Based Frequencies
  check_intervals:
    trial: 1      # Trial: check every 1 hour
    standard: 24  # Standard: check every 24 hours
    premium: 168  # Premium: check every 7 days
  
  # Support
  support_email: support@water-balance.com
  support_phone: +27 123 456 7890
  
  # Google Sheets
  sheet_url: https://docs.google.com/spreadsheets/d/1_WA6A8rCg...
  sheet_name: licenses
  service_account_json: C:\keys\water-balance-license-manager...json
```

---

## 🎯 Summary

**With STRICT MODE enabled:**
- ✅ Piracy **significantly harder** (hardware binding + remote check)
- ✅ Revocations **caught immediately** (online validation at startup)
- ✅ Mid-session theft **prevented** (hourly background checks)
- ✅ Trial abuse **limited** (transfer limit of 3)
- ✅ Offline exploitation **prevented** (7-day grace period only)
- ✅ Full audit trail **available** (every action logged)

---

## ❓ Support

For questions or issues:
- **Email**: support@water-balance.com
- **Phone**: +27 123 456 7890
- **Sheet**: [License Management](https://docs.google.com/spreadsheets/d/1_WA6A8rCg5Av2CNzArEI_aqalW_DMYelq8a6OPcd_js/)

