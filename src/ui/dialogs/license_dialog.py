"""
License Activation Dialog

Modal dialog for entering and activating license keys.
Shows HWID, validates online, and provides clear feedback.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont, QIcon, QPixmap

from services.license_service import get_license_service, LicenseStatus

logger = logging.getLogger(__name__)


# (STYLES)

LICENSE_DIALOG_STYLE = """
/* ============================================================================
   License Activation Dialog - Commercial Grade Design
   Based on Primer Design System (GitHub) + Carbon Design System (IBM)
   ============================================================================ */

QDialog#LicenseDialog {
    background-color: #0D1117;
}

/* --------------------------------------------------------------------------
   HEADER SECTION - Hero area with branding
   -------------------------------------------------------------------------- */
QFrame#headerFrame {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #161B22,
        stop: 1 #0D1117
    );
    border: 1px solid #30363D;
    border-radius: 12px;
}

QLabel#iconLabel {
    font-size: 48px;
    color: #58A6FF;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: 600;
    color: #E6EDF3;
    letter-spacing: -0.5px;
}

QLabel#subtitleLabel {
    font-size: 13px;
    font-weight: 400;
    color: #8B949E;
    line-height: 1.5;
}

/* --------------------------------------------------------------------------
   INPUT SECTION - License key entry
   -------------------------------------------------------------------------- */
QFrame#inputFrame {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
}

QLabel#fieldLabel {
    font-size: 12px;
    font-weight: 600;
    color: #8B949E;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

QLineEdit#licenseKeyInput {
    background-color: #0D1117;
    border: 2px solid #30363D;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 18px;
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-weight: 500;
    color: #E6EDF3;
    letter-spacing: 3px;
    selection-background-color: #388BFD;
}

QLineEdit#licenseKeyInput:focus {
    border-color: #58A6FF;
    background-color: #161B22;
}

QLineEdit#licenseKeyInput:hover {
    border-color: #484F58;
}

QLineEdit#licenseKeyInput:disabled {
    background-color: #21262D;
    color: #484F58;
    border-color: #21262D;
}

/* Format hint below license input */
QLabel#formatHint {
    font-size: 11px;
    color: #6E7681;
    font-style: italic;
    padding-left: 4px;
}

/* Machine ID display */
QFrame#hwidFrame {
    background-color: #0D1117;
    border: 1px solid #21262D;
    border-radius: 6px;
}

QLabel#hwidLabel {
    font-size: 11px;
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
    color: #6E7681;
    letter-spacing: 0.5px;
}

QLabel#hwidCopyHint {
    font-size: 10px;
    color: #484F58;
    font-style: italic;
}

/* --------------------------------------------------------------------------
   STATUS FEEDBACK - Visual feedback area
   -------------------------------------------------------------------------- */
QFrame#statusFrame {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
}

QLabel#statusIcon {
    font-size: 18px;
}

QLabel#statusLabel {
    font-size: 13px;
    font-weight: 500;
    color: #8B949E;
}

/* Status variants */
QFrame#statusFrame[status="success"] {
    background-color: rgba(35, 134, 54, 0.15);
    border-color: #238636;
}

QFrame#statusFrame[status="error"] {
    background-color: rgba(248, 81, 73, 0.15);
    border-color: #F85149;
}

QFrame#statusFrame[status="warning"] {
    background-color: rgba(210, 153, 34, 0.15);
    border-color: #D29922;
}

QFrame#statusFrame[status="info"] {
    background-color: rgba(88, 166, 255, 0.1);
    border-color: #58A6FF;
}

QLabel#statusLabel[status="success"] { color: #3FB950; }
QLabel#statusLabel[status="error"] { color: #F85149; }
QLabel#statusLabel[status="warning"] { color: #D29922; }
QLabel#statusLabel[status="info"] { color: #58A6FF; }

/* --------------------------------------------------------------------------
   BUTTONS - Primary and secondary actions
   -------------------------------------------------------------------------- */
QPushButton#activateButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #238636,
        stop: 1 #1A7F37
    );
    border: none;
    border-radius: 8px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: 600;
    color: #FFFFFF;
    min-width: 160px;
}

QPushButton#activateButton:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #2EA043,
        stop: 1 #238636
    );
}

QPushButton#activateButton:pressed {
    background-color: #1A7F37;
}

QPushButton#activateButton:disabled {
    background: #21262D;
    color: #484F58;
}

QPushButton#cancelButton {
    background-color: transparent;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 500;
    color: #8B949E;
    min-width: 100px;
}

