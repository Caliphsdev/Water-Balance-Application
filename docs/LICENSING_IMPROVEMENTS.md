# Water Balance License System - Improvement Recommendations

**Date:** January 22, 2026  
**Status:** Proposed Enhancements  
**Current System:** Google Sheets + Apps Script webhook + Python client

---

## Current Architecture Analysis

### ✅ **Strengths:**
- Simple, no dedicated license server needed
- Google Sheets provides built-in UI for license management
- Webhook pattern allows Python app to validate remotely
- Hardware fingerprinting prevents unauthorized transfers
- Offline grace period (7 days default)

### ⚠️ **Weaknesses Identified:**
1. **No authentication on webhook** → Anyone with URL can send POST requests
2. **No audit trail** → Can't track who validated when, or failed attempts
3. **Transfer tracking incomplete** → Only counter, no timestamp/reason
4. **Expiry date manual** → Admin must set manually in sheet
5. **No request rate limiting** → Could be abused for DoS
6. **Hardware change detection basic** → Needs better heuristics
7. **No license revocation notification** → App only checks on interval
8. **Error responses generic** → Hard to debug issues
9. **No batch validation** → One request per validation check

---

## Recommended Improvements (Priority Order)

### **🔥 CRITICAL (Implement First)**

#### 1. Add API Key Authentication to Webhook
**Problem:** Webhook URL is public; anyone can POST fake data  
**Solution:** Require API key in request headers

**Google Apps Script Update:**
```javascript
function doPost(e) {
  // SECURITY: Validate API key before processing
  var apiKey = e.parameter.api_key || (e.postData.params && e.postData.params.api_key);
  var validKey = PropertiesService.getScriptProperties().getProperty('API_KEY');
  
  if (!apiKey || apiKey !== validKey) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "UNAUTHORIZED",
      message: "Invalid or missing API key"
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  // ... rest of existing code
}
```

**Python Side (license_client.py):**
```python
# In config/app_config.yaml add:
# licensing:
#   api_key: "your-secret-api-key-here"

def _validate_online(self):
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': config.get('licensing.api_key')  # Add to all requests
    }
    response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
```

**Setup Steps:**
1. In Google Apps Script editor: File → Project properties → Script properties
2. Add property: `API_KEY` = `your-secret-key-here` (generate random 32-char string)
3. Update Python config with same key
4. Test with invalid key to verify rejection

---

#### 2. Implement Audit Trail (Separate Sheet)
**Problem:** No record of validation attempts, hardware changes, or transfer history  
**Solution:** Log every validation attempt to "audit_log" sheet

**New Sheet Structure: `audit_log`**
| Column | Name | Description |
|--------|------|-------------|
| A | timestamp | Auto-timestamp of validation |
| B | license_key | License key validated |
| C | event_type | `validate`, `activate`, `transfer`, `revoke` |
| D | status | `success`, `failure` |
| E | hw_component_1 | Hardware at time of validation |
| F | hw_component_2 | Hardware at time of validation |
| G | hw_component_3 | Hardware at time of validation |
| H | ip_address | Requester IP (if available) |
| I | error_message | If validation failed, why? |
| J | user_email | Licensee email |

**Google Apps Script Enhancement:**
```javascript
function logAuditEvent(licenseKey, eventType, status, hwComponents, errorMsg, userEmail) {
  var auditSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("audit_log");
  if (!auditSheet) {
    // Create audit sheet if doesn't exist
    auditSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet("audit_log");
    auditSheet.appendRow(["timestamp", "license_key", "event_type", "status", 
                          "hw1", "hw2", "hw3", "ip_address", "error_message", "user_email"]);
  }
  
  auditSheet.appendRow([
    new Date(),
    licenseKey,
    eventType,
    status,
    hwComponents.hw1 || "",
    hwComponents.hw2 || "",
    hwComponents.hw3 || "",
    "", // IP address (not available in Apps Script, but placeholder)
    errorMsg || "",
    userEmail || ""
  ]);
}

// Call in doPost after validation:
logAuditEvent(data.license_key, data.event_type || "validate", "success", 
              {hw1: data.hw1, hw2: data.hw2, hw3: data.hw3}, null, data.licensee_email);
```

**Benefits:**
- Track all validation attempts (success + failures)
- Identify suspicious patterns (multiple failed attempts)
- Debug customer issues ("When did this hardware change?")
- Compliance audit trail

---

#### 3. Enhanced Transfer Tracking with History
**Problem:** Only tracks transfer count; no date/reason/previous hardware  
**Solution:** Create "transfer_history" sheet with detailed records

