"""
License Manager Window

Standalone admin GUI for creating and managing licenses in Supabase.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QDateTime, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.crypto import generate_license_key, generate_ed25519_keypair_base64, VALID_TIERS
from services.license_admin_service import get_license_admin_service


LICENSE_MANAGER_STYLE = """
QMainWindow {
    background-color: #F3F5F7;
}

QFrame#headerFrame {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                     stop:0 #0D47A1, stop:1 #1E3A8A);
    border-radius: 8px;
}

QLabel#headerTitle {
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 600;
}

QLabel#headerSubtitle {
    color: #C7D2FE;
    font-size: 12px;
}

QLabel#statusLabel {
    color: #E2E8F0;
    font-size: 11px;
}

QFrame#panelFrame {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}

QLabel#sectionTitle {
    color: #111827;
    font-size: 14px;
    font-weight: 600;
}

QLineEdit, QComboBox, QDateTimeEdit {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #111827;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
    border-color: #2563EB;
}

QPushButton {
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#primaryButton {
    background-color: #2563EB;
    color: #FFFFFF;
}

QPushButton#primaryButton:hover {
    background-color: #1D4ED8;
}

QPushButton#secondaryButton {
    background-color: #E2E8F0;
    color: #111827;
}

QPushButton#secondaryButton:hover {
    background-color: #CBD5E1;
}

QPushButton#dangerButton {
    background-color: #DC2626;
    color: #FFFFFF;
}

QPushButton#dangerButton:hover {
    background-color: #B91C1C;
}

QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: #E5E7EB;
    selection-background-color: #DBEAFE;
    selection-color: #111827;
}

