# Water Balance Calculations Guide

This document explains how the application calculates each part of the mine water balance, from individual components through to the final balance and closure check.

The goal is to help users understand **what the app is doing**, **which inputs matter**, and **how to interpret the results**.

---

## 1. Overview of the Water Balance

For each calculation date (usually monthly), the app applies the standard water balance equation:

$$
\text{Closure Error} = \text{Total Inflows} - \text{Total Outflows} - \Delta\text{Storage}
$$

- If the system is perfectly balanced, **Closure Error = 0**.
- In practice, we accept some error due to data gaps and estimates (e.g. \(< 5\%\) of total inflows).

The app calculates:

1. **Total Inflows** (all water entering the system)
2. **Total Outflows** (all water leaving the system or being consumed)
3. **Change in Storage** (net increase/decrease in dam/TSF volumes)
4. **Closure Error** and **Closure Error %**

All of this happens inside `WaterBalanceCalculator.calculate_water_balance()`.

---

## 2. Inflow Calculations

### 2.1 Source Inflows (Rivers, Boreholes, Underground)

Each source (river, borehole, underground dewatering) has an ID and type.

For each source on the calculation date, the app does:

1. **Try a direct measurement** from the `measurements` table:
   - `measurement_type` in `('inflow', 'source_flow')`
   - Uses `volume` if present, otherwise `flow_rate`.
2. **If no measurement**, optionally use **historical averaging** of past data.
3. **If still no value**, fall back to the source default:

$$
\text{Inflow} = \text{average\_flow\_rate} \times \text{reliability\_factor}
$$

- `average_flow_rate` comes from the source definition (e.g. m³/month).
- `reliability_factor` can be stored as **0–1** (fraction) or **0–100** (percent). The calculator automatically adjusts.

#### Example

- Average flow rate (borehole): **10,000 m³/month**
- Reliability factor: **0.9** (90%)

Then:

$$
\text{Inflow} = 10{,}000 \times 0.9 = 9{,}000\;\text{m}^3
$$

If a measurement exists (say **8,500 m³**), that measured value replaces the estimate.

#### Grouping into Inflow Categories

Each source is mapped into a category based on its type name:

- **Surface Water** (rivers, streams, dams)
- **Groundwater** (boreholes)
- **Underground** (dewatering from underground workings)

The app sums all sources in each category:

- `surface_water`
- `groundwater`
- `underground`

These appear in the Inflows tab.

---

### 2.2 Rainfall Inflow

The app converts rainfall (mm) over all storage surfaces into a volume (m³).

1. Get rainfall for the date:
   - If measured: use sum of `rainfall_mm` where `measurement_type = 'rainfall'`.
   - If no measurement: use default constant `DEFAULT_MONTHLY_RAINFALL_MM`.
2. Get total surface area of all storage facilities (m²).
3. Convert mm to m³:

$$
\text{Rainfall Volume} = \frac{\text{rainfall\_mm}}{1000} \times \text{total\_surface\_area}
$$

#### Example

- Rainfall: **50 mm** in the month
- Total surface area (all dams & TSF pond): **200,000 m²**

Then:

$$
\text{Rainfall Volume} = \frac{50}{1000} \times 200{,}000 = 10{,}000\;\text{m}^3
$$

This appears as **Rainfall** in the Inflows tab.

---

### 2.3 Ore Moisture Water

Ore contains moisture. When ore is processed, that water enters the system.

The app finds **tonnes of ore processed** in this order:

1. Explicit `ore_tonnes` passed from the UI
2. Exact-date measurement `tonnes_milled`
3. Exact-date legacy measurement `ore_processed`
4. Default constant `monthly_ore_processing`

Then the app converts ore tonnage into water volume using:

$$
	ext{Ore Moisture Water (m³)} =
\frac{\text{ore tonnes} \times (\text{ore moisture \%} / 100)}{\text{ore density}}
$$

Typical constants:

- `ore_moisture_percent` (e.g. **3.4%**)
- `ore_density` (e.g. **2.7 t/m³**)

#### Example

- Ore processed: **350,000 t**
- Moisture: **3.4%**
- Density: **2.7 t/m³**

