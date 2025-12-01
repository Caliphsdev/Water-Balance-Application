"""Chart Style Utilities
Provides centralized professional color palettes and styling helpers for matplotlib charts.
"""
from matplotlib import cm, colors

PRIMARY_PALETTE = [
    '#0D47A1', '#1565C0', '#1976D2', '#1E88E5', '#2196F3', '#42A5F5'
]
ACCENT_PALETTE = [
    '#00695C', '#00897B', '#00ACC1', '#26C6DA', '#4DD0E1'
]
WARM_PALETTE = [
    '#BF360C', '#D84315', '#E64A19', '#F4511E', '#FF5722', '#FF7043'
]
NEUTRAL_BG = '#FAFAFA'
GRID_COLOR = '#E0E0E0'
FONT_FAMILY = 'DejaVu Sans'


def gradient_cmap(base='#2196F3'):
    return colors.LinearSegmentedColormap.from_list('custom_grad', [colors.to_rgba(base, 0.9), colors.to_rgba('#BBDEFB', 0.9)])


def apply_common_style(ax, title: str):
    ax.set_title(title, fontsize=12, pad=12, fontweight='bold')
    ax.grid(axis='y', color=GRID_COLOR, alpha=0.4, linestyle='--', linewidth=0.6)
    ax.set_facecolor('white')
    for spine in ['top','right']:
        ax.spines[spine].set_visible(False)


def color_by_threshold(values, threshold, low_color='#43A047', high_color='#E53935'):
    return [high_color if v > threshold else low_color for v in values]


def annotate_barh(ax, bars, fmt='{:.2f}'):    
    for b in bars:
        w = b.get_width()
        ax.text(w + max(ax.get_xlim())*0.01, b.get_y()+b.get_height()/2, fmt.format(w), va='center', fontsize=9)


def annotate_bar(ax, bars, fmt='{:.2f}'):    
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h, fmt.format(h), ha='center', va='bottom', fontsize=9)
