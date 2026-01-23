"""
Analytics & Trends Dashboard
Statistical analysis and trend visualization of water balance data
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date
from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.app_logger import logger
from utils.config_manager import ConfigManager


class AnalyticsDashboard:
    """Analytics dashboard for water source trend analysis with auto-detection"""
    
    def __init__(self, parent):
        self.parent = parent
        self.config = ConfigManager()
        self.main_frame = None
        self.chart_canvas = None
        self.excel_file_path = tk.StringVar(master=parent, value="")
        self.selected_source = tk.StringVar(master=parent, value="All Sources")
        self.chart_type = tk.StringVar(master=parent, value="Line Chart")
        self.start_year = tk.StringVar(master=parent, value="")
        self.start_month = tk.StringVar(master=parent, value="")
        self.end_year = tk.StringVar(master=parent, value="")
        self.end_month = tk.StringVar(master=parent, value="")
        self.source_data = None  # Cached DataFrame
        self.available_sources = []  # List of detected column names
        self.min_date = None  # For date range validation
        self.max_date = None
        self.file_section_expanded = tk.BooleanVar(master=parent, value=True)  # Collapsible state
        self.file_section_content = None  # Reference to collapsible content
        self.chart_options_expanded = tk.BooleanVar(master=parent, value=True)  # Chart options collapsible state
        self.chart_options_content = None  # Reference to chart options content
        self.chart_expand_indicator = None  # Reference to expand/collapse indicator
        
    def load(self):
        """Load the analytics dashboard"""
        if self.main_frame:
            self.main_frame.destroy()
        
        # Create outer container with professional background
        outer = tk.Frame(self.parent, bg='#f5f6f7')
        outer.pack(fill=tk.BOTH, expand=True)
        
        self.main_frame = tk.Frame(outer, bg='#f5f6f7')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header
        self._create_header()
        
        # File selector
        self._create_file_selector()
        
        # Controls placeholder (will be populated after file load)
        self.control_container = ttk.Frame(self.main_frame)
        self.control_container.pack(fill=tk.X, pady=(0, 15))
        
        # Chart area
        self._create_chart_area()
        
        # Show placeholder
        self._show_placeholder()
    
    def _create_header(self):
        """Create modern header section"""
        header_frame = tk.Frame(self.main_frame, bg='white', relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 0), padx=0)
        
        inner = tk.Frame(header_frame, bg='white')
        inner.pack(fill=tk.X, padx=20, pady=20)
        
        title = tk.Label(inner, text="📊 Analytics & Trends", 
                         font=('Segoe UI', 22, 'bold'),
                         bg='white', fg='#2c3e50')
        title.pack(anchor='w')
        
        info = tk.Label(inner, 
                        text="Water source trend analysis and visualization",
                        font=('Segoe UI', 11),
                        fg='#7f8c8d',
                        bg='white')
        info.pack(anchor='w', pady=(3, 0))
    
    def _create_file_selector(self):
        """Create modern collapsible file selection card"""
        # Add padding to main frame and separator after header
        separator = tk.Frame(self.main_frame, bg='#f5f6f7', height=0)
        separator.pack(fill=tk.X, padx=0)
        
        # Content area
        content_frame = tk.Frame(self.main_frame, bg='#f5f6f7')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        file_frame = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=1, highlightbackground='#d0d5dd', highlightthickness=1)
        file_frame.pack(fill=tk.X, pady=(0, 20), padx=0)
        
        # Collapsible header with click handler
        header_frame = tk.Frame(file_frame, bg='white', cursor='hand2')
        header_frame.pack(fill=tk.X, padx=20, pady=16)
        header_frame.bind('<Button-1>', lambda e: self._toggle_file_section())
        
        # Icon and title row
        icon_title_row = tk.Frame(header_frame, bg='white')
        icon_title_row.pack(fill=tk.X)
        
        # Expand/collapse indicator
        self.expand_indicator = tk.Label(
            icon_title_row, 
            text="▼", 
            font=('Segoe UI', 10), 
            bg='white', 
            fg='#3498db',
            cursor='hand2'
        )
        self.expand_indicator.pack(side=tk.LEFT, padx=(0, 8))
        self.expand_indicator.bind('<Button-1>', lambda e: self._toggle_file_section())
        
        title_label = tk.Label(
            icon_title_row, 
            text="📁 Data Source File", 
            font=('Segoe UI', 12, 'bold'), 
            bg='white', 
            fg='#2c3e50',
            cursor='hand2'
        )
        title_label.pack(side=tk.LEFT)
        title_label.bind('<Button-1>', lambda e: self._toggle_file_section())
        
        # Status indicator (shows file loaded state)
        self.file_status_label = tk.Label(
            icon_title_row,
            text="",
            font=('Segoe UI', 9),
            bg='white',
            fg='#27ae60'
        )
        self.file_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Collapsible content section
        self.file_section_content = tk.Frame(file_frame, bg='white')
        self.file_section_content.pack(fill=tk.X, padx=20, pady=(0, 16))
        
        tk.Label(
            self.file_section_content, 
            text="Excel file with Meter Readings:", 
            font=('Segoe UI', 10), 
            bg='white', 
            fg='#34495e'
        ).pack(anchor='w', pady=(0, 5))
        
        path_row = tk.Frame(self.file_section_content, bg='white')
        path_row.pack(fill=tk.X)
        
        entry = tk.Entry(path_row, textvariable=self.excel_file_path, state='readonly', 
                 font=('Segoe UI', 10), bg='#f5f6f7', relief=tk.FLAT, bd=0)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)
        
        select_btn = tk.Button(path_row, text="📂 Select File", 
                  command=self._select_and_load_file,
                  font=('Segoe UI', 10),
                  bg='#3498db', fg='white',
                  relief=tk.FLAT, bd=0,
                  padx=20, pady=8,
                  cursor='hand2')
        select_btn.pack(side=tk.LEFT)
        
        tk.Label(
            self.file_section_content, 
            text="Auto-loads: columns from row 3, data from row 5 onwards", 
            fg='#95a5a6', bg='white', font=('Segoe UI', 9, 'italic')
        ).pack(anchor='w', pady=(5, 0))
    
    def _toggle_file_section(self):
        """Toggle visibility of file selector content"""
        is_expanded = self.file_section_expanded.get()
        
        if is_expanded:
            # Collapse
            self.file_section_content.pack_forget()
            self.expand_indicator.config(text="►")
            self.file_section_expanded.set(False)
        else:
            # Expand
            self.file_section_content.pack(fill=tk.X, padx=20, pady=(0, 16), after=self.expand_indicator.master.master)
            self.expand_indicator.config(text="▼")
            self.file_section_expanded.set(True)
    
    def _toggle_chart_options(self):
        """Toggle visibility of chart options content"""
        is_expanded = self.chart_options_expanded.get()
        
        if is_expanded:
            # Collapse
            self.chart_options_content.pack_forget()
            self.chart_expand_indicator.config(text="►")
            self.chart_options_expanded.set(False)
        else:
            # Expand
            self.chart_options_content.pack(fill=tk.X, padx=20, pady=(0, 16), after=self.chart_expand_indicator.master.master)
            self.chart_expand_indicator.config(text="▼")
            self.chart_options_expanded.set(True)
    
    def _create_controls(self):
        """Create modern collapsible chart control panel"""
        # Clear existing controls
        for widget in self.control_container.winfo_children():
            widget.destroy()
        
        control_frame = tk.Frame(self.control_container, bg='white', relief=tk.FLAT, bd=1, highlightbackground='#d0d5dd', highlightthickness=1)
        control_frame.pack(fill=tk.BOTH, expand=True, padx=0)
        
        # Collapsible header
        header_frame = tk.Frame(control_frame, bg='white', cursor='hand2')
        header_frame.pack(fill=tk.X, padx=20, pady=16)
        header_frame.bind('<Button-1>', lambda e: self._toggle_chart_options())
        
        # Icon and title row
        icon_title_row = tk.Frame(header_frame, bg='white')
        icon_title_row.pack(fill=tk.X)
        
        # Expand/collapse indicator
        self.chart_expand_indicator = tk.Label(
            icon_title_row, 
            text="▼", 
            font=('Segoe UI', 10), 
            bg='white', 
            fg='#27ae60',
            cursor='hand2'
        )
        self.chart_expand_indicator.pack(side=tk.LEFT, padx=(0, 8))
        self.chart_expand_indicator.bind('<Button-1>', lambda e: self._toggle_chart_options())
        
        title_label = tk.Label(
            icon_title_row, 
            text="📈 Chart Options", 
            font=('Segoe UI', 12, 'bold'), 
            bg='white', 
            fg='#2c3e50',
            cursor='hand2'
        )
        title_label.pack(side=tk.LEFT)
        title_label.bind('<Button-1>', lambda e: self._toggle_chart_options())
        
        # Hint label
        hint_label = tk.Label(
            icon_title_row,
            text="(click to collapse and save space)",
            font=('Segoe UI', 8),
            bg='white',
            fg='#95a5a6',
            cursor='hand2'
        )
        hint_label.pack(side=tk.LEFT, padx=(8, 0))
        hint_label.bind('<Button-1>', lambda e: self._toggle_chart_options())
        
        # Collapsible content
        self.chart_options_content = tk.Frame(control_frame, bg='white')
        self.chart_options_content.pack(fill=tk.X, padx=20, pady=(0, 16))
        
        # Use chart_options_content as the inner frame for controls
        inner = self.chart_options_content
        
        # Use inner frame as control_frame for remaining code
        control_frame = inner
        
        # Row 1: Chart type and source selection
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="Chart Type:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        chart_types = ["Line Chart", "Bar Chart", "Area Chart"]
        ttk.Combobox(row1, textvariable=self.chart_type, values=chart_types, 
                    state='readonly', width=15).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row1, text="Water Source:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        source_options = ["All Sources"] + self.available_sources
        self.source_combo = ttk.Combobox(row1, textvariable=self.selected_source, 
                                        values=source_options, state='readonly', width=40)
        self.source_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Row 2: Date range selection (Year/Month filters)
        row2 = ttk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row2, text="Date Range:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row2, text="From:", width=6).pack(side=tk.LEFT, padx=(0, 3))
        
        # Start year
        ttk.Label(row2, text="Year:", width=5).pack(side=tk.LEFT, padx=(0, 2))
        years = [""] + sorted([str(y) for y in range(self.min_date.year, self.max_date.year + 1)])
        ttk.Combobox(row2, textvariable=self.start_year, values=years, 
                    state='readonly', width=6).pack(side=tk.LEFT, padx=(0, 10))
        
        # Start month
        ttk.Label(row2, text="Month:", width=6).pack(side=tk.LEFT, padx=(0, 2))
        months = [""] + [f"{m:02d}" for m in range(1, 13)]
        ttk.Combobox(row2, textvariable=self.start_month, values=months, 
                    state='readonly', width=6).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row2, text="To:", width=4).pack(side=tk.LEFT, padx=(0, 3))
        
        # End year
        ttk.Label(row2, text="Year:", width=5).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Combobox(row2, textvariable=self.end_year, values=years, 
                    state='readonly', width=6).pack(side=tk.LEFT, padx=(0, 10))
        
        # End month
        ttk.Label(row2, text="Month:", width=6).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Combobox(row2, textvariable=self.end_month, values=months, 
                    state='readonly', width=6).pack(side=tk.LEFT)
        
        # Row 3: Actions
        row3 = tk.Frame(control_frame, bg='white')
        row3.pack(fill=tk.X, pady=(10, 0))
        
        gen_btn = tk.Button(row3, text="📈 Generate Chart", command=self._generate_chart, 
                  font=('Segoe UI', 10, 'bold'),
                  bg='#27ae60', fg='white',
                  relief=tk.FLAT, bd=0,
                  padx=20, pady=8,
                  cursor='hand2')
        gen_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = tk.Button(row3, text="💾 Save Chart", 
                  command=self._save_chart,
                  font=('Segoe UI', 10),
                  bg='#3498db', fg='white',
                  relief=tk.FLAT, bd=0,
                  padx=20, pady=8,
                  cursor='hand2')
        save_btn.pack(side=tk.LEFT)
    
    def _get_y_axis_label(self, source_name):
        """Detect y-axis label based on source column name"""
        source_lower = source_name.lower()
        
        if 'ton' in source_lower or 'tonne' in source_lower:
            return 'Volume (Tonnes)'
        elif 'm/t' in source_lower or 'mega' in source_lower:
            return 'Volume (ML)'
        elif '%' in source_lower or 'percent' in source_lower or 'recycl' in source_lower:
            return 'Percentage (%)'
        elif 'dispatch' in source_lower or 'count' in source_lower:
            return 'Count'
        elif 'moisture' in source_lower or 'wet' in source_lower:
            return 'Moisture Content (%)'
        else:
            return 'Volume (m³)'
    
    def _get_default_y_label(self):
        """Get default y-axis label for multi-source charts"""
        return 'Value'
    
    def _select_and_load_file(self):
        """Select Excel file and auto-load water source data"""
        file_path = filedialog.askopenfilename(
            title="Select Water Balance Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self.excel_file_path.set(file_path)
        self._load_water_source_data(file_path)
    
    def _load_water_source_data(self, file_path):
        """Load and parse water source data from Excel Meter Readings sheet"""
        try:
            # Read Excel with header at row 3 (index 2), data starts at row 5
            df = pd.read_excel(file_path, sheet_name='Meter Readings', header=2, engine='openpyxl')

            # Normalize column names (trim spaces) so duplicates are detected correctly
            df.columns = [str(col).strip() for col in df.columns]

            # Drop duplicate column names while keeping the first occurrence to avoid pandas
            # duplicate-key errors during selection
            duplicate_mask = df.columns.duplicated()
            if duplicate_mask.any():
                dropped_cols = df.columns[duplicate_mask].tolist()
                logger.warning(f"Dropping duplicate columns from Excel: {dropped_cols}")
                df = df.loc[:, ~duplicate_mask]

            # First column should be Date
            date_col = df.columns[0]
            df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=['Date'])

            # Collect usable numeric source columns, skipping duplicates and non-numeric data
            source_columns = []
            seen_sources = set()
            skipped_sources = []
            
            for col in df.columns[1:]:
                # Skip renamed duplicates (pandas renames to FlowA.1, FlowA.2, etc.) and other unwanted columns
                if (col == date_col or col == 'Date' or col.startswith('Unnamed') or 
                    col in seen_sources or '.' in col):
                    continue
                try:
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    non_null_count = numeric_series.dropna().shape[0]
                    
                    # Skip columns with no numeric data at all
                    if non_null_count == 0:
                        skipped_sources.append((col, "no numeric data"))
                        continue
                    
                    # Warn if column has sparse data but include it anyway
                    # (user may want to plot data that starts at different dates)
                    if non_null_count < len(df) * 0.1:  # Less than 10% data
                        logger.warning(f"Source '{col}' has sparse data ({non_null_count}/{len(df)} rows)")
                    
                    source_columns.append(col)
                    seen_sources.add(col)
                    
                except Exception as e:
                    skipped_sources.append((col, str(e)))
                    continue

            self.source_data = df[['Date'] + source_columns].copy()
            self.available_sources = source_columns
            
            # Store date range for validation
            self.min_date = self.source_data['Date'].min()
            self.max_date = self.source_data['Date'].max()
            
            # Log summary
            logger.info(f"Loaded {len(df)} records with {len(source_columns)} water sources from Excel")
            logger.info(f"Date range: {self.min_date.date()} to {self.max_date.date()}")
            if skipped_sources:
                skipped_list = "; ".join([f"{col} ({reason})" for col, reason in skipped_sources[:5]])
                logger.info(f"Skipped {len(skipped_sources)} columns: {skipped_list}" + 
                           (f" ... and {len(skipped_sources)-5} more" if len(skipped_sources) > 5 else ""))
            
            # Create controls now that data is loaded
            self.control_container.after(10, self._create_controls)
            
            # Update status indicator and auto-collapse file section
            source_count = len(source_columns)
            record_count = len(df)
            self.file_status_label.config(
                text=f"✓ {record_count} records, {source_count} sources loaded"
            )
            
            # Auto-collapse to save space after successful load
            if self.file_section_expanded.get():
                self.file_section_content.after(500, self._toggle_file_section)
            
            # Show success message
            messagebox.showinfo("Data Loaded", 
                              f"✓ Loaded {len(df)} records\n✓ Found {len(source_columns)} water sources\n\n" +
                              "Select options and click 'Generate Chart'")
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            messagebox.showerror("Load Error", f"Failed to load Excel file:\n{str(e)}")
    
    def _create_chart_area(self):
        """Create chart display area"""
        # Use the outer container frame
        chart_frame = tk.Frame(self.main_frame, bg='white', relief=tk.FLAT, bd=1, highlightbackground='#d0d5dd', highlightthickness=1)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create matplotlib figure with professional settings - wider to accommodate external legend
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _show_placeholder(self):
        """Show placeholder message when no chart is loaded"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 
                '📊\n\nSelect Excel file above to load water source data\n' +
                'then choose options and click "Generate Chart"',
                ha='center', va='center', fontsize=13, color='#666',
                bbox=dict(boxstyle='round,pad=1.2', facecolor='#f5f6f7', 
                         edgecolor='#dee2e6', linewidth=2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
    
    
    def _generate_chart(self):
        """Generate professional water source trend chart"""
        if self.source_data is None or self.source_data.empty:
            messagebox.showwarning("No Data", "Please load an Excel file first")
            return
        
        try:
            # Parse and validate date range (year/month only)
            data_to_plot = self.source_data.copy()
            
            start_year_str = self.start_year.get().strip()
            start_month_str = self.start_month.get().strip()
            end_year_str = self.end_year.get().strip()
            end_month_str = self.end_month.get().strip()
            
            # Apply start date filter (only if year is selected)
            if start_year_str:
                try:
                    start_year = int(start_year_str)
                    start_month = int(start_month_str) if start_month_str else 1
                    start_date = pd.to_datetime(f"{start_year}-{start_month:02d}-01")
                    data_to_plot = data_to_plot[data_to_plot['Date'] >= start_date]
                    logger.info(f"Applied start date filter: {start_date.date()}")
                except Exception as e:
                    logger.error(f"Error parsing start date: {e}")
                    messagebox.showerror("Date Error", f"Invalid start date: {e}")
                    return
            
            # Apply end date filter (only if year is selected)
            if end_year_str:
                try:
                    end_year = int(end_year_str)
                    end_month = int(end_month_str) if end_month_str else 12
                    # Get last day of the end month
                    if end_month == 12:
                        end_date = pd.to_datetime(f"{end_year + 1}-01-01") - pd.Timedelta(days=1)
                    else:
                        end_date = pd.to_datetime(f"{end_year}-{end_month + 1:02d}-01") - pd.Timedelta(days=1)
                    data_to_plot = data_to_plot[data_to_plot['Date'] <= end_date]
                    logger.info(f"Applied end date filter: {end_date.date()}")
                except Exception as e:
                    logger.error(f"Error parsing end date: {e}")
                    messagebox.showerror("Date Error", f"Invalid end date: {e}")
                    return
            
            logger.info(f"Data after date filtering: {len(data_to_plot)} rows (from {len(self.source_data)} total)")
            
            if data_to_plot.empty:
                messagebox.showwarning("No Data in Range", "No data found for the specified date range.")
                return
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            selected = self.selected_source.get()
            chart_type = self.chart_type.get()
            
            # Determine which sources to plot
            if selected == "All Sources":
                sources_to_plot = self.available_sources[:10]  # Limit to 10 for readability
                if len(self.available_sources) > 10:
                    messagebox.showinfo("Info", f"Showing first 10 of {len(self.available_sources)} sources for readability")
            else:
                sources_to_plot = [selected]
            
            # Professional color palette
            colors = plt.cm.tab10(np.linspace(0, 1, len(sources_to_plot)))
            
            for idx, source in enumerate(sources_to_plot):
                try:
                    # Get the source column
                    if source not in data_to_plot.columns:
                        logger.warning(f"Source '{source}' not found in data; skipping")
                        continue
                    
                    data = data_to_plot[['Date', source]].copy()
                    col_data = data[source]
                    
                    # If duplicate column names exist, pandas returns a DataFrame; use the first column
                    if isinstance(col_data, pd.DataFrame):
                        col_data = col_data.iloc[:, 0]
                    
                    # Convert to numeric, handling any remaining type issues
                    col_data = pd.to_numeric(col_data, errors='coerce')
                    data[source] = col_data
                    
                    # Drop rows with missing dates or values
                    data = data.dropna(subset=['Date', source])
                    
                    # Skip source if no valid data points remain
                    if data.empty or len(data) < 2:
                        logger.warning(f"Source '{source}' has insufficient data points after filtering; skipping")
                        continue
                    
                    dates = pd.to_datetime(data['Date']).tolist()
                    values = data[source].tolist()
                    color = colors[idx % len(colors)]  # Wrap color index if we have extra sources
                    
                    if chart_type == "Line Chart":
                        ax.plot(dates, values, label=source, color=color, linewidth=2.5, 
                               marker='o', markersize=4, alpha=0.85)
                    
                    elif chart_type == "Bar Chart":
                        width = 20 if len(sources_to_plot) == 1 else 15 / len(sources_to_plot)
                        offset = (idx - len(sources_to_plot)/2) * width
                        positions = [d + pd.Timedelta(days=offset) for d in dates]
                        ax.bar(positions, values, width=width, label=source, color=color, 
                              alpha=0.75, edgecolor='white', linewidth=1)
                    
                    elif chart_type == "Area Chart":
                        ax.fill_between(dates, values, alpha=0.4, color=color, label=source)
                        ax.plot(dates, values, color=color, linewidth=2, alpha=0.9)
                
                except Exception as e:
                    logger.error(f"Error plotting source '{source}': {e}")
                    continue
            
            # Professional styling
            if selected == "All Sources":
                title = "Water Source Trends (Multiple Sources)"
                y_label = self._get_default_y_label()
            else:
                title = f"Water Source Trends - {selected}"
                y_label = self._get_y_axis_label(selected)
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
            
            # Position legend outside plot area to avoid overlapping data
            # Place to the right of the plot with smaller font
            ax.legend(
                loc='center left', 
                bbox_to_anchor=(1.02, 0.5),  # Position outside plot area
                framealpha=0.95, 
                fontsize=9, 
                shadow=True,
                ncol=1,  # Single column for cleaner look
                borderpad=1,
                labelspacing=0.8
            )
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Adjust layout to prevent legend cutoff
            self.figure.tight_layout(rect=[0, 0, 0.85, 1])  # Leave 15% on right for legend
            self.canvas.draw()
            
            logger.info(f"Chart generated: {chart_type} for {selected}")
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            messagebox.showerror("Chart Error", f"Failed to generate chart:\n{str(e)}")
    
    def _save_chart(self):
        """Save current chart to file with proper aspect ratio"""
        if self.source_data is None:
            messagebox.showwarning("No Chart", "Generate a chart first")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = self.selected_source.get().replace(" ", "_").replace(":", "")
            default_name = f"water_source_{source}_{timestamp}"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("PDF Document", "*.pdf"),
                    ("SVG Vector", "*.svg")
                ],
                title="Save Chart As"
            )
            
            if file_path:
                # Save with high DPI and proper bounding to prevent stretching
                # Use bbox_inches='tight' to include legend without distortion
                self.figure.savefig(
                    file_path, 
                    dpi=300,  # High quality for reports
                    bbox_inches='tight',  # Auto-crop to content
                    facecolor='white', 
                    edgecolor='none',
                    pad_inches=0.3  # Small padding around edges
                )
                messagebox.showinfo("Success", f"Chart saved to:\n{file_path}")
                logger.info(f"Chart saved: {file_path}")
                
        except Exception as e:
            logger.error(f"Error saving chart: {e}")
            messagebox.showerror("Save Error", f"Failed to save chart:\n{str(e)}")