**New Sheet: `transfer_history`**
| Column | Name | Description |
|--------|------|-------------|
| A | transfer_date | When transfer occurred |
| B | license_key | License key |
| C | old_hw1 | Previous hardware component 1 |
| D | old_hw2 | Previous hardware component 2 |
| E | old_hw3 | Previous hardware component 3 |
| F | new_hw1 | New hardware component 1 |
| G | new_hw2 | New hardware component 2 |
| H | new_hw3 | New hardware component 3 |
| I | transfer_reason | `user_requested`, `auto_recovery`, `admin_reset` |
| J | approved_by | Admin email if manual approval |

**Google Apps Script Function:**
```javascript
function recordTransfer(licenseKey, oldHW, newHW, reason, approvedBy) {
  var transferSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("transfer_history");
  if (!transferSheet) {
    transferSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet("transfer_history");
    transferSheet.appendRow(["transfer_date", "license_key", "old_hw1", "old_hw2", "old_hw3",
                             "new_hw1", "new_hw2", "new_hw3", "transfer_reason", "approved_by"]);
  }
  
  transferSheet.appendRow([
    new Date(),
    licenseKey,
    oldHW.hw1, oldHW.hw2, oldHW.hw3,
    newHW.hw1, newHW.hw2, newHW.hw3,
    reason,
    approvedBy || "system"
  ]);
}
```

---

### **⚡ HIGH PRIORITY**

#### 4. Auto-Calculate Expiry Date on Activation
**Problem:** Expiry date manually set; prone to errors  
**Solution:** Auto-set based on license tier when first activated

**License Tier Durations:**
- `trial`: 30 days
- `standard`: 365 days (1 year)
- `premium`: 730 days (2 years)
- `lifetime`: 36500 days (100 years)

**Google Apps Script Logic:**
```javascript
function calculateExpiryDate(licenseTier, activationDate) {
  var daysMap = {
    "trial": 30,
    "standard": 365,
    "premium": 730,
    "lifetime": 36500
  };
  
  var days = daysMap[licenseTier] || 365; // Default to standard
  var expiry = new Date(activationDate);
  expiry.setDate(expiry.getDate() + days);
  return expiry;
}

// In doPost, when creating new license:
if (targetRow === sheet.getLastRow() + 1) {
  // New activation - set expiry
  var expiryDate = calculateExpiryDate(data.license_tier || "standard", new Date());
  sheet.getRange(targetRow, 3).setValue(expiryDate); // Column C: expiry_date
}
```

**Python Side - Request Expiry Extension:**
```python
def request_expiry_extension(self, license_key: str, extension_days: int = 365) -> bool:
    """Request license expiry extension (admin approval required)."""
    payload = {
        'license_key': license_key,
        'action': 'extend_expiry',
        'extension_days': extension_days,
        'requested_by': self.licensee_email,
        'request_date': datetime.now().isoformat()
    }
    # Send to webhook; admin reviews in sheet
```

---

#### 5. Enhanced Hardware Change Detection
**Problem:** Simple 2-component threshold; needs smarter heuristics  
**Solution:** Weighted scoring + component type importance

**Python Enhancement (license_manager.py):**
```python
def _calculate_hardware_similarity(self, hw1: dict, hw2: dict) -> float:
    """
    Calculate similarity score between two hardware fingerprints (0.0 = different, 1.0 = identical).
    
    Weighted by component importance:
    - Motherboard UUID: 40% (most stable)
    - CPU serial: 30% (semi-stable)
    - MAC address: 20% (changes on network card replacement)
    - Disk serial: 10% (changes on drive replacement)
    """
    weights = {
        'motherboard_uuid': 0.40,
        'cpu_serial': 0.30,
        'mac_address': 0.20,
        'disk_serial': 0.10
    }
    
    score = 0.0
    for component, weight in weights.items():
        if hw1.get(component) and hw2.get(component):
            if hw1[component] == hw2[component]:
                score += weight
    
    return score

def _is_hardware_match(self, current_hw: dict, stored_hw: dict) -> bool:
    """
    Determine if hardware matches (ENHANCED LOGIC).
    
    Returns True if similarity >= 60% (allows 1-2 minor component changes).
    """
    similarity = self._calculate_hardware_similarity(current_hw, stored_hw)
    logger.debug(f"Hardware similarity score: {similarity * 100:.1f}%")
    
    # Threshold: 60% similarity = pass (allows minor component changes)
    # Below 60% = likely different machine, requires transfer approval
    return similarity >= 0.60
```

**Benefits:**
- Motherboard change = definite transfer needed
- RAM upgrade = doesn't trigger transfer (not fingerprinted)
- Network card replacement = minor change, doesn't block
- Complete machine change = blocks and requires transfer

---

