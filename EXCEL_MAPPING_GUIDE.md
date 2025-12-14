# Excel Column Mapping Guide

## Where Are Excel Mappings Stored?

**File Location:** `data/diagrams/ug2_north_decline.json`

This is the **master diagram** containing all 8 mine areas and their flow connections.

## Mapping Structure

Each flow edge has an `excel_mapping` object:

```json
{
  "from": "oldtsf_old_tsf_rainrun",
  "to": "oldtsf_old_tsf",
  "segments": [...],
  "excel_mapping": {
    "enabled": true,
    "sheet": "Flows_OLDTSF",
    "column": "oldtsf_old_tsf_rainrun__TO__oldtsf_old_tsf"
  }
}
```

## Excel Sheet Names (Actual in Template)

| Area | Sheet Name | Area Code |
|------|------------|-----------|
| UG2 North Decline | `Flows_UG2N` | UG2N |
| Merensky North | `Flows_MERN` | MERN |
| Merensky South | `Flows_MERS` | MERS |
| Merensky Plant | `Flows_MERP` | MERPLANT |
| UG2 South | `Flows_UG2S` | UG2S |
| UG2 Plant | `Flows_UG2P` | UG2PLANT |
| Old TSF | `Flows_OLDTSF` | OLDTSF |
| Stockpile | `Flows_STOCKPILE` | STOCKPILE |

**Note:** Excel uses abbreviated names (`Flows_MERP`, `Flows_UG2P`) but JSON area codes use full names (MERPLANT, UG2PLANT)

## How to Edit Mappings

### Option 1: Using Python Scripts

```python
import json

# Load master diagram
with open('data/diagrams/ug2_north_decline.json', 'r') as f:
    data = json.load(f)

# Find the edge you want to update
for edge in data['edges']:
    if edge['from'] == 'your_source' and edge['to'] == 'your_destination':
        # Enable mapping
        edge['excel_mapping']['enabled'] = True
        
        # Change sheet
        edge['excel_mapping']['sheet'] = 'Flows_UG2N'
        
        # Change column
        edge['excel_mapping']['column'] = 'your_column_name'

# Save back
with open('data/diagrams/ug2_north_decline.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### Option 2: Direct JSON Edit

1. Open `data/diagrams/ug2_north_decline.json` in text editor
2. Search for the flow edge (use `from` and `to` node IDs)
3. Update the `excel_mapping` section:
   ```json
   "excel_mapping": {
     "enabled": true,
     "sheet": "Flows_OLDTSF",
     "column": "your_column_name"
   }
   ```
4. Save file

### Option 3: Using UI (Partial Support)

Currently, the Flow Diagram Dashboard **does not** have a UI for editing Excel mappings.
You must edit the JSON file directly or use Python scripts.

## Column Naming Convention

Columns follow this pattern:
```
{area}_{source_component}__TO__{area}_{destination_component}
```

Examples:
- `oldtsf_old_tsf_rainrun__TO__oldtsf_old_tsf`
- `mers_sdsa__TO__ug2s_mdcdg` (inter-area flow)
- `ug2n_ug2ncd1__TO__ug2n_ug2ncd1_sump`

## Verifying Mappings

Use the "🔍 Validate Excel Mapping" button in Flow Diagram Dashboard to check:
- Which flows have mappings enabled
- Which flows are missing mappings
- Whether columns exist in Excel

## Troubleshooting

### Flow Not Loading from Excel?

Check these in order:

1. **Is mapping enabled?**
   ```json
   "enabled": true
   ```

2. **Correct sheet name?**
   - Must match actual Excel sheet name exactly
   - Use abbreviated names: `Flows_MERP`, `Flows_UG2P`

3. **Column exists in Excel?**
   - Open Excel file: `test_templates/Water_Balance_TimeSeries_Template.xlsx`
   - Go to the sheet (e.g., `Flows_OLDTSF`)
   - Check if column name exists in row 3 (header row)

4. **Data row exists?**
   - Excel must have at least 1 data row (row 4+)
   - Month/Year must match selected date

### Inter-Area Flows

Inter-area flows (MERS→UG2S, MERPLANT→OLDTSF) load from the **source** area sheet:

```json
// MERS → UG2S flow
{
  "from": "mers_sdsa",
  "to": "ug2s_mdcdg",
  "excel_mapping": {
    "enabled": true,
    "sheet": "Flows_MERS",  // Source area (not UG2S)
    "column": "mers_sdsa__TO__ug2s_mdcdg"
  }
}
```

## Current Status (All Areas)

As of Dec 14, 2025:

✅ All 152 flow edges have correct mappings
✅ All mappings enabled
✅ All sheet names corrected to match Excel
✅ Inter-area flows point to source sheets

**Ready to use!**
