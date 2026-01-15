"""
Data Quality Manager UI
Manage missing measurements, historical averaging, and data quality
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import DatabaseManager
from utils.historical_averaging import HistoricalAveraging


class DataQualityManager(ttk.Frame):
    """UI for data quality management and gap filling"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.ha = HistoricalAveraging(self.db)
        
        self.setup_ui()
        self.refresh_quality_report()
    
    def setup_ui(self):
        """Setup the UI layout"""
        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill='x', padx=10, pady=10)
        
        title = ttk.Label(
            title_frame,
            text="📊 Data Quality Manager",
            font=('Arial', 16, 'bold')
        )
        title.pack(side='left')
        
        # Period selection
        period_frame = ttk.LabelFrame(self, text="Analysis Period", padding=10)
        period_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(period_frame, text="From:").grid(row=0, column=0, sticky='w', padx=5)
        self.start_date_var = tk.StringVar(value=(date.today() - timedelta(days=365)).isoformat())
        self.start_date_entry = ttk.Entry(period_frame, textvariable=self.start_date_var, width=15)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(period_frame, text="To:").grid(row=0, column=2, sticky='w', padx=5)
        self.end_date_var = tk.StringVar(value=date.today().isoformat())
        self.end_date_entry = ttk.Entry(period_frame, textvariable=self.end_date_var, width=15)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(
            period_frame,
            text="🔄 Refresh",
            command=self.refresh_quality_report
        ).grid(row=0, column=4, padx=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Quality Report
        self.quality_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.quality_tab, text="📈 Quality Report")
        self.setup_quality_tab()
        
        # Tab 2: Gap Filling
        self.gap_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.gap_tab, text="🔧 Fill Missing Data")
        self.setup_gap_tab()
        
        # Tab 3: Estimation Methods
        self.methods_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.methods_tab, text="⚙️ Estimation Methods")
        self.setup_methods_tab()
    
    def setup_quality_tab(self):
        """Setup quality report tab"""
        # Summary section
        summary_frame = ttk.LabelFrame(self.quality_tab, text="📊 Overall Quality", padding=10)
        summary_frame.pack(fill='x', padx=10, pady=10)
        
        self.total_measurements_label = ttk.Label(summary_frame, text="Total Measurements: -")
        self.total_measurements_label.pack(anchor='w', pady=2)
        
        self.quality_score_label = ttk.Label(summary_frame, text="Quality Score: -")
        self.quality_score_label.pack(anchor='w', pady=2)
        
        self.quality_rating_label = ttk.Label(summary_frame, text="Rating: -")
        self.quality_rating_label.pack(anchor='w', pady=2)
        
        # Breakdown section
        breakdown_frame = ttk.LabelFrame(self.quality_tab, text="📊 Quality Breakdown", padding=10)
        breakdown_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create treeview for breakdown
        columns = ('Category', 'Count', 'Percentage', 'Avg Volume')
        self.quality_tree = ttk.Treeview(breakdown_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.quality_tree.heading(col, text=col)
            self.quality_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(breakdown_frame, orient='vertical', command=self.quality_tree.yview)
        self.quality_tree.configure(yscrollcommand=scrollbar.set)
        
        self.quality_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Recommendations
        rec_frame = ttk.LabelFrame(self.quality_tab, text="💡 Recommendations", padding=10)
        rec_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.recommendations_text = tk.Text(rec_frame, height=4, wrap='word', state='disabled')
        self.recommendations_text.pack(fill='x')
    
    def setup_gap_tab(self):
        """Setup gap filling tab"""
        # Configuration
        config_frame = ttk.LabelFrame(self.gap_tab, text="⚙️ Configuration", padding=10)
        config_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(config_frame, text="Window (months):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.window_var = tk.StringVar(value="12")
        ttk.Entry(config_frame, textvariable=self.window_var, width=10).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(config_frame, text="Method:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.method_var = tk.StringVar(value="weighted")
        methods = ttk.Combobox(
            config_frame,
            textvariable=self.method_var,
            values=['average', 'median', 'weighted', 'seasonal'],
            state='readonly',
            width=15
        )
        methods.grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(config_frame, text="Sources:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.sources_var = tk.StringVar(value="all")
        sources_opt = ttk.Combobox(
            config_frame,
            textvariable=self.sources_var,
            values=['all', 'specific'],
            state='readonly',
            width=15
        )
        sources_opt.grid(row=2, column=1, sticky='w', padx=5)
        
        # Actions
        action_frame = ttk.Frame(self.gap_tab)
        action_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(
            action_frame,
            text="🔍 Preview Gap Filling",
            command=self.preview_gap_filling
        ).pack(side='left', padx=5)
        
        ttk.Button(
            action_frame,
            text="✅ Apply Gap Filling",
            command=self.apply_gap_filling
        ).pack(side='left', padx=5)
        
        # Results
        results_frame = ttk.LabelFrame(self.gap_tab, text="📊 Preview Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.gap_results_text = tk.Text(results_frame, height=15, wrap='word', state='disabled')
        gap_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.gap_results_text.yview)
        self.gap_results_text.configure(yscrollcommand=gap_scrollbar.set)
        
        self.gap_results_text.pack(side='left', fill='both', expand=True)
        gap_scrollbar.pack(side='right', fill='y')
    
    def setup_methods_tab(self):
        """Setup estimation methods comparison tab"""
        info_frame = ttk.LabelFrame(self.methods_tab, text="ℹ️ Estimation Methods", padding=10)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        info_text = """
AVERAGE (Excel: =AVERAGE)
• Simple arithmetic mean of historical values
• Best for: Stable sources with consistent flow
• Excel pattern: =AVERAGE(U144:U165)

MEDIAN (Excel: =MEDIAN)
• Middle value of historical dataset
• Best for: Sources with outliers or spikes
• More robust to extreme values

WEIGHTED (Recommended)
• Recent data weighted more heavily
• Best for: Trending sources
• Excel pattern: Recent months have higher weight

SEASONAL (Excel: Same Month)
• Average of same month in previous years
• Best for: Seasonal sources (rainfall, rivers)
• Excel pattern: =AVERAGE(Jan2020, Jan2019, Jan2018)
        """
        
        info_label = ttk.Label(info_frame, text=info_text.strip(), justify='left')
        info_label.pack(anchor='w')
        
        # Test comparison
        test_frame = ttk.LabelFrame(self.methods_tab, text="🧪 Test Methods", padding=10)
        test_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        ttk.Label(test_frame, text="Source:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        sources = self.db.get_water_sources(active_only=True)
        source_names = [f"{s['source_name']} (ID: {s['source_id']})" for s in sources]
        
        self.test_source_var = tk.StringVar(master=test_frame)
        test_source = ttk.Combobox(
            test_frame,
            textvariable=self.test_source_var,
            values=source_names,
            state='readonly',
            width=40
        )
        test_source.grid(row=0, column=1, sticky='w', padx=5)
        if source_names:
            test_source.current(0)
        
        ttk.Label(test_frame, text="Date:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.test_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(test_frame, textvariable=self.test_date_var, width=20).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Button(
            test_frame,
            text="🔬 Compare Methods",
            command=self.compare_methods
        ).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Comparison results
        columns = ('Method', 'Value', 'Confidence', 'Data Points', 'Quality')
        self.methods_tree = ttk.Treeview(test_frame, columns=columns, show='headings', height=6)
        
        for col in columns:
            self.methods_tree.heading(col, text=col)
            self.methods_tree.column(col, width=120)
        
        self.methods_tree.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
    
    def refresh_quality_report(self):
        """Refresh the quality report"""
        try:
            start_date = date.fromisoformat(self.start_date_var.get())
            end_date = date.fromisoformat(self.end_date_var.get())
            
            report = self.ha.get_data_quality_report(start_date, end_date)
            
            # Update summary
            self.total_measurements_label.config(
                text=f"Total Measurements: {report['total_measurements']:,}"
            )
            self.quality_score_label.config(
                text=f"Quality Score: {report['overall_quality_score']:.1%}",
                foreground=self._get_score_color(report['overall_quality_score'])
            )
            self.quality_rating_label.config(
                text=f"Rating: {report['quality_rating']}",
                foreground=self._get_score_color(report['overall_quality_score'])
            )
            
            # Update breakdown
            self.quality_tree.delete(*self.quality_tree.get_children())
            
            emojis = {'good': '✅', 'estimated': '📊', 'interpolated': '📉', 'default': '⚠️'}
            for flag, data in report['quality_breakdown'].items():
                emoji = emojis.get(flag, '❓')
                self.quality_tree.insert('', 'end', values=(
                    f"{emoji} {flag.upper()}",
                    f"{data['count']:,}",
                    f"{data['percentage']:.1f}%",
                    f"{data['avg_volume']:,.0f} m³"
                ))
            
            # Update recommendations
            self.recommendations_text.config(state='normal')
            self.recommendations_text.delete('1.0', 'end')
            
            score = report['overall_quality_score']
            if score >= 0.9:
                rec = "✅ Excellent data quality. High confidence in water balance calculations."
            elif score >= 0.75:
                rec = "✅ Good data quality. Water balance results are reliable."
            elif score >= 0.6:
                rec = "⚠️  Acceptable quality. Consider collecting more measured data."
            elif score >= 0.4:
                rec = "⚠️  Poor quality. Significant reliance on estimates - measurements needed."
            else:
                rec = "❌ Critical quality issues. Urgent data collection required."
            
            self.recommendations_text.insert('1.0', rec)
            self.recommendations_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh quality report:\n{e}")
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on quality score"""
        if score >= 0.9:
            return '#27ae60'  # Green
        elif score >= 0.75:
            return '#3498db'  # Blue
        elif score >= 0.6:
            return '#f39c12'  # Orange
        else:
            return '#e74c3c'  # Red
    
    def preview_gap_filling(self):
        """Preview gap filling results"""
        try:
            start_date = date.fromisoformat(self.start_date_var.get())
            end_date = date.fromisoformat(self.end_date_var.get())
            
            result = self.ha.fill_missing_measurements(
                start_date=start_date,
                end_date=end_date,
                dry_run=True
            )
            
            # Display results
            self.gap_results_text.config(state='normal')
            self.gap_results_text.delete('1.0', 'end')
            
            output = f"""DRY RUN PREVIEW
{'=' * 70}

Period: {result['date_range']}
Sources Processed: {result['sources_processed']}
Total Estimates: {result['total_estimates']}
Would Fill: {result['filled_count']} measurements

Sample Estimates (first 10):
{'-' * 70}
"""
            
            for i, est in enumerate(result['estimates'][:10], 1):
                output += f"\n{i}. {est['date']} - Source {est['source_id']}\n"
                output += f"   Value: {est['estimated_value']:,.2f} m³\n"
                output += f"   Quality: {est['quality_flag']} (confidence: {est['confidence']:.1%})\n"
                output += f"   Data Points: {est['data_points_used']}\n"
            
            if len(result['estimates']) > 10:
                output += f"\n... and {len(result['estimates']) - 10} more estimates\n"
            
            self.gap_results_text.insert('1.0', output)
            self.gap_results_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview gap filling:\n{e}")
    
    def apply_gap_filling(self):
        """Apply gap filling to database"""
        if not messagebox.askyesno(
            "Confirm",
            "This will add estimated measurements to the database.\n\n"
            "Are you sure you want to proceed?"
        ):
            return
        
        try:
            start_date = date.fromisoformat(self.start_date_var.get())
            end_date = date.fromisoformat(self.end_date_var.get())
            
            result = self.ha.fill_missing_measurements(
                start_date=start_date,
                end_date=end_date,
                dry_run=False
            )
            
            messagebox.showinfo(
                "Success",
                f"✅ Gap filling complete!\n\n"
                f"Filled {result['filled_count']} missing measurements.\n"
                f"Period: {result['date_range']}"
            )
            
            # Refresh quality report
            self.refresh_quality_report()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply gap filling:\n{e}")
    
    def compare_methods(self):
        """Compare estimation methods"""
        try:
            # Extract source ID from selection
            source_text = self.test_source_var.get()
            if not source_text:
                messagebox.showwarning("Warning", "Please select a source")
                return
            
            source_id = int(source_text.split('ID: ')[1].rstrip(')'))
            test_date = date.fromisoformat(self.test_date_var.get())
            
            # Clear existing results
            self.methods_tree.delete(*self.methods_tree.get_children())
            
            # Test each method
            methods = ['average', 'median', 'weighted', 'seasonal']
            for method in methods:
                estimate = self.ha.estimate_missing_value(
                    source_id=source_id,
                    measurement_date=test_date,
                    measurement_type='inflow',
                    window_months=12,
                    method=method
                )
                
                self.methods_tree.insert('', 'end', values=(
                    method.upper(),
                    f"{estimate['estimated_value']:,.2f} m³",
                    f"{estimate['confidence']:.0%}",
                    estimate['data_points_used'],
                    estimate['quality_flag']
                ))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to compare methods:\n{e}")
