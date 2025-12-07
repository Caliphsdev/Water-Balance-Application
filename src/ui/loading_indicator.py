"""
Loading Indicator Widget
Shows database loading progress during async startup
"""

import tkinter as tk
from tkinter import ttk


class LoadingIndicator:
    """Overlay loading indicator for async operations"""
    
    def __init__(self, parent, message="Loading database..."):
        """
        Create loading indicator overlay
        
        Args:
            parent: Parent tkinter widget
            message: Loading message to display
        """
        self.parent = parent
        self.overlay = None
        self.message = message
        self.animation_id = None
        self.dots = 0
        
    def show(self):
        """Display loading overlay"""
        if self.overlay:
            return  # Already showing
            
        # Create semi-transparent overlay
        self.overlay = tk.Frame(self.parent, bg='#1E2A38')
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Loading content frame
        content_frame = tk.Frame(self.overlay, bg='#1E2A38')
        content_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Loading message with animated dots (no progress bar to avoid threading issues)
        self.label = tk.Label(
            content_frame,
            text=self.message,
            font=('Segoe UI', 16, 'bold'),
            fg='#FFFFFF',
            bg='#1E2A38'
        )
        self.label.pack(pady=20)
        
        # Animate dots
        self._animate_dots()
        
    def _animate_dots(self):
        """Animate loading dots (. .. ...)"""
        self.dots = (self.dots + 1) % 4
        dots_str = '.' * self.dots
        self.label.config(text=f"{self.message}{dots_str}")
        
        # Schedule next animation frame
        self.animation_id = self.parent.after(500, self._animate_dots)
        
    def update_message(self, message: str):
        """Update loading message"""
        self.message = message
        if self.label:
            self.label.config(text=message)
            
    def hide(self):
        """Remove loading overlay"""
        try:
            if self.animation_id:
                try:
                    self.parent.after_cancel(self.animation_id)
                except:
                    pass  # Already cancelled or parent destroyed
                self.animation_id = None
                
            if self.overlay:
                try:
                    self.overlay.destroy()
                except:
                    pass  # Already destroyed
                self.overlay = None
        except Exception as e:
            # Silently handle any cleanup errors
            pass
            
    def is_showing(self) -> bool:
        """Check if loading indicator is visible"""
        return self.overlay is not None
