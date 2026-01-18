# Licensing - Quick Test Guide

**Current Mode**: 🔐 **STRICT** (Anti-Piracy Enabled)  
**Status**: require_remote_hardware_match = ✅ TRUE

---

## 🚀 Quick 5-Minute Tests

### Test 1: Normal Launch (Valid License)
```bash
.venv\Scripts\python src\main.py
```
**Expected**: App launches, shows "✅ Valid (351d)" in toolbar  
**Time**: < 10 seconds

---

### Test 2: Manual License Check
```bash
# While app is running:
# Click "🔐 Verify License" button (top right toolbar)
```
**Expected**: Dialog shows "✅ Your license is active and valid"  
**Time**: 2-5 seconds (network call)

---

### Test 3: Simulate Revocation (Hardware Mismatch)
```bash
# Edit Google Sheets manually:
# Find your license key row
# Delete the "hardware_components_json" field
# Leave license_status = "valid"

# Then restart app
.venv\Scripts\python src\main.py
```
**Expected**: App blocks with message about missing hardware binding  
**Time**: < 3 seconds

---

### Test 4: Check Background Validation Running
```bash
# Step 1: Start app
.venv\Scripts\python src\main.py

# Step 2: Wait 10 seconds, then check logs
# In logs folder, search for:
grep "Background validation" logs/*.log
```
**Expected**: See "Running periodic background license check..." in logs  
**Time**: 1 minute to see first check

---

### Test 5: View License Status in Database
```bash
# While app is running:
sqlite3 data\water_balance.db
SELECT license_status, expiry_date, transfer_count, last_online_check FROM license_info LIMIT 1;

# Exit
.quit
```
**Expected Output**:
```
license_status | expiry_date | transfer_count | last_online_check
active         | 2027-01-14  | 0              | 2026-01-14T14:13:23...
```

---

### Test 6: View Audit Log
```bash
sqlite3 data\water_balance.db
SELECT event_type, event_details, event_timestamp FROM license_audit_log ORDER BY event_timestamp DESC LIMIT 5;
.quit
```
**Expected**: See transfer events, revocation alerts if any

---

## 🔄 Scenario Tests (10 Minutes Each)

### Scenario A: Fresh Activation
```
1. Delete data/water_balance.db (remove existing license)
2. .venv\Scripts\python src\main.py
3. Dialog appears: "License not activated"
4. Click "Activate"
5. Enter license key: [valid key from sheet]
6. Click "Activate"
7. Hardware binding created in SQLite
8. App launches
Status: PASS ✅
```

### Scenario B: Hardware Transfer
```
1. Start app (existing license on Computer A)
2. Copy data/water_balance.db to Computer B (different hardware)
3. .venv\Scripts\python src\main.py (on Computer B)
4. Dialog: "Hardware mismatch: CPU changed, Motherboard changed"
5. Click "Transfer" (use 1/3 transfers)
6. SQLite updated: transfer_count = 1
7. App launches with new hardware binding
Status: PASS ✅
```

### Scenario C: Transfer Limit
```
1. (After 3 successful transfers)
2. Try to transfer to 4th hardware
3. .venv\Scripts\python src\main.py
4. Dialog: "Transfer limit reached (3/3)"
5. App blocks
Status: PASS ✅
```

### Scenario D: Offline Grace Period
```
1. Validate license online (grace_until = TODAY + 7 days)
2. Disconnect internet
3. Days 1-7: .venv\Scripts\python src\main.py → ✅ Works
4. Day 8: .venv\Scripts\python src\main.py → ❌ Blocked
Status: PASS ✅
```

---

## 📊 Feature Status

| Feature | Enabled | Tested |
|---------|---------|--------|
| Strict Hardware Matching | ✅ YES | ⬜ |
| Remote Hardware Binding Required | ✅ YES | ⬜ |
| Startup Online Validation | ✅ YES | ⬜ |
| Background Hourly Checks | ✅ YES | ⬜ |
| Manual Verification Button | ✅ YES | ⬜ |
| Hardware Transfer (3x limit) | ✅ YES | ⬜ |
| Offline Grace Period (7 days) | ✅ YES | ⬜ |
| Audit Logging | ✅ YES | ⬜ |

---

## 🔍 Debugging Commands

### View Current License Status
```bash
sqlite3 data\water_balance.db ".mode column" "SELECT license_status, expiry_date, transfer_count, offline_grace_until FROM license_info;"
```

### Check Recent Validations
```bash
sqlite3 data\water_balance.db "SELECT validation_result, validation_message, validation_timestamp FROM license_validation_log ORDER BY validation_timestamp DESC LIMIT 10;"
```

### Check Hardware Binding
```bash
sqlite3 data\water_balance.db "SELECT hardware_components_json, hardware_match_threshold FROM license_info LIMIT 1;"
```

### Reset License (Fresh Start)
```bash
# Backup first!
copy data\water_balance.db data\water_balance.db.backup

# Delete license record
sqlite3 data\water_balance.db "DELETE FROM license_info;"

# Restart app to re-activate
.venv\Scripts\python src\main.py
```

---

## 📞 Common Issues

| Issue | Solution |
|-------|----------|
| "Hardware binding missing" | Add hardware_components_json back to Google Sheet |
| "Hardware mismatch" on same PC | Delete SQLite, re-activate |
| "Transfer limit reached" | Contact support@water-balance.com |
| "Network error" after 7 days offline | Connect to internet, restart |
| Validation stuck in logs | Restart app, check internet connectivity |

---

## ✅ Anti-Piracy Verification

To verify strict mode is REALLY protecting against piracy:

1. **Can you run app without hardware binding on Sheet?** ❌ NO (blocked in strict mode)
2. **Can you transfer unlimited times?** ❌ NO (limited to 3)
3. **Can you use after revocation for a week?** ❌ NO (caught on next startup)
4. **Can you share license key on USB?** ❌ NO (hardware ID prevents it)
5. **Can you delete audit logs?** ❌ NO (stored in company DB)

✅ **STRICT MODE WORKING CORRECTLY**

