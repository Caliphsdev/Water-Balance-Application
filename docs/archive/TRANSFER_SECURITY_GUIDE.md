# Transfer Security Guide - Protecting Against License Theft

**Purpose**: Understand how the 5-layer transfer protection prevents unauthorized license transfers and protects legitimate users.

---

## The Problem: License Theft Scenario

### Without Protection (Old System)
```
1. User A activates license on Computer A (LEGITIMATE USER)
2. Thief steals license key (data breach, phishing, etc.)
3. Thief enters license on Computer B
4. System detects hardware mismatch, offers "Transfer License" button
5. Thief clicks "Transfer" → SUCCESS ✅
6. License now bound to Computer B (THIEF'S COMPUTER)
7. User A loses access on Computer A (LEGITIMATE USER LOCKED OUT!)
```

**Result**: Legitimate user can't use their own license, thief has full access.

---

## The Solution: 5-Layer Anti-Theft Protection

### Layer 1: Transfer Limit ⏱️
**What it does**: Limits total transfers to 3 across license lifetime  
**How it helps**: Prevents unlimited bouncing between computers  
**Example**:
- Transfer 1: User A upgrades from Computer A → Computer A2 ✅
- Transfer 2: User A upgrades from Computer A2 → Computer A3 ✅
- Transfer 3: User A upgrades from Computer A3 → Computer A4 ✅
- Transfer 4: BLOCKED ❌ (contact support)

**Thief impact**: If thief uses all 3 transfers, license becomes stuck on their hardware (they can't use it elsewhere, but neither can legitimate user)

---

### Layer 2: Email Verification ✉️ **(CRITICAL ANTI-THEFT)**
**What it does**: Requires registered email address to approve transfer  
**How it helps**: Only the person who knows the registered email can transfer  
**Example**:

#### Legitimate Transfer ✅
```
1. User A enters license on new computer
2. System detects hardware mismatch
3. Dialog shows: "Enter your registered email to confirm transfer"
4. User A enters: user@company.com (CORRECT EMAIL)
5. System checks: remote sheet has registered_email = user@company.com
6. ✅ Email matches → Transfer allowed
```

#### Thief Attempt ❌
```
1. Thief enters stolen license on Computer B
2. System detects hardware mismatch
3. Dialog shows: "Enter your registered email to confirm transfer"
4. Thief enters: thief@hacker.com (WRONG EMAIL)
5. System checks: remote sheet has registered_email = user@company.com
6. ❌ Email mismatch → Transfer BLOCKED
7. Security alert sent to user@company.com
```

**Why this works**: Thief doesn't know the registered email address (it's not stored in local database, only on remote Google Sheets)

---

### Layer 3: Owner Notification 📧 **(EARLY WARNING SYSTEM)**
**What it does**: Sends immediate email to registered owner before ANY transfer  
**How it helps**: User A gets notified even if thief knows the email  
**Example**:

#### Notification Email Content
```
Subject: [SECURITY ALERT] License Transfer Requested

Dear User A,

A license transfer has been requested for your Water Balance Application license.

LICENSE DETAILS:
- License Key: WB-xxxx-xxxx-xxxx
- Current Hardware: Computer A (CPU: GenuineIntel-XXXX, Motherboard: ASUSTeK-XXXX)
- New Hardware: Computer B (CPU: AuthenticAMD-YYYY, Motherboard: Gigabyte-YYYY)
- Transfer Date: 2025-01-10 14:30:00
- IP Address: 192.168.1.100

IF YOU AUTHORIZED THIS TRANSFER:
No action needed. Your license will be transferred in 24 hours.

IF YOU DID NOT AUTHORIZE THIS:
IMMEDIATE ACTION REQUIRED!
1. Reply to this email with "REVOKE TRANSFER"
2. Call support: +27 123 456 7890
3. We will revoke the transfer and secure your account

You have 24 hours to report unauthorized transfers.

Support Team
support@water-balance.com
```

**How User A is protected**:
- User A sees the new hardware details (CPU/Motherboard serials)
- User A recognizes it's NOT their computer
- User A contacts support within 24 hours
- Support revokes the transfer and blocks the thief's hardware

---

### Layer 4: Server-Side IP Logging 🌐
**What it does**: Records IP address of every transfer request on Google Sheets  
**How it helps**: Creates forensic trail for investigations  
**Example**:

#### Google Sheets Transfer Log
| Timestamp | License Key | Old Hardware | New Hardware | IP Address | Email Used |
|-----------|-------------|--------------|--------------|------------|------------|
| 2025-01-10 14:30 | WB-1234 | Computer A | Computer B | 197.85.1.50 (South Africa) | user@company.com | ← Legitimate (same country)
| 2025-01-10 15:45 | WB-1234 | Computer B | Computer C | 103.45.2.10 (China) | user@company.com | ← SUSPICIOUS (geo-jump)

