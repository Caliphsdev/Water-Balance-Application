# Fix Apps Script Column Mapping Issue

## Problem Summary

Your webhook is sending all the correct data, but the Apps Script is writing to the **wrong columns**:

```
Current Behavior (WRONG):
┌─────────────────┬─────────────────┬─────────────────┐
│ Column          │ Expected Data   │ Actual Data     │
├─────────────────┼─────────────────┼─────────────────┤
│ D: hw_comp_1    │ hw1 hash        │ [EMPTY] ❌      │
│ E: hw_comp_2    │ hw2 hash        │ hw2 hash ✅     │
│ F: hw_comp_3    │ hw3 hash        │ hw3 hash ✅     │
│ J: license_tier │ "standard"      │ "active" ❌     │
└─────────────────┴─────────────────┴─────────────────┘
```

**Root Cause**: Your Apps Script `doPost()` handler has incorrect column indices.

---

## Solution: Fix Apps Script Handler

### Step 1: Open Apps Script Editor

1. Go to your Google Sheet: https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/
2. Click **Extensions** → **Apps Script**
3. Find the `doPost(e)` function

### Step 2: Replace with Corrected Code

Delete the existing `doPost` function and paste this corrected version:

```javascript
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActive().getSheetByName("licenses");
    
    if (!sheet) {
      return ContentService.createTextOutput("Sheet 'licenses' not found");
    }
    
    // Find row by license_key (column A = index 0)
    const range = sheet.getDataRange();
    const values = range.getValues();
    let rowIndex = -1;
    
    for (let i = 1; i < values.length; i++) {
      if (String(values[i][0]).trim() === String(payload.license_key).trim()) {
        rowIndex = i + 1; // Convert to 1-indexed sheet row
        break;
      }
    }
    
    if (rowIndex === -1) {
      return ContentService.createTextOutput("License key not found: " + payload.license_key);
    }
    
    // CORRECT column mappings (1-indexed for getRange)
    const columnMap = {
      "B": 2,   // status
      "D": 4,   // hw_component_1
      "E": 5,   // hw_component_2
      "F": 6,   // hw_component_3
      "H": 8,   // licensee_name
      "I": 9,   // licensee_email
      "J": 10   // license_tier
    };
    
    // Map JSON fields to sheet columns
    const updates = {
      [columnMap["B"]]: payload.status || "active",
      [columnMap["D"]]: payload.hw1 || "",
      [columnMap["E"]]: payload.hw2 || "",
      [columnMap["F"]]: payload.hw3 || "",
      [columnMap["H"]]: payload.licensee_name || "",
      [columnMap["I"]]: payload.licensee_email || "",
      [columnMap["J"]]: payload.license_tier || "standard"
    };
    
    // Write each field to correct column
    for (const [col, value] of Object.entries(updates)) {
      sheet.getRange(rowIndex, parseInt(col)).setValue(value);
      Logger.log(`Updated row ${rowIndex}, col ${col}: ${value}`);
    }
    
    Logger.log(`Successfully updated license ${payload.license_key}`);
    return ContentService.createTextOutput("OK");
    
  } catch (err) {
    Logger.log("Error in doPost: " + err);
    return ContentService.createTextOutput("Error: " + err.message);
  }
}
```

### Step 3: Deploy the Updated Script

1. Click **Deploy** → **New Deployment** (or update existing)
2. Choose **Web app**
3. Set **Execute as**: Your email
4. Set **Who has access**: Anyone
5. Click **Deploy**
6. Copy the new webhook URL (should be same as before)

### Step 4: Verify Column Layout

Your sheet should have these columns:

| Column | Header | Notes |
|--------|--------|-------|
| A | license_key | Primary key |
| B | status | active/pending/revoked/expired |
| C | expiry_date | YYYY-MM-DD |
| D | **hw_component_1** | ← Should receive hw1 hash |
| E | **hw_component_2** | ← Should receive hw2 hash |
| F | **hw_component_3** | ← Should receive hw3 hash |
| G | _(skip)_ | |
| H | licensee_name | ← Should receive name |
| I | licensee_email | ← Should receive email |
| J | license_tier | ← Should receive "standard" |
| K | transfer_count | (leave as-is) |

If your columns are different, adjust the column numbers in the script above.

---

## Test After Fix

### Option A: Create New Test License

1. Add this row to your Sheet (Row 3):
   ```
   TEST-456-DEF | active | 2026-06-01 | | | | | | | |
   ```

2. Run this test in your terminal:
   ```bash
   cd c:\PROJECTS\Water-Balance-Application
   python -c "
from src.licensing.license_manager import LicenseManager
mgr = LicenseManager()
ok, msg = mgr.activate('TEST-456-DEF', 'Test User 2', 'test2@example.com')
print(f'Activation: {ok} - {msg}')
   "
   ```

3. Check your Sheet - all columns should be populated:
   - ✅ hw_component_1: hw1 hash (not empty!)
   - ✅ hw_component_2: hw2 hash
   - ✅ hw_component_3: hw3 hash
   - ✅ licensee_name: Test User 2
   - ✅ licensee_email: test2@example.com
   - ✅ license_tier: standard (not "active"!)

### Option B: Re-test ABC-123-XYZ

Clear Row 2 columns D-J and activate again:

```bash
python -c "
from src.licensing.license_manager import LicenseManager
mgr = LicenseManager()
ok, msg = mgr.activate('ABC-123-XYZ', 'Updated User', 'updated@example.com')
print(f'Activation: {ok} - {msg}')
"
```

---

## What Changed in Python Code

✅ Updated `license_client.py` to send complete payload:
- Added `license_tier: "standard"`
- Moved `status` to come earlier in payload

This ensures the webhook handler has all the data it needs. The real fix is the Apps Script column mapping.

---

## Debugging Checklist

- [ ] Apps Script `doPost` updated with correct column map
- [ ] Script deployed (new deployment URL visible)
- [ ] Column headers verified in Sheet (A-J)
- [ ] Test activation run
- [ ] Sheet updated: hw_component_1 is NOT empty
- [ ] Sheet updated: license_tier shows "standard", not "active"
- [ ] Apps Script execution log checked for errors

---

## Apps Script Logs (Troubleshooting)

To see what the webhook is doing:

1. Open Apps Script Editor
2. Click **Executions** (clock icon on left)
3. Look for recent runs
4. Click a run to see logs
5. Check for any errors like "License key not found" or column mapping issues

---

**After applying this fix, your Sheet should update correctly with all fields populated!**
