# Professional Google Sheets License Manager Setup Guide

## Overview
This guide walks you through creating a professional, visually appealing Google Sheet for managing Water Balance software licenses with conditional formatting, data validation, and automatic webhook updates.

---

## Part 1: Create the Sheet Structure

### Step 1: Create New Google Sheet
1. Go to Google Sheets: https://sheets.google.com
2. Create a new blank spreadsheet
3. Rename it to "**Water Balance License Manager**"
4. Rename Sheet1 to "**licenses**" (lowercase)

### Step 2: Set Up Column Headers (Row 1)

Enter these headers in Row 1:

| Column | Header Name | Description |
|--------|------------|-------------|
| A | license_key | Unique license identifier (e.g., ABC-123-XYZ) |
| B | status | Current license status |
| C | expiry_date | Expiration date (YYYY-MM-DD) |
| D | hw_component_1 | MAC address hash |
| E | hw_component_2 | CPU ID hash |
| F | hw_component_3 | Motherboard hash |
| G | transfer_count | Number of hardware transfers |
| H | licensee_name | Customer/company name |
| I | licensee_email | Contact email |
| J | license_tier | License tier/plan |
| K | last_validated | Last online validation timestamp |

### Step 3: Format Header Row

1. **Select Row 1** (entire row)
2. **Make it bold**: Click Bold button or Ctrl+B
3. **Background color**: Click fill color → choose **Dark blue (#0D47A1)** or similar
4. **Text color**: Click text color → choose **White (#FFFFFF)**
5. **Center align**: Click align center button
6. **Freeze header**: View → Freeze → 1 row

---

## Part 2: Set Column Widths

Select each column and resize:

| Column | Width (pixels) | How to Set |
|--------|----------------|------------|
| A (license_key) | 180 | Click column A header → drag right edge |
| B (status) | 100 | Click column B header → drag |
| C (expiry_date) | 120 | Click column C header → drag |
| D-F (hw_*) | 250 each | Click each column → drag |
| G (transfer_count) | 80 | Click column G → drag |
| H (licensee_name) | 200 | Click column H → drag |
| I (licensee_email) | 220 | Click column I → drag |
| J (license_tier) | 100 | Click column J → drag |
| K (last_validated) | 180 | Click column K → drag |

**Quick Tip:** Double-click the column border to auto-resize to content.

---

## Part 3: Data Validation (Dropdowns)

### Status Column (B)

1. **Select B2:B1000** (or however many rows you need)
2. **Data → Data validation**
3. **Criteria**: List of items
4. **Items**: 
   ```
   active
   revoked
   expired
   pending
   ```
   (One per line or comma-separated)
5. **Show dropdown**: ✅ Checked
6. **Show warning**: ❌ Unchecked (reject invalid data)
7. Click **Save**

### License Tier Column (J)

1. **Select J2:J1000**
2. **Data → Data validation**
3. **Criteria**: List of items
4. **Items**:
   ```
   trial
   standard
   premium
   ```
5. **Show dropdown**: ✅ Checked
6. Click **Save**

---

## Part 4: Conditional Formatting (Visual Status Indicators)

### Rule 1: Revoked Status (Red Alert)
1. **Select B2:B1000** (status column)
2. **Format → Conditional formatting**
3. **Format rules**:
   - **Format cells if**: Text contains
   - **Value**: `revoked`
4. **Formatting style**:
   - **Background color**: Light red (#FFCDD2)
   - **Text color**: Dark red (#D32F2F)
   - **Bold**: ✅ Checked
5. Click **Done**

### Rule 2: Expired Status (Orange Warning)
1. **Select B2:B1000**
2. **Format → Conditional formatting**
3. **Format cells if**: Text contains
4. **Value**: `expired`
5. **Formatting style**:
   - **Background**: Light orange (#FFE0B2)
   - **Text**: Orange (#F57C00)
   - **Bold**: ✅
6. Click **Done**

### Rule 3: Expiring Soon (Yellow Warning) - Advanced
1. **Select C2:C1000** (expiry_date column)
2. **Format → Conditional formatting**
3. **Format cells if**: Custom formula is
4. **Formula**:
   ```
   =AND(C2<>"", C2>=TODAY(), C2<=TODAY()+7)
   ```
   (Highlights dates 1-7 days from today)
5. **Formatting style**:
   - **Background**: Light yellow (#FFF9C4)
   - **Text**: Orange (#F57C00)
6. Click **Done**

### Rule 4: Active Status (Green Success)
1. **Select B2:B1000**
2. **Format → Conditional formatting**
3. **Format cells if**: Text contains
4. **Value**: `active`
5. **Formatting style**:
   - **Background**: Light green (#C8E6C9)
   - **Text**: Dark green (#2E7D32)
6. Click **Done**

### Rule 5: Pending Status (Blue Info)
1. **Select B2:B1000**
2. **Format → Conditional formatting**
3. **Format cells if**: Text contains
4. **Value**: `pending`
5. **Formatting style**:
   - **Background**: Light blue (#BBDEFB)
   - **Text**: Blue (#1976D2)
6. Click **Done**

---

## Part 5: Number Formatting

### Transfer Count (Column G)
1. **Select G2:G1000**
2. **Format → Number → Number**
3. This ensures integers only (no decimals)

### Expiry Date (Column C)
1. **Select C2:C1000**
2. **Format → Number → Date**
3. Choose format: **YYYY-MM-DD** (e.g., 2026-01-15)

### Last Validated (Column K)
1. **Select K2:K1000**
2. **Format → Number → Date time**
3. Choose format showing both date and time

---

## Part 6: Sample Data (For Testing)

Add these test licenses to Row 2 (first data row):

| A | B | C | D | E | F | G | H | I | J | K |
|---|---|---|---|---|---|---|---|---|---|---|
| ABC-123-XYZ | active | 2026-12-31 | 2241367234182d6dc76c5 | 9b4943be60223d8e56f7 | 9bd943be0822 | 0 | Test Company | test@example.com | standard | (auto) |
| TEST-456-DEF | revoked | 2026-06-15 | abc123def456 | 789xyz321 | motherboardXYZ | 2 | Revoked User | revoked@test.com | trial | (auto) |
| TRIAL-789-GHI | pending | 2026-02-01 | pending123 | pending456 | pending789 | 0 | Trial User | trial@demo.com | trial | (auto) |

**Note**: Column K (last_validated) will auto-update from the webhook. Leave it blank for manual entries.

---

## Part 7: Protect the Sheet (Optional)

### Lock Header Row
1. **Select Row 1** (header)
2. **Data → Protect sheets and ranges**
3. **Description**: "Header Row"
4. **Set permissions**: Only you can edit
5. Click **Done**

### Lock Hardware Columns (Auto-Updated Only)
1. **Select D2:F1000, K2:K1000** (hardware components and last_validated)
2. **Data → Protect sheets and ranges**
3. **Description**: "Auto-updated fields"
4. **Set permissions**: Show a warning when editing
5. This prevents accidental manual edits to webhook-managed fields

---

## Part 8: Make Sheet Publicly Readable (for CSV API)

1. **Click Share button** (top right)
2. **Change to "Anyone with the link"**
3. **Viewer access** (read-only)
4. **Copy the share link** (you'll need this for Python config)
5. Click **Done**

Example link:
```
https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/edit?usp=sharing
```

---

## Part 9: Deploy Apps Script Webhook

### 9.1 Open Script Editor
1. In your Google Sheet, click **Extensions → Apps Script**
2. Delete any existing code in `Code.gs`
3. Copy the entire contents of `docs/Google_Apps_Script_License_Webhook.js`
4. Paste into the Apps Script editor

### 9.2 Deploy as Web App
1. Click **Deploy → New deployment**
2. Click **⚙️ (gear icon) → Web app**
3. **Description**: "License Manager Webhook v1"
4. **Execute as**: Me (your email)
5. **Who has access**: Anyone
6. Click **Deploy**
7. **Authorize** (click your Google account, then "Advanced" → "Go to License Manager (unsafe)" → Allow)
8. **Copy the Web App URL** (this is your webhook URL)

Example webhook URL:
```
https://script.google.com/macros/s/AKfycbxvTGp5kZXITwVq709vhstAiHU3qigzej3jNOXybWuj2ZFgOwvNa_ATO6RxR8nT2GxJ/exec
```

### 9.3 Update Python Config
1. Open `config/app_config.yaml`
2. Update the webhook URL:
   ```yaml
   licensing:
     webhook_url: https://script.google.com/macros/s/YOUR_NEW_DEPLOYMENT_ID/exec
   ```
3. Save the file

---

## Part 10: Test the Integration

### 10.1 Test with Python Script

Create a test file `test_license_sync.py`:

```python
import requests

WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"

payload = {
    "license_key": "PYTHON-TEST-001",
    "status": "active",
    "hw1": "test_mac_hash_12345",
    "hw2": "test_cpu_hash_67890",
    "hw3": "test_board_hash_abcde",
    "licensee_name": "Python Test User",
    "licensee_email": "python@test.com",
    "license_tier": "standard",
    "is_transfer": False
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

Run: `.venv\Scripts\python test_license_sync.py`

**Expected Result**: Check your Google Sheet - Row should appear with all data populated!

### 10.2 Test Transfer (Increment Counter)

```python
payload = {
    "license_key": "PYTHON-TEST-001",  # Same key as above
    "status": "active",
    "hw1": "new_mac_hash_99999",  # Changed hardware
    "hw2": "new_cpu_hash_88888",
    "hw3": "new_board_hash_77777",
    "license_tier": "standard",
    "is_transfer": True  # This increments transfer_count
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
print(response.text)
```

**Expected Result**: Same row updates with new hardware, transfer_count = 1

---

## Part 11: Visual Enhancements (Optional Polish)

### Add Borders
1. **Select A1:K1000**
2. **Borders button** → All borders
3. Choose light gray color (#E0E0E0)

### Alternate Row Colors
1. **Select A2:K1000**
2. **Format → Alternating colors**
3. **Choose style**: Light gray 2 or Custom
4. **Header**: Dark blue (matching Row 1)
5. **Color 1**: White (#FFFFFF)
6. **Color 2**: Very light gray (#F5F5F5)
7. Click **Done**

### Filter Views
1. **Select A1:K1**
2. **Data → Create a filter**
3. Now you can filter by status, tier, etc.

---

## Troubleshooting

### ❌ Webhook returns ERROR
- **Check**: Sheet name is exactly "licenses" (lowercase)
- **Check**: Apps Script is deployed as Web App with "Anyone" access
- **Check**: Payload JSON is valid

### ❌ Conditional formatting not working
- **Check**: Rules are applied to correct range (B2:B1000, etc.)
- **Check**: Formula syntax (no typos)
- **Check**: Color codes are correct

### ❌ Dropdowns not showing
- **Check**: Data validation applied to range (not just one cell)
- **Check**: "Show dropdown" is checked

### ❌ Can't edit protected ranges
- **Check**: Protection settings (Data → Protected ranges)
- **Remove protection**: Click the protected range → trash icon

---

## Final Checklist

- [ ] Header row: Bold, dark blue background, white text, frozen
- [ ] Column widths: Adjusted for readability
- [ ] Data validation: Dropdowns on status (B) and license_tier (J)
- [ ] Conditional formatting: 5 rules (revoked, expired, expiring, active, pending)
- [ ] Number formatting: Dates, integers, timestamps
- [ ] Sample data: At least one test row
- [ ] Sheet sharing: Public link (read-only)
- [ ] Apps Script: Deployed as Web App, webhook URL copied
- [ ] Python config: Updated with new webhook URL
- [ ] Integration test: Python script successfully updates Sheet

---

## Next Steps

1. **Add Real Licenses**: Manually enter or import your actual license keys
2. **Set Expiry Dates**: Add expiration dates for time-limited licenses
3. **Test App**: Run `python src/main.py` with a valid license
4. **Monitor Sheet**: Watch as licenses auto-validate and update `last_validated`
5. **Revoke Test**: Change status to "revoked" and test app blocking

---

## Visual Preview

Your final sheet should look like this:

```
┌──────────────────┬─────────┬──────────────┬────────────────────┬────────────────────┬────────────────────┬──────────────┬──────────────┬──────────────────┬──────────────┬────────────────────┐
│ license_key      │ status  │ expiry_date  │ hw_component_1     │ hw_component_2     │ hw_component_3     │ transfer_cnt │ licensee_name│ licensee_email   │ license_tier │ last_validated     │
├──────────────────┼─────────┼──────────────┼────────────────────┼────────────────────┼────────────────────┼──────────────┼──────────────┼──────────────────┼──────────────┼────────────────────┤
│ ABC-123-XYZ      │ active  │ 2026-12-31   │ 2241367234182d6... │ 9b4943be60223d8... │ 9bd943be0822...   │ 0            │ Test Company │ test@example.com │ standard     │ 2026-01-14 13:45   │
│ TEST-456-DEF     │ revoked │ 2026-06-15   │ abc123def456       │ 789xyz321          │ motherboardXYZ     │ 2            │ Revoked User │ revoked@test.com │ trial        │ 2026-01-10 09:20   │
└──────────────────┴─────────┴──────────────┴────────────────────┴────────────────────┴────────────────────┴──────────────┴──────────────┴──────────────────┴──────────────┴────────────────────┘
```

**Color coding:**
- 🟢 Active = Green background
- 🔴 Revoked = Red background
- 🟠 Expired = Orange background
- 🟡 Expiring soon = Yellow background
- 🔵 Pending = Blue background

---

**You're done!** 🎉 You now have a professional, enterprise-grade license management system with Google Sheets!

