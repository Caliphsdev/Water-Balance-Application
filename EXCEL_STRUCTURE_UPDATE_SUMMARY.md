# Excel Structure Update Summary

**Date:** 2025-01-19  
**Purpose:** Align Excel file structure with diagram restructuring changes

## Changes Applied

### 1. ✅ Excel Structure Manager - Column Population Fix

**Issue:** Columns tab in Excel Manager showed empty list when selecting a sheet

**Root Cause:** 
- `refresh_columns()` was called immediately after `sheet_combo.current(0)` but before the combo box value was fully set
- The `sheet_var.get()` returned empty string, causing early return in `refresh_columns()`

**Solution:**
- Changed `refresh_sheets_combo()` to trigger the ComboboxSelected event explicitly after setting the value
- Removed direct `refresh_columns()` call
- Now properly triggers the binding: `sheet_combo.bind('<<ComboboxSelected>>', lambda e: refresh_columns())`

**Code Change (line 3795-3804):**
```python
# BEFORE:
def refresh_sheets_combo():
    try:
        wb = load_workbook(excel_path)
        sheet_combo['values'] = wb.sheetnames
        if wb.sheetnames:
            sheet_combo.current(0)
        wb.close()
        refresh_columns()  # ❌ Called too early
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load sheets:\n{e}")

# AFTER:
def refresh_sheets_combo():
    try:
        wb = load_workbook(excel_path)
        sheet_combo['values'] = wb.sheetnames
        if wb.sheetnames:
            sheet_combo.current(0)
            # Trigger column refresh after combo value is set
            sheet_combo.event_generate('<<ComboboxSelected>>')  # ✅ Proper event trigger
        wb.close()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load sheets:\n{e}")
```

---

### 2. ✅ Excel File Structure Update

**Script:** `update_excel_structure.py`  
**Excel Path:** `test_templates/Water_Balance_TimeSeries_Template.xlsx`  
**Backup Created:** `Water_Balance_TimeSeries_Template.backup_20251219_162836.xlsx`

#### Changes Made:

##### A. Removed Sheets
- **Flows_MERN** (Merensky North Area)
  - **Reason:** Area was deleted from flow diagram during restructuring
  - **Status:** Sheet removed cleanly

##### B. Added Sheets
- **Flows_NEWTSF** (New TSF facility)
  - **Reason:** Old TSF split into Old TSF + New TSF during restructuring
  - **Position:** Inserted after Flows_OLDTSF
  - **Structure:**
    - Standard headers: Date, Year, Month
    - Formatted with header styling (bold, yellow fill, centered)
    - Column widths: A=12, B=8, C=10

##### C. Updated Reference Guide Sheet

New Reference Guide includes:

**OVERVIEW Section:**
- Explanation of Excel file purpose
- Sheet structure overview

**SHEET STRUCTURE Section:**
| Sheet Name | Area | Description |
|------------|------|-------------|
| Reference Guide | N/A | This guide sheet |
| Flows_UG2N | UG2 North Decline | Underground 2 North mining area flows |
| Flows_STOCKPILE | Stockpile Area | Ore stockpile facility flows |
| Flows_UG2S | UG2 South Decline | Underground 2 South mining area flows |
| Flows_MERS | Merensky South | Merensky South mining area flows |
| Flows_OLDTSF | Old TSF | Old Tailings Storage Facility (original facility) |
| Flows_NEWTSF | New TSF | New Tailings Storage Facility (split from Old TSF) |
| Flows_UG2P | UG2 Plant | Underground 2 processing plant flows |
| Flows_MERP | Merensky Plant | Merensky processing plant flows |

**IMPORTANT NOTES Section:**
- ✓ Standard column requirements (Date, Year, Month)
- ✓ Flow column naming conventions
- ✓ Data format guidelines
- ⚠️ **Changes from previous version:**
  - Merensky North Area removed (area deleted from operations)
  - Old TSF split into two facilities: Old TSF and New TSF
  - Flows_MERN sheet removed
  - Flows_NEWTSF sheet added for New TSF facility
- 💡 **Tips:**
  - Use Excel Manager in Flow Diagram Dashboard
  - Auto-Map feature available
  - Always backup before changes

---

## Final Excel Structure

**Total Sheets:** 9 (was 9, changed 2)

