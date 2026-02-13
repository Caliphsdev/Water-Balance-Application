import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFormLayout,
    QSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QTextEdit,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QTableView,
    QFrame,
)

from services.storage_history_service import StorageHistoryService
from ui.models.storage_history_model import StorageHistoryModel


class StorageHistoryDialog(QDialog):
    """Dialog to view and update monthly storage history for a facility."""

    def __init__(
        self,
        facility_code: str,
        facility_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._facility_code = facility_code
        self._facility_name = facility_name
        self._service = StorageHistoryService()
        self._model: Optional[StorageHistoryModel] = None

        self._build_ui()
        self._load_defaults()
        self._refresh_history()

    def _build_ui(self) -> None:
        self.setWindowTitle("Storage History")
        self.setMinimumSize(840, 560)
        self.setWindowIcon(QIcon(":/icons/Storage_facility_icon.svg"))

        layout = QVBoxLayout(self)
        header = QLabel(f"Storage History - {self._facility_name} ({self._facility_code})")
        header.setObjectName("storage_history_title")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setMinimumHeight(28)
        layout.addWidget(header)

        form_frame = QFrame(self)
        form_layout = QFormLayout(form_frame)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.input_year = QSpinBox(form_frame)
        self.input_year.setRange(2000, 2100)
        self.input_month = QComboBox(form_frame)
        for month in range(1, 13):
            self.input_month.addItem(str(month), month)

        self.input_closing = QDoubleSpinBox(form_frame)
        self.input_closing.setRange(0, 1_000_000_000)
        self.input_closing.setDecimals(2)
        self.input_closing.setSingleStep(100.0)

        self.input_source = QComboBox(form_frame)
        self.input_source.addItems(["measured", "calculated", "estimated", "imported"])

        self.label_opening = QLineEdit(form_frame)
        self.label_opening.setReadOnly(True)
        self.label_opening.setPlaceholderText("Opening volume will be inferred from history")

        self.label_delta = QLineEdit(form_frame)
        self.label_delta.setReadOnly(True)

        self.input_notes = QTextEdit(form_frame)
        self.input_notes.setFixedHeight(60)

        form_layout.addRow("Year", self.input_year)
        form_layout.addRow("Month", self.input_month)
        form_layout.addRow("Opening (m3)", self.label_opening)
        form_layout.addRow("Closing (m3)", self.input_closing)
        form_layout.addRow("Delta (m3)", self.label_delta)
        form_layout.addRow("Data source", self.input_source)
        form_layout.addRow("Notes", self.input_notes)

        layout.addWidget(form_frame)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.btn_save = QPushButton("Save Monthly Volume", self)
        self.btn_close = QPushButton("Close", self)
        button_row.addWidget(self.btn_save)
        button_row.addWidget(self.btn_close)
        layout.addLayout(button_row)

        self.table_history = QTableView(self)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_history, 1)

        self.btn_save.clicked.connect(self._on_save)
        self.btn_close.clicked.connect(self.reject)
        self.input_year.valueChanged.connect(self._update_opening_preview)
        self.input_month.currentIndexChanged.connect(self._update_opening_preview)
        self.input_closing.valueChanged.connect(self._update_delta_preview)

    def _load_defaults(self) -> None:
        from datetime import datetime

        now = datetime.now()
        self.input_year.setValue(now.year)
        self.input_month.setCurrentIndex(now.month - 1)

        current_volume = self._service.get_current_volume(self._facility_code)
        if current_volume is not None:
            self.input_closing.setValue(current_volume)
        self._update_opening_preview()

    def _refresh_history(self) -> None:
        if self._model is None:
            self._model = StorageHistoryModel(self._service, self._facility_code, self)
            self.table_history.setModel(self._model)
        else:
            self._model.refresh()

    def _update_opening_preview(self) -> None:
        year = self.input_year.value()
        month = self.input_month.currentData()
        opening, source_note = self._service.get_opening_for_period(
            self._facility_code, year, month
        )
        self.label_opening.setText(f"{opening:,.2f} ({source_note})")
        self._update_delta_preview()

    def _update_delta_preview(self) -> None:
        try:
            opening_text = self.label_opening.text().split(" ")[0].replace(",", ""
            )
            opening_value = float(opening_text) if opening_text else 0.0
        except ValueError:
            opening_value = 0.0
        closing_value = self.input_closing.value()
        delta = closing_value - opening_value
        self.label_delta.setText(f"{delta:,.2f}")

    def _on_save(self) -> None:
        year = self.input_year.value()
        month = self.input_month.currentData()
        closing_value = self.input_closing.value()
        data_source = self.input_source.currentText().strip()
        notes = self.input_notes.toPlainText().strip() or None

        try:
            record = self._service.upsert_monthly_storage(
                facility_code=self._facility_code,
                year=year,
                month=month,
                closing_volume_m3=closing_value,
                data_source=data_source,
                notes=notes,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", f"Could not save storage history: {exc}")
            return

        QMessageBox.information(
            self,
            "Saved",
            f"Saved {record.year}-{record.month:02d} storage for {record.facility_code}.",
        )
        self._refresh_history()
        self._update_opening_preview()
