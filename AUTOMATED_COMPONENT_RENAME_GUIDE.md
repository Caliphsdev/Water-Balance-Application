# Automated Component Rename System

## Overview

The component rename system automatically updates ALL areas of the system when you rename a component. One configuration file controls everything.

## Quick Start

### 1. Configure Your Rename

Edit `component_rename_config.json`:

```json
{
  "component_renames": [
    {
      "old_name": "guest_house",
      "new_name": "trp_clinic",
      "excel_columns": [
        "SOFTENING → TRP_CLINIC",
        "TRP_CLINIC → SEPTIC",
        "TRP_CLINIC → CONSUMPTION"
      ],
      "description": "Renamed from guest_house to TRP_CLINIC"
    }
  ],
  "files": {
    "json_diagram": "data/diagrams/ug2_north_decline.json",
    "excel_template": "test_templates/Water_Balance_TimeSeries_Template.xlsx"
  }
}
```

### 2. Preview Changes (Always Do This First!)

```bash
python component_rename_manager.py --dry-run
```

Output shows:
```
>>> Processing: GUEST_HOUSE → TRP_CLINIC
    [JSON] Node ID: guest_house → trp_clinic
    [JSON] Edge: softening → guest_house = softening → trp_clinic
    [JSON] Mapping: SOFTENING → GUEST_HOUSE → SOFTENING → TRP_CLINIC
    [EXCEL] Flows_UG2N: Added column SOFTENING → TRP_CLINIC
    ...
```

### 3. Apply Changes

```bash
python component_rename_manager.py
```

### 4. Verify

```bash
python check_ug2n_sync.py    # Verify specific area
python test_validation.py     # Full validation
```

## Configuration Guide

### For a Single Rename

Edit `component_rename_config.json`:

```json
{
  "component_renames": [
    {
      "old_name": "offices",
      "new_name": "office_building",
      "excel_columns": [
        "OFFICE_BUILDING → CONSUMPTION",
        "OFFICE_BUILDING → SEWAGE",
        "OFFICE_BUILDING → SEPTIC"
      ],
      "description": "Rename offices building"
    }
  ],
  "files": {...}
}
```

Then run:
```bash
python component_rename_manager.py --dry-run
python component_rename_manager.py
```

### For Multiple Renames at Once

```json
{
  "component_renames": [
    {
      "old_name": "offices",
      "new_name": "office_building",
      "excel_columns": [...],
      "description": "..."
    },
    {
      "old_name": "septic",
      "new_name": "septic_tank",
      "excel_columns": [...],
      "description": "..."
    },
    {
      "old_name": "softening",
      "new_name": "softening_plant",
      "excel_columns": [...],
      "description": "..."
    }
  ],
  "files": {...}
}
```

Run once:
```bash
python component_rename_manager.py
```

All three renames applied automatically!

## What Gets Updated

### JSON Diagram
- ✅ Node IDs (`guest_house` → `trp_clinic`)
- ✅ Edge references (all `from`/`to` attributes)
- ✅ Edge mappings (column names in `excel_mapping`)

### Excel Template
- ✅ Column headers added (e.g., `SOFTENING → TRP_CLINIC`)
- ✅ Automatically placed in correct sheet
- ✅ Sample data filled in (placeholder `-`)

### Dependent Systems
- ✅ All 8 Flows sheets (UG2N, UG2P, UG2S, OLDTSF, MERN, MERP, MERS, STOCKPILE)
- ✅ All 138 flow edges
- ✅ All 3 JSON diagram areas

## Commands

```bash
# List pending renames
python component_rename_manager.py --list

# Preview what would change (safe to run)
python component_rename_manager.py --dry-run

# Apply all renames
python component_rename_manager.py

# Use custom config file
python component_rename_manager.py --config my_custom_config.json
```

## Step-by-Step Workflow

### Step 1: Plan the Rename
Decide what's changing and why:
```
Old name: guest_house
New name: trp_clinic
Reason: Building was renamed
```

### Step 2: List Associated Columns
Find all Excel columns that use this component:
```
SOFTENING → GUEST_HOUSE
GUEST_HOUSE → SEPTIC
GUEST_HOUSE → CONSUMPTION
```