QPushButton#cancelButton:hover {
    background-color: #21262D;
    border-color: #8B949E;
    color: #E6EDF3;
}

QPushButton#cancelButton:pressed {
    background-color: #30363D;
}

/* --------------------------------------------------------------------------
   HELP LINK - Support information
   -------------------------------------------------------------------------- */
QLabel#helpLink {
    font-size: 12px;
    color: #58A6FF;
}

QLabel#helpLink:hover {
    color: #79C0FF;
    text-decoration: underline;
}
"""


# (ACTIVATION WORKER)

class ActivationWorker(QObject):
    """Worker for background license activation."""
    
    finished = Signal(object)  # LicenseStatus
    error = Signal(str)
    
    def __init__(self, license_key: str):
        super().__init__()
        self.license_key = license_key
    
    def run(self):
        """Perform activation in background thread."""
        try:
            service = get_license_service()
            status = service.activate(self.license_key)
            self.finished.emit(status)
        except Exception as e:
            logger.error(f"Activation worker error: {e}")
            self.error.emit(str(e))


# (LICENSE DIALOG)

class LicenseDialog(QDialog):
    """
    Dialog for license key activation.
    
    Shows:
    - License key input field
    - Machine HWID (read-only)
    - Activation status and feedback
    """
    
    activation_successful = Signal(str)  # Emits tier on success
    
    def __init__(self, parent=None, allow_cancel: bool = True):
        """
        Initialize license dialog.
        
        Args:
            parent: Parent widget.
            allow_cancel: Whether to show cancel button.
        """
        super().__init__(parent)
        self.allow_cancel = allow_cancel
        self._worker_thread: Optional[QThread] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the dialog UI with commercial-grade design."""
        self.setObjectName("LicenseDialog")
        self.setWindowTitle("Activate License")
        self.setFixedSize(520, 580)  # Taller to fit status message
        self.setModal(True)
        self.setStyleSheet(LICENSE_DIALOG_STYLE)
        
        # Main layout with generous margins
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # ══════════════════════════════════════════════════════════════════
        # HEADER - Brand and welcome message
        # ══════════════════════════════════════════════════════════════════
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setMinimumHeight(100)  # Ensure consistent height
        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(24, 24, 24, 24)
        
        # App icon/logo
        icon_label = QLabel("🔐")
        icon_label.setObjectName("iconLabel")
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        
        title_label = QLabel("License Activation")
        title_label.setObjectName("titleLabel")
        text_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Activate Water Balance Dashboard to unlock all features")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setWordWrap(True)
        text_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(text_layout, stretch=1)
        layout.addWidget(header_frame)
        
        # ══════════════════════════════════════════════════════════════════
        # INPUT SECTION - License key and machine ID
        # ══════════════════════════════════════════════════════════════════
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_frame.setMinimumHeight(220)  # Ensure consistent height
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(16)
        input_layout.setContentsMargins(24, 24, 24, 24)
        
        # License key field
        key_label = QLabel("LICENSE KEY")
        key_label.setObjectName("fieldLabel")
        key_label.setMinimumHeight(20)
        input_layout.addWidget(key_label)
        
        self.key_input = QLineEdit()
        self.key_input.setObjectName("licenseKeyInput")
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_input.setMaxLength(50)
        self.key_input.setClearButtonEnabled(True)
        self.key_input.setMinimumHeight(50)  # Ensure consistent height
        input_layout.addWidget(self.key_input)
        
        # Format hint
        format_hint = QLabel("Format: XXXX-XXXX-XXXX-XXXX (include dashes)")
        format_hint.setObjectName("formatHint")
        input_layout.addWidget(format_hint)
        
        # Machine ID section with frame
        input_layout.addSpacing(8)
        
        hwid_label = QLabel("MACHINE ID")
        hwid_label.setObjectName("fieldLabel")
        hwid_label.setMinimumHeight(20)
        input_layout.addWidget(hwid_label)
        
        hwid_frame = QFrame()
        hwid_frame.setObjectName("hwidFrame")
        hwid_frame.setMinimumHeight(60)  # Ensure consistent height
        hwid_layout = QVBoxLayout(hwid_frame)
        hwid_layout.setSpacing(4)
        hwid_layout.setContentsMargins(12, 12, 12, 12)
        
        service = get_license_service()
        self.hwid_label = QLabel(service.hwid_display)
        self.hwid_label.setObjectName("hwidLabel")
        self.hwid_label.setMinimumHeight(18)
        self.hwid_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        hwid_layout.addWidget(self.hwid_label)
        
        hwid_hint = QLabel("Click to select • Ctrl+C to copy")
        hwid_hint.setObjectName("hwidCopyHint")
        hwid_hint.setMinimumHeight(16)
        hwid_layout.addWidget(hwid_hint)
        
        input_layout.addWidget(hwid_frame)
        
        layout.addWidget(input_frame)
        
        # ══════════════════════════════════════════════════════════════════
        # STATUS SECTION - Feedback and validation (separate from input frame)
        # ══════════════════════════════════════════════════════════════════
        self.status_frame = QFrame()
        self.status_frame.setObjectName("statusFrame")
        self.status_frame.setVisible(False)
        self.status_frame.setMinimumHeight(56)
        self.status_frame.setMaximumHeight(56)
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setSpacing(12)
        status_layout.setContentsMargins(16, 12, 16, 12)
        
        self.status_icon = QLabel("ℹ️")
        self.status_icon.setObjectName("statusIcon")
        self.status_icon.setFixedSize(24, 24)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label, stretch=1)
        
        layout.addWidget(self.status_frame)
        
        # Spacer
        layout.addStretch()
        
        # ══════════════════════════════════════════════════════════════════
        # FOOTER - Actions and help
        # ══════════════════════════════════════════════════════════════════
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(16)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.setObjectName("cancelButton")
        button_layout.addWidget(self.exit_button)
        
        button_layout.addStretch()
        
        self.activate_button = QPushButton("Activate License")
        self.activate_button.setObjectName("activateButton")
        self.activate_button.setDefault(True)
        self.activate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.activate_button)
        
        footer_layout.addLayout(button_layout)
        
        # Help text
        help_label = QLabel("Need help? Contact support@example.com")
        help_label.setObjectName("helpLink")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(help_label)
        
        layout.addLayout(footer_layout)
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.activate_button.clicked.connect(self._on_activate)
        self.key_input.returnPressed.connect(self._on_activate)
        self.key_input.textChanged.connect(self._on_key_changed)
        self.exit_button.clicked.connect(self._on_exit_clicked)
    
    def _on_exit_clicked(self):
        """Handle exit button - reject dialog (will close app if no license)."""
        self.reject()
    
    def _on_key_changed(self, text: str):
        """Handle license key text changes."""
        # Convert to uppercase only (don't auto-format to allow various key formats)
        upper_text = text.upper()
        if upper_text != text:
            cursor_pos = self.key_input.cursorPosition()
            self.key_input.blockSignals(True)
            self.key_input.setText(upper_text)
            self.key_input.setCursorPosition(cursor_pos)
            self.key_input.blockSignals(False)
        
        # Enable activate button when key has reasonable length
        self.activate_button.setEnabled(len(text.strip()) >= 10)
    
    def _on_activate(self):
        """Handle activate button click."""
        license_key = self.key_input.text().strip()
        
        if len(license_key) < 10:
            self._show_status("Please enter a valid license key", "warning")
            return
        
        # Disable inputs during activation
        self.key_input.setEnabled(False)
        self.activate_button.setEnabled(False)
        self._show_status("Activating license...", "info")
        
        # Run activation in background
        self._worker_thread = QThread()
        self._worker = ActivationWorker(license_key)
        self._worker.moveToThread(self._worker_thread)
        
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_activation_complete)
        self._worker.error.connect(self._on_activation_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)
        
        self._worker_thread.start()
    
    def _on_activation_complete(self, status: LicenseStatus):
        """Handle activation completion."""
        self.key_input.setEnabled(True)
        self.activate_button.setEnabled(True)
        
        if status.is_valid:
            self._show_status(
                f"✓ License activated! Tier: {status.tier.title()}", 
                "success"
            )
            self.activation_successful.emit(status.tier)
            
            # Close dialog after brief delay
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, self.accept)
        else:
            self._show_status(f"✗ {status.message}", "error")
    
    def _on_activation_error(self, error: str):
        """Handle activation error."""
        self.key_input.setEnabled(True)
        self.activate_button.setEnabled(True)
        self._show_status(f"✗ Error: {error}", "error")
    
    def _show_status(self, message: str, status_type: str = "info"):
        """
        Show status message with icon and styled feedback.
        
        Args:
            message: Status message to display.
            status_type: 'info', 'success', 'error', or 'warning'.
        """
        # Status icons for visual feedback
        icons = {
            'info': '⏳',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        }
        
        self.status_frame.setVisible(True)
        self.status_icon.setText(icons.get(status_type, 'ℹ️'))
        self.status_label.setText(message)
        
        # Update frame and label status properties for QSS styling
        self.status_frame.setProperty("status", status_type)
        self.status_label.setProperty("status", status_type)
        
        # Force style refresh
        self.status_frame.style().unpolish(self.status_frame)
        self.status_frame.style().polish(self.status_frame)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def closeEvent(self, event):
        """Handle dialog close."""
        if not self.allow_cancel:
            # Don't allow closing without activation
            event.ignore()
            return
        
        # Clean up worker thread
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(1000)
        
        super().closeEvent(event)


