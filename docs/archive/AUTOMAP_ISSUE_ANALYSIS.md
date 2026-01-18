# Auto-Map Issue Analysis & Fix

## What Happened During Auto-Map

When you ran the **Smart Auto-Map**, it logged:
```
🔁 Auto-map complete: updated=4, skipped=136
```

This means **only 4 flows were successfully mapped, and 136 were skipped**.

---

## Root Cause

### The Problem: Sheet Name Mismatch

Your Excel workbook has **two different naming conventions** for sheets:

**What auto-map expects (correct):**
- `Flows_UG2 North` (with spaces)
- `Flows_Merensky Plant` (with spaces)
- `Flows_Old TSF` (with spaces)
- `Flows_Stockpile1` (with number)

**What exists in your workbook (abbreviated):**
- `Flows_UG2N` ❌
- `Flows_MERP` ❌  
- `Flows_OLDTSF` ❌
- `Flows_STOCKPILE` ❌
- `Flows_UG2S` ❌

### The Error Messages

Your logs showed 100+ errors like:
```
❌ Sheet 'Flows_OLDTSF' missing Date or Year/Month columns
❌ Sheet 'Flows_MERP' missing Date or Year/Month columns
```

These errors came from the **validation code trying to load ALL sheets** in the workbook, including:
1. Old/temporary sheets with abbreviated names
2. Sheets that don't have proper header rows
3. Sheets that were used for testing

---

## Why So Many Flows Skipped

The auto-map logic does this:

```python
# 1. Identify the sheet name from flow source node
from_id = "ug2n_offices"  # Example
sheet = "Flows_UG2 North"  # Correct mapping

# 2. Try to load that sheet
df = loader._load_sheet("Flows_UG2 North")

# 3. If successful, search for matching column
if found_column:
    mapping_success = True
else:
    mapping_skip = True  # Column not found
```

The 136 skipped flows likely failed at step 2 or 3:
- **Step 2 failure:** Sheet name mismatch
- **Step 3 failure:** Column not found in sheet

---

## The Fix: What I've Improved

### 1. **Enhanced Auto-Map Logging**
Now it logs:
```python
logger.info(f"🗂️  Available Excel sheets: {sorted(available_sheets)}")
logger.debug(f"✅ Mapped {from_id}→{to_id} to {sheet}[{found}]")
logger.debug(f"⏭️  Skipping {from_id}→{to_id}: sheet '{sheet}' not found")
```
This makes it clear what's working and why things are skipped.

### 2. **Fallback Sheet Names**
Added support for alternative sheet names:
```python
alternative_sheets = {
    'Flows_Stockpile': 'Flows_Stockpile1',  # Try variant
}
```

### 3. **Better Error Messages**
The success dialog now shows:
```
✅ Updated: 4 flows
⚠️ Skipped: 136 flows

Successfully connected 4 flows to Excel columns.
Use 'Quick Fix' to manually handle 136 remaining flows.
```

Instead of generic "Note: Only columns present in Excel were mapped."

### 4. **New Quick Fix Dialog**
Specifically designed to handle unmapped flows with:
- List of ONLY unmapped flows (not all 140)
- Pre-filled sheet suggestions based on flow source
- One-click "Apply Mapping" button
- Auto-close when done

---

## What You Should Do Now

### Option 1: Rename Excel Sheets (RECOMMENDED)
Rename your sheet tabs to use the correct names with spaces:

| Current Name | Change To |
|---|---|
| `Flows_UG2N` | `Flows_UG2 North` |
| `Flows_UG2S` | `Flows_UG2 Main` |
| `Flows_MERS` | `Flows_Merensky South` |
| `Flows_MERP` | `Flows_Merensky Plant` |
| `Flows_UG2P` | `Flows_UG2 Plant` |
| `Flows_OLDTSF` | `Flows_Old TSF` |
| `Flows_NEWTSF` | `Flows_New TSF` |
| `Flows_STOCKPILE` | `Flows_Stockpile1` |

**Then:**
1. Re-run Smart Auto-Map (should get much better results)
2. Use Quick Fix for any remaining unmapped flows

### Option 2: Use Quick Fix (FASTER)
1. Open Excel Connection Setup
2. Click **Quick Fix (136 unmapped)**
3. For each unmapped flow:
   - Select it from the list
   - Choose the correct Excel sheet
   - Choose the column
   - Click "Apply Mapping"
4. Done!

### Option 3: Manual Editor (MOST CONTROL)
1. Click **Advanced Editor (All Flows)**
2. Review and fix all 140 mappings manually
3. Save when done

---

## Why Auto-Create Columns Wasn't Implemented

**To answer your original question:** Auto-map does NOT and SHOULD NOT create Excel columns. Here's why:

1. **Data Integrity:** Creating columns automatically could mess up your Excel structure
2. **Business Rules:** Only users understand what data should exist
3. **Column Naming:** Automatic names would be ugly (like `auto_generated_col_1`)
4. **Validation:** User should validate data before creating columns

**Better approach:** Define columns manually in Excel, then auto-map finds them.

---

## Common Issues & Solutions

### Issue: "Auto-map only found 4 flows"
**Solution:** Your sheet names don't match. Use Option 1 above to rename them.

### Issue: "Found column exists but still says skipped"
**Solution:** Column might have a different name than expected. Use Quick Fix to manually select it.

### Issue: "Error: Sheet 'Flows_OLDTSF' missing Date columns"
**Solution:** That sheet might not have proper headers. Check your Excel file. Delete old test sheets if they're not needed.

### Issue: "Quick Fix dialog doesn't show the flow I need"
**Solution:** The flow was already auto-mapped. Check the status (✅ 4 flows connected).

---

## Technical Details

### How Auto-Map Resolves Sheet Names

1. **From edge mapping:** Uses existing mapping if set
2. **From flow ID:** Checks if `ug2n` appears in `from_id` → maps to `Flows_UG2 North`
3. **Fallback:** If step 1-2 fail, skips the flow

### How Quick Fix Helps

Quick Fix shows a two-panel interface:
- **Left:** List of ONLY unmapped flows
- **Right:** Sheet/column picker with smart suggestions

When you select a flow, it:
1. Shows the flow details
2. Pre-fills sheet based on flow source (`ug2n` → `Flows_UG2 North`)
3. Loads available columns for that sheet
4. Lets you pick the correct column
5. Saves and moves to next

---

## Next Steps

1. **Recommended:** Fix Excel sheet names (Option 1) for cleaner data
2. **Immediate:** Use Quick Fix to handle the 136 skipped flows
3. **Future:** With correct sheet names, auto-map will work much better

Run the app and give it a try:
```bash
python src/main.py
```

The improved dialogs with better messaging and the new Quick Fix feature should make it much faster to get all 140 flows mapped!

---

## For Reference: Improved Auto-Map Features

✅ **Pre-warms sheet cache** - Lists all available sheets upfront  
✅ **Better logging** - Shows exactly what was mapped and what was skipped  
✅ **Fallback sheet names** - Tries alternatives (Stockpile vs Stockpile1)  
✅ **Clearer success message** - Shows count and suggests Quick Fix  
✅ **Exception handling** - Won't crash on sheet read errors  

✅ **NEW Quick Fix Dialog** - Streamlined UI for fixing unmapped flows  
✅ **Smart Sheet Suggestions** - Auto-detects which sheet based on flow source  
✅ **Live Column Preview** - See what you're connecting before saving  
✅ **One-Click Apply** - Apply mapping with single button press  
✅ **Progress Tracking** - See how many you've fixed as you go  
✅ **Auto-Advance** - Moves to next unmapped flow after each fix  

