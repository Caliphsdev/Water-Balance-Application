"""
Manual Test: Pump Transfer Confirmation Dialog

Quick test script to verify the pump transfer confirmation dialog UI works correctly.
Tests dialog display, user interaction, and result handling.

Run this script to visually verify:
- Dialog appears correctly centered on screen
- Summary metrics display (count, total volume)
- Transfer table shows all columns
- Source/Dest level changes calculated correctly
- Apply/Cancel buttons work
- Keyboard shortcuts (Enter=Apply, Escape=Cancel)

Usage:
    .venv\Scripts\python test_pump_transfer_dialog.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import tkinter as tk
from datetime import date
from ui.pump_transfer_confirm_dialog import PumpTransferConfirmDialog
from database.db_manager import DatabaseManager

def main():
    """Run manual UI test for pump transfer confirmation dialog."""
    print("🧪 Testing Pump Transfer Confirmation Dialog...")
    
    # Create test data (simulates calculator output)
    pump_transfers = {
        'UG2N_DAM': {
            'transfers': [
                {'destination': 'PLANT_RWD', 'volume_m3': 5000.0},
                {'destination': 'AUXILIARY_DAM', 'volume_m3': 2500.0}
            ]
        },
        'OLDTSF_DAM': {
            'transfers': [
                {'destination': 'NDCD1', 'volume_m3': 3000.0}
            ]
        }
    }
    
    test_date = date(2025, 1, 23)
    
    # Create root window (parent for dialog)
    root = tk.Tk()
    root.title("Test Parent Window")
    root.geometry("600x400")
    
    # Add test button to trigger dialog
    def show_dialog():
        dialog = PumpTransferConfirmDialog(root, pump_transfers, test_date)
        result = dialog.show()
        
        # Show result
        result_label.config(text=f"User Response: {result.upper()}")
        print(f"✅ Dialog returned: {result}")
    
    test_btn = tk.Button(
        root,
        text="Show Pump Transfer Dialog",
        command=show_dialog,
        font=('Segoe UI', 12),
        bg='#4CAF50',
        fg='white',
        padx=20,
        pady=10
    )
    test_btn.pack(expand=True)
    
    result_label = tk.Label(
        root,
        text="Click button to test dialog",
        font=('Segoe UI', 10),
        fg='#666'
    )
    result_label.pack(pady=10)
    
    # Instructions
    instructions = tk.Label(
        root,
        text="Test Checklist:\n"
             "✓ Dialog appears centered on parent\n"
             "✓ Summary shows 3 transfers, total volume\n"
             "✓ Table shows all 3 transfer rows\n"
             "✓ Level changes calculated (Current% → New%)\n"
             "✓ Apply button sets result='apply'\n"
             "✓ Cancel button sets result='cancel'\n"
             "✓ Enter key triggers Apply\n"
             "✓ Escape key triggers Cancel",
        font=('Segoe UI', 9),
        fg='#333',
        justify='left',
        bg='#f0f0f0',
        padx=10,
        pady=10
    )
    instructions.pack(fill='x', padx=20, pady=20)
    
    print("\n📋 Manual Test Checklist:")
    print("1. Click 'Show Pump Transfer Dialog' button")
    print("2. Verify dialog appears centered")
    print("3. Check summary metrics (3 transfers)")
    print("4. Check table has 3 rows")
    print("5. Try Apply button (should show 'apply')")
    print("6. Try Cancel button (should show 'cancel')")
    print("7. Try Enter key (should apply)")
    print("8. Try Escape key (should cancel)")
    print("\n⌨️  Press Ctrl+C in terminal to exit test\n")
    
    root.mainloop()

if __name__ == "__main__":
    main()
