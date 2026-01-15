# Professional License System Upgrade Plan
**Date:** January 14, 2026  
**Status:** Implementation in Progress

## Overview
Complete redesign of the licensing system to production-grade quality with professional UI/UX, comprehensive security features, and enterprise-ready Google Sheets management.

---

## Phase 1: Google Sheets Professional Design

### New Sheet Structure (11 columns + conditional formatting)
| Column | Name | Purpose | Type | Apps Script Col# |
|--------|------|---------|------|-----------------|
| A | license_key | Unique license identifier | TEXT | 1 |
| B | status | active/revoked/expired/pending | DROPDOWN | 2 |
| C | expiry_date | YYYY-MM-DD format | DATE | 3 |
| D | hw_component_1 | MAC address hash | TEXT | 4 |
| E | hw_component_2 | CPU ID hash | TEXT | 5 |
| F | hw_component_3 | Motherboard hash | TEXT | 6 |
| G | transfer_count | Number of hardware transfers | NUMBER | 7 |
| H | licensee_name | Customer/company name | TEXT | 8 |
| I | licensee_email | Contact email | TEXT | 9 |
| J | license_tier | trial/standard/premium | DROPDOWN | 10 |
| K | last_validated | Timestamp of last online check | TIMESTAMP | 11 |

### Visual Design Features
1. **Header Row (Row 1)**
   - Bold white text on dark blue background (#0D47A1)
   - Frozen row for scrolling
   - Center-aligned headers

2. **Conditional Formatting Rules**
   - **Revoked Status**: Red background (#FFCDD2) + red text (#D32F2F)
   - **Expired Status**: Orange background (#FFE0B2) + orange text (#F57C00)
   - **Expiring Soon** (≤7 days): Yellow background (#FFF9C4) + orange text
   - **Active Status**: Light green background (#C8E6C9) + green text (#2E7D32)
   - **Pending Status**: Light blue background (#BBDEFB) + blue text (#1976D2)

3. **Column Widths** (auto-resize after)
   - A (license_key): 180px
   - B (status): 100px
   - C (expiry_date): 120px
   - D-F (hw_*): 250px each
   - G (transfer_count): 80px
   - H (licensee_name): 200px
   - I (licensee_email): 220px
   - J (license_tier): 100px
   - K (last_validated): 180px

4. **Data Validation**
   - Status: Dropdown (active, revoked, expired, pending)
   - Tier: Dropdown (trial, standard, premium)
   - Expiry: Date format validation
   - Transfer_count: Integer >= 0

---

## Phase 2: Apps Script Webhook Update

### Updated doPost() Function
```javascript
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("licenses");
    var data = JSON.parse(e.postData.contents);
    
    // Search for existing license_key
    var dataRange = sheet.getDataRange();
    var values = dataRange.getValues();
    var targetRow = -1;
    
    for (var i = 1; i < values.length; i++) {
      if (values[i][0] == data.license_key) {
        targetRow = i + 1;
        break;
      }
    }
    
    // Append new row if not found
    if (targetRow === -1) {
      targetRow = sheet.getLastRow() + 1;
    }
    
    // Column mapping (1-indexed)
    sheet.getRange(targetRow, 1).setValue(data.license_key);          // A: license_key
    sheet.getRange(targetRow, 2).setValue(data.status);               // B: status
    // C: expiry_date (preserve existing or set from data)
    sheet.getRange(targetRow, 4).setValue(data.hw1 || "");            // D: hw_component_1
    sheet.getRange(targetRow, 5).setValue(data.hw2 || "");            // E: hw_component_2
    sheet.getRange(targetRow, 6).setValue(data.hw3 || "");            // F: hw_component_3
    // G: transfer_count (increment if transfer, else preserve)
    sheet.getRange(targetRow, 8).setValue(data.licensee_name || "");  // H: licensee_name
    sheet.getRange(targetRow, 9).setValue(data.licensee_email || ""); // I: licensee_email
    sheet.getRange(targetRow, 10).setValue(data.license_tier || "standard"); // J: license_tier
    sheet.getRange(targetRow, 11).setValue(new Date());               // K: last_validated
    
    // Increment transfer_count if this is a transfer operation
    if (data.is_transfer) {
      var currentCount = sheet.getRange(targetRow, 7).getValue() || 0;
      sheet.getRange(targetRow, 7).setValue(currentCount + 1);
    }
    
    return ContentService.createTextOutput("OK: License updated");
  } catch (error) {
    return ContentService.createTextOutput("ERROR: " + error.toString());
  }
}
```

---

## Phase 3: Python Backend Enhancements

### 3.1 Transfer Limits Enforcement
**File:** `src/licensing/license_manager.py`

```python
def request_transfer(self, license_key: str) -> Tuple[bool, str]:
    # Check transfer limit BEFORE allowing transfer
    record = self._fetch_license_row() or {}
    current_count = record.get("transfer_count", 0)
    max_transfers = int(config.get("licensing.max_transfers", 3))
    
    if current_count >= max_transfers:
        msg = f"Transfer limit reached ({current_count}/{max_transfers}). Contact support."
        return False, msg
    
    # ... rest of existing transfer logic
```

### 3.2 Better Error Messages
**File:** `src/licensing/license_client.py`

```python
SUPPORT_EMAIL = "support@water-balance.com"
SUPPORT_PHONE = "+27 123 456 7890"

# In validate() method:
if status == 'revoked':
    return {
        "valid": False,
        "status": "revoked",
        "message": f"License revoked. Contact {SUPPORT_EMAIL} or {SUPPORT_PHONE}"
    }

if expiry_date and expiry_date < dt.date.today():
    return {
        "valid": False,
        "status": "expired",
        "message": f"License expired on {expiry_date.isoformat()}. Renew at {SUPPORT_EMAIL}"
    }
```

### 3.3 Expiry Warning System
**File:** `src/licensing/license_manager.py`

```python
def validate_startup(self) -> Tuple[bool, str, Optional[dt.date]]:
    # ... existing validation ...
    
    # Check expiry and warn if approaching
    expiry = record.get("expiry_date")
    expiry_date = None
    if expiry:
        try:
            expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d").date()
            days_remaining = (expiry_date - dt.date.today()).days
            
            if days_remaining < 0:
                return False, "License expired", None
            elif 0 < days_remaining <= 7:
                logger.warning(f"⚠️ License expires in {days_remaining} days!")
                # Show non-blocking warning in UI
        except Exception:
            pass
    
    return True, "License valid", expiry_date
```

### 3.4 Audit Logging
**File:** `src/database/schema.py`

```python
def _create_license_audit_log_table(self, cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS license_audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_id INTEGER,
            event_type TEXT NOT NULL,
            event_details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (license_id) REFERENCES license_info(license_id)
        )
    """)
```

**File:** `src/licensing/license_manager.py`

```python
def _log_security_event(self, license_id: int, event_type: str, details: str):
    try:
        db.execute_insert(
            "INSERT INTO license_audit_log (license_id, event_type, event_details) VALUES (?, ?, ?)",
            (license_id, event_type, details)
        )
    except Exception as exc:
        logger.warning(f"Failed to log security event: {exc}")
```

### 3.5 Tier-Based Check Intervals
**File:** `config/app_config.yaml`

```yaml
licensing:
  check_intervals:
    trial: 1        # Hourly for trial
    standard: 24    # Daily for standard
    premium: 168    # Weekly for premium (more trust)
  max_transfers: 3
  offline_grace_days: 7
```

**File:** `src/licensing/license_manager.py`

```python
def __init__(self):
    # ... existing ...
    self.check_intervals = config.get("licensing.check_intervals", {
        "trial": 1,
        "standard": 24,
        "premium": 168
    })

def _get_check_interval_for_tier(self, tier: str) -> int:
    return self.check_intervals.get(tier, 24)  # Default 24h
```

### 3.6 Offline Grace Period
**File:** `src/licensing/license_manager.py`

```python
def validate_startup(self) -> Tuple[bool, str, Optional[dt.date]]:
    # ... after checking last_online_check ...
    
    if needs_online:
        try:
            online_ok, online_msg = self._validate_online(record)
            if not online_ok:
                # Check if still within grace period
                grace_until = record.get("offline_grace_until")
                if grace_until:
                    grace_date = dt.datetime.fromisoformat(grace_until)
                    if dt.datetime.utcnow() < grace_date:
                        logger.warning("Offline mode - grace period active")
                        return True, "License valid (offline grace)", expiry_date
                
                return False, online_msg, None
        except NetworkError:
            # Allow offline if grace period is valid
            grace_until = record.get("offline_grace_until")
            if grace_until:
                grace_date = dt.datetime.fromisoformat(grace_until)
                if dt.datetime.utcnow() < grace_date:
                    logger.info("Network unavailable - using offline grace period")
                    return True, "License valid (offline mode)", expiry_date
            raise
```

---

## Phase 4: Professional License Dialog (ttkbootstrap)

### New UI Design Features
1. **Modern ttkbootstrap theme** matching app theme (arc/flatly/litera)
2. **Icon indicators** for status (✅ valid, ❌ revoked, ⚠️ expiring)
3. **Progress indicator** during validation
4. **Real-time field validation** with visual feedback
5. **Expiry countdown** display
6. **Transfer counter** visualization
7. **Smooth transitions** and animations
8. **Responsive layout** adapting to content

### File Structure
```
src/ui/license_dialog_pro.py  (new professional dialog)
src/ui/components/
  ├── license_status_card.py  (status display component)
  ├── license_form_fields.py  (validated input fields)
  └── license_progress.py     (validation progress indicator)
```

---

## Phase 5: Implementation Checklist

### Backend
- [ ] Update `app_config.yaml` with tier intervals and max_transfers
- [ ] Add `license_audit_log` table to schema
- [ ] Implement transfer limits enforcement
- [ ] Add better error messages with support contact
- [ ] Implement expiry warning (7-day threshold)
- [ ] Add security audit logging
- [ ] Implement tier-based check intervals
- [ ] Add offline grace period logic
- [ ] Update `sync_activation_to_sheet()` to include `is_transfer` flag and `last_validated`

### Google Sheets
- [ ] Create professionally formatted sheet template (Excel)
- [ ] Apply header styling (bold, dark blue, frozen)
- [ ] Set up conditional formatting rules (5 status colors)
- [ ] Configure data validation dropdowns
- [ ] Set column widths for readability
- [ ] Add sample license entries for testing

### Apps Script
- [ ] Update doPost() with 11-column mapping
- [ ] Add `last_validated` timestamp update
- [ ] Handle transfer_count increment logic
- [ ] Add error handling and logging
- [ ] Deploy new version and update webhook URL

### UI (ttkbootstrap)
- [ ] Create modern license dialog with ttkbootstrap
- [ ] Add status indicator icons
- [ ] Implement validation progress spinner
- [ ] Add expiry countdown display
- [ ] Add transfer counter visualization
- [ ] Implement smooth form transitions
- [ ] Add real-time field validation
- [ ] Add responsive layout
- [ ] Match app's existing theme

### Testing
- [ ] Test transfer limit enforcement
- [ ] Test expiry warnings (7 days, 1 day, expired)
- [ ] Test offline grace period scenarios
- [ ] Test tier-based validation intervals
- [ ] Test audit log entries
- [ ] Test Sheet conditional formatting
- [ ] Test Apps Script webhook with all fields
- [ ] Test professional dialog on different screen sizes

---

## Support Information
**Email:** support@water-balance.com  
**Phone:** +27 123 456 7890  
**Website:** https://water-balance.com/support

---

## Expected Outcomes
✅ Professional-grade license management system  
✅ Enterprise-ready Google Sheets with visual indicators  
✅ Modern, intuitive UI matching app design  
✅ Comprehensive security and audit trail  
✅ Flexible licensing tiers with different validation rules  
✅ Better user experience with warnings and grace periods  
✅ Production-ready error handling and support contact info