$$
\text{Ore Moisture Water} = \frac{350{,}000 \times 0.034}{2.7} \approx 4{,}407\;\text{m}^3
$$

This is shown as **Ore Moisture** in the Inflows tab.

---

### 2.4 Recycled / Return Inflows

The app separates different types of recycled water:

- **TSF Return Water** (from TSF back to process dam; calculated from plant consumption)
- **Plant Returns** (other returns from plant circuits; measured or modeled)
- **Returns to Pit** (water pumped back into pit or from pit sumps)
- **Seepage Gain** (if groundwater flows into storages and is treated as a gain)

#### TSF Return Water (Credited as Inflow)

Calculated from plant consumption (see Section 3):

$$
	ext{TSF Return} = \text{Plant Consumption} \times (\text{TSF Return \%} / 100)
$$

Where **TSF Return %** comes from `tsf_return_percentage` (e.g. **56%**).

#### Plant Returns & Returns to Pit

Taken directly from measurements:

- `measurement_type = 'plant_returns'`
- `measurement_type = 'returns_to_pit'`

If you do not record these, they remain **0**.

#### Seepage Gain

From `measurement_type = 'seepage_gain'` if recorded. If there are only seepage losses, this may be **0**.

---

### 2.5 Total Inflows

All inflow components are added together:

- Surface water
- Groundwater
- Underground
- Rainfall
- Ore moisture
- TSF return (credited as inflow)
- Plant returns
- Returns to pit
- Seepage gain

The app reports:

- Each component separately
- `inflows['total']` = sum of all components above

#### Example Summary

Suppose for a month:

- Surface water: **20,000 m³**
- Groundwater: **9,000 m³**
- Underground: **5,000 m³**
- Rainfall: **10,000 m³**
- Ore moisture: **4,400 m³**
- TSF return: **30,000 m³**
- Plant returns: **2,000 m³**
- Returns to pit: **1,000 m³**
- Seepage gain: **0 m³**

Then:

$$
\text{Total Inflows} = 20{,}000 + 9{,}000 + 5{,}000 + 10{,}000 + 4{,}400 + 30{,}000 + 2{,}000 + 1{,}000 + 0 = 81{,}400\;\text{m}^3
$$

---

## 3. Outflow Calculations

### 3.1 Plant Water Consumption (Gross)

Plant water consumption is proportional to ore processed:

$$
\text{Plant Consumption (Gross)} = \text{ore\_tonnes} \times \text{mining\_water\_per\_tonne}
$$

Where `mining_water_per_tonne` is a constant (e.g. **0.18 m³/t**).

#### Example

- Ore processed: **350,000 t**
- Water per tonne: **0.18 m³/t**

$$
\text{Plant Consumption (Gross)} = 350{,}000 \times 0.18 = 63{,}000\;\text{m}^3
$$

### 3.2 TSF Return Water (Calculated Outflow Component)

From Section 2.4, TSF return is:

$$
\text{TSF Return} = \text{Plant Consumption (Gross)} \times (\text{TSF Return %} / 100)
$$

This is **subtracted** from plant consumption to give **net** consumption, but is **credited** as an inflow.

#### Example (continued)

- Plant gross: **63,000 m³**
- TSF return %: **56%**

$$
\text{TSF Return} = 63{,}000 \times 0.56 = 35{,}280\;\text{m}^3
$$

Net plant consumption:

$$
\text{Plant Consumption (Net)} = 63{,}000 - 35{,}280 = 27{,}720\;\text{m}^3
$$

### 3.3 Tailings Moisture Retention

Some water is permanently locked up in the tailings (as moisture). The app models this as a percentage of **non-returned** plant water:

1. Non-returned water:

$$
\text{Non-returned water} = \text{Plant Consumption (Gross)} \times (1 - \text{TSF Return %})
$$

2. Tailings moisture retention:

$$
\text{Tailings Retention} = \text{Non-returned water} \times \text{tailings\_moisture\_retention\_pct}
$$

Where `tailings_moisture_retention_pct` is usually **15–25%**.

#### Example

- Plant gross: **63,000 m³**
- TSF return %: **56%**
- Tailings moisture retention: **20%**

Non-returned water:

