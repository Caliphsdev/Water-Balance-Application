"""
Professional Charts Dashboard
Time series analysis, trends, moving averages, and comparative statistics
with downloadable charts and on-demand loading
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.excel_timeseries_extended import ExcelTimeSeriesExtended
from utils.app_logger import logger
from utils.config_manager import config

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ChartsDashboard:
    """Professional charts dashboard with time series analysis"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.excel = ExcelTimeSeriesExtended()
        self.main_frame = None
        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.current_data = None  # Cache for download
        
    def load(self):
        """Load the charts dashboard"""
        if self.main_frame:
            self.main_frame.destroy()
        
        self.main_frame = tk.Frame(self.parent, bg=config.get_color('bg_main'))
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._create_header()
        
        # Controls
        self._create_controls()
        
        # Chart area (lazy loaded)
        self._create_chart_area()
        
        logger.info("Charts dashboard loaded (charts render on-demand)")
    
    def _create_header(self):
        """Create header section"""
        header_frame = tk.Frame(self.main_frame, bg=config.get_color('bg_main'))
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(
            header_frame,
            text="📈 Water Balance Charts & Analytics",
            font=('Segoe UI', 18, 'bold'),
            fg=config.get_color('primary'),
            bg=config.get_color('bg_main')
        )
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(
            header_frame,
            text="Professional time series analysis with trends and statistics",
            font=('Segoe UI', 10),
            fg='#666',
            bg=config.get_color('bg_main')
        )
        subtitle.pack(side=tk.LEFT, padx=(15, 0))
    
    def _create_controls(self):
        """Create control panel"""
        control_frame = tk.Frame(self.main_frame, bg='white', relief='solid', borderwidth=1)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        inner = tk.Frame(control_frame, bg='white')
        inner.pack(fill=tk.BOTH, padx=15, pady=15)
        
        # Row 1: Chart style and time range
        row1 = tk.Frame(inner, bg='white')
        row1.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(row1, text="Chart Style:", font=('Segoe UI', 10, 'bold'), 
                bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=(0, 5))
        
        self.style_var = tk.StringVar(value="Line Trend")
        styles = ["Line Trend", "Bar Chart"]
        
        style_combo = ttk.Combobox(row1, textvariable=self.style_var,
                                   values=styles, state='readonly', width=15)
        style_combo.pack(side=tk.LEFT, padx=(0, 25))
        
        tk.Label(row1, text="Time Period:", font=('Segoe UI', 10, 'bold'),
                bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=(0, 5))
        
        self.period_var = tk.StringVar(value="Last 6 Months")
        periods = ["Last Month", "Last 3 Months", "Last 6 Months", 
                  "Last Year", "Last 2 Years", "All Available"]
        
        period_combo = ttk.Combobox(row1, textvariable=self.period_var,
                                    values=periods, state='readonly', width=18)
        period_combo.pack(side=tk.LEFT)
        
        # Row 2: Data source filter
        row2 = tk.Frame(inner, bg='white')
        row2.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(row2, text="Data Source:", font=('Segoe UI', 10, 'bold'),
                bg='white', width=12, anchor='w').pack(side=tk.LEFT, padx=(0, 5))
        
        self.source_var = tk.StringVar(value="All Sources")
        
        # Build source options with codes
        sources = self.db.get_water_sources(active_only=True)
        
        source_options = ["All Sources"] + \
                        [f"{s['source_code']}: {s['source_name']}" for s in sources[:15]]
        
        source_combo = ttk.Combobox(row2, textvariable=self.source_var,
                                    values=source_options, state='readonly', width=45)
        source_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # Row 3: Action buttons
        row3 = tk.Frame(inner, bg='white')
        row3.pack(fill=tk.X)
        
        generate_btn = tk.Button(
            row3, text="📊 Generate Chart", command=self._generate_chart,
            font=('Segoe UI', 10, 'bold'), bg=config.get_color('primary'),
            fg='white', padx=20, pady=8, relief='flat', cursor='hand2'
        )
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        download_btn = tk.Button(
            row3, text="💾 Download PNG", command=self._download_chart,
            font=('Segoe UI', 10), bg='#28a745', fg='white',
            padx=15, pady=8, relief='flat', cursor='hand2'
        )
        download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        export_csv_btn = tk.Button(
            row3, text="📄 Export Data (CSV)", command=self._export_data_csv,
            font=('Segoe UI', 10), bg='#17a2b8', fg='white',
            padx=15, pady=8, relief='flat', cursor='hand2'
        )
        export_csv_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(
            row3, text="🗑 Clear", command=self._clear_chart,
            font=('Segoe UI', 10), bg='#6c757d', fg='white',
            padx=15, pady=8, relief='flat', cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = tk.Label(
            row3, text="Ready. Select options and click Generate Chart.",
            font=('Segoe UI', 9, 'italic'), fg='#666', bg='white'
        )
        self.status_label.pack(side=tk.RIGHT, padx=15)
    
    def _create_chart_area(self):
        """Create chart display area (empty until generated)"""
        self.chart_container = tk.Frame(self.main_frame, bg='white', 
                                        relief='solid', borderwidth=1)
        self.chart_container.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder
        placeholder = tk.Label(
            self.chart_container,
            text="📊\n\nSelect chart options above and click 'Generate Chart'\nto view professional time series analysis",
            font=('Segoe UI', 14),
            fg='#999',
            bg='white',
            justify='center'
        )
        placeholder.pack(expand=True)
    
    def _generate_chart(self):
        """Generate chart on-demand (lazy loading)"""
        try:
            self.status_label.config(text="⏳ Generating chart...", fg='#ff9800')
            self.parent.update()
            
            period = self.period_var.get()
            source = self.source_var.get()
            
            # Clear existing chart
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            
            if not MATPLOTLIB_AVAILABLE:
                messagebox.showerror("Error", "Matplotlib not available")
                return
            
            # Create matplotlib figure
            self.figure = Figure(figsize=(14, 7), dpi=100, facecolor='white')
            
            # Always plot water source trends
            self._plot_source_trends(period, source)
            
            # Embed chart
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_container)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add toolbar
            toolbar_frame = tk.Frame(self.chart_container, bg='white')
            toolbar_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()
            
            chart_style = self.style_var.get()
            self.status_label.config(text=f"✅ Chart generated: {chart_style}", fg='#28a745')
            logger.info(f"Chart generated: Water Source Trends ({chart_style})")
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            self.status_label.config(text=f"❌ Error: {str(e)[:50]}", fg='#dc3545')
            messagebox.showerror("Chart Error", f"Failed to generate chart:\n{str(e)}")
    
    def _get_date_range(self, period: str) -> Tuple[date, date]:
        """Calculate start and end dates"""
        end_date = date.today()
        
        if period == "Last Month":
            start_date = end_date - relativedelta(months=1)
        elif period == "Last 3 Months":
            start_date = end_date - relativedelta(months=3)
        elif period == "Last 6 Months":
            start_date = end_date - relativedelta(months=6)
        elif period == "Last Year":
            start_date = end_date - relativedelta(years=1)
        elif period == "Last 2 Years":
            start_date = end_date - relativedelta(years=2)
        else:  # All Available
            start_date = date(2020, 1, 1)
        
        return start_date, end_date
    
    def _plot_source_trends(self, period: str, source_filter: str):
        """Plot water source volume trends with real measurement data from Excel"""
        ax = self.figure.add_subplot(111)
        start_date, end_date = self._get_date_range(period)
        
        # Get chart style
        try:
            chart_style = self.style_var.get()
        except:
            chart_style = "Line Trend"
        
        sources = self.db.get_water_sources(active_only=True)
        
        # Filter if specific source selected (format: "CODE: Name")
        if source_filter != "All Sources" and ":" in source_filter:
            source_code = source_filter.split(":")[0].strip()
            sources = [s for s in sources if s['source_code'] == source_code]
        
        # Limit to top 5 sources for readability
        sources = sources[:5]
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        self.current_data = {'dates': [], 'sources': {}}
        
        # Read data from Excel file using configurable path
        import pandas as pd
        from pathlib import Path
        from utils.config_manager import ConfigManager
        
        config = ConfigManager()
        excel_path_str = config.get('data_sources.legacy_excel_path', 'data/New Water Balance  20250930 Oct.xlsx')
        base_dir = Path(__file__).parent.parent.parent
        excel_path = base_dir / excel_path_str if not Path(excel_path_str).is_absolute() else Path(excel_path_str)
        
        if not excel_path.exists():
            messagebox.showwarning("No Data", 
                                 f"TRP Excel file not found:\n{excel_path}\n\n"
                                 "Configure the correct path in Settings > Data Sources tab.")
            return
        
        try:
            # Read Meter Readings sheet with proper headers (skip first 2 rows)
            df = pd.read_excel(excel_path, sheet_name='Meter Readings', engine='openpyxl', header=2)
            
            # Convert first column to dates
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df = df.dropna(subset=['Date'])
            
            # Filter by date range
            df = df[(df['Date'] >= pd.Timestamp(start_date)) & (df['Date'] <= pd.Timestamp(end_date))]
            
        except Exception as e:
            logger.error(f"Error reading Excel: {e}")
            messagebox.showerror("Excel Error", f"Failed to read Excel file:\n{str(e)}")
            return
        
        for idx, source in enumerate(sources):
            source_code = source['source_code']
            source_name = source['source_name']
            
            # Check if this source code exists as a column in the Excel
            # Try exact match first, then with common suffixes
            excel_col = None
            if source_code in df.columns:
                excel_col = source_code
            elif f"{source_code} River" in df.columns:
                excel_col = f"{source_code} River"
            elif source_code.replace(" ", "") in [col.replace(" ", "") for col in df.columns]:
                # Try matching without spaces
                for col in df.columns:
                    if col.replace(" ", "") == source_code.replace(" ", ""):
                        excel_col = col
                        break
            
            if excel_col is None:
                continue
            
            # Get data for this source
            source_data = df[['Date', excel_col]].dropna()
            
            if source_data.empty:
                continue
            
            dates = [d.date() for d in source_data['Date']]
            volumes = source_data[excel_col].astype(float).tolist()
            
            if dates:
                color = colors[idx % len(colors)]
                
                if chart_style == "Bar Chart":
                    # Bar chart with offset for multiple sources
                    width = 15 / max(len(sources), 1)  # Bar width in days
                    offset = (idx - len(sources)/2) * width
                    positions = [mdates.date2num(d) + offset for d in dates]
                    ax.bar(positions, volumes, width=width, 
                          label=f"{source_code}: {source_name}",
                          color=color, alpha=0.8, edgecolor='white', linewidth=0.5)
                else:
                    # Line trend
                    ax.plot(dates, volumes, label=f"{source_code}: {source_name}", 
                           color=color, marker='o', 
                           markersize=5, linewidth=2.5, alpha=0.85)
                
                # Store data for export
                if not self.current_data['dates']:
                    self.current_data['dates'] = dates
                self.current_data['sources'][f"{source_code}: {source_name}"] = volumes
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Volume (m³)', fontsize=12, fontweight='bold')
        title = f'Water Source Volume Trends ({chart_style})'
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.95, fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format x-axis dates
        if chart_style == "Bar Chart":
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        self.figure.autofmt_xdate()
        self.figure.tight_layout()
    
    def _plot_storage_trends(self, period: str, source_filter: str):
        """Plot storage facility volume trends"""
        ax = self.figure.add_subplot(111)
        start_date, end_date = self._get_date_range(period)
        
        facilities = self.db.get_storage_facilities(active_only=True)
        
        # Filter if specific facility selected
        if source_filter.startswith("Facility:"):
            facility_name = source_filter.replace("Facility:", "").strip()
            facilities = [f for f in facilities if f['facility_name'] == facility_name]
        
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
        self.current_data = {'dates': [], 'facilities': {}}
        
        for idx, facility in enumerate(facilities[:5]):
            code = facility['facility_code']
            name = facility['facility_name']
            capacity = facility.get('total_capacity', 0)
            surface_area = facility.get('surface_area', 0)
            
            dates = []
            volumes = []
            
            # Collect monthly data
            current = start_date.replace(day=1)
            while current <= end_date:
                try:
                    data = self.excel.get_storage_data(code, current, capacity, surface_area, self.db)
                    if data:
                        dates.append(current)
                        volumes.append(data.get('closing_volume', 0) / 1000)  # Convert to thousands
                except Exception:
                    pass
                
                current += relativedelta(months=1)
            
            if dates:
                ax.plot(dates, volumes, label=f"{name} ({capacity/1000:.0f}k m³ capacity)",
                       color=colors[idx % len(colors)], marker='s',
                       markersize=6, linewidth=2.5, alpha=0.85)
                
                # Store data
                self.current_data['dates'] = dates
                self.current_data['facilities'][name] = volumes
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Volume (thousands m³)', fontsize=12, fontweight='bold')
        ax.set_title('Storage Facility Volume Trends', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.95, fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        self.figure.autofmt_xdate()
        self.figure.tight_layout()
    
    def _plot_flow_analysis(self, period: str, source_filter: str):
        """Plot inflow vs outflow with bar charts"""
        ax = self.figure.add_subplot(111)
        start_date, end_date = self._get_date_range(period)
        
        facilities = self.db.get_storage_facilities(active_only=True)
        
        dates = []
        inflows = []
        outflows = []
        net_flow = []
        
        # Aggregate monthly flows
        current = start_date.replace(day=1)
        while current <= end_date:
            monthly_inflow = 0
            monthly_outflow = 0
            
            for facility in facilities:
                code = facility['facility_code']
                capacity = facility.get('total_capacity', 0)
                surface_area = facility.get('surface_area', 0)
                
                try:
                    data = self.excel.get_storage_data(code, current, capacity, surface_area, self.db)
                    if data:
                        monthly_inflow += data.get('inflow_total', 0)
                        monthly_outflow += data.get('outflow_total', 0)
                except Exception:
                    pass
            
            if monthly_inflow > 0 or monthly_outflow > 0:
                dates.append(current)
                inflows.append(monthly_inflow / 1000)
                outflows.append(monthly_outflow / 1000)
                net_flow.append((monthly_inflow - monthly_outflow) / 1000)
            
            current += relativedelta(months=1)
        
        if dates:
            x = np.arange(len(dates))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, inflows, width, label='Total Inflow',
                          color='#2ecc71', alpha=0.8, edgecolor='white')
            bars2 = ax.bar(x + width/2, outflows, width, label='Total Outflow',
                          color='#e74c3c', alpha=0.8, edgecolor='white')
            
            # Net flow line
            ax2 = ax.twinx()
            line = ax2.plot(x, net_flow, label='Net Flow', color='#3498db',
                           marker='D', linewidth=2.5, markersize=6)
            ax2.set_ylabel('Net Flow (thousands m³)', fontsize=11, fontweight='bold')
            ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            
            # Store data
            self.current_data = {
                'dates': dates,
                'inflows': inflows,
                'outflows': outflows,
                'net_flow': net_flow
            }
        
        # Formatting
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel('Volume (thousands m³)', fontsize=12, fontweight='bold')
        ax.set_title('Inflow vs Outflow Analysis', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([d.strftime('%b %y') for d in dates], rotation=45, ha='right')
        
        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='best', framealpha=0.95)
        
        ax.grid(True, alpha=0.3, axis='y')
        self.figure.tight_layout()
    
    def _plot_moving_average(self, period: str, source_filter: str):
        """Plot with 30-day moving average"""
        ax = self.figure.add_subplot(111)
        start_date, end_date = self._get_date_range(period)
        
        # Example: plot storage with moving average
        facilities = self.db.get_storage_facilities(active_only=True)[:3]
        
        for facility in facilities:
            code = facility['facility_code']
            name = facility['facility_name']
            capacity = facility.get('total_capacity', 0)
            surface_area = facility.get('surface_area', 0)
            
            dates = []
            volumes = []
            
            current = start_date.replace(day=1)
            while current <= end_date:
                try:
                    data = self.excel.get_storage_data(code, current, capacity, surface_area, self.db)
                    if data:
                        dates.append(current)
                        volumes.append(data.get('closing_volume', 0) / 1000)
                except Exception:
                    pass
                current += relativedelta(months=1)
            
            if len(dates) >= 3:
                # Plot original
                ax.plot(dates, volumes, label=f"{name} (actual)", 
                       alpha=0.4, linewidth=1, marker='o', markersize=3)
                
                # Calculate and plot moving average (3-month)
                window = 3
                ma = np.convolve(volumes, np.ones(window)/window, mode='valid')
                ma_dates = dates[window-1:]
                ax.plot(ma_dates, ma, label=f"{name} (MA)", 
                       linewidth=2.5, marker='s', markersize=5)
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Volume (thousands m³)', fontsize=12, fontweight='bold')
        ax.set_title('Storage Trends with Moving Average (3-month)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.95, fontsize=9)
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _plot_source_comparison(self, period: str):
        """Compare multiple sources side by side with real data"""
        start_date, end_date = self._get_date_range(period)
        
        sources = self.db.get_water_sources(active_only=True)[:6]
        
        # Fetch all measurements
        measurements = self.db.get_measurements(
            start_date, end_date,
            measurement_type='source_flow'
        )
        
        # Create subplots for comparison
        n_sources = len(sources)
        rows = (n_sources + 1) // 2
        
        for idx, source in enumerate(sources, 1):
            ax = self.figure.add_subplot(rows, 2, idx)
            source_id = source['source_id']
            source_code = source['source_code']
            source_name = source['source_name']
            
            # Filter measurements for this source
            source_measurements = [
                m for m in measurements
                if m.get('source_id') == source_id
            ]
            
            # Organize by date
            date_volume_map = {}
            for m in source_measurements:
                mdate = m['measurement_date']
                if isinstance(mdate, str):
                    mdate = datetime.strptime(mdate, '%Y-%m-%d').date()
                volume = m.get('measured_value', 0) or 0
                
                if mdate in date_volume_map:
                    date_volume_map[mdate] += volume
                else:
                    date_volume_map[mdate] = volume
            
            if date_volume_map:
                sorted_dates = sorted(date_volume_map.keys())
                dates = sorted_dates
                volumes = [date_volume_map[d] for d in sorted_dates]
                
                ax.plot(dates, volumes, color='#3498db', linewidth=2, marker='o', markersize=4)
                ax.fill_between(dates, volumes, alpha=0.2, color='#3498db')
                
                # Stats
                avg = np.mean(volumes)
                ax.axhline(y=avg, color='red', linestyle='--', linewidth=1, alpha=0.7, label=f'Avg: {avg:.0f} m³')
            else:
                # No data available
                ax.text(0.5, 0.5, 'No data available', 
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=10, color='#999')
            
            ax.set_title(f"{source_name}\n({source_code})", fontsize=9, fontweight='bold')
            ax.set_ylabel('Volume (m³)', fontsize=8)
            ax.grid(True, alpha=0.2)
            if date_volume_map:
                ax.legend(fontsize=7, loc='best')
            
            if idx > n_sources - 2:
                ax.set_xlabel('Date', fontsize=8)
        
        self.figure.suptitle('Water Source Comparison', fontsize=14, fontweight='bold')
        self.figure.tight_layout(rect=[0, 0, 1, 0.96])
    
    def _plot_statistical_summary(self, period: str, source_filter: str):
        """Statistical summary with box plots and distribution"""
        start_date, end_date = self._get_date_range(period)
        
        facilities = self.db.get_storage_facilities(active_only=True)[:5]
        
        data_for_box = []
        labels = []
        stats_text = []
        
        for facility in facilities:
            code = facility['facility_code']
            name = facility['facility_name'][:15]  # Truncate long names
            capacity = facility.get('total_capacity', 0)
            surface_area = facility.get('surface_area', 0)
            
            volumes = []
            current = start_date.replace(day=1)
            while current <= end_date:
                try:
                    data = self.excel.get_storage_data(code, current, capacity, surface_area, self.db)
                    if data:
                        volumes.append(data.get('closing_volume', 0) / 1000)
                except Exception:
                    pass
                current += relativedelta(months=1)
            
            if volumes:
                data_for_box.append(volumes)
                labels.append(name)
                
                # Calculate statistics
                mean_vol = np.mean(volumes)
                std_vol = np.std(volumes)
                min_vol = np.min(volumes)
                max_vol = np.max(volumes)
                stats_text.append(f"{name}:\nμ={mean_vol:.1f} σ={std_vol:.1f}\nMin={min_vol:.1f} Max={max_vol:.1f}")
        
        if data_for_box:
            ax = self.figure.add_subplot(121)
            bp = ax.boxplot(data_for_box, labels=labels, patch_artist=True,
                           notch=True, showmeans=True)
            
            # Color boxes
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.set_ylabel('Volume (thousands m³)', fontsize=11, fontweight='bold')
            ax.set_title('Statistical Distribution', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Stats table
            ax2 = self.figure.add_subplot(122)
            ax2.axis('off')
            stats_combined = '\n\n'.join(stats_text)
            ax2.text(0.1, 0.5, stats_combined, fontsize=9, family='monospace',
                    verticalalignment='center')
            ax2.set_title('Summary Statistics', fontsize=12, fontweight='bold')
        
        self.figure.tight_layout()
    
    def _plot_cumulative_analysis(self, period: str, source_filter: str):
        """Cumulative inflow/outflow over time"""
        ax = self.figure.add_subplot(111)
        start_date, end_date = self._get_date_range(period)
        
        facilities = self.db.get_storage_facilities(active_only=True)
        
        dates = []
        cumulative_inflow = []
        cumulative_outflow = []
        
        total_in = 0
        total_out = 0
        
        current = start_date.replace(day=1)
        while current <= end_date:
            monthly_in = 0
            monthly_out = 0
            
            for facility in facilities:
                code = facility['facility_code']
                capacity = facility.get('total_capacity', 0)
                surface_area = facility.get('surface_area', 0)
                
                try:
                    data = self.excel.get_storage_data(code, current, capacity, surface_area, self.db)
                    if data:
                        monthly_in += data.get('inflow_total', 0)
                        monthly_out += data.get('outflow_total', 0)
                except Exception:
                    pass
            
            total_in += monthly_in
            total_out += monthly_out
            
            dates.append(current)
            cumulative_inflow.append(total_in / 1000000)  # Convert to Mm³
            cumulative_outflow.append(total_out / 1000000)
            
            current += relativedelta(months=1)
        
        if dates:
            ax.fill_between(dates, cumulative_inflow, alpha=0.3, color='#2ecc71', label='Cumulative Inflow')
            ax.plot(dates, cumulative_inflow, color='#2ecc71', linewidth=3, marker='o')
            
            ax.fill_between(dates, cumulative_outflow, alpha=0.3, color='#e74c3c', label='Cumulative Outflow')
            ax.plot(dates, cumulative_outflow, color='#e74c3c', linewidth=3, marker='s')
            
            # Net cumulative
            net = [i - o for i, o in zip(cumulative_inflow, cumulative_outflow)]
            ax.plot(dates, net, color='#3498db', linewidth=2.5, linestyle='--', 
                   marker='D', label='Net Cumulative')
            
            self.current_data = {
                'dates': dates,
                'cumulative_inflow': cumulative_inflow,
                'cumulative_outflow': cumulative_outflow,
                'net': net
            }
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cumulative Volume (Mm³)', fontsize=12, fontweight='bold')
        ax.set_title('Cumulative Water Balance Analysis', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.95, fontsize=10)
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _download_chart(self):
        """Download current chart as PNG"""
        if not self.figure:
            messagebox.showwarning("No Chart", "Generate a chart first before downloading")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf"), ("All Files", "*.*")],
                initialfile=f"water_balance_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Success", f"Chart saved to:\n{filename}")
                logger.info(f"Chart downloaded: {filename}")
        except Exception as e:
            logger.error(f"Error downloading chart: {e}")
            messagebox.showerror("Download Error", f"Failed to save chart:\n{str(e)}")
    
    def _export_data_csv(self):
        """Export current chart data as CSV"""
        if not self.current_data:
            messagebox.showwarning("No Data", "Generate a chart first to export data")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV File", "*.csv"), ("All Files", "*.*")],
                initialfile=f"chart_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if filename:
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    if 'dates' in self.current_data:
                        dates = self.current_data['dates']
                        headers = ['Date'] + [k for k in self.current_data.keys() if k != 'dates']
                        writer.writerow(headers)
                        
                        # Write rows
                        for i, date_val in enumerate(dates):
                            row = [date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)]
                            for key in headers[1:]:
                                data = self.current_data.get(key, [])
                                if isinstance(data, dict):
                                    # Handle nested dict (e.g., sources)
                                    for subkey, subdata in data.items():
                                        if i < len(subdata):
                                            row.append(subdata[i])
                                elif i < len(data):
                                    row.append(data[i])
                            writer.writerow(row)
                
                messagebox.showinfo("Success", f"Data exported to:\n{filename}")
                logger.info(f"Data exported: {filename}")
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    
    def _clear_chart(self):
        """Clear current chart"""
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        self.figure = None
        self.canvas = None
        self.current_data = None
        
        # Restore placeholder
        placeholder = tk.Label(
            self.chart_container,
            text="📊\n\nChart cleared. Select options and click 'Generate Chart'\nto create a new visualization",
            font=('Segoe UI', 14),
            fg='#999',
            bg='white',
            justify='center'
        )
        placeholder.pack(expand=True)
        
        self.status_label.config(text="Ready. Select options and click Generate Chart.", fg='#666')
