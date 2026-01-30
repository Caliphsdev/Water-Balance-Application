"""
Monitoring Dashboard - Tkinter UI Component

Displays monitoring data from configured sources.

Features:
- Source tabs (borehole_static, borehole_monitoring, pcd_monitoring, etc.)
- Data table with sorting/filtering
- Charts (line, area) - REUSE chart_utils.embed_matplotlib_canvas()
- Loading indicator - REUSE LoadingIndicator
- Error display
- Refresh button

Architecture:
1. UI created with Tkinter Notebook (tabs per source)
2. Each tab has: Data table, Charts, Status
3. Load button triggers async loader
4. Background thread parses Excel files
5. Results displayed in table + chart
6. Errors shown in status frame

REUSE from existing app:
- chart_utils.embed_matplotlib_canvas()
- LoadingIndicator animation
- AsyncDatabaseLoader pattern (threading)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Optional, Dict, List
import threading

from models.monitoring_data import DataSourceDefinition
from services.monitoring_data_loader import MonitoringDataLoader
from utils.config_manager import config
from utils.app_logger import logger

# Try to import existing UI utilities
try:
    from ui.chart_utils import embed_matplotlib_canvas
    HAS_CHART_UTILS = True
except ImportError:
    HAS_CHART_UTILS = False
    logger.warning("chart_utils not available - charts disabled")

try:
    from ui.loading_indicator import LoadingIndicator
    HAS_LOADING_INDICATOR = True
except ImportError:
    HAS_LOADING_INDICATOR = False
    logger.warning("loading_indicator not available - using simple spinner")


# ============================================================================
# MONITORING DATA TAB
# ============================================================================

class MonitoringDataTab(ttk.Frame):
    """
    Single monitoring data source tab.
    
    Display:
    - Data table with search
    - Charts
    - Loading indicator
    - Error messages
    """
    
    def __init__(self, parent: ttk.Notebook, source_def: DataSourceDefinition):
        """
        Initialize tab for monitoring source.
        
        Args:
            parent: Parent Notebook widget
            source_def: Data source configuration
        """
        super().__init__(parent)
        
        self.source_def = source_def
        self.loader: Optional[MonitoringDataLoader] = None
        self.data: Optional[pd.DataFrame] = None
        
        self._create_widgets()
        
        logger.info(f"✓ Tab created: {source_def.name}")
    
    def _create_widgets(self):
        """Create UI components"""
        
        # ===== HEADER (buttons, status) =====
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        # Load button
        self.btn_load = ttk.Button(
            header,
            text=f"Load {self.source_def.name}",
            command=self._on_load
        )
        self.btn_load.pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.lbl_status = ttk.Label(header, textvariable=self.status_var)
        self.lbl_status.pack(side=tk.LEFT, padx=10)
        
        # Progress spinner (placeholder - will be replaced if loading indicator available)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            header,
            variable=self.progress_var,
            mode='indeterminate'
        )
        self.progress.pack(side=tk.LEFT, padx=5)
        
        # ===== PANED WINDOW (table + chart) =====
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ----- TABLE FRAME -----
        table_frame = ttk.LabelFrame(paned, text="Data")
        paned.add(table_frame, weight=1)
        
        # Search box
        search_frame = ttk.Frame(table_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind('<KeyRelease>', self._on_search)
        
        # Treeview (table)
        self.tree = ttk.Treeview(table_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=vsb.set)
        
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscroll=hsb.set)
        
        # ----- CHART FRAME -----
        if HAS_CHART_UTILS:
            self.chart_frame = ttk.LabelFrame(paned, text="Chart", width=400, height=300)
            paned.add(self.chart_frame, weight=1)
            self.canvas = None
        else:
            self.chart_frame = None
        
        # ===== ERROR FRAME (collapsible) =====
        error_frame = ttk.LabelFrame(self, text="Errors", height=100)
        error_frame.pack(fill=tk.X, padx=5, pady=5)
        error_frame.pack_propagate(False)
        
        self.text_errors = tk.Text(error_frame, height=5, wrap=tk.WORD)
        self.text_errors.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for errors
        esb = ttk.Scrollbar(error_frame, orient=tk.VERTICAL, command=self.text_errors.yview)
        esb.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_errors.configure(yscroll=esb.set)
    
    def _on_load(self):
        """Load data (async)"""
        
        self.btn_load.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Loading...")
        
        # Create loader
        self.loader = MonitoringDataLoader(self.source_def)
        
        # Start async load
        self.loader.load_async(on_complete=self._on_load_complete)
    
    def _on_load_complete(self, loader: MonitoringDataLoader, result, error: Optional[str]):
        """Called when async load completes"""
        
        self.progress.stop()
        self.btn_load.config(state=tk.NORMAL)
        
        if error:
            self.status_var.set(f"Error: {error}")
            self.text_errors.delete('1.0', tk.END)
            self.text_errors.insert(tk.END, error)
            messagebox.showerror("Load Error", error)
            return
        
        # Get data
        self.data = loader.get_dataframe()
        stats = loader.get_statistics()
        
        self.status_var.set(
            f"{stats['total_records']} records from {stats['files_scanned']} files "
            f"({stats['total_time_ms']})"
        )
        
        # Display table
        self._display_table()
        
        # Display chart if available
        if HAS_CHART_UTILS and self.chart_frame and len(self.data) > 0:
            self._display_chart()
        
        # Display errors (if any)
        if result.total_errors > 0:
            errors_text = "Parsing Errors:\n\n"
            for file_result in result.file_results:
                if file_result.errors:
                    errors_text += f"{file_result.file_path}:\n"
                    for error_msg in file_result.errors[:5]:  # Show first 5
                        errors_text += f"  - {error_msg}\n"
            
            self.text_errors.delete('1.0', tk.END)
            self.text_errors.insert(tk.END, errors_text)
    
    def _display_table(self):
        """Populate Treeview with data"""
        
        if self.data is None or len(self.data) == 0:
            self.tree.delete(*self.tree.get_children())
            return
        
        # Define columns
        columns = list(self.data.columns)
        self.tree['columns'] = columns
        self.tree.column('#0', width=0, stretch=tk.NO)
        
        for col in columns:
            self.tree.column(col, anchor=tk.W, width=100)
            self.tree.heading(col, text=col)
        
        # Add rows
        for idx, row in self.data.iterrows():
            values = [str(row[col]) for col in columns]
            self.tree.insert('', 'end', values=values)
        
        logger.debug(f"Table displayed: {len(self.data)} rows, {len(columns)} columns")
    
    def _display_chart(self):
        """Display line chart of numerical data over time"""
        
        if not HAS_CHART_UTILS or not self.data or len(self.data) == 0:
            return
        
        try:
            # Find numerical columns
            numerical_cols = self.data.select_dtypes(include=['number']).columns.tolist()
            
            if not numerical_cols:
                logger.warning("No numerical columns for chart")
                return
            
            # Create chart
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(5, 3))
            
            # Plot first 3 numerical columns
            for col in numerical_cols[:3]:
                ax.plot(self.data.index, self.data[col], marker='o', label=col, alpha=0.7)
            
            ax.set_xlabel("Measurement")
            ax.set_ylabel("Value")
            ax.set_title(f"{self.source_def.name} Trends")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Embed in Tkinter
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            self.canvas = embed_matplotlib_canvas(fig, self.chart_frame)
            
            logger.info("Chart displayed")
        
        except Exception as e:
            logger.error(f"Chart error: {e}")
    
    def _on_search(self, event):
        """Filter table based on search string"""
        
        if not self.data or len(self.data) == 0:
            return
        
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self._display_table()
            return
        
        # Filter data
        mask = self.data.astype(str).apply(lambda x: x.str.contains(search_text)).any(axis=1)
        filtered = self.data[mask]
        
        # Display filtered
        self.tree.delete(*self.tree.get_children())
        for idx, row in filtered.iterrows():
            values = [str(row[col]) for col in self.data.columns]
            self.tree.insert('', 'end', values=values)


# ============================================================================
# MONITORING DASHBOARD (MAIN WIDGET)
# ============================================================================

class MonitoringDashboard(ttk.Frame):
    """
    Main monitoring data dashboard.
    
    Features:
    - Multiple tabs (one per monitoring source)
    - Each tab displays: data table + chart + errors
    - Search/filter per tab
    - Async loading from Excel directories
    
    Usage:
        app = tk.Tk()
        dashboard = MonitoringDashboard(app)
        dashboard.pack(fill=tk.BOTH, expand=True)
        app.mainloop()
    """
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize dashboard.
        
        Args:
            parent: Parent Tkinter widget
        """
        super().__init__(parent)
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Load sources from config
        self.tabs: Dict[str, MonitoringDataTab] = {}
        self._create_tabs()
        
        logger.info("✓ Monitoring dashboard created")
    
    def _create_tabs(self):
        """Create tabs for each enabled monitoring source"""
        
        # Load all sources from config
        try:
            from models.monitoring_data import DataSourceDefinition
            import yaml
            
            config_path = Path('config/monitoring_data_sources.yaml')
            if not config_path.exists():
                logger.warning(f"Config not found: {config_path}")
                return
            
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            
            sources = config_data.get('sources', [])
            
            for source_dict in sources:
                # Create source definition
                source_def = DataSourceDefinition(**source_dict)
                
                # Skip disabled sources
                if not source_dict.get('enabled', True):
                    logger.debug(f"Skipping disabled source: {source_def.id}")
                    continue
                
                # Create tab
                tab = MonitoringDataTab(self.notebook, source_def)
                self.notebook.add(tab, text=source_def.name)
                self.tabs[source_def.id] = tab
                
                logger.info(f"✓ Tab added: {source_def.name}")
        
        except Exception as e:
            logger.error(f"Tab creation error: {e}", exc_info=True)
            messagebox.showerror("Configuration Error", f"Failed to load sources: {e}")


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    """Test dashboard"""
    
    root = tk.Tk()
    root.title("Monitoring Dashboard")
    root.geometry("1200x700")
    
    dashboard = MonitoringDashboard(root)
    dashboard.pack(fill=tk.BOTH, expand=True)
    
    print("✅ Dashboard test window ready")
    print("Click 'Load' buttons to parse Excel files\n")
    
    root.mainloop()