$$
63{,}000 \times (1 - 0.56) = 63{,}000 \times 0.44 = 27{,}720\;\text{m}^3
$$

Tailings retention:

$$
27{,}720 \times 0.20 = 5{,}544\;\text{m}^3
$$

### 3.4 Evaporation Losses

Evaporation is calculated using a monthly rate for the site and the total surface area of all storage facilities.

1. Get evaporation mm for the month from the `evaporation_rates` table.
2. Get total surface area of all storage facilities (m²).
3. Convert mm to m³:

$$
\text{Evaporation Volume} = \frac{\text{evap\_mm}}{1000} \times \text{total\_surface\_area}
$$

#### Example

- Evaporation: **120 mm/month**
- Total surface area: **200,000 m²**

$$
\text{Evaporation Volume} = \frac{120}{1000} \times 200{,}000 = 24{,}000\;\text{m}^3
$$

### 3.5 Seepage Losses

If there are measurements with `measurement_type = 'seepage_loss'`, these are used.

If not, the app applies a default seepage rate per facility:

$$
\text{Seepage Loss} = \sum_{\text{facilities}} (\text{current\_volume} \times \text{default\_seepage\_rate\_pct})
$$

Where `default_seepage_rate_pct` is a constant (e.g. **0.5%/month**).

#### Example

- Single dam current volume: **500,000 m³**
- Default seepage rate: **0.5%**

$$
\text{Seepage Loss} = 500{,}000 \times 0.005 = 2{,}500\;\text{m}^3
$$

### 3.6 Dust Suppression

If you record dust suppression in `measurements` (type `dust_suppression`), those values are used.

If not, the app estimates from ore tonnage:

$$
\text{Dust Suppression} = \text{ore\_tonnes} \times \text{dust\_suppression\_rate}
$$

Where `dust_suppression_rate` is a constant (e.g. **0.02 m³/t**).

#### Example

- Ore processed: **350,000 t**
- Dust suppression rate: **0.02 m³/t**

$$
\text{Dust Suppression} = 350{,}000 \times 0.02 = 7{,}000\;\text{m}^3
$$

### 3.7 Other Outflows

From measurements and constants:

- **Mining Consumption**: `measurement_type = 'mining_consumption'`
- **Domestic Consumption**: `measurement_type = 'domestic_consumption'`
- **Controlled Discharge**: `measurement_type = 'discharge'`
- **Product Moisture**:

$$
\text{Product Moisture} = \text{concentrate\_tonnes} \times (\text{concentrate\_moisture\_%} / 100)
$$

Where:

- `monthly_concentrate_production` = tonnes/month
- `concentrate_moisture` = % moisture

### 3.8 Total Outflows (Used for Closure Check)

For the closure error calculation, the app uses a simplified definition:

$$
\text{Total Outflows} = \text{Plant Consumption (Net)} + \text{Evaporation} + \text{Discharge}
$$

- **Plant Consumption (Net)** already accounts for TSF return.
- Other losses (dust suppression, seepage, product moisture, etc.) are still shown in reports and KPIs, but the core **closure test** is aligned with the legacy Excel model using the formula above.

#### Example Summary

From earlier examples:

- Plant net consumption: **27,720 m³**
- Evaporation: **24,000 m³**
- Discharge: say **5,000 m³**

Then:

$$
\text{Total Outflows} = 27{,}720 + 24{,}000 + 5{,}000 = 56{,}720\;\text{m}^3
$$

Other reported outflows (not in the closure total but visible in UI):

- Tailings retention: **5,544 m³**
- Dust suppression: **7,000 m³**
- Seepage loss: **2,500 m³**
- Mining/domestic consumption, product moisture, etc.

---

## 4. Storage Change (ΔStorage)

The app calculates change in storage across all dams and TSF facilities by running a **facility-level balance**.

### 4.1 Per-Facility Balance

For each facility:

- **Opening volume**: `current_volume` (at start of period)
- **Inflows**:
  - Facility/pump/transfer inflows from `measurements`
  - Rainfall on that facility: \((\text{rainfall\_mm} / 1000) \times \text{surface\_area}\)
