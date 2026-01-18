"""
Mouse wheel scrolling support for Tkinter widgets.
Provides cross-platform (Windows, Linux) mouse wheel scrolling for Canvas, Text, Listbox, and Treeview widgets.
"""

def enable_canvas_mousewheel(canvas):
    """
    Enable mouse wheel scrolling on a Tkinter Canvas widget.
    
    Supports:
    - Windows: MouseWheel events
    - Linux: Button-4 (scroll up) and Button-5 (scroll down)
    
    Args:
        canvas: tk.Canvas widget to enable mouse wheel scrolling on
    """
    def _on_mousewheel(event):
        """Handle mouse wheel scroll events."""
        # event.delta is positive for scroll up, negative for scroll down (Windows)
        # On Linux, we handle Button-4 and Button-5 separately
        if hasattr(event, 'delta'):
            scroll_amount = -1 * (event.delta // 120)
        elif event.num == 4:
            scroll_amount = -1  # Scroll up
        elif event.num == 5:
            scroll_amount = 1   # Scroll down
        else:
            return
        canvas.yview_scroll(scroll_amount, "units")
    
    # Bind mouse wheel events
    canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
    canvas.bind("<Button-4>", _on_mousewheel)    # Linux scroll up
    canvas.bind("<Button-5>", _on_mousewheel)    # Linux scroll down


def enable_text_mousewheel(text_widget):
    """
    Enable mouse wheel scrolling on a Tkinter Text widget.
    
    Supports:
    - Windows: MouseWheel events
    - Linux: Button-4 (scroll up) and Button-5 (scroll down)
    
    Args:
        text_widget: tk.Text widget to enable mouse wheel scrolling on
    """
    def _on_mousewheel(event):
        """Handle mouse wheel scroll events."""
        if hasattr(event, 'delta'):
            scroll_amount = -1 * (event.delta // 120)
        elif event.num == 4:
            scroll_amount = -1
        elif event.num == 5:
            scroll_amount = 1
        else:
            return
        text_widget.yview_scroll(scroll_amount, "units")
    
    text_widget.bind("<MouseWheel>", _on_mousewheel)
    text_widget.bind("<Button-4>", _on_mousewheel)
    text_widget.bind("<Button-5>", _on_mousewheel)


def enable_listbox_mousewheel(listbox):
    """
    Enable mouse wheel scrolling on a Tkinter Listbox widget.
    
    Supports:
    - Windows: MouseWheel events
    - Linux: Button-4 (scroll up) and Button-5 (scroll down)
    
    Args:
        listbox: tk.Listbox widget to enable mouse wheel scrolling on
    """
    def _on_mousewheel(event):
        """Handle mouse wheel scroll events."""
        if hasattr(event, 'delta'):
            scroll_amount = -1 * (event.delta // 120)
        elif event.num == 4:
            scroll_amount = -1
        elif event.num == 5:
            scroll_amount = 1
        else:
            return
        listbox.yview_scroll(scroll_amount, "units")
    
    listbox.bind("<MouseWheel>", _on_mousewheel)
    listbox.bind("<Button-4>", _on_mousewheel)
    listbox.bind("<Button-5>", _on_mousewheel)


def enable_treeview_mousewheel(treeview):
    """
    Enable mouse wheel scrolling on a ttk.Treeview widget.
    
    Supports:
    - Windows: MouseWheel events
    - Linux: Button-4 (scroll up) and Button-5 (scroll down)
    
    Args:
        treeview: ttk.Treeview widget to enable mouse wheel scrolling on
    """
    def _on_mousewheel(event):
        """Handle mouse wheel scroll events."""
        # Windows provides delta, Linux uses Button-4/5
        if hasattr(event, 'delta'):
            scroll_amount = -1 * (event.delta // 120)
        elif event.num == 4:
            scroll_amount = -1
        elif event.num == 5:
            scroll_amount = 1
        else:
            return
        try:
            treeview.yview_scroll(scroll_amount, "units")
        except Exception:
            # If treeview was destroyed, ignore
            pass
    
    treeview.bind("<MouseWheel>", _on_mousewheel)
    treeview.bind("<Button-4>", _on_mousewheel)
    treeview.bind("<Button-5>", _on_mousewheel)
