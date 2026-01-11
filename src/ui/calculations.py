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
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.water_balance_calculator import WaterBalanceCalculator
from utils.excel_timeseries import get_default_excel_repo
from utils.app_logger import logger
from utils.template_data_parser import get_template_parser
from utils.balance_check_engine import get_balance_check_engine
from utils.balance_engine import BalanceEngine
from utils.balance_services_legacy import LegacyBalanceServices
from ui.area_exclusion_dialog import AreaExclusionDialog
from utils.inputs_audit import collect_inputs_audit
from utils.inputs_audit import collect_inputs_audit


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
        self.engine_result = None
        self.year_var = None
        self.month_var = None
        self.manual_inputs_vars = {}

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
        
        # Determine default month/year: latest DB date first, then Excel, then today
        try:
            db_latest = self.db.get_latest_data_date()
        except Exception:
            db_latest = None
        try:
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
        
        # Default to 0 when no data; let user enter explicit value if needed
        self.ore_tonnes_var = tk.StringVar(value='0')
        self.ore_entry = ttk.Entry(date_frame, textvariable=self.ore_tonnes_var, width=15)
        self.ore_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Source indicator label removed for cleaner UI
        
        # Calculate button
        calc_btn = ttk.Button(date_frame, text="🔢 Calculate Balance", 
                             command=self._calculate_balance,
                             style='Accent.TButton')
        calc_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Configure Balance Check button - DISABLED (using all template flows)
        # config_btn = ttk.Button(date_frame, text="⚙️ Configure Balance Check",
        #                        command=self._open_balance_config_editor)
        # config_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Removed Save Calculation and Area Exclusions per request


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

        # Tab 5: Consumption Trends (historical analysis)
        self.consumption_trends_frame = ttk.Frame(notebook)
        notebook.add(self.consumption_trends_frame, text="📈 Consumption Trends")

        # Tab 6: Scenario Planner (what-if analysis)
        self.scenario_planner_frame = ttk.Frame(notebook)
        notebook.add(self.scenario_planner_frame, text="🔮 Scenario Planner")

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

    def _show_placeholder(self):
        """Show initial placeholder prompting user to run calculation on demand"""
        frames_to_clear = [
            getattr(self, 'closure_frame', None),
            getattr(self, 'recycled_frame', None),
            getattr(self, 'quality_frame', None),
            getattr(self, 'inputs_frame', None),
                        getattr(self, 'days_of_operation_frame', None),
                        getattr(self, 'consumption_trends_frame', None),
                        getattr(self, 'scenario_planner_frame', None),
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
                          bg='#2c3e50', fg='#ecf0f1')
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
            var = self.manual_inputs_vars.setdefault(key, tk.StringVar(value='0'))
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
            self._update_consumption_trends_display()
            self._update_scenario_planner_display()
            self._update_future_balance_placeholder()
            logger.info(f"  ✓ UI update: {(time.perf_counter() - ui_start)*1000:.0f}ms")
            
            total_elapsed = (time.perf_counter() - calc_start) * 1000
            logger.info(f"✅ Calculations completed in {total_elapsed:.0f}ms")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate balance:\n{str(e)}")
            logger.error(f"Calculation error: {e}", exc_info=True)
    
    def _update_balance_calculation_breakdown(self):
        """Professional Balance Calculation Breakdown tab with parameters and formula"""
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
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame,
                text="📐 Balance Calculation Breakdown",
                font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
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
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
        
        formula_text = (
            "Total Inflows − Total Recirculation − Total Outflows = Balance Difference\n"
            "Balance Error % = (Balance Difference ÷ Total Inflows) × 100"
        )
        tk.Label(formula_frame,
                text=formula_text,
                font=('Segoe UI', 10, 'italic'),
                bg='#34495e', fg='#ecf0f1',
                justify='left').pack(anchor='w', padx=12, pady=(0, 10))
        
        # Parameters section
        params_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        params_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(params_frame,
                text="⚙️ Input Parameters",
                font=('Segoe UI', 11, 'bold'),
                bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
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
            ("Excluded Areas", ", ".join(self.balance_engine.get_excluded_areas()) or "None", "⛔"),
            ("Included Areas", f"{len([a for a in metrics.area_metrics.keys() if a not in self.balance_engine.get_excluded_areas()])} areas", "🏭"),
        ]
        
        for i, (label, value, icon) in enumerate(params_data):
            param_card = tk.Frame(params_grid, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            param_card.pack(fill=tk.X, pady=5)
            
            tk.Label(param_card, text=f"{icon} {label}:", font=('Segoe UI', 10, 'bold'),
                    bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(8, 2))
            tk.Label(param_card, text=str(value), font=('Segoe UI', 10),
                    bg='#34495e', fg='#3498db').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Calculation steps section
        steps_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tk.Label(steps_frame,
                text="📊 Calculation Steps",
                font=('Segoe UI', 11, 'bold'),
                bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
        # Step 1: Total Inflows
        step1_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step1_frame.pack(fill=tk.X, pady=(10, 5))
        
        tk.Label(step1_frame, text="Step 1️⃣ Calculate Total Inflows",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#3498db').pack(anchor='w', padx=12, pady=(8, 5))
        tk.Label(step1_frame, text=f"Total Inflows = {metrics.total_inflows:,.0f} m³  ({metrics.inflow_count} sources)",
                font=('Segoe UI', 10),
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 2: Total Recirculation
        step2_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step2_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step2_frame, text="Step 2️⃣ Calculate Total Recirculation",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#27ae60').pack(anchor='w', padx=12, pady=(8, 5))
        tk.Label(step2_frame, text=f"Total Recirculation = {metrics.total_recirculation:,.0f} m³  ({metrics.recirculation_count} self-loops)",
                font=('Segoe UI', 10),
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 3: Total Outflows
        step3_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step3_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step3_frame, text="Step 3️⃣ Calculate Total Outflows",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#e74c3c').pack(anchor='w', padx=12, pady=(8, 5))
        tk.Label(step3_frame, text=f"Total Outflows = {metrics.total_outflows:,.0f} m³  ({metrics.outflow_count} flows)",
                font=('Segoe UI', 10),
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 8))
        
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
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Step 5: Error Percentage
        step5_frame = tk.Frame(steps_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        step5_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(step5_frame, text="Step 5️⃣ Calculate Error Percentage",
                font=('Segoe UI', 10, 'bold'),
                bg='#34495e', fg='#9b59b6').pack(anchor='w', padx=12, pady=(8, 5))
        
        error_calc = (
            f"({metrics.balance_difference:,.0f} ÷ {metrics.total_inflows:,.0f}) × 100 "
            f"= {metrics.balance_error_percent:.2f}%"
        )
        tk.Label(step5_frame, text=error_calc,
                font=('Segoe UI', 10),
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 8))
        
        # Final result
        result_frame = tk.Frame(steps_frame, bg='#27ae60' if metrics.is_balanced else '#e74c3c', relief=tk.SOLID, borderwidth=2)
        result_frame.pack(fill=tk.X, pady=(10, 0))
        
        status_icon = "✅" if metrics.is_balanced else "⚠️"
        tk.Label(result_frame, text=f"{status_icon} Final Status: {metrics.status_label}",
                font=('Segoe UI', 12, 'bold'),
                bg='#27ae60' if metrics.is_balanced else '#e74c3c', fg='#ecf0f1').pack(padx=12, pady=12)
    
    
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
                bg='#2c3e50', fg='#ecf0f1').pack(side='left', padx=15, pady=15)
        
        tk.Label(header,
                text="Select which flows to include in the balance calculation",
                font=('Segoe UI', 9),
                bg='#2c3e50', fg='#95a5a6').pack(side='left', padx=(0, 15))
        
        # Main content
        content = tk.Frame(dialog, bg='#ecf0f1')
        content.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Info box
        info_frame = tk.Frame(content, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        info_text = (
            "📋 Instructions: Check/uncheck flows to include/exclude them from balance calculation.\n"
            "Only ENABLED flows will be included when you click 'Calculate Balance' in the Calculations module."
        )
        tk.Label(info_frame, text=info_text, font=('Segoe UI', 9),
                bg='#34495e', fg='#ecf0f1', justify='left').pack(padx=12, pady=8)
        
        # Notebook for flow types
        from tkinter import ttk
        notebook = ttk.Notebook(content)
        notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        flow_checks = {}  # Store checkbutton variables
        
        # Create tabs for each flow type
        for flow_type in ['inflows', 'recirculation', 'outflows']:
            tab_frame = tk.Frame(notebook, bg='#ecf0f1')
            notebook.add(tab_frame, text=f"{flow_type.title()}")
            
            # Scrollable area
            canvas_frame = tk.Frame(tab_frame, bg='#ecf0f1')
            canvas_frame.pack(fill='both', expand=True)
            
            canvas = tk.Canvas(canvas_frame, bg='#ecf0f1', highlightthickness=0)
            scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
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
                item_frame = tk.Frame(scrollable_frame, bg='#ecf0f1')
                item_frame.pack(fill='x', padx=10, pady=4)
                
                # Checkbutton
                check = ttk.Checkbutton(item_frame, text=f"{entry.code}", variable=var)
                check.pack(side='left', anchor='w')
                
                # Flow name and value
                label_text = f"{entry.name} ({entry.value_m3:,.0f} {entry.unit})"
                label = tk.Label(item_frame, text=label_text, font=('Segoe UI', 9),
                               bg='#ecf0f1', fg='#7f8c8d')
                label.pack(side='left', padx=(10, 0), anchor='w')
        
        # Footer buttons
        footer = tk.Frame(dialog, bg='#ecf0f1', height=60)
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
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="⚖️ System Water Balance (Regulator Mode)",
                font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        tk.Label(header_frame, text="Authoritative closure using fresh + dirty water inflows",
                font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))
        
        # Master equation display
        eq_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        eq_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(eq_frame, text="📝 Master Balance Equation",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
        
        eq_text = "(Fresh Inflows + Dirty Inflows) − Total Outflows − ΔStorage = Balance Error"
        tk.Label(eq_frame, text=eq_text, font=('Segoe UI', 10, 'italic'),
                bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 10))
        
        # Key metrics cards
        metrics_grid = tk.Frame(scrollable_frame, bg='#2c3e50')
        metrics_grid.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        def add_metric(parent, label, value, color, row, col):
            card = tk.Frame(parent, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            tk.Label(card, text=label, font=('Segoe UI', 9), bg='#34495e', fg='#95a5a6').pack(padx=10, pady=(8, 2))
            tk.Label(card, text=value, font=('Segoe UI', 14, 'bold'), bg='#34495e', fg=color).pack(padx=10, pady=(0, 8))
        
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
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
        
        for comp, val in result.fresh_in.components.items():
            comp_frame = tk.Frame(inflows_frame, bg='#34495e')
            comp_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(comp_frame, text=f"• {comp.replace('_', ' ').title()}:",
                    font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
            tk.Label(comp_frame, text=f"{val:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#3498db').pack(side='left', padx=10)
        
        tk.Frame(inflows_frame, bg='#7f8c8d', height=1).pack(fill=tk.X, padx=12, pady=5)
        total_frame = tk.Frame(inflows_frame, bg='#34495e')
        total_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        tk.Label(total_frame, text="TOTAL FRESH INFLOWS:",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
        tk.Label(total_frame, text=f"{result.fresh_in.total:,.0f} m³",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#3498db').pack(side='left', padx=10)
        
        # Dirty inflows breakdown (RWD only)
        rwd_value = result.recycled.components.get('rwd_inflow', 0) if result.recycled.components else 0
        if rwd_value > 0:
            dirty_inflows_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
            dirty_inflows_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
            
            tk.Label(dirty_inflows_frame, text="💧 Dirty Water Inflows",
                    font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
            
            rwd_frame = tk.Frame(dirty_inflows_frame, bg='#34495e')
            rwd_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(rwd_frame, text="• RWD (Return Water Dam):",
                    font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
            tk.Label(rwd_frame, text=f"{rwd_value:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#95a5a6').pack(side='left', padx=10)
            
            tk.Frame(dirty_inflows_frame, bg='#7f8c8d', height=1).pack(fill=tk.X, padx=12, pady=5)
            total_dirty_frame = tk.Frame(dirty_inflows_frame, bg='#34495e')
            total_dirty_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
            tk.Label(total_dirty_frame, text="TOTAL DIRTY INFLOWS:",
                    font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
            tk.Label(total_dirty_frame, text=f"{rwd_value:,.0f} m³",
                    font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#95a5a6').pack(side='left', padx=10)
        
        # Outflows breakdown
        outflows_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        outflows_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(outflows_frame, text="🚰 Total Outflows",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
        
        for comp, val in result.outflows.components.items():
            comp_frame = tk.Frame(outflows_frame, bg='#34495e')
            comp_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(comp_frame, text=f"• {comp.replace('_', ' ').title()}:",
                    font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
            tk.Label(comp_frame, text=f"{val:,.0f} m³",
                    font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#e74c3c').pack(side='left', padx=10)
        
        tk.Frame(outflows_frame, bg='#7f8c8d', height=1).pack(fill=tk.X, padx=12, pady=5)
        total_out_frame = tk.Frame(outflows_frame, bg='#34495e')
        total_out_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        tk.Label(total_out_frame, text="TOTAL OUTFLOWS:",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
        tk.Label(total_out_frame, text=f"{result.outflows.total:,.0f} m³",
                font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#e74c3c').pack(side='left', padx=10)
        
        # Storage
        storage_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        storage_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(storage_frame, text="🏗️ Storage Change",
                font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
        
        for label, val in [("Opening Volume", result.storage.opening),
                           ("Closing Volume", result.storage.closing),
                           ("Net Change (ΔStorage)", result.storage.delta)]:
            st_frame = tk.Frame(storage_frame, bg='#34495e')
            st_frame.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(st_frame, text=f"• {label}:",
                    font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1', width=25, anchor='w').pack(side='left')
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
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Header
        tk.Label(frame, text="🏗️ Storage & Dams — Per‑Facility Drivers",
                 font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w', padx=15, pady=(15, 6))
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


    def _update_days_of_operation_display(self):
        """Display Days of Operation dashboard with data quality, KPIs, and storage runway chart."""
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
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="⏳ Days of Operation — Water Runway Analysis",
                 font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        tk.Label(header_frame, text="Estimate how many days the mine can operate based on current water storage and consumption rates",
                 font=('Segoe UI', 9), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(0, 5))
        
        # Data Quality Banner
        try:
            completeness_result = quality_checker.check_input_completeness(calc_date)
            confidence_score = completeness_result['confidence_score']
            quality_level, quality_color = quality_checker.get_quality_level(confidence_score, confidence_score)
            warning_count = len([w for w in completeness_result['warnings'] if w])
            
            quality_frame = tk.Frame(scrollable_frame, bg=quality_color, relief=tk.SOLID, borderwidth=2)
            quality_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
            
            quality_icon = "✅" if quality_level == "GOOD" else "⚠️" if quality_level == "FAIR" else "❌"
            tk.Label(quality_frame, text=f"{quality_icon} Data Quality: {quality_level}",
                     font=('Segoe UI', 11, 'bold'), bg=quality_color, fg='#ffffff').pack(anchor='w', padx=12, pady=(8, 2))
            tk.Label(quality_frame, text=f"Confidence Score: {confidence_score:.0f}/100 • Warnings: {warning_count}",
                     font=('Segoe UI', 9), bg=quality_color, fg='#ffffff').pack(anchor='w', padx=12, pady=(0, 8))
            
        except Exception as e:
            logger.warning(f"Could not generate data quality banner: {e}")
        
        # KPI Cards Row
        kpi_container = tk.Frame(scrollable_frame, bg='#2c3e50')
        kpi_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Calculate KPIs
        try:
            # Get current storage and consumption from balance
            storage_data = self.current_balance.get('storage', {})
            total_storage = storage_data.get('closing', 0.0)
            capacity = storage_data.get('capacity', 1000000.0)  # Default 1M m³ if not available
            
            outflows = self.current_balance.get('outflows', {})
            monthly_consumption = outflows.get('total', 0.0)
            daily_consumption = monthly_consumption / 30.0 if monthly_consumption > 0 else 1.0  # Avoid division by zero
            
            # Calculate days remaining
            days_remaining = total_storage / daily_consumption if daily_consumption > 0 else 999
            
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
            
            tk.Label(chart_frame, text="📊 Storage Projection (90 days)",
                     font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
            
            # Generate projection data
            projection_days_count = 90
            projection_days = list(range(projection_days_count + 1))
            storage_levels = []
            for day in range(projection_days_count + 1):
                projected_storage = max(0, total_storage - (daily_consumption * day))
                storage_levels.append(projected_storage)
            
            # Create chart
            # Create projection and pass percentage thresholds
            thresholds_pct = {
                'critical': 20.0,  # 20% of capacity
                'warning': 40.0,   # 40% of capacity
                'safe': 70.0       # 70% of capacity
            }
            
            fig = create_storage_runway_chart(projection_days, storage_levels, capacity, 
                                            critical_threshold_pct=thresholds_pct['critical'],
                                            empty_threshold_pct=0.0)
            embed_matplotlib_canvas(chart_frame, fig, toolbar=False)
            
        except Exception as e:
            logger.error(f"Failed to create storage runway chart: {e}", exc_info=True)
            tk.Label(chart_frame, text=f"Chart generation failed: {e}",
                     font=('Segoe UI', 9), bg='#34495e', fg='#e74c3c').pack(padx=10, pady=10)
        
        # Optimization Panel
        optimization_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        optimization_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(optimization_frame, text="🎯 Target Days Optimizer",
                 font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
        tk.Label(optimization_frame, text="Find operational adjustments needed to meet a target number of days",
                 font=('Segoe UI', 9), bg='#34495e', fg='#95a5a6').pack(anchor='w', padx=10, pady=(0, 10))
        
        # Target days input and optimize button
        input_frame = tk.Frame(optimization_frame, bg='#34495e')
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(input_frame, text="Target Days:", font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#ecf0f1').pack(side='left', padx=(0, 5))
        
        target_days_var = tk.StringVar(value="60")
        target_entry = ttk.Entry(input_frame, textvariable=target_days_var, width=10)
        target_entry.pack(side='left', padx=(0, 10))
        
        def run_optimization():
            try:
                target = int(target_days_var.get())
                
                # Get current constants from database
                constants = self.db.get_all_constants()
                
                # Run optimization
                result = optimizer.optimize_for_target_days(
                    target_days=target,
                    current_storage=total_storage,
                    daily_consumption=daily_consumption,
                    current_constants=constants,
                    constraints={
                        'plant_water_recovery_rate': (0.60, 0.95),
                        'tailings_moisture_pct': (0.15, 0.35),
                        'evaporation_mitigation_factor': (0.70, 0.95)
                    }
                )
                
                # Show results dialog
                show_optimization_results(result, target)
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number for target days")
            except Exception as e:
                messagebox.showerror("Optimization Error", f"Failed to optimize:\n{e}")
        
        def show_optimization_results(result, target):
            # Create results dialog
            dialog = tk.Toplevel(self.days_of_operation_frame)
            dialog.title("Optimization Results")
            dialog.geometry("600x500")
            dialog.configure(bg='#2c3e50')
            
            # Header
            header_text = "✅ Target Achievable" if result['achievable'] else "⚠️ Target Not Achievable"
            header_color = '#28a745' if result['achievable'] else '#fd7e14'
            
            header = tk.Frame(dialog, bg=header_color)
            header.pack(fill=tk.X, padx=2, pady=2)
            tk.Label(header, text=header_text, font=('Segoe UI', 14, 'bold'), bg=header_color, fg='#ffffff').pack(pady=15)
            
            # Results container
            results_frame = tk.Frame(dialog, bg='#2c3e50')
            results_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # Summary
            tk.Label(results_frame, text=result['message'], font=('Segoe UI', 10), bg='#2c3e50', fg='#ecf0f1', wraplength=550).pack(anchor='w', pady=(0, 15))
            
            # Recommendations
            if result['recommended_changes']:
                tk.Label(results_frame, text="Recommended Adjustments:", font=('Segoe UI', 11, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w', pady=(0, 5))
                
                for change in result['recommended_changes']:
                    change_frame = tk.Frame(results_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
                    change_frame.pack(fill=tk.X, pady=5)
                    
                    tk.Label(change_frame, text=f"• {change['parameter']}", font=('Segoe UI', 9, 'bold'), bg='#34495e', fg='#f39c12').pack(anchor='w', padx=10, pady=(5, 2))
                    tk.Label(change_frame, text=f"  Current: {change['current']:.2%} → New: {change['new']:.2%}", font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10)
                    tk.Label(change_frame, text=f"  Change: {change['change_pct']:+.1f}%", font=('Segoe UI', 9), bg='#34495e', fg='#17a2b8').pack(anchor='w', padx=10, pady=(0, 5))
            
            # Close button
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=15)
        
        optimize_btn = ttk.Button(input_frame, text="🎯 Optimize", command=run_optimization)
        optimize_btn.pack(side='left')
        
        # Water-saving recommendations
        try:
            # Build consumption dict from daily_consumption estimate
            test_consumption = {
                'dust_suppression': daily_consumption * 0.15,     # ~15% of daily consumption
                'plant_consumption_gross': daily_consumption * 0.5,  # ~50%
                'tsf_return': daily_consumption * 0.2,            # ~20%
                'discharge': daily_consumption * 0.1,             # ~10%
                'evaporation': daily_consumption * 0.05           # ~5%
            }
            recommendations = optimizer.suggest_water_saving_actions(test_consumption, storage_pct)
            
            if recommendations:
                tk.Label(optimization_frame, text="💡 Water-Saving Recommendations:",
                         font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
                
                for rec in recommendations[:5]:  # Show top 5
                    rec_frame = tk.Frame(optimization_frame, bg='#2c3e50', relief=tk.SOLID, borderwidth=1)
                    rec_frame.pack(fill=tk.X, padx=10, pady=3)
                    
                    priority_color = {'HIGH': '#dc3545', 'MEDIUM': '#fd7e14', 'LOW': '#28a745'}.get(rec['priority'], '#6c757d')
                    
                    header_rec = tk.Frame(rec_frame, bg='#2c3e50')
                    header_rec.pack(fill=tk.X)
                    
                    tk.Label(header_rec, text=f"[{rec['priority']}]", font=('Segoe UI', 8, 'bold'), bg=priority_color, fg='#ffffff').pack(side='left', padx=(5, 5), pady=5)
                    tk.Label(header_rec, text=rec['category'], font=('Segoe UI', 9, 'bold'), bg='#2c3e50', fg='#f39c12').pack(side='left')
                    tk.Label(header_rec, text=f"Save: {rec['potential_saving_m3']:,.0f} m³", font=('Segoe UI', 9, 'bold'), bg='#2c3e50', fg='#28a745').pack(side='right', padx=5)
                    
                    tk.Label(rec_frame, text=rec['description'], font=('Segoe UI', 8), bg='#2c3e50', fg='#95a5a6', wraplength=550).pack(anchor='w', padx=10, pady=(0, 5))
        
        except Exception as e:
            logger.warning(f"Could not generate recommendations: {e}")


    def _update_consumption_trends_display(self):
        """Display historical consumption trends with charts and breakdown."""
        if not hasattr(self, 'consumption_trends_frame') or not self.consumption_trends_frame.winfo_exists():
            return
        
        for widget in self.consumption_trends_frame.winfo_children():
            widget.destroy()
        
        # Main container
        container = tk.Frame(self.consumption_trends_frame, bg='#2c3e50')
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scrollable area
        canvas = tk.Canvas(container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="📈 Consumption Trends — Historical Analysis",
                 font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        tk.Label(header_frame, text="Analyze water consumption patterns over time",
                 font=('Segoe UI', 9), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(0, 5))
        
        # Date Range Picker
        date_picker_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        date_picker_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(date_picker_frame, text="📅 Date Range:",
                 font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
        
        picker_row = tk.Frame(date_picker_frame, bg='#34495e')
        picker_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(picker_row, text="From:", font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1').pack(side='left', padx=(0, 5))
        
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        # Default to last 6 months
        end_date = datetime.now().date()
        start_date = end_date - relativedelta(months=6)
        
        from_date_var = tk.StringVar(value=start_date.strftime('%Y-%m-%d'))
        from_entry = ttk.Entry(picker_row, textvariable=from_date_var, width=12)
        from_entry.pack(side='left', padx=(0, 15))
        
        tk.Label(picker_row, text="To:", font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1').pack(side='left', padx=(0, 5))
        
        to_date_var = tk.StringVar(value=end_date.strftime('%Y-%m-%d'))
        to_entry = ttk.Entry(picker_row, textvariable=to_date_var, width=12)
        to_entry.pack(side='left', padx=(0, 15))
        
        def refresh_trends():
            try:
                start = datetime.strptime(from_date_var.get(), '%Y-%m-%d').date()
                end = datetime.strptime(to_date_var.get(), '%Y-%m-%d').date()
                
                if start >= end:
                    messagebox.showerror("Invalid Range", "Start date must be before end date")
                    return
                
                # Clear existing charts and reload
                for widget in charts_container.winfo_children():
                    widget.destroy()
                
                load_trends_data(start, end, charts_container, stats_container)
                
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter dates in YYYY-MM-DD format")
        
        refresh_btn = ttk.Button(picker_row, text="🔄 Refresh", command=refresh_trends)
        refresh_btn.pack(side='left')
        
        # Stats Panel
        stats_container = tk.Frame(scrollable_frame, bg='#2c3e50')
        stats_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Charts Container
        charts_container = tk.Frame(scrollable_frame, bg='#2c3e50')
        charts_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        def load_trends_data(start_date, end_date, charts_frame, stats_frame):
            """Load and display trends data for the given date range."""
            try:
                from ui.chart_utils import create_trends_chart, create_outflow_breakdown_chart, embed_matplotlib_canvas
                
                # Fetch historical calculations from database
                calculations = self.db.execute_query(
                    """
                    SELECT calc_date, total_inflows, total_outflows, 
                           storage_change
                    FROM calculations
                    WHERE calc_date BETWEEN ? AND ?
                    ORDER BY calc_date
                    """,
                    (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                )
                
                if not calculations or len(calculations) == 0:
                    tk.Label(charts_frame, text="No calculation data found for this date range",
                             font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(pady=20)
                    return
                
                # Prepare data for charts
                dates = [datetime.strptime(row['calc_date'], '%Y-%m-%d').date() for row in calculations]
                inflows = [float(row['total_inflows'] or 0) for row in calculations]
                outflows = [float(row['total_outflows'] or 0) for row in calculations]
                storage_changes = [float(row['storage_change'] or 0) for row in calculations]
                
                # Calculate storage levels from cumulative changes (starting from current)
                storage_levels = []
                cumulative = 0
                for change in storage_changes:
                    cumulative += change
                    storage_levels.append(cumulative)
                
                # Calculate statistics
                avg_inflow = sum(inflows) / len(inflows) if inflows else 0
                avg_outflow = sum(outflows) / len(outflows) if outflows else 0
                avg_storage = sum(storage_levels) / len(storage_levels) if storage_levels else 0
                total_consumption = sum(outflows)
                max_consumption = max(outflows) if outflows else 0
                min_consumption = min(outflows) if outflows else 0
                
                # Display stats
                for widget in stats_frame.winfo_children():
                    widget.destroy()
                
                stats_title = tk.Label(stats_frame, text="📊 Summary Statistics",
                                      font=('Segoe UI', 11, 'bold'), bg='#2c3e50', fg='#ecf0f1')
                stats_title.pack(anchor='w', pady=(0, 10))
                
                stats_grid = tk.Frame(stats_frame, bg='#2c3e50')
                stats_grid.pack(fill=tk.X)
                
                # Create stat cards
                stats_data = [
                    ("Avg Inflow", f"{avg_inflow:,.0f} m³/month", '#17a2b8'),
                    ("Avg Outflow", f"{avg_outflow:,.0f} m³/month", '#fd7e14'),
                    ("Avg Storage", f"{avg_storage:,.0f} m³", '#28a745'),
                    ("Total Consumption", f"{total_consumption:,.0f} m³", '#6c757d'),
                    ("Max Consumption", f"{max_consumption:,.0f} m³", '#dc3545'),
                    ("Min Consumption", f"{min_consumption:,.0f} m³", '#17a2b8')
                ]
                
                for i, (label, value, color) in enumerate(stats_data):
                    stat_card = tk.Frame(stats_grid, bg=color, relief=tk.RAISED, borderwidth=2)
                    stat_card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky='ew')
                    stats_grid.columnconfigure(i % 3, weight=1)
                    
                    tk.Label(stat_card, text=label, font=('Segoe UI', 8), bg=color, fg='#ffffff').pack(pady=(8, 2))
                    tk.Label(stat_card, text=value, font=('Segoe UI', 10, 'bold'), bg=color, fg='#ffffff').pack(pady=(0, 8))
                
                # Trends Chart
                trends_frame = tk.Frame(charts_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
                trends_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                
                tk.Label(trends_frame, text="📈 Water Balance Trends",
                         font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
                
                series_dict = {
                    'Inflows': inflows,
                    'Outflows': outflows,
                    'Storage': storage_levels
                }
                
                fig = create_trends_chart(dates, series_dict, "Volume (m³)", "Water Balance Over Time")
                embed_matplotlib_canvas(trends_frame, fig, toolbar=False)
                
                # Breakdown Chart (if we have detailed outflow data)
                try:
                    # Fetch outflow breakdown for the most recent calculation
                    latest_calc = calculations[-1]
                    latest_date = latest_calc['calc_date']
                    
                    # Get outflow details from the calculator
                    calc_date_obj = datetime.strptime(latest_date, '%Y-%m-%d').date()
                    balance = self.calculator.calculate_water_balance(calc_date_obj, None)
                    
                    if balance and 'outflows' in balance:
                        outflows_data = balance['outflows']
                        
                        # Build breakdown dictionary
                        breakdown_dict = {}
                        for key, value in outflows_data.items():
                            if key != 'total' and isinstance(value, (int, float)) and value > 0:
                                # Format key for display
                                display_key = key.replace('_', ' ').title()
                                breakdown_dict[display_key] = [value]  # Single month breakdown
                        
                        if breakdown_dict:
                            breakdown_frame = tk.Frame(charts_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
                            breakdown_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                            
                            tk.Label(breakdown_frame, text=f"📊 Outflow Breakdown ({latest_date})",
                                     font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
                            
                            fig2 = create_outflow_breakdown_chart([calc_date_obj], breakdown_dict)
                            embed_matplotlib_canvas(breakdown_frame, fig2, toolbar=False)
                
                except Exception as e:
                    logger.warning(f"Could not create breakdown chart: {e}")
                
            except Exception as e:
                logger.error(f"Failed to load trends data: {e}", exc_info=True)
                tk.Label(charts_frame, text=f"Error loading trends: {e}",
                         font=('Segoe UI', 9), bg='#2c3e50', fg='#e74c3c').pack(pady=20)
        
        # Initial load with default date range
        load_trends_data(start_date, end_date, charts_container, stats_container)

    def _update_scenario_planner_display(self):
        """Display scenario planning interface with what-if analysis."""
        if not hasattr(self, 'scenario_planner_frame') or not self.scenario_planner_frame.winfo_exists():
            return
        
        for widget in self.scenario_planner_frame.winfo_children():
            widget.destroy()
        
        # Main container
        container = tk.Frame(self.scenario_planner_frame, bg='#2c3e50')
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scrollable area
        canvas = tk.Canvas(container, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(header_frame, text="🔮 Scenario Planner — What-If Analysis",
                 font=('Segoe UI', 14, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        tk.Label(header_frame, text="Create and compare scenarios by adjusting water balance constants",
                 font=('Segoe UI', 9), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(0, 5))
        
        # Scenario Manager
        manager_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        manager_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(manager_frame, text="📋 Scenarios",
                 font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
        
        # Scenario list and buttons
        scenario_list_frame = tk.Frame(manager_frame, bg='#34495e')
        scenario_list_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Scenario storage (in-memory for this session)
        scenarios = {
            'Baseline': self.db.get_all_constants()
        }
        active_scenario_var = tk.StringVar(value='Baseline')
        
        scenario_listbox = tk.Listbox(scenario_list_frame, height=5, bg='#2c3e50', fg='#ecf0f1', 
                                      selectbackground='#17a2b8', font=('Segoe UI', 9))
        scenario_listbox.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        for scenario_name in scenarios.keys():
            scenario_listbox.insert(tk.END, scenario_name)
        
        scenario_listbox.select_set(0)
        
        buttons_frame = tk.Frame(scenario_list_frame, bg='#34495e')
        buttons_frame.pack(side='left', fill='y')
        
        def create_new_scenario():
            name = tk.simpledialog.askstring("New Scenario", "Enter scenario name:")
            if name and name not in scenarios:
                # Clone baseline constants (create a copy of the dict)
                scenarios[name] = dict(scenarios['Baseline'])
                scenario_listbox.insert(tk.END, name)
                scenario_listbox.selection_clear(0, tk.END)
                scenario_listbox.select_set(scenario_listbox.size() - 1)
                active_scenario_var.set(name)
                refresh_editor()
            elif name in scenarios:
                messagebox.showerror("Duplicate", "Scenario already exists")
        
        def clone_scenario():
            selection = scenario_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a scenario to clone")
                return
            
            source_name = scenario_listbox.get(selection[0])
            name = tk.simpledialog.askstring("Clone Scenario", f"Clone '{source_name}' as:")
            
            if name and name not in scenarios:
                scenarios[name] = [dict(row) for row in scenarios[source_name]]
                scenario_listbox.insert(tk.END, name)
                scenario_listbox.selection_clear(0, tk.END)
                scenario_listbox.select_set(scenario_listbox.size() - 1)
                active_scenario_var.set(name)
                refresh_editor()
            elif name in scenarios:
                messagebox.showerror("Duplicate", "Scenario already exists")
        
        def delete_scenario():
            selection = scenario_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a scenario to delete")
                return
            
            name = scenario_listbox.get(selection[0])
            if name == 'Baseline':
                messagebox.showerror("Cannot Delete", "Cannot delete Baseline scenario")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Delete scenario '{name}'?"):
                del scenarios[name]
                scenario_listbox.delete(selection[0])
                scenario_listbox.select_set(0)
                active_scenario_var.set('Baseline')
                refresh_editor()
        
        def on_scenario_select(event):
            selection = scenario_listbox.curselection()
            if selection:
                active_scenario_var.set(scenario_listbox.get(selection[0]))
                refresh_editor()
        
        scenario_listbox.bind('<<ListboxSelect>>', on_scenario_select)
        
        ttk.Button(buttons_frame, text="➕ New", command=create_new_scenario, width=10).pack(pady=2)
        ttk.Button(buttons_frame, text="📋 Clone", command=clone_scenario, width=10).pack(pady=2)
        ttk.Button(buttons_frame, text="🗑️ Delete", command=delete_scenario, width=10).pack(pady=2)
        
        # Constants Editor
        editor_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tk.Label(editor_frame, text="⚙️ Constants Editor",
                 font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
        
        editor_container = tk.Frame(editor_frame, bg='#34495e')
        editor_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview for constants
        columns = ('key', 'value', 'description')
        constants_tree = ttk.Treeview(editor_container, columns=columns, show='headings', height=12)
        
        constants_tree.heading('key', text='Constant')
        constants_tree.heading('value', text='Value')
        constants_tree.heading('description', text='Description')
        
        constants_tree.column('key', width=250, minwidth=200)
        constants_tree.column('value', width=120, minwidth=100)
        constants_tree.column('description', width=350, minwidth=250)
        
        tree_scroll = ttk.Scrollbar(editor_container, orient='vertical', command=constants_tree.yview)
        constants_tree.configure(yscrollcommand=tree_scroll.set)
        
        constants_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        def refresh_editor():
            """Reload constants for active scenario."""
            constants_tree.delete(*constants_tree.get_children())
            
            scenario_name = active_scenario_var.get()
            if scenario_name in scenarios:
                # scenarios[scenario_name] is now a dict: {'CONSTANT_KEY': value, ...}
                scenario_constants = scenarios[scenario_name]
                for key, value in scenario_constants.items():
                    constants_tree.insert('', 'end', values=(
                        key,
                        f"{float(value):.4f}",
                        ''  # No description column available from dict
                    ))
        
        def edit_constant():
            selection = constants_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a constant to edit")
                return
            
            item = constants_tree.item(selection[0])
            key = item['values'][0]
            current_value = item['values'][1]
            
            new_value = tk.simpledialog.askfloat("Edit Constant", 
                                                  f"Enter new value for {key}:",
                                                  initialvalue=float(current_value))
            
            if new_value is not None:
                scenario_name = active_scenario_var.get()
                # Update the dict value directly
                if key in scenarios[scenario_name]:
                    scenarios[scenario_name][key] = new_value
                
                refresh_editor()
        
        def reset_to_baseline():
            scenario_name = active_scenario_var.get()
            if scenario_name != 'Baseline':
                scenarios[scenario_name] = dict(scenarios['Baseline'])
                refresh_editor()
        
        edit_buttons = tk.Frame(editor_frame, bg='#34495e')
        edit_buttons.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(edit_buttons, text="✏️ Edit Value", command=edit_constant).pack(side='left', padx=(0, 5))
        ttk.Button(edit_buttons, text="🔄 Reset to Baseline", command=reset_to_baseline).pack(side='left')
        
        # Comparison Panel
        comparison_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        comparison_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(comparison_frame, text="📊 Scenario Comparison",
                 font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
        tk.Label(comparison_frame, text="Select scenarios to compare and run projections",
                 font=('Segoe UI', 9), bg='#34495e', fg='#95a5a6').pack(anchor='w', padx=10, pady=(0, 10))
        
        comparison_controls = tk.Frame(comparison_frame, bg='#34495e')
        comparison_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(comparison_controls, text="Scenarios to compare:", font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1').pack(side='left', padx=(0, 10))
        
        # Multi-select for scenarios
        selected_scenarios_var = tk.StringVar(value='Baseline')
        
        def run_comparison():
            """Run comparison between selected scenarios."""
            try:
                from ui.chart_utils import create_scenario_comparison_chart, embed_matplotlib_canvas
                
                # Clear existing results
                for widget in comparison_results.winfo_children():
                    widget.destroy()
                
                # Get selected scenarios (for simplicity, compare all)
                scenario_results = {}
                
                for scenario_name, constants_list in scenarios.items():
                    # Simulate projection (simplified - would use actual calculator in production)
                    # For now, just show the impact of key constants
                    
                    constants_dict = {c['constant_key']: c['constant_value'] for c in constants_list}
                    
                    # Calculate projected days of operation with these constants
                    # This is a simplified model - real implementation would use the calculator
                    recovery_rate = float(constants_dict.get('plant_water_recovery_rate', 0.75))
                    evap_factor = float(constants_dict.get('evaporation_mitigation_factor', 0.85))
                    
                    # Simplified projection formula
                    base_days = 60.0
                    projected_days = base_days * (recovery_rate / 0.75) * (evap_factor / 0.85)
                    
                    scenario_results[scenario_name] = {
                        'days_of_operation': projected_days,
                        'recovery_rate': recovery_rate,
                        'evap_factor': evap_factor
                    }
                
                # Display results table
                results_table = tk.Frame(comparison_results, bg='#2c3e50')
                results_table.pack(fill=tk.X, pady=10)
                
                # Header row
                tk.Label(results_table, text="Scenario", font=('Segoe UI', 9, 'bold'), 
                        bg='#17a2b8', fg='#ffffff', width=20, anchor='w').grid(row=0, column=0, sticky='ew', padx=1, pady=1)
                tk.Label(results_table, text="Days of Operation", font=('Segoe UI', 9, 'bold'), 
                        bg='#17a2b8', fg='#ffffff', width=20).grid(row=0, column=1, sticky='ew', padx=1, pady=1)
                tk.Label(results_table, text="Recovery Rate", font=('Segoe UI', 9, 'bold'), 
                        bg='#17a2b8', fg='#ffffff', width=20).grid(row=0, column=2, sticky='ew', padx=1, pady=1)
                tk.Label(results_table, text="Evap Factor", font=('Segoe UI', 9, 'bold'), 
                        bg='#17a2b8', fg='#ffffff', width=20).grid(row=0, column=3, sticky='ew', padx=1, pady=1)
                
                # Data rows
                for i, (name, results) in enumerate(scenario_results.items(), start=1):
                    bg_color = '#34495e' if i % 2 == 0 else '#2c3e50'
                    
                    tk.Label(results_table, text=name, font=('Segoe UI', 9), 
                            bg=bg_color, fg='#ecf0f1', width=20, anchor='w').grid(row=i, column=0, sticky='ew', padx=1, pady=1)
                    tk.Label(results_table, text=f"{results['days_of_operation']:.1f} days", font=('Segoe UI', 9), 
                            bg=bg_color, fg='#ecf0f1', width=20).grid(row=i, column=1, sticky='ew', padx=1, pady=1)
                    tk.Label(results_table, text=f"{results['recovery_rate']:.2%}", font=('Segoe UI', 9), 
                            bg=bg_color, fg='#ecf0f1', width=20).grid(row=i, column=2, sticky='ew', padx=1, pady=1)
                    tk.Label(results_table, text=f"{results['evap_factor']:.2%}", font=('Segoe UI', 9), 
                            bg=bg_color, fg='#ecf0f1', width=20).grid(row=i, column=3, sticky='ew', padx=1, pady=1)
                
                # Chart
                chart_frame = tk.Frame(comparison_results, bg='#34495e', relief=tk.SOLID, borderwidth=1)
                chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
                
                tk.Label(chart_frame, text="📈 Scenario Comparison Chart",
                         font=('Segoe UI', 10, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=10, pady=(10, 5))
                
                fig = create_scenario_comparison_chart(scenario_results)
                embed_matplotlib_canvas(chart_frame, fig, toolbar=False)
                
            except Exception as e:
                logger.error(f"Failed to run scenario comparison: {e}", exc_info=True)
                tk.Label(comparison_results, text=f"Comparison failed: {e}",
                         font=('Segoe UI', 9), bg='#34495e', fg='#e74c3c').pack(pady=10)
        
        ttk.Button(comparison_controls, text="▶️ Run Comparison", command=run_comparison).pack(side='left')
        
        # Results area
        comparison_results = tk.Frame(comparison_frame, bg='#34495e')
        comparison_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        tk.Label(comparison_results, text="Click 'Run Comparison' to see results",
                 font=('Segoe UI', 9, 'italic'), bg='#34495e', fg='#95a5a6').pack(pady=20)
        
        # Initial load
        refresh_editor()

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
                 font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
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
                font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
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
                        font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1', wraplength=700, justify='left').pack(anchor='w', padx=12, pady=(0, 8))
    
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
        tk.Label(header, text="🧾 Inputs Audit", font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        tk.Label(header, text=f"Month: {audit.get('month', '-')}", font=('Segoe UI', 10), bg='#2c3e50', fg='#95a5a6').pack(anchor='w', pady=(5, 0))

        # Legacy Excel section
        legacy = audit.get('legacy_excel', {}) or {}
        legacy_frame = tk.Frame(scrollable_frame, bg='#34495e', relief=tk.SOLID, borderwidth=1)
        legacy_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        tk.Label(legacy_frame, text="📑 Meter Readings (Legacy Excel)", font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(10, 5))
        path_txt = legacy.get('path') or '—'
        exists = bool(legacy.get('exists'))
        matched = legacy.get('matched_row_date') or '—'
        tk.Label(legacy_frame, text=f"Path: {path_txt}", font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12)
        tk.Label(legacy_frame, text=f"File Exists: {'Yes' if exists else 'No'}", font=('Segoe UI', 9), bg='#34495e', fg=('#27ae60' if exists else '#e74c3c')).pack(anchor='w', padx=12, pady=(0, 2))
        tk.Label(legacy_frame, text=f"Matched Row (month): {matched}", font=('Segoe UI', 9), bg='#34495e', fg='#ecf0f1').pack(anchor='w', padx=12, pady=(0, 8))

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
        self._update_balance_calculation_breakdown()
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
        
        # Fallback to zero (no synthetic defaults per user preference)
        self.ore_tonnes_var.set('0')
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
        self._load_manual_inputs()

    def _get_calc_date_obj(self) -> Optional[date]:
        """Return calc date as date or None if invalid."""
        if not self.calc_date_var:
            return None
        try:
            return datetime.strptime(self.calc_date_var.get(), '%Y-%m-%d').date()
        except Exception:
            return None

