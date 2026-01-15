# Fix Excel Sheet Mappings - Step-by-Step Guide

## Problem Summary
Auto-map only succeeded for 4 flows out of 140 because your Excel sheet names don't match what the app expects.

**Expected names:** `Flows_UG2 North`, `Flows_Old TSF` (with spaces)  
**Your actual names:** `Flows_UG2N`, `Flows_OLDTSF` (abbreviated)

---

## Solution: Quick Fix Dialog (Fastest)

### Step 1: Start the App
```bash
python src/main.py
```

### Step 2: Open Excel Connection Setup
1. Go to **Flow Diagram** tab
2. Click the **Excel setup button** (gear icon or "Excel Connection Setup" button)

### Step 3: Use Smart Auto-Map (Optional Refresher)
1. Click **Smart Auto-Map** button
2. Review the preview
3. Click "Yes" to run
4. It will find the same 4 flows again
5. Click OK on the success message

### Step 4: Fix Remaining Flows
1. Click **Quick Fix (136 unmapped)** button
2. The dialog shows:
   - **Left side:** List of unmapped flows
   - **Right side:** Sheet/column picker

### Step 5: Map Each Flow
For each unmapped flow:

1. **Select it from the list**
   - Click on a flow like "042 | offices → dam"
   - The right panel updates with details

2. **Choose Excel Sheet** (usually pre-filled)
   - Click the "Excel Sheet" dropdown
   - Select the sheet that contains this flow's data
   - Example: offices → dam should be in `Flows_UG2 North`

3. **Choose Excel Column**
   - Click the "Excel Column" dropdown  
   - Look for a column like `offices__TO__dam` or similar
   - If it doesn't exist exactly, look for partial matches
   - Example: might be named `offices_to_dam` or `offices_→_dam`

4. **Apply the Mapping**
   - Click the **✓ Apply Mapping** button
   - The flow is saved and removed from the list
   - Next unmapped flow is automatically selected

5. **Repeat** for all flows (or until done)
   - The dialog keeps count: "✓ Connected! (3 fixed)"
   - When all 136 are done, it auto-closes

### Step 6: Done!
All 140 flows should now be mapped. The status will show:
```
✅ 140 flows connected  •  ⚠️ 0 flows need attention
```

---

## Alternative: Rename Excel Sheets (More Permanent)

If you want to prevent this issue in the future:

### Rename Your Sheets
In Excel, right-click each sheet tab and rename:

| Old Name | New Name |
|---|---|
| `Flows_UG2N` | `Flows_UG2 North` |
| `Flows_UG2S` | `Flows_UG2 Main` |
| `Flows_MERS` | `Flows_Merensky South` |
| `Flows_MERP` | `Flows_Merensky Plant` |
| `Flows_UG2P` | `Flows_UG2 Plant` |
| `Flows_OLDTSF` | `Flows_Old TSF` |
| `Flows_NEWTSF` | `Flows_New TSF` |
| `Flows_STOCKPILE` | `Flows_Stockpile1` |

### Then Re-Run Auto-Map
1. Open Excel Connection Setup
2. Click **Smart Auto-Map**
3. Much better results! (Hopefully 130+/140 mapped)
4. Use Quick Fix for any remaining stragglers

---

## Understanding the Quick Fix Dialog

### Left Panel (Unmapped Flows List)
```
Unmapped Flows:
┌────────────────────────┐
│ 001 | ug2_shaft → dam  │  ← Click to select
│ 014 | concentrate → .. │
│ 027 | tailings → tsf   │  ← Currently selected
│ ...                    │
│ 136 flows total        │
└────────────────────────┘
```

### Right Panel (Sheet & Column Selector)
```
Selected Flow:
Flow: tailings → tsf
Index: 027

Excel Sheet:
[Flows_Old TSF] ▼  ← Dropdown to choose sheet

Excel Column:
[tailings__TO__tsf] ▼  ← Dropdown to choose column

✓ Will connect to: Flows_Old TSF → tailings__TO__tsf

[✓ Apply Mapping] [Skip This Flow]
```

