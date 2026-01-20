"""
Excel Configuration Dialog
Prompts user to configure Excel file when missing or needed
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from utils.config_manager import config
from utils.app_logger import logger


class ExcelConfigDialog:
    """Dialog for configuring Excel file location"""
    
    def __init__(self, parent_window, missing_path: str = None):
        """
        Show dialog to configure Excel file
        
        Args:
            parent_window: Parent Tkinter window
            missing_path: Path that was missing (for display)
        """
        self.parent = parent_window
        self.missing_path = missing_path
        self.selected_path = None
    
    def show(self) -> bool:
        """
        Show configuration dialog
        
        Returns:
            True if user selected a file, False if cancelled
        """
        # First ask if user wants to configure now
        result = messagebox.askyesno(
            "Excel Data File Not Found",
            f"The Excel data file is not found:\n\n{self.missing_path}\n\n"
            "Would you like to select it now?\n\n"
            "(You can also configure this later in Settings → Data Sources)"
        )
        
        if not result:
            return False
        
        # Let user select file
        return self._browse_for_file()
    
    def _browse_for_file(self) -> bool:
        """Let user browse for Excel file"""
        try:
            file_path = filedialog.askopenfilename(
                parent=self.parent,
                title="Select Water Balance Excel Template",
                filetypes=[
                    ("Excel Files", "*.xlsx"),
                    ("All Files", "*.*")
                ],
                initialdir=str(Path.home() / "Documents")
            )
            
            if not file_path:
                return False  # User cancelled
            
            # Save selection
            self.selected_path = file_path
            
            # Update config using public API
            try:
                config.set('data_sources.template_excel_path', file_path)
                
                logger.info(f"Excel path configured: {file_path}")
                messagebox.showinfo(
                    "Success",
                    "Excel file configured successfully!\n\n"
                    "The app will use this file for data."
                )
                return True
                
            except Exception as e:
                logger.error(f"Error saving Excel path: {e}")
                messagebox.showerror(
                    "Error",
                    f"Failed to save Excel path:\n{e}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error in file browser: {e}")
            messagebox.showerror(
                "Error",
                f"Error selecting file:\n{e}"
            )
            return False
    
    def get_selected_path(self) -> str:
        """Get the path user selected"""
        return self.selected_path


def show_excel_config_dialog(parent_window, missing_path: str = None) -> bool:
    """
    Convenience function to show Excel config dialog
    
    Args:
        parent_window: Parent Tkinter window
        missing_path: Path that was missing (for display)
        
    Returns:
        True if user configured a file, False otherwise
    """
    dialog = ExcelConfigDialog(parent_window, missing_path)
    return dialog.show()
