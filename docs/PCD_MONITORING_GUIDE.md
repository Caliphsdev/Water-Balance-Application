# PCD (Pollution Control Dam) Monitoring Guide

## Overview

The PCD Monitoring tab enables you to:
- Upload Excel files containing water quality monitoring data from Pollution Control Dams
- Preview parsed data with data quality warnings
- Generate professional charts for water quality parameters
- Filter and analyze data by monitoring point and parameter

## Features

### 1. Upload & Preview Tab

#### Simple Folder Selection
- **Location**: "Upload & Preview" sub-tab
- **Process**: Click "📂 Choose Folder" to select a directory containing PCD monitoring Excel files
- **Auto-Load**: Once a folder is selected, the app automatically scans and loads all `.xls` and `.xlsx` files
- **Supported Formats**: Excel workbooks with stacked block layouts (similar to Borehole Monitoring)

#### Monitoring Point Filter
- **Default**: "All" - shows all monitoring points from parsed data
- **Usage**: Select a specific monitoring point name to filter the preview table to just that location
- **Instant Refresh**: Changing the filter immediately updates the preview

#### Data Quality Warnings
- **Orange Alerts** (⚠️): Highlight monitoring points with insufficient data
  - "only X data point" indicates fewer than 2 records
  - Insufficient for reliable trend analysis
- **Blue Explanations** (ℹ️): Clarify what each warning means
  - "Warnings show monitoring points with <2 data points (insufficient for reliable trend analysis)"

#### Preview Table
- **Responsive Layout**: Column widths adjust based on screen size
  - Laptop (<1024px): 70-90px columns
  - Desktop (1024-1440px): 80-105px columns
  - Large monitors (>1440px): 90-125px columns
- **Horizontal Scrollbar**: Scroll to view all water quality parameters
- **Color-Coded Rows**: Different monitoring points shown in alternating colors for easy identification
- **Sorting**: Data sorted by date (newest first) for quick review

### 2. Visualize Tab

#### Chart Options
- **Chart Type**: Select Line, Bar, or Box plot visualization
  - **Line**: Time series trend visualization (default)
  - **Bar**: Bar chart for period-specific values
  - **Box**: Statistical distribution (min, Q1, median, Q3, max)
- **Parameter**: Choose which water quality parameter to display
  - Common parameters: Calcium, Chloride, Alkalinity, pH, Electrical Conductivity, Iron, Magnesium, Sodium, etc.
  - List auto-populated from parsed data
- **Monitoring Point**: Filter to a specific location or view all combined
  - "All": Shows all monitoring points on same chart (color-coded)
  - Specific name: Shows only data from that monitoring point

#### Chart Generation
1. **Select Options**: Choose chart type, parameter, and monitoring point
2. **Generate Charts**: Click "📈 Generate Charts" button
3. **View Result**: Interactive matplotlib chart displays in the visualization area
4. **Save Chart**: Click "💾 Save Chart" to export as PNG

#### Chart Styling
- **Professional Standards**
  - 120 DPI resolution for clarity
  - Major grid lines (solid) and minor grid lines (dotted)
  - Color-coded monitoring points (palette of 5 colors)
  - Proper axis labels and titles
  - Legend for multiple monitoring points
- **Responsive Sizing**: Chart dimensions adapt to available space
- **Interactive**: Hover over data points for values; pan/zoom with matplotlib toolbar

## Excel File Format

### Expected Structure
The parser automatically detects and handles:

1. **Header Row**: Contains "Date" column and parameter names
   - Parameters detected by scanning for common water quality keywords
   - Header automatically identified in first 20 rows
2. **Monitoring Point Column**: First column (A) contains location/dam names
3. **Data Rows**: Each row is a date + parameter values for that monitoring point
4. **Stacked Block Layout**: Multiple measurement dates grouped per monitoring point
   - Similar format to Borehole Monitoring Excel files

### Supported Column Names
- **Location**: Monitoring Point, Dam, Site, Location
- **Date**: Date, Measurement Date, Sampling Date, Collection Date
- **Parameters**: Any water quality parameter
  - Examples: Calcium (Ca), Chloride (Cl⁻), Total Alkalinity (CaCO₃), pH, Electrical Conductivity (EC), Total Dissolved Solids (TDS), Iron (Fe), Magnesium (Mg), Sodium (Na), Potassium (K), Manganese (Mn), Chrome (Cr), Cadmium (Cd), Vanadium (V), Lead (Pb), Copper (Cu), Sulphate (SO₄), Nitrate (NO₃), Fluoride (F), Hardness, etc.

### Date Format Support
- Automatic detection of common formats
- Supported: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY, YYYY/MM/DD
- Excel numeric dates (days since 1899-12-30) automatically converted
- Dates in cells with notes like "2024-01-15 (data collected)" automatically parsed

