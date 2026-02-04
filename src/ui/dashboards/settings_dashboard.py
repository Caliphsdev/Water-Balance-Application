"""
Settings Dashboard Controller (APPLICATION CONFIGURATION).

Purpose:
- Load settings.ui (container for settings controls)
- Display application preferences
- Handle feature flags, data paths, etc.
"""

from datetime import datetime
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

    def _configure_constants_tab_layout(self) -> None:
        """Apply responsive layout rules to the Constants tab.

        Uses a top/middle/bottom vertical layout so the table grows with
        the window while the filter and quick-edit bars remain fixed height.
        """
        constants_tab = self.ui.Constants

        # Add a layout only if the designer did not define one.
        if constants_tab.layout() is None:
            layout = QVBoxLayout(constants_tab)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            layout.addWidget(self.ui.frame_2)
            layout.addWidget(self.ui.frame_3, 1)
            layout.addWidget(self.ui.frame_4)

        # Keep bars compact while allowing the table frame to expand.
        self.ui.frame_2.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.ui.frame_3.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.ui.frame_4.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        # Ensure the table is governed by a layout (not fixed geometry).
        if self.ui.frame_3.layout() is None:
            frame_layout = QVBoxLayout(self.ui.frame_3)
            frame_layout.setContentsMargins(10, 30, 10, 10)
            frame_layout.setSpacing(8)
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

    def _wire_constants_tab(self) -> None:
        """Connect Constants tab widgets to service actions.

        This sets up filters, table selection, and CRUD button handlers.
        """
        self.ui.comboBox_filter_constants.currentIndexChanged.connect(
            lambda: self._load_constants()
        )
        self.ui.lineEdit_searchbox.returnPressed.connect(self._load_constants)

        self.ui.save_button.clicked.connect(self._save_selected_constant)
        self.ui.add_button.clicked.connect(self._add_constant_dialog)
        self.ui.delete_button.clicked.connect(self._delete_selected_constant)
        self.ui.details_button.clicked.connect(self._show_constant_details)
        self.ui.history_button.clicked.connect(self._show_constants_history)
        self.ui.export_button.clicked.connect(self._export_constants_csv)

        self.ui.tableWidget_constant_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.ui.tableWidget_constant_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.ui.tableWidget_constant_table.itemSelectionChanged.connect(
            self._on_constant_selected
        )

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
        dialog.setWindowTitle("Constants History")
        dialog.resize(700, 400)

        layout = QVBoxLayout(dialog)
        table = QTableWidget(dialog)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Changed At", "Constant Key", "Old Value", "New Value", "Updated By"]
        )
        table.setRowCount(len(history))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        for row_index, row in enumerate(history):
            table.setItem(row_index, 0, QTableWidgetItem(str(row.get("changed_at", ""))))
            table.setItem(row_index, 1, QTableWidgetItem(str(row.get("constant_key", ""))))
            table.setItem(row_index, 2, QTableWidgetItem(str(row.get("old_value", ""))))
            table.setItem(row_index, 3, QTableWidgetItem(str(row.get("new_value", ""))))
            table.setItem(row_index, 4, QTableWidgetItem(str(row.get("updated_by", ""))))

        layout.addWidget(table)
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
