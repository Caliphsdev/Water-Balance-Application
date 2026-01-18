# Water Balance Constants - Usage Reference

## Complete Usage Map

| Constant | Category | Used In | Formula/Calculation | Impact |
|----------|----------|---------|---------------------|---------|
| `DEFAULT_MONTHLY_RAINFALL_MM` | Evaporation | `water_balance_calculator.py` | Rainfall fallback when no measurements exist | Affects rainfall calculations when data is missing |
| `evaporation_mitigation_factor` | Optimization | `optimization_engine.py` | Evaporation × (1 - mitigation_factor) | Reduces evaporation losses in optimization scenarios |
| `plant_water_recovery_rate` | Optimization | `optimization_engine.py` | Recovered water = Consumption × recovery_rate | Calculates water recycled within plant operations |
| `tailings_moisture_pct` | Optimization | `water_balance_calculator.py:calculate_tailings_retention()` | Tailings retention = (Ore - Concentrate) × moisture% | Water permanently lost in tailings solids |
| `MINING_WATER_RATE` | Plant | `water_balance_calculator.py` | Mining water = Ore tonnage × mining_rate | Water used in mining operations per tonne |
| `monthly_ore_processing` | Plant | `water_balance_calculator.py` | Fallback ore tonnage when Excel has no data | Default processing tonnage for calculations |
| `ore_density` | Plant | `water_balance_calculator.py` | Volume (m³) = Mass (t) / density (t/m³) | Converts ore mass to volume for moisture calc |
| `ore_moisture_percent` | Plant | `water_balance_calculator.py:calculate_ore_moisture_inflow()` | Moisture inflow = Ore tonnage × density × moisture% | Water brought in with wet ore feed |
| `lined_seepage_rate_pct` | Seepage | `water_balance_calculator.py:calculate_facility_seepage()` | Seepage = Volume × 0.1% (for lined facilities) | Monthly seepage loss for lined dams |
| `unlined_seepage_rate_pct` | Seepage | `water_balance_calculator.py:calculate_facility_seepage()` | Seepage = Volume × 0.5% (for unlined facilities) | Monthly seepage loss for unlined dams |
| `dust_suppression_rate` | Plant | `water_balance_calculator.py:calculate_dust_suppression()` | Dust water = Ore tonnage × dust_rate (m³/t) | Water used for dust control |

## Missing Constants to Add

### dust_suppression_rate
- **Current Status**: Hardcoded fallback (0.02 m³/tonne) in code
- **Category**: Plant
- **Unit**: m³/t
- **Description**: Dust suppression water requirement per tonne of ore processed
- **Typical Range**: 0.01 - 0.05 m³/t
- **Used In**: `calculate_dust_suppression()` - calculates water used for dust control on roads, stockpiles, and ore handling areas

## Constant Location by Module

### water_balance_calculator.py
- `calculate_ore_moisture_inflow()` → `ore_moisture_percent`, `ore_density`
- `calculate_tailings_retention()` → `tailings_moisture_pct` (from monthly table OR constant)
- `calculate_dust_suppression()` → `dust_suppression_rate`
- `calculate_facility_seepage()` → `lined_seepage_rate_pct`, `unlined_seepage_rate_pct`
- `calculate_mining_water()` → `MINING_WATER_RATE`

### optimization_engine.py
- `plant_water_recovery_rate` → Water recycling optimization
- `tailings_moisture_pct` → Tailings dewatering optimization
- `evaporation_mitigation_factor` → Evaporation reduction strategies

## How to Use This Information

For **clients**:
- Shows which operational parameters affect water balance calculations
- Helps identify which constants to adjust for site-specific conditions
- Clarifies the formulas so users understand the impact of changes

For **developers**:
- Quick reference for where constants are consumed
- Helps identify dependencies when modifying calculations
- Documents the calculation logic for each constant
