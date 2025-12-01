"""
Analytics & Trends Dashboard
Statistical analysis and trend visualization of water balance data
"""

import tkinter as tk
from tkinter import ttk
# tkcalendar removed: using default All Data, no date picker
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns
from tkinter import filedialog, messagebox

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.excel_timeseries_extended import ExcelTimeSeriesExtended
from utils.app_logger import logger
from utils.chart_style import apply_common_style, PRIMARY_PALETTE, ACCENT_PALETTE


class AnalyticsDashboard:
    """Analytics dashboard for trend analysis and statistics"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.excel = ExcelTimeSeriesExtended()
        self.main_frame = None
        self.chart_canvas = None
        
    def load(self):
        """Load the analytics dashboard"""
        if self.main_frame:
            self.main_frame.destroy()
        
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        self._create_header()
        
        # Controls
        self._create_controls()
        
        # Chart area
        self._create_chart_area()
        
        # Show placeholder instead of loading chart immediately
        self._show_placeholder()
    
    def _create_header(self):
        """Create header section"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title = ttk.Label(header_frame, text="📊 Analytics & Trends", 
                         font=('Segoe UI', 18, 'bold'))
        title.pack(side=tk.LEFT)
        
        info = ttk.Label(header_frame, 
                        text="Statistical analysis and trend visualization",
                        font=('Segoe UI', 10),
                        foreground='#666')
        info.pack(side=tk.LEFT, padx=(15, 0))
    
    def _create_controls(self):
        """Create simplified control panel for water source time series charts"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Water Source Time Series", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        try:
            logger.info("Analytics dashboard: simplified time series controls initializing (styles: Line Trend, Bar Chart)")
        except Exception:
            pass
        
        # Row 1: Style + Time Range
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="Chart Style:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.style_var = tk.StringVar(value="Line Trend")
        styles = ["Line Trend", "Bar Chart"]
        style_combo = ttk.Combobox(row1, textvariable=self.style_var, values=styles, state='readonly', width=18)
        style_combo.pack(side=tk.LEFT, padx=(0, 20))
        # Auto-update removed - use Generate Chart button
        
        # Moving average toggle (works for both line and bar)
        self.ma_var = tk.BooleanVar(value=False)
        ma_check = ttk.Checkbutton(row1, text="Show Moving Avg (3-month)", variable=self.ma_var)
        ma_check.pack(side=tk.LEFT, padx=(0, 20))
        
        # Time Range default to All Data; hide range selector
        self.range_var = tk.StringVar(value="All Data")
        self.range_map = {"All Data": "all"}
        
        # Row 2: Source filter (code-based)
        row2 = ttk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(row2, text="Source Filter:", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All Sources")
        sources = self.db.get_water_sources(active_only=True)
        # Exclude monitoring and static boreholes from source options
        sources = [s for s in sources if s.get('source_purpose') not in ('MONITORING', 'STATIC')]
        source_options = ["All Sources"] + [f"{s['source_code']}: {s['source_name']}" for s in sources]
        filter_combo = ttk.Combobox(row2, textvariable=self.filter_var, values=source_options, state='readonly', width=45)
        filter_combo.pack(side=tk.LEFT, padx=(0, 20))
        # Auto-update removed - use Generate Chart button
        
        # Action buttons
        generate_btn = ttk.Button(row2, text="📊 Generate Chart", command=self._update_chart, style='Accent.TButton')
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        download_btn = ttk.Button(row2, text="💾 Download Chart", command=self._download_chart)
        download_btn.pack(side=tk.LEFT)
    
    def _create_chart_area(self):
        """Create chart display area"""
        chart_frame = ttk.Frame(self.main_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _show_placeholder(self):
        """Show placeholder message when no chart is loaded"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 
                '📊\n\nSelect your options above and click\n"Generate Chart" to view trends',
                ha='center', va='center', fontsize=14, color='#666',
                bbox=dict(boxstyle='round,pad=1', facecolor='#f8f9fa', edgecolor='#dee2e6', linewidth=2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
    
    def _update_chart(self):
        """Render water source time series based on selections"""
        try:
            range_label = self.range_var.get()
            time_range = self.range_map.get(range_label, "3_months")
            filter_text = self.filter_var.get()
            style = getattr(self, 'style_var', tk.StringVar(value='Line Trend')).get()
            
            # Force All Data when defaulting (no range widget)
            time_range = "all"
            
            self.figure.clear()
            self._plot_source_trends(time_range, filter_text, style)
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Error updating source trends: {e}")
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"Error loading chart:\n{str(e)}", ha='center', va='center', fontsize=12, color='red')
            self.canvas.draw()

    def _plot_source_trends(self, time_range: str, filter_text: str, style: str):
        """Plot water source time series with code-based labels from Excel Meter Readings"""
        # Apply seaborn styling for beautiful charts
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        ax = self.figure.add_subplot(111)
        start_date, end_date = self._get_date_range(time_range)
        sources = self.db.get_water_sources(active_only=True)
        # Exclude monitoring and static boreholes from chart data
        sources = [s for s in sources if s.get('source_purpose') not in ('MONITORING', 'STATIC')]
        
        # Filter specific source
        if filter_text != 'All Sources' and ':' in filter_text:
            code = filter_text.split(':')[0].strip()
            sources = [s for s in sources if s['source_code'] == code]
        
        # Limit number of sources for readability
        sources = sources[:5]
        
        import pandas as pd
        from pathlib import Path
        from utils.config_manager import ConfigManager
        
        config = ConfigManager()
        excel_path_str = config.get('data_sources.legacy_excel_path', 'data/New Water Balance  20250930 Oct.xlsx')
        base_dir = Path(__file__).parent.parent.parent
        excel_path = base_dir / excel_path_str if not Path(excel_path_str).is_absolute() else Path(excel_path_str)
        
        if not excel_path.exists():
            ax.text(0.5, 0.5, 'TRP Excel file not found\nConfigure path in Settings > Data Sources', 
                   ha='center', va='center', fontsize=10, color='red')
            return
        try:
            df = pd.read_excel(excel_path, sheet_name='Meter Readings', engine='openpyxl', header=2)
            df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df[(df['Date'] >= pd.Timestamp(start_date)) & (df['Date'] <= pd.Timestamp(end_date))]
        except Exception as e:
            ax.text(0.5, 0.5, f'Excel load error:\n{e}', ha='center', va='center', color='red')
            return
        
        # Use seaborn color palette for vibrant colors
        colors = sns.color_palette("husl", len(sources))
        show_ma = self.ma_var.get() if hasattr(self, 'ma_var') else False
        
        for idx, source in enumerate(sources):
            code = source['source_code']
            name = source['source_name']
            # Attempt column matching (exact, with " River", whitespace-insensitive)
            excel_col = None
            if code in df.columns:
                excel_col = code
            elif f"{code} River" in df.columns:
                excel_col = f"{code} River"
            else:
                for col in df.columns:
                    if col.replace(' ', '').lower() == code.replace(' ', '').lower():
                        excel_col = col
                        break
            if not excel_col:
                continue
            data = df[['Date', excel_col]].dropna()
            if data.empty:
                continue
            dates = [d.date() for d in data['Date']]
            values = data[excel_col].astype(float).tolist()
            color = colors[idx]
            if style == 'Bar Chart':
                from matplotlib import dates as mdates
                locator = mdates.AutoDateLocator()
                formatter = mdates.ConciseDateFormatter(locator)
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(formatter)
                width = 15 / max(len(sources), 1)
                offset = (idx - len(sources)/2) * width
                positions = [mdates.date2num(d) + offset for d in dates]
                ax.bar(positions, values, width=width, label=f"{code}: {name}", color=color, alpha=0.7, edgecolor='white', linewidth=1.5)
                # Add moving average line overlay for bar charts
                if show_ma and len(values) >= 3:
                    ma_series = pd.Series(values).rolling(window=3, center=True).mean()
                    ma_dates_num = [mdates.date2num(d) + offset for d in dates]
                    ax.plot(ma_dates_num, ma_series, label=f"{code} MA(3)", color=color, linestyle='--', linewidth=3, alpha=0.9, marker='o', markersize=6)
            else:  # Line Trend
                ax.plot(dates, values, label=f"{code}: {name}", color=color, marker='o', linewidth=2.5, markersize=6, alpha=0.8)
                # Add moving average overlay if enabled
                if show_ma and len(values) >= 3:
                    ma_series = pd.Series(values).rolling(window=3, center=True).mean()
                    ax.plot(dates, ma_series, label=f"{code} MA(3)", color=color, linestyle='--', linewidth=3, alpha=0.9)
        
        title_suffix = " with Moving Avg" if show_ma else ""
        ax.set_title(f"Water Source Volume Trends ({style}){title_suffix}", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Volume (m³)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, shadow=True, fancybox=True)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self.figure.autofmt_xdate()
        self.figure.tight_layout()
    
    def _get_date_range(self, time_range):
        """Calculate start and end dates based on time range"""
        end_date = date.today()
        
        if time_range == "1_month":
            start_date = end_date - relativedelta(months=1)
        elif time_range == "3_months":
            start_date = end_date - relativedelta(months=3)
        elif time_range == "6_months":
            start_date = end_date - relativedelta(months=6)
        elif time_range == "12_months":
            start_date = end_date - relativedelta(months=12)
        else:  # all
            start_date = date(2020, 1, 1)  # Far back start
        
        return start_date, end_date
    
    def _download_chart(self):
        """Download current chart as PNG or PDF"""
        try:
            # Get default filename
            style = self.style_var.get().replace(" ", "_")
            filter_text = self.filter_var.get().replace(": ", "_").replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"water_source_{style}_{filter_text}_{timestamp}"
            
            # Ask user for file location and type
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("PDF Document", "*.pdf"),
                    ("SVG Vector", "*.svg"),
                    ("JPEG Image", "*.jpg")
                ],
                title="Save Chart As"
            )
            
            if file_path:
                # Save with high DPI for quality
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                messagebox.showinfo("Success", f"Chart saved successfully to:\n{file_path}")
                logger.info(f"Chart downloaded: {file_path}")
        except Exception as e:
            logger.error(f"Error downloading chart: {e}")
            messagebox.showerror("Download Error", f"Failed to save chart:\n{str(e)}")
