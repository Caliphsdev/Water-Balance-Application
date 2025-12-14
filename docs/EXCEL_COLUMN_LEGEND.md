# Water Balance Flow Column Legend

**Quick Reference Guide for Excel Sheets**

---

## How to Use This Guide

When entering monthly flow data in the Excel workbook (`Water_Balance_TimeSeries_Template.xlsx`), refer to the **Reference Guide sheet** (first tab) to understand what each column represents.

Each column is color-coded by flow type:
- 🟢 **Green** = Water inflow (entering the area)
- 🔴 **Red** = Water outflow (leaving the area)
- 🟡 **Yellow** = Water losses (evaporation, seepage, infiltration)
- 🔵 **Cyan** = Storage (water held in facilities)
- 🟣 **Purple** = Recirculation (water reused internally)
- ⚪ **Gray** = Process (internal process water)

---

## UG2 North Decline (Flows_UG2N)

| Column | Description | Type |
|--------|-------------|------|
| **BOREHOLE_ABSTRACTION** | Water pumped from underground borehole | 🟢 Inflow |
| **RAINFALL_UG2N** | Rainwater collected in UG2 North area | 🟢 Inflow |
| **OFFICES** | Water supplied for offices and ablutions | 🟢 Inflow |
| **ACCOMMODATION** | Water for accommodation facilities (hostels, etc.) | 🟢 Inflow |
| **NDCD1_INFLOW** | Dewatering from North Decline Shaft 1 | 🟢 Inflow |
| **NDCD2_INFLOW** | Dewatering from North Decline Shaft 2 | 🟢 Inflow |
| **RECOVERY_PLANT** | Water from water recovery/treatment plant | 🟢 Inflow |
| **RECYCLED_WATER** | Recycled water returned to process | 🟢 Inflow |
| **SPILLAGE_LOSS** | Water lost through spillage or overflow | 🟡 Loss |
| **SEEPAGE_LOSS** | Water lost through ground seepage | 🟡 Loss |

---

## Merensky North (Flows_MERN)

| Column | Description | Type |
|--------|-------------|------|
| **RAINFALL_MERN** | Rainwater collected in Merensky North area | 🟢 Inflow |
| **MERENSKY_PLANT_INFLOW** | Total water fed to Merensky North plant | 🟢 Inflow |
| **TREATMENT_PLANT** | Treated water from treatment facility | 🟢 Inflow |
| **DISCHARGE_POINT** | Water discharged from the area | 🔴 Outflow |
| **EVAPORATION_LOSS** | Water lost through evaporation | 🟡 Loss |
| **CONSERVATION_POOL** | Water volume stored in conservation pool | 🔵 Storage |

---

## Merensky South (Flows_MERENSKY_SOUTH)

| Column | Description | Type |
|--------|-------------|------|
| **RAINFALL_MERENSKY_SOUTH** | Rainwater collected in Merensky South area | 🟢 Inflow |
| **STORAGE_VOLUME** | Total water in storage facilities | 🔵 Storage |
| **TREATMENT_OUTFLOW** | Treated water returning to process | 🔴 Outflow |
| **EVAPORATION_MERENSKY_SOUTH** | Water lost through evaporation | 🟡 Loss |
| **RECIRCULATION_LOOP** | Water reused in internal loop | 🟣 Recirculation |

---

## UG2 South (Flows_UG2S)

| Column | Description | Type |
|--------|-------------|------|
| **RAINFALL_UG2S** | Rainwater collected in UG2 South area | 🟢 Inflow |
| **UG2S_INFLOW** | Dewatering from UG2 South underground | 🟢 Inflow |
| **OUTFLOW_PLANT** | Water flowing from processing plant | 🔴 Outflow |
| **SEEPAGE_UG2S** | Water lost through seepage | 🟡 Loss |

---

## Stockpile Area (Flows_STOCKPILE)

| Column | Description | Type |
|--------|-------------|------|
| **RAINFALL_STOCKPILE** | Rainwater collected on stockpile surface | 🟢 Inflow |
| **STOCKPILE_RUNOFF** | Runoff water from stockpile slopes | 🔴 Outflow |
| **INFILTRATION_LOSS** | Water soaking into ground below stockpile | 🟡 Loss |
| **PUMP_EXTRACTION** | Water pumped out from stockpile | 🔴 Outflow |
| **TREATMENT_INPUT** | Water sent to treatment facility | 🟢 Inflow |

---

## Old TSF (Tailings Storage Facility) (Flows_OLDTSF)

| Column | Description | Type |
|--------|-------------|------|
| **RAINFALL_OLDTSF** | Rainwater collected in Old TSF area | 🟢 Inflow |
| **TSF_INFLOW** | Water fed into tailings storage facility | 🟢 Inflow |
| **DECANT_OUTFLOW** | Clarified water decanted from TSF | 🔴 Outflow |
| **SEEPAGE_OLDTSF** | Water seeping through TSF walls/base | 🟡 Loss |
| **EVAPORATION_OLDTSF** | Water lost through evaporation from TSF | 🟡 Loss |
| **SPILLWAY_FLOW** | Water flowing through emergency spillway | 🔴 Outflow |

---

## UG2 Processing Plant (Flows_UG2PLANT)

| Column | Description | Type |
|--------|-------------|------|
| **PLANT_INFLOW** | Total water fed to UG2 processing plant | 🟢 Inflow |
| **PROCESS_WATER_USAGE** | Water consumed in mining/processing operations | 🔴 Outflow |
| **RECYCLED_PROCESS_WATER** | Water recycled back into process | 🟢 Inflow |
| **PLANT_OUTFLOW** | Total water leaving the processing plant | 🔴 Outflow |
| **EVAPORATION_UG2PLANT** | Water lost through evaporation at plant | 🟡 Loss |
| **TREATMENT_DISCHARGE** | Treated water discharged after processing | 🔴 Outflow |

---

## Merensky Processing Plant (Flows_MERPLANT)

| Column | Description | Type |
|--------|-------------|------|
| **PLANT_INFLOW_MER** | Total water fed to Merensky processing plant | 🟢 Inflow |
| **PROCESS_WATER_MER** | Water consumed in Merensky processing | 🔴 Outflow |
| **RECYCLED_MER** | Recycled water at Merensky plant | 🟢 Inflow |
| **OUTFLOW_MER** | Total water leaving Merensky plant | 🔴 Outflow |
| **EVAPORATION_MER** | Water lost through evaporation at Merensky | 🟡 Loss |
| **TAILING_THICKENER** | Water in tailings thickening process | ⚪ Process |

---

## Data Entry Tips

1. **All values in m³** (cubic meters per month)
2. **Zero is acceptable** — if a flow doesn't occur some months, enter `0`
3. **Negative values ignored** — the system skips them automatically
4. **Use the Reference Guide sheet** to look up unfamiliar column names
5. **Color coding helps** — quickly spot Inflows (green) vs Losses (yellow)

---

## Area Abbreviations

- **UG2N** = UG2 North Decline
- **MERN** = Merensky North
- **MERENSKY_SOUTH** = Merensky South (mine area)
- **UG2S** = UG2 South Decline
- **OLDTSF** = Old Tailings Storage Facility
- **UG2PLANT** = UG2 Processing Plant
- **MERPLANT** = Merensky Processing Plant

---

## Questions?

If a column name is unclear:
1. Open the Excel file and go to the **Reference Guide** sheet (first tab)
2. Search for the column name — it will have a detailed description
3. Check the color coding (Inflow/Outflow/Loss/Storage/Recirculation)
4. If still unclear, refer to the flow diagram in the application

