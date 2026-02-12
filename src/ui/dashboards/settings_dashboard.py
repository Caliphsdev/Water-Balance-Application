"""
Settings Dashboard Controller (APPLICATION CONFIGURATION).

Purpose:
- Load settings.ui (container for settings controls)
- Display application preferences
- Handle feature flags, data paths, etc.
"""

from datetime import datetime
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QSpacerItem,
)

from models.system_constant import SystemConstant
from services.system_constants_service import SystemConstantsService
from services.environmental_data_service import get_environmental_data_service

from ui.dashboards.generated_ui_settings import Ui_Form


class SettingsPage(QWidget):
    """Settings Page (CONFIGURATION).
    
    Displays application settings including:
    - Data paths (Excel files, diagrams)
    - Feature flags
    - Database paths
    - Licensing info
    - Preferences
    """
    
    def __init__(self, parent=None):
        """Initialize Settings page.
        
        Args:
            parent: Parent widget (usually MainWindow)
        """
        super().__init__(parent)
        
        # Load compiled UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Service for database-backed constants management.
        self.constants_service = SystemConstantsService()
        self.selected_constant_key = None

        # Service for environmental data (rainfall, evaporation).
        self.environmental_service = get_environmental_data_service()
        
        # Ensure environmental_data tables exist (safe schema update)
        from database.schema import DatabaseSchema
        schema = DatabaseSchema()
        schema.ensure_environmental_data_tables()

        # Make the Settings UI responsive (layouts instead of fixed geometry).
        self._configure_responsive_layouts()
        self._apply_visual_refresh()

        # Constants are code-defined; allow value updates only.
        self._lock_constants_structure()

        # Wire constants tab actions to database-backed service.
        self._wire_constants_tab()
        self._load_constants()
        
        # Wire environmental tab actions
        self._wire_environmental_tab()
        self._load_environmental_data()

    def _configure_responsive_layouts(self) -> None:
        """Configure responsive layouts for the Settings dashboard.

        Ensures the Constants tab stretches with the window by:
        - Adding a vertical layout to the tab container
        - Letting the table expand to fill available space
        - Stretching columns for consistent readability
        """
        # Guard against missing widgets if the UI changes in Qt Designer.
        if not hasattr(self.ui, "Constants"):
            return

        self._configure_constants_tab_layout()

    def resizeEvent(self, event) -> None:
        """Keep Settings content width responsive as the page resizes."""
        super().resizeEvent(event)
        self._apply_responsive_content_width()

    def _configure_constants_tab_layout(self) -> None:
        """Apply responsive layout rules to the Constants tab.

        Uses a top/middle/bottom vertical layout so the table grows with
        the window while the filter and quick-edit bars remain fixed height.
        """
        constants_tab = self.ui.Constants

        # Add a layout only if the designer did not define one.
        if constants_tab.layout() is None:
            layout = QVBoxLayout(constants_tab)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)
            layout.addWidget(self.ui.frame_2)
            layout.addWidget(self.ui.frame_3, 0)
            layout.addWidget(self.ui.frame_4)
            layout.addStretch(1)

        # Keep bars compact while allowing the table frame to expand.
        self.ui.frame_2.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.ui.frame_3.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.ui.frame_4.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        # Ensure the table is governed by a layout (not fixed geometry).
        if self.ui.frame_3.layout() is None:
            frame_layout = QVBoxLayout(self.ui.frame_3)
            frame_layout.setContentsMargins(10, 10, 10, 10)
            frame_layout.setSpacing(6)
            frame_layout.addWidget(self.ui.label_8)
            frame_layout.addWidget(self.ui.tableWidget_constant_table, 1)

        # Make the constants table resize smoothly with the window.
        table = self.ui.tableWidget_constant_table
        table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def _apply_visual_refresh(self) -> None:
        """Apply polished visual hierarchy for Settings/Constants page."""
        if hasattr(self.ui, "label"):
            self.ui.label.setObjectName("label_title")
        if hasattr(self.ui, "label_2"):
            self.ui.label_2.setObjectName("label_subtitle")
        if hasattr(self.ui, "frame"):
            self.ui.frame.setObjectName("settings_page_header")
            self.ui.frame.setMinimumHeight(102)
            self.ui.frame.setMaximumHeight(114)
        if hasattr(self.ui, "Settings"):
            self.ui.Settings.setObjectName("settings_tab_widget")

        # Constants tab structure
        if hasattr(self.ui, "frame_2"):
            self.ui.frame_2.setObjectName("settings_filter_bar")
            self.ui.frame_2.setMinimumHeight(46)
            self.ui.frame_2.setMaximumHeight(52)
        if hasattr(self.ui, "frame_3"):
            self.ui.frame_3.setObjectName("settings_table_panel")
            self.ui.frame_3.setMinimumHeight(280)
            self.ui.frame_3.setMaximumHeight(460)
        if hasattr(self.ui, "frame_4"):
            self.ui.frame_4.setObjectName("settings_quick_edit_bar")
            self.ui.frame_4.setMinimumHeight(56)
            self.ui.frame_4.setMaximumHeight(64)
        if hasattr(self.ui, "label_8"):
            self.ui.label_8.setObjectName("settings_section_label")
            self.ui.label_8.setText("System Constants")

        # Filter controls
        if hasattr(self.ui, "comboBox_filter_constants"):
            self.ui.comboBox_filter_constants.setMinimumWidth(118)
            self.ui.comboBox_filter_constants.setMaximumWidth(140)
        if hasattr(self.ui, "lineEdit_searchbox"):
            self.ui.lineEdit_searchbox.setMinimumWidth(188)
            self.ui.lineEdit_searchbox.setMaximumWidth(260)
            self.ui.lineEdit_searchbox.setPlaceholderText("Key, category, unit or description")
        if hasattr(self.ui, "history_button"):
            self.ui.history_button.setObjectName("ghostButton")
            self.ui.history_button.setMinimumWidth(84)
            self.ui.history_button.setIcon(QIcon(":/icons/history_icon.svg"))
            self.ui.history_button.setIconSize(QSize(14, 14))

        # Quick edit bar cleanup (remove big designer spacers).
        if hasattr(self.ui, "horizontalLayout_3"):
            row = self.ui.horizontalLayout_3
            row.setSpacing(10)
            row.setContentsMargins(10, 6, 10, 6)
            for idx in range(row.count() - 1, -1, -1):
                item = row.itemAt(idx)
                if item and item.spacerItem():
                    row.takeAt(idx)
            row.addStretch(1)

        if hasattr(self.ui, "label_9"):
            self.ui.label_9.setObjectName("settings_quick_label")
        if hasattr(self.ui, "label_10"):
            self.ui.label_10.setObjectName("settings_quick_label")
        if hasattr(self.ui, "selected_constant"):
            self.ui.selected_constant.setObjectName("settings_quick_constant")
            self.ui.selected_constant.setMinimumWidth(170)
            self.ui.selected_constant.setMaximumWidth(240)
        if hasattr(self.ui, "lineEdit_value"):
            self.ui.lineEdit_value.setMinimumWidth(140)
            self.ui.lineEdit_value.setMaximumWidth(170)
        if hasattr(self.ui, "save_button"):
            self.ui.save_button.setText("Save")
            self.ui.save_button.setObjectName("primaryButton")
            self.ui.save_button.setMinimumWidth(92)
            # Force an explicit primary style for this control to avoid object-name style collisions.
            self.ui.save_button.setStyleSheet(
                "QPushButton {"
                "background-color: #1f3a5f;"
                "color: #ffffff;"
                "font-weight: 700;"
                "border: 1px solid #1f3a5f;"
                "border-radius: 6px;"
                "padding: 6px 12px;"
                "}"
                "QPushButton:hover {"
                "background-color: #1a2f4c;"
                "border-color: #1a2f4c;"
                "}"
            )
        if hasattr(self.ui, "details_button"):
            self.ui.details_button.setText("Details")
            self.ui.details_button.setObjectName("ghostButton")
            self.ui.details_button.setMinimumWidth(92)
            self.ui.details_button.setIcon(QIcon(":/icons/details_icon.svg"))
            self.ui.details_button.setIconSize(QSize(14, 14))

        # Environmental tab structure and controls
        if hasattr(self.ui, "frame_5"):
            self.ui.frame_5.setObjectName("settings_env_filter_bar")
            self.ui.frame_5.setMinimumHeight(72)
            self.ui.frame_5.setMaximumHeight(94)
        if hasattr(self.ui, "frame_6"):
            self.ui.frame_6.setObjectName("settings_env_section_header")
            self.ui.frame_6.setMinimumHeight(44)
            self.ui.frame_6.setMaximumHeight(52)
        if hasattr(self.ui, "frame_7"):
            self.ui.frame_7.setObjectName("settings_env_section_header")
            self.ui.frame_7.setMinimumHeight(44)
            self.ui.frame_7.setMaximumHeight(52)
        if hasattr(self.ui, "Rainfall"):
            self.ui.Rainfall.setObjectName("settings_env_panel")
        if hasattr(self.ui, "Evaporation"):
            self.ui.Evaporation.setObjectName("settings_env_panel")
        if hasattr(self.ui, "Rainfall_2"):
            self.ui.Rainfall_2.setObjectName("settings_env_panel_inner")

        if hasattr(self.ui, "historical_data_label"):
            self.ui.historical_data_label.setObjectName("settings_section_label")
        if hasattr(self.ui, "rainfall_label"):
            self.ui.rainfall_label.setObjectName("settings_section_label")
        if hasattr(self.ui, "label_64"):
            self.ui.label_64.setObjectName("settings_section_label")

        if hasattr(self.ui, "comboBox_year_filter"):
            self.ui.comboBox_year_filter.setMinimumWidth(110)
            self.ui.comboBox_year_filter.setMaximumWidth(130)
        if hasattr(self.ui, "save_button_environment"):
            self.ui.save_button_environment.setText("Save")
            self.ui.save_button_environment.setObjectName("primaryButton")
            self.ui.save_button_environment.setMinimumWidth(96)
            self.ui.save_button_environment.setStyleSheet(
                "QPushButton {"
                "background-color: #1f3a5f;"
                "color: #ffffff;"
                "font-weight: 700;"
                "border: 1px solid #1f3a5f;"
                "border-radius: 6px;"
                "padding: 6px 12px;"
                "}"
                "QPushButton:hover {"
                "background-color: #1a2f4c;"
                "border-color: #1a2f4c;"
                "}"
            )
        if hasattr(self.ui, "load_button_environment"):
            self.ui.load_button_environment.setText("Reload")
            self.ui.load_button_environment.setObjectName("ghostButton")
            self.ui.load_button_environment.setMinimumWidth(96)
            self.ui.load_button_environment.setIcon(QIcon(":/icons/reload_icon.svg"))
            self.ui.load_button_environment.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "select_year_label"):
            self.ui.select_year_label.setObjectName("settings_quick_label")

        # Remove oversized designer spacers and keep one responsive stretch.
        if hasattr(self.ui, "horizontalLayout_30"):
            row = self.ui.horizontalLayout_30
            row.setSpacing(10)
            row.setContentsMargins(0, 0, 0, 0)
            for idx in range(row.count() - 1, -1, -1):
                item = row.itemAt(idx)
                if item and item.spacerItem():
                    row.takeAt(idx)
            row.addStretch(1)
        if hasattr(self.ui, "horizontalLayout_31"):
            row = self.ui.horizontalLayout_31
            row.setSpacing(8)
            row.setContentsMargins(0, 0, 0, 0)
            for idx in range(row.count() - 1, -1, -1):
                item = row.itemAt(idx)
                if item and item.spacerItem():
                    row.takeAt(idx)
            row.addStretch(1)
        if hasattr(self.ui, "horizontalLayout_32"):
            row = self.ui.horizontalLayout_32
            row.setSpacing(8)
            row.setContentsMargins(8, 6, 8, 6)
            for idx in range(row.count() - 1, -1, -1):
                item = row.itemAt(idx)
                if item and item.spacerItem():
                    row.takeAt(idx)

        # Keep month value fields compact and consistent across both grids.
        for edit in self.findChildren(QLineEdit):
            name = edit.objectName() or ""
            if "_rainfall" in name or "_evaporation" in name:
                edit.setMinimumWidth(78)
                edit.setMaximumWidth(96)

        # Align month labels and unit suffixes so columns line up cleanly.
        if hasattr(self.ui, "Rainfall") and hasattr(self.ui, "Rainfall_2"):
            for panel in (self.ui.Rainfall, self.ui.Rainfall_2):
                for lbl in panel.findChildren(QLabel):
                    obj_name = lbl.objectName() or ""
                    if (
                        "rainfall_label" in obj_name
                        or "evaporation_label" in obj_name
                        or obj_name.startswith("label_")
                    ) and lbl.text().strip().endswith(":"):
                        lbl.setFixedWidth(34)
                        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    if obj_name.startswith("unit"):
                        lbl.setFixedWidth(22)
                        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Keep layout left-aligned and apply adaptive max width for wide screens.
        for name in ("frame_2", "frame_3", "frame_4"):
            widget = getattr(self.ui, name, None)
            if widget and self.ui.Constants.layout() is not None:
                self.ui.Constants.layout().setAlignment(widget, Qt.AlignmentFlag.AlignLeft)
        for name in ("frame_5", "frame_6", "frame_7", "Rainfall", "Evaporation"):
            widget = getattr(self.ui, name, None)
            if widget and self.ui.Environmental.layout() is not None:
                self.ui.Environmental.layout().setAlignment(widget, Qt.AlignmentFlag.AlignLeft)
        self._apply_responsive_content_width()

    def _apply_responsive_content_width(self) -> None:
        """Set adaptive max width so content scales better across screen sizes."""
        available = max(600, self.width() - 32)
        target = int(available * 0.92)
        target = min(1500, max(900, target))
        target = min(target, available)

        for name in (
            "frame_2", "frame_3", "frame_4",
            "frame_5", "frame_6", "frame_7",
            "Rainfall", "Evaporation",
        ):
            widget = getattr(self.ui, name, None)
            if widget:
                widget.setMinimumWidth(target)
                widget.setMaximumWidth(target)

    def _wire_constants_tab(self) -> None:
        """Connect Constants tab widgets to service actions.

        This sets up filters, table selection, and CRUD button handlers.
        """
        self.ui.comboBox_filter_constants.currentIndexChanged.connect(
            lambda: self._load_constants()
        )
        self.ui.lineEdit_searchbox.returnPressed.connect(self._load_constants)

        self.ui.save_button.clicked.connect(self._save_selected_constant)
        self.ui.details_button.clicked.connect(self._show_constant_details)
        self.ui.history_button.clicked.connect(self._show_constants_history)

        self.ui.tableWidget_constant_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.ui.tableWidget_constant_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.ui.tableWidget_constant_table.itemSelectionChanged.connect(
            self._on_constant_selected
        )

    def _lock_constants_structure(self) -> None:
        """Hide actions that change or export constant definitions."""
        for button_name in ("add_button", "delete_button", "export_button"):
            if hasattr(self.ui, button_name):
                button = getattr(self.ui, button_name)
                button.setVisible(False)
                button.setEnabled(False)

    def _load_constants(self) -> None:
        """Load constants into the table with filtering and search.

        Uses service layer to pull constants from SQLite and populates the
        QTableWidget using the existing designer-defined columns.
        """
        self._refresh_categories()

        category_filter = self.ui.comboBox_filter_constants.currentText().strip()
        search_text = self.ui.lineEdit_searchbox.text().strip().lower()

        # Map UI headers to column indexes so designer changes don't break data mapping.
        column_map = self._get_constants_column_map()

        constants = self.constants_service.list_constants()
        filtered = []

        for constant in constants:
            if category_filter and category_filter != "All":
                if (constant.category or "") != category_filter:
                    continue

            if search_text:
                hay = " ".join(
                    [
                        constant.constant_key or "",
                        constant.category or "",
                        constant.description or "",
                        constant.unit or "",
                    ]
                ).lower()
                if search_text not in hay:
                    continue

            filtered.append(constant)

        table = self.ui.tableWidget_constant_table
        table.setRowCount(len(filtered))

        for row_index, constant in enumerate(filtered):
            # Populate only known columns (safe if UI columns were reordered).
            self._set_table_item(
                table,
                row_index,
                column_map["category"],
                constant.category or "",
            )
            self._set_table_item(
                table,
                row_index,
                column_map["key"],
                constant.constant_key,
            )
            self._set_table_item(
                table,
                row_index,
                column_map["value"],
                str(constant.constant_value),
            )
            self._set_table_item(
                table,
                row_index,
                column_map["unit"],
                constant.unit or "",
            )
            # Use description as the "Used In / Formula" placeholder until rules exist.
            self._set_table_item(
                table,
                row_index,
                column_map["usage"],
                constant.description or "",
            )

        table.resizeRowsToContents()

    def _refresh_categories(self) -> None:
        """Refresh category filter dropdown from database.

        Ensures the filter list stays consistent with stored constants.
        """
        categories = ["All"] + self.constants_service.list_categories()
        current = self.ui.comboBox_filter_constants.currentText()
        self.ui.comboBox_filter_constants.blockSignals(True)
        self.ui.comboBox_filter_constants.clear()
        self.ui.comboBox_filter_constants.addItems(categories)
        if current and current in categories:
            self.ui.comboBox_filter_constants.setCurrentText(current)
        self.ui.comboBox_filter_constants.blockSignals(False)

    def _on_constant_selected(self) -> None:
        """Handle table row selection (SYNC QUICK EDIT BAR).

        Updates the quick-edit controls with the selected row.
        """
        table = self.ui.tableWidget_constant_table
        selected = table.selectedItems()
        if not selected:
            self.selected_constant_key = None
            self.ui.selected_constant.setText("constant")
            self.ui.lineEdit_value.clear()
            return

        # Read by mapped column indexes to stay aligned with UI column order.
        column_map = self._get_constants_column_map()
        key_item = table.item(selected[0].row(), column_map["key"])
        value_item = table.item(selected[0].row(), column_map["value"])
        if not key_item or not value_item:
            return

        self.selected_constant_key = key_item.text()
        self.ui.selected_constant.setText(self.selected_constant_key)
        self.ui.lineEdit_value.setText(value_item.text())

    def _save_selected_constant(self) -> None:
        """Save quick-edit value back to database.

        Validates numeric input and updates the constant in SQLite.
        """
        if not self.selected_constant_key:
            QMessageBox.information(self, "No Selection", "Select a constant first.")
            return

        try:
            new_value = float(self.ui.lineEdit_value.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", "Enter a valid numeric value.")
            return

        constant_map = self.constants_service.get_constant_map()
        constant = constant_map.get(self.selected_constant_key)
        if not constant:
            QMessageBox.warning(self, "Missing Constant", "Constant not found in database.")
            return

        if constant.editable == 0:
            QMessageBox.warning(self, "Locked Constant", "This constant is locked and cannot be edited.")
            return

        updated = constant.copy(update={"constant_value": new_value})
        try:
            self.constants_service.update_constant(updated)
            self._load_constants()
            QMessageBox.information(self, "Saved", "Constant updated successfully.")
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))

    def _add_constant_dialog(self) -> None:
        """Open dialog to add a new constant (UI INPUT FLOW)."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Constant")
        dialog.setMinimumWidth(420)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        key_input = QLineEdit()
        value_input = QLineEdit()
        unit_input = QLineEdit()
        category_input = QLineEdit()
        description_input = QLineEdit()
        min_input = QLineEdit()
        max_input = QLineEdit()

        form.addRow("Key:", key_input)
        form.addRow("Value:", value_input)
        form.addRow("Unit:", unit_input)
        form.addRow("Category:", category_input)
        form.addRow("Description:", description_input)
        form.addRow("Min Value:", min_input)
        form.addRow("Max Value:", max_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setIcon(QIcon(":/icons/cancel_icon.svg"))
        cancel_btn.setIconSize(QSize(14, 14))
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        cancel_btn.clicked.connect(dialog.reject)

        def handle_create() -> None:
            key = key_input.text().strip()
            if not key:
                QMessageBox.warning(dialog, "Missing Key", "Constant key is required.")
                return
            try:
                value = float(value_input.text().strip())
            except ValueError:
                QMessageBox.warning(dialog, "Invalid Value", "Enter a numeric value.")
                return

            min_val = min_input.text().strip()
            max_val = max_input.text().strip()

            constant = SystemConstant(
                constant_key=key,
                constant_value=value,
                unit=unit_input.text().strip() or None,
                category=category_input.text().strip() or None,
                description=description_input.text().strip() or None,
                min_value=float(min_val) if min_val else None,
                max_value=float(max_val) if max_val else None,
                editable=1,
            )

            try:
                self.constants_service.create_constant(constant)
                self._load_constants()
                dialog.accept()
            except Exception as exc:
                QMessageBox.critical(dialog, "Create Failed", str(exc))

        save_btn.clicked.connect(handle_create)
        dialog.exec()

    def _delete_selected_constant(self) -> None:
        """Delete selected constant with confirmation."""
        if not self.selected_constant_key:
            QMessageBox.information(self, "No Selection", "Select a constant first.")
            return

        constant = self.constants_service.get_constant_map().get(self.selected_constant_key)
        if constant and constant.editable == 0:
            QMessageBox.warning(self, "Locked Constant", "This constant is locked and cannot be deleted.")
            return

        confirm = QMessageBox.question(
            self,
            "Delete Constant",
            f"Delete constant '{self.selected_constant_key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.constants_service.delete_constant(self.selected_constant_key)
            self.selected_constant_key = None
            self._load_constants()
            QMessageBox.information(self, "Deleted", "Constant removed.")
        except Exception as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))

    def _show_constant_details(self) -> None:
        """Show details for the selected constant."""
        if not self.selected_constant_key:
            QMessageBox.information(self, "No Selection", "Select a constant first.")
            return

        constant = self.constants_service.get_constant_map().get(self.selected_constant_key)
        if not constant:
            QMessageBox.warning(self, "Missing Constant", "Constant not found.")
            return

        details = (
            f"Key: {constant.constant_key}\n"
            f"Value: {constant.constant_value}\n"
            f"Unit: {constant.unit or '—'}\n"
            f"Category: {constant.category or '—'}\n"
            f"Description: {constant.description or '—'}\n"
            f"Editable: {'Yes' if constant.editable == 1 else 'No'}\n"
            f"Min: {constant.min_value if constant.min_value is not None else '—'}\n"
            f"Max: {constant.max_value if constant.max_value is not None else '—'}"
        )
        QMessageBox.information(self, "Constant Details", details)

    def _show_constants_history(self) -> None:
        """Show constants audit history in a dialog."""
        history = self.constants_service.list_history(limit=200)

        dialog = QDialog(self)
        dialog.setObjectName("settings_history_dialog")
        dialog.setWindowTitle("Constants History")
        dialog.resize(760, 320)
        dialog.setMinimumSize(700, 220)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        table = QTableWidget(dialog)
        table.setObjectName("settings_history_table")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Changed At", "Constant Key", "Old Value", "New Value", "Updated By"]
        )
        table.setRowCount(len(history))
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setMinimumSectionSize(80)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        for row_index, row in enumerate(history):
            table.setItem(row_index, 0, QTableWidgetItem(str(row.get("changed_at", ""))))
            table.setItem(row_index, 1, QTableWidgetItem(str(row.get("constant_key", ""))))
            table.setItem(row_index, 2, QTableWidgetItem(str(row.get("old_value", ""))))
            table.setItem(row_index, 3, QTableWidgetItem(str(row.get("new_value", ""))))
            table.setItem(row_index, 4, QTableWidgetItem(str(row.get("updated_by", ""))))

        layout.addWidget(table)
        table.resizeRowsToContents()
        table.setColumnWidth(0, max(table.columnWidth(0), 170))

        # Keep dialog compact for small histories and expand only when needed.
        visible_rows = min(max(table.rowCount(), 1), 8)
        row_height = table.verticalHeader().defaultSectionSize()
        rows_height = sum(table.rowHeight(i) for i in range(visible_rows))
        header_height = table.horizontalHeader().height()
        chrome_height = 92  # margins + dialog frame + small safety buffer
        target_height = max(220, min(620, header_height + rows_height + row_height + chrome_height))
        dialog.resize(760, target_height)
        dialog.exec()

    def _export_constants_csv(self) -> None:
        """Export constants to CSV (BASIC EXPORT SUPPORT)."""
        from PySide6.QtWidgets import QFileDialog
        import csv

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Constants",
            "constants.csv",
            "CSV Files (*.csv)"
        )
        if not file_path:
            return

        constants = self.constants_service.list_constants()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Category", "Key", "Value", "Unit", "Description"])
                for constant in constants:
                    writer.writerow(
                        [
                            constant.category or "",
                            constant.constant_key,
                            constant.constant_value,
                            constant.unit or "",
                            constant.description or "",
                        ]
                    )
            QMessageBox.information(self, "Export Complete", "Constants exported.")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _get_constants_column_map(self) -> dict:
        """Resolve table column indexes by header label (UI COMPATIBILITY).

        Returns:
            Dict with keys: category, key, value, unit, usage
        """
        table = self.ui.tableWidget_constant_table
        header_labels = []
        for index in range(table.columnCount()):
            item = table.horizontalHeaderItem(index)
            header_labels.append((index, (item.text() if item else "").lower()))

        def find_index(label_candidates: list, fallback: int) -> int:
            for index, label in header_labels:
                if any(candidate in label for candidate in label_candidates):
                    return index
            return fallback

        return {
            "category": find_index(["category"], 0),
            "key": find_index(["constant key", "key"], 1),
            "value": find_index(["value"], 2),
            "unit": find_index(["unit"], 3),
            "usage": find_index(["used", "formula"], 4),
        }

    @staticmethod
    def _set_table_item(
        table: QTableWidget,
        row: int,
        column: int,
        value: str,
    ) -> None:
        """Set table cell value safely (INTERNAL - CELL UPDATE).

        Args:
            table: QTableWidget instance
            row: Row index
            column: Column index
            value: Display text
        """
        if column < 0:
            return
        item = QTableWidgetItem(value)
        table.setItem(row, column, item)

    # ==================== ENVIRONMENTAL TAB ====================

    def _wire_environmental_tab(self) -> None:
        """Wire Environmental tab signals to slots (INITIALIZATION).
        
        Connects:
        - Save button → save all 12 months of data
        - Load button → reload data for selected year
        - Year selector → auto-load data on change
        """
        # Populate year selector with years
        self._populate_year_selector()
        
        # Connect Save button
        if hasattr(self.ui, 'save_button_environment'):
            self.ui.save_button_environment.clicked.connect(self._save_environmental_data)
        
        # Connect Load button  
        if hasattr(self.ui, 'load_button_environment'):
            self.ui.load_button_environment.clicked.connect(lambda: self._load_environmental_data())
        
        # Connect year selector to reload data when year changes
        if hasattr(self.ui, 'comboBox_year_filter'):
            self.ui.comboBox_year_filter.currentTextChanged.connect(self._on_year_changed)

    def _populate_year_selector(self) -> None:
        """Populate year selector combobox with available years (INITIALIZATION).
        
        Populates with:
        - All years that have environmental data (from database)
        - Current year (always included even if no data)
        - Range: Current year ± 5 years for easy selection
        
        Default selection: Current year
        """
        if not hasattr(self.ui, 'comboBox_year_filter'):
            return
        
        # Block signals while populating to prevent triggering load events
        self.ui.comboBox_year_filter.blockSignals(True)
        
        try:
            current_year = datetime.now().year
            
            # Get years with existing data
            existing_years = set(self.environmental_service.get_available_years())
            
            # Add range around current year (current - 5 to current + 5)
            year_range = set(range(current_year - 5, current_year + 6))
            
            # Combine and sort (descending, most recent first)
            all_years = sorted(existing_years | year_range, reverse=True)
            
            # Clear and populate combobox
            self.ui.comboBox_year_filter.clear()
            for year in all_years:
                self.ui.comboBox_year_filter.addItem(str(year))
            
            # Set current year as default selection
            current_index = self.ui.comboBox_year_filter.findText(str(current_year))
            if current_index >= 0:
                self.ui.comboBox_year_filter.setCurrentIndex(current_index)
        
        finally:
            # Re-enable signals
            self.ui.comboBox_year_filter.blockSignals(False)

    def _on_year_changed(self, year_text: str) -> None:
        """Handle year selector change (EVENT HANDLER).
        
        Args:
            year_text: Selected year as string (e.g., "2025")
        
        Loads environmental data for the selected year into all 12 input fields.
        """
        if not year_text:
            return
        
        try:
            year = int(year_text)
            self._load_environmental_data(year)
        except ValueError:
            # Invalid year format (shouldn't happen with combobox)
            pass

    def _load_environmental_data(self, year: int = None) -> None:
        """Load environmental data for year into UI (DATA LOAD).
        
        Args:
            year: Year to load (None = current year)
        
        Populates all 12 rainfall and evaporation input fields with database values.
        Empty fields if no data exists for that month.
        """
        if year is None:
            year = datetime.now().year
        
        # Get all data for year
        entries = self.environmental_service.list_entries(year)
        
        # Create lookup dict by month
        data_by_month = {entry.month: entry for entry in entries}
        
        # Map of month number to (rainfall_widget, evaporation_widget)
        month_widgets = {
            1: ('lineEdit_january_rainfall', 'lineEdit_jan_evaporation'),
            2: ('lineEdit_february_rainfall', 'lineEdit_feb_evaporation'),
            3: ('lineEdit_march_rainfall', 'lineEdit_march_evaporation'),
            4: ('lineEdit_april_rainfall', 'lineEdit_april_evaporation'),
            5: ('lineEdit_may_rainfall', 'lineEdit_may_evaporation'),
            6: ('lineEdit_jun_rainfall', 'lineEdit_jun_evaporation'),
            7: ('lineEdit_july_rainfall', 'lineEdit_jul_evaporation'),
            8: ('lineEdit_august_rainfall', 'lineEdit_augevaporation'),
            9: ('lineEdit_sep_rainfall', 'lineEdit_sep_evaporation'),
            10: ('lineEdit_oct_rainfall', 'lineEdit_oct_evaporation'),
            11: ('lineEdit_nov_rainfall', 'lineEdit_nov_evaporation'),
            12: ('lineEdit_dec_rainfall', 'lineEdit_dec_evaporation'),
        }
        
        # Populate widgets
        for month, (rainfall_widget_name, evap_widget_name) in month_widgets.items():
            # Get widget references
            rainfall_widget = getattr(self.ui, rainfall_widget_name, None)
            evap_widget = getattr(self.ui, evap_widget_name, None)
            
            if not rainfall_widget or not evap_widget:
                continue
            
            # Get data for this month (or use empty string if no data)
            if month in data_by_month:
                entry = data_by_month[month]
                rainfall_widget.setText(str(entry.rainfall_mm))
                evap_widget.setText(str(entry.evaporation_mm))
            else:
                # Clear fields if no data
                rainfall_widget.setText('')
                evap_widget.setText('')

    def _save_environmental_data(self) -> None:
        """Save all 12 months of environmental data to database (DATA SAVE).
        
        Reads all 12 rainfall and evaporation inputs, validates, and saves to database.
        Shows success/error messages to user.
        """
        try:
            # Get selected year from combobox (or default to current year)
            year = datetime.now().year
            if hasattr(self.ui, 'comboBox_year_filter'):
                year_text = self.ui.comboBox_year_filter.currentText()
                if year_text:
                    year = int(year_text)
            
            # Map of month number to (rainfall_widget, evaporation_widget)
            month_widgets = {
                1: ('lineEdit_january_rainfall', 'lineEdit_jan_evaporation'),
                2: ('lineEdit_february_rainfall', 'lineEdit_feb_evaporation'),
                3: ('lineEdit_march_rainfall', 'lineEdit_march_evaporation'),
                4: ('lineEdit_april_rainfall', 'lineEdit_april_evaporation'),
                5: ('lineEdit_may_rainfall', 'lineEdit_may_evaporation'),
                6: ('lineEdit_jun_rainfall', 'lineEdit_jun_evaporation'),
                7: ('lineEdit_july_rainfall', 'lineEdit_jul_evaporation'),
                8: ('lineEdit_august_rainfall', 'lineEdit_augevaporation'),
                9: ('lineEdit_sep_rainfall', 'lineEdit_sep_evaporation'),
                10: ('lineEdit_oct_rainfall', 'lineEdit_oct_evaporation'),
                11: ('lineEdit_nov_rainfall', 'lineEdit_nov_evaporation'),
                12: ('lineEdit_dec_rainfall', 'lineEdit_dec_evaporation'),
            }
            
            saved_count = 0
            errors = []
            
            for month, (rainfall_widget_name, evap_widget_name) in month_widgets.items():
                # Get widget references
                rainfall_widget = getattr(self.ui, rainfall_widget_name, None)
                evap_widget = getattr(self.ui, evap_widget_name, None)
                
                if not rainfall_widget or not evap_widget:
                    continue
                
                # Get values from widgets
                rainfall_text = rainfall_widget.text().strip()
                evap_text = evap_widget.text().strip()
                
                # Skip if both empty (user didn't enter data for this month)
                if not rainfall_text and not evap_text:
                    continue
                
                try:
                    # Parse values (default to 0 if empty)
                    rainfall_mm = float(rainfall_text) if rainfall_text else 0.0
                    evap_mm = float(evap_text) if evap_text else 0.0
                    
                    # Save to database (create or update)
                    self.environmental_service.create_or_update_entry(
                        year=year,
                        month=month,
                        rainfall_mm=rainfall_mm,
                        evaporation_mm=evap_mm
                    )
                    
                    saved_count += 1
                    
                except ValueError as e:
                    # Pydantic validation failed (negative values, extremes, etc.)
                    month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month - 1]
                    errors.append(f"{month_name}: {str(e)}")
            
            # Show results to user
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(
                    self,
                    "Validation Errors",
                    f"Saved {saved_count} months successfully.\n\nErrors:\n{error_msg}"
                )
            elif saved_count > 0:
                QMessageBox.information(
                    self,
                    "Save Successful",
                    f"Saved {saved_count} month(s) of environmental data for {year}."
                )
            else:
                QMessageBox.information(
                    self,
                    "No Changes",
                    "No data entered. Enter rainfall and/or evaporation values to save."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save environmental data: {str(e)}"
            )
