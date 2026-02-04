# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'storage_facility_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_AddEditFacilityDialog(object):
    def setupUi(self, AddEditFacilityDialog):
        if not AddEditFacilityDialog.objectName():
            AddEditFacilityDialog.setObjectName(u"AddEditFacilityDialog")
        AddEditFacilityDialog.resize(500, 450)
        self.verticalLayout_main = QVBoxLayout(AddEditFacilityDialog)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.groupBox_facility = QGroupBox(AddEditFacilityDialog)
        self.groupBox_facility.setObjectName(u"groupBox_facility")
        self.formLayout_facility = QFormLayout(self.groupBox_facility)
        self.formLayout_facility.setObjectName(u"formLayout_facility")
        self.label_code = QLabel(self.groupBox_facility)
        self.label_code.setObjectName(u"label_code")

        self.formLayout_facility.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_code)

        self.input_code = QLineEdit(self.groupBox_facility)
        self.input_code.setObjectName(u"input_code")

        self.formLayout_facility.setWidget(0, QFormLayout.ItemRole.FieldRole, self.input_code)

        self.label_name = QLabel(self.groupBox_facility)
        self.label_name.setObjectName(u"label_name")

        self.formLayout_facility.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_name)

        self.input_name = QLineEdit(self.groupBox_facility)
        self.input_name.setObjectName(u"input_name")

        self.formLayout_facility.setWidget(1, QFormLayout.ItemRole.FieldRole, self.input_name)

        self.label_type = QLabel(self.groupBox_facility)
        self.label_type.setObjectName(u"label_type")

        self.formLayout_facility.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_type)

        self.combo_type = QComboBox(self.groupBox_facility)
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.addItem("")
        self.combo_type.setObjectName(u"combo_type")

        self.formLayout_facility.setWidget(2, QFormLayout.ItemRole.FieldRole, self.combo_type)

        self.label_capacity = QLabel(self.groupBox_facility)
        self.label_capacity.setObjectName(u"label_capacity")

        self.formLayout_facility.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_capacity)

        self.spin_capacity = QDoubleSpinBox(self.groupBox_facility)
        self.spin_capacity.setObjectName(u"spin_capacity")
        self.spin_capacity.setMinimum(1.000000000000000)
        self.spin_capacity.setMaximum(1000000.000000000000000)
        self.spin_capacity.setValue(100000.000000000000000)

        self.formLayout_facility.setWidget(3, QFormLayout.ItemRole.FieldRole, self.spin_capacity)

        self.label_volume = QLabel(self.groupBox_facility)
        self.label_volume.setObjectName(u"label_volume")

        self.formLayout_facility.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_volume)

        self.spin_volume = QDoubleSpinBox(self.groupBox_facility)
        self.spin_volume.setObjectName(u"spin_volume")
        self.spin_volume.setMinimum(0.000000000000000)
        self.spin_volume.setMaximum(1000000.000000000000000)
        self.spin_volume.setValue(0.000000000000000)

        self.formLayout_facility.setWidget(4, QFormLayout.ItemRole.FieldRole, self.spin_volume)

        self.label_surface = QLabel(self.groupBox_facility)
        self.label_surface.setObjectName(u"label_surface")

        self.formLayout_facility.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_surface)

        self.spin_surface = QDoubleSpinBox(self.groupBox_facility)
        self.spin_surface.setObjectName(u"spin_surface")
        self.spin_surface.setMinimum(0.000000000000000)
        self.spin_surface.setMaximum(100000.000000000000000)
        self.spin_surface.setValue(0.000000000000000)

        self.formLayout_facility.setWidget(5, QFormLayout.ItemRole.FieldRole, self.spin_surface)

        self.label_status = QLabel(self.groupBox_facility)
        self.label_status.setObjectName(u"label_status")

        self.formLayout_facility.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_status)

        self.combo_status = QComboBox(self.groupBox_facility)
        self.combo_status.addItem("")
        self.combo_status.addItem("")
        self.combo_status.addItem("")
        self.combo_status.setObjectName(u"combo_status")

        self.formLayout_facility.setWidget(6, QFormLayout.ItemRole.FieldRole, self.combo_status)

        self.label_lined = QLabel(self.groupBox_facility)
        self.label_lined.setObjectName(u"label_lined")

        self.formLayout_facility.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_lined)

        self.combo_lined = QComboBox(self.groupBox_facility)
        self.combo_lined.addItem("")
        self.combo_lined.addItem("")
        self.combo_lined.addItem("")
        self.combo_lined.setObjectName(u"combo_lined")

        self.formLayout_facility.setWidget(7, QFormLayout.ItemRole.FieldRole, self.combo_lined)

        self.label_notes = QLabel(self.groupBox_facility)
        self.label_notes.setObjectName(u"label_notes")

        self.formLayout_facility.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_notes)

        self.input_notes = QPlainTextEdit(self.groupBox_facility)
        self.input_notes.setObjectName(u"input_notes")
        self.input_notes.setMinimumHeight(80)
        self.input_notes.setMaximumHeight(100)

        self.formLayout_facility.setWidget(8, QFormLayout.ItemRole.FieldRole, self.input_notes)


        self.verticalLayout_main.addWidget(self.groupBox_facility)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer)

        self.btn_save = QPushButton(AddEditFacilityDialog)
        self.btn_save.setObjectName(u"btn_save")

        self.horizontalLayout_buttons.addWidget(self.btn_save)

        self.btn_cancel = QPushButton(AddEditFacilityDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")

        self.horizontalLayout_buttons.addWidget(self.btn_cancel)


        self.verticalLayout_main.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(AddEditFacilityDialog)

        QMetaObject.connectSlotsByName(AddEditFacilityDialog)
    # setupUi

    def retranslateUi(self, AddEditFacilityDialog):
        AddEditFacilityDialog.setWindowTitle(QCoreApplication.translate("AddEditFacilityDialog", u"Storage Facility", None))
        self.groupBox_facility.setTitle(QCoreApplication.translate("AddEditFacilityDialog", u"Facility Information", None))
        self.label_code.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Facility Code:", None))
        self.input_code.setPlaceholderText(QCoreApplication.translate("AddEditFacilityDialog", u"e.g., NDCD1", None))
        self.label_name.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Facility Name:", None))
        self.input_name.setPlaceholderText(QCoreApplication.translate("AddEditFacilityDialog", u"e.g., North Decline Decant 1", None))
        self.label_type.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Facility Type:", None))
        self.combo_type.setItemText(0, QCoreApplication.translate("AddEditFacilityDialog", u"TSF", None))
        self.combo_type.setItemText(1, QCoreApplication.translate("AddEditFacilityDialog", u"Pond", None))
        self.combo_type.setItemText(2, QCoreApplication.translate("AddEditFacilityDialog", u"Dam", None))
        self.combo_type.setItemText(3, QCoreApplication.translate("AddEditFacilityDialog", u"Tank", None))
        self.combo_type.setItemText(4, QCoreApplication.translate("AddEditFacilityDialog", u"Other", None))

        self.label_capacity.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Capacity (m\u00b3):", None))
        self.label_volume.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Current Volume (m\u00b3):", None))
        self.label_surface.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Surface Area (m\u00b2):", None))
        self.label_status.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Status:", None))
        self.combo_status.setItemText(0, QCoreApplication.translate("AddEditFacilityDialog", u"active", None))
        self.combo_status.setItemText(1, QCoreApplication.translate("AddEditFacilityDialog", u"inactive", None))
        self.combo_status.setItemText(2, QCoreApplication.translate("AddEditFacilityDialog", u"decommissioned", None))

        self.label_lined.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Lined Status:", None))
        self.combo_lined.setItemText(0, QCoreApplication.translate("AddEditFacilityDialog", u"Not Applicable", None))
        self.combo_lined.setItemText(1, QCoreApplication.translate("AddEditFacilityDialog", u"Lined", None))
        self.combo_lined.setItemText(2, QCoreApplication.translate("AddEditFacilityDialog", u"Unlined", None))

        self.label_notes.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Notes:", None))
        self.btn_save.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Save", None))
        self.btn_cancel.setText(QCoreApplication.translate("AddEditFacilityDialog", u"Cancel", None))
    # retranslateUi

