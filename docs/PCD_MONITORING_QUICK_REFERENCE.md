# PCD Monitoring - Quick Reference

## At a Glance

| Feature | Details |
|---------|---------|
| **Purpose** | Upload, preview, and visualize water quality monitoring data from Pollution Control Dams |
| **Location** | Main Dashboard → "🌊 PCD Monitoring" tab |
| **Subtabs** | Upload & Preview \| Visualize |
| **Data Source** | Excel files (.xls, .xlsx) in a single folder |
| **Auto-Load** | Folder selection triggers automatic parsing and loading |
| **Supported Parameters** | Water quality: Calcium, Chloride, pH, EC, TDS, Hardness, Alkalinity, Iron, Magnesium, Sodium, etc. |

## Quick Steps

### Load PCD Data
1. Click **"Upload & Preview"** sub-tab
2. Click **"📂 Choose Folder"** → select folder with Excel files
3. App automatically scans and loads data (shows progress)
4. Preview table appears with parsed records
5. Optionally filter by Monitoring Point using dropdown

### Generate Chart
1. Click **"Visualize"** sub-tab
2. **Chart** dropdown: Select Line / Bar / Box
3. **Parameter** dropdown: Select water quality parameter
4. **Point** dropdown: Select specific dam or "All"
5. Click **"📈 Generate Charts"**
6. Chart displays with color-coded monitoring points

### Save Chart
- Click **"💾 Save Chart"** → choose PNG save location
- Default filename: `pcd_chart_YYYYMMDD_HHMMSS.png`

## Common Parameters

| Parameter | Abbreviation | Units | Use |
|-----------|--------------|-------|-----|
| Calcium | Ca | mg/L | Water hardness |
| Chloride | Cl⁻ | mg/L | Salinity, contamination |
| pH | pH | - | Acidity/alkalinity (6.5-8.5 typical) |
| Electrical Conductivity | EC | µS/cm | Total dissolved solids |
| Total Dissolved Solids | TDS | mg/L | Water purity |
| Hardness | Hard. | mg/L CaCO₃ | Scale formation risk |
| Total Alkalinity | Alk. | mg/L CaCO₃ | Buffer capacity |
| Iron | Fe | mg/L | Corrosion, discoloration |
| Magnesium | Mg | mg/L | Water hardness |
| Sodium | Na | mg/L | Salinity |
| Potassium | K | mg/L | Nutrient (minor) |
| Manganese | Mn | mg/L | Discoloration, corrosion |
| Chrome | Cr | mg/L | Toxicity (heavy metal) |
| Lead | Pb | mg/L | Toxicity (heavy metal) |
| Copper | Cu | mg/L | Toxicity (algaecide) |
| Cadmium | Cd | mg/L | Toxicity (heavy metal) |
| Fluoride | F⁻ | mg/L | Bone health (1-2 mg/L) |
| Sulphate | SO₄ | mg/L | Corrosion, tasting |
| Nitrate | NO₃ | mg/L | Contamination risk |

## Data Quality Warnings

| Warning | Meaning | Action |
|---------|---------|--------|
| ⚠️ only 1 data point | Single measurement for monitoring point | Cannot determine trends; need more data |
| ⚠️ only 2 data points | Two measurements for monitoring point | Minimal trend data; collect more |
| ℹ️ Blue explanation | Clarifies data quality meaning | Reference for interpreting warnings |

## Filters

### Upload & Preview Tab
- **Monitoring Point**: Filter preview table to single location (default: "All")
- **Effect**: Instantly hides/shows rows for selected point

### Visualize Tab
- **Chart Type**: Line (trend) | Bar (period) | Box (distribution)
- **Parameter**: Select which water quality metric to display
- **Point**: Show specific dam or all dams combined on one chart

## Chart Types

| Type | Best For | Example |
|------|----------|---------|
| **Line** | Time-series trends | pH trending upward over 12 months |
| **Bar** | Period-specific values | Chloride levels by quarter |
| **Box** | Statistical distribution | Iron concentration ranges across dams |

## File Format Requirements

✓ **Excel files** with header row containing "Date" and parameter columns  
✓ **Monitoring point names** in first column (e.g., "Main Dam", "Control Point 1")  
✓ **Date values** in common formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)  
✓ **Parameter values** as numbers (e.g., 7.2 for pH, 125 for Chloride mg/L)  

✗ **Not supported**: Complex merged cells, multiple header rows, non-date first columns

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data appears in preview | Verify folder path and check Excel files exist with proper headers |
| Chart blank | Ensure parameter selected and monitoring point has data |
| Data quality warnings | Need more measurements for affected monitoring points |
| Excel file won't parse | Check date column format and monitoring point names are valid |
| Filter doesn't update preview | Click filter dropdown again; ensure monitoring point name matches data |

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Choose Folder | Alt+C (if available) |
| Generate Charts | Alt+G (if available) |
| Save Chart | Alt+S (if available) |
| Switch Tabs | Ctrl+Page Down / Page Up |

## Performance Tips

- **First Load**: Parsing large Excel files takes 1-3 seconds (background process)
- **Subsequent Filters**: Instant (data cached in memory)
- **Large Charts**: Multi-point charts (all dams) may take 1-2 seconds to render
- **Deduplication**: Automatic if same data appears in multiple Excel files

## Example Scenarios

### Scenario 1: Monthly pH Monitoring Compliance
1. Upload monthly pH measurements for all 5 dams
2. Filter Point: "All" → shows all dams in one preview
3. Chart: Line, Parameter: pH, Point: All
4. Generate → Compare pH trends; verify within acceptable range (6.5-8.5)

### Scenario 2: Single Dam Quarterly Review
1. Upload Q1, Q2, Q3, Q4 measurements from "Primary Dam" folder
2. Filter Point: "Primary Dam" → preview shows only that dam
3. Generate multiple charts (pH, EC, Chloride, Hardness)
4. Compare parameter values quarter-to-quarter
5. Save charts for quarterly report

### Scenario 3: Heavy Metals Investigation
1. Upload recent measurements for all dams
2. Chart: Box, Parameter: Lead, Point: All
3. Identify dams with high median lead or outliers
4. Investigate contamination source

## Related Topics

- **Borehole Monitoring**: Similar upload/preview/visualize for groundwater data
- **Static Tab**: Historical dam water levels
- **Flow Diagram**: Water balance and recirculation paths
- **Database**: Store analysis results for historical comparison

---

**Print This**: Use Ctrl+P to print quick reference (fits 1 page)  
**Last Updated**: 2025-01-11

