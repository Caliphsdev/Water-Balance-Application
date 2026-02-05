"""
License Admin Tool - Main Application

Standalone PySide6 application for managing license keys.
Uses Supabase as backend for license storage.

Features:
- Generate new license keys
- View all licenses with filtering
- Activate/Deactivate licenses
- Update license tiers
- Revoke licenses
- Export license list

Author: Water Balance Dashboard Team
"""
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import logging
from datetime import datetime, timedelta
from typing import Optional, List
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QSpinBox, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QGroupBox, QStatusBar, QMenuBar,
    QMenu, QFileDialog, QCheckBox, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QAction, QFont, QClipboard

from core.supabase_client import get_supabase_client, configure_supabase
from core.crypto import generate_license_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# (STYLES)

ADMIN_STYLE = """
QMainWindow {
    background-color: #0d1117;
}

QWidget {
    background-color: #0d1117;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QMenuBar {
    background-color: #161b22;
    color: #e0e0e0;
    border-bottom: 1px solid #30363d;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #21262d;
}

QMenu {
    background-color: #161b22;
    border: 1px solid #30363d;
}

QMenu::item:selected {
    background-color: #21262d;
}

QGroupBox {
    font-weight: 600;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 8px;
    color: #58a6ff;
}

QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    gridline-color: #21262d;
    selection-background-color: #21262d;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #21262d;
}

QTableWidget::item:selected {
    background-color: #21262d;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8892a0;
    font-weight: 600;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #30363d;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    min-height: 20px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #0d1117;
    border: 1px solid #30363d;
    selection-background-color: #21262d;
}

QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    color: #e0e0e0;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #8892a0;
}

QPushButton:pressed {
    background-color: #1a1a2e;
}

QPushButton#primaryButton {
    background-color: #238636;
    border: none;
}

QPushButton#primaryButton:hover {
    background-color: #2ea043;
}

QPushButton#dangerButton {
    background-color: #da3633;
    border: none;
}

QPushButton#dangerButton:hover {
    background-color: #f85149;
}

QStatusBar {
    background-color: #161b22;
    border-top: 1px solid #30363d;
    color: #8892a0;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #8892a0;
}

QLabel#statsLabel {
    font-size: 18px;
    font-weight: 600;
    color: #58a6ff;
}

QFrame#separator {
    background-color: #30363d;
    max-height: 1px;
}

QCheckBox {
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #30363d;
    border-radius: 3px;
    background-color: #0d1117;
}

QCheckBox::indicator:checked {
    background-color: #238636;
    border-color: #238636;
}
"""


# (DATA MODELS)

class License:
    """License data model."""
    
    def __init__(self, data: dict):
        self.id = data.get("id")
        self.license_key = data.get("license_key", "")
        self.hwid = data.get("hwid")
        self.tier = data.get("tier", "standard")
        self.status = data.get("status", "active")
        self.expires_at = data.get("expires_at")
        self.last_validated = data.get("last_validated")
        self.notes = data.get("notes", "")
        self.created_at = data.get("created_at")
    
    @property
    def is_active(self) -> bool:
        return self.status == "active"
    
    @property
    def is_bound(self) -> bool:
        return self.hwid is not None
    
    @property
    def display_key(self) -> str:
        """Masked key for display."""
        if len(self.license_key) > 10:
            return f"{self.license_key[:8]}...{self.license_key[-4:]}"
        return self.license_key


# (WORKER THREADS)

class FetchLicensesWorker(QThread):
    """Worker to fetch licenses from Supabase."""
    
    success = Signal(list)  # List of license dicts
    error = Signal(str)
    
    def __init__(self, filters: dict = None):
        super().__init__()
        self.filters = filters or {}
    
    def run(self):
        try:
            client = get_supabase_client()
            if not client:
                self.error.emit("Failed to connect to Supabase")
                return
            
            # Build query
            query_params = {}
            if self.filters.get("status"):
                query_params["status"] = f"eq.{self.filters['status']}"
            if self.filters.get("tier"):
                query_params["tier"] = f"eq.{self.filters['tier']}"
            
            result = client.select("licenses", query_params)
            
            if result:
                self.success.emit(result)
            else:
                self.success.emit([])
                
        except Exception as e:
            logger.exception("Failed to fetch licenses")
            self.error.emit(str(e))