### Smart Features
- **Sheet pre-filled:** Auto-detects based on flow source
- **Column dropdown:** Only shows columns from selected sheet
- **Live preview:** Shows what you're connecting before saving
- **Skip option:** If a flow shouldn't be mapped, click Skip

---

## Troubleshooting

### "I don't see the Quick Fix button"
- All flows are already mapped ✅
- Go back to main screen and check status

### "The column I need isn't in the dropdown"
- The column might not exist in that sheet
- Try a different sheet
- Or create the column in Excel and refresh

### "Auto-map says 'updated=4, skipped=136'"
- Correct! Use Quick Fix to fix the 136
- That's exactly what the new Quick Fix dialog is for

### "Quick Fix closed without finishing"
- Check the status - maybe it finished! 
- The dialog auto-closes when all flows are mapped
- Verify in the main Excel Setup dialog

### "I'm stuck on one flow"
- Click **Skip This Flow** to move to the next
- You can come back to skipped flows later in Advanced Editor

---

## Understanding Sheet Names

### Why the names matter
The app looks for flows in specific sheets:

**Flow from ug2_shaft:**
```
Flow: ug2_shaft → dam
↓
App detects: "ug2" in source
↓
Looks in sheet: "Flows_UG2 North"
↓
Searches for column: "ug2_shaft__TO__dam"
```

### If column names don't match exactly
The app tries fallbacks:
1. Exact match: `ug2_shaft__TO__dam`
2. Alias match: Uses column aliases (if configured)
3. Partial match: Contains both "ug2_shaft" and "dam"
4. Manual override: Quick Fix lets you pick manually

### Example mapping in Quick Fix
```
Flow found: ug2_shaft → dam
Sheet selected: Flows_UG2 North ✓
Column selected: ug2_shaft → dam ✓

This will create mapping:
  From: ug2_shaft (in diagram)
  To: Column "ug2_shaft → dam" (in Excel)
  Sheet: Flows_UG2 North
```

---

## Performance Note

### How long does this take?
- **136 flows × 1-2 seconds per flow = ~2-3 minutes**
- Click Apply → Next flow loads → Repeat
- You can batch-process them quickly

### Tips for speed
1. Pre-scan your Excel to know column names
2. Use the auto-filled sheet suggestion
3. Accept partial column matches to save time
4. Skip unusual flows that don't need mapping

---

## Success Indicators

### Before (from your logs)
```
🔁 Auto-map complete: updated=4, skipped=136  ❌
```

### After (what you want)
```
✅ 140 flows connected  •  ⚠️ 0 flows need attention  ✅
Current Status:
✅ 140 flows connected  •  ⚠️ 0 flows need attention • 📊 140 total flows
```

---

## What NOT to Do

❌ **Don't** create new columns in Excel for auto-map  
→ The app finds EXISTING columns only

❌ **Don't** rename flows in the diagram to match Excel  
→ The app maps diagram flows → Excel columns (one direction)

❌ **Don't** delete the `excel_flow_links.json` file  
→ This stores all the mappings you create

❌ **Don't** move columns in Excel  
→ Column names matter, not positions

---

## Getting Help

If stuck, check these files:
- [docs/AUTOMAP_ISSUE_ANALYSIS.md](../AUTOMAP_ISSUE_ANALYSIS.md) - Technical details
- [docs/EXCEL_SETUP_IMPROVEMENTS.md](../EXCEL_SETUP_IMPROVEMENTS.md) - Feature overview
- [data/excel_flow_links.json](../../data/excel_flow_links.json) - Your saved mappings

---

## Summary

**Quick and Easy:**
1. Start app → Open Excel Setup
2. Click Quick Fix (136 unmapped)
3. For each flow: pick sheet → pick column → Apply
4. Done in ~3 minutes!

**Better for Long-term:**
1. Rename Excel sheets to match expected names
2. Re-run Auto-Map (gets 130+/140)
3. Use Quick Fix for remaining 10
4. Future auto-maps will work instantly!

