# 🤖 AUTOMATED EXCEL MAPPING SOLUTIONS

## Quick Summary
We've created **2 automated solutions** so you never have to manually edit JSON again:

1. **Auto-Map Script** - Command-line tool (3 seconds to map all flows)
2. **Mapping GUI** - Point-and-click interface (visual, user-friendly)

---

## Solution 1: Auto-Map Script (EASIEST)

### For Non-Programmers
This is the fastest way. Just run one command:

```bash
python auto_map_excel_flows.py
```

**What it does:**
- ✅ Reads all flows from JSON
- ✅ Reads all columns from Excel
- ✅ Automatically matches flows to columns
- ✅ Adds excel_mapping to every flow
- ✅ Saves to JSON automatically
- ✅ Takes ~3 seconds

**Result:**
```
AUTO-MAPPING FLOWS TO EXCEL COLUMNS
======================================================================
✅ MAPPED: oldtsf_old_tsf_rainr → oldtsf_old_tsf
   Column: oldtsf_old_tsf_rainrun__TO__oldtsf_old_tsf
✅ MAPPED: oldtsf_gwa_boreholes → oldtsf_offices
   Column: oldtsf_gwa_boreholes__TO__oldtsf_offices
... (111 flows mapped) ...

RESULTS: 111 flows mapped, 0 still unmapped
```

### Steps:
1. **Close the Flow Diagram app** (important!)
2. Open terminal/command prompt
3. Navigate to project folder
4. Run: `python auto_map_excel_flows.py`
5. Wait for "RESULTS" message
6. Reopen Flow Diagram app
7. Done! All flows now have Excel mappings

### Advanced: Custom Mapping Patterns
Edit `auto_map_excel_flows.py` to change how it matches columns:

```python
# Line 60-70: Change matching logic here
# Default: looks for exact column name match
# You can customize for your Excel format
```

---

## Solution 2: Mapping GUI (VISUAL)

### For Users Who Want Control
Interactive visual tool to see and edit mappings:

```bash
python excel_mapping_gui.py
```

**Features:**
- 📊 See all 152 flows in a table
- 🔍 View current Excel mappings
- ✏️ Double-click to edit any flow
- 🔄 Auto-map all at once
- 💾 Save all changes with one click
- 📂 Browse to different JSON/Excel files

### Steps:
1. **Close the Flow Diagram app**
2. Run: `python excel_mapping_gui.py`
3. Window opens showing all flows
4. Click **"🔄 Auto-Map All"** button (recommended)
5. Or **double-click** any flow to manually edit
6. Click **"💾 Save Changes"** when done
7. Close the GUI
8. Reopen Flow Diagram app

### Using the GUI:

**View All Flows:**
```
Flow Connection          | Type      | Sheet         | Column              | Status
========================================================================================
oldtsf_old_tsf_rainr...  | dirty     | Flows_OLDTSF  | oldtsf_old_tsf_r... | ✅
oldtsf_gwa_boreholes...  | clean     | Flows_OLDTSF  | oldtsf_gwa_boreh... | ✅
```

**Edit a Flow:**
1. Double-click any row
2. Edit dialog opens
3. Choose Sheet from dropdown
4. Select Column from list
5. Check "Enable Excel mapping"
6. Click "Save Mapping"

**Auto-Map:**
1. Click "🔄 Auto-Map All" button
2. Confirm when prompted
3. All unmapped flows are matched automatically

---

## Comparison: Script vs GUI

| Feature | Script | GUI |
|---------|--------|-----|
| Speed | ⚡ 3 seconds | ⏱️ Manual |
| User-Friendly | 💻 Technical | 🎯 Visual |
| Automation | ✅ Full auto | ✅ + Manual control |
| See Results | 📋 Terminal | 👁️ Table view |
| Edit Individual | ❌ No | ✅ Yes |
| Best For | Quick batch mapping | Fine-tuning individual flows |

---

## When to Use Each:

### Use the Script if:
- ✅ You just created new flows and want to map them all at once
- ✅ You want the fastest solution (3 seconds)
- ✅ You trust the auto-matching logic
- ✅ You're comfortable with terminal commands

