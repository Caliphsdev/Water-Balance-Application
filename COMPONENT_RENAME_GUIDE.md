# Component Rename Automation Guide

## Quick Start

When a component is renamed in the system (e.g., `guest_house` → `trp_clinic`), use this script to update everything automatically:

```bash
# 1. First, add new column names to Excel
python add_trp_clinic_columns.py   # (or create similar script for your component)

# 2. Then run the rename automation
python rename_component.py old_name new_name
```

## What It Does

The `rename_component.py` script automatically updates:
- ✅ JSON diagram node IDs
- ✅ JSON edge from/to references  
- ✅ Excel column header references
- ✅ Edge mapping column names

### Example: Renaming guest_house to trp_clinic

```bash
# Test first (see what would change)
python rename_component.py guest_house trp_clinic --dry-run

# Output shows:
#   Node ID: guest_house → trp_clinic
#   Edge: softening → guest_house → softening → trp_clinic
#   Mapping: GUEST_HOUSE → SEPTIC → TRP_CLINIC → SEPTIC
#   Total changes: 7

# Apply the changes
python rename_component.py guest_house trp_clinic
```

## Step-by-Step Process

### Step 1: Add Excel Columns (if new names)
If the Excel columns don't already exist, create a script to add them:

```python
# add_new_component_columns.py
from openpyxl import load_workbook

wb = load_workbook('test_templates/Water_Balance_TimeSeries_Template.xlsx')
ws = wb['Flows_UG2N']

# Add columns in row 3
ws.cell(3, next_col).value = 'SOFTENING → TRP_CLINIC'
ws.cell(3, next_col+1).value = 'TRP_CLINIC → SEPTIC'
ws.cell(3, next_col+2).value = 'TRP_CLINIC → CONSUMPTION'

wb.save('test_templates/Water_Balance_TimeSeries_Template.xlsx')
```

### Step 2: Dry Run the Rename
Always test first to see what changes:

```bash
python rename_component.py guest_house trp_clinic --dry-run
```

Review the output to ensure:
- Correct nodes are being renamed
- Correct edges are being updated
- Correct mappings are being adjusted

### Step 3: Apply the Rename
Once confident, run without `--dry-run`:

```bash
python rename_component.py guest_house trp_clinic
```

### Step 4: Verify the Changes
Run validation to confirm:

```bash
python test_validation.py    # Validate all mappings
python check_ug2n_sync.py     # Check specific area
```

## Key Points

### Node IDs vs Labels
- **Node ID** (internal): `guest_house` (used in JSON edge references)
- **Node Label** (display): `TRP Clinic` (shown in diagram UI)
- **Excel format**: `TRP_CLINIC` (all caps with underscores)

The rename script converts between these formats automatically.

### What Needs Manual Updates
The automation script handles most updates, but you may need to:
1. **Add Excel columns first** - if new component names don't exist in Excel yet
2. **Update node labels** - manually in the JSON if the display name changed
3. **Verify cross-area references** - edges that reference nodes in other areas

### Supported Formats
The script automatically converts between:
- Lowercase with underscores: `guest_house` (node IDs)
- UPPERCASE with underscores: `GUEST_HOUSE` (Excel columns)
- Mixed case: `Guest House` (user input)

## Troubleshooting

### Script says "no changes" but I expect changes
- Check the naming format - use lowercase with underscores
- Verify the component exists in JSON and Excel
- Confirm spelling matches exactly

### Changes not appearing in Excel
- Make sure Excel column headers are in row 3
- Verify your column names match the format: `COMPONENT_NAME`
- Check you're editing the right sheet (Flows_UG2N, etc.)

### Changes in JSON but validation still fails
- Excel columns may need updating first
- Run `test_validation.py` to see what's mismatched
- Run sync script to update remaining mappings: `python sync_json_final.py`

## Automation for Future Use

To make this fully automated:
1. Store component renames in a configuration file
2. Run the rename script in CI/CD pipeline
3. Add validation checks after rename
4. Generate reports of all changes made

Example config:
```json
{
  "component_renames": [
    {"old": "guest_house", "new": "trp_clinic"},
    {"old": "offices", "new": "office_building"}
  ]
}
```

## Related Scripts

- `sync_json_final.py` - Syncs all JSON edges to Excel headers
- `update_excel_to_new_format.py` - Converts Excel naming conventions
- `test_validation.py` - Validates all mappings
- `check_ug2n_sync.py` - Checks specific area mappings

## Questions?

If a component rename isn't handled correctly:
1. Run with `--dry-run` to see what would change
2. Check the JSON file for unexpected references
3. Verify Excel column names match expected format
4. Update the script if needed (it's extensible)
