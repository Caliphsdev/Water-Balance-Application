# 🚀 Quick Start: Excel Flow Volume Loading

## 5-Minute Setup

### 1. ✅ Excel Template Ready
```
test_templates/Water_Balance_TimeSeries_Template.xlsx
  ├─ Flows_UG2N (sheet with 10 flow columns)
  ├─ Flows_MERN (sheet with 6 flow columns)
  ├─ Flows_MERENSKY_SOUTH
  ├─ Flows_UG2S
  ├─ Flows_STOCKPILE
  ├─ Flows_OLDTSF
  ├─ Flows_UG2PLANT
  └─ Flows_MERPLANT
```

### 2. 📝 Add Excel Mapping to Flows
In your diagram JSON (e.g., `data/diagrams/ug2_north_decline.json`):

```json
{
  "from": "bh_ndgwa",
  "to": "offices",
  "volume": 500,
  "label": "500",
  "excel_mapping": {
    "enabled": true,
    "column": "OFFICES"
  }
}
```

✅ Column name must match Excel sheet exactly!

### 3. 📊 Fill Excel with Data
```
File: test_templates/Water_Balance_TimeSeries_Template.xlsx
Sheet: Flows_UG2N

| Date       | BOREHOLE_ABSTRACTION | RAINFALL_UG2N | OFFICES | ...
|------------|----------------------|---------------|---------|----
| 2025-01-01 | 3000                 | 150           | 500     | ...
| 2025-02-01 | 3200                 | 200           | 450     | ...
```

### 4. 🔄 Load in Dashboard

```
Flow Diagram Dashboard
  ↓
Month/Year Selector: Year [2025] Month [January]
  ↓
Click: 🔄 Load from Excel
  ↓
All flows update! ✅
```

---

## 📚 Files to Understand

| File | Purpose |
|------|---------|
| `src/utils/flow_volume_loader.py` | Core loader (reads Excel) |
| `src/ui/flow_diagram_dashboard.py` | Dashboard with UI controls |
| `test_templates/Water_Balance_TimeSeries_Template.xlsx` | Data source |
| `setup_flow_sheets.py` | Add new area sheets |

---

## 🎯 Workflow Example

**Scenario**: Load December 2025 flows for UG2 North

### Step-by-Step:

1. **Open Dashboard**
   ```
   Application → Calculations → Flow Diagram
   ```

2. **Navigate to UG2 North**
   ```
   Select area: UG2 North Decline
   ```

3. **Select Month**
   ```
   Year: [2025] ↓
   Month: [December] ↓
   ```

4. **Load Volumes**
   ```
   Click: 🔄 Load from Excel
   ```

5. **Result**
   ```
   System queries: Flows_UG2N sheet
   Matches: 2025-12-01 row
   Reads columns: BOREHOLE_ABSTRACTION, OFFICES, etc.
   Updates flows with December values ✅
   Diagram refreshes showing new volumes
   ```

---

## 💡 Common Tasks

### Task 1: Add a New Flow
1. Draw flow line in diagram
2. Edit line properties (type, volume)
3. In JSON, add:
   ```json
   "excel_mapping": {
     "enabled": true,
     "column": "MY_NEW_FLOW"
   }
   ```
4. Add column to Excel sheet
5. Reload from Excel

### Task 2: Update Monthly Data
1. Open Excel template
2. Go to relevant area sheet (e.g., `Flows_UG2N`)
3. Update volume for that month
4. Save Excel file
5. Return to dashboard and click "Load from Excel"

### Task 3: Compare Months
1. Select **January 2025**, click "Load from Excel"
2. Note the values
3. Select **February 2025**, click "Load from Excel"
4. Compare side-by-side

### Task 4: Add New Area
1. Run: `python setup_flow_sheets.py`
2. Edit to add your area config
3. New sheets added automatically
4. Fill with data

---

## 🔍 Data Validation

### Column Names Must Match!