QHeaderView::section {
    background-color: #F1F5F9;
    padding: 6px;
    border: 1px solid #E2E8F0;
    font-size: 11px;
    font-weight: 600;
}
"""


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


class LicenseManagerWindow(QMainWindow):
    """Admin window for license management."""

    TABLE_COLUMNS: List[Tuple[str, str]] = [
        ("License Key", "license_key"),
        ("Tier", "tier"),
        ("Status", "status"),
        ("Expires", "expires_at"),
        ("Customer", "customer_name"),
        ("Email", "customer_email"),
        ("HWID", "hwid"),
        ("Last Validated", "last_validated"),
    ]

    def __init__(self):
        super().__init__()
        self._service = get_license_admin_service()
        self._threads: List[QThread] = []
        self._workers: List[AsyncWorker] = []
        self._licenses: List[Dict[str, Any]] = []

        self._setup_ui()
        self._connect_signals()
        self._refresh_licenses()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Water Balance License Manager")
        self.setMinimumSize(1200, 720)
        self.setStyleSheet(LICENSE_MANAGER_STYLE)

        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 16, 18, 16)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("License Manager")
        title.setObjectName("headerTitle")
        title_layout.addWidget(title)

        subtitle = QLabel("Create, assign, and manage Supabase licenses")
        subtitle.setObjectName("headerSubtitle")
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)

        main_layout.addWidget(header)

        filter_frame = QFrame()
        filter_frame.setObjectName("panelFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search license key, customer, or email")
        filter_layout.addWidget(self.search_input, stretch=2)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "active", "expired", "revoked"])
        filter_layout.addWidget(self.status_filter)

        self.feedback_button = QPushButton("Feedback")
        self.feedback_button.setObjectName("secondaryButton")
        filter_layout.addWidget(self.feedback_button)

        self.notifications_button = QPushButton("Notifications")
        self.notifications_button.setObjectName("secondaryButton")
        filter_layout.addWidget(self.notifications_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("secondaryButton")
        filter_layout.addWidget(self.refresh_button)

        main_layout.addWidget(filter_frame)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        form_frame = QFrame()
        form_frame.setObjectName("panelFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(12)

        form_title = QLabel("License Details")
        form_title.setObjectName("sectionTitle")
        form_layout.addWidget(form_title)

        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText("WB-XXXX-XXXX-XXXX")

        generate_button = QPushButton("Generate")
        generate_button.setObjectName("secondaryButton")
        self.generate_button = generate_button

        key_row = QHBoxLayout()
        key_row.addWidget(self.license_key_input)
        key_row.addWidget(generate_button)
        form_layout.addLayout(key_row)

        self.tier_input = QComboBox()
        self.tier_input.addItems([tier for tier in VALID_TIERS])
        form_layout.addWidget(self._labeled("Tier", self.tier_input))

        self.status_input = QComboBox()
        self.status_input.addItems(["active", "expired", "revoked"])
        form_layout.addWidget(self._labeled("Status", self.status_input))

        self.expires_toggle = QCheckBox("Set expiry")
        self.expires_toggle.setChecked(False)
        self.expires_input = QDateTimeEdit()
        self.expires_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.expires_input.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.expires_input.setEnabled(False)

        expires_row = QHBoxLayout()
        expires_row.addWidget(self.expires_toggle)
        expires_row.addWidget(self.expires_input)
        form_layout.addLayout(expires_row)

        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Customer or company name")
        form_layout.addWidget(self._labeled("Customer", self.customer_name_input))

        self.customer_email_input = QLineEdit()
        self.customer_email_input.setPlaceholderText("customer@example.com")
        form_layout.addWidget(self._labeled("Email", self.customer_email_input))

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Internal notes")
        form_layout.addWidget(self._labeled("Notes", self.notes_input))

        button_row = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.create_button.setObjectName("primaryButton")
        self.update_button = QPushButton("Update")
        self.update_button.setObjectName("secondaryButton")
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("secondaryButton")

        button_row.addWidget(self.create_button)
        button_row.addWidget(self.update_button)
        button_row.addWidget(self.clear_button)
        form_layout.addLayout(button_row)

        key_row = QHBoxLayout()
        self.generate_keys_button = QPushButton("Generate Signing Keys")
        self.generate_keys_button.setObjectName("secondaryButton")
        key_row.addWidget(self.generate_keys_button)
        key_row.addStretch(1)
        form_layout.addLayout(key_row)

        form_layout.addStretch(1)

        splitter.addWidget(form_frame)

        table_frame = QFrame()
        table_frame.setObjectName("panelFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)

        table_header = QHBoxLayout()
        table_title = QLabel("Licenses")
        table_title.setObjectName("sectionTitle")
        table_header.addWidget(table_title)
        table_header.addStretch(1)

        self.revoke_button = QPushButton("Revoke")
        self.revoke_button.setObjectName("dangerButton")
        self.expire_button = QPushButton("Expire")
        self.expire_button.setObjectName("secondaryButton")
        self.clear_hwid_button = QPushButton("Clear HWID")
        self.clear_hwid_button.setObjectName("secondaryButton")
        self.verify_button = QPushButton("Verify Binding")
        self.verify_button.setObjectName("secondaryButton")

        table_header.addWidget(self.verify_button)
        table_header.addWidget(self.clear_hwid_button)
        table_header.addWidget(self.expire_button)
        table_header.addWidget(self.revoke_button)

        table_layout.addLayout(table_header)

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

        table_layout.addWidget(self.table)
        splitter.addWidget(table_frame)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        self.setCentralWidget(central)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)

    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self._on_generate)
        self.generate_keys_button.clicked.connect(self._on_generate_keys)
        self.create_button.clicked.connect(self._on_create)
        self.update_button.clicked.connect(self._on_update)
        self.clear_button.clicked.connect(self._clear_form)
        self.refresh_button.clicked.connect(self._refresh_licenses)
        self.revoke_button.clicked.connect(lambda: self._on_status_change("revoked"))
        self.expire_button.clicked.connect(lambda: self._on_status_change("expired"))
        self.clear_hwid_button.clicked.connect(self._on_clear_hwid)
        self.verify_button.clicked.connect(self._on_verify_binding)

        self.expires_toggle.toggled.connect(self.expires_input.setEnabled)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self._search_timer.timeout.connect(self._apply_filters)
        self.feedback_button.clicked.connect(self._open_feedback_viewer)
        self.notifications_button.clicked.connect(self._open_notification_manager)

    def _labeled(self, text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setStyleSheet("color: #374151; font-size: 11px; font-weight: 600;")
        layout.addWidget(label)
        layout.addWidget(widget)
        return container

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

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
        QMessageBox.critical(self, "License Manager", message)
        self._set_status(message)

    def _on_generate(self) -> None:
        self.license_key_input.setText(generate_license_key())

    def _on_generate_keys(self) -> None:
        try:
            public_key, private_key = generate_ed25519_keypair_base64()
        except Exception as exc:
            message = str(exc)
            if "PyNaCl" in message:
                message = (
                    "Key generation failed: PyNaCl is required.\n\n"
                    "Install it with: pip install PyNaCl\n"
                    "Then restart the License Manager."
                )
            self._show_error(message)
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Signing Keys")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        warning = QLabel(
            "Keep the private key secret. "
            "Store it only in the admin/server environment."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #b45309; font-size: 11px;")
        layout.addWidget(warning)

        public_label = QLabel("Public key (use in app)")
        layout.addWidget(public_label)

        public_row = QHBoxLayout()
        public_input = QLineEdit(public_key)
        public_input.setReadOnly(True)
        public_row.addWidget(public_input)
        public_copy = QPushButton("Copy")
        public_copy.setObjectName("secondaryButton")
        public_copy.clicked.connect(lambda: QApplication.clipboard().setText(public_key))
        public_row.addWidget(public_copy)
        layout.addLayout(public_row)

        private_label = QLabel("Private key (server only)")
        layout.addWidget(private_label)

        private_row = QHBoxLayout()
        private_input = QLineEdit(private_key)
        private_input.setReadOnly(True)
        private_row.addWidget(private_input)
        private_copy = QPushButton("Copy")
        private_copy.setObjectName("secondaryButton")
        private_copy.clicked.connect(lambda: QApplication.clipboard().setText(private_key))
        private_row.addWidget(private_copy)
        layout.addLayout(private_row)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(dialog.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        dialog.exec()

    def _on_search_text_changed(self) -> None:
        self._search_timer.start()

    def _refresh_licenses(self) -> None:
        self._set_status("Loading licenses...")

        def load():
            return self._service.list_licenses(limit=500)

        def done(result):
            try:
                self._licenses = result or []
                self._apply_filters()
                self._set_status(f"Loaded {len(self._licenses)} licenses")
            except Exception as exc:
                self._show_error(f"Refresh failed: {exc}")

        self._run_async(load, done)

    def _apply_filters(self) -> None:
        search_text = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentText().strip().lower()

        filtered: List[Dict[str, Any]] = []
        for row in self._licenses:
            if status_filter != "all":
                if (row.get("status") or "").lower() != status_filter:
                    continue

            if search_text:
                haystack = " ".join(
                    [
                        str(row.get("license_key", "")),
                        str(row.get("customer_name", "")),
                        str(row.get("customer_email", "")),
                    ]
                ).lower()
                if search_text not in haystack:
                    continue
            filtered.append(row)

        self._populate_table(filtered)

    def _populate_table(self, rows: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, (_, key) in enumerate(self.TABLE_COLUMNS):
                value = row.get(key, "")
                display = self._format_value(key, value)
                item = QTableWidgetItem(display)
                if key == "license_key":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()

    def _format_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""
        if key in ("expires_at", "last_validated", "created_at", "updated_at"):
            return self._format_datetime(value)
        return str(value)

    def _format_datetime(self, value: Any) -> str:
        if isinstance(value, str) and value:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                return value
        return str(value) if value else ""

    def _on_table_selection(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        license_key_item = self.table.item(row, 0)
        if not license_key_item:
            return
        license_key = license_key_item.text().strip().upper()
        record = next((item for item in self._licenses if item.get("license_key") == license_key), None)
        if not record:
            return

        self.license_key_input.setText(record.get("license_key", ""))
        tier = (record.get("tier") or "standard").lower()
        self.tier_input.setCurrentText(tier)
        status = (record.get("status") or "active").lower()
        self.status_input.setCurrentText(status)

        expires_at = record.get("expires_at")
        if expires_at:
            try:
                dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                self.expires_toggle.setChecked(True)
                qt_dt = QDateTime.fromSecsSinceEpoch(int(dt.timestamp()))
                self.expires_input.setDateTime(qt_dt)
            except ValueError:
                self.expires_toggle.setChecked(False)
        else:
            self.expires_toggle.setChecked(False)

        self.customer_name_input.setText(record.get("customer_name", "") or "")
        self.customer_email_input.setText(record.get("customer_email", "") or "")
        self.notes_input.setText(record.get("notes", "") or "")

    def _collect_form(self) -> Dict[str, Any]:
        expires_at = None
        if self.expires_toggle.isChecked():
            expires_at = self.expires_input.dateTime().toPython()
        return {
            "license_key": self.license_key_input.text().strip().upper(),
            "tier": self.tier_input.currentText().strip().lower(),
            "status": self.status_input.currentText().strip().lower(),
            "expires_at": expires_at,
            "customer_name": self.customer_name_input.text().strip(),
            "customer_email": self.customer_email_input.text().strip(),
            "notes": self.notes_input.text().strip(),
        }

    def _on_create(self) -> None:
        form = self._collect_form()
        if not form["license_key"]:
            form["license_key"] = generate_license_key()
            self.license_key_input.setText(form["license_key"])

        self._set_status("Creating license...")

        def create():
            return self._service.create_license(
                license_key=form["license_key"],
                tier=form["tier"],
                status=form["status"],
                expires_at=form["expires_at"],
                customer_name=form["customer_name"],
                customer_email=form["customer_email"],
                notes=form["notes"],
            )

        def done(_):
            self._set_status("License created")
            self._refresh_licenses()

        self._run_async(create, done)

    def _on_update(self) -> None:
        form = self._collect_form()
        if not form["license_key"]:
            self._show_error("Select a license to update")
            return

        updates = {
            "tier": form["tier"],
            "status": form["status"],
            "expires_at": form["expires_at"],
            "customer_name": form["customer_name"],
            "customer_email": form["customer_email"],
            "notes": form["notes"],
        }

        self._set_status("Updating license...")

        def update():
            return self._service.update_license(form["license_key"], updates)

        def done(_):
            self._set_status("License updated")
            self._refresh_licenses()

        self._run_async(update, done)

    def _on_status_change(self, status: str) -> None:
        license_key = self.license_key_input.text().strip().upper()
        if not license_key:
            self._show_error("Select a license to change status")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Status Change",
            f"Set status to {status} for {license_key}?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._set_status(f"Updating status to {status}...")

        def update():
            return self._service.set_status(license_key, status)

        def done(_):
            self._set_status(f"Status set to {status}")
            self._refresh_licenses()

        self._run_async(update, done)

    def _on_clear_hwid(self) -> None:
        license_key = self.license_key_input.text().strip().upper()
        if not license_key:
            self._show_error("Select a license to clear HWID")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm HWID Clear",
            f"Clear HWID binding for {license_key}?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._set_status("Clearing HWID...")

        def update():
            return self._service.update_license(
                license_key,
                {"hwid": None, "last_validated": None},
            )

        def done(_):
            self._set_status("HWID cleared")
            self._refresh_licenses()

        self._run_async(update, done)

    def _on_verify_binding(self) -> None:
        license_key = self.license_key_input.text().strip().upper()
        if not license_key:
            self._show_error("Select a license to verify")
            return

        self._set_status("Checking latest binding...")

        def load():
            return self._service.get_license(license_key)

        def done(result):
            if not result:
                self._show_error("License not found")
                return
            updated = False
            for idx, row in enumerate(self._licenses):
                if row.get("license_key") == license_key:
                    self._licenses[idx] = result
                    updated = True
                    break
            if not updated:
                self._licenses.append(result)
            self._apply_filters()
            self._set_status("Binding verified")

        self._run_async(load, done)

    def _clear_form(self) -> None:
        self.license_key_input.clear()
        self.tier_input.setCurrentText("standard")
        self.status_input.setCurrentText("active")
        self.expires_toggle.setChecked(False)
        self.expires_input.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.customer_name_input.clear()
        self.customer_email_input.clear()
        self.notes_input.clear()

    def _open_feedback_viewer(self) -> None:
        from ui.admin.feedback_viewer_dialog import FeedbackViewerDialog

        dialog = FeedbackViewerDialog(self)
        dialog.showMaximized()
        dialog.exec()

    def _open_notification_manager(self) -> None:
        from ui.admin.notification_manager_dialog import NotificationManagerDialog

        dialog = NotificationManagerDialog(self)
        dialog.showMaximized()
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Water Balance License Manager")
    window = LicenseManagerWindow()
    window.showMaximized()
    sys.exit(app.exec())
