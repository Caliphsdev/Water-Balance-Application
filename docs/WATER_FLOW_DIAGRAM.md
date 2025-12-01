# Water Balance System - Flow Diagram

## Overview
This document explains how water flows through the mining operation water balance system.

---

## 🌊 COMPLETE WATER FLOW DIAGRAM

```
═══════════════════════════════════════════════════════════════════════════════════════════
                           MINING WATER BALANCE SYSTEM
═══════════════════════════════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                          💧 FRESH WATER SOURCES (219,405 m³)                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
         │
         ├──→ Surface Water (94,194 m³) ────────┐
         ├──→ Underground Dewatering (87,530 m³) │
         ├──→ Groundwater/Boreholes (21,261 m³)  │
         ├──→ Seepage Gain (12,000 m³) ──────────┤ ──→ TOTAL FRESH WATER
         ├──→ Ore Moisture (3,855 m³) ───────────│     AVAILABLE: 219,405 m³
         └──→ Rainfall (565 m³) ─────────────────┘
                                                  │
                                                  │
         ┌────────────────────────────────────────┴────────────────────────────────────────┐
         │                        WATER DISTRIBUTION                                       │
         │                                                                                  │
         │  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────────┐  │
         │  │  AUXILIARY      │    │   MAIN PLANT     │    │   ENVIRONMENTAL          │  │
         │  │  OPERATIONS     │    │   PROCESSING     │    │   LOSSES                 │  │
         │  │                 │    │                  │    │                          │  │
         │  │  51,500 m³      │    │   167,905 m³     │    │    17,256 m³             │  │
         │  └─────────────────┘    └──────────────────┘    └──────────────────────────┘  │
         │                                                                                  │
         └──────────────────────────────────────────────────────────────────────────────────┘
                 │                           │                           │
                 │                           │                           │
                 ▼                           ▼                           ▼

┌───────────────────────┐   ┌─────────────────────────────────────┐   ┌──────────────────────┐
│   AUXILIARY USES      │   │      MAIN PLANT PROCESSING          │   │  ENVIRONMENTAL LOSS  │
│   (Non-recoverable)   │   │                                     │   │  (Non-recoverable)   │
├───────────────────────┤   ├─────────────────────────────────────┤   ├──────────────────────┤
│                       │   │                                     │   │                      │
│ • Dust Suppression    │   │  Fresh Water: 167,905 m³            │   │ • Evaporation        │
│   15,000 m³           │   │       +                             │   │   2,256 m³           │
│                       │   │  TSF Return: 158,118 m³ ◄───────┐   │   │                      │
│ • Mining Operations   │   │       =                         │   │   │ • Controlled         │
│   28,000 m³           │   │  GROSS: 326,023 m³              │   │   │   Discharge          │
│                       │   │                                 │   │   │   15,000 m³          │
│ • Domestic Use        │   │  ┌───────────────────────────┐  │   │   │                      │
│   8,500 m³            │   │  │   PROCESSING PLANT        │  │   │   │                      │
│                       │   │  │                           │  │   │   │                      │
│                       │   │  │  • Ore Grinding           │  │   │   │                      │
│                       │   │  │  • Flotation Circuits     │  │   │   │                      │
│                       │   │  │  • Concentrate Filtering  │  │   │   │                      │
│                       │   │  │  • Tailings Thickening    │  │   │   │                      │
│                       │   │  └───────────────────────────┘  │   │   │                      │
│                       │   │              │                  │   │   │                      │
│                       │   │              ▼                  │   │   │                      │
│                       │   │  ┌───────────────────────────┐  │   │   │                      │
│                       │   │  │    PLANT OUTPUTS          │  │   │   │                      │
│                       │   │  ├───────────────────────────┤  │   │   │                      │
│                       │   │  │ • Concentrate + Moisture  │  │   │   │                      │
│                       │   │  │   (1,000 m³ locked up)    │  │   │   │                      │
│                       │   │  │                           │  │   │   │                      │
│                       │   │  │ • Tailings Slurry ─────►  │  │   │   │                      │
│                       │   │  │   (to TSF)                │  │   │   │                      │
│                       │   │  └───────────────────────────┘  │   │   │                      │
│                       │   │              │                  │   │   │                      │
└───────────────────────┘   └──────────────┼──────────────────┘   └──────────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────┐
                            │  TAILINGS STORAGE FACILITY (TSF) │
                            ├──────────────────────────────────┤
                            │                                  │
                            │  Receives slurry from plant      │
                            │                                  │
                            │  • Solids settle to bottom       │
                            │  • Water retained in tailings:   │
                            │    102,765 m³ (35% moisture)     │
                            │                                  │
                            │  • Clear water returns to plant  │
                            │    158,118 m³ (TSF Return) ──────┘
                            │                                   (Recycled ♻️)
                            │  • Seepage Loss: 45,000 m³       │
                            │    (affects storage change)      │
                            │                                  │
                            └──────────────────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────┐
                            │      STORAGE FACILITIES          │
                            │                                  │
                            │  Opening Volume: 147,000 m³      │
                            │  Closing Volume: 160,000 m³      │
                            │                                  │
                            │  NET CHANGE: +13,000 m³          │
                            └──────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════════
                                MASS BALANCE SUMMARY
═══════════════════════════════════════════════════════════════════════════════════════════

  INPUTS (Fresh Water):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Total Fresh Water IN:                219,405 m³  (100%)

  OUTPUTS:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Main Plant (net):                    167,905 m³  (76.5%)
    Auxiliary Operations:                 51,500 m³  (23.5%)
    Environmental Losses:                 17,256 m³  ( 7.9%)
    ──────────────────────────────────────────────────────────────────────────────────
    TOTAL OUTFLOWS:                      236,662 m³  (107.9%) ⚠️  Exceeds input!

  STORAGE:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Storage Increase:                     13,000 m³  ( 5.9%)

  BALANCE:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Closure Error:                       -30,256 m³  (13.8%)
    
    ⚠️  Outflows + Storage exceed Fresh Input by 30,256 m³
    
    Typical causes of closure error (10-15% is common):
      • Unmeasured evaporation from plant processes
      • Flow meter measurement uncertainties
      • Timing differences in monthly data aggregation
      • Dust suppression water evaporating before reaching destination
      • Unmeasured seepage from conveyance pipes/channels

═══════════════════════════════════════════════════════════════════════════════════════════
```

