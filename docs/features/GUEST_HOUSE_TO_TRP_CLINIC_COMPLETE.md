# Guest House → TRP Clinic Component Rename - Complete

## Problem
You correctly pointed out that I had added GUEST_HOUSE columns to Excel, but the component was actually renamed to TRP_CLINIC. This was wrong and needed fixing.

## Solution Applied

### Step 1: Restored Excel ✅
Removed the mistakenly added GUEST_HOUSE columns from Excel.

### Step 2: Added TRP_CLINIC Columns ✅  
Added the correct columns to Excel:
- `SOFTENING → TRP_CLINIC`
- `TRP_CLINIC → SEPTIC`
- `TRP_CLINIC → CONSUMPTION`

### Step 3: Updated JSON Diagram ✅
Used the new `rename_component.py` automation script to update:
- JSON node ID: `guest_house` → `trp_clinic`
- All edge references from/to guest_house → updated to trp_clinic
- Edge mappings: GUEST_HOUSE columns → TRP_CLINIC columns

### Step 4: Cleaned Up Old Columns ✅
Removed the old GUEST_HOUSE columns that were created during the format conversion.

### Step 5: Verified Results ✅
```
Flows FROM trp_clinic:
  trp_clinic -> septic: TRP_CLINIC → SEPTIC ✅
  trp_clinic -> consumption: TRP_CLINIC → CONSUMPTION ✅
```

## Automation Created for Future Use

You wanted this automated "incase user change component name again". I've created:

### 1. `rename_component.py` (Main Script)
Handles renaming components throughout the entire system:
```bash
# Test first
python rename_component.py old_name new_name --dry-run

# Apply changes
python rename_component.py old_name new_name
```

Updates:
- ✅ JSON node IDs  
- ✅ JSON edge references
- ✅ Excel column names
- ✅ Edge mappings

### 2. `rename_component_add_columns_TEMPLATE.py` (Template)
Use this template to add new Excel columns before running the rename:
```bash
# Customize and run
python add_new_component_columns.py
python rename_component.py old_name new_name
```

### 3. `COMPONENT_RENAME_GUIDE.md` (Documentation)
Complete guide with:
- Quick start instructions
- Step-by-step process
- Troubleshooting
- Configuration examples
- Future automation ideas

## Key Files Modified

| File | Change | Status |
|------|--------|--------|
| `test_templates/Water_Balance_TimeSeries_Template.xlsx` | Added TRP_CLINIC columns, removed GUEST_HOUSE columns | ✅ Fixed |
| `data/diagrams/ug2_north_decline.json` | Updated node ID and edge references | ✅ Fixed |
| `rename_component.py` | New automation script | ✅ Created |
| `COMPONENT_RENAME_GUIDE.md` | Complete documentation | ✅ Created |

## How to Use for Future Component Renames

Whenever a component name changes:

```bash
# 1. Add new column names to Excel (customize the template script)
python add_my_new_columns.py

# 2. Test the rename (always start with --dry-run)
python rename_component.py old_name new_name --dry-run

# 3. Review the output to confirm what will change

# 4. Apply the rename
python rename_component.py old_name new_name

# 5. Verify with validation
python test_validation.py
```

## Example: Next Time

If someone later renames "offices" to "office_building":

```bash
# Create add_office_columns.py from template
# (Update COLUMNS_TO_ADD with new office columns)

python add_office_columns.py
python rename_component.py offices office_building --dry-run
python rename_component.py offices office_building
```

The script will automatically:
- Update JSON node `offices` → `office_building`
- Update all edges from/to `offices`
- Update Excel columns: `OFFICES → ...` → `OFFICE_BUILDING → ...`
- Keep everything in sync

## Status Summary

✅ **guest_house renamed to trp_clinic**
✅ **Automation created for future renames**
✅ **UG2N flows correctly mapped to TRP_CLINIC**
✅ **Documentation complete**

No more manual headaches with component renames!