#### 6. Real-Time Revocation via Webhook Polling
**Problem:** App only checks license on interval (1-24 hours); revoked licenses work until next check  
**Solution:** Add "instant revoke" mechanism with smaller poll interval for critical checks

**Google Sheet Enhancement:**
Add column `L: revoked_at` (timestamp when license revoked)

**Python Side - Check Revocation on Critical Actions:**
```python
def check_instant_revocation(self) -> bool:
    """
    Quick revocation check (lightweight API call, no full validation).
    Called before critical operations (save calculation, export data).
    
    Returns True if license is still active, False if revoked.
    """
    try:
        response = requests.get(
            f"{config.get('licensing.sheet_url')}/values/licenses!A:L",
            params={'key': config.get('licensing.api_key')},
            timeout=3  # Fast timeout
        )
        
        # Find row with our license key, check revoked_at column
        data = response.json().get('values', [])
        for row in data[1:]:  # Skip header
            if row[0] == self.license_key:
                revoked_at = row[11] if len(row) > 11 else None
                if revoked_at:
                    logger.warning(f"License revoked at {revoked_at}")
                    return False
        return True
    except Exception as e:
        logger.error(f"Revocation check failed: {e}")
        return True  # Fail open (grace period handles offline)
```

**Usage:**
```python
# In src/utils/water_balance_calculator.py, before save:
def save_calculation(self, calculation_date):
    license_mgr = get_license_manager()
    if not license_mgr.check_instant_revocation():
        raise LicenseError("License has been revoked. Contact support.")
    # ... proceed with save
```

---

### **🔧 MEDIUM PRIORITY**

#### 7. Batch Validation for Multi-User Installs
**Problem:** Each validation = 1 API call; inefficient for org licenses  
**Solution:** Support batch validation in webhook

**Google Apps Script Enhancement:**
```javascript
function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  
  // Support both single and batch validation
  if (data.batch && Array.isArray(data.licenses)) {
    return handleBatchValidation(data.licenses);
  } else {
    return handleSingleValidation(data);
  }
}

function handleBatchValidation(licenseKeys) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("licenses");
  var results = [];
  
  licenseKeys.forEach(function(key) {
    // Validate each license, return status
    var row = findLicenseRow(sheet, key);
    if (row) {
      results.push({
        license_key: key,
        status: sheet.getRange(row, 2).getValue(),
        expiry_date: sheet.getRange(row, 3).getValue()
      });
    } else {
      results.push({license_key: key, error: "NOT_FOUND"});
    }
  });
  
  return ContentService.createTextOutput(JSON.stringify({
    batch: true,
    results: results
  })).setMimeType(ContentService.MimeType.JSON);
}
```

---

#### 8. License Tier-Specific Features
**Problem:** All tiers get same features; no differentiation  
**Solution:** Add feature flags per tier in sheet

**New Sheet Columns (after K):**
| Column | Name | Allowed Values | Description |
|--------|------|----------------|-------------|
| L | max_calculations | integer | Max calculations per month |
| M | export_enabled | boolean | Can export data? |
| N | api_access | boolean | Has API access? |
| O | priority_support | boolean | Priority support ticket queue |

**Python Side - Feature Check:**
```python
def has_feature(self, feature_name: str) -> bool:
    """Check if current license tier includes feature."""
    tier_features = {
        'trial': {
            'max_calculations': 10,
            'export_enabled': False,
            'api_access': False,
            'priority_support': False
        },
        'standard': {
            'max_calculations': 100,
            'export_enabled': True,
            'api_access': False,
            'priority_support': False
        },
        'premium': {
            'max_calculations': 1000,
            'export_enabled': True,
            'api_access': True,
            'priority_support': True
        }
    }
    
    tier = self.license_info.get('license_tier', 'standard')
    return tier_features.get(tier, {}).get(feature_name, False)

# Usage in UI:
if not license_mgr.has_feature('export_enabled'):
    export_button.config(state='disabled', text='Export (Premium Only)')
```

---

### **📈 NICE TO HAVE**

#### 9. License Usage Analytics
**New Sheet: `usage_stats`**
Track monthly usage per license (for billing, compliance)

| Column | Content |
|--------|---------|
| A | month (YYYY-MM) |
| B | license_key |
| C | calculations_count |
| D | exports_count |
| E | api_calls_count |
| F | active_days |

**Python Side - Report Usage:**
```python
def report_monthly_usage(self):
    """Send usage stats to webhook at end of month."""
    stats = {
        'license_key': self.license_key,
        'month': datetime.now().strftime('%Y-%m'),
        'calculations_count': self.db.get_calculations_count_this_month(),
        'exports_count': self.db.get_exports_count_this_month()
    }
    # POST to webhook with action='report_usage'
```

