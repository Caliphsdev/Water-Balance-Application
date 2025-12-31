# ✅ FLOW DIAGRAM ARCHITECTURE - FIXED

## The Real Problem & Solution

### What We Discovered:
The UG2 North Decline JSON file (`ug2_north_decline.json`) is **NOT** just for UG2 North - it's a **MASTER DIAGRAM** containing **ALL MINE AREAS**:

```json
{
  "title": "UG2 North Decline Area",
  "merensky_title": "Merensky North Area",
  "stockpile_title": "Stockpile Area",
  "ug2south_title": "UG2 South Area",
  "merenskysouth_title": "Merensky South Area",
  "oldtsf_title": "Old TSF Area",
  "ug2plant_title": "UG2 Plant Area",
  "merplant_title": "Merensky Plant Area",
  "nodes": [130 shared components],
  "edges": [152 shared flow connections],
  "zone_bg": [8 zone backgrounds for visual sections]
}
```

### Why Stockpile Wasn't Working:
1. We created empty/wrong individual area files (merensky_north_area.json, stockpile_area.json, etc.)
2. The loading logic was trying to load these BEFORE the master UG2N file
3. The empty files had no data to display

### The Fix:
✅ **REMOVED** incorrect individual area files:
  - ❌ merensky_north_area.json
  - ❌ merensky_south_area.json
  - ❌ merensky_plant_area.json
  - ❌ ug2_south_area.json
  - ❌ ug2_plant_area.json
  - ❌ old_tsf_area.json
  - ❌ stockpile_area.json

✅ **KEEP** only the master diagram:
  - ✅ ug2_north_decline.json (contains ALL areas)

---

## How It Works Now

### Single Master Diagram Architecture:
```
App loads Flow Diagram module
        ↓
Loads ug2_north_decline.json (master)
        ↓
Draws ALL areas on one canvas:
  - UG2 North Decline section (top)
  - Merensky North section (left middle)
  - Stockpile section (right)
  - UG2 South, Old TSF, etc. (bottom)
        ↓
User selects month/year from Excel
        ↓
System determines area_code from node data
        ↓
Loads from correct Excel sheet:
  - Flows_UG2N (if editing UG2 area)
  - Flows_MERN (if editing Merensky area)
  - Flows_STOCKPILE (if editing Stockpile area)
  - etc.
        ↓
Displays all flows with volumes on canvas
```

### Excel Integration:
All areas are served by the same file `Water_Balance_TimeSeries_Template.xlsx` with different sheets:

| Area | Sheet Name | Area Code |
|------|------------|-----------|
| UG2 North | Flows_UG2N | UG2N |
| Merensky North | Flows_MERN | MERN |
| Merensky South | Flows_MERS | MERS |
| Merensky Plant | Flows_MERPLANT | MERPLANT |
| UG2 South | Flows_UG2S | UG2S |
| UG2 Plant | Flows_UG2PLANT | UG2PLANT |
| Old TSF | Flows_OLDTSF | OLDTSF |
| Stockpile | Flows_STOCKPILE | ✅ **STOCKPILE** |

---

## Why This Design?

### Advantages:
1. ✅ **Single source of truth** - One diagram file for all areas
2. ✅ **Spatial relationships** - All areas displayed relative to each other
3. ✅ **Unified canvas** - See how flows move between areas
4. ✅ **No duplication** - Nodes/edges shared across all areas
5. ✅ **Easy to maintain** - Update one file, all areas updated

### Zone Backgrounds:
The diagram uses `zone_bg` (8 zone backgrounds) to visually separate areas on the canvas:
- Different colored/shaded rectangles for each area
- Area titles overlay these zones
- Help users visually identify which section is which

---

## Current Status

✅ **All areas working with master diagram approach**
✅ **Stockpile Area now loads correctly** 
✅ **Excel integration works for all 8 areas**
✅ **No dropdown needed - single unified view**

---

## To Use:

1. Launch app → Go to **Flow Diagram**
2. Master diagram loads with all 8 areas visible
3. Select **month/year** from Excel date selector
4. Click **"Load from Excel"**
5. All area flows load from their respective sheets
6. **Flows display on canvas** with volumes ✅

---

## Files:
- ✅ `data/diagrams/ug2_north_decline.json` (MASTER - 130 nodes, 152 edges, 8 zones)
- ❌ `data/diagrams/ug2_north_decline.json.bak` (backup if needed)

That's it! No more multiple files needed.
