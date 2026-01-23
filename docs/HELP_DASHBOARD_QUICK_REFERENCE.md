# Help Dashboard - Complete Feature Coverage Reference

**Last Updated:** January 23, 2026

## Evaporation Documentation ✅

### What is Evaporation?
- **Type:** Source Pan Evaporation (Standard Category A Measurement)
- **Units:** mm/month
- **Application:** Regional rates applied to individual facilities based on surface area
- **Formula:** `(Evaporation mm / 1000) × Surface Area m² = Loss (m³)`

### Where to Configure
**Settings → Environmental Parameters → Regional Evaporation**
- Set monthly rates (January through December) in mm/month
- Configure evaporation zone (default: 4A)
- Per-facility enable/disable via "Include in evaporation" checkbox

### In Balance Calculations
- Treated as **outflow** (loss from storage)
- Applied only to facilities with `evap_active = 1`
- Capped at current facility volume (can't go negative)
- Auto-sums across all facilities

### Typical Ranges
- **Summer months:** 200-300 mm/month
- **Winter months:** 50-100 mm/month
- **Region-dependent:** Check local meteorological data

---

## Storage Facilities Features ✅

### Configuration Options
| Feature | Setting | Type | Default |
|---------|---------|------|---------|
| Evaporation Participation | evap_active | Checkbox | Enabled |
| Seepage Loss (Unlined) | unlined_seepage_rate_pct | Constant | 0.5%/month |
| Seepage Loss (Lined) | lined_seepage_rate_pct | Constant | 0.1%/month |
| Aquifer Seepage Gain | aquifer_gain_rate_pct | Per-facility | 0.0% |
| Pump Trigger Level | pump_start_level | Per-facility | 70% |
| Pump Stop Level | pump_stop_level | Per-facility | 20% |

### Per-Facility Monthly Parameters
Access: **Storage Facilities → Select Facility → Edit Monthly Parameters**

Can configure:
- Monthly inflow (m³)
- Monthly outflow (m³)
- Monthly abstraction (m³)

---

## Environmental Parameters ✅

### Location
**Settings → Environmental Tab**

### Configurable Items
1. **Evaporation Zone**
   - Default: 4A
   - Purpose: Regional classification for evaporation rates
   - Change if: Facility moves or regional zone changes

2. **Regional Rainfall (mm/month)**
   - 12 monthly values
   - Applied to all facilities with evap_active = 1
   - Year-specific or baseline

3. **Regional Evaporation (mm/month)**
   - 12 monthly values
   - Source Pan standard (Category A)
   - Applied to all facilities with evap_active = 1
   - Year-specific or baseline

---

## System Constants ✅

### Location
**Settings → Constants Tab**

### Seepage-Related Constants
```
lined_seepage_rate_pct: 0.1       # Lined dams lose 0.1% volume per month
unlined_seepage_rate_pct: 0.5     # Unlined dams lose 0.5% volume per month
```

### Ore Processing Constants
```
ore_moisture_percent: 3.4          # Water content in incoming ore
ore_density_tonnes_per_m3: 2.7    # Ore specific density
```

### Production Constants
```
default_ore_tonnes_per_month: 350000  # Default processing rate
```

### Evaporation Constants
```
evaporation_zone: 4A               # Regional classification
```

---

## Data Sources & Excel Files ✅

### Two Separate Excel Files

**1. Meter Readings Excel** (legacy_excel_path)
- Contains: Historical meter readings, flow data, production data
- Path: `data/New Water Balance 20250930 Oct.xlsx` (example)
- Sheets: Meter Readings, Production, Discharge, etc.
- Purpose: Source data for calculations

**2. Flow Diagram Excel** (timeseries_excel_path)
- Contains: Flow volumes by area
- Path: `data/Water_Balance_TimeSeries_Template.xlsx`
- Sheets: Flows_UG2N, Flows_UG2S, Flows_PLANT, etc.
- Purpose: Visual flow diagram overlay data

### Important Distinction
- **Never mix these files** - Code explicitly checks which path to use
- Meter Readings: Used by calculator for balance computations
- Flow Diagram: Used by flow diagram dashboard for visualization

---

## Pump Transfer System ✅

### How It Works
1. Facility reaches `pump_start_level` (default: 70%)
2. System transfers 5% of volume to destination facility
3. Destination specified in `feeds_to` field
4. Transfer stops when destination reaches its pump_start_level
5. Respects facility priority order

### Configuration Per Facility
**Storage Facilities → Edit Facility → Pump Settings**

```
pump_start_level:    70%   (trigger for transfer)
pump_stop_level:     20%   (trigger to stop transfer)
feeds_to:            DEST_CODE_1, DEST_CODE_2  (priority order)
active:              Yes/No (enable/disable)
```

### Example
```
Source (NDCD1): Reaches 75% level
  → Triggers pump
  → Transfers 5% to PLANT_RWD (feeds_to destination 1)
  → Continues until PLANT_RWD reaches 70% or NDCD1 reaches 20%
```

---

## Features Requiring Attention ✅

### Licensing System
- **Type:** Cloud-based via Google Sheets
- **Tiers:** Trial (1h), Standard (24h), Premium (168h) check intervals
- **Offline Grace:** 7 days (if network fails)
- **Hardware:** Tracked to prevent unauthorized transfers

### Async Startup
- **Fast Loading:** UI shows immediately while DB loads in background
- **Non-Blocking:** Calculations available as soon as DB ready
- **Check State:** `app.db_loaded` flag indicates readiness

### Caching Strategy
- **Multi-tier:** Balance results, KPI values, per-date metrics
- **Speed:** 40,000x improvement on repeated calculations
- **Auto-invalidate:** On Excel change, config update, or facility edit
- **Manual Clear:** Settings → Cache (if needed)

---

## Common Configuration Issues & Solutions ✅

### Issue: Evaporation shows as 0
**Cause:** Facility missing surface area or evap_active disabled  
**Fix:** 
1. Storage Facilities → Edit facility
2. Check evap_active checkbox is ✓
3. Verify surface_area > 0
4. Confirm rainfall/evaporation values in Environmental Parameters

### Issue: High closure error despite good data
**Cause:** Missing facility water levels or outdated measurements  
**Fix:**
1. Update all facility current_volume in Storage Facilities
2. Verify measurement dates are current (not historical)
3. Check Settings → Constants for correct seepage rates
4. Confirm Excel data loaded (check Extended Summary)

### Issue: Pump transfers not happening
**Cause:** Configuration missing or criteria not met  
**Fix:**
1. Verify pump_start_level setting (should be < current facility %)
2. Check feeds_to field populated with destination facility code
3. Confirm destination has available capacity
4. Check facility active = Yes in Storage Facilities

### Issue: Rainfall/Evaporation not applied
**Cause:** evap_active disabled or surface_area = 0  
**Fix:**
1. Storage Facilities → Edit facility
2. Enable "Include in evaporation & rainfall calculations" checkbox
3. Verify surface_area > 0
4. For tanks: set approximate surface area (Length × Width)

---

## Quick Links in Help Dashboard 🔗

### By Category

**Storage Management**
- Storage Tab → "Rainfall & Evaporation in Storage"
- Storage Tab → "Facility-Level Configuration"
- Storage Tab → "Seepage Losses"
- Storage Tab → "Operational Guidelines"

**Calculations**
- Calculations Tab → "1. Evaporation Loss"
- Calculations Tab → "4. Rainfall"
- Formulas Tab → "Evaporation Loss Formula"
- Formulas Tab → "Rainfall Formula"

**Configuration**
- Features Tab → "⚙️ Configuration & Settings"
- Features Tab → "💾 Data Management"

**Advanced Features**
- Features Tab → "🔄 Pump Transfer System"
- Features Tab → "⚡ Performance Optimization"
- Features Tab → "🔐 Licensing & Access Control"

**Troubleshooting**
- Troubleshooting Tab → "❓ Evaporation values too high/low"
- Troubleshooting Tab → "❓ Closure error >5%"
- Troubleshooting Tab → "❓ Facility water levels not updating"

---

## Validation Checklist ✅

Before running calculations, verify:

- [ ] Evaporation zone set in Settings → Environmental Parameters
- [ ] Monthly regional evaporation values entered (mm/month)
- [ ] All facilities have surface_area > 0 (if participating in rainfall/evap)
- [ ] evap_active checkbox enabled for main storage dams
- [ ] Facility water levels current (recent measurement)
- [ ] Excel files loaded with latest meter readings
- [ ] Pump settings configured (if using auto-transfer feature)
- [ ] Seepage rates appropriate for dam type (lined vs unlined)
- [ ] Constants reviewed in Settings (ore moisture, density, etc.)

---

**All Help Documentation is Current and Accurate ✅**
