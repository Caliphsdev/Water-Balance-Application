"""
Measurements Module
Daily/monthly measurement data entry with date pickers and historical views
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, date, timedelta
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager


class MeasurementsModule:
    """Measurements data entry and management interface"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.main_frame = None
        self.tree = None
        
        # Filter variables
        self.date_from_var = None
        self.date_to_var = None
        self.type_var = None
        self.source_var = None
        self.facility_var = None
        
        # Data caches
        self.water_sources = []
        self.storage_facilities = []
        self.measurement_types = [
            'source_flow', 'facility_level', 'rainfall', 
            'evaporation', 'plant_consumption', 'discharge'
        ]
    
    def load(self):
        """Load the measurements module"""
        # Clear existing content
        if self.main_frame:
            self.main_frame.destroy()
        
        # Load data
        self.water_sources = self.db.get_water_sources()
        self.storage_facilities = self.db.get_storage_facilities()
        
        # Create main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._create_header()
        
        # Filter panel
        self._create_filter_panel()
        
        # Action buttons
        self._create_action_buttons()
        
        # Data grid
        self._create_data_grid()
        
        # Load initial data
        self._load_measurements()
    
    def _create_header(self):
        """Create header section"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="Measurements & Time-Series Data", 
                         font=('Segoe UI', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Info label
        info = ttk.Label(header_frame, 
                        text="Record and manage water measurements",
                        font=('Segoe UI', 9),
                        foreground='#666')
        info.pack(side=tk.LEFT, padx=(20, 0))
    
    def _create_filter_panel(self):
        """Create filter controls"""
        filter_frame = ttk.LabelFrame(self.main_frame, text="Filters", padding=15)
        filter_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Date range
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="From:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        default_from = date.today() - timedelta(days=30)
        self.date_from_var = tk.StringVar()
        date_from = DateEntry(date_frame, textvariable=self.date_from_var,
                             width=12, background='darkblue',
                             foreground='white', borderwidth=2,
                             date_pattern='yyyy-mm-dd')
        date_from.set_date(default_from)
        date_from.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(date_frame, text="To:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        self.date_to_var = tk.StringVar()
        date_to = DateEntry(date_frame, textvariable=self.date_to_var,
                           width=12, background='darkblue',
                           foreground='white', borderwidth=2,
                           date_pattern='yyyy-mm-dd')
        date_to.set_date(date.today())
        date_to.pack(side=tk.LEFT, padx=(0, 20))
        
        # Measurement type filter
        ttk.Label(date_frame, text="Type:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.type_var = tk.StringVar(value='All')
        type_combo = ttk.Combobox(date_frame, textvariable=self.type_var,
                                 values=['All'] + self.measurement_types,
                                 state='readonly', width=18)
        type_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Apply filter button
        apply_btn = ttk.Button(date_frame, text="Apply Filter", 
                              command=self._load_measurements,
                              style='Accent.TButton')
        apply_btn.pack(side=tk.LEFT)
        
        # Source/Facility filter
        entity_frame = ttk.Frame(filter_frame)
        entity_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(entity_frame, text="Source:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.source_var = tk.StringVar(value='All')
        source_values = ['All'] + [f"{s['source_code']} - {s['source_name']}" 
                                   for s in self.water_sources]
        source_combo = ttk.Combobox(entity_frame, textvariable=self.source_var,
                                    values=source_values,
                                    state='readonly', width=35)
        source_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(entity_frame, text="Facility:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.facility_var = tk.StringVar(value='All')
        facility_values = ['All'] + [f"{f['facility_code']} - {f['facility_name']}" 
                                     for f in self.storage_facilities]
        facility_combo = ttk.Combobox(entity_frame, textvariable=self.facility_var,
                                     values=facility_values,
                                     state='readonly', width=35)
        facility_combo.pack(side=tk.LEFT)
    
    def _create_action_buttons(self):
        """Create action buttons"""
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Add button
        add_btn = ttk.Button(btn_frame, text="➕ Add Measurement", 
                            command=self._add_measurement,
                            style='Accent.TButton')
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Edit button
        edit_btn = ttk.Button(btn_frame, text="✏️ Edit", 
                             command=self._edit_measurement)
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Delete selected (supports multi-select)
        delete_btn = ttk.Button(btn_frame, text="🗑️ Delete Selected", 
                       command=self._delete_measurements)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh button
        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh", 
                                command=self._load_measurements)
        refresh_btn.pack(side=tk.LEFT)
        
        # Statistics label
        self.stats_label = ttk.Label(btn_frame, text="", foreground='#666')
        self.stats_label.pack(side=tk.RIGHT)
    
    def _create_data_grid(self):
        """Create measurement data grid"""
        grid_frame = ttk.LabelFrame(self.main_frame, text="Measurement Records", 
                                   padding=10)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ('id', 'date', 'type', 'source', 'facility', 'volume', 
                  'flow_rate', 'measured', 'data_source')
        
        self.tree = ttk.Treeview(grid_frame, columns=columns, show='headings',
                    yscrollcommand=scroll_y.set,
                    xscrollcommand=scroll_x.set,
                    height=15,
                    selectmode='extended')
        
        # Configure columns
        column_configs = {
            'id': ('ID', 50, 'center'),
            'date': ('Date', 100, 'center'),
            'type': ('Type', 130, 'w'),
            'source': ('Water Source', 150, 'w'),
            'facility': ('Storage Facility', 150, 'w'),
            'volume': ('Volume (m³)', 100, 'e'),
            'flow_rate': ('Flow Rate', 100, 'e'),
            'measured': ('Measured', 80, 'center'),
            'data_source': ('Source', 80, 'center')
        }
        
        for col, (heading, width, anchor) in column_configs.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor=anchor)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Bind double-click to edit
        self.tree.bind('<Double-Button-1>', lambda e: self._edit_measurement())
    
    def _load_measurements(self):
        """Load measurements based on filters"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get date range
        date_from = datetime.strptime(self.date_from_var.get(), '%Y-%m-%d').date()
        date_to = datetime.strptime(self.date_to_var.get(), '%Y-%m-%d').date()
        
        # Get measurements
        measurements = self.db.get_measurements(date_from, date_to)
        
        # Apply filters
        type_filter = self.type_var.get()
        if type_filter != 'All':
            measurements = [m for m in measurements if m['measurement_type'] == type_filter]
        
        source_filter = self.source_var.get()
        if source_filter != 'All':
            source_code = source_filter.split(' - ')[0]
            measurements = [m for m in measurements if m.get('source_code') == source_code]
        
        facility_filter = self.facility_var.get()
        if facility_filter != 'All':
            facility_code = facility_filter.split(' - ')[0]
            measurements = [m for m in measurements if m.get('facility_code') == facility_code]
        
        # Insert data
        for m in measurements:
            values = (
                m['measurement_id'],
                m['measurement_date'],
                m['measurement_type'],
                m.get('source_name', '—'),
                m.get('facility_name', '—'),
                f"{m['volume']:,.0f}" if m['volume'] else '—',
                f"{m['flow_rate']:,.0f}" if m['flow_rate'] else '—',
                '✓' if m['measured'] == 1 else '✗',
                m['data_source']
            )
            self.tree.insert('', tk.END, values=values)
        
        # Update statistics
        self.stats_label.config(text=f"Total: {len(measurements)} records")
    
    def _sort_column(self, col):
        """Sort treeview by column"""
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children()]
        items.sort()
        
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def _add_measurement(self):
        """Open add measurement dialog"""
        dialog = MeasurementDialog(self.main_frame, self.db, 
                                   self.water_sources, self.storage_facilities)
        self.main_frame.wait_window(dialog.dialog)
        
        if dialog.result:
            self._load_measurements()
    
    def _edit_measurement(self):
        """Open edit measurement dialog"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a measurement to edit.")
            return
        
        # Get measurement ID
        item = self.tree.item(selection[0])
        measurement_id = item['values'][0]
        
        # Get full measurement data
        measurement = self.db.execute_query(
            "SELECT * FROM measurements WHERE measurement_id = ?",
            (measurement_id,)
        )
        
        if measurement:
            dialog = MeasurementDialog(self.main_frame, self.db,
                                      self.water_sources, self.storage_facilities,
                                      measurement[0])
            self.main_frame.wait_window(dialog.dialog)
            
            if dialog.result:
                self._load_measurements()
    
    def _delete_measurements(self):
        """Bulk delete selected measurements"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select one or more measurements to delete.")
            return
        # Collect ALL IDs for deletion, build preview separately (first 10)
        ids = []
        preview = []
        for idx, item_id in enumerate(selection):
            item = self.tree.item(item_id)
            vals = item.get('values')
            if not vals:
                continue
            mid = vals[0]
            ids.append(mid)
            if idx < 10:
                preview.append(f"{mid}: {vals[1]} {vals[2]}")
        if not ids:
            messagebox.showwarning("No Data", "Unable to resolve selected rows.")
            return
        extra = "" if len(selection) <= 10 else f"\n... plus {len(selection)-10} more"
        confirm = messagebox.askyesno(
            "Confirm Bulk Delete",
            f"Delete {len(selection)} measurements?\n\n" + "\n".join(preview) + extra + "\n\nThis cannot be undone."
        )
        if not confirm:
            return
        try:
            deleted = self.db.delete_measurements(ids)
            messagebox.showinfo("Deleted", f"Deleted {deleted} measurements.")
            self._load_measurements()
        except Exception as e:
            messagebox.showerror("Error", f"Bulk delete failed:\n{e}")
    
    def refresh_data(self):
        """Refresh module data"""
        self._load_measurements()


