# Utility Scripts Directory

This directory contains one-off automation scripts, data transformations, and setup utilities used to build, fix, and populate the system.

## Purpose

These scripts perform one-time operations like:
- Creating initial data structures
- Fixing known issues or data problems
- Automating bulk operations (adding columns, mapping flows, etc.)
- Setting up new areas or components
- Data synchronization and reconciliation

## Organization

Scripts are organized alphabetically for easy searching. Common prefixes indicate their function:

| Prefix | Purpose |
|--------|---------|
| `add_*` | Add missing columns, components, or data |
| `fix_*` | Fix known issues or data problems |
| `create_*` | Generate new structures or diagrams |
| `populate_*` | Fill in missing data or mappings |
| `rebuild_*` | Reconstruct system data from source |
| `sync_*` | Synchronize data between formats |
| `regenerate_*` | Recreate data from scratch |
| `update_*` | Modify existing data structures |
| `calculate_*` | Compute derived data |
| `test_*` | Test features or validate changes |

## Common Use Cases

### Updating System Data
```bash
python scripts/utilities/regenerate_excel_flows.py
python scripts/utilities/rebuild_excel_structure.py
python scripts/utilities/sync_json_to_excel_headers.py
```

### Adding New Components/Areas
```bash
python scripts/utilities/create_area_diagrams.py
python scripts/utilities/populate_area_diagrams.py
python scripts/utilities/setup_flow_sheets.py
```

### Fixing Data Issues
```bash
python scripts/utilities/fix_column_mismatches.py
python scripts/utilities/fix_encoding.py
python scripts/utilities/fix_stockpile_mappings.py
```

### Component Renames
```bash
python scripts/utilities/rename_component.py
python scripts/utilities/populate_ug2n_excel_from_diagram.py
```

## Important Notes

⚠️ **Caution**: Many of these scripts modify data or system state:
- Always backup your database and Excel files first
- Test on a copy of your data when unsure
- Read the script documentation/code before running
- Some scripts are designed for one-time use and may not be idempotent

## Adding New Utility Scripts

When creating a new utility:
1. Use descriptive naming with appropriate prefix
2. Add a docstring explaining:
   - What data it modifies
   - Prerequisites (files, database state)
   - Expected outcome
3. Include error handling and validation
4. Log or print progress for long operations

---

## Script Categories

### Excel/Mapping Utilities
- `add_missing_columns_to_excel.py` - Add missing flow columns
- `auto_map_excel_flows.py` - Auto-generate flow mappings
- `dedupe_excel_and_json.py` - Remove duplicate entries
- `regenerate_excel_flows.py` - Rebuild Excel flows from diagrams
- `sync_json_to_excel_headers.py` - Sync headers between formats

### Area Setup
- `create_area_diagrams.py` - Generate diagrams for new areas
- `populate_area_diagrams.py` - Fill diagram with flow data
- `create_mern_sheet.py` - Create Merensky area sheet

### Component Operations
- `add_reference_guide.py` - Create component reference
- `add_trp_clinic_columns.py` - Add TRP clinic columns
- `add_ug2n_loop.py` - Add UG2N recirculation loop
- `rename_component.py` - Rename a component

### Data Fixes
- `calculate_dam_recirculation.py` - Compute recirculation
- `cleanup_old_guest_house_columns.py` - Remove obsolete columns
- `fix_categorization_final.py` - Fix area categorization
- `fix_encoding.py` - Fix character encoding
- `populate_ug2n_excel_from_diagram.py` - Fill UG2N from diagram

### Structure Management
- `rebuild_excel_structure.py` - Recreate Excel structure
- `setup_flow_sheets.py` - Set up flow worksheets
- `update_excel_structure.py` - Modify Excel layout

### Testing/Validation
- `test_flow_diagram.py` - Test diagram functionality
- `test_singleton_reset.py` - Verify singleton reset
- `test_validation.py` - General validation tests
- `water_balance_check.py` - Validate balance calculations
