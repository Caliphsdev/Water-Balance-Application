# Water Balance Time Series Data Mapping

## Overview
This document describes the current time-series data mapping and identifies additional parameters that can be loaded from Excel.

---

## CURRENTLY MAPPED (Excel: "Meter Readings" Sheet)

### ✅ Source Inflows
**Status:** Fully implemented - loaded from Excel monthly

| Parameter | Excel Column | Type | Usage |
|-----------|-------------|------|-------|
| **Rivers** | MDSR, LMSR, NDSF, etc. | Surface Water | Monthly flow in m³ |
| **Boreholes** | NTSFGWA 1-2, MDGWA 1-5, NDGWA 1-6, MERGWA 1-2 | Groundwater | Monthly abstraction in m³ |
| **Dewatering** | N Dewat, M Dewat, S Dewat | Underground Water | Monthly dewatering in m³ |
| **Tonnes Milled** | Tonnes Milled | Production | Monthly ore processing in tonnes |
| **TSF Return (RWD)** | RWD | Return Water | Monthly TSF return water in m³ |

**Excel Structure:**
- Row 1-2: Title/headers
- Row 3: Column names (source codes)
- Row 4+: Monthly data (Date in column A, values in subsequent columns)

---

## NOT YET MAPPED (Potential Time Series)

### 🔄 Environmental Parameters

| Parameter | Current Source | Potential Excel Sheet | Impact |
|-----------|---------------|---------------------|--------|
| **Rainfall** | Constant (60 mm) | Environmental | Calculate actual rainfall inflows |
| **Custom Evaporation** | evaporation_rates table | Environmental | Override monthly evaporation rates |
| **Pan Coefficient** | Constant (0.8) | Environmental | Adjust evaporation calculations |

**Current Behavior:**
- Rainfall: Uses `DEFAULT_MONTHLY_RAINFALL_MM` constant (60 mm)
- Evaporation: Uses `evaporation_rates` database table (12 monthly values)
- Pan Coefficient: Uses `evap_pan_coefficient` constant (0.8)

**Proposed Enhancement:**
```
Sheet: Environmental
Columns: Date | Rainfall (mm) | Custom Evaporation (mm) | Pan Coefficient | Notes
```

---

### 🔄 Storage Facility Measurements

| Parameter | Current Source | Potential Excel Sheet | Impact |
|-----------|---------------|---------------------|--------|
| **Opening Volume** | Calculated | Storage_Facilities | Actual measured opening volumes |
| **Closing Volume** | Calculated | Storage_Facilities | Actual measured closing volumes |
| **Storage Level (%)** | Calculated | Storage_Facilities | Measured fill levels |
| **Facility Inflow** | Calculated | Storage_Facilities | Direct facility inflows |
| **Facility Outflow** | Calculated | Storage_Facilities | Direct facility outflows |

**Current Behavior:**
- All storage changes calculated from water balance
- No direct facility-level measurements used

**Proposed Enhancement:**
```
Sheet: Storage_Facilities
Columns: Date | Facility Code | Opening Volume | Closing Volume | Level % | Inflow | Outflow | Notes
```

---

### 🔄 Production & Processing

| Parameter | Current Source | Potential Excel Sheet | Impact |
|-----------|---------------|---------------------|--------|
| **Concentrate Produced** | Constant (0 t) | Production | Calculate product moisture accurately |
| **Concentrate Moisture** | Constant (8%) | Production | Actual product moisture content |
| **Slurry Density** | Constant/Calculated | Production | TSF slurry characteristics |
| **Tailings Moisture** | Calculated | Production | Actual tailings retention |

**Current Behavior:**
- Concentrate production defaults to 0 (not tracked)
- Moisture constants used for calculations
- Slurry density estimated from formulas

**Proposed Enhancement:**
```
Sheet: Production
Columns: Date | Concentrate Produced (t) | Concentrate Moisture % | Slurry Density | Tailings Moisture % | Notes
```

---

### 🔄 Water Consumption

| Parameter | Current Source | Potential Excel Sheet | Impact |
|-----------|---------------|---------------------|--------|
| **Dust Suppression** | Calculated (2% of ore) | Consumption | Actual dust suppression volumes |
| **Mining Consumption** | Not tracked | Consumption | Direct mining water use |
| **Domestic Consumption** | Not tracked | Consumption | Camp/office water consumption |
| **Irrigation** | Not tracked | Consumption | Landscaping/dust suppression |
| **Other Consumption** | Not tracked | Consumption | Miscellaneous uses |

**Current Behavior:**
- Dust suppression: `ore_tonnes * 0.02` (2% of production)
- Other consumption types not separately tracked

**Proposed Enhancement:**
```
Sheet: Consumption
Columns: Date | Dust Suppression | Mining Consumption | Domestic Consumption | Irrigation | Other | Notes
```

---

### 🔄 Seepage & Losses

| Parameter | Current Source | Potential Excel Sheet | Impact |
|-----------|---------------|---------------------|--------|
| **Seepage Loss** | Calculated/Modeled | Seepage_Losses | Measured seepage losses |
| **Seepage Gain** | Calculated/Modeled | Seepage_Losses | Measured seepage recovery |
| **Unaccounted Losses** | Closure Error | Seepage_Losses | Known but unmeasured losses |

