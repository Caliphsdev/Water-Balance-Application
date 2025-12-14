"""
Calculations Module
Water balance calculations and projections interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import calendar
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.water_balance_calculator import WaterBalanceCalculator
from utils.excel_timeseries import get_default_excel_repo
from utils.app_logger import logger
from utils.template_data_parser import get_template_parser
from utils.balance_check_engine import get_balance_check_engine
from ui.area_exclusion_dialog import AreaExclusionDialog


class CalculationsModule:
    """Water balance calculations interface"""

    # === UI HELPER FUNCTIONS ===
    def add_metric_card(self, parent, label, value, color, icon=None):
        frame = ttk.LabelFrame(parent, text=f"{icon or ''} {label}".strip(), padding=12)
        frame.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.BOTH, expand=True)
        value_label = tk.Label(frame, text=value, font=('Segoe UI', 15, 'bold'), fg=color)
        value_label.pack()
        return frame

    def add_info_box(self, parent, text, icon=None):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 15))
        info_text = tk.Text(frame, height=3, wrap=tk.WORD, font=('Segoe UI', 9), relief=tk.FLAT, background='#f0f0f0', borderwidth=0)
        info_text.pack(fill=tk.X)
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
        self.ore_tonnes_var = None
        self.current_balance = None
        self.year_var = None
        self.month_var = None

    def load(self):
        """Load the calculations module"""
        if self.main_frame:
            self.main_frame.destroy()

        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

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
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="⚖️ Water Balance Calculations", 
                         font=('Segoe UI', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        info = ttk.Label(header_frame, 
                        text="📊 Calculate water balance using TRP formulas",
                        font=('Segoe UI', 9),
                        foreground='#666')
        info.pack(side=tk.LEFT, padx=(20, 0))
    
    def _create_input_section(self):
        """Create input controls"""
        input_frame = ttk.LabelFrame(self.main_frame, text="⚙️ Calculation Parameters", 
                                    padding=15)
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Date selection (Month/Year selectors for performance, no tkcalendar)
        date_frame = ttk.Frame(input_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="📅 Calculation Month:", width=18).pack(side=tk.LEFT, padx=(0, 10))
        
        self.calc_date_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        
        # Determine default month/year from Excel latest date or today
        try:
            excel_repo = get_default_excel_repo()
            latest_date = excel_repo.get_latest_date()
        except Exception:
            latest_date = None
        base_date = latest_date or date.today()
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
        
        # Compose an actual date as last day of selected month
        def update_calc_date_var(*_):
            try:
                y = int(self.year_var.get())
                m = list(calendar.month_abbr).index(self.month_var.get())
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
        
        # Ore tonnage
        ttk.Label(date_frame, text="⛏️ Ore Processed (tonnes):", width=22).pack(side=tk.LEFT, padx=(0, 10))
        
        default_ore = self.calculator.get_constant('monthly_ore_processing', 350000.0)
        self.ore_tonnes_var = tk.StringVar(value=str(int(default_ore)))
        self.ore_entry = ttk.Entry(date_frame, textvariable=self.ore_tonnes_var, width=15)
        self.ore_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Source indicator label removed for cleaner UI
        
        # Calculate button
        calc_btn = ttk.Button(date_frame, text="🔢 Calculate Balance", 
                             command=self._calculate_balance,
                             style='Accent.TButton')
        calc_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Save button
        save_btn = ttk.Button(date_frame, text="💾 Save Calculation", 
                             command=self._save_calculation)
        save_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Area Exclusions button
        exclusions_btn = ttk.Button(date_frame, text="⚙️ Area Exclusions",
                                   command=self._show_exclusion_manager)
        exclusions_btn.pack(side=tk.LEFT, padx=(10, 0))


        # Event bindings
        self.ore_entry.bind("<KeyRelease>", lambda e: self._mark_manual_override())

        # Initial prefill after building UI
        self._prefill_ore_tonnage()
    
    def _create_results_section(self):
        """Create results display"""
        # Create notebook for organized display with Flow Diagram theme
        notebook_frame = ttk.Frame(self.main_frame)
        notebook_frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(notebook_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Flow Diagram Parameters (pending wiring)
        self.flow_params_frame = ttk.Frame(notebook)
        notebook.add(self.flow_params_frame, text="🧭 Flow Diagram Parameters")

        # Tab 2: Future Water Balance Calc (placeholder)
        self.future_balance_frame = ttk.Frame(notebook)
        notebook.add(self.future_balance_frame, text="📈 Water Balance Calculation")
        """Show initial placeholder prompting user to run calculation on demand"""
        frames_to_clear = [
            getattr(self, 'flow_params_frame', None),
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
                          bg='#2c3e50', fg='#ecf0f1')
            msg.pack(pady=40)
    
    def _calculate_balance(self):
        """Perform water balance calculation"""
        import time
        calc_start = time.perf_counter()
        logger.info("⏱️  Calculations: on-demand run started")
        
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
            ore_tonnes = float(self.ore_tonnes_var.get()) if self.ore_tonnes_var.get() else None
            
            # Calculate balance
            balance_calc_start = time.perf_counter()
            self.current_balance = self.calculator.calculate_water_balance(calc_date, ore_tonnes)
            logger.info(f"  ✓ Balance calculation: {(time.perf_counter() - balance_calc_start)*1000:.0f}ms")
            
            # Calculate balance check from templates
            check_start = time.perf_counter()
            self.balance_engine.calculate_balance()
            logger.info(f"  ✓ Balance check engine: {(time.perf_counter() - check_start)*1000:.0f}ms")
            
            # Update displays
            ui_start = time.perf_counter()
            self._update_flow_params_preview()
            self._update_future_balance_placeholder()
            logger.info(f"  ✓ UI update: {(time.perf_counter() - ui_start)*1000:.0f}ms")
            
            total_elapsed = (time.perf_counter() - calc_start) * 1000
            logger.info(f"✅ Calculations completed in {total_elapsed:.0f}ms")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate balance:\n{str(e)}")
            logger.error(f"Calculation error: {e}", exc_info=True)
    
    
    def _update_balance_check_summary(self):
        """Update balance check summary tab with overall water balance"""
        # Clear existing
        for widget in self.balance_summary_frame.winfo_children():
            widget.destroy()
        
        metrics = self.balance_engine.get_metrics()
        if not metrics:
            return
        
        excluded_areas = self.balance_engine.get_excluded_areas()
        
        # Header
        header_text = "⚖️ Water Balance Check (Overall)"
        if excluded_areas:
            header_text += f" - {len(excluded_areas)} area(s) excluded"
        
        ttk.Label(self.balance_summary_frame, 
                 text=header_text, 
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # Exclusions info if any
        if excluded_areas:
            self.add_info_box(self.balance_summary_frame,
                             f"⚠️ Excluded areas: {', '.join(excluded_areas)}\n"
                             "These areas are NOT included in balance calculations below.",
                             icon="⚙️")
        
        # Info box explaining the calculation
        self.add_info_box(self.balance_summary_frame,
                         "Balance Equation: Total Inflows − Recirculation − Total Outflows = Balance Difference\n"
                         "Error %: (Balance Difference ÷ Total Inflows) × 100\n"
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
        
        # Breakdown table
        breakdown_data = [
            {"values": ("Total Inflows (Fresh + Recycled)", f"{metrics.total_inflows:,.0f}"), "tag": "input"},
            {"values": ("─" * 35, "─" * 20), "tag": "separator"},
            {"values": ("Less: Dam Recirculation", f"({metrics.total_recirculation:,.0f})"), "tag": "calculation"},
            {"values": ("Less: Total Outflows", f"({metrics.total_outflows:,.0f})"), "tag": "calculation"},
            {"values": ("─" * 35, "─" * 20), "tag": "separator"},
            {"values": ("= Balance Difference", f"{metrics.balance_difference:,.0f}"), "tag": "result"},
            {"values": ("", ""), "tag": "separator"},
            {"values": ("Error %", f"{metrics.balance_error_percent:.2f}%"), "tag": "error"},
        ]
        
        breakdown_frame = ttk.LabelFrame(self.balance_summary_frame, text="📊 Balance Calculation Breakdown", padding=10)
        breakdown_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tag_configs = {
            'input': {'foreground': '#007bff'},
            'calculation': {'foreground': '#666'},
            'result': {'font': ('Segoe UI', 10, 'bold'), 'foreground': '#000'},
            'error': {'font': ('Segoe UI', 10, 'bold'), 'foreground': error_color},
            'separator': {'foreground': '#ccc'}
        }
        
        self.add_treeview(breakdown_frame, ('item', 'value'), 
                         ['Item', 'Value (m³)'], breakdown_data, tag_configs)
        
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
        # Clear existing
        for widget in self.area_balance_frame.winfo_children():
            widget.destroy()
        
        metrics = self.balance_engine.get_metrics()
        if not metrics or not metrics.area_metrics:
            return
        
        # Header
        ttk.Label(self.area_balance_frame,
                 text="🗺️ Balance Check by Mine Area",
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # Info box
        self.add_info_box(self.area_balance_frame,
                         "Detailed balance breakdown for each mine area.\n"
                         "Shows inflows, outflows, and recirculation specific to each area.",
                         icon="💡")

    def _update_flow_params_preview(self):
        """Placeholder table for flow diagram-linked parameters (monthly)."""
        for widget in self.flow_params_frame.winfo_children():
            widget.destroy()
        
        # Main container with Flow Diagram theme
        container = tk.Frame(self.flow_params_frame, bg='#2c3e50')
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header
        header_frame = tk.Frame(container, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame,
                text="🧭 Flow Diagram Parameters (Monthly)",
                font=('Segoe UI', 14, 'bold'),
                bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
        # Info box
        info_frame = tk.Frame(container, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(info_frame,
                text="ℹ️  Awaiting parameter list. This table will summarize selected flow diagram metrics on a monthly basis.",
                font=('Segoe UI', 9),
                bg='#34495e', fg='#ecf0f1',
                wraplength=800, justify='left').pack(padx=12, pady=10)
        
        # Table frame
        table_frame = tk.Frame(container, bg='#2c3e50')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Styled table
        columns = ('parameter', 'value', 'unit', 'status')
        table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        table.heading('parameter', text='Parameter')
        table.heading('value', text='Value')
        table.heading('unit', text='Unit')
        table.heading('status', text='Status')
        table.column('parameter', width=300, anchor='w')
        table.column('value', width=150, anchor='e')
        table.column('unit', width=100, anchor='center')
        table.column('status', width=150, anchor='center')
        
        # Placeholder rows
        placeholder_data = [
            ('Parameter 1', '-', 'm³', 'Pending'),
            ('Parameter 2', '-', 'm³', 'Pending'),
            ('Parameter 3', '-', 'm³', 'Pending'),
        ]
        
        for row in placeholder_data:
            table.insert('', 'end', values=row, tags=('pending',))
        
        table.tag_configure('pending', foreground='#95a5a6')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        table.pack(side='left', fill='both', expand=True)

    def _update_future_balance_placeholder(self):
        """Placeholder for future water balance calculation table."""
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
                bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
        # Info box
        info_frame = tk.Frame(container, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(info_frame,
                text="⏳  This dashboard will host water balance calculations once parameters are defined.",
                font=('Segoe UI', 9),
                bg='#34495e', fg='#ecf0f1',
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
                'mining_water_rate': self.calculator.get_constant('MINING_WATER_RATE', 0.65),
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
                'MINING_WATER_RATE': self.calculator.get_constant('MINING_WATER_RATE', 0.65),
                'MEAN_ANNUAL_EVAPORATION': self.calculator.get_constant('MEAN_ANNUAL_EVAPORATION', 1800),
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
                ore_tonnes = float(self.ore_tonnes_var.get()) if self.ore_tonnes_var.get() else None
                
                results = []
                
                # Save to database
                if option in ("database", "both"):
                    # Check if duplicate exists
                    existing_id = self.calculator._check_duplicate_calculation(calc_date, ore_tonnes or 0)
                    
                    if existing_id:
                        # Duplicate found - inform user
                        results.append(f"ℹ️  Duplicate calculation detected\n"
                                     f"   Same date and input values already saved (ID: {existing_id})\n"
                                     f"   Skipping database save to avoid duplicate")
                    else:
                        # No duplicate - save normally
                        calc_id = self.calculator.save_calculation(calc_date, ore_tonnes)
                        results.append(f"✅ Saved to database (ID: {calc_id})")
                
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

    def _show_exclusion_manager(self):
        """Show area exclusion manager dialog"""
        dialog = AreaExclusionDialog(self.parent)
        if dialog.show():
            logger.info("Area exclusions updated")
            if self.current_balance:
                messagebox.showinfo("Exclusions Updated",
                    "Area exclusions have been updated.\n"
                    "Click 'Calculate Balance' again to see results with new exclusions.")
    

    # ==================== ORE TONNAGE PREFILL ====================
    def _prefill_ore_tonnage(self):
        """Populate ore tonnes from Excel data.
        
        Precedence:
          1. Excel 'Tonnes Milled' for the selected month
          2. Constant 'monthly_ore_processing' as fallback
        
        Skips overwrite if user manually edited after last prefill.
        """
        try:
            calc_date = datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        except Exception:
            return
        
        if getattr(self, '_manual_override', False):
            return
        
        # Try to get from Excel
        try:
            excel_repo = get_default_excel_repo()
            excel_tonnes = excel_repo.get_monthly_value(calc_date, "Tonnes Milled")
            
            if excel_tonnes > 0:
                self.ore_tonnes_var.set(str(int(excel_tonnes)))
                self._manual_override = False
                return
        except Exception:
            pass  # Fall through to constant
        
        # Fallback to constant
        const_val = self.calculator.get_constant('monthly_ore_processing', 350000.0)
        self.ore_tonnes_var.set(str(int(const_val)))
        self._manual_override = False

    def _mark_manual_override(self):
        """Mark that the user manually edited ore tonnes; prevent auto overwrite until date changes."""
        self._manual_override = True
        # Label removed; no UX change needed

    def _on_calc_date_change(self):
        """Handle date changes whether via calendar selection or manual typing.
        Resets manual override so the user always sees authoritative source for the new date."""
        # Only act if widget constructed (defensive) and date looks valid
        if not self.calc_date_var.get():
            return
        try:
            datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d')
        except Exception:
            return  # ignore incomplete typing until valid
        # Reset override; new date means new source context
        self._manual_override = False
        self._prefill_ore_tonnage()

