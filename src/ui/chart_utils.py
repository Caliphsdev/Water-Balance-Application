"""
Chart Utilities for Water Balance Dashboards
Matplotlib-based charting with Tkinter embedding
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from typing import Dict, List, Optional, Tuple
from datetime import date

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates


# Color palette for consistency
CHART_COLORS = {
    'inflows': '#17a2b8',      # Cyan/Blue
    'outflows': '#dc3545',     # Red
    'storage': '#28a745',      # Green
    'critical': '#fd7e14',     # Orange
    'empty': '#6c757d',        # Gray
    'recycled': '#6610f2',     # Purple
    'fresh': '#007bff',        # Primary blue
    'projection': '#ffc107',   # Yellow/Gold
    'scenario1': '#20c997',    # Teal
    'scenario2': '#e83e8c',    # Pink
    'scenario3': '#17a2b8',    # Info blue
}


def embed_matplotlib_canvas(parent_frame: tk.Frame, figure: Figure, toolbar: bool = True) -> FigureCanvasTkAgg:
    """
    Embed a matplotlib figure into a Tkinter frame.
    
    Args:
        parent_frame: Tkinter parent widget
        figure: Matplotlib Figure instance
        toolbar: Whether to show navigation toolbar
        
    Returns:
        FigureCanvasTkAgg instance
    """
    canvas = FigureCanvasTkAgg(figure, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    if toolbar:
        toolbar_frame = tk.Frame(parent_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(canvas, toolbar_frame)
    
    return canvas


def create_storage_runway_chart(projection_days: List[int], 
                                storage_levels: List[float],
                                capacity: float,
                                critical_threshold_pct: float = 25.0,
                                empty_threshold_pct: float = 0.0,
                                title: str = "Storage Depletion Projection") -> Figure:
    """
    Create storage projection chart with threshold bands.
    
    Args:
        projection_days: List of days from now (e.g., [0, 1, 2, ..., 90])
        storage_levels: Projected storage volume at each day (m³)
        capacity: Total storage capacity (m³)
        critical_threshold_pct: Critical level percentage (default 25%)
        empty_threshold_pct: Empty level percentage (default 0%)
        title: Chart title
        
    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Calculate threshold lines
    critical_line = capacity * (critical_threshold_pct / 100)
    empty_line = capacity * (empty_threshold_pct / 100)
    
    # Plot storage projection
    ax.plot(projection_days, storage_levels, linewidth=2.5, color=CHART_COLORS['storage'], 
            label='Projected Storage', marker='o', markersize=4, markevery=max(1, len(projection_days)//20))
    
    # Add threshold lines
    ax.axhline(y=capacity, color=CHART_COLORS['fresh'], linestyle='--', linewidth=1.5, 
               alpha=0.7, label=f'Full Capacity ({capacity:,.0f} m³)')
    ax.axhline(y=critical_line, color=CHART_COLORS['critical'], linestyle='--', linewidth=1.5,
               alpha=0.7, label=f'Critical ({critical_threshold_pct}%)')
    ax.axhline(y=empty_line, color=CHART_COLORS['empty'], linestyle='--', linewidth=1.5,
               alpha=0.7, label=f'Empty ({empty_threshold_pct}%)')
    
    # Add shaded threshold bands
    ax.fill_between(projection_days, critical_line, capacity, alpha=0.1, color='green', label='Safe Zone')
    ax.fill_between(projection_days, empty_line, critical_line, alpha=0.1, color='orange', label='Warning Zone')
    ax.fill_between(projection_days, 0, empty_line, alpha=0.1, color='red', label='Critical Zone')
    
    ax.set_xlabel('Days from Now', fontsize=11, fontweight='bold')
    ax.set_ylabel('Storage Volume (m³)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='best', fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    fig.tight_layout()
    return fig


def create_trends_chart(dates: List[date], 
                        series_dict: Dict[str, List[float]],
                        ylabel: str = 'Volume (m³)',
                        title: str = 'Water Balance Trends',
                        show_legend: bool = True) -> Figure:
    """
    Create multi-line trend chart.
    
    Args:
        dates: List of dates for x-axis
        series_dict: Dictionary of {series_name: [values]}
        ylabel: Y-axis label
        title: Chart title
        show_legend: Whether to display legend
        
    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each series
    for series_name, values in series_dict.items():
        color = CHART_COLORS.get(series_name.lower(), None)
        linestyle = '-' if 'storage' not in series_name.lower() else '--'
        ax.plot(dates, values, label=series_name, linewidth=2, color=color, 
                linestyle=linestyle, marker='o', markersize=3)
    
    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    
    if show_legend:
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
    
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(dates)//12)))
    fig.autofmt_xdate()
    
    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    fig.tight_layout()
    return fig


def create_outflow_breakdown_chart(dates: List[date],
                                   breakdown_dict: Dict[str, List[float]],
                                   title: str = 'Outflow Breakdown') -> Figure:
    """
    Create stacked bar chart for outflow categories.
    
    Args:
        dates: List of dates for x-axis
        breakdown_dict: Dictionary of {category: [values_per_date]}
        title: Chart title
        
    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Prepare data for stacking
    categories = list(breakdown_dict.keys())
    values_matrix = [breakdown_dict[cat] for cat in categories]
    
    # Create stacked bars
    bottom = [0] * len(dates)
    colors = plt.cm.Set3.colors  # Use colormap for variety
    
    for i, (category, values) in enumerate(zip(categories, values_matrix)):
        ax.bar(dates, values, bottom=bottom, label=category, 
               color=colors[i % len(colors)], edgecolor='white', linewidth=0.5)
        bottom = [b + v for b, v in zip(bottom, values)]
    
    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Volume (m³)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=9)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8, axis='y')
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(dates)//12)))
    fig.autofmt_xdate()
    
    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    fig.tight_layout()
    return fig


def create_scenario_comparison_chart(scenario_results: Dict[str, Dict],
                                     title: str = 'Scenario Comparison - Storage Projection') -> Figure:
    """
    Create overlay chart comparing multiple scenarios.
    
    Args:
        scenario_results: Dict of {scenario_name: {'months': [0,1,2,...], 'storage': [values]}}
        title: Chart title
        
    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Define distinct colors for scenarios
    scenario_colors = [CHART_COLORS['scenario1'], CHART_COLORS['scenario2'], 
                       CHART_COLORS['scenario3'], CHART_COLORS['critical'], 
                       CHART_COLORS['projection']]
    
    for i, (scenario_name, data) in enumerate(scenario_results.items()):
        months = data['months']
        storage = data['storage']
        color = scenario_colors[i % len(scenario_colors)]
        linestyle = '-' if scenario_name.lower() == 'baseline' else '--'
        linewidth = 2.5 if scenario_name.lower() == 'baseline' else 2.0
        
        ax.plot(months, storage, label=scenario_name, linewidth=linewidth, 
                color=color, linestyle=linestyle, marker='o', markersize=4)
    
    ax.set_xlabel('Months from Now', fontsize=11, fontweight='bold')
    ax.set_ylabel('Storage Volume (m³)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    fig.tight_layout()
    return fig


def add_threshold_bands(ax, critical_y: float, empty_y: float, max_y: float):
    """
    Add colored threshold bands to an existing axis.
    
    Args:
        ax: Matplotlib axis object
        critical_y: Y-value for critical threshold
        empty_y: Y-value for empty threshold
        max_y: Maximum Y-value (full capacity)
    """
    ax.fill_between(ax.get_xlim(), critical_y, max_y, alpha=0.1, color='green', label='Safe Zone')
    ax.fill_between(ax.get_xlim(), empty_y, critical_y, alpha=0.1, color='orange', label='Warning Zone')
    ax.fill_between(ax.get_xlim(), 0, empty_y, alpha=0.1, color='red', label='Critical Zone')


def create_efficiency_chart(dates: List[date],
                            efficiency_values: List[float],
                            metric_name: str = 'Water Use Efficiency (m³/tonne)',
                            title: str = 'Water Use Efficiency Trend') -> Figure:
    """
    Create line chart for efficiency metrics.
    
    Args:
        dates: List of dates
        efficiency_values: Efficiency metric values
        metric_name: Name of the metric
        title: Chart title
        
    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(dates, efficiency_values, linewidth=2.5, color=CHART_COLORS['fresh'],
            marker='o', markersize=5, label=metric_name)
    
    # Add average line
    avg = sum(efficiency_values) / len(efficiency_values) if efficiency_values else 0
    ax.axhline(y=avg, color=CHART_COLORS['critical'], linestyle='--', 
               linewidth=1.5, alpha=0.7, label=f'Average: {avg:.2f}')
    
    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel(metric_name, fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate()
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    
    fig.tight_layout()
    return fig
