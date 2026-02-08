"""
Notification Manager Dialog

Create and review notifications stored in Supabase.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer, QDateTime
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
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


class NotificationManagerDialog(QDialog):
    """Dialog to create and review notifications."""

    TABLE_COLUMNS = [
        ("Type", "type"),
        ("Title", "title"),
        ("Published", "published_at"),
        ("Expires", "expires_at"),
        ("Tiers", "target_tiers"),
    ]

    TYPES = ["announcement", "alert", "maintenance", "update"]
    TIERS = ["developer", "premium", "standard", "free_trial"]
    TEMPLATES = {
        "Standard Update": {
            "sections": ["Summary", "Details", "Action", "Support"],
        },
        "Maintenance Notice": {
            "sections": ["Summary", "Impact", "Timeline", "Action", "Support"],
        },
        "Incident Alert": {
            "sections": ["Summary", "Impact", "Current Status", "Action", "Support"],
        },
        "Release Announcement": {
            "sections": ["Summary", "Highlights", "Action", "Support"],
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = get_license_admin_service()
        self._threads: List[QThread] = []
        self._workers: List[AsyncWorker] = []
        self._rows: List[Dict[str, Any]] = []
        self._selected_notification_id: Optional[str] = None

        self.setWindowTitle("Notification Manager")
        self.setMinimumSize(1120, 640)
        self.resize(1180, 720)
        self.setStyleSheet("""
            QDialog { background-color: #f4f6fb; }
            QFrame#panelCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QFrame#headerCard {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                 stop:0 #0F172A, stop:1 #1E293B);
                border-radius: 12px;
            }
            QLabel#headerTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: 600;
            }
            QLabel#headerSubtitle {
                color: #cbd5f5;
                font-size: 11px;
            }
            QLineEdit, QComboBox, QDateTimeEdit, QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QTextEdit#previewBox {
                background-color: #f8fafc;
                border: 1px dashed #cbd5e1;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                padding: 6px;
                border: 1px solid #e2e8f0;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#primaryButton {
                background-color: #2563eb;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#primaryButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#ghostButton {
                background-color: #e2e8f0;
                color: #0f172a;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton#ghostButton:hover {
                background-color: #cbd5e1;
            }
            QPushButton#dangerButton {
                background-color: #fee2e2;
                color: #991b1b;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton#dangerButton:hover {
                background-color: #fecaca;
            }
            QLabel#metaLabel {
                color: #475569;
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
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(2)
        title = QLabel("Notification Center")
        title.setObjectName("headerTitle")
        title_stack.addWidget(title)
        subtitle = QLabel("Compose structured updates and review delivery history")
        subtitle.setObjectName("headerSubtitle")
        title_stack.addWidget(subtitle)
        header_layout.addLayout(title_stack)
        header_layout.addStretch(1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("ghostButton")
        header_layout.addWidget(self.refresh_button)
        layout.addWidget(header_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        form_panel = QFrame()
        form_panel.setObjectName("panelCard")
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(10)

        self.type_input = QComboBox()
        self.type_input.addItems(self.TYPES)
        form_layout.addWidget(self._labeled("Type", self.type_input))

        self.template_input = QComboBox()
        self.template_input.addItems(list(self.TEMPLATES.keys()))
        form_layout.addWidget(self._labeled("Message Template", self.template_input))

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Notification title")
        form_layout.addWidget(self._labeled("Title", self.title_input))

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Write the message or apply a structured template")
        self.body_input.setMinimumHeight(160)
        form_layout.addWidget(self._labeled("Message Body", self.body_input))

        template_row = QHBoxLayout()
        template_hint = QLabel("Use templates for consistent, professional wording.")
        template_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        template_row.addWidget(template_hint)
        template_row.addStretch(1)
        self.apply_template_button = QPushButton("Apply Template")
        self.apply_template_button.setObjectName("ghostButton")
        template_row.addWidget(self.apply_template_button)
        form_layout.addLayout(template_row)

        self.action_url_input = QLineEdit()
        self.action_url_input.setPlaceholderText("Optional action URL")
        form_layout.addWidget(self._labeled("Action URL", self.action_url_input))

        self.expires_toggle = QCheckBox("Set expiry")
        self.expires_input = QDateTimeEdit()
        self.expires_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.expires_input.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.expires_input.setEnabled(False)
        expires_row = QHBoxLayout()
        expires_row.addWidget(self.expires_toggle)
        expires_row.addWidget(self.expires_input)
        form_layout.addLayout(expires_row)

        tiers_container = QFrame()
        tiers_layout = QVBoxLayout(tiers_container)
        tiers_layout.setContentsMargins(0, 0, 0, 0)
        tiers_layout.setSpacing(4)
        tiers_label = QLabel("Target Tiers")
        tiers_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        tiers_layout.addWidget(tiers_label)

        self.tier_checks = []
        for tier in self.TIERS:
            checkbox = QCheckBox(tier)
            checkbox.setChecked(True)
            self.tier_checks.append(checkbox)
            tiers_layout.addWidget(checkbox)
        form_layout.addWidget(tiers_container)

        self.preview_box = QTextEdit()
        self.preview_box.setReadOnly(True)
        self.preview_box.setObjectName("previewBox")
        self.preview_box.setMinimumHeight(140)
        form_layout.addWidget(self._labeled("Preview", self.preview_box))

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.create_button = QPushButton("Send Notification")
        self.create_button.setObjectName("primaryButton")
        button_row.addWidget(self.create_button)
        form_layout.addLayout(button_row)

        splitter.addWidget(form_panel)

        list_panel = QFrame()
        list_panel.setObjectName("panelCard")
        list_layout = QHBoxLayout(list_panel)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_layout.setSpacing(12)

        history_splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels([col[0] for col in self.TABLE_COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)
        history_splitter.addWidget(self.table)

        history_preview = QFrame()
        history_layout = QVBoxLayout(history_preview)
        history_layout.setContentsMargins(8, 8, 8, 8)
        history_layout.setSpacing(6)

        history_title = QLabel("Selected Notification")
        history_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #0f172a;")
        history_layout.addWidget(history_title)

        meta_row = QHBoxLayout()
        self.history_type = QLabel("Type: -")
        self.history_type.setObjectName("metaLabel")
        meta_row.addWidget(self.history_type)
        meta_row.addStretch(1)
        self.history_tiers = QLabel("Tiers: -")
        self.history_tiers.setObjectName("metaLabel")
        meta_row.addWidget(self.history_tiers)
        history_layout.addLayout(meta_row)

        meta_row_two = QHBoxLayout()
        self.history_published = QLabel("Published: -")
        self.history_published.setObjectName("metaLabel")
        meta_row_two.addWidget(self.history_published)
        meta_row_two.addStretch(1)
        self.history_expires = QLabel("Expires: -")
        self.history_expires.setObjectName("metaLabel")
        meta_row_two.addWidget(self.history_expires)
        history_layout.addLayout(meta_row_two)

        self.history_title_text = QLineEdit()
        self.history_title_text.setReadOnly(True)
        history_layout.addWidget(self._labeled("Title", self.history_title_text))

        self.history_body = QTextEdit()
        self.history_body.setReadOnly(True)
        self.history_body.setMinimumHeight(120)
        history_layout.addWidget(self._labeled("Message", self.history_body))

        self.history_action = QLineEdit()
        self.history_action.setReadOnly(True)
        history_layout.addWidget(self._labeled("Action URL", self.history_action))

        history_actions = QHBoxLayout()
        history_actions.addStretch(1)
        self.delete_button = QPushButton("Delete Notification")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)
        history_actions.addWidget(self.delete_button)
        history_layout.addLayout(history_actions)

        history_splitter.addWidget(history_preview)
        history_splitter.setStretchFactor(0, 3)
        history_splitter.setStretchFactor(1, 2)

        list_layout.addWidget(history_splitter, 1)

        splitter.addWidget(list_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

        self.refresh_button.clicked.connect(self._refresh)
        self.create_button.clicked.connect(self._on_create)
        self.expires_toggle.toggled.connect(self.expires_input.setEnabled)
        self.apply_template_button.clicked.connect(self._apply_template)
        self.body_input.textChanged.connect(self._update_preview)
        self.title_input.textChanged.connect(self._update_preview)
        self.action_url_input.textChanged.connect(self._update_preview)
        self.expires_toggle.toggled.connect(self._update_preview)
        self.expires_input.dateTimeChanged.connect(self._update_preview)
        self.table.itemSelectionChanged.connect(self._update_history_preview)
        self.delete_button.clicked.connect(self._delete_selected)

        self._apply_template()
        self._refresh()

    def _labeled(self, text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; font-weight: 600; color: #334155;")
        layout.addWidget(label)
        layout.addWidget(widget)
        return container

    def _selected_tiers(self) -> List[str]:
        return [c.text() for c in self.tier_checks if c.isChecked()]

    def _apply_template(self) -> None:
        template_name = self.template_input.currentText()
        template = self.TEMPLATES.get(template_name, {})
        sections = template.get("sections", ["Summary", "Details", "Action", "Support"])

        title = self.title_input.text().strip() or "Notification Title"
        tiers = ", ".join(self._selected_tiers()) or "All tiers"
        lines = [title, "", f"Audience: {tiers}", ""]

        for section in sections:
            lines.append(f"{section}:")
            lines.append("- ")
            lines.append("")

        if self.action_url_input.text().strip():
            lines.append(f"Action URL: {self.action_url_input.text().strip()}")

        if self.expires_toggle.isChecked():
            expires_at = self.expires_input.dateTime().toPython()
            lines.append(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}")

        self.body_input.setPlainText("\n".join(lines).strip())
        self._update_preview()

    def _update_preview(self) -> None:
        body = self.body_input.toPlainText().strip()
        lines = [body] if body else []

        if self.action_url_input.text().strip() and "Action URL:" not in body:
            lines.append("")
            lines.append(f"Action URL: {self.action_url_input.text().strip()}")

        if self.expires_toggle.isChecked() and "Expires:" not in body:
            expires_at = self.expires_input.dateTime().toPython()
            lines.append(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}")

        self.preview_box.setPlainText("\n".join(lines).strip())

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
        QMessageBox.warning(self, "Notification Manager", message)

    def _refresh(self) -> None:
        def load():
            return self._service.list_notifications(limit=200)

        def done(result):
            self._rows = result or []
            self._populate_table(self._rows)

        self._run_async(load, done)

    def _populate_table(self, rows: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, (_, key) in enumerate(self.TABLE_COLUMNS):
                value = row.get(key, "")
                if key == "target_tiers" and isinstance(value, list):
                    value = ", ".join(value)
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
        if rows:
            self.table.selectRow(0)
        else:
            self._clear_history_preview()

    def _clear_history_preview(self) -> None:
        self._selected_notification_id = None
        self.history_type.setText("Type: -")
        self.history_tiers.setText("Tiers: -")
        self.history_published.setText("Published: -")
        self.history_expires.setText("Expires: -")
        self.history_title_text.clear()
        self.history_body.clear()
        self.history_action.clear()
        self.delete_button.setEnabled(False)

    def _update_history_preview(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self._clear_history_preview()
            return

        row = selected[0].row()
        if row < 0 or row >= len(self._rows):
            self._clear_history_preview()
            return

        data = self._rows[row]
        tiers = data.get("target_tiers") or []
        if isinstance(tiers, list):
            tiers_text = ", ".join(tiers)
        else:
            tiers_text = str(tiers)

        self._selected_notification_id = data.get("id")

        self.history_type.setText(f"Type: {data.get('type') or '-'}")
        self.history_tiers.setText(f"Tiers: {tiers_text or '-'}")
        self.history_published.setText(f"Published: {data.get('published_at') or '-'}")
        self.history_expires.setText(f"Expires: {data.get('expires_at') or '-'}")
        self.history_title_text.setText(data.get("title") or "")
        self.history_body.setPlainText(data.get("body") or "")
        self.history_action.setText(data.get("action_url") or "")
        self.delete_button.setEnabled(bool(self._selected_notification_id))

    def _delete_selected(self) -> None:
        notification_id = self._selected_notification_id
        if not notification_id:
            self._show_error("Select a notification to delete")
            return

        confirm = QMessageBox.question(
            self,
            "Delete Notification",
            "Delete the selected notification? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        def do_delete():
            self._service.delete_notification(notification_id)
            return True

        def done(_):
            self._clear_history_preview()
            self._refresh()

        self._run_async(do_delete, done)

    def _on_create(self) -> None:
        title = self.title_input.text().strip()
        body = self.body_input.toPlainText().strip()
        if not title or not body:
            self._show_error("Title and message are required")
            return

        tiers = self._selected_tiers()
        if not tiers:
            self._show_error("Select at least one target tier")
            return

        expires_at = None
        if self.expires_toggle.isChecked():
            expires_at = self.expires_input.dateTime().toPython()

        payload = {
            "type": self.type_input.currentText().strip(),
            "title": title,
            "body": body,
            "action_url": self.action_url_input.text().strip() or None,
            "target_tiers": tiers,
            "expires_at": expires_at,
        }

        def create():
            return self._service.create_notification(payload)

        def done(_):
            self.title_input.clear()
            self.body_input.clear()
            self.action_url_input.clear()
            self.expires_toggle.setChecked(False)
            for checkbox in self.tier_checks:
                checkbox.setChecked(True)
            self._refresh()

        self._run_async(create, done)
