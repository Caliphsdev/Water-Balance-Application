// Google Apps Script for Water Balance License Manager Sheet
// Deploy as Web App to get webhook URL for POST requests from Python app
// IMPROVEMENTS: API key auth, audit trail, auto-expiry, usage stats (NO TRANSFER TRACKING)

// ==================== CONFIGURATION ====================
// Set these in Script Properties (File → Project properties → Script properties)
// - API_KEY: Secret key for authenticating webhook requests
// Example: PropertiesService.getScriptProperties().setProperty('API_KEY', 'your-secret-key-here');

function doPost(e) {
  try {
    // Parse the JSON body first
    var data = {};
    if (e.postData && e.postData.contents) {
      try {
        data = JSON.parse(e.postData.contents);
      } catch (parseErr) {
        Logger.log("Failed to parse JSON: " + parseErr);
      }
    }
    
    // SECURITY: Validate API key before processing
    // Check in JSON body first (our Python client sends it here)
    var apiKey = data.api_key || e.parameter.api_key;
    
    var validKey = PropertiesService.getScriptProperties().getProperty('API_KEY');
    
    if (!apiKey || !validKey || apiKey !== validKey) {
      logAuditEvent("UNKNOWN", "validate", "UNAUTHORIZED", {}, "Invalid or missing API key", "");
      return ContentService.createTextOutput(JSON.stringify({
        error: "UNAUTHORIZED",
        message: "Invalid or missing API key"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Handle different actions
    if (data.action === "report_usage") {
      return handleUsageReport(data);
    } else {
      return handleLicenseUpdate(data);
    }
    
  } catch (error) {
    Logger.log("ERROR: " + error.toString());
    return ContentService.createTextOutput(JSON.stringify({
      error: "SERVER_ERROR",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// ==================== LICENSE UPDATE ====================
function handleLicenseUpdate(data) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("licenses");
  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "CONFIG_ERROR",
      message: "Sheet 'licenses' not found"
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  // Validate required fields
  if (!data.license_key) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "VALIDATION_ERROR",
      message: "license_key required"
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  // Search for existing license_key
  var dataRange = sheet.getDataRange();
  var values = dataRange.getValues();
  var targetRow = -1;
  
  for (var i = 1; i < values.length; i++) {  // Skip header row
    if (values[i][0] == data.license_key) {
      targetRow = i + 1;  // Convert to 1-indexed row number
      break;
    }
  }
  
  // Append new row if license_key not found
  var isNewActivation = (targetRow === -1);
  if (isNewActivation) {
    targetRow = sheet.getLastRow() + 1;
  }
  
  // Column mapping (1-indexed for Google Sheets)
  // A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9, J=10, K=11
  
  sheet.getRange(targetRow, 1).setValue(data.license_key);           // A: license_key
  sheet.getRange(targetRow, 2).setValue(data.status || "active");    // B: status
  
  // C: expiry_date - AUTO-CALCULATE on new activation based on tier
  if (isNewActivation) {
    var expiryDate = calculateExpiryDate(data.license_tier || "standard", new Date());
    sheet.getRange(targetRow, 3).setValue(expiryDate);
  }
  
  sheet.getRange(targetRow, 4).setValue(data.hw1 || "");             // D: hw_component_1
  sheet.getRange(targetRow, 5).setValue(data.hw2 || "");             // E: hw_component_2
  sheet.getRange(targetRow, 6).setValue(data.hw3 || "");             // F: hw_component_3
  
  sheet.getRange(targetRow, 7).setValue(data.licensee_name || "");   // G: licensee_name
  sheet.getRange(targetRow, 8).setValue(data.licensee_email || "");  // H: licensee_email
  sheet.getRange(targetRow, 9).setValue(data.license_tier || "standard"); // I: license_tier
  sheet.getRange(targetRow, 10).setValue(new Date());                // J: last_validated
  
  // K: feature flags (optional, can be set manually or via tier defaults)
  // L: max_calculations (set based on tier)
  var tierLimits = {
    "trial": 10,
    "standard": 100,
    "premium": 1000
  };
  var maxCalcs = tierLimits[data.license_tier || "standard"] || 100;
  sheet.getRange(targetRow, 11).setValue(maxCalcs);
  
  // Log audit event
  var eventType = data.event_type || "activate";
  logAuditEvent(
    data.license_key,
    eventType,
    "success",
    {hw1: data.hw1 || "", hw2: data.hw2 || "", hw3: data.hw3 || ""},
    "",
    data.licensee_email || ""
  );
  
  return ContentService.createTextOutput(JSON.stringify({
    success: true,
    message: "License updated at row " + targetRow,
    row: targetRow,
    is_new: isNewActivation
  })).setMimeType(ContentService.MimeType.JSON);
}

// ==================== USAGE REPORTING ====================
function handleUsageReport(data) {
  if (!data.license_key || !data.month) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "VALIDATION_ERROR",
      message: "license_key and month required for usage report"
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  var usageSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("usage_stats");
  if (!usageSheet) {
    // Create usage_stats sheet if doesn't exist
    usageSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet("usage_stats");
    usageSheet.appendRow(["month", "license_key", "calculations_count", "exports_count", "reported_at"]);
  }
  
  usageSheet.appendRow([
    data.month,
    data.license_key,
    data.calculations_count || 0,
    data.exports_count || 0,
    new Date()
  ]);
  
  Logger.log("Usage reported for " + data.license_key + ": " + data.month);
  
  return ContentService.createTextOutput(JSON.stringify({
    success: true,
    message: "Usage stats recorded"
  })).setMimeType(ContentService.MimeType.JSON);
}

// ==================== AUDIT TRAIL ====================
function logAuditEvent(licenseKey, eventType, status, hwComponents, errorMsg, userEmail) {
  var auditSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("audit_log");
  if (!auditSheet) {
    // Create audit sheet if doesn't exist
    auditSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet("audit_log");
    auditSheet.appendRow([
      "timestamp", "license_key", "event_type", "status",
      "hw1", "hw2", "hw3", "error_message", "user_email"
    ]);
  }
  
  auditSheet.appendRow([
    new Date(),
    licenseKey,
    eventType,
    status,
    hwComponents.hw1 || "",
    hwComponents.hw2 || "",
    hwComponents.hw3 || "",
    errorMsg || "",
    userEmail || ""
  ]);
}

// ==================== EXPIRY CALCULATION ====================
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

// ==================== BATCH VALIDATION ====================
function handleBatchValidation(licenses) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("licenses");
  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({
      error: "CONFIG_ERROR",
      message: "Sheet 'licenses' not found"
    })).setMimeType(ContentService.MimeType.JSON);
  }
  
  var results = [];
  
  licenses.forEach(function(key) {
    var row = findLicenseRow(sheet, key);
    if (row) {
      results.push({
        license_key: key,
        status: sheet.getRange(row, 2).getValue(),
        expiry_date: sheet.getRange(row, 3).getValue(),
        license_tier: sheet.getRange(row, 9).getValue()
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

function findLicenseRow(sheet, licenseKey) {
  var dataRange = sheet.getDataRange();
  var values = dataRange.getValues();
  
  for (var i = 1; i < values.length; i++) {
    if (values[i][0] == licenseKey) {
      return i + 1;
    }
  }
  return null;
}

// ==================== TEST ENDPOINT ====================
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    service: "Water Balance License Manager",
    status: "active",
    message: "Use POST requests for license operations",
    version: "2.0"
  })).setMimeType(ContentService.MimeType.JSON);
}

// ==================== SETUP INSTRUCTIONS ====================
/*
SETUP STEPS:

1. CREATE GOOGLE SHEET with these sheets:
   - licenses (main sheet with columns A-K)
   - audit_log (auto-created on first validation)
   - usage_stats (auto-created on first usage report)

2. SET API KEY:
   - Open Apps Script Editor
   - File → Project properties → Script properties
   - Add property: API_KEY = your-secret-key-here
   - Generate random 32-char string for security

3. DEPLOY AS WEB APP:
   - Click "Deploy" → "New deployment"
   - Type: Web app
   - Execute as: Me
   - Who has access: Anyone
   - Copy the webhook URL

4. UPDATE PYTHON CONFIG:
   - Add to app_config.yaml:
     licensing:
       api_key: same-secret-key-here
       webhook_url: https://script.google.com/macros/s/.../exec

5. TEST:
   - Send POST request with api_key in headers or body
   - Check audit_log sheet for logged event

SHEET STRUCTURE (licenses):
A: license_key (text)
B: status (active/revoked/expired)
C: expiry_date (date, auto-calculated on activation)
D: hw_component_1 (text, MAC address hash)
E: hw_component_2 (text, CPU serial hash)
F: hw_component_3 (text, motherboard UUID hash)
G: licensee_name (text)
H: licensee_email (text)
I: license_tier (trial/standard/premium)
J: last_validated (timestamp)
K: max_calculations (number, tier-based limit)

AUDIT LOG STRUCTURE:
A: timestamp
B: license_key
C: event_type (activate/validate/revoke)
D: status (success/failure/unauthorized)
E: hw1
F: hw2
G: hw3
H: error_message
I: user_email

USAGE STATS STRUCTURE:
A: month (YYYY-MM)
B: license_key
C: calculations_count
D: exports_count
E: reported_at (timestamp)

SECURITY NOTES:
- API key required for all POST requests
- Stored in Script Properties (encrypted by Google)
- Rotate API key every 90 days
- Monitor audit_log for suspicious activity
- Rate limit: 20,000 executions/day (Google Apps Script limit)
*/
