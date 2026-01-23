# Help Dashboard Maintenance Checklist

**Last Updated:** January 23, 2026  
**For:** Admins, Maintainers, Future Developers

---

## About This Checklist

This document helps ensure the Help Dashboard stays accurate and complete as the app evolves.

---

## When to Update Help Dashboard

### 🔴 HIGH PRIORITY - Update Immediately

- [ ] **New Feature Added**
  - Add to Features Tab with description
  - Add access path in UI
  - Document configuration options
  - Add troubleshooting if applicable

- [ ] **Calculation Changed**
  - Update Calculations Tab
  - Update Formulas Tab
  - Update affected examples
  - Test formulas in code

- [ ] **Settings/Configuration Changed**
  - Update Features Tab → Configuration & Settings
  - Update exact setting path
  - Update default values
  - Note if breaking change

- [ ] **Database Schema Changed**
  - Update Data Sources Tab
  - Update table descriptions
  - Note new columns/fields
  - Update any formulas using those fields

### 🟡 MEDIUM PRIORITY - Update Soon

- [ ] **Bug Fix**
  - If it fixes common user issue, add to Troubleshooting
  - Remove old workaround if applicable
  - Verify solution still works

- [ ] **UI Path Changes**
  - Search for all references to old path
  - Update with new access location
  - Test that path works

- [ ] **Constants Updated**
  - Update Features Tab → Constants section
  - Update app_config.yaml reference
  - Verify new defaults in code

### 🟢 LOW PRIORITY - Update When Convenient

- [ ] **Documentation Improved**
  - Clarify confusing sections
  - Add examples
  - Improve formatting

- [ ] **Minor Wording Changes**
  - Fix typos
  - Improve clarity
  - Update outdated references

---

## Checklist: Adding a New Feature to Help

When adding new feature documentation:

### 1. Planning
- [ ] Identify feature category (Storage, Calculation, Feature, etc.)
- [ ] Determine complexity level (simple vs complex)
- [ ] Gather: description, formula, config options, troubleshooting

### 2. Documentation
- [ ] Write clear title with emoji/icon
- [ ] Add description (what user needs to know)
- [ ] Add access path (where to find in UI)
- [ ] Add configuration section (if applicable)
- [ ] Add example (if helpful)
- [ ] Add related troubleshooting (if applicable)

### 3. Integration
- [ ] Add to appropriate Tab section
- [ ] Link to Settings if configuration-based
- [ ] Reference in related sections
- [ ] Add to Features list if major feature

### 4. Testing
- [ ] Verify all UI paths exist
- [ ] Verify all references are accurate
- [ ] Test that examples work
- [ ] Verify syntax is valid
- [ ] Check for typos and clarity

### 5. Cross-Linking
- [ ] Add to Troubleshooting if applicable
- [ ] Reference from Formulas tab if calculation
- [ ] Link from Features tab
- [ ] Note in Quick Reference docs

---

## Checklist: Fixing Outdated Information

When discovering outdated info:

### 1. Identification
- [ ] Note exact location (Tab and section)
- [ ] Identify what's wrong (old path, old value, removed feature)
- [ ] Find current correct information
- [ ] Verify against actual code

### 2. Verification
- [ ] Check app_config.yaml for current values
- [ ] Check settings.py for current UI paths
- [ ] Check schema.py for database structure
- [ ] Check relevant feature code

### 3. Update
- [ ] Replace with accurate information
- [ ] Verify syntax is correct
- [ ] Test that paths work
- [ ] Run py_compile to check syntax

### 4. Cross-Reference Check
- [ ] Update related sections if needed
- [ ] Update Quick Reference docs
- [ ] Update related tabs
- [ ] Note in commit message

---

## Key Settings to Track

These commonly change - monitor them:

### Environmental Parameters
```
Location: Settings → Environmental Parameters
Check if changed:
  • evaporation_zone (should be 4A)
  • Monthly rainfall values (if updated)
  • Monthly evaporation values (if updated)
```

### System Constants
```
Location: Settings → Constants
Check if changed:
  • lined_seepage_rate_pct (should be 0.1)
  • unlined_seepage_rate_pct (should be 0.5)
  • ore_moisture_percent (should be 3.4)
  • ore_density_tonnes_per_m3 (should be 2.7)
```

### Data Sources
```
Location: app_config.yaml
Check if changed:
  • legacy_excel_path (Meter Readings file)
  • timeseries_excel_path (Flow Diagram file)
  • database path
  • template paths
```

### Calculation Thresholds
```
Location: settings.py and database
Check if changed:
  • Closure error threshold (should be 5%)
  • Pump start level (should be 70%)
  • Pump stop level (should be 20%)
  • Transfer increment (should be 5%)
```

---

## Files to Monitor for Changes

When these files change, consider Help Dashboard updates:

### High Impact
- `src/utils/water_balance_calculator.py` - Formulas, calculations
- `src/database/schema.py` - Database structure
- `src/ui/storage_facilities.py` - Facility configuration
- `src/ui/settings.py` - Settings/configuration
- `config/app_config.yaml` - Configuration values

### Medium Impact
- `src/ui/flow_diagram_dashboard.py` - Flow diagram features
- `src/utils/pump_transfer_engine.py` - Pump transfer logic
- `src/licensing/license_manager.py` - Licensing features

### Reference Impact
- `src/ui/calculations.py` - Calculation tab access
- `src/database/db_manager.py` - Database operations
- `src/main.py` - Startup sequence

---

