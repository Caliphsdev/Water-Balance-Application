"""
Column Editor Dialog (EXCEL COLUMN MANAGEMENT UI).

Purpose:
- Provide UI for programmatic Excel column operations
- Display existing columns in selected sheet
- Allow add/rename/delete operations with real-time preview
- Validate column names and prevent conflicts

Data Sources:
- Flow Diagram Excel: timeseries_excel_path (from config)
- Flow sheets: "Flows_*" for each mining area
- Column headers: Row 3 (auto-detected by ExcelManager)

Key Responsibilities:
1. Load and display columns from selected sheet
2. Manage add/rename/delete operations
3. Persist changes to Excel file
4. Update mappings when columns change
5. Provide clear feedback on success/failure
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QComboBox,
    QFrame,
    QApplication,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon
from typing import List, Optional

from services.excel_manager import get_excel_manager
from core.app_logger import logger as app_logger

# Column editor-specific logger
logger = app_logger


class ColumnEditorDialog(QDialog):
    """
    Column Editor Dialog (PROGRAMMATIC EXCEL COLUMN MANAGEMENT).

    Purpose:
    - Provide user-friendly interface for managing Excel columns
    - Support add/rename/delete operations without leaving the app
    - Validate changes and prevent data loss
    - Update Excel file and invalidate caches

    Responsibilities:
    - Load columns from selected sheet
    - Display in editable table
    - Handle add/rename/delete buttons
    - Persist changes to Excel
    - Provide clear feedback and error messages

    Data Flow:
    1. User selects area code or sheet from dropdown
    2. Dialog loads existing columns from Excel
    3. User can add/rename/delete columns
    4. Preview shows current columns in table
    5. Save button persists changes to Excel file
    6. Success/error message displayed to user
    """

    def __init__(self, parent=None, area_code: Optional[str] = None):
        """
        Initialize Column Editor Dialog.

        Args:
            parent: Parent widget (typically ExcelSetupDialog)
            area_code: Initial area code to display (e.g., 'UG2N')
        """
        super().__init__(parent)
        self.setWindowTitle("Excel Column Manager")
        self.excel_manager = get_excel_manager()
        self.area_code = area_code or "UG2N"
        self.current_sheet = None
        self.original_columns = []  # Track original state for rollback
        self.modified_columns = {}  # Track changes: {old_name: new_name}
        self.new_columns = []  # Track newly added columns
        self.deleted_columns = []  # Track deleted columns

        # Setup UI
        self._setup_ui()
        self._load_columns()

        # Set modal and size
        self.setModal(True)
        self.resize(700, 600)

    def _setup_ui(self):
        """Setup dialog UI (LAYOUT CONSTRUCTION).

        Creates:
        - Sheet selection dropdown
        - Column table (Name, Type, Action)
        - Add/Rename/Delete buttons
        - Save/Cancel buttons
        """
        main_layout = QVBoxLayout()

        # Sheet selection section
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Select Sheet:"))

        self.sheet_combo = QComboBox()
        flow_sheets = self.excel_manager.list_flow_sheets()
        self.sheet_combo.addItems(flow_sheets)

        # Set current sheet based on area_code
        current_sheet = self.excel_manager.resolve_flow_sheet_name(self.area_code)
        index = self.sheet_combo.findText(current_sheet)
        if index >= 0:
            self.sheet_combo.setCurrentIndex(index)

        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)
        sheet_layout.addWidget(self.sheet_combo)
        sheet_layout.addStretch()

        main_layout.addLayout(sheet_layout)

        # Column table section
        table_label = QLabel("Columns in Selected Sheet:")
        table_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        main_layout.addWidget(table_label)

        self.table_columns = QTableWidget()
        self.table_columns.setColumnCount(3)
        self.table_columns.setHorizontalHeaderLabels(
            ["Column Name", "Data Type", "Action"]
        )
        self.table_columns.horizontalHeader().setStretchLastSection(False)
        self.table_columns.setColumnWidth(0, 250)
        self.table_columns.setColumnWidth(1, 150)
        self.table_columns.setColumnWidth(2, 100)
        main_layout.addWidget(self.table_columns)

        # Operation buttons section
        operations_layout = QHBoxLayout()
        operations_layout.addWidget(QLabel("Manage Columns:"))

        btn_add = QPushButton("+ Add Column")
        btn_add.clicked.connect(self._on_add_column)
        operations_layout.addWidget(btn_add)

        btn_rename = QPushButton("✎ Rename")
        btn_rename.clicked.connect(self._on_rename_column)
        operations_layout.addWidget(btn_rename)

        btn_delete = QPushButton("✕ Delete")
        btn_delete.clicked.connect(self._on_delete_column)
        btn_delete.setStyleSheet("QPushButton { color: #E74C3C; }")
        operations_layout.addWidget(btn_delete)

        operations_layout.addStretch()
        main_layout.addLayout(operations_layout)

        # Info section
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #E8F4F8; border: 1px solid #3498DB; border-radius: 4px;"
        )
        info_layout = QVBoxLayout(info_frame)
        info_label = QLabel(
            "💡 Add: Create new column for flow data\n"
            "✎ Rename: Change column header name\n"
            "✕ Delete: Remove column (data will be lost)"
        )
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet("background-color: transparent;")
        info_layout.addWidget(info_label)
        main_layout.addWidget(info_frame)

        # Save/Cancel buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        btn_cancel.setIconSize(QSize(14, 14))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save Changes")
        btn_save.setStyleSheet("QPushButton { background-color: #27AE60; color: white; }")
        btn_save.clicked.connect(self._on_save_changes)
        button_layout.addWidget(btn_save)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _load_columns(self):
        """Load columns from selected sheet and populate table (DATA LOADING).

        Reads column headers from Excel sheet and displays in table.
        Stores original state for validation.
        """
        sheet_name = self.sheet_combo.currentText()
        self.current_sheet = sheet_name

        try:
            # Load columns from Excel
            columns = self.excel_manager.list_flow_columns(sheet_name)

            # Store original state
            self.original_columns = columns.copy()
            self.modified_columns = {}
            self.new_columns = []
            self.deleted_columns = []

            # Populate table
            self.table_columns.setRowCount(len(columns))

            for row, col_name in enumerate(columns):
                # Column Name cell (editable via double-click)
                name_item = QTableWidgetItem(col_name)
                self.table_columns.setItem(row, 0, name_item)

                # Data Type cell (informational)
                type_item = QTableWidgetItem("Text/Number")
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.table_columns.setItem(row, 1, type_item)

                # Action cell (delete button)
                action_item = QTableWidgetItem("🗑️ Delete")
                action_item.setForeground(QColor("#E74C3C"))
                action_item.setFlags(action_item.flags() & ~Qt.ItemIsEditable)
                self.table_columns.setItem(row, 2, action_item)

            logger.debug(f"Loaded {len(columns)} columns from '{sheet_name}'")

        except Exception as e:
            logger.error(f"Failed to load columns: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to load columns from Excel:\n\n{e}"
            )

    def _on_sheet_changed(self):
        """Handle sheet selection change (EVENT HANDLER).

        Reloads columns when user changes sheet dropdown.
        """
        self._load_columns()

    def _on_add_column(self):
        """Show dialog to add new column (USER ACTION - ADD).

        Prompts user for new column name and adds row to table.
        Column will be persisted when user clicks Save.
        """
        dialog = AddColumnDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_column_name()

            # Validate name doesn't already exist
            existing_names = [
                self.table_columns.item(row, 0).text()
                for row in range(self.table_columns.rowCount())
            ]

            if new_name in existing_names:
                QMessageBox.warning(
                    self,
                    "Column Exists",
                    f"Column '{new_name}' already exists in this sheet.",
                )
                return

            if not new_name or len(new_name.strip()) == 0:
                QMessageBox.warning(self, "Invalid Name", "Column name cannot be empty.")
                return

            # Add row to table
            row = self.table_columns.rowCount()
            self.table_columns.insertRow(row)

            name_item = QTableWidgetItem(new_name)
            self.table_columns.setItem(row, 0, name_item)

            type_item = QTableWidgetItem("Text/Number")
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table_columns.setItem(row, 1, type_item)

            action_item = QTableWidgetItem("🗑️ Delete")
            action_item.setForeground(QColor("#E74C3C"))
            self.table_columns.setItem(row, 2, action_item)

            self.new_columns.append(new_name)
            logger.debug(f"Added new column '{new_name}' (pending save)")

    def _on_rename_column(self):
        """Show dialog to rename selected column (USER ACTION - RENAME).

        Prompts user for new name and updates table.
        Column will be persisted when user clicks Save.
        """
        selected_rows = self.table_columns.selectedIndexes()
        if not selected_rows:
            QMessageBox.information(self, "Select Column", "Please select a column to rename.")
            return

        row = selected_rows[0].row()
        old_name = self.table_columns.item(row, 0).text()

        dialog = RenameColumnDialog(self, old_name)
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_column_name()

            # Validate name doesn't already exist
            existing_names = [
                self.table_columns.item(r, 0).text()
                for r in range(self.table_columns.rowCount())
                if r != row
            ]

            if new_name in existing_names:
                QMessageBox.warning(
                    self,
                    "Column Exists",
                    f"Column '{new_name}' already exists in this sheet.",
                )
                return

            if not new_name or len(new_name.strip()) == 0:
                QMessageBox.warning(self, "Invalid Name", "Column name cannot be empty.")
                return

            # Update table
            self.table_columns.item(row, 0).setText(new_name)

            # Track modification
            if old_name in self.original_columns:
                self.modified_columns[old_name] = new_name
            else:
                # Column was just added, update new_columns list
                if old_name in self.new_columns:
                    self.new_columns.remove(old_name)
                self.new_columns.append(new_name)

            logger.debug(f"Renamed column '{old_name}' → '{new_name}' (pending save)")

    def _on_delete_column(self):
        """Delete selected column (USER ACTION - DELETE).

        Removes row from table after confirmation.
        Column will be deleted from Excel when user clicks Save.
        """
        selected_rows = self.table_columns.selectedIndexes()
        if not selected_rows:
            QMessageBox.information(self, "Select Column", "Please select a column to delete.")
            return

        row = selected_rows[0].row()
        col_name = self.table_columns.item(row, 0).text()

        reply = QMessageBox.warning(
            self,
            "Delete Column",
            f"Are you sure you want to delete '{col_name}'?\n\n"
            "This action cannot be undone. All data in this column will be lost.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.table_columns.removeRow(row)

            # Track deletion
            if col_name in self.original_columns:
                self.deleted_columns.append(col_name)
            if col_name in self.new_columns:
                self.new_columns.remove(col_name)

            logger.debug(f"Marked column '{col_name}' for deletion (pending save)")

    def _on_save_changes(self):
        """Persist all column changes to Excel file (PERSISTENCE).

        Executes all add/rename/delete operations in Excel:
        1. Add new columns via ExcelManager.create_flow_column()
        2. Rename existing columns via ExcelManager.rename_flow_column()
        3. Delete columns via ExcelManager.delete_flow_column()

        Rollback all changes if any operation fails.
        """
        sheet_name = self.current_sheet

        try:
            # Create new columns
            for col_name in self.new_columns:
                if not self.excel_manager.create_flow_column(sheet_name, col_name):
                    raise Exception(f"Failed to create column '{col_name}'")

            # Rename columns
            for old_name, new_name in self.modified_columns.items():
                if not self.excel_manager.rename_flow_column(
                    sheet_name, old_name, new_name
                ):
                    raise Exception(f"Failed to rename column '{old_name}' → '{new_name}'")

            # Delete columns (in reverse order to maintain stability)
            for col_name in reversed(self.deleted_columns):
                if not self.excel_manager.delete_flow_column(sheet_name, col_name):
                    raise Exception(f"Failed to delete column '{col_name}'")

            logger.info(
                f"✓ Saved changes: +{len(self.new_columns)} -{len(self.deleted_columns)} "
                f"~{len(self.modified_columns)} columns"
            )

            QMessageBox.information(
                self,
                "Success",
                f"✓ Column changes saved successfully!\n\n"
                f"Added: {len(self.new_columns)}\n"
                f"Renamed: {len(self.modified_columns)}\n"
                f"Deleted: {len(self.deleted_columns)}",
            )

            # Reload to show final state
            self._load_columns()
            self.accept()

        except Exception as e:
            logger.error(f"Failed to save column changes: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save changes:\n\n{e}\n\n"
                f"No changes were made to the Excel file.",
            )


class AddColumnDialog(QDialog):
    """Simple dialog to prompt for new column name (INPUT DIALOG).

    Purpose: Get user input for new column name with validation.
    """

    def __init__(self, parent=None):
        """Initialize Add Column dialog."""
        super().__init__(parent)
        self.setWindowTitle("Add New Column")
        self.setModal(True)
        self.setFixedWidth(400)

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Enter a name for the new column (e.g., 'BH_to_Sump'):")
        )

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Column name...")
        layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        btn_cancel.setIconSize(QSize(14, 14))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("Add")
        btn_ok.setStyleSheet("QPushButton { background-color: #27AE60; color: white; }")
        btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(btn_ok)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_column_name(self) -> str:
        """Get entered column name.

        Returns:
            Column name entered by user (stripped).
        """
        return self.input_field.text().strip()


class RenameColumnDialog(QDialog):
    """Simple dialog to prompt for new column name (INPUT DIALOG).

    Purpose: Get user input for renaming an existing column with validation.
    """

    def __init__(self, parent=None, old_name: str = ""):
        """Initialize Rename Column dialog.

        Args:
            parent: Parent widget.
            old_name: Current column name (shown for reference).
        """
        super().__init__(parent)
        self.setWindowTitle("Rename Column")
        self.setModal(True)
        self.setFixedWidth(400)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Rename column '{old_name}':"))

        self.input_field = QLineEdit()
        self.input_field.setText(old_name)
        self.input_field.selectAll()
        layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        btn_cancel.setIconSize(QSize(14, 14))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("Rename")
        btn_ok.setStyleSheet("QPushButton { background-color: #3498DB; color: white; }")
        btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(btn_ok)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_column_name(self) -> str:
        """Get entered column name.

        Returns:
            Column name entered by user (stripped).
        """
        return self.input_field.text().strip()
