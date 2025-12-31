# Flow Label Data Loading - Status Report

## Summary

**Total Edges:** 138  
**✅ Enabled (showing data):** 56  
**❌ Disabled (no data):** 82

## What Was Fixed

### 1. Column Name Mismatches (7 issues)
Fixed 2 mismatches where JSON column names didn't match Excel:
- ✅ `Flows_MERP`: `MERPLANT_MPSWD12 → MERPLANT_MPSWD12_SPILL` → `MERPLANT_MPSWD12 → MERPLANT_MPSWD12_DUST`
- ✅ `Flows_UG2N`: `RAINFALL_INFLOW → NDCD` → `RAINFALL → NDCD`

Disabled 5 mappings that don't exist in Excel:
- ❌ `Flows_UG2N`: `NDCD → DUST_SUPPRESSION`
- ❌ `Flows_UG2N`: `SOFTENING → TRP_CLINIC`
- ❌ `Flows_UG2N`: `TRP_CLINIC → SEPTIC`
- ❌ `Flows_UG2N`: `TRP_CLINIC → CONSUMPTION`
- ❌ `Flows_STOCKPILE`: `SPCD1 → JUNCTION_129_1140_1242`

## Current Status

### ✅ Working (56 enabled edges)
All 56 enabled edges now have:
1. Valid Excel column mappings
2. Matching column names in Excel
3. Data in the Excel template

These edges **will display flow volumes** when you load from Excel.

### ❌ Not Working (82 disabled edges)
These edges are disabled because:
1. **77 edges**: Previously disabled due to UTF-8 corruption or invalid mappings (sheet titles, old format)
2. **5 edges**: Just disabled due to missing Excel columns

These edges **will NOT display flow volumes** until:
- Excel columns are added for them, OR
- They are mapped to existing Excel columns

## What Needs To Happen

To get all 138 edges showing data, you need to:

1. **Review the 82 disabled edges** - Decide which ones should show data
2. **Add Excel columns** - For edges that need new flows, add columns to the Excel template
3. **Map to existing columns** - For edges that represent existing flows, update their mappings
4. **Re-enable mappings** - Change `"enabled": false` to `"enabled": true` in the JSON

## How to Verify It Works

1. Run the app: `python src/main.py`
2. Open the Flow Diagram dashboard
3. Select an area (e.g., UG2N)
4. Click "Load from Excel"
5. You should see:
   - **56 flow lines with data** (numbers like "70,000 m³")
   - **82 flow lines with dashes** ("-")

## Files Modified

- `data/diagrams/ug2_north_decline.json` - Fixed 2 column names, disabled 5 invalid mappings
- `fix_column_mismatches.py` - Script that applied the fixes

## Next Steps

If you want to enable more flow labels:

1. **Identify which disabled edges should show data**
   ```python
   python -c "import json; d = json.load(open('data/diagrams/ug2_north_decline.json')); print('\n'.join(f'{e[\"from\"]} → {e[\"to\"]}' for e in d['edges'] if not e.get('excel_mapping', {}).get('enabled')))"
   ```

2. **Add the missing Excel columns** or **map to existing columns**

3. **Re-enable the mappings** in the JSON file

4. **Test** to ensure data loads correctly