**Current Behavior:**
- Seepage calculated from facility characteristics
- Closure error absorbs unaccounted differences

**Proposed Enhancement:**
```
Sheet: Seepage_Losses
Columns: Date | Seepage Loss | Seepage Gain | Unaccounted Losses | Notes
```

---

### 🔄 Discharge & Releases

| Parameter | Current Source | Potential Excel Sheet | Impact |
|-----------|---------------|---------------------|--------|
| **Controlled Discharge** | Not tracked (0) | Discharge | Authorized water releases |
| **Emergency Discharge** | Not tracked | Discharge | Unplanned releases |
| **Transfer Volumes** | Not tracked | Discharge | Inter-facility transfers |

**Current Behavior:**
- All discharge defaults to 0
- No tracking of water releases

**Proposed Enhancement:**
```
Sheet: Discharge
Columns: Date | Facility Code | Discharge Volume | Discharge Type | Reason | Approval Reference | Notes
```

---

## IMPLEMENTATION PRIORITY

### Priority 1: High Impact ⭐⭐⭐
1. **Environmental Parameters** (Rainfall, Custom Evaporation)
   - Direct impact on water balance accuracy
   - Simple to implement
   - Widely variable parameter

2. **Storage Facility Measurements** (Opening/Closing Volumes)
   - Validates calculated storage changes
   - Improves closure error tracking
   - Essential for reconciliation

3. **Discharge & Releases**
   - Regulatory compliance tracking
   - Currently missing from calculations
   - Critical for audits

### Priority 2: Medium Impact ⭐⭐
4. **Water Consumption** (Dust, Mining, Domestic)
   - Better consumption breakdown
   - Improves accountability
   - Useful for optimization

5. **Production Parameters** (Concentrate, Moisture)
   - Completes product water tracking
   - Minor impact on total balance
   - Good for detailed analysis

### Priority 3: Lower Impact ⭐
6. **Seepage Measurements**
   - Validates seepage model
   - Model currently adequate
   - Difficult to measure accurately

---

## FILE STRUCTURE

### Current Setup (1 File)
```
data/
  └── New Water Balance 20250930 Oct.xlsx
      └── Sheet: "Meter Readings"
          - Source inflows (rivers, boreholes, dewatering)
          - Tonnes Milled
          - RWD (TSF return)
```

### Proposed Setup (2 Files)
```
data/
  ├── New Water Balance 20250930 Oct.xlsx          ← Keep as-is
  │   └── Sheet: "Meter Readings"
  │       - Source inflows
  │       - Tonnes Milled
  │       - RWD
  │
  └── Water_Balance_TimeSeries.xlsx                ← New file
      ├── Sheet: "Documentation"
      ├── Sheet: "Environmental"                   Priority 1
      ├── Sheet: "Storage_Facilities"              Priority 1
      ├── Sheet: "Production"                      Priority 2
      ├── Sheet: "Consumption"                     Priority 2
      ├── Sheet: "Seepage_Losses"                  Priority 3
      └── Sheet: "Discharge"                       Priority 1
```

---

## IMPLEMENTATION APPROACH

### Phase 1: Template Creation ✅
- [x] Create Excel template with all sheets
- [x] Add documentation and instructions
- [x] Include sample data structure

### Phase 2: Data Repository Extension
- [ ] Extend `ExcelTimeSeriesRepository` to support multiple files
- [ ] Add methods for each new data type
- [ ] Implement optional fallback (blank = use defaults)

### Phase 3: Calculator Integration
- [ ] Update `WaterBalanceCalculator` to check new data sources
- [ ] Maintain backward compatibility (blank cells = current behavior)
- [ ] Add source tracking (Excel vs constant vs calculated)

### Phase 4: Import Feature
- [ ] Add UI for importing the new time series file
- [ ] Validate data structure
- [ ] Preview imported data before applying

### Phase 5: Reporting
- [ ] Add source indicators in calculations tab
- [ ] Show "Excel", "Constant", or "Calculated" for each parameter
- [ ] Export reports with data source transparency

---

## BENEFITS

### 🎯 Accuracy
- Actual measured values instead of constants/estimates
- Reduced dependency on default assumptions
- Better closure error tracking

### 📊 Transparency
- Clear data source for each parameter
- Easier to identify data gaps
- Audit trail for regulatory compliance

### 🔄 Flexibility
- Easy to update/correct historical data
- No database changes required
- Simple Excel-based workflow

### 💾 Maintainability
- Separation of concerns (sources vs other parameters)
- Easy backup and version control
- Can update files independently

---

## NEXT STEPS

1. **Test Template**: Fill in sample data for 1-2 months
2. **Implement Reader**: Extend Excel repository for new sheets
3. **Integrate Calculator**: Update water balance calculations
4. **Add Import UI**: Create interface for loading the new file
5. **Documentation**: Update user guides and help docs

---

## NOTES

- All new parameters are **optional** - blank cells use current defaults
- Maintains **backward compatibility** - app works without the new file
- **Incremental adoption** - can populate sheets gradually
- **Source transparency** - UI shows where each value comes from
