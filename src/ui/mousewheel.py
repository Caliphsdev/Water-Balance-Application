"""Cross-platform mouse wheel scrolling utility.

Provides functions to attach mouse wheel scrolling behavior to scrollable
widgets (Canvas, Text, Treeview, Listbox) across Windows, macOS, and Linux.

Usage:
    from ui.mousewheel import apply_mousewheel_recursive
    apply_mousewheel_recursive(root_container)

This binds scroll events only while the pointer is inside a widget to avoid
interference with other input areas.
"""

from __future__ import annotations

import platform
import tkinter as tk
from tkinter import ttk


_SYSTEM = platform.system().lower()


def _bind_widget_mousewheel(widget, yview_target):
    """Bind mousewheel events to a widget using the provided yview target."""
    def _on_mousewheel(event):
        if _SYSTEM in ('windows', 'darwin'):
            # event.delta is multiple of 120 typically
            yview_target.yview_scroll(int(-event.delta / 120), 'units')
        # Linux handled via Button-4/5

    def _on_linux_up(_event):
        yview_target.yview_scroll(-1, 'units')

    def _on_linux_down(_event):
        yview_target.yview_scroll(1, 'units')

    def _activate(_event=None):
        if _SYSTEM in ('windows', 'darwin'):
            widget.bind_all('<MouseWheel>', _on_mousewheel, add='+')
        else:
            widget.bind_all('<Button-4>', _on_linux_up, add='+')
            widget.bind_all('<Button-5>', _on_linux_down, add='+')

    def _deactivate(_event=None):
        if _SYSTEM in ('windows', 'darwin'):
            widget.unbind_all('<MouseWheel>')
        else:
            widget.unbind_all('<Button-4>')
            widget.unbind_all('<Button-5>')

    widget.bind('<Enter>', _activate, add='+')
    widget.bind('<Leave>', _deactivate, add='+')


def enable_mousewheel(widget):
    """Enable mousewheel scrolling directly on a widget if it supports yview."""
    if hasattr(widget, 'yview'):
        _bind_widget_mousewheel(widget, widget)


def apply_mousewheel_recursive(root):
    """Recursively apply mouse wheel bindings to scrollable widgets under root."""
    for child in root.winfo_children():
        # Widgets with yview capability (Canvas, Text, Listbox, Treeview, etc.)
        if hasattr(child, 'yview'):
            enable_mousewheel(child)
        # Treeview might have an internal yview
        if isinstance(child, ttk.Treeview):
            enable_mousewheel(child)
        # Recurse
        apply_mousewheel_recursive(child)


__all__ = ['enable_mousewheel', 'apply_mousewheel_recursive']
