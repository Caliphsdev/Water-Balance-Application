"""
Data Import Module
Handles importing data from Excel files with validation and progress tracking
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import os
import subprocess
import platform
from pathlib import Path
import json


class DataImportModule:
    """Data import interface with Excel file support"""
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.main_frame = None
        self.tree = None
        self.import_type_var = None
        self.file_path_var = None
        self.progress_var = None
        self.status_label = None
        
        # Import configurations
        # Monitoring-related import types removed (scope C)
        self.import_configs = {
            'water_sources': {
                'columns': ['source_code', 'source_name', 'source_type', 'average_flow_rate', 'flow_units'],
                'required': ['source_code', 'source_name', 'source_type']
            },
            'storage_facilities': {
                'columns': ['facility_code', 'facility_name', 'facility_type', 'total_capacity', 'surface_area'],
                'required': ['facility_code', 'facility_name', 'total_capacity']
            },
            'borehole_abstraction': {
                'columns': ['measurement_date', 'source_code', 'flow_rate_m3_month', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'source_code', 'flow_rate_m3_month']
            },
            'river_abstraction': {
                'columns': ['measurement_date', 'source_code', 'flow_rate_m3_month', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'source_code', 'flow_rate_m3_month']
            },
            'facility_level': {
                'columns': ['measurement_date', 'facility_code', 'level_percent', 'level_meters', 'data_source', 'notes'],
                'required': ['measurement_date', 'facility_code']
            },
            'rainfall': {
                'columns': ['measurement_date', 'location_code', 'rainfall_mm', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'location_code', 'rainfall_mm']
            },
            'evaporation': {
                'columns': ['measurement_date', 'location_code', 'evaporation_mm', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'location_code', 'evaporation_mm']
            },
            'plant_consumption': {
                'columns': ['measurement_date', 'department', 'volume_m3', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'department', 'volume_m3']
            },
            'discharge': {
                'columns': ['measurement_date', 'discharge_point', 'volume_m3', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'discharge_point', 'volume_m3']
            },
            'tailings_density': {
                'columns': ['measurement_date', 'density_t_per_m3', 'measured', 'data_source', 'notes'],
                'required': ['measurement_date', 'density_t_per_m3']
            },
            'production_metrics': {
                'columns': [
                    'measurement_date',
                    'tonnes_milled',
                    'pgm_concentrate_wet_tonnes',
                    'pgm_concentrate_moisture_pct',
                    'chromite_concentrate_wet_tonnes',
                    'chromite_concentrate_moisture_pct',
                    'return_water_ratio_m3_per_tonne',
                    'tailings_density_t_per_m3',
                    'measured',
                    'data_source',
                    'notes'
                ],
                'required': ['measurement_date','tonnes_milled']
            },
            'monthly_production': {
                'columns': [
                    'measurement_date',
                    'tonnes_milled',
                    'dry_tonnes_shaft_A',
                    'dry_tonnes_shaft_B',
                    'dry_tonnes_shaft_C',
                    'return_water_volume_m3',
                    'tailings_density_t_per_m3',
                    'pgm_concentrate_wet_tonnes',
                    'pgm_concentrate_moisture_pct',
                    'chromite_concentrate_wet_tonnes',
                    'chromite_concentrate_moisture_pct',
                    'measured',
                    'data_source',
                    'notes'
                ],
                'required': ['measurement_date','tonnes_milled']
            },
            'tsf_return_monthly': {
                'columns': ['month_start', 'tsf_return_m3', 'source', 'notes'],
                'required': ['month_start', 'tsf_return_m3']
            },
            # Monitoring & quality types removed
        }
        # Column synonym maps for flexible import; canonical -> list of possible names
        self.column_synonyms = {
            'water_sources': {
                'source_code': ['source_code', 'code'],
                'source_name': ['source_name', 'name'],
                'source_type': ['source_type', 'type', 'category'],
                'average_flow_rate': ['average_flow_rate', 'avg_flow', 'flow_rate'],
                'flow_units': ['flow_units', 'units'],
                'reliability_factor': ['reliability_factor', 'reliability', 'confidence'],
                'description': ['description', 'notes', 'details'],
                'active': ['active', 'is_active', 'enabled']
            },
            'storage_facilities': {
                'facility_code': ['facility_code', 'code'],
                'facility_name': ['facility_name', 'name'],
                'facility_type': ['facility_type', 'type'],
                'total_capacity': ['total_capacity', 'capacity'],
                'surface_area': ['surface_area', 'area'],
                'max_depth': ['max_depth', 'depth', 'maximum_depth'],
                'purpose': ['purpose', 'type_purpose'],
                'water_quality': ['water_quality', 'quality'],
                'description': ['description', 'notes', 'details'],
                'active': ['active', 'is_active', 'enabled']
            },
            'measurements': {
                'measurement_date': ['measurement_date', 'date'],
                'measurement_type': ['measurement_type', 'type'],
                'source_id': ['source_id', 'src_id'],
                'facility_id': ['facility_id', 'fac_id'],
                'volume': ['volume', 'vol'],
                'flow_rate': ['flow_rate', 'rate'],
                'measured': ['measured', 'is_measured'],
                'data_source': ['data_source', 'source']
            },
            'tailings_density': {
                'measurement_date': ['measurement_date','date'],
                'density_t_per_m3': ['density_t_per_m3','density','tailings_density','slurry_density','density_t_m3'],
                'measured': ['measured','is_measured'],
                'data_source': ['data_source','source'],
                'notes': ['notes','comment','description']
            },
            'production_metrics': {
                'measurement_date': ['measurement_date','date','month'],
                'tonnes_milled': ['tonnes_milled','milled_tonnes','ore_tonnes','tonnes_processed'],
                'pgm_concentrate_wet_tonnes': ['pgm_concentrate_wet_tonnes','pgm_conc_wet_t','pgm_concentrate_tonnes','pgm_wet_tonnes'],
                'pgm_concentrate_moisture_pct': ['pgm_concentrate_moisture_pct','pgm_conc_moisture','pgm_moisture_pct'],
                'chromite_concentrate_wet_tonnes': ['chromite_concentrate_wet_tonnes','chromite_conc_wet_t','chromite_concentrate_tonnes','chromite_wet_tonnes'],
                'chromite_concentrate_moisture_pct': ['chromite_concentrate_moisture_pct','chromite_conc_moisture','chromite_moisture_pct'],
                'return_water_ratio_m3_per_tonne': ['return_water_ratio_m3_per_tonne','return_water_m3_per_t','return_water_ratio','rw_m3_t'],
                'tailings_density_t_per_m3': ['tailings_density_t_per_m3','tailings_density','slurry_density','density_t_per_m3'],
                'measured': ['measured','is_measured'],
                'data_source': ['data_source','source'],
                'notes': ['notes','comment','description']
            },
            'monthly_production': {
                'measurement_date': ['measurement_date','date','month'],
                'tonnes_milled': ['tonnes_milled','milled_tonnes','ore_tonnes','tonnes_processed'],
                'dry_tonnes_shaft_A': ['dry_tonnes_shaft_A','shaft_A_dry_tonnes','shaftA_dry_t','shaft_A_dry'],
                'dry_tonnes_shaft_B': ['dry_tonnes_shaft_B','shaft_B_dry_tonnes','shaftB_dry_t','shaft_B_dry'],
                'dry_tonnes_shaft_C': ['dry_tonnes_shaft_C','shaft_C_dry_tonnes','shaftC_dry_t','shaft_C_dry'],
                'return_water_volume_m3': ['return_water_volume_m3','return_water_m3','return_water_volume','rw_volume_m3'],
                'tailings_density_t_per_m3': ['tailings_density_t_per_m3','tailings_density','slurry_density','density_t_per_m3'],
                'pgm_concentrate_wet_tonnes': ['pgm_concentrate_wet_tonnes','pgm_conc_wet_t','pgm_concentrate_tonnes','pgm_wet_tonnes'],
                'pgm_concentrate_moisture_pct': ['pgm_concentrate_moisture_pct','pgm_conc_moisture','pgm_moisture_pct'],
                'chromite_concentrate_wet_tonnes': ['chromite_concentrate_wet_tonnes','chromite_conc_wet_t','chromite_concentrate_tonnes','chromite_wet_tonnes'],
                'chromite_concentrate_moisture_pct': ['chromite_concentrate_moisture_pct','chromite_conc_moisture','chromite_moisture_pct'],
                'measured': ['measured','is_measured'],
                'data_source': ['data_source','source'],
                'notes': ['notes','comment','description']
            },
            'tsf_return_monthly': {
                'month_start': ['month_start','date','month'],
                'tsf_return_m3': ['tsf_return_m3','return_water_m3','tsf_return','return_volume_m3'],
                'source': ['source','data_source'],
                'notes': ['notes','comment','description']
            },
            # Monitoring synonyms removed
        }

    def _read_excel(self, file_path: str, import_type: str) -> pd.DataFrame:
        """Attempt several sheet names then fall back to first sheet."""
        preferred_names = {
            'water_sources': ['Water Sources', 'Sources', 'water_sources'],
            'storage_facilities': ['Storage Facilities', 'Facilities', 'storage_facilities'],
            'borehole_abstraction': ['Borehole Abstraction', 'Borehole', 'Boreholes', 'borehole_abstraction'],
            'river_abstraction': ['River Abstraction', 'River', 'Rivers', 'river_abstraction'],
            'facility_level': ['Facility Levels', 'Levels', 'Storage Levels', 'facility_level'],
            'rainfall': ['Rainfall', 'Rain', 'rainfall'],
            'evaporation': ['Evaporation', 'Evap', 'evaporation'],
            'plant_consumption': ['Plant Consumption', 'Consumption', 'plant_consumption'],
            'discharge': ['Discharge', 'Discharges', 'discharge'],
            'tailings_density': ['Tailings Density','Slurry Density','tailings_density','slurry_density'],
            'production_metrics': ['Production Metrics','Processing Metrics','Mill Production','production_metrics'],
            'measurements': ['Measurements', 'Data', 'measurements']
        }.get(import_type, ['Data', 'Sheet1'])
        
        # Templates have headers at row 4 (index 3), user files might have headers at row 1
        # Try header at row 4 first (templates), then row 1 (custom files)
        # First attempt: canonical header expected at row index 3 (4th row) for generated templates
        for header_row in [3, 0]:
            try:
                df_try = pd.read_excel(file_path, sheet_name=0, header=header_row)
                # If monitoring_points and columns look shifted (e.g., many unnamed columns), reconstruct
                if import_type == 'monitoring_points' and ('source_code' not in df_try.columns or len(df_try.columns) > 25):
                    raise ValueError('Header misalignment – retry manual extraction')
                return df_try
            except Exception:
                continue
        
        # Try preferred sheet names with different header rows
        for sheet in preferred_names:
            for header_row in [3, 0]:
                try:
                    df_try = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
                    if import_type == 'monitoring_points' and 'source_code' not in df_try.columns:
                        raise ValueError('Need manual header reconstruction (monitoring_points)')
                    return df_try
                except Exception:
                    continue

        # Manual reconstruction fallback for generated multi-row templates
        try:
            raw = pd.read_excel(file_path, sheet_name=0, header=None)
            # Row 3 (index 3) should contain canonical headers for our templates
            header_row = raw.iloc[3].fillna('').tolist()
            raw = raw.iloc[4:]  # data after header
            raw.columns = header_row
            raw = raw[[c for c in header_row if c]]  # drop empty columns
            return raw
        except Exception:
            pass
        
        # Fallback to default behavior
        return pd.read_excel(file_path)

    def _normalize_columns(self, df: pd.DataFrame, import_type: str) -> pd.DataFrame:
        mapping = self.column_synonyms.get(import_type, {})
        # Robust handling: some Excel exports yield non-string column headers (e.g., integers)
        # Cast to string before lowering to avoid AttributeError.
        lower_existing = {}
        for c in df.columns:
            try:
                lower_existing[str(c).lower()] = c
            except Exception:
                continue
        rename_map = {}
        for canonical, variants in mapping.items():
            for variant in variants:
                key = str(variant).lower()
                if key in lower_existing:
                    rename_map[lower_existing[key]] = canonical
                    break
        if rename_map:
            df = df.rename(columns=rename_map)
        return df

    def _validate_required(self, df: pd.DataFrame, import_type: str) -> List[str]:
        required = self.import_configs[import_type]['required']
        return [c for c in required if c not in df.columns]
    
    def load(self):
        """Load the data import interface"""
        # Clear existing content
        if self.main_frame:
            self.main_frame.destroy()
        
        # Create main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="Data Import", font=('Segoe UI', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Import type selection
        selection_frame = ttk.LabelFrame(self.main_frame, text="Import Configuration", padding=15)
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Import type
        type_frame = ttk.Frame(selection_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Import Type:", width=15).pack(side=tk.LEFT, padx=(0, 10))
        self.import_type_var = tk.StringVar(value='borehole_abstraction')
        # Limit import types to those with existing templates in templates folder
        template_types = self._get_template_backed_import_types()
        type_combo = ttk.Combobox(type_frame, textvariable=self.import_type_var,
                                   values=template_types,
                                   state='readonly', width=30)
        type_combo.pack(side=tk.LEFT)
        type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)
        
        # File selection
        file_frame = ttk.Frame(selection_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(file_frame, text="Excel File:", width=15).pack(side=tk.LEFT, padx=(0, 10))
        self.file_path_var = tk.StringVar(master=file_frame)
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self._browse_file)
        browse_btn.pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = ttk.Frame(selection_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        preview_btn = ttk.Button(btn_frame, text="Preview Data", command=self._preview_data)
        preview_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        import_btn = ttk.Button(btn_frame, text="Import Data", command=self._import_data, 
                                style='Accent.TButton')
        import_btn.pack(side=tk.LEFT)
        
        clear_btn = ttk.Button(btn_frame, text="Clear Preview", command=self._clear_preview)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Template folder button
        template_btn = ttk.Button(btn_frame, text="📁 Open Templates Folder", 
                                  command=self._open_templates_folder)
        template_btn.pack(side=tk.RIGHT)
        
        # Progress bar
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.DoubleVar(master=progress_frame)
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                       maximum=100, mode='determinate')
        progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready to import", 
                                      foreground='#666')
        self.status_label.pack()
        
        # Preview area with scrollbars
        preview_frame = ttk.LabelFrame(self.main_frame, text="Data Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(preview_frame, 
                                yscrollcommand=tree_scroll_y.set,
                                xscrollcommand=tree_scroll_x.set,
                                show='headings', height=15)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Instructions
        info_frame = ttk.Frame(self.main_frame)
        info_frame.pack(fill=tk.X, pady=(15, 0))
        
        info_text = """Instructions:
