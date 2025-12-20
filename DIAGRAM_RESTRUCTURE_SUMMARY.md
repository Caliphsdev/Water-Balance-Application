# Flow Diagram Restructuring Summary

**Date:** December 19, 2025  
**Changes:** Removed Merensky North Area and split Old TSF into separate facilities

---

## ✅ Changes Applied

### 1. **Removed Merensky North Area** 
- ❌ Deleted zone background (was at y: 470-890, height: 420px)
- ❌ Removed 12 nodes:
  - `bh_mcgwa` - Borehole Abstraction (MCGWA 1-2)
  - `rainfall_merensky` - Direct Rainfall
  - `softening_merensky` - Softening Plant
  - `offices_merensky` - Offices
  - `merensky_north_decline` - Merensky North Decline
  - `merensky_north_shaft` - Merensky North Decline Shaft Area
  - `ndcd_merensky` - NDCD 3-4 / NDSWD 2
  - `losses_merensky` - Losses
  - `consumption_merensky` - Consumption
  - `spill_merensky` - Spill
  - `evaporation_merensky` - Evaporation
  - `dust_suppression_merensky` - Dust Suppression
- ❌ Removed 14 flow edges connected to these nodes
- ❌ Removed `merensky_title` from diagram

### 2. **Split Old TSF Area**
The Old TSF Area (was single zone at y: 2070-2640, height: 570px) has been split into:

#### **Old TSF** (Top Half)
- 📍 Position: y: 1650, height: 285px
- 🎨 Color: Light green (#e8f5e9)
- Contains nodes for:
  - Old Tailings Storage Facility
  - TRTD 1-2 (Return Water Dams)
  - Associated inflows and outflows

#### **New TSF** (Bottom Half)  
- 📍 Position: y: 1935, height: 285px
- 🎨 Color: Light yellow (#fff9c4)
- Contains nodes for:
  - New Tailings Storage Facility
  - NT RWD 1&2 (Return Water Dams)
  - Associated inflows and outflows

### 3. **Repositioned All Zones Below**
After removing Merensky North (420px), all subsequent zones moved up:
- Stockpile Area: 900 → **480**
- UG2 South Decline: 1320 → **900**
- Merensky South: 1640 → **1220**
- Old TSF: 2070 → **1650**
- New TSF: 2355 → **1935**
- UG2 Plant: 2650 → **2230**
- Merensky Plant: 3230 → **2810**

### 4. **Adjusted Positions**
- ⬆️ 100 nodes moved up by 420px
- ⬆️ 119 edge segments/positions adjusted
- 📏 Overall diagram height: 3810 → **3390** (-420px)

---

## 📊 Final Statistics

| Item | Before | After | Change |
|------|--------|-------|--------|
| **Zones** | 9 | 8 | -1 (removed Merensky North, but split Old TSF into 2) |
| **Nodes** | 130 | 118 | -12 (Merensky North) |
| **Edges** | 152 | 138 | -14 (Merensky North connections) |
| **Height** | 3810px | 3390px | -420px |

---

## 🗺️ New Zone Layout

```
┌─────────────────────────────────────────┐
│ UG2 North Decline Area (y: 40-460)     │ ← Unchanged
├─────────────────────────────────────────┤
│ Stockpile Area (y: 480-900)            │ ← Moved up 420px
├─────────────────────────────────────────┤
│ UG2 South Decline (y: 900-1220)        │ ← Moved up 420px
├─────────────────────────────────────────┤
│ Merensky South Area (y: 1220-1640)     │ ← Moved up 420px
├─────────────────────────────────────────┤
│ Old TSF (y: 1650-1935) 🆕              │ ← NEW: Top half of old zone
├─────────────────────────────────────────┤
│ New TSF (y: 1935-2220) 🆕              │ ← NEW: Bottom half of old zone
├─────────────────────────────────────────┤
│ UG2 Plant Area (y: 2230-2800)          │ ← Moved up 420px
├─────────────────────────────────────────┤
│ Merensky Plant Area (y: 2810-3380)     │ ← Moved up 420px
└─────────────────────────────────────────┘
```

---

## 💾 Backup & Recovery

### Backup Location
A complete backup of the original diagram was saved automatically:
```
data/diagrams/ug2_north_decline.json.backup
```

### To Restore Original
If you need to undo these changes:
```powershell
cd C:\PROJECTS\Water-Balance-Application\data\diagrams
Copy-Item ug2_north_decline.json.backup ug2_north_decline.json -Force
```

---

## ⚠️ Important Notes

1. **Excel Mappings**: All Excel mappings for Merensky North flows have been removed. Other areas' mappings are preserved intact.

2. **Flow Connections**: Any flows that connected FROM or TO Merensky North nodes have been deleted. Review your Excel sheets if you had cross-area flows.

3. **Old TSF Nodes**: The Old TSF area nodes remain in their original positions but are now split between two visual zones:
   - Nodes with `oldtsf_old_tsf*` prefix → Old TSF zone
   - Nodes with `oldtsf_new_tsf*` prefix → New TSF zone
   - Office nodes → Old TSF zone

4. **Node IDs**: All node IDs remain unchanged. The prefix `oldtsf_` is kept for consistency even though the area is now split.

5. **Testing**: After reopening the app, verify:
   - All zones display correctly
   - Flow lines render properly
   - Excel "Load from Excel" still works for remaining areas
   - Save functionality works

---

## 🔄 Next Steps

1. **Open the Flow Diagram Dashboard** in your app
2. **Verify the layout** - check that zones are properly separated
3. **Test Excel loading** for Old TSF and New TSF flows
4. **Update Excel sheets** if needed to match the new zone structure
5. **Use "Validate Excel Mapping"** button to check all mappings
6. **Save the diagram** from the UI to confirm changes are preserved

---

## 📝 Related Files

- **Diagram JSON**: `data/diagrams/ug2_north_decline.json`
- **Backup**: `data/diagrams/ug2_north_decline.json.backup`
- **Restructure Script**: `scripts/restructure_diagram.py`
- **Dashboard Code**: `src/ui/flow_diagram_dashboard.py`

---

*Generated by automated restructuring script*
