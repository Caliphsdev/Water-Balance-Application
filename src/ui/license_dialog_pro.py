"""Professional license activation and transfer dialog with ttkbootstrap styling."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import datetime as dt
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
except ImportError:
    import tkinter.ttk as ttk
    from tkinter import LEFT, RIGHT, BOTH, X, Y, TOP, BOTTOM, E, W, N, S

from licensing.license_manager import LicenseManager
from utils.app_logger import logger
from utils.config_manager import config


class ProfessionalLicenseDialog(ttk.Window):
    """Modern professional license dialog with ttkbootstrap styling."""

    def __init__(self, mode: str = "activate", theme: str = "flatly"):
        """
        Initialize professional license dialog.
        
        Args:
            mode: 'activate' for new activation, 'transfer' for hardware transfer
            theme: ttkbootstrap theme name (flatly, litera, cosmo, etc.)
        """
        # Get theme from app config or use default
        app_theme = config.get("window.theme", "arc")
        # Map arc theme to ttkbootstrap equivalent
        theme_map = {
            "arc": "flatly",
            "clam": "litera",
            "alt": "cosmo",
            "default": "flatly"
        }
        bootstrap_theme = theme_map.get(app_theme, "flatly")
        
        super().__init__(themename=bootstrap_theme)
        
        self.title("Water Balance - License Activation")
        self.resizable(False, False)
        self.result = False
        self.mode = mode
        self.manager = LicenseManager()
        
        # Colors matching app branding
        self.primary_color = config.get("colors.primary", "#1976D2")
        self.success_color = config.get("colors.success", "#2E7D32")
        self.warning_color = config.get("colors.warning", "#F57C00")
        self.error_color = config.get("colors.error", "#D32F2F")
        
        self._build_ui()
        self._center_window()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _center_window(self):
        """Center dialog on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
    
    def _build_ui(self):
        """Build professional UI layout"""
        # Main container with padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Header section
        self._build_header(main_frame)
        
        # Form section
        self._build_form(main_frame)
        
        # Status section
        self._build_status(main_frame)
        
        # Action buttons
        self._build_actions(main_frame)
        
        # Footer info
        self._build_footer(main_frame)
    
    def _build_header(self, parent):
        """Build header with icon and title"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Icon (using Unicode symbol)
        icon_label = ttk.Label(
            header_frame,
            text="🔐",
            font=("Segoe UI", 32)
        )
        icon_label.pack(side=LEFT, padx=(0, 15))
        
        # Title and subtitle
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        if self.mode == "transfer":
            title_text = "Hardware Transfer Request"
            subtitle_text = "Transfer your license to this computer"
        else:
            title_text = "License Activation"
            subtitle_text = "Activate your Water Balance software"
        
        ttk.Label(
            title_frame,
            text=title_text,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor=W)
        
        ttk.Label(
            title_frame,
            text=subtitle_text,
            font=("Segoe UI", 10),
            foreground="gray"
        ).pack(anchor=W)
    
    def _build_form(self, parent):
        """Build input form"""
        form_frame = ttk.LabelFrame(parent, text="License Information")
        form_frame.pack(fill=X, pady=(0, 15), padx=5)
        
        # Inner padding frame
        inner_frame = ttk.Frame(form_frame, padding=15)
        inner_frame.pack(fill=BOTH, expand=True)
        
        # License Key (required)
        ttk.Label(
            inner_frame,
            text="License Key *",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, sticky=W, pady=(0, 5))
        
        self.license_var = tk.StringVar()
        self.license_entry = ttk.Entry(
            inner_frame,
            textvariable=self.license_var,
            width=45,
            font=("Consolas", 11)
        )
        self.license_entry.grid(row=1, column=0, sticky=W+E, pady=(0, 15))
        self.license_entry.bind("<FocusOut>", self._validate_license_format)
        self.license_entry.focus_set()
        
        # Licensee Name (optional)
        ttk.Label(
            inner_frame,
            text="Licensee Name (optional)",
            font=("Segoe UI", 10)
        ).grid(row=2, column=0, sticky=W, pady=(0, 5))
        
        self.name_var = tk.StringVar()
        ttk.Entry(
            inner_frame,
            textvariable=self.name_var,
            width=45
        ).grid(row=3, column=0, sticky=W+E, pady=(0, 15))
        
        # Email (optional)
        ttk.Label(
            inner_frame,
            text="Email Address (optional)",
            font=("Segoe UI", 10)
        ).grid(row=4, column=0, sticky=W, pady=(0, 5))
        
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(
            inner_frame,
            textvariable=self.email_var,
            width=45
        )
        self.email_entry.grid(row=5, column=0, sticky=W+E)
        self.email_entry.bind("<FocusOut>", self._validate_email_format)
        
        inner_frame.columnconfigure(0, weight=1)
    
    def _build_status(self, parent):
        """Build status message section"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=X, pady=(0, 15))
        
        self.status_icon = ttk.Label(
            self.status_frame,
            text="",
            font=("Segoe UI", 14)
        )
        self.status_icon.pack(side=LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="",
            font=("Segoe UI", 10),
            wraplength=450
        )
        self.status_label.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Initially hidden
        self.status_frame.pack_forget()
        
        if self.mode == "transfer":
            self._show_status(
                "⚠️",
                "Hardware mismatch detected. Request a transfer to bind this license to your current hardware.",
                "warning"
            )
    
    def _build_actions(self, parent):
        """Build action buttons"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=X, pady=(0, 15))
        
        # Spacer to push buttons right
        ttk.Frame(action_frame).pack(side=LEFT, fill=BOTH, expand=True)
        
        # Cancel button
        ttk.Button(
            action_frame,
            text="Cancel",
            command=self._on_close,
            width=12,
            bootstyle="secondary"
        ).pack(side=LEFT, padx=(0, 10))
        
        # Primary action button (activation only)
        primary_text = "Activate License"
        primary_command = self._on_activate
        
        self.primary_btn = ttk.Button(
            action_frame,
            text=primary_text,
            command=primary_command,
            width=18,
            bootstyle="primary"
        )
        self.primary_btn.pack(side=LEFT)
    
    def _build_footer(self, parent):
        """Build footer with support info"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Separator(footer_frame, orient=HORIZONTAL).pack(fill=X, pady=(0, 10))
        
        support_email = config.get("licensing.support_email", "caliphs@transafreso.com")
        support_phone = config.get("licensing.support_phone", "+27 82 355 8130")
        
        ttk.Label(
            footer_frame,
            text=f"Need help? Contact: {support_email} | {support_phone}",
            font=("Segoe UI", 9),
            foreground="gray"
        ).pack(anchor=W)
    
    def _validate_license_format(self, event=None):
        """Validate license key format (basic check)"""
        key = self.license_var.get().strip()
        if key and "-" not in key:
            self._show_status(
                "⚠️",
                "License key should contain dashes (e.g., ABC-123-XYZ)",
                "warning"
            )
    
    def _validate_email_format(self, event=None):
        """Validate email format (basic check)"""
        email = self.email_var.get().strip()
        if email and "@" not in email:
            self._show_status(
                "⚠️",
                "Please enter a valid email address",
                "warning"
            )
    
    def _show_status(self, icon: str, message: str, status_type: str = "info"):
        """
        Show status message with icon.
        
        Args:
            icon: Unicode icon (emoji)
            message: Status message
            status_type: 'success', 'error', 'warning', 'info'
        """
        self.status_icon.config(text=icon)
        self.status_label.config(text=message)
        
        # Color based on type
        colors = {
            "success": self.success_color,
            "error": self.error_color,
            "warning": self.warning_color,
            "info": self.primary_color
        }
        self.status_label.config(foreground=colors.get(status_type, "gray"))
        
        # Show status frame
        self.status_frame.pack(fill=X, pady=(0, 15))
    
    def _hide_status(self):
        """Hide status message"""
        self.status_frame.pack_forget()
    
    def _on_activate(self):
        """Handle activation button click"""
        key = self.license_var.get().strip()
        if not key:
            self._show_status("❌", "Please enter a license key", "error")
            return
        
        # Show progress
        self._show_status("⏳", "Validating license online...", "info")
        self.primary_btn.config(state="disabled")
        self.update()
        
        # Attempt activation
        name = self.name_var.get().strip() or None
        email = self.email_var.get().strip() or None
        
        ok, msg = self.manager.activate(key, name, email)
        
        if ok:
            logger.info("License activated successfully")
            self._show_status("✅", "License activated successfully!", "success")
            self.after(1000, self._close_success)
        else:
            logger.error(f"Activation failed: {msg}")
            self._show_status("❌", msg, "error")
            self.primary_btn.config(state="normal")
    
    def _close_success(self):
        """Close dialog after successful operation"""
        self.result = True
        self.destroy()
    
    def _on_close(self):
        """Handle dialog close"""
        self.result = False
        self.destroy()


def show_professional_license_dialog(mode: str = "activate") -> bool:
    """
    Open professional license dialog and return result.
    
    Args:
        mode: 'activate' for new activation, 'transfer' for hardware transfer
        
    Returns:
        True if activation/transfer succeeded, False otherwise
    """
    dialog = ProfessionalLicenseDialog(mode=mode)
    dialog.mainloop()
    return dialog.result


if __name__ == "__main__":
    # Test dialog
    result = show_professional_license_dialog(mode="activate")
    print(f"Dialog result: {result}")
