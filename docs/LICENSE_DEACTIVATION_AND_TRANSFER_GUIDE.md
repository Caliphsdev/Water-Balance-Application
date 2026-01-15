# License Management Guide

## 🔒 Deactivating a User (Admin)

### Method 1: Revoke License
1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/
2. Find the user's license key row
3. Change **status** column (B) from `active` to `revoked`
4. Save (auto-saves)

**Result:**
- Next app startup → "License revoked" error
- User cannot use the app
- Data preserved in Sheet for audit trail

### Method 2: Expire License
1. Open Google Sheet
2. Find the user's license key row
3. Set **expiry_date** column (C) to past date (e.g., `2020-01-01`)
4. Save

**Result:**
- Next app startup → "License expired" error
- User cannot use the app

### Method 3: Delete License Row (NOT RECOMMENDED)
- Deletes all activation history
- No audit trail
- Better to revoke instead

---

## 🖥️ Transfer to New Computer (User)

### Scenario: User Gets New Computer

**Step 1: User Installs App on New Computer**
- Downloads app
- Runs for first time
- License dialog appears

**Step 2: User Enters Same License Key**
- Enters their existing license key (e.g., ABC-123-XYZ)
- Enters licensee name and email (optional)
- Clicks "Activate Online"

**Step 3: Hardware Mismatch Detected**
- App detects hardware doesn't match Sheet
- Dialog shows: "Hardware mismatch detected. Request transfer to continue."
- Two buttons visible:
  - ❌ "Activate Online" (will fail)
  - ✅ "Request Transfer" (user clicks this)

**Step 4: Transfer Approved**
- User clicks "Request Transfer"
- App updates hardware binding:
  - Local SQLite: new hardware components saved
  - Google Sheet: hw_component_1/2/3 updated to new machine
  - transfer_count increments (e.g., 0 → 1)
  - last_transfer_at timestamp updated
- Success message: "Transfer approved and hardware updated."
- App proceeds to dashboard

**Step 5: Old Computer Can't Activate**
- Old computer now has mismatched hardware
- User would need another transfer to go back (increments counter again)

---

## 📊 What Gets Updated in Sheet During Transfer

| Column | Before Transfer | After Transfer | Notes |
|--------|----------------|----------------|-------|
| hw_component_1 | Old MAC hash | **New MAC hash** | Updated |
| hw_component_2 | Old CPU hash | **New CPU hash** | Updated |
| hw_component_3 | Old board hash | **New board hash** | Updated |
| transfer_count | 0 | **1** | Incremented |
| last_transfer_at | NULL | **2026-01-14T13:15:00** | Timestamp |
| status | active | active | Unchanged |
| licensee_name | User Name | User Name | Unchanged |

---

## 🛡️ Transfer Policies (Optional Enforcement)

### Option 1: Unlimited Transfers (Current Default)
- Users can transfer as many times as needed
- transfer_count tracked but not enforced
- Good for development/testing

### Option 2: Limit Transfers (Requires Code Change)
Add to `license_manager.py` → `request_transfer()`:

```python
# Check transfer limit before approving
max_transfers = 3  # Allow 3 transfers per license
current_transfers = record.get("transfer_count") or 0

if current_transfers >= max_transfers:
    return False, f"Transfer limit reached ({max_transfers} transfers max)"
```

### Option 3: Manual Approval (Sheet-Based)
Add column `transfer_approved` to Sheet:
- Admin sets to TRUE to allow transfer
- App checks this field before approving
- After transfer, resets to FALSE

---

## 🧪 Testing Transfer Flow

### Test Scenario 1: Simulate New Computer
```bash
# Clear local SQLite binding
python -c "
from src.database.db_manager import db
db.execute_update('UPDATE license_info SET hardware_components_json = \\'{\\\"mac\\\":\\\"different123\\\",\\\"cpu\\\":\\\"different456\\\",\\\"board\\\":\\\"different789\\\"}\\' WHERE license_key = \\'ABC-123-XYZ\\'')
print('✅ Simulated hardware change')
"

# Run app - should show hardware mismatch
python src/main.py
# Click "Request Transfer" → Should succeed
```

### Test Scenario 2: Check Transfer Count
```bash
# View Sheet transfer_count column (should increment)
python -c "
from src.licensing.license_client import LicenseClient
client = LicenseClient()
records = client._get_records()
for row in records:
    if row.get('license_key') == 'ABC-123-XYZ':
        print(f'Transfer count: {row.get(\\\"transfer_count\\\")}')
"
```

---

## 🔍 Monitoring Transfers (Admin)

### Google Sheet Audit
- **transfer_count**: Number of times license transferred
- **last_transfer_at**: When last transfer occurred
- **hw_component_***: Current hardware binding

### Red Flags
- transfer_count > 10: Possible license sharing
- Frequent transfers (daily): Investigate
- Multiple transfers in short time: Suspicious

### Admin Actions
1. Contact user to verify legitimate transfer
2. Revoke license if abuse confirmed
3. Issue new license key if needed

---

## 📋 Common Questions

**Q: Can user use app on multiple computers simultaneously?**  
A: No. License is bound to one hardware configuration at a time.

**Q: What if user's hardware fails (motherboard replacement)?**  
A: User requests transfer. New hardware binding saved automatically.

**Q: Can admin force a transfer without user action?**  
A: Yes. Admin can manually update hw_component_* columns in Sheet + increment transfer_count.

**Q: How to reset a license completely?**  
A: In Sheet, clear hw_component_1/2/3 columns, set transfer_count to 0, status to active.

**Q: Can user revert to old computer?**  
A: Yes, but requires another transfer (increments counter again).

---

## 🚀 Summary

**Deactivation (Admin):**  
Sheet → Change status to "revoked" → User blocked at next startup

**Transfer (User):**  
New computer → Enter license key → Click "Request Transfer" → Hardware rebinding → App works on new machine → Old machine blocked

Both workflows are **already implemented** and tested ✅
