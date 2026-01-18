# Flow Diagram Balance Check Guide

## Overview
The Flow Diagram Balance Check is a flexible, user-controlled feature that allows you to validate water balance using actual flowlines from your diagram. Unlike the template-based system, this approach adapts automatically to component changes and gives you full control over flow categorization.

## Access
**Location:** Flow Diagram Dashboard → **⚖️ Balance Check** button (in Excel data toolbar)

## How It Works

### 1. **Open Balance Check Dialog**
- Navigate to any Flow Diagram (e.g., UG2 North, Merensky, etc.)
- Click the **⚖️ Balance Check** button in the toolbar
- A dialog window opens showing all flowlines from the current diagram

### 2. **Categorize Flowlines**
Each flowline in your diagram is displayed with:
- **Flow ID** - Unique identifier
- **From → To** - Visual representation of flow direction
- **Excel Mapping** - Column name in Excel (shows "⚠️ Not mapped" if missing)
- **Category** - Dropdown to classify the flow

**Categories:**
- **Inflow** - Water entering the system
- **Recirculation** - Internal water loops (excluded from net balance)
- **Outflow** - Water leaving the system
- **Ignore** - Exclude from calculation

### 3. **Select Period**
- **Year** - Spinbox selector (2020-2100)
- **Month** - Dropdown with month names
- Click **🔄 Recalculate** to update results

### 4. **View Results**
The balance is calculated using the formula:

```
Balance Error % = (Inflows - Recirculation - Outflows) / Inflows × 100
```

**Results Display:**
- **Period & Area** - Selected month/year and area code
- **Balance Components** - Total m³ for inflows, recirculation, outflows
- **Balance Equation** - Step-by-step calculation
- **Balance Error %** - Percentage deviation
- **Status Indicator:**
  - ✅ CLOSED (<5% error)
  - ⚠️ ACCEPTABLE (5-10% error)
  - ❌ CHECK REQUIRED (>10% error)

### 5. **Save Categorizations**
- Click **💾 Save Categories** to persist your selections
- Categorizations are saved per area in `data/balance_check_flow_categories.json`
- Next time you open the dialog, your previous selections are restored

## Key Features

### Flexible & Component-Agnostic
- No hardcoded templates - works with any flow diagram structure
- Automatically adapts when you add/rename/remove components
- No need to update configuration files when diagram changes

### Excel-Driven Data
- Uses the same Excel data source as flow diagrams
- Values extracted from mapped columns in your timeseries Excel file
- Consistent with flow diagram visualizations

### User Control
- You decide which flows are inflows, recirculation, or outflows
- Easy to experiment with different categorizations
- Visual feedback shows which flows are mapped/unmapped

### Persistent Settings
- Categorizations saved automatically per area
- JSON format for easy backup/version control
- Can be shared across team members

## Data Requirements

### Excel Mapping
Flowlines **must have Excel mappings** to be included in balance calculations:
1. Use **🔧 Excel Setup** to map flowlines to Excel columns
2. Unmapped flows show "⚠️ Not mapped" and contribute 0 m³
3. Map critical flows first (inflows/outflows) for accurate balance

### Excel File Structure
The system reads from the Excel file specified in Settings:
- **Priority:** `data_sources.timeseries_excel_path` → `data_sources.template_excel_path` → fallback
- **Sheet naming:** Match area codes (e.g., "UG2N", "MERN", etc.)
- **Column headers:** Row 3 of each sheet

## Example Workflow

1. **Open UG2 North diagram**
2. **Click ⚖️ Balance Check**
3. **Categorize major flows:**
   - `RWD → UG2N_underground`: **Inflow**
   - `UG2N_PCD → UG2N_dam`: **Recirculation**
   - `UG2N_dam → discharge`: **Outflow**
4. **Select November 2025**
5. **Click Recalculate**
6. **Review results** - if error >10%, investigate data quality
7. **Save Categories** for future use

## Troubleshooting

### "No Flowlines Found"
- Ensure you've drawn flows in the diagram
- Save the diagram before opening Balance Check

### "⚠️ Not Mapped" Shows for Flows
- Use **🔧 Excel Setup** to map flows to Excel columns
- Ensure columns exist in the Excel sheet for this area

### Balance Error Too High
- Verify Excel mappings are correct
- Check for missing/duplicate flows in categorization
- Ensure month/year has data in Excel
- Review unmapped flows (they contribute 0 m³)

### Categories Not Saving
- Check file permissions for `data/balance_check_flow_categories.json`
- Ensure `data/` folder exists and is writable

## Comparison with Old System

| Feature | Old (Template-Based) | New (Flow Diagram) |
|---------|---------------------|-------------------|
| **Data Source** | Fixed template files | User-selected flowlines |
| **Flexibility** | Breaks when components change | Adapts automatically |
| **Control** | Hardcoded categories | User categorizes each flow |
| **Visibility** | Abstract calculation | Visual flow selection |
| **Setup** | Manual template editing | Click and categorize |
| **Updates** | Requires code changes | Just update JSON |

## Files Modified
- **New Feature:** `FlowDiagramBalanceCheckDialog` class in `src/ui/flow_diagram_dashboard.py`
- **Persistence:** `data/balance_check_flow_categories.json` (auto-created)
- **Deprecated:** `_update_balance_calculation_breakdown()` in `src/ui/calculations.py`

## Technical Notes

### Calculation Engine
- Formula: `(Inflows - Recirculation - Outflows) / Inflows × 100`
- Same loader as flow diagram: `flow_volume_loader.get_flow_volume()`
- Cache cleared before each calculation for fresh data

### Category Storage Format
```json
{
  "UG2N": {
    "edge_12345": "inflow",
    "edge_67890": "recirculation",
    "edge_abcde": "outflow"
  },
  "MERN": { ... }
}
```

### Edge ID Stability
- IDs persist across sessions if diagram saved
- Renaming components doesn't affect edge IDs
- Re-categorize if edges are deleted and redrawn

## Future Enhancements
- Export balance report to PDF/Excel
- Historical trend analysis across months
- Automatic flow categorization suggestions
- Tolerance threshold customization
- Integration with PCD monitoring alerts

---

**Quick Tip:** Start by categorizing major flows (largest volumes) first. Small unmapped flows typically have minimal impact on overall balance error.
