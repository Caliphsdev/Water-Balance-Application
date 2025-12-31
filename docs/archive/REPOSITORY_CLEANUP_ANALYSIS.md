# Repository Cleanup and Consolidation Analysis

**Date**: December 31, 2025  
**Status**: Analysis Complete

---

## Executive Summary

The repository has accumulated **200+ files** at the root level, creating significant management overhead. This analysis categorizes files and provides a consolidation strategy.

**Key Findings:**
- ✅ **Core System Files**: ~30 (keep in root)
- ✅ **Source Code**: ~60 (already in `src/` - good)
- ⚠️ **Temporary Check/Debug Scripts**: ~70 (consolidate to `scripts/debug`)
- ⚠️ **Documentation**: ~50+ markdown files (consolidate to `docs/`)
- ❌ **Obsolete/Redundant**: ~20+ (recommend deletion)
- ❌ **Component-Specific Guides**: ~15+ (consolidate to feature docs)

---

## File Categorization

### 1. ROOT-LEVEL ESSENTIALS (Keep) ✅
These belong at root level:
```
README.md                                    # Main project doc
requirements.txt                             # Dependencies
.gitignore, .gitattributes                   # Git config
component_rename_config.json                 # Active config
DAM_RECIRCULATION_TEMPLATE.txt              # Data template
INFLOW_CODES_TEMPLATE.txt                    # Data template
OUTFLOW_CODES_TEMPLATE_CORRECTED.txt         # Data template
QUICK_REFERENCE.txt                          # Quick lookup
app_output.log                               # Runtime logs
```

### 2. CRITICAL DIRECTORIES (Already Well-Organized) ✅
```
src/                    # Application code (DO NOT MOVE)
config/                 # Configuration files
data/                   # Data files (Excel, JSON, database)
.github/                # GitHub workflows, instructions
backups/                # Backup data
docs/                   # Documentation
scripts/                # Utility scripts
test_templates/         # Test data
monitoring/             # Monitoring configs
assets/                 # UI assets
logo/                   # Logo assets
```

### 3. TEMPORARY/DEBUG SCRIPTS (70+ files) → `scripts/debug/`
These are one-off checks and debugging utilities:

**Mapping/Excel Checks:**
```
add_excel_mapping_to_edges.py
add_missing_columns.py
add_missing_columns_to_excel.py
auto_map_excel_flows.py
check_excel.py
check_excel_structure.py
check_invalid_mappings_all.py
check_unmapped_flows.py
fix_all_area_mappings.py
fix_area_mapping_v2.py
regenerate_excel_flows.py
regenerate_excel_from_json.py
verify_excel_json.py
verify_excel_vs_app.py
→ **Consolidate to**: `scripts/debug/excel_mapping/`
```

**Database/Structure Checks:**
```
check_db_schema.py
check_tables.py
check_diagram.py
check_json_structure.py
check_json_edges.py
check_flow_schema.py
verify_all_edges.py
check_diagram_nodes.py
extract_db_connections.py
→ **Consolidate to**: `scripts/debug/structure/`
```

**Area-Specific Checks (UG2N, Merensky, Old TSF, etc.):**
```
check_ug2n_data.py
check_ug2n_database.py
check_ug2n_loops.py
check_ug2n_sync.py
check_merensky_mappings.py
check_mern_columns.py
debug_merensky.py
debug_mern_categorization.py
debug_mern_loading.py
check_oldtsf_loops.py
add_oldtsf_loops.py
verify_ug2pcd1_mapping.py
check_ug2s_db.py
compare_ug2n.py
populate_ug2n_excel_from_diagram.py
list_oldtsf_cols.py
→ **Consolidate to**: `scripts/debug/area_specific/`
```

**Flow/Component Checks:**
```
check_enabled_edges.py
check_enabled_mappings.py
check_edge_mapping.py
check_edge_mappings.py
check_flow_labels.py
check_label_display.py
check_codes.py
check_path.py
check_templates.py
find_missing_flows.py
find_trtd_edges.py
query_components.py
→ **Consolidate to**: `scripts/debug/flow_checks/`
```

**Validation/Verification Scripts:**
```
verify_all_areas.py
verify_excel_fix.py
verify_autosync.py
verify_mern_mappings.py
verify_stockpile_fix.py
final_verify.py
final_verification.py
verify_corrected_excel.py
show_verification_summary.py
verify_configure_feature.py
→ **Consolidate to**: `scripts/debug/verification/`
```