---

## Implementation Roadmap

### **Phase 1: Security (Week 1)**
- [ ] Add API key authentication to webhook
- [ ] Implement request signing/HMAC
- [ ] Test with invalid keys to verify rejection

### **Phase 2: Audit Trail (Week 1)**
- [ ] Create `audit_log` sheet
- [ ] Implement logging in Apps Script
- [ ] Update Python client to send event_type in payloads

### **Phase 3: Transfer Management (Week 2)**
- [ ] Create `transfer_history` sheet
- [ ] Enhanced hardware matching logic
- [ ] Test transfer approval workflow

### **Phase 4: Expiry Automation (Week 2)**
- [ ] Auto-calculate expiry on activation
- [ ] Add expiry extension request mechanism
- [ ] Test tier-based durations

### **Phase 5: Features & Analytics (Week 3)**
- [ ] Tier-specific feature flags
- [ ] Usage analytics tracking
- [ ] Admin dashboard in Google Sheets

---

## Testing Checklist

- [ ] API key rejection works (invalid key → 401 error)
- [ ] Audit log captures all validation attempts
- [ ] Transfer history records hardware changes
- [ ] Expiry dates auto-set correctly for each tier
- [ ] Hardware similarity scoring allows minor changes
- [ ] Revocation check blocks critical operations
- [ ] Feature flags restrict trial users appropriately
- [ ] Batch validation returns all license statuses
- [ ] Usage stats report monthly correctly

---

## Security Best Practices

1. **API Key Storage:**
   - Store in Google Apps Script Project Properties (encrypted at rest)
   - Never commit to Git
   - Rotate every 90 days

2. **HTTPS Only:**
   - Webhook must be HTTPS (Google Apps Script enforces this)
   - Python client validates SSL certificates

3. **Rate Limiting:**
   - Apps Script has built-in 20,000 executions/day limit
   - Add per-license-key rate limit (max 100 validations/hour)

4. **Data Encryption:**
   - Hardware components already hashed (SHA-256)
   - Consider encrypting licensee email in sheet

5. **Audit Retention:**
   - Keep audit logs for 2 years minimum
   - Archive to separate spreadsheet quarterly

---

## Cost Analysis

**Current:** Free (Google Sheets + Apps Script)

**After Improvements:**
- Still free (within Google's quotas)
- Apps Script limits: 20,000 executions/day (enough for 1000 users * 20 checks/day)
- Sheet size: ~5MB limit per sheet (millions of rows supported)

**If Scaling Beyond Google:**
- Consider Firebase Realtime Database ($25/mo for 1GB)
- Or migrate to dedicated license server (Keygen.sh, $50/mo)

---

## Migration Guide

### **Step 1: Backup Current Sheet**
```
File → Make a copy → Rename to "licenses_backup_YYYYMMDD"
```

### **Step 2: Add New Columns**
Add columns L, M, N, O to existing `licenses` sheet (feature flags)

### **Step 3: Create New Sheets**
- Create `audit_log` sheet with headers
- Create `transfer_history` sheet with headers
- Create `usage_stats` sheet with headers

### **Step 4: Deploy Updated Apps Script**
- Copy new script code
- Test with doGet() first
- Deploy as new version
- Update webhook URL in Python config if changed

### **Step 5: Update Python Client**
- Add API key to `app_config.yaml`
- Update `license_client.py` with enhanced hardware matching
- Test activation on dev machine

### **Step 6: Monitor**
- Check audit logs for validation attempts
- Verify transfer tracking works
- Confirm expiry dates auto-set

---

## Support & Troubleshooting

**Common Issues:**

1. **"UNAUTHORIZED" error:**
   - Check API key in config matches Script Properties
   - Verify headers include `X-API-Key`

2. **Audit log not populating:**
   - Check sheet name is exactly "audit_log" (case-sensitive)
   - Verify Apps Script has write permissions

3. **Transfer not recording:**
   - Check `is_transfer: true` in payload
   - Verify transfer_history sheet exists

4. **Expiry date not setting:**
   - Confirm license_tier in payload is valid
   - Check column C is date-formatted

---

## Conclusion

These improvements transform the licensing system from basic validation to a **production-grade license management platform** with:

✅ **Security:** API key auth, audit trails, revocation  
✅ **Automation:** Auto-expiry, transfer tracking, usage stats  
✅ **Compliance:** Full audit trail, transfer history  
✅ **Scalability:** Batch validation, efficient caching  
✅ **Flexibility:** Tier-based features, easy admin control  

**Recommended Priority:** Implement Critical + High priority items first (Phases 1-4), then add Nice-to-Have features based on user feedback.

