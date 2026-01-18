# Daily Consumption (370,513 m³/month) - Source Breakdown

## Calculation Path

1. **Water Balance Calculator** (`calculate_total_outflows()`)
   - Sums 6 major outflow components
   
2. **Formula** (line 902 in water_balance_calculator.py):
   ```
   total = mining_use + domestic_use + dust_suppression + discharge + product_moisture + tailings_retention
   ```

3. **Displayed as**:
   - Monthly: 370,513 m³/month
   - Daily: 370,513 ÷ 30 = 12,350 m³/day

---

## Components in the 370,513 m³/month

The 370,513 is the **total of these 6 sources**:

| Component | Purpose | Source |
|-----------|---------|--------|
| **Mining Consumption** | Water used in underground mining operations | Configuration/Constants or Excel |
| **Domestic Consumption** | Personnel water use (offices, housing, sanitation) | Configuration/Constants or Excel |
| **Dust Suppression** | Water sprayed for dust control during ore handling | Configuration/Constants or Excel |
| **Discharge** | Water released to environment (environmental compliance) | Configuration/Constants or Excel |
| **Product Moisture** | Water shipped off-site with concentrated concentrate | Calculated from ore tonnage × concentrate moisture % |
| **Tailings Retention** | Water locked in tailings solids at TSF | Calculated from tailings tonnage × moisture % |

---

## Key Points

- **NOT included** in daily consumption:
  - Evaporation (captured in storage change instead)
  - Seepage loss (captured in storage change instead)
  - TSF Return (recycled water - counted separately as "Dirty Inflows")
  
- **Data sources**:
  - Configuration constants (mining, domestic, dust rates)
  - Excel manual inputs (if configured)
  - Calculated values (product moisture, tailings based on ore/tailings volume)

---

## How to Verify

1. Go to **Calculations** tab
2. Check **"Total Outflows"** section
3. You'll see breakdown of all components
4. Sum of components = 370,513 m³/month in your example

---

## Why Monthly?

The system works on monthly cycles to match:
- Regulatory reporting periods (monthly submissions)
- Mine operational planning (monthly budgets)
- Water supply/demand variations (monthly changes)
