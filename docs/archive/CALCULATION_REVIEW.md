# Water Balance Calculation System - Review

## 📊 Current Architecture Overview

### 1. **Dual Calculation System**

The calculations dashboard uses TWO separate calculation engines:

#### A. **WaterBalanceCalculator** (`src/utils/water_balance_calculator.py`)
- **Purpose**: Complex water balance with operational data
- **Data Sources**:
  - Database: system_constants, water_sources, facilities, measurements
  - Excel: Time-series data (boreholes, rivers, dewatering)
  - Historical averaging: Past 6-12 months of data
- **Outputs**: Monthly water balance with detailed breakdown
- **Complexity**: 2000+ lines, handles:
  - Source inflows (rivers, boreholes, dewatering)
  - Plant water consumption
  - TSF return water
  - Evaporation calculations
  - Storage level changes
  - Recovery factors and scenario overrides

#### B. **BalanceCheckEngine** (`src/utils/balance_check_engine.py`)
- **Purpose**: Simple balance check using template files only
- **Data Sources**: 
  - `INFLOW_CODES_TEMPLATE.txt` (34 entries, 8 areas)
  - `OUTFLOW_CODES_TEMPLATE_CORRECTED.txt` (64 entries, 8 areas)
  - `DAM_RECIRCULATION_TEMPLATE.txt` (12 entries)
- **Outputs**: Quick verification metrics
- **Complexity**: ~230 lines, simplified balance equation

---

## 🔄 Calculation Flow in Dashboard

```
User clicks "Calculate Balance"
        ↓
_calculate_balance() called
        ↓
    ├─→ WaterBalanceCalculator.calculate_water_balance(date, ore_tonnes)
    │    └─→ Returns: { inflows, outflows, storage, balance }
    │
    ├─→ BalanceCheckEngine.calculate_balance()
    │    └─→ Returns: Overall & per-area metrics
    │
    └─→ Updates 6 tabs:
         1. Balance Check Summary (from balance_engine)
         2. Area Balance Breakdown (from balance_engine)
         3. Summary (from calculator)
         4. Inflows (from calculator)
         5. Outflows (from calculator)
         6. Storage (from calculator)
```

---

## 📋 Key Data Points per Calculation

### **Balance Check Engine Output**
```
Overall Metrics:
  ✅ Total Inflows: 5,157,071 m³ (34 sources from template)
  🚰 Total Outflows: 5,136,756 m³ (64 flows from template)
  ♻️ Recirculation: 12,223 m³ (12 loops from template)
  ⚖️ Balance Diff: 8,092 m³
  📊 Error %: 0.16% (Good)

Per-Area Breakdown (8 areas):
  - NDCD1-4 (Merensky North Decline)
  - NDSWD1-2 (Merensky Plant)
  - MDCD5-6 (Merensky South Decline)
  - MDSWD3-4 (Merensky South Plant)
  - OLD_TSF (Tailings Storage)
  - STOCKPILE (Stockpile Area)
  - UG2_NORTH (UG2 North)
  - UG2_PLANT (UG2 Plant)
```

### **Water Balance Calculator Output**
```
Detailed Calculations:
  1. Source Inflows
     - Rivers (from Excel or default)
     - Boreholes (from Excel or default)
     - Dewatering (from underground operations)
  
  2. Consumption
     - Mining water per tonne × ore input
     - Processing water per tonne
     - Dust suppression losses
  
  3. Recovery
     - TSF return water
     - Facility recycling
     - Recovery factors by type
  
  4. Losses
     - Evaporation (from constants)
     - Seepage/losses
     - Unmeasured flows
  
  5. Storage Changes
     - Storage facility level changes
     - Closing vs opening balance
```

---

## ✅ Current Strengths

| Aspect | Status |
|--------|--------|
| **Dual validation** | ✅ Two independent calculations verify each other |
| **Template-based checking** | ✅ Quick sanity checks without database dependency |
| **Detailed breakdown** | ✅ 6 different view tabs for different users |
| **Area exclusion** | ✅ Can exclude areas from balance calc |
| **Historical averaging** | ✅ Falls back to 6-month average if no current data |
| **Scenario support** | ✅ Can apply constant overrides per scenario |
| **Performance** | ✅ Caching of expensive calculations |

---

## ⚠️ Potential Issues / Questions to Explore

### 1. **Data Source Discrepancies**
   - Balance engine uses only templates (fixed 8 areas)
   - Calculator uses database + Excel (50+ water sources)
   - **Question**: Which is authoritative? When do they disagree?

### 2. **Missing Water Sources in Templates**
   - Templates have fixed entries (34 inflows, 64 outflows)
   - Database may have 50+ active water sources
   - **Question**: Are new sources being captured?

### 3. **Ore Tonnes Input**
   - User must enter ore tonnes manually
   - Not auto-fetched from database
   - **Question**: Is there a time-series for ore production?

### 4. **Calculation Date**
   - User must select calculation date manually
   - **Question**: Should it auto-default to latest available?

### 5. **Template Updates**
   - Inflows/outflows are in .txt files (user-editable)
   - No automatic sync with database flows
   - **Question**: When templates change, are they reflected in calculations?

### 6. **Error Thresholds**
   - Good: < 0.5% error
   - Excellent: < 0.1% error
   - **Question**: Are these thresholds suitable for mining operations?

---

## 🎯 Next Steps to Consider

### Option A: **Validation & Alignment**
- Compare calculator vs template engine outputs
- Identify data gaps between database and templates
- Document which data source is authoritative

### Option B: **Enhanced Automation**
- Auto-fetch latest ore production data
- Auto-detect latest calculation date
- Auto-sync new flows from database to templates

### Option C: **Reporting & Export**
- Add PDF/Excel export of balance reports
- Add historical trend analysis
- Add variance analysis (actual vs forecast)

### Option D: **Scenario Modeling**
- What-if analysis: "If ore goes up 10%, water demand?"
- Sensitivity analysis: "Which factor impacts balance most?"
- Forecasting: "Predict next month's balance"

### Option E: **Integration with Flow Diagram**
- Use flow diagram flows as data source for balance calculation
- Instead of templates, read from flow_diagram.json
- Real-time balance updates as flows change in diagram

---

## 📌 Recommended Review Items

1. **Data Integrity**: Run both calculators and compare outputs
2. **Template Coverage**: Check if all active database flows are in templates
3. **User Workflow**: Is the current calculation process intuitive?
4. **Output Format**: Are the 6 tabs the right view for users?
5. **Performance**: Is <1s total calculation time acceptable?

---

**Last Updated**: 2025-12-14
**Created for**: Water Balance Application Review Session
