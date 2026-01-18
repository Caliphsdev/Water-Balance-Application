"""
KPI Dashboard Module
Display water balance Key Performance Indicators matching Excel Dashboard
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, date
from typing import Optional
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from ui.mouse_wheel_support import enable_canvas_mousewheel
from utils.water_balance_calculator import WaterBalanceCalculator
from utils.app_logger import logger
from utils.ui_notify import notifier
from utils.error_handler import error_handler, ErrorCategory


class KPIDashboard:
    """KPI Dashboard matching Excel metrics"""
    
    def __init__(self, parent):
        self.parent = parent
        self.db = DatabaseManager()
        self.calculator = WaterBalanceCalculator()
        self.main_frame = None
        self.kpi_data = None
    
    def load(self):
        """Load the KPI dashboard"""
        if self.main_frame:
            self.main_frame.destroy()
        
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._create_header()
        
        # Date selector
        self._create_date_selector()
        
        # KPI sections
        self._create_kpi_sections()
        
        # Load default KPIs
        self._load_kpis()
    
    def _create_header(self):
        """Create header section"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = ttk.Label(header_frame, text="Performance Dashboard", 
                         font=('Segoe UI', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        info = ttk.Label(header_frame, 
                        text="Key Performance Indicators - Excel Dashboard Parity",
                        font=('Segoe UI', 9),
                        foreground='#666')
        info.pack(side=tk.LEFT, padx=(20, 0))
    
    def _create_date_selector(self):
        """Create date selection controls"""
        date_frame = ttk.Frame(self.main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(date_frame, text="Period:", width=10).pack(side=tk.LEFT, padx=(0, 10))
        
        self.date_var = tk.StringVar(master=date_frame)
        date_entry = DateEntry(date_frame, textvariable=self.date_var,
                              width=15, background='darkblue',
                              foreground='white', borderwidth=2,
                              date_pattern='yyyy-mm-dd')
        date_entry.set_date(date.today())
        date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        refresh_btn = ttk.Button(date_frame, text="Refresh KPIs", 
                                command=self._load_kpis,
                                style='Accent.TButton')
        refresh_btn.pack(side=tk.LEFT)
    
    def _create_kpi_sections(self):
        """Create all KPI display sections in multi-column layout"""
        # Container with scrollbar for many KPIs
        container = ttk.Frame(self.main_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="center")
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Center container for all KPI sections
        center_container = ttk.Frame(self.scrollable_frame)
        center_container.pack(expand=True, anchor='center', padx=50)
        
        
        # Row 1: Efficiency and Recycling side-by-side
        row1 = ttk.Frame(center_container)
        row1.pack(fill=tk.X, pady=(0, 10))
        self._create_efficiency_section(parent=row1, pack_side='left')
        self._create_recycling_section(parent=row1, pack_side='left')
        
        # Row 2: Dependency (full width)
        self._create_dependency_section(parent=center_container)
        
        # Row 3: Security and Compliance side-by-side
        row3 = ttk.Frame(center_container)
        row3.pack(fill=tk.X, pady=(0, 10))
        self._create_security_section(parent=row3, pack_side='left')
        self._create_compliance_section(parent=row3, pack_side='left')
    
    def _create_efficiency_section(self, parent=None, pack_side='top'):
        """Water use efficiency KPIs"""
        parent = parent or self.scrollable_frame
        frame = ttk.LabelFrame(parent, text="Water Use Efficiency", padding=15)
        if pack_side == 'left':
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        else:
            frame.pack(fill=tk.X, pady=(0, 10))
        self.efficiency_labels = {}
        metrics = [
            ('total_efficiency', 'Total Efficiency', 'm³/tonne'),
            ('plant_efficiency', 'Plant Efficiency', 'm³/tonne'),
            ('mining_efficiency', 'Mining Efficiency', 'm³/tonne'),
            ('overall_efficiency', 'Overall Efficiency', 'm³/tonne'),
        ]
        # Grid layout 2 columns
        for idx, (key, label, unit) in enumerate(metrics):
            r = idx // 2
            c = idx % 2
            cell = ttk.Frame(frame)
            cell.grid(row=r, column=c, sticky='ew', padx=5, pady=6)
            ttk.Label(cell, text=label, font=('Segoe UI', 9)).pack(anchor='w')
            val_row = ttk.Frame(cell)
            val_row.pack(anchor='w')
            value_label = ttk.Label(val_row, text="--", font=('Segoe UI', 11, 'bold'))
            value_label.pack(side=tk.LEFT)
            ttk.Label(val_row, text=unit, foreground='#666').pack(side=tk.LEFT, padx=(6,0))
            self.efficiency_labels[key] = value_label
        for i in range(2):
            frame.columnconfigure(i, weight=1)
    
    def _create_recycling_section(self, parent=None, pack_side='top'):
        """Recycling ratio KPIs"""
        parent = parent or self.scrollable_frame
        frame = ttk.LabelFrame(parent, text="Water Recycling", padding=15)
        if pack_side == 'left':
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        else:
            frame.pack(fill=tk.X, pady=(0, 10))
        self.recycling_labels = {}
        metrics = [
            ('tsf_recycling_ratio', 'TSF Return Rate', '%'),
            ('total_recycling_ratio', 'Total Recycling Rate', '%'),
            ('fresh_water_ratio', 'Fresh Water Usage', '%'),
        ]
        for idx, (key, label, unit) in enumerate(metrics):
            cell = ttk.Frame(frame)
            cell.grid(row=0, column=idx, sticky='ew', padx=5, pady=6)
            ttk.Label(cell, text=label, font=('Segoe UI', 9)).pack(anchor='w')
            val_row = ttk.Frame(cell)
            val_row.pack(anchor='w')
            value_label = ttk.Label(val_row, text="--", font=('Segoe UI', 11, 'bold'))
            value_label.pack(side=tk.LEFT)
            ttk.Label(val_row, text=unit, foreground='#666').pack(side=tk.LEFT, padx=(6,0))
            self.recycling_labels[key] = value_label
        for i in range(len(metrics)):
            frame.columnconfigure(i, weight=1)
    
    def _create_dependency_section(self, parent=None, pack_side='top'):
        """Source dependency breakdown"""
        parent = parent or self.scrollable_frame
        frame = ttk.LabelFrame(parent, text="Water Source Dependency", padding=15)
        if pack_side == 'left':
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        else:
            frame.pack(fill=tk.X, pady=(0, 10))
        self.dependency_labels = {}
        metrics = [
            ('surface_water_pct', 'Surface Water', '%'),
            ('groundwater_pct', 'Groundwater', '%'),
            ('underground_pct', 'Underground', '%'),
            ('recycled_pct', 'Recycled Water', '%'),
            ('rainfall_pct', 'Rainfall', '%'),
            ('other_pct', 'Other Sources', '%'),
        ]
        for idx, (key, label, unit) in enumerate(metrics):
            r = idx // 3
            c = idx % 3
            cell = ttk.Frame(frame)
            cell.grid(row=r, column=c, sticky='ew', padx=5, pady=6)
            ttk.Label(cell, text=label, font=('Segoe UI', 9)).pack(anchor='w')
            val_row = ttk.Frame(cell)
            val_row.pack(anchor='w')
            value_label = ttk.Label(val_row, text="--", font=('Segoe UI', 11, 'bold'))
            value_label.pack(side=tk.LEFT)
            ttk.Label(val_row, text=unit, foreground='#666').pack(side=tk.LEFT, padx=(6,0))
            self.dependency_labels[key] = value_label
        for i in range(3):
            frame.columnconfigure(i, weight=1)
    
    def _create_security_section(self, parent=None, pack_side='top'):
        """Storage security metrics"""
        parent = parent or self.scrollable_frame
        frame = ttk.LabelFrame(parent, text="Storage Security", padding=15)
        if pack_side == 'left':
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        else:
            frame.pack(fill=tk.X, pady=(0, 10))
        self.security_labels = {}
        metrics = [
            ('days_cover', 'Days of Operation Cover', 'days'),
            ('days_to_minimum', 'Days to Minimum Level', 'days'),
            ('current_storage_m3', 'Current Storage', 'm³'),
            ('daily_consumption_m3', 'Daily Consumption', 'm³/day'),
            ('security_status', 'Security Status', ''),
        ]
        for idx, (key, label, unit) in enumerate(metrics):
            r = idx // 2
            c = idx % 2
            cell = ttk.Frame(frame)
            cell.grid(row=r, column=c, sticky='ew', padx=5, pady=6)
            ttk.Label(cell, text=label, font=('Segoe UI', 9)).pack(anchor='w')
            val_row = ttk.Frame(cell)
            val_row.pack(anchor='w')
            value_label = ttk.Label(val_row, text="--", font=('Segoe UI', 11, 'bold'))
            value_label.pack(side=tk.LEFT)
            if unit:
                ttk.Label(val_row, text=unit, foreground='#666').pack(side=tk.LEFT, padx=(6,0))
            self.security_labels[key] = value_label
        for i in range(2):
            frame.columnconfigure(i, weight=1)
    
    def _create_compliance_section(self, parent=None, pack_side='top'):
        """Compliance metrics"""
        parent = parent or self.scrollable_frame
        frame = ttk.LabelFrame(parent, text="Compliance Status", padding=15)
        if pack_side == 'left':
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        else:
            frame.pack(fill=tk.X, pady=(0, 10))
        self.compliance_labels = {}
        metrics = [
            ('overall_compliant', 'Overall Compliance', ''),
            ('overall_utilization_pct', 'Authorization Utilization', '%'),
            ('violations_count', 'Violations', 'sources'),
            ('closure_error_pct', 'Closure Error', '%'),
            ('closure_compliant', 'Balance Closed', ''),
        ]
        for idx, (key, label, unit) in enumerate(metrics):
            r = idx // 3
            c = idx % 3
            cell = ttk.Frame(frame)
            cell.grid(row=r, column=c, sticky='ew', padx=5, pady=6)
            ttk.Label(cell, text=label, font=('Segoe UI', 9)).pack(anchor='w')
            val_row = ttk.Frame(cell)
            val_row.pack(anchor='w')
            value_label = ttk.Label(val_row, text="--", font=('Segoe UI', 11, 'bold'))
            value_label.pack(side=tk.LEFT)
            if unit:
                ttk.Label(val_row, text=unit, foreground='#666').pack(side=tk.LEFT, padx=(6,0))
            self.compliance_labels[key] = value_label
        for i in range(3):
            frame.columnconfigure(i, weight=1)
    
    def _load_kpis(self):
        """Load and display all KPIs"""
        start_time = time.perf_counter()
        try:
            calc_date = datetime.strptime(self.date_var.get(), '%Y-%m-%d').date()
            
            logger.calculation("KPI calculation", str(calc_date), "Starting")
            notifier.status(f"Calculating KPIs for {calc_date}...", log=False)
            
            # Calculate all KPIs
            kpi_start = time.perf_counter()
            self.kpi_data = self.calculator.calculate_all_kpis(calc_date)
            kpi_elapsed = (time.perf_counter() - kpi_start) * 1000
            logger.performance(f"KPI calculation for {calc_date}", kpi_elapsed)
            
            # Update displays
            display_start = time.perf_counter()
            self._update_efficiency_display()
            self._update_recycling_display()
            self._update_dependency_display()
            self._update_security_display()
            self._update_compliance_display()
            display_elapsed = (time.perf_counter() - display_start) * 1000
            logger.performance("KPI display update", display_elapsed)
            
            total_elapsed = (time.perf_counter() - start_time) * 1000
            logger.calculation("KPI calculation", str(calc_date), f"Completed in {total_elapsed:.2f}ms")
            notifier.status(f"KPIs updated for {calc_date}", log=False)
            
        except ValueError as e:
            tech_msg, user_msg, severity = error_handler.handle(
                e, 
                context="KPI calculation - invalid date",
                category=ErrorCategory.VALIDATION
            )
            notifier.notify_from_error(severity, user_msg, tech_msg)
        except Exception as e:
            tech_msg, user_msg, severity = error_handler.handle(
                e, 
                context="KPI calculation",
                category=ErrorCategory.CALCULATION
            )
            notifier.notify_from_error(severity, user_msg, tech_msg)
    
    def _update_efficiency_display(self):
        """Update efficiency KPI display"""
        if not self.kpi_data:
            return
        
        efficiency = self.kpi_data['water_efficiency']
        
        for key, label in self.efficiency_labels.items():
            value = efficiency.get(key, 0)
            label.config(text=f"{value:.3f}")
            
            # Color code based on thresholds
            if value < 0.15:
                label.config(foreground='#28a745')  # Green - excellent
            elif value < 0.20:
                label.config(foreground='#007bff')  # Blue - good
            elif value < 0.25:
                label.config(foreground='#ffc107')  # Yellow - acceptable
            else:
                label.config(foreground='#dc3545')  # Red - poor
    
    def _update_recycling_display(self):
        """Update recycling KPI display"""
        if not self.kpi_data:
            return
        
        recycling = self.kpi_data['recycling']
        
        for key, label in self.recycling_labels.items():
            value = recycling.get(key, 0)
            label.config(text=f"{value:.1f}")
            
            # Color code - higher recycling is better
            if 'fresh_water' in key:
                # Inverse - lower fresh water is better
                if value < 40:
                    label.config(foreground='#28a745')
                elif value < 60:
                    label.config(foreground='#007bff')
                else:
                    label.config(foreground='#ffc107')
            else:
                # Higher recycling is better
                if value > 50:
                    label.config(foreground='#28a745')
                elif value > 30:
                    label.config(foreground='#007bff')
                else:
                    label.config(foreground='#ffc107')
    
    def _update_dependency_display(self):
        """Update source dependency display"""
        if not self.kpi_data:
            return
        
        dependency = self.kpi_data['source_dependency']
        
        for key, label in self.dependency_labels.items():
            value = dependency.get(key, 0)
            label.config(text=f"{value:.1f}")
    
    def _update_security_display(self):
        """Update storage security display"""
        if not self.kpi_data:
            return
        
        security = self.kpi_data['storage_security']
        
        for key, label in self.security_labels.items():
            if key == 'security_status':
                value = security.get(key, 'unknown').upper()
                label.config(text=value)
                
                # Color code status
                status_colors = {
                    'EXCELLENT': '#28a745',
                    'GOOD': '#007bff',
                    'ADEQUATE': '#17a2b8',
                    'LOW': '#ffc107',
                    'CRITICAL': '#dc3545'
                }
                label.config(foreground=status_colors.get(value, '#666'))
            else:
                value = security.get(key, 0)
                if 'm3' in key:
                    label.config(text=f"{value:,.0f}")
                else:
                    label.config(text=f"{value:.1f}")
                
                # Color code days cover
                if key == 'days_cover':
                    if value >= 30:
                        label.config(foreground='#28a745')
                    elif value >= 14:
                        label.config(foreground='#007bff')
                    elif value >= 7:
                        label.config(foreground='#ffc107')
                    else:
                        label.config(foreground='#dc3545')
    
    def _update_compliance_display(self):
        """Update compliance display"""
        if not self.kpi_data:
            return
        
        compliance = self.kpi_data['compliance']
        
        for key, label in self.compliance_labels.items():
            if 'compliant' in key:
                value = compliance.get(key, False)
                text = "[YES]" if value else "[NO]"
                color = '#28a745' if value else '#dc3545'
                label.config(text=text, foreground=color)
            elif key == 'violations_count':
                value = compliance.get(key, 0)
                label.config(text=str(int(value)))
                label.config(foreground='#dc3545' if value > 0 else '#28a745')
            else:
                value = compliance.get(key, 0)
                label.config(text=f"{value:.1f}")
                
                if key == 'closure_error_pct':
                    if value < 2:
                        label.config(foreground='#28a745')
                    elif value < 5:
                        label.config(foreground='#007bff')
                    else:
                        label.config(foreground='#dc3545')
    
    def refresh_data(self):
        """Refresh KPI data"""
        logger.user_action("KPI dashboard refresh")
        self._load_kpis()