### Step 3: Update Configuration
```bash
# Edit component_rename_config.json
{
  "component_renames": [
    {
      "old_name": "guest_house",
      "new_name": "trp_clinic",
      "excel_columns": [
        "SOFTENING → TRP_CLINIC",
        "TRP_CLINIC → SEPTIC",
        "TRP_CLINIC → CONSUMPTION"
      ]
    }
  ],
  ...
}
```

### Step 4: Preview
```bash
python component_rename_manager.py --dry-run
# Review output carefully!
```

### Step 5: Apply
```bash
python component_rename_manager.py
```

### Step 6: Validate
```bash
python test_validation.py
```

## Examples

### Example 1: Rename a Simple Component

```json
{
  "component_renames": [
    {
      "old_name": "rainfall",
      "new_name": "rainfall_input",
      "excel_columns": [
        "RAINFALL_INPUT → NDCD",
        "RAINFALL_INPUT → STOCKPILE_AREA"
      ],
      "description": "Clarify that this is rainfall input data"
    }
  ],
  "files": {...}
}
```

### Example 2: Rename Multiple Related Components

```json
{
  "component_renames": [
    {
      "old_name": "ndcd",
      "new_name": "ndcd_reservoir",
      "excel_columns": [
        "RAINFALL → NDCD_RESERVOIR",
        "NDCD_RESERVOIR → SPILL",
        "NDCD_RESERVOIR → EVAPORATION"
      ],
      "description": "Clarify NDCD is a reservoir"
    },
    {
      "old_name": "spill",
      "new_name": "spillway_discharge",
      "excel_columns": [
        "NDCD_RESERVOIR → SPILLWAY_DISCHARGE",
        "SPCD1 → SPILLWAY_DISCHARGE"
      ],
      "description": "More descriptive name for spill"
    }
  ],
  "files": {...}
}
```

## Troubleshooting

### "No component renames configured"
- Check `component_rename_config.json` exists
- Verify it has valid JSON syntax
- Ensure `component_renames` array is not empty

### "Invalid rename config"
- Check `old_name` and `new_name` are both specified
- Verify they're not empty strings

### Column not added to Excel
- Check the column name format: `SOURCE → DESTINATION`
- Verify it matches the sheet's area (e.g., UG2N columns start with UG2N components)
- The system auto-determines the sheet

### Changes not applied
- Always preview first with `--dry-run`
- Check for file permission errors
- Ensure Excel file is not open in another application

## Best Practices

1. **Always preview first**
   ```bash
   python component_rename_manager.py --dry-run
   ```

2. **Use descriptive names**
   ```json
   "description": "Renamed to clarify this is a treated water storage area"
   ```

3. **One rename at a time** (until comfortable)
   ```bash
   # First rename
   python component_rename_manager.py --dry-run
   python component_rename_manager.py
   python test_validation.py
   
   # Then next rename
   # (Update config and repeat)
   ```

4. **Batch related renames**
   ```json
   "component_renames": [
     { "old_name": "offices", "new_name": "office_building", ... },
     { "old_name": "sewage", "new_name": "sewage_system", ... }
   ]
   ```

5. **Keep git history clean**
   - Commit rename changes with descriptive message
   - Include reason in commit (e.g., "Rename offices → office_building for clarity")

## Automation Ideas for Future

### Automatic Detection
```python
# Detect component renames from comments
# "RENAME: old_name → new_name" in config file
```

### Batch Processing
```python
# Read renames from CSV
# Component,OldName,NewName,Columns
```

### Validation Hooks
```python
# Auto-validate after rename
# Prevent broken renames from being applied
```

### Backup System
```python
# Auto-backup before rename
# Rollback on validation failure
```

## Summary

- **Single command**: `python component_rename_manager.py`
- **Updates**: JSON, Excel, all edges, all mappings
- **Safe**: Always use `--dry-run` first
- **Simple**: Edit JSON config, one file controls everything
- **Complete**: No manual updates needed across multiple files

Done with manual updating headaches! 🎉