❌ **Won't work:**
- Excel column: `BOREHOLE_ABSTRACTION`
- JSON mapping: `column: "borehole_abstraction"` (lowercase)

✅ **Will work:**
- Excel column: `BOREHOLE_ABSTRACTION`
- JSON mapping: `column: "BOREHOLE_ABSTRACTION"` (exact match)

### Missing Data Handling

- ✅ Missing month row → Volume stays at current value
- ✅ Missing column → Skips that flow (returns 0)
- ✅ Invalid number → Treated as 0
- ✅ Negative numbers → Ignored

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Volumes don't load | Check `excel_mapping.enabled = true` in JSON |
| "Column not found" | Verify column name matches Excel **exactly** |
| "Sheet not found" | Check area code (UG2N, MERN, etc.) correct |
| Stale data showing | Click "Load from Excel" again |
| Excel file not found | Verify path: `test_templates/Water_Balance_TimeSeries_Template.xlsx` |
| Permission denied | Close Excel file and try again |

---

## 📊 Sheet Reference

### Flows_UG2N (UG2 North Decline)
```
- BOREHOLE_ABSTRACTION
- RAINFALL_UG2N
- OFFICES
- ACCOMMODATION
- NDCD1_INFLOW
- NDCD2_INFLOW
- RECOVERY_PLANT
- RECYCLED_WATER
- SPILLAGE_LOSS
- SEEPAGE_LOSS
```

### Flows_MERN (Merensky North)
```
- RAINFALL_MERN
- MERENSKY_PLANT_INFLOW
- TREATMENT_PLANT
- DISCHARGE_POINT
- EVAPORATION_LOSS
- CONSERVATION_POOL
```

### [Other areas available too...]

---

## ⚙️ Technical Details

### Singleton Pattern
```python
from utils.flow_volume_loader import get_flow_volume_loader
loader = get_flow_volume_loader()  # Always same instance
```

### Memory Caching
```python
# First call: reads Excel from disk (~500ms)
volumes = loader.get_all_volumes_for_month('UG2N', 2025, 1)

# Second call: uses cache (~50ms)
volumes = loader.get_all_volumes_for_month('UG2N', 2025, 1)

# Clear if needed
loader.clear_cache()
```

### Direct API Usage
```python
# Get single volume
vol = loader.get_monthly_volume('UG2N', 'OFFICES', 2025, 1)
# Returns: 500.0

# Get all volumes
vols = loader.get_all_volumes_for_month('UG2N', 2025, 1)
# Returns: {'OFFICES': 500, 'RAINFALL_UG2N': 150, ...}

# Update diagram
loader.update_diagram_edges(area_data, 'UG2N', 2025, 1)
# Updates all edges with excel_mapping enabled
```

---

## ✅ Checklist

- [ ] Excel template opened (`test_templates/Water_Balance_TimeSeries_Template.xlsx`)
- [ ] Area sheet found (e.g., `Flows_UG2N`)
- [ ] Column names identified and exact
- [ ] Sample data entered for at least one month
- [ ] JSON flows have `excel_mapping` section
- [ ] Column names in JSON match Excel **exactly**
- [ ] Dashboard loads without errors
- [ ] Month selector visible and working
- [ ] "Load from Excel" button visible
- [ ] Volumes update on click ✅

---

## 🎓 Learning Resources

- 📖 Full guide: `EXCEL_FLOW_MAPPING.md`
- 📊 Summary: `EXCEL_INTEGRATION_SUMMARY.md`
- 💻 Code: `src/utils/flow_volume_loader.py`
- 🎨 Dashboard: `src/ui/flow_diagram_dashboard.py`

---

## 🚀 You're Ready!

```
1. Fill Excel with data ✅
2. Add excel_mapping to JSON ✅  
3. Open dashboard ✅
4. Select month ✅
5. Click "Load from Excel" ✅
6. Watch flows update! 🎉
```

**No database involved. Pure Excel-to-Diagram streaming!**

---

**Questions? Check EXCEL_FLOW_MAPPING.md for full documentation.**
