"""
Notification Manager Dialog

Create and review notifications stored in Supabase.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QDateTime, QObject, QThread, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDateTimeEdit,
    QDialog,
    QFileDialog,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import get_resource_path
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
    TIERS = ["developer", "premium", "standard", "free_trial", "customer"]
    TEMPLATES = {
        "Standard Update": {"sections": ["Summary", "Details", "Action", "Support"]},
        "Maintenance Notice": {"sections": ["Summary", "Impact", "Timeline", "Action", "Support"]},
        "Incident Alert": {"sections": ["Summary", "Impact", "Current Status", "Action", "Support"]},
        "Release Announcement": {"sections": ["Summary", "Highlights", "Action", "Support"]},
    }
    _LIGHT_COLOR_PATTERN = re.compile(
        r"(color\s*:\s*(?:#fff(?:fff)?|white|rgb\(\s*2[0-5]{2}\s*,\s*2[0-5]{2}\s*,\s*2[0-5]{2}\s*\)|rgba\(\s*2[0-5]{2}\s*,\s*2[0-5]{2}\s*,\s*2[0-5]{2}\s*,\s*(?:0?\.\d+|1(?:\.0+)?)\s*\)))",
        re.IGNORECASE,
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = get_license_admin_service()
        self._threads: List[QThread] = []
        self._workers: List[AsyncWorker] = []
        self._rows: List[Dict[str, Any]] = []
        self._filtered_rows: List[Dict[str, Any]] = []
        self._selected_notification_id: Optional[str] = None
        self._sanitizing_editor = False

        self.setWindowTitle("Notification Manager")
        self.setMinimumSize(1120, 680)
        self.resize(1220, 780)
        icon_path = get_resource_path("src/ui/resources/icons/Water Balance.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet(
            """
            QDialog { background-color: #f3f6fb; }
            QLabel { color: #0f172a; }
            QFrame#headerCard { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e293b); border-radius: 12px; }
            QFrame#panelCard { background-color: #ffffff; border: 1px solid #d6dfeb; border-radius: 10px; }
            QScrollArea#composeScroll { background: #ffffff; border: none; }
            QScrollArea#composeScroll > QWidget > QWidget { background: #ffffff; color: #0f172a; }
            QWidget#composeSurface { background: #ffffff; color: #0f172a; }
            QFrame#tiersCard { background: #ffffff; border: 1px solid #d6dfeb; border-radius: 8px; }
            QLabel#headerTitle { color: #ffffff; font-size: 18px; font-weight: 700; }
            QLabel#headerSubtitle { color: #d5e1f4; font-size: 11px; font-weight: 500; }
            QPushButton#modeButton { background: #e6edf8; color: #0f172a; border: 1px solid #bfccde; border-radius: 8px; min-height: 30px; padding: 0 14px; font-weight: 700; }
            QPushButton#modeButton[active="true"] { background: #1d4ed8; color: #ffffff; border-color: #1d4ed8; }
            QLineEdit, QComboBox, QDateTimeEdit, QTextEdit, QTextBrowser { background-color: #ffffff; color: #0f172a; border: 1px solid #c2cfdf; border-radius: 6px; padding: 6px 10px; font-size: 12px; }
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QTextEdit:focus { border: 1px solid #2563eb; }
            QTextEdit#bodyEditor { min-height: 220px; }
            QTextBrowser#previewBox { background: #f8fbff; color: #0f172a; border: 1px dashed #c2cfdf; }
            QLabel#sectionLabel { color: #1e293b; font-size: 12px; font-weight: 700; }
            QLabel#helpText { color: #334155; font-size: 11px; font-weight: 500; }
            QLabel#statusError { color: #b42318; font-size: 11px; font-weight: 700; }
            QLabel#statusSuccess { color: #166534; font-size: 11px; font-weight: 700; }
            QTableWidget { color: #0f172a; background: #ffffff; selection-background-color: #dbeafe; selection-color: #0f172a; border: 1px solid #d6dfeb; }
            QHeaderView::section { background: #eef3fb; color: #0f172a; border: 1px solid #d6dfeb; padding: 6px; font-size: 11px; font-weight: 700; }
            QPushButton { min-height: 30px; border-radius: 6px; border: 1px solid #bfccde; background: #e6edf8; color: #0f172a; padding: 0 12px; font-size: 12px; font-weight: 700; }
            QPushButton#primaryButton { background: #1d4ed8; color: #ffffff; border-color: #1d4ed8; }
            QPushButton#primaryButton:hover { background: #1e40af; }
            QPushButton#ghostButton:hover { background: #d7e3f5; }
            QPushButton#dangerButton { background: #fee2e2; color: #991b1b; border-color: #f4b4b4; }
            QToolButton { min-height: 28px; border: 1px solid #c2cfdf; border-radius: 6px; background: #ffffff; color: #0f172a; padding: 0 8px; font-weight: 700; }
            QToolButton:hover { background: #f1f5f9; }
            QCheckBox { color: #0f172a; spacing: 6px; font-size: 12px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
            QLabel#metaLabel { color: #1f2937; font-size: 11px; font-weight: 700; }
            """
        )

        self._setup_ui()
        self._connect_signals()
        self._set_mode(0)
        self._reset_editor_text_style()
        self._apply_template()
        self._refresh()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header_card = QFrame()
        header_card.setObjectName("headerCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_stack = QVBoxLayout()
        title = QLabel("Notification Center")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Compose structured updates and review delivery history")
        subtitle.setObjectName("headerSubtitle")
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)
        header_layout.addLayout(title_stack)
        header_layout.addStretch(1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("ghostButton")
        header_layout.addWidget(self.refresh_button)
        root.addWidget(header_card)

        mode_row = QHBoxLayout()
        mode_row.setContentsMargins(2, 0, 2, 0)
        mode_row.setSpacing(8)
        self.compose_mode_btn = QPushButton("Compose")
        self.compose_mode_btn.setObjectName("modeButton")
        self.history_mode_btn = QPushButton("History")
        self.history_mode_btn.setObjectName("modeButton")
        mode_row.addWidget(self.compose_mode_btn)
        mode_row.addWidget(self.history_mode_btn)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        self.main_stack = QStackedWidget()
        self.compose_page = self._build_compose_page()
        self.history_page = self._build_history_page()
        self.main_stack.addWidget(self.compose_page)
        self.main_stack.addWidget(self.history_page)
        root.addWidget(self.main_stack, 1)

    def _build_compose_page(self) -> QWidget:
        card = QFrame()
        card.setObjectName("panelCard")
        page_layout = QVBoxLayout(card)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(10)

        compose_scroll = QScrollArea()
        compose_scroll.setObjectName("composeScroll")
        compose_scroll.setWidgetResizable(True)
        compose_scroll.setFrameShape(QFrame.Shape.NoFrame)
        page_layout.addWidget(compose_scroll)

        compose = QWidget()
        compose.setObjectName("composeSurface")
        compose_layout = QVBoxLayout(compose)
        compose_layout.setContentsMargins(0, 0, 0, 0)
        compose_layout.setSpacing(10)

        type_template_row = QHBoxLayout()
        self.type_input = QComboBox()
        self.type_input.addItems(self.TYPES)
        self.template_input = QComboBox()
        self.template_input.addItems(list(self.TEMPLATES.keys()))
        self.apply_template_button = QPushButton("Apply Template")
        self.apply_template_button.setObjectName("ghostButton")
        type_template_row.addWidget(self._labeled("Type", self.type_input))
        type_template_row.addWidget(self._labeled("Message Template", self.template_input))
        type_template_row.addWidget(self.apply_template_button, 0, Qt.AlignmentFlag.AlignBottom)
        compose_layout.addLayout(type_template_row)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Notification title")
        compose_layout.addWidget(self._labeled("Title", self.title_input))

        self.simple_mode_label = QLabel("Simple mode is recommended for operational clarity.")
        self.simple_mode_label.setObjectName("helpText")
        compose_layout.addWidget(self.simple_mode_label)

        self.basic_toolbar = self._build_basic_toolbar()
        compose_layout.addWidget(self.basic_toolbar)

        self.advanced_toggle_btn = QPushButton("Show Advanced Formatting")
        self.advanced_toggle_btn.setObjectName("ghostButton")
        self.advanced_toggle_btn.setCheckable(True)
        self.advanced_toggle_btn.setChecked(False)
        compose_layout.addWidget(self.advanced_toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.advanced_toolbar = self._build_advanced_toolbar()
        self.advanced_toolbar.setVisible(False)
        compose_layout.addWidget(self.advanced_toolbar)

        self.advanced_mode_label = QLabel("Advanced formatting is optional.")
        self.advanced_mode_label.setObjectName("helpText")
        compose_layout.addWidget(self.advanced_mode_label)

        self.body_input = QTextEdit()
        self.body_input.setObjectName("bodyEditor")
        self.body_input.setAcceptRichText(True)
        self.body_input.setPlaceholderText("Write structured message content")
        compose_layout.addWidget(self._labeled("Message Body", self.body_input))

        tiers_container = QFrame()
        tiers_container.setObjectName("tiersCard")
        tiers_layout = QVBoxLayout(tiers_container)
        tiers_layout.setContentsMargins(0, 0, 0, 0)
        tiers_layout.setSpacing(4)
        tiers_label = QLabel("Target Tiers")
        tiers_label.setObjectName("sectionLabel")
        tiers_layout.addWidget(tiers_label)
        self.tier_checks = []
        for tier in self.TIERS:
            checkbox = QCheckBox(tier)
            checkbox.setChecked(True)
            self.tier_checks.append(checkbox)
            tiers_layout.addWidget(checkbox)
        compose_layout.addWidget(tiers_container)

        optional_row = QHBoxLayout()
        self.action_url_input = QLineEdit()
        self.action_url_input.setPlaceholderText("Optional action URL")
        optional_row.addWidget(self._labeled("Action URL", self.action_url_input), 3)
        expiry_box = QWidget()
        expiry_layout = QVBoxLayout(expiry_box)
        expiry_layout.setContentsMargins(0, 0, 0, 0)
        self.expires_toggle = QCheckBox("Set expiry")
        self.expires_input = QDateTimeEdit()
        self.expires_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.expires_input.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.expires_input.setEnabled(False)
        expiry_layout.addWidget(self.expires_toggle)
        expiry_layout.addWidget(self.expires_input)
        optional_row.addWidget(expiry_box, 2)
        compose_layout.addLayout(optional_row)

        self.preview_box = QTextBrowser()
        self.preview_box.setObjectName("previewBox")
        self.preview_box.setOpenExternalLinks(True)
        self.preview_box.setMinimumHeight(170)
        self.preview_box.document().setDefaultStyleSheet(
            "body{color:#0f172a;background:#f8fbff;font-family:'Segoe UI';}"
            "a{color:#1d4ed8;} p, li{color:#0f172a;}"
        )
        compose_layout.addWidget(self._labeled("Preview", self.preview_box))

        footer_row = QHBoxLayout()
        self.validation_status = QLabel("")
        self.validation_status.setObjectName("statusError")
        footer_row.addWidget(self.validation_status)
        footer_row.addStretch(1)
        self.view_history_button = QPushButton("View in History")
        self.view_history_button.setObjectName("ghostButton")
        self.view_history_button.setVisible(False)
        footer_row.addWidget(self.view_history_button)
        self.create_button = QPushButton("Send Notification")
        self.create_button.setObjectName("primaryButton")
        footer_row.addWidget(self.create_button)
        compose_layout.addLayout(footer_row)

        send_hint = QLabel("Send Notification publishes immediately to selected tiers.")
        send_hint.setObjectName("helpText")
        compose_layout.addWidget(send_hint)

        compose_layout.addStretch(1)
        compose_scroll.setWidget(compose)
        return card

    def _build_history_page(self) -> QWidget:
        card = QFrame()
        card.setObjectName("panelCard")
        page_layout = QVBoxLayout(card)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(10)

        tools_row = QHBoxLayout()
        self.history_filter_input = QLineEdit()
        self.history_filter_input.setPlaceholderText("Filter by title or type")
        tools_row.addWidget(self.history_filter_input, 1)
        cleanup_label = QLabel("Auto cleanup (days)")
        cleanup_label.setObjectName("sectionLabel")
        tools_row.addWidget(cleanup_label)
        self.cleanup_days_input = QSpinBox()
        self.cleanup_days_input.setRange(1, 3650)
        self.cleanup_days_input.setValue(30)
        self.cleanup_days_input.setFixedWidth(90)
        tools_row.addWidget(self.cleanup_days_input)
        self.cleanup_button = QPushButton("Cleanup Images")
        self.cleanup_button.setObjectName("ghostButton")
        tools_row.addWidget(self.cleanup_button)
        page_layout.addLayout(tools_row)

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
        history_layout.setSpacing(8)

        history_title = QLabel("Selected Notification")
        history_title.setObjectName("sectionLabel")
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

        self.history_body = QTextBrowser()
        self.history_body.setReadOnly(True)
        self.history_body.setMinimumHeight(120)
        self.history_body.document().setDefaultStyleSheet("body{color:#0f172a;background:#ffffff;} a{color:#1d4ed8;}")
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
        page_layout.addWidget(history_splitter, 1)
        return card

    def _labeled(self, text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        return container

    def _connect_signals(self) -> None:
        self.compose_mode_btn.clicked.connect(lambda: self._set_mode(0))
        self.history_mode_btn.clicked.connect(lambda: self._set_mode(1))
        self.refresh_button.clicked.connect(self._refresh)
        self.apply_template_button.clicked.connect(self._apply_template)
        self.advanced_toggle_btn.toggled.connect(self._toggle_advanced)
        self.expires_toggle.toggled.connect(self.expires_input.setEnabled)
        self.title_input.textChanged.connect(self._on_body_changed)
        self.body_input.textChanged.connect(self._on_body_changed)
        self.action_url_input.textChanged.connect(self._on_body_changed)
        self.expires_toggle.toggled.connect(self._on_body_changed)
        self.expires_input.dateTimeChanged.connect(self._on_body_changed)
        self.create_button.clicked.connect(self._on_send_clicked)
        self.view_history_button.clicked.connect(lambda: self._set_mode(1))
        self.cleanup_button.clicked.connect(self._cleanup_images)
        self.history_filter_input.textChanged.connect(self._on_history_filter_changed)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.delete_button.clicked.connect(self._delete_selected)

    def _set_mode(self, index: int) -> None:
        self.main_stack.setCurrentIndex(index)
        self.compose_mode_btn.setProperty("active", index == 0)
        self.history_mode_btn.setProperty("active", index == 1)
        for btn in (self.compose_mode_btn, self.history_mode_btn):
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def _build_basic_toolbar(self) -> QWidget:
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.clicked.connect(self._toggle_bold)
        layout.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.clicked.connect(self._toggle_italic)
        layout.addWidget(self.italic_btn)

        self.underline_btn = QToolButton()
        self.underline_btn.setText("U")
        self.underline_btn.setCheckable(True)
        self.underline_btn.clicked.connect(self._toggle_underline)
        layout.addWidget(self.underline_btn)

        bullet_btn = QToolButton()
        bullet_btn.setText("• List")
        bullet_btn.clicked.connect(self._toggle_bullets)
        layout.addWidget(bullet_btn)

        link_btn = QToolButton()
        link_btn.setText("Link")
        link_btn.clicked.connect(self._insert_link)
        layout.addWidget(link_btn)

        layout.addStretch(1)
        return toolbar

    def _build_advanced_toolbar(self) -> QWidget:
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.font_family_input = QFontComboBox()
        self.font_family_input.setCurrentFont(QFont("Segoe UI"))
        self.font_family_input.currentFontChanged.connect(self._set_font_family)
        layout.addWidget(self.font_family_input)

        self.font_size_input = QComboBox()
        self.font_size_input.addItems(["10", "11", "12", "13", "14", "16", "18", "20", "24", "28"])
        self.font_size_input.setCurrentText("12")
        self.font_size_input.currentTextChanged.connect(self._set_font_size)
        self.font_size_input.setMaximumWidth(80)
        layout.addWidget(self.font_size_input)

        color_btn = QToolButton()
        color_btn.setText("Color")
        color_btn.clicked.connect(self._set_text_color)
        layout.addWidget(color_btn)

        align_left = QToolButton()
        align_left.setText("Left")
        align_left.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))
        layout.addWidget(align_left)

        align_center = QToolButton()
        align_center.setText("Center")
        align_center.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignCenter))
        layout.addWidget(align_center)

        align_right = QToolButton()
        align_right.setText("Right")
        align_right.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(align_right)

        image_btn = QToolButton()
        image_btn.setText("Image")
        image_btn.clicked.connect(self._insert_image)
        layout.addWidget(image_btn)

        layout.addStretch(1)
        return toolbar

    def _toggle_advanced(self, checked: bool) -> None:
        self.advanced_toolbar.setVisible(checked)
        self.advanced_mode_label.setVisible(checked)
        self.advanced_toggle_btn.setText("Hide Advanced Formatting" if checked else "Show Advanced Formatting")

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.body_input.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.body_input.mergeCurrentCharFormat(fmt)

    def _set_font_family(self, font: QFont) -> None:
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self._merge_format(fmt)

    def _set_font_size(self, size_text: str) -> None:
        try:
            size = float(size_text)
        except ValueError:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_format(fmt)

    def _toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.bold_btn.isChecked() else QFont.Weight.Normal)
        self._merge_format(fmt)

    def _toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic_btn.isChecked())
        self._merge_format(fmt)

    def _toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline_btn.isChecked())
        self._merge_format(fmt)

    def _set_text_color(self) -> None:
        color = QColorDialog.getColor(parent=self)
        if not color.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self._merge_format(fmt)

    def _set_alignment(self, alignment: Qt.AlignmentFlag) -> None:
        self.body_input.setAlignment(alignment)

    def _toggle_bullets(self) -> None:
        cursor = self.body_input.textCursor()
        cursor.beginEditBlock()
        if cursor.currentList():
            cursor.currentList().remove(cursor.block())
        else:
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_format)
        cursor.endEditBlock()

    def _insert_link(self) -> None:
        cursor = self.body_input.textCursor()
        selected = cursor.selectedText().strip() or "link text"
        cursor.insertHtml(f'<a href="https://">{selected}</a>')

    def _insert_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        )
        if not file_path:
            return
        try:
            image_url = self._service.upload_notification_asset(file_path)
            cursor = self.body_input.textCursor()
            cursor.insertHtml(f'<img src="{image_url}" style="max-width: 100%;" />')
            self._on_body_changed()
        except Exception as exc:
            self._show_error(f"Image upload failed: {exc}")

    def _build_template_body(self, title: str, tiers: str, action_url: str, expires_text: str) -> str:
        template_name = self.template_input.currentText()
        template = self.TEMPLATES.get(template_name, {})
        sections = template.get("sections", ["Summary", "Details", "Action", "Support"])

        lines = [title, "", f"Audience: {tiers}", ""]
        for section in sections:
            lines.append(f"{section}:")
            lines.append("- ")
            lines.append("")
        if action_url:
            lines.append(f"Action URL: {action_url}")
        if expires_text:
            lines.append(f"Expires: {expires_text}")
        return "\n".join(lines).strip()

    def _reset_editor_text_style(self) -> None:
        self.body_input.setTextColor(Qt.GlobalColor.black)
        self.body_input.setFont(QFont("Segoe UI", 10))
        self.body_input.document().setDefaultStyleSheet("body, p, li, div, span { color: #0f172a; }")

    def _sanitize_editor_html_for_readability(self, html: str) -> str:
        if not html:
            return ""
        sanitized = self._LIGHT_COLOR_PATTERN.sub("color:#0f172a", html)
        sanitized = sanitized.replace("color:transparent", "color:#0f172a")
        return sanitized

    def _normalize_body_html(self) -> None:
        if self._sanitizing_editor:
            return
        current_html = self.body_input.toHtml()
        sanitized = self._sanitize_editor_html_for_readability(current_html)
        if sanitized == current_html:
            return
        self._sanitizing_editor = True
        cursor = self.body_input.textCursor()
        pos = cursor.position()
        self.body_input.blockSignals(True)
        self.body_input.setHtml(sanitized)
        self.body_input.blockSignals(False)
        cursor = self.body_input.textCursor()
        cursor.setPosition(min(pos, len(self.body_input.toPlainText())))
        self.body_input.setTextCursor(cursor)
        self._sanitizing_editor = False

    def _apply_template(self) -> None:
        title = self.title_input.text().strip() or "Notification Title"
        tiers = ", ".join(self._collect_selected_tiers()) or "All tiers"
        action_url = self.action_url_input.text().strip()
        expires_text = ""
        if self.expires_toggle.isChecked():
            expires_at = self.expires_input.dateTime().toPython()
            expires_text = expires_at.strftime("%Y-%m-%d %H:%M")

        plain = self._build_template_body(title, tiers, action_url, expires_text)
        self.body_input.setPlainText(plain)
        self._reset_editor_text_style()
        self._normalize_body_html()
        self._on_body_changed()

    def _collect_selected_tiers(self) -> List[str]:
        return [c.text() for c in self.tier_checks if c.isChecked()]

    def _validate_form(self) -> Optional[str]:
        if not self.title_input.text().strip():
            return "Title is required."
        if not self.body_input.toPlainText().strip():
            return "Message body is required."
        if not self._collect_selected_tiers():
            return "Select at least one target tier."
        if self.expires_toggle.isChecked():
            if self.expires_input.dateTime() <= QDateTime.currentDateTime():
                return "Expiry must be in the future."
        return None

    def _on_body_changed(self) -> None:
        self._normalize_body_html()
        error = self._validate_form()
        if error:
            self.validation_status.setObjectName("statusError")
            self.validation_status.setText(error)
        else:
            self.validation_status.setObjectName("statusSuccess")
            self.validation_status.setText("Ready to send.")
        self.validation_status.style().unpolish(self.validation_status)
        self.validation_status.style().polish(self.validation_status)
        self.validation_status.update()

        body_html = self.body_input.toHtml().strip()
        footer_lines = []
        action_url = self.action_url_input.text().strip()
        if action_url:
            footer_lines.append(f"Action URL: {action_url}")
        if self.expires_toggle.isChecked():
            expires_at = self.expires_input.dateTime().toPython()
            footer_lines.append(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}")
        footer_html = f"<br><br>{'<br>'.join(footer_lines)}" if footer_lines else ""
        self.preview_box.setHtml(self._sanitize_editor_html_for_readability(body_html + footer_html))

    def _on_send_clicked(self) -> None:
        validation_error = self._validate_form()
        if validation_error:
            self.validation_status.setObjectName("statusError")
            self.validation_status.setText(validation_error)
            self.validation_status.style().unpolish(self.validation_status)
            self.validation_status.style().polish(self.validation_status)
            self.validation_status.update()
            return

        payload = {
            "type": self.type_input.currentText().strip(),
            "title": self.title_input.text().strip(),
            "body": self._sanitize_editor_html_for_readability(self.body_input.toHtml().strip()),
            "action_url": self.action_url_input.text().strip() or None,
            "target_tiers": self._collect_selected_tiers(),
            "expires_at": self.expires_input.dateTime().toPython() if self.expires_toggle.isChecked() else None,
        }
        self.create_button.setEnabled(False)
        self._run_in_background(
            lambda: self._service.create_notification(payload),
            self._on_create_finished,
            self._on_create_failed,
        )

    def _on_create_finished(self, _result: Any) -> None:
        self.create_button.setEnabled(True)
        self.title_input.clear()
        self.body_input.clear()
        self.action_url_input.clear()
        self.expires_toggle.setChecked(False)
        for checkbox in self.tier_checks:
            checkbox.setChecked(True)
        self._reset_editor_text_style()
        self.validation_status.setObjectName("statusSuccess")
        self.validation_status.setText("Notification sent successfully.")
        self.validation_status.style().unpolish(self.validation_status)
        self.validation_status.style().polish(self.validation_status)
        self.validation_status.update()
        self.view_history_button.setVisible(True)
        QTimer.singleShot(3500, self, lambda: self.view_history_button.setVisible(False))
        self._on_body_changed()
        self._refresh()

    def _on_create_failed(self, message: str) -> None:
        self.create_button.setEnabled(True)
        self.validation_status.setObjectName("statusError")
        self.validation_status.setText(f"Send failed: {message}")
        self.validation_status.style().unpolish(self.validation_status)
        self.validation_status.style().polish(self.validation_status)
        self.validation_status.update()

    def _refresh(self) -> None:
        self.refresh_button.setEnabled(False)
        self._run_in_background(
            lambda: self._service.list_notifications(limit=200),
            self._on_notifications_loaded,
            self._on_notifications_error,
        )

    def _on_notifications_loaded(self, result: Any) -> None:
        self.refresh_button.setEnabled(True)
        self._rows = result or []
        self._on_history_filter_changed(self.history_filter_input.text())

    def _on_notifications_error(self, message: str) -> None:
        self.refresh_button.setEnabled(True)
        self._show_error(message)

    def _on_history_filter_changed(self, text: str) -> None:
        term = (text or "").strip().lower()
        if not term:
            self._filtered_rows = list(self._rows)
        else:
            self._filtered_rows = [
                row for row in self._rows
                if term in str(row.get("title", "")).lower() or term in str(row.get("type", "")).lower()
            ]
        self._populate_table(self._filtered_rows)

    def _populate_table(self, rows: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, (_, key) in enumerate(self.TABLE_COLUMNS):
                value = row.get(key, "")
                if key == "target_tiers" and isinstance(value, list):
                    value = ", ".join(value)
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setToolTip(str(value) if value is not None else "")
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()
        if rows:
            self.table.selectRow(0)
            self._on_table_selection_changed()
        else:
            self._clear_history_details()

    def _on_table_selection_changed(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self._clear_history_details()
            return
        row_idx = selected[0].row()
        if row_idx < 0 or row_idx >= len(self._filtered_rows):
            self._clear_history_details()
            return
        self._render_history_details(self._filtered_rows[row_idx])

    def _render_history_details(self, data: Dict[str, Any]) -> None:
        tiers = data.get("target_tiers") or []
        tiers_text = ", ".join(tiers) if isinstance(tiers, list) else str(tiers or "-")
        self._selected_notification_id = data.get("id")
        self.history_type.setText(f"Type: {data.get('type') or '-'}")
        self.history_tiers.setText(f"Tiers: {tiers_text or '-'}")
        self.history_published.setText(f"Published: {data.get('published_at') or '-'}")
        self.history_expires.setText(f"Expires: {data.get('expires_at') or '-'}")
        self.history_title_text.setText(data.get("title") or "")
        self.history_body.setHtml(self._sanitize_editor_html_for_readability(data.get("body") or ""))
        self.history_action.setText(data.get("action_url") or "")
        self.delete_button.setEnabled(bool(self._selected_notification_id))

    def _clear_history_details(self) -> None:
        self._selected_notification_id = None
        self.history_type.setText("Type: -")
        self.history_tiers.setText("Tiers: -")
        self.history_published.setText("Published: -")
        self.history_expires.setText("Expires: -")
        self.history_title_text.clear()
        self.history_body.clear()
        self.history_action.clear()
        self.delete_button.setEnabled(False)

    def _delete_selected(self) -> None:
        notification_id = self._selected_notification_id
        if not notification_id:
            self._show_error("Select a notification to delete.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete Notification",
            "Delete the selected notification? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.delete_button.setEnabled(False)
        self._run_in_background(
            lambda: self._service.delete_notification(notification_id),
            self._on_delete_finished,
            self._on_delete_failed,
        )

    def _on_delete_finished(self, _result: Any) -> None:
        self._selected_notification_id = None
        self._refresh()

    def _on_delete_failed(self, message: str) -> None:
        self.delete_button.setEnabled(True)
        self._show_error(message)

    def _cleanup_images(self) -> None:
        days = int(self.cleanup_days_input.value())
        confirm = QMessageBox.question(
            self,
            "Cleanup Images",
            f"Delete notification images older than {days} days?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.cleanup_button.setEnabled(False)
        self._run_in_background(
            lambda: self._service.delete_notification_assets_older_than(days),
            self._on_cleanup_finished,
            self._on_cleanup_failed,
        )

    def _on_cleanup_finished(self, result: Any) -> None:
        self.cleanup_button.setEnabled(True)
        removed = int(result or 0)
        QMessageBox.information(self, "Cleanup Complete", f"Deleted {removed} old image(s).")

    def _on_cleanup_failed(self, message: str) -> None:
        self.cleanup_button.setEnabled(True)
        self._show_error(message)

    def _run_in_background(self, fn, on_success, on_error=None) -> None:
        thread = QThread(self)
        worker = AsyncWorker(fn)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        worker.finished.connect(lambda result: self._track_thread_cleanup(thread, worker, on_success, result))
        worker.error.connect(lambda message: self._track_thread_error(thread, worker, on_error, message))
        thread.finished.connect(thread.deleteLater)

        self._threads.append(thread)
        self._workers.append(worker)
        thread.start()

    def _track_thread_cleanup(self, thread: QThread, worker: AsyncWorker, callback, result: Any) -> None:
        if thread in self._threads:
            self._threads.remove(thread)
        if worker in self._workers:
            self._workers.remove(worker)
        thread.quit()
        if callback:
            callback(result)

    def _track_thread_error(self, thread: QThread, worker: AsyncWorker, callback, message: str) -> None:
        if thread in self._threads:
            self._threads.remove(thread)
        if worker in self._workers:
            self._workers.remove(worker)
        thread.quit()
        if callback:
            callback(message)
        else:
            self._show_error(message)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Notification Manager", message)