## Syntax & Format Checklist

When adding to Help Documentation:

### Code Format
- [ ] Uses `self._add_section()` for headers
- [ ] Uses `self._add_formula()` for formulas
- [ ] Proper indentation (4 spaces)
- [ ] Proper string quotes
- [ ] Tab name parameter included

### Content Format
- [ ] Clear, user-friendly language
- [ ] No jargon (or explain if necessary)
- [ ] Organized with bullet points where applicable
- [ ] Related items grouped together
- [ ] Examples provided for complex items

### Formula Format
- [ ] Includes EQUATION line
- [ ] Includes INPUT line
- [ ] Includes OUTPUT line
- [ ] Includes NOTES/explanation
- [ ] Shows example calculation

### Troubleshooting Format
- [ ] Starts with "Cause:" section
- [ ] Lists "Investigation Steps:" (numbered)
- [ ] Includes "How to Fix:" with clear instructions
- [ ] References related configuration

---

## Testing After Updates

After any Help Dashboard changes:

```bash
# 1. Syntax Check
.venv\Scripts\python -m py_compile src/ui/help_documentation.py

# 2. Import Test
.venv\Scripts\python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('src'))); from ui.help_documentation import HelpDocumentation; print('✅ Success')"

# 3. Manual Verification
- Open app
- Click Help button
- Navigate through all tabs
- Verify new content displays
- Verify all links/paths work
- Check formatting looks correct
```

---

## Common Maintenance Tasks

### Task: Update Evaporation Values
**Frequency:** Annually (when environmental data updates)

```
1. Go to Settings → Environmental Parameters
2. Check Regional Evaporation values
3. If changed, update Help Dashboard:
   → Storage Tab → "Rainfall & Evaporation in Storage"
   → Troubleshooting → "Evaporation values too high/low"
   → Note typical ranges in description
4. Update Quick Reference document
```

### Task: Add New Feature Documentation
**Frequency:** Per new feature release

```
1. Identify feature category (Storage, Calculation, etc.)
2. Find feature code to understand it
3. Create section in appropriate Help tab
4. Add to Features Tab → Features list
5. Add troubleshooting if applicable
6. Test syntax and links
7. Verify in running app
```

### Task: Fix User-Reported Inaccuracy
**Frequency:** As discovered

```
1. Verify the error
2. Check actual implementation in code
3. Update Help Dashboard with correct info
4. Test the fix
5. Add to changelog
6. Consider adding to Troubleshooting
```

### Task: Quarterly Review
**Frequency:** Every 3 months

```
1. Check for any moved UI elements
2. Verify all Settings paths still valid
3. Check for new features not documented
4. Review recent bug fixes
5. Update Troubleshooting with new common issues
6. Test py_compile
7. Verify module imports
```

---

## Red Flags - What Should Trigger Updates

- ❌ User asks "how do I...?" about something not in Help
- ❌ Help describes feature that no longer exists
- ❌ UI path mentioned in Help doesn't work
- ❌ Formula or value in Help doesn't match code
- ❌ New feature added but not documented
- ❌ Setting moved to different location
- ❌ Database table renamed or restructured
- ❌ Troubleshooting solution doesn't work anymore

---

## Documentation Standards

### For All New Sections

**MUST HAVE:**
- ✅ Clear title
- ✅ Purpose statement
- ✅ How to access (UI path)
- ✅ Step-by-step instructions

**SHOULD HAVE:**
- ✅ Related settings/configuration
- ✅ Examples or use cases
- ✅ Cross-reference to related topics
- ✅ Common issues/variations

**NICE TO HAVE:**
- ✅ Formulas or equations
- ✅ Typical values or ranges
- ✅ Pro tips or best practices
- ✅ Warning about common mistakes

### Clarity Standards

**User Should Understand:**
- What the feature does
- Why they might use it
- How to access it
- How to configure it
- Common issues and fixes

**NO Jargon Without Explanation:**
- Define technical terms first
- Link to related topics
- Provide context

---

## Version History

| Date | Author | Changes |
|------|--------|---------|
| Jan 23, 2026 | AI Assistant | Initial comprehensive audit; Added evaporation documentation; Updated features list |
| | | Updated troubleshooting; Enhanced storage section; Added pump transfer & licensing docs |

---

## Useful Code References

When updating, reference these key files:

| Information Type | Source File |
|------------------|-------------|
| Calculations/Formulas | `src/utils/water_balance_calculator.py` |
| Database Structure | `src/database/schema.py` |
| Settings/Configuration | `src/ui/settings.py` and `config/app_config.yaml` |
| Storage Facility Features | `src/ui/storage_facilities.py` |
| Flow Diagram Features | `src/ui/flow_diagram_dashboard.py` |
| Pump Transfer Logic | `src/utils/pump_transfer_engine.py` |
| Licensing System | `src/licensing/license_manager.py` |

---

## Contact & Escalation

If you encounter Help Dashboard issues:

1. **Syntax Error?**
   - Run: `.venv\Scripts\python -m py_compile src/ui/help_documentation.py`
   - Fix the line number shown

2. **Inaccurate Information?**
   - Verify against source code
   - Update with correct info
   - Test in running app

3. **Feature Not Documented?**
   - Add new section
   - Include access path
   - Add to Features tab
   - Consider troubleshooting

4. **UI Path Broken?**
   - Find new path in actual app
   - Update all references
   - Test path works

---

**Maintenance Standards:** ✅ ESTABLISHED AND DOCUMENTED