class CreateLicenseWorker(QThread):
    """Worker to create a new license."""
    
    success = Signal(dict)  # New license data
    error = Signal(str)
    
    def __init__(self, tier: str, expires_days: int, notes: str = ""):
        super().__init__()
        self.tier = tier
        self.expires_days = expires_days
        self.notes = notes
    
    def run(self):
        try:
            client = get_supabase_client()
            if not client:
                self.error.emit("Failed to connect to Supabase")
                return
            
            # Generate key
            license_key = generate_license_key()
            
            # Calculate expiry
            expires_at = None
            if self.expires_days > 0:
                expires_at = (datetime.utcnow() + timedelta(days=self.expires_days)).isoformat() + "Z"
            
            # Create record
            data = {
                "license_key": license_key,
                "tier": self.tier,
                "status": "active",
                "expires_at": expires_at,
                "notes": self.notes
            }
            
            result = client.insert("licenses", data)
            
            if result and len(result) > 0:
                self.success.emit(result[0])
            else:
                self.error.emit("Failed to create license")
                
        except Exception as e:
            logger.exception("Failed to create license")
            self.error.emit(str(e))


class UpdateLicenseWorker(QThread):
    """Worker to update a license."""
    
    success = Signal()
    error = Signal(str)
    
    def __init__(self, license_id: str, updates: dict):
        super().__init__()
        self.license_id = license_id
        self.updates = updates
    
    def run(self):
        try:
            client = get_supabase_client()
            if not client:
                self.error.emit("Failed to connect to Supabase")
                return
            
            result = client.update("licenses", {"id": f"eq.{self.license_id}"}, self.updates)
            
            if result is not None:
                self.success.emit()
            else:
                self.error.emit("Failed to update license")
                
        except Exception as e:
            logger.exception("Failed to update license")
            self.error.emit(str(e))


# (CREATE LICENSE DIALOG)