### Sheet List:
1. Reference Guide _(updated documentation)_
2. Flows_OLDTSF _(unchanged)_
3. **Flows_NEWTSF** _(NEW - added for New TSF facility)_
4. Flows_UG2P _(unchanged)_
5. Flows_UG2S _(unchanged)_
6. Flows_UG2N _(unchanged)_
7. Flows_MERP _(unchanged)_
8. Flows_MERS _(unchanged)_
9. Flows_STOCKPILE _(unchanged)_

### Removed:
- ~~Flows_MERN~~ _(Merensky North Area deleted)_

---

## Diagram vs Excel Alignment

| Diagram Area | Excel Sheet | Status |
|--------------|-------------|--------|
| UG2 North Decline | Flows_UG2N | ✅ Aligned |
| Stockpile Area | Flows_STOCKPILE | ✅ Aligned |
| UG2 South Decline | Flows_UG2S | ✅ Aligned |
| Merensky South | Flows_MERS | ✅ Aligned |
| **Old TSF** | **Flows_OLDTSF** | ✅ **Aligned (original facility)** |
| **New TSF** | **Flows_NEWTSF** | ✅ **Aligned (split facility)** |
| UG2 Plant | Flows_UG2P | ✅ Aligned |
| Merensky Plant | Flows_MERP | ✅ Aligned |
| ~~Merensky North~~ | ~~Flows_MERN~~ | ✅ **Both removed** |

**Result:** 100% alignment between diagram structure and Excel structure ✅

---

## User-Facing Changes

### Excel Manager (UI)
- **Columns Tab:** Now properly populates columns when selecting a sheet
- **Sheets Tab:** Will now show 9 sheets (Flows_NEWTSF added, Flows_MERN removed)

### Reference Guide
- Updated documentation reflects current structure
- Clear explanation of what changed and why
- User guidance for managing Excel structure

### Data Migration Notes
- **No data loss:** Flows_MERN removed but can be restored from backup if needed
- **Flows_NEWTSF:** Empty sheet with headers ready for data entry
- **Backup:** Previous version saved as `.backup_20251219_162836.xlsx`

---

## Testing Checklist

- [x] Excel file loads without errors
- [x] All 9 sheets present and named correctly
- [x] Flows_MERN removed
- [x] Flows_NEWTSF created with standard headers
- [x] Reference Guide updated with new content
- [x] Excel Manager opens successfully
- [x] Columns populate when selecting sheets
- [x] Backup file created
- [ ] User verification of structure
- [ ] Add New TSF flow columns as needed
- [ ] Test Excel Manager add/rename/delete operations

---

## Next Steps

1. **Add New TSF Flow Columns:**
   - Use Excel Manager to add columns for New TSF flows
   - Follow naming convention: COMPONENT1_COMPONENT2
   - Map columns to diagram edges using Excel Manager

2. **Data Entry:**
   - Begin populating Flows_NEWTSF with historical data
   - Split relevant Old TSF data between Old TSF and New TSF sheets

3. **Validation:**
   - Run Balance Check to verify flow calculations
   - Check Calculations Dashboard with new structure
   - Verify Flow Diagram Dashboard loads all areas

---

## Files Modified

1. **src/ui/flow_diagram_dashboard.py** (line 3795-3804)
   - Fixed column population in Excel Manager

2. **test_templates/Water_Balance_TimeSeries_Template.xlsx**
   - Removed Flows_MERN sheet
   - Added Flows_NEWTSF sheet
   - Updated Reference Guide sheet

3. **Created:**
   - `update_excel_structure.py` (script for Excel updates)
   - `Water_Balance_TimeSeries_Template.backup_20251219_162836.xlsx` (backup)
   - `EXCEL_STRUCTURE_UPDATE_SUMMARY.md` (this file)

---

## Rollback Procedure

If issues arise, restore from backup:

```powershell
# Restore original Excel file
Copy-Item test_templates\Water_Balance_TimeSeries_Template.backup_20251219_162836.xlsx test_templates\Water_Balance_TimeSeries_Template.xlsx -Force

# Revert code change in flow_diagram_dashboard.py
git checkout src/ui/flow_diagram_dashboard.py
```

---

**Status:** ✅ All changes completed successfully  
**Author:** GitHub Copilot  
**Date:** 2025-01-19
