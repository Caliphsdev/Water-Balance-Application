# Flow Types Legend and Excel Mapping

This legend standardizes flow types, colors, and Excel naming so users understand where each flow comes from and how it maps to monthly data.

## Categories and Colors
- Clean water: Blue (#3498db)
- Evaporation/Losses: Black (#000000)
- Dirty water (and variants): Red (#e74c3c)
 - Recirculation: Purple (#9b59b6) — unchanged behavior

### Dirty Variants
- effluent, runoff, ug_return, dewatering, outflow, inflow, drainage, return, irrigation

All variants render red by default. You can override colors per line in the editor if needed.

## Editing Flow Lines
- Use the Flow Diagram "Edit Line" dialog to set `flow_type`.
- If you leave color empty, the system applies the default based on type.
- Volume/label accepts numbers (m³) or text like "N/A".

## Excel Mapping (User-Friendly Names)
To load volumes from Excel per month, each edge can include:

```json
{
  "excel_mapping": {
    "enabled": true,
    "sheet": "Flows_UG2N",
    "column": "OFFICES"
  }
}
```

Guidelines:
- `sheet`: A user-recognizable area sheet (e.g., Flows_UG2N, Flows_MERPLANT).
- `column`: A friendly column name matching the Excel header exactly.
- Recommended column naming examples: `BOREHOLE_ABSTRACTION`, `OFFICES`, `ACCOMMODATION`, `NDCD1_INFLOW`, `SEEPAGE_LOSS`, `IRRIGATION`.

## Tips
- Keep column names concise and readable; use underscores for multi-word names.
- For evaporation/losses, consider columns like `EVAPORATION`, `SEEPAGE_LOSS`, `SPILLAGE_LOSS`.
- For dirty flows, use specific names: `EFFLUENT_STP`, `RUNOFF_STOCKPILE`, `UG_RETURN_NORTH`.

## Troubleshooting
- If a line doesn't update from Excel, verify `sheet` and `column` match the workbook.
- Missing months return 0 and log a warning.

