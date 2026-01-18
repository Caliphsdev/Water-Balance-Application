# Anti-Piracy Licensing: Quick Reference

## What's Running

✅ **License validation** via public Google Sheets (free, no auth)  
✅ **Hardware binding** prevents software piracy  
✅ **Webhook write-back** logs activations to Sheet  
✅ **SQLite caching** enables offline operation

---

## For End Users

**First Time**:
```
1. Launch app
2. License dialog appears
3. Enter: Key (ABC-123-XYZ), Name, Email
4. Click "Activate"
5. Done! App proceeds to dashboard
```

**Ongoing**:
- App validates license locally every 24 hours
- Online check required if 24h has passed
- Hardware mismatch = error with "Request Transfer" option

---

## For Admins

### Create License
1. Open [Google Sheet](https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/)
2. Add row: `ABC-123-XYZ | active | | 365 | | | | Name | Email | 2025-01-10 | 0 | |`
3. Hardware fields auto-filled on first user activation

### Revoke License
1. Find row in Sheet
2. Change status to "revoked" or set expiry_date to past date
3. Next activation attempt: rejected

### View Activation History
- **Sheet**: licensee_name, licensee_email, hw_component_1/2/3 (hashes)
- **SQLite** (`data/water_balance.db`): license_validation_log table shows all checks with timestamps

---

## Config (`config/app_config.yaml`)

```yaml
licensing:
  sheet_url: "https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/edit?usp=sharing"
  sheet_name: "licenses"
  webhook_url: "https://script.google.com/macros/s/AKfycbzMduOQtHmZXdrIposfeD1j2y7E1tXvgp1wXkfKAQGoCHwr4UqDMzvwToDtEf4Or_cI/exec"
  hardware_match_threshold: 2        # 2/3 components must match
  check_interval_hours: 24           # Re-validate online every 24h
  offline_grace_days: 0              # No offline grace
  request_timeout: 10
```

---

## How It Works

### Online Validation
1. User enters license key
2. App fetches public Sheet CSV
3. Validates key exists + status is active + not expired
4. Auto-binds hardware (MAC + CPU + board hash)
5. Saves to SQLite
6. POSTs activation data to webhook (audit trail)

### Offline Operation
1. Subsequent startups use SQLite cache
2. Hardware fuzzy-match (2/3 components required)
3. Online check skipped if done within 24h
4. First startup or 24h+ elapsed: forces online validation

### Hardware Transfer
User on new device:
1. Same license key triggers mismatch error
2. User clicks "Request Transfer"
3. App rebinds hardware + increments transfer_count
4. Sheet updated

---

## Testing

### Did it work?
```bash
# Check SQLite
sqlite3 data/water_balance.db "SELECT license_key, licensee_name, activated_at FROM license_info LIMIT 1;"

# Check Sheet (anyone can read)
# Visit: https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/
```

### Troubleshooting
- **"License not found"** → Check key spelling in Sheet
- **"Hardware mismatch"** → Click "Request Transfer" to rebind
- **"Online validation failed"** → Check internet connection / Google Sheet accessibility
- **Webhook not posting** → Check logs (`logs/` folder), webhook is best-effort (non-blocking)

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| License Read | Public Google Sheets API (CSV export) | Validate key, status, expiry |
| License Write | Apps Script Webhook (personal account) | Log activation + hardware |
| Local Cache | SQLite | Fast startup, offline operation |
| Hardware ID | SHA-256 hashing (MAC + CPU + board) | Prevent copying, hardware binding |
| Fuzzy Match | 2/3 component matching | Allow minor hardware changes |

---

## Security Notes

✅ **Prevents**: License sharing, indefinite use, bulk activation without audit  
⚠️ **Assumes**: Internet available for initial activation + periodic validation  
⚠️ **Limitations**: SQLite not encrypted, fuzzy match (not strict), periodic re-validation only (not real-time)

---

## Key URLs

- **Google Sheet**: https://docs.google.com/spreadsheets/d/1vWWDEjVX0d-96AqfcbM_AaOEmgIkRxgu2NFJ723LfcM/
- **Webhook**: https://script.google.com/macros/s/AKfycbzMduOQtHmZXdrIposfeD1j2y7E1tXvgp1wXkfKAQGoCHwr4UqDMzvwToDtEf4Or_cI/exec
- **SQLite DB**: `data/water_balance.db`
- **Config**: `config/app_config.yaml`

---

## Example License Keys

| Key | Status | User | Notes |
|-----|--------|------|-------|
| ABC-123-XYZ | active | Test User | Tested + verified |

---

*See full documentation: [WEBHOOK_LICENSING_IMPLEMENTATION.md](WEBHOOK_LICENSING_IMPLEMENTATION.md)*