**Miscellaneous Checks:**
```
check_rainfall.py
check_formatting.py
check_inter_area_columns.py
check_inter_area_flows.py
check_stockpile_mapping.py
check_dam_loops.py
check_all_areas.py
check_last_3.py
check_last_3_columns.py
check_tsf_split.py
check_mismatches.py
check_ref_guide.py
analyze_disabled_edges.py
compare_edge_configs.py
investigate_areas.py
check_master.py
debug_excel_contents.py
→ **Consolidate to**: `scripts/debug/misc/`
```

### 4. UTILITY/AUTOMATION SCRIPTS (20+ files) → `scripts/utilities/`
One-off fixes and automation tasks:

```
add_reference_guide.py
add_trp_clinic_columns.py
add_ug2n_loop.py
calculate_dam_recirculation.py
calculate_outflows.py
cleanup_old_guest_house_columns.py
create_area_diagrams.py
create_mern_sheet.py
dedupe_excel_and_json.py
detailed_outflows.py
enable_last_3_edges.py
enable_mappable_edges.py
final_fixes.py
final_status.py
fix_arrows.py
fix_categorization_and_excel.py
fix_categorization_final.py
fix_column_mismatches.py
fix_encoding.py
fix_encoding_and_remove_mern.py
fix_grid.py
fix_grid2.py
fix_inter_area.py
fix_inter_area_final.py
fix_json_arrows_final.py
fix_mers_merplant.py
fix_sheet_names.py
fix_stockpile_mappings.py
fix_ug2n_excel_mapping.py
inspect_mers.py
manage_column_aliases.py
map_excel_to_display.py
map_all_mern_edges.py
populate_area_diagrams.py
populate_missing_columns.py
rebuild_excel_structure.py
regenerate_excel_from_real_db.py
remove_mern.py
rename_component.py
rename_component_add_columns_TEMPLATE.py
reverse_flow_direction.py
setup_flow_sheets.py
sync_json_final.py
sync_json_to_excel_headers.py
temp_check.py
test_area_diagrams.py
test_config_feature.py
test_flow_diagram.py
test_flow_loader.py
test_junction_connections.py
test_manual_mapper_fix.py
test_singleton_reset.py
test_validation.py
update_excel_structure.py
update_excel_to_new_format.py
water_balance_check.py
```

### 5. DOCUMENTATION FILES (50+ .md files) → `docs/`
**Already good**: Some are in `docs/`, others scattered at root

