"""UI components package.

Reusable custom widgets (charts, KPI cards, flow diagrams, tables, etc.).
Components can be used across multiple dashboards and dialogs.
"""

from .flow_graphics_items import FlowNodeItem, FlowEdgeItem
from .excel_preview_widget import ExcelPreviewWidget

__all__ = ["FlowNodeItem", "FlowEdgeItem", "ExcelPreviewWidget"]
