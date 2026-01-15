# Production Directory Cleanup Plan
## Water Balance Application - PyInstaller & Inno Setup Preparation

### Current Status
- **Total .md files**: 146 files
- **Target**: 15 essential documentation files
- **Debug scripts**: Multiple test/debug scripts in root and scripts/
- **Backup files**: Unused database backups
- **Log files**: Development logs to be cleared

---

## Phase 1: Documentation Consolidation (146 → 15 files)

### Keep in Root (5 files)
1. **README.md** - Main project overview and quick start
2. **DOCUMENTATION_INDEX.md** - Central index to all documentation
3. **CHANGELOG.md** - Version history (to be created)
4. **LICENSE.txt** - Software license (to be created)
5. **INSTALLATION.md** - Installation and deployment guide (to be created)

### Keep in docs/ (10 files max)
1. **docs/USER_GUIDE.md** - Consolidated end-user manual
2. **docs/DEVELOPER_GUIDE.md** - Consolidated developer documentation
3. **docs/LICENSING_GUIDE.md** - Licensing system guide
4. **docs/BALANCE_CHECK_GUIDE.md** - Balance check system
5. **docs/FLOW_DIAGRAM_GUIDE.md** - Already exists, keep
6. **docs/EXCEL_INTEGRATION.md** - Excel data integration
7. **docs/CONFIGURATION.md** - App configuration reference
8. **docs/TROUBLESHOOTING.md** - Common issues and solutions
9. **docs/API_REFERENCE.md** - Internal API documentation
10. **docs/DEPLOYMENT.md** - Deployment and packaging guide

### Archive (Move to docs/archive/)
- All session summaries
- All implementation summaries
- All quick reference duplicates
- All "COMPLETE" status files
- Feature-specific docs (consolidate into USER_GUIDE)

### Delete Completely
- UI/UX session files (work completed)
- Auto-recovery session files (work completed)
- Verification/completion reports
- Debug/fix summaries

---

## Phase 2: Script Cleanup

### Keep in scripts/ (Production utilities)
1. **component_rename_manager.py** - Component renaming tool
2. **generate_timeseries_template.py** - Template generator
3. **seed_timeseries_sheets.py** - Database seeding
4. **activate_all_facilities.py** - Facility activation utility

### Delete from Root
- check_license_status.py → Move to scripts/utilities/
- clear_license.py → Move to scripts/utilities/
- simple_license_check.py → Move to scripts/utilities/
- test_*.py (all test files) → Delete (tests in pytest)
- startup_debug.log → Delete

### Delete from scripts/
- smoke_test_balance.py
- test_*.py files
- migrate_license_verification_limit.py (migration complete)
- comprehensive_edge_mapping_audit.py (audit complete)
- scripts/debug/ (entire folder)

---

## Phase 3: Data Cleanup

### Keep
- water_balance.db (production database)
- *.json config files
- templates/ folder
- diagrams/ folder (clean up .bak files)

### Delete
- water_balance.db.new (backup)
- excel_cache.sqlite (will regenerate)
- All .bak and .backup files in diagrams/

---

## Phase 4: Log Cleanup

### Action
- Clear contents of logs/errors.log (keep empty file)
- Clear contents of logs/water_balance.log (keep empty file)
- Delete startup_debug.log from root

---

## Phase 5: Asset Organization

### Create Structure
```
assets/
  ├── icons/
  │   ├── app_icon.ico (256x256 for Windows)
  │   ├── app_icon.png (for about dialog)
  │   └── installer_icon.ico (for Inno Setup)
  └── images/
      └── splash.png (if needed)
```

### Update Paths in Code
- src/main.py: Update icon path
- Inno Setup script: Reference assets/icons/installer_icon.ico

---

## Phase 6: Additional Cleanup

### Delete Folders
- .pytest_cache/
- __pycache__/ (all instances - will regenerate)
- test_templates/ (if empty or unused)
- new_templates/ (if not needed)
- reports/ (if empty or development only)
- .playwright-mcp/ (development tool)

### Keep Folders
- .git/ (version control)
- .github/ (CI/CD if used)
- .venv/ (development only - exclude from distribution)
- .vscode/ (development only - exclude from distribution)
- config/ (production configs)
- backups/ (check if needed)

---

## Phase 7: PyInstaller Preparation

### Create Files
1. **build_spec.spec** - PyInstaller spec file
2. **.spec** configurations for:
   - Icon path
   - Data files inclusion
   - Hidden imports
   - Exclude modules

### Update .gitignore
Add:
```
# Build artifacts
build/
dist/
*.spec
*.exe
*.msi

# Logs
logs/*.log
!logs/.gitkeep

# Cache
__pycache__/
*.pyc
*.pyo
.pytest_cache/
```

---

## Phase 8: Inno Setup Preparation

### Create
1. **installer.iss** - Inno Setup script
2. **installer/assets/** - Installer-specific assets
3. **installer/license.txt** - EULA for installation

---

## Expected Results

### Before Cleanup
- **Total files**: 500+ files
- **.md files**: 146 files
- **Scripts**: 20+ files
- **Directory size**: Large with many redundant files

### After Cleanup
- **Total files**: <200 essential files
- **.md files**: 15 files
- **Scripts**: 4-8 production utilities
- **Directory size**: 30-50% reduction
- **Ready for**: PyInstaller and Inno Setup packaging

---

## Execution Order

1. ✅ Create consolidated documentation files
2. ✅ Move files to archive
3. ✅ Delete redundant files
4. ✅ Clean up scripts
5. ✅ Clear logs
6. ✅ Remove backup databases
7. ✅ Clean diagrams folder
8. ✅ Setup assets structure
9. ✅ Create PyInstaller spec
10. ✅ Create Inno Setup script
11. ✅ Test build process
12. ✅ Final verification

---

**Status**: Ready for approval and execution
**Estimated time**: 30-45 minutes
**Risk level**: Low (all changes are file management, no code changes)
