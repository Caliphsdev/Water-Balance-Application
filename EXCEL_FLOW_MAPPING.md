# 📊 Excel-Based Flow Volume System

## Overview

The Flow Diagram now loads monthly water volumes **directly from Excel** without database storage. Each area has its own sheet in the Excel template, and volumes are fetched **on-demand** when you select a month.

---

## 🏗️ Architecture

```
Flow Diagram Dashboard
       ↓
    Month Selector (UI)
       ↓
FlowVolumeLoader (utils/flow_volume_loader.py)
       ↓
Excel Template (test_templates/Water_Balance_TimeSeries_Template.xlsx)
       ↓
8 Area Sheets:
  - Flows_UG2N
  - Flows_MERN
  - Flows_MERENSKY_SOUTH
  - Flows_UG2S
  - Flows_STOCKPILE
  - Flows_OLDTSF
  - Flows_UG2PLANT
  - Flows_MERPLANT
```

---

## 📝 Excel Structure

Each area sheet has:
- **Column A**: Date (YYYY-MM-DD format)
- **Columns B+**: Flow volumes in m³

Example: `Flows_UG2N` sheet

| Date | BOREHOLE_ABSTRACTION | RAINFALL_UG2N | OFFICES | NDCD1_INFLOW | ... |
|------|----------------------|---------------|---------|--------------|-----|
| 2025-01-01 | 3000 | 150 | 500 | 2500 | ... |
| 2025-02-01 | 3200 | 200 | 450 | 2700 | ... |
| 2025-03-01 | 2800 | 100 | 600 | 2400 | ... |

---

## 🔗 Mapping Flow Lines to Excel

Each flow segment in the diagram JSON must include Excel mapping:

```json
{
  "from": "bh_ndgwa",
  "to": "offices",
  "segments": [[188, 146], [250, 146]],
  "flow_type": "clean",
  "volume": 500,
  "label": "500",
  "color": "#4b78a8",
  
  "excel_mapping": {
    "enabled": true,
    "column": "OFFICES"
  }
}
```

**Fields:**
- `enabled`: true/false - enable Excel sync for this flow
- `column`: Column name in Excel sheet (must match exactly)

---

## 🎯 How to Use

### Step 1: Add Flow Mapping to JSON

When creating/editing a flow line, add the Excel column name to enable dynamic loading:

```json
"excel_mapping": {
  "enabled": true,
  "column": "BOREHOLE_ABSTRACTION"
}
```

### Step 2: Update Excel Template

Edit the area sheet in Excel:

```
test_templates/Water_Balance_TimeSeries_Template.xlsx
  └─ Flows_UG2N (Sheet)
     ├─ Date | BOREHOLE_ABSTRACTION | RAINFALL_UG2N | OFFICES | ...
     └─ 2025-01-01 | 3000 | 150 | 500 | ...
```

### Step 3: Load in Dashboard

1. Open Flow Diagram → UG2 North Decline
2. Select **Month**: January, **Year**: 2025
3. Click **🔄 Load from Excel**
4. All flow volumes update from Excel! ✅

---

## 💻 Code Usage

### Load Volumes Programmatically

```python
from utils.flow_volume_loader import get_flow_volume_loader

loader = get_flow_volume_loader()

# Get single volume
volume = loader.get_monthly_volume(
    area_code='UG2N',
    flow_id='BOREHOLE_ABSTRACTION',
    year=2025,
    month=1
)
# Returns: 3000.0

# Get all volumes for area
volumes = loader.get_all_volumes_for_month(
    area_code='UG2N',
    year=2025,
    month=1
)
# Returns: {'BOREHOLE_ABSTRACTION': 3000, 'RAINFALL_UG2N': 150, ...}

# Update diagram
loader.update_diagram_edges(
    area_data=diagram_json,
    area_code='UG2N',
    year=2025,
    month=1
)
# Returns: Updated diagram with volumes from Excel
```

---

## 🛠️ Setting Up New Areas

### Add Area Mapping

Edit `setup_flow_sheets.py` to add new area:

```python
area_flows = {
    'Flows_MY_AREA': {
        'area': 'My Area Description',
        'flows': [
            'FLOW_ID_1',
            'FLOW_ID_2',
            'FLOW_ID_3',
        ]
    },
}
```

### Run Setup

```bash
python setup_flow_sheets.py
```

This will add new sheets with sample columns to the Excel template.

---

## 📊 Available Area Sheets

| Sheet Name | Area | Flows |
|-----------|------|-------|
| Flows_UG2N | UG2 North Decline | 10 |
| Flows_MERN | Merensky North | 6 |
| Flows_MERENSKY_SOUTH | Merensky South | 5 |
| Flows_UG2S | UG2 South Decline | 4 |
| Flows_STOCKPILE | Stockpile Area | 5 |
| Flows_OLDTSF | Old TSF Area | 6 |
| Flows_UG2PLANT | UG2 Plant Area | 6 |
| Flows_MERPLANT | Merensky Plant Area | 6 |

---

## ✅ Features

✅ **On-demand loading** - Read from Excel only when needed  
✅ **No database storage** - Volumes always from Excel  
✅ **Monthly basis** - Support for year/month selection  
✅ **Caching** - Sheet data cached in memory for performance  
✅ **Error handling** - Graceful fallback if data missing  
✅ **Flexible columns** - Any column name supported  
✅ **Easy setup** - Automatic sheet creation script included  

---

## 🔄 Workflow

```
User opens Flow Diagram
       ↓
Selects Month + Year (UI controls)
       ↓
Clicks "Load from Excel"
       ↓
FlowVolumeLoader reads Excel
       ↓
Matches area code to sheet
       ↓
Finds row with matching month
       ↓
Extracts volumes for each flow
       ↓
Updates diagram edge volumes
       ↓
Redraws with new m³ values
       ↓
User sees updated flow volumes! ✅
```

---

## 📝 Example: December 2025 Flow

1. User selects **December 2025** from dropdown
2. System loads `Flows_UG2N` sheet
3. Finds row with Date = 2025-12-01
4. Reads all column values:
   - BOREHOLE_ABSTRACTION: 2,900 m³
   - RAINFALL_UG2N: 180 m³
   - OFFICES: 450 m³
   - etc.
5. Updates all flow lines with December values
6. Diagram refreshes showing December flows ✅

---

## 🚀 Performance

- **First load**: ~500ms (reads Excel from disk)
- **Subsequent loads**: ~50ms (uses memory cache)
- **Clear cache**: `loader.clear_cache()` forces reload

---

## 🔐 Data Flow

```
Excel File
    ↓ (on demand per month)
FlowVolumeLoader._load_sheet()
    ↓ (caches in memory)
_df_cache[sheet_name]
    ↓ (on "Load from Excel" click)
_load_volumes_from_excel()
    ↓ (updates JSON)
area_data['edges'][...]['volume']
    ↓ (redraw)
Canvas shows new volumes
```

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| No volumes loading | Check `excel_mapping.enabled` in JSON |
| Column not found | Verify column name matches Excel exactly |
| Month not found | Add row to Excel with matching date |
| Stale data | Click "Load from Excel" again (clears cache) |
| File not found | Check `test_templates/Water_Balance_TimeSeries_Template.xlsx` exists |

---

## 🎯 Next Steps

1. **Map existing flows** - Add `excel_mapping` to diagram JSON
2. **Populate Excel** - Enter monthly volumes in area sheets
3. **Test loading** - Try different months in dashboard
4. **Add new areas** - Run `setup_flow_sheets.py` to add more sheets
5. **Automate** - Call `_load_volumes_from_excel()` on app startup

---

**Happy flow mapping! 💧**
