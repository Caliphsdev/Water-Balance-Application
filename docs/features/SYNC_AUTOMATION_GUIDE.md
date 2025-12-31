# Future-Proof Mapping Sync Guide

## Overview
This guide explains how to keep your JSON diagram mappings synchronized with Excel headers, ensuring validation always works no matter how your naming convention evolves.

## The System

**Source of Truth:** `test_templates/Water_Balance_TimeSeries_Template.xlsx`
- Contains all flow data entry columns
- Headers define valid mappings

**Document:** `data/diagrams/ug2_north_decline.json`
- Stores which flow connects to which Excel column
- Gets updated by the sync script to match Excel headers

**Automation:** `sync_json_to_excel_headers.py`
- Runs the sync process
- Handles naming convention changes automatically
- Uses fuzzy matching if headers change slightly

---

## When to Run the Sync

Run the sync script **anytime you:**
1. Rename Excel column headers
2. Add new flow columns to Excel sheets
3. Regenerate the Excel template
4. Change the naming convention globally
5. Get validation errors about missing columns

---

## How to Sync

### Quick Start
```bash
cd c:/PROJECTS/Water-Balance-Application
python sync_json_to_excel_headers.py
```

### What It Does
1. **Reads Excel** and extracts all sheet headers
2. **Reads JSON** and identifies all flow mappings
3. **Matches columns** - tries exact match first, then fuzzy matching
4. **Updates JSON** with correct header names
5. **Reports results** showing what was synced, what failed

---

## How It Works (Technical Details)

### Matching Strategy
The script uses a three-tier matching approach:

1. **Exact Match** (Best)
   - Old column name matches header exactly (case-insensitive)
   - No changes needed

2. **Normalized Match**
   - Converts both old and new to uppercase
   - Compares after removing extra spaces/underscores
   - Used when case or formatting differs

3. **Fuzzy Match** (Fallback)
   - Extracts key words from old column name
   - Finds Excel headers with most keyword overlap
   - Handles semantic name changes

### Naming Convention Examples

#### Old Format (Pre-Update)
```
ug2plant_ug2p_rivers__TO__ug2plant_cprwsd1    (lowercase, __TO__ separator)
oldtsf_old_tsf_rainrun__TO__oldtsf_old_tsf    
```

#### New Format (Current)
```
UG2PLANT_UG2P_RIVERS → UG2PLANT_CPRWSD1       (UPPERCASE, →  separator)
OLDTSF_OLD_TSF_RAINRUN → OLDTSF_OLD_TSF
```

#### Future Format (Custom)
```
{source}-{from_id}-TO-{dest}-{to_id}          (Any new format)
{component}:{direction}:{type}                (Or any other pattern)
```

The sync script will adapt automatically—**just update Excel headers and run the script**.

---

## Handling Unmatched Mappings

If the script reports unmapped flows (e.g., "rainfall → ndcd"):

### Option 1: Add Missing Columns to Excel
1. Open Excel sheet (e.g., `Flows_UG2N`)
2. Add column header: `RAINFALL → NDCD`
3. Save Excel
4. Re-run the sync script

### Option 2: Disable Flows in Diagram
If a flow doesn't need to be tracked in Excel:
1. Open Flow Diagram in app
2. Go to Flow Diagram module
3. Select the flow edge
4. In Excel Mapping section, disable it
5. Save diagram

### Option 3: Manual UI Update
1. Open app → Flow Diagram → Columns tab
2. Rename Excel columns or add new ones
3. The diagram updates automatically
4. Run Validate to confirm

---

## Automation for CI/CD

To keep mappings always in sync in your development workflow:

### Add to `.github/workflows/` (if using GitHub Actions)
```yaml
- name: Sync JSON Mappings to Excel
  run: python sync_json_to_excel_headers.py
```

### Or add pre-commit hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python sync_json_to_excel_headers.py
git add data/diagrams/ug2_north_decline.json
```

---

## Troubleshooting

### "Excel file not found"
- Check that `test_templates/Water_Balance_TimeSeries_Template.xlsx` exists
- Update the `EXCEL_PATH` variable in the script if needed

### "Sheet not found in Excel"
- Verify the sheet exists in Excel (e.g., `Flows_UG2N`, `Flows_UG2P`, etc.)
- The script only processes sheets starting with `Flows_`

### Many "fuzzy match" results
- Indicates the naming convention has changed significantly
- Review the matches to ensure they're correct
- If incorrect, manually rename the Excel column and re-run

### Mapping still fails after sync
- Run the script with verbose output:
  ```bash
  python sync_json_to_excel_headers.py 2>&1 | tee sync_output.log
  ```
- Check the log for details on what matched/failed
- Review the JSON file manually: `data/diagrams/ug2_north_decline.json`

---

## Example Scenarios

### Scenario 1: Rename Convention from `A→B` to `A_TO_B`
1. In Excel, find/replace all headers: `→` → `_TO_`
2. Save Excel
3. Run sync script
4. Script converts all JSON mappings automatically ✅

### Scenario 2: Add Prefix to All Headers
1. In Excel, add a prefix to all flow headers (e.g., `FLOW_` prefix)
2. Save Excel
3. Run sync script
4. Fuzzy matching finds the renamed headers ✅

### Scenario 3: Add New Flow Column
1. In Excel, add a new header: `NEW_COMPONENT → DEST`
2. In Flow Diagram, add the edge and map it to the new column
3. Run sync script (confirms mapping exists)
4. No further action needed ✅

### Scenario 4: Change Naming Convention Completely
1. Update Excel headers to new format
2. Run sync script
3. If fuzzy matching works, mappings update automatically
4. If not, manually update via UI or JSON

---

## Quick Reference Commands

```bash
# Sync JSON to Excel headers
python sync_json_to_excel_headers.py

# Check status after sync (no changes)
cd c:/PROJECTS/Water-Balance-Application
python src/main.py
# Open Flow Diagram → click Validate

# View the JSON to verify mappings
cat data/diagrams/ug2_north_decline.json | grep -A 3 "excel_mapping"
```

---

## Key Principles

✅ **Excel is the source of truth** - Headers in Excel are authoritative  
✅ **JSON follows Excel** - Mappings automatically sync to Excel headers  
✅ **Naming convention agnostic** - Works with any header format  
✅ **Reversible** - Run script anytime without loss of data  
✅ **Future-proof** - When you change conventions, just run the script  

---

## Support

If mappings are still broken after syncing:
1. Check app logs: `Console → Performance Dashboard → Logs`
2. Run Validate in Flow Diagram to see specific failures
3. Check this guide or create an issue with sync output

---