**Red flags for support team**:
- Geographic impossibility (South Africa → China in 1 hour)
- Multiple rapid transfers (1 hour apart)
- IP addresses from unusual countries

---

### Layer 5: Security Event Audit Log 📝
**What it does**: Logs all transfer attempts (successful + failed) locally  
**How it helps**: User A can review all attempts in UI  
**Example**:

#### Audit Log in Database (license_audit_log table)
```
Event: TRANSFER_REQUESTED
Timestamp: 2025-01-10 14:30:00
License: WB-1234-5678-90AB
Old Hardware: Computer A (Intel-1234...)
New Hardware: Computer B (AMD-5678...)
Email: user@company.com
Result: SUCCESS
IP: 197.85.1.50

Event: TRANSFER_REQUESTED
Timestamp: 2025-01-10 15:45:00
License: WB-1234-5678-90AB
Old Hardware: Computer B (AMD-5678...)
New Hardware: Computer C (AMD-9999...)
Email: thief@hacker.com
Result: FAILED - EMAIL_MISMATCH
IP: 103.45.2.10
```

**User A can**:
- Click "View Audit Log" in UI
- See ALL transfer attempts (even failed ones)
- Recognize suspicious patterns
- Report to support

---

## Complete Attack Scenario with Protections

### Scenario: Thief steals license database file

#### Step 1: Thief Gets License Key
```
Thief: Hacks into User A's computer, copies water_balance.db file
Thief: Extracts license key: WB-1234-5678-90AB
Thief: Thinks: "I'll use this on my computer!"
```

#### Step 2: Thief Tries to Activate on Computer B
```
Thief: Launches app on Computer B, enters license key
System: Detects hardware mismatch (Computer B ≠ Computer A)
System: Shows dialog: "Hardware mismatch. Transfer license to this computer?"
Thief: Clicks "Transfer License"
System: Shows popup: "Enter your registered email to confirm transfer"
```

#### Step 3: Protection 2 Kicks In (Email Verification)
```
Thief: Enters email: thief@hacker.com
System: Calls request_transfer(license_key, "thief@hacker.com")
System: Checks Google Sheets → registered_email = "user@company.com"
System: Email mismatch detected! ❌
System: Transfer BLOCKED
System: Returns error: "Invalid email. Transfer denied."
```

#### Step 4: Protection 3 Kicks In (Owner Notification)
```
System: Sends SECURITY ALERT email to user@company.com
Email Subject: "SUSPICIOUS TRANSFER ATTEMPT BLOCKED"
Email Body:
  "Someone tried to transfer your license using incorrect email.
   Hardware Details: Computer B (CPU: AMD-9999, MB: Gigabyte-ZZZZ)
   Email Used: thief@hacker.com ← NOT YOUR EMAIL
   IP Address: 103.45.2.10 (China)
   Time: 2025-01-10 15:45:00
   
   ACTION REQUIRED: Change your license password immediately.
   Call support: +27 123 456 7890"
```

#### Step 5: User A Gets Protected
```
User A: Checks email, sees SECURITY ALERT
User A: "Wait, I didn't try to transfer! And I'm not in China!"
User A: Calls support immediately
Support: Reviews server logs (Layer 4 - IP Logging)
Support: Sees China IP attempting transfer
Support: Revokes license key WB-1234-5678-90AB
Support: Issues new key: WB-NEW-KEY-HERE
Support: Blocks thief's hardware fingerprint
User A: Activates new key on Computer A ✅
Thief: Can never use old or new key (hardware blocked) ❌
```

---

## Why Layer 2 (Email) is the Critical Protection

### Attack Vector Analysis

#### If Email Verification Didn't Exist
```
Thief: Gets license key (easy - just copy database file)
Thief: Transfers to Computer B (no email required)
Result: Thief wins ❌, User A locked out
```

#### With Email Verification
```
Thief: Gets license key (easy - just copy database file)
Thief: Tries to transfer to Computer B
System: "Enter registered email"
Thief: Doesn't know the email (not in local database)
Thief: Guesses random emails → ALL REJECTED ❌
Thief: Can't transfer, gives up
Result: User A protected ✅
```

### Why Thief Can't Get the Email
- Email is stored ONLY on Google Sheets (remote server)
- Local database (water_balance.db) has: license_key, hardware_id, expiry_date
- Local database does NOT have: registered_email, user_name, phone
- Thief would need to hack Google Sheets (much harder than stealing local file)

---

## Configuration Required

