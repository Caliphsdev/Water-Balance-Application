# Water Balance Metrics - Tooltip Guide

## System Balance Tab Metrics

This guide explains each metric displayed in the **System Water Balance (Regulator Mode)** tab and what the tooltips mean.

---

## Master Balance Equation

```
(Fresh Inflows + Dirty Inflows) − Total Outflows − ΔStorage = Balance Error
```

The goal is to have Balance Error = 0 (perfect closure).

---

## Key Metrics Explained

### **Fresh Inflows** 💧
- **What it is**: Natural water entering the system
- **Components**:
  - Surface Water (rivers, streams)
  - Groundwater (aquifer abstraction)
  - Rainfall (direct precipitation)
  - Underground (dewatering from mining)
  - Ore Moisture (water contained in ore)
- **Good to know**: Baseline for water availability

---

### **Dirty Inflows** ♻️
- **What it is**: Recycled or recirculated water
- **Components**:
  - Return Water Dam (RWD) - treated water returning from plant
  - TSF Return - water from tailings storage facility
- **Good to know**: Allows the system to reuse water, reducing fresh water demand

---

### **Total Outflows** 🚰
- **What it is**: All water leaving the system
- **Components**:
  - Mining Consumption (used in extraction processes)
  - Domestic Consumption (offices, accommodation)
  - Plant Consumption (processing requirements)
  - Discharge (environmental release)
  - Evaporation (loss to atmosphere)
  - Dust Suppression (water sprayed for dust control)
  - Tailings Retention (water stored with tailings)
  - Product Moisture (water in final product)
- **Good to know**: Should roughly equal Total Inflows + Opening Storage - Closing Storage

---

### **Total Inflows** 📊
- **What it is**: Fresh Inflows + Dirty Inflows
- **Formula**: Total Inflows = Fresh + Recycled
- **Good to know**: Total water available to the system each month

---

### **ΔStorage (Delta Storage)** 📈
- **What it is**: Change in storage volume during the period
- **Interpretation**:
  - **Positive** = Storage increased (dam filled up)
  - **Negative** = Storage decreased (water drawn down)
  - **Zero** = Storage stable
- **Formula**: ΔStorage = Closing Volume - Opening Volume
- **Good to know**: Large positive values = high water security. Large negative values = depletion risk

---

### **Balance Error** ⚠️
- **What it is**: Residual unaccounted water
- **Formula**: Balance Error = (Fresh + Dirty) - Outflows - ΔStorage
- **Interpretation**:
  - **< ±5%**: Excellent - good data quality
  - **5-10%**: Acceptable - minor measurement variations
  - **> 10%**: Investigate - likely measurement or data quality issue
- **Common causes of high error**:
  - Unmeasured inflows (seepage, groundwater)
  - Unmeasured outflows (evaporation underestimated)
  - Meter calibration issues
  - Manual input errors
  - Missing data points

---

### **Error %** 📉
- **What it is**: Balance error expressed as percentage of total inflows
- **Formula**: Error % = (Balance Error ÷ Total Inflows) × 100
- **Thresholds**:
  - **< 5%**: GREEN - Closed ✅
  - **5-10%**: YELLOW - Acceptable
  - **> 10%**: RED - Investigate ⚠️
- **Good to know**: This is the primary closure metric regulators use to assess data quality

---

### **Status** 🔴🟢
- **What it is**: Overall balance closure status
- **States**:
  - **✅ CLOSED** - Error < 5% (good)
  - **⚠️ CHECK REQUIRED** - Error ≥ 5% (needs investigation)
- **What to do if CHECK REQUIRED**:
  1. Review fresh water source measurements
  2. Verify outflow meter calibrations
  3. Check for data entry errors
  4. Confirm storage opening/closing levels
  5. Look for missed flows (seepage, evaporation)

---

### **Opening Volume** 📍
- **What it is**: Storage level at start of period
- **Unit**: m³
- **Good to know**: Baseline for calculating storage change

---

### **Closing Volume** 📍
- **What it is**: Storage level at end of period
- **Unit**: m³
- **Good to know**: Reflects water security at period end

---

### **Net Change** 📊
- **What it is**: Closing Volume - Opening Volume
- **Interpretation**:
  - **Positive**: Water accumulated (safety margin improved)
  - **Negative**: Water consumed (storage depleted)
- **Risk assessment**:
  - Sustained negative = drought/insufficient supply
  - Sustained positive = good water balance

---

## Troubleshooting High Closure Errors

| Error % | Likely Issue | Action |
|---------|--------------|--------|
| 5-10% | Minor meter drift | Calibrate meters |
| 10-20% | Missing small flows | Identify & add seepage, leakage |
| 20-50% | Major unmeasured flow | Check TSF return, groundwater estimates |
| > 50% | Data quality issue or model error | Review all input sources |

---

## Tips for Better Closure

1. **Meter Maintenance**: Regularly calibrate all flow meters
2. **Data Consistency**: Use same measurement units throughout
3. **Peak Validation**: Check high/low values for outliers
4. **Cross-Check**: Compare to historical monthly patterns
5. **Documentation**: Record any manually entered vs measured data
6. **Review Frequency**: Check closure monthly, not just annually

---

## Questions?

Hover over any metric card in the Balance Tab to see its tooltip explanation in the status bar at the bottom of the screen.
