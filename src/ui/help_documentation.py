"""
Help Documentation Module
Comprehensive user guide and technical documentation for the Water Balance Application
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
import platform

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config_manager import config


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
        style.configure('Enhanced.TNotebook.Tab',
                        foreground=config.get_color('primary'),
                        font=config.get_font('body_bold'),
                        padding=(14, 8))
        style.map('Enhanced.TNotebook.Tab',
                   foreground=[('selected', config.get_color('accent')), ('active', config.get_color('accent'))],
                   background=[('selected', '#F0F4FF'), ('active', '#F8FAFF')])

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
        self._create_calculations_tab()
        self._create_formulas_tab()
        self._create_data_sources_tab()
        self._create_storage_tab()
        self._create_features_tab()
        
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
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store canvas for later scrolling
        self._tab_canvas[tab_name] = (canvas, scrollable_frame)

        # Bind mouse wheel scrolling (platform-specific)
        self._bind_mousewheel(scrollable_frame, canvas)
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
        
        self._add_section(content, "Water Balance Application", 
            "This application performs comprehensive water balance calculations for mining operations, "
            "tracking all water inflows, outflows, and storage changes to ensure accurate water management "
            "and regulatory compliance.", level=1, tab_name='Overview')
        
        self._add_section(content, "Purpose", 
            "The water balance system helps you:\n\n"
            "• Track water from all sources (rivers, boreholes, underground sources)\n"
            "• Monitor water storage levels across multiple facilities\n"
            "• Calculate plant water consumption and TSF (Tailings Storage Facility) return water\n"
            "• Account for environmental factors (rainfall, evaporation)\n"
            "• Ensure closure error remains within acceptable limits (±5%)\n"
            "• Generate compliance reports for regulatory authorities\n"
            "• Optimize water usage and recycling efficiency", level=2)
        
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
    
    def _create_calculations_tab(self):
        """Main calculation process"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Calculations')
        
        content = self._create_scrollable_frame(tab, 'Calculations')
        
        self._add_section(content, "⏱️ CALCULATION PERIOD: MONTHLY", 
            "All water balance calculations are designed for MONTHLY periods:\n\n"
            "• Default ore processing: 350,000 tonnes/month\n"
            "• Evaporation rates: stored as mm/month, converted to daily\n"
            "• Historical averaging: 12-month rolling window\n"
            "• Seepage calculations: 0.5% of volume per month\n"
            "• TSF return and consumption rates: monthly basis\n\n"
            "While you can calculate for any specific date, the underlying formulas "
            "and constants are calibrated for monthly water balance periods, which is "
            "standard practice for mine water management.", level=1, tab_name='Calculations')
        
        self._add_section(content, "Water Balance Calculation Process", 
            "The application performs a complete water balance calculation for any date, "
            "following these steps:", level=1, tab_name='Calculations')
        
        self._add_section(content, "Step 1: Calculate Total Inflows", 
            "All water entering the system is summed:\n\n"
            "1. SURFACE WATER: From rivers, streams, and catchment areas\n"
            "2. GROUNDWATER: From boreholes and wells\n"
            "3. UNDERGROUND WATER: From dewatering and mine drainage\n"
            "4. RAINFALL: Direct precipitation on storage facilities\n"
            "5. TSF RETURN WATER: Water recovered from tailings (counted as inflow)\n\n"
            "Each source is queried from measurements or calculated from average flow rates.", level=2, tab_name='Calculations')
        
        self._add_formula(content,
            "Total Inflows = Surface Water + Groundwater + Underground Water + Rainfall + TSF Return",
            "All values in m³ for the calculation period", tab_name='Calculations')
        
        self._add_section(content, "Step 2: Calculate Total Outflows", 
            "All water leaving or consumed in the system:\n\n"
            "1. PLANT CONSUMPTION (Gross): Water used in ore processing\n"
            "2. TSF RETURN: Portion of plant water that returns from tailings\n"
            "3. NET PLANT CONSUMPTION: Actual water consumed (Gross - Return)\n"
            "4. EVAPORATION: Water lost to atmosphere from storage surfaces\n"
            "5. DISCHARGE: Controlled releases to environment\n"
            "6. OTHER LOSSES: Seepage, dust suppression, etc.", level=2)
        
        self._add_formula(content,
            "Plant Consumption (Gross) = Ore Tonnes × Mining Water Rate\n"
            "TSF Return = Plant Consumption × TSF Return Rate\n"
            "Net Plant Consumption = Plant Consumption - TSF Return\n"
            "Total Outflows = Net Plant Consumption + Evaporation + Discharge + Other",
            "Mining Water Rate default: 1.43 m³/tonne, TSF Return Rate configurable (stored as percentage)", tab_name='Calculations')
        
        self._add_section(content, "Step 3: Calculate Storage Changes", 
            "For each storage facility (dam, tank), track:\n\n"
            "• Opening volume (start of period)\n"
            "• Closing volume (end of period)\n"
            "• Net change = Closing - Opening\n"
            "• Total system storage change = Sum of all facility changes", level=2)
        
        self._add_formula(content,
            "Net Storage Change = Σ(Closing Volume - Opening Volume) for all facilities",
            "Positive = water added to storage, Negative = water drawn from storage", tab_name='Calculations')
        
        self._add_section(content, "Step 4: Calculate Closure Error", 
            "The closure error measures the water balance accuracy:\n\n"
            "Ideally: Inflows - Outflows = Storage Change\n"
            "In practice: Small errors occur due to measurement uncertainty", level=2)
        
        self._add_formula(content,
            "Closure Error (m³) = Inflows - Outflows - Storage Change\n"
            "Closure Error (%) = (Closure Error / Inflows) × 100\n\n"
            "Acceptable Range: ±5% (Excel parity standard)",
            "Errors outside ±5% indicate measurement issues or missing data", tab_name='Calculations')
        
        self._add_section(content, "Step 5: Generate Results", 
            "The final water balance includes:\n\n"
            "• Detailed breakdown of all inflow components\n"
            "• Detailed breakdown of all outflow components\n"
            "• Net balance (Inflows - Outflows)\n"
            "• Storage change for each facility\n"
            "• Closure error (absolute and percentage)\n"
            "• Balance status: CLOSED (<5% error) or OPEN (≥5% error)\n"
            "• Quality flags for all measurements", level=2, tab_name='Calculations')
    
    def _create_formulas_tab(self):
        """Detailed formulas and calculations"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Formulas')
        
        content = self._create_scrollable_frame(tab, 'Formulas')
        
        self._add_section(content, "Core Calculation Formulas", 
            "Detailed mathematical formulas used throughout the application.", level=1, tab_name='Formulas')
        
        self._add_section(content, "Plant Water Consumption", 
            "Water required for ore processing operations.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "Plant Makeup Water (m³) = Monthly Ore Tonnes × Mining Water Rate (m³/tonne)",
            "Mining Water Rate is configurable, default = 1.43 m³/tonne. Adjust in Settings based on your plant's actual water consumption.", tab_name='Formulas')
        
        self._add_section(content, "TSF Return Water", 
            "Water recovered from the Tailings Storage Facility and recycled back to the plant.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "TSF Return (m³) = Plant Consumption × (TSF Return Rate / 100)\n"
            "Net Plant Consumption = Plant Consumption - TSF Return",
            "TSF Return Rate is configurable in Settings, stored as percentage. Typical range: 50-60% for mining operations.", tab_name='Formulas')
        
        self._add_section(content, "Evaporation Loss", 
            "Water lost to the atmosphere from open storage surfaces.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "Evaporation (m³) = (Evaporation Rate mm / 1000) × Surface Area m²\n"
            "Monthly Evaporation = Daily Rate × Days in Month",
            "Evaporation rates from S-pan measurements, Zone 4A climate classification\n"
            "Surface area dynamically calculated from facility water levels", tab_name='Formulas')
        
        self._add_section(content, "Rainfall Contribution", 
            "Direct precipitation captured in storage facilities.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "Rainfall Volume (m³) = (Rainfall mm / 1000) × Surface Area m²",
            "Rainfall data from on-site weather station or regional measurements", tab_name='Formulas')
        
        self._add_section(content, "Surface Water Flow", 
            "Water from rivers, streams, and surface catchments.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "For measured sources:\n"
            "  Volume = Measured Flow (m³) from flow meters\n\n"
            "For unmeasured sources:\n"
            "  Volume = Average Flow Rate (m³/day) × Days in Period\n\n"
            "If no data available:\n"
            "  Volume = Historical Average for same period (quality flag: ESTIMATED)",
            "Historical averaging uses 12-month rolling window of available data", tab_name='Formulas')
        
        self._add_section(content, "Storage Facility Calculations", 
            "Volume, capacity, and utilization for dams and tanks.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "Current Volume (m³) = f(Water Level, Facility Geometry)\n"
            "Available Capacity (m³) = Total Capacity - Current Volume\n"
            "Utilization (%) = (Current Volume / Total Capacity) × 100\n"
            "Freeboard (m) = Maximum Level - Current Level",
            "Volume-level relationships defined by facility-specific rating curves", tab_name='Formulas')
        
        self._add_section(content, "Closure Error Calculation", 
            "Measures the accuracy of the water balance.", level=2, tab_name='Formulas')
        
        self._add_formula(content,
            "Closure Error Absolute = |Inflows - Outflows - Storage Change|\n"
            "Closure Error Percentage = (Closure Error / Inflows) × 100\n\n"
            "Balance Status:\n"
            "  CLOSED: Error ≤ 5% (acceptable)\n"
            "  OPEN: Error > 5% (requires investigation)",
            "Target: ±5% or better for regulatory compliance", tab_name='Formulas')
    
    def _create_data_sources_tab(self):
        """Water source types and management"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='Water Sources')
        
        content = self._create_scrollable_frame(tab, 'Water Sources')
        
        self._add_section(content, "Water Source Types", 
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
        
        self._add_section(content, "TSF Return Water", 
            "Water recovered from the Tailings Storage Facility.\n\n"
            "Characteristics:\n"
            "• Most sustainable source (recycled)\n"
            "• Reduces freshwater demand\n"
            "• Quality suitable for plant use\n"
            "• Volume depends on tailings density and settling", level=2, tab_name='Water Sources')
        
        self._add_formula(content,
            "TSF Return = Plant Consumption × (TSF Return Rate / 100)\n"
            "Typical Return Rate: 50-60% of gross plant water (stored as percentage in Settings)",
            "Optimizing TSF return is key to water sustainability", tab_name='Water Sources')
    
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
        
        self._add_section(content, "Application Features", 
            "Overview of key capabilities and how to use them.", level=1, tab_name='Features')
        
        self._add_section(content, "Dashboard", 
            "Real-time overview of water balance status.\n\n"
            "Displays:\n"
            "• Current storage levels across all facilities\n"
            "• Active water sources and volumes\n"
            "• Recent calculations and trends\n"
            "• Quick-access KPI cards", level=2, tab_name='Features')
        
        self._add_section(content, "KPI Dashboard", 
            "Performance monitoring with Excel parity.\n\n"
            "Features:\n"
            "• Water use efficiency metrics\n"
            "• Recycling ratio tracking\n"
            "• Source dependency breakdown\n"
            "• Storage security indicators\n"
            "• Compliance status checks\n"
            "• Date selection for historical analysis\n"
            "• Visual indicators (color-coded performance)", level=2, tab_name='Features')
        
        self._add_section(content, "Data Quality Management", 
            "Ensures reliable calculations through data validation.\n\n"
            "Capabilities:\n"
            "• Historical averaging for missing data\n"
            "• Quality flags (MEASURED, CALCULATED, ESTIMATED, ASSUMED)\n"
            "• Gap detection and filling algorithms\n"
            "• Outlier identification\n"
            "• Data completeness scoring\n"
            "• Audit trail for all estimates", level=2, tab_name='Features')
        
        self._add_section(content, "Extended Summary", 
            "Detailed breakdown of water balance components.\n\n"
            "Shows:\n"
            "• Complete inflow breakdown by source\n"
            "• Complete outflow breakdown by category\n"
            "• Storage change for each facility\n"
            "• Closure error analysis\n"
            "• Data quality indicators for each value\n"
            "• Supporting calculations and assumptions", level=2, tab_name='Features')
        
        self._add_section(content, "Calculations Module", 
            "Run water balance calculations for any date.\n\n"
            "⏱️ TIME PERIOD: All calculations are designed for MONTHLY periods\n\n"
            "Options:\n"
            "• Single date calculation\n"
            "• Date range calculations\n"
            "• Custom ore tonnage override (default: 350,000 tonnes/month)\n"
            "• Batch processing for multiple dates\n"
            "• Save results to database\n"
            "• Export to Excel/PDF", level=2, tab_name='Features')
        
        self._add_section(content, "Data Import", 
            "Import water balance data from Excel files.\n\n"
            "📁 TEMPLATES AVAILABLE: Click '📁 Open Templates Folder' button to access "
            "pre-formatted Excel templates.\n\n"
            "Templates include:\n"
            "• Borehole Abstraction (monthly flow rates in m³/month)\n"
            "• River Abstraction (monthly flow rates in m³/month)\n"
            "• Facility Levels (storage levels)\n"
            "• Rainfall (monthly mm)\n"
            "• Evaporation (monthly mm)\n"
            "• Plant Consumption (monthly volumes)\n"
            "• Discharge (monthly volumes)\n"
            "• Water Sources (source definitions)\n"
            "• Storage Facilities (facility definitions)\n\n"
            "⏱️ TIME PERIOD: All measurement templates are designed for MONTHLY data\n\n"
            "Import Process:\n"
            "1. Click '📁 Open Templates Folder' to get templates\n"
            "2. Fill template with your data in Excel/LibreOffice\n"
            "3. Select import type matching your template\n"
            "4. Browse to select your filled Excel file\n"
            "5. Click 'Preview Data' to validate structure\n"
            "6. Review data and click 'Import Data' to add to database\n\n"
            "File Requirements:\n"
            "• First row contains column headers\n"
            "• Column names match template fields\n"
            "• Dates in YYYY-MM-DD format\n"
            "• Required columns have values\n"
            "• One row per location per month for measurements", level=2, tab_name='Features')
        
        self._add_section(content, "Reports Generator", 
            "Professional reports for stakeholders and regulators.\n\n"
            "Report Types:\n"
            "• Monthly water balance report\n"
            "• Annual compliance report\n"
            "• Source performance report\n"
            "• Storage capacity report\n"
            "• KPI trends report\n\n"
            "Formats:\n"
            "• PDF with charts and tables\n"
            "• Excel workbook with raw data\n"
            "• CSV for data analysis", level=2, tab_name='Features')
        
        self._add_section(content, "Performance Optimization", 
            "Smart caching for fast calculations.\n\n"
            "Technology:\n"
            "• Memoization: 40,000x faster repeated calculations\n"
            "• Database caching: Reduced query overhead\n"
            "• Single-pass KPI calculations\n"
            "• Automatic cache invalidation when data changes\n\n"
            "Result:\n"
            "• Instant dashboard updates\n"
            "• Real-time KPI refresh\n"
            "• Responsive user interface", level=2, tab_name='Features')
        
        self._add_section(content, "Error Handling & Logging", 
            "Enterprise-grade reliability and diagnostics.\n\n"
            "Features:\n"
            "• User-friendly error messages\n"
            "• Detailed technical logs for debugging\n"
            "• Performance timing on all operations\n"
            "• Automatic error classification\n"
            "• Notification history tracking\n"
            "• Rotating log files (prevents disk filling)", level=2, tab_name='Features')
    

def create_help_window():
    """Create standalone help window"""
    help_window = tk.Toplevel()
    help_window.title("Water Balance Application - Help & Documentation")
    help_window.geometry("1200x800")
    
    help_doc = HelpDocumentation(help_window)
    help_doc.create_ui()
    
    return help_window
