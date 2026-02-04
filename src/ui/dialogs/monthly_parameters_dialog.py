"""
Monthly Parameters dialog controller (PySide6).

Purpose:
- Provide a modal dialog for editing monthly inflows/outflows per facility
- Display historical monthly records for the selected facility
- Support create/update/delete of monthly totals

Notes:
- UI is defined in generated_ui_monthly_parameters_dialog.py
- Data source is SQLite table: facility_monthly_parameters
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
import sqlite3
from PySide6.QtWidgets import QDialog, QMessageBox, QAbstractItemView

from services.monthly_parameters_service import MonthlyParametersService
from ui.models.monthly_parameters_history_model import MonthlyParametersHistoryModel

from ui.dialogs.generated_ui_monthly_parameters_dialog import Ui_Dialog


class MonthlyParametersDialog(QDialog):
    """Monthly Parameters dialog (UI controller).

    Responsibilities:
    - Load and present the dialog UI
    - Display selected facility label
    - Load historical monthly totals from SQLite
    - Create, update, and delete monthly records
    """

    def __init__(
        self,
        facility_id: int,
        facility_code: str,
        facility_name: str,
        parent: Optional[QDialog] = None
    ) -> None:
        """Initialize the dialog and bind UI elements.

        Args:
            facility_id: Storage facility ID (FK to storage_facilities.id).
            facility_code: Facility code to display in the header (e.g., "UG2N").
            facility_name: Facility name for user context.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Service layer (handles validation + DB access)
        self.service = MonthlyParametersService()

        # Facility context
        self.facility_id = facility_id
        self.facility_code = facility_code
        self.facility_name = facility_name

        # Track selected record ID for update/delete
        self._selected_record_id: Optional[int] = None

        # Month name mapping (index 0 -> January)
        self._month_names: List[str] = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        # Show facility context in header (user clarity)
        self.ui.label_facility.setText(f"Facility: {facility_code} - {facility_name}")

        # Initialize default year/month to current date
        self._set_default_period()

        # Wire buttons and table interactions
        self.ui.btn_close.clicked.connect(self.reject)
        self.ui.btn_save.clicked.connect(self._on_save)
        self.ui.btn_update.clicked.connect(self._on_update)
        self.ui.btn_delete.clicked.connect(self._on_delete)
        self.ui.spin_year.valueChanged.connect(self._on_period_changed)
        self.ui.combo_month.currentIndexChanged.connect(self._on_period_changed)

        # Initialize history model (lazy loading with pagination)
        self._history_model = MonthlyParametersHistoryModel(
            service=self.service,
            facility_id=self.facility_id,
            page_size=120,
            parent=self,
        )
        self._setup_history_view()
        self._history_model.refresh()
        self._update_action_states()

    def _set_default_period(self) -> None:
        """Set default year/month inputs to current date (UX DEFAULTS).

        Why:
        - Users most often enter data for current month
        - Reduces clicks and errors
        """
        today = datetime.now()
        self.ui.spin_year.setValue(today.year)
        self.ui.combo_month.setCurrentIndex(today.month - 1)

    def _setup_history_view(self) -> None:
        """Configure history QTableView with lazy-loading model.

        Why QTableView:
        - Only renders visible rows (performance for large datasets)
        - Works with QAbstractTableModel fetchMore pagination
        """
        self.ui.table_history.setModel(self._history_model)
        self.ui.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.table_history.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.table_history.horizontalHeader().setStretchLastSection(True)
        self.ui.table_history.verticalHeader().setVisible(False)
        self.ui.table_history.setSortingEnabled(False)

        # Connect selection change after model is set (QTableView API)
        self.ui.table_history.selectionModel().selectionChanged.connect(
            lambda _selected, _deselected: self._on_history_selected()
        )

    def _get_selected_period(self) -> tuple[int, int]:
        """Get year and month from input controls (INPUT PARSING).

        Returns:
            Tuple of (year, month_number)
        """
        year = int(self.ui.spin_year.value())
        month = self.ui.combo_month.currentIndex() + 1
        return year, month

    def _on_history_selected(self) -> None:
        """Handle history table selection (SYNC INPUTS).

        When a user clicks a history row, update input fields and
        store selected record ID for Update/Delete actions.
        """
        selection = self.ui.table_history.selectionModel().selectedRows()
        if not selection:
            self._selected_record_id = None
            return

        row = selection[0].row()
        record = self._history_model.get_record(row)
        if not record:
            self._selected_record_id = None
            return

        self._selected_record_id = record.id

        try:
            year = int(record.year)
            month_name = self._month_names[record.month - 1]
            inflows = float(record.total_inflows_m3)
            outflows = float(record.total_outflows_m3)

            self.ui.spin_year.setValue(year)
            if month_name in self._month_names:
                self.ui.combo_month.setCurrentIndex(self._month_names.index(month_name))
            self.ui.spin_inflows.setValue(inflows)
            self.ui.spin_outflows.setValue(outflows)
            self._update_action_states()
        except Exception:
            # Keep UI stable even if parsing fails
            pass

    def _on_period_changed(self) -> None:
        """Handle year/month changes to update button states (UX SAFETY).

        When the selected period changes, re-check whether a record exists
        so Save/Update options remain accurate and prevent duplicates.
        """
        self._selected_record_id = None
        self._update_action_states()

    def _update_action_states(self) -> None:
        """Enable/disable Save/Update/Delete based on existing record.

        Behavior:
        - If record exists for selected period: disable Save, enable Update/Delete
        - If no record exists: enable Save, disable Update/Delete
        """
        year, month = self._get_selected_period()
        existing = self.service.get_record_by_period(self.facility_id, year, month)

        if existing:
            self._selected_record_id = existing.id
            self.ui.btn_save.setEnabled(False)
            self.ui.btn_update.setEnabled(True)
            self.ui.btn_delete.setEnabled(True)
            if hasattr(self.ui, "label_record_status"):
                self.ui.label_record_status.setText(
                    f"Status: Existing record found for {year}-{month:02d}"
                )
        else:
            self._selected_record_id = None
            self.ui.btn_save.setEnabled(True)
            self.ui.btn_update.setEnabled(False)
            self.ui.btn_delete.setEnabled(False)
            if hasattr(self.ui, "label_record_status"):
                self.ui.label_record_status.setText(
                    f"Status: No record for {year}-{month:02d} (Save to create)"
                )

    def _on_save(self) -> None:
        """Save new monthly record (CREATE ACTION).

        Validates inputs and inserts new record for facility/month.
        If record exists, prompts user to use Update instead.
        """
        year, month = self._get_selected_period()
        inflows = float(self.ui.spin_inflows.value())
        outflows = float(self.ui.spin_outflows.value())

        try:
            created = self.service.create_monthly_parameters(
                facility_id=self.facility_id,
                year=year,
                month=month,
                total_inflows_m3=inflows,
                total_outflows_m3=outflows,
            )
            QMessageBox.information(
                self,
                "Saved",
                f"Saved monthly parameters for {year}-{month:02d}."
            )
            self._history_model.refresh()
            self._selected_record_id = created.id
            self._update_action_states()
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Duplicate",
                "A record for this month already exists. Use Update instead."
            )
            self._update_action_states()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _on_update(self) -> None:
        """Update existing monthly record (UPDATE ACTION).

        Requires a selected history row or an existing record for the
        chosen year/month.
        """
        year, month = self._get_selected_period()
        inflows = float(self.ui.spin_inflows.value())
        outflows = float(self.ui.spin_outflows.value())

        try:
            record_id = self._selected_record_id
            if not record_id:
                existing = self.service.get_record_by_period(self.facility_id, year, month)
                if not existing:
                    QMessageBox.warning(
                        self,
                        "Not Found",
                        "No existing record for this month. Use Save instead."
                    )
                    return
                record_id = existing.id

            self.service.update_monthly_parameters(
                record_id=record_id,
                total_inflows_m3=inflows,
                total_outflows_m3=outflows,
            )
            QMessageBox.information(
                self,
                "Updated",
                f"Updated monthly parameters for {year}-{month:02d}."
            )
            self._history_model.refresh()
            self._update_action_states()
        except Exception as e:
            QMessageBox.critical(self, "Update Error", str(e))

    def _on_delete(self) -> None:
        """Delete selected monthly record (DELETE ACTION).

        Requires a selected history row.
        """
        if not self._selected_record_id:
            QMessageBox.warning(self, "No Selection", "Select a record to delete")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete selected monthly record?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.service.delete_monthly_parameters(self._selected_record_id)
            QMessageBox.information(self, "Deleted", "Record deleted successfully")
            self._selected_record_id = None
            self._history_model.refresh()
            self._update_action_states()
        except Exception as e:
            QMessageBox.critical(self, "Delete Error", str(e))
