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
        self.container.pack(fill='both', expand=True)
        self._build_ui()
        
    def unload(self):
        """Unload the module"""
        self.container.pack_forget()
        
    def _build_ui(self):
        """Build the modern user interface"""
        # Create wrapper frame with background color
        wrapper = tk.Frame(self.container, bg='#f5f6f7')
        wrapper.pack(fill='both', expand=True)
        
        # Title section with professional background
        title_frame = tk.Frame(wrapper, bg='#f5f6f7', relief=tk.FLAT, bd=0)
        title_frame.pack(fill='x', pady=(0, 0), padx=0)
        
        inner_title = tk.Frame(title_frame, bg='#f5f6f7')
        inner_title.pack(fill='x', padx=20, pady=20)
        
        title = tk.Label(inner_title, text="📊 Monitoring Data Dashboard", 
                         font=('Segoe UI', 22, 'bold'),
                         bg='#f5f6f7', fg='#2c3e50')
        title.pack(anchor='w')
        
        subtitle = tk.Label(inner_title, 
                           text="Environmental and operational monitoring data visualization",
                           font=('Segoe UI', 11),
                           fg='#7f8c8d',
                           bg='#f5f6f7')
        subtitle.pack(anchor='w', pady=(3, 0))
        
        # Modern tab styling with improved UX
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TNotebook', background='#f5f6f7', borderwidth=0)
        # Enhanced tab styling: larger font, more padding for better visibility
        style.configure('Modern.TNotebook.Tab', 
                       background='#d6dde8', 
                       foreground='#2c3e50',
                       padding=[24, 16],  # Increased from [20, 10] for larger tab size
                       font=('Segoe UI', 11, 'bold'),  # Increased from 10 to 11, added bold
                       relief='flat',
                       borderwidth=0)
        # Enhanced map with better visual feedback on interaction
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', '#3498db'), ('active', '#5dade2'), ('!active', '#d6dde8')],
                 foreground=[('selected', '#ffffff'), ('active', '#ffffff'), ('!active', '#2c3e50')],
                 lightcolor=[('selected', '#3498db')],
                 darkcolor=[('selected', '#3498db')])
        
        # Status bar (create early so sub-tabs can update it)
        status_frame = tk.Frame(wrapper, bg='#f5f6f7')
        status_frame.pack(fill='x', pady=(15, 10), padx=20)

        self.status_label = tk.Label(status_frame, text="Ready to load monitoring data",
                          foreground='#7f8c8d', bg='#f5f6f7', font=('Segoe UI', 10))
        self.status_label.pack(side='left')

        # Tabs for different monitoring categories (with light background container)
        tab_container = tk.Frame(wrapper, bg='#f5f6f7')
        tab_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Modern tab styling with improved UX
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('DashboardNotebook.TNotebook', background='#f5f6f7', borderwidth=0)
        # Enhanced tab styling: larger font, more padding for better visibility
        style.configure('DashboardNotebook.TNotebook.Tab',
                       background='#d6dde8',
                       foreground='#2c3e50',
                       padding=[24, 16],  # Increased from [20, 12] for larger tab size
                       font=('Segoe UI', 11, 'bold'),  # Increased from 10 to 11, added bold
                       relief='flat',
                       borderwidth=0)
        # Enhanced map with better visual feedback on interaction
        style.map('DashboardNotebook.TNotebook.Tab',
                 background=[('selected', '#3498db'), ('active', '#5dade2'), ('!active', '#d6dde8')],
                 foreground=[('selected', '#ffffff'), ('active', '#ffffff'), ('!active', '#2c3e50')],
                 lightcolor=[('selected', '#3498db')],
                 darkcolor=[('selected', '#3498db')])
        
        # Configure all ttk elements for modern colors
        style.configure('TFrame', background='#f5f6f7')
        style.configure('TLabelFrame', background='#e8eef5', foreground='#2c3e50', borderwidth=1, relief='flat')
        style.configure('TLabelFrame.Label', background='#e8eef5', foreground='#2c3e50', font=('Segoe UI', 10, 'bold'))
        style.configure('TLabel', background='#f5f6f7', foreground='#2c3e50')
        style.configure('TButton', background='#0066cc', foreground='white', borderwidth=0, focuscolor='none', font=('Segoe UI', 9))
        style.map('TButton', background=[('active', '#0052a3'), ('pressed', '#003d7a')])
        style.configure('Treeview', background='white', foreground='#2c3e50', fieldbackground='white', borderwidth=1, relief='solid')
        style.configure('Treeview.Heading', background='#c5d3e6', foreground='#2c3e50', borderwidth=1, relief='raised', font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', '#0066cc')], foreground=[('selected', 'white')])
        style.map('Treeview.Heading', background=[('active', '#b8c7d9')])
        
        self.notebook = ttk.Notebook(tab_container, style='DashboardNotebook.TNotebook')
        self.notebook.pack(fill='both', expand=True)

        # Create tabs
        self._create_borehole_static_tab()
        self._create_borehole_monitoring_tab()
        self._create_pcd_tab()
        # Undeveloped tabs removed - can be re-enabled when ready
        # self._create_rwd_tab()
        # self._create_sewage_tab()
        # self._create_river_tab()
        
    # ==================== TAB 1: BOREHOLE STATIC LEVELS ====================
    def _create_borehole_static_tab(self):
        """Tab for borehole static water levels"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🏔️ Borehole Static Levels")

        # Sub-tabs: Upload | Visualize
        self.bh_static_tabs = ttk.Notebook(tab, style='Modern.TNotebook')
        self.bh_static_tabs.pack(fill='both', expand=True)

        upload_tab = ttk.Frame(self.bh_static_tabs, padding=10)
        self.bh_static_tabs.add(upload_tab, text="Upload & Preview")
        self._create_bh_static_upload_tab(upload_tab)

        viz_tab = ttk.Frame(self.bh_static_tabs, padding=10)
        self.bh_static_tabs.add(viz_tab, text="Visualize")
        self._create_bh_static_visualize_tab(viz_tab)

        
    # ==================== TAB 2: BOREHOLE MONITORING ====================
    def _create_borehole_monitoring_tab(self):
        """Tab for borehole monitoring data"""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🕳️ Borehole Monitoring")

        self.bh_mon_tabs = ttk.Notebook(tab, style='Modern.TNotebook')
        self.bh_mon_tabs.pack(fill='both', expand=True)

        # Upload & Preview tab
        upload = ttk.Frame(self.bh_mon_tabs, padding=10)
        self.bh_mon_tabs.add(upload, text="Upload & Preview")
        self._create_bh_mon_upload_tab(upload)

        # Visualize tab
        viz = ttk.Frame(self.bh_mon_tabs, padding=10)
        self.bh_mon_tabs.add(viz, text="Visualize")
        self._create_bh_mon_visualize_tab(viz)

    def _create_bh_mon_upload_tab(self, parent: ttk.Frame):
        """Upload & preview tab for monitoring data (simple folder selection with auto-load)."""
        # Simplified folder selection
        folder_frame = ttk.Frame(parent)
        folder_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(folder_frame, text="Folder with monitoring borehole Excel files:", font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))
        
        folder_row = ttk.Frame(folder_frame)
        folder_row.pack(fill='x')
        
        self.bh_mon_dir = tk.StringVar(master=folder_row, value="")
        folder_entry = ttk.Entry(folder_row, textvariable=self.bh_mon_dir, state='readonly', font=('Segoe UI', 9))
        folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(folder_row, text="📂 Choose Folder", command=self._select_and_load_bh_mon_folder).pack(side='left')
        
        # Auto-loads message
        auto_msg = ttk.Label(folder_frame, text="Auto-loads: date + borehole + parameters", 
                            foreground='#666', font=('Segoe UI', 8, 'italic'))
        auto_msg.pack(anchor='w', pady=(2, 0))

        # Aquifer filter only
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill='x', pady=(5, 10))
        ttk.Label(filter_frame, text="Aquifer:").pack(side='left', padx=(0, 5))
        self.bh_mon_aquifer_filter = tk.StringVar(master=filter_frame, value='All')
        aquifer_combo = ttk.Combobox(filter_frame, textvariable=self.bh_mon_aquifer_filter, 
                    values=['All', 'Shallow Aquifer', 'Deep Aquifer'], width=16, state='readonly')
        aquifer_combo.pack(side='left')
        aquifer_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_bh_mon_preview())
        
        # Hidden vars for compatibility with existing code
        self.bh_mon_from_year = tk.StringVar(master=parent, value="All")
        self.bh_mon_from_month = tk.StringVar(master=parent, value="All")
        self.bh_mon_to_year = tk.StringVar(master=parent, value="All")
        self.bh_mon_to_month = tk.StringVar(master=parent, value="All")
        self.bh_mon_only_registered = tk.BooleanVar(master=parent, value=False)
        self.bh_mon_single_borehole = tk.BooleanVar(master=parent, value=False)
        self.bh_mon_single_borehole_name = tk.StringVar(master=parent, value='')
        self.bh_mon_preview_cap = tk.IntVar(master=parent, value=100)
        self.bh_mon_single_borehole_combo = ttk.Combobox(parent)  # Hidden
        self.bh_mon_progress = ttk.Progressbar(parent, mode='determinate')  # Hidden
        self.bh_mon_progress_label = ttk.Label(parent, text="")  # Hidden
        self._bh_mon_scan_thread = None

        # Info text
        ttk.Label(parent, text="Preview from files (no database)", foreground='#666', 
                 font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 10))

        # Content area for preview
        self.bh_mon_content = ttk.Frame(parent)
        self.bh_mon_content.pack(fill='both', expand=True)
        placeholder = ttk.Label(self.bh_mon_content,
                                text="Choose a folder to auto-load and preview monitoring data",
                                foreground='#999', font=('Segoe UI', 11))
        placeholder.pack(expand=True)

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
        v_code = tk.StringVar(master=dlg); v_name = tk.StringVar(master=dlg);
        e_code = ttk.Entry(dlg, textvariable=v_code, width=28); e_code.grid(row=0, column=1, padx=8, pady=6)
        e_name = ttk.Entry(dlg, textvariable=v_name, width=28); e_name.grid(row=1, column=1, padx=8, pady=6)
        # Type list filtered to borehole-like
        types = self.db.get_source_types()
        borehole_types = [t for t in types if 'borehole' in (t.get('type_name','') or '').lower() or 'borehole' in (t.get('type_code','') or '').lower()]
        type_names = [t['type_name'] for t in (borehole_types or types)]
        v_type = tk.StringVar(master=dlg, value=type_names[0] if type_names else '')
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
        """Visualize tab for monitoring charts with aquifer and borehole filters."""
        control_frame = ttk.LabelFrame(parent, text="Chart Options", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))

        self.bh_mon_chart_type = tk.StringVar(master=control_frame, value='Line')
        self.bh_mon_selected_param = tk.StringVar(master=control_frame, value='')
        self.bh_mon_viz_aquifer = tk.StringVar(master=control_frame, value='All')
        self.bh_mon_viz_borehole = tk.StringVar(master=control_frame, value='All')

        ttk.Label(control_frame, text='Chart:').grid(row=0, column=0, sticky='w')
        ttk.Combobox(control_frame, textvariable=self.bh_mon_chart_type, values=['Line','Bar','Box'], width=10, state='readonly').grid(row=0, column=1, padx=(4,10), sticky='w')
        ttk.Label(control_frame, text='Parameter:').grid(row=0, column=2, sticky='w')
        self.bh_mon_param_combo = ttk.Combobox(control_frame, textvariable=self.bh_mon_selected_param, values=[], width=18, state='readonly')
        self.bh_mon_param_combo.grid(row=0, column=3, padx=(4,10), sticky='w')
        ttk.Label(control_frame, text='Aquifer:').grid(row=0, column=4, sticky='w', padx=(10,0))
        ttk.Combobox(control_frame, textvariable=self.bh_mon_viz_aquifer, values=['All', 'Shallow Aquifer', 'Deep Aquifer'], width=14, state='readonly').grid(row=0, column=5, padx=(4,10), sticky='w')
        ttk.Label(control_frame, text='Borehole:').grid(row=0, column=6, sticky='w', padx=(10,0))
        self.bh_mon_borehole_combo = ttk.Combobox(control_frame, textvariable=self.bh_mon_viz_borehole, values=['All'], width=14, state='readonly')
        self.bh_mon_borehole_combo.grid(row=0, column=7, padx=(4,10), sticky='w')

        ttk.Button(control_frame, text='📈 Generate Charts', command=self._generate_bh_mon_charts, style='Accent.TButton').grid(row=0, column=8, padx=(8,0))
        ttk.Button(control_frame, text='💾 Save Chart', command=self._save_current_chart, width=12).grid(row=0, column=9, padx=(6,0))

        control_frame.columnconfigure(3, weight=1)

        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', pady=(0,10))
        ttk.Label(info_frame, text="ℹ️  Load data first in 'Upload & Preview'. Select aquifer, borehole (or 'All'), parameter, and chart type. Click 'Generate Charts'.", foreground='#1976D2', font=('Segoe UI', 9, 'italic')).pack(anchor='w')

        # Chart area container
        self.bh_mon_chart_area = ttk.Frame(parent)
        self.bh_mon_chart_area.pack(fill='both', expand=True)
        ttk.Label(self.bh_mon_chart_area, text="Load data then click 'Generate Charts'", foreground='#999', font=('Segoe UI', 11)).pack(expand=True)

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
        """Plot static levels using selected chart options with professional report-ready styling."""
        if df is None or df.empty:
            return
        # Determine target container
        if hasattr(self, '_bh_static_chart_frame') and self._bh_static_chart_frame.winfo_exists():
            target = self._bh_static_chart_frame
        else:
            target = self.borehole_static_content
        chart_type = (self.chart_type.get() or 'Line')
        # Calculate responsive figure size based on content area
        try:
            content_width = target.winfo_width()
            # Use 90% of content width, min 700px, max 1400px for better readability
            fig_width_px = max(700, min(1400, int(content_width * 0.9)))
            fig_width_inch = fig_width_px / 100  # 100 DPI
            fig_height_inch = fig_width_inch * 0.6  # Better aspect for reports
        except Exception:
            # Fallback if window not yet realized
            fig_width_inch, fig_height_inch = 10, 6
        
        # Professional styling for reports
        fig = Figure(figsize=(fig_width_inch, fig_height_inch), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        # Professional color palette (colorblind-friendly)
        colors = ['#0173B2', '#DE8F05', '#029E73', '#CC78BC', '#CA9161', 
                  '#949494', '#ECE133', '#56B4E9', '#F0E442', '#D55E00']
        
        for idx, (name, g) in enumerate(df.groupby('borehole')):
            g = g.sort_values('date')
            color = colors[idx % len(colors)]
            y = g['level'].values
            x = g['date'].values
            label = name
            
            if chart_type == 'Bar':
                # 40% wider bars: 40 * 1.4 = 56
                ax.bar(x, y, width=56, alpha=0.8, label=label, color=color, edgecolor='black', linewidth=1.5)
            else:
                # Plot with markers and lines
                ax.plot(x, y, marker='o', label=label, color=color, 
                       linewidth=2, markersize=6, markeredgecolor='white', markeredgewidth=1)
        
        # Professional title and labels
        ax.set_title('Borehole Static Water Levels', fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Static Level (m)', fontsize=11, fontweight='bold')
        
        # Professional grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)  # Grid behind data
        
        # Professional legend with frame
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0., 
                 fontsize=9, frameon=True, shadow=True, fancybox=True)
        
        # Format axes
        ax.tick_params(labelsize=9)
        fig.autofmt_xdate(rotation=45, ha='right')  # Angled dates for readability
        
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

    # ==================== BOREHOLE STATIC (DB-BACKED) ====================
    def _create_bh_static_upload_tab(self, parent: ttk.Frame):
        """Folder-based loading of static borehole Excel files (no DB writes)."""
        self._bh_static_folder = tk.StringVar(master=parent, value="")
        self._bh_static_data = []

        # Toolbar
        bar = ttk.Frame(parent)
        bar.pack(fill='x', pady=(0,8))
        ttk.Label(bar, text="Folder with static borehole Excel files:").pack(side='left')
        self._bh_static_folder_entry = ttk.Entry(bar, textvariable=self._bh_static_folder, width=50)
        self._bh_static_folder_entry.pack(side='left', padx=(6,6), fill='x', expand=True)
        ttk.Button(bar, text="📂 Choose Folder", command=self._bh_static_pick_folder, style='Accent.TButton').pack(side='left')
        ttk.Label(bar, text="Auto-loads: date + borehole headers (TRM x)", foreground="#666").pack(side='right')

        # Preview table
        frame = ttk.LabelFrame(parent, text="Preview from files (no database)", padding=8)
        frame.pack(fill='both', expand=True)
        self._bh_static_upload_tree = ttk.Treeview(frame, height=12, show='headings')
        self._bh_static_upload_tree.pack(fill='both', expand=True)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=self._bh_static_upload_tree.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=self._bh_static_upload_tree.xview)
        self._bh_static_upload_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        cols = ['date','borehole','static_level_m','file']
        self._bh_static_upload_tree['columns'] = cols
        headings = {'date':'Date','borehole':'Borehole Name','static_level_m':'Static Level (m)','file':'File'}
        for c in cols:
            self._bh_static_upload_tree.heading(c, text=headings.get(c,c))
            self._bh_static_upload_tree.column(c, width=140 if c=='file' else 120, anchor='w')

    def _bh_static_pick_folder(self):
        path = filedialog.askdirectory(title="Select folder with static borehole files")
        if not path:
            return
        self._bh_static_folder.set(path)
        self._bh_static_load_folder()

    def _bh_static_load_folder(self):
        folder = self._bh_static_folder.get().strip()
        if not folder:
            messagebox.showerror("Folder missing", "Please choose a folder containing Excel/CSV files")
            return
        p = Path(folder)
        if not p.exists() or not p.is_dir():
            messagebox.showerror("Folder missing", f"Folder not found: {folder}")
            return
        loaded = []
        errors = []
        for file in sorted(p.iterdir()):
            if file.suffix.lower() not in {'.xls','.xlsx','.csv'}:
                continue
            try:
                if file.suffix.lower() == '.csv':
                    df = pd.read_csv(file)
                    cols_lower = {c.lower(): c for c in df.columns}
                    required = {'date','borehole','static_level_m'}
                    if not required.issubset(set(cols_lower.keys())):
                        # try alternate name for borehole
                        if 'source_code' in cols_lower:
                            cols_lower['borehole'] = cols_lower['source_code']
                    if required.issubset(set(cols_lower.keys())):
                        for _, r in df.iterrows():
                            try:
                                d = pd.to_datetime(r[cols_lower['date']], errors='coerce')
                                lvl = float(r[cols_lower['static_level_m']])
                                name = str(r[cols_lower['borehole']]).strip()
                                if pd.isna(d) or not name:
                                    continue
                                loaded.append({'date': d.date(), 'borehole': name, 'static_level_m': lvl, 'file': file.name})
                            except Exception:
                                continue
                        continue
                # Excel path: read raw and try paired layout parser
                df_raw = pd.read_excel(file, header=None)
                try:
                    parsed = self._parse_paired_column_layout(df_raw)
                except Exception:
                    parsed = pd.DataFrame()
                if not parsed.empty:
                    for _, r in parsed.iterrows():
                        try:
                            d = pd.to_datetime(r['date']).date()
                            loaded.append({'date': d, 'borehole': r['source_code'], 'static_level_m': float(r['static_level_m']), 'file': file.name})
                        except Exception:
                            continue
            except Exception as e:
                errors.append(f"{file.name}: {e}")

        self._bh_static_data = loaded
        
        # Duplicate detection and removal
        seen = set()
        unique_data = []
        duplicates = []
        duplicate_sources = {}  # Track which files had duplicates
        
        for row in loaded:
            # Create unique key: (date, borehole, level)
            key = (row['date'], row['borehole'].upper(), round(row['static_level_m'], 3))
            if key in seen:
                duplicates.append(row)
                # Track duplicate source files
                dup_key = f"{row['date']} | {row['borehole']}"
                if dup_key not in duplicate_sources:
                    duplicate_sources[dup_key] = []
                duplicate_sources[dup_key].append(row['file'])
            else:
                seen.add(key)
                unique_data.append(row)
        
        # Use deduplicated data
        self._bh_static_data = unique_data
        
        # populate tree
        for i in self._bh_static_upload_tree.get_children():
            self._bh_static_upload_tree.delete(i)
        
        # Sort data by date automatically for data integrity
        loaded_sorted = sorted(unique_data, key=lambda x: x['date'])
        
        # Calculate data quality metrics
        bores = sorted({row['borehole'] for row in loaded_sorted})
        quality_summary = []
        for bore in bores:
            bore_data = [r for r in loaded_sorted if r['borehole'] == bore]
            quality_summary.append(f"{bore}: {len(bore_data)} readings")
        
        # Display sorted data
        for r in loaded_sorted[:1000]:
            self._bh_static_upload_tree.insert('', 'end', values=(r['date'], r['borehole'], r['static_level_m'], r['file']))
        
        # Show comprehensive status with data quality info including duplicates
        status_msg = f"✓ Loaded {len(loaded_sorted)} unique rows"
        if len(duplicates) > 0:
            status_msg += f" | ⚠️ {len(duplicates)} duplicates removed"
        status_msg += f" | {len(bores)} boreholes"
        if len(errors) > 0:
            status_msg += f" | {len(errors)} file errors"
        if quality_summary:
            status_msg += f" | {', '.join(quality_summary)}"
        self.status_label.config(text=status_msg)
        
        # Log duplicate details for audit trail
        if duplicates:
            logger.warning(f"Removed {len(duplicates)} duplicate entries")
            for dup_key, files in duplicate_sources.items():
                logger.warning(f"  Duplicate: {dup_key} found in files: {', '.join(files)}")
        
        # Refresh borehole list for combos
        if hasattr(self, 'single_borehole_combo'):
            self.single_borehole_combo['values'] = bores


    def _create_bh_static_visualize_tab(self, parent: ttk.Frame):
        """Visualize loaded static borehole data (in-memory)."""
        control = ttk.LabelFrame(parent, text="Chart Options", padding=10)
        control.pack(fill='x', pady=(0,10))
        self.chart_type = tk.StringVar(master=control, value='Line')
        self.single_borehole = tk.BooleanVar(master=control, value=False)
        self.single_borehole_name = tk.StringVar(master=control, value='')
        ttk.Label(control, text='Chart').grid(row=0, column=0, sticky='e')
        ttk.Combobox(control, textvariable=self.chart_type, values=['Line','Bar'], width=8, state='readonly').grid(row=0, column=1, sticky='w')
        ttk.Checkbutton(control, text='Single borehole', variable=self.single_borehole).grid(row=0, column=2, sticky='w')
        self.single_borehole_combo = ttk.Combobox(control, textvariable=self.single_borehole_name, values=[], width=18, state='readonly')
        self.single_borehole_combo.grid(row=0, column=3, sticky='w', padx=(6,0))
        ttk.Button(control, text='📈 Generate Charts', command=self._bh_static_generate_from_data, style='Accent.TButton').grid(row=0, column=4, sticky='w', padx=(8,0))
        control.columnconfigure(3, weight=1)

        # Content
        self.borehole_static_content = ttk.Frame(parent)
        self.borehole_static_content.pack(fill='both', expand=True)
        ttk.Label(self.borehole_static_content, text="Load files then generate charts", foreground="#999").pack(pady=10)

    def _is_paired_column_layout(self, df_raw):
        """
        Detect if Excel has paired column layout (date/level, date/level, ...).
        Checks for 'Static Level' header pattern and date columns.
        """
        try:
            # Look for 'Static Level' in first 10 rows
            for idx in range(min(10, len(df_raw))):
                row = df_raw.iloc[idx].astype(str).str.lower()
                if row.str.contains('static level').any():
                    return True
            return False
        except:
            return False
    
    def _parse_paired_column_layout(self, df_raw):
        """
        Parse Excel where borehole codes (e.g., TRM 3 in A9, TRM 6 in C9, ...)
        appear above their data columns. Each borehole uses a pair of columns:
        [date_col, level_col]. Data sits below the code cell until the next
        code cell in the same column. Columns can shift; we detect headers
        anywhere within the first ~60 rows and across available columns.

        Returns DataFrame with columns: date, source_code, static_level_m
        """
        rows = []

        def _looks_like_borehole_code(val: str) -> bool:
            if val is None:
                return False
            s = str(val).strip()
            if not s:
                return False
            lower = s.lower()
            # Exclude common non-borehole strings
            if any(k in lower for k in ["static level", "monitoring point", "all points", "environmental", "dam", "area"]):
                return False
            # Exclude date-like patterns (dates often have /, :, or "am"/"pm")
            if '/' in s or ':' in s or 'am' in lower or 'pm' in lower:
                return False
            if len(s) > 25:
                return False
            # Must have both letters and digits (borehole codes like TRM 3, BH 12)
            has_alpha = any(c.isalpha() for c in s)
            has_digit = any(c.isdigit() for c in s)
            return has_alpha and has_digit

        max_header_rows = min(200, len(df_raw))
        max_cols = df_raw.shape[1]

        # Collect all borehole headers (row-based, stacked vertically)
        headers = []
        for r in range(max_header_rows):
            for c in range(max_cols):
                val = df_raw.iat[r, c]
                if _looks_like_borehole_code(val):
                    code = " ".join(str(val).upper().split())
                    headers.append({'row': r, 'col': c, 'code': code})
        
        if not headers:
            raise ValueError("Could not find borehole code headers (e.g., TRM 3)")
        
        # Group headers by row (boreholes in same row are a set)
        headers_by_row = {}
        for h in headers:
            headers_by_row.setdefault(h['row'], []).append(h)
        
        # Process each header row
        header_rows = sorted(headers_by_row.keys())
        for i, row in enumerate(header_rows):
            row_headers = headers_by_row[row]
            # Data starts right after this header row
            data_start = row + 1
            # Data ends at next header row or end of file
            data_end = header_rows[i + 1] if i + 1 < len(header_rows) else len(df_raw)
            
            # Extract data for each borehole in this header row
            for h in row_headers:
                date_col = h['col']
                level_col = h['col'] + 1 if h['col'] + 1 < max_cols else None
                if level_col is None:
                    continue
                
                for r in range(data_start, data_end):
                    dval = df_raw.iat[r, date_col]
                    lval = df_raw.iat[r, level_col]
                    
                    if pd.isna(dval) and pd.isna(lval):
                        continue
                    
                    # Parse date with robust cleanup for malformed timestamps
                    parsed_date = None
                    if isinstance(dval, (datetime, pd.Timestamp)):
                        parsed_date = dval
                    else:
                        try:
                            # Clean malformed times like '09.:55' → '09:55'
                            date_str = str(dval).replace('.:', ':')
                            parsed_date = pd.to_datetime(date_str, errors='coerce')
                            if pd.isna(parsed_date):
                                # Try Excel serial date number
                                fv = float(date_str.replace(',', '.'))
                                parsed_date = pd.to_datetime("1899-12-30") + pd.to_timedelta(fv, unit='D')
                        except Exception:
                            parsed_date = None
                    if parsed_date is None or pd.isna(parsed_date):
                        continue
                    
                    # Parse level
                    try:
                        if isinstance(lval, str):
                            lvl = float(lval.replace(',', '.'))
                        else:
                            lvl = float(lval)
                    except Exception:
                        continue
                    
                    rows.append({
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'source_code': h['code'],
                        'static_level_m': lvl
                    })

        if not rows:
            # Fallback: scan all column pairs for date/level patterns and map to nearest header above
            fallback_rows = []
            max_rows, max_cols = df_raw.shape
            for c in range(0, max_cols - 1):
                date_col = c
                level_col = c + 1
                # Quick heuristic: check a window for date-like and number-like cells
                date_like = 0
                num_like = 0
                window = min(40, max_rows)
                for r in range(0, window):
                    dv = df_raw.iat[r, date_col]
                    lv = df_raw.iat[r, level_col]
                    # date like
                    try:
                        if isinstance(dv, (datetime, pd.Timestamp)):
                            date_like += 1
                        else:
                            _ = pd.to_datetime(dv, errors='coerce')
                            if pd.notna(_):
                                date_like += 1
                    except Exception:
                        pass
                    # number like
                    try:
                        if isinstance(lv, str):
                            float(lv.replace(',', '.'))
                            num_like += 1
                        else:
                            _ = float(lv)
                            num_like += 1
                    except Exception:
                        pass
                if date_like < 3 or num_like < 3:
                    continue

                # Find header code above this pair (scan top 120 rows)
                header_code = None
                for r in range(0, min(120, max_rows)):
                    val = df_raw.iat[r, date_col]
                    if _looks_like_borehole_code(val):
                        header_code = " ".join(str(val).upper().split())
                        start_row = r + 1
                        break
                if header_code is None:
                    continue

                blank_streak = 0
                for r in range(start_row, max_rows):
                    dval = df_raw.iat[r, date_col]
                    lval = df_raw.iat[r, level_col]
                    if pd.isna(dval) and pd.isna(lval):
                        blank_streak += 1
                        if blank_streak >= 3:
                            break
                        continue
                    blank_streak = 0

                    # Parse date
                    parsed_date = None
                    if isinstance(dval, (datetime, pd.Timestamp)):
                        parsed_date = dval
                    else:
                        try:
                            parsed_date = pd.to_datetime(dval, errors='coerce')
                            if pd.isna(parsed_date):
                                fv = float(str(dval).replace(',', '.'))
                                parsed_date = pd.to_datetime("1899-12-30") + pd.to_timedelta(fv, unit='D')
                        except Exception:
                            parsed_date = None
                    if parsed_date is None or pd.isna(parsed_date):
                        continue

                    # Parse level
                    try:
                        if isinstance(lval, str):
                            lvl = float(lval.replace(',', '.'))
                        else:
                            lvl = float(lval)
                    except Exception:
                        continue

                    fallback_rows.append({
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'source_code': header_code,
                        'static_level_m': lvl
                    })

            if not fallback_rows:
                raise ValueError("No valid data found under detected headers")
            rows = fallback_rows

        return pd.DataFrame(rows)

    def _bh_static_select_csv(self):
        path = filedialog.askopenfilename(title="Select Static Levels File", filetypes=[("Excel/CSV files","*.xlsx *.xls *.csv"),("Excel files","*.xlsx *.xls"),("CSV files","*.csv"),("All files","*.*")])
        if not path:
            return
        # Auto-detect file type and read
        try:
            ext = Path(path).suffix.lower()
            if ext == '.csv':
                df = pd.read_csv(path)
            elif ext in ('.xlsx', '.xls'):
                # Read Excel, check for paired column layout
                df_raw = pd.read_excel(path, header=None)
                if self._is_paired_column_layout(df_raw):
                    df = self._parse_paired_column_layout(df_raw)
                else:
                    # Standard tabular format
                    df = pd.read_excel(path)
            else:
                # Try CSV first, fallback to Excel
                try:
                    df = pd.read_csv(path)
                except Exception:
                    df_raw = pd.read_excel(path, header=None)
                    if self._is_paired_column_layout(df_raw):
                        df = self._parse_paired_column_layout(df_raw)
                    else:
                        df = pd.read_excel(path)
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to read file: {e}")
            return
        # Flexible column mapping (case-insensitive, supports common synonyms)
        col_aliases = {
            'date': ['date', 'measurement_date', 'sample_date', 'reading_date', 'datetime', 'timestamp'],
            'source_code': ['source_code', 'borehole', 'borehole_code', 'code', 'bh_code', 'source', 'site', 'well'],
            'static_level_m': ['static_level_m', 'level', 'depth', 'water_level', 'level_m', 'static_level', 'depth_m', 'swl', 'static_water_level']
        }
        
        # Find actual column names by checking aliases
        cols_map = {}
        df_cols_lower = {c.strip().lower(): c for c in df.columns}
        
        for key, aliases in col_aliases.items():
            found = False
            for alias in aliases:
                if alias.lower() in df_cols_lower:
                    cols_map[key] = df_cols_lower[alias.lower()]
                    found = True
                    break
            if not found:
                # Show available columns to help user
                available = ', '.join(df.columns[:10])
                messagebox.showerror("Missing Columns", 
                    f"Could not find '{key}' column.\n\n"
                    f"Accepted names for '{key}': {', '.join(aliases[:5])}\n\n"
                    f"Available columns in file: {available}{'...' if len(df.columns) > 10 else ''}")
                return
        rows = []
        unknown = set()
        # Prepare known codes
        try:
            sources = self.db.get_water_sources(active_only=False)
            known_codes = { (s.get('source_code') or '').strip().upper(): s for s in sources }
        except Exception:
            known_codes = {}
        for _, r in df.iterrows():
            try:
                raw_date = r[cols_map['date']]
                # Parse date (ISO or Excel serial)
                try:
                    dt = pd.to_datetime(raw_date, errors='coerce')
                    if pd.isna(dt):
                        try:
                            fv = float(raw_date)
                            dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(fv, unit='D')
                        except Exception:
                            dt = None
                except Exception:
                    dt = None
                if dt is None:
                    continue
                code = str(r[cols_map['source_code']]).strip().upper()
                lvl = r[cols_map['static_level_m']]
                try:
                    lvl = float(lvl)
                except Exception:
                    continue
                measured = int(r[cols_map.get('measured','measured')] or 1) if 'measured' in cols_map else 1
                qflag = str(r[cols_map.get('quality_flag','quality_flag')]).strip() if 'quality_flag' in cols_map else 'good'
                notes = str(r[cols_map.get('notes','notes')]).strip() if 'notes' in cols_map else None
                rows.append({'date': dt.date(), 'source_code': code, 'level_meters': lvl, 'measured': measured, 'quality_flag': qflag, 'notes': notes})
                if code not in known_codes:
                    unknown.add(code)
            except Exception:
                continue
        # Update staging and preview
        self._bh_static_staging_rows = rows
        self._bh_static_unknown_codes = unknown
        for i in self._bh_static_upload_tree.get_children():
            self._bh_static_upload_tree.delete(i)
        cap = 500
        for r in rows[:cap]:
            self._bh_static_upload_tree.insert('', 'end', values=(r['date'], r['source_code'], r['level_meters'], r['measured'], r['quality_flag'], r['notes'] or ''))
        # Enable actions
        self._bh_static_commit_btn.config(state='normal')
        self._bh_static_resolve_btn.config(state='normal' if unknown else 'disabled')
        self.status_label.config(text=f"Staged {len(rows)} rows ({len(unknown)} unknown codes)")

    def _bh_static_resolve_unknowns(self):
        """Guided dialog to map or create unknown boreholes."""
        unknown = sorted(list(self._bh_static_unknown_codes or set()))
        if not unknown:
            messagebox.showinfo("None", "No unknown borehole codes to resolve.")
            return
        dlg = tk.Toplevel(self.container); dlg.title("Resolve Unknown Boreholes"); dlg.transient(self.container.winfo_toplevel()); dlg.grab_set()
        ttk.Label(dlg, text="Map to existing or create new as STATIC Borehole", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=3, pady=(6,8))
        # Existing boreholes list
        try:
            sources = self.db.get_water_sources(active_only=False)
            bh_sources = [s for s in sources if 'borehole' in (s.get('type_name','') or '').lower()]
            existing_codes = [s.get('source_code') for s in bh_sources]
        except Exception:
            existing_codes = []
        actions = {}
        for idx, code in enumerate(unknown, start=1):
            ttk.Label(dlg, text=code, width=12).grid(row=idx, column=0, sticky='w', padx=8, pady=4)
            act = tk.StringVar(value='create')
            ttk.Radiobutton(dlg, text='Create new', variable=act, value='create').grid(row=idx, column=1, sticky='w')
            ttk.Radiobutton(dlg, text='Map to existing', variable=act, value='map').grid(row=idx, column=2, sticky='w')
            cmb = ttk.Combobox(dlg, values=existing_codes, state='readonly', width=16)
            cmb.grid(row=idx, column=3, padx=4)
            name_var = tk.StringVar(value=code)
            ttk.Entry(dlg, textvariable=name_var, width=18).grid(row=idx, column=4, padx=4)
            actions[code] = {'mode': act, 'combo': cmb, 'name': name_var}
        def apply():
            # Fetch Borehole type_id
            types = self.db.get_source_types()
            borehole_type_id = None
            for t in types:
                if (t.get('type_code','') or '').upper()=='BH' or 'borehole' in (t.get('type_name','') or '').lower():
                    borehole_type_id = t['type_id']
                    break
            for code, obj in actions.items():
                mode = obj['mode'].get()
                if mode == 'map' and obj['combo'].get():
                    # Map: replace staged rows' source_code with selected existing code
                    target = obj['combo'].get().strip().upper()
                    for r in self._bh_static_staging_rows:
                        if r['source_code'] == code:
                            r['source_code'] = target
                elif mode == 'create':
                    # Create new water source as STATIC Borehole
                    try:
                        self.db.add_water_source(source_code=code, source_name=obj['name'].get().strip() or code, type_id=borehole_type_id, source_purpose='STATIC', active=1, created_by='ui')
                    except Exception:
                        continue
            # Recompute unknowns
            sources = self.db.get_water_sources(active_only=False)
            known_codes = { (s.get('source_code') or '').strip().upper() for s in sources }
            self._bh_static_unknown_codes = { r['source_code'] for r in self._bh_static_staging_rows if r['source_code'] not in known_codes }
            self._bh_static_resolve_btn.config(state='disabled' if not self._bh_static_unknown_codes else 'normal')
            dlg.destroy()
            messagebox.showinfo("Resolved", "Unknown boreholes resolved. You can now commit.")
        ttk.Button(dlg, text="Apply", command=apply, style='Accent.TButton').grid(row=len(unknown)+1, column=0, columnspan=5, pady=(10,8))

    def _bh_static_commit_upload(self):
        """Commit staged rows into measurements with dedup (INSERT OR IGNORE)."""
        if not self._bh_static_staging_rows:
            messagebox.showinfo("No Data", "No staged rows to commit.")
            return
        # Build code→id map
        sources = self.db.get_water_sources(active_only=False)
        code_to_id = { (s.get('source_code') or '').strip().upper(): s['source_id'] for s in sources }
        inserted = 0; skipped = 0
        for r in self._bh_static_staging_rows:
            sid = code_to_id.get(r['source_code'])
            if not sid:
                skipped += 1; continue
            try:
                self.db.execute_update(
                    """
                    INSERT OR IGNORE INTO measurements (
                        measurement_date, measurement_type, source_id, facility_id,
                        volume, flow_rate, level_meters, level_percent, rainfall_mm,
                        measured, quality_flag, data_source, notes, recorded_by
                    ) VALUES (?, 'static_level', ?, NULL, NULL, NULL, ?, NULL, NULL, ?, ?, 'csv', ?, 'ui')
                    """,
                    (r['date'], sid, r['level_meters'], r.get('measured',1), r.get('quality_flag','good'), r.get('notes'))
                )
                inserted += 1
            except Exception:
                skipped += 1
        self.status_label.config(text=f"Committed {inserted} rows, skipped {skipped}")
        messagebox.showinfo("Upload Complete", f"Committed {inserted} rows, skipped {skipped}")

    def _bh_static_preview_query(self):
        """Query DB and show preview table for static levels."""
        # Build date range
        df_all = self._bh_static_query_db()
        # Fill single borehole list
        names = sorted(df_all['source_name'].unique().tolist()) if not df_all.empty else []
        self.single_borehole_combo['values'] = names
        # Apply filters
        df = df_all.copy()
        if bool(self.only_registered.get()):
            registered = self._get_registered_borehole_names()
            df = df[df['source_name'].str.upper().isin(registered)]
        if bool(self.single_borehole.get()):
            nm = (self.single_borehole_name.get() or '').strip()
            if nm:
                df = df[df['source_name'] == nm]
        # Populate table
        for i in self._bh_static_preview_tree.get_children():
            self._bh_static_preview_tree.delete(i)
        cap = int(self.preview_cap.get() or 100)
        for _, r in df.head(cap).iterrows():
            self._bh_static_preview_tree.insert('', 'end', values=(r['source_code'], r['source_name'], r['measurement_date'], r['level_meters'], r.get('quality_flag','')))
        self.status_label.config(text=f"Preview {len(df)} records")


    def _bh_static_generate_from_data(self):
        data = self._bh_static_data or []
        if not data:
            messagebox.showinfo("No Data", "Load a folder with static borehole files first")
            return
        
        df = pd.DataFrame(data)
        if self.single_borehole.get():
            target = (self.single_borehole_name.get() or '').strip()
            if target:
                df = df[df['borehole'] == target]
        
        if df.empty:
            messagebox.showinfo("No Data", "No rows match the selected filters")
            return
        
        # Data quality validation
        warnings = []
        total_points = len(df)
        boreholes = df['borehole'].unique()
        
        for bore in boreholes:
            bore_data = df[df['borehole'] == bore]
            if len(bore_data) < 2:
                warnings.append(f"{bore}: Only {len(bore_data)} data point(s) - trend analysis limited")
        
        if warnings:
            warning_msg = "Data Quality Alerts:\n" + "\n".join(warnings[:5])
            if len(warnings) > 5:
                warning_msg += f"\n...and {len(warnings)-5} more"
            logger.warning(f"Borehole data quality issues: {'; '.join(warnings)}")
        
        plot_df = pd.DataFrame({
            'borehole': df['borehole'],
            'date': pd.to_datetime(df['date']),
            'level': df['static_level_m'],
            'borehole_norm': df['borehole'].str.upper()
        })
        
        # Sort by date for proper time series
        plot_df = plot_df.sort_values(['borehole', 'date'])
        for w in self.borehole_static_content.winfo_children():
            w.destroy()
        btn_bar = ttk.Frame(self.borehole_static_content)
        btn_bar.pack(fill='x', padx=6, pady=(0,6))
        ttk.Button(btn_bar, text='💾 Save Chart', command=self._save_current_chart, width=12).pack(side='right')
        self._bh_static_chart_frame = ttk.Frame(self.borehole_static_content)
        self._bh_static_chart_frame.pack(fill='both', expand=False, padx=6, pady=6)
        self._plot_static_levels(plot_df)
            
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

    def _select_and_load_bh_mon_folder(self):
        """Select folder and auto-load monitoring data (simplified workflow)."""
        directory = filedialog.askdirectory(title="Select Folder with Monitoring Borehole Excel Files")
        if directory:
            self.bh_mon_dir.set(directory)
            self.status_label.config(text=f"Loading from: {Path(directory).name}...")
            self.data_cache.setdefault('bh_mon_index', {'dir': directory, 'files': {}, 'combined': None})
            if self.data_cache['bh_mon_index']['dir'] != directory:
                self.data_cache['bh_mon_index'] = {'dir': directory, 'files': {}, 'combined': None}
            # Auto-trigger scan and load
            self._scan_and_load_bh_mon()
    
    def _refresh_bh_mon_preview(self):
        """Refresh preview table when aquifer filter changes."""
        directory = self.bh_mon_dir.get()
        if directory and directory != 'Not set' and directory:
            self._render_bh_mon_from_df(directory)

    def _select_bh_mon_directory(self):
        """Backward compat - kept for potential old references."""
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
            parsed, removed_dup = self._bh_mon_dedupe(parsed)
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
            if removed_dup:
                info_text += f" — removed {removed_dup} duplicate rows"
            ttk.Label(self.bh_mon_content, text=info_text, foreground='#2E7D32', font=('Segoe UI', 10, 'bold')).pack(pady=(6,6), anchor='w')
            quality = self._bh_mon_quality_messages(df)
            if quality:
                quality_text = "⚠️ Data quality warnings: " + "; ".join(quality[:3]) + ("..." if len(quality) > 3 else "")
                quality_label = ttk.Label(self.bh_mon_content, text=quality_text, foreground='#E65100', font=('Segoe UI', 9, 'italic'))
                quality_label.pack(pady=(0,2), anchor='w')
                # Add informative message about what warnings mean
                info_text2 = "ℹ️ Warnings show boreholes with <2 data points (insufficient for reliable trend analysis)."
                info_label = ttk.Label(self.bh_mon_content, text=info_text2, foreground='#1565C0', font=('Segoe UI', 8), wraplength=600, justify='left')
                info_label.pack(pady=(0,6), anchor='w')
            names = sorted([str(n) for n in df['borehole'].dropna().unique().tolist()])
            self.bh_mon_single_borehole_combo['values'] = names
            param_cols = [c for c in df.columns if c not in ['borehole', 'date', 'source_file', 'borehole_norm', 'aquifer']]
            self.bh_mon_param_combo['values'] = param_cols
            if param_cols and not self.bh_mon_selected_param.get():
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
        """Generate charts for monitoring data with aquifer and borehole filters."""
        if not hasattr(self, '_bh_mon_current_df') or self._bh_mon_current_df is None or self._bh_mon_current_df.empty:
            messagebox.showinfo("No Data", "Please load data first before generating charts")
            return
        # Apply filters to the dataframe
        df = self._bh_mon_current_df.copy()
        
        # Aquifer filter from visualize tab
        aquifer_filter = self.bh_mon_viz_aquifer.get() if hasattr(self, 'bh_mon_viz_aquifer') else self.bh_mon_aquifer_filter.get()
        if aquifer_filter and aquifer_filter != 'All':
            df = df[df['aquifer'] == aquifer_filter]
        
        # Borehole filter from visualize tab
        borehole_filter = self.bh_mon_viz_borehole.get() if hasattr(self, 'bh_mon_viz_borehole') else 'All'
        if borehole_filter and borehole_filter != 'All':
            df = df[df['borehole'] == borehole_filter]
        
        if df.empty:
            messagebox.showinfo("No Data", "No data matches the current filters (Aquifer + Borehole)")
            return
        # Clear existing chart area in visualize tab
        if hasattr(self, 'bh_mon_chart_area') and self.bh_mon_chart_area.winfo_exists():
            for widget in self.bh_mon_chart_area.winfo_children():
                widget.destroy()
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
        # Scan button removed during UI simplification
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
                if not combined.empty:
                    before = len(combined)
                    combined = (
                        combined
                        .sort_values(['borehole_norm', 'aquifer', 'date'])
                        .drop_duplicates(subset=['borehole_norm', 'aquifer', 'date'], keep='first')
                        .reset_index(drop=True)
                    )
                    removed = before - len(combined)
                    if removed > 0:
                        logger.warning(f"Removed {removed} duplicate monitoring rows across files")
                cache['combined'] = combined
            finally:
                def on_done():
                    self._bh_mon_scan_thread = None
                    # Scan button removed during UI simplification
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

    def _bh_mon_dedupe(self, df: pd.DataFrame):
        """Remove duplicate monitoring rows by borehole, aquifer, date."""
        if df is None or df.empty:
            return df, 0
        before = len(df)
        deduped = (
            df
            .sort_values(['borehole_norm', 'aquifer', 'date'])
            .drop_duplicates(subset=['borehole_norm', 'aquifer', 'date'], keep='first')
            .reset_index(drop=True)
        )
        return deduped, before - len(deduped)

    def _bh_mon_quality_messages(self, df: pd.DataFrame):
        """Return quality warnings for monitoring data (e.g., insufficient data points).
        Warnings help identify boreholes with limited historical data for analysis.
        """
        msgs = []
        if df is None or df.empty:
            return msgs
        for bh, g in df.groupby('borehole'):
            if len(g) < 2:
                msgs.append(f"{bh}: only {len(g)} data point (limited for trend analysis)")
        return msgs

    def _render_bh_mon_from_df(self, directory: str):
        """Render monitoring data from cached combined DF."""
        try:
            df = self.data_cache.get('bh_mon_index', {}).get('combined')
            if df is None or df.empty:
                messagebox.showinfo("No Data", "No monitoring data found in directory")
                return
            df, removed_dup = self._bh_mon_dedupe(df)
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
            
            # Sort by date (newest first) for better preview organization
            df = df.sort_values('date', ascending=False).reset_index(drop=True)
            
            # Info
            shallow_count = len(df[df['aquifer'] == 'Shallow Aquifer'])
            deep_count = len(df[df['aquifer'] == 'Deep Aquifer'])
            info_text = f"✓ Directory parsed: {len(df)} records across {df['borehole'].nunique()} boreholes (Shallow: {shallow_count}, Deep: {deep_count})"
            if removed_dup:
                info_text += f" — removed {removed_dup} duplicate rows"
            ttk.Label(self.bh_mon_content, text=info_text, foreground='#2E7D32', font=('Segoe UI', 10, 'bold')).pack(pady=(6,6), anchor='w')
            quality = self._bh_mon_quality_messages(df)
            if quality:
                quality_text = "⚠️ Data quality warnings: " + "; ".join(quality[:3]) + ("..." if len(quality) > 3 else "")
                quality_label = ttk.Label(self.bh_mon_content, text=quality_text, foreground='#E65100', font=('Segoe UI', 9, 'italic'))
                quality_label.pack(pady=(0,2), anchor='w')
                # Add informative message about what warnings mean
                info_text2 = "ℹ️ Warnings show boreholes with <2 data points (insufficient for reliable trend analysis)."
                info_label = ttk.Label(self.bh_mon_content, text=info_text2, foreground='#1565C0', font=('Segoe UI', 8), wraplength=600, justify='left')
                info_label.pack(pady=(0,6), anchor='w')
            # Update combo
            try:
                names = sorted([str(n) for n in df['borehole'].dropna().unique().tolist()])
                self.bh_mon_single_borehole_combo['values'] = names
                if self.bh_mon_single_borehole_name.get() and self.bh_mon_single_borehole_name.get() not in names:
                    self.bh_mon_single_borehole_name.set('')
                # Also populate visualize tab borehole combo
                if hasattr(self, 'bh_mon_borehole_combo'):
                    borehole_values = ['All'] + names
                    self.bh_mon_borehole_combo['values'] = borehole_values
                    self.bh_mon_viz_borehole.set('All')
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
            # Preview table with responsive layout
            preview = ttk.LabelFrame(self.bh_mon_content, text='Parsed Monitoring Data (scroll horizontally for all parameters)', padding=8)
            preview.pack(fill='both', expand=True, padx=6, pady=6)
            
            # Create tree with scrollbars
            tree = ttk.Treeview(preview, height=12)
            tree.pack(fill='both', expand=True, side='left')
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
            
            # Responsive column widths based on screen width
            try:
                screen_width = self.winfo_width()
            except Exception:
                screen_width = 1400  # Default width
            
            # Adapt column widths for different screen sizes
            if screen_width < 1024:  # Laptop screens
                borehole_width = 90
                aquifer_width = 95
                date_width = 85
                param_width = 75
            elif screen_width < 1440:  # Standard desktop
                borehole_width = 110
                aquifer_width = 110
                date_width = 100
                param_width = 85
            else:  # Large monitors
                borehole_width = 130
                aquifer_width = 120
                date_width = 110
                param_width = 95
            
            # Configure columns
            tree.column('borehole', width=borehole_width, anchor='w')
            tree.column('aquifer', width=aquifer_width, anchor='w')
            tree.column('date', width=date_width, anchor='center')
            for pc in param_cols:
                tree.column(pc, width=param_width, anchor='center')
            
            tree.heading('borehole', text='Borehole')
            tree.heading('aquifer', text='Aquifer')
            tree.heading('date', text='Date')
            for c in param_cols:
                tree.heading(c, text=c.title())
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
        # Industry-standard figure with better DPI and professional styling
        fig = Figure(figsize=(fig_width_inch, fig_height_inch), dpi=120, facecolor='white')
        ax = fig.add_subplot(111)
        
        # Color palette by aquifer type (professional blue/orange scheme)
        aquifer_colors = {'Shallow Aquifer': '#1976D2', 'Deep Aquifer': '#F57C00'}
        
        # Plot by borehole, aquifer
        plotted_count = 0
        for name, g in df.groupby(['borehole', 'aquifer']):
            g = g.sort_values('date')
            color = aquifer_colors.get(name[1], '#424242')
            aquifer_short = 'S' if 'Shallow' in name[1] else 'D'
            label = f"{name[0]} ({aquifer_short})"
            
            if selected_param not in g.columns:
                continue
            
            y = g[selected_param]
            
            if chart_type == 'Bar':
                # Wide bars for readability
                ax.bar(g['date'], y, width=56, alpha=0.7, label=label, color=color, edgecolor='white', linewidth=0.5)
            elif chart_type == 'Box':
                bp = ax.boxplot(y.dropna(), positions=[plotted_count], widths=0.6, patch_artist=True,
                               boxprops=dict(facecolor=color, alpha=0.7),
                               medianprops=dict(color='#D32F2F', linewidth=2),
                               whiskerprops=dict(color=color, linewidth=1.5),
                               capprops=dict(color=color, linewidth=1.5))
                ax.set_xticks([plotted_count])
                ax.set_xticklabels([label])
            else:
                # Line charts with markers for clarity
                ax.plot(g['date'], y, marker='o', markersize=6, linewidth=2, label=label, color=color, alpha=0.9)
            
            plotted_count += 1
        
        if plotted_count == 0:
            ax.text(0.5, 0.5, 'No data available for selected parameter', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='#999')
        
        # Professional title and labels
        title = f'{selected_param}\n{chart_type} Chart'
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'{selected_param} (mg/L)' if selected_param != 'Static Level' else f'{selected_param} (m)', 
                     fontsize=11, fontweight='bold')
        
        # Industry-standard grid (major + minor)
        ax.grid(True, which='major', linestyle='-', linewidth=0.8, alpha=0.3, color='#666')
        ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.2, color='#999')
        ax.minorticks_on()
        
        # Professional legend (only if multiple series)
        if plotted_count > 1:
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0., 
                     fontsize=9, frameon=True, shadow=True, fancybox=True)
        elif plotted_count == 1:
            # For single borehole, add legend at top
            ax.legend(loc='best', fontsize=9, frameon=True, shadow=True)
        
        # Rotate date labels for readability
        if chart_type != 'Box':
            fig.autofmt_xdate(rotation=45)
        
        # Professional tight layout with extra space for legend
        fig.tight_layout(rect=[0, 0, 0.85 if plotted_count > 1 else 1, 1])
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
        """Parse borehole monitoring Excel files arranged in stacked blocks per borehole.

        Observed pattern (example: Boreholes Q3 2021.xls):
        - Header row (row 6, index 5): parameter names in cols B-J (1-9)
        - Units row (row 7, index 6): mg/l, m, etc. (ignored except for reference)
        - Borehole name in col A (0), e.g., TRPGWM 01, TRPGWM 02, ... stacked vertically
        - Data rows follow each borehole name until the next borehole name row
        - Date/time is in col A; suffix (S) = Shallow, (D) = Deep aquifer
        - Parameters are in the same columns as the header row
        """
        try:
            sheet = pd.read_excel(filepath, header=None, engine='xlrd')
        except Exception:
            sheet = pd.read_excel(filepath, header=None)

        if sheet.empty:
            return pd.DataFrame()

        import re

        # Locate header row by searching for "Static Level"
        header_row = None
        for i in range(min(len(sheet), 20)):
            row_str = sheet.iloc[i].astype(str).str.lower()
            if row_str.str.contains('static level').any():
                header_row = i
                break
        if header_row is None:
            header_row = 5 if len(sheet) > 5 else 0

        # Extract parameters from header row; strip control chars so column names are stable
        params = []
        for c, val in enumerate(sheet.iloc[header_row]):
            if pd.notna(val):
                name = str(val).replace('\xa0', ' ').strip()
                if name:
                    name = re.sub(r"[\r\n]+", " ", name).replace('^', '').strip()
                    if name:
                        params.append((c, name))

        # Identify borehole name rows in col A after header
        name_rows = []
        bh_pattern = re.compile(r'^[A-Z]{3,}\s*\d+[A-Z]*')
        for i in range(header_row + 1, len(sheet)):
            v = sheet.iat[i, 0]
            if pd.isna(v):
                continue
            s = str(v).replace('\xa0', '').strip()
            if bh_pattern.match(s):
                name_rows.append(i)

        if not name_rows:
            return pd.DataFrame()

        name_rows.append(len(sheet))  # sentinel to mark end

        records = []
        for idx in range(len(name_rows) - 1):
            start = name_rows[idx]
            end = name_rows[idx + 1]
            bh_name = str(sheet.iat[start, 0]).replace('\xa0', '').strip()
            if not bh_name:
                continue
            bh_norm = bh_name.upper()

            for r in range(start + 1, end):
                date_cell = sheet.iat[r, 0]
                if pd.isna(date_cell):
                    continue
                date_raw = str(date_cell).replace('\xa0', '').strip()
                aquifer = ''
                if '(S' in date_raw.upper():
                    aquifer = 'Shallow Aquifer'
                elif '(D' in date_raw.upper():
                    aquifer = 'Deep Aquifer'
                # remove suffix in parentheses for parsing
                if '(' in date_raw:
                    date_raw = date_raw.split('(')[0].strip()
                
                # Try to parse date with multiple formats to avoid day/month confusion
                dt = None
                # First try: pandas default (handles most formats)
                dt = pd.to_datetime(date_raw, errors='coerce', dayfirst=True)
                
                # If that fails, try Excel date number format
                if pd.isna(dt):
                    try:
                        fv = float(date_raw)
                        dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(fv, unit='D')
                    except Exception:
                        # Try explicit formats as fallback
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                            try:
                                dt = pd.to_datetime(date_raw, format=fmt)
                                break
                            except Exception:
                                continue
                
                if pd.isna(dt) or dt is None:
                    continue

                record = {
                    'borehole': bh_name,
                    'borehole_norm': bh_norm,
                    'date': dt.to_pydatetime() if hasattr(dt, 'to_pydatetime') else dt,
                    'aquifer': aquifer
                }

                for col_idx, param_name in params:
                    if col_idx >= sheet.shape[1]:
                        continue
                    val = sheet.iat[r, col_idx]
                    if pd.isna(val):
                        continue
                    val_str = str(val).strip()
                    if not val_str or val_str.upper() == 'NO ACCESS' or '<' in val_str:
                        continue
                    try:
                        record[param_name] = float(val)
                    except Exception:
                        record[param_name] = val_str

                records.append(record)

        parsed = pd.DataFrame(records)
        if not parsed.empty:
            parsed['source_file'] = Path(filepath).name
            parsed = parsed.sort_values(['borehole', 'date']).reset_index(drop=True)
        return parsed

    # ==================== TAB 3: PCD MONITORING ====================
    def _create_pcd_tab(self):
        """Tab for PCD (Pollution Control Dam) monitoring with Upload & Visualize tabs."""
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="🌊 PCD Monitoring")

        # Sub-tabs: Upload & Preview | Visualize
        pcd_tabs = ttk.Notebook(tab, style='Modern.TNotebook')
        pcd_tabs.pack(fill='both', expand=True)

        # Upload & Preview tab
        upload_tab = ttk.Frame(pcd_tabs, padding=10)
        pcd_tabs.add(upload_tab, text="Upload & Preview")
        self._create_pcd_upload_tab(upload_tab)

        # Visualize tab
        viz_tab = ttk.Frame(pcd_tabs, padding=10)
        pcd_tabs.add(viz_tab, text="Visualize")
        self._create_pcd_visualize_tab(viz_tab)

    def _create_pcd_upload_tab(self, parent: ttk.Frame):
        """Upload & preview tab for PCD monitoring data (simple folder selection with auto-load)."""
        # Simplified folder selection
        folder_frame = ttk.Frame(parent)
        folder_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(folder_frame, text="Folder with PCD monitoring Excel files:", font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))
        
        folder_row = ttk.Frame(folder_frame)
        folder_row.pack(fill='x')
        
        self.pcd_dir = tk.StringVar(master=folder_row, value="")
        folder_entry = ttk.Entry(folder_row, textvariable=self.pcd_dir, state='readonly', font=('Segoe UI', 9))
        folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(folder_row, text="📂 Choose Folder", command=self._select_and_load_pcd_folder).pack(side='left')
        
        # Auto-loads message
        auto_msg = ttk.Label(folder_frame, text="Auto-loads: date + monitoring point + parameters", 
                            foreground='#666', font=('Segoe UI', 8, 'italic'))
        auto_msg.pack(anchor='w', pady=(2, 0))

        # Monitoring point filter
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill='x', pady=(5, 10))
        ttk.Label(filter_frame, text="Monitoring Point:").pack(side='left', padx=(0, 5))
        self.pcd_point_filter = tk.StringVar(master=filter_frame, value='All')
        
        # Simple Combobox - values updated dynamically when files are loaded
        self.pcd_point_combo = ttk.Combobox(filter_frame, textvariable=self.pcd_point_filter,
                                             values=['All'], width=20, state='readonly')
        self.pcd_point_combo.pack(side='left')
        self.pcd_point_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_pcd_preview())
        
        # Hidden vars for compatibility
        self._init_pcd_hidden_vars(parent)

        # Info text
        ttk.Label(parent, text="Preview from files (no database)", foreground='#666', 
                 font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 10))

        # Content area for preview
        self.pcd_content = ttk.Frame(parent)
        self.pcd_content.pack(fill='both', expand=True)
        placeholder = ttk.Label(self.pcd_content,
                                text="Choose a folder to auto-load and preview PCD monitoring data",
                                foreground='#999', font=('Segoe UI', 11))
        placeholder.pack(expand=True)

    def _init_pcd_hidden_vars(self, parent):
        """Initialize hidden variables for PCD tab compatibility."""
        self.pcd_from_year = tk.StringVar(master=parent, value="All")
        self.pcd_from_month = tk.StringVar(master=parent, value="All")
        self.pcd_to_year = tk.StringVar(master=parent, value="All")
        self.pcd_to_month = tk.StringVar(master=parent, value="All")
        self.pcd_only_registered = tk.BooleanVar(master=parent, value=False)
        self.pcd_single_point = tk.BooleanVar(master=parent, value=False)
        self.pcd_single_point_name = tk.StringVar(master=parent, value='')
        self.pcd_preview_cap = tk.IntVar(master=parent, value=100)
        # Note: pcd_point_combo is created in _create_pcd_upload_tab, not here
        self.pcd_progress = ttk.Progressbar(parent, mode='determinate')  # Hidden
        self.pcd_progress_label = ttk.Label(parent, text="")  # Hidden
        self._pcd_scan_thread = None

    def _create_pcd_visualize_tab(self, parent: ttk.Frame):
        """Visualize tab for PCD charts with monitoring point and parameter filters."""
        control_frame = ttk.LabelFrame(parent, text="Chart Options", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))

        self.pcd_chart_type = tk.StringVar(master=control_frame, value='Line')
        self.pcd_selected_param = tk.StringVar(master=control_frame, value='')
        self.pcd_viz_point = tk.StringVar(master=control_frame, value='All')

        ttk.Label(control_frame, text='Chart:').grid(row=0, column=0, sticky='w')
        ttk.Combobox(control_frame, textvariable=self.pcd_chart_type, values=['Line','Bar','Box'], width=10, state='readonly').grid(row=0, column=1, padx=(4,10), sticky='w')
        ttk.Label(control_frame, text='Parameter:').grid(row=0, column=2, sticky='w')
        self.pcd_param_combo = ttk.Combobox(control_frame, textvariable=self.pcd_selected_param, values=[], width=18, state='readonly')
        self.pcd_param_combo.grid(row=0, column=3, padx=(4,10), sticky='w')
        ttk.Label(control_frame, text='Point:').grid(row=0, column=4, sticky='w', padx=(10,0))
        self.pcd_viz_point_combo = ttk.Combobox(control_frame, textvariable=self.pcd_viz_point, values=['All'], width=14, state='readonly')
        self.pcd_viz_point_combo.grid(row=0, column=5, padx=(4,10), sticky='w')

        ttk.Button(control_frame, text='📈 Generate Charts', command=self._generate_pcd_charts, style='Accent.TButton').grid(row=0, column=6, padx=(8,0))
        ttk.Button(control_frame, text='💾 Save Chart', command=self._save_current_pcd_chart, width=12).grid(row=0, column=7, padx=(6,0))

        control_frame.columnconfigure(3, weight=1)

        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', pady=(0,10))
        ttk.Label(info_frame, text="ℹ️  Load data first in 'Upload & Preview'. Select monitoring point (or 'All'), parameter, and chart type. Click 'Generate Charts'.", foreground='#1976D2', font=('Segoe UI', 9, 'italic')).pack(anchor='w')

        # Chart area container
        self.pcd_chart_area = ttk.Frame(parent)
        self.pcd_chart_area.pack(fill='both', expand=True)
        ttk.Label(self.pcd_chart_area, text="Load data then click 'Generate Charts'", foreground='#999', font=('Segoe UI', 11)).pack(expand=True)

    def _select_and_load_pcd_folder(self):
        """Select folder and auto-load PCD monitoring data."""
        directory = filedialog.askdirectory(title="Select Folder with PCD Monitoring Excel Files")
        if directory:
            self.pcd_dir.set(directory)
            self.status_label.config(text=f"Loading from: {Path(directory).name}...")
            self.data_cache.setdefault('pcd_index', {'dir': directory, 'files': {}, 'combined': None})
            if self.data_cache['pcd_index']['dir'] != directory:
                self.data_cache['pcd_index'] = {'dir': directory, 'files': {}, 'combined': None}
            # Auto-trigger scan and load
            self._scan_and_load_pcd()

    def _refresh_pcd_preview(self):
        """Refresh preview table when monitoring point filter changes."""
        directory = self.pcd_dir.get()
        if directory and directory != 'Not set' and directory:
            self._render_pcd_from_df(directory)

    def _scan_and_load_pcd(self):
        """Scan directory for PCD monitoring Excel files and load."""
        directory = self.pcd_dir.get()
        if not directory or directory == 'Not set':
            messagebox.showwarning("No Directory", "Please select a directory first")
            return
        if self._pcd_scan_thread and self._pcd_scan_thread.is_alive():
            messagebox.showinfo("Please wait", "A scan is already running")
            return
        paths = []
        for ext in ('*.xls','*.xlsx'):
            paths.extend(list(Path(directory).glob(ext)))
        if not paths:
            messagebox.showinfo("No Files", "No .xls/.xlsx files found in directory")
            return
        self.pcd_progress['maximum'] = len(paths)
        self.pcd_progress['value'] = 0
        self.pcd_progress_label.config(text=f"0/{len(paths)}")
        self.status_label.config(text="Scanning directory for PCD monitoring files...")

        def worker(file_list):
            try:
                cache = self.data_cache.setdefault('pcd_index', {'dir': directory, 'files': {}, 'combined': None})
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
                            df = self._parse_pcd_monitoring_excel(str(fp))
                            if df is not None and not df.empty:
                                df['source_file'] = str(fp)
                            files[str(fp)] = {'mtime': mtime, 'df': df}
                        if df is not None and not df.empty:
                            combined_list.append(df)
                    except Exception as e:
                        logger.warning(f"Skip PCD file {fp}: {e}")
                    finally:
                        processed += 1
                        def upd(p=processed, total=len(file_list)):
                            self.pcd_progress['value'] = p
                            self.pcd_progress_label.config(text=f"{p}/{total}")
                        self.container.after(0, upd)
                combined = pd.concat(combined_list, ignore_index=True) if combined_list else pd.DataFrame()
                if not combined.empty:
                    before = len(combined)
                    combined = (
                        combined
                        .sort_values(['monitoring_point', 'date'])
                        .drop_duplicates(subset=['monitoring_point', 'date'], keep='first')
                        .reset_index(drop=True)
                    )
                    removed = before - len(combined)
                    if removed > 0:
                        logger.warning(f"Removed {removed} duplicate PCD monitoring rows across files")
                cache['combined'] = combined
            finally:
                def on_done():
                    self._pcd_scan_thread = None
                    self._render_pcd_from_df(directory)
                self.container.after(0, on_done)

        self._pcd_scan_thread = threading.Thread(target=worker, args=(paths,), daemon=True)
        self._pcd_scan_thread.start()

    def _render_pcd_from_df(self, directory: str):
        """Render PCD monitoring data from cached combined DF."""
        try:
            df = self.data_cache.get('pcd_index', {}).get('combined')
            if df is None or df.empty:
                messagebox.showinfo("No Data", "No PCD monitoring data found in directory")
                return
            df, removed_dup = self._pcd_dedupe(df)
            # Clean content
            for widget in self.pcd_content.winfo_children():
                widget.destroy()
            # Monitoring point filter
            point_filter = self.pcd_point_filter.get()
            if point_filter and point_filter != 'All':
                df = df[df['monitoring_point'] == point_filter]
            
            # Sort by date (newest first)
            df = df.sort_values('date', ascending=False).reset_index(drop=True)
            
            # Info
            info_text = f"✓ Directory parsed: {len(df)} records across {df['monitoring_point'].nunique()} monitoring points"
            if removed_dup:
                info_text += f" — removed {removed_dup} duplicate rows"
            ttk.Label(self.pcd_content, text=info_text, foreground='#2E7D32', font=('Segoe UI', 10, 'bold')).pack(pady=(6,6), anchor='w')
            quality = self._pcd_quality_messages(df)
            if quality:
                quality_text = "⚠️ Data quality warnings: " + "; ".join(quality[:3]) + ("..." if len(quality) > 3 else "")
                quality_label = ttk.Label(self.pcd_content, text=quality_text, foreground='#E65100', font=('Segoe UI', 9, 'italic'))
                quality_label.pack(pady=(0,2), anchor='w')
                info_text2 = "ℹ️ Warnings show monitoring points with <2 data points (insufficient for reliable trend analysis)."
                info_label = ttk.Label(self.pcd_content, text=info_text2, foreground='#1565C0', font=('Segoe UI', 8), wraplength=600, justify='left')
                info_label.pack(pady=(0,6), anchor='w')
            
            # Update monitoring point filter with extracted points
            names = sorted([str(n) for n in df['monitoring_point'].dropna().unique().tolist()])
            point_values = ['All'] + names
            
            # Update Combobox values
            if hasattr(self, 'pcd_point_combo') and self.pcd_point_combo:
                self.pcd_point_combo['values'] = tuple(point_values)
            
            # Update Visualize tab combo
            if hasattr(self, 'pcd_viz_point_combo') and self.pcd_viz_point_combo:
                self.pcd_viz_point_combo['values'] = point_values
                if not self.pcd_viz_point.get():
                    self.pcd_viz_point.set('All')
            
            # Update parameter dropdown
            param_cols = [c for c in df.columns if c not in ['monitoring_point', 'date', 'source_file']]
            if hasattr(self, 'pcd_param_combo'):
                self.pcd_param_combo['values'] = param_cols
                if param_cols and not self.pcd_selected_param.get():
                    self.pcd_selected_param.set(param_cols[0])
            
            # Store df for chart generation
            self._pcd_current_df = df
            
            # Preview table with horizontal scrollbar
            preview = ttk.LabelFrame(self.pcd_content, text='Parsed PCD Monitoring Data (scroll horizontally for all parameters)', padding=8)
            preview.pack(fill='both', expand=True, padx=6, pady=6)
            
            # Create frame for tree and scrollbars
            tree_frame = ttk.Frame(preview)
            tree_frame.pack(fill='both', expand=True)
            
            # Horizontal scrollbar (pack first, at bottom)
            hsb = ttk.Scrollbar(tree_frame, orient='horizontal')
            hsb.pack(side='bottom', fill='x')
            
            # Vertical scrollbar (pack second, at right)
            vsb = ttk.Scrollbar(tree_frame, orient='vertical')
            vsb.pack(side='right', fill='y')
            
            # Tree (pack last, fills remaining space)
            tree = ttk.Treeview(tree_frame, height=12, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            tree.pack(side='left', fill='both', expand=True)
            
            # Configure scrollbar commands
            vsb.config(command=tree.yview)
            hsb.config(command=tree.xview)
            
            param_cols = [c for c in df.columns if c not in ['monitoring_point', 'date', 'source_file']]
            cols = ['monitoring_point', 'date'] + param_cols
            tree['columns'] = cols
            tree['show'] = 'headings'
            
            # Auto-fit column widths based on content
            tree.column('#0', width=0, stretch='no')
            
            # Monitoring Point column - fit to header or longest point name
            max_point_len = max([len(str(p)) for p in df['monitoring_point'].unique()] + [len('Monitoring Point')])
            point_width = min(max(max_point_len * 8, 120), 200)
            tree.column('monitoring_point', width=point_width, anchor='w', stretch=False)
            
            # Date column - fixed width
            tree.column('date', width=100, anchor='center', stretch=False)
            
            # Parameter columns - fit to header text
            for pc in param_cols:
                param_width = max(len(pc) * 8, 70)
                tree.column(pc, width=param_width, anchor='center', stretch=False)
            
            tree.heading('#0', text='')
            tree.heading('monitoring_point', text='Monitoring Point')
            tree.heading('date', text='Date')
            for c in param_cols:
                tree.heading(c, text=c.title())
            
            cap = int(self.pcd_preview_cap.get() or 100)
            tree.tag_configure('point1', background='#E3F2FD')
            tree.tag_configure('point2', background='#FFF3E0')
            
            colors = ['#E3F2FD', '#FFF3E0', '#F1F8E9', '#FCE4EC', '#E0F2F1']
            for idx, (_, r) in enumerate(df.head(cap).iterrows()):
                vals = [r['monitoring_point'], getattr(r['date'],'date',lambda: r['date'])()]
                for pc in param_cols:
                    vals.append(r.get(pc, ''))
                color_idx = hash(r['monitoring_point']) % len(colors)
                tag = f'point{color_idx}'
                tree.tag_configure(tag, background=colors[color_idx])
                tree.insert('', 'end', values=vals, tags=(tag,))
            
            self.status_label.config(text=f"Loaded {len(df)} PCD monitoring records from {Path(directory).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Render failed: {e}")
            logger.error(f"PCD Render error: {e}")

    def _generate_pcd_charts(self):
        """Generate charts for PCD monitoring data with point filter."""
        if not hasattr(self, '_pcd_current_df') or self._pcd_current_df is None or self._pcd_current_df.empty:
            messagebox.showinfo("No Data", "Please load data first before generating charts")
            return
        df = self._pcd_current_df.copy()
        
        # Point filter from visualize tab
        point_filter = self.pcd_viz_point.get() if hasattr(self, 'pcd_viz_point') else 'All'
        if point_filter and point_filter != 'All':
            df = df[df['monitoring_point'] == point_filter]
        
        if df.empty:
            messagebox.showinfo("No Data", "No data matches the current filter")
            return
        
        # Clear existing chart area
        if hasattr(self, 'pcd_chart_area') and self.pcd_chart_area.winfo_exists():
            for widget in self.pcd_chart_area.winfo_children():
                widget.destroy()
        
        self._plot_pcd_chart(df)

    def _plot_pcd_chart(self, df: pd.DataFrame):
        """Plot PCD monitoring parameters with industry-standard styling."""
        for widget in getattr(self, 'pcd_chart_area', ttk.Frame()).winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'pcd_selected_param'):
            return
        selected_param = self.pcd_selected_param.get()
        chart_type = self.pcd_chart_type.get() if hasattr(self, 'pcd_chart_type') else 'Line'
        
        if not selected_param or df.empty:
            lbl = ttk.Label(self.pcd_chart_area, text="Select a parameter and click 'Generate Charts' to display", foreground='#999')
            lbl.pack()
            self._last_pcd_plot_figure = None
            return
        
        try:
            content_width = self.pcd_chart_area.winfo_width()
            fig_width_px = max(600, min(1200, int(content_width * 0.9)))
            fig_width_inch = fig_width_px / 100
            fig_height_inch = fig_width_inch * 0.5
        except Exception:
            fig_width_inch, fig_height_inch = 9, 4.5
        
        fig = Figure(figsize=(fig_width_inch, fig_height_inch), dpi=120, facecolor='white')
        ax = fig.add_subplot(111)
        
        color_palette = ['#1976D2', '#F57C00', '#388E3C', '#D32F2F', '#7B1FA2']
        plotted_count = 0
        
        for idx, (name, g) in enumerate(df.groupby('monitoring_point')):
            g = g.sort_values('date')
            color = color_palette[idx % len(color_palette)]
            label = f"{name}"
            
            if selected_param not in g.columns:
                continue
            
            y = g[selected_param]
            
            if chart_type == 'Bar':
                ax.bar(g['date'], y, width=56, alpha=0.7, label=label, color=color, edgecolor='white', linewidth=0.5)
            elif chart_type == 'Box':
                bp = ax.boxplot(y.dropna(), positions=[plotted_count], widths=0.6, patch_artist=True,
                               boxprops=dict(facecolor=color, alpha=0.7),
                               medianprops=dict(color='#D32F2F', linewidth=2),
                               whiskerprops=dict(color=color, linewidth=1.5),
                               capprops=dict(color=color, linewidth=1.5))
                ax.set_xticks([plotted_count])
                ax.set_xticklabels([label])
            else:
                ax.plot(g['date'], y, marker='o', markersize=6, linewidth=2, label=label, color=color, alpha=0.9)
            
            plotted_count += 1
        
        if plotted_count == 0:
            ax.text(0.5, 0.5, 'No data available for selected parameter', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='#999')
        
        title = f'{selected_param}\n{chart_type} Chart'
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel(selected_param, fontsize=11, fontweight='bold')
        
        ax.grid(True, which='major', linestyle='-', linewidth=0.8, alpha=0.3, color='#666')
        ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.2, color='#999')
        ax.minorticks_on()
        
        if plotted_count > 1:
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0., 
                     fontsize=9, frameon=True, shadow=True, fancybox=True)
        elif plotted_count == 1:
            ax.legend(loc='best', fontsize=9, frameon=True, shadow=True)
        
        if chart_type != 'Box':
            fig.autofmt_xdate(rotation=45)
        
        fig.tight_layout(rect=[0, 0, 0.85 if plotted_count > 1 else 1, 1])
        
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=self.pcd_chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        self._last_pcd_plot_figure = fig

    def _save_current_pcd_chart(self):
        """Save current PCD chart as PNG."""
        if not hasattr(self, '_last_pcd_plot_figure') or self._last_pcd_plot_figure is None:
            messagebox.showwarning("No Chart", "Generate a chart first before saving")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=f"pcd_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if filepath:
            try:
                self._last_pcd_plot_figure.savefig(filepath, dpi=150, bbox_inches='tight')
                messagebox.showinfo("Success", f"Chart saved to {Path(filepath).name}")
                logger.info(f"PCD chart saved: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save chart: {e}")

    def _pcd_quality_messages(self, df: pd.DataFrame):
        """Return quality warnings for PCD monitoring data."""
        msgs = []
        if df is None or df.empty:
            return msgs
        for point, g in df.groupby('monitoring_point'):
            if len(g) < 2:
                msgs.append(f"{point}: only {len(g)} data point (limited for trend analysis)")
        return msgs

    def _pcd_dedupe(self, df: pd.DataFrame):
        """Remove duplicate PCD monitoring rows by point and date."""
        if df is None or df.empty:
            return df, 0
        before = len(df)
        deduped = (
            df
            .sort_values(['monitoring_point', 'date'])
            .drop_duplicates(subset=['monitoring_point', 'date'], keep='first')
            .reset_index(drop=True)
        )
        return deduped, before - len(deduped)

    def _parse_pcd_monitoring_excel(self, filepath: str) -> pd.DataFrame:
        """Parse PCD monitoring Excel files with flexible header detection."""
        try:
            sheet = pd.read_excel(filepath, header=None, engine='xlrd')
        except Exception:
            sheet = pd.read_excel(filepath, header=None)

        if sheet.empty:
            return pd.DataFrame()

        import re

        # Locate header row by searching for date or common parameter names
        header_row = None
        for i in range(min(len(sheet), 20)):
            row_str = sheet.iloc[i].astype(str).str.lower()
            if (row_str.str.contains('date').any() or 
                row_str.str.contains('calcium').any() or
                row_str.str.contains('chloride').any() or
                row_str.str.contains('alkalinity').any()):
                header_row = i
                break
        if header_row is None:
            header_row = 5 if len(sheet) > 5 else 0

        # Extract parameters from header row
        params = []
        for c, val in enumerate(sheet.iloc[header_row]):
            if pd.notna(val):
                name = str(val).replace('\xa0', ' ').strip()
                if name:
                    name = re.sub(r"[\r\n]+", " ", name).replace('^', '').strip()
                    if name and name.lower() != 'monitoring point' and name.lower() != 'date':
                        params.append((c, name))

        # Identify monitoring point rows
        point_rows = []
        for i in range(header_row + 1, len(sheet)):
            v = sheet.iat[i, 0]
            if pd.isna(v):
                continue
            s = str(v).strip()
            if len(s) > 2 and not s[0].isdigit():  # Likely a point name, not a date/number
                point_rows.append(i)

        if not point_rows:
            # Fallback: treat all rows as data rows under monitoring_point
            point_rows = [header_row + 1]

        point_rows.append(len(sheet))  # Sentinel

        records = []
        for idx in range(len(point_rows) - 1):
            start = point_rows[idx]
            end = point_rows[idx + 1]
            point_cell = sheet.iat[start, 0]
            if pd.isna(point_cell):
                continue
            point_name = str(point_cell).strip()
            if not point_name or point_name.lower() in ['monitoring point', 'date']:
                continue

            for r in range(start + 1, end):
                date_cell = sheet.iat[r, 0]
                if pd.isna(date_cell):
                    continue
                date_raw = str(date_cell).strip()
                
                if '(' in date_raw:
                    date_raw = date_raw.split('(')[0].strip()
                
                dt = pd.to_datetime(date_raw, errors='coerce', dayfirst=True)
                
                if pd.isna(dt):
                    try:
                        fv = float(date_raw)
                        dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(fv, unit='D')
                    except Exception:
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                            try:
                                dt = pd.to_datetime(date_raw, format=fmt)
                                break
                            except Exception:
                                continue
                
                if pd.isna(dt) or dt is None:
                    continue

                record = {
                    'monitoring_point': point_name,
                    'date': dt.to_pydatetime() if hasattr(dt, 'to_pydatetime') else dt,
                }

                for col_idx, param_name in params:
                    if col_idx >= sheet.shape[1]:
                        continue
                    val = sheet.iat[r, col_idx]
                    if pd.isna(val):
                        continue
                    val_str = str(val).strip()
                    if not val_str or val_str.upper() == 'NO ACCESS' or '<' in val_str:
                        continue
                    try:
                        record[param_name] = float(val)
                    except Exception:
                        record[param_name] = val_str

                records.append(record)

        parsed = pd.DataFrame(records)
        if not parsed.empty:
            parsed['source_file'] = Path(filepath).name
            parsed = parsed.sort_values(['monitoring_point', 'date']).reset_index(drop=True)
        return parsed

    # ==================== TAB 4: RETURN WATER DAM MONITORING (DISABLED) ====================
    # Undeveloped tab - can be re-enabled when ready
    # def _create_rwd_tab(self):
    #     """Tab for Return Water Dam monitoring"""
    #     tab = ttk.Frame(self.notebook, padding=15)
    #     self.notebook.add(tab, text="💧 Return Water Dam")
    #
    #     # Sub-tabs: Register | Visualize
    #     rwd_tabs = ttk.Notebook(tab)
    #     rwd_tabs.pack(fill='both', expand=True)
    #
    #     # Register tab
    #     reg_tab = ttk.Frame(rwd_tabs, padding=10)
    #     rwd_tabs.add(reg_tab, text="Register")
    #     ttk.Label(reg_tab, text="Return Water Dam registration features coming soon", 
    #              font=('Segoe UI', 12)).pack(pady=20)
    #
    #     # Visualize tab
    #     viz_tab = ttk.Frame(rwd_tabs, padding=10)
    #     rwd_tabs.add(viz_tab, text="Visualize")
    #     
    #     # Control panel placeholder
    #     control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
    #     control_frame.pack(fill='x', pady=(0, 10))
    #     
    #     ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
    #     rwd_dir = tk.StringVar(value="Not set")
    #     ttk.Entry(control_frame, textvariable=rwd_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
    #     ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
    #     ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
    #     
    #     # Content area
    #     content = ttk.Frame(viz_tab)
    #     content.pack(fill='both', expand=True, pady=10)
    #     ttk.Label(content, text="🚧 Return Water Dam monitoring visualization will be implemented with column mapping", 
    #              font=('Segoe UI', 11), foreground='#666').pack(pady=40)

    # ==================== TAB 5: SEWAGE TREATMENT MONITORING (DISABLED) ====================
    # Undeveloped tab - can be re-enabled when ready
    # def _create_sewage_tab(self):
    #     """Tab for Sewage Treatment monitoring"""
    #     tab = ttk.Frame(self.notebook, padding=15)
    #     self.notebook.add(tab, text="🏭 Sewage Treatment")
    #
    #     # Sub-tabs: Register | Visualize
    #     sewage_tabs = ttk.Notebook(tab)
    #     sewage_tabs.pack(fill='both', expand=True)
    #
    #     # Register tab
    #     reg_tab = ttk.Frame(sewage_tabs, padding=10)
    #     sewage_tabs.add(reg_tab, text="Register")
    #     ttk.Label(reg_tab, text="Sewage Treatment registration features coming soon", 
    #              font=('Segoe UI', 12)).pack(pady=20)
    #
    #     # Visualize tab
    #     viz_tab = ttk.Frame(sewage_tabs, padding=10)
    #     sewage_tabs.add(viz_tab, text="Visualize")
    #     
    #     # Control panel placeholder
    #     control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
    #     control_frame.pack(fill='x', pady=(0, 10))
    #     
    #     ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
    #     sewage_dir = tk.StringVar(value="Not set")
    #     ttk.Entry(control_frame, textvariable=sewage_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
    #     ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
    #     ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
    #     
    #     # Content area
    #     content = ttk.Frame(viz_tab)
    #     content.pack(fill='both', expand=True, pady=10)
    #     ttk.Label(content, text="🚧 Sewage Treatment monitoring visualization will be implemented with column mapping", 
    #              font=('Segoe UI', 11), foreground='#666').pack(pady=40)

    # ==================== TAB 6: RIVER MONITORING (DISABLED) ====================
    # Undeveloped tab - can be re-enabled when ready
    # def _create_river_tab(self):
    #     """Tab for River monitoring"""
    #     tab = ttk.Frame(self.notebook, padding=15)
    #     self.notebook.add(tab, text="🌊 River Monitoring")
    #
    #     # Sub-tabs: Register | Visualize
    #     river_tabs = ttk.Notebook(tab)
    #     river_tabs.pack(fill='both', expand=True)
    #
    #     # Register tab
    #     reg_tab = ttk.Frame(river_tabs, padding=10)
    #     river_tabs.add(reg_tab, text="Register")
    #     ttk.Label(reg_tab, text="River monitoring registration features coming soon", 
    #              font=('Segoe UI', 12)).pack(pady=20)
    #
    #     # Visualize tab
    #     viz_tab = ttk.Frame(river_tabs, padding=10)
    #     river_tabs.add(viz_tab, text="Visualize")
    #     
    #     # Control panel placeholder
    #     control_frame = ttk.LabelFrame(viz_tab, text="Data Source", padding=10)
    #     control_frame.pack(fill='x', pady=(0, 10))
    #     
    #     ttk.Label(control_frame, text="Directory:").grid(row=0, column=0, sticky='w', padx=(0, 10))
    #     river_dir = tk.StringVar(value="Not set")
    #     ttk.Entry(control_frame, textvariable=river_dir, state='readonly', width=60).grid(row=0, column=1, sticky='ew', padx=(0, 10))
    #     ttk.Button(control_frame, text="📂 Select Directory", state='disabled').grid(row=0, column=2, padx=(0,5))
    #     ttk.Button(control_frame, text="🔎 Scan Directory & Load", state='disabled', style='Accent.TButton').grid(row=0, column=3)
    #     
    #     # Content area
    #     content = ttk.Frame(viz_tab)
    #     content.pack(fill='both', expand=True, pady=10)
    #     ttk.Label(content, text="🚧 River monitoring visualization will be implemented with column mapping", 
    #              font=('Segoe UI', 11), foreground='#666').pack(pady=40)
