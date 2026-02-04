# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_edit_node_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_AddEditNodeDialog(object):
    def setupUi(self, AddEditNodeDialog):
        if not AddEditNodeDialog.objectName():
            AddEditNodeDialog.setObjectName(u"AddEditNodeDialog")
        AddEditNodeDialog.resize(450, 350)
        AddEditNodeDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(AddEditNodeDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_id = QLabel(AddEditNodeDialog)
        self.label_id.setObjectName(u"label_id")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_id)

        self.input_id = QLineEdit(AddEditNodeDialog)
        self.input_id.setObjectName(u"input_id")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.input_id)

        self.label_label = QLabel(AddEditNodeDialog)
        self.label_label.setObjectName(u"label_label")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_label)

        self.input_label = QPlainTextEdit(AddEditNodeDialog)
        self.input_label.setObjectName(u"input_label")
        self.input_label.setMaximumHeight(60)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.input_label)

        self.label_type = QLabel(AddEditNodeDialog)
        self.label_type.setObjectName(u"label_type")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_type)

        self.combo_type = QComboBox(AddEditNodeDialog)
        self.combo_type.addItem("")  # None
        self.combo_type.addItem("")  # Sewage Treatment Plant
        self.combo_type.addItem("")  # Discharge/Sink
        self.combo_type.addItem("")  # Dam
        self.combo_type.addItem("")  # Reservoir
        self.combo_type.addItem("")  # TSF
        self.combo_type.addItem("")  # Boreholes
        self.combo_type.addItem("")  # Rainfall
        self.combo_type.addItem("")  # Office/Buildings
        self.combo_type.addItem("")  # Plant
        self.combo_type.setObjectName(u"combo_type")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.combo_type)

        self.label_shape = QLabel(AddEditNodeDialog)
        self.label_shape.setObjectName(u"label_shape")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_shape)

        self.combo_shape = QComboBox(AddEditNodeDialog)
        self.combo_shape.addItem("")
        self.combo_shape.addItem("")
        self.combo_shape.setObjectName(u"combo_shape")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.combo_shape)

        self.label_color = QLabel(AddEditNodeDialog)
        self.label_color.setObjectName(u"label_color")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_color)

        self.horizontalLayout_color = QHBoxLayout()
        self.horizontalLayout_color.setObjectName(u"horizontalLayout_color")
        self.btn_color_picker = QPushButton(AddEditNodeDialog)
        self.btn_color_picker.setObjectName(u"btn_color_picker")
        self.btn_color_picker.setMinimumHeight(32)

        self.horizontalLayout_color.addWidget(self.btn_color_picker)

        self.label_color_preview = QLabel(AddEditNodeDialog)
        self.label_color_preview.setObjectName(u"label_color_preview")
        self.label_color_preview.setMinimumSize(QSize(50, 32))
        self.label_color_preview.setMaximumSize(QSize(50, 32))

        self.horizontalLayout_color.addWidget(self.label_color_preview)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_color.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(4, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_color)

        self.label_lock = QLabel(AddEditNodeDialog)
        self.label_lock.setObjectName(u"label_lock")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_lock)

        self.checkbox_lock = QCheckBox(AddEditNodeDialog)
        self.checkbox_lock.setObjectName(u"checkbox_lock")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.checkbox_lock)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.horizontalSpacer_buttons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer_buttons)

        self.btn_ok = QPushButton(AddEditNodeDialog)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton(AddEditNodeDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(AddEditNodeDialog)
        self.btn_ok.clicked.connect(AddEditNodeDialog.accept)
        self.btn_cancel.clicked.connect(AddEditNodeDialog.reject)

        self.btn_ok.setDefault(True)


        QMetaObject.connectSlotsByName(AddEditNodeDialog)
    # setupUi

    def retranslateUi(self, AddEditNodeDialog):
        AddEditNodeDialog.setWindowTitle(QCoreApplication.translate("AddEditNodeDialog", u"Add/Edit Component", None))
        self.label_id.setText(QCoreApplication.translate("AddEditNodeDialog", u"Component ID:", None))
        self.input_id.setPlaceholderText(QCoreApplication.translate("AddEditNodeDialog", u"e.g., bh_ndgwa (lowercase, underscores)", None))
        self.label_label.setText(QCoreApplication.translate("AddEditNodeDialog", u"Label:", None))
        self.input_label.setPlaceholderText(QCoreApplication.translate("AddEditNodeDialog", u"Display text (supports line breaks with \\n)", None))
        self.label_type.setText(QCoreApplication.translate("AddEditNodeDialog", u"Component Type:", None))
        self.combo_type.setItemText(0, QCoreApplication.translate("AddEditNodeDialog", u"None", None))
        self.combo_type.setItemText(1, QCoreApplication.translate("AddEditNodeDialog", u"Sewage Treatment Plant", None))
        self.combo_type.setItemText(2, QCoreApplication.translate("AddEditNodeDialog", u"Discharge/Sink", None))
        self.combo_type.setItemText(3, QCoreApplication.translate("AddEditNodeDialog", u"Dam", None))
        self.combo_type.setItemText(4, QCoreApplication.translate("AddEditNodeDialog", u"Reservoir", None))
        self.combo_type.setItemText(5, QCoreApplication.translate("AddEditNodeDialog", u"TSF", None))
        self.combo_type.setItemText(6, QCoreApplication.translate("AddEditNodeDialog", u"Boreholes", None))
        self.combo_type.setItemText(7, QCoreApplication.translate("AddEditNodeDialog", u"Rainfall", None))
        self.combo_type.setItemText(8, QCoreApplication.translate("AddEditNodeDialog", u"Office/Buildings", None))
        self.combo_type.setItemText(9, QCoreApplication.translate("AddEditNodeDialog", u"Plant", None))

        self.label_shape.setText(QCoreApplication.translate("AddEditNodeDialog", u"Shape:", None))
        self.combo_shape.setItemText(0, QCoreApplication.translate("AddEditNodeDialog", u"Rectangle", None))
        self.combo_shape.setItemText(1, QCoreApplication.translate("AddEditNodeDialog", u"Oval/Circle", None))

        self.label_color.setText(QCoreApplication.translate("AddEditNodeDialog", u"Fill Color:", None))
        self.btn_color_picker.setText(QCoreApplication.translate("AddEditNodeDialog", u"Choose Color", None))
        self.label_color_preview.setStyleSheet(QCoreApplication.translate("AddEditNodeDialog", u"border: 1px solid #333;", None))
        self.label_color_preview.setText("")
        self.label_lock.setText(QCoreApplication.translate("AddEditNodeDialog", u"Lock Component:", None))
        self.checkbox_lock.setText(QCoreApplication.translate("AddEditNodeDialog", u"Prevent dragging", None))
        self.btn_ok.setText(QCoreApplication.translate("AddEditNodeDialog", u"OK", None))
        self.btn_cancel.setText(QCoreApplication.translate("AddEditNodeDialog", u"Cancel", None))
    # retranslateUi