### 1. Add SMTP Settings to app_config.yaml
```yaml
licensing:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  smtp_user: support@water-balance.com
  smtp_password: 'your-app-password-here'  # Gmail App Password
  support_email: support@water-balance.com
  support_phone: +27 123 456 7890
```

### 2. Get Gmail App Password (if using Gmail SMTP)
```
1. Go to Google Account Settings
2. Security → 2-Step Verification (enable if not already)
3. Security → App Passwords
4. Select app: Mail
5. Select device: Other (Water Balance App)
6. Generate password (16 characters)
7. Copy password to app_config.yaml → smtp_password
```

### 3. Test Email Sending
```python
# Run this in Python console to test SMTP
from src.licensing.license_manager import LicenseManager
manager = LicenseManager()
manager._send_transfer_notification(
    email="your@email.com",
    name="Test User",
    new_hardware="Test Hardware",
    suspicious=False
)
# Check your inbox for email
```

---

## UI Flow for Transfers (Updated)

### Before (No Email Protection)
```
1. User enters license key
2. System: "Hardware mismatch. Transfer?"
3. User clicks "Yes"
4. Transfer happens immediately
```

### After (With Email Protection)
```
1. User enters license key
2. System: "Hardware mismatch. Transfer?"
3. User clicks "Yes"
4. Popup appears: "Enter your registered email to confirm transfer"
5. User types email
6. System validates email against Google Sheets
7a. If correct → Transfer proceeds, notification sent
7b. If wrong → Transfer blocked, security alert sent
```

---

## Testing the Protection

### Test 1: Legitimate Transfer (Should Work)
```
1. Activate license on Computer A with email: user@company.com
2. Record hardware ID from database
3. Move to Computer B (different hardware)
4. Enter same license key
5. When prompted for email, enter: user@company.com (CORRECT)
6. ✅ Transfer should succeed
7. Check email for notification
```

### Test 2: Thief Attempt (Should Fail)
```
1. Have license activated on Computer A with email: user@company.com
2. On Computer B, enter same license key
3. When prompted for email, enter: wrong@email.com (WRONG)
4. ❌ Transfer should fail with "Invalid email"
5. Check user@company.com inbox for security alert
```

### Test 3: No Email Provided (Should Fail)
```
1. On Computer B, enter license key
2. When prompted for email, leave blank
3. ❌ Transfer should fail with "Email required"
```

### Test 4: Transfer Limit (Should Fail)
```
1. Transfer license 3 times (use up all transfers)
2. Try 4th transfer with correct email
3. ❌ Should fail with "Transfer limit reached"
```

---

## Support Workflow for Unauthorized Transfers

### User Reports Theft
```
User A: "I got an email about a transfer I didn't authorize!"
Support: "Let me check the logs..."
Support: [Checks Google Sheets transfer_history]
Support: "I see the attempt. IP: 103.45.2.10 (China), Email: wrong@email.com"
Support: "This was blocked automatically. Your license is safe."
Support: "Would you like us to issue a new license key for extra security?"
```

### User A Wants New Key
```
Support: Revokes old key WB-1234-5678-90AB
Support: Issues new key WB-NEW-KEY-HERE
Support: Updates Google Sheets:
  - Old key: status = REVOKED, reason = "Security - unauthorized attempt"
  - New key: status = ACTIVE, registered_email = user@company.com
Support: Sends email with new key to user@company.com
User A: Activates new key on Computer A ✅
```

---

## Summary

| Layer | Protection | Thief Impact | User A Impact |
|-------|-----------|--------------|---------------|
| 1. Transfer Limit | Max 3 transfers | Limits damage | Prevents unlimited theft |
| 2. **Email Verification** | Must know registered email | **CAN'T TRANSFER** ❌ | **Fully protected** ✅ |
| 3. Owner Notification | Alert before transfer | User A gets early warning | Can report immediately |
| 4. IP Logging | Records location | Forensic evidence | Support can investigate |
| 5. Audit Log | Local + remote logs | Can't hide attempts | Can review all activity |

**Bottom line**: Layer 2 (Email Verification) is the **kill switch** for thieves. Without the registered email, they can't transfer the license, period.

---

## Next Steps

1. **Add SMTP configuration** to app_config.yaml (see Configuration section)
2. **Test email sending** (see Testing section)
3. **Update UI** to prompt for email during transfer (currently code is ready, UI needs update)
4. **Train users** on what to do if they get a security alert email

---

**Questions? See**:
- [LICENSING_INDEX.md](LICENSING_INDEX.md) - Full feature documentation
- [ANTIPIRACY_TECHNICAL_DETAILS.md](ANTIPIRACY_TECHNICAL_DETAILS.md) - Technical details
- [LICENSING_QUICK_TEST_GUIDE.md](LICENSING_QUICK_TEST_GUIDE.md) - Quick testing guide