# (BLOCKED DIALOG)

class LicenseBlockedDialog(QDialog):
    """
    Dialog shown when license is blocked (expired/invalid).
    
    Provides options to:
    - Enter new license key
    - Exit application
    """
    
    def __init__(self, status: LicenseStatus, parent=None):
        """
        Initialize blocked dialog.
        
        Args:
            status: Current license status.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.status = status
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setObjectName("LicenseDialog")
        self.setWindowTitle("License Required")
        self.setFixedSize(420, 280)
        self.setModal(True)
        self.setStyleSheet(LICENSE_DIALOG_STYLE)
        
        # Prevent closing
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Icon and title
        title_layout = QHBoxLayout()
        
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px;")
        title_layout.addWidget(icon_label)
        
        title_text = QVBoxLayout()
        
        title = QLabel(self._get_title())
        title.setObjectName("titleLabel")
        title_text.addWidget(title)
        
        message = QLabel(self.status.message)
        message.setObjectName("subtitleLabel")
        message.setWordWrap(True)
        title_text.addWidget(message)
        
        title_layout.addLayout(title_text)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Additional info
        if self.status.status == LicenseStatus.EXPIRED:
            info = QLabel(
                "Your offline license token has expired.\n"
                "Please connect to the internet and restart the application,\n"
                "or enter a new license key."
            )
        elif self.status.status == LicenseStatus.HWID_MISMATCH:
            info = QLabel(
                "This license is registered to a different computer.\n"
                "Please contact support if you need to transfer your license."
            )
        else:
            info = QLabel(
                "Please enter a valid license key to continue."
            )
        
        info.setStyleSheet("color: #8892a0; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        exit_button = QPushButton("Exit")
        exit_button.setObjectName("cancelButton")
        exit_button.clicked.connect(self._on_exit)
        button_layout.addWidget(exit_button)
        
        button_layout.addStretch()
        
        activate_button = QPushButton("Enter License Key")
        activate_button.setObjectName("activateButton")
        activate_button.clicked.connect(self._on_activate)
        button_layout.addWidget(activate_button)
        
        layout.addLayout(button_layout)
    
    def _get_title(self) -> str:
        """Get title based on status."""
        titles = {
            LicenseStatus.EXPIRED: "License Expired",
            LicenseStatus.INVALID: "Invalid License",
            LicenseStatus.NOT_ACTIVATED: "License Required",
            LicenseStatus.HWID_MISMATCH: "Hardware Mismatch",
            LicenseStatus.REVOKED: "License Revoked",
        }
        return titles.get(self.status.status, "License Error")
    
    def _on_exit(self):
        """Handle exit button."""
        QApplication.quit()
    
    def _on_activate(self):
        """Handle activate button - show license dialog."""
        dialog = LicenseDialog(self, allow_cancel=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept()


# (HELPER FUNCTIONS)

def check_license_or_activate(parent=None) -> bool:
    """
    Check license and show activation dialog if needed.
    
    Use this at app startup to enforce licensing.
    
    Args:
        parent: Parent widget for dialogs.
        
    Returns:
        True if licensed, False if user cancelled/exited.
    """
    service = get_license_service()
    status = service.validate(try_refresh=True)
    
    if status.is_valid:
        return True
    
    if status.status == LicenseStatus.NOT_ACTIVATED:
        # First time - show activation dialog
        dialog = LicenseDialog(parent, allow_cancel=False)
        return dialog.exec() == QDialog.DialogCode.Accepted
    else:
        # Blocked - show blocked dialog
        dialog = LicenseBlockedDialog(status, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted


# (MODULE TEST)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Test license dialog
    dialog = LicenseDialog(allow_cancel=True)
    result = dialog.exec()
    
    print(f"Dialog result: {'Accepted' if result else 'Rejected'}")
    
    sys.exit(0)
