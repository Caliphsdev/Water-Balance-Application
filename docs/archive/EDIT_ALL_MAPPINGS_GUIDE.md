# 📋 Edit All Mappings - Review & Correct Auto-Map Errors

## ✨ What's New

Two new buttons in the **Edit Mappings** dialog:

| Button | Purpose |
|--------|---------|
| **[Manual Mapper]** | Fix the 28 flows with **invalid columns** (don't exist in Excel) |
| **[Edit All Mappings]** | Review & correct **ALL 152 flows** for wrong mappings |

## 🎯 When to Use Each

### Use [Manual Mapper] When:
- ✅ You want to fix flows that **don't have a valid Excel column**
- ✅ 28 flows need attention (column doesn't exist in the sheet)
- ✅ You want step-by-step guided fixing

### Use [Edit All Mappings] When:
- ✅ You want to review/verify **all 152 flows**
- ✅ Auto-map picked the **wrong column** (even though it exists)
- ✅ You want to search and filter flows
- ✅ You want quick table view with status indicators

## 🚀 How to Use [Edit All Mappings]

### 1. **Open Edit Mappings Dialog**
   - Flow Diagram Dashboard → "[🔗 Edit Mappings]" button

### 2. **Click [Edit All Mappings]**
   - See all 152 flows in a table
   - Invalid mappings marked with ⚠️
   - Valid mappings marked with ✅

### 3. **Search for Flows** (optional)
   - Type flow name or column name in search box
   - Filter down to specific flows you want to check

### 4. **Click Any Flow to Edit**
   - Pick correct **Sheet** from dropdown
   - Pick correct **Column** from sheet
   - Click "Save" to update

### 5. **Changes Saved Immediately**
   - Mapping updated in diagram JSON
   - Re-run manual mapper or auto-map if needed

## 📊 Table Columns

```
✅/⚠️  | Flow Name                 | Sheet            | Column
-------|---------------------------|------------------|-----------------------
✅     | bh_ndgwa → softening      | Flows_UG2N       | bh_ndgwa__TO__softening
⚠️     | oldtsf_nt_rwd → new_tsf  | Flows_OLDTSF     | oldtsf_new_tsf__TO__nt_rwd (INVALID!)
✅     | mers_bh → mers_soft       | Flows_MERS       | mers_borehole__TO__mers_soft
```

**Status Meaning:**
- ✅ = Column exists in Excel, mapping is valid
- ⚠️ = Column does NOT exist in Excel, needs fixing

## 💡 Example Workflow

**Scenario**: Auto-map guessed wrong for sewage flows

1. Open "[Edit All Mappings]"
2. Search for: "sewage"
3. Find: "sewage_treatment → ndcd" showing wrong column
4. Click the flow
5. Select: Sheet = Flows_OLDTSF, Column = (correct one from dropdown)
6. Click Save
7. Done! Ready to re-verify with manual mapper

## 🔍 Search Tips

- Search **by flow name**: "sewage", "ndcd", "borehole"
- Search **by column**: "TO__ndcd", "rainrun"
- Case-insensitive and partial matches work
- Shows only matching flows

## ✅ Quick Checklist

- [ ] Open Edit Mappings
- [ ] Click [Edit All Mappings]
- [ ] Review the ⚠️ marked flows (invalid columns)
- [ ] Click on any wrong mapping to fix
- [ ] Select correct sheet/column
- [ ] Click Save
- [ ] Search/filter for specific flows
- [ ] After fixing, run Manual Mapper again or Auto-Map

## 📈 Statistics

After using [Edit All Mappings]:

```
Before: 124 ✅ valid, 28 ⚠️ invalid
After:  152 ✅ valid,  0 ⚠️ invalid
```

All mappings now correct and ready for flow volume loading!

---

**Ready to test?** Launch the app and try both buttons!
