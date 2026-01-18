"""
Area Exclusion Dialog - UI for managing which areas are included in balance calculations
"""

import tkinter as tk
from tkinter import ttk
from utils.balance_check_engine import get_balance_check_engine
from utils.template_data_parser import get_template_parser
from utils.app_logger import logger
from ui.mouse_wheel_support import enable_canvas_mousewheel, enable_text_mousewheel


class AreaExclusionDialog:
    """Dialog for managing area exclusions"""
    
    def __init__(self, parent):
        """Initialize exclusion dialog
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        self.engine = get_balance_check_engine()
        self.parser = get_template_parser()
        self.dialog = None
        self.checkbuttons = {}
        self.result = None
    
    def show(self):
        """Show the area exclusion dialog
        
        Returns:
            True if user clicked OK, False if cancelled
        """
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("⚙️ Manage Area Exclusions")
        self.dialog.geometry("500x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(self.dialog, padding=15)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="⚙️ Area Exclusion Manager",
                 font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Uncheck areas to exclude them from balance calculations",
                 font=('Segoe UI', 9), foreground='#666').pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Scrollable frame for checkboxes
        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0, height=300)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        enable_canvas_mousewheel(canvas)
        
        # Get all areas
        all_areas = sorted(self.parser.get_areas())
        excluded_areas = self.engine.get_excluded_areas()
        
        # Create checkboxes for each area
        self.checkbuttons = {}
        for area in all_areas:
            is_included = area not in excluded_areas
            var = tk.BooleanVar(value=is_included)
            
            cb = ttk.Checkbutton(
                scrollable_frame,
                text=f"✓ {area}",
                variable=var,
                command=lambda a=area, v=var: self._on_area_toggled(a, v)
            )
            cb.pack(anchor=tk.W, pady=5)
            
            self.checkbuttons[area] = (var, cb)
        
        # Pack scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Info box
        info_frame = ttk.LabelFrame(self.dialog, text="ℹ️ About Exclusions", padding=10)
        info_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        info_text = tk.Text(info_frame, height=3, wrap=tk.WORD, font=('Segoe UI', 8),
                           relief=tk.FLAT, background='#f0f0f0', borderwidth=0)
        info_text.pack(fill=tk.X)
        enable_text_mousewheel(info_text)
        info_text.insert('1.0',
            "Excluded areas will be removed from balance calculations.\n"
            "The balance equation will only use data from included areas.\n"
            "Changes are saved automatically and take effect on next calculation.")
        info_text.configure(state='disabled', foreground='#666')
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=15)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="✅ OK",
                  command=self._on_ok,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel",
                  command=self._on_cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="↺ Reset",
                  command=self._on_reset).pack(side=tk.LEFT)
        
        # Wait for dialog
        self.dialog.wait_window()
        return self.result
    
    def _on_area_toggled(self, area: str, var: tk.BooleanVar):
        """Handle area inclusion toggle"""
        is_included = var.get()
        
        if is_included:
            self.engine.include_area(area)
            logger.info(f"Area {area} toggled: INCLUDED")
        else:
            self.engine.exclude_area(area)
            logger.info(f"Area {area} toggled: EXCLUDED")
    
    def _on_ok(self):
        """Handle OK button"""
        self.result = True
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = False
        self.dialog.destroy()
    
    def _on_reset(self):
        """Reset all exclusions"""
        response = tk.messagebox.askyesno(
            "Reset Exclusions",
            "Reset all areas to INCLUDED? This will clear all exclusions."
        )
        
        if response:
            self.engine.exclusion_manager.clear_exclusions()
            
            # Update checkboxes
            for area, (var, cb) in self.checkbuttons.items():
                var.set(True)
            
            logger.info("All area exclusions cleared")
