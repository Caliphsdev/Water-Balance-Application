"""
Pump Transfer Confirmation Dialog

User-facing dialog that displays calculated pump transfers and allows user to
approve or reject before applying volume changes to the database.

Data Sources:
- pump_transfers dict from WaterBalanceCalculator.calculate_water_balance()
- storage_facilities table (for current volumes and levels)

UI Components:
- Summary card: count of transfers, total volume
- Transfer table: source, destination, volume, new levels
- Apply/Cancel buttons

Business Logic:
- Only shows if transfers exist (pump_transfers dict not empty)
- Apply button calls db.apply_pump_transfers() transactionally
- Cancel button returns without applying (user can review calculated values in tabs)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional
from datetime import date

from database.db_manager import DatabaseManager
from utils.config_manager import config
from utils.app_logger import logger


class PumpTransferConfirmDialog:
    """Confirmation dialog for pump transfers (USER APPROVAL REQUIRED).
    
    Displays calculated pump transfers before applying to database:
    - Shows source/destination facilities
    - Displays transfer volumes (m³)
    - Shows current and projected facility levels (%)
    - Allows user to approve or reject
    
    Only applies transfers to database if user clicks "Apply".
    If user clicks "Cancel", transfers are discarded (volumes unchanged).
    
    Args:
        parent: Parent tkinter window (for centering dialog)
        pump_transfers: Dict of transfers from calculate_water_balance()
            Format: {facility_code: {'transfers': [{'destination': str, 'volume_m3': float}]}}
        calculation_date: Date for which transfers calculated
    
    Returns:
        'apply' if user approved, 'cancel' if rejected
    
    Example:
        dialog = PumpTransferConfirmDialog(parent, pump_transfers, date(2025, 1, 23))
        if dialog.show() == 'apply':
            db.apply_pump_transfers(date, pump_transfers, user=current_user)
    """
    
    def __init__(self, parent: tk.Tk, pump_transfers: Dict, calculation_date: date):
        """Initialize pump transfer confirmation dialog (MODAL UI).
        
        Args:
            parent: Parent window for modal centering
            pump_transfers: Transfer data from calculator
            calculation_date: Date of calculation
        """
        self.parent = parent
        self.pump_transfers = pump_transfers
        self.calculation_date = calculation_date
        self.result = 'cancel'  # Default to cancel if user closes window
        self.db = DatabaseManager()
        
        # Build dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Confirm Pump Transfers - {calculation_date.strftime('%B %Y')}")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()  # Modal behavior (blocks parent until closed)
        
        self._create_ui()
        self._center_dialog()
    
    def _create_ui(self):
        """Build dialog UI components (SUMMARY + TABLE + BUTTONS).
        
        Layout:
        - Header frame: Summary metrics (count, total volume)
        - Content frame: Scrollable table of transfers
        - Button frame: Apply (primary) and Cancel (secondary)
        """
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header: Summary metrics
        self._create_summary_section(main_frame)
        
        # Content: Transfer table
        self._create_transfer_table(main_frame)
        
        # Footer: Action buttons
        self._create_button_section(main_frame)
    
    def _create_summary_section(self, parent):
        """Create summary card with transfer statistics (TOP SECTION).
        
        Displays:
        - Total number of transfers
        - Total volume to be transferred (m³)
        - Date of calculation
        
        Args:
            parent: Parent frame for summary section
        """
        summary_frame = ttk.LabelFrame(parent, text="Transfer Summary", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Calculate totals from pump_transfers dict
        transfer_count = 0
        total_volume = 0.0
        
        for facility_code, data in self.pump_transfers.items():
            transfers = data.get('transfers', [])
            for transfer in transfers:
                transfer_count += 1
                total_volume += float(transfer.get('volume_m3', 0))
        
        # Display metrics in grid layout
        ttk.Label(
            summary_frame, 
            text=f"Calculated {transfer_count} pump transfer(s) for {self.calculation_date.strftime('%B %Y')}",
            font=('Segoe UI', 10, 'bold')
        ).grid(row=0, column=0, sticky='w', columnspan=2, pady=(0, 5))
        
        ttk.Label(summary_frame, text="Total Volume:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        ttk.Label(
            summary_frame, 
            text=f"{total_volume:,.0f} m³",
            font=('Segoe UI', 9, 'bold')
        ).grid(row=1, column=1, sticky='w')
        
        # Warning message (transfers will update database volumes)
        warning_frame = ttk.Frame(summary_frame)
        warning_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        
        ttk.Label(
            warning_frame,
            text="⚠️ Applying transfers will update facility volumes in the database.",
            foreground='#FF6B35',
            font=('Segoe UI', 9)
        ).pack(anchor='w')
    
    def _create_transfer_table(self, parent):
        """Create scrollable table of transfers (MAIN CONTENT).
        
        Columns:
        - Source Facility: Facility transferring water out
        - Destination: Facility receiving water
        - Volume (m³): Amount to transfer
        - Source Level: Current % → New % after transfer
        - Dest Level: Current % → New % after transfer
        
        Reads current volumes from database to calculate projected levels.
        
        Args:
            parent: Parent frame for table section
        """
        table_frame = ttk.LabelFrame(parent, text="Transfer Details", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(table_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ('source', 'destination', 'volume', 'source_level', 'dest_level')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=tree_scroll.set,
            height=15
        )
        tree_scroll.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.heading('source', text='Source Facility')
        self.tree.heading('destination', text='Destination')
        self.tree.heading('volume', text='Volume (m³)')
        self.tree.heading('source_level', text='Source Level Change')
        self.tree.heading('dest_level', text='Dest Level Change')
        
        self.tree.column('source', width=150)
        self.tree.column('destination', width=150)
        self.tree.column('volume', width=100, anchor='e')
        self.tree.column('source_level', width=180, anchor='center')
        self.tree.column('dest_level', width=180, anchor='center')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate table with transfer data
        self._populate_transfer_table()
    
    def _populate_transfer_table(self):
        """Populate transfer table with calculated data (DATA BINDING).
        
        For each transfer:
        1. Fetch current facility volumes from database
        2. Calculate current utilization % (volume / capacity)
        3. Calculate new volumes after transfer
        4. Calculate new utilization %
        5. Format as "Current% → New%" for display
        
        Uses DatabaseManager to fetch facility data (current_volume, total_capacity).
        """
        for source_code, data in self.pump_transfers.items():
            transfers = data.get('transfers', [])
            
            # Get source facility data from database
            source_facility = self._get_facility_data(source_code)
            if not source_facility:
                continue
            
            for transfer in transfers:
                dest_code = transfer.get('destination')
                volume = float(transfer.get('volume_m3', 0))
                
                # Get destination facility data
                dest_facility = self._get_facility_data(dest_code)
                if not dest_facility:
                    continue
                
                # Calculate current and projected levels
                source_current_vol = float(source_facility['current_volume'] or 0)
                source_capacity = float(source_facility['total_capacity'] or 1)
                dest_current_vol = float(dest_facility['current_volume'] or 0)
                dest_capacity = float(dest_facility['total_capacity'] or 1)
                
                # Current levels (%)
                source_current_pct = (source_current_vol / source_capacity) * 100
                dest_current_pct = (dest_current_vol / dest_capacity) * 100
                
                # New levels after transfer (%)
                source_new_pct = ((source_current_vol - volume) / source_capacity) * 100
                dest_new_pct = ((dest_current_vol + volume) / dest_capacity) * 100
                
                # Format level change strings
                source_level_str = f"{source_current_pct:.1f}% → {source_new_pct:.1f}%"
                dest_level_str = f"{dest_current_pct:.1f}% → {dest_new_pct:.1f}%"
                
                # Insert row into table
                self.tree.insert('', 'end', values=(
                    source_code,
                    dest_code,
                    f"{volume:,.0f}",
                    source_level_str,
                    dest_level_str
                ))
    
    def _get_facility_data(self, facility_code: str) -> Optional[Dict]:
        """Fetch facility data from database (HELPER).
        
        Args:
            facility_code: Facility code to lookup (e.g., 'UG2N', 'OLDTSF')
        
        Returns:
            Dict with current_volume and total_capacity, or None if not found
        """
        try:
            rows = self.db.execute_query(
                "SELECT current_volume, total_capacity FROM storage_facilities WHERE facility_code = ? LIMIT 1",
                (facility_code,)
            )
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error fetching facility {facility_code}: {e}")
            return None
    
    def _create_button_section(self, parent):
        """Create action buttons (BOTTOM SECTION).
        
        Buttons:
        - Apply (green, primary): Calls _on_apply(), sets result='apply', closes dialog
        - Cancel (gray, secondary): Calls _on_cancel(), sets result='cancel', closes dialog
        
        Args:
            parent: Parent frame for button section
        """
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        # Cancel button (left)
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        )
        cancel_btn.pack(side=tk.LEFT)
        
        # Apply button (right, styled as primary)
        apply_btn = ttk.Button(
            button_frame,
            text="Apply Transfers",
            command=self._on_apply,
            width=15
        )
        apply_btn.pack(side=tk.RIGHT)
        
        # Set focus on Apply button (Enter key activates)
        apply_btn.focus_set()
        
        # Bind Enter key to Apply, Escape to Cancel
        self.dialog.bind('<Return>', lambda e: self._on_apply())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _center_dialog(self):
        """Center dialog on parent window (POSITIONING).
        
        Calculates parent window center and positions dialog accordingly.
        If parent not available, centers on screen.
        """
        self.dialog.update_idletasks()
        
        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _on_apply(self):
        """Handle Apply button click (USER APPROVED).
        
        Sets result to 'apply' and closes dialog.
        Calling code will then call db.apply_pump_transfers().
        """
        self.result = 'apply'
        logger.info(f"User approved pump transfers for {self.calculation_date}")
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click (USER REJECTED).
        
        Sets result to 'cancel' and closes dialog.
        Transfers will not be applied to database.
        """
        self.result = 'cancel'
        logger.info(f"User cancelled pump transfers for {self.calculation_date}")
        self.dialog.destroy()
    
    def show(self) -> str:
        """Display dialog and wait for user response (BLOCKING CALL).
        
        Returns:
            'apply' if user clicked Apply button
            'cancel' if user clicked Cancel or closed window
        
        Example:
            dialog = PumpTransferConfirmDialog(parent, transfers, date)
            if dialog.show() == 'apply':
                # Apply transfers to database
                db.apply_pump_transfers(...)
        """
        self.dialog.wait_window()  # Block until dialog closed
        return self.result
