import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from models.storage_history import StorageHistoryRecord
from services.storage_history_service import StorageHistoryService


class StorageHistoryModel(QAbstractTableModel):
    """Qt table model for facility storage history."""

    _headers = [
        "Year",
        "Month",
        "Opening (m3)",
        "Closing (m3)",
        "Delta (m3)",
        "Source",
        "Updated",
    ]

    def __init__(
        self,
        service: StorageHistoryService,
        facility_code: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._facility_code = facility_code
        self._records: List[StorageHistoryRecord] = []
        self.refresh()

    def refresh(self) -> None:
        self.beginResetModel()
        self._records = self._service.get_history(self._facility_code)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        record = self._records[index.row()]
        col = index.column()
        if col == 0:
            return record.year
        if col == 1:
            return record.month
        if col == 2:
            return f"{record.opening_volume_m3:,.2f}"
        if col == 3:
            return f"{record.closing_volume_m3:,.2f}"
        if col == 4:
            return f"{record.delta_volume_m3:,.2f}"
        if col == 5:
            return record.data_source
        if col == 6:
            return record.updated_at or ""
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers[section]
        return section + 1
