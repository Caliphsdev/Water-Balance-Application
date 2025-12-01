# PDF Export Feature - User Guide

## Overview
The Water Balance Calculations module now includes professional PDF report generation. This feature allows you to export your monthly water balance calculations into structured, professional PDF reports suitable for documentation and presentation to stakeholders.

## Features

### Professional Formatting
- **Branded Header**: Company logo and report title with month identification
- **Calculation Information**: Date, month, company details in structured table
- **Input Parameters Table**: All calculation inputs (tonnes milled, water rates, rainfall, evaporation, TSF return %)
- **Storage Facilities Results**: Detailed water balance for each facility (opening, inflow, outflow, closing, change, level %)
- **Summary Totals**: Comprehensive totals including closure error metrics
- **System Constants**: Reference section showing all constants and coefficients used
- **Professional Footer**: Generation timestamp and disclaimer

### Report Structure
1. **Header Section**
   - Logo (if available in `assets/icons/`)
   - Report title: "Water Balance Calculation Report"
   - Subtitle with month and year
   
2. **Calculation Info**
   - Calculation date and time
   - Report generation date
   - Company name
   - Reporting month
   
3. **Input Parameters**
   - Tonnes Milled
   - Mining Water Rate (m³/tonne)
   - Rainfall (mm)
   - Evaporation (mm)
   - TSF Return Percentage (%)
   
4. **Storage Facilities Water Balance**
   - Per-facility breakdown showing:
     - Opening volume (m³)
     - Total inflow (m³)
     - Total outflow (m³)
     - Closing volume (m³)
     - Volume change (m³)
     - Level percentage (%)
   
5. **Summary Totals**
   - Total opening volume
   - Total inflow
   - Total outflow
   - Total closing volume
   - Net change
   - **Closure error (m³ and %)**
   
6. **System Constants & Coefficients**
   - Mining water rate
   - TSF return rate
   - Mean annual evaporation
   - Rainfall factor

## How to Use

### Step 1: Calculate Water Balance
1. Open the **Calculations** tab
2. Select the month and year
3. Enter ore processed (or use auto-filled value from Excel)
4. Click **🔢 Calculate Balance**
5. Review the results in all tabs

### Step 2: Export to PDF
1. Click the **💾 Save Calculation** button
2. In the dialog, select one of three options:
   - **📊 Save to Database Only**: Store in database for tracking
   - **📄 Export to PDF Only**: Generate PDF report without database save
   - **💾 Both (Database + PDF)**: Save to database AND export PDF (recommended)
3. Click **✅ Save**
4. If PDF export was selected:
   - A file save dialog will appear
   - Default filename: `Water_Balance_YYYYMM.pdf`
   - Choose location and click Save
5. Success message will show:
   - Database save confirmation (if selected)
   - PDF export path (if selected)

### Step 3: Review PDF
Open the generated PDF to see:
- Professional formatted report
- All calculation inputs and results
- Structured tables with proper alignment
- Color-coded sections for easy navigation
- Generation timestamp and metadata

## PDF Technical Details

### Styling
- **Title**: 24pt Helvetica Bold, Blue (#1976D2)
- **Section Headers**: 16pt Helvetica Bold, Blue with underline
- **Tables**: Alternating row colors (white/#F5F5F5)
- **Headers**: Colored backgrounds (Blue, Green, Grey) with white text
- **Numbers**: Right-aligned with thousand separators
- **Text**: Left-aligned, 10-11pt Helvetica

### Page Layout
- **Size**: A4 (210mm × 297mm)
- **Margins**: 20mm (left/right), 25mm (top/bottom)
- **Orientation**: Portrait
- **Tables**: Responsive column widths based on content

### Unicode Support
The PDF generator fully supports Unicode characters:
- International text
- Special symbols (m³, °C, %, etc.)
- Greek letters (if needed for formulas)
- Mathematical operators

## File Location Recommendations

### Suggested Folder Structure
```
/reports/
  /water_balance/
    /2025/
      Water_Balance_202501.pdf
      Water_Balance_202502.pdf
      Water_Balance_202503.pdf
    /2024/
      Water_Balance_202412.pdf
      ...
```

### Default Filename Format
`Water_Balance_YYYYMM.pdf`
- Example: `Water_Balance_202510.pdf` (October 2025)

## Troubleshooting

### Missing Logo
- If no logo appears, place a logo file in `assets/icons/`
- Supported formats: `.png`, `.jpg`, `.jpeg`
- Filename: `logo.png`, `logo.jpg`, or `logo.jpeg`
- Recommended size: 50mm × 15mm (approx 189px × 57px at 96 DPI)

### PDF Generation Fails
- Check that `reportlab` is installed: `pip install reportlab`
- Ensure write permissions to target folder
- Verify calculation was run successfully before saving
- Check logs in `logs/water_balance.log` for errors

### Data Source Differences
- PDF uses the same data as displayed in UI
- Excel data (📊) prioritized over Database (💾) when available
- Opening volumes shown are start-of-month balances

### Large Reports
- Reports typically 3-5 pages for standard facilities
- PDF file size: 50-200 KB
- Generation time: < 1 second for typical report

## Best Practices

### Recommended Workflow
1. **Monthly Routine**:
   - Run calculation for current month
   - Review all tabs (Summary, Inflows, Outflows, Storage)
   - Verify closure error is within threshold (< 5%)
   - Export to PDF AND save to database
   - Store PDF in organized folder structure

2. **Quality Checks**:
   - Compare PDF inputs with source data
   - Verify closure error explanation
   - Check facility volumes against physical measurements
   - Review summary totals for reasonableness

3. **Documentation**:
   - Export PDF at end of each month
   - Include in monthly reports package
   - Archive for regulatory compliance
   - Share with stakeholders as needed

### Report Distribution
- **Internal**: Database records for analysis and trending
- **External**: PDF reports for presentations and documentation
- **Regulatory**: Both database and PDF for audit trail
- **Management**: PDF summary for monthly reviews

## Advanced: Customization

### Modify Company Name
Edit `src/ui/calculations.py`, line ~528:
```python
generator = WaterBalanceReportGenerator(
    company_name="Your Company Name Here",
    logo_path=logo_path
)
```

### Change Colors
Edit `src/utils/pdf_report_generator.py`:
- Title color: `textColor=colors.HexColor('#1976D2')`
- Table headers: `BACKGROUND` in TableStyle
- Section headers: `textColor=colors.HexColor('#1976D2')`

### Add Custom Sections
Edit `generate_calculation_report()` method:
```python
# Add your custom section
story.extend(self._create_custom_section(calculation_data))
```

Then implement `_create_custom_section()` method following existing patterns.

## Dependencies
- **reportlab**: PDF generation library (automatically installed)
- **Python 3.8+**: Required for f-strings and type hints
- **PIL/Pillow**: Optional, for image processing (already in environment)

## Compliance Notes
- **Timestamp**: Every PDF includes generation timestamp
- **Disclaimer**: Footer states report is computer-generated
- **Verification Note**: Recommends verifying against source data
- **Audit Trail**: Use "Both" option to maintain database record + PDF

## Performance
- **Generation Time**: < 1 second typical
- **File Size**: 50-200 KB per report
- **Memory**: Minimal (<10 MB during generation)
- **Concurrent**: Safe to generate multiple PDFs simultaneously

## Version History
- **v1.0** (Current): Initial PDF export with professional formatting
  - Input parameters table
  - Storage facilities results
  - Summary totals with closure error
  - System constants reference
  - Professional styling and layout
  - Unicode support
  - Logo integration
  - Structured sections with color-coding
