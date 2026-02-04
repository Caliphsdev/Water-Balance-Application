"""
Monthly Parameters History Model (LAZY-LOADING TABLE MODEL).

Purpose:
- Provide a QAbstractTableModel for monthly parameters history
- Load records in pages (fetchMore) for large datasets
- Render only visible cells (Qt's model/view lazy rendering)

Data source:
- MonthlyParametersService.get_history() (SQLite-backed)

Why this model:
- QTableView + QAbstractTableModel only renders visible rows
- fetchMore enables pagination for large history tables
- Keeps memory usage low for thousands of monthly records
"""

from __future__ import annotations

from typing import List, Optional
import logging

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from models.monthly_parameters import MonthlyParameters
from services.monthly_parameters_service import MonthlyParametersService


logger = logging.getLogger(__name__)


class MonthlyParametersHistoryModel(QAbstractTableModel):
    """Lazy-loading model for monthly parameters history (MODEL/VIEW).

    Features:
    - Paged loading via fetchMore()
    - O(visible_rows) rendering (Qt calls data() only for visible cells)
    - Sorted history order (year DESC, month DESC) from service

    Data flow:
    1. refresh() resets model and loads first page
    2. QTableView calls canFetchMore()/fetchMore() as user scrolls
    3. data() returns formatted values for visible cells
    """

    def __init__(
        self,
        service: MonthlyParametersService,
        facility_id: int,
        page_size: int = 120,
        parent=None,
    ) -> None:
        """Initialize the history model.

        Args:
            service: MonthlyParametersService for data access
            facility_id: Storage facility ID for history filtering
            page_size: Number of records to fetch per page
            parent: Optional QObject parent
        """
        super().__init__(parent)
        self._service = service
        self._facility_id = facility_id
        self._page_size = page_size
        self._records: List[MonthlyParameters] = []
        self._has_more = True

        self._headers = [
            "Year",
            "Month",
            "Total Inflows (m³)",
            "Total Outflows (m³)",
        ]
        self._month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of loaded rows (ROW COUNT).

        Args:
            parent: Unused in flat table models
        """
        if parent.isValid():
            return 0
        return len(self._records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns (COLUMN COUNT)."""
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
        """Return data for visible cells (LAZY CELL RENDERING).

        Args:
            index: Model index for cell
            role: Display role or custom role

        Returns:
            Formatted string for display, or None
        """
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._records):
            return None

        record = self._records[row]

        if role == Qt.DisplayRole:
            if col == 0:
                return str(record.year)
            if col == 1:
                return self._month_names[record.month - 1]
            if col == 2:
                return f"{record.total_inflows_m3:,.2f}"
            if col == 3:
                return f"{record.total_outflows_m3:,.2f}"

        if role == Qt.UserRole:
            # Return record id for selection mapping
            return record.id

        if role == Qt.TextAlignmentRole:
            if col in (0, 2, 3):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Optional[str]:
        """Return header labels (COLUMN HEADERS)."""
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self._headers[section] if section < len(self._headers) else None

        return str(section + 1)

    def canFetchMore(self, parent: QModelIndex = QModelIndex()) -> bool:
        """Indicate if more data can be fetched (PAGINATION CHECK)."""
        if parent.isValid():
            return False
        return self._has_more

    def fetchMore(self, parent: QModelIndex = QModelIndex()) -> None:
        """Fetch next page of history records (LAZY PAGINATION).

        Called by QTableView when it needs more rows.
        """
        if parent.isValid() or not self._has_more:
            return

        offset = len(self._records)
        try:
            new_records = self._service.get_history(
                facility_id=self._facility_id,
                limit=self._page_size,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"Failed to fetch history page: {e}")
            self._has_more = False
            return

        if not new_records:
            self._has_more = False
            return

        start = len(self._records)
        end = start + len(new_records) - 1

        self.beginInsertRows(QModelIndex(), start, end)
        self._records.extend(new_records)
        self.endInsertRows()

        if len(new_records) < self._page_size:
            self._has_more = False

    def refresh(self) -> None:
        """Reset and reload the model (FULL REFRESH).

        Use after Save/Update/Delete to reload history from the database.
        """
        self.beginResetModel()
        self._records = []
        self._has_more = True
        self.endResetModel()

        # Load first page immediately for UI responsiveness
        self.fetchMore(QModelIndex())

    def get_record(self, row: int) -> Optional[MonthlyParameters]:
        """Get record by row index (SELECTION HELPER)."""
        if 0 <= row < len(self._records):
            return self._records[row]
        return None
