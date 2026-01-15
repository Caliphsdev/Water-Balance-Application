# Help Module Fixes - January 2026

## Problem Identified
The Help documentation was mixing old and new code with:
- Unclear water balance equation explanation
- Outdated outflow calculations missing actual components
- Vague inflow descriptions
- Missing references to actual implementation
- Duplicate/confusing Calculations and Formulas sections

## What Was Fixed

### ✅ CALCULATIONS TAB - COMPLETELY REWRITTEN
**Now Shows Exact Current Implementation:**

#### INFLOWS (6 Components)
1. **Surface Water** - From rivers, streams, dams (priority: measured → estimated)
2. **Groundwater** - From boreholes, wells, aquifer abstraction
3. **Underground Water** - From mine dewatering operations
4. **Rainfall** - Direct precipitation on facility surfaces = Regional mm/1000 × Surface area m²
5. **Ore Moisture Water** - From wet ore tonnage (Priority: Excel Tonnes Milled → zero)
6. **RWD (Return Water Dam)** - Only when explicitly in Excel; otherwise TSF calculated

**Key Equation:**
```
Total Inflows = Surface + Groundwater + Underground + Rainfall + Ore Moisture + RWD
Fresh Inflows = Total Inflows - TSF Return (excludes recycled water)
```

#### OUTFLOWS (Actual Components)
1. **Plant Consumption Gross** = Fresh water to plant + TSF Return
2. **TSF Return** = Plant Consumption × 56% (configurable, recycled water)
3. **Plant Consumption Net** = Gross - TSF Return (fresh water actually consumed)
4. **Evaporation Loss** = Regional mm/1000 × Facility surface area m²
5. **Discharge** = Environmental releases (Excel → Measurement → Manual input → Zero)
6. **Product Moisture** = (PGM + Chromite wet tons) × weighted moisture %
7. **Tailings Retention** = Water locked in tailings solids (typically 18-22%)

**Key Equation:**
```
Total Outflows = Net Plant Consumption + Evaporation + Discharge
(Seepage NOT included - it affects storage change, not total outflows)
```

#### PLANT CONSUMPTION Breakdown
**Gross includes:**
- Ore grinding, flotation, filtering
- Product moisture (water in concentrate)
- Tailings retention (water in tailings)
- Dust suppression
- Mining operations
- Domestic/site use

**Calculation when ore data available:**
```
Ore Tonnes × Mining Water Rate (1.43 m³/tonne default)
+ Auxiliary water uses
= Fresh water to plant
+ TSF Return (56% of gross)
= Plant Consumption Gross
```

#### STORAGE CHANGE
```
Net Storage Change = Σ(Closing Volume - Opening Volume) for all facilities
Includes: Opening/closing from Excel, seepage loss (0.5%/month), aquifer gains
```

#### CLOSURE ERROR
```
Closure Error (m³) = |Fresh Inflows - Total Outflows - Storage Change|
Closure Error (%) = (Closure Error / Fresh Inflows) × 100
Status: CLOSED if ≤5%, OPEN if >5%
```

---

### ✅ FORMULAS TAB - COMPLETELY REWRITTEN
**Now Shows All Actual Current Formulas:**

#### Main Water Balance Equation
```
Fresh Inflows - Total Outflows - Storage Change = Closure Error
```

#### Inflow Formulas
- **Surface Water**: Flow meter readings or estimated flow × days
- **Groundwater**: Borehole abstraction (rate × days or direct measurement)
- **Underground/Dewatering**: Pump rates × operating hours
- **Rainfall**: (Regional mm / 1000) × Facility surface area m²
- **Ore Moisture**: Ore tonnes × Ore moisture content %
- **Priority order**: Excel → Database measurements → Zero

#### Outflow Formulas
- **Plant Gross**: Fresh to plant + TSF Return
- **TSF Return**: Plant Consumption × 56% (or Excel RWD if available)
- **Plant Net**: Gross - TSF Return
- **Evaporation**: (Regional mm / 1000) × Surface area per facility
- **Discharge**: Excel → Measurement → Manual input → Zero
- **Product Moisture**: (PGM_wet × PGM_moist + CHR_wet × CHR_moist) / 100
- **Tailings Retention**: Plant consumption × tailings moisture rate

#### Storage Formulas
- **Per Facility**: Closing volume - Opening volume
- **System Total**: Σ(Closing - Opening) for all facilities

#### Closure Error Formula
```
|Fresh In - Total Out - Storage Change| / Fresh In × 100
Target: ≤ 5% (acceptable)
```

#### Supporting KPI Formulas
- **Net Balance**: Total Inflows - Total Outflows
- **Water Efficiency**: Plant output × 100 / Net consumption
- **Recycling Ratio**: TSF Return × 100 / (TSF Return + Fresh Inflows)
- **Days of Operation**: Current storage / Average daily consumption

---

## Removed
- ❌ Vague "Step 1, Step 2, Step 3" descriptions
- ❌ Outdated TSF return explanations
- ❌ Generic formula descriptions
- ❌ Duplicate closure error sections
- ❌ Unclear "legacy total" comments
- ❌ Missing component details

## Added
- ✅ Direct references to actual code (line numbers, variable names)
- ✅ Clear explanation of Fresh vs Total inflows
- ✅ Why TSF Return is counted as inflow
- ✅ Why seepage is NOT in total outflows
- ✅ Excel column references (RWD, Discharge, etc.)
- ✅ Default values (1.43 m³/tonne, 56% TSF, 0.5% seepage, 5% closure threshold)
- ✅ Priority order for all calculations (Excel → Measurement → Default → Zero)
- ✅ KPI and supporting metrics formulas
- ✅ Clear water flow explanation diagram in outflows

## All 8 Help Tabs - Current Status
1. ✅ **Overview** - Application introduction
2. ✅ **Dashboards** - All 6 dashboards documented (Main, KPI, Analytics, Charts, Flow Diagram, Monitoring)
3. ✅ **Calculations** - Water balance with actual equations and component details
4. ✅ **Formulas** - All mathematical formulas currently used
5. ✅ **Water Sources** - Source types and priority order
6. ✅ **Storage** - Facility management and capacity
7. ✅ **Features** - 8 feature categories (Data Management, Settings, Calculation Engine, etc.)
8. ✅ **Troubleshooting** - 11 common issues and solutions

## Testing
✅ Application loads successfully
✅ Help module loads without errors
✅ All 8 tabs present and accessible
✅ No duplicate content
✅ Equations match actual implementation in water_balance_calculator.py

## Impact
Users can now:
- Understand exactly how water balance is calculated
- See the actual formulas used
- Know the default parameters (1.43, 56%, 0.5%, 5%)
- Understand data priorities (Excel → Measurement → Default)
- See which components contribute to each calculation
- Troubleshoot issues with accurate information