### Missing/Invalid Values
Handled gracefully:
- Empty cells: Ignored
- "NO ACCESS" notation: Skipped
- Values with "<" (below detection limit): Skipped
- Invalid numbers: Treated as text

## Workflow Examples

### Example 1: Compare Chloride Levels Across Dams
1. Load PCD monitoring Excel files from folder
2. Preview shows all dams and recent chloride measurements
3. In Visualize tab:
   - Chart Type: Line
   - Parameter: Chloride
   - Point: All
4. Click "Generate Charts" → Displays line graph with one line per dam
5. Identify dams with highest chloride concentrations

### Example 2: Analyze Single Dam pH Trend
1. Load folder with quarterly water quality measurements
2. In Upload & Preview, filter to specific dam (e.g., "Main Dam")
3. Preview shows pH and other parameters for that dam only
4. In Visualize tab:
   - Chart Type: Line
   - Parameter: pH
   - Point: Main Dam
5. Click "Generate Charts" → Displays pH trend over time

### Example 3: Statistical Distribution of Iron Content
1. Load Excel files from folder
2. In Visualize tab:
   - Chart Type: Box
   - Parameter: Iron (Fe)
   - Point: All
3. Click "Generate Charts" → Displays box plots for each dam
4. Compare statistical distributions (median, quartiles, outliers)

## Troubleshooting

### "No .xls/.xlsx files found in directory"
- **Cause**: Selected folder has no Excel files
- **Solution**: Verify folder path and ensure Excel files are present

### "Choose a folder to auto-load and preview PCD monitoring data"
- **Cause**: No folder selected yet
- **Solution**: Click "📂 Choose Folder" to select directory with PCD monitoring files

### Chart doesn't appear after clicking "Generate Charts"
- **Cause**: 
  - No parameter selected (dropdown empty)
  - No data for selected monitoring point
  - Data parsing failed
- **Solution**:
  1. Verify folder was loaded successfully (check preview table)
  2. Select a parameter from dropdown
  3. Ensure monitoring point filter matches available data

### Data quality warnings appear
- **Meaning**: One or more monitoring points have fewer than 2 measurement dates
- **Impact**: Trend analysis unreliable for those locations
- **Solution**: Collect more measurements or remove from trend analysis

### Excel file not parsing correctly
- **Check**:
  1. File has header row with "Date" column
  2. Monitoring point names are in first column
  3. Date values are valid (not corrupted)
  4. No merge cells in critical columns
- **Note**: Complex Excel formats with merged cells may not parse correctly

### "No data matches the current filter"
- **Cause**: Selected monitoring point has no measurements for chosen parameter
- **Solution**: 
  1. Switch Point filter to "All"
  2. Select different parameter
  3. Check preview table to confirm data availability

## Performance Notes

- **Large Datasets**: Parsing hundreds of measurements across many monitoring points takes a few seconds (background thread)
- **Chart Generation**: Generating charts for all monitoring points may take 1-2 seconds
- **Memory**: Data cached after first load; switching filters is instant
- **File Scanning**: Automatically detects duplicate measurements across multiple Excel files and removes them

## Data Deduplication

If monitoring data appears in multiple Excel files (e.g., exports from different dates):
- **Detection**: Automatic by monitoring point + date combination
- **Action**: Keeps first occurrence, removes duplicates
- **Log**: Displays message if duplicates removed (e.g., "removed 5 duplicate rows")

## Best Practices

1. **Organize Files Logically**: Store all PCD monitoring data for a project/year in one folder
2. **Use Consistent Naming**: Use consistent monitoring point names across all Excel files
3. **Regular Backups**: Keep original Excel files; don't edit parsed data directly
4. **Validate Before Uploading**: Ensure Excel dates are valid before loading
5. **Filter Before Exporting**: Use monitoring point filter to focus on specific dams before saving charts
6. **Document Parameters**: Keep note of what each parameter name means (e.g., "Hardness in mg/L CaCO₃ equivalent")

## Keyboard Shortcuts

- **Folder Selection**: Alt+F (if underlined)
- **Generate Charts**: Alt+G (if underlined)
- **Save Chart**: Alt+S (if underlined)
- **Navigate Tabs**: Ctrl+Page Down / Ctrl+Page Up (between sub-tabs)

## Related Features

- **Static Tab**: View dam water levels without trends
- **Borehole Monitoring**: Similar upload/preview/visualize workflow for groundwater data
- **Flow Diagram**: See water balance for dams and control points
- **Reports**: Export analysis results to PDF/Excel

---

**Last Updated**: 2025-01-11  
**Version**: 1.0  
**Compatible With**: Python 3.14+, Tkinter, pandas, matplotlib

