"""
Monitoring Data Dashboard - Loads monitoring data from Excel on demand
Displays environmental and operational monitoring data with graphs and tables
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import date, datetime
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from calendar import monthrange
import threading
import warnings

from utils.config_manager import config
from utils.app_logger import logger
from database.db_manager import DatabaseManager

# Suppress noisy pandas date conversion warnings
warnings.filterwarnings('ignore', message='Discarding nonzero nanoseconds')


class MonitoringDataModule:
    """Dashboard for monitoring data visualization from Excel files"""
    
    def __init__(self, parent):
        self.parent = parent
        self.container = ttk.Frame(parent)
        self.db = DatabaseManager()
        
        # Excel file paths (configurable)
        self.excel_files = {
            'borehole_static': None,
            'borehole_monitoring': None,
            'pcd': None,
            'return_water_dam': None,
            'sewage_treatment': None,
            'river_monitoring': None
        }
        
        # Cached data
        self.data_cache = {}
        
    def load(self):
        """Load the monitoring data module"""
        self.container.pack(fill='both', expand=True, padx=20, pady=20)
        self._build_ui()
        
    def unload(self):
        """Unload the module"""
        self.container.pack_forget()
        
    def _build_ui(self):
        """Build the user interface"""
        # Title section
        title_frame = ttk.Frame(self.container)
        title_frame.pack(fill='x', pady=(0, 15))
        
        title = ttk.Label(title_frame, text="📊 Monitoring Data Dashboard", 
                         style='Heading1.TLabel')
        title.pack(anchor='w')
        
        subtitle = ttk.Label(title_frame, 
                           text="Environmental and operational monitoring data visualization",
                           style='Body.TLabel')
        subtitle.pack(anchor='w', pady=(0, 5))
        
        # Status bar (create early so sub-tabs can update it)
        status_frame = ttk.Frame(self.container)
        status_frame.pack(fill='x', pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="Ready to load monitoring data",
                          foreground='#666')
        self.status_label.pack(side='left')

        # Tabs for different monitoring categories
        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(fill='both', expand=True)

        # Create tabs
        self._create_borehole_static_tab()
        self._create_borehole_monitoring_tab()
        self._create_pcd_tab()
        self._create_rwd_tab()
        self._create_sewage_tab()
        self._create_river_tab()
        
    # ==================== TAB 1: BOREHOLE STATIC LEVELS ====================
    def _create_borehole_static_tab(self):
        """Tab for borehole static water levels"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🏔️ Borehole Static Levels")

        # Sub-tabs: Register | Visualize
        self.bh_static_tabs = ttk.Notebook(tab)
        self.bh_static_tabs.pack(fill='both', expand=True)

        # Register tab
        reg_tab = ttk.Frame(self.bh_static_tabs, padding=10)
        self.bh_static_tabs.add(reg_tab, text="Register")
        self._create_bh_register_tab(reg_tab)

        # Visualize tab
        viz_tab = ttk.Frame(self.bh_static_tabs, padding=10)
        self.bh_static_tabs.add(viz_tab, text="Visualize")

        # Control panel (Visualize)
        control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(control_frame, text="Excel File:").grid(row=0, column=0, sticky='w', padx=(0, 10))

        # default path if exists
        default_excel = Path(__file__).resolve().parents[2] / 'monitoring' / 'Boreholes Static Levels Apr-Jun 25.xls'
        default_text = default_excel.name if default_excel.exists() else "Not loaded"
        self.borehole_static_path = tk.StringVar(value=default_text)
        if default_excel.exists():
            self.excel_files['borehole_static'] = str(default_excel)

        ttk.Entry(control_frame, textvariable=self.borehole_static_path,
                  state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))

        ttk.Button(control_frame, text="📁 Select File",
                   command=lambda: self._select_excel_file('borehole_static')).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(control_frame, text="📊 Load & Visualize",
                   command=lambda: self._load_borehole_static_data(),
                   style='Accent.TButton').grid(row=0, column=3)

        # Directory-based loading row
        ttk.Label(control_frame, text="Directory:").grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(8, 0))
        self.borehole_static_dir = tk.StringVar(value="Not set")
        ttk.Entry(control_frame, textvariable=self.borehole_static_dir, state='readonly', width=60).grid(row=1, column=1, sticky='ew', padx=(0, 10), pady=(8, 0))
        ttk.Button(control_frame, text="📂 Select Directory", command=self._select_bh_static_directory).grid(row=1, column=2, padx=(0,5), pady=(8,0))
        self.bh_scan_btn = ttk.Button(control_frame, text="🔎 Scan Directory & Load", command=self._scan_and_load_bh_static, style='Accent.TButton')
        self.bh_scan_btn.grid(row=1, column=3, pady=(8,0))

        # Period filters row
        period_frame = ttk.Frame(control_frame)
        period_frame.grid(row=2, column=0, columnspan=4, sticky='ew', pady=(10,0))
        ttk.Label(period_frame, text="Period:").pack(side='left')
        self.period_from_year = tk.StringVar(value="All")
        self.period_from_month = tk.StringVar(value="All")
        self.period_to_year = tk.StringVar(value="All")
        self.period_to_month = tk.StringVar(value="All")

        years = ['All'] + [str(y) for y in range(2015, 2036)]
        months = ['All','01','02','03','04','05','06','07','08','09','10','11','12']
        ttk.Label(period_frame, text=" From ").pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.period_from_year, values=years, width=6, state='readonly').pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.period_from_month, values=months, width=4, state='readonly').pack(side='left', padx=(4,8))
        ttk.Label(period_frame, text=" To ").pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.period_to_year, values=years, width=6, state='readonly').pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.period_to_month, values=months, width=4, state='readonly').pack(side='left', padx=(4,8))

        # Chart options row
        opts_frame = ttk.Frame(control_frame)
        opts_frame.grid(row=3, column=0, columnspan=4, sticky='ew', pady=(8,0))
        self.chart_type = tk.StringVar(value='Line')
        self.use_ma = tk.BooleanVar(value=False)
        self.ma_window = tk.IntVar(value=3)
        self.only_registered = tk.BooleanVar(value=True)
        self.preview_cap = tk.IntVar(value=100)
        self.single_borehole = tk.BooleanVar(value=False)
        self.single_borehole_name = tk.StringVar(value='')
        ttk.Label(opts_frame, text='Chart:').pack(side='left')
        ttk.Combobox(opts_frame, textvariable=self.chart_type, values=['Line','Bar'], width=8, state='readonly').pack(side='left', padx=(4,10))
        ttk.Checkbutton(opts_frame, text='Moving Avg', variable=self.use_ma).pack(side='left')
        ttk.Label(opts_frame, text='Window').pack(side='left', padx=(6,0))
        try:
            # ttk.Spinbox available in recent Tk versions
            spin = ttk.Spinbox(opts_frame, from_=2, to=24, textvariable=self.ma_window, width=4)
        except Exception:
            spin = tk.Spinbox(opts_frame, from_=2, to=24, textvariable=self.ma_window, width=4)
        spin.pack(side='left', padx=(4,10))
        ttk.Checkbutton(opts_frame, text='Only registered', variable=self.only_registered).pack(side='left', padx=(6,0))
        ttk.Label(opts_frame, text='Preview cap').pack(side='left', padx=(10,0))
        try:
            cap_spin = ttk.Spinbox(opts_frame, from_=20, to=1000, textvariable=self.preview_cap, width=5)
        except Exception:
            cap_spin = tk.Spinbox(opts_frame, from_=20, to=1000, textvariable=self.preview_cap, width=5)
        cap_spin.pack(side='left', padx=(4,0))
        ttk.Checkbutton(opts_frame, text='Single borehole', variable=self.single_borehole).pack(side='left', padx=(12,0))
        self.single_borehole_combo = ttk.Combobox(opts_frame, textvariable=self.single_borehole_name, values=[], width=16, state='readonly')
        self.single_borehole_combo.pack(side='left', padx=(6,0))

        # Progress row
        prog_frame = ttk.Frame(control_frame)
        prog_frame.grid(row=4, column=0, columnspan=4, sticky='ew', pady=(8,0))
        self.bh_progress = ttk.Progressbar(prog_frame, mode='determinate')
        self.bh_progress.pack(side='left', fill='x', expand=True, padx=(0,8))
        self.bh_progress_label = ttk.Label(prog_frame, text="")
        self.bh_progress_label.pack(side='left')
        ttk.Button(prog_frame, text='📈 Generate Charts', command=self._generate_bh_static_charts, style='Accent.TButton').pack(side='left', padx=(10,0))
        ttk.Button(prog_frame, text='🧹 Clear Cache', command=self._bh_clear_cache).pack(side='left', padx=(6,0))
        ttk.Button(prog_frame, text='🔄 Rescan', command=self._scan_and_load_bh_static).pack(side='left', padx=(6,0))
        self._bh_scan_thread = None

        control_frame.columnconfigure(1, weight=1)

        # Info box
        info_frame = ttk.Frame(viz_tab)
        info_frame.pack(fill='x', pady=(0, 10))

        info_label = ttk.Label(info_frame,
                               text="ℹ️  Displays static water levels over time. Only registered static boreholes are included.",
                               foreground='#1976D2', font=('Segoe UI', 9, 'italic'))
        info_label.pack(anchor='w')

        # Content area (graphs and tables)
        self.borehole_static_content = ttk.Frame(viz_tab)
        self.borehole_static_content.pack(fill='both', expand=True)

        # Placeholder
        placeholder = ttk.Label(self.borehole_static_content,
                                text="Select an Excel file and click 'Load & Visualize' to display data",
                                foreground='#999', font=('Segoe UI', 11))
        placeholder.pack(expand=True)

    def _create_bh_register_tab(self, parent: ttk.Frame):
        """Create the register UI for static boreholes (uses water_sources)."""
        header = ttk.Label(parent, text="Registered Static Boreholes",
                           font=('Segoe UI', 11, 'bold'))
        header.pack(anchor='w', pady=(0, 8))

        toolbar = ttk.Frame(parent)
        toolbar.pack(fill='x', pady=(0, 8))

        ttk.Button(toolbar, text="➕ Add", command=self._bh_reg_add,
                   style='Accent.TButton').pack(side='left')
        ttk.Button(toolbar, text="✅ Activate", command=self._bh_reg_activate).pack(side='left', padx=(6, 0))
        ttk.Button(toolbar, text="❌ Deactivate", command=self._bh_reg_deactivate).pack(side='left', padx=(6, 0))
        ttk.Button(toolbar, text="🔄 Refresh", command=self._bh_reg_load).pack(side='left', padx=(6, 0))

        # Grid
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill='both', expand=True)

        vsb = ttk.Scrollbar(grid_frame, orient='vertical')
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(grid_frame, orient='horizontal')
        hsb.pack(side='bottom', fill='x')

        self.bh_reg_tree = ttk.Treeview(grid_frame, columns=(
            'source_id', 'source_code', 'source_name', 'purpose', 'type', 'status'
        ), show='headings', yscrollcommand=vsb.set, xscrollcommand=hsb.set, selectmode='browse')
        vsb.config(command=self.bh_reg_tree.yview)
        hsb.config(command=self.bh_reg_tree.xview)

        for col, title, width in [
            ('source_code', 'Code', 120),
            ('source_name', 'Name', 220),
            ('purpose', 'Purpose', 90),
            ('type', 'Type', 120),
            ('status', 'Status', 80),
        ]:
            self.bh_reg_tree.heading(col, text=title)
            self.bh_reg_tree.column(col, width=width, anchor='w')

        # Hide internal id column
        self.bh_reg_tree.column('source_id', width=1, stretch=False)
        self.bh_reg_tree.heading('source_id', text='')

        self.bh_reg_tree.pack(fill='both', expand=True)

        self._bh_reg_load()

    def _bh_reg_load(self):
        """Load registered static boreholes from DB."""
        # Get all water sources (active and inactive) and filter to 'Borehole' types with STATIC purpose only
        sources = self.db.get_water_sources(active_only=False)
        rows = []
        for s in sources:
            type_name = (s.get('type_name') or '').lower()
            purpose = (s.get('source_purpose') or 'ABSTRACTION').upper()
            if 'borehole' in type_name and purpose == 'STATIC':
                rows.append(s)

        # Clear tree
        for i in self.bh_reg_tree.get_children():
            self.bh_reg_tree.delete(i)

        # Insert
        for s in rows:
            status = 'Active' if s.get('active', 1) == 1 else 'Inactive'
            self.bh_reg_tree.insert('', 'end', values=(
                s['source_id'], s.get('source_code'), s.get('source_name'),
                s.get('source_purpose'), s.get('type_name'), status
            ))

    def _bh_reg_add(self):
        """Add a static borehole to register (minimal dialog)."""
        dlg = tk.Toplevel(self.container)
        dlg.title("Add Static Borehole")
        dlg.transient(self.container.winfo_toplevel())
        dlg.grab_set()

        ttk.Label(dlg, text="Code:").grid(row=0, column=0, sticky='e', padx=8, pady=6)
        ttk.Label(dlg, text="Name:").grid(row=1, column=0, sticky='e', padx=8, pady=6)

        code_var = tk.StringVar()
        name_var = tk.StringVar()
        ttk.Entry(dlg, textvariable=code_var, width=28).grid(row=0, column=1, padx=8, pady=6)
        ttk.Entry(dlg, textvariable=name_var, width=28).grid(row=1, column=1, padx=8, pady=6)

        btn_frame = ttk.Frame(dlg)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 6))

        def on_save():
            code = code_var.get().strip()
            name = name_var.get().strip()
            if not code or not name:
                messagebox.showwarning("Missing", "Please enter both code and name")
                return
            # Check if source already exists (even if inactive)
            try:
                existing_sources = self.db.get_water_sources(active_only=False)
                for s in existing_sources:
                    if s.get('source_code') == code or s.get('source_name') == name:
                        if s.get('active') == 0:
                            if messagebox.askyesno("Inactive Exists", f"Borehole '{code}' or '{name}' exists but is inactive.\nDo you want to activate it?"):
                                self.db.activate_water_source(s['source_id'])
                                self._bh_reg_load()
                                dlg.destroy()
                            return
                        else:
                            messagebox.showerror("Already Exists", f"Borehole '{code}' or '{name}' already exists and is active.")
                            return
            except Exception:
                pass
            try:
                # find borehole type_id
                types = self.db.get_source_types()
                borehole_type_id = None
                for t in types:
                    if 'borehole' in (t.get('type_name','') or '').lower() or 'borehole' in (t.get('type_code','') or '').lower():
                        borehole_type_id = t['type_id']
                        break
                if borehole_type_id is None and types:
                    borehole_type_id = types[0]['type_id']  # fallback
                self.db.add_water_source(
                    source_code=code, source_name=name, type_id=borehole_type_id,
                    source_purpose='STATIC', active=1, created_by='ui'
                )
                self._bh_reg_load()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add borehole: {e}")

        ttk.Button(btn_frame, text="Save", command=on_save, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side='left', padx=5)

    def _bh_reg_activate(self):
        """Activate an inactive static borehole."""
        sel = self.bh_reg_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a borehole to activate")
            return
        vals = self.bh_reg_tree.item(sel[0], 'values')
        source_id, code, status = int(vals[0]), vals[1], vals[5]
        if status == 'Active':
            messagebox.showinfo("Already Active", f"Borehole '{code}' is already active.")
            return
        try:
            self.db.activate_water_source(source_id)
            self._bh_reg_load()
            messagebox.showinfo("Success", f"Borehole '{code}' activated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to activate: {e}")

    def _bh_reg_deactivate(self):
        """Deactivate an active static borehole."""
        sel = self.bh_reg_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a borehole to deactivate")
            return
        vals = self.bh_reg_tree.item(sel[0], 'values')
        source_id, code, status = int(vals[0]), vals[1], vals[5]
        if status == 'Inactive':
            messagebox.showinfo("Already Inactive", f"Borehole '{code}' is already inactive.")
            return
        if not messagebox.askyesno("Confirm", f"Deactivate borehole '{code}'?"):
            return
        try:
            self.db.delete_water_source(source_id)
            self._bh_reg_load()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to deactivate: {e}")

    def _bh_reg_delete(self):
        sel = self.bh_reg_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a borehole to delete")
            return
        vals = self.bh_reg_tree.item(sel[0], 'values')
        source_id = int(vals[0])
        code = vals[1]
        if not messagebox.askyesno("Confirm", f"Delete static borehole '{code}' from register?\nThis will deactivate it in water sources."):
            return
        try:
            self.db.delete_water_source(source_id)
            self._bh_reg_load()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")
        
    # ==================== TAB 2: BOREHOLE MONITORING ====================
    def _create_borehole_monitoring_tab(self):
        """Tab for borehole monitoring data"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🕳️ Borehole Monitoring")

        self.bh_mon_tabs = ttk.Notebook(tab)
        self.bh_mon_tabs.pack(fill='both', expand=True)

        # Register sub-tab
        reg = ttk.Frame(self.bh_mon_tabs, padding=10)
        self.bh_mon_tabs.add(reg, text="Register")
        self._create_bh_mon_register_tab(reg)

        # Visualize tab
        viz = ttk.Frame(self.bh_mon_tabs, padding=10)
        self.bh_mon_tabs.add(viz, text="Visualize")
        self._create_bh_mon_visualize_tab(viz)

    def _create_bh_mon_register_tab(self, parent: ttk.Frame):
        ttk.Label(parent, text="Registered Monitoring Boreholes", font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0,8))
        bar = ttk.Frame(parent)
        bar.pack(fill='x', pady=(0,8))
        ttk.Button(bar, text="➕ Add", command=self._bh_mon_reg_add, style='Accent.TButton').pack(side='left')
        ttk.Button(bar, text="✅ Activate", command=self._bh_mon_reg_activate).pack(side='left', padx=(6,0))
        ttk.Button(bar, text="❌ Deactivate", command=self._bh_mon_reg_deactivate).pack(side='left', padx=(6,0))
        ttk.Button(bar, text="🔄 Refresh", command=self._bh_mon_reg_load).pack(side='left', padx=(6,0))
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        vsb = ttk.Scrollbar(frame, orient='vertical'); vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(frame, orient='horizontal'); hsb.pack(side='bottom', fill='x')
        self.bh_mon_reg_tree = ttk.Treeview(frame, columns=('source_id','source_code','source_name','purpose','type','status'),
                                            show='headings', yscrollcommand=vsb.set, xscrollcommand=hsb.set, selectmode='browse')
        vsb.config(command=self.bh_mon_reg_tree.yview); hsb.config(command=self.bh_mon_reg_tree.xview)
        for col, title, width in [('source_code','Code',120),('source_name','Name',220),('purpose','Purpose',90),('type','Type',120),('status','Status',80)]:
            self.bh_mon_reg_tree.heading(col, text=title); self.bh_mon_reg_tree.column(col, width=width, anchor='w')
        self.bh_mon_reg_tree.column('source_id', width=1, stretch=False); self.bh_mon_reg_tree.heading('source_id', text='')
        self.bh_mon_reg_tree.pack(fill='both', expand=True)
        self._bh_mon_reg_load()

    def _bh_mon_reg_load(self):
        rows = []
        try:
            sources = self.db.get_water_sources(active_only=False)
            for s in sources:
                type_name = (s.get('type_name') or '').lower()
                purpose = (s.get('source_purpose') or 'ABSTRACTION').upper()
                if 'borehole' in type_name and purpose == 'MONITORING':
                    rows.append(s)
        except Exception:
            rows = []
        for i in self.bh_mon_reg_tree.get_children():
            self.bh_mon_reg_tree.delete(i)
        for s in rows:
            status = 'Active' if s.get('active', 1) == 1 else 'Inactive'
            self.bh_mon_reg_tree.insert('', 'end', values=(s['source_id'], s.get('source_code'), s.get('source_name'), s.get('source_purpose'), s.get('type_name'), status))

    def _bh_mon_reg_add(self):
        dlg = tk.Toplevel(self.container); dlg.title("Add Monitoring Borehole"); dlg.transient(self.container.winfo_toplevel()); dlg.grab_set()
        ttk.Label(dlg, text="Code:").grid(row=0, column=0, sticky='e', padx=8, pady=6)
        ttk.Label(dlg, text="Name:").grid(row=1, column=0, sticky='e', padx=8, pady=6)
        ttk.Label(dlg, text="Type:").grid(row=2, column=0, sticky='e', padx=8, pady=6)
        v_code = tk.StringVar(); v_name = tk.StringVar();
        e_code = ttk.Entry(dlg, textvariable=v_code, width=28); e_code.grid(row=0, column=1, padx=8, pady=6)
        e_name = ttk.Entry(dlg, textvariable=v_name, width=28); e_name.grid(row=1, column=1, padx=8, pady=6)
        # Type list filtered to borehole-like
        types = self.db.get_source_types()
        borehole_types = [t for t in types if 'borehole' in (t.get('type_name','') or '').lower() or 'borehole' in (t.get('type_code','') or '').lower()]
        type_names = [t['type_name'] for t in (borehole_types or types)]
        v_type = tk.StringVar(value=type_names[0] if type_names else '')
        cb = ttk.Combobox(dlg, textvariable=v_type, values=type_names, state='readonly', width=25); cb.grid(row=2, column=1, padx=8, pady=6)
        btns = ttk.Frame(dlg); btns.grid(row=3, column=0, columnspan=2, pady=(10,6))
        def save():
            code, name = v_code.get().strip(), v_name.get().strip()
            if not code or not name:
                messagebox.showwarning("Missing", "Please enter both code and name"); return
            # Check if source already exists (even if inactive)
            try:
                existing_sources = self.db.get_water_sources(active_only=False)
                for s in existing_sources:
                    if s.get('source_code') == code or s.get('source_name') == name:
                        if s.get('active') == 0:
                            if messagebox.askyesno("Inactive Exists", f"Borehole '{code}' or '{name}' exists but is inactive.\nDo you want to activate it?"):
                                self.db.activate_water_source(s['source_id'])
                                self._bh_mon_reg_load()
                                dlg.destroy()
                            return
                        else:
                            messagebox.showerror("Already Exists", f"Borehole '{code}' or '{name}' already exists and is active.")
                            return
            except Exception:
                pass
            selected = next((t for t in (borehole_types or types) if t['type_name']==v_type.get()), None)
            type_id = selected['type_id'] if selected else (types[0]['type_id'] if types else None)
            try:
                self.db.add_water_source(source_code=code, source_name=name, type_id=type_id, source_purpose='MONITORING', active=1, created_by='ui')
                self._bh_mon_reg_load(); dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add: {e}")
        ttk.Button(btns, text="Save", command=save, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side='left', padx=5)

    def _bh_mon_reg_activate(self):
        """Activate an inactive monitoring borehole."""
        sel = self.bh_mon_reg_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a borehole to activate"); return
        vals = self.bh_mon_reg_tree.item(sel[0], 'values')
        sid, code, status = int(vals[0]), vals[1], vals[5]
        if status == 'Active':
            messagebox.showinfo("Already Active", f"Borehole '{code}' is already active.")
            return
        try:
            self.db.activate_water_source(sid); self._bh_mon_reg_load()
            messagebox.showinfo("Success", f"Borehole '{code}' activated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to activate: {e}")

    def _bh_mon_reg_deactivate(self):
        """Deactivate an active monitoring borehole."""
        sel = self.bh_mon_reg_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a borehole to deactivate"); return
        vals = self.bh_mon_reg_tree.item(sel[0], 'values')
        sid, code, status = int(vals[0]), vals[1], vals[5]
        if status == 'Inactive':
            messagebox.showinfo("Already Inactive", f"Borehole '{code}' is already inactive.")
            return
        if not messagebox.askyesno("Confirm", f"Deactivate borehole '{code}'?"):
            return
        try:
            self.db.delete_water_source(sid); self._bh_mon_reg_load()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to deactivate: {e}")

    def _bh_mon_reg_delete(self):
        sel = self.bh_mon_reg_tree.selection()
        if not sel: messagebox.showinfo("Select", "Select a row to delete"); return
        vals = self.bh_mon_reg_tree.item(sel[0], 'values'); sid, code = int(vals[0]), vals[1]
        if not messagebox.askyesno("Confirm", f"Delete monitoring borehole '{code}'?\nThis will deactivate it."):
            return
        try:
            self.db.delete_water_source(sid); self._bh_mon_reg_load()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")
        
    def _create_bh_mon_visualize_tab(self, parent: ttk.Frame):
        """Create visualize tab for borehole monitoring with controls."""
        # Control panel
        control_frame = ttk.LabelFrame(parent, text="Data Source", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))

        # Single file row
        ttk.Label(control_frame, text="Excel File:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.bh_mon_file_path = tk.StringVar(value="Not loaded")
        ttk.Entry(control_frame, textvariable=self.bh_mon_file_path, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Button(control_frame, text="📁 Select File", command=lambda: self._select_bh_mon_file()).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(control_frame, text="📊 Load & Visualize", command=lambda: self._load_bh_mon_file(), style='Accent.TButton').grid(row=0, column=3)

        # Directory row
        ttk.Label(control_frame, text="Directory:").grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(8, 0))
        self.bh_mon_dir = tk.StringVar(value="Not set")
        ttk.Entry(control_frame, textvariable=self.bh_mon_dir, state='readonly', width=60).grid(row=1, column=1, sticky='ew', padx=(0, 10), pady=(8, 0))
        ttk.Button(control_frame, text="📂 Select Directory", command=self._select_bh_mon_directory).grid(row=1, column=2, padx=(0,5), pady=(8,0))
        self.bh_mon_scan_btn = ttk.Button(control_frame, text="🔎 Scan Directory & Load", command=self._scan_and_load_bh_mon, style='Accent.TButton')
        self.bh_mon_scan_btn.grid(row=1, column=3, pady=(8,0))

        # Period filters
        period_frame = ttk.Frame(control_frame)
        period_frame.grid(row=2, column=0, columnspan=4, sticky='ew', pady=(10,0))
        ttk.Label(period_frame, text="Period:").pack(side='left')
        self.bh_mon_from_year = tk.StringVar(value="All")
        self.bh_mon_from_month = tk.StringVar(value="All")
        self.bh_mon_to_year = tk.StringVar(value="All")
        self.bh_mon_to_month = tk.StringVar(value="All")
        years = ['All'] + [str(y) for y in range(2015, 2036)]
        months = ['All','01','02','03','04','05','06','07','08','09','10','11','12']
        ttk.Label(period_frame, text=" From ").pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.bh_mon_from_year, values=years, width=6, state='readonly').pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.bh_mon_from_month, values=months, width=4, state='readonly').pack(side='left', padx=(4,8))
        ttk.Label(period_frame, text=" To ").pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.bh_mon_to_year, values=years, width=6, state='readonly').pack(side='left')
        ttk.Combobox(period_frame, textvariable=self.bh_mon_to_month, values=months, width=4, state='readonly').pack(side='left', padx=(4,8))

        # Chart and filter options
        opts_frame = ttk.Frame(control_frame)
        opts_frame.grid(row=3, column=0, columnspan=4, sticky='ew', pady=(8,0))
        self.bh_mon_chart_type = tk.StringVar(value='Line')
        self.bh_mon_selected_param = tk.StringVar(value='')
        self.bh_mon_only_registered = tk.BooleanVar(value=True)
        self.bh_mon_preview_cap = tk.IntVar(value=100)
        self.bh_mon_single_borehole = tk.BooleanVar(value=False)
        self.bh_mon_single_borehole_name = tk.StringVar(value='')
        self.bh_mon_aquifer_filter = tk.StringVar(value='All')
        ttk.Label(opts_frame, text='Chart:').pack(side='left')
        ttk.Combobox(opts_frame, textvariable=self.bh_mon_chart_type, values=['Line','Bar','Box'], width=8, state='readonly').pack(side='left', padx=(4,10))
        ttk.Label(opts_frame, text='Parameter:').pack(side='left')
        self.bh_mon_param_combo = ttk.Combobox(opts_frame, textvariable=self.bh_mon_selected_param, values=[], width=20, state='readonly')
        self.bh_mon_param_combo.pack(side='left', padx=(4,10))
        ttk.Checkbutton(opts_frame, text='Only registered', variable=self.bh_mon_only_registered).pack(side='left', padx=(6,0))
        ttk.Label(opts_frame, text='Aquifer').pack(side='left', padx=(10,0))
        ttk.Combobox(opts_frame, textvariable=self.bh_mon_aquifer_filter, values=['All', 'Shallow Aquifer', 'Deep Aquifer'], width=14, state='readonly').pack(side='left', padx=(4,0))
        ttk.Label(opts_frame, text='Preview cap').pack(side='left', padx=(10,0))
        try:
            ttk.Spinbox(opts_frame, from_=20, to=1000, textvariable=self.bh_mon_preview_cap, width=5).pack(side='left', padx=(4,0))
        except Exception:
            tk.Spinbox(opts_frame, from_=20, to=1000, textvariable=self.bh_mon_preview_cap, width=5).pack(side='left', padx=(4,0))
        ttk.Checkbutton(opts_frame, text='Single borehole', variable=self.bh_mon_single_borehole).pack(side='left', padx=(12,0))
        self.bh_mon_single_borehole_combo = ttk.Combobox(opts_frame, textvariable=self.bh_mon_single_borehole_name, values=[], width=16, state='readonly')
        self.bh_mon_single_borehole_combo.pack(side='left', padx=(6,0))

        # Progress row
        prog_frame = ttk.Frame(control_frame)
        prog_frame.grid(row=4, column=0, columnspan=4, sticky='ew', pady=(8,0))
        self.bh_mon_progress = ttk.Progressbar(prog_frame, mode='determinate')
        self.bh_mon_progress.pack(side='left', fill='x', expand=True, padx=(0,8))
        self.bh_mon_progress_label = ttk.Label(prog_frame, text="")
        self.bh_mon_progress_label.pack(side='left')
        ttk.Button(prog_frame, text='📈 Generate Charts', command=self._generate_bh_mon_charts, style='Accent.TButton').pack(side='left', padx=(10,0))
        ttk.Button(prog_frame, text='🧹 Clear Cache', command=self._bh_mon_clear_cache).pack(side='left', padx=(6,0))
        ttk.Button(prog_frame, text='🔄 Rescan', command=self._scan_and_load_bh_mon).pack(side='left', padx=(6,0))
        self._bh_mon_scan_thread = None

        control_frame.columnconfigure(1, weight=1)

        # Info box
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', pady=(0, 10))
        info_label = ttk.Label(info_frame,
                               text="ℹ️  Displays borehole monitoring parameters. Only registered monitoring boreholes are included.",
                               foreground='#1976D2', font=('Segoe UI', 9, 'italic'))
        info_label.pack(anchor='w')

        # Content area
        self.bh_mon_content = ttk.Frame(parent)
        self.bh_mon_content.pack(fill='both', expand=True)
        placeholder = ttk.Label(self.bh_mon_content,
                                text="Select a directory and click 'Scan Directory & Load' to display data",
                                foreground='#999', font=('Segoe UI', 11))
        placeholder.pack(expand=True)

    def _select_excel_file(self, data_type: str):
        """Open file dialog to select Excel file"""
        filepath = filedialog.askopenfilename(
            title=f"Select {data_type.replace('_', ' ').title()} Excel File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            self.excel_files[data_type] = filepath
            
            # Update the corresponding path variable
            if data_type == 'borehole_static':
                self.borehole_static_path.set(Path(filepath).name)
            elif data_type == 'borehole_monitoring':
                self.borehole_monitoring_path.set(Path(filepath).name)
            elif data_type == 'pcd':
                self.pcd_path.set(Path(filepath).name)
            elif data_type == 'return_water_dam':
                self.rwd_path.set(Path(filepath).name)
            elif data_type == 'sewage_treatment':
                self.sewage_path.set(Path(filepath).name)
            elif data_type == 'river_monitoring':
                self.river_path.set(Path(filepath).name)
            
            self.status_label.config(text=f"Selected: {Path(filepath).name}")
            logger.info(f"Selected {data_type} file: {filepath}")
            
    def _load_borehole_static_data(self):
        """Load and visualize borehole static levels data"""
        if not self.excel_files['borehole_static']:
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
            
        try:
            self.status_label.config(text="Loading borehole static data...")
            # Clear existing content
            for widget in self.borehole_static_content.winfo_children():
                widget.destroy()
            
            # Parse according to specified mapping
            parsed = self._parse_static_levels_excel(self.excel_files['borehole_static'])
            if parsed.empty:
                raise ValueError("No static level data found using the provided mapping.")

            # Filter to registered static/monitoring boreholes
            if bool(self.only_registered.get()):
                registered = self._get_registered_borehole_names()
                if registered:
                    parsed = parsed[parsed['borehole_norm'].isin(registered)]
            # Apply single-borehole filter if enabled
            if bool(self.single_borehole.get()):
                name = (self.single_borehole_name.get() or '').strip()
                if name:
                    parsed = parsed[parsed['borehole'] == name]
            
            # Summarize
            info_text = f"✓ Parsed {len(parsed)} records across {parsed['borehole'].nunique()} boreholes"
            if registered:
                info_text += f" (filtered by {len(registered)} registered)"
            info_label = ttk.Label(self.borehole_static_content,
                                   text=info_text,
                                   foreground='#2E7D32', font=('Segoe UI', 10, 'bold'))
            info_label.pack(pady=(6, 6), anchor='w')

            # Download chart button at top
            btn_bar = ttk.Frame(self.borehole_static_content)
            btn_bar.pack(fill='x', padx=6, pady=(0, 6))
            ttk.Button(btn_bar, text='💾 Save Chart', command=self._save_current_chart, width=12).pack(side='right')

            # Plot according to options
            self._plot_static_levels(parsed)
            # Update single-borehole list with available names
            try:
                names = sorted([str(n) for n in parsed['borehole'].dropna().unique().tolist()])
                self.single_borehole_combo['values'] = names
                if self.single_borehole_name.get() and self.single_borehole_name.get() not in names:
                    self.single_borehole_name.set('')
            except Exception:
                pass

            # Data preview
            preview_frame = ttk.LabelFrame(self.borehole_static_content,
                                           text="Parsed Data", padding=8)
            preview_frame.pack(fill='both', expand=True, padx=6, pady=6)

            tree = ttk.Treeview(preview_frame, height=10)
            tree.pack(fill='both', expand=True)
            vsb = ttk.Scrollbar(preview_frame, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(preview_frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.pack(side='right', fill='y')
            hsb.pack(side='bottom', fill='x')

            cols = ['borehole', 'date', 'level']
            tree['columns'] = cols
            tree['show'] = 'headings'
            for c, w in [('borehole', 200), ('date', 120), ('level', 100)]:
                tree.heading(c, text=c.title())
                tree.column(c, width=w, anchor='w')
            # Insert preview rows up to cap
            cap = int(self.preview_cap.get() or 100)
            for _, r in parsed.head(cap).iterrows():
                tree.insert('', 'end', values=(r['borehole'], r['date'].date(), r['level']))

            self.status_label.config(text=f"Loaded and visualized {len(parsed)} static level records from {Path(self.excel_files['borehole_static']).name}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")
            logger.error(f"Error loading borehole static data: {e}")
            self.status_label.config(text="Error loading data")

    def _select_bh_static_directory(self):
        directory = filedialog.askdirectory(title="Select Static Boreholes Directory")
        if directory:
            self.borehole_static_dir.set(directory)
            self.status_label.config(text=f"Directory selected: {Path(directory).name}")
            # init or reset cache for directory
            self.data_cache.setdefault('bh_static_index', {'dir': directory, 'files': {}, 'combined': None})
            if self.data_cache['bh_static_index']['dir'] != directory:
                self.data_cache['bh_static_index'] = {'dir': directory, 'files': {}, 'combined': None}

    def _scan_and_load_bh_static(self):
        """Scan the selected directory, index files (incremental), then filter by period and visualize."""
        directory = self.borehole_static_dir.get()
        if not directory or directory == 'Not set':
            messagebox.showwarning("No Directory", "Please select a directory first")
            return
        if self._bh_scan_thread and self._bh_scan_thread.is_alive():
            messagebox.showinfo("Please wait", "A scan is already running")
            return
        # Gather file list first to set progress maximum
        paths = []
        for ext in ('*.xls','*.xlsx'):
            paths.extend(list(Path(directory).glob(ext)))
        if not paths:
            messagebox.showinfo("No Files", "No .xls/.xlsx files found in directory")
            return
        # Init progress UI
        self.bh_progress['maximum'] = len(paths)
        self.bh_progress['value'] = 0
        self.bh_progress_label.config(text=f"0/{len(paths)}")
        self.bh_scan_btn.config(state='disabled')
        self.status_label.config(text="Scanning directory for static level files...")

        def worker(file_list):
            try:
                cache = self.data_cache.setdefault('bh_static_index', {'dir': directory, 'files': {}, 'combined': None})
                cache['dir'] = directory
                files = cache['files']
                combined_list = []
                processed = 0
                for fp in file_list:
                    try:
                        mtime = fp.stat().st_mtime
                        entry = files.get(str(fp))
                        if entry and entry.get('mtime') == mtime:
                            df = entry.get('df')
                        else:
                            df = self._parse_static_levels_excel(str(fp))
                            if df is not None and not df.empty:
                                df['source_file'] = str(fp)
                            files[str(fp)] = {'mtime': mtime, 'df': df}
                        if df is not None and not df.empty:
                            combined_list.append(df)
                    except Exception as e:
                        logger.warning(f"Skip file {fp}: {e}")
                    finally:
                        processed += 1
                        def upd(p=processed, total=len(file_list)):
                            self.bh_progress['value'] = p
                            self.bh_progress_label.config(text=f"{p}/{total}")
                        self.container.after(0, upd)
                combined = pd.concat(combined_list, ignore_index=True) if combined_list else pd.DataFrame(columns=['borehole','date','level','borehole_norm','source_file'])
                cache['combined'] = combined
            finally:
                def on_done():
                    self._bh_scan_thread = None
                    self.bh_scan_btn.config(state='normal')
                    self._render_bh_static_from_df(directory)
                self.container.after(0, on_done)

        self._bh_scan_thread = threading.Thread(target=worker, args=(paths,), daemon=True)
        self._bh_scan_thread.start()

    def _bh_clear_cache(self):
        """Clear the cached index for static borehole directory and reset progress UI."""
        try:
            current_dir = self.borehole_static_dir.get()
            self.data_cache['bh_static_index'] = {'dir': current_dir, 'files': {}, 'combined': None}
            self.bh_progress['value'] = 0
            self.bh_progress_label.config(text="")
            self.status_label.config(text="Cache cleared for static levels")
            # Also clear current rendered content
            for widget in self.borehole_static_content.winfo_children():
                widget.destroy()
            placeholder = ttk.Label(self.borehole_static_content,
                                    text="Select an Excel file or scan a directory to display data",
                                    foreground='#999', font=('Segoe UI', 11))
            placeholder.pack(expand=True)
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            messagebox.showerror("Error", f"Failed to clear cache: {e}")

    def _index_static_levels_directory(self, directory: str):
        """Index directory of Excel files incrementally and cache a combined DataFrame."""
        cache = self.data_cache.setdefault('bh_static_index', {'dir': directory, 'files': {}, 'combined': None})
        cache['dir'] = directory
        files = cache['files']
        combined_list = []
        for ext in ('*.xls','*.xlsx'):
            for fp in Path(directory).glob(ext):
                try:
                    mtime = fp.stat().st_mtime
                    entry = files.get(str(fp))
                    if entry and entry.get('mtime') == mtime:
                        df = entry.get('df')
                    else:
                        df = self._parse_static_levels_excel(str(fp))
                        if not df.empty:
                            df['source_file'] = str(fp)
                        files[str(fp)] = {'mtime': mtime, 'df': df}
                    if df is not None and not df.empty:
                        combined_list.append(df)
                except Exception as e:
                    logger.warning(f"Skip file {fp}: {e}")
                    continue
        combined = pd.concat(combined_list, ignore_index=True) if combined_list else pd.DataFrame(columns=['borehole','date','level','borehole_norm','source_file'])
        cache['combined'] = combined

    def _filter_df_by_period(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter a parsed dataframe by selected From/To period if set."""
        fy, fm = self.period_from_year.get(), self.period_from_month.get()
        ty, tm = self.period_to_year.get(), self.period_to_month.get()
        if fy == 'All' and ty == 'All':
            return df
        # Build start and end dates
        if fy == 'All':
            start = df['date'].min()
        else:
            sm = 1 if fm == 'All' else int(fm)
            start = datetime(int(fy), sm, 1)
        if ty == 'All':
            end = df['date'].max()
        else:
            em = 12 if tm == 'All' else int(tm)
            last_day = monthrange(int(ty), em)[1]
            end = datetime(int(ty), em, last_day, 23, 59, 59)
        return df[(df['date'] >= start) & (df['date'] <= end)]

    def _render_bh_static_from_df(self, directory: str):
        """Render charts and preview from cached combined DF after scan completes."""
        try:
            df = self.data_cache.get('bh_static_index', {}).get('combined')
            if df is None or df.empty:
                messagebox.showinfo("No Data", "No static level data found in directory")
                return
            # Filter by period
            df = self._filter_df_by_period(df)
            # Clean content
            for widget in self.borehole_static_content.winfo_children():
                widget.destroy()
            # Filter by register
            if bool(self.only_registered.get()):
                registered = self._get_registered_borehole_names()
                if registered:
                    df = df[df['borehole_norm'].isin(registered)]
            # Apply single-borehole filter if enabled
            if bool(self.single_borehole.get()):
                name = (self.single_borehole_name.get() or '').strip()
                if name:
                    df = df[df['borehole'] == name]
            # Info
            info_text = f"✓ Directory parsed: {len(df)} records across {df['borehole'].nunique()} boreholes"
            ttk.Label(self.borehole_static_content, text=info_text, foreground='#2E7D32', font=('Segoe UI', 10, 'bold')).pack(pady=(6,6), anchor='w')
            # Update single-borehole list with available names
            try:
                names = sorted([str(n) for n in df['borehole'].dropna().unique().tolist()])
                self.single_borehole_combo['values'] = names
                if self.single_borehole_name.get() and self.single_borehole_name.get() not in names:
                    self.single_borehole_name.set('')
            except Exception:
                pass
            # Store df for chart generation
            self._bh_static_current_df = df
            # Preview table
            preview = ttk.LabelFrame(self.borehole_static_content, text='Parsed Data', padding=8)
            preview.pack(fill='both', expand=True, padx=6, pady=6)
            tree = ttk.Treeview(preview, height=10)
            tree.pack(fill='both', expand=True)
            vsb = ttk.Scrollbar(preview, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(preview, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.pack(side='right', fill='y')
            hsb.pack(side='bottom', fill='x')
            cols = ['borehole','date','level','source_file']
            tree['columns'] = cols
            tree['show'] = 'headings'
            for c, w in [('borehole', 200), ('date', 120), ('level', 100)]:
                tree.heading(c, text=c.title())
                tree.column(c, width=w, anchor='w')
            cap = int(self.preview_cap.get() or 100)
            for _, r in df.head(cap).iterrows():
                src = Path(r['source_file']).name if 'source_file' in r and pd.notna(r['source_file']) else ''
                tree.insert('', 'end', values=(r['borehole'], getattr(r['date'],'date',lambda: r['date'])(), r['level'], src))
            self.status_label.config(text=f"Scanned and loaded {len(df)} records from {Path(directory).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Render failed: {e}")
            logger.error(f"Render error: {e}")

    def _generate_bh_static_charts(self):
        """Generate charts for static data."""
        if not hasattr(self, '_bh_static_current_df') or self._bh_static_current_df is None or self._bh_static_current_df.empty:
            messagebox.showinfo("No Data", "Please load data first before generating charts")
            return
        # Apply filters to the dataframe
        df = self._bh_static_current_df.copy()
        # Filter by register
        if bool(self.only_registered.get()):
            registered = self._get_registered_borehole_names()
            if registered:
                df = df[df['borehole_norm'].isin(registered)]
        # Apply single-borehole filter if enabled
        if bool(self.single_borehole.get()):
            name = (self.single_borehole_name.get() or '').strip()
            if name:
                df = df[df['borehole'] == name]
        # Period filter
        df = self._filter_df_by_period(df)
        if df.empty:
            messagebox.showinfo("No Data", "No data matches the current filters")
            return
        # Clear existing chart widgets if present
        if hasattr(self, '_bh_static_chart_btn_bar') and self._bh_static_chart_btn_bar.winfo_exists():
            self._bh_static_chart_btn_bar.destroy()
        if hasattr(self, '_bh_static_chart_frame') and self._bh_static_chart_frame.winfo_exists():
            self._bh_static_chart_frame.destroy()
        # Find preview table
        preview_widget = None
        for widget in self.borehole_static_content.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                try:
                    if 'Parsed Data' in str(widget.cget('text')):
                        preview_widget = widget
                        break
                except:
                    pass
        # Add download button before preview
        self._bh_static_chart_btn_bar = ttk.Frame(self.borehole_static_content)
        if preview_widget:
            self._bh_static_chart_btn_bar.pack(fill='x', padx=6, pady=(0, 6), before=preview_widget)
        else:
            self._bh_static_chart_btn_bar.pack(fill='x', padx=6, pady=(0, 6))
        ttk.Button(self._bh_static_chart_btn_bar, text='💾 Save Chart', command=self._save_current_chart, width=12).pack(side='right')
        # Create chart frame before preview
        self._bh_static_chart_frame = ttk.Frame(self.borehole_static_content)
        if preview_widget:
            self._bh_static_chart_frame.pack(fill='both', expand=False, padx=6, pady=6, before=preview_widget)
        else:
            self._bh_static_chart_frame.pack(fill='both', expand=False, padx=6, pady=6)
        # Plot chart with filtered data
        self._plot_static_levels(df)

    def _plot_static_levels(self, df: pd.DataFrame):
        """Plot static levels using selected chart options."""
        if df is None or df.empty:
            return
        # Determine target container
        if hasattr(self, '_bh_static_chart_frame') and self._bh_static_chart_frame.winfo_exists():
            target = self._bh_static_chart_frame
        else:
            target = self.borehole_static_content
        chart_type = (self.chart_type.get() or 'Line')
        use_ma = bool(self.use_ma.get())
        try:
            win = int(self.ma_window.get())
        except Exception:
            win = 3
        # Calculate responsive figure size based on content area
        try:
            content_width = target.winfo_width()
            # Use 90% of content width, min 600px, max 1200px
            fig_width_px = max(600, min(1200, int(content_width * 0.9)))
            fig_width_inch = fig_width_px / 100  # 100 DPI
            fig_height_inch = fig_width_inch * 0.5  # Maintain aspect ratio
        except Exception:
            # Fallback if window not yet realized
            fig_width_inch, fig_height_inch = 9, 4.5
        fig = Figure(figsize=(fig_width_inch, fig_height_inch), dpi=100)
        ax = fig.add_subplot(111)
        for name, g in df.groupby('borehole'):
            g = g.sort_values('date')
            y = g['level']
            label = name
            if use_ma and win and win > 1:
                y = y.rolling(win, min_periods=1).mean()
                label = f"{name} (MA{win})"
            if chart_type == 'Bar':
                # Width in days for datetime axis
                ax.bar(g['date'], y, width=8, alpha=0.6, label=label)
            else:
                ax.plot(g['date'], y, marker='o', label=label)
        ax.set_title('Static Water Levels')
        ax.set_xlabel('Date')
        ax.set_ylabel('Level (m)')
        # Place legend outside to the right
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0., fontsize=8)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        # Wrap canvas in scrollable frame
        canvas_frame = ttk.Frame(target)
        canvas_frame.pack(fill='both', expand=False, padx=6, pady=6)
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        # Keep a reference for saving
        self._last_plot_figure = fig

    def _get_registered_borehole_names(self):
        """Return a set of normalized registered static/monitoring borehole names."""
        names = set()
        try:
            sources = self.db.get_water_sources(active_only=True)
            for s in sources:
                type_name = (s.get('type_name') or '').lower()
                purpose = (s.get('source_purpose') or 'ABSTRACTION').upper()
                if 'borehole' in type_name and purpose in ('STATIC', 'MONITORING'):
                    nm = str(s.get('source_name') or '').strip().upper()
                    if nm:
                        names.add(nm)
        except Exception:
            pass
        return names

    def _save_current_chart(self):
        """Save the last plotted chart to an image file."""
        try:
            if not hasattr(self, '_last_plot_figure') or self._last_plot_figure is None:
                messagebox.showinfo("No Chart", "There is no chart to save yet.")
                return
            fpath = filedialog.asksaveasfilename(
                title="Save Chart",
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg *.jpeg"), ("PDF", "*.pdf")]
            )
            if not fpath:
                return
            # Choose backend by extension
            ext = Path(fpath).suffix.lower()
            if ext in ('.png', '.jpg', '.jpeg'):
                self._last_plot_figure.savefig(fpath, bbox_inches='tight', dpi=150)
            elif ext == '.pdf':
                self._last_plot_figure.savefig(fpath, bbox_inches='tight')
            else:
                # default to png
                self._last_plot_figure.savefig(fpath, bbox_inches='tight', dpi=150)
            messagebox.showinfo("Saved", f"Chart saved to {Path(fpath).name}")
        except Exception as e:
            logger.error(f"Save chart failed: {e}")
            messagebox.showerror("Error", f"Failed to save chart: {e}")

    def _parse_static_levels_excel(self, filepath: str) -> pd.DataFrame:
        """Parse static level sheet with robust detection of shifted rows/columns.

        Heuristic detection:
        - Treat any non-empty text cell as a potential borehole name cell (r,c).
        - Validate block below it: rows r+1.. (2-6 rows), same column c must be dates,
          adjacent column c+1 must be numeric levels. Stop at first failure.
        - Collect all valid blocks across all columns/rows. De-duplicate rows.
        Returns DataFrame columns: borehole, date, level, borehole_norm
        """
        # Load with best-effort engine fallback
        try:
            sheet = pd.read_excel(filepath, header=None)
        except Exception as e:
            try:
                sheet = pd.read_excel(filepath, header=None, engine='xlrd')
            except Exception:
                raise e

        nrows, ncols = sheet.shape

        def try_parse_date(val):
            if pd.isna(val):
                return None
            v = val
            if isinstance(v, str):
                v = v.replace('\xa0', '').strip()
                if not v:
                    return None
            # Direct datetime parse
            try:
                return pd.to_datetime(v).to_pydatetime()
            except Exception:
                pass
            # Excel serial fallback
            try:
                return pd.to_datetime("1899-12-30") + pd.to_timedelta(float(v), unit='D')
            except Exception:
                return None

        def is_number(val):
            if pd.isna(val):
                return False
            try:
                float(val)
                return True
            except Exception:
                return False

        results = []
        seen = set()  # (name, date)
        # Scan all cells for potential name headers
        for r0 in range(nrows):
            for c0 in range(ncols):
                name_val = sheet.iat[r0, c0]
                if pd.isna(name_val):
                    continue
                # A name is a short-to-medium string; skip obvious non-text
                if not isinstance(name_val, str):
                    # Accept non-string only if it looks like a code when casted
                    try:
                        name_str = str(name_val).strip()
                    except Exception:
                        continue
                else:
                    name_str = name_val.strip()
                if not name_str:
                    continue
                # Skip if this cell itself looks like a date or a number (likely a data row, not header)
                if try_parse_date(name_val) is not None:
                    continue
                if is_number(name_val):
                    continue
                # Validate that below we have date/level columns (c0 is date, c0+1 is level)
                if c0 + 1 >= ncols:
                    continue
                # Accumulate 2..6 rows as a block, commit only if >=2
                local = []
                local_keys = set()
                collected = 0
                for rr in range(r0 + 1, min(r0 + 1 + 6, nrows)):
                    dval = sheet.iat[rr, c0]
                    lval = sheet.iat[rr, c0 + 1]
                    d = try_parse_date(dval)
                    if d is None or not is_number(lval):
                        break
                    level = float(lval)
                    key = (name_str, d)
                    if key in seen or key in local_keys:
                        continue
                    local_keys.add(key)
                    local.append({
                        'borehole': name_str,
                        'date': d,
                        'level': level,
                        'borehole_norm': name_str.upper()
                    })
                    collected += 1
                if collected >= 2:
                    results.extend(local)
                    seen.update(local_keys)

        parsed = pd.DataFrame(results)
        if parsed.empty:
            return parsed
        # Clean and sort
        parsed = parsed.sort_values(['borehole', 'date']).reset_index(drop=True)
        return parsed
            
    def _load_borehole_monitoring_data(self):
        """Load and visualize borehole monitoring data"""
        if not self.excel_files['borehole_monitoring']:
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
        
        messagebox.showinfo("Coming Soon", "Borehole monitoring visualization will be implemented with column mapping")
        
    def _load_pcd_data(self):
        """Load and visualize PCD data"""
        if not self.excel_files['pcd']:
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
        
        messagebox.showinfo("Coming Soon", "PCD monitoring visualization will be implemented with column mapping")
        
    def _load_rwd_data(self):
        """Load and visualize Return Water Dam data"""
        if not self.excel_files['return_water_dam']:
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
        
        messagebox.showinfo("Coming Soon", "RWD monitoring visualization will be implemented with column mapping")
        
    def _load_sewage_data(self):
        """Load and visualize Sewage Treatment data"""
        if not self.excel_files['sewage_treatment']:
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
        
        messagebox.showinfo("Coming Soon", "Sewage treatment visualization will be implemented with column mapping")
        
    def _load_river_data(self):
        """Load and visualize river monitoring data"""
        if not self.excel_files['river_monitoring']:
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
        
        messagebox.showinfo("Coming Soon", "River monitoring visualization will be implemented with column mapping")

    def _select_bh_mon_directory(self):
        directory = filedialog.askdirectory(title="Select Borehole Monitoring Directory")
        if directory:
            self.bh_mon_dir.set(directory)
            self.status_label.config(text=f"Directory selected: {Path(directory).name}")
            self.data_cache.setdefault('bh_mon_index', {'dir': directory, 'files': {}, 'combined': None})
            if self.data_cache['bh_mon_index']['dir'] != directory:
                self.data_cache['bh_mon_index'] = {'dir': directory, 'files': {}, 'combined': None}

    def _select_bh_mon_file(self):
        """Select a single monitoring Excel file."""
        filepath = filedialog.askopenfilename(
            title="Select Borehole Monitoring Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filepath:
            self.bh_mon_file_path.set(Path(filepath).name)
            self.excel_files['borehole_monitoring'] = filepath
            self.status_label.config(text=f"Selected: {Path(filepath).name}")

    def _load_bh_mon_file(self):
        """Load and visualize a single monitoring Excel file."""
        if not self.excel_files.get('borehole_monitoring'):
            messagebox.showwarning("No File", "Please select an Excel file first")
            return
        try:
            self.status_label.config(text="Loading borehole monitoring data...")
            for widget in self.bh_mon_content.winfo_children():
                widget.destroy()
            parsed = self._parse_borehole_monitoring_excel(self.excel_files['borehole_monitoring'])
            if parsed.empty:
                raise ValueError("No monitoring data found in file.")
            # Apply filters
            df = self._filter_df_by_period_bh_mon(parsed)
            if bool(self.bh_mon_only_registered.get()):
                registered = self._get_registered_monitoring_names()
                if registered:
                    df = df[df['borehole_norm'].isin(registered)]
            if bool(self.bh_mon_single_borehole.get()):
                name = (self.bh_mon_single_borehole_name.get() or '').strip()
                if name:
                    df = df[df['borehole'] == name]
            aquifer_filter = self.bh_mon_aquifer_filter.get()
            if aquifer_filter and aquifer_filter != 'All':
                df = df[df['aquifer'] == aquifer_filter]
            # Display info
            shallow_count = len(df[df['aquifer'] == 'Shallow Aquifer'])
            deep_count = len(df[df['aquifer'] == 'Deep Aquifer'])
            info_text = f"✓ Parsed {len(df)} records across {df['borehole'].nunique()} boreholes (Shallow: {shallow_count}, Deep: {deep_count})"
            ttk.Label(self.bh_mon_content, text=info_text, foreground='#2E7D32', font=('Segoe UI', 10, 'bold')).pack(pady=(6,6), anchor='w')
            # Update combos
            names = sorted([str(n) for n in df['borehole'].dropna().unique().tolist()])
            self.bh_mon_single_borehole_combo['values'] = names
            param_cols = [c for c in df.columns if c not in ['borehole', 'date', 'source_file', 'borehole_norm', 'aquifer']]
            self.bh_mon_param_combo['values'] = param_cols
            if param_cols:
                self.bh_mon_selected_param.set(param_cols[0])
            # Store df
            self._bh_mon_current_df = df
            # Preview table
            self._render_bh_mon_preview_table(df)
            self.status_label.config(text=f"Loaded {len(df)} monitoring records from {Path(self.excel_files['borehole_monitoring']).name}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")
            logger.error(f"Error loading borehole monitoring file: {e}")
            self.status_label.config(text="Error loading data")

    def _generate_bh_mon_charts(self):
        """Generate charts for monitoring data."""
        if not hasattr(self, '_bh_mon_current_df') or self._bh_mon_current_df is None or self._bh_mon_current_df.empty:
            messagebox.showinfo("No Data", "Please load data first before generating charts")
            return
        # Apply filters to the dataframe
        df = self._bh_mon_current_df.copy()
        # Filter by register
        if bool(self.bh_mon_only_registered.get()):
            registered = self._get_registered_monitoring_names()
            if registered:
                df = df[df['borehole_norm'].isin(registered)]
        # Single-borehole filter
        if bool(self.bh_mon_single_borehole.get()):
            name = (self.bh_mon_single_borehole_name.get() or '').strip()
            if name:
                df = df[df['borehole'] == name]
        # Aquifer filter
        aquifer_filter = self.bh_mon_aquifer_filter.get()
        if aquifer_filter and aquifer_filter != 'All':
            df = df[df['aquifer'] == aquifer_filter]
        # Period filter
        df = self._filter_df_by_period_bh_mon(df)
        if df.empty:
            messagebox.showinfo("No Data", "No data matches the current filters")
            return
        # Clear existing chart area and button bar if present
        if hasattr(self, 'bh_mon_chart_btn_bar') and self.bh_mon_chart_btn_bar.winfo_exists():
            self.bh_mon_chart_btn_bar.destroy()
        if hasattr(self, 'bh_mon_chart_area') and self.bh_mon_chart_area.winfo_exists():
            self.bh_mon_chart_area.destroy()
        # Find the preview table widget
        preview_widget = None
        for widget in self.bh_mon_content.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                try:
                    if 'Parsed Monitoring Data' in str(widget.cget('text')):
                        preview_widget = widget
                        break
                except:
                    pass
        # Create download button bar before preview
        self.bh_mon_chart_btn_bar = ttk.Frame(self.bh_mon_content)
        if preview_widget:
            self.bh_mon_chart_btn_bar.pack(fill='x', padx=6, pady=(0, 6), before=preview_widget)
        else:
            self.bh_mon_chart_btn_bar.pack(fill='x', padx=6, pady=(0, 6))
        ttk.Button(self.bh_mon_chart_btn_bar, text='💾 Save Chart', command=self._save_current_chart, width=12).pack(side='right')
        # Create chart area before preview
        self.bh_mon_chart_area = ttk.Frame(self.bh_mon_content)
        if preview_widget:
            self.bh_mon_chart_area.pack(fill='both', expand=False, padx=6, pady=6, before=preview_widget)
        else:
            self.bh_mon_chart_area.pack(fill='both', expand=False, padx=6, pady=6)
        # Plot chart with filtered data
        self._plot_bh_mon_chart(df)

    def _render_bh_mon_preview_table(self, df: pd.DataFrame):
        """Render preview table for monitoring data."""
        preview = ttk.LabelFrame(self.bh_mon_content, text='Parsed Monitoring Data', padding=8)
        preview.pack(fill='both', expand=True, padx=6, pady=6)
        tree = ttk.Treeview(preview, height=12)
        tree.pack(fill='both', expand=True)
        vsb = ttk.Scrollbar(preview, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(preview, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        param_cols = [c for c in df.columns if c not in ['borehole', 'date', 'source_file', 'borehole_norm', 'aquifer']]
        cols = ['borehole', 'aquifer', 'date'] + param_cols
        tree['columns'] = cols
        tree['show'] = 'headings'
        for c in cols:
            tree.heading(c, text=c.title())
            tree.column(c, width=110 if c == 'aquifer' else 100, anchor='w')
        cap = int(self.bh_mon_preview_cap.get() or 100)
        tree.tag_configure('shallow', background='#E3F2FD')
        tree.tag_configure('deep', background='#FFF3E0')
        for _, r in df.head(cap).iterrows():
            vals = [r['borehole'], r.get('aquifer', ''), getattr(r['date'],'date',lambda: r['date'])()]
            for pc in param_cols:
                vals.append(r.get(pc, ''))
            aquifer_val = r.get('aquifer', '')
            tag = 'shallow' if aquifer_val == 'Shallow Aquifer' else ('deep' if aquifer_val == 'Deep Aquifer' else '')
            tree.insert('', 'end', values=vals, tags=(tag,) if tag else ())

    # ==================== BOREHOLE MONITORING METHODS ====================
    def _select_bh_mon_directory(self):
        directory = filedialog.askdirectory(title="Select Borehole Monitoring Directory")
        if directory:
            self.bh_mon_dir.set(directory)
            self.status_label.config(text=f"Directory selected: {Path(directory).name}")
            self.data_cache.setdefault('bh_mon_index', {'dir': directory, 'files': {}, 'combined': None})
            if self.data_cache['bh_mon_index']['dir'] != directory:
                self.data_cache['bh_mon_index'] = {'dir': directory, 'files': {}, 'combined': None}

    def _scan_and_load_bh_mon(self):
        """Scan directory for borehole monitoring Excel files and load."""
        directory = self.bh_mon_dir.get()
        if not directory or directory == 'Not set':
            messagebox.showwarning("No Directory", "Please select a directory first")
            return
        if self._bh_mon_scan_thread and self._bh_mon_scan_thread.is_alive():
            messagebox.showinfo("Please wait", "A scan is already running")
            return
        paths = []
        for ext in ('*.xls','*.xlsx'):
            paths.extend(list(Path(directory).glob(ext)))
        if not paths:
            messagebox.showinfo("No Files", "No .xls/.xlsx files found in directory")
            return
        self.bh_mon_progress['maximum'] = len(paths)
        self.bh_mon_progress['value'] = 0
        self.bh_mon_progress_label.config(text=f"0/{len(paths)}")
        self.bh_mon_scan_btn.config(state='disabled')
        self.status_label.config(text="Scanning directory for monitoring files...")

        def worker(file_list):
            try:
                cache = self.data_cache.setdefault('bh_mon_index', {'dir': directory, 'files': {}, 'combined': None})
                cache['dir'] = directory
                files = cache['files']
                combined_list = []
                processed = 0
                for fp in file_list:
                    try:
                        mtime = fp.stat().st_mtime
                        entry = files.get(str(fp))
                        if entry and entry.get('mtime') == mtime:
                            df = entry.get('df')
                        else:
                            df = self._parse_borehole_monitoring_excel(str(fp))
                            if df is not None and not df.empty:
                                df['source_file'] = str(fp)
                            files[str(fp)] = {'mtime': mtime, 'df': df}
                        if df is not None and not df.empty:
                            combined_list.append(df)
                    except Exception as e:
                        logger.warning(f"Skip file {fp}: {e}")
                    finally:
                        processed += 1
                        def upd(p=processed, total=len(file_list)):
                            self.bh_mon_progress['value'] = p
                            self.bh_mon_progress_label.config(text=f"{p}/{total}")
                        self.container.after(0, upd)
                combined = pd.concat(combined_list, ignore_index=True) if combined_list else pd.DataFrame()
                cache['combined'] = combined
            finally:
                def on_done():
                    self._bh_mon_scan_thread = None
                    self.bh_mon_scan_btn.config(state='normal')
                    self._render_bh_mon_from_df(directory)
                self.container.after(0, on_done)

        self._bh_mon_scan_thread = threading.Thread(target=worker, args=(paths,), daemon=True)
        self._bh_mon_scan_thread.start()

    def _bh_mon_clear_cache(self):
        """Clear cached monitoring data."""
        try:
            current_dir = self.bh_mon_dir.get()
            self.data_cache['bh_mon_index'] = {'dir': current_dir, 'files': {}, 'combined': None}
            self.bh_mon_progress['value'] = 0
            self.bh_mon_progress_label.config(text="")
            self.status_label.config(text="Cache cleared for borehole monitoring")
            for widget in self.bh_mon_content.winfo_children():
                widget.destroy()
            placeholder = ttk.Label(self.bh_mon_content,
                                    text="Select a directory to display data",
                                    foreground='#999', font=('Segoe UI', 11))
            placeholder.pack(expand=True)
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            messagebox.showerror("Error", f"Failed to clear cache: {e}")

    def _render_bh_mon_from_df(self, directory: str):
        """Render monitoring data from cached combined DF."""
        try:
            df = self.data_cache.get('bh_mon_index', {}).get('combined')
            if df is None or df.empty:
                messagebox.showinfo("No Data", "No monitoring data found in directory")
                return
            # Filter by period
            df = self._filter_df_by_period_bh_mon(df)
            # Clean content
            for widget in self.bh_mon_content.winfo_children():
                widget.destroy()
            # Filter by register
            if bool(self.bh_mon_only_registered.get()):
                registered = self._get_registered_monitoring_names()
                if registered:
                    df = df[df['borehole_norm'].isin(registered)]
            # Single-borehole filter
            if bool(self.bh_mon_single_borehole.get()):
                name = (self.bh_mon_single_borehole_name.get() or '').strip()
                if name:
                    df = df[df['borehole'] == name]
            # Aquifer filter
            aquifer_filter = self.bh_mon_aquifer_filter.get()
            if aquifer_filter and aquifer_filter != 'All':
                df = df[df['aquifer'] == aquifer_filter]
            # Info
            shallow_count = len(df[df['aquifer'] == 'Shallow Aquifer'])
            deep_count = len(df[df['aquifer'] == 'Deep Aquifer'])
            info_text = f"✓ Directory parsed: {len(df)} records across {df['borehole'].nunique()} boreholes (Shallow: {shallow_count}, Deep: {deep_count})"
            ttk.Label(self.bh_mon_content, text=info_text, foreground='#2E7D32', font=('Segoe UI', 10, 'bold')).pack(pady=(6,6), anchor='w')
            # Update combo
            try:
                names = sorted([str(n) for n in df['borehole'].dropna().unique().tolist()])
                self.bh_mon_single_borehole_combo['values'] = names
                if self.bh_mon_single_borehole_name.get() and self.bh_mon_single_borehole_name.get() not in names:
                    self.bh_mon_single_borehole_name.set('')
            except Exception:
                pass
            # Update parameter dropdown
            param_cols = [c for c in df.columns if c not in ['borehole', 'date', 'source_file', 'borehole_norm', 'aquifer']]
            if hasattr(self, 'bh_mon_param_combo'):
                self.bh_mon_param_combo['values'] = param_cols
                if param_cols and not self.bh_mon_selected_param.get():
                    self.bh_mon_selected_param.set(param_cols[0])
            # Store df for chart generation
            self._bh_mon_current_df = df
            # Preview table
            preview = ttk.LabelFrame(self.bh_mon_content, text='Parsed Monitoring Data', padding=8)
            preview.pack(fill='both', expand=True, padx=6, pady=6)
            tree = ttk.Treeview(preview, height=12)
            tree.pack(fill='both', expand=True)
            vsb = ttk.Scrollbar(preview, orient='vertical', command=tree.yview)
            hsb = ttk.Scrollbar(preview, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            vsb.pack(side='right', fill='y')
            hsb.pack(side='bottom', fill='x')
            # Show all parameter columns with horizontal scrolling
            param_cols = [c for c in df.columns if c not in ['borehole', 'date', 'source_file', 'borehole_norm', 'aquifer']]
            cols = ['borehole', 'aquifer', 'date'] + param_cols  # Show all parameters
            tree['columns'] = cols
            tree['show'] = 'headings'
            for c in cols:
                tree.heading(c, text=c.title())
                tree.column(c, width=110 if c == 'aquifer' else 100, anchor='w')
            cap = int(self.bh_mon_preview_cap.get() or 100)
            # Configure tags for color-coding aquifer types
            tree.tag_configure('shallow', background='#E3F2FD')  # Light blue for shallow
            tree.tag_configure('deep', background='#FFF3E0')     # Light orange for deep
            for _, r in df.head(cap).iterrows():
                vals = [r['borehole'], r.get('aquifer', ''), getattr(r['date'],'date',lambda: r['date'])()]
                for pc in param_cols:
                    vals.append(r.get(pc, ''))
                # Apply tag based on aquifer type
                aquifer_val = r.get('aquifer', '')
                tag = 'shallow' if aquifer_val == 'Shallow Aquifer' else ('deep' if aquifer_val == 'Deep Aquifer' else '')
                tree.insert('', 'end', values=vals, tags=(tag,) if tag else ())
            self.status_label.config(text=f"Loaded {len(df)} monitoring records from {Path(directory).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Render failed: {e}")
            logger.error(f"Render error: {e}")

    def _plot_bh_mon_chart(self, df: pd.DataFrame):
        """Plot selected monitoring parameters for borehole monitoring data."""
        # Clear previous chart
        for widget in getattr(self, 'bh_mon_chart_area', ttk.Frame()).winfo_children():
            widget.destroy()
        # Get selected parameter from Combobox
        if not hasattr(self, 'bh_mon_selected_param'):
            return
        selected_param = self.bh_mon_selected_param.get()
        chart_type = self.bh_mon_chart_type.get() if hasattr(self, 'bh_mon_chart_type') else 'Line'
        if not selected_param or df.empty:
            lbl = ttk.Label(self.bh_mon_chart_area, text="Select a parameter and click 'Generate Charts' to display", foreground='#999')
            lbl.pack()
            self._last_plot_figure = None
            return
        # Responsive figure size
        try:
            content_width = self.bh_mon_chart_area.winfo_width()
            fig_width_px = max(600, min(1200, int(content_width * 0.9)))
            fig_width_inch = fig_width_px / 100
            fig_height_inch = fig_width_inch * 0.5
        except Exception:
            fig_width_inch, fig_height_inch = 9, 4.5
        fig = Figure(figsize=(fig_width_inch, fig_height_inch), dpi=100)
        ax = fig.add_subplot(111)
        # Color by aquifer type
        aquifer_colors = {'Shallow Aquifer': '#1976D2', 'Deep Aquifer': '#F57C00'}
        # Plot by borehole, aquifer
        for name, g in df.groupby(['borehole', 'aquifer']):
            g = g.sort_values('date')
            color = aquifer_colors.get(name[1], None)
            label = f"{name[0]} ({name[1]})"
            if selected_param not in g.columns:
                continue
            y = g[selected_param]
            if chart_type == 'Bar':
                ax.bar(g['date'], y, width=8, alpha=0.6, label=label, color=color)
            elif chart_type == 'Box':
                ax.boxplot(y.dropna(), positions=[0], widths=0.6, patch_artist=True, boxprops=dict(facecolor=color or '#90CAF9'))
            else:
                ax.plot(g['date'], y, marker='o', label=label, color=color)
        # Dynamic title based on parameter and chart type
        title = f'{selected_param} - {chart_type} Chart'
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel(selected_param)
        # Place legend outside to the right
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0., fontsize=8)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        # Canvas
        canvas = FigureCanvasTkAgg(fig, master=self.bh_mon_chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        self._last_plot_figure = fig

    def _filter_df_by_period_bh_mon(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter monitoring dataframe by period."""
        fy, fm = self.bh_mon_from_year.get(), self.bh_mon_from_month.get()
        ty, tm = self.bh_mon_to_year.get(), self.bh_mon_to_month.get()
        if fy == 'All' and ty == 'All':
            return df
        if fy == 'All':
            start = df['date'].min()
        else:
            sm = 1 if fm == 'All' else int(fm)
            start = datetime(int(fy), sm, 1)
        if ty == 'All':
            end = df['date'].max()
        else:
            em = 12 if tm == 'All' else int(tm)
            last_day = monthrange(int(ty), em)[1]
            end = datetime(int(ty), em, last_day, 23, 59, 59)
        return df[(df['date'] >= start) & (df['date'] <= end)]

    def _get_registered_monitoring_names(self):
        """Return normalized monitoring borehole names."""
        names = set()
        try:
            sources = self.db.get_water_sources(active_only=True)
            for s in sources:
                type_name = (s.get('type_name') or '').lower()
                purpose = (s.get('source_purpose') or 'ABSTRACTION').upper()
                if 'borehole' in type_name and purpose == 'MONITORING':
                    nm = str(s.get('source_name') or '').strip().upper()
                    if nm:
                        names.add(nm)
        except Exception:
            pass
        return names

    def _parse_borehole_monitoring_excel(self, filepath: str) -> pd.DataFrame:
        """Parse borehole monitoring Excel with variable-length date blocks.
        
        Structure:
        - Row 6 (index 5): Parameter names in cols B-I (1-8) and N-R (13-17)
        - Row 7 (index 6): Units
        - Borehole names: dynamically detected in column A (start with TRP or TRM)
        - Below each name: dates with data in same columns as headers
        """
        try:
            sheet = pd.read_excel(filepath, header=None, engine='xlrd')
        except Exception:
            sheet = pd.read_excel(filepath, header=None)

        # Extract parameter names and their column indices from row 6 (index 5)
        param_row = sheet.iloc[5]
        params = []
        for c, val in enumerate(param_row):
            if pd.notna(val) and str(val).strip() != '':
                params.append((c, str(val).strip()))

        # Dynamically find borehole name rows (start after row 7, look for TRP/TRM in col A)
        name_rows = []
        for i in range(8, len(sheet)):
            val = sheet.iloc[i, 0]
            if pd.notna(val):
                s = str(val).strip()
                if s.startswith('TRP') or s.startswith('TRM'):
                    name_rows.append(i)
        
        results = []
        for nr in name_rows:
            if nr >= len(sheet):
                continue
            bh_name = sheet.iloc[nr, 0]
            if pd.isna(bh_name) or str(bh_name).strip() == '':
                continue
            bh_name = str(bh_name).strip()
            bh_name_clean = bh_name
            # Scan subsequent rows for dates
            for offset in range(1, 6):  # Check up to 5 rows below
                row_idx = nr + offset
                if row_idx >= len(sheet):
                    break
                date_cell = sheet.iloc[row_idx, 0]
                # Try parse date and extract aquifer type from suffix
                dt = None
                aquifer_type = ''
                if pd.notna(date_cell):
                    v = date_cell
                    if isinstance(v, str):
                        v_orig = v.replace('\xa0', '').strip()
                        # Detect aquifer type from date cell suffix
                        if '(S)' in v_orig:
                            aquifer_type = 'Shallow Aquifer'
                        elif '(D)' in v_orig:
                            aquifer_type = 'Deep Aquifer'
                        # Remove suffix for date parsing
                        v = v_orig
                        if '(' in v:
                            v = v.split('(')[0].strip()
                    else:
                        v = date_cell
                    try:
                        if isinstance(v, (str, int, float)):
                            dt = pd.to_datetime(v, errors='coerce')
                            if pd.notna(dt):
                                dt = dt.to_pydatetime() if hasattr(dt, 'to_pydatetime') else dt
                            else:
                                dt = None
                    except Exception:
                        try:
                            fv = None
                            if isinstance(v, (int, float)):
                                fv = float(v)
                            elif isinstance(v, str):
                                try:
                                    fv = float(v)
                                except Exception:
                                    fv = None
                            if fv is not None:
                                dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(fv, unit='D')
                        except Exception:
                            dt = None
                if dt is None:
                    break  # Stop at first non-date
                # Collect parameter values
                record = {
                    'borehole': bh_name_clean,
                    'date': dt,
                    'borehole_norm': bh_name_clean.upper(),
                    'aquifer': aquifer_type
                }
                for col_idx, param_name in params:
                    if col_idx < len(sheet.columns):
                        val = sheet.iloc[row_idx, col_idx]
                        val_str = str(val).strip().upper()
                        # Skip invalid values: 'NO ACCESS', empty, or containing '<'
                        if pd.notna(val) and val_str not in ('NO ACCESS', '') and '<' not in val_str:
                            try:
                                if isinstance(val, (int, float)):
                                    record[param_name] = float(val)
                                elif isinstance(val, str):
                                    try:
                                        record[param_name] = float(val)
                                    except Exception:
                                        record[param_name] = val.strip()
                                else:
                                    record[param_name] = str(val).strip()
                            except Exception:
                                record[param_name] = str(val).strip()
                results.append(record)
        parsed = pd.DataFrame(results)
        if not parsed.empty:
            parsed = parsed.sort_values(['borehole', 'date']).reset_index(drop=True)
        return parsed

    # ==================== TAB 3: PCD MONITORING ====================
    def _create_pcd_tab(self):
        """Tab for PCD (Pollution Control Dam) monitoring"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🌊 PCD Monitoring")

        # Sub-tabs: Register | Visualize
        pcd_tabs = ttk.Notebook(tab)
        pcd_tabs.pack(fill='both', expand=True)

        # Register tab
        reg_tab = ttk.Frame(pcd_tabs, padding=10)
        pcd_tabs.add(reg_tab, text="Register")
        ttk.Label(reg_tab, text="PCD registration features coming soon", 
                 font=('Segoe UI', 12)).pack(pady=20)

        # Visualize tab
        viz_tab = ttk.Frame(pcd_tabs, padding=10)
        pcd_tabs.add(viz_tab, text="Visualize")
        
        # Control panel placeholder
        control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        pcd_dir = tk.StringVar(value="Not set")
        ttk.Entry(control_frame, textvariable=pcd_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
        ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
        
        # Content area
        content = ttk.Frame(viz_tab)
        content.pack(fill='both', expand=True, pady=10)
        ttk.Label(content, text="🚧 PCD monitoring visualization will be implemented with column mapping", 
                 font=('Segoe UI', 11), foreground='#666').pack(pady=40)

    # ==================== TAB 4: RETURN WATER DAM MONITORING ====================
    def _create_rwd_tab(self):
        """Tab for Return Water Dam monitoring"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="💧 Return Water Dam")

        # Sub-tabs: Register | Visualize
        rwd_tabs = ttk.Notebook(tab)
        rwd_tabs.pack(fill='both', expand=True)

        # Register tab
        reg_tab = ttk.Frame(rwd_tabs, padding=10)
        rwd_tabs.add(reg_tab, text="Register")
        ttk.Label(reg_tab, text="Return Water Dam registration features coming soon", 
                 font=('Segoe UI', 12)).pack(pady=20)

        # Visualize tab
        viz_tab = ttk.Frame(rwd_tabs, padding=10)
        rwd_tabs.add(viz_tab, text="Visualize")
        
        # Control panel placeholder
        control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        rwd_dir = tk.StringVar(value="Not set")
        ttk.Entry(control_frame, textvariable=rwd_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
        ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
        
        # Content area
        content = ttk.Frame(viz_tab)
        content.pack(fill='both', expand=True, pady=10)
        ttk.Label(content, text="🚧 Return Water Dam monitoring visualization will be implemented with column mapping", 
                 font=('Segoe UI', 11), foreground='#666').pack(pady=40)

    # ==================== TAB 5: SEWAGE TREATMENT MONITORING ====================
    def _create_sewage_tab(self):
        """Tab for Sewage Treatment monitoring"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🏭 Sewage Treatment")

        # Sub-tabs: Register | Visualize
        sewage_tabs = ttk.Notebook(tab)
        sewage_tabs.pack(fill='both', expand=True)

        # Register tab
        reg_tab = ttk.Frame(sewage_tabs, padding=10)
        sewage_tabs.add(reg_tab, text="Register")
        ttk.Label(reg_tab, text="Sewage Treatment registration features coming soon", 
                 font=('Segoe UI', 12)).pack(pady=20)

        # Visualize tab
        viz_tab = ttk.Frame(sewage_tabs, padding=10)
        sewage_tabs.add(viz_tab, text="Visualize")
        
        # Control panel placeholder
        control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        sewage_dir = tk.StringVar(value="Not set")
        ttk.Entry(control_frame, textvariable=sewage_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
        ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
        
        # Content area
        content = ttk.Frame(viz_tab)
        content.pack(fill='both', expand=True, pady=10)
        ttk.Label(content, text="🚧 Sewage Treatment monitoring visualization will be implemented with column mapping", 
                 font=('Segoe UI', 11), foreground='#666').pack(pady=40)

    # ==================== TAB 6: RIVER MONITORING ====================
    def _create_river_tab(self):
        """Tab for River monitoring"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🌊 River Monitoring")

        # Sub-tabs: Register | Visualize
        river_tabs = ttk.Notebook(tab)
        river_tabs.pack(fill='both', expand=True)

        # Register tab
        reg_tab = ttk.Frame(river_tabs, padding=10)
        river_tabs.add(reg_tab, text="Register")
        ttk.Label(reg_tab, text="River monitoring registration features coming soon", 
                 font=('Segoe UI', 12)).pack(pady=20)

        # Visualize tab
        viz_tab = ttk.Frame(river_tabs, padding=10)
        river_tabs.add(viz_tab, text="Visualize")
        
        # Control panel placeholder
        control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        river_dir = tk.StringVar(value="Not set")
        ttk.Entry(control_frame, textvariable=river_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
        ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
        
        # Content area
        content = ttk.Frame(viz_tab)
        content.pack(fill='both', expand=True, pady=10)
        ttk.Label(content, text="🚧 River monitoring visualization will be implemented with column mapping", 
                 font=('Segoe UI', 11), foreground='#666').pack(pady=40)