### Use the GUI if:
- ✅ You want to see all mappings visually
- ✅ You need to edit specific flows
- ✅ You prefer point-and-click interface
- ✅ You're verifying mappings before saving
- ✅ You want to map flows one-by-one

---

## Workflow for Adding New Flows

### Old Way (Manual - Hard) ❌
```
1. Create flow in UI
2. Save in UI
3. Close app
4. Open JSON in text editor
5. Find the flow
6. Manually add excel_mapping
7. Save JSON
8. Reopen app
9. Pray it works
```
**Time: 10-15 minutes per flow**

### New Way (Automated - Easy) ✅
```
1. Create flow in UI
2. Save in UI  
3. Close app
4. Run: python auto_map_excel_flows.py
5. Or open: python excel_mapping_gui.py
6. Click "Auto-Map All" (or edit manually)
7. Click "Save Changes"
8. Reopen app
```
**Time: 1 minute for 100 flows**

---

## Troubleshooting

### Script Says "0 flows mapped"
**Problem:** Script can't find Excel columns
**Solution:**
1. Check Excel file path in script (line 40)
2. Verify Excel sheets are named correctly (Flows_UG2N, Flows_MERP, etc.)
3. Ensure Excel header row is on row 3

### GUI Shows Wrong Columns
**Problem:** Column dropdown is empty
**Solution:**
1. Select the correct sheet first
2. Columns populate based on selected sheet
3. Close and reopen if columns don't appear

### Mapping Still Not Working After Auto-Map
**Problem:** Flows created in UI don't have exact column matches
**Solution:**
1. Use the GUI to manually select the correct column
2. Or check if Excel column name is different
3. Verify Excel file has the expected columns

---

## Advanced: Customize the Auto-Matching Logic

Edit `auto_map_excel_flows.py` to change how it finds columns:

**Current Logic (Line 80-95):**
```python
# Exact match first
for col in excel_cols:
    if col.lower() == flow_name:
        found_col = col
        break

# Partial match if exact fails
if not found_col:
    from_part = from_node.lower()
    to_part = to_node.lower()
    for col in excel_cols:
        col_lower = col.lower()
        if from_part in col_lower and to_part in col_lower:
            found_col = col
            break
```

**Customize:**
- Change matching strategy
- Add prefix/suffix handling
- Case-sensitivity options
- Custom naming conventions

---

## Summary Table: All 8 Areas (Auto-Mapped)

| Area | Code | Sheet | Flows |
|------|------|-------|-------|
| UG2 North | UG2N | Flows_UG2N | ✅ All mapped |
| Merensky North | MERN | Flows_MERN | ✅ All mapped |
| Merensky South | MERS | Flows_MERS | ✅ All mapped |
| Merensky Plant | MERPLANT | Flows_MERP | ✅ All mapped |
| UG2 South | UG2S | Flows_UG2S | ✅ All mapped |
| UG2 Plant | UG2PLANT | Flows_UG2P | ✅ All mapped |
| Old TSF | OLDTSF | Flows_OLDTSF | ✅ All mapped |
| Stockpile | STOCKPILE | Flows_STOCKPILE | ✅ All mapped |

**Total: 111 flows automatically mapped**

---

## Next Time You Add Flows:

1. Create flows in Flow Diagram UI ✅
2. Save in UI ✅
3. Close app ✅
4. Run: `python auto_map_excel_flows.py` or `python excel_mapping_gui.py` ✅
5. Reopen app ✅
6. All new flows have Excel mappings! 🎉

---

## Pro Tip: Add to Your Workflow

Create a batch script (`.bat` on Windows or `.sh` on Mac/Linux) to automate:

**Windows (`auto_map.bat`):**
```batch
@echo off
echo Closing app and auto-mapping flows...
python auto_map_excel_flows.py
echo Done! You can now reopen the Flow Diagram app.
pause
```

**Mac/Linux (`auto_map.sh`):**
```bash
#!/bin/bash
echo "Closing app and auto-mapping flows..."
python3 auto_map_excel_flows.py
echo "Done! You can now reopen the Flow Diagram app."
```

Then just double-click the script file to run!

---

**That's it!** No more manual JSON editing. The automation handles it all. 🚀
