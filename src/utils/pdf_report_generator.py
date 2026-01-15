"""
Professional PDF Report Generator for Water Balance Calculations
Uses ReportLab for high-quality PDF generation with proper formatting
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os
from pathlib import Path


class WaterBalanceReportGenerator:
    """Generate professional PDF reports for water balance calculations"""
    
    def __init__(self, company_name="Water Balance Management System", logo_path=None):
        self.company_name = company_name
        self.logo_path = logo_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderPadding=(0, 0, 5, 0),
            borderColor=colors.HexColor('#1976D2'),
            borderWidth=2
        ))
        
        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#424242'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Info text
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6,
            fontName='Helvetica'
        ))
    
    def generate_calculation_report(self, filename, calculation_data):
        """
        Generate a professional water balance calculation report
        
        Args:
            filename: Output PDF filename
            calculation_data: Dict containing:
                - month: str (e.g., "October 2025")
                - calculation_date: datetime
                - inputs: dict with calculation input parameters
                - storage_results: list of dicts with facility results
                - summary: dict with totals
                - constants: dict with system constants used
        """
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=25*mm
        )
        
        story = []
        
        # Header with logo and title
        story.extend(self._create_header(calculation_data))
        
        # Calculation info section
        story.extend(self._create_info_section(calculation_data))
        
        # Input parameters section
        story.extend(self._create_inputs_section(calculation_data))
        
        # Water balance summary with clear equation
        story.extend(self._create_water_balance_summary(calculation_data))
        
        # Inflows breakdown
        story.extend(self._create_inflows_section(calculation_data))
        
        # Outflows breakdown
        story.extend(self._create_outflows_section(calculation_data))
        
        # Storage facilities results
        story.extend(self._create_storage_results_section(calculation_data))
        
        # Storage statistics and security metrics
        story.extend(self._create_storage_statistics_section(calculation_data))
        
        # Constants used
        story.extend(self._create_constants_section(calculation_data))
        
        # Footer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        return filename
    
    def _create_header(self, data):
        """Create report header with logo and title"""
        elements = []
        
        # Logo if available
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=50*mm, height=15*mm)
                elements.append(logo)
                elements.append(Spacer(1, 10*mm))
            except Exception:
                pass
        
        # Title
        title = Paragraph("Water Balance Calculation Report", self.styles['ReportTitle'])
        elements.append(title)
        
        # Subtitle
        month_str = data.get('month', 'N/A')
        subtitle = Paragraph(f"Monthly Water Balance - {month_str}", self.styles['ReportSubtitle'])
        elements.append(subtitle)
        
        # Horizontal line
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1976D2')))
        elements.append(Spacer(1, 5*mm))
        
        return elements
    
    def _create_info_section(self, data):
        """Create calculation information section"""
        elements = []
        
        calc_date = data.get('calculation_date', datetime.now())
        generated_date = datetime.now()
        
        info_data = [
            ['Calculation Date:', calc_date.strftime('%Y-%m-%d %H:%M')],
            ['Report Generated:', generated_date.strftime('%Y-%m-%d %H:%M')],
            ['Company:', self.company_name],
            ['Month:', data.get('month', 'N/A')],
        ]
        
        info_table = Table(info_data, colWidths=[45*mm, 120*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#666666')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_inputs_section(self, data):
        """Create input parameters section"""
        elements = []
        
        header = Paragraph("Calculation Input Parameters", self.styles['SectionHeader'])
        elements.append(header)
        
        inputs = data.get('inputs', {})
        
        input_rows = [
            ['Parameter', 'Value', 'Unit']
        ]
        
        # Extract input parameters
        params = [
            ('Tonnes Milled', inputs.get('tonnes_milled', 0), 'tonnes'),
            ('Rainfall', inputs.get('rainfall', 0), 'mm'),
            ('Evaporation', inputs.get('evaporation', 0), 'mm'),
        ]
        
        for param_name, value, unit in params:
            if isinstance(value, (int, float)):
                value_str = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
            else:
                value_str = str(value)
            input_rows.append([param_name, value_str, unit])
        
        input_table = Table(input_rows, colWidths=[70*mm, 55*mm, 40*mm])
        input_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders and styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(input_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_storage_results_section(self, data):
        """Create storage facilities results section"""
        elements = []
        
        header = Paragraph("Storage Facilities Water Balance", self.styles['SectionHeader'])
        elements.append(header)
        
        storage_results = data.get('storage_results', [])
        
        if not storage_results:
            elements.append(Paragraph("No storage facility data available.", self.styles['InfoText']))
            return elements
        
        # Results table
        result_rows = [
            ['Facility', 'Opening\n(m³)', 'Inflow\n(m³)', 'Outflow\n(m³)', 'Closing\n(m³)', 'Change\n(m³)', 'Level\n(%)']
        ]
        
        for facility in storage_results:
            result_rows.append([
                facility.get('facility_code', 'N/A'),
                f"{facility.get('opening_volume', 0):,.0f}",
                f"{facility.get('inflow_total', 0):,.0f}",
                f"{facility.get('outflow_total', 0):,.0f}",
                f"{facility.get('closing_volume', 0):,.0f}",
                f"{facility.get('volume_change', 0):,.0f}",
                f"{facility.get('level_percent', 0):.1f}",
            ])
        
        result_table = Table(result_rows, colWidths=[30*mm, 22*mm, 22*mm, 22*mm, 22*mm, 22*mm, 20*mm])
        result_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders and styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(result_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_water_balance_summary(self, data):
        """Create clear water balance summary with equation"""
        elements = []
        
        header = Paragraph("Water Balance Summary", self.styles['SectionHeader'])
        elements.append(header)
        
        # Explanation box
        explanation = Paragraph(
            "<b>Water Balance Equation:</b> Fresh Water IN - Total Outflows - Net Storage Change = Closure Error<br/>",
            self.styles['InfoText']
        )
        elements.append(explanation)
        elements.append(Spacer(1, 3*mm))
        
        summary = data.get('summary', {})
        
        # Clear equation breakdown
        summary_rows = [
            ['Component', 'Volume (m³)', 'Volume (Mm³)', 'Note']
        ]
        
        fresh_inflow = summary.get('fresh_inflow', 0)
        recycled = summary.get('recycled_inflow', 0)
        total_outflow = summary.get('total_outflow', 0)
        storage_change = summary.get('net_storage_change', 0)
        closure_error = summary.get('closure_error_m3', 0)
        closure_pct = summary.get('closure_error_percent', 0)
        
        summary_rows.extend([
            ['Fresh Water Inflows', f"{fresh_inflow:,.0f}", f"{fresh_inflow/1000000:.2f}", 'New water entering system'],
            ['Recycled Water (TSF Return)', f"{recycled:,.0f}", f"{recycled/1000000:.2f}", 'Internal circulation'],
            ['', '', '', ''],  # Spacer
            ['Total Outflows', f"-{total_outflow:,.0f}", f"-{total_outflow/1000000:.2f}", 'Water leaving system'],
            ['Net Storage Change', f"-{storage_change:,.0f}", f"-{storage_change/1000000:.2f}", 'Increase in storage'],
            ['', '', '', ''],  # Spacer
            ['= Closure Error', f"{closure_error:,.0f}", f"{closure_pct:.2f}%", 'Balance accuracy'],
        ])
        
        summary_table = Table(summary_rows, colWidths=[65*mm, 40*mm, 30*mm, 50*mm])
        summary_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders and styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            # Highlight fresh water (green)
            ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#28a745')),
            # Highlight recycled (blue)
            ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor('#17a2b8')),
            # Highlight closure error (yellow background)
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF9C4')),
            ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            # Hide borders for spacer rows
            ('LINEABOVE', (0, 3), (-1, 3), 0, colors.white),
            ('LINEBELOW', (0, 3), (-1, 3), 0, colors.white),
            ('LINEABOVE', (0, 6), (-1, 6), 0, colors.white),
            ('LINEBELOW', (0, 6), (-1, 6), 0, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_inflows_section(self, data):
        """Create detailed inflows breakdown"""
        elements = []
        
        header = Paragraph("Water Inflows Breakdown", self.styles['SectionHeader'])
        elements.append(header)
        
        inflows = data.get('inflows', {})
        fresh_total = inflows.get('fresh_total', 0)
        
        # Fresh water sources
        inflow_rows = [
            ['Water Source', 'Volume (m³)', '% of Fresh', 'Category']
        ]
        
        fresh_sources = [
            ('Surface Water (Rivers/Streams)', inflows.get('surface_water', 0), 'Surface Water'),
            ('Rainfall on Facilities', inflows.get('rainfall', 0), 'Surface Water'),
            ('Underground Dewatering', inflows.get('underground', 0), 'Groundwater'),
            ('Groundwater Boreholes', inflows.get('groundwater', 0), 'Groundwater'),
            ('Ore Moisture Content', inflows.get('ore_moisture', 0), 'Process Water'),
            ('Seepage Gain', inflows.get('seepage_gain', 0), 'Process Water'),
            ('Plant Returns (misc)', inflows.get('plant_returns', 0), 'Returns'),
            ('Returns to Pit', inflows.get('returns_to_pit', 0), 'Returns'),
        ]
        
        for source, volume, category in fresh_sources:
            pct = (volume / fresh_total * 100) if fresh_total > 0 else 0
            inflow_rows.append([source, f"{volume:,.0f}", f"{pct:.1f}%", category])
        
        # Subtotal for fresh water
        inflow_rows.append(['', '', '', ''])
        inflow_rows.append(['TOTAL FRESH WATER', f"{fresh_total:,.0f}", '100.0%', 'New Water'])
        
        # Recycled water
        tsf_return = inflows.get('tsf_return', 0)
        total_inflow = inflows.get('total', 0)
        inflow_rows.append(['', '', '', ''])
        inflow_rows.append(['TSF Return (Recycled)', f"{tsf_return:,.0f}", f"{(tsf_return/total_inflow*100):.1f}%", 'Recycled'])
        inflow_rows.append(['GRAND TOTAL', f"{total_inflow:,.0f}", '—', 'All Inflows'])
        
        inflow_table = Table(inflow_rows, colWidths=[70*mm, 40*mm, 30*mm, 40*mm])
        inflow_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            # Highlight totals
            ('BACKGROUND', (0, -4), (-1, -4), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, -4), (0, -4), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#E8F5E9')),
            ('FONTNAME', (0, -2), (0, -2), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF9C4')),
            ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(inflow_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_outflows_section(self, data):
        """Create detailed outflows breakdown"""
        elements = []
        
        header = Paragraph("Water Outflows Breakdown", self.styles['SectionHeader'])
        elements.append(header)
        
        outflows = data.get('outflows', {})
        total_outflow = outflows.get('total', 0)
        
        # Outflows breakdown
        outflow_rows = [
            ['Component', 'Volume (m³)', '% of Total', 'Category']
        ]
        
        components = [
            ('Net Plant Consumption', outflows.get('plant_consumption_net', 0), 'Plant Operations'),
            ('  ├─ Tailings Retention', outflows.get('tailings_retention', 0), '  Detail'),
            ('  └─ Product Moisture', outflows.get('product_moisture', 0), '  Detail'),
            ('Dust Suppression', outflows.get('dust_suppression', 0), 'Mining Operations'),
            ('Mining Water Usage', outflows.get('mining_consumption', 0), 'Mining Operations'),
            ('Domestic Consumption', outflows.get('domestic_consumption', 0), 'Utilities'),
            ('Evaporation Losses', outflows.get('evaporation', 0), 'Environmental'),
            ('Controlled Discharge', outflows.get('discharge', 0), 'Environmental'),
        ]
        
        for component, volume, category in components:
            pct = (volume / total_outflow * 100) if total_outflow > 0 else 0
            outflow_rows.append([component, f"{volume:,.0f}", f"{pct:.1f}%", category])
        
        # Total
        outflow_rows.append(['', '', '', ''])
        outflow_rows.append(['TOTAL OUTFLOWS', f"{total_outflow:,.0f}", '100.0%', 'All Water Leaving'])
        
        # Reference info
        outflow_rows.append(['', '', '', ''])
        gross = outflows.get('plant_consumption_gross', 0)
        tsf_ret = outflows.get('tsf_return', 0)
        outflow_rows.append([f'Plant Gross: {gross:,.0f} m³', f'TSF Return: {tsf_ret:,.0f} m³', '', 'Reference'])
        
        outflow_table = Table(outflow_rows, colWidths=[70*mm, 40*mm, 30*mm, 40*mm])
        outflow_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            # Indent detail rows
            ('FONTSIZE', (0, 2), (0, 3), 8),
            ('TEXTCOLOR', (0, 2), (0, 3), colors.grey),
            # Highlight total
            ('BACKGROUND', (0, -3), (-1, -3), colors.HexColor('#FFF9C4')),
            ('FONTNAME', (0, -3), (0, -3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -3), (-1, -3), 10),
            # Reference row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTSIZE', (0, -1), (-1, -1), 8),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.grey),
            ('SPAN', (0, -1), (2, -1)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(outflow_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_constants_section(self, data):
        """Create system constants section"""
        elements = []
        
        header = Paragraph("System Constants & Coefficients", self.styles['SubsectionHeader'])
        elements.append(header)
        
        constants = data.get('constants', {})
        
        const_rows = [
            ['Constant', 'Value', 'Description']
        ]
        
        const_data = [
        ]
        
        for name, value, desc in const_data:
            const_rows.append([name, value, desc])
        
        const_table = Table(const_rows, colWidths=[60*mm, 40*mm, 65*mm])
        const_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#607D8B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders and styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(const_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _create_storage_statistics_section(self, data):
        """Create storage statistics and security metrics section"""
        elements = []
        
        header = Paragraph("Storage Statistics & Security Metrics", self.styles['SectionHeader'])
        elements.append(header)
        
        storage_stats = data.get('storage_statistics', {})
        
        # Overall storage metrics
        stats_rows = [
            ['Metric', 'Value', 'Status']
        ]
        
        total_capacity = storage_stats.get('total_capacity', 0)
        current_volume = storage_stats.get('current_volume', 0)
        available_capacity = storage_stats.get('available_capacity', 0)
        utilization = storage_stats.get('utilization_percent', 0)
        
        stats_rows.extend([
            ['Total Storage Capacity', f"{total_capacity:,.0f} m³", f"{total_capacity/1000000:.2f} Mm³"],
            ['Current Storage Volume', f"{current_volume:,.0f} m³", f"{current_volume/1000000:.2f} Mm³"],
            ['Available Capacity', f"{available_capacity:,.0f} m³", f"{available_capacity/1000000:.2f} Mm³"],
            ['Storage Utilization', f"{utilization:.1f}%", self._get_utilization_status(utilization)],
        ])
        
        stats_table = Table(stats_rows, colWidths=[70*mm, 60*mm, 50*mm])
        stats_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#607D8B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders and styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 5*mm))
        
        # Security metrics
        security_rows = [
            ['Security Metric', 'Value', 'Assessment']
        ]
        
        days_cover = storage_stats.get('days_cover', 0)
        days_to_min = storage_stats.get('days_to_minimum', 0)
        daily_consumption = storage_stats.get('daily_consumption', 0)
        security_status = storage_stats.get('security_status', 'unknown')
        
        security_rows.extend([
            ['Days of Operation Cover', f"{days_cover:.1f} days", self._get_days_cover_status(days_cover)],
            ['Days to Minimum Level', f"{days_to_min:.1f} days", self._get_days_to_min_status(days_to_min)],
            ['Daily Water Consumption', f"{daily_consumption:,.0f} m³/day", 'Reference'],
            ['Overall Security Status', security_status.upper(), self._get_security_status_description(security_status)],
        ])
        
        security_table = Table(security_rows, colWidths=[70*mm, 60*mm, 50*mm])
        security_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Borders and styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            # Highlight security status row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF9C4')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(security_table)
        elements.append(Spacer(1, 8*mm))
        
        return elements
    
    def _get_utilization_status(self, utilization):
        """Get status description for storage utilization"""
        if utilization < 30:
            return 'Low'
        elif utilization < 60:
            return 'Moderate'
        elif utilization < 80:
            return 'Good'
        elif utilization < 95:
            return 'High'
        else:
            return 'Critical'
    
    def _get_days_cover_status(self, days):
        """Get status for days of operation cover"""
        if days >= 60:
            return 'Excellent'
        elif days >= 30:
            return 'Good'
        elif days >= 14:
            return 'Adequate'
        elif days >= 7:
            return 'Low'
        else:
            return 'Critical'
    
    def _get_days_to_min_status(self, days):
        """Get status for days to minimum level"""
        if days >= 90:
            return 'Safe'
        elif days >= 60:
            return 'Adequate'
        elif days >= 30:
            return 'Monitor'
        elif days >= 14:
            return 'Concern'
        else:
            return 'Urgent'
    
    def _get_security_status_description(self, status):
        """Get description for security status"""
        status_map = {
            'excellent': 'Strong reserves',
            'good': 'Healthy levels',
            'adequate': 'Acceptable',
            'low': 'Action needed',
            'critical': 'Urgent attention',
            'unknown': 'Not assessed'
        }
        return status_map.get(status.lower(), 'Unknown')
    
    def _create_footer(self):
        """Create report footer"""
        elements = []
        
        elements.append(Spacer(1, 10*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        
        footer_text = f"Generated by {self.company_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, self.styles['InfoText'])
        elements.append(footer)
        
        disclaimer = Paragraph(
            "<i>This report is computer-generated and contains calculated water balance data. "
            "Values should be verified against source data before making operational decisions.</i>",
            self.styles['InfoText']
        )
        elements.append(disclaimer)
        
        return elements