**Component/Feature Guides (should consolidate into main docs):**
```
ADD_COMPONENTS_UI_GUIDE.md
AREA_EXCLUSION_FEATURE.md
AREA_SELECTOR_FIX.md
AREA_SELECTOR_QUICK_REFERENCE.md
AUTOMATED_COMPONENT_RENAME_GUIDE.md
AUTOMATION_GUIDE.md
BALANCE_CHECK_IMPLEMENTATION.md
BALANCE_CHECK_IMPLEMENTATION_SUMMARY.md
BALANCE_CHECK_PARAMETERS_COMPLETE_ANSWER.md
BALANCE_CHECK_QUICK_REFERENCE.md
BALANCE_CHECK_README.md
COMPONENT_RENAME_ARCHITECTURE.md
COMPONENT_RENAME_AUTOMATION_SUMMARY.md
COMPONENT_RENAME_GUIDE.md
COMPONENT_RENAME_QUICK_REFERENCE.md
COMPONENT_RENAME_SYSTEM_COMPLETE.md
COMPONENT_RENAME_SYSTEM_INDEX.md
COMPONENT_TEXT_SCALING_FIX.md
COMPONENT_TEXT_SCALING_QUICK_REF.md
COMPONENT_TEXT_SCALING_VISUAL_GUIDE.md
COLOR_PICKER_GUIDE.md
COMPLETE_WORKFLOW_UI_GUIDE.md
EXCEL_FLOW_MAPPING.md
EXCEL_INTEGRATION_SUMMARY.md
EXCEL_MAPPING_GUIDE.md
EXCEL_PATH_SWITCHING_FIX.md
EXCEL_PATH_SWITCHING_TEST.md
EXCEL_REGENERATION_SUMMARY.md
EXCEL_STRUCTURE_UPDATE_SUMMARY.md
EXCEL_VERIFICATION_SUMMARY.md
EXCEL_INTEGRATION_SUMMARY.md
FEATURE_UPDATE_RIGHT_CLICK.md
FEATURE_VERIFICATION_REPORT.md
FLOW_DIAGRAM_BEFORE_AFTER.md
FLOW_DIAGRAM_EDITOR_GUIDE.md
FLOW_DIAGRAM_FEATURE.md
FLOW_DIAGRAM_FEATURES.md
FLOW_DIAGRAM_GUIDE.md
FLOW_DIAGRAM_NEW_APPROACH.md
FLOW_DIAGRAM_SOLUTION.md
FLOW_DIAGRAM_UPDATE_SUMMARY.md
FLOW_DIAGRAM_VISUAL_GUIDE.md
FLOW_DIAGRAM_VISUAL_STRUCTURE.md
FLOW_LABELS_COMPLETE.md
FLOW_LABEL_STATUS.md
FONT_CONTROLS_FEATURE.md
GUEST_HOUSE_TO_TRP_CLINIC_COMPLETE.md
IMPLEMENTATION_COMPLETE.md
INTERACTIVE_EDITOR_COMPLETE.md
INTERACTIVE_EDITOR_GUIDE.md
INTERACTIVE_EDITOR_QUICK_REFERENCE.md
JUNCTION_CONNECTIONS_GUIDE.md
JUNCTION_QUICK_START.md
MAPPING_SOLUTION_COMPLETE.md
MANUAL_MAPPER_FIX.md
MASTER_DIAGRAM_ARCHITECTURE.md
RIGHT_CLICK_CONTEXT_MENU_GUIDE.md
RIGHT_CLICK_FEATURE_DOCUMENTATION_INDEX.md
RIGHT_CLICK_FEATURE_IMPLEMENTATION_COMPLETE.md
RIGHT_CLICK_IMPLEMENTATION_SUMMARY.md
RIGHT_CLICK_QUICK_REFERENCE.md
SYNC_AUTOMATION_GUIDE.md
UI_ADD_COMPONENTS_FEATURE.md
UI_ENHANCEMENTS_SUMMARY.md
→ **Move all to**: `docs/features/` or consolidate into existing feature documentation
```

**Status/Summary Reports (temporary, should be archived or deleted):**
```
BEFORE_AFTER_COMPARISON.md
CALCULATION_REVIEW.md
COMPLETE_WORKFLOW_UI_GUIDE.md
CONFIGURE_BALANCE_CHECK_IMPLEMENTATION.md
CONFIGURE_FEATURE_COMPLETE.md
CONFIGURE_QUICK_START.md
COPILOT_INSTRUCTIONS_UPDATE.md
DECIMAL_FONT_SIZES_IMPLEMENTATION.md
DELIVERY_PACKAGE_RIGHT_CLICK_FEATURE.md
DETAILED_NETWORK_DIAGRAM.md
DIAGRAM_FIXES_SUMMARY.md
DIAGRAM_RESTRUCTURE_SUMMARY.md
DYNAMIC_LABELS_PLAN.md
EDIT_ALL_MAPPINGS_GUIDE.md
ENHANCED_FLOW_DIAGRAM_SUMMARY.md
ENHANCEMENT_VALIDATION_REPORT.md
EXACT_FILE_LOCATIONS.md
FINAL_EXCEL_SUMMARY.md
FINAL_SUMMARY.md
IMPLEMENTATION_COMPLETE.md
PARAMETER_ACTIVATION_CODE_FLOW.md
PARAMETER_DATA_FLOW.md
PARAMETER_SOURCES_QUICK_REFERENCE.md
PHASE_1_IMPLEMENTATION.md
QUICK_REFERENCE_ADD_COMPONENTS.md
QUICK_START_EXCEL_FLOWS.md
README_INTERACTIVE_EDITOR.md
README_RIGHT_CLICK_FEATURE.md
SESSION_SUMMARY_COMPONENT_RENAME_SYSTEM.md
VALIDATION_FIX_SUMMARY.md
VALUE_DISPLAY_UPDATE.md
VERIFICATION_COMPLETE.txt
→ **Archive to**: `docs/archive/` (they may contain useful context)
```

