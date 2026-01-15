// Google Apps Script for Water Balance License Manager Sheet
// Deploy as Web App to get webhook URL for POST requests from Python app

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("licenses");
    if (!sheet) {
      return ContentService.createTextOutput("ERROR: Sheet 'licenses' not found");
    }
    
    var data = JSON.parse(e.postData.contents);
    
    // Validate required fields
    if (!data.license_key) {
      return ContentService.createTextOutput("ERROR: license_key required");
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
    if (targetRow === -1) {
      targetRow = sheet.getLastRow() + 1;
    }
    
    // Column mapping (1-indexed for Google Sheets)
    // A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9, J=10, K=11
    
    sheet.getRange(targetRow, 1).setValue(data.license_key);           // A: license_key
    sheet.getRange(targetRow, 2).setValue(data.status || "active");    // B: status
    // C: expiry_date (preserve existing, don't overwrite from webhook)
    sheet.getRange(targetRow, 4).setValue(data.hw1 || "");             // D: hw_component_1
    sheet.getRange(targetRow, 5).setValue(data.hw2 || "");             // E: hw_component_2
    sheet.getRange(targetRow, 6).setValue(data.hw3 || "");             // F: hw_component_3
    
    // G: transfer_count (increment if transfer, else preserve or initialize)
    if (data.is_transfer === true) {
      var currentCount = sheet.getRange(targetRow, 7).getValue() || 0;
      sheet.getRange(targetRow, 7).setValue(currentCount + 1);
    } else if (targetRow === sheet.getLastRow()) {
      // New activation - initialize to 0
      sheet.getRange(targetRow, 7).setValue(0);
    }
    
    sheet.getRange(targetRow, 8).setValue(data.licensee_name || "");   // H: licensee_name
    sheet.getRange(targetRow, 9).setValue(data.licensee_email || "");  // I: licensee_email
    sheet.getRange(targetRow, 10).setValue(data.license_tier || "standard"); // J: license_tier
    sheet.getRange(targetRow, 11).setValue(new Date());                // K: last_validated
    
    return ContentService.createTextOutput("OK: License updated at row " + targetRow);
    
  } catch (error) {
    return ContentService.createTextOutput("ERROR: " + error.toString());
  }
}

// Test function for development
function doGet(e) {
  return ContentService.createTextOutput("License Manager Webhook - Use POST requests");
}