---

## 📊 KEY CONCEPTS

### 1. **Fresh vs. Recycled Water**

- **Fresh Water**: New water entering the system from external sources
  - Must be measured and managed carefully (limited resource)
  - Total: 219,405 m³/month in this example

- **Recycled Water (TSF Return)**: Water returning from tailings storage
  - Already counted when it first entered as fresh water
  - NOT counted again in fresh water totals (would be double-counting)
  - Total: 158,118 m³/month recycled (48.5% recycling rate)

### 2. **Plant Consumption**

- **Gross Plant Consumption**: Total water circulating in plant
  - = Fresh water to plant + TSF return
  - = 167,905 + 158,118 = 326,023 m³
  - This is the water:ore ratio needed for processing

- **Net Plant Consumption**: Fresh water actually consumed by plant
  - = Gross - TSF return
  - = 326,023 - 158,118 = 167,905 m³
  - This is the "new" water the plant needs

### 3. **Component Relationships**

**Components WITHIN Plant Consumption:**
- Tailings retention (102,765 m³) - water locked in tailings
- Product moisture (1,000 m³) - water locked in concentrate
- These are sub-components showing where plant water goes

**Components SEPARATE from Plant:**
- Dust suppression (15,000 m³)
- Mining operations (28,000 m³)
- Domestic use (8,500 m³)
- Evaporation (2,256 m³)
- Discharge (15,000 m³)

### 4. **Seepage Loss**