- **Outflows**:
  - Facility/pump/transfer outflows and discharges
  - Evaporation: \((\text{evap\_mm} / 1000) \times \text{surface\_area}\)
  - Seepage: \(\text{current\_volume} \times \text{default\_seepage\_rate\_pct}\)

Then:

$$
\text{Net Balance} = \text{Inflows} - \text{Outflows}
$$

$$
\text{Closing Volume (pre-clamp)} = \text{Opening Volume} + \text{Net Balance}
$$

The app then **clamps** closing volume between 0 and capacity:

- If above capacity → overflow is tracked
- If below 0 → deficit is tracked and closing volume set to 0

The final **Net Balance** used in reports is:

$$
\text{Net Balance (final)} = \text{Closing Volume} - \text{Opening Volume}
$$

### 4.2 Aggregated Storage Change

Across all facilities:

- `total_opening_volume` = sum of opening volumes
- `total_closing_volume` = sum of closing volumes

Net change in storage:

$$
\Delta\text{Storage} = \text{total\_closing\_volume} - \text{total\_opening\_volume}
$$

This is reported as **Storage Change** in the Summary tab.

#### Example

Two facilities:

1. Process Dam
   - Opening: **300,000 m³**
   - Closing: **320,000 m³**
2. TSF Pond
   - Opening: **700,000 m³**
   - Closing: **690,000 m³**

Totals:

- Opening: **1,000,000 m³**
- Closing: **1,010,000 m³**

Then:

$$
\Delta\text{Storage} = 1{,}010{,}000 - 1{,}000{,}000 = +10{,}000\;\text{m}^3
$$

Positive ΔStorage means **more water stored** at the end than at the start.

---

## 5. Final Balance and Closure Check

After inflows, outflows, and ΔStorage are calculated, the app computes:

### 5.1 Closure Error (m³)

$$
\text{Closure Error} = \text{Total Inflows} - \text{Total Outflows} - \Delta\text{Storage}
$$

- If everything is perfect: **Closure Error = 0**.
- Normally, some error is expected due to measurement gaps, estimates, and rounding.

### 5.2 Closure Error (%)

Percentage error, relative to total inflows:

$$
\text{Closure Error %} = \begin{cases}
\dfrac{|\text{Closure Error}|}{\text{Total Inflows}} \times 100 & \text{if Total Inflows} > 0 \\
0 & \text{otherwise}
\end{cases}
$$

The app also sets a status:

- **CLOSED** if Closure Error % < 5%
- **OPEN** otherwise

(The threshold can be adjusted via configuration/constants.)

### 5.3 Net Balance (Surplus/Deficit)

This is a simpler indicator:

$$
\text{Net Balance} = \text{Total Inflows} - \text{Total Outflows}
$$

- **Net Balance > 0** → Surplus (more water coming in than going out)
- **Net Balance < 0** → Deficit

Combined with current storage, the app determines risk of shortage or overflow in `calculate_deficit_surplus()`.

### 5.4 Example Closure Check

Using earlier examples:

- Total Inflows = **81,400 m³**
- Total Outflows = **56,720 m³**
- ΔStorage = **+10,000 m³**

Closure Error:

$$
\text{Closure Error} = 81{,}400 - 56{,}720 - 10{,}000 = 14{,}680\;\text{m}^3
$$

Closure Error %:

$$
\text{Closure Error %} = \dfrac{|14{,}680|}{81{,}400} \times 100 \approx 18.0\% 
$$

In this example, the error is **18%**, which is **above** the typical 5% target, so the status would be **OPEN** and you should review:

- Meter data (missing or zero readings?)
- Rainfall and evaporation assumptions
- TSF return assumptions
- Any unrecorded discharges or leaks

---

## 6. How to Use This Guide

- Use this document when reviewing **unexpected balances** or **high closure errors**.
- When a category looks too high or too low in the UI, check the matching formula here and see which input (meter, constant, assumption) is driving it.
- If needed, update:
  - Measurements (via the **Measurements** module)
  - Constants and assumptions (via **Settings** → **Constants/Scenarios**)

For questions or future enhancements, this document can be extended with **site-specific notes**, such as which sources map to which categories, or which facilities are considered part of the core balance.