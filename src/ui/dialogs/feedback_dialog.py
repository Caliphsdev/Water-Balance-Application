"""
Feedback Dialog

Dialog for submitting bug reports, feature requests, and general feedback.
Posts submissions to Supabase feature_requests table.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QLineEdit, QComboBox,
    QFrame, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QSize
from PySide6.QtGui import QFont, QIcon

from core.hwid import get_hwid, get_hwid_display
from services.license_service import get_license_service
from services.feedback_service import get_feedback_service

logger = logging.getLogger(__name__)


# (ENUMS AND DATA)

class FeedbackType(Enum):
    """Type of feedback submission."""
    BUG = "bug"
    FEATURE = "feature"
    GENERAL = "general"


@dataclass
class FeedbackSubmission:
    """Feedback data to submit."""
    type: FeedbackType
    title: str
    description: str
    email: Optional[str] = None
    hwid: Optional[str] = None
    license_key: Optional[str] = None
    app_version: Optional[str] = None


# (STYLES)

FEEDBACK_DIALOG_STYLE = """
QDialog {
    background-color: #16213e;
}

QLabel {
    color: #e0e0e0;
}

QLabel#dialogTitle {
    font-size: 18px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#dialogSubtitle {
    font-size: 12px;
    color: #8892a0;
}

QLabel#fieldLabel {
    font-size: 12px;
    font-weight: 500;
    color: #c0c0c0;
}

QLabel#requiredMark {
    color: #f85149;
    font-weight: bold;
}

QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #58a6ff;
}

QComboBox:focus {
    border-color: #58a6ff;
    outline: none;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    image: none;
    width: 0;
}

QComboBox QAbstractItemView {
    background-color: #0d1117;
    border: 1px solid #30363d;
    selection-background-color: #21262d;
    color: #e0e0e0;
}

QLineEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
}

QLineEdit:hover {
    border-color: #58a6ff;
}

QLineEdit:focus {
    border-color: #58a6ff;
}

QLineEdit::placeholder {
    color: #6e7681;
}

QTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
}

QTextEdit:hover {
    border-color: #58a6ff;
}

QTextEdit:focus {
    border-color: #58a6ff;
}

QPushButton#primaryButton {
    background-color: #238636;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #2ea043;
}

QPushButton#primaryButton:pressed {
    background-color: #1a7f37;
}

QPushButton#primaryButton:disabled {
    background-color: #21262d;
    color: #6e7681;
}

QPushButton#secondaryButton {
    background-color: transparent;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px 24px;
    color: #c0c0c0;
    font-size: 13px;
}

QPushButton#secondaryButton:hover {
    background-color: #21262d;
    border-color: #8892a0;
}

QFrame#separator {
    background-color: #30363d;
    max-height: 1px;
}

QLabel#charCount {
    font-size: 11px;
    color: #6e7681;
}

QLabel#charCount[warning="true"] {
    color: #d29922;
}

QLabel#charCount[error="true"] {
    color: #f85149;
}
"""


# (WORKER THREAD)

class SubmitWorker(QThread):
    """Worker thread for submitting feedback to Supabase."""
    
    success = Signal()
    error = Signal(str)
    
    def __init__(self, submission: FeedbackSubmission):
        super().__init__()
        self.submission = submission
    
    def run(self):
        """Submit feedback in background."""
        try:
            service = get_feedback_service()
            success = service.submit_feedback(
                feedback_type=self.submission.type.value,
                title=self.submission.title,
                description=self.submission.description,
                email=self.submission.email
            )
            if success:
                logger.info(f"Feedback submitted successfully: {self.submission.title}")
                self.success.emit()
            else:
                self.error.emit(service.last_error or "Failed to submit feedback")
                
        except Exception as e:
            logger.exception("Error submitting feedback")
            self.error.emit(str(e))


# (FEEDBACK DIALOG)

class FeedbackDialog(QDialog):
    """
    Dialog for submitting bug reports, feature requests, and general feedback.
    
    Features:
    - Type selector (Bug, Feature Request, General)
    - Title and description fields
    - Optional email for follow-up
    - Automatic HWID and license info attachment
    - Character count with limits
    """
    
    # Field limits
    TITLE_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 2000
    
    def __init__(self, parent=None, app_version: str = "1.0.0"):
        super().__init__(parent)
        
        self.app_version = app_version
        self._worker: Optional[SubmitWorker] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Send Feedback")
        self.setModal(True)
        self.setMinimumSize(500, 550)
        self.setMaximumSize(600, 700)
        self.setStyleSheet(FEEDBACK_DIALOG_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title = QLabel("Send Feedback")
        title.setObjectName("dialogTitle")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Help us improve the Water Balance Dashboard")
        subtitle.setObjectName("dialogSubtitle")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)
        
        # Type selector
        type_layout = QVBoxLayout()
        type_layout.setSpacing(6)
        
        type_label = self._create_field_label("Type", required=True)
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("🐛  Bug Report", FeedbackType.BUG)
        self.type_combo.addItem("💡  Feature Request", FeedbackType.FEATURE)
        self.type_combo.addItem("💬  General Feedback", FeedbackType.GENERAL)
        type_layout.addWidget(self.type_combo)
        
        layout.addLayout(type_layout)
        
        # Title field
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        
        title_label = self._create_field_label("Title", required=True)
        title_layout.addWidget(title_label)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Brief summary of your feedback")
        self.title_edit.setMaxLength(self.TITLE_MAX_LENGTH)
        title_layout.addWidget(self.title_edit)
        
        self.title_count = QLabel(f"0/{self.TITLE_MAX_LENGTH}")
        self.title_count.setObjectName("charCount")
        self.title_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.title_count)
        
        layout.addLayout(title_layout)
        
        # Description field
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(6)
        
        desc_label = self._create_field_label("Description", required=True)
        desc_layout.addWidget(desc_label)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText(
            "Please provide as much detail as possible.\n\n"
            "For bugs: Steps to reproduce, expected vs actual behavior\n"
            "For features: Use case and benefits"
        )
        self.desc_edit.setMinimumHeight(150)
        desc_layout.addWidget(self.desc_edit)
        
        self.desc_count = QLabel(f"0/{self.DESCRIPTION_MAX_LENGTH}")
        self.desc_count.setObjectName("charCount")
        self.desc_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        desc_layout.addWidget(self.desc_count)
        
        layout.addLayout(desc_layout)
        
        # Email field (optional)
        email_layout = QVBoxLayout()
        email_layout.setSpacing(6)
        
        email_label = self._create_field_label("Email (optional)")
        email_layout.addWidget(email_label)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("your@email.com - for follow-up questions")
        email_layout.addWidget(self.email_edit)
        
        layout.addLayout(email_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setIcon(QIcon(":/icons/cancel_icon.svg"))
        cancel_btn.setIconSize(QSize(14, 14))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        self.submit_btn = QPushButton("Submit Feedback")
        self.submit_btn.setObjectName("primaryButton")
        self.submit_btn.clicked.connect(self._on_submit)
        button_layout.addWidget(self.submit_btn)
        
        layout.addLayout(button_layout)
    
    def _create_field_label(self, text: str, required: bool = False) -> QLabel:
        """Create a field label, optionally with required marker."""
        if required:
            label = QLabel(f"{text} <span style='color: #f85149;'>*</span>")
        else:
            label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.title_edit.textChanged.connect(self._on_title_changed)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
    
    # (VALIDATION)
    
    def _on_title_changed(self, text: str):
        """Handle title text change."""
        length = len(text)
        self.title_count.setText(f"{length}/{self.TITLE_MAX_LENGTH}")
        
        # Update styling based on length
        if length >= self.TITLE_MAX_LENGTH:
            self.title_count.setProperty("error", True)
        elif length >= self.TITLE_MAX_LENGTH * 0.9:
            self.title_count.setProperty("warning", True)
            self.title_count.setProperty("error", False)
        else:
            self.title_count.setProperty("warning", False)
            self.title_count.setProperty("error", False)
        
        self.title_count.style().unpolish(self.title_count)
        self.title_count.style().polish(self.title_count)
        
        self._update_submit_button()
    
    def _on_desc_changed(self):
        """Handle description text change."""
        text = self.desc_edit.toPlainText()
        length = len(text)
        self.desc_count.setText(f"{length}/{self.DESCRIPTION_MAX_LENGTH}")
        
        # Enforce max length
        if length > self.DESCRIPTION_MAX_LENGTH:
            cursor = self.desc_edit.textCursor()
            pos = cursor.position()
            self.desc_edit.setPlainText(text[:self.DESCRIPTION_MAX_LENGTH])
            cursor.setPosition(min(pos, self.DESCRIPTION_MAX_LENGTH))
            self.desc_edit.setTextCursor(cursor)
            length = self.DESCRIPTION_MAX_LENGTH
        
        # Update styling
        if length >= self.DESCRIPTION_MAX_LENGTH:
            self.desc_count.setProperty("error", True)
        elif length >= self.DESCRIPTION_MAX_LENGTH * 0.9:
            self.desc_count.setProperty("warning", True)
            self.desc_count.setProperty("error", False)
        else:
            self.desc_count.setProperty("warning", False)
            self.desc_count.setProperty("error", False)
        
        self.desc_count.style().unpolish(self.desc_count)
        self.desc_count.style().polish(self.desc_count)
        
        self._update_submit_button()
    
    def _update_submit_button(self):
        """Enable/disable submit button based on form validity."""
        title = self.title_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip()
        
        is_valid = len(title) >= 5 and len(desc) >= 20
        self.submit_btn.setEnabled(is_valid)
    
    # (SUBMISSION)
    
    def _on_submit(self):
        """Handle submit button click."""
        # Validate
        title = self.title_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip()
        email = self.email_edit.text().strip() or None
        
        if len(title) < 5:
            QMessageBox.warning(self, "Invalid Input", "Title must be at least 5 characters.")
            return
        
        if len(desc) < 20:
            QMessageBox.warning(self, "Invalid Input", "Description must be at least 20 characters.")
            return
        
        # Get type
        feedback_type = self.type_combo.currentData()
        
        # Get license info
        license_service = get_license_service()
        license_key = license_service._license_key if license_service else None
        
        # Create submission
        submission = FeedbackSubmission(
            type=feedback_type,
            title=title,
            description=desc,
            email=email,
            hwid=get_hwid(),
            license_key=license_key,
            app_version=self.app_version
        )
        
        # Disable UI
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Submitting...")
        
        # Submit in background
        self._worker = SubmitWorker(submission)
        self._worker.success.connect(self._on_submit_success)
        self._worker.error.connect(self._on_submit_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
    
    @Slot()
    def _on_submit_success(self):
        """Handle successful submission."""
        QMessageBox.information(
            self,
            "Thank You!",
            "Your feedback has been submitted successfully.\n\n"
            "We appreciate you taking the time to help improve the application."
        )
        self.accept()
    
    @Slot(str)
    def _on_submit_error(self, error: str):
        """Handle submission error."""
        QMessageBox.critical(
            self,
            "Submission Failed",
            f"Failed to submit feedback:\n\n{error}\n\n"
            "Please check your internet connection and try again."
        )
    
    @Slot()
    def _on_worker_finished(self):
        """Handle worker completion."""
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Submit Feedback")
        self._worker = None


# (MODULE TEST)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    dialog = FeedbackDialog(app_version="2.0.0-beta")
    result = dialog.exec()
    
    logger.info("Dialog result: %s", "Accepted" if result else "Rejected")