**Important**: Seepage loss (45,000 m³) is NOT included in total outflows because:
- When facilities lose water to seepage, their volumes decrease
- This decrease is captured in the "Storage Change" calculation
- Including seepage in both outflows AND storage would double-count it
- Seepage is shown separately for analysis/monitoring purposes

### 5. **Total Outflows Calculation**

```
Total Outflows = Net Plant + Auxiliary + Environmental
               = 167,905 + 51,500 + 17,256
               = 236,662 m³
```

**Why not include seepage?**
- Seepage affects storage (water leaves facilities → volume decreases)
- Storage change already captures this effect
- Total outflows represents water leaving the SYSTEM, not just facilities

### 6. **Water Balance Equation**

**Scientifically Correct Formula:**
```
Fresh Water IN = Outflows + Storage Change + Closure Error

219,405 = 236,662 + 13,000 + (-30,256)
219,405 = 219,407  (2 m³ rounding difference)
```

**Why not use Total Inflows (including TSF return)?**
- TSF return is recycled - already counted when it first entered
- Using total inflows would artificially inflate the water budget
- Fresh water is the limiting resource we need to manage

---

## 💧 WATER EFFICIENCY METRICS

### Recycling Rate
```
Recycling Rate = TSF Return / Gross Plant × 100%
               = 158,118 / 326,023 × 100%
               = 48.5%
```

**Industry Benchmarks:**
- Excellent: > 70%
- Good: 50-70%
- Adequate: 30-50%
- Poor: < 30%

**This operation: 48.5% (Adequate to Good)**

### Fresh Water Intensity
```
Fresh Water Intensity = Fresh Water IN / Ore Processed
                      = 219,405 / 306,116
                      = 0.717 m³/tonne
```

**Industry Benchmarks:**
- Excellent: < 0.5 m³/tonne
- Good: 0.5-1.0 m³/tonne
- Moderate: 1.0-2.0 m³/tonne
- High: > 2.0 m³/tonne

**This operation: 0.717 m³/tonne (Good)**

### Plant Water Use
```
Plant Water Use = Net Plant Consumption / Ore Processed
                = 167,905 / 306,116
                = 0.549 m³/tonne
```

This shows how much fresh water the main plant needs per tonne of ore processed.

---

## 🔄 MONTHLY CYCLE

This water balance represents a snapshot for **October 2025**. The cycle repeats monthly with:

1. **Fresh water sources** replenish (rivers, boreholes, rainfall)
2. **Storage facilities** carry over closing volumes as next month's opening
3. **TSF return** continues recycling (amount varies by plant efficiency)
4. **Closure error** may vary month-to-month (measurement variations)

---

## 📈 IMPROVING WATER EFFICIENCY

To reduce fresh water demand:

1. **Increase recycling** from 48.5% → 60-70%
   - Improve TSF return water quality/flow
   - Install additional recycling pumps

2. **Reduce losses** (currently 17,256 m³ environmental + 30,256 m³ unaccounted)
   - Fix leaks in conveyance systems
   - Cover water storage to reduce evaporation
   - Improve dust suppression efficiency

3. **Optimize plant processes**
   - Reduce water:ore ratio where possible
   - Install water-efficient technologies
   - Monitor and control consumption in real-time

---

## ✅ VALIDATION CHECKLIST

When reviewing water balance:

- [x] Fresh water sources identified and measured
- [x] TSF return calculated (not double-counted)
- [x] Plant consumption split into gross/net
- [x] Auxiliary uses accounted separately
- [x] Environmental losses tracked
- [x] Seepage shown but not double-counted
- [x] Storage change calculated
- [x] Closure error < 15% (13.8% - acceptable)
- [x] Water efficiency metrics calculated

---

## 📞 QUESTIONS?

For clarification on any aspect of the water balance system:
- Review inline code documentation in `water_balance_calculator.py`
- Check calculation methods for specific components
- Verify Excel template data in `Water_Balance_TimeSeries_Template.xlsx`

**Last Updated**: November 26, 2025
**Closure Error Status**: 13.8% (Acceptable - within typical range for mining operations)
