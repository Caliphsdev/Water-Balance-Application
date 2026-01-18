"""
Dashboard Module - Water Balance Overview
Professional dashboard with KPIs, charts, and real-time data
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta

from utils.config_manager import config
from utils.app_logger import logger
from utils.excel_timeseries_extended import get_extended_excel_repo
from utils.excel_timeseries import get_default_excel_repo
from utils.flow_volume_loader import get_flow_volume_loader
from tkinter import messagebox
from database.db_manager import DatabaseManager
from ui.mouse_wheel_support import enable_canvas_mousewheel

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
    # Centralized chart styling
    try:
        from utils.chart_style import (
            apply_common_style,
            gradient_cmap,
            annotate_barh,
            PRIMARY_PALETTE,
            ACCENT_PALETTE,
            color_by_threshold
        )
    except Exception:
        # Fallback if style module unavailable
        apply_common_style = None
        gradient_cmap = None
        annotate_barh = None
        PRIMARY_PALETTE = []
        ACCENT_PALETTE = []
        color_by_threshold = None
except ImportError:
    MATPLOTLIB_AVAILABLE = False



class DashboardModule:
    """Dashboard module with KPIs and visualizations (Excel-driven)"""

    def __init__(self, parent):
        """Initialize dashboard"""
        self.parent = parent
        self.container = None
        self.kpi_widgets = {}
        # Lazy-load Excel repos only when needed
        self.excel_repo = None
        self.meter_repo = None
        self.db = DatabaseManager()
        self.latest_date = None
        self.sources = []
        self.facilities = []
    
    def _get_excel_repo(self):
        """Lazy-load extended Excel repository"""
        if self.excel_repo is None:
            self.excel_repo = get_extended_excel_repo()
        return self.excel_repo
    
    def _get_meter_repo(self):
        """Lazy-load meter Excel repository"""
        if self.meter_repo is None:
            self.meter_repo = get_default_excel_repo()
        return self.meter_repo

    def load(self):
        """Load dashboard content (Excel + DB metadata)"""
        import time
        load_start = time.perf_counter()
        logger.info("⏱️  Dashboard loading started")
        
        # Clear parent
        widget_clear_start = time.perf_counter()
        for widget in self.parent.winfo_children():
            widget.destroy()
        logger.info(f"  ✓ Widget cleanup: {(time.perf_counter() - widget_clear_start)*1000:.0f}ms")

        # Get latest available month from Excel (use cached if available)
        try:
            date_fetch_start = time.perf_counter()
            self.latest_date = self._get_meter_repo().get_latest_date()
            if not self.latest_date:
                # Excel not available - use current date instead
                from datetime import datetime
                self.latest_date = datetime.now().date().replace(day=1)
                logger.info(f"  ⚠️  Excel not available, using current month: {self.latest_date}")
            else:
                logger.info(f"  ✓ Latest date fetch: {(time.perf_counter() - date_fetch_start)*1000:.0f}ms")
        except Exception as e:
            # Excel not available - continue with current date
            from datetime import datetime
            self.latest_date = datetime.now().date().replace(day=1)
            logger.info(f"  ⚠️  Excel not available ({e}), using current month: {self.latest_date}")

        # Get facility metadata from database (capacity, surface area, etc.)
        # Get operational data (flows) from Excel
        try:
            # Get full facility metadata from database
            db_fetch_start = time.perf_counter()
            self.facilities = self.db.get_storage_facilities()
            logger.info(f"  ✓ DB facilities fetch: {(time.perf_counter() - db_fetch_start)*1000:.0f}ms ({len(self.facilities)} facilities)")
            
            # Map storage metrics directly from database (no Excel dependency)
            calc_start = time.perf_counter()
            for facility in self.facilities:
                facility['excel_inflow'] = 0
                facility['excel_outflow'] = 0
                facility['opening_volume'] = facility.get('current_volume', 0)
                facility['closing_volume'] = facility.get('current_volume', 0)
                facility['level_percent'] = facility.get('current_level_percent', 0)
                facility['inflow_total'] = 0
                facility['outflow_total'] = 0
            calc_total = (time.perf_counter() - calc_start) * 1000
            logger.info(f"  ✓ Storage (DB) mapping: {calc_total:.0f}ms ({len(self.facilities)} facilities)")
            
            # For sources, get metadata from database (for charts/display)
            # Excel column names are just for counting
            sources_start = time.perf_counter()
            self.sources = self.db.get_water_sources(active_only=True)
            
            # Get Excel column names for counting
            df = self._get_meter_repo()._df
            if df is not None:
                self.excel_columns = [col for col in df.columns if col not in ("Date", "Year", "Month")]
            else:
                self.excel_columns = []
            logger.info(f"  ✓ Sources fetch: {(time.perf_counter() - sources_start)*1000:.0f}ms ({len(self.sources)} sources)")
        except Exception as e:
            messagebox.showerror("Data Error", f"Could not load facility data: {e}")
            return

        # Create main container
        ui_start = time.perf_counter()
        self.container = tk.Frame(self.parent, bg=config.get_color('bg_main'))
        self.container.pack(fill='both', expand=True, padx=20, pady=20)

        # Build dashboard sections
        self._create_header()
        self._create_kpi_section()
        # Optional: new dashboard additions
        if config.get('features.new_dashboard', False):
            self._create_environment_kpis_section()
            # Rainfall chart removed - not needed
        # Add balance check results section
        self._create_balance_check_section()
        # self._create_charts_section()  # Commented out - charts not needed
        # Closure error section removed - user has a plan for it

        # Update data in widgets
        self._update_data()
        
        ui_elapsed = (time.perf_counter() - ui_start) * 1000
        logger.info(f"  ✓ UI construction: {ui_elapsed:.0f}ms")
        
        total_elapsed = (time.perf_counter() - load_start) * 1000
        logger.info(f"✅ Dashboard loaded in {total_elapsed:.0f}ms")
    
    def _create_header(self):
        """Create dashboard header"""
        header_frame = tk.Frame(self.container, bg=config.get_color('bg_main'))
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title
        title = tk.Label(
            header_frame,
            text="📊 Water Balance Dashboard",
            font=config.get_font('heading_large'),
            fg=config.get_color('primary'),
            bg=config.get_color('bg_main'),
            anchor='w'
        )
        title.pack(side='left')
        
        # Date info subtitle with volume calculation date
        date_str = self.latest_date.strftime('%B %Y') if self.latest_date else 'N/A'
        
        # Check if facilities have volume_calc_date to show when volumes were last updated
        volume_dates = set()
        for f in self.facilities:
            vol_date = f.get('volume_calc_date')
            if vol_date:
                volume_dates.add(vol_date)
        
        if volume_dates:
            # Show volume calculation date if available
            vol_date_str = sorted(volume_dates)[-1] if volume_dates else None
            if vol_date_str:
                from datetime import datetime
                try:
                    vol_date_obj = datetime.strptime(vol_date_str, '%Y-%m-%d').date()
                    vol_date_display = vol_date_obj.strftime('%B %Y')
                    date_info = f'  •  Latest: {date_str} | DB Volumes: {vol_date_display}'
                except:
                    date_info = f'  •  Latest: {date_str}'
            else:
                date_info = f'  •  Latest: {date_str}'
        else:
            date_info = f'  •  Latest: {date_str}'
        
        subtitle = tk.Label(
            header_frame,
            text=date_info,
            font=('Segoe UI', 9),
            bg=config.get_color('bg_main'),
            fg='#666'
        )
        subtitle.pack(side='left', padx=(5, 0))
    
    def _create_kpi_section(self):
        """Create KPI cards section (DB metadata + Excel flows)"""
        kpi_frame = tk.Frame(self.container, bg=config.get_color('bg_main'))
        kpi_frame.pack(fill='x', pady=(0, 20))

        # Aggregate statistics from database metadata and Excel calculated volumes
        # Count all ACTIVE database sources (already filtered by get_water_sources(active_only=True))
        total_sources = len(self.sources)
        total_facilities = len(self.facilities)
        total_capacity = sum(f.get('total_capacity', 0) for f in self.facilities)
        # Use current_volume from database (updated when calculations are saved)
        total_opening = sum(f.get('current_volume', 0) for f in self.facilities)
        total_volume = total_opening
        utilization = (total_volume / total_capacity * 100) if total_capacity > 0 else 0.0

        # Debug logging to verify totals
        try:
            from utils.app_logger import logger
            logger.info(f"Dashboard totals → Current (DB): {total_volume:,.0f} m³, Capacity: {total_capacity:,.0f} m³")
        except Exception:
            pass

        kpi_configs = [
            {
                'key': 'total_sources',
                'title': 'Water Sources',
                'value': total_sources,
                'unit': 'active',
                'icon': '≈',
                'color': config.get_color('info')
            },
            {
                'key': 'total_facilities',
                'title': 'Storage Facilities',
                'value': total_facilities,
                'unit': 'dams',
                'icon': '▣',
                'color': config.get_color('primary')
            },
            {
                'key': 'total_capacity',
                'title': 'Total Capacity',
                'value': f"{total_capacity / 1000000:.2f}",
                'unit': 'Mm³',
                'icon': '▥',
                'color': config.get_color('success')
            },
            {
                'key': 'total_volume',
                'title': 'Current Volume',
                'value': f"{total_volume / 1000000:.2f}",
                'unit': 'Mm³ (DB)',
                'icon': '▤',
                'color': config.get_color('primary')
            },
            {
                'key': 'utilization',
                'title': 'Utilization',
                'value': f"{utilization:.1f}",
                'unit': '%',
                'icon': '▲',
                'color': self._get_utilization_color(utilization)
            },
        ]

        for i, kpi in enumerate(kpi_configs):
            card, value_widget = self._create_kpi_card(kpi_frame, kpi)
            card.grid(row=0, column=i, padx=5, sticky='ew')
            kpi_frame.columnconfigure(i, weight=1)
            self.kpi_widgets[kpi['key']] = {'value': value_widget}

    def _create_environment_kpis_section(self):
        """Environment KPIs: rainfall, evaporation, seepage gain (latest month)."""
        try:
            section = tk.Frame(self.container, bg=config.get_color('bg_main'))
            section.pack(fill='x', pady=(0, 20))

            # Title
            tk.Label(
                section,
                text="Environmental KPIs",
                font=config.get_font('heading_medium'),
                fg=config.get_color('text_primary'),
                bg=config.get_color('bg_main'),
                anchor='w'
            ).pack(fill='x')

            grid = tk.Frame(section, bg=config.get_color('bg_main'))
            grid.pack(fill='x', pady=(8, 0))

            # Latest month/year
            latest = self.latest_date or date.today().replace(day=1)
            month = latest.month
            year = latest.year

            # Rainfall and evaporation (regional) - use year-specific values when available
            rainfall_mm = self.db.get_regional_rainfall_monthly(month, year=year)
            evaporation_mm = self.db.get_regional_evaporation_monthly(month, zone=None, year=year)

            # Seepage gain (sum across active facilities)
            # NOTE: Seepage methods were removed as seepage is now calculated automatically
            # based on facility properties (aquifer_gain_rate_pct, is_lined flag)
            seepage_total_m3 = 0.0

            cards = [
                {'key': 'rainfall_mm', 'title': 'Rainfall (Regional)', 'value': f"{rainfall_mm:.0f}", 'unit': 'mm', 'icon': '☔', 'color': config.get_color('primary')},
                {'key': 'evaporation_mm', 'title': 'Evaporation (Regional)', 'value': f"{evaporation_mm:.0f}", 'unit': 'mm', 'icon': '☀', 'color': config.get_color('warning')},
            ]

            for i, kpi in enumerate(cards):
                card, value_widget = self._create_kpi_card(grid, kpi)
                card.grid(row=0, column=i, padx=5, sticky='ew')
                grid.columnconfigure(i, weight=1)
                self.kpi_widgets[kpi['key']] = {'value': value_widget}
        except Exception as e:
            logger.warning(f"Environmental KPIs failed: {e}")

    def _create_balance_check_section(self):
        """Display last run balance check results (saved from Flow Diagram balance check)"""
        try:
            import json
            from pathlib import Path
            
            # Load saved balance check results
            results_path = Path('data/balance_check_last_run.json')
            if not results_path.exists():
                logger.info("No balance check results available yet - run balance check from Flow Diagram first")
                return
            
            with open(results_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Extract results
            year = results.get('year', 2025)
            month = results.get('month', 1)
            month_name = results.get('month_name', 'Unknown')
            inflows_total = results.get('inflows_total', 0.0)
            outflows_total = results.get('outflows_total', 0.0)
            recirculation_total = results.get('recirculation_total', 0.0)
            balance_error_pct = results.get('balance_error_pct', 0.0)
            timestamp = results.get('timestamp', 'Unknown')
            
            logger.info(f"Dashboard: Loaded balance check from {timestamp}")
            
            # Status color based on balance error
            error_pct = abs(balance_error_pct)
            if error_pct < 0.1:
                status_color = config.get_color('success')
                status_icon = "✅"
                status_text = "Excellent"
            elif error_pct < 5.0:
                status_color = config.get_color('warning')
                status_icon = "⚠️"
                status_text = "Good"
            else:
                status_color = config.get_color('error')
                status_icon = "❌"
                status_text = "Check"
            
            # Create a section for balance check
            section = tk.Frame(self.container, bg=config.get_color('bg_main'))
            section.pack(fill='x', pady=(0, 15), padx=0)

            # Small heading
            heading_frame = tk.Frame(section, bg=config.get_color('bg_main'))
            heading_frame.pack(fill='x', pady=(0, 6), padx=0)
            
            # Parse timestamp for display
            try:
                from datetime import datetime as dt
                run_time = dt.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M')
            except:
                run_time = 'Unknown'
            
            tk.Label(
                heading_frame,
                text=f"⚖️  Balance Status  •  {month_name} {year}  •  Last Run: {run_time}",
                font=config.get_font('heading_small'),
                fg=config.get_color('primary'),
                bg=config.get_color('bg_main'),
                anchor='w'
            ).pack(side='left')

            # Mini cards grid
            balance_grid = tk.Frame(section, bg=config.get_color('bg_main'))
            balance_grid.pack(fill='x', padx=0)

            # Balance metrics in compact card format
            balance_cards = [
                {
                    'title': 'Total Inflows',
                    'value': f"{inflows_total:,.0f}",
                    'unit': 'm³',
                    'icon': '💧',
                    'color': config.get_color('info')
                },
                {
                    'title': 'Total Outflows',
                    'value': f"{outflows_total:,.0f}",
                    'unit': 'm³',
                    'icon': '🚰',
                    'color': config.get_color('error')
                },
                {
                    'title': 'Recirculation',
                    'value': f"{recirculation_total:,.0f}",
                    'unit': 'm³',
                    'icon': '♻️',
                    'color': config.get_color('success')
                },
                {
                    'title': 'Balance Error',
                    'value': f"{balance_error_pct:.2f}",
                    'unit': '%',
                    'icon': '📊',
                    'color': status_color
                },
                {
                    'title': 'Status',
                    'value': status_text,
                    'unit': 'Result',
                    'icon': status_icon,
                    'color': status_color
                },
            ]

            # Create compact cards
            for i, card_data in enumerate(balance_cards):
                # Mini card frame
                card = tk.Frame(
                    balance_grid,
                    bg='white',
                    relief='solid',
                    borderwidth=1,
                    highlightbackground='#e0e0e0',
                    highlightthickness=1
                )
                card.grid(row=0, column=i, padx=3, sticky='ew', pady=0)
                balance_grid.columnconfigure(i, weight=1)

                # Icon
                icon_label = tk.Label(card, text=card_data['icon'], font=('Segoe UI', 18, 'bold'), 
                                     bg='white', fg=card_data['color'])
                icon_label.pack(pady=(6, 2))

                # Value
                value_label = tk.Label(
                    card,
                    text=str(card_data['value']),
                    font=('Segoe UI', 10, 'bold'),
                    fg=card_data['color'],
                    bg='white'
                )
                value_label.pack()

                # Unit
                unit_label = tk.Label(card, text=card_data['unit'], font=('Segoe UI', 7),
                                     fg='#757575', bg='white')
                unit_label.pack(pady=(0, 1))

                # Title
                title_label = tk.Label(card, text=card_data['title'], font=('Segoe UI', 8),
                                      fg='#2c3e50', bg='white')
                title_label.pack(pady=(0, 4))

            logger.info(f"✅ Balance check displayed: {month_name} {year}, Error={balance_error_pct:.2f}% (Last run: {run_time})")

        except Exception as e:
            logger.error(f"Balance check section failed: {e}", exc_info=True)

    def _create_rain_evap_trend_section(self):
        """Mini-trend: last 6 months rainfall vs evaporation."""
        try:
            section = tk.Frame(self.container, bg=config.get_color('bg_main'))
            section.pack(fill='x', pady=(0, 20))

            frame = tk.Frame(section, bg='white', relief='solid', borderwidth=1)
            frame.pack(fill='both', expand=True)

            header = tk.Frame(frame, bg='white')
            header.pack(fill='x', padx=15, pady=(15, 10))
            tk.Label(
                header,
                text="Rainfall vs Evaporation (6 months)",
                font=config.get_font('heading_medium'),
                fg=config.get_color('text_primary'),
                bg='white',
                anchor='w'
            ).pack(side='left')

            if not MATPLOTLIB_AVAILABLE:
                self._show_no_data_message(frame)
                return

            # Build month sequence ending at latest
            latest = self.latest_date or date.today().replace(day=1)
            months = []
            cur = latest
            for _ in range(6):
                months.append(cur)
                # previous month
                prev_m = cur.month - 1
                prev_y = cur.year if prev_m >= 1 else cur.year - 1
                prev_m = 12 if prev_m == 0 else prev_m
                cur = cur.replace(year=prev_y, month=prev_m, day=1)
            months.reverse()

            rain = []
            evap = []
            labels = []
            for d in months:
                labels.append(d.strftime('%b %Y'))
                rain.append(self.db.get_regional_rainfall_monthly(d.month, year=None))
                evap.append(self.db.get_regional_evaporation_monthly(d.month, zone=None, year=None))

            fig = Figure(figsize=(10, 3.8), dpi=80, facecolor='white')
            ax = fig.add_subplot(111)
            ax.plot(labels, rain, color='#1E88E5', linewidth=2.0, marker='o', markersize=6, label='Rainfall (mm)')
            ax.plot(labels, evap, color='#E53935', linewidth=2.0, marker='o', markersize=6, label='Evaporation (mm)')
            ax.fill_between(range(len(labels)), rain, [0]*len(rain), color='#1E88E5', alpha=0.08)
            ax.fill_between(range(len(labels)), evap, [0]*len(evap), color='#E53935', alpha=0.08)
            if apply_common_style:
                apply_common_style(ax, 'Rainfall vs Evaporation')
            else:
                ax.set_title('Rainfall vs Evaporation', fontsize=11, pad=14)
                ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.set_ylabel('mm', fontsize=9)
            ax.set_xlabel('Month', fontsize=9)
            ax.tick_params(axis='x', labelrotation=0, labelsize=8)
            ax.legend(fontsize=8, frameon=False, loc='upper left')
            # Ensure the title isn't clipped by the figure's top margin
            # Leave extra space at the top using the rect parameter.
            fig.tight_layout(pad=2, rect=[0, 0.02, 1, 0.97])

            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        except Exception as e:
            logger.warning(f"Rain/Evap trend failed: {e}")
    
    def _create_kpi_card(self, parent, data):
        """Create a single KPI card"""
        card = tk.Frame(
            parent,
            bg='white',
            relief='solid',
            borderwidth=1,
            highlightbackground='#e0e0e0',
            highlightthickness=1
        )
        
        # Icon - simple and clean
        icon_text = data['icon']
        icon_label = tk.Label(card, text=icon_text, font=('Segoe UI', 28, 'bold'), bg='white', fg=data['color'])
        icon_label.pack(pady=(12, 5))
        
        # Value
        value_label = tk.Label(
            card,
            text=str(data['value']),
            font=('Segoe UI', 18, 'bold'),
            fg=data['color'],
            bg='white'
        )
        value_label.pack()
        # Unit
        unit_label = tk.Label(card, text=data['unit'], font=('Segoe UI', 8),
                               fg='#757575', bg='white')
        unit_label.pack(pady=(0, 5))
        # Title
        title_label = tk.Label(card, text=data['title'], font=('Segoe UI', 10, 'bold'),
                                fg='#2c3e50', bg='white')
        title_label.pack(pady=(0, 10))
        # Return card and main value label (unit/title stored visually only)
        return card, value_label
    
    def _create_charts_section(self):
        """Create charts section"""
        charts_frame = tk.Frame(self.container, bg=config.get_color('bg_main'))
        charts_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Left chart - Storage Overview
        left_chart = tk.Frame(charts_frame, bg='white', relief='solid', borderwidth=1)
        left_chart.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self._create_storage_chart(left_chart)
        
        # Right chart - Water Sources
        right_chart = tk.Frame(charts_frame, bg='white', relief='solid', borderwidth=1)
        right_chart.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        self._create_sources_chart(right_chart)

    def _create_closure_error_section(self):
        """Create closure error trend section with enhanced styling"""
        try:
            section = tk.Frame(self.container, bg=config.get_color('bg_main'))
            section.pack(fill='x', pady=(0, 20), padx=0)

            frame = tk.Frame(section, bg='white', relief='solid', borderwidth=2)
            frame.pack(fill='both', expand=True, padx=15)

            header = tk.Frame(frame, bg='#f5f7fa', relief='solid', borderwidth=0)
            header.pack(fill='x', padx=15, pady=(0, 0))
            title = tk.Label(
                header,
                text="Closure Error Trend",
                font=config.get_font('heading_medium'),
                fg='#2c3e50',
                bg='#f5f7fa',
                anchor='w',
                pady=12
            )
            title.pack(side='left')
            # Controls: timeframe and smoothing
            controls = tk.Frame(header, bg='#f5f7fa')
            controls.pack(side='right', padx=15)
            view_var = tk.StringVar(value='sparkline')
            timeframe_var = tk.StringVar(value='90')
            smoothing_var = tk.BooleanVar(value=True)
            # View mode toggle
            tk.Label(controls, text="View:", bg='#f5f7fa', font=('Segoe UI', 9), fg='#2c3e50').pack(side='left', padx=(0,6))
            for mode,label in (("sparkline","Sparkline"),("heatmap","Heatmap")):
                rbv = tk.Radiobutton(controls, text=label, variable=view_var, value=mode, bg='#f5f7fa', fg='#2c3e50', indicatoron=False, activebackground='#3498db', activeforeground='white', selectcolor='#3498db', relief='raised', bd=1, padx=8, pady=3)
                rbv.pack(side='left', padx=3)
            tk.Label(controls, text="Range:", bg='#f5f7fa', font=('Segoe UI', 9), fg='#2c3e50').pack(side='left', padx=(10,6))
            for days in ('30d','90d','180d'):
                rb = tk.Radiobutton(controls, text=days, variable=timeframe_var, value=days[:-1], bg='#f5f7fa', fg='#2c3e50', indicatoron=False, activebackground='#3498db', activeforeground='white', selectcolor='#3498db', relief='raised', bd=1, padx=6, pady=3)
                rb.pack(side='left', padx=2)
            chk = tk.Checkbutton(controls, text='Smooth', variable=smoothing_var, bg='#f5f7fa', fg='#2c3e50', activebackground='#f5f7fa', activeforeground='#2c3e50', selectcolor='#3498db')
            chk.pack(side='left', padx=(8,0))

            if not MATPLOTLIB_AVAILABLE:
                self._show_no_data_message(frame)
                return

            # Initial data fetch based on default timeframe
            trend = self.db.get_closure_error_trend(int(timeframe_var.get()))
            if not trend or len(trend) == 0:
                self._show_no_data_message(frame)
                return
        except Exception as e:
            logger.error(f"Error creating closure error section: {e}")
            return

        dates = [t['calc_date'] for t in trend]
        percents = [t.get('closure_error_percent', 0) for t in trend]
        threshold = 5.0  # percent
        colors_line = '#1E88E5'

        # Choose visualization by view mode
        fig = Figure(figsize=(10, 2.8), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)
        view_mode = view_var.get()
        if view_mode == 'heatmap':
            # Build a simple weekly heatmap: rows=weeks, cols=days
            import numpy as np
            import datetime as dt
            # Map dates to weekday (0-6) and week index
            start = dates[0]
            week_starts = []
            current = start - dt.timedelta(days=start.weekday())
            while current <= dates[-1]:
                week_starts.append(current)
                current += dt.timedelta(days=7)
            week_index = {ws:i for i,ws in enumerate(week_starts)}
            grid = np.full((len(week_starts), 7), np.nan)
            for d,p in zip(dates, percents):
                ws = d - dt.timedelta(days=d.weekday())
                r = week_index.get(ws, None)
                c = d.weekday()
                if r is not None:
                    grid[r, c] = p
            # Colormap thresholds
            import matplotlib
            cmap = matplotlib.colors.ListedColormap(['#E3F2FD','#90CAF9','#1E88E5','#E53935'])
            bounds = [0, threshold*0.5, threshold, threshold*1.5, 100]
            norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
            im = ax.imshow(grid, aspect='auto', cmap=cmap, norm=norm, interpolation='nearest')
            ax.set_yticks(range(len(week_starts)))
            ax.set_yticklabels([ws.strftime('%b %d') for ws in week_starts], fontsize=8)
            ax.set_xticks(range(7))
            ax.set_xticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], fontsize=8)
            ax.set_title('Closure Error Heatmap', fontsize=11, pad=6)
            cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.ax.set_ylabel('%', rotation=0, labelpad=10)
        else:
            # Sparkline view
            series = percents
            if smoothing_var.get() and len(series) >= 7:
                ma = []
                w = 7
                for i in range(len(series)):
                    window = series[max(0, i-w+1):i+1]
                    ma.append(sum(window)/len(window))
                ax.plot(dates, ma, color=colors_line, linewidth=1.8)
                ax.fill_between(dates, ma, [0]*len(ma), color=colors_line, alpha=0.08)
            else:
                ax.plot(dates, series, color=colors_line, linewidth=1.6)
                ax.fill_between(dates, series, [0]*len(series), color=colors_line, alpha=0.08)
            ax.axhline(threshold, color='#E53935', linestyle='--', linewidth=1, label=f'Threshold {threshold:.0f}%')

        # Highlight points exceeding threshold
        exceed_x = [d for d, p in zip(dates, percents) if p > threshold]
        exceed_y = [p for p in percents if p > threshold]
        if exceed_x:
            ax.scatter(exceed_x, exceed_y, color='#E53935', s=22, zorder=3)

        # Styling
        if apply_common_style:
            apply_common_style(ax, 'Daily Closure Error %')
        else:
            ax.set_title('Daily Closure Error %', fontsize=11, pad=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
        if view_mode == 'heatmap':
            ax.set_xlabel('Day of Week', fontsize=9)
            ax.set_ylabel('Week', fontsize=9)
        else:
            ax.set_ylabel('Error (%)', fontsize=9)
            ax.set_xlabel('Date', fontsize=9)
            ax.tick_params(axis='x', labelrotation=0, labelsize=8)
            ax.legend(fontsize=8, frameon=False, loc='upper left')
        fig.tight_layout(pad=2)

        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Summary stats row
        stats_row = tk.Frame(frame, bg='white')
        stats_row.pack(fill='x', padx=15, pady=(0, 10))
        avg_val = sum(percents)/len(percents) if percents else 0
        min_val = min(percents) if percents else 0
        max_val = max(percents) if percents else 0
        for label, val in (('Avg', avg_val), ('Min', min_val), ('Max', max_val)):
            box = tk.Frame(stats_row, bg='#F7F9FC', relief='flat', borderwidth=0)
            box.pack(side='left', padx=8)
            tk.Label(box, text=f"{label}", bg='#F7F9FC', fg='#607D8B').pack()
            tk.Label(box, text=f"{val:.1f}%", bg='#F7F9FC', fg=config.get_color('text_primary'), font=config.get_font('body_bold')).pack()

        # Persistent alert if 3+ consecutive days exceed threshold at end of series
        streak = 0
        for p in reversed(percents):
            if p > threshold:
                streak += 1
            else:
                break
        if streak >= 3:
            alert = tk.Frame(frame, bg='#FFEBEE')
            alert.pack(fill='x', padx=10, pady=(0, 10))
            tk.Label(alert, text="Closure error warning", bg='#FFEBEE', fg='#B71C1C', font=config.get_font('body_bold')).pack(anchor='w', padx=8, pady=(6,0))
            tk.Label(alert, text=f"Above {threshold:.0f}% for last {streak} days", bg='#FFEBEE', fg='#B71C1C').pack(anchor='w', padx=8, pady=(0,6))

        # Wire controls to refresh chart
        def refresh_chart(*_):
            # Recreate section with new settings
            for w in frame.winfo_children():
                w.destroy()
            # Reset by calling again (will rebuild with current var values)
            self._create_closure_error_section()
        timeframe_var.trace_add('write', lambda *_: refresh_chart())
        smoothing_var.trace_add('write', lambda *_: refresh_chart())
        view_var.trace_add('write', lambda *_: refresh_chart())
    
    def _create_storage_chart(self, parent):
        """Create storage facilities chart"""
        # Title
        title = tk.Label(
            parent,
            text="Storage Facilities Overview",
            font=config.get_font('heading_medium'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        title.pack(fill='x', padx=15, pady=(15, 10))
        
        if MATPLOTLIB_AVAILABLE:
            # Use cached facilities data
            facilities = self.facilities
            
            if facilities:
                # Create matplotlib figure
                fig = Figure(figsize=(6, 4), dpi=80, facecolor='white')
                ax = fig.add_subplot(111)
                
                # Prepare data
                names = [f['facility_code'] for f in facilities[:8]]  # Top 8
                capacities = [f['total_capacity'] / 1000000 for f in facilities[:8]]  # Convert to Mm³
                # Colors cycle (fallback to primary if style palette missing)
                colors_cycle = PRIMARY_PALETTE if PRIMARY_PALETTE else [config.get_color('primary')]
                bar_colors = [colors_cycle[i % len(colors_cycle)] for i in range(len(names))]
                bars = ax.barh(names, capacities, color=bar_colors, edgecolor='white')

                # Annotate values if helper available
                if annotate_barh:
                    annotate_barh(ax, bars, fmt='{:.2f} Mm³')

                # Styling
                if apply_common_style:
                    apply_common_style(ax, 'Storage Capacity by Facility')
                else:
                    ax.set_title('Storage Capacity by Facility', fontsize=11, pad=10)
                    ax.grid(axis='x', alpha=0.3, linestyle='--')
                ax.set_xlabel('Capacity (Mm³)', fontsize=10)
                ax.tick_params(axis='y', labelsize=9)
                fig.tight_layout(pad=2)
                
                # Embed in tkinter
                canvas = FigureCanvasTkAgg(fig, parent)
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=(0, 10))
            else:
                self._show_no_data_message(parent)
        else:
            self._show_fallback_storage_list(parent)
    
    def _create_sources_chart(self, parent):
        """Create water sources chart"""
        # Title
        title = tk.Label(
            parent,
            text="Water Sources by Type",
            font=config.get_font('heading_medium'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        title.pack(fill='x', padx=15, pady=(15, 10))
        
        if MATPLOTLIB_AVAILABLE:
            # Use cached sources data (exclude monitoring-only and non-abstraction types like PCD/STP)
            sources = self.sources
            # Filter out monitoring-only purposes
            sources = [s for s in sources if s.get('source_purpose','ABSTRACTION') in ('ABSTRACTION','DUAL_PURPOSE')]
            # Explicitly exclude known monitoring-only type codes that were added to the type table (PCD/STP)
            sources = [s for s in sources if s.get('type_code') not in {'PCD','STP'}]
            
            if sources:
                # Count by type
                type_counts = {}
                for source in sources:
                    stype = source['type_name']
                    type_counts[stype] = type_counts.get(stype, 0) + 1
                # Aggregate very small slices (<5% of total) under 'Other' to declutter
                total = sum(type_counts.values())
                major_items = []
                other_total = 0
                for label, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                    pct = count / total
                    if pct < 0.05 and len(type_counts) > 6:  # threshold only if many categories
                        other_total += count
                    else:
                        major_items.append((label, count))
                if other_total > 0:
                    major_items.append(('Other', other_total))

                data_labels = [m[0] for m in major_items]
                data_values = [m[1] for m in major_items]
                # Custom autopct: show percent only if >=3% else blank
                def _pct_fmt(pct):
                    return f"{pct:.0f}%" if pct >= 3 else ''

                # Distinct color palette (tab20 or fallback accent palette)
                try:
                    from matplotlib import cm
                    cmap = cm.get_cmap('tab20')
                    colors = [cmap(i / max(1, len(data_values)-1)) for i in range(len(data_values))]
                except Exception:
                    base_palette = ACCENT_PALETTE if ACCENT_PALETTE else [
                        config.get_color('primary'),
                        config.get_color('success'),
                        config.get_color('warning'),
                        config.get_color('info'),
                        config.get_color('secondary'),
                        '#6A4C93', '#0077B6', '#FF6F91', '#1982C4', '#8AC926'
                    ]
                    colors = base_palette[:len(data_values)]

                # Create figure
                fig = Figure(figsize=(6, 4), dpi=80, facecolor='white')
                ax = fig.add_subplot(111)
                wedges, texts, autotexts = ax.pie(
                    data_values,
                    labels=None,  # use legend instead
                    autopct=_pct_fmt,
                    colors=colors,
                    startangle=90,
                    pctdistance=0.70,
                    wedgeprops={'linewidth': 0.8, 'edgecolor': 'white'}
                )
                ax.axis('equal')  # circular
                # Title styling
                ax.set_title('Distribution by Source Type', fontsize=11, pad=10)
                # Format autopct texts
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_weight('bold')
                    autotext.set_color('white')
                # Add legend outside to avoid label collision
                ax.legend(wedges, data_labels, title='Source Types',
                          loc='center left', bbox_to_anchor=(1, 0.5), frameon=False, fontsize=8)
                fig.tight_layout(pad=2)

                canvas = FigureCanvasTkAgg(fig, parent)
                canvas.draw()
                widget = canvas.get_tk_widget()
                widget.pack(fill='both', expand=True, padx=10, pady=(0, 10))
            else:
                self._show_no_data_message(parent)
        else:
            self._show_fallback_sources_list(parent)
    
    def _create_status_section(self):
        """Create status and recent activity section"""
        status_frame = tk.Frame(self.container, bg='white', relief='solid', borderwidth=1)
        status_frame.pack(fill='both', expand=True)
        
        # Title
        title = tk.Label(
            status_frame,
            text="System Status & Information",
            font=config.get_font('heading_medium'),
            fg=config.get_color('text_primary'),
            bg='white',
            anchor='w'
        )
        title.pack(fill='x', padx=15, pady=(15, 10))
        
        # Status items
        status_items = tk.Frame(status_frame, bg='white')
        status_items.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Get actual data
        sources = self.sources
        facilities = self.facilities
        constants = self.db.get_all_constants()
        
        # Status information
        info_items = [
            ("Active Water Sources", f"{len(sources)} sources operational"),
            ("Storage Facilities", f"{len(facilities)} dams and tanks"),
            ("Total Storage Capacity", f"{sum(f['total_capacity'] for f in facilities) / 1000000:.2f} Mm³"),
            ("System Constants", f"{len(constants)} calculation parameters configured"),
            ("Database Status", "Connected and operational"),
        ]
        
        for i, (label, value) in enumerate(info_items):
            item_frame = tk.Frame(status_items, bg='white')
            item_frame.pack(fill='x', pady=3)
            
            label_widget = tk.Label(
                item_frame,
                text=label,
                font=config.get_font('body_bold'),
                fg=config.get_color('text_primary'),
                bg='white',
                anchor='w'
            )
            label_widget.pack(side='left')
            
            value_widget = tk.Label(
                item_frame,
                text=value,
                font=config.get_font('body'),
                fg=config.get_color('text_secondary'),
                bg='white',
                anchor='e'
            )
            value_widget.pack(side='right')
    
    def _show_fallback_storage_list(self, parent):
        """Fallback storage list when matplotlib not available"""
        facilities = self.facilities
        
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        enable_canvas_mousewheel(canvas)
        
        # Add facilities
        for facility in facilities:
            item = tk.Frame(scrollable_frame, bg='white')
            item.pack(fill='x', padx=15, pady=5)
            
            name = tk.Label(
                item,
                text=f"{facility['facility_code']}: {facility['facility_name']}",
                font=config.get_font('body_bold'),
                fg=config.get_color('text_primary'),
                bg='white',
                anchor='w'
            )
            name.pack(side='left')
            
            capacity = tk.Label(
                item,
                text=f"{facility['total_capacity'] / 1000000:.2f} Mm³",
                font=config.get_font('body'),
                fg=config.get_color('text_secondary'),
                bg='white',
                anchor='e'
            )
            capacity.pack(side='right')
        
        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=(0, 10))
        scrollbar.pack(side='right', fill='y')
    
    def _show_fallback_sources_list(self, parent):
        """Fallback sources list when matplotlib not available"""
        sources = self.sources
        
        # Count by type
        type_counts = {}
        for source in sources:
            stype = source['type_name']
            type_counts[stype] = type_counts.get(stype, 0) + 1
        
        # Display counts
        list_frame = tk.Frame(parent, bg='white')
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        for stype, count in type_counts.items():
            item = tk.Frame(list_frame, bg='white')
            item.pack(fill='x', pady=5)
            
            label = tk.Label(
                item,
                text=stype,
                font=config.get_font('body_bold'),
                fg=config.get_color('text_primary'),
                bg='white',
                anchor='w'
            )
            label.pack(side='left')
            
            value = tk.Label(
                item,
                text=f"{count} sources",
                font=config.get_font('body'),
                fg=config.get_color('text_secondary'),
                bg='white',
                anchor='e'
            )
            value.pack(side='right')
    
    def _show_no_data_message(self, parent):
        """Show no data available message"""
        msg = tk.Label(
            parent,
            text="No data available",
            font=config.get_font('body'),
            fg=config.get_color('text_secondary'),
            bg='white'
        )
        msg.pack(expand=True)
    
    def _get_utilization_color(self, percent):
        """Get color based on utilization percentage"""
        if percent < 30:
            return config.get_color('error')  # Low - red
        elif percent < 60:
            return config.get_color('warning')  # Medium - orange
        else:
            return config.get_color('success')  # Good - green
    
    def _update_data(self):
        """Update dashboard data from DB + Excel"""
        try:
            # Recompute stats from database and Excel
            # Count all active database sources (already filtered by get_water_sources(active_only=True))
            total_sources = len(self.sources)
            total_facilities = len(self.facilities)
            total_capacity = sum(f.get('total_capacity', 0) for f in self.facilities)
            # Use closing_volume from Excel (real-time calculated) instead of database current_volume (static)
            total_volume = sum(f.get('closing_volume', 0) for f in self.facilities)
            utilization = (total_volume / total_capacity * 100) if total_capacity > 0 else 0.0

            if 'total_sources' in self.kpi_widgets:
                self.kpi_widgets['total_sources']['value'].config(text=str(total_sources))
            if 'total_facilities' in self.kpi_widgets:
                self.kpi_widgets['total_facilities']['value'].config(text=str(total_facilities))
            if 'total_capacity' in self.kpi_widgets:
                self.kpi_widgets['total_capacity']['value'].config(text=f"{total_capacity / 1000000:.2f}")
            if 'total_volume' in self.kpi_widgets:
                self.kpi_widgets['total_volume']['value'].config(text=f"{total_volume / 1000000:.2f}")
            if 'utilization' in self.kpi_widgets:
                self.kpi_widgets['utilization']['value'].config(text=f"{utilization:.1f}%")
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
    
    def refresh_data(self):
        """Refresh dashboard data"""
        # Just update the data, don't recreate everything
        self._update_data()

