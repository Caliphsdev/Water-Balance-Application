# 🧪 Excel Path Switching - Test Plan

## What Was Fixed

**Problem:** Settings path changes weren't taking effect because:
1. `FlowVolumeLoader` is a singleton (created once, never recreated)
2. Path was cached in `self.excel_path` at initialization
3. Even with config reload, singleton instance kept the old path

**Solution:**
1. Added `reset_flow_volume_loader()` function to clear singleton instance
2. Settings now calls this reset after updating paths
3. Flow diagram re-gets loader instance before loading from Excel

## Test Workflow

### Test 1: Switch from POPULATED to TEMPLATE

**Setup:**
- Current state: Config has `timeseries_excel_path: ...POPULATED.xlsx` (19 flows)
- Target state: Switch to template (1 flow - only bh_ndgwa)

**Steps:**
1. Launch app: `python src/main.py`
2. Navigate to **Flow Diagram** module
3. Click **"📥 Load from Excel"**
4. Select **December 2024**
5. **Expected:** Should load 19 flows from POPULATED file
6. **Verify:** Check flow labels on diagram show values like:
   - bh_ndgwa → ndcd: 3000 m³
   - freshwater_supply → ndcd: 15000 m³
   - etc. (19 total flows)

7. Navigate to **⚙️ Settings** module
8. Go to **📂 Data Sources** tab
9. Click **"📁 Browse"** next to Application Inputs
10. Select: `test_templates\Water_Balance_TimeSeries_Template.xlsx` (TEMPLATE)
11. Click **"Apply"**
12. **Expected:** Success message shown
13. **Verify:** Path label shows `test_templates\Water_Balance_TimeSeries_Template.xlsx`

14. Navigate back to **Flow Diagram**
15. Click **"📥 Load from Excel"** again
16. Select **December 2024**
17. **Expected:** Should load only 1 flow from TEMPLATE
18. **Verify:** Check flow labels:
    - bh_ndgwa → ndcd: 1000 m³ (from template)
    - freshwater_supply → ndcd: **"-"** (no data in template)
    - All other flows: **"-"** (no data)

### Test 2: Switch back to POPULATED

**Steps:**
1. Still in **Flow Diagram** module
2. Navigate to **⚙️ Settings**
3. Go to **📂 Data Sources** tab
4. Click **"📁 Browse"**
5. Select: `test_templates\Water_Balance_TimeSeries_Template_POPULATED.xlsx`
6. Click **"Apply"**
7. Navigate back to **Flow Diagram**
8. Click **"📥 Load from Excel"**
9. Select **December 2024**
10. **Expected:** Should load all 19 flows again
11. **Verify:** All flow labels show values (not "-")

### Test 3: Excel Edits Refresh

**Steps:**
1. Open Excel file: `Water_Balance_TimeSeries_Template_POPULATED.xlsx`
2. Go to **"Flows_UG2N"** sheet
3. Find row with **bh_ndgwa** in Column A
4. Change December value from **3000** to **9999**
5. Save Excel file
6. Go back to app (Flow Diagram)
7. Click **"📥 Load from Excel"**
8. Select **December 2024**
9. **Expected:** bh_ndgwa flow label shows **9999 m³**
10. **Verify:** Cache was cleared, fresh data loaded

### Test 4: Invalid Path Handling

**Steps:**
1. Navigate to **⚙️ Settings** → **📂 Data Sources**
2. Click **"📁 Browse"**
3. Type in a non-existent path: `fake_file.xlsx`
4. **Expected:** Status shows "❌ Missing"
5. Navigate to **Flow Diagram**
6. Click **"📥 Load from Excel"**
7. **Expected:** Error message (file not found)

## Success Criteria

✅ Test 1: Template file loads only 1 flow, rest show "-"
✅ Test 2: Populated file loads all 19 flows
✅ Test 3: Excel edits immediately reflected in diagram
✅ Test 4: Invalid path shows error gracefully

## Verification Checklist

- [ ] Settings path change triggers singleton reset (check logs: "🔄 Flow volume loader reset")
- [ ] Config file updated with new path (check `config/app_config.yaml`)
- [ ] Flow diagram re-gets loader before loading (check logs: "📥 Loading flows from Excel")
- [ ] Cache cleared on each load (check logs)
- [ ] No errors in app or logs
- [ ] All 21 mapped edges load correctly from Excel
- [ ] Unmapped edges show "-" (no data)

## Debug Commands

If something doesn't work, run these to investigate:

```powershell
# Check current config
Get-Content config\app_config.yaml | Select-String "excel_path"

# Run singleton test
python test_singleton_reset.py

# Check flow diagram JSON
Get-Content data\diagrams\ug2_north_decline.json | Select-String "excel_mapping" | Select-Object -First 5

# Check Excel file exists
Test-Path test_templates\Water_Balance_TimeSeries_Template.xlsx
Test-Path test_templates\Water_Balance_TimeSeries_Template_POPULATED.xlsx
```

## Technical Details

**Files Changed:**
1. `src/utils/flow_volume_loader.py`:
   - Added `reset_flow_volume_loader()` function
   - Line ~280: Reset global `_loader_instance` to None

2. `src/ui/settings_revamped.py`:
   - Line ~714: Call `reset_flow_volume_loader()` after path change
   - Updates both `template_excel_path` and `timeseries_excel_path`

3. `src/ui/flow_diagram_dashboard.py`:
   - Line ~2505: Re-get loader before loading from Excel
   - Added `refresh_flow_loader()` helper method

**Singleton Pattern:**
```python
# Before path change
loader1 = get_flow_volume_loader()  # ID: 123456, Path: POPULATED

# Settings changes path and resets
reset_flow_volume_loader()  # Clears global instance

# After reset
loader2 = get_flow_volume_loader()  # ID: 789012, Path: TEMPLATE (NEW!)
```

**Config Priority:**
1. `timeseries_excel_path` (used first)
2. `template_excel_path` (fallback)
3. Default hardcoded path (last resort)

## Expected Logs

When test works correctly, you should see:

```
18:56:12 | INFO | 🔄 Flow volume loader reset
18:56:13 | INFO | 🔄 Flow loader reset after path change to: test_templates\Water_Balance_TimeSeries_Template.xlsx
18:56:14 | INFO | 📥 Loading flows from Excel: UG2N for 2024-12
18:56:14 | INFO | ✅ Loaded 1 flows from Excel
```

---

**Ready to test!** Follow the steps above and report any issues.