class MeasurementDialog:
    """Dialog for adding/editing measurements"""
    
    def __init__(self, parent, db, sources, facilities, measurement=None):
        self.db = db
        self.sources = sources
        self.facilities = facilities
        self.measurement = measurement
        self.result = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Measurement" if not measurement else "Edit Measurement")
        self.dialog.geometry("600x650")
        self.dialog.transient(parent)

        # Defer grab_set until dialog mapped (prevents window not viewable errors)
        def _defer_grab():
            try:
                if self.dialog.winfo_viewable():
                    self.dialog.grab_set()
                else:
                    self.dialog.after(25, _defer_grab)
            except Exception:
                pass
        self.dialog.after(25, _defer_grab)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (650 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Variables
        self.date_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.facility_var = tk.StringVar()
        self.volume_var = tk.StringVar()
        self.flow_rate_var = tk.StringVar()
        self.level_meters_var = tk.StringVar()
        self.level_percent_var = tk.StringVar()
        self.rainfall_var = tk.StringVar()
        self.measured_var = tk.IntVar(value=1)
        self.quality_var = tk.StringVar(value='good')
        self.data_source_var = tk.StringVar(value='manual')
        self.notes_var = tk.StringVar()
        
        self._create_form()
        self._populate_form()
    
    def _create_form(self):
        """Create form fields"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Date
        row = 0
        ttk.Label(main_frame, text="Date:*").grid(row=row, column=0, sticky='w', pady=5)
        date_entry = DateEntry(main_frame, textvariable=self.date_var,
                              width=20, background='darkblue',
                              foreground='white', borderwidth=2,
                              date_pattern='yyyy-mm-dd')
        date_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Measurement Type
        row += 1
        ttk.Label(main_frame, text="Type:*").grid(row=row, column=0, sticky='w', pady=5)
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var,
                                 values=['source_flow', 'facility_level', 'rainfall',
                                        'evaporation', 'plant_consumption', 'discharge'],
                                 state='readonly')
        type_combo.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)
        
        # Water Source
        row += 1
        ttk.Label(main_frame, text="Water Source:").grid(row=row, column=0, sticky='w', pady=5)
        source_values = ['—'] + [f"{s['source_code']} - {s['source_name']}" for s in self.sources]
        source_combo = ttk.Combobox(main_frame, textvariable=self.source_var,
                                    values=source_values, state='readonly')
        source_combo.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Storage Facility
        row += 1
        ttk.Label(main_frame, text="Storage Facility:").grid(row=row, column=0, sticky='w', pady=5)
        facility_values = ['—'] + [f"{f['facility_code']} - {f['facility_name']}" for f in self.facilities]
        facility_combo = ttk.Combobox(main_frame, textvariable=self.facility_var,
                                     values=facility_values, state='readonly')
        facility_combo.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Separator
        row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, 
                                                            sticky='ew', pady=10)
        
        # Volume
        row += 1
        ttk.Label(main_frame, text="Volume (m³):").grid(row=row, column=0, sticky='w', pady=5)
        volume_entry = ttk.Entry(main_frame, textvariable=self.volume_var)
        volume_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Flow Rate
        row += 1
        ttk.Label(main_frame, text="Flow Rate (m³/day):").grid(row=row, column=0, sticky='w', pady=5)
        flow_entry = ttk.Entry(main_frame, textvariable=self.flow_rate_var)
        flow_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Level (meters)
        row += 1
        ttk.Label(main_frame, text="Level (m):").grid(row=row, column=0, sticky='w', pady=5)
        level_m_entry = ttk.Entry(main_frame, textvariable=self.level_meters_var)
        level_m_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Level (percent)
        row += 1
        ttk.Label(main_frame, text="Level (%):").grid(row=row, column=0, sticky='w', pady=5)
        level_p_entry = ttk.Entry(main_frame, textvariable=self.level_percent_var)
        level_p_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Rainfall
        row += 1
        ttk.Label(main_frame, text="Rainfall (mm):").grid(row=row, column=0, sticky='w', pady=5)
        rainfall_entry = ttk.Entry(main_frame, textvariable=self.rainfall_var)
        rainfall_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Separator
        row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2,
                                                            sticky='ew', pady=10)
        
        # Measured checkbox
        row += 1
        measured_check = ttk.Checkbutton(main_frame, text="Measured (vs Calculated)",
                                        variable=self.measured_var)
        measured_check.grid(row=row, column=0, columnspan=2, sticky='w', pady=5)
        
        # Quality
        row += 1
        ttk.Label(main_frame, text="Quality:").grid(row=row, column=0, sticky='w', pady=5)
        quality_combo = ttk.Combobox(main_frame, textvariable=self.quality_var,
                                    values=['good', 'fair', 'poor', 'estimated'],
                                    state='readonly')
        quality_combo.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Data Source
        row += 1
        ttk.Label(main_frame, text="Data Source:").grid(row=row, column=0, sticky='w', pady=5)
        datasource_combo = ttk.Combobox(main_frame, textvariable=self.data_source_var,
                                       values=['manual', 'import', 'scada', 'sensor', 'calculated'],
                                       state='readonly')
        datasource_combo.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Notes
        row += 1
        ttk.Label(main_frame, text="Notes:").grid(row=row, column=0, sticky='nw', pady=5)
        notes_entry = ttk.Entry(main_frame, textvariable=self.notes_var)
        notes_entry.grid(row=row, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        main_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding=(20, 0, 20, 20))
        btn_frame.pack(fill=tk.X)
        
        save_btn = ttk.Button(btn_frame, text="Save", command=self._save,
                             style='Accent.TButton')
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _populate_form(self):
        """Populate form with measurement data if editing"""
        if self.measurement:
            m = self.measurement
            
            # Parse date
            meas_date = m['measurement_date']
            if isinstance(meas_date, str):
                meas_date = datetime.strptime(meas_date, '%Y-%m-%d').date()
            
            self.date_var.set(meas_date.strftime('%Y-%m-%d'))
            self.type_var.set(m['measurement_type'])
            
            # Set source/facility
            if m['source_id']:
                source = next((s for s in self.sources if s['source_id'] == m['source_id']), None)
                if source:
                    self.source_var.set(f"{source['source_code']} - {source['source_name']}")
            
            if m['facility_id']:
                facility = next((f for f in self.facilities if f['facility_id'] == m['facility_id']), None)
                if facility:
                    self.facility_var.set(f"{facility['facility_code']} - {facility['facility_name']}")
            
            # Set values
            if m['volume']:
                self.volume_var.set(str(m['volume']))
            if m['flow_rate']:
                self.flow_rate_var.set(str(m['flow_rate']))
            if m['level_meters']:
                self.level_meters_var.set(str(m['level_meters']))
            if m['level_percent']:
                self.level_percent_var.set(str(m['level_percent']))
            if m['rainfall_mm']:
                self.rainfall_var.set(str(m['rainfall_mm']))
            
            self.measured_var.set(m['measured'])
            self.quality_var.set(m['quality_flag'])
            self.data_source_var.set(m['data_source'])
            
            if m['notes']:
                self.notes_var.set(m['notes'])
    
    def _on_type_changed(self, event=None):
        """Handle measurement type change"""
        # Could auto-populate relevant fields based on type
        pass
    
    def _save(self):
        """Save measurement"""
        # Validate
        if not self.type_var.get():
            messagebox.showwarning("Validation", "Please select a measurement type.")
            return
        
        # Get source/facility IDs
        source_id = None
        if self.source_var.get() and self.source_var.get() != '—':
            source_code = self.source_var.get().split(' - ')[0]
            source = next((s for s in self.sources if s['source_code'] == source_code), None)
            if source:
                source_id = source['source_id']
        
        facility_id = None
        if self.facility_var.get() and self.facility_var.get() != '—':
            facility_code = self.facility_var.get().split(' - ')[0]
            facility = next((f for f in self.facilities if f['facility_code'] == facility_code), None)
            if facility:
                facility_id = facility['facility_id']
        
        # Prepare data
        data = {
            'measurement_date': self.date_var.get(),
            'measurement_type': self.type_var.get(),
            'source_id': source_id,
            'facility_id': facility_id,
            'volume': float(self.volume_var.get()) if self.volume_var.get() else None,
            'flow_rate': float(self.flow_rate_var.get()) if self.flow_rate_var.get() else None,
            'level_meters': float(self.level_meters_var.get()) if self.level_meters_var.get() else None,
            'level_percent': float(self.level_percent_var.get()) if self.level_percent_var.get() else None,
            'rainfall_mm': float(self.rainfall_var.get()) if self.rainfall_var.get() else None,
            'measured': self.measured_var.get(),
            'quality_flag': self.quality_var.get(),
            'data_source': self.data_source_var.get(),
            'notes': self.notes_var.get() if self.notes_var.get() else None
        }
        
        try:
            if self.measurement:
                # Update
                query = """
                    UPDATE measurements SET
                        measurement_date = ?, measurement_type = ?,
                        source_id = ?, facility_id = ?,
                        volume = ?, flow_rate = ?,
                        level_meters = ?, level_percent = ?, rainfall_mm = ?,
                        measured = ?, quality_flag = ?, data_source = ?, notes = ?
                    WHERE measurement_id = ?
                """
                params = (
                    data['measurement_date'], data['measurement_type'],
                    data['source_id'], data['facility_id'],
                    data['volume'], data['flow_rate'],
                    data['level_meters'], data['level_percent'], data['rainfall_mm'],
                    data['measured'], data['quality_flag'], data['data_source'], data['notes'],
                    self.measurement['measurement_id']
                )
                self.db.execute_update(query, params)
                messagebox.showinfo("Success", "Measurement updated successfully.")
            else:
                # Insert
                self.db.add_measurement(data)
                messagebox.showinfo("Success", "Measurement added successfully.")
            
            self.result = True
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save measurement:\n{str(e)}")
