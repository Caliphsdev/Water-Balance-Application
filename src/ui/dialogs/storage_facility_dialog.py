"""
Storage Facility Add/Edit Dialog Controller (DIALOG FORM CONTROLLER).

Handles user interaction with Add/Edit facility form.

Responsibilities:
1. Display form (empty for Add, populated for Edit)
2. Validate user input
3. Call service to save (create or update)
4. Return result to parent (accept/reject)

Data flow:
1. StorageFacilitiesPage creates dialog (Add mode or Edit mode)
2. Dialog populates form with facility data (if Edit)
3. User enters/modifies data
4. User clicks Save
5. Dialog validates and calls service
6. Dialog closes with accept() if success
7. Parent refreshes table
"""

from typing import Optional
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from models.storage_facility import StorageFacility
from services.storage_facility_service import StorageFacilityService
from ui.dialogs.generated_ui_storage_facility_dialog import Ui_AddEditFacilityDialog
import logging


logger = logging.getLogger(__name__)


class StorageFacilityDialog(QDialog):
    """Storage Facility Add/Edit Dialog (FORM DIALOG CONTROLLER).
    
    Modal dialog for adding or editing a storage facility.
    
    Modes:
    - ADD: Create new facility (code editable, default empty values)
    - EDIT: Modify existing facility (code read-only, values pre-populated)
    
    Usage (from StorageFacilitiesPage):
    
    # Add new facility
    dialog = StorageFacilityDialog(service, mode='add', parent=self)
    if dialog.exec() == QDialog.Accepted:
        # Dialog closed successfully, refresh table
        self._load_facilities()
    
    # Edit existing facility
    dialog = StorageFacilityDialog(service, mode='edit', facility=facility, parent=self)
    if dialog.exec() == QDialog.Accepted:
        # Dialog closed successfully, refresh table
        self._load_facilities()
    """
    
    def __init__(
        self,
        service: StorageFacilityService,
        mode: str = 'add',
        facility: Optional[StorageFacility] = None,
        parent=None
    ):
        """Initialize dialog (CONSTRUCTOR).
        
        Args:
            service: StorageFacilityService instance (for saving data)
            mode: 'add' (new facility) or 'edit' (existing facility)
            facility: StorageFacility object (required if mode='edit')
            parent: Parent widget
        """
        super().__init__(parent)
        self.ui = Ui_AddEditFacilityDialog()
        self.ui.setupUi(self)
        
        self.service = service
        self.mode = mode
        self.facility = facility
        self._apply_dialog_polish()
        self._normalize_status_options()
        
        # Set dialog title based on mode
        if mode == 'add':
            self.setWindowTitle("Add Storage Facility")
        else:
            self.setWindowTitle("Edit Storage Facility")
        
        # Wire up buttons (proper naming: btn_save, btn_cancel)
        self.ui.btn_save.clicked.connect(self._on_save)
        self.ui.btn_cancel.clicked.connect(self.reject)
        
        # Wire up facility type change to auto-update lined status (SMART UX)
        # When user changes type to Tank, automatically set lined status to Not Applicable
        self.ui.combo_type.currentTextChanged.connect(self._on_facility_type_changed)
        
        # Wire up automatic utilization calculation (AUTOMATIC CALCULATION)
        # When volume or capacity changes, utilization updates automatically
        if hasattr(self.ui, 'spin_volume'):
            self.ui.spin_volume.valueChanged.connect(self._update_utilization_display)
        if hasattr(self.ui, 'spin_capacity'):
            self.ui.spin_capacity.valueChanged.connect(self._update_utilization_display)
        
        # Configure based on mode
        if mode == 'edit':
            # Load existing facility data (block signals to prevent auto-set during load)
            self.ui.combo_type.blockSignals(True)
            self._populate_form_from_facility()
            self.ui.combo_type.blockSignals(False)
            # Make code read-only in edit mode
            self.ui.input_code.setReadOnly(True)
        else:
            # Add mode: focus on code field
            self.ui.input_code.setFocus()
            # Initialize lined combo to 'Not Applicable' as default
            self.ui.combo_lined.setCurrentIndex(0)  # 0 = Not Applicable
            # Wire automatic utilization for Add mode too
            self._update_utilization_display()
    
    def _update_utilization_display(self) -> None:
        """Update utilization percentage display (AUTOMATIC CALCULATION).
        
        Calculates: Utilization % = (Current Volume / Capacity) × 100
        
        Called automatically whenever volume or capacity spinboxes change.
        Displays result in label_utilization (read-only, auto-calculated).
        """
        try:
            capacity = self.ui.spin_capacity.value()
            volume = self.ui.spin_volume.value()
            
            if capacity > 0:
                utilization_pct = (volume / capacity) * 100
            else:
                utilization_pct = 0
            
            # Update utilization display label
            if hasattr(self.ui, 'label_utilization'):
                self.ui.label_utilization.setText(f"Utilization: {utilization_pct:.1f}%")
        except Exception as e:
            logger.warning(f"Failed to calculate utilization: {e}")
    
    def _on_facility_type_changed(self, facility_type: str) -> None:
        """Handle facility type change - auto-set lined status for tanks (SMART UX).
        
        When user changes facility type to Tank:
        1. Auto-set lined status to 'Not Applicable'
        2. Disable combo to prevent user override (greyed out)
        3. Ensures Tank facilities always save as None (NULL in database)
        
        For non-Tank types: Enable combo to allow user selection.
        
        Args:
            facility_type: Selected facility type
        """
        if facility_type == "Tank":
            self.ui.combo_lined.setCurrentIndex(0)  # Not Applicable
            self.ui.combo_lined.setEnabled(False)  # Greyed out, prevent changes
            logger.info(f"Tank type selected - locked lined status to 'Not Applicable' (disabled)")
        else:
            # Non-Tank: Enable combo to allow user choice
            self.ui.combo_lined.setEnabled(True)
            logger.debug(f"Non-Tank type '{facility_type}' selected - enabled lined status selection")
    
    def _populate_form_from_facility(self) -> None:
        """Populate form fields from facility object (EDIT MODE).
        
        Called when mode='edit' to show current facility data.
        Also sets up automatic utilization calculation.
        """
        if not self.facility:
            return
        
        try:
            self.ui.input_code.setText(self.facility.code)
            self.ui.input_name.setText(self.facility.name)
            self.ui.combo_type.setCurrentText(self.facility.facility_type)
            self.ui.spin_capacity.setValue(self.facility.capacity_m3)
            self.ui.spin_volume.setValue(self.facility.current_volume_m3)
            self.ui.spin_surface.setValue(self.facility.surface_area_m2 or 0)
            status_text = (self.facility.status or "Active").strip().capitalize()
            if self.ui.combo_status.findText(status_text) >= 0:
                self.ui.combo_status.setCurrentText(status_text)
            else:
                self.ui.combo_status.setCurrentIndex(0)
            self.ui.input_notes.setPlainText(self.facility.notes or "")
            
            # Apply auto-set logic: If Tank, set lined status to Not Applicable & disable
            # This is done AFTER loading the type to ensure correct behavior
            if self.facility.facility_type == "Tank":
                self.ui.combo_lined.setCurrentIndex(0)  # Not Applicable
                self.ui.combo_lined.setEnabled(False)  # Greyed out, locked for Tank
                logger.debug(f"Tank facility: Locked lined status to 'Not Applicable' (disabled combo)")
            else:
                # For non-Tank, load the actual stored value and enable combo for editing
                self.ui.combo_lined.setEnabled(True)  # Enable for user to change
                if self.facility.is_lined is True:
                    self.ui.combo_lined.setCurrentIndex(1)  # Lined
                elif self.facility.is_lined is False:
                    self.ui.combo_lined.setCurrentIndex(2)  # Unlined
                else:  # None = not applicable
                    self.ui.combo_lined.setCurrentIndex(0)  # Not Applicable
            
            # Calculate and display utilization (automatic)
            self._update_utilization_display()
            
            logger.debug(f"Form populated with facility: {self.facility.code}")
        except Exception as e:
            logger.error(f"Failed to populate form: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load facility data: {e}")
    
    def _get_form_data(self) -> dict:
        """Extract form data into dict (INTERNAL - FORM READING).
        
        Returns:
            Dict with form values for validation/save
        """
        # Extract is_lined from combo: 0=Not Applicable(None), 1=Lined(True), 2=Unlined(False)
        combo_index = self.ui.combo_lined.currentIndex()
        if combo_index == 1:  # Lined
            is_lined = True
        elif combo_index == 2:  # Unlined
            is_lined = False
        else:  # 0 = Not Applicable
            is_lined = None
        
        return {
            'code': self.ui.input_code.text().strip(),
            'name': self.ui.input_name.text().strip(),
            'facility_type': self.ui.combo_type.currentText(),
            'capacity_m3': self.ui.spin_capacity.value(),
            'surface_area_m2': self.ui.spin_surface.value() or None,
            'current_volume_m3': self.ui.spin_volume.value(),
            'is_lined': is_lined,
            # Persist lowercase to match DB check constraint and model defaults.
            'status': self.ui.combo_status.currentText().strip().lower(),
            'notes': self.ui.input_notes.toPlainText().strip() or None
        }

    def _normalize_status_options(self) -> None:
        """Use title-case statuses for cleaner UI labels."""
        if hasattr(self.ui, "combo_status"):
            self.ui.combo_status.clear()
            self.ui.combo_status.addItems(["Active", "Inactive", "Decommissioned"])

    def _apply_dialog_polish(self) -> None:
        """Apply consistent dialog styling and fix spinbox appearance."""
        self.setMinimumSize(560, 470)
        self.resize(560, 500)

        self.ui.formLayout_facility.setHorizontalSpacing(14)
        self.ui.formLayout_facility.setVerticalSpacing(10)
        self.ui.formLayout_facility.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        for widget_name in ("input_code", "input_name", "combo_type", "combo_status", "combo_lined"):
            if hasattr(self.ui, widget_name):
                getattr(self.ui, widget_name).setMinimumHeight(31)
        if hasattr(self.ui, "input_notes"):
            self.ui.input_notes.setMinimumHeight(90)
            self.ui.input_notes.setMaximumHeight(110)

        # Stabilize numeric controls so stepper area does not look clipped.
        for spin_name in ("spin_capacity", "spin_volume", "spin_surface"):
            if hasattr(self.ui, spin_name):
                spin = getattr(self.ui, spin_name)
                spin.setMinimumHeight(31)
                spin.setButtonSymbols(spin.ButtonSymbols.UpDownArrows)
                spin.setKeyboardTracking(False)

        self.ui.btn_save.setMinimumHeight(34)
        self.ui.btn_cancel.setMinimumHeight(34)
        self.ui.btn_cancel.setIcon(QIcon(":/icons/cancel_icon.svg"))
        self.ui.btn_cancel.setIconSize(QSize(14, 14))

        self.setStyleSheet(
            """
            QDialog {
                background: #f5f8fc;
            }
            QGroupBox {
                border: 1px solid #c9d8ea;
                border-radius: 10px;
                margin-top: 8px;
                padding: 10px;
                color: #173b68;
                font-weight: 600;
            }
            QLineEdit, QComboBox, QPlainTextEdit, QDoubleSpinBox {
                background: #ffffff;
                border: 1px solid #b8c9dd;
                border-radius: 6px;
                padding: 4px 8px;
                color: #0f2747;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border: none;
            }
            QPushButton {
                min-width: 88px;
                border: 1px solid #b7c7db;
                border-radius: 8px;
                padding: 6px 12px;
                background: #f8fbff;
                color: #173b68;
            }
            QPushButton:hover {
                background: #eef4fb;
            }
            QPushButton#btn_save {
                background: #1f4f8f;
                border: 1px solid #1f4f8f;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton#btn_save:hover {
                background: #1a457d;
            }
            """
        )
    
    def _validate_form(self, data: dict) -> Optional[str]:
        """Validate form data before save (VALIDATION).
        
        Args:
            data: Dict from _get_form_data()
        
        Returns:
            Error message if validation fails, None if valid
        """
        # Required fields
        if not data['code']:
            return "Facility code is required"
        if not data['name']:
            return "Facility name is required"
        if not data['facility_type']:
            return "Facility type is required"
        
        # Logical validations
        if data['capacity_m3'] <= 0:
            return "Capacity must be greater than 0"
        if data['current_volume_m3'] > data['capacity_m3']:
            return "Current volume cannot exceed capacity"
        if data['surface_area_m2'] and data['surface_area_m2'] < 0:
            return "Surface area cannot be negative"
        
        return None  # Valid
    
    def _on_save(self) -> None:
        """Save facility data (SAVE OPERATION).
        
        Validates form, calls service to save, closes dialog if successful.
        Shows error dialog if validation or save fails.
        """
        try:
            # Get form data
            data = self._get_form_data()
            
            # Validate
            error = self._validate_form(data)
            if error:
                QMessageBox.warning(self, "Validation Error", error)
                return
            
            # Save via service
            if self.mode == 'add':
                # Create new facility
                self.service.add_facility(
                    code=data['code'],
                    name=data['name'],
                    facility_type=data['facility_type'],
                    capacity_m3=data['capacity_m3'],
                    surface_area_m2=data['surface_area_m2'],
                    current_volume_m3=data['current_volume_m3'],
                    is_lined=data['is_lined'],
                    notes=data['notes']
                )
                logger.info(f"Created facility: {data['code']}")
                QMessageBox.information(self, "Success", f"Facility '{data['code']}' created successfully!")
            else:
                # Update existing facility
                self.service.update_facility(
                    facility_id=self.facility.id,
                    name=data['name'],
                    facility_type=data['facility_type'],
                    capacity_m3=data['capacity_m3'],
                    surface_area_m2=data['surface_area_m2'],
                    current_volume_m3=data['current_volume_m3'],
                    is_lined=data['is_lined'],
                    status=data['status'],
                    notes=data['notes']
                )
                logger.info(f"Updated facility: {data['code']}")
                QMessageBox.information(self, "Success", f"Facility '{data['code']}' updated successfully!")
            
            # Close dialog (accept)
            self.accept()
        except ValueError as e:
            # Service validation error (user-friendly error message)
            logger.warning(f"Validation error: {e}")
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            # Unexpected error
            logger.error(f"Failed to save facility: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save facility: {e}")
