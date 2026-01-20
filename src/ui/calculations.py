"""
Calculations Module
Water balance calculations and projections interface

DATA SOURCES:
- Meter Readings Excel (legacy_excel_path): "Meter Readings" sheet with tonnes milled, RWD, dewatering volumes
  → Used by this module for water balance calculations
- Flow Diagram Excel (timeseries_excel_path): "Flows_*" sheets with flow volumes
  → Used by Flow Diagram module, NOT by this Calculations module
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
from typing import Optional, Any, Dict, List
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.water_balance_calculator import WaterBalanceCalculator
from utils.excel_timeseries import get_default_excel_repo
from utils.app_logger import logger
from utils.config_manager import config
from utils.template_data_parser import get_template_parser
from utils.balance_check_engine import get_balance_check_engine
from utils.balance_engine import BalanceEngine
from utils.balance_services_legacy import LegacyBalanceServices
from utils.inputs_audit import collect_inputs_audit
from ui.mouse_wheel_support import enable_canvas_mousewheel, enable_text_mousewheel


class CalculationsModule:
    """Water balance calculations interface"""

    # Tooltip definitions for balance metrics
    BALANCE_TOOLTIPS = {
        'Fresh Inflows': 'Natural water entering the system: surface water, groundwater, rainfall, underground, ore moisture',
        'Dirty Inflows': 'Recycled/recirculated water: Return Water Dam (RWD) from treatment plants and processes',
        'Total Outflows': 'All water leaving the system: mining/domestic consumption, discharge, dust suppression, tailings, product moisture',
        'Total Inflows': 'Fresh + recycled inflows combined; represents total water available in the system',
        'ΔStorage': 'Change in storage volume: Positive = storage increased (filled). Negative = storage decreased (drew down)',
        'Balance Error': 'Residual difference in the water balance equation (fresh inflows − outflows − ΔStorage). Should be ≤5% for acceptable closure. Check for measurement errors if >5%',
        'Error %': 'Error percentage = (Balance Error ÷ Fresh Inflows) × 100. Fresh inflows exclude recycled/TSF returns. <5% = Good. 5-10% = Acceptable. >10% = Investigate data quality',
        'Status': 'Closure status: GREEN = Balanced (<5% error). RED = Check Required (>5% error). Verify inflow/outflow measurements',
        'Opening Volume': 'Storage volume at the beginning of the period (m³)',
        'Closing Volume': 'Storage volume at the end of the period (m³)',
        'Net Change': 'Closing Volume - Opening Volume. Positive = Filled. Negative = Drawdown',
        'Closure Error %': 'Indicates how well the balance closes. <5% is excellent. Higher values suggest measurement or data quality issues',
    }

    # === UI HELPER FUNCTIONS ===
    def add_metric_card(self, parent, label, value, color, icon=None):
        frame = ttk.LabelFrame(parent, text=f"{icon or ''} {label}".strip(), padding=12)
        frame.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.BOTH, expand=True)
        value_label = tk.Label(frame, text=value, font=('Segoe UI', 15, 'bold'), fg=color)
        value_label.pack()
        return frame
    
    def _bind_balance_tooltip(self, widget, label):
        """Bind floating tooltip to balance metric widget"""
        tooltip_text = self.BALANCE_TOOLTIPS.get(label, '')
        if not tooltip_text:
            return
        
        tooltip_window = None
        
        def show_tooltip(event):
            nonlocal tooltip_window
            if tooltip_window or not tooltip_text:
                return
            
            # Create tooltip window
            tooltip_window = tk.Toplevel(widget)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
            
            # Create tooltip frame
            tooltip_frame = tk.Frame(tooltip_window, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            tooltip_frame.pack()
            
            # Add text with word wrap
            label_widget = tk.Label(
                tooltip_frame,
                text=tooltip_text,
                bg='#34495e',
                fg='#e8eef5',
                font=('Segoe UI', 9),
                wraplength=300,
                justify='left',
                padx=10,
                pady=8
            )
            label_widget.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip_window
            if tooltip_window:
                try:
                    tooltip_window.destroy()
                except:
                    pass
                tooltip_window = None
        
        widget.bind('<Enter>', show_tooltip, add='+')
        widget.bind('<Leave>', hide_tooltip, add='+')

    def add_info_box(self, parent, text, icon=None):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 15))
        info_text = tk.Text(frame, height=3, wrap=tk.WORD, font=('Segoe UI', 9), relief=tk.FLAT, background='#f0f0f0', borderwidth=0)
        info_text.pack(fill=tk.X)
        enable_text_mousewheel(info_text)
        info_text.insert('1.0', f"{icon or ''} {text}".strip())
        info_text.configure(state='disabled', foreground='#666')
        return frame

    def add_legend(self, parent, text):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(10, 0))
        legend = ttk.Label(frame, text=text, font=('Segoe UI', 8, 'italic'), foreground='#666')
        legend.pack()
        return frame

    def add_treeview(self, parent, columns, headings, data, tag_configs):
        tree = ttk.Treeview(parent, columns=columns, show='tree headings', height=len(data)+2)
        for col, head in zip(columns, headings):
            # Determine alignment based on column type
            if col in ['volume', 'percentage', 'value']:
                data_anchor = 'e'  # Right-align numeric data
                heading_anchor = 'e'
                width = 150
            elif col in ['status', 'source']:
                data_anchor = 'center'
                heading_anchor = 'center'
                width = 150
            else:
                data_anchor = 'w'  # Left-align text data
                heading_anchor = 'w'
                width = 200
            tree.heading(col, text=head, anchor=heading_anchor)
            tree.column(col, width=width, anchor=data_anchor)
        for row in data:
            tree.insert('', 'end', values=row['values'], tags=(row.get('tag', ''),))
        for tag, config in tag_configs.items():
            tree.tag_configure(tag, **config)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.calculator = WaterBalanceCalculator()
        self.balance_engine = get_balance_check_engine()
        self.template_parser = get_template_parser()
        self.main_frame = None

        # Variables
        self.calc_date_var = None
        self.current_balance = None
        self.engine_result = None
        self.year_var = None
        self.month_var = None
        self.manual_inputs_vars = {}
        self.facility_flows_month_var = None
        self.facility_flows_year_var = None
        self.facility_flows_tree = None

    def load(self):
        """Load the calculations module"""
        if self.main_frame:
            self.main_frame.destroy()

        # Create outer container with professional background
        outer = tk.Frame(self.parent, bg='#f5f6f7')
        outer.pack(fill=tk.BOTH, expand=True)

        self.main_frame = tk.Frame(outer, bg='#f5f6f7')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Header
        self._create_header()

        # Input section
        self._create_input_section()
        
        # Results section
        self._create_results_section()
        
        # Show placeholder until user clicks Calculate
        self._show_placeholder()
    
    def _create_header(self):
        """Create header section"""
        header_frame = tk.Frame(self.main_frame, bg='white', relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 0), padx=0)
        
        inner = tk.Frame(header_frame, bg='white')
        inner.pack(fill=tk.X, padx=20, pady=(10, 10))
        
        title = tk.Label(inner, text="⚖️ Water Balance Calculations", 
                         font=('Segoe UI', 22, 'bold'),
                         bg='white', fg='#2c3e50')
        title.pack(anchor='w')
        
        info = tk.Label(inner, 
                        text="Calculate water balance using TRP formulas",
                        font=('Segoe UI', 11),
                        fg='#7f8c8d',
                        bg='white')
        info.pack(anchor='w', pady=(3, 0))
    
    def _create_input_section(self):
        """Create modern input controls with card design"""
        # Content area wrapper
        content_frame = tk.Frame(self.main_frame, bg='#f5f6f7')
        content_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 10))
        
        input_frame = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=1, highlightbackground='#c5d3e6', highlightthickness=1)
        input_frame.pack(fill=tk.X, pady=(0, 10), padx=0)
        
        inner = tk.Frame(input_frame, bg='white')
        inner.pack(fill=tk.X, padx=20, pady=12)
        
        tk.Label(inner, text="⚙️ Calculation Parameters", font=('Segoe UI', 12, 'bold'), bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 12))
        
        # Date selection (Month/Year selectors for performance, no tkcalendar)
        date_frame = tk.Frame(inner, bg='white')
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="📅 Calculation Month:", width=18).pack(side=tk.LEFT, padx=(0, 10))
        
        self.calc_date_var = tk.StringVar(master=date_frame)
        self.year_var = tk.StringVar(master=date_frame)
        self.month_var = tk.StringVar(master=date_frame)
        
        # Determine default month/year: latest DB date first, then Excel, then today
        try:
            db_latest = self.db.get_latest_data_date()
        except Exception:
            db_latest = None
        try:
            # Load METER READINGS Excel (legacy_excel_path: data\New Water Balance...xlsx)
            # This file contains the "Meter Readings" sheet with tonnes milled, RWD, etc.
            # NOT the flow diagram Excel (which has Flows_* sheets)
            excel_repo = get_default_excel_repo()
            latest_date = excel_repo.get_latest_date()
        except Exception:
            latest_date = None
        base_date = db_latest or latest_date or date.today()
        default_year = base_date.year
        default_month = base_date.month
        
        # Year selector (range: default_year-6 .. default_year+1)
        years = [str(y) for y in range(default_year - 6, default_year + 2)]
        ttk.Label(date_frame, text="Year:").pack(side=tk.LEFT, padx=(0, 6))
        year_combo = ttk.Combobox(date_frame, textvariable=self.year_var, values=years, width=6, state='readonly')
        year_combo.set(str(default_year))
        year_combo.pack(side=tk.LEFT, padx=(0, 12))
        
        # Month selector (Jan..Dec)
        month_names = [calendar.month_abbr[m] for m in range(1, 13)]
        ttk.Label(date_frame, text="Month:").pack(side=tk.LEFT, padx=(0, 6))
        month_combo = ttk.Combobox(date_frame, textvariable=self.month_var, values=month_names, width=6, state='readonly')
        month_combo.set(calendar.month_abbr[default_month])
        month_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Compose an actual date: use latest available date in selected month from Excel
        def update_calc_date_var(*_):
            try:
                y = int(self.year_var.get())
                m = list(calendar.month_abbr).index(self.month_var.get())
                
                # Default to last day of month (fastest path - no Excel access during init)
                last_day = calendar.monthrange(y, m)[1]
                composed = date(y, m, last_day)
                
                self.calc_date_var.set(composed.strftime('%Y-%m-%d'))
                # Date changed → reset override and prefill ore tonnage
                self._on_calc_date_change()
            except Exception:
                pass
        year_combo.bind('<<ComboboxSelected>>', update_calc_date_var)
        month_combo.bind('<<ComboboxSelected>>', update_calc_date_var)
        update_calc_date_var()
        
        # Calculate button
        calc_btn = tk.Button(date_frame, text="🔢 Calculate Balance", 
                             command=self._calculate_balance,
                             font=('Segoe UI', 10, 'bold'),
                             bg='#0066cc', fg='white',
                             relief=tk.FLAT, bd=0,
                             padx=20, pady=8,
                             cursor='hand2')
        calc_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Configure Balance Check button - DISABLED (using all template flows)
        # config_btn = ttk.Button(date_frame, text="⚙️ Configure Balance Check",
        #                        command=self._open_balance_config_editor)
        # config_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Removed Save Calculation and Area Exclusions per request
        # Auto-save is now ALWAYS enabled (no UI toggle)
    
    def _create_results_section(self):
        """Create results display"""
        # Modern tab styling with improved UX: larger, more readable, better spacing
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('CalcNotebook.TNotebook', background='#f5f6f7', borderwidth=0)
        # Enhanced tab styling: larger font, more padding for better visibility
        style.configure('CalcNotebook.TNotebook.Tab', 
                       background='#d6dde8', 
                       foreground='#2c3e50',
                       padding=[24, 16],  # Increased from [20, 12] for larger tab size
                       font=('Segoe UI', 11, 'bold'),  # Increased from 10 to 11, added bold for better visibility
                       relief='flat',
                       borderwidth=0)
        # Enhanced map with better visual feedback on interaction
        style.map('CalcNotebook.TNotebook.Tab',
                 background=[('selected', '#3498db'), ('active', '#5dade2'), ('!active', '#d6dde8')],
                 foreground=[('selected', '#ffffff'), ('active', '#ffffff'), ('!active', '#2c3e50')],
                 lightcolor=[('selected', '#3498db')],
                 darkcolor=[('selected', '#3498db')])
        
        # Create notebook for organized display with professional styling
        notebook_frame = tk.Frame(self.main_frame, bg='#f5f6f7')
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        notebook = ttk.Notebook(notebook_frame, style='CalcNotebook.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, pady=0)
        
        # Tab 1: System Balance (Regulator Mode - Authoritative Closure)
        self.closure_frame = ttk.Frame(notebook)
        notebook.add(self.closure_frame, text="⚖️ System Balance (Regulator)")

        # Tab 2: Recycled Water (Info Only)
        self.recycled_frame = ttk.Frame(notebook)
        notebook.add(self.recycled_frame, text="♻️ Recycled Water")
        
        # Data Quality tab removed per request

        # Tab 3b: Inputs Audit (read-only)
        self.inputs_frame = ttk.Frame(notebook)
        notebook.add(self.inputs_frame, text="🧾 Inputs Audit")

        # Tab 3c: Manual Inputs (monthly overrides)
        self.manual_inputs_frame = ttk.Frame(notebook)
        notebook.add(self.manual_inputs_frame, text="📝 Manual Inputs")

        # Tab 3c: Storage & Dams (per-facility drivers)
        self.storage_dams_frame = ttk.Frame(notebook)
        notebook.add(self.storage_dams_frame, text="🏗️ Storage & Dams")

        # Tab 4: Days of Operation (water runway analysis)
        self.days_of_operation_frame = ttk.Frame(notebook)
        notebook.add(self.days_of_operation_frame, text="⏳ Days of Operation")

        # Tab 5: Facility Flows (per-facility inflows/outflows by month)
        self.facility_flows_frame = ttk.Frame(notebook)
        notebook.add(self.facility_flows_frame, text="🏭 Facility Flows")

        # Template Balance (QA) and Template Check Summary tabs removed per request

        # Hidden for now - can be enabled later
        # Tab 3: Area Balance Breakdown
        self.area_balance_frame = ttk.Frame(notebook)
        # notebook.add(self.area_balance_frame, text="🗺️ Area Breakdown")

        # ORIGINAL Calculation Tabs (hidden for now)
        # Tab 4: Summary (water balance calculation)
        self.summary_frame = ttk.Frame(notebook)
        # notebook.add(self.summary_frame, text="📋 Summary")
        
        # Tab 5: Inflows
        self.inflows_frame = ttk.Frame(notebook)
        # notebook.add(self.inflows_frame, text="💧 Inflows")
        
        # Tab 6: Outflows
        self.outflows_frame = ttk.Frame(notebook)
        # notebook.add(self.outflows_frame, text="🚰 Outflows")
        
        # Tab 7: Storage
        self.storage_frame = ttk.Frame(notebook)
        # notebook.add(self.storage_frame, text="🏗️ Storage")

        # Tab 8: Future Water Balance Calc (placeholder)
        self.future_balance_frame = ttk.Frame(notebook)
        # notebook.add(self.future_balance_frame, text="📈 Water Balance Calculation")

        # Build manual inputs UI once tabs exist
        self._build_manual_inputs_tab()
        
        # Build facility flows UI
        self._build_facility_flows_tab()

    def _show_placeholder(self):
        """Show initial placeholder prompting user to run calculation on demand"""
        frames_to_clear = [
            getattr(self, 'closure_frame', None),
            getattr(self, 'recycled_frame', None),
            getattr(self, 'quality_frame', None),
            getattr(self, 'inputs_frame', None),
            getattr(self, 'days_of_operation_frame', None),
            # NOTE: manual_inputs_frame is intentionally excluded - it should always show the form
            getattr(self, 'breakdown_frame', None),
            getattr(self, 'balance_summary_frame', None),
            getattr(self, 'area_balance_frame', None),
            getattr(self, 'summary_frame', None),
            getattr(self, 'inflows_frame', None),
            getattr(self, 'outflows_frame', None),
            getattr(self, 'storage_frame', None),
            getattr(self, 'future_balance_frame', None)
        ]
        
        for frame in frames_to_clear:
            if not frame:
                continue
            for w in frame.winfo_children():
                w.destroy()
            
            # Styled placeholder matching Flow Diagram theme
            container = tk.Frame(frame, bg='#2c3e50')
            container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            
            msg = tk.Label(container, 
                          text="Select a month and click 'Calculate Balance' to generate results.",
                          font=('Segoe UI', 10),
                          bg='#2c3e50', fg='#e8eef5')
            msg.pack(pady=40)

    def _build_manual_inputs_tab(self):
        """Create manual inputs form with per-field descriptions and save action."""
        if not hasattr(self, 'manual_inputs_frame') or not self.manual_inputs_frame.winfo_exists():
            return

        for w in self.manual_inputs_frame.winfo_children():
            w.destroy()

        header = ttk.Label(self.manual_inputs_frame, text="Manual Monthly Inputs (m³)", font=('Segoe UI', 12, 'bold'))
        header.pack(anchor='w', pady=(4, 2))

        ttk.Label(self.manual_inputs_frame, text="Enter site consumption values when TRP historical Excel lacks data. Dust, tailings, and product moisture are auto-calculated from ore/concentrate data.", foreground='#555').pack(anchor='w', pady=(0, 8))

        form = ttk.Frame(self.manual_inputs_frame)
        form.pack(fill=tk.X, pady=4)

        fields = [
            ('mining_consumption_m3', 'Mining Consumption', 'Ancillary mining uses (wash-down, drills). If blank, zero.'),
            ('domestic_consumption_m3', 'Domestic Consumption', 'Offices, ablutions, kitchen. If blank, zero.'),
            ('discharge_m3', 'Discharge', 'Controlled releases to environment. If blank, zero.'),
        ]

        for key, label, desc in fields:
            row = ttk.Frame(form)
            row.pack(fill=tk.X, pady=4)
            ttk.Label(row, text=f"{label} (m³):", width=24).pack(side=tk.LEFT)
            var = self.manual_inputs_vars.setdefault(key, tk.StringVar(master=row, value='0'))
            ttk.Entry(row, textvariable=var, width=16).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(row, text=desc, foreground='#555').pack(side=tk.LEFT, fill=tk.X, expand=True)

        btns = ttk.Frame(self.manual_inputs_frame)
        btns.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(btns, text="💾 Save Manual Inputs", command=self._save_manual_inputs, style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="⟳ Reload", command=self._load_manual_inputs).pack(side=tk.LEFT)
        ttk.Button(btns, text="Clear to Zero", command=self._clear_manual_inputs).pack(side=tk.LEFT, padx=(8, 0))

        self._load_manual_inputs()

    def _clear_manual_inputs(self):
        for var in self.manual_inputs_vars.values():
            var.set('0')

    def _load_manual_inputs(self):
        calc_date = self._get_calc_date_obj()
        if not calc_date:
            return
        month_start = date(calc_date.year, calc_date.month, 1)
        manual = self.db.get_monthly_manual_inputs(month_start)
        for key, var in self.manual_inputs_vars.items():
            var.set(str(manual.get(key, 0) or 0))

    def _save_manual_inputs(self):
        calc_date = self._get_calc_date_obj()
        if not calc_date:
            messagebox.showwarning("Missing date", "Select a calculation month before saving manual inputs.")
            return
        month_start = date(calc_date.year, calc_date.month, 1)
        payload = {}
        try:
            for key, var in self.manual_inputs_vars.items():
                text = var.get().strip()
                payload[key] = float(text) if text else 0.0
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter numeric values only (m³).")
            return
        try:
            self.db.upsert_monthly_manual_inputs(month_start, payload)
            messagebox.showinfo("Saved", f"Manual inputs saved for {month_start.strftime('%Y-%m')}.")
        except Exception as exc:
            logger.error(f"Failed to save manual inputs: {exc}", exc_info=True)
            messagebox.showerror("Save failed", f"Could not save manual inputs:\n{exc}")

    def _build_facility_flows_tab(self):
        """Create facility-level inflows/outflows input interface"""
        if not hasattr(self, 'facility_flows_frame') or not self.facility_flows_frame.winfo_exists():
            return

        for w in self.facility_flows_frame.winfo_children():
            w.destroy()

        header = ttk.Label(self.facility_flows_frame, text="Facility-Level Inflows & Outflows (m³)", font=('Segoe UI', 12, 'bold'))
        header.pack(anchor='w', pady=(4, 2))

        ttk.Label(self.facility_flows_frame, 
                  text="Enter per-facility monthly inflows (pumped in) and outflows (pumped out). Data stored by month and year.", 
                  foreground='#555').pack(anchor='w', pady=(0, 8))

        # Control panel: Month/Year selector and action buttons
        control = ttk.Frame(self.facility_flows_frame)
        control.pack(fill=tk.X, pady=(8, 0), padx=4)

        ttk.Label(control, text="Month:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.facility_flows_month_var = tk.IntVar(value=datetime.now().month)
        month_combo = ttk.Combobox(control, textvariable=self.facility_flows_month_var, 
                                   values=list(range(1, 13)), width=8, state='readonly')
        month_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(control, text="Year:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.facility_flows_year_var = tk.IntVar(value=datetime.now().year)
        year_combo = ttk.Combobox(control, textvariable=self.facility_flows_year_var, 
                                  values=list(range(2020, 2030)), width=8, state='readonly')
        year_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(control, text="Load Data", command=self._load_facility_flows_data).pack(side=tk.LEFT, padx=3)
        ttk.Button(control, text="💾 Save All", command=self._save_facility_flows_data, style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(control, text="Clear Month", command=self._clear_facility_flows_month).pack(side=tk.LEFT, padx=3)

        # Treeview for facility flows
        tree_frame = ttk.Frame(self.facility_flows_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=8, padx=4)

        columns = ('facility_name', 'inflow', 'outflow', 'net')
        self.facility_flows_tree = ttk.Treeview(tree_frame, columns=columns, height=15, selectmode='browse')
        
        self.facility_flows_tree.column('#0', width=120)
        self.facility_flows_tree.column('facility_name', width=180)
        self.facility_flows_tree.column('inflow', width=120)
        self.facility_flows_tree.column('outflow', width=120)
        self.facility_flows_tree.column('net', width=100)

        self.facility_flows_tree.heading('#0', text='Facility Code')
        self.facility_flows_tree.heading('facility_name', text='Facility Name')
        self.facility_flows_tree.heading('inflow', text='Inflow (m³)')
        self.facility_flows_tree.heading('outflow', text='Outflow (m³)')
        self.facility_flows_tree.heading('net', text='Net (m³)')

        self.facility_flows_tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.facility_flows_tree.yview)
        self.facility_flows_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to edit values
        self.facility_flows_tree.bind('<Double-1>', self._on_facility_flow_cell_double_click)

        # Load data for current month/year
        self._load_facility_flows_data()

    def _load_facility_flows_data(self):
        """Load facility flows from database for selected month/year"""
        try:
            month = self.facility_flows_month_var.get()
            year = self.facility_flows_year_var.get()

            # Clear treeview
            for item in self.facility_flows_tree.get_children():
                self.facility_flows_tree.delete(item)

            # Populate from DB
            facilities = self.db.get_storage_facilities(active_only=False)
            for facility in facilities:
                fac_id = facility['facility_id']
                fac_code = facility['facility_code']
                fac_name = facility['facility_name']

                inflow = self.db.get_facility_inflow_monthly(fac_id, month, year) or 0.0
                outflow = self.db.get_facility_outflow_monthly(fac_id, month, year) or 0.0
                net = inflow - outflow

                self.facility_flows_tree.insert('', 'end', iid=f'fac_{fac_id}',
                                               text=fac_code,
                                               values=(fac_name, f'{inflow:.0f}', f'{outflow:.0f}', f'{net:.0f}'))
        except Exception as e:
            logger.error(f"Error loading facility flows: {e}", exc_info=True)
            messagebox.showerror('Error', f'Failed to load facility flows: {e}')

    def _on_facility_flow_cell_double_click(self, event):
        """Handle double-click to edit facility flow values"""
        region = self.facility_flows_tree.identify_region(event.x, event.y)
        if region != 'cell':
            return

        item_id = self.facility_flows_tree.identify('item', event.x, event.y)
        column = self.facility_flows_tree.identify_column(event.x)
        
        # Column mapping: #0=code, #1=name, #2=inflow, #3=outflow, #4=net
        # We want to edit columns #2 (inflow) and #3 (outflow)
        if column == '#2':  # Inflow column
            column_name = 'Inflow (m³)'
        elif column == '#3':  # Outflow column
            column_name = 'Outflow (m³)'
        else:
            return  # Ignore other columns
        
        item_values = list(self.facility_flows_tree.item(item_id)['values'])
        col_index = 1 if column == '#2' else 2  # 1=inflow (values[1]), 2=outflow (values[2])
        old_value = item_values[col_index]
        
        # Create popup dialog
        popup = tk.Toplevel(self.facility_flows_frame)
        popup.title('Edit Flow Value')
        popup_width, popup_height = 420, 220
        # Center on screen
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        pos_x = int((screen_w - popup_width) / 2)
        pos_y = int((screen_h - popup_height) / 2)
        popup.geometry(f'{popup_width}x{popup_height}+{pos_x}+{pos_y}')
        popup.resizable(False, False)
        popup.transient(self.facility_flows_frame)
        popup.grab_set()
        popup.configure(bg='#f5f7fb')

        content = tk.Frame(popup, bg='#f5f7fb', padx=18, pady=14)
        content.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content, text=f'Edit {column_name}', font=('Segoe UI', 12, 'bold'), background='#f5f7fb').pack(anchor='w', pady=(0, 6))
        ttk.Label(content, text=f'Current value: {old_value}', foreground='#666', background='#f5f7fb').pack(anchor='w', pady=(0, 12))

        entry = ttk.Entry(content, width=36, font=('Segoe UI', 11))
        entry.pack(fill=tk.X, pady=(0, 12))
        entry.insert(0, str(old_value))
        entry.focus()
        entry.select_range(0, tk.END)

        def save_edit():
            try:
                new_value = float(entry.get())
                if new_value < 0:
                    messagebox.showerror('Invalid', 'Values must be ≥ 0')
                    return
                item_values[col_index] = f'{new_value:.0f}'
                self.facility_flows_tree.item(item_id, values=item_values)
                popup.destroy()
            except ValueError:
                messagebox.showerror('Invalid', 'Please enter a numeric value')

        def cancel():
            popup.destroy()

        buttons = tk.Frame(content, bg='#f5f7fb')
        buttons.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(buttons, text='Save', command=save_edit, style='Accent.TButton').pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(buttons, text='Cancel', command=cancel).pack(side=tk.RIGHT)

        entry.bind('<Return>', lambda e: save_edit())
        entry.bind('<Escape>', lambda e: cancel())

    def _save_facility_flows_data(self):
        """Save all facility flows for selected month/year to database"""
        try:
            month = self.facility_flows_month_var.get()
            year = self.facility_flows_year_var.get()
            save_count = 0

            # Iterate through all rows in treeview
            for item_id in self.facility_flows_tree.get_children():
                values = self.facility_flows_tree.item(item_id)['values']
                if values:
                    fac_id = int(item_id.split('_')[1])
                    inflow = float(values[1]) if values[1] else 0.0
                    outflow = float(values[2]) if values[2] else 0.0

                    # Save to DB (only if value > 0)
                    if inflow > 0:
                        self.db.set_facility_inflow_monthly(fac_id, month, inflow, year)
                        save_count += 1
                    else:
                        # Delete if zero
                        self.db.delete_facility_inflow(fac_id, month, year)

                    if outflow > 0:
                        self.db.set_facility_outflow_monthly(fac_id, month, outflow, year)
                        save_count += 1
                    else:
                        # Delete if zero
                        self.db.delete_facility_outflow(fac_id, month, year)

            messagebox.showinfo('Saved', f'Facility flows for {month:02d}/{year} saved ({save_count} entries)!')
            
            # Recalculate balance to show updated closure error
            self._calculate_balance()
        except Exception as e:
            logger.error(f"Error saving facility flows: {e}", exc_info=True)
            messagebox.showerror('Error', f'Failed to save facility flows: {e}')

    def _clear_facility_flows_month(self):
        """Clear all facility flows for current month/year"""
        if messagebox.askyesno('Confirm', f'Clear all facility flows for month {self.facility_flows_month_var.get():02d}/{self.facility_flows_year_var.get()}?'):
            try:
                month = self.facility_flows_month_var.get()
                year = self.facility_flows_year_var.get()

                for item_id in self.facility_flows_tree.get_children():
                    fac_id = int(item_id.split('_')[1])
                    self.db.delete_facility_inflow(fac_id, month, year)
                    self.db.delete_facility_outflow(fac_id, month, year)

                messagebox.showinfo('Cleared', f'Facility flows cleared for {month:02d}/{year}')
                self._load_facility_flows_data()
            except Exception as e:
                logger.error(f"Error clearing facility flows: {e}", exc_info=True)
                messagebox.showerror('Error', f'Failed to clear flows: {e}')
    
    def _calculate_balance(self):
        """Perform water balance calculation"""
        import time
        calc_start = time.perf_counter()
        logger.info("⏱️  Calculations: on-demand run started")
        
        try:
            # Validate Meter Readings Excel file exists before proceeding
            excel_repo = get_default_excel_repo()
            if not excel_repo.config.file_path.exists():
                messagebox.showerror(
                    "Excel File Missing",
                    f"Meter Readings Excel file not found:\n\n{excel_repo.config.file_path}\n\n"
                    "This file contains tonnes milled, RWD, and dewatering volumes.\n"
                    "Please configure the path in Settings > Data Sources (legacy_excel_path)."
                )
                logger.error(f"❌ Meter Readings Excel not found: {excel_repo.config.file_path}")
                return
            
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
            ore_tonnes = None
            
            # Clear caches to ensure fresh Excel data is read
            self.calculator.clear_cache()
            logger.info("  ✓ Caches cleared (fresh Excel read enabled)")
            
            # Calculate balance
            balance_calc_start = time.perf_counter()
            self.current_balance = self.calculator.calculate_water_balance(calc_date, ore_tonnes)
            logger.info(f"  ✓ Balance calculation: {(time.perf_counter() - balance_calc_start)*1000:.0f}ms")

            # Run new closure engine (fresh-only closure) using legacy-backed services
            legacy_services = LegacyBalanceServices(ore_tonnes=ore_tonnes)
            engine = BalanceEngine(
                inflows_service=legacy_services,
                outflows_service=legacy_services,
                storage_service=legacy_services,
                mode="REGULATOR",
            )
            self.engine_result = engine.run(calc_date)
            logger.info(
                f"  ✓ Closure engine: fresh_in={self.engine_result.fresh_in.total:.0f}, "
                f"dirty_in={self.engine_result.recycled.total:.0f}, "
                f"total_in={self.engine_result.fresh_in.total + self.engine_result.recycled.total:.0f}, "
                f"outflows={self.engine_result.outflows.total:.0f}, "
                f"dS={self.engine_result.storage.delta:.0f}, "
                f"err={self.engine_result.error_m3:.0f} m3 ({self.engine_result.error_pct:.2f}%)"
            )
            
            # Calculate balance check from templates
            check_start = time.perf_counter()
            self.balance_engine.calculate_balance()
            logger.info(f"  ✓ Balance check engine: {(time.perf_counter() - check_start)*1000:.0f}ms")
            
            # Update displays
            ui_start = time.perf_counter()
            self._update_closure_display()
            self._update_recycled_display()
            self._update_inputs_audit_display()
            self._update_storage_dams_display()
            self._update_days_of_operation_display()
            self._update_future_balance_placeholder()
            logger.info(f"  ✓ UI update: {(time.perf_counter() - ui_start)*1000:.0f}ms")
            
            total_elapsed = (time.perf_counter() - calc_start) * 1000
            logger.info(f"✅ Calculations completed in {total_elapsed:.0f}ms")

            # ALWAYS auto-save calculation and persist storage volumes (no option to disable)
            try:
                existing_id = self.calculator._check_duplicate_calculation(calc_date, ore_tonnes or 0)
                if existing_id:
                    # Replace existing calculation silently
                    self.db.execute_update("DELETE FROM calculations WHERE calc_id = ?", (existing_id,))
                    calc_id = self.calculator.save_calculation(calc_date, ore_tonnes, persist_storage=True)
                    logger.info(f"🔄 Auto-saved calculation for {calc_date} (replaced ID {existing_id} → new ID {calc_id}); storage volumes persisted")
                else:
                    calc_id = self.calculator.save_calculation(calc_date, ore_tonnes, persist_storage=True)
                    logger.info(f"💾 Auto-saved calculation for {calc_date} (ID {calc_id}); storage volumes persisted")
                # Invalidate DB caches so other modules (Dashboard) see latest volumes
                self.db.invalidate_all_caches()
            except Exception as e:
                logger.warning(f"Auto-save skipped due to error: {e}")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate balance:\n{str(e)}")
            logger.error(f"Calculation error: {e}", exc_info=True)
    
    # DEPRECATED: Balance check moved to Flow Diagram dashboard
    def _update_balance_calculation_breakdown(self):
        """DEPRECATED: Balance calculation breakdown moved to Flow Diagram - use Balance Check button there"""
        # This method is no longer used - balance check with recirculation formula
        # is now available in the Flow Diagram dashboard via "Balance Check" button
        return
        # Check if frame still exists
        if not hasattr(self, 'breakdown_frame') or not self.breakdown_frame.winfo_exists():
            logger.warning("Breakdown frame no longer exists, skipping update")
            return
        
        # Clear existing
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()
        
        metrics = self.balance_engine.get_metrics()
        if not metrics:
            return
        
        # Main container with Flow Diagram theme
        main_container = tk.Frame(self.breakdown_frame, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create scrollable area
        canvas = tk.Canvas(main_container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame,
                text="📐 Balance Calculation Breakdown",
                font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        
        tk.Label(header_frame,
                text="Step-by-step calculation with all parameters and formula",
                font=('Segoe UI', 10),
                bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))
        
        # Formula section
        formula_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        formula_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(formula_frame,
                text="📝 Balance Formula",
                font=('Segoe UI', 11, 'bold'),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
        
        formula_text = (
            "Total Inflows − Total Recirculation − Total Outflows = Balance Difference\n"
            "Balance Error % = (Balance Difference ÷ Total Inflows) × 100"
        )
        tk.Label(formula_frame,
                text=formula_text,
                font=('Segoe UI', 10, 'italic'),
                bg='#34495e', fg='#e8eef5',
                justify='left').pack(anchor='w', padx=12, pady=(0, 10))
        
        # Parameters section
        params_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        params_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(params_frame,
                text="⚙️ Input Parameters",
                font=('Segoe UI', 11, 'bold'),
                bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        
        # Parameters in a grid
        params_grid = tk.Frame(params_frame, bg='#2c3e50')
        params_grid.pack(fill=tk.X, pady=(10, 0))
        
        # Get calculation date from UI
        try:
            calc_date_str = self.calc_date_var.get() if hasattr(self, 'calc_date_var') else datetime.now().strftime('%Y-%m-%d')
        except:
            calc_date_str = datetime.now().strftime('%Y-%m-%d')
        
        params_data = [
            ("Calculation Date", calc_date_str, "📅"),
        ]
        
        for i, (label, value, icon) in enumerate(params_data):
            param_card = tk.Frame(params_grid, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            param_card.pack(fill=tk.X, pady=5)
            
            tk.Label(param_card, text=f"{icon} {label}:", font=('Segoe UI', 10, 'bold'),
                    bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(8, 2))
            tk.Label(param_card, text=str(value), font=('Segoe UI', 10),
                    bg='#34495e', fg='#3498db').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Calculation steps section
        steps_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tk.Label(steps_frame,
                text="📊 Calculation Steps",
                font=('Segoe UI', 11, 'bold'),
                bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        
        # Step 1: Total Inflows
        step1_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step1_frame.pack(fill=tk.X, pady=(10, 5))
        
        tk.Label(step1_frame, text="Step 1️⃣ Calculate Total Inflows",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#3498db').pack(anchor='w', padx=12, pady=(8, 5))
        tk.Label(step1_frame, text=f"Total Inflows = {metrics.total_inflows:,.0f} m³  ({metrics.inflow_count} sources)",
                font=('Segoe UI', 10),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 2: Total Recirculation
        step2_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step2_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step2_frame, text="Step 2️⃣ Calculate Total Recirculation",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#27ae60').pack(anchor='w', padx=12, pady=(8, 5))
        tk.Label(step2_frame, text=f"Total Recirculation = {metrics.total_recirculation:,.0f} m³  ({metrics.recirculation_count} self-loops)",
                font=('Segoe UI', 10),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 3: Total Outflows
        step3_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step3_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step3_frame, text="Step 3️⃣ Calculate Total Outflows",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#e74c3c').pack(anchor='w', padx=12, pady=(8, 5))
        tk.Label(step3_frame, text=f"Total Outflows = {metrics.total_outflows:,.0f} m³  ({metrics.outflow_count} flows)",
                font=('Segoe UI', 10),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 4: Balance Difference
        step4_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step4_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step4_frame, text="Step 4️⃣ Calculate Balance Difference",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#f39c12').pack(anchor='w', padx=12, pady=(8, 5))
        
        calc_text = (
            f"{metrics.total_inflows:,.0f} − {metrics.total_recirculation:,.0f} − {metrics.total_outflows:,.0f} "
            f"= {metrics.balance_difference:,.0f} m³"
        )
        tk.Label(step4_frame, text=calc_text,
                font=('Segoe UI', 10),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 5: Error Percentage
        step5_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step5_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step5_frame, text="Step 5️⃣ Calculate Error Percentage",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#9b59b6').pack(anchor='w', padx=12, pady=(8, 5))
        
        error_calc = (
            f"({metrics.balance_difference:,.0f} ÷ {metrics.total_inflows:,.0f} fresh inflows) × 100 "
            f"= {metrics.balance_error_percent:.2f}%"
        )
        tk.Label(step5_frame, text=error_calc,
                font=('Segoe UI', 10),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Final result
        result_frame = tk.Frame(steps_frame, bg='#27ae60' if metrics.is_balanced else '#e74c3c', relief=tk.SOLID, borderwidth=2)
        result_frame.pack(fill=tk.X, pady=(10, 0))
        
        status_icon = "✅" if metrics.is_balanced else "⚠️"
        tk.Label(result_frame, text=f"{status_icon} Final Status: {metrics.status_label}",
                font=('Segoe UI', 12, 'bold'),
                bg='#27ae60' if metrics.is_balanced else '#e74c3c', fg='#e8eef5').pack(padx=12, pady=12)
    
    
    def _update_balance_check_summary(self):
        """Update balance check summary tab with overall water balance"""
        # Check if frame still exists
        if not hasattr(self, 'balance_summary_frame') or not self.balance_summary_frame.winfo_exists():
            logger.warning("Balance summary frame no longer exists, skipping update")
            return
        
        # Clear existing
        for widget in self.balance_summary_frame.winfo_children():
            widget.destroy()
        
        metrics = self.balance_engine.get_metrics()
        if not metrics:
            return
        
        ttk.Label(self.balance_summary_frame, 
                 text="⚖️ Water Balance Check (Overall)", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # Info box explaining the calculation
        self.add_info_box(self.balance_summary_frame,
                 "Balance Equation: Fresh Inflows − Recirculation − Total Outflows = Balance Difference\n"
                 "Error %: (Balance Difference ÷ Fresh Inflows) × 100 (fresh excludes recycled/TSF returns)\n"
                 "Status: < 0.1% = Excellent | < 0.5% = Good | ≥ 0.5% = Check needed",
                 icon="⚙️")
        
        # Key metrics
        metrics_frame = ttk.Frame(self.balance_summary_frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.add_metric_card(metrics_frame, "Total Inflows", f"{metrics.total_inflows:,.0f} m³",
                            "#007bff", icon="💧")
        self.add_metric_card(metrics_frame, "Total Outflows", f"{metrics.total_outflows:,.0f} m³",
                            "#dc3545", icon="🚰")
        self.add_metric_card(metrics_frame, "Dam Recirculation", f"{metrics.total_recirculation:,.0f} m³",
                            "#28a745", icon="♻️")
        self.add_metric_card(metrics_frame, "Balance Difference", f"{metrics.balance_difference:,.0f} m³",
                            "#ff6b6b" if abs(metrics.balance_error_percent) > 0.5 else "#007bff", icon="⚖️")
        
        # Error percentage and status
        error_color = "#28a745" if abs(metrics.balance_error_percent) < 0.5 else "#ffc107" if abs(metrics.balance_error_percent) < 1.0 else "#dc3545"
        error_frame = ttk.Frame(self.balance_summary_frame)
        error_frame.pack(fill=tk.X, pady=15)
        
        self.add_metric_card(error_frame, "Balance Error %", f"{metrics.balance_error_percent:.2f}%",
                            error_color, icon="📊")
        self.add_metric_card(error_frame, "Status", metrics.status_label,
                            error_color, icon="✅")
        
        # Summary statistics
        stats_frame = ttk.LabelFrame(self.balance_summary_frame, text="📈 Summary Statistics", padding=10)
        stats_frame.pack(fill=tk.X)
        
        stats_data = [
            {"values": ("Total Inflow Sources", str(metrics.inflow_count)), "tag": "normal"},
            {"values": ("Total Outflow Flows", str(metrics.outflow_count)), "tag": "normal"},
            {"values": ("Total Recirculation Loops", str(metrics.recirculation_count)), "tag": "normal"},
            {"values": ("Number of Areas", str(len(metrics.area_metrics))), "tag": "normal"},
            {"values": ("Balanced Areas", str(sum(1 for a in metrics.area_metrics.values() if a.is_balanced))), "tag": "normal"},
        ]
        
        self.add_treeview(stats_frame, ('stat', 'count'), 
                         ['Statistic', 'Count'], stats_data, {'normal': {}})
    
    def _update_area_balance_breakdown(self):
        """Update per-area balance breakdown tab"""
        # Check if frame still exists
        if not hasattr(self, 'area_balance_frame') or not self.area_balance_frame.winfo_exists():
            logger.warning("Area balance frame no longer exists, skipping update")
            return
        
        # Clear existing
        for widget in self.area_balance_frame.winfo_children():
            widget.destroy()
        
        metrics = self.balance_engine.get_metrics()
        if not metrics or not metrics.area_metrics:
            return
        
        # Create notebook for each area
        area_notebook = ttk.Notebook(self.area_balance_frame)
        area_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Overall summary tab
        summary_tab = ttk.Frame(area_notebook, padding=15)
        area_notebook.add(summary_tab, text="📊 All Areas Summary")
        
        # Create summary table
        summary_data = []
        for area_name in sorted(metrics.area_metrics.keys()):
            area = metrics.area_metrics[area_name]
            summary_data.append({
                "values": (
                    area_name,
                    f"{area.total_inflows:,.0f}",
                    f"{area.total_outflows:,.0f}",
                    f"{area.total_recirculation:,.0f}",
                    f"{area.balance_difference:,.0f}",
                    f"{area.balance_error_percent:.2f}%",
                    area.status_label
                ),
                "tag": "balanced" if area.is_balanced else "unbalanced"
            })
        
        tag_configs_summary = {
            'balanced': {'foreground': '#28a745'},
            'unbalanced': {'foreground': '#ff6b6b', 'font': ('Segoe UI', 9, 'bold')}
        }
        
        self.add_treeview(summary_tab, 
                         ('area', 'inflows', 'outflows', 'recirculation', 'difference', 'error_pct', 'status'),
                         ['Area', 'Inflows (m³)', 'Outflows (m³)', 'Recirculation (m³)', 
                          'Difference (m³)', 'Error %', 'Status'],
                         summary_data, tag_configs_summary)
        
        # Individual area tabs
        for area_name in sorted(metrics.area_metrics.keys()):
            area = metrics.area_metrics[area_name]
            area_tab = ttk.Frame(area_notebook, padding=15)
            area_notebook.add(area_tab, text=f"🏭 {area_name}")
            
            # Area metrics
            metrics_frame = ttk.Frame(area_tab)
            metrics_frame.pack(fill=tk.X, pady=(0, 15))
            
            self.add_metric_card(metrics_frame, "Inflows", f"{area.total_inflows:,.0f} m³",
                                "#007bff", icon="💧")
            self.add_metric_card(metrics_frame, "Outflows", f"{area.total_outflows:,.0f} m³",
                                "#dc3545", icon="🚰")
            self.add_metric_card(metrics_frame, "Recirculation", f"{area.total_recirculation:,.0f} m³",
                                "#28a745", icon="♻️")
            
            error_color = "#28a745" if area.is_balanced else "#ff6b6b"
            self.add_metric_card(metrics_frame, "Balance Error %", f"{area.balance_error_percent:.2f}%",
                                error_color, icon="⚖️")
            
            # Breakdown
            breakdown_data = [
                {"values": (f"{area_name} Inflows", f"{area.total_inflows:,.0f}"), "tag": "input"},
                {"values": ("Less: Recirculation", f"({area.total_recirculation:,.0f})"), "tag": "calculation"},
                {"values": ("Less: Outflows", f"({area.total_outflows:,.0f})"), "tag": "calculation"},
                {"values": ("─" * 35, "─" * 20), "tag": "separator"},
                {"values": ("= Balance Difference", f"{area.balance_difference:,.0f}"), "tag": "result"},
                {"values": ("Error %", f"{area.balance_error_percent:.2f}%"), "tag": "error"},
            ]
            
            breakdown_frame = ttk.LabelFrame(area_tab, text="⚖️ Balance Breakdown", padding=10)
            breakdown_frame.pack(fill=tk.BOTH, expand=True)
            
            tag_configs_area = {
                'input': {'foreground': '#007bff'},
                'calculation': {'foreground': '#666'},
                'result': {'font': ('Segoe UI', 10, 'bold'), 'foreground': '#000'},
                'error': {'font': ('Segoe UI', 10, 'bold'), 'foreground': error_color},
                'separator': {'foreground': '#ccc'}
            }
            
            self.add_treeview(breakdown_frame, ('item', 'value'),
                             ['Item', 'Value (m³)'], breakdown_data, tag_configs_area)
            
            # Component details
            details_data = [
                {"values": ("Inflow Count", str(area.inflow_count)), "tag": "normal"},
                {"values": ("Outflow Count", str(area.outflow_count)), "tag": "normal"},
                {"values": ("Recirculation Count", str(area.recirculation_count)), "tag": "normal"},
                {"values": ("Status", area.status_label), "tag": "status"},
            ]
            
            details_frame = ttk.LabelFrame(area_tab, text="📋 Details", padding=10)
            details_frame.pack(fill=tk.X, pady=(15, 0))
            
            self.add_treeview(details_frame, ('detail', 'value'),
                             ['Detail', 'Value'], details_data, {'normal': {}, 'status': {}})

    def _open_balance_config_editor(self):
        """Open dialog to configure which flows are included in balance check.
        
        Uses template flow codes to enable/disable flows from:
        - INFLOW_CODES_TEMPLATE.txt
        - OUTFLOW_CODES_TEMPLATE_CORRECTED.txt
        - DAM_RECIRCULATION_TEMPLATE.txt
        """
        import json
        from pathlib import Path
        from utils.template_data_parser import get_template_parser
        
        config_path = Path('data/balance_check_config.json')
        
        # Load existing config or create default
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {'inflows': [], 'recirculation': [], 'outflows': []}
        
        # Get available flows from templates
        try:
            parser = get_template_parser()
            
            # Collect all flows
            available_flows = {
                'inflows': parser.inflows,
                'recirculation': parser.recirculation,
                'outflows': parser.outflows
            }
        except Exception as e:
            messagebox.showerror("Error Loading Templates", 
                               f"Cannot load template files.\n\n"
                               f"Error: {str(e)}")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("⚖️ Configure Balance Check - Select Flows to Include")
        dialog.transient(self.parent)
        dialog.grab_set()
        self._center_window(dialog, 1000, 700)
        
        # Header
        header = tk.Frame(dialog, bg='#2c3e50', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="Balance Check Configuration",
                font=('Segoe UI', 12, 'bold'),
                bg='#2c3e50', fg='#e8eef5').pack(side='left', padx=15, pady=15)
        
        tk.Label(header,
                text="Select which flows to include in the balance calculation",
                font=('Segoe UI', 9),
                bg='#2c3e50', fg='#95a5a6').pack(side='left', padx=(0, 15))
        
        # Main content
        content = tk.Frame(dialog, bg='#e8eef5')
        content.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Info box
        info_frame = tk.Frame(content, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        info_text = (
            "📋 Instructions: Check/uncheck flows to include/exclude them from balance calculation.\n"
            "Only ENABLED flows will be included when you click 'Calculate Balance' in the Calculations module."
        )
        tk.Label(info_frame, text=info_text, font=('Segoe UI', 9),
                bg='#34495e', fg='#e8eef5', justify='left').pack(padx=12, pady=8)
        
        # Notebook for flow types
        from tkinter import ttk
        notebook = ttk.Notebook(content)
        notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        flow_checks = {}  # Store checkbutton variables
        
        # Create tabs for each flow type
        for flow_type in ['inflows', 'recirculation', 'outflows']:
            tab_frame = tk.Frame(notebook, bg='#e8eef5')
            notebook.add(tab_frame, text=f"{flow_type.title()}")
            
            # Scrollable area
            canvas_frame = tk.Frame(tab_frame, bg='#e8eef5')
            canvas_frame.pack(fill='both', expand=True)
            
            canvas = tk.Canvas(canvas_frame, bg='#e8eef5', highlightthickness=0)
            scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#e8eef5')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            enable_canvas_mousewheel(canvas)
            
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Get flows for this type
            flows = available_flows[flow_type]
            
            # Create checkbutton for each flow
            for entry in flows:
                # Check if flow is in config
                is_enabled = False
                for config_item in config.get(flow_type, []):
                    if config_item.get('code') == entry.code:
                        is_enabled = config_item.get('enabled', True)
                        break
                
                var = tk.BooleanVar(value=is_enabled)
                flow_checks[entry.code] = (var, flow_type)
                
                # Frame for each flow item
                item_frame = tk.Frame(scrollable_frame, bg='#e8eef5')
                item_frame.pack(fill='x', padx=10, pady=4)
                
                # Checkbutton
                check = ttk.Checkbutton(item_frame, text=f"{entry.code}", variable=var)
                check.pack(side='left', anchor='w')
                
                # Flow name and value
                label_text = f"{entry.name} ({entry.value_m3:,.0f} {entry.unit})"
                label = tk.Label(item_frame, text=label_text, font=('Segoe UI', 9),
                               bg='#e8eef5', fg='#7f8c8d')
                label.pack(side='left', padx=(10, 0), anchor='w')
        
        # Footer buttons
        footer = tk.Frame(dialog, bg='#e8eef5', height=60)
        footer.pack(fill='x')
        footer.pack_propagate(False)
        
        def save_and_close():
            # Build new config from checked items
            new_config = {'inflows': [], 'recirculation': [], 'outflows': []}
            
            for flow_code, (var, flow_type) in flow_checks.items():
                # Find the flow in templates to get metadata
                for entry in available_flows[flow_type]:
                    if entry.code == flow_code:
                        new_config[flow_type].append({
                            'code': entry.code,
                            'name': entry.name,
                            'area': entry.area,
                            'enabled': var.get()
                        })
                        break
            
            # Save config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            # Count enabled flows
            enabled_count = sum(
                len([item for item in new_config[flow_type] if item.get('enabled')])
                for flow_type in ['inflows', 'recirculation', 'outflows']
            )
            
            messagebox.showinfo("Saved", 
                              f"✅ Balance check configuration saved!\n\n"
                              f"{enabled_count} flows will be included in calculations.")
            dialog.destroy()
        
        ttk.Button(footer, text="💾 Save Configuration", command=save_and_close,
                  width=25).pack(side='right', padx=10, pady=12)
        ttk.Button(footer, text="Cancel", command=dialog.destroy,
                  width=15).pack(side='right', pady=12)

    def _center_window(self, window, width, height):
        """Center a window on the parent."""
        window.update_idletasks()
        try:
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_w = self.parent.winfo_width() or window.winfo_screenwidth()
            parent_h = self.parent.winfo_height() or window.winfo_screenheight()
        except Exception:
            parent_x, parent_y = 0, 0
            parent_w, parent_h = window.winfo_screenwidth(), window.winfo_screenheight()
        
        x = parent_x + max((parent_w - width) // 2, 0)
        y = parent_y + max((parent_h - height) // 2, 0)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _update_closure_display(self):
        """Display System Balance (Regulator Mode) - authoritative closure."""
        if not hasattr(self, 'closure_frame') or not self.closure_frame.winfo_exists():
            return
        
        for widget in self.closure_frame.winfo_children():
            widget.destroy()
        
        if not self.engine_result:
            return
        
        result = self.engine_result
        
        # Main container with Flow Diagram theme
        main_container = tk.Frame(self.closure_frame, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create scrollable area
        canvas = tk.Canvas(main_container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="⚖️ System Water Balance (Regulator Mode)",
                font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        tk.Label(header_frame, text="Authoritative closure using fresh + dirty water inflows",
                font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))
        
        # Master equation display
        eq_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        eq_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(eq_frame, text="📝 Master Balance Equation",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
        
        eq_text = "(Fresh Inflows + Dirty Inflows) − Total Outflows − ΔStorage = Balance Error"
        tk.Label(eq_frame, text=eq_text, font=('Segoe UI', 10, 'italic'),
                bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 10))
        
        # Key metrics cards
        metrics_grid = tk.Frame(scrollable_frame, bg='#2c3e50')
        metrics_grid.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def add_metric(parent, label, value, color, row, col):
            card = tk.Frame(parent, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            label_widget = tk.Label(card, text=label, font=('Segoe UI', 9), bg='#34495e', fg='#95a5a6')
            label_widget.pack(padx=10, pady=(8, 2))
            value_widget = tk.Label(card, text=value, font=('Segoe UI', 14, 'bold'), bg='#34495e', fg=color)
            value_widget.pack(padx=10, pady=(0, 8))
            
            # Add tooltip binding to both label and value
            self._bind_balance_tooltip(label_widget, label)
            self._bind_balance_tooltip(value_widget, label)
            self._bind_balance_tooltip(card, label)
        
        metrics_grid.columnconfigure(0, weight=1)
        metrics_grid.columnconfigure(1, weight=1)
        metrics_grid.columnconfigure(2, weight=1)
        
        add_metric(metrics_grid, "Fresh Inflows", f"{result.fresh_in.total:,.0f} m³", "#3498db", 0, 0)
        add_metric(metrics_grid, "Dirty Inflows", f"{result.recycled.total:,.0f} m³", "#95a5a6", 0, 1)
        add_metric(metrics_grid, "Total Outflows", f"{result.outflows.total:,.0f} m³", "#e74c3c", 0, 2)
        
        # Total inflows (fresh + dirty)
        total_inflows = result.fresh_in.total + result.recycled.total
        add_metric(metrics_grid, "Total Inflows", f"{total_inflows:,.0f} m³", "#2ecc71", 1, 0)
        
        error_color = "#27ae60" if abs(result.error_pct) < 5.0 else "#e74c3c"
        add_metric(metrics_grid, "ΔStorage", f"{result.storage.delta:,.0f} m³", "#f39c12", 1, 1)
        add_metric(metrics_grid, "Balance Error", f"{result.error_m3:,.0f} m³", error_color, 1, 2)
        add_metric(metrics_grid, "Error %", f"{result.error_pct:.2f}%", error_color, 2, 0)
        
        status = "✅ CLOSED" if abs(result.error_pct) < 5.0 else "⚠️ CHECK REQUIRED"
        status_color = "#27ae60" if abs(result.error_pct) < 5.0 else "#e74c3c"
        add_metric(metrics_grid, "Status", status, status_color, 2, 1)
        
        # Fresh inflows breakdown
        inflows_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        inflows_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(inflows_frame, text="💧 Fresh Water Inflows",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
        
        for comp, val in result.fresh_in.components.items():
            comp_frame = tk.Frame(inflows_frame, bg='#34495e')
            comp_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(comp_frame, text=f"• {comp.replace('_', ' ').title()}:",
                    font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
            tk.Label(comp_frame, text=f"{val:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#3498db').pack(side='left', padx=10)
        
        tk.Frame(inflows_frame, bg='#7f8c8d', height=1).pack(fill=tk.X, padx=12, pady=5)
        total_frame = tk.Frame(inflows_frame, bg='#34495e')
        total_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        tk.Label(total_frame, text="TOTAL FRESH INFLOWS:",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
        tk.Label(total_frame, text=f"{result.fresh_in.total:,.0f} m³",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#3498db').pack(side='left', padx=10)
        
        # Dirty inflows breakdown (RWD only)
        rwd_value = result.recycled.components.get('rwd_inflow', 0) if result.recycled.components else 0
        if rwd_value > 0:
            dirty_inflows_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            dirty_inflows_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
            
            tk.Label(dirty_inflows_frame, text="💧 Dirty Water Inflows",
                    font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
            
            rwd_frame = tk.Frame(dirty_inflows_frame, bg='#34495e')
            rwd_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(rwd_frame, text="• RWD (Return Water Dam):",
                    font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
            tk.Label(rwd_frame, text=f"{rwd_value:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#95a5a6').pack(side='left', padx=10)
            
            tk.Frame(dirty_inflows_frame, bg='#7f8c8d', height=1).pack(fill=tk.X, padx=12, pady=5)
            total_dirty_frame = tk.Frame(dirty_inflows_frame, bg='#34495e')
            total_dirty_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
            tk.Label(total_dirty_frame, text="TOTAL DIRTY INFLOWS:",
                    font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
            tk.Label(total_dirty_frame, text=f"{rwd_value:,.0f} m³",
                    font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#95a5a6').pack(side='left', padx=10)
        
        # Outflows breakdown
        outflows_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        outflows_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(outflows_frame, text="🚰 Total Outflows",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
        
        for comp, val in result.outflows.components.items():
            comp_frame = tk.Frame(outflows_frame, bg='#34495e')
            comp_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(comp_frame, text=f"• {comp.replace('_', ' ').title()}:",
                    font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
            tk.Label(comp_frame, text=f"{val:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#e74c3c').pack(side='left', padx=10)
        
        tk.Frame(outflows_frame, bg='#7f8c8d', height=1).pack(fill=tk.X, padx=12, pady=5)
        total_out_frame = tk.Frame(outflows_frame, bg='#34495e')
        total_out_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        tk.Label(total_out_frame, text="TOTAL OUTFLOWS:",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
        tk.Label(total_out_frame, text=f"{result.outflows.total:,.0f} m³",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#e74c3c').pack(side='left', padx=10)
        
        # Storage
        storage_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        storage_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(storage_frame, text="🏗️ Storage Change",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
        
        for label, val in [("Opening Volume", result.storage.opening),
                           ("Closing Volume", result.storage.closing),
                           ("Net Change (ΔStorage)", result.storage.delta)]:
            st_frame = tk.Frame(storage_frame, bg='#34495e')
            st_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(st_frame, text=f"• {label}:",
                    font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5', width=25, anchor='w').pack(side='left')
            tk.Label(st_frame, text=f"{val:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#f39c12').pack(side='left', padx=10)
        tk.Label(storage_frame, text=f"Source: {result.storage.source}",
                font=('Segoe UI', 8, 'italic'), bg='#34495e', fg='#95a5a6').pack(anchor='w', padx=12, pady=(5, 10))

    def _update_storage_dams_display(self):
        """Display per-facility storage breakdown with drivers.
        Uses Extended Excel auto-calculation when available; falls back to DB-based
        facility balance otherwise. Sorted by Δ (most negative first).
        """
        if not hasattr(self, 'storage_dams_frame') or not self.storage_dams_frame.winfo_exists():
            return

        for w in self.storage_dams_frame.winfo_children():
            w.destroy()

        if not self.current_balance:
            return

        # Parse month
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        except Exception:
            return

        # Containers
        container = tk.Frame(self.storage_dams_frame, bg='#2c3e50')
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        canvas = tk.Canvas(container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        frame = tk.Frame(canvas, bg='#2c3e50')
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=frame, anchor='nw')
        # Ensure the inner frame width follows the canvas width for responsive layouts
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Header
        tk.Label(frame, text="🏗️ Storage & Dams — Per‑Facility Drivers",
                 font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='#e8eef5').pack(anchor='w', padx=15, pady=(15, 6))
        tk.Label(frame, text="Closing = Opening + Inflow + Rain + Seepage Gain − (Outflow + Evap + Abstraction + Seepage Loss)",
                 font=('Segoe UI', 9), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', padx=15, pady=(0, 10))

        # Inform users when required Excel parameters are missing (zero-defaults applied)
        try:
            audit = collect_inputs_audit(calc_date)
            legacy_headers = (audit.get('legacy_excel', {}) or {}).get('headers', [])
            relevant = {
                'Tonnes Milled',
                'Main decline dewatering',
                'North decline dewatering',
                'Merensky dewatering',
                'Plant BH sum',
                'MDGWA sum',
                'NDGWA sum',
                'MERGWA sum',
                'Groot Dwars',
                'Klein Dwars'
            }
            missing = []
            for h in legacy_headers:
                name = h.get('name')
                if name in relevant:
                    found = bool(h.get('found'))
                    val = h.get('value')
                    if (not found) or (val is None):
                        missing.append(name)
            info_frame = tk.Frame(frame, bg=('#f39c12' if missing else '#27ae60'), relief=tk.SOLID, borderwidth=1)
            info_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
            msg = (
                "⚠️ Excel data missing for: " + ", ".join(missing) + ". Zero-defaults applied for these inflows this month."
                if missing else
                "✅ All required Excel parameters for inflow categories are present this month."
            )
            tk.Label(info_frame, text=msg, font=('Segoe UI', 9, 'bold'), bg=info_frame['bg'], fg=('#000' if info_frame['bg']=='#f39c12' else '#fff'))\
                .pack(padx=12, pady=8, anchor='w')
        except Exception:
            # Non-critical; continue without the info banner
            pass

        # Build data from database calculator results
        facilities = {f['facility_code']: f for f in self.db.get_storage_facilities()}
        changes = self.current_balance.get('storage_change', {}).get('facilities', {})

        rows = []
        totals = {
            'opening': 0.0, 'inflow': 0.0, 'rain': 0.0, 'seep_gain': 0.0,
            'outflow': 0.0, 'evap': 0.0, 'abstr': 0.0, 'seep_loss': 0.0,
            'closing': 0.0, 'delta': 0.0
        }

        for code, rec in changes.items():
            meta = facilities.get(code, {})
            source = rec.get('source', 'Database')
            drivers = rec.get('drivers', {})

            opening = float(rec.get('opening', 0.0))
            closing = float(rec.get('closing', 0.0))
            delta = float(rec.get('change', closing - opening))

            # Use database-calculated drivers (from regional rainfall/evaporation + per-facility flows)
            inflow = float(drivers.get('inflow_manual', 0.0))
            outflow = float(drivers.get('outflow_manual', 0.0))
            rain = float(drivers.get('rainfall', 0.0))
            evap = float(drivers.get('evaporation', 0.0))
            abstr = float(drivers.get('abstraction', 0.0))
            seep_gain = float(drivers.get('seepage_gain', 0.0))
            seep_loss = float(drivers.get('seepage_loss', 0.0))

            rows.append({
                'code': code,
                'name': meta.get('facility_name', code),
                'opening': opening,
                'inflow': inflow,
                'rain': rain,
                'outflow': outflow,
                'evap': evap,
                'abstr': abstr,
                'seep_gain': seep_gain,
                'seep_loss': seep_loss,
                'closing': closing,
                'delta': delta,
                'source': source
            })

            totals['opening'] += opening
            totals['inflow'] += inflow
            totals['rain'] += rain
            totals['outflow'] += outflow
            totals['evap'] += evap
            totals['abstr'] += abstr
            totals['seep_gain'] += seep_gain
            totals['seep_loss'] += seep_loss
            totals['closing'] += closing
            totals['delta'] += delta

        # Sort by delta (most negative first)
        rows.sort(key=lambda r: r['delta'])

        # Table
        table_frame = tk.Frame(frame, bg='#2c3e50')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        cols = ('code','name','opening','inflow','rain','seep_gain','outflow','evap','abstr','seep_loss','closing','delta','source')
        tv = ttk.Treeview(table_frame, columns=cols, show='headings', height=min(18, max(8, len(rows)+2)))
        headings = {
            'code':'Code','name':'Facility','opening':'Opening',
            'inflow':'Inflow','rain':'Rain','seep_gain':'Seep. Gain','outflow':'Outflow','evap':'Evap',
            'abstr':'Abstraction','seep_loss':'Seep. Loss','closing':'Closing','delta':'Δ','source':'Source'
        }
        # Base widths used for auto-fit (only Facility column stretches)
        base_widths = {}
        for c in cols:
            anchor = 'e' if c in ('opening','inflow','rain','seep_gain','outflow','evap','abstr','seep_loss','closing','delta') else ('center' if c=='source' else 'w')
            width = 120 if c in ('opening','inflow','rain','seep_gain','outflow','evap','abstr','seep_loss','closing','delta') else (130 if c=='code' else 240 if c=='name' else 140)
            base_widths[c] = width
            tv.heading(c, text=headings[c], anchor=anchor)
            # Minimum widths and stretch behavior
            minw = 100 if c in ('opening','inflow','rain','seep_gain','outflow','evap','abstr','seep_loss','closing','delta') else (110 if c=='code' else 160 if c=='name' else 110)
            tv.column(c, anchor=anchor, width=width, minwidth=minw, stretch=(c == 'name'))

        for r in rows:
            tv.insert('', 'end', values=(
                r['code'], r['name'], f"{r['opening']:,.0f}", f"{r['inflow']:,.0f}", f"{r['rain']:,.0f}", f"{r['seep_gain']:,.0f}",
                f"{r['outflow']:,.0f}", f"{r['evap']:,.0f}", f"{r['abstr']:,.0f}", f"{r['seep_loss']:,.0f}", f"{r['closing']:,.0f}",
                f"{r['delta']:,.0f}", r['source']
            ))

        # Totals row
        tv.insert('', 'end', values=(
            'TOTAL','', f"{totals['opening']:,.0f}", f"{totals['inflow']:,.0f}", f"{totals['rain']:,.0f}", f"{totals['seep_gain']:,.0f}",
            f"{totals['outflow']:,.0f}", f"{totals['evap']:,.0f}", f"{totals['abstr']:,.0f}", f"{totals['seep_loss']:,.0f}", f"{totals['closing']:,.0f}",
            f"{totals['delta']:,.0f}", ''
        ), tags=('total',))

        tv.tag_configure('total', font=('Segoe UI', 10, 'bold'))

        # Add scrollbars to avoid clipping rightmost columns
        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=tv.yview)
        hsb = ttk.Scrollbar(table_frame, orient='horizontal', command=tv.xview)
        tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        # Use grid for reliable scrollbar placement
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        tv.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew', columnspan=1)

        # Auto-fit: keep fixed widths for numeric columns; stretch Facility to available space.
        def _autofit_columns(event=None):
            try:
                tv.update_idletasks()
                avail = max(tv.winfo_width() - 6, 320)
                # Sum of fixed columns (all except 'name')
                fixed_total = 0
                for c in cols:
                    if c != 'name':
                        fixed_total += base_widths[c]
                        tv.column(c, width=base_widths[c])
                # Remaining space goes to the Facility column; if negative, overflow triggers horizontal scrollbar
                name_min = int(tv.column('name', option='minwidth'))
                remaining = avail - fixed_total
                tv.column('name', width=max(name_min, remaining))
            except Exception:
                pass

        table_frame.bind('<Configure>', _autofit_columns)
        _autofit_columns()

        # Removed "Σ Abstraction to Plant" section per user request.
        
        # Add Pump Transfers Display section
        pump_transfers = self.current_balance.get('pump_transfers', {})
        self._display_pump_transfers(pump_transfers, frame)


    def _update_days_of_operation_display(self):
        """Display Days of Operation dashboard with data quality, KPIs, and storage runway chart.
        
        Critical threshold calculation:
        - Uses each facility's pump_stop_level (the level at which pumps cannot operate)
        - Dynamically weighted by surface area (or capacity if area not available)
        - Automatically adapts when facilities are added, removed, or deactivated
        - Example: If RWD has 10% pump_stop and PWD has 20%, the site-wide threshold
          will be weighted by their respective surface areas/capacities
        """
        if not hasattr(self, 'days_of_operation_frame') or not self.days_of_operation_frame.winfo_exists():
            return
        
        for widget in self.days_of_operation_frame.winfo_children():
            widget.destroy()
        
        if not self.current_balance:
            return
        
        # Get singleton utilities
        from utils.data_quality_checker import get_data_quality_checker
        from utils.optimization_engine import get_optimization_engine
        from ui.chart_utils import create_storage_runway_chart, embed_matplotlib_canvas
        
        quality_checker = get_data_quality_checker()
        optimizer = get_optimization_engine()
        
        # Parse current date
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        except Exception:
            return
        
        # Main container
        container = tk.Frame(self.days_of_operation_frame, bg='#2c3e50')
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scrollable area
        canvas = tk.Canvas(container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="⏳ Days of Operation — Water Runway Analysis",
                 font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        tk.Label(header_frame, text="Estimate how many days the mine can operate based on current water storage and consumption rates",
                 font=('Segoe UI', 9), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(0, 5))
        
        # KPI Cards Row
        kpi_container = tk.Frame(scrollable_frame, bg='#2c3e50')
        kpi_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Calculate KPIs
        try:
            # Get current storage and consumption from balance
            # NOTE: Use engine_result (BalanceEngine) for consistency with System Balance tab
            storage_data = self.current_balance.get('storage', {}) if self.current_balance else {}
            total_storage = storage_data.get('closing', 0.0)
            capacity = storage_data.get('capacity', 1000000.0)  # Default 1M m³ if not available

            # Surface-area weighted critical threshold using facility-specific pump_stop_level
            # Dynamically adapts to active facilities - no hardcoded values
            facilities = self.db.get_storage_facilities(active_only=True)
            default_pct = config.get('storage.critical_threshold_pct_default', 0.20)

            total_capacity = 0.0
            total_area = 0.0
            weighted_area_pct = 0.0
            weighted_cap_pct = 0.0
            
            for f in facilities:
                cap = float(f.get('total_capacity', 0) or 0.0)
                area = float(f.get('surface_area', 0) or 0.0)
                
                # Use facility's pump_stop_level (stored as %), convert to decimal
                # Falls back to config default if pump_stop_level is not set
                pump_stop = float(f.get('pump_stop_level') or (default_pct * 100))
                pct = pump_stop / 100.0
                
                total_capacity += cap
                weighted_cap_pct += cap * pct
                if area > 0:
                    total_area += area
                    weighted_area_pct += area * pct

            # Calculate site-wide threshold from weighted average
            site_pct = default_pct
            if total_area > 0:
                site_pct = weighted_area_pct / total_area
            elif total_capacity > 0:
                site_pct = weighted_cap_pct / total_capacity

            critical_threshold = site_pct * capacity

            # Use engine_result for outflows (same as System Balance tab for consistency)
            if self.engine_result:
                monthly_consumption = self.engine_result.outflows.total
            else:
                outflows = self.current_balance.get('outflows', {})
                monthly_consumption = outflows.get('total', 0.0)
            
            daily_consumption = monthly_consumption / 30.0 if monthly_consumption > 0 else 1.0  # Avoid division by zero

            # Calculate days remaining using usable storage above the critical threshold
            usable_storage = max(total_storage - critical_threshold, 0.0)
            days_remaining = usable_storage / daily_consumption if daily_consumption > 0 else 999

            # Calculate storage percentage
            storage_pct = (total_storage / capacity * 100.0) if capacity > 0 else 0.0
            
            # Determine status colors
            if days_remaining >= 60:
                days_color = '#28a745'  # Green
                days_status = 'Healthy'
            elif days_remaining >= 30:
                days_color = '#fd7e14'  # Orange
                days_status = 'Caution'
            else:
                days_color = '#dc3545'  # Red
                days_status = 'Critical'
            
            if storage_pct >= 70:
                storage_color = '#28a745'
            elif storage_pct >= 40:
                storage_color = '#fd7e14'
            else:
                storage_color = '#dc3545'
            
            # KPI 1: Days Remaining
            kpi1 = tk.Frame(kpi_container, bg=days_color, relief=tk.RAISED, borderwidth=2)
            kpi1.pack(side='left', fill='both', expand=True, padx=(0, 10))
            tk.Label(kpi1, text="Days of Operation", font=('Segoe UI', 9), bg=days_color, fg='#ffffff').pack(pady=(10, 2))
            tk.Label(kpi1, text=f"{days_remaining:.0f} days", font=('Segoe UI', 18, 'bold'), bg=days_color, fg='#ffffff').pack()
            tk.Label(kpi1, text=days_status, font=('Segoe UI', 9, 'italic'), bg=days_color, fg='#ffffff').pack(pady=(2, 10))
            
            # KPI 2: Current Storage
            kpi2 = tk.Frame(kpi_container, bg=storage_color, relief=tk.RAISED, borderwidth=2)
            kpi2.pack(side='left', fill='both', expand=True, padx=(0, 10))
            tk.Label(kpi2, text="Current Storage", font=('Segoe UI', 9), bg=storage_color, fg='#ffffff').pack(pady=(10, 2))
            tk.Label(kpi2, text=f"{total_storage:,.0f} m³", font=('Segoe UI', 14, 'bold'), bg=storage_color, fg='#ffffff').pack()
            tk.Label(kpi2, text=f"{storage_pct:.1f}% of capacity", font=('Segoe UI', 9, 'italic'), bg=storage_color, fg='#ffffff').pack(pady=(2, 10))
            
            # KPI 3: Daily Consumption
            kpi3 = tk.Frame(kpi_container, bg='#17a2b8', relief=tk.RAISED, borderwidth=2)
            kpi3.pack(side='left', fill='both', expand=True)
            tk.Label(kpi3, text="Daily Consumption", font=('Segoe UI', 9), bg='#17a2b8', fg='#ffffff').pack(pady=(10, 2))
            tk.Label(kpi3, text=f"{daily_consumption:,.0f} m³/day", font=('Segoe UI', 14, 'bold'), bg='#17a2b8', fg='#ffffff').pack()
            tk.Label(kpi3, text=f"{monthly_consumption:,.0f} m³/month", font=('Segoe UI', 9, 'italic'), bg='#17a2b8', fg='#ffffff').pack(pady=(2, 10))
            
        except Exception as e:
            logger.error(f"Failed to calculate KPIs: {e}", exc_info=True)
            days_remaining = 0
            total_storage = 0
            daily_consumption = 1
        
        # Storage Runway Chart
        try:
            chart_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
            
            # Calculate actual depletion point (when storage hits critical threshold)
            # Uses same calculation as Days of Operation: usable_storage = total_storage - critical_threshold
            depletion_days = int(days_remaining) + 5  # Add 5 days buffer for context
            
            # Create chart frame with duration selector
            chart_outer_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            chart_outer_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
            
            # Header with duration selector
            header_chart_frame = tk.Frame(chart_outer_frame, bg='#34495e')
            header_chart_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
            
            tk.Label(header_chart_frame, text="📊 Storage Depletion Projection",
                     font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(side='left')
            
            # Projection duration buttons
            button_frame = tk.Frame(header_chart_frame, bg='#34495e')
            button_frame.pack(side='right')
            
            # Store chart reference for updating
            chart_frames = {}
            current_projection_days = tk.IntVar(master=chart_frame, value=min(max(depletion_days, 30), 120))
            
            def update_projection(duration):
                """Regenerate chart with specified duration"""
                current_projection_days.set(duration)
                
                # Clear chart frame
                for widget in chart_frame.winfo_children():
                    if isinstance(widget, tk.Label) and 'days' in str(widget.cget('text')).lower():
                        continue  # Keep the duration label
                    widget.destroy()
                
                # Recalculate projection
                projection_days = list(range(duration + 1))
                storage_levels = []
                for day in range(duration + 1):
                    projected_storage = max(critical_threshold, total_storage - (daily_consumption * day))
                    storage_levels.append(projected_storage)
                
                # Regenerate chart
                try:
                    critical_pct = max(site_pct * 100.0, 0.0)
                    fig = create_storage_runway_chart(projection_days, storage_levels, capacity,
                                                    critical_threshold_pct=critical_pct,
                                                    empty_threshold_pct=0.0)
                    embed_matplotlib_canvas(chart_frame, fig, toolbar=False)
                except Exception as e:
                    logger.error(f"Failed to update chart: {e}")
            
            # Duration buttons
            for duration in [30, 60, 90, 120]:
                btn = ttk.Button(
                    button_frame,
                    text=f"{duration}d",
                    command=lambda d=duration: update_projection(d),
                    width=6
                )
                btn.pack(side='left', padx=2)
            
            # Chart container
            chart_frame = tk.Frame(chart_outer_frame, bg='#34495e')
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
            
            # Initial projection
            projection_days_count = min(max(depletion_days, 30), 120)
            projection_days = list(range(projection_days_count + 1))
            storage_levels = []
            for day in range(projection_days_count + 1):
                # Project total storage (not usable) - chart shows when we hit critical threshold
                projected_storage = max(critical_threshold, total_storage - (daily_consumption * day))
                storage_levels.append(projected_storage)
            
            # Create projection and pass percentage thresholds
            critical_pct = max(site_pct * 100.0, 0.0)
            warning_pct = max(critical_pct + 20.0, 40.0)
            thresholds_pct = {
                'critical': critical_pct,
                'warning': warning_pct,
                'safe': 70.0
            }

            fig = create_storage_runway_chart(projection_days, storage_levels, capacity, 
                                            critical_threshold_pct=thresholds_pct['critical'],
                                            empty_threshold_pct=0.0)
            embed_matplotlib_canvas(chart_frame, fig, toolbar=False)
            
        except Exception as e:
            logger.error(f"Failed to create storage runway chart: {e}", exc_info=True)
            tk.Label(chart_frame, text=f"Chart generation failed: {e}",
                     font=('Segoe UI', 9), bg='#34495e', fg='#e74c3c').pack(padx=10, pady=10)

    def _update_recycled_display(self):
        """Display Recycled Water (Dewatering + RWD) with totals and percentage.
        
        Percentage is calculated against Fresh + Dirty inflows (excluding TSF Return).
        This represents recycled water as a % of new water entering the system,
        not including water recycled from tailings storage.
        """
        if not hasattr(self, 'recycled_frame') or not self.recycled_frame.winfo_exists():
            return
        for widget in self.recycled_frame.winfo_children():
            widget.destroy()
        if not self.current_balance:
            return
        inflows = self.current_balance['inflows']
        
        # Calculate denominator: Fresh + Dirty (excluding TSF Return which is recycled)
        # Fresh = Surface + Groundwater + Rainfall + Ore Moisture + Underground (minus RWD)
        # Dirty = RWD only
        # Total for % = Fresh + Dirty (excludes TSF recycled return)
        fresh_total = (inflows.get('surface_water', 0.0) + 
                      inflows.get('groundwater', 0.0) + 
                      inflows.get('rainfall', 0.0) + 
                      inflows.get('ore_moisture', 0.0) + 
                      inflows.get('underground', 0.0))
        dirty_total = inflows.get('rwd_inflow', 0.0)
        denominator = fresh_total + dirty_total  # Fresh + Dirty, excludes TSF return
        
        dewatering = inflows.get('underground', 0.0)
        rwd = inflows.get('rwd_inflow', 0.0)
        recycled_total = dewatering + rwd
        recycled_pct = (recycled_total / denominator * 100.0) if denominator > 0 else 0.0

        main_container = tk.Frame(self.recycled_frame, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        canvas = tk.Canvas(main_container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        tk.Label(header_frame, text="♻️ Recycled Water",
                 font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        tk.Label(header_frame, text="Includes Dewatering (Underground) + RWD (Return Water Dam)",
                 font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))

        # Components table
        table_frame = ttk.LabelFrame(scrollable_frame, text="Components", padding=10)
        table_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        cols = ('component', 'volume', 'percent')
        tv = ttk.Treeview(table_frame, columns=cols, show='headings', height=4)
        tv.heading('component', text='Component')
        tv.heading('volume', text='Volume (m³)')
        tv.heading('percent', text='% of Total Inflows')
        tv.column('component', width=260, anchor='w')
        tv.column('volume', width=140, anchor='e')
        tv.column('percent', width=160, anchor='center')
        tv.insert('', 'end', values=('Underground Dewatering', f"{dewatering:,.0f}", f"{(dewatering/denominator*100.0) if denominator>0 else 0.0:.1f}%"))
        tv.insert('', 'end', values=('RWD (Return Water Dam)', f"{rwd:,.0f}", f"{(rwd/denominator*100.0) if denominator>0 else 0.0:.1f}%"))
        tv.insert('', 'end', values=('─'*40, '─'*12, '─'*8))
        tv.insert('', 'end', values=('TOTAL RECYCLED', f"{recycled_total:,.0f}", f"{recycled_pct:.1f}%"))
        tv.pack(fill=tk.X)

        # Metric cards
        metrics_frame = ttk.Frame(scrollable_frame)
        metrics_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        self.add_metric_card(metrics_frame, 'Recycled Total', f"{recycled_total:,.0f} m³", '#28a745', icon='♻️')
        self.add_metric_card(metrics_frame, 'Recycled % of Fresh + Dirty Inflows', f"{recycled_pct:.1f}%", '#17a2b8', icon='📊')

    def _update_quality_display(self):
        """Display data quality flags and notes."""
        if not hasattr(self, 'quality_frame') or not self.quality_frame.winfo_exists():
            return
        
        for widget in self.quality_frame.winfo_children():
            widget.destroy()
        
        if not self.engine_result:
            return
        
        result = self.engine_result
        flags_dict = result.flags.as_dict()
        
        main_container = tk.Frame(self.quality_frame, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        canvas = tk.Canvas(main_container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="📋 Data Quality & Assumptions",
                font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        tk.Label(header_frame, text="Transparency for auditors and regulators",
                font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))
        
        if not flags_dict:
            # No issues
            ok_frame = tk.Frame(scrollable_frame, bg='#27ae60', relief=tk.SOLID, borderwidth=2)
            ok_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
            tk.Label(ok_frame, text="✅ All data from measured sources - no quality issues detected.",
                    font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='#fff').pack(padx=12, pady=15)
        else:
            # Show flags
            for flag_key, flag_msg in flags_dict.items():
                flag_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
                flag_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
                
                icon = "⚠️" if "missing" in flag_key.lower() or "simulated" in flag_key.lower() else "ℹ️"
                tk.Label(flag_frame, text=f"{icon} {flag_key.replace('_', ' ').title()}",
                        font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#f39c12').pack(anchor='w', padx=12, pady=(8, 2))
                tk.Label(flag_frame, text=flag_msg,
                        font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5', wraplength=700, justify='left').pack(anchor='w', padx=12, pady=(0, 8))
    
    def _update_inputs_audit_display(self):
        """Display Inputs Audit for the selected month (read-only)."""
        if not hasattr(self, 'inputs_frame') or not self.inputs_frame.winfo_exists():
            return

        for widget in self.inputs_frame.winfo_children():
            widget.destroy()

        # Parse calculation date
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        except Exception:
            return

        audit = collect_inputs_audit(calc_date)

        # Main container with Flow Diagram theme
        main_container = tk.Frame(self.inputs_frame, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Scrollable area
        canvas = tk.Canvas(main_container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Header
        header = tk.Frame(scrollable_frame, bg='#2c3e50')
        header.pack(fill=tk.X, padx=15, pady=(15, 10))
        tk.Label(header, text="🧾 Inputs Audit", font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        tk.Label(header, text=f"Month: {audit.get('month', '-')}", font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))

        # Legacy Excel section
        legacy = audit.get('legacy_excel', {}) or {}
        legacy_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        legacy_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        tk.Label(legacy_frame, text="📑 Meter Readings (Legacy Excel)", font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(10, 5))
        path_txt = legacy.get('path') or '—'
        exists = bool(legacy.get('exists'))
        matched = legacy.get('matched_row_date') or '—'
        tk.Label(legacy_frame, text=f"Path: {path_txt}", font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12)
        tk.Label(legacy_frame, text=f"File Exists: {'Yes' if exists else 'No'}", font=('Segoe UI', 9), bg='#34495e', fg=('#27ae60' if exists else '#e74c3c')).pack(anchor='w', padx=12, pady=(0, 2))
        tk.Label(legacy_frame, text=f"Matched Row (month): {matched}", font=('Segoe UI', 9), bg='#34495e', fg='#e8eef5').pack(anchor='w', padx=12, pady=(0, 8))

        # Headers table
        headers = legacy.get('headers', [])
        table = ttk.Treeview(legacy_frame, columns=("header", "value", "status"), show='headings', height=max(3, len(headers)))
        table.heading('header', text='Header')
        table.heading('value', text='Value')
        table.heading('status', text='Status')
        table.column('header', width=220, anchor='w')
        table.column('value', width=150, anchor='e')
        table.column('status', width=140, anchor='center')
        for h in headers:
            name = h.get('name')
            val = h.get('value')
            found = bool(h.get('found'))
            status = 'Found' if found and (val is not None) else 'Missing'
            val_txt = f"{val:,.2f}" if isinstance(val, (int, float)) else (str(val) if val is not None else '—')
            table.insert('', 'end', values=(name, val_txt, status), tags=("ok" if status == 'Found' else "warn",))
        table.tag_configure('ok', foreground='#27ae60')
        table.tag_configure('warn', foreground='#e74c3c')
        table.pack(fill=tk.X, padx=12, pady=(0, 12))

        # Template/Extended Excel section removed per request
    
    def _update_flow_params_preview(self):
        """Update template balance check tabs (QA only)"""
        # Note: _update_balance_calculation_breakdown removed - balance check moved to Flow Diagram
        self._update_balance_check_summary()

    def _update_future_balance_placeholder(self):
        """Placeholder for future water balance calculation table."""
        # Check if frame still exists
        if not hasattr(self, 'future_balance_frame') or not self.future_balance_frame.winfo_exists():
            logger.warning("Future balance frame no longer exists, skipping update")
            return
        
        for widget in self.future_balance_frame.winfo_children():
            widget.destroy()
        
        # Main container with Flow Diagram theme
        container = tk.Frame(self.future_balance_frame, bg='#2c3e50')
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header
        header_frame = tk.Frame(container, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame,
                text="📈 Water Balance Calculation",
                font=('Segoe UI', 14, 'bold'),
                bg='#2c3e50', fg='#e8eef5').pack(anchor='w')
        
        # Info box
        info_frame = tk.Frame(container, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(info_frame,
                text="⏳  This dashboard will host water balance calculations once parameters are defined.",
                font=('Segoe UI', 9),
                bg='#34495e', fg='#e8eef5',
                wraplength=800, justify='left').pack(padx=12, pady=10)
        
        # Table frame
        table_frame = tk.Frame(container, bg='#2c3e50')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Styled table
        columns = ('metric', 'formula', 'value', 'unit')
        table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        table.heading('metric', text='Metric')
        table.heading('formula', text='Formula/Computation')
        table.heading('value', text='Value')
        table.heading('unit', text='Unit')
        table.column('metric', width=250, anchor='w')
        table.column('formula', width=300, anchor='w')
        table.column('value', width=120, anchor='e')
        table.column('unit', width=100, anchor='center')
        
        # Placeholder rows
        placeholder_data = [
            ('Metric 1', 'Formula pending', '-', 'm³'),
            ('Metric 2', 'Formula pending', '-', 'm³'),
            ('Metric 3', 'Formula pending', '-', 'm³'),
        ]
        
        for row in placeholder_data:
            table.insert('', 'end', values=row, tags=('pending',))
        
        table.tag_configure('pending', foreground='#95a5a6')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        table.pack(side='left', fill='both', expand=True)
    
    def _update_summary_display(self):
        """Update summary tab with clear water balance equation"""
        # Clear existing
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        if not self.current_balance:
            return
        balance = self.current_balance
        inflows = balance['inflows']
        outflows = balance['outflows']
        storage_change = balance['storage_change']['net_storage_change']
        closure_error = balance['closure_error_m3']
        fresh_inflows = inflows['total'] - inflows.get('tsf_return', 0)
        # Header
        ttk.Label(self.summary_frame, text=f"Water Balance Summary - {balance['calculation_date']}", font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        # Equation
        self.add_info_box(self.summary_frame, "Fresh Water IN − Total Outflows − Storage Change = Closure Error", icon="⚖️")

        # Missing-parameters banner (always show): includes Tonnes Milled and key inflow headers
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
            audit = collect_inputs_audit(calc_date)
            legacy_headers = (audit.get('legacy_excel', {}) or {}).get('headers', [])
            relevant = {
                'Tonnes Milled',
                'Main decline dewatering',
                'North decline dewatering',
                'Merensky dewatering',
                'Plant BH sum',
                'MDGWA sum',
                'NDGWA sum',
                'MERGWA sum',
                'Groot Dwars',
                'Klein Dwars'
            }
            missing = []
            for h in legacy_headers:
                name = h.get('name')
                if name in relevant:
                    found = bool(h.get('found'))
                    val = h.get('value')
                    if (not found) or (val is None):
                        missing.append(name)
            banner = tk.Frame(self.summary_frame, bg=('#f39c12' if missing else '#27ae60'), relief=tk.SOLID, borderwidth=1)
            banner.pack(fill=tk.X, padx=15, pady=(0, 12))
            msg = (
                "⚠️ Excel data missing for: " + ", ".join(missing) + ". Zero-defaults applied for these inflows this month."
                if missing else
                "✅ All required Excel parameters for inflow categories are present this month."
            )
            tk.Label(banner, text=msg, font=('Segoe UI', 9, 'bold'), bg=banner['bg'], fg=('#000' if banner['bg']=='#f39c12' else '#fff')).pack(padx=12, pady=8, anchor='w')
        except Exception:
            pass
        # Key Metrics
        metrics = [
            {"label": "Fresh Water Inflows", "value": f"{fresh_inflows:,.0f} m³", "color": "#28a745", "icon": "💧"},
            {"label": "Recycled Water (TSF)", "value": f"{inflows.get('tsf_return', 0):,.0f} m³", "color": "#17a2b8", "icon": "♻️"},
            {"label": "Total Outflows", "value": f"{outflows['total']:,.0f} m³", "color": "#dc3545", "icon": "🚰"},
            {"label": "Net Storage Change", "value": f"{storage_change:,.0f} m³", "color": "#007bff" if storage_change >= 0 else "#ffc107", "icon": "📊"},
            {"label": "Closure Error", "value": f"{closure_error:,.0f} m³", "color": "#dc3545" if abs(closure_error) > fresh_inflows * 0.05 else "#28a745", "icon": "⚠️"},
            {"label": "Closure Error %", "value": f"{balance['closure_error_percent']:.2f}%", "color": "#dc3545" if balance['closure_error_percent'] > 5.0 else "#28a745", "icon": "📈"},
            {"label": "Ore Processed", "value": f"{balance['ore_processed']:,.0f} t", "color": "#6c757d", "icon": "⛏️"},
            {"label": "Balance Status", "value": balance['balance_status'], "color": "#28a745" if balance['balance_status'] == 'CLOSED' else "#ffc107", "icon": "✅"},
        ]
        metrics_frame = ttk.Frame(self.summary_frame)
        metrics_frame.pack(fill=tk.X, pady=(0, 15))
        for m in metrics:
            self.add_metric_card(metrics_frame, m['label'], m['value'], m['color'], icon=m['icon'])
        # Water Efficiency
        recycling_rate = (inflows.get('tsf_return', 0) / inflows['total'] * 100) if inflows['total'] > 0 else 0
        water_intensity = (fresh_inflows / balance['ore_processed']) if balance['ore_processed'] > 0 else 0
        eff_frame = ttk.Frame(self.summary_frame)
        eff_frame.pack(fill=tk.X, pady=(0, 15))
        self.add_metric_card(eff_frame, "Recycling Rate", f"{recycling_rate:.1f}%", "#28a745" if recycling_rate > 50 else "#ffc107" if recycling_rate > 30 else "#dc3545", icon="♻️")
        self.add_metric_card(eff_frame, "Fresh Water Intensity", f"{water_intensity:.3f} m³/t", "#28a745" if water_intensity < 0.5 else "#007bff" if water_intensity < 1.0 else "#ffc107", icon="💧")
        # Status
        deficit_surplus = self.calculator.calculate_deficit_surplus(balance['calculation_date'])
        status_colors = {
            'surplus': '#28a745',
            'deficit': '#ffc107',
            'critical_deficit': '#dc3545',
            'overflow_risk': '#ff6b6b'
        }
        self.add_metric_card(self.summary_frame, "Status", deficit_surplus['message'], status_colors.get(deficit_surplus['status'], '#666'), icon="📌")
        # Closure error alert
        threshold = self.db.get_constant('BALANCE_ERROR_THRESHOLD') or 5.0
        if balance['closure_error_percent'] > threshold:
            self.add_info_box(self.summary_frame, f"⚠️ Closure error {balance['closure_error_percent']:.2f}% exceeds threshold {threshold:.1f}%\nReview: rainfall measurements, evaporation estimates, TSF return flow, meter calibrations")
    
    def _update_inflows_display(self):
        """Update inflows tab with clear categorization"""
        for widget in self.inflows_frame.winfo_children():
            widget.destroy()
        if not self.current_balance:
            return
        inflows = self.current_balance['inflows']
        tsf_return = inflows.get('tsf_return', 0)
        total_inflows = inflows['total']
        fresh_total = total_inflows - tsf_return
        # Info box
        self.add_info_box(self.inflows_frame, "Fresh Water Inflows = New water entering the system (used in water balance closure calculation)\nComponents marked ✓ are included in closure calculation | TSF return is recycled water (not fresh)", icon="💡")

        # Missing-parameters banner for inflows tab as well
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
            audit = collect_inputs_audit(calc_date)
            legacy_headers = (audit.get('legacy_excel', {}) or {}).get('headers', [])
            relevant = {
                'Tonnes Milled',
                'Main decline dewatering',
                'North decline dewatering',
                'Merensky dewatering',
                'Plant BH sum',
                'MDGWA sum',
                'NDGWA sum',
                'MERGWA sum',
                'Groot Dwars',
                'Klein Dwars'
            }
            missing = []
            for h in legacy_headers:
                name = h.get('name')
                if name in relevant:
                    found = bool(h.get('found'))
                    val = h.get('value')
                    if (not found) or (val is None):
                        missing.append(name)
            banner = tk.Frame(self.inflows_frame, bg=('#f39c12' if missing else '#27ae60'), relief=tk.SOLID, borderwidth=1)
            banner.pack(fill=tk.X, padx=15, pady=(0, 12))
            msg = (
                "⚠️ Excel data missing for: " + ", ".join(missing) + ". Zero-defaults applied for these inflows this month."
                if missing else
                "✅ All required Excel parameters for inflow categories are present this month."
            )
            tk.Label(banner, text=msg, font=('Segoe UI', 9, 'bold'), bg=banner['bg'], fg=('#000' if banner['bg']=='#f39c12' else '#fff')).pack(padx=12, pady=8, anchor='w')
        except Exception:
            pass
        # Fresh water sources treeview
        fresh_data = []
        fresh_sources = [
            ('Surface Water Sources', None, None, 'header'),
            ('  • Rivers & Streams', inflows.get('surface_water', 0), '✓ Fresh water', 'fresh'),
            ('  • Rainfall on facilities', inflows.get('rainfall', 0), '✓ Fresh water', 'fresh'),
            ('Underground Water', None, None, 'header'),
            ('  • Underground dewatering', inflows.get('underground', 0), '✓ Fresh water', 'fresh'),
            ('  • Groundwater boreholes', inflows.get('groundwater', 0), '✓ Fresh water', 'fresh'),
            ('Process Sources', None, None, 'header'),
            ('  • Ore moisture content', inflows.get('ore_moisture', 0), '✓ Fresh water', 'fresh'),
            ('  • Seepage gain', inflows.get('seepage_gain', 0), '✓ Fresh water', 'fresh'),
            ('Other Returns', None, None, 'header'),
            ('  • Plant returns (misc)', inflows.get('plant_returns', 0), '✓ Fresh water', 'fresh'),
            ('  • Returns to pit', inflows.get('returns_to_pit', 0), '✓ Fresh water', 'fresh'),
        ]
        for source, volume, status, tag in fresh_sources:
            if volume is None:
                fresh_data.append({"values": (source, '', '', ''), "tag": tag})
            else:
                pct = (volume / fresh_total * 100) if fresh_total > 0 else 0
                fresh_data.append({"values": (source, f"{volume:,.0f}", f"{pct:.1f}%", status), "tag": tag})
        fresh_data.append({"values": ('─' * 40, '─' * 15, '─' * 10, '─' * 20), "tag": 'separator'})
        fresh_data.append({"values": ('TOTAL FRESH WATER', f"{fresh_total:,.0f}", '100.0%', '✓ Used in closure'), "tag": 'total'})
        tag_configs = {
            'header': {'font': ('Segoe UI', 9, 'bold'), 'foreground': '#333'},
            'fresh': {'foreground': '#007bff'},
            'total': {'font': ('Segoe UI', 11, 'bold'), 'foreground': '#000', 'background': '#e8f4f8'},
            'separator': {'foreground': '#ccc'}
        }
        fresh_frame = ttk.LabelFrame(self.inflows_frame, text="💧 Fresh Water Sources (Used in Closure Calculation)", padding=10)
        fresh_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.add_treeview(fresh_frame, ('source', 'volume', 'percentage', 'status'), ['Water Source', 'Volume (m³)', '% of Fresh', 'Status'], fresh_data, tag_configs)
        # Recycled water treeview
        recycled_data = [
            {"values": ('TSF Return Water', f"{tsf_return:,.0f}", f"{(tsf_return / total_inflows * 100) if total_inflows > 0 else 0:.1f}%", 'ⓘ Recycled (not fresh)'), "tag": 'recycled'},
            {"values": ('─' * 40, '─' * 15, '─' * 10, '─' * 20), "tag": 'separator'},
            {"values": ('GRAND TOTAL (Fresh + Recycled)', f"{total_inflows:,.0f}", f"{(total_inflows/fresh_total*100):.1f}%" if fresh_total > 0 else '—', 'ⓘ Total circulation'), "tag": 'grand'}
        ]
        tag_configs_recycled = {
            'recycled': {'foreground': '#28a745', 'font': ('Segoe UI', 9, 'italic')},
            'separator': {'foreground': '#ccc'},
            'grand': {'font': ('Segoe UI', 10, 'bold'), 'foreground': '#666'}
        }
        recycled_frame = ttk.LabelFrame(self.inflows_frame, text="♻️ Recycled Water (Internal Circulation)", padding=10)
        recycled_frame.pack(fill=tk.BOTH, expand=True)
        self.add_treeview(recycled_frame, ('source', 'volume', 'percentage', 'status'), ['Water Source', 'Volume (m³)', '% of Gross', 'Status'], recycled_data, tag_configs_recycled)
        # Efficiency metrics
        metrics_frame = ttk.Frame(self.inflows_frame)
        metrics_frame.pack(fill=tk.X, pady=(15, 0))
        recycling_rate = (tsf_return / total_inflows * 100) if total_inflows > 0 else 0
        self.add_metric_card(metrics_frame, "Fresh Water", f"{fresh_total:,.0f} m³", "#007bff", icon="💧")
        self.add_metric_card(metrics_frame, "Recycled Water", f"{tsf_return:,.0f} m³", "#28a745", icon="♻️")
        self.add_metric_card(metrics_frame, "Recycling Rate", f"{recycling_rate:.1f}%", "#17a2b8", icon="📊")
        # Legend
        self.add_legend(self.inflows_frame, "Legend:  ✓ = Fresh water used in closure calculation  |  ⓘ = Recycled/reference only  |  ♻️ = Internal water recycling")
    
    def _update_outflows_display(self):
        """Update outflows tab with clear categorization"""
        for widget in self.outflows_frame.winfo_children():
            widget.destroy()
        if not self.current_balance:
            return
        outflows = self.current_balance['outflows']
        gross = outflows.get('plant_consumption_gross', 0)
        tsf_return = outflows.get('tsf_return', 0)
        net = outflows.get('plant_consumption_net', 0)
        tailings = outflows.get('tailings_retention', 0)
        product = outflows.get('product_moisture', 0)
        total = outflows['total']
        # Info box
        self.add_info_box(self.outflows_frame, "Total Outflows = Fresh water leaving the system (used in water balance closure calculation)\nComponents marked ✓ are included in closure calculation | Components marked ⓘ are shown for reference only", icon="💡")
        # Plant water flow treeview
        plant_data = [
            {"values": ('Gross Plant Circulation', f"{gross:,.0f}", 'ⓘ Reference only'), "tag": 'info'},
            {"values": ('  - TSF Return (recycled)', f"({tsf_return:,.0f})", 'ⓘ Internal recycling'), "tag": 'return'},
            {"values": ('= Net Plant Consumption', f"{net:,.0f}", '✓ Included in closure'), "tag": 'included'},
            {"values": ('    • Tailings retention', f"{tailings:,.0f}", 'Detail component'), "tag": 'detail'},
            {"values": ('    • Product moisture', f"{product:,.0f}", 'Detail component'), "tag": 'detail'}
        ]
        tag_configs_plant = {
            'info': {'foreground': '#666'},
            'return': {'foreground': '#28a745', 'font': ('Segoe UI', 9, 'italic')},
            'included': {'foreground': '#007bff', 'font': ('Segoe UI', 10, 'bold')},
            'detail': {'foreground': '#999', 'font': ('Segoe UI', 9)}
        }
        plant_frame = ttk.LabelFrame(self.outflows_frame, text="🏭 Plant Water Flow", padding=10)
        plant_frame.pack(fill=tk.X, pady=(0, 10))
        self.add_treeview(plant_frame, ('item', 'value', 'status'), ['Component', 'Volume (m³)', 'Status'], plant_data, tag_configs_plant)
        # Water balance components treeview
        included_items = [
            ('Net Plant Consumption', net, '✓ Included', 'included'),
            ('Auxiliary Operations', None, None, 'header'),
            ('  • Dust Suppression', outflows.get('dust_suppression', 0), '✓ Included', 'included'),
            ('  • Mining Operations', outflows.get('mining_consumption', 0), '✓ Included', 'included'),
            ('  • Domestic Use', outflows.get('domestic_consumption', 0), '✓ Included', 'included'),
            ('Environmental Losses', None, None, 'header'),
            ('  • Evaporation', outflows.get('evaporation', 0), '✓ Included', 'included'),
            ('  • Controlled Discharge', outflows.get('discharge', 0), '✓ Included', 'included'),
        ]
        balance_data = []
        for component, volume, status, tag in included_items:
            if volume is None:
                balance_data.append({"values": (component, '', '', ''), "tag": tag})
            else:
                pct = (volume / total * 100) if total > 0 else 0
                balance_data.append({"values": (component, f"{volume:,.0f}", f"{pct:.1f}%", status), "tag": tag})
        balance_data.append({"values": ('─' * 40, '─' * 15, '─' * 10, '─' * 20), "tag": 'separator'})
        balance_data.append({"values": ('TOTAL OUTFLOWS', f"{total:,.0f}", '100.0%', '✓ Used in closure'), "tag": 'total'})
        balance_data.append({"values": ('', '', '', ''), "tag": 'separator'})
        seepage = outflows.get('seepage_loss', 0)
        balance_data.append({"values": ('Seepage Loss', f"{seepage:,.0f}", '—', '⚠️ Affects storage'), "tag": 'excluded'})
        tag_configs_balance = {
            'header': {'font': ('Segoe UI', 9, 'bold'), 'foreground': '#333'},
            'included': {'foreground': '#007bff'},
            'total': {'font': ('Segoe UI', 11, 'bold'), 'foreground': '#000', 'background': '#e8f4f8'},
            'excluded': {'foreground': '#ffc107', 'font': ('Segoe UI', 9, 'italic')},
            'separator': {'foreground': '#ccc'}
        }
        balance_frame = ttk.LabelFrame(self.outflows_frame, text="⚖️ Total Outflows (Water Balance Closure)", padding=10)
        balance_frame.pack(fill=tk.BOTH, expand=True)
        self.add_treeview(balance_frame, ('component', 'volume', 'percentage', 'status'), ['Component', 'Volume (m³)', '% of Total', 'Status'], balance_data, tag_configs_balance)
        # Legend
        self.add_legend(self.outflows_frame, "Legend:  ✓ = Included in water balance closure calculation  |  ⓘ = Reference/informational  |  ⚠️ = Excluded (affects storage instead)")
    
    def _update_storage_display(self):
        """Update storage tab"""
        for widget in self.storage_frame.winfo_children():
            widget.destroy()
        if not self.current_balance:
            return
        storage = self.current_balance['storage']
        # Storage security metrics
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
            security = self.calculator.calculate_storage_security(calc_date)
        except:
            security = None
        if security:
            metrics = [
                {"label": "Days of Operation Cover", "value": f"{security.get('days_cover', 0):.1f} days", "color": "#007bff", "icon": "📅"},
                {"label": "Days to Minimum Level", "value": f"{security.get('days_to_minimum', 0):.1f} days", "color": "#ffc107", "icon": "⏱️"},
                {"label": "Daily Consumption", "value": f"{security.get('daily_consumption_m3', 0):.1f} m³/day", "color": "#6c757d", "icon": "📊"},
                {"label": "Security Status", "value": security.get('security_status', 'unknown').upper(), "color": self._get_security_color(security.get('security_status', 'unknown')), "icon": "🔒"}
            ]
            metrics_frame = ttk.Frame(self.storage_frame)
            metrics_frame.pack(fill=tk.X, pady=(0, 10))
            for m in metrics:
                self.add_metric_card(metrics_frame, m['label'], m['value'], m['color'], icon=m['icon'])
        # Storage statistics
        calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        stats = [
            {"label": "Total Capacity", "value": f"{storage['total_capacity']:,.0f} m³", "color": "#007bff", "icon": "🏗️"},
            {"label": f"Opening Volume ({calc_date.strftime('%b %Y')})", "value": f"{storage['current_volume']:,.0f} m³", "color": "#28a745", "icon": "💧"},
            {"label": "Available Capacity", "value": f"{storage['available_capacity']:,.0f} m³", "color": "#6c757d", "icon": "📦"},
            {"label": "Utilization (Start)", "value": f"{storage['utilization_percent']:.1f}%", "color": "#ffc107", "icon": "📊"}
        ]
        stats_frame = ttk.Frame(self.storage_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        for s in stats:
            self.add_metric_card(stats_frame, s['label'], s['value'], s['color'], icon=s['icon'])
        # Facilities treeview with data source indicators
        facilities = self.db.get_storage_facilities()
        storage_changes = self.current_balance.get('storage_change', {}).get('facilities', {})
        facilities_data = []
        for f in facilities:
            util = (f.get('current_volume', 0) / f.get('total_capacity', 1) * 100)
            code = f['facility_code']
            # Check data source from storage_change calculations
            source = storage_changes.get(code, {}).get('source', 'Database')
            source_icon = '📊' if source == 'Excel' else '💾'
            source_label = f"{source_icon} {source}"
            facilities_data.append({"values": (
                f['facility_code'],
                f['facility_name'],
                f"{f.get('current_volume', 0):,.0f}",
                f"{f.get('total_capacity', 0):,.0f}",
                f"{util:.1f}%",
                source_label
            )})
        facilities_frame = ttk.LabelFrame(self.storage_frame, text="Storage Facilities", padding=10)
        facilities_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        self.add_info_box(facilities_frame, "ℹ️ Volumes shown are OPENING balances (start of month). 📊 = Excel data used | 💾 = Database fallback used", icon="💡")
        self.add_treeview(facilities_frame, ('code', 'name', 'volume', 'capacity', 'utilization', 'source'), ['📋 Code', '🏭 Facility Name', '💧 Opening Volume (m³)', '📏 Capacity (m³)', '📊 Util. %', '📍 Data Source'], facilities_data, {})
        
        # Pump Transfers Display (always show)
        pump_transfers = self.current_balance.get('pump_transfers', {})
        self._display_pump_transfers(pump_transfers)
    
    def _display_pump_transfers(self, pump_transfers, parent_frame=None):
        """Display automatic pump transfers and configured connections
        
        Args:
            pump_transfers: Dict of facility transfers from calculator
            parent_frame: Parent frame to pack into (default: self.storage_frame for backward compat)
        """
        if parent_frame is None:
            parent_frame = self.storage_frame
            
        logger.info(f"🔧 _display_pump_transfers called with {len(pump_transfers) if pump_transfers else 0} facilities")
        transfers_frame = ttk.LabelFrame(parent_frame, text="⚙️ Automatic Pump Transfers & Connections", padding=10)
        transfers_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        
        # Header
        self.add_info_box(
            transfers_frame,
            "Configured connections (where water can go) and actual transfers. Transfers happen when source ≥ pump_start_level. Shows transfer volume even if 0 m³.",
            icon="🔄"
        )
        
        # If no transfers configured
        if not pump_transfers:
            no_transfers_label = tk.Label(
                transfers_frame,
                text="ℹ️ No pump connections configured yet. Add connections in Storage Facilities to enable automatic transfers.",
                font=('Segoe UI', 9),
                fg='#5d6d7b',
                bg='#f5f6fa',
                wraplength=500,
                justify='left',
                padx=10,
                pady=10
            )
            no_transfers_label.pack(fill='x', padx=5, pady=5)
            return
        
        # Transfer details for each facility
        for facility_code, transfer_data in pump_transfers.items():
            current_level_pct = transfer_data['current_level_pct']
            pump_start = transfer_data['pump_start_level']
            is_at_pump_start = transfer_data['is_at_pump_start']
            transfers = transfer_data.get('transfers', [])
            
            # Facility header
            fac_frame = tk.Frame(transfers_frame, bg='#f5f6fa', relief='solid', borderwidth=1)
            fac_frame.pack(fill=tk.X, pady=8, padx=5)
            
            # Status indicator
            status = "✓ Ready to Transfer" if is_at_pump_start else "✗ Below Pump Start"
            status_color = '#27ae60' if is_at_pump_start else '#e74c3c'
            
            header_info = (
                f"  {facility_code}  |  "
                f"Level: {current_level_pct:.1f}%  |  "
                f"Pump Start: {pump_start:.1f}%  |  "
                f"{status}"
            )
            
            header_label = tk.Label(
                fac_frame,
                text=header_info,
                font=('Segoe UI', 10, 'bold'),
                bg='#f5f6fa',
                fg=status_color,
                anchor='w',
                padx=10,
                pady=8
            )
            header_label.pack(fill=tk.X)
            
            # Show configured connections (even if no transfers happened)
            if transfers:
                # Show transfers that happened
                for transfer in transfers:
                    transfer_frame = tk.Frame(transfers_frame, bg='#e8f5e9', relief='solid', borderwidth=1)
                    transfer_frame.pack(fill=tk.X, pady=2, padx=20)
                    
                    transfer_text = (
                        f"  ➜ {transfer['destination']:12} (Priority {transfer['priority']})  |  "
                        f"Volume: {transfer['volume_m3']:>10,.0f} m³  |  "
                        f"Dest: {transfer['destination_level_before']:>5.1f}% → {transfer['destination_level_after']:>5.1f}%"
                    )
                    
                    transfer_label = tk.Label(
                        transfer_frame,
                        text=transfer_text,
                        font=('Segoe UI', 9),
                        bg='#e8f5e9',
                        fg='#1b5e20',
                        anchor='w',
                        padx=10,
                        pady=5
                    )
                    transfer_label.pack(fill=tk.X)
            else:
                # No transfers - show why
                if not is_at_pump_start:
                    reason_frame = tk.Frame(transfers_frame, bg='#fff3cd', relief='solid', borderwidth=1)
                    reason_frame.pack(fill=tk.X, pady=2, padx=20)
                    reason_label = tk.Label(
                        reason_frame,
                        text=f"  ℹ️ No transfers - facility level {current_level_pct:.1f}% is below pump_start_level {pump_start:.1f}%",
                        font=('Segoe UI', 9),
                        bg='#fff3cd',
                        fg='#856404',
                        anchor='w',
                        padx=10,
                        pady=5
                    )
                    reason_label.pack(fill=tk.X)
                else:
                    reason_frame = tk.Frame(transfers_frame, bg='#fff3cd', relief='solid', borderwidth=1)
                    reason_frame.pack(fill=tk.X, pady=2, padx=20)
                    reason_label = tk.Label(
                        reason_frame,
                        text=f"  ℹ️ No active transfers - check facility connections or all destinations are full",
                        font=('Segoe UI', 9),
                        bg='#fff3cd',
                        fg='#856404',
                        anchor='w',
                        padx=10,
                        pady=5
                    )
                    reason_label.pack(fill=tk.X)
    
    def _get_security_color(self, status):
        """Get color for security status"""
        status_colors = {
            'excellent': '#28a745',
            'good': '#007bff',
            'adequate': '#17a2b8',
            'low': '#ffc107',
            'critical': '#dc3545'
        }
        return status_colors.get(status.lower(), '#666666')
    
    def _export_to_pdf(self, filename, calc_date, ore_tonnes):
        """Export calculation results to professional PDF report"""
        from utils.pdf_report_generator import WaterBalanceReportGenerator
        from pathlib import Path
        
        # Prepare calculation data for PDF
        balance = self.current_balance
        inflows = balance['inflows']
        outflows = balance['outflows']
        storage = balance['storage']
        
        # Get logo path if available
        logo_path = None
        assets_dir = Path(__file__).parent.parent.parent / "assets" / "icons"
        if assets_dir.exists():
            # Look for logo file
            for ext in ['.png', '.jpg', '.jpeg']:
                logo_file = assets_dir / f"logo{ext}"
                if logo_file.exists():
                    logo_path = str(logo_file)
                    break
        
        # Prepare calculation data structure
        calculation_data = {
            'month': calc_date.strftime('%B %Y'),
            'calculation_date': datetime.now(),
            'inputs': {
                'tonnes_milled': ore_tonnes or 0,
                'rainfall': inflows.get('rainfall', 0),
                'evaporation': outflows.get('evaporation', 0),
            },
            'inflows': {
                'surface_water': inflows.get('surface_water', 0),
                'rainfall': inflows.get('rainfall', 0),
                'underground': inflows.get('underground', 0),
                'groundwater': inflows.get('groundwater', 0),
                'ore_moisture': inflows.get('ore_moisture', 0),
                'seepage_gain': inflows.get('seepage_gain', 0),
                'plant_returns': inflows.get('plant_returns', 0),
                'returns_to_pit': inflows.get('returns_to_pit', 0),
                'tsf_return': inflows.get('tsf_return', 0),
                'fresh_total': inflows['total'] - inflows.get('tsf_return', 0),
                'total': inflows['total'],
            },
            'outflows': {
                'plant_consumption_gross': outflows.get('plant_consumption_gross', 0),
                'tsf_return': outflows.get('tsf_return', 0),
                'plant_consumption_net': outflows.get('plant_consumption_net', 0),
                'tailings_retention': outflows.get('tailings_retention', 0),
                'product_moisture': outflows.get('product_moisture', 0),
                'dust_suppression': outflows.get('dust_suppression', 0),
                'mining_consumption': outflows.get('mining_consumption', 0),
                'domestic_consumption': outflows.get('domestic_consumption', 0),
                'evaporation': outflows.get('evaporation', 0),
                'discharge': outflows.get('discharge', 0),
                'seepage_loss': outflows.get('seepage_loss', 0),
                'total': outflows['total'],
            },
            'storage_results': [],
            'summary': {
                'total_opening': storage.get('current_volume', 0),
                'fresh_inflow': inflows['total'] - inflows.get('tsf_return', 0),
                'recycled_inflow': inflows.get('tsf_return', 0),
                'total_inflow': inflows['total'],
                'total_outflow': outflows['total'],
                'net_storage_change': balance['storage_change']['net_storage_change'],
                'total_closing': storage.get('current_volume', 0) + balance['storage_change']['net_storage_change'],
                'closure_error_m3': balance['closure_error_m3'],
                'closure_error_percent': balance['closure_error_percent'],
            },
            'constants': {
                'RAINFALL_FACTOR': self.calculator.get_constant('RAINFALL_FACTOR', 0.85),
            }
        }
        
        # Add storage facility details
        facilities = self.db.get_storage_facilities()
        storage_changes = balance.get('storage_change', {}).get('facilities', {})
        
        # Calculate storage statistics
        try:
            security = self.calculator.calculate_storage_security(calc_date)
        except:
            security = None
        
        for facility in facilities:
            code = facility['facility_code']
            change_data = storage_changes.get(code, {})
            
            calculation_data['storage_results'].append({
                'facility_code': code,
                'facility_name': facility['facility_name'],
                'opening_volume': facility.get('current_volume', 0),
                'inflow_total': change_data.get('inflow', 0),
                'outflow_total': change_data.get('outflow', 0),
                'closing_volume': facility.get('current_volume', 0) + change_data.get('net_change', 0),
                'volume_change': change_data.get('net_change', 0),
                'level_percent': (facility.get('current_volume', 0) / facility.get('total_capacity', 1) * 100) if facility.get('total_capacity', 0) > 0 else 0,
                'total_capacity': facility.get('total_capacity', 0),
            })
        
        # Add storage statistics to calculation data
        calculation_data['storage_statistics'] = {
            'total_capacity': storage.get('total_capacity', 0),
            'current_volume': storage.get('current_volume', 0),
            'available_capacity': storage.get('available_capacity', 0),
            'utilization_percent': storage.get('utilization_percent', 0),
            'days_cover': security.get('days_cover', 0) if security else 0,
            'days_to_minimum': security.get('days_to_minimum', 0) if security else 0,
            'daily_consumption': security.get('daily_consumption_m3', 0) if security else 0,
            'security_status': security.get('security_status', 'unknown') if security else 'unknown',
        }
        
        # Generate PDF
        generator = WaterBalanceReportGenerator(
            company_name="Water Balance Management System",
            logo_path=logo_path
        )
        
        generator.generate_calculation_report(filename, calculation_data)
        logger.info(f"PDF report exported: {filename}")
    
    def _save_calculation(self):
        """Save current calculation to database and/or export to PDF"""
        if not self.current_balance:
            messagebox.showwarning("No Calculation", "Please calculate the balance first.")
            return
        
        # Show dialog to select save option
        save_dialog = tk.Toplevel(self.parent)
        save_dialog.title("Save Calculation")
        save_dialog.geometry("450x280")
        save_dialog.transient(self.parent)
        save_dialog.grab_set()
        
        # Center dialog
        save_dialog.update_idletasks()
        x = (save_dialog.winfo_screenwidth() // 2) - (save_dialog.winfo_width() // 2)
        y = (save_dialog.winfo_screenheight() // 2) - (save_dialog.winfo_height() // 2)
        save_dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(save_dialog, padding=15)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="💾 Save Calculation Results", 
                 font=('Segoe UI', 14, 'bold')).pack()
        ttk.Label(header_frame, text="Choose how to save your water balance calculation",
                 font=('Segoe UI', 9), foreground='#666').pack(pady=(5, 0))
        
        ttk.Separator(save_dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Options frame
        options_frame = ttk.Frame(save_dialog, padding=(15, 5))
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        save_option = tk.StringVar(value="both")
        
        ttk.Radiobutton(options_frame, text="📊 Save to Database Only", 
                       variable=save_option, value="database",
                       style='TRadiobutton').pack(anchor=tk.W, pady=8)
        ttk.Label(options_frame, text="Store calculation in database for tracking and analysis",
                 font=('Segoe UI', 8), foreground='#666').pack(anchor=tk.W, padx=(25, 0))
        
        ttk.Radiobutton(options_frame, text="📄 Export to PDF Only", 
                       variable=save_option, value="pdf",
                       style='TRadiobutton').pack(anchor=tk.W, pady=8)
        ttk.Label(options_frame, text="Generate professional PDF report for documentation",
                 font=('Segoe UI', 8), foreground='#666').pack(anchor=tk.W, padx=(25, 0))
        
        ttk.Radiobutton(options_frame, text="💾 Both (Database + PDF)", 
                       variable=save_option, value="both",
                       style='TRadiobutton').pack(anchor=tk.W, pady=8)
        ttk.Label(options_frame, text="Save to database and export professional PDF report",
                 font=('Segoe UI', 8), foreground='#666').pack(anchor=tk.W, padx=(25, 0))
        
        # Buttons
        button_frame = ttk.Frame(save_dialog, padding=15)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        def on_save():
            option = save_option.get()
            save_dialog.destroy()
            
            try:
                calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
                ore_tonnes = None
                
                results = []
                
                # Save to database
                if option in ("database", "both"):
                    # Check if duplicate exists
                    existing_id = self.calculator._check_duplicate_calculation(calc_date, ore_tonnes or 0)
                    
                    if existing_id:
                        # Duplicate found - ask user if they want to replace
                        replace = messagebox.askyesno(
                            "Duplicate Found",
                            f"A calculation for {calc_date} already exists (ID: {existing_id}).\n\n"
                            "Do you want to replace it with the new calculation?\n\n"
                            "• Yes: Replace old calculation and update storage volumes\n"
                            "• No: Keep existing calculation"
                        )
                        
                        if replace:
                            # Delete old calculation and save new one
                            self.db.execute_update("DELETE FROM calculations WHERE calc_id = ?", (existing_id,))
                            calc_id = self.calculator.save_calculation(calc_date, ore_tonnes, persist_storage=True)
                            results.append(f"✅ Replaced existing calculation (new ID: {calc_id})\n"
                                         f"   Storage volumes updated to {calc_date}")
                        else:
                            results.append(f"ℹ️  Kept existing calculation (ID: {existing_id})\n"
                                         f"   No changes made")
                    else:
                        # No duplicate - save normally with volume persistence
                        calc_id = self.calculator.save_calculation(calc_date, ore_tonnes, persist_storage=True)
                        results.append(f"✅ Saved to database (ID: {calc_id})\n"
                                     f"   Storage volumes updated to {calc_date}")
                
                # Export to PDF
                if option in ("pdf", "both"):
                    from tkinter import filedialog
                    default_filename = f"Water_Balance_{calc_date.strftime('%Y%m')}.pdf"
                    pdf_path = filedialog.asksaveasfilename(
                        title="Save PDF Report",
                        defaultextension=".pdf",
                        initialfile=default_filename,
                        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
                    )
                    
                    if pdf_path:
                        self._export_to_pdf(pdf_path, calc_date, ore_tonnes)
                        results.append(f"✅ PDF exported to:\n{pdf_path}")
                
                if results:
                    messagebox.showinfo("Success", "\n\n".join(results))
                    
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save calculation:\n{str(e)}")
                logger.error(f"Save calculation error: {e}", exc_info=True)
        
        ttk.Button(button_frame, text="✅ Save", command=on_save,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=save_dialog.destroy).pack(side=tk.RIGHT)

    def refresh_data(self):
        """Refresh module data"""
        self._show_placeholder()

    def _on_calc_date_change(self):
        """Handle date changes whether via calendar selection or manual typing."""
        # Only act if widget constructed (defensive) and date looks valid
        if not self.calc_date_var.get():
            return
        try:
            datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d')
        except Exception:
            return  # ignore incomplete typing until valid
        self._load_manual_inputs()
    
    def _toggle_auto_save(self):
        """Toggle auto-save feature and persist to config."""
        enabled = self.auto_save_var.get()
        config.set('features.auto_save_calculation', enabled)
        status = "enabled" if enabled else "disabled"
        logger.info(f"Auto-save {status} - storage volumes will {'be persisted' if enabled else 'NOT be persisted'} after calculations")

    def _get_calc_date_obj(self) -> Optional[date]:
        """Return calc date as date or None if invalid."""
        if not self.calc_date_var:
            return None
        try:
            return datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        except Exception:
            return None


