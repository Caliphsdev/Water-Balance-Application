# Component Rename Quick Reference

## 📋 Quick Start (Copy-Paste)

### Rename Any Component in 3 Steps

```bash
# Step 1: Edit configuration
# Edit component_rename_config.json and add/modify:
{
  "component_renames": [
    {
      "old_name": "existing_component_name",
      "new_name": "new_component_name",
      "excel_columns": [
        "OLD_NAME → DESTINATION",
        "DESTINATION → NEW_NAME"
      ],
      "description": "Why you're renaming this"
    }
  ]
}

# Step 2: Preview (ALWAYS RUN THIS FIRST)
python component_rename_manager.py --dry-run

# Step 3: Apply
python component_rename_manager.py
```

## 🎯 Common Scenarios

### Scenario 1: Rename One Component
```json
{
  "old_name": "offices",
  "new_name": "office_building",
  "excel_columns": ["OFFICE_BUILDING → SEWAGE"],
  "description": "Renamed for clarity"
}
```

### Scenario 2: Rename Multiple Related Components
```json
[
  {
    "old_name": "ndcd",
    "new_name": "ndcd_reservoir",
    "excel_columns": ["RAINFALL → NDCD_RESERVOIR"],
    "description": "Clarify it's a reservoir"
  },
  {
    "old_name": "spill",
    "new_name": "spillway_discharge",
    "excel_columns": ["NDCD_RESERVOIR → SPILLWAY_DISCHARGE"],
    "description": "More descriptive name"
  }
]
```

## 🛠️ All Commands

```bash
# List pending renames
python component_rename_manager.py --list

# Preview changes (safe, no modifications)
python component_rename_manager.py --dry-run

# Apply all renames
python component_rename_manager.py

# Use custom config file
python component_rename_manager.py --config custom_config.json
```

## 📊 What Gets Updated

| Component | Updated | Example |
|-----------|---------|---------|
| JSON Node IDs | ✓ | `guest_house` → `trp_clinic` |
| JSON Edge From/To | ✓ | `rainfall → guest_house` → `rainfall → trp_clinic` |
| JSON Edge Mappings | ✓ | `RAINFALL → GUEST_HOUSE` → `RAINFALL → TRP_CLINIC` |
| Excel Columns | ✓ | New column added in correct sheet |
| All 8 Flow Sheets | ✓ | UG2N, UG2P, UG2S, OLDTSF, MERN, MERP, MERS, STOCKPILE |

## ⚠️ Important Notes

1. **Always preview first**: `--dry-run` shows exactly what will change
2. **One configuration file**: All renames in `component_rename_config.json`
3. **Batch processing**: Run multiple renames with one command
4. **Excel columns required**: Each rename needs at least one Excel column
5. **Column format**: Use `SOURCE → DESTINATION` format

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No component renames configured" | Check `component_rename_config.json` exists and has valid JSON |
| "Invalid rename config" | Ensure `old_name` and `new_name` are specified |
| Column not added | Verify column format: `OLD_NAME → NEW_NAME` |
| Changes didn't apply | Check file permissions; Excel file shouldn't be open |
| Unexpected behavior | Run `--dry-run` first to preview changes |

## 📝 Configuration Template

```json
{
  "component_renames": [
    {
      "old_name": "component_to_rename",
      "new_name": "new_component_name",
      "excel_columns": [
        "NEW_NAME → DESTINATION1",
        "NEW_NAME → DESTINATION2"
      ],
      "description": "Brief reason for rename"
    }
  ],
  "files": {
    "json_diagram": "data/diagrams/ug2_north_decline.json",
    "excel_template": "test_templates/Water_Balance_TimeSeries_Template.xlsx"
  },
  "settings": {
    "auto_backup": true,
    "validate_after_rename": true
  }
}
```

## ✨ Capabilities

- ✅ Single rename
- ✅ Batch renames (multiple at once)
- ✅ Dry-run preview
- ✅ Configuration-based (no code changes)
- ✅ JSON + Excel sync
- ✅ Auto sheet detection
- ✅ Edge mapping updates
- ✅ Automatic backup support

## 🚀 Time Comparison

| Task | Manual | Automated |
|------|--------|-----------|
| Rename one component | 20-30 min | 3-5 min |
| Rename three components | 60+ min | 5-7 min |
| Add new flow sheet | 15 min | 0 min (auto) |
| Risk of errors | High | None |

## 📚 Full Documentation

See [AUTOMATED_COMPONENT_RENAME_GUIDE.md](AUTOMATED_COMPONENT_RENAME_GUIDE.md) for:
- Detailed workflow
- Step-by-step examples
- Best practices
- Advanced usage
- Automation ideas

## 💡 Pro Tips

1. **Test with dry-run first**
   ```bash
   python component_rename_manager.py --dry-run
   # Review output carefully!
   ```

2. **Batch related renames**
   ```json
   "component_renames": [
     {"old_name": "a", ...},
     {"old_name": "b", ...},
     {"old_name": "c", ...}
   ]
   ```
   Then run once - all three renamed!

3. **Keep git history clean**
   ```bash
   git add component_rename_config.json
   git commit -m "Rename offices → office_building for clarity"
   ```

4. **Descriptive names matter**
   ```json
   "description": "Renamed to clarify this is a treated water storage area"
   ```

## 🎓 Example: Complete Workflow

```bash
# 1. Edit config
cat << 'EOF' > component_rename_config.json
{
  "component_renames": [
    {
      "old_name": "offices",
      "new_name": "office_building",
      "excel_columns": ["OFFICE_BUILDING → CONSUMPTION"],
      "description": "More descriptive name"
    }
  ],
  ...
}
EOF

# 2. Preview (always first!)
python component_rename_manager.py --dry-run
# Output shows: 3 JSON changes, 1 Excel change

# 3. Apply
python component_rename_manager.py
# Output: Changes applied successfully

# 4. Validate
python test_validation.py
# Output: All checks passed ✓

# 5. Commit
git add -A
git commit -m "Rename offices → office_building"
```

Done! The system updated everything automatically. 🎉

---

**See full guide**: [AUTOMATED_COMPONENT_RENAME_GUIDE.md](AUTOMATED_COMPONENT_RENAME_GUIDE.md)
