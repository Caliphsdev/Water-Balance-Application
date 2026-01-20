"""
Help Documentation Module
Comprehensive user guide and technical documentation for the Water Balance Application

Updated: January 2026
Covers all dashboards, calculations, data sources, and features
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
import platform

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config
from ui.mouse_wheel_support import enable_canvas_mousewheel


class HelpDocumentation:
    """Help and documentation viewer with tabbed interface.

    Provides optional focusing on a given tab and section title for contextual help.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.main_frame = None
        self.notebook = None
        # Maps tab name -> list of (title, widget, canvas, scrollable_frame)
        self._sections_index = {}
        # Keep canvas references per tab for scrolling
        self._tab_canvas = {}
        
    def create_ui(self, initial_tab: str = None, initial_section: str = None):
        """Create help documentation interface.

        Args:
            initial_tab: Name of tab to select (e.g. 'Overview', 'Calculations').
            initial_section: Section title inside that tab to scroll to.
        """
        if self.main_frame:
            self.main_frame.destroy()
            
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill='both', expand=True)
        
        # Style enhancements for clearer, brighter tabs
        style = ttk.Style()
        try:
            style.theme_use(style.theme_use())  # keep current theme
        except Exception:
            pass
        style.configure('Enhanced.TNotebook', background='white')
        # Enhanced tab styling: larger padding, bolder font for better visibility and usability
        style.configure('Enhanced.TNotebook.Tab',
                        foreground=config.get_color('primary'),
                        font=config.get_font('body_bold'),
                        padding=(24, 14))  # Increased from (14, 8) for larger tab size and better UX
        # Enhanced map with better visual feedback on interaction
        style.map('Enhanced.TNotebook.Tab',
                   foreground=[('selected', 'white'), ('active', 'white')],
                   background=[('selected', config.get_color('accent')), ('active', config.get_color('accent_hover') or '#5dade2')])

        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title = tk.Label(
            header_frame,
            text="📖 Water Balance Application - User Guide & Technical Documentation",
            font=config.get_font('heading_large'),
            fg=config.get_color('primary')
        )
        title.pack(anchor='center')
        
        subtitle = tk.Label(
            header_frame,
            text="Comprehensive guide to calculations, formulas, and features",
            font=config.get_font('body'),
            fg=config.get_color('text_secondary')
        )
        subtitle.pack(anchor='center', pady=(5, 0))
        
        # Tabbed notebook for different sections
        self.notebook = ttk.Notebook(self.main_frame, style='Enhanced.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create tabs
        self._create_overview_tab()
        self._create_dashboards_tab()
        self._create_calculations_tab()
        self._create_formulas_tab()
        self._create_data_sources_tab()
        self._create_storage_tab()
        self._create_features_tab()
        self._create_troubleshooting_tab()
        
        # Focus requested tab/section
        if initial_tab:
            self.focus_tab(initial_tab, initial_section)
        
        return self.main_frame
    
    def _create_scrollable_frame(self, parent, tab_name: str):
        """Create a scrollable frame for content and register for indexing."""
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store canvas for later scrolling
        self._tab_canvas[tab_name] = (canvas, scrollable_frame)

        return scrollable_frame

    def _bind_mousewheel(self, target, canvas):
        """Enable mouse wheel scrolling for the given canvas across platforms.

        Linux uses Button-4/Button-5 events; Windows/macOS use <MouseWheel> with delta.
        We bind on enter/leave so global scrolling does not interfere with other widgets.
        """
        system = platform.system().lower()

        def _on_mousewheel(event):
            if system == 'windows' or system == 'darwin':
                # event.delta multiples of 120 (positive up, negative down)
                canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            else:
                # Should not reach here for Linux using specific buttons
                pass

        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-1, 'units')

        def _on_linux_scroll_down(event):
            canvas.yview_scroll(1, 'units')

        def _bind_active(_event=None):
            if system in ('windows', 'darwin'):
                target.bind_all('<MouseWheel>', _on_mousewheel, add='+')
            else:  # linux
                target.bind_all('<Button-4>', _on_linux_scroll_up, add='+')
                target.bind_all('<Button-5>', _on_linux_scroll_down, add='+')

        def _unbind_active(_event=None):
            if system in ('windows', 'darwin'):
                target.unbind_all('<MouseWheel>')
            else:
                target.unbind_all('<Button-4>')
                target.unbind_all('<Button-5>')

        # Activate bindings only when pointer inside the scrollable area
        target.bind('<Enter>', _bind_active)
        target.bind('<Leave>', _unbind_active)
    
    def _add_section(self, parent, title, content, level=1, tab_name: str = None):
        """Add a documentation section"""
        if level == 1:
            font = config.get_font('heading')
            color = config.get_color('primary')
        elif level == 2:
            font = config.get_font('subheading')
            color = config.get_color('accent')
        else:
            font = config.get_font('body_bold')
            color = config.get_color('text_primary')
        
        title_label = tk.Label(
            parent,
            text=title,
            font=font,
            fg=color,
            bg='white',
            anchor='w'
        )
        # Increased horizontal padding for better visual centering
        title_label.pack(fill='x', padx=60, pady=(15, 5))
        
        content_label = tk.Label(
            parent,
            text=content,
            font=config.get_font('body'),
            fg=config.get_color('text_primary'),
            bg='white',
            justify='left',
            wraplength=900,
            anchor='w'
        )
        content_label.pack(fill='x', padx=60, pady=(0, 10))
        
        # Index for contextual help scrolling
        if tab_name:
            self._sections_index.setdefault(tab_name, []).append((title, title_label))
    
    def _add_formula(self, parent, formula, description="", tab_name: str = None):
        """Add a formula box"""
        formula_frame = tk.Frame(parent, bg='#E3F2FD', relief='solid', borderwidth=1)
        formula_frame.pack(fill='x', padx=30, pady=10)
        
        formula_label = tk.Label(
            formula_frame,
            text=formula,
            font=('Courier', 11),
            fg='#0D47A1',
            bg='#E3F2FD',
            justify='left',
            anchor='w',
            padx=15,
            pady=10
        )
        formula_label.pack(fill='x')
        
        if description:
            desc_label = tk.Label(
                formula_frame,
                text=description,
                font=config.get_font('body_small'),
                fg=config.get_color('text_secondary'),
                bg='#E3F2FD',
                justify='left',
                wraplength=850,
                anchor='w',
                padx=15
            )
            # Use pack pady (geometry) not widget internal padding tuple
            desc_label.pack(fill='x', pady=(0, 10))
        
        if tab_name:
            # Index formulas by first line for potential scrolling
            first_line = formula.split('\n', 1)[0].strip()
            self._sections_index.setdefault(tab_name, []).append((first_line, formula_frame))

    def focus_tab(self, tab_name: str, section_title: str = None):
        """Select a tab and optionally scroll to a section title."""
        if not self.notebook:
            return
        # Find tab index
        for i in range(len(self.notebook.tabs())):
            tab_id = self.notebook.tabs()[i]
            text = self.notebook.tab(tab_id, 'text')
            if text.lower() == tab_name.lower():
                self.notebook.select(i)
                break
        if section_title:
            # Attempt to scroll
            indexed = self._sections_index.get(tab_name, [])
            for title, widget in indexed:
                if title.lower().startswith(section_title.lower()):
                    # Retrieve canvas
                    canvas, scrollable = self._tab_canvas.get(tab_name, (None, None))
                    if canvas and scrollable:
                        widget.update_idletasks()
                        scrollable.update_idletasks()
                        try:
                            rel_y = widget.winfo_y() / max(1, scrollable.winfo_height())
                            canvas.yview_moveto(min(max(rel_y, 0.0), 1.0))
                        except Exception:
                            pass
                    break
    
    def _create_overview_tab(self):
        """Overview and introduction"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Overview')
        
        content = self._create_scrollable_frame(tab, 'Overview')
        
        self._add_section(content, "🎯 WHAT IS THIS APPLICATION?", 
            "Water Balance Management System for Mining Operations\n\n"
            "Complete water tracking solution for calculating water inflows, outflows, and storage changes "
            "to ensure accurate water management and regulatory compliance.", level=1, tab_name='Overview')
        
        self._add_section(content, "📌 PRIMARY EQUATION", 
            "Fresh Inflows - Total Outflows - Storage Change = Closure Error\n\n"
            "✓ CLOSED: Closure Error ≤ 5% (acceptable)\n"
            "✗ OPEN: Closure Error > 5% (needs investigation)", level=1, tab_name='Overview')
        
        self._add_section(content, "🔑 CORE CONCEPTS", 
            "• Fresh Inflows: Total water entering the system from all sources\n"
            "• Total Outflows: Evaporation, discharge, and moisture in products/tailings\n"
            "• Storage Change: Volume gained/lost in dams and tanks\n"
            "• Closure Error: Accuracy measure (target: ±5%)", level=1, tab_name='Overview')
        
        self._add_section(content, "⚙️ KEY PARAMETERS & DEFAULTS", 
            "Seepage Loss: 0.5% per month (configurable)\n"
            "Closure Error Threshold: ±5% (Excel standard)\n"
            "Calculation Period: MONTHLY (all formulas calibrated for monthly base)", level=1, tab_name='Overview')
        
        self._add_section(content, "📊 WHAT YOU CAN DO", 
            "✓ Calculate complete water balance for any month\n"
            "✓ Track water from multiple sources (surface, groundwater, underground, rainfall)\n"
            "✓ Monitor storage across multiple facilities\n"
            "✓ Analyze outflow components (evaporation, discharge, moisture)\n"
            "✓ Export reports for compliance\n"
            "✓ Forecast storage capacity\n"
            "✓ Visualize water flows on interactive diagrams", level=1, tab_name='Overview')
        
        self._add_section(content, "🎛️ QUICK START", 
            "Step 1: Go to Calculations tab → Select date\n"
            "Step 2: System loads all inflows and calculates outflows automatically\n"
            "Step 3: Review results in Dashboard\n"
            "Step 4: Check Closure Error (should be ≤ 5%)\n"
            "Step 5: Analyze trends in Analytics Dashboard\n\n"
            "See Troubleshooting tab if Closure Error > 5%", level=1, tab_name='Overview')
        
        self._add_section(content, "📑 OTHER DOCUMENTATION TABS", 
            "Dashboards: Overview of all 6 visualization dashboards and their uses\n"
            "Calculations: Water balance components, data sources, and calculation logic\n"
            "Formulas: All mathematical equations with inputs, outputs, and examples\n"
            "Water Sources: Where water comes from and measurement priorities\n"
            "Storage: Facility volumes and capacity management\n"
            "Features: Application capabilities and configuration options\n"
            "Troubleshooting: Solutions for common issues and errors", level=1, tab_name='Overview')
        
        self._add_section(content, "Purpose", 
            "The water balance system helps you:\n\n"
            "• Track water from all sources (rivers, boreholes, underground sources)\n"
            "• Monitor water storage levels across multiple facilities\n"
            "• Account for environmental factors (rainfall, evaporation)\n"
            "• Ensure closure error remains within acceptable limits (±5%)\n"
            "• Generate compliance reports for regulatory authorities\n"
            "• Manage water usage efficiently", level=2)
        
        self._add_section(content, "Key Concepts", 
            "WATER BALANCE EQUATION:\n"
            "The fundamental principle is conservation of mass - water in equals water out plus storage change:\n\n"
            "Total Inflows - Total Outflows = Net Storage Change\n\n"
            "The closure error measures how well this equation balances. A small error (<5%) indicates "
            "accurate measurements and calculations.", level=2, tab_name='Overview')
        
        self._add_section(content, "Units Used", 
            "• Volume: cubic meters (m³) for most calculations\n"
            "• Large volumes: megalitres (ML) = 1,000 m³ or megacubic meters (Mm³) = 1,000,000 m³\n"
            "• Flow rates: m³/day or m³/month\n"
            "• Rainfall/Evaporation: millimeters (mm) converted to m³ using surface area\n"
            "• Plant consumption: m³/tonne of ore processed\n"
            "• Percentages: closure error, recycling ratio, utilization", level=2)
        
        self._add_section(content, "Data Quality", 
            "The system uses quality flags to indicate data reliability:\n\n"
            "• MEASURED: Direct measurements from flow meters (highest quality)\n"
            "• CALCULATED: Derived from reliable formulas (good quality)\n"
            "• ESTIMATED: Based on historical averages (use with caution)\n"
            "• ASSUMED: Default values when no data available (lowest quality)\n\n"
            "The application automatically handles missing data using historical averaging "
            "and marks calculations accordingly.", level=2, tab_name='Overview')
    
    def _create_dashboards_tab(self):
        """All available dashboards and their purposes"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Dashboards')
        
        content = self._create_scrollable_frame(tab, 'Dashboards')
        
        self._add_section(content, "Available Dashboards", 
            "The application provides 5 specialized dashboards (accessible from the left sidebar), each designed for different aspects of water management.", 
            level=1, tab_name='Dashboards')
        
        self._add_section(content, "📊 Main Dashboard", 
            "Real-time overview of water balance status and KPI metrics.\n\n"
            "Displays:\n"
            "• Water source count (active sources in database)\n"
            "• Storage facilities count (number of dams/tanks)\n"
            "• Total system capacity (Mm³)\n"
            "• Current volume across all facilities (end of month)\n"
            "• Overall utilization percentage\n"
            "• Environmental factors: Monthly rainfall, evaporation\n"
            "• Key Performance Indicators:\n"
            "  - Water sources tracked\n"
            "  - Facilities monitored\n"
            "  - System capacity utilization\n"
            "  - Latest balance check status\n"
            "• Balance check results (closure error %)\n\n"
            "⏱️ TIME PERIOD: Displays latest available month from Excel (closing volumes)", 
            level=2, tab_name='Dashboards')
        
        self._add_section(content, "📈 Analytics & Trends Dashboard", 
            "Trend analysis and historical pattern recognition.\n\n"
            "Features:\n"
            "• Load water balance data from Excel by date range\n"
            "• Auto-detect available data sources/columns\n"
            "• Create trend charts:\n"
            "  - Line charts for time series\n"
            "  - Bar charts for comparisons\n"
            "  - Scatter plots for correlations\n"
            "  - Area charts for cumulative trends\n"
            "• Analyze patterns across:\n"
            "  - Inflow trends over time\n"
            "  - Outflow patterns\n"
            "  - Storage trajectory\n"
            "• Date range selection (start/end month and year)\n"
            "• Export charts as images\n\n"
            "Use for:\n"
            "• Identifying seasonal water demand patterns\n"
            "• Visualizing historical trends\n"
            "• Understanding source contribution changes\n"
            "• Water demand forecasting", 
            level=2, tab_name='Dashboards')
        
        self._add_section(content, "🔍 Monitoring Data Dashboard", 
            "Real-time data tracking and validation for measurements.\n\n"
            "Features:\n"
            "• Load monitoring data from Excel timeseries\n"
            "• Visualize daily/monthly measurements:\n"
            "  - Borehole abstraction rates\n"
            "  - River/surface water flows\n"
            "  - Facility water levels (mm)\n"
            "• Track measurement characteristics:\n"
            "  - Measurement dates and frequency\n"
            "  - Data quality flags (MEASURED, ESTIMATED, MISSING)\n"
            "  - Data availability percentage\n"
            "• Time series visualization with:\n"
            "  - Outlier detection and highlighting\n"
            "  - Gap filling with historical averages\n"
            "  - Trend indicators\n\n"
            "Use for:\n"
            "• Day-to-day operations monitoring\n"
            "• Data validation before calculations\n"
            "• Identifying measurement anomalies\n"
            "• Quality assurance checks", 
            level=2, tab_name='Dashboards')
        
        self._add_section(content, "🌊 Flow Diagram Dashboard", 
            "Visual mapping of water flows between operational components.\n\n"
            "Features:\n"
            "• Interactive flow diagram with components from all 8 operational areas\n"
            "• Visual component positioning:\n"
            "  - Drag-and-drop to reposition\n"
            "  - Component locking to prevent accidental moves\n"
            "  - Grid alignment helpers\n"
            "• Flow line management:\n"
            "  - Draw orthogonal (right-angle) flow lines\n"
            "  - Edit existing lines\n"
            "  - Delete unwanted connections\n"
            "• Color-coded flow types:\n"
            "  - Blue: Clean water sources/flows\n"
            "  - Red: Dirty water/effluent\n"
            "  - Black: Losses/evaporation\n"
            "• Excel volume overlays:\n"
            "  - Load monthly volume data\n"
            "  - Display volumes on edges\n"
            "  - Map Excel columns to diagram flows\n"
            "  - Auto-map using column name aliases\n"
            "• Diagram management:\n"
            "  - Save to JSON format\n"
            "  - Load previously saved diagrams\n"
            "  - Clear and start fresh\n\n"
            "Use for:\n"
            "• Understanding water connectivity between components\n"
            "• Validating flow balance logic\n"
            "• Communicating water processes to stakeholders\n"
            "• Process and system documentation", 
            level=2, tab_name='Dashboards')
        
        self._add_section(content, "⚙️ Calculations Module", 
            "Water balance calculations and detailed results analysis.\n\n"
            "Functions:\n"
            "• Date selection for any month/year\n"
            "• Ore tonnage input (optional - auto-loads from Excel)\n"
            "• Calculate complete water balance on-demand\n\n"
            "Results Display:\n"
            "• Balance Check Results:\n"
            "  - Closure error % (target: ≤5%)\n"
            "  - Balance status (CLOSED or OPEN)\n"
            "  - Calculation timestamp\n"
            "• Detailed Breakdown Tabs:\n"
            "  - Summary: Key numbers at a glance\n"
            "  - Inflows: All 6 source components\n"
            "  - Outflows: All consumption and loss components\n"
            "  - Storage: Facility-level changes\n"
            "  - Area Breakdown: Per-facility analysis\n"
            "  - Balance Check Details: Step-by-step calculation walkthrough\n\n"
            "Features:\n"
            "• Manual input section for when Excel data unavailable\n"
            "• Step-by-step calculation breakdown\n"
            "• Component-level detail and sourcing\n"
            "• Real-time Excel-based calculations\n\n"
            "Use for:\n"
            "• Running monthly water balance\n"
            "• Investigating closure errors\n"
            "• Understanding calculation logic\n"
            "• Validating input data completeness", 
            level=2, tab_name='Dashboards')
    
    def _create_calculations_tab(self):
        """Main calculation process with actual implementation"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Calculations')
        
        content = self._create_scrollable_frame(tab, 'Calculations')
        
        self._add_section(content, "� WATER BALANCE CALCULATION ENGINE", 
            "INPUT (User provides):\n"
            "  • Calculation date (any date in system)\n"
            "  • Ore tonnage (from Excel or manual entry, optional)\n\n"
            "SYSTEM RETRIEVES:\n"
            "  • Water source measurements (flow meters, levels)\n"
            "  • Facility storage volumes (opening/closing)\n"
            "  • Excel monthly data (rainfall, evaporation, production, discharge)\n"
            "  • Regional climate data (rainfall mm/month, evaporation mm/month)\n\n"
            "SYSTEM CALCULATES:\n"
            "  • Total inflows (6 components)\n"
            "  • Total outflows (7 components)\n"
            "  • Storage change per facility\n"
            "  • Closure error (accuracy measure)\n\n"
            "OUTPUT (Application shows):\n"
            "  • Complete water balance breakdown by component\n"
            "  • Closure error status (CLOSED ≤5% or OPEN >5%)\n"
            "  • Inflow/outflow percentages\n"
            "  • Storage facility details\n"
            "  • KPIs (water efficiency, recycling ratio, days of supply)", level=1, tab_name='Calculations')
        
        self._add_section(content, "📊 MAIN WATER BALANCE EQUATION", 
            "The water balance equation is the foundation of all calculations:\n\n"
            "Inflows = Total Outflows + Storage Change + Closure Error\n\n"
            "All calculations are MONTHLY based but can be run for any calendar date.", level=1, tab_name='Calculations')
        
        self._add_section(content, "INFLOWS - What Water Enters the System", 
            "The system tracks water entering from multiple sources:", level=1, tab_name='Calculations')
        
        self._add_section(content, "1. Surface Water (Rivers, Streams, Dams)", 
            "Water from external surface sources measured or estimated.\n"
            "Sources: Water sources database with type 'Surface' or 'River'", level=2, tab_name='Calculations')
        
        self._add_section(content, "2. Groundwater (Boreholes, Wells)", 
            "Underground water abstraction from aquifers.\n"
            "Sources: Water sources database with type 'Borehole' or 'Groundwater'", level=2, tab_name='Calculations')
        
        self._add_section(content, "3. Underground Water (Dewatering, Mine Drainage)", 
            "Water from active mining dewatering operations.\n"
            "Sources: Water sources database with type 'Underground' or 'Dewater'", level=2, tab_name='Calculations')
        
        self._add_section(content, "4. Rainfall", 
            "Precipitation directly onto storage facility surfaces.\n"
            "Calculation: Regional monthly rainfall (mm) × Facility surface area (m²)\n"
            "Sources: Database regional_rainfall_monthly table (by month)", level=2, tab_name='Calculations')
        
        self._add_section(content, "5. Ore Moisture Water (From Wet Ore)", 
            "Water content in incoming ore (moisture locked in ore being processed).\n\n"
            "DATA PRIORITY:\n"
            "  1. Excel column: 'Tonnes Milled' (automatic monthly lookup by year+month)\n"
            "  2. Manual ore_tonnes parameter (if explicitly provided and > 0)\n"
            "  3. Zero (if no data available)\n\n"
            "CALCULATION:\n"
            "  Ore Moisture Water (m³) = (Ore Tonnes × Ore Moisture % / 100) / Ore Density\n"
            "  Default constants: Ore Moisture % = 3.4%, Ore Density = 2.7 t/m³\n\n"
            "Returns TWO values: (volume_m3, source_present_bool)\n"
            "source_present_bool is True only if Excel or explicit tonnage provided", level=2, tab_name='Calculations')
        
        self._add_formula(content,
            "Total Inflows = Surface Water + Groundwater + Underground + Rainfall + Ore Moisture\n\n"
            "All values in m³ for the monthly period.",
            "All values in m³ for the monthly period.", tab_name='Calculations')
        
        self._add_section(content, "OUTFLOWS - What Water Leaves the System", 
            "Water exiting through evaporation and discharge:", level=1, tab_name='Calculations')
        
        self._add_section(content, "1. Evaporation Loss", 
            "Water lost to atmosphere from storage facility surfaces.\n"
            "Calculation (per facility):\n"
            "  Evaporation (m³) = Evaporation Rate (mm/month) × Facility Surface Area (m²) / 1000\n"
            "  Total = Sum across all facilities with evap_active = 1\n"
            "Source: database regional_evaporation_monthly table (by month)", level=2, tab_name='Calculations')
        
        self._add_section(content, "2. Discharge (Controlled Environmental Release)", 
            "Water deliberately released to environment (compliance, management).\n"
            "Priority: Excel Discharge column → Database measurement → Manual input → Zero", level=2, tab_name='Calculations')
        
        self._add_section(content, "3. Product Moisture (Concentrate Moisture)", 
            "Water locked in concentrate product being dispatched.\n"
            "Priority: Excel PGM/Chromite wet tons + moisture % → Production sheet → Zero\n"
            "Calculation: Concentrate wet tonnes × Moisture % = Water output\n"
            "Formula: (PGM_wet × PGM_moist + CHR_wet × CHR_moist) / 100", level=2, tab_name='Calculations')
        
        self._add_section(content, "4. Tailings Retention (Water in Tailings)", 
            "Water locked in tailings solids deposited to TSF.\n\n"
            "CALCULATION (always auto-calculated from actual tonnages):\n"
            "  Tailings Dry Mass (tonnes) = Ore Tonnes - Concentrate Tonnes\n"
            "  Tailings Retention (m³) = Tailings Dry Mass × Tailings Moisture %\n\n"
            "DATA SOURCES:\n"
            "  • Ore Tonnes: Excel column 'Tonnes Milled' (monthly lookup)\n"
            "  • Concentrate: Excel columns 'PGM Concentrate Wet tons dispatched'\n"
            "               + 'Chromite Concentrate Wet tons dispatched'\n"
            "  • Tailings Moisture %: Database table tailings_moisture_monthly\n"
            "                        (by month+year) OR constant fallback\n\n"
            "PRIORITY:\n"
            "  1. Database monthly tailings_moisture_monthly (month, year)\n"
            "  2. System constant 'tailings_moisture_pct'\n"
            "  3. Zero (if no data)\n\n"
            "EXAMPLE:\n"
            "  Ore: 350,000 tonnes, Concentrate: 15,000 tonnes\n"
            "  Tailings: 335,000 tonnes × 20% moisture = 67,000 m³ retention", level=2, tab_name='Calculations')
        
        self._add_formula(content,
            "Total Outflows = Evaporation + Discharge + Product Moisture + Tailings Retention\n\n"
            "WHERE Outflows include:\n"
            "  • Evaporation from storage facilities\n"
            "  • Controlled discharge to environment\n"
            "  • Product moisture (water in concentrate)\n"
            "  • Tailings retention (water locked in tailings)\n\n"
            "NOTE: Seepage loss NOT included in total outflows (handled in storage change)",
            "All values in m³ for the monthly period.", tab_name='Calculations')
        
        self._add_section(content, "STORAGE CHANGE - Facility Volume Tracking", 
            "Each facility (dam, tank, pit) has opening and closing volumes.\n"
            "Storage Change = Closing Volume - Opening Volume\n"
            "Positive change = water added to storage\n"
            "Negative change = water drawn from storage\n\n"
            "PER-FACILITY CALCULATION:\n"
            "  • Opening volume: Volume at period start (Excel/DB)\n"
            "  • Closing volume: Volume at period end (Excel/DB)\n"
            "  • Seepage loss: AUTOMATIC calculation (facility-level only)\n"
            "    - Unlined facilities: Opening Volume × Seepage Loss Rate %\n"
            "    - Lined facilities: Zero seepage (is_lined = 1)\n"
            "    - Default rate: 0.5% per month (configurable per facility)\n"
            "  • Seepage gain: AUTOMATIC aquifer recharge (facility-level only)\n"
            "    - Gain = Opening Volume × Aquifer Gain Rate %\n"
            "    - Default: 0.0% (only for facilities with aquifer connection)\n"
            "  • Net Change = Closing - Opening\n\n"
            "IMPORTANT: Seepage is NOT a mine-level inflow/outflow.\n"
            "It is calculated automatically per facility based on lining status.\n"
            "The calculate_seepage_losses() method returns (0.0, 0.0) for mine-level\n"
            "balance for backward compatibility.", level=1, tab_name='Calculations')
        
        self._add_formula(content,
            "Net Storage Change = Σ(Closing - Opening) for all facilities\n\n"
            "Total System Storage Change includes:\n"
            "  • Opening volumes from Excel (start of month)\n"
            "  • Closing volumes from Excel (end of month)\n"
            "  • Seepage losses per facility (0.5% of volume/month default)\n"
            "  • Seepage gains from aquifer recharge",
            "Positive = capacity increased, Negative = capacity decreased", tab_name='Calculations')
        
        self._add_section(content, "CLOSURE ERROR - Balance Accuracy Check", 
            "Measures if the water balance equation balances:\n\n"
            "Ideal equation: Fresh Inflows - Total Outflows - Storage Change = 0\n"
            "In practice: Small errors from measurement uncertainty\n\n"
            "Calculation:\n"
            "  Closure Error (m³) = |Fresh In - Total Out - Storage Change|\n"
            "  Closure Error (%) = (Closure Error / Fresh Inflows) × 100\n"
            "  Balance Status: CLOSED if Error ≤ 5%, OPEN if Error > 5%", level=1, tab_name='Calculations')
        
        self._add_formula(content,
            "Closure Error % = |Fresh Inflows - Total Outflows - Storage Change| / Fresh Inflows × 100\n\n"
            "Acceptable: ≤ 5% (Excel standard, regulatory compliance)\n"
            "Flag values: CLOSED (good) or OPEN (needs investigation)",
            "Quality metric: Shows data quality and measurement accuracy. >5% indicates missing data or measurement errors.", tab_name='Calculations')
    
    def _create_formulas_tab(self):
        """All mathematical formulas used in calculations"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Formulas')
        
        content = self._create_scrollable_frame(tab, 'Formulas')
        
        self._add_section(content, "📐 FORMULA DOCUMENTATION STRUCTURE", 
            "Each formula below shows:\n\n"
            "EQUATION: Mathematical formula with variable definitions\n"
            "INPUT: What values the formula uses (data sources)\n"
            "OUTPUT: What the formula produces (result/unit)\n"
            "NOTES: Important details, defaults, or special cases\n\n"
            "All formulas are MONTHLY BASED - calculated for month periods even if run on specific dates", level=1, tab_name='Formulas')
        
        self._add_section(content, "🧮 MAIN WATER BALANCE EQUATION", 
            "The fundamental equation all other calculations support:", level=1, tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Inflows - Total Outflows - Storage Change = Closure Error\n\n"
            "REARRANGED: Inflows = Total Outflows + Storage Change + Closure Error\n\n"
            "COMPONENT DEFINITIONS:\n"
            "  Inflows = Sum of all water sources (5 types)\n"
            "  Total Outflows = Evaporation + discharge + moisture in products/tailings\n"
            "  Storage Change = Closing volume - Opening volume (all facilities)\n"
            "  Closure Error = |Inflows - Total Out - Storage Change|",
            "INPUT: Water in, total water out, facility volumes\nOUTPUT: Closure error (m³ and %)\nTARGET: Error ≤ 5%", tab_name='Formulas')
        
        self._add_section(content, "INFLOW FORMULAS (5 Water Source Types)", 
            "Calculating all water entering the system:", level=1, tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Surface Water (m³) = Σ(Flow readings for each surface source)\n\n"
            "SOURCE TYPES: 'Surface', 'River', 'Stream', 'Dam'\n"
            "DATA PRIORITY: Measured flow meter → Estimated average → Zero",
            "INPUT: Water source database, flow meter readings, Excel sheets\nOUTPUT: Surface water volume (m³)\nEXAMPLE: River inflow measured at 500 m³/day × 30 days = 15,000 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Groundwater (m³) = Σ(Borehole abstraction for each borehole)\n\n"
            "SOURCE TYPES: 'Borehole', 'Groundwater'\n"
            "CALCULATION: (Pump rate m³/day × operating days) OR direct volume measurement",
            "INPUT: Borehole database, pump flow rates, water levels\nOUTPUT: Groundwater volume (m³)\nEXAMPLE: Borehole 1 at 100 m³/day × 25 operating days = 2,500 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Underground/Dewatering (m³) = Σ(Mine dewater volumes)\n\n"
            "SOURCE TYPES: 'Underground', 'Dewater', 'Mine Drainage'\n"
            "MEASURES: Water from active mining dewatering operations",
            "INPUT: Dewatering pump rates, operating hours, mine workings\nOUTPUT: Underground water volume (m³)\nEXAMPLE: Dewater pump 80 m³/day × 30 days = 2,400 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Rainfall (m³) = (Regional Rainfall mm / 1000) × Facility Surface Area m²\n\n"
            "APPLIED TO: Each storage facility with evap_active = 1\n"
            "DATA SOURCE: Database regional_rainfall_monthly table (by calendar month)",
            "INPUT: Monthly rainfall (mm), facility surface area (m²)\nOUTPUT: Rainfall volume (m³)\nEXAMPLE: 50mm rainfall × 50,000 m² surface area = 2,500 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Ore Moisture (m³) = Ore Tonnes Milled × Ore Moisture Content %\n\n"
            "ORE TONNAGE PRIORITY:\n"
            "  1. Excel 'Tonnes Milled' column (by year+month)\n"
            "  2. Manually entered ore_tonnes parameter\n"
            "  3. Zero (if no data provided)",
            "INPUT: Ore tonnage, ore moisture %\nOUTPUT: Ore moisture water volume (m³)\nEXAMPLE: 350,000 tonnes × 2% moisture = 7,000 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Total Inflows (m³) = Surface + Groundwater + Underground + Rainfall + Ore Moisture\n\n"
            "All values are measured or estimated water entering the system from external sources.",
            "INPUT: All inflow component volumes\nOUTPUT: Total inflows (m³)\nEXAMPLE: 15,000 + 2,500 + 2,400 + 2,500 + 7,000 = 29,400 m³", tab_name='Formulas')
        
        self._add_section(content, "OUTFLOW FORMULAS (4 Water Use Types)", 
            "Calculating all water leaving the system:", level=1, tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Evaporation Loss (m³) = Σ for all facilities:\n"
            "  (Regional Evaporation Rate mm/month / 1000) × Surface Area m²\n\n"
            "APPLIED TO: Facilities with evap_active = 1\n"
            "RATE SOURCE: Database regional_evaporation_monthly (by calendar month)",
            "INPUT: Monthly evaporation rate (mm), facility surface area (m²)\nOUTPUT: Evaporation loss (m³)\nEXAMPLE: 200 mm evap × 50,000 m² = 10,000 m³ loss", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Discharge (m³) = Environmental releases\n\n"
            "DATA PRIORITY:\n"
            "  1. Excel 'Discharge' column (monthly value)\n"
            "  2. Database measurement (measurement_type='discharge')\n"
            "  3. Manual input from Settings\n"
            "  4. Zero",
            "INPUT: Compliance/management release requirements\nOUTPUT: Discharge volume (m³)\nEXAMPLE: Monthly compliance release 5,000 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Product Moisture (m³) = (PGM_wet × PGM_moist + CHR_wet × CHR_moist) / 100\n\n"
            "DATA PRIORITY:\n"
            "  1. Excel columns 'PGM Concentrate Wet tons dispatched',\n"
            "     'Chromite Concentrate Wet tons dispatched' (Meter Readings section)\n"
            "  2. Excel columns 'PGM Concentrate moisture %',\n"
            "     'Chromite Concentrate moisture %'\n"
            "  3. Zero (if no data)\n\n"
            "REPRESENTS: Water locked in concentrate product being shipped",
            "INPUT: Concentrate wet tonnage, moisture %\nOUTPUT: Water in product (m³)\nEXAMPLE: (8,000t × 10%) + (2,000t × 8%) / 100 = 960 m³", tab_name='Formulas')
        
        self._add_formula(content,
            "EQUATION: Tailings Retention (m³) = Tailings Dry Mass (tonnes) × Tailings Moisture %\n\n"
            "WHERE:\n"
            "  Tailings Dry Mass = Ore Tonnes - Concentrate Tonnes\n"
            "  Ore Tonnes = Excel 'Tonnes Milled' (monthly)\n"
            "  Concentrate = Excel 'PGM Concentrate Wet tons' + 'Chromite Concentrate Wet tons'\n\n"
            "MOISTURE PRIORITY:\n"
            "  1. Database table: tailings_moisture_monthly (by month+year)\n"
            "  2. System constant: 'tailings_moisture_pct'\n"
            "  3. Zero (if no data)\n\n"
            "REPRESENTS: Water locked in tailings solids deposited to TSF",
            "INPUT: Ore tonnes, concentrate tonnes, tailings moisture %\nOUTPUT: Water in tailings (m³)\nEXAMPLE: (350,000 - 10,000) tonnes × 20% = 68,000 m³ water in tailings", tab_name='Formulas')
        
        self._add_section(content, "STORAGE CHANGE FORMULAS", 
            "Tracking facility volume changes:", level=1, tab_name='Formulas')
        
        self._add_formula(content,
            "Storage Change per Facility (m³) = Closing Volume - Opening Volume\n\n"
            "Opening Volume: From Excel at month start\n"
            "Closing Volume: From Excel at month end",
            "Source: Facility water level measurements converted to volume", tab_name='Formulas')
        
        self._add_formula(content,
            "Net System Storage Change (m³) = Σ(Storage Change) for all facilities\n\n"
            "Includes:\n"
            "  • Opening/closing volumes from Excel\n"
            "  • Seepage loss adjustments (0.5% of volume/month default)\n"
            "  • Seepage gain from aquifer recharge",
            "Positive = capacity increase, Negative = capacity decrease", tab_name='Formulas')
        
        self._add_section(content, "CLOSURE ERROR FORMULA", 
            "Measuring water balance accuracy:", level=1, tab_name='Formulas')
        
        self._add_formula(content,
            "Closure Error (m³) = |Fresh Inflows - Total Outflows - Storage Change|\n\n"
            "Closure Error (%) = (Closure Error m³ / Fresh Inflows m³) × 100\n\n"
            "Balance Status:\n"
            "  CLOSED: ≤ 5% error (acceptable, meets Excel standard)\n"
            "  OPEN: > 5% error (requires investigation)",
            "Quality indicator: Shows measurement accuracy and data completeness", tab_name='Formulas')
        
        self._add_section(content, "SUPPORTING CALCULATION FORMULAS", 
            "Additional formulas for derived metrics:", level=1, tab_name='Formulas')
        
        self._add_formula(content,
            "Net Balance (m³) = Total Inflows - Total Outflows\n\n"
            "Operational planning metric",
            "Is the system gaining or losing water operationally?", tab_name='Formulas')
        
        self._add_formula(content,
            "Water Use Efficiency (%) = Plant Output × 100 / Net Plant Consumption\n\n"
            "Plant Output: Concentrate tonnes + tailings tonnes\n"
            "Net Plant Consumption: Water used for processing",
            "KPI: More output per water unit = better efficiency", tab_name='Formulas')
        
        self._add_formula(content,
            "Days of Operation = Current Storage Volume / Average Daily Consumption\n\n"
            "Average Daily = Monthly Net Consumption / Days in Month",
            "How many days the system can operate with current storage if no inflows occur", tab_name='Formulas')
    
    def _create_data_sources_tab(self):
        """Water source types and management"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Water Sources')
        
        content = self._create_scrollable_frame(tab, 'Water Sources')
        
        self._add_section(content, "📋 DATA SOURCES OVERVIEW", 
            "The application combines data from multiple sources:\n\n"
            "1. Excel TRP Template (Water_Balance_TimeSeries_Template.xlsx)\n"
            "2. SQLite Database (water_balance.db)\n"
            "3. Text Templates (inflow/outflow codes)\n"
            "4. User Settings (configurable parameters)\n\n"
            "Priority order is critical - Excel is checked first, then database,\n"
            "then defaults/fallbacks.", level=1, tab_name='Water Sources')
        
        self._add_section(content, "📊 EXCEL TEMPLATE COLUMNS (TRP Sheet)", 
            "The Excel template is the PRIMARY data source for monthly values.\n\n"
            "Path Configuration: Settings → timeseries_excel_path\n"
            "Default: test_templates/Water_Balance_TimeSeries_Template.xlsx\n\n"
            "CRITICAL COLUMNS (exact names):", level=1, tab_name='Water Sources')
        
        self._add_section(content, "Production Data Columns", 
            "• 'Tonnes Milled' - Ore processed (used for ore moisture, plant consumption)\n"
            "• 'PGM Concentrate Wet tons dispatched' - Platinum group metals product\n"
            "• 'Chromite Concentrate Wet tons dispatched' - Chromite product\n"
            "• 'PGM Concentrate moisture %' - Water in PGM product\n"
            "• 'Chromite Concentrate moisture %' - Water in chromite product\n\n"
            "These drive calculations for:\n"
            "  → Ore moisture water (inflow)\n"
            "  → Plant consumption estimation\n"
            "  → Product moisture (outflow)\n"
            "  → Tailings retention (ore - concentrate)", level=2, tab_name='Water Sources')
        
        self._add_section(content, "Environmental Data Columns", 
            "• 'Discharge' - Controlled environmental water release (outflow)\n"
            "• Regional rainfall (mm/month) - From regional_rainfall_monthly table\n"
            "• Regional evaporation (mm/month) - From regional_evaporation_monthly table\n\n"
            "Rainfall and evaporation are DATABASE lookups (not Excel) by month+year.", level=2, tab_name='Water Sources')
        
        self._add_section(content, "Facility Volume Columns", 
            "• Opening volumes - Start-of-month facility storage (m³)\n"
            "• Closing volumes - End-of-month facility storage (m³)\n\n"
            "Used to calculate Storage Change = Closing - Opening", level=2, tab_name='Water Sources')
        
        self._add_section(content, "🗄️ DATABASE TABLES (SQLite)", 
            "The database stores configuration, constants, and measurements.", level=1, tab_name='Water Sources')
        
        self._add_section(content, "system_constants Table", 
            "Configurable calculation parameters.\n\n"
            "Key Constants:\n"
            "• ore_moisture_percent (default: 3.4%) - Water in ore\n"
            "• ore_density (default: 2.7 t/m³) - Ore bulk density\n"
            "• tailings_moisture_pct - Water locked in tailings\n\n"
            "Accessed via: Settings → Configurable Parameters", level=2, tab_name='Water Sources')
        
        self._add_section(content, "regional_rainfall_monthly Table", 
            "Monthly rainfall (mm) by calendar month.\n\n"
            "Columns:\n"
            "• month (1-12)\n"
            "• rainfall_mm (precipitation depth)\n\n"
            "Applied to: Each facility surface area for rainfall inflow calculation", level=2, tab_name='Water Sources')
        
        self._add_section(content, "regional_evaporation_monthly Table", 
            "Monthly evaporation (mm) by calendar month.\n\n"
            "Columns:\n"
            "• month (1-12)\n"
            "• evaporation_mm (pan evaporation depth)\n\n"
            "Applied to: Each facility with evap_active = 1 for evaporation loss", level=2, tab_name='Water Sources')
        
        self._add_section(content, "🔄 DATA PRIORITY RULES", 
            "When multiple sources provide the same data, this is the priority order:", level=1, tab_name='Water Sources')
        
        self._add_formula(content,
            "ORE TONNAGE:\n"
            "  1. Excel 'Tonnes Milled' (by year+month)\n"
            "  2. Manual ore_tonnes parameter\n"
            "  3. Zero (no data)\n\n"
            "WATER SOURCES (Surface/Groundwater/Underground):\n"
            "  1. Database measurements table (by date+type)\n"
            "  2. Historical average (flagged ESTIMATED)\n"
            "  3. Zero\n\n"
            "DISCHARGE:\n"
            "  1. Excel 'Discharge' column\n"
            "  2. Database measurement (type='discharge')\n"
            "  3. Manual Settings input\n"
            "  4. Zero\n\n"
            "TAILINGS MOISTURE:\n"
            "  1. Database tailings_moisture_monthly (month+year)\n"
            "  2. System constant 'tailings_moisture_pct'\n"
            "  3. Zero",
            "Always check Excel FIRST for production/volume data!", tab_name='Water Sources')
        
        self._add_section(content, "WATER SOURCE TYPES", 
            "The application tracks multiple types of water sources, each with different "
            "characteristics and calculation methods.", level=1, tab_name='Water Sources')
        
        self._add_section(content, "Surface Water Sources", 
            "Rivers, streams, dams, and surface catchment areas.\n\n"
            "Characteristics:\n"
            "• Highly variable flow (seasonal and weather dependent)\n"
            "• Usually measured with flow meters or weirs\n"
            "• May require water use licenses\n"
            "• Quality can vary significantly", level=2, tab_name='Water Sources')
        
        self._add_formula(content,
            "Measured: Volume = Flow Meter Reading (m³)\n"
            "Unmeasured: Volume = Estimated Flow Rate × Time Period\n"
            "Missing Data: Volume = Historical Average (flagged as ESTIMATED)",
            "Priority: Install flow meters for major sources", tab_name='Water Sources')
        
        self._add_section(content, "Groundwater Sources", 
            "Boreholes, wells, and aquifer abstraction.\n\n"
            "Characteristics:\n"
            "• More stable than surface water\n"
            "• Usually metered (hours of pump operation × flow rate)\n"
            "• Requires groundwater use permit\n"
            "• Quality generally consistent", level=2, tab_name='Water Sources')
        
        self._add_formula(content,
            "Volume = Pump Hours × Pump Rate (m³/hour)\n"
            "OR Volume = Direct Flow Meter Reading",
            "Monitor sustainable yield to prevent aquifer depletion", tab_name='Water Sources')
        
        self._add_section(content, "Underground Sources", 
            "Mine dewatering, pit inflows, and underground seepage.\n\n"
            "Characteristics:\n"
            "• Increases as mining depth increases\n"
            "• Often requires continuous pumping\n"
            "• Quality may be poor (high minerals/sediment)\n"
            "• Free water source (already on site)", level=2, tab_name='Water Sources')
        
        self._add_formula(content,
            "Volume = Σ(Dewatering Pump Flow × Operating Hours)\n"
            "Quality: Track TDS, pH, suspended solids",
            "Can be significant source but quality may limit use", tab_name='Water Sources')
        
        self._add_section(content, "Rainfall", 
            "Direct precipitation captured in storage facilities.\n\n"
            "Characteristics:\n"
            "• Highly seasonal and unpredictable\n"
            "• Free water source\n"
            "• Quality excellent (low TDS)\n"
            "• Quantity depends on facility surface area", level=2, tab_name='Water Sources')
        
        self._add_formula(content,
            "Volume = Rainfall (mm) × Surface Area (m²) / 1000\n"
            "Surface Area = f(facility geometry, water level)",
            "Large dams can capture significant rainfall during wet season", tab_name='Water Sources')
        
    def _create_storage_tab(self):
        """Storage facility management"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Storage')
        
        content = self._create_scrollable_frame(tab, 'Storage')
        
        self._add_section(content, "Storage Facility Management", 
            "Dams, tanks, and ponds used to store water for operations.", level=1, tab_name='Storage')
        
        self._add_section(content, "Facility Types", 
            "Different storage facilities serve different purposes:\n\n"
            "• PROCESS WATER DAM: Primary supply for plant operations\n"
            "• RAW WATER DAM: Storage before treatment\n"
            "• EMERGENCY DAM: Backup supply for contingencies\n"
            "• POLLUTION CONTROL DAM (PCD): Capture dirty water/runoff\n"
            "• TANKS: Treated water storage, usually smaller volume\n"
            "• TSF: Tailings storage (water recovery facility)", level=2, tab_name='Storage')
        
        self._add_section(content, "Volume Calculations", 
            "Storage volume is calculated from water level using facility-specific curves.", level=2, tab_name='Storage')
        
        self._add_formula(content,
            "For dams with rating curves:\n"
            "  Volume = f(Water Level) using polynomial or lookup table\n\n"
            "For rectangular tanks:\n"
            "  Volume = Length × Width × Water Depth\n\n"
            "For cylindrical tanks:\n"
            "  Volume = π × Radius² × Water Depth",
            "Rating curves derived from topographic surveys", tab_name='Storage')
        
        self._add_section(content, "Capacity and Utilization", 
            "Track how much storage is available and being used.", level=2, tab_name='Storage')
        
        self._add_formula(content,
            "Total Capacity = Maximum safe operating volume\n"
            "Current Volume = f(measured water level)\n"
            "Available Capacity = Total - Current\n"
            "Utilization (%) = (Current / Total) × 100\n"
            "Freeboard (m) = Maximum Level - Current Level",
            "Freeboard critical for flood safety and dam stability", tab_name='Storage')
        
        self._add_section(content, "Storage Change Analysis", 
            "Understanding storage changes reveals water balance dynamics.", level=2, tab_name='Storage')
        
        self._add_formula(content,
            "For each facility:\n"
            "  Opening Volume = Volume at start of period\n"
            "  Closing Volume = Volume at end of period\n"
            "  Net Change = Closing - Opening\n\n"
            "System-wide:\n"
            "  Total Storage Change = Σ(Net Change for all facilities)\n\n"
            "Interpretation:\n"
            "  Positive Change = Water accumulating (inflows > outflows)\n"
            "  Negative Change = Water depleting (outflows > inflows)",
            "Trend analysis helps predict future storage levels", tab_name='Storage')
        
        self._add_section(content, "Operational Guidelines", 
            "Recommended storage management practices:\n\n"
            "• Maintain 40-70% utilization for operational flexibility\n"
            "• Keep minimum 90 days supply based on average consumption\n"
            "• Monitor freeboard especially during rainy season\n"
            "• Balance water levels across facilities for efficiency\n"
            "• Track evaporation losses and adjust for seasonal variation\n"
            "• Plan drawdown before wet season to maximize rainfall capture", level=2, tab_name='Storage')
    
    def _create_features_tab(self):
        """Application features and capabilities"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Features')
        
        content = self._create_scrollable_frame(tab, 'Features')
        
        self._add_section(content, "Core Features & Capabilities", 
            "Comprehensive list of all application functions and tools.", level=1, tab_name='Features')
        
        self._add_section(content, "💾 Data Management", 
            "Import, store, and organize water balance data.\n\n"
            "Capabilities:\n"
            "• Excel template import (9 template types)\n"
            "• SQLite database persistence\n"
            "• Automatic data validation\n"
            "• Historical data management\n"
            "• Data quality scoring\n"
            "• Missing data detection and flagging\n"
            "• Backup and recovery\n"
            "• Audit trail for all changes\n"
            "• Batch data import\n"
            "• Database reset/rebuild functionality", 
            level=2, tab_name='Features')
        
        self._add_section(content, "⚙️ Configuration & Settings", 
            "Customize application behavior and calculations.\n\n"
            "Adjustable Parameters:\n"
            "• Seepage loss rate (0.5% per month)\n"
            "• Closure error threshold (5%)\n"
            "• Default ore processing (default: 350,000 tonnes/month)\n\n"
            "Access: Click 'Settings' in navigation menu", 
            level=2, tab_name='Features')
        
        self._add_section(content, "🔢 Calculation Engine", 
            "Advanced water balance computation with 40,000x performance optimization.\n\n"
            "⏱️ TIME PERIOD: All formulas calibrated for MONTHLY calculations\n"
            "   Can calculate for any specific date, but underlying rates are monthly", 
            level=2, tab_name='Features')
        
        self._add_section(content, "📊 Extended Summary View", 
            "Detailed breakdown of balance components.", 
            level=2, tab_name='Features')
        
        self._add_section(content, "📁 Data Import from Excel", 
            "9 pre-formatted templates for easy data entry.", 
            level=2, tab_name='Features')
        
        self._add_section(content, "📈 Analytics & Trends", 
            "12-month moving averages, seasonal analysis, forecasting.", 
            level=2, tab_name='Features')
        
        self._add_section(content, "📄 Report Generation", 
            "Professional PDF, Excel, and CSV reports.", 
            level=2, tab_name='Features')
        
        self._add_section(content, "🔒 Data Quality & Validation", 
            "Historical averaging, quality flags, gap detection.", 
            level=2, tab_name='Features')
        
        self._add_section(content, "⚡ Performance Optimization", 
            "Memoization cache provides 40,000x speed improvement.", 
            level=2, tab_name='Features')
        
        self._add_section(content, "🛡️ Error Handling & Logging", 
            "Enterprise-grade reliability with detailed diagnostics.", 
            level=2, tab_name='Features')
    
    def _create_troubleshooting_tab(self):
        """Common issues and solutions"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Troubleshooting')
        
        content = self._create_scrollable_frame(tab, 'Troubleshooting')
        
        self._add_section(content, "Troubleshooting Guide", 
            "Solutions for common issues and error messages.", level=1, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Dashboards show '-' instead of data", 
            "Cause: Excel data not loaded\n\n"
            "Solution:\n"
            "1. Go to Flow Diagram tab\n"
            "2. Select Year and Month from dropdowns\n"
            "3. Click 'Load Excel' button\n"
            "4. Return to Dashboard to see volumes", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Closure error >5% (Balance Open)", 
            "Indicates measurement inconsistencies\n\n"
            "Investigation Steps:\n"
            "1. Check Extended Summary for detailed breakdown\n"
            "2. Verify facility water levels are current\n"
            "3. Look for '-' values (missing data)\n"
            "4. Compare with previous months\n"
            "5. Manually verify largest inflow/outflow values", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Import fails: 'File format error'", 
            "Check:\n"
            "1. File is Excel (.xlsx) or CSV\n"
            "2. First row contains column headers\n"
            "3. Dates in YYYY-MM-DD format\n"
            "4. Numbers are numeric (not text)\n"
            "5. Column names match template exactly", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Calculations are very slow", 
            "Solutions:\n"
            "1. First calculation of new date is slow (~1-3 sec) - this is normal\n"
            "2. Subsequent calculations reuse cache (40,000x faster)\n"
            "3. Very slow every time: check database size\n"
            "4. Enable 'Fast Startup' in Settings for background loading", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Flow Diagram won't save", 
            "Check:\n"
            "1. File permissions: data/diagrams/ must be writable\n"
            "2. Disk space: ensure >100MB free\n"
            "3. Solution: Click 'Save' again or restart application", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ 'No data available' on Analytics", 
            "Analytics require at least 3 months of data\n\n"
            "Solution:\n"
            "1. Import historical data using Data Import tab\n"
            "2. Use templates in 'Open Templates Folder'\n"
            "3. Once 3+ months loaded, Analytics becomes available", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Excel mapping errors in Flow Diagram", 
            "Cause: Column not found in Excel file\n\n"
            "Solutions:\n"
            "1. Click 'Validate' to find missing columns\n"
            "2. Click 'Auto-Map' to auto-fix using aliases\n"
            "3. Click 'Mappings' to manually edit column names", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ KPI values don't match Excel", 
            "Check Settings for:\n"
            "1. Default ore tonnage (default: 350,000 tonnes/month)\n"
            "2. Product moisture percentages\n"
            "3. Seepage loss rates\n\n"
            "Update if different and recalculate", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Missing data warnings on Dashboard", 
            "This is normal when:\n"
            "• Just imported data\n"
            "• Some facilities don't have measurements\n"
            "• New sources not activated yet\n\n"
            "App automatically uses historical averages to fill gaps", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "❓ Database errors", 
            "Quick Fix:\n"
            "1. Close application completely\n"
            "2. Wait 5 seconds\n"
            "3. Reopen application\n\n"
            "If Still Failing:\n"
            "1. Go to Settings\n"
            "2. Click 'Reset Database'\n"
            "3. Application will recreate database", 
            level=2, tab_name='Troubleshooting')
        
        self._add_section(content, "📞 Getting Help & Support", 
            "Resources:\n"
            "• This Help Documentation (click ? Help)\n"
            "• Check docs/ folder for detailed guides\n"
            "• Check data/logs/ for error details\n"
            "• Hover over fields for tooltips\n\n"
            "When Reporting Issues:\n"
            "• Provide error message\n"
            "• Attach relevant log file\n"
            "• State what you were doing\n"
            "• List steps to reproduce", 
            level=2, tab_name='Troubleshooting')


    

def create_help_window():
    """Create standalone help window"""
    help_window = tk.Toplevel()
    help_window.title("Water Balance Application - Help & Documentation")
    help_window.geometry("1200x800")
    
    help_doc = HelpDocumentation(help_window)
    help_doc.create_ui()
    
    return help_window