### 6. OBSOLETE/REDUNDANT FILES (Delete) ❌
```
outflows_analysis.txt               # One-time analysis, data in code
disabled_edges_categorized.json     # Data captured in system
excel_mapping_gui.py                # Functionality in UI, not maintained
flow_diagram_editor.py              # Replaced by integrated editor
demo_mapping_features.py            # Demo script, not part of app
```

---

## Consolidation Strategy

### Phase 1: Create Directory Structure
```bash
mkdir -p scripts/debug/{excel_mapping,structure,area_specific,flow_checks,verification,misc}
mkdir -p docs/archive
mkdir -p docs/features
```

### Phase 2: Move Files
1. Move all 70+ debug scripts to `scripts/debug/` subdirectories
2. Move all utility scripts to `scripts/utilities/`
3. Move documentation to `docs/features/` or `docs/archive/`

### Phase 3: Update Documentation
- Create `scripts/debug/README.md` with index of all debug utilities
- Create `docs/features/INDEX.md` consolidating all feature documentation
- Update main `README.md` with directory structure guide

### Phase 4: Delete Obsolete Files
- Remove demo files, one-time analysis outputs
- Keep backups in `backups/` directory

---

## Recommended Structure After Cleanup

```
Water-Balance-Application/
├── src/                           ✅ Keep as-is
├── config/                        ✅ Keep as-is
├── data/                          ✅ Keep as-is
├── .github/                       ✅ Keep as-is
├── docs/
│   ├── features/                  📍 Move feature docs here
│   ├── archive/                   📍 Archive old status reports
│   ├── DATABASE.md                (already here)
│   ├── FLOW_DIAGRAM_GUIDE.md      (already here)
│   └── BALANCE_CHECK_README.md    (move here)
├── scripts/
│   ├── debug/                     📍 Consolidate debug tools
│   │   ├── excel_mapping/
│   │   ├── structure/
│   │   ├── area_specific/
│   │   ├── flow_checks/
│   │   ├── verification/
│   │   ├── misc/
│   │   └── README.md
│   ├── utilities/                 📍 Consolidate one-off fixes
│   └── README.md
├── backups/                       ✅ Keep as-is
├── assets/                        ✅ Keep as-is
├── logo/                          ✅ Keep as-is
├── monitoring/                    ✅ Keep as-is
├── test_templates/                ✅ Keep as-is
├── logs/                          ✅ Keep as-is
├── README.md                      ✅ Update with new structure
├── requirements.txt               ✅ Keep
├── component_rename_config.json   ✅ Keep
├── *.txt (templates)              ✅ Keep
└── .git*, .venv/, .vscode/       ✅ Keep (hidden/reserved)
```

**Result**: From 200+ root files → ~15 essential files at root + organized subdirectories

---

## Implementation Plan

### Quick Wins (Low Risk):
1. ✅ Create `scripts/debug/` and move check scripts
2. ✅ Create `scripts/utilities/` and move fix scripts  
3. ✅ Create `docs/archive/` and move status reports
4. ✅ Create `docs/features/` and consolidate feature guides

### Medium Effort (Review First):
1. ✅ Create index/README files for each new directory
2. ✅ Update navigation in main README.md
3. ✅ Delete obsolete files

### Documentation Updates:
1. Update `README.md` with new directory guide
2. Create `scripts/debug/README.md` with script index
3. Create `docs/features/INDEX.md` with feature guide index

---

## Summary Table

| Category | Count | Action | New Location |
|----------|-------|--------|--------------|
| Root Essentials | 8 | Keep | Root |
| Core Directories | 10+ | Keep | Original |
| Debug Scripts | 70+ | Move | `scripts/debug/` |
| Utility Scripts | 50+ | Move | `scripts/utilities/` |
| Feature Docs | 45+ | Move | `docs/features/` |
| Status Reports | 30+ | Archive | `docs/archive/` |
| Obsolete Files | 5 | Delete | - |
| **TOTAL** | **220+** | → Consolidated | ~20 root + organized |

---

## Next Steps

1. **Approve this analysis** - Review categories and confirm deletions
2. **Execute Phase 1-4** above (can be automated with shell scripts)
3. **Verify nothing broken** - Ensure imports/references still work
4. **Update documentation** - Refresh README with new structure

This will reduce cognitive load significantly and make the repository much easier to navigate.
