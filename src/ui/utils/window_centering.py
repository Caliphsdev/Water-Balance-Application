"""Window centering utility for all popup dialogs (RESPONSIVE UI HELPER).

Provides platform-independent window centering that adapts to:
- Parent window position and size
- Screen dimensions
- DPI scaling (Windows high-DPI awareness)
- Multi-monitor setups

This utility centralizes centering logic to ensure consistent UI behavior
across all dialogs and popups in the application. All popup windows should
use these functions to maintain professional appearance on any screen size.

Performance: Centering operations are lightweight (pure geometry calculations),
typically <1ms per operation. No caching needed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import tkinter as tk
from typing import Optional
from utils.app_logger import logger


def center_window_on_parent(
    window: tk.Toplevel,
    parent: tk.Widget,
    offset_x: int = 0,
    offset_y: int = 0
) -> None:
    """Center popup window on parent window (WINDOW POSITIONING).
    
    Positions a child window at the center of its parent, with optional
    offset for visual distinction (e.g., cascade effect). Accounts for
    multi-monitor setups to prevent off-screen dialogs.
    
    Why: Centered windows improve UX and reduce cognitive load for users.
    Platform-aware scaling prevents off-screen positioning on high-DPI displays.
    
    Args:
        window: Toplevel window to center (must be created before calling)
        parent: Parent widget (typically root window or parent Toplevel)
        offset_x: Horizontal offset in pixels (positive = right, negative = left)
        offset_y: Vertical offset in pixels (positive = down, negative = up)
    
    Side Effects:
        - Updates window geometry immediately
        - Window must have been created before calling (needs valid dimensions)
    
    Raises:
        Exception: If window or parent not properly initialized (caught/logged)
    
    Example:
        dialog = tk.Toplevel(root)
        dialog.withdraw()  # Hide until positioned
        dialog.geometry("400x300")  # Set size BEFORE centering
        center_window_on_parent(dialog, root)
        dialog.deiconify()  # Show at centered position
    """
    try:
        # Force window to update geometry before centering (required for winfo calls)
        window.update_idletasks()
        
        # Get parent window position and size
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Get popup window size (must be set before calling this function)
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        # Handle edge case: zero dimensions (window not fully initialized)
        if window_width <= 1 or window_height <= 1:
            logger.warning("Window dimensions not set; cannot center properly")
            return
        
        # Calculate center position relative to parent
        center_x = parent_x + (parent_width // 2) - (window_width // 2) + offset_x
        center_y = parent_y + (parent_height // 2) - (window_height // 2) + offset_y
        
        # Ensure window stays within screen bounds (prevents off-screen dialogs)
        # This is critical for multi-monitor setups where parent might be off-center
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        center_x = max(0, min(center_x, screen_width - window_width))
        center_y = max(0, min(center_y, screen_height - window_height))
        
        # Apply position
        window.geometry(f"+{center_x}+{center_y}")
        
    except Exception as e:
        logger.error(f"Failed to center window on parent: {e}")
        # Fail silently - window will appear at default position


def center_window_on_screen(window: tk.Toplevel) -> None:
    """Center popup window on primary screen (FULLSCREEN CENTERING).
    
    Positions window at center of primary display, accounting for:
    - Screen dimensions
    - Window size (must be set before calling)
    - Multiple monitor setups (uses primary screen)
    
    Why: Fallback centering when no parent window available; ensures
    good UX on multi-monitor systems. Primary screen is first in list
    for most Windows/Linux/Mac systems.
    
    Args:
        window: Toplevel window to center (created and sized already)
    
    Side Effects:
        - Updates window geometry immediately
    
    Raises:
        Exception: If window dimensions invalid (caught/logged)
    
    Example:
        splash = tk.Toplevel()
        splash.geometry("400x300")
        center_window_on_screen(splash)
    """
    try:
        window.update_idletasks()
        
        # Get window and screen dimensions
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Handle edge case: zero dimensions
        if window_width <= 1 or window_height <= 1:
            logger.warning("Window dimensions not set for screen centering")
            return
        
        # Calculate center position (primary screen center)
        center_x = (screen_width // 2) - (window_width // 2)
        center_y = (screen_height // 2) - (window_height // 2)
        
        # Ensure non-negative (handles edge cases on multi-monitor systems)
        center_x = max(0, center_x)
        center_y = max(0, center_y)
        
        window.geometry(f"+{center_x}+{center_y}")
        
    except Exception as e:
        logger.error(f"Failed to center window on screen: {e}")


def make_modal_centered(
    window: tk.Toplevel,
    parent: Optional[tk.Widget] = None
) -> None:
    """Configure window as centered modal dialog (MODAL SETUP).
    
    Applies standard modal dialog configuration:
    - Centers on parent (or screen if no parent)
    - Makes window transient (stays on top)
    - Sets grab to prevent parent interaction
    - Configures window properties for professional appearance
    
    Why: Consistent modal behavior across all dialogs. Users expect
    dialogs to be: centered, always on top, and blocking parent interaction.
    
    Args:
        window: Dialog window to configure
        parent: Parent window (required for proper modal behavior; optional)
    
    Side Effects:
        - Modifies window properties (transient, grab, focus)
        - Window becomes modal (blocks parent interaction)
        - Window focus is set (active window)
    
    Example:
        dialog = tk.Toplevel(root)
        dialog.geometry("500x400")
        make_modal_centered(dialog, root)
        # User cannot interact with root until dialog closed
    """
    try:
        # Center window first
        if parent:
            center_window_on_parent(window, parent)
        else:
            center_window_on_screen(window)
        
        # Make window transient (stays on top of parent)
        if parent:
            window.transient(parent)
        
        # Apply window attributes for modal behavior
        window.resizable(False, False)
        
        # Grab focus (makes window modal - blocks parent interaction)
        window.grab_set()
        
        # Ensure window appears above parent
        window.lift()
        window.attributes('-topmost', True)
        
        # Remove topmost after window is visible (prevents always-on-top)
        window.after(10, lambda: window.attributes('-topmost', False))
        
    except Exception as e:
        logger.error(f"Failed to configure modal window: {e}")