1. Select the import type (water sources, storage facilities, or measurements)
2. Browse and select your Excel file
3. Click 'Preview Data' to validate the file structure
4. Review the data and click 'Import Data' to add to database"""
        
        info_label = ttk.Label(info_frame, text=info_text, foreground='#666', 
                              justify=tk.LEFT, font=('Segoe UI', 9))
        info_label.pack()
    
    def _on_type_changed(self, event=None):
        """Handle import type change"""
        self._clear_preview()
        self._update_status("Import type changed. Please select a file.", 'info')
    
    def _browse_file(self):
        """Open file browser to select Excel file"""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
            self._update_status(f"File selected: {os.path.basename(filename)}", 'info')
    
    def _preview_data(self):
        """Preview Excel file data"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("No File", "Please select an Excel file first.")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"File not found: {file_path}")
            return
        
        import_type = self.import_type_var.get()
        
        try:
            self._update_status("Reading Excel file...", 'info')
            self.progress_var.set(20)
            
            # Read Excel file with flexible sheet + normalize columns
            df = self._read_excel(file_path, import_type)
            df = self._normalize_columns(df, import_type)
            
            self.progress_var.set(40)
            
            # Validate required columns
            missing_required = self._validate_required(df, import_type)
            
            if missing_required:
                required_cols = self.import_configs[import_type]['required']
                messagebox.showerror("Invalid File", 
                    f"Missing required columns: {', '.join(missing_required)}\n\n"
                    f"Required columns: {', '.join(required_cols)}")
                self._update_status("File validation failed", 'error')
                self.progress_var.set(0)
                return
            
            self.progress_var.set(60)
            
            # Display preview
            self._display_preview(df, import_type)

            # Monitoring import assistance: detect missing source codes for measurement types
            # Monitoring assistance removed
            
            self.progress_var.set(100)
            self._update_status(f"Preview loaded: {len(df)} rows", 'success')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file: {str(e)}")
            self._update_status(f"Error: {str(e)}", 'error')
            self.progress_var.set(0)
    
    def _display_preview(self, df: pd.DataFrame, import_type: str):
        """Display data in treeview"""
        # Clear existing data
        self._clear_preview()
        
        # Determine display columns (canonical order + optional recognized columns)
        config = self.import_configs[import_type]
        display_cols = []
        for col in config['columns']:
            if col in df.columns:
                display_cols.append(col)
        # Include additional canonical columns found via synonyms if present
        for col in df.columns:
            if col not in display_cols and col in self.column_synonyms.get(import_type, {}):
                display_cols.append(col)
        
        # Configure columns
        self.tree['columns'] = display_cols
        
        # Autosize columns based on header + sample cell lengths
        sample_rows = df.head(50)
        for col in display_cols:
            header_text = col.replace('_', ' ').title()
            # Long headers remain single line; no wrapping supported in ttk.Treeview
            max_len = len(header_text)
            for val in sample_rows[col].astype(str).tolist():
                if len(val) > max_len:
                    max_len = len(val)
            # Approximate character width in pixels (depends on font; use 7)
            px_width = max(90, min(420, int(max_len * 7)))
            self.tree.heading(col, text=header_text)
            self.tree.column(col, width=px_width, anchor='w', stretch=False)
        
        # Insert data (limit to first 100 rows for preview)
        for idx, row in df.head(100).iterrows():
            values = [str(row.get(col, '')) for col in display_cols]
            self.tree.insert('', tk.END, values=values)
        
        if len(df) > 100:
            # Add info row
            self.tree.insert('', tk.END, values=['...' for _ in display_cols])
        # Force horizontal scrollbar visibility when total width exceeds frame
        total_width = sum(self.tree.column(c, option='width') for c in display_cols)
        try:
            container_width = self.tree.winfo_width()
            if total_width > container_width:
                # Re-pack to ensure horizontal scrollbar is active; already configured but this triggers layout
                self.tree.update_idletasks()
        except Exception:
            pass
    
    def _import_data(self):
        """Import data from Excel file to database"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("No File", "Please select an Excel file first.")
            return
        
        import_type = self.import_type_var.get()
        
        # Confirm import
        result = messagebox.askyesno("Confirm Import", 
            f"Import data from:\n{os.path.basename(file_path)}\n\n"
            f"Import type: {import_type.replace('_', ' ').title()}\n\n"
            "Continue with import?")
        
        if not result:
            return
        
        try:
            self._update_status("Starting import...", 'info')
            self.progress_var.set(10)
            
            # Read Excel file (flexible sheet + normalize)
            df = self._read_excel(file_path, import_type)
            df = self._normalize_columns(df, import_type)
            total_rows = len(df)
            
            self.progress_var.set(20)
            
            # Import based on type
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    if import_type == 'water_sources':
                        self._import_water_source(row)
                    elif import_type == 'storage_facilities':
                        self._import_storage_facility(row)
                    elif import_type == 'borehole_abstraction':
                        self._import_borehole_abstraction(row)
                    elif import_type == 'river_abstraction':
                        self._import_river_abstraction(row)
                    elif import_type == 'facility_level':
                        self._import_facility_level(row)
                    elif import_type == 'rainfall':
                        self._import_rainfall(row)
                    elif import_type == 'evaporation':
                        self._import_evaporation(row)
                    elif import_type == 'plant_consumption':
                        self._import_plant_consumption(row)
                    elif import_type == 'discharge':
                        self._import_discharge(row)
                    elif import_type == 'tailings_density':
                        self._import_tailings_density(row)
                    elif import_type == 'production_metrics':
                        self._import_production_metrics(row)
                    elif import_type == 'monthly_production':
                        self._import_monthly_production(row)
                    elif import_type == 'tsf_return_monthly':
                        self._import_tsf_return_monthly(row)
                    # Monitoring branches removed
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {idx + 2}: {str(e)}")
                
                # Update progress
                progress = 20 + (idx / total_rows * 70)
                self.progress_var.set(progress)
                self.parent.update_idletasks()
            
            self.progress_var.set(100)
            
            # Show results
            if error_count == 0:
                messagebox.showinfo("Import Complete", 
                    f"Successfully imported {success_count} records!")
                self._update_status(f"Import complete: {success_count} records", 'success')
            else:
                error_msg = f"Imported {success_count} records\n"
                error_msg += f"Failed: {error_count} records\n\n"
                error_msg += "Errors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                
                messagebox.showwarning("Import Complete with Errors", error_msg)
                self._update_status(f"Import complete: {success_count} success, {error_count} errors", 'warning')
            
            # Refresh preview
            self._preview_data()
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Error during import: {str(e)}")
            self._update_status(f"Import failed: {str(e)}", 'error')
            self.progress_var.set(0)
    
    def _import_water_source(self, row: pd.Series):
        """Import a water source record"""
        source_code = str(row.get('source_code', '')).strip()
        source_name = str(row.get('source_name', '')).strip()
        source_type_val = str(row.get('source_type', '')).strip()
        if not source_code or not source_name or not source_type_val:
            raise ValueError("Missing required fields (source_code, source_name, source_type)")

        # Resolve type_id from water_source_types by matching type_code or type_name (case-insensitive)
        types = self.db.execute_query("SELECT type_id, type_code, type_name FROM water_source_types")
        match = None
        for t in types:
            if source_type_val.lower() in {t['type_code'].lower(), t['type_name'].lower()}:
                match = t
                break
        if not match:
            raise ValueError(f"Unknown source_type '{source_type_val}' - must match one of {[t['type_code'] for t in types]}")
        type_id = match['type_id']

        # Duplicate check
        existing = self.db.execute_query(
            "SELECT source_id FROM water_sources WHERE source_code = ?",
            (source_code,)
        )
        if existing:
            raise ValueError(f"Water source {source_code} already exists")

        # Reliability factor may be given as percentage (e.g. 85) or fraction (0.85)
        raw_reliability = row.get('reliability_factor', 0.85)
        try:
            rf = float(raw_reliability) if raw_reliability is not None else 0.85
        except Exception:
            rf = 0.85
        if rf > 1:  # assume percentage
            rf = rf / 100.0
        data = {
            'source_code': source_code,
            'source_name': source_name,
            'type_id': type_id,
            'average_flow_rate': float(row.get('average_flow_rate', 0) or 0),
            'flow_units': str(row.get('flow_units', 'm³/month')),
            'reliability_factor': rf,
            'description': str(row.get('description', '')),
            'active': int(row.get('active', 1) or 1)
        }
        self.db.add_water_source(**data)

    
    def _import_storage_facility(self, row: pd.Series):
        """Import a storage facility record"""
        data = {
            'facility_code': str(row.get('facility_code', '')),
            'facility_name': str(row.get('facility_name', '')),
            'facility_type': str(row.get('facility_type', 'Dam')),
            'total_capacity': float(row.get('total_capacity', 0)),
            'surface_area': float(row.get('surface_area', 0)) if row.get('surface_area') else None,
            'max_depth': float(row.get('max_depth', 0)) if row.get('max_depth') else None,
            'purpose': str(row.get('purpose', 'raw_water')),
            'water_quality': str(row.get('water_quality', 'process')),
            'description': str(row.get('description', '')),
            'active': int(row.get('active', 1))
        }
        
        # Check if facility already exists
        existing = self.db.execute_query(
            "SELECT facility_id FROM storage_facilities WHERE facility_code = ?",
            (data['facility_code'],)
        )
        
        if existing:
            raise ValueError(f"Storage facility {data['facility_code']} already exists")
        
        # Correct call signature: unpack dict as keywords
        self.db.add_storage_facility(**data)
    
    def _import_measurement(self, row: pd.Series):
        """Import a measurement record"""
        # Parse date
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()
        
        data = {
            'measurement_date': measurement_date,
            'measurement_type': str(row.get('measurement_type', '')),
            'source_id': int(row['source_id']) if pd.notna(row.get('source_id')) else None,
            'facility_id': int(row['facility_id']) if pd.notna(row.get('facility_id')) else None,
            'volume': float(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
            'flow_rate': float(row.get('flow_rate', 0)) if pd.notna(row.get('flow_rate')) else None,
            'measured': int(row.get('measured', 1)),
            'data_source': str(row.get('data_source', 'import'))
        }
        # Duplicate safety: composite uniqueness (date, type, source_id, facility_id)
        existing = self.db.execute_query(
            """
            SELECT measurement_id FROM measurements
            WHERE measurement_date = ? AND measurement_type = ?
                  AND IFNULL(source_id,'') = IFNULL(?, '')
                  AND IFNULL(facility_id,'') = IFNULL(?, '')
            LIMIT 1
            """,
            (
                data['measurement_date'], data['measurement_type'],
                data['source_id'], data['facility_id']
            )
        )
        if existing:
            raise ValueError("Duplicate measurement (date/type/source/facility) already exists")

        self.db.add_measurement(data)
    
    def _import_borehole_abstraction(self, row: pd.Series):
        """Import borehole abstraction record using source_code"""
        # Parse date
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()

        # Anchor to first day of month (Option C) while preserving original day
        original_date = measurement_date
        if measurement_date.day != 1:
            measurement_date = measurement_date.replace(day=1)
            original_note_fragment = f" (orig date {original_date.isoformat()})"
        else:
            original_note_fragment = ""
        
        # Lookup source_id from source_code
        source_code = str(row.get('source_code', '')).strip()
        source = self.db.execute_query(
            "SELECT source_id FROM water_sources WHERE source_code = ?",
            (source_code,)
        )
        
        if not source:
            raise ValueError(f"Borehole not found with code: {source_code}")
        
        source_id = source[0]['source_id']
        flow_rate = float(row.get('flow_rate_m3_month', 0))
        
        # Robust measured parsing (defaults to 1 if blank/NaN)
        measured_raw = row.get('measured', 1)
        measured_flag = 1
        try:
            if pd.isna(measured_raw) or str(measured_raw).strip() == '':
                measured_flag = 1
            else:
                txt = str(measured_raw).strip().lower()
                if txt in {'0','no','n','false','f'}:
                    measured_flag = 0
                elif txt in {'1','yes','y','true','t'}:
                    measured_flag = 1
                else:
                    measured_flag = int(float(measured_raw))
        except Exception:
            measured_flag = 1
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'source_flow',
            'source_id': source_id,
            'facility_id': None,
            'volume': None,
            'flow_rate': flow_rate,
            'measured': measured_flag,
            'data_source': str(row.get('data_source', 'import')),
            'notes': (str(row.get('notes', '')) + original_note_fragment).strip() if pd.notna(row.get('notes')) or original_note_fragment else (original_note_fragment.strip() or None)
        }
        
        # Check for duplicates
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'source_flow'
               AND source_id = ?""",
            (data['measurement_date'], source_id)
        )
        
        if existing:
            raise ValueError(f"Duplicate: {source_code} abstraction for {measurement_date} already exists")
        
        self.db.add_measurement(data)
    
    def _import_river_abstraction(self, row: pd.Series):
        """Import river abstraction record using source_code"""
        # Parse date
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()

        # Anchor to first day of month (Option C)
        original_date = measurement_date
        if measurement_date.day != 1:
            measurement_date = measurement_date.replace(day=1)
            original_note_fragment = f" (orig date {original_date.isoformat()})"
        else:
            original_note_fragment = ""
        
        # Lookup source_id from source_code
        source_code = str(row.get('source_code', '')).strip()
        source = self.db.execute_query(
            "SELECT source_id FROM water_sources WHERE source_code = ?",
            (source_code,)
        )
        
        if not source:
            raise ValueError(f"River not found with code: {source_code}")
        
        source_id = source[0]['source_id']
        flow_rate = float(row.get('flow_rate_m3_month', 0))
        
        measured_raw = row.get('measured', 1)
        measured_flag = 1
        try:
            if pd.isna(measured_raw) or str(measured_raw).strip() == '':
                measured_flag = 1
            else:
                txt = str(measured_raw).strip().lower()
                if txt in {'0','no','n','false','f'}:
                    measured_flag = 0
                elif txt in {'1','yes','y','true','t'}:
                    measured_flag = 1
                else:
                    measured_flag = int(float(measured_raw))
        except Exception:
            measured_flag = 1
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'source_flow',
            'source_id': source_id,
            'facility_id': None,
            'volume': None,
            'flow_rate': flow_rate,
            'measured': measured_flag,
            'data_source': str(row.get('data_source', 'import')),
            'notes': (str(row.get('notes', '')) + original_note_fragment).strip() if pd.notna(row.get('notes')) or original_note_fragment else (original_note_fragment.strip() or None)
        }
        
        # Check for duplicates
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'source_flow'
               AND source_id = ?""",
            (data['measurement_date'], source_id)
        )
        
        if existing:
            raise ValueError(f"Duplicate: {source_code} abstraction for {measurement_date} already exists")
        
        self.db.add_measurement(data)
    
    def _import_facility_level(self, row: pd.Series):
        """Import storage facility level record using facility_code"""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()
        
        facility_code = str(row.get('facility_code', '')).strip()
        facility = self.db.execute_query(
            "SELECT facility_id FROM storage_facilities WHERE facility_code = ?",
            (facility_code,)
        )
        
        if not facility:
            raise ValueError(f"Storage facility not found with code: {facility_code}")
        
        facility_id = facility[0]['facility_id']
        
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'facility_level',
            'source_id': None,
            'facility_id': facility_id,
            'volume': None,
            'flow_rate': None,
            'level_meters': float(row.get('level_meters')) if pd.notna(row.get('level_meters')) else None,
            'level_percent': float(row.get('level_percent')) if pd.notna(row.get('level_percent')) else None,
            'data_source': str(row.get('data_source', 'import')),
            'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
        }
        
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'facility_level'
               AND facility_id = ?""",
            (data['measurement_date'], facility_id)
        )
        
        if existing:
            raise ValueError(f"Duplicate: {facility_code} level for {measurement_date} already exists")
        
        self.db.add_measurement(data)
    
    def _import_rainfall(self, row: pd.Series):
        """Import rainfall record"""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()
        
        location_code = str(row.get('location_code', '')).strip()
        rainfall_mm = float(row.get('rainfall_mm', 0))
        
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'rainfall',
            'source_id': None,
            'facility_id': None,
            'volume': None,
            'flow_rate': None,
            'rainfall_mm': rainfall_mm,
            'measured': int(row.get('measured', 1)),
            'data_source': str(row.get('data_source', 'import')),
            'notes': f"{location_code}: {row.get('notes', '')}" if pd.notna(row.get('notes')) else location_code
        }
        
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'rainfall'
               AND notes LIKE ?""",
            (data['measurement_date'], f"{location_code}:%")
        )
        
        if existing:
            raise ValueError(f"Duplicate: Rainfall for {location_code} on {measurement_date} already exists")
        
        self.db.add_measurement(data)
    
    def _import_evaporation(self, row: pd.Series):
        """Import evaporation record"""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()
        
        location_code = str(row.get('location_code', '')).strip()
        evaporation_mm = float(row.get('evaporation_mm', 0))
        
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'evaporation',
            'source_id': None,
            'facility_id': None,
            'volume': None,
            'flow_rate': None,
            # Correct field name: store evaporation in its own column
            'evaporation_mm': evaporation_mm,
            'measured': int(row.get('measured', 0)),
            'data_source': str(row.get('data_source', 'import')),
            'notes': f"{location_code}: {row.get('notes', '')}" if pd.notna(row.get('notes')) else location_code
        }
        
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'evaporation'
               AND notes LIKE ?""",
            (data['measurement_date'], f"{location_code}:%")
        )
        
        if existing:
            raise ValueError(f"Duplicate: Evaporation for {location_code} on {measurement_date} already exists")
        
        self.db.add_measurement(data)
    
    def _import_plant_consumption(self, row: pd.Series):
        """Import plant consumption record"""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()
        
        department = str(row.get('department', '')).strip()
        volume_m3 = float(row.get('volume_m3', 0))
        
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'plant_consumption',
            'source_id': None,
            'facility_id': None,
            'volume': volume_m3,
            'flow_rate': None,
            'measured': int(row.get('measured', 1)),
            'data_source': str(row.get('data_source', 'import')),
            'notes': f"{department}: {row.get('notes', '')}" if pd.notna(row.get('notes')) else department
        }
        
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'plant_consumption'
               AND notes LIKE ?""",
            (data['measurement_date'], f"{department}:%")
        )
        
        if existing:
            raise ValueError(f"Duplicate: Plant consumption for {department} on {measurement_date} already exists")
        
        self.db.add_measurement(data)
    
    def _import_discharge(self, row: pd.Series):
        """Import discharge/outflow record"""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()
        
        discharge_point = str(row.get('discharge_point', '')).strip()
        volume_m3 = float(row.get('volume_m3', 0))
        
        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'discharge',
            'source_id': None,
            'facility_id': None,
            'volume': volume_m3,
            'flow_rate': None,
            'measured': int(row.get('measured', 1)),
            'data_source': str(row.get('data_source', 'import')),
            'notes': f"{discharge_point}: {row.get('notes', '')}" if pd.notna(row.get('notes')) else discharge_point
        }
        
        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'discharge'
               AND notes LIKE ?""",
            (data['measurement_date'], f"{discharge_point}:%")
        )
        
        if existing:
            raise ValueError(f"Duplicate: Discharge from {discharge_point} on {measurement_date} already exists")
        
        self.db.add_measurement(data)

    def _import_tailings_density(self, row: pd.Series):
        """Import monthly tailings slurry density (t/m³). Stored in flow_rate field."""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            # Allow YYYY-MM or full date; normalize to first day of month for uniqueness
            try:
                if len(measurement_date) == 7:  # YYYY-MM
                    measurement_date = datetime.strptime(measurement_date+'-01', '%Y-%m-%d').date()
                else:
                    measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
            except Exception:
                # Fallback robust parse
                measurement_date = pd.to_datetime(measurement_date).date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()

        # Accept multiple synonym column names
        density_val = None
        for key in ['density_t_per_m3','density','tailings_density','slurry_density','density_t_m3']:
            if key in row and pd.notna(row.get(key)):
                try:
                    density_val = float(row.get(key))
                    break
                except Exception:
                    continue
        if density_val is None:
            raise ValueError("Missing density value (t/m³)")
        if density_val <= 0:
            raise ValueError("Density must be positive")

        data = {
            'measurement_date': measurement_date,
            'measurement_type': 'tailings_density',
            'source_id': None,
            'facility_id': None,
            'volume': None,
            'flow_rate': density_val,
            'measured': int(row.get('measured', 1)),
            'data_source': str(row.get('data_source', 'import')),
            'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
        }

        existing = self.db.execute_query(
            """SELECT measurement_id FROM measurements
               WHERE measurement_date = ? AND measurement_type = 'tailings_density'""",
            (data['measurement_date'],)
        )
        if existing:
            raise ValueError(f"Duplicate: tailings density for {measurement_date} already exists")
        self.db.add_measurement(data)

    def _import_production_metrics(self, row: pd.Series):
        """Import a row of production / processing metrics creating multiple measurement rows."""
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            try:
                if len(measurement_date) == 7:  # YYYY-MM
                    measurement_date = datetime.strptime(measurement_date+'-01', '%Y-%m-%d').date()
                else:
                    measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
            except Exception:
                measurement_date = pd.to_datetime(measurement_date).date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()

        metrics_map = {
            'tonnes_milled': ('tonnes_milled', 'volume'),
            'pgm_concentrate_wet_tonnes': ('pgm_concentrate_wet_tonnes', 'volume'),
            'pgm_concentrate_moisture_pct': ('pgm_concentrate_moisture_pct', 'flow_rate'),
            'chromite_concentrate_wet_tonnes': ('chromite_concentrate_wet_tonnes', 'volume'),
            'chromite_concentrate_moisture_pct': ('chromite_concentrate_moisture_pct', 'flow_rate'),
            'return_water_ratio_m3_per_tonne': ('return_water_ratio_m3_per_tonne', 'flow_rate'),
            'tailings_density_t_per_m3': ('tailings_density', 'flow_rate')  # Reuse tailings_density type
        }

        inserted = 0
        for col, (m_type, target_field) in metrics_map.items():
            if col in row and pd.notna(row.get(col)):
                try:
                    val = float(row.get(col))
                except Exception:
                    continue
                if val < 0:
                    continue
                # Duplicate check
                existing = self.db.execute_query(
                    """SELECT measurement_id FROM measurements
                           WHERE measurement_date = ? AND measurement_type = ? LIMIT 1""",
                    (measurement_date, m_type)
                )
                if existing:
                    # Skip duplicates silently to allow partial updates without failure
                    continue
                data = {
                    'measurement_date': measurement_date,
                    'measurement_type': m_type,
                    'source_id': None,
                    'facility_id': None,
                    'volume': val if target_field == 'volume' else None,
                    'flow_rate': val if target_field == 'flow_rate' else None,
                    'measured': int(row.get('measured', 1)),
                    'data_source': str(row.get('data_source', 'import')),
                    'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
                }
                self.db.add_measurement(data)
                inserted += 1
        if inserted == 0:
            raise ValueError("No production metrics values found to import")

    def _import_monthly_production(self, row: pd.Series):
        """Import monthly production metrics (Option A) as separate measurement rows.
        Expected columns (with synonyms):
        - measurement_date (YYYY-MM or date)
        - tonnes_milled (t)
        - dry_tonnes_shaft_A (t)
        - dry_tonnes_shaft_B (t)
        - return_water_volume_m3 (m³)
        - tailings_density_t_per_m3 (t/m³)
        Creates measurement rows: tonnes_milled, dry_tonnes_shaft_A, dry_tonnes_shaft_B,
        return_water_volume, tailings_density.
        """
        measurement_date = row.get('measurement_date')
        if isinstance(measurement_date, str):
            try:
                if len(measurement_date) == 7:  # YYYY-MM
                    measurement_date = datetime.strptime(measurement_date+'-01', '%Y-%m-%d').date()
                else:
                    measurement_date = datetime.strptime(measurement_date, '%Y-%m-%d').date()
            except Exception:
                measurement_date = pd.to_datetime(measurement_date).date()
        elif hasattr(measurement_date, 'date'):
            measurement_date = measurement_date.date()

        mapping = [
            ('tonnes_milled', 'tonnes_milled', 'volume'),
            ('dry_tonnes_shaft_A', 'dry_tonnes_shaft_A', 'volume'),
            ('dry_tonnes_shaft_B', 'dry_tonnes_shaft_B', 'volume'),
            ('dry_tonnes_shaft_C', 'dry_tonnes_shaft_C', 'volume'),
            ('return_water_volume_m3', 'return_water_volume', 'volume'),
            ('tailings_density_t_per_m3', 'tailings_density', 'flow_rate')
            ,('pgm_concentrate_wet_tonnes','pgm_concentrate_wet_tonnes','volume')
            ,('pgm_concentrate_moisture_pct','pgm_concentrate_moisture_pct','flow_rate')
            ,('chromite_concentrate_wet_tonnes','chromite_concentrate_wet_tonnes','volume')
            ,('chromite_concentrate_moisture_pct','chromite_concentrate_moisture_pct','flow_rate')
        ]
        inserted = 0
        for col, m_type, target_field in mapping:
            if col in row and pd.notna(row.get(col)):
                try:
                    val = float(row.get(col))
                except Exception:
                    continue
                if val < 0:
                    continue
                # Duplicate prevention (monthly uniqueness)
                existing = self.db.execute_query(
                    """SELECT measurement_id FROM measurements
                        WHERE measurement_date = ? AND measurement_type = ? LIMIT 1""",
                    (measurement_date, m_type)
                )
                if existing:
                    # Skip duplicates to allow partial updates
                    continue
                data = {
                    'measurement_date': measurement_date,
                    'measurement_type': m_type,
                    'source_id': None,
                    'facility_id': None,
                    'volume': val if target_field == 'volume' else None,
                    'flow_rate': val if target_field == 'flow_rate' else None,
                    'measured': int(row.get('measured', 1)),
                    'data_source': str(row.get('data_source', 'import')),
                    'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
                }
                self.db.add_measurement(data)
                inserted += 1
        if inserted == 0:
            raise ValueError("No monthly production values found to import")

    def _parse_date(self, value):
        """Parse a date from string or excel datetime-like into date object."""
        if isinstance(value, str):
            # Try common formats
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y', '%Y-%m'):
                try:
                    return datetime.strptime(value, fmt).date()
                except Exception:
                    continue
            # Fallback: try pandas to_datetime
            try:
                return pd.to_datetime(value).date()
            except Exception:
                raise ValueError(f"Unrecognized date format: {value}")
        elif hasattr(value, 'date'):
            return value.date()
        return value

    def _lookup_source_id_by_code(self, code: str) -> Optional[int]:
        code = (code or '').strip()
        if not code:
            return None
        source = self.db.execute_query(
            "SELECT source_id FROM water_sources WHERE source_code = ?",
            (code,)
        )
        return source[0]['source_id'] if source else None






    # ===== New comprehensive template handlers =====



    def _import_tsf_return_monthly(self, row: pd.Series):
        """Import or update monthly TSF return volume (m3) in tsf_return_monthly table.
        Expects month_start (YYYY-MM or date) and tsf_return_m3 columns.
        """
        month_start = row.get('month_start')
        if isinstance(month_start, str):
            try:
                # Allow YYYY-MM or full date and normalize to first of month
                if len(month_start) == 7:  # YYYY-MM
                    month_start = datetime.strptime(month_start + '-01', '%Y-%m-%d').date()
                else:
                    month_start = datetime.strptime(month_start, '%Y-%m-%d').date()
            except Exception:
                month_start = pd.to_datetime(month_start).date()
        elif hasattr(month_start, 'date'):
            month_start = month_start.date()

        if not month_start:
            raise ValueError("month_start is required")

        # Anchor to first day of the month for all parsed dates
        try:
            month_start = month_start.replace(day=1)
        except Exception:
            raise ValueError("Invalid month_start date value")

        try:
            tsf_val = float(row.get('tsf_return_m3', 0))
        except Exception:
            raise ValueError("tsf_return_m3 must be a number")
        if tsf_val < 0:
            raise ValueError("tsf_return_m3 must be non-negative")

        source = str(row.get('source', 'import')).strip() or 'import'
        notes = str(row.get('notes', '')).strip() or None

        existing = self.db.execute_query(
            "SELECT tsf_id FROM tsf_return_monthly WHERE month_start = ?",
            (month_start,)
        )
        if existing:
            self.db.execute_update(
                """
                UPDATE tsf_return_monthly
                SET tsf_return_m3 = ?, source = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE month_start = ?
                """,
                (tsf_val, source, notes, month_start)
            )
        else:
            self.db.execute_update(
                """
                INSERT INTO tsf_return_monthly (month_start, tsf_return_m3, source, notes)
                VALUES (?, ?, ?, ?)
                """,
                (month_start, tsf_val, source, notes)
            )


    
    def _clear_preview(self):
        """Clear preview treeview"""
        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.tree['columns'] = []
    
    def _open_templates_folder(self):
        """Open the templates folder in the system file manager"""
        try:
            # Get absolute templates folder path
            templates_path = Path(__file__).parent.parent.parent / 'templates'
            templates_path = templates_path.resolve()  # Convert to absolute path
            
            # Ensure the folder exists
            if not templates_path.exists():
                messagebox.showerror("Error", f"Templates folder not found at:\n{templates_path}")
                return
            
            # Open folder based on platform
            system = platform.system()
            
            if system == 'Linux':
                subprocess.Popen(['xdg-open', str(templates_path)])
            elif system == 'Windows':
                os.startfile(str(templates_path))
            elif system == 'Darwin':  # macOS
                subprocess.Popen(['open', str(templates_path)])
            else:
                messagebox.showinfo("Info", 
                                  f"Templates folder location:\n{templates_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open templates folder:\n{str(e)}")
    
    def _update_status(self, message: str, status: str = 'info'):
        """Update status label"""
        colors = {
            'info': '#666',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545'
        }
        
        if self.status_label:
            self.status_label.config(text=message, foreground=colors.get(status, '#666'))
    
    def refresh_data(self):
        """Refresh the module data"""
        # Nothing to refresh in import module
        pass

    def _get_template_backed_import_types(self) -> List[str]:
        """Return list of import types for which a template workbook exists.
        Maps template filename stems to import type keys used in import_configs.
        """
        # Mapping from template stem to import type
        stem_map = {
            'borehole_abstraction': 'borehole_abstraction',
            'river_abstraction': 'river_abstraction',
            'facility_level': 'facility_level',
            'rainfall': 'rainfall',
            'evaporation': 'evaporation',
            'plant_consumption': 'plant_consumption',
            'discharge': 'discharge',
            'tailings_density': 'tailings_density',
            'production_metrics': 'production_metrics',
            'monthly_production': 'monthly_production',
            'tsf_return_monthly': 'tsf_return_monthly',
            'water_sources': 'water_sources',
            'storage_facilities': 'storage_facilities',
            'static_level': 'static_level',
            'monitoring_borehole': 'monitoring_borehole',
            'groundwater_quality': 'groundwater_quality',
            'river_monitoring': 'river_monitoring',
            'pcd_quality': 'pcd_quality',
            'stp_effluent': 'stp_effluent',
            'monitoring_points': 'monitoring_points'
        }
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        
        # Stable ordering preference (defined first)
        order = ['water_sources','storage_facilities','production_metrics','monitoring_points','borehole_abstraction','river_abstraction','facility_level',
               'rainfall','evaporation','plant_consumption','discharge','static_level','monitoring_borehole','groundwater_quality',
               'river_monitoring','pcd_quality','stp_effluent','tailings_density','tsf_return_monthly']
        
        available = []
        if templates_dir.exists():
            for f in templates_dir.glob('*_template.xlsx'):
                stem = f.name.replace('_template.xlsx', '')
                mapped = stem_map.get(stem)
                if mapped and mapped in self.import_configs:
                    available.append(mapped)
        
        ordered = [t for t in order if t in available]
        return ordered or ['water_sources']

    # ===== Monitoring import assistance =====
    def _detect_missing_source_codes(self, df: pd.DataFrame, import_type: str) -> List[str]:
        """Return list of codes in dataframe that are not present in water_sources."""
        code_cols_priority = {
            'static_level': ['source_code','borehole_code'],
            'monitoring_borehole': ['borehole_code','source_code'],
            'groundwater_quality': ['source_code','borehole_code'],
            'surface_water_quality': ['location_code','river_code','source_code'],
            'river_monitoring': ['river_code','location_code','source_code'],
            'pcd_quality': ['pcd_code','source_code'],
            'stp_effluent': ['plant_code','source_code'],
        }
        cols = code_cols_priority.get(import_type, [])
        use_col = None
        for c in cols:
            if c in df.columns:
                use_col = c
                break
        if not use_col:
            return []
        codes = sorted({str(v).strip() for v in df[use_col].tolist() if str(v).strip()})
        if not codes:
            return []
        placeholders = ",".join(['?']*len(codes))
        existing_rows = self.db.execute_query(f"SELECT source_code FROM water_sources WHERE source_code IN ({placeholders})", tuple(codes))
        existing_codes = {r['source_code'] for r in existing_rows}
        return [c for c in codes if c not in existing_codes]

    def _infer_source_type_for_import(self, import_type: str) -> str:
        mapping = {
            'static_level': 'Borehole',
            'monitoring_borehole': 'Borehole',
            'groundwater_quality': 'Borehole',
            'surface_water_quality': 'River',
            'river_monitoring': 'River',
            'pcd_quality': 'PCD',
            'stp_effluent': 'STP'
        }
        return mapping.get(import_type, 'Borehole')

    def _auto_create_monitoring_points(self, codes: List[str], type_name: str) -> int:
        """Create monitoring water_sources for missing codes with given type_name."""
        if not codes:
            return 0
        types = self.db.execute_query("SELECT type_id, type_code, type_name FROM water_source_types")
        match = None
        for t in types:
            if type_name.lower() in {t['type_code'].lower(), t['type_name'].lower()}:
                match = t
                break
        if not match:
            raise ValueError(f"Source type '{type_name}' not found")
        type_id = match['type_id']
        created = 0
        for code in codes:
            try:
                data = {
                    'source_code': code,
                    'source_name': code,
                    'type_id': type_id,
                    'source_purpose': 'MONITORING',
                    'average_flow_rate': 0.0,
                    'flow_units': 'm³/month',
                    'reliability_factor': 1.0,
                    'active': 1
                }
                self.db.add_water_source(**data)
                created += 1
            except Exception:
                continue
        return created
