# Debug Scripts Directory

This directory contains diagnostic and debugging utilities used during development and troubleshooting. These scripts are organized by purpose for easier navigation.

## Directory Structure

### [`excel_mapping/`](excel_mapping/)
**Purpose**: Validate and repair Excel-to-diagram flow mappings
- Checks for unmapped flows, missing columns, and mapping mismatches
- Regenerates Excel structure from JSON diagrams
- Verifies Excel vs. application state

**Key Scripts**:
- `check_unmapped_flows.py` - Find flows missing from Excel
- `verify_excel_json.py` - Compare Excel and JSON consistency
- `regenerate_excel_flows.py` - Rebuild Excel from diagram definitions

### [`structure/`](structure/)
**Purpose**: Analyze database and JSON diagram structure
- Validates database schema, tables, and relationships
- Checks JSON diagram node/edge integrity
- Extracts database connection information

**Key Scripts**:
- `check_db_schema.py` - Verify database structure
- `check_json_structure.py` - Validate diagram JSON format
- `verify_all_edges.py` - Check all edge definitions

### [`area_specific/`](area_specific/)
**Purpose**: Debug and validate specific areas (UG2N, Merensky, Old TSF, etc.)
- Area-specific data loading and categorization
- Loop and recirculation validation
- Syncing area data with Excel

**Key Scripts**:
- `check_ug2n_data.py` - Debug UG2N area
- `debug_merensky.py` - Analyze Merensky plant flows
- `check_oldtsf_loops.py` - Verify Old TSF recirculation

### [`flow_checks/`](flow_checks/)
**Purpose**: Validate individual flows, components, and labels
- Edge enable/disable status checks
- Component code verification
- Flow label display validation

**Key Scripts**:
- `check_enabled_edges.py` - List enabled/disabled edges
- `find_missing_flows.py` - Locate missing flow definitions
- `check_flow_labels.py` - Verify label display

### [`verification/`](verification/)
**Purpose**: Final validation and feature verification
- Test results after fixes and updates
- Feature completion verification
- Cross-validation of changes

**Key Scripts**:
- `verify_all_areas.py` - Full system validation
- `verify_excel_fix.py` - Check Excel fixes
- `show_verification_summary.py` - Display summary of changes

### [`misc/`](misc/)
**Purpose**: Miscellaneous checks and one-off diagnostics
- General data checks (rainfall, formatting)
- Inter-area flow validation
- Comparison and analysis utilities

**Key Scripts**:
- `check_all_areas.py` - Quick overview of all areas
- `check_rainfall.py` - Validate rainfall data
- `compare_edge_configs.py` - Compare edge configurations

---

## How to Use

1. **Identify the issue**: Determine which aspect of the system needs debugging
2. **Find the appropriate script**: Use the category guide above
3. **Run the script**: `python scripts/debug/<category>/<script_name>.py`
4. **Review output**: Check console output for diagnostic information

---

## Adding New Debug Scripts

When creating a new debug script:
1. Place it in the appropriate subdirectory
2. Add a docstring explaining its purpose
3. Update this README with its description
4. Ensure it doesn't modify system state (unless intentional)

---

## Notes

- These scripts are meant for development and troubleshooting only
- Never run these in production without understanding their impact
- Some scripts may require database access or Excel files
- Always backup data before running repair scripts
