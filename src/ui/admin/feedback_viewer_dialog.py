"""
Feedback Viewer Dialog

Shows feedback submissions stored in Supabase (feature_requests table).

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QComboBox,
    QVBoxLayout,
)

from services.license_admin_service import get_license_admin_service


class AsyncWorker(QObject):
    """Run a callable on a background QThread."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


class FeedbackViewerDialog(QDialog):
    """Dialog for viewing feedback submissions."""

    TABLE_COLUMNS = [
        ("Type", "type"),
        ("Title", "title"),
        ("Status", "status"),
        ("Customer", "customer_name"),
        ("Email", "email"),
        ("License", "license_key"),
        ("HWID", "hwid"),
        ("Created", "created_at"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = get_license_admin_service()
        self._threads: List[QThread] = []
        self._workers: List[AsyncWorker] = []
        self._rows: List[Dict[str, Any]] = []

        self.setWindowTitle("Feedback Viewer")
        self.setMinimumSize(980, 560)
        self.setStyleSheet("""
            QDialog {
                background-color: #f6f7fb;
            }
            QFrame#headerCard {
                background-color: #0f172a;
                border-radius: 10px;
            }
            QLabel#headerTitle {
                color: #f8fafc;
                font-size: 18px;
                font-weight: 600;
            }
            QLabel#headerSubtitle {
                color: #cbd5f5;
                font-size: 11px;
            }
            QFrame#filterCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QFrame#panelCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QLineEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLabel#filterLabel {
                color: #475569;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton {
                background-color: #0f172a;
                color: #f8fafc;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
            QPushButton#ghostButton {
                background-color: transparent;
                border: 1px solid #cbd5e1;
                color: #334155;
            }
            QPushButton#ghostButton:hover {
                background-color: #f1f5f9;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                selection-background-color: #e0f2fe;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                padding: 6px;
                border: 1px solid #e2e8f0;
                font-size: 11px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_card = QFrame()
        header_card.setObjectName("headerCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)

        title_col = QVBoxLayout()
        title = QLabel("Feedback Submissions")
        title.setObjectName("headerTitle")
        title_col.addWidget(title)

        subtitle = QLabel("Review bug reports and requests from users")
        subtitle.setObjectName("headerSubtitle")
        title_col.addWidget(subtitle)

        header_layout.addLayout(title_col)
        header_layout.addStretch(1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("ghostButton")
        header_layout.addWidget(self.refresh_button)
        layout.addWidget(header_card)

        filter_card = QFrame()
        filter_card.setObjectName("filterCard")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        search_col = QVBoxLayout()
        search_label = QLabel("Search")
        search_label.setObjectName("filterLabel")
        search_col.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title, email, or license key")
        search_col.addWidget(self.search_input)
        filter_layout.addLayout(search_col, 3)

        type_col = QVBoxLayout()
        type_label = QLabel("Type")
        type_label.setObjectName("filterLabel")
        type_col.addWidget(type_label)
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "bug", "feature", "general"])
        type_col.addWidget(self.type_filter)
        filter_layout.addLayout(type_col, 1)

        status_col = QVBoxLayout()
        status_label = QLabel("Status")
        status_label.setObjectName("filterLabel")
        status_col.addWidget(status_label)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "open", "in_progress", "resolved", "closed", "wont_fix"])
        status_col.addWidget(self.status_filter)
        filter_layout.addLayout(status_col, 1)

        self.clear_filters_button = QPushButton("Clear")
        self.clear_filters_button.setObjectName("ghostButton")
        filter_layout.addWidget(self.clear_filters_button)

        layout.addWidget(filter_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        list_panel = QFrame()
        list_panel.setObjectName("panelCard")
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels([col[0] for col in self.TABLE_COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.setSortingEnabled(False)
        list_layout.addWidget(self.table)

        detail_panel = QFrame()
        detail_panel.setObjectName("panelCard")
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(14, 12, 14, 12)
        detail_layout.setSpacing(10)

        self.detail_title = QLabel("Select feedback to view details")
        self.detail_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #0f172a;")
        detail_layout.addWidget(self.detail_title)

        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #64748b; font-size: 11px;")
        self.detail_meta.setWordWrap(True)
        detail_layout.addWidget(self.detail_meta)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        status_action_label = QLabel("Set status")
        status_action_label.setObjectName("filterLabel")
        action_row.addWidget(status_action_label)

        self.status_action = QComboBox()
        self.status_action.addItems(["open", "in_progress", "resolved", "closed", "wont_fix"])
        action_row.addWidget(self.status_action)

        self.apply_status_button = QPushButton("Update Status")
        action_row.addWidget(self.apply_status_button)

        self.resolve_button = QPushButton("Mark Resolved")
        self.resolve_button.setObjectName("ghostButton")
        action_row.addWidget(self.resolve_button)

        self.copy_email_button = QPushButton("Copy Email")
        self.copy_email_button.setObjectName("ghostButton")
        action_row.addWidget(self.copy_email_button)

        self.copy_license_button = QPushButton("Copy License")
        self.copy_license_button.setObjectName("ghostButton")
        action_row.addWidget(self.copy_license_button)

        self.copy_hwid_button = QPushButton("Copy HWID")
        self.copy_hwid_button.setObjectName("ghostButton")
        action_row.addWidget(self.copy_hwid_button)

        action_row.addStretch(1)
        detail_layout.addLayout(action_row)

        self.detail_body = QTextEdit()
        self.detail_body.setReadOnly(True)
        self.detail_body.setMinimumHeight(220)
        detail_layout.addWidget(self.detail_body, 1)

        self.detail_notes = QTextEdit()
        self.detail_notes.setReadOnly(True)
        self.detail_notes.setPlaceholderText("Admin notes")
        self.detail_notes.setMinimumHeight(120)
        detail_layout.addWidget(self.detail_notes)

        splitter.addWidget(list_panel)
        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setChildrenCollapsible(False)

        layout.addWidget(splitter, 1)

        self.refresh_button.clicked.connect(self._refresh)
        self.search_input.textChanged.connect(self._apply_filter)
        self.type_filter.currentTextChanged.connect(self._apply_filter)
        self.status_filter.currentTextChanged.connect(self._apply_filter)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.apply_status_button.clicked.connect(self._on_apply_status)
        self.resolve_button.clicked.connect(self._on_mark_resolved)
        self.copy_email_button.clicked.connect(lambda: self._copy_selected("email"))
        self.copy_license_button.clicked.connect(lambda: self._copy_selected("license_key"))
        self.copy_hwid_button.clicked.connect(lambda: self._copy_selected("hwid"))
        self.clear_filters_button.clicked.connect(self._reset_filters)

        self._refresh()

    def _run_async(self, fn, on_success, on_error=None) -> None:
        thread = QThread(self)
        worker = AsyncWorker(fn)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        def _run_on_ui(callback, *args):
            QTimer.singleShot(0, self, lambda: callback(*args))

        def _cleanup_and_call(callback, *args):
            thread.quit()
            if QThread.currentThread() is not thread:
                thread.wait()
            if thread in self._threads:
                self._threads.remove(thread)
            if worker in self._workers:
                self._workers.remove(worker)
            callback(*args)

        def handle_success(result):
            _run_on_ui(_cleanup_and_call, on_success, result)

        def handle_error(message):
            def _call_error():
                if on_error:
                    on_error(message)
                else:
                    self._show_error(message)
            _run_on_ui(_cleanup_and_call, _call_error)

        worker.finished.connect(handle_success)
        worker.error.connect(handle_error)

        self._threads.append(thread)
        self._workers.append(worker)
        thread.start()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Feedback Viewer", message)

    def _refresh(self) -> None:
        def load():
            return self._service.list_feedback(limit=200)

        def done(result):
            self._rows = result or []
            self._apply_filter()

        self._run_async(load, done)

    def _apply_filter(self) -> None:
        text = self.search_input.text().strip().lower()
        type_filter = self.type_filter.currentText().strip().lower()
        status_filter = self.status_filter.currentText().strip().lower()
        if not text:
            rows = self._rows
        else:
            rows = []
            for row in self._rows:
                haystack = " ".join(
                    [
                        str(row.get("title", "")),
                        str(row.get("customer_name", "")),
                        str(row.get("email", "")),
                        str(row.get("license_key", "")),
                    ]
                ).lower()
                if text in haystack:
                    rows.append(row)
        if type_filter != "all":
            rows = [r for r in rows if (r.get("type") or "").lower() == type_filter]
        if status_filter != "all":
            rows = [r for r in rows if (r.get("status") or "").lower() == status_filter]

        self._populate_table(rows)

    def _reset_filters(self) -> None:
        self.search_input.clear()
        self.type_filter.setCurrentText("All")
        self.status_filter.setCurrentText("All")

    def _populate_table(self, rows: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, (_, key) in enumerate(self.TABLE_COLUMNS):
                value = row.get(key, "")
                item = QTableWidgetItem(str(value) if value is not None else "")
                if key == "title":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setData(Qt.ItemDataRole.UserRole, row.get("id"))
                self.table.setItem(row_idx, col_idx, item)

    def _on_row_selected(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
        row_index = selected[0].row()
        title_item = self.table.item(row_index, 1)
        if not title_item:
            return
        feedback_id = title_item.data(Qt.ItemDataRole.UserRole)
        match = next((r for r in self._rows if r.get("id") == feedback_id), None)
        if not match:
            return

        self._selected_feedback_id = feedback_id

        self.detail_title.setText(match.get("title", "Untitled"))
        meta = (
            f"Type: {match.get('type', 'n/a')} | Status: {match.get('status', 'n/a')}\n"
            f"Customer: {match.get('customer_name', 'n/a')} | Email: {match.get('email', 'n/a')}\n"
            f"License: {match.get('license_key', 'n/a')} | HWID: {match.get('hwid', 'n/a')}\n"
            f"Created: {match.get('created_at', 'n/a')}"
        )
        self.detail_meta.setText(meta)
        self.detail_body.setText(match.get("description", ""))
        self.detail_notes.setText(match.get("admin_notes", ""))
        current_status = (match.get("status") or "open").lower()
        if current_status in [self.status_action.itemText(i) for i in range(self.status_action.count())]:
            self.status_action.setCurrentText(current_status)

    def _copy_selected(self, field: str) -> None:
        if not hasattr(self, "_selected_feedback_id"):
            return
        match = next((r for r in self._rows if r.get("id") == self._selected_feedback_id), None)
        if not match:
            return
        value = match.get(field)
        if not value:
            return
        QGuiApplication.clipboard().setText(str(value))

    def _on_apply_status(self) -> None:
        if not hasattr(self, "_selected_feedback_id"):
            return
        status = self.status_action.currentText().strip().lower()

        def update():
            return self._service.update_feedback_status(self._selected_feedback_id, status)

        def done(result):
            for idx, row in enumerate(self._rows):
                if row.get("id") == self._selected_feedback_id:
                    self._rows[idx] = result
                    break
            self._apply_filter()

        self._run_async(update, done)

    def _on_mark_resolved(self) -> None:
        if not hasattr(self, "_selected_feedback_id"):
            return
        self.status_action.setCurrentText("resolved")
        self._on_apply_status()
