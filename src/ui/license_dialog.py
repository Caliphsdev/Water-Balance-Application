"""License activation and transfer dialog - modern design."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from licensing.license_manager import LicenseManager
from utils.app_logger import logger


class LicenseDialog(tk.Toplevel):
    """Modal dialog for activation and transfer workflows - modern clean design."""

    def __init__(self, parent=None, mode: str = "activate"):
        self.own_parent = (parent is None)
        self.parent = parent or tk.Tk()
        if parent is None:
            self.parent.withdraw()
        super().__init__(self.parent)
        self.title("License Activation")
        self.resizable(False, False)
        self.result = False
        self.manager = LicenseManager()
        
        # Modern color scheme
        self.bg_color = '#f5f6f7'
        self.card_color = '#ffffff'
        self.accent_color = '#0066cc'
        self.accent_hover = '#0052a3'
        self.success_color = '#28a745'
        self.danger_color = '#dc3545'
        self.text_primary = '#2c3e50'
        self.text_secondary = '#7f8c8d'
        self.border_color = '#e0e0e0'
        
        self.configure(bg=self.bg_color)
        
        self._build_ui(mode)
        
        # Set window size and center it
        self.update_idletasks()
        window_width = 520
        window_height = 420
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self, mode: str):
        """Build modern license dialog UI."""
        # Main container
        main_frame = tk.Frame(self, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True)
        
        # Header section with icon and title
        header_frame = tk.Frame(main_frame, bg=self.accent_color, height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_icon = tk.Label(
            header_frame,
            text="🔐",
            font=('Segoe UI', 28),
            fg='white',
            bg=self.accent_color
        )
        header_icon.pack(pady=(16, 2))
        
        header_title = tk.Label(
            header_frame,
            text="License Activation",
            font=('Segoe UI', 14, 'bold'),
            fg='white',
            bg=self.accent_color
        )
        header_title.pack(pady=(0, 8))
        
        # Content frame with padding
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill="both", expand=True, padx=24, pady=16)
        
        # License key field
        ttk.Label(
            content_frame,
            text="License Key",
            font=("Segoe UI", 9, "bold"),
            foreground=self.text_primary,
            background=self.bg_color
        ).pack(anchor='w', pady=(0, 5))
        
        self.license_var = tk.StringVar()
        license_entry = ttk.Entry(
            content_frame,
            textvariable=self.license_var,
            width=50,
            font=("Segoe UI", 10)
        )
        license_entry.pack(fill='x', pady=(0, 12))
        license_entry.focus_set()
        
        # Licensee name field
        ttk.Label(
            content_frame,
            text="Full Name (Required)",
            font=("Segoe UI", 9, "bold"),
            foreground=self.text_primary,
            background=self.bg_color
        ).pack(anchor='w', pady=(0, 5))
        
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(
            content_frame,
            textvariable=self.name_var,
            width=50,
            font=("Segoe UI", 10)
        )
        self.name_entry.pack(fill='x', pady=(0, 12))
        
        # Email field
        ttk.Label(
            content_frame,
            text="Email Address (Required)",
            font=("Segoe UI", 9, "bold"),
            foreground=self.text_primary,
            background=self.bg_color
        ).pack(anchor='w', pady=(0, 5))
        
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(
            content_frame,
            textvariable=self.email_var,
            width=50,
            font=("Segoe UI", 10)
        )
        self.email_entry.pack(fill='x', pady=(0, 16))
        
        # Status label (for error messages)
        self.status_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 9),
            fg=self.danger_color,
            bg=self.bg_color,
            wraplength=450,
            justify='left'
        )
        self.status_label.pack(fill='x', pady=(0, 12))
        
        if mode == "transfer":
            self.status_label.config(
                text="⚠️ Hardware mismatch detected.\nEnter your registered email to authorize transfer to this device.",
                fg='#ff9800'
            )
            self.email_entry.focus_set()
        
        # Footer with buttons
        button_frame = tk.Frame(content_frame, bg=self.bg_color)
        button_frame.pack(fill='x', pady=(8, 0))
        
        # Cancel button (left side)
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=('Segoe UI', 9),
            fg=self.text_secondary,
            bg=self.border_color,
            activebackground='#d0d0d0',
            relief='flat',
            bd=0,
            padx=16,
            pady=8,
            command=self._on_close,
            cursor='hand2'
        )
        cancel_btn.pack(side='left', padx=(0, 8))
        
        # Buttons on right side
        right_button_frame = tk.Frame(button_frame, bg=self.bg_color)
        right_button_frame.pack(side='right')
        
        # Request Transfer button
        transfer_btn = tk.Button(
            right_button_frame,
            text="Request Transfer",
            font=('Segoe UI', 9, 'bold'),
            fg='white',
            bg=self.accent_color,
            activebackground=self.accent_hover,
            relief='flat',
            bd=0,
            padx=16,
            pady=8,
            command=self._on_transfer,
            cursor='hand2'
        )
        transfer_btn.pack(side='left', padx=(0, 8))
        
        # Activate button (primary action)
        activate_btn = tk.Button(
            right_button_frame,
            text="Activate License",
            font=('Segoe UI', 9, 'bold'),
            fg='white',
            bg=self.success_color,
            activebackground='#218838',
            relief='flat',
            bd=0,
            padx=16,
            pady=8,
            command=self._on_activate,
            cursor='hand2'
        )
        activate_btn.pack(side='left')

    def _on_activate(self):
        key = self.license_var.get().strip()
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        
        # Validate all required fields
        if not key:
            self.status_label.config(text="❌ License key is required")
            return
        
        if not name:
            self.status_label.config(text="❌ Licensee name is required")
            self.name_entry.focus_set()
            return
        
        if not email:
            self.status_label.config(text="❌ Email is required")
            self.email_entry.focus_set()
            return
        
        # Basic email format validation
        if "@" not in email or "." not in email.split("@")[-1]:
            self.status_label.config(text="❌ Please enter a valid email address")
            self.email_entry.focus_set()
            self.email_entry.select_range(0, tk.END)
            return
        
        ok, msg = self.manager.activate(key, name, email)
        if ok:
            logger.info("License activated")
            self.result = True
            messagebox.showinfo("Activation", "✅ License activated successfully!", parent=self)
            self.destroy()
            if self.own_parent:
                self.parent.destroy()
        else:
            self.status_label.config(text=msg)

    def _on_transfer(self):
        key = self.license_var.get().strip()
        email = self.email_var.get().strip()
        
        # Validate email is provided
        if not email:
            self.status_label.config(text="❌ Email is required for transfer verification")
            self.email_entry.focus_set()
            return
        
        # Basic email format validation
        if "@" not in email or "." not in email.split("@")[-1]:
            self.status_label.config(text="❌ Please enter a valid email address")
            self.email_entry.focus_set()
            return
        
        ok, msg = self.manager.request_transfer(key, user_email=email)
        if ok:
            logger.info(f"License transfer approved for email: {email}")
            self.result = True
            messagebox.showinfo("Transfer", "✅ Transfer approved!\n\nHardware updated successfully.\nCheck your email for confirmation.", parent=self)
            self.destroy()
        else:
            self.status_label.config(text=f"❌ {msg}")
            # If email mismatch, highlight the email field
            if "email" in msg.lower() or "invalid" in msg.lower():
                self.email_entry.focus_set()
                self.email_entry.select_range(0, tk.END)

    def _on_close(self):
        self.result = False
        self.destroy()
        if self.own_parent:
            self.parent.destroy()


def show_license_dialog(parent=None, mode: str = "activate") -> bool:
    """Open dialog and return True if activation/transfer succeeded."""
    dialog = LicenseDialog(parent=parent, mode=mode)
    dialog.wait_window()
    return dialog.result