class CreateLicenseDialog(QDialog):
    """Dialog for creating a new license."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New License")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Create New License")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        # Tier
        self.tier_combo = QComboBox()
        self.tier_combo.addItems(["developer", "premium", "standard", "free_trial"])
        self.tier_combo.setCurrentText("standard")
        form.addRow("Tier:", self.tier_combo)
        
        # Expiry
        expires_layout = QHBoxLayout()
        self.expires_spin = QSpinBox()
        self.expires_spin.setRange(0, 3650)  # Up to 10 years
        self.expires_spin.setValue(365)
        self.expires_spin.setSpecialValueText("Never expires")
        expires_layout.addWidget(self.expires_spin)
        expires_layout.addWidget(QLabel("days"))
        expires_layout.addStretch()
        form.addRow("Expires in:", expires_layout)
        
        # Notes
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes (customer name, etc.)")
        form.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self) -> dict:
        """Get dialog values."""
        return {
            "tier": self.tier_combo.currentText(),
            "expires_days": self.expires_spin.value(),
            "notes": self.notes_edit.text().strip()
        }


# (MAIN WINDOW)

class LicenseAdminWindow(QMainWindow):
    """Main window for License Admin Tool."""
    
    def __init__(self):
        super().__init__()
        
        self._licenses: List[License] = []
        self._workers: List[QThread] = []
        
        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_status_bar()
        
        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_licenses)
        self._refresh_timer.start(30000)  # 30 seconds
        
        # Initial load
        QTimer.singleShot(500, self._refresh_licenses)
    
    def _setup_window(self):
        """Configure main window."""
        self.setWindowTitle("Water Balance - License Admin")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.setStyleSheet(ADMIN_STYLE)
    
    def _setup_menu(self):
        """Set up menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        export_action = QAction("&Export Licenses...", self)
        export_action.triggered.connect(self._export_licenses)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        config_action = QAction("&Configure Supabase...", self)
        config_action.triggered.connect(self._configure_supabase)
        tools_menu.addAction(config_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_ui(self):
        """Set up main UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel("License Management")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Manage license keys for Water Balance Dashboard")
        subtitle.setObjectName("subtitleLabel")
        title_layout.addWidget(subtitle)
        
        header.addLayout(title_layout)
        header.addStretch()
        
        # Stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)
        
        self.total_label = QLabel("0")
        self.total_label.setObjectName("statsLabel")
        stats_layout.addWidget(QLabel("Total:"))
        stats_layout.addWidget(self.total_label)
        
        self.active_label = QLabel("0")
        self.active_label.setObjectName("statsLabel")
        stats_layout.addWidget(QLabel("Active:"))
        stats_layout.addWidget(self.active_label)
        
        header.addLayout(stats_layout)
        
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Filters
        toolbar.addWidget(QLabel("Filter:"))
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "active", "expired", "revoked"])
        self.status_filter.currentTextChanged.connect(self._refresh_licenses)
        toolbar.addWidget(self.status_filter)
        
        self.tier_filter = QComboBox()
        self.tier_filter.addItems(["All Tiers", "developer", "premium", "standard", "free_trial"])
        self.tier_filter.currentTextChanged.connect(self._refresh_licenses)
        toolbar.addWidget(self.tier_filter)
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by key or notes...")
        self.search_edit.textChanged.connect(self._apply_search)
        self.search_edit.setMaximumWidth(300)
        toolbar.addWidget(self.search_edit)
        
        toolbar.addStretch()
        
        # Actions
        refresh_btn = QPushButton("⟳ Refresh")
        refresh_btn.clicked.connect(self._refresh_licenses)
        toolbar.addWidget(refresh_btn)
        
        create_btn = QPushButton("+ Create License")
        create_btn.setObjectName("primaryButton")
        create_btn.clicked.connect(self._create_license)
        toolbar.addWidget(create_btn)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "License Key", "Tier", "Status", "HWID", "Expires", "Last Validated", "Notes", "Actions"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 140)
        self.table.setColumnWidth(7, 140)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
    
    def _setup_status_bar(self):
        """Set up status bar."""
        self.statusBar().showMessage("Ready")
    
    # (DATA OPERATIONS)
    
    def _refresh_licenses(self):
        """Refresh license list from Supabase."""
        self.statusBar().showMessage("Loading licenses...")
        
        # Build filters
        filters = {}
        
        status = self.status_filter.currentText()
        if status != "All Status":
            filters["status"] = status
        
        tier = self.tier_filter.currentText()
        if tier != "All Tiers":
            filters["tier"] = tier
        
        # Fetch
        worker = FetchLicensesWorker(filters)
        worker.success.connect(self._on_licenses_fetched)
        worker.error.connect(self._on_fetch_error)
        worker.finished.connect(lambda: self._workers.remove(worker))
        
        self._workers.append(worker)
        worker.start()
    
    @Slot(list)
    def _on_licenses_fetched(self, data: list):
        """Handle fetched licenses."""
        self._licenses = [License(d) for d in data]
        self._update_table()
        self._update_stats()
        self.statusBar().showMessage(f"Loaded {len(self._licenses)} licenses")
    
    @Slot(str)
    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.statusBar().showMessage(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"Failed to fetch licenses:\n\n{error}")
    
    def _update_table(self):
        """Update table with current licenses."""
        self.table.setRowCount(len(self._licenses))
        
        for row, lic in enumerate(self._licenses):
            # License Key (copyable)
            key_item = QTableWidgetItem(lic.license_key)
            key_item.setData(Qt.ItemDataRole.UserRole, lic.id)
            self.table.setItem(row, 0, key_item)
            
            # Tier
            tier_item = QTableWidgetItem(lic.tier)
            tier_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, tier_item)
            
            # Status
            status_item = QTableWidgetItem(lic.status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if lic.status == "active":
                status_item.setForeground(Qt.GlobalColor.green)
            elif lic.status == "revoked":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 2, status_item)
            
            # HWID
            hwid_text = lic.hwid[:12] + "..." if lic.hwid else "-"
            self.table.setItem(row, 3, QTableWidgetItem(hwid_text))
            
            # Expires
            expires_text = self._format_date(lic.expires_at) if lic.expires_at else "Never"
            self.table.setItem(row, 4, QTableWidgetItem(expires_text))
            
            # Last Validated
            validated_text = self._format_date(lic.last_validated) if lic.last_validated else "-"
            self.table.setItem(row, 5, QTableWidgetItem(validated_text))
            
            # Notes
            self.table.setItem(row, 6, QTableWidgetItem(lic.notes or ""))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            copy_btn = QPushButton("📋")
            copy_btn.setToolTip("Copy Key")
            copy_btn.setMaximumWidth(30)
            copy_btn.clicked.connect(lambda checked, k=lic.license_key: self._copy_key(k))
            actions_layout.addWidget(copy_btn)
            
            if lic.status == "active":
                revoke_btn = QPushButton("⛔")
                revoke_btn.setToolTip("Revoke")
                revoke_btn.setMaximumWidth(30)
                revoke_btn.clicked.connect(lambda checked, i=lic.id: self._revoke_license(i))
                actions_layout.addWidget(revoke_btn)
            else:
                reactivate_btn = QPushButton("✓")
                reactivate_btn.setToolTip("Reactivate")
                reactivate_btn.setMaximumWidth(30)
                reactivate_btn.clicked.connect(lambda checked, i=lic.id: self._reactivate_license(i))
                actions_layout.addWidget(reactivate_btn)
            
            self.table.setCellWidget(row, 7, actions_widget)
    
    def _update_stats(self):
        """Update statistics labels."""
        total = len(self._licenses)
        active = sum(1 for lic in self._licenses if lic.is_active)
        
        self.total_label.setText(str(total))
        self.active_label.setText(str(active))
    
    def _apply_search(self, text: str):
        """Filter table by search text."""
        text = text.lower()
        
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).text().lower()
            notes = self.table.item(row, 6).text().lower()
            
            match = not text or text in key or text in notes
            self.table.setRowHidden(row, not match)
    
    def _format_date(self, iso_date: str) -> str:
        """Format ISO date for display."""
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except:
            return iso_date[:10] if iso_date else "-"
    
    # (ACTIONS)
    
    def _create_license(self):
        """Create a new license."""
        dialog = CreateLicenseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            
            self.statusBar().showMessage("Creating license...")
            
            worker = CreateLicenseWorker(
                tier=values["tier"],
                expires_days=values["expires_days"],
                notes=values["notes"]
            )
            worker.success.connect(self._on_license_created)
            worker.error.connect(self._on_create_error)
            worker.finished.connect(lambda: self._workers.remove(worker))
            
            self._workers.append(worker)
            worker.start()
    
    @Slot(dict)
    def _on_license_created(self, data: dict):
        """Handle license created."""
        license_key = data.get("license_key", "")
        
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(license_key)
        
        QMessageBox.information(
            self,
            "License Created",
            f"New license key created and copied to clipboard:\n\n{license_key}"
        )
        
        self._refresh_licenses()
    
    @Slot(str)
    def _on_create_error(self, error: str):
        """Handle create error."""
        self.statusBar().showMessage(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"Failed to create license:\n\n{error}")
    
    def _copy_key(self, key: str):
        """Copy license key to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(key)
        self.statusBar().showMessage(f"Copied: {key[:20]}...", 3000)
    
    def _revoke_license(self, license_id: str):
        """Revoke a license."""
        reply = QMessageBox.question(
            self,
            "Revoke License",
            "Are you sure you want to revoke this license?\n\n"
            "The user will be blocked from using the application.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._update_license_status(license_id, "revoked")
    
    def _reactivate_license(self, license_id: str):
        """Reactivate a license."""
        self._update_license_status(license_id, "active")
    
    def _update_license_status(self, license_id: str, status: str):
        """Update license status."""
        self.statusBar().showMessage(f"Updating license to {status}...")
        
        worker = UpdateLicenseWorker(license_id, {"status": status})
        worker.success.connect(lambda: self._on_license_updated(status))
        worker.error.connect(self._on_update_error)
        worker.finished.connect(lambda: self._workers.remove(worker))
        
        self._workers.append(worker)
        worker.start()
    
    @Slot()
    def _on_license_updated(self, status: str):
        """Handle license updated."""
        self.statusBar().showMessage(f"License {status}")
        self._refresh_licenses()
    
    @Slot(str)
    def _on_update_error(self, error: str):
        """Handle update error."""
        self.statusBar().showMessage(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"Failed to update license:\n\n{error}")
    
    def _export_licenses(self):
        """Export licenses to CSV."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Licenses",
            "licenses.csv",
            "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("License Key,Tier,Status,HWID,Expires,Last Validated,Notes\n")
                    for lic in self._licenses:
                        f.write(f'"{lic.license_key}",{lic.tier},{lic.status},'
                                f'"{lic.hwid or ""}",{lic.expires_at or ""},{lic.last_validated or ""},'
                                f'"{lic.notes or ""}"\n')
                
                QMessageBox.information(self, "Export Complete", f"Exported {len(self._licenses)} licenses")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Failed to export:\n\n{e}")
    
    def _configure_supabase(self):
        """Configure Supabase connection."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Supabase")
        dialog.setModal(True)
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        form = QFormLayout()
        
        url_edit = QLineEdit()
        url_edit.setPlaceholderText("https://xxxxx.supabase.co")
        form.addRow("Supabase URL:", url_edit)
        
        key_edit = QLineEdit()
        key_edit.setPlaceholderText("anon-key or service-role-key")
        key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key:", key_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = url_edit.text().strip()
            key = key_edit.text().strip()
            
            if url and key:
                configure_supabase(url, key)
                self._refresh_licenses()
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About License Admin",
            "Water Balance Dashboard - License Admin Tool\n\n"
            "Version 1.0.0\n\n"
            "Manage license keys for the Water Balance Dashboard application.\n\n"
            "© 2026 Water Balance Team"
        )


# (MAIN)

def main():
    """Run the License Admin application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("License Admin")
    
    # Check for environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    
    if supabase_url and supabase_key:
        configure_supabase(supabase_url, supabase_key)
    
    window = LicenseAdminWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
