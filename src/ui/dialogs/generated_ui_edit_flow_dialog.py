# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'edit_flow_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_EditFlowDialog(object):
    def setupUi(self, EditFlowDialog):
        if not EditFlowDialog.objectName():
            EditFlowDialog.setObjectName(u"EditFlowDialog")
        EditFlowDialog.resize(500, 400)
        EditFlowDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(EditFlowDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_from = QLabel(EditFlowDialog)
        self.label_from.setObjectName(u"label_from")
        self.label_from.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_from)

        self.value_from = QLabel(EditFlowDialog)
        self.value_from.setObjectName(u"value_from")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.value_from)

        self.label_to = QLabel(EditFlowDialog)
        self.label_to.setObjectName(u"label_to")
        self.label_to.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_to)

        self.value_to = QLabel(EditFlowDialog)
        self.value_to.setObjectName(u"value_to")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.value_to)

        self.label_flow_type = QLabel(EditFlowDialog)
        self.label_flow_type.setObjectName(u"label_flow_type")
        self.label_flow_type.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_flow_type)

        self.combo_flow_type = QComboBox(EditFlowDialog)
        self.combo_flow_type.addItem("")
        self.combo_flow_type.addItem("")
        self.combo_flow_type.addItem("")
        self.combo_flow_type.addItem("")
        self.combo_flow_type.setObjectName(u"combo_flow_type")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.combo_flow_type)

        self.label_color = QLabel(EditFlowDialog)
        self.label_color.setObjectName(u"label_color")
        self.label_color.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_color)

        self.horizontalLayout_color = QHBoxLayout()
        self.horizontalLayout_color.setObjectName(u"horizontalLayout_color")
        self.btn_color_picker = QPushButton(EditFlowDialog)
        self.btn_color_picker.setObjectName(u"btn_color_picker")
        self.btn_color_picker.setMinimumHeight(32)

        self.horizontalLayout_color.addWidget(self.btn_color_picker)

        self.label_color_preview = QLabel(EditFlowDialog)
        self.label_color_preview.setObjectName(u"label_color_preview")
        self.label_color_preview.setMinimumSize(QSize(50, 32))
        self.label_color_preview.setMaximumSize(QSize(50, 32))

        self.horizontalLayout_color.addWidget(self.label_color_preview)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_color.addItem(self.horizontalSpacer)


        self.formLayout.setLayout(3, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_color)

        self.label_excel = QLabel(EditFlowDialog)
        self.label_excel.setObjectName(u"label_excel")
        self.label_excel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_excel)

        self.groupBox_excel = QGroupBox(EditFlowDialog)
        self.groupBox_excel.setObjectName(u"groupBox_excel")
        self.formLayout_excel = QFormLayout(self.groupBox_excel)
        self.formLayout_excel.setObjectName(u"formLayout_excel")
        self.label_sheet = QLabel(self.groupBox_excel)
        self.label_sheet.setObjectName(u"label_sheet")

        self.formLayout_excel.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_sheet)

        self.combo_sheet = QComboBox(self.groupBox_excel)
        self.combo_sheet.setObjectName(u"combo_sheet")
        self.combo_sheet.setEditable(True)

        self.formLayout_excel.setWidget(0, QFormLayout.ItemRole.FieldRole, self.combo_sheet)

        self.label_column = QLabel(self.groupBox_excel)
        self.label_column.setObjectName(u"label_column")

        self.formLayout_excel.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_column)

        self.combo_column = QComboBox(self.groupBox_excel)
        self.combo_column.setObjectName(u"combo_column")
        self.combo_column.setEditable(True)

        self.formLayout_excel.setWidget(1, QFormLayout.ItemRole.FieldRole, self.combo_column)

        self.btn_auto_map = QPushButton(self.groupBox_excel)
        self.btn_auto_map.setObjectName(u"btn_auto_map")

        self.formLayout_excel.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.btn_auto_map)


        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.groupBox_excel)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.horizontalSpacer_buttons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer_buttons)

        self.btn_ok = QPushButton(EditFlowDialog)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton(EditFlowDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(EditFlowDialog)
        self.btn_ok.clicked.connect(EditFlowDialog.accept)
        self.btn_cancel.clicked.connect(EditFlowDialog.reject)

        self.btn_ok.setDefault(True)


        QMetaObject.connectSlotsByName(EditFlowDialog)
    # setupUi

    def retranslateUi(self, EditFlowDialog):
        EditFlowDialog.setWindowTitle(QCoreApplication.translate("EditFlowDialog", u"Edit Flow Line", None))
        self.label_from.setText(QCoreApplication.translate("EditFlowDialog", u"From Component:", None))
        self.value_from.setText(QCoreApplication.translate("EditFlowDialog", u"[Source Node Name]", None))
        self.value_from.setStyleSheet(QCoreApplication.translate("EditFlowDialog", u"QLabel { background-color: #f0f0f0; padding: 5px; border-radius: 3px; }", None))
        self.label_to.setText(QCoreApplication.translate("EditFlowDialog", u"To Component:", None))
        self.value_to.setText(QCoreApplication.translate("EditFlowDialog", u"[Destination Node Name]", None))
        self.value_to.setStyleSheet(QCoreApplication.translate("EditFlowDialog", u"QLabel { background-color: #f0f0f0; padding: 5px; border-radius: 3px; }", None))
        self.label_flow_type.setText(QCoreApplication.translate("EditFlowDialog", u"Flow Type:", None))
        self.combo_flow_type.setItemText(0, QCoreApplication.translate("EditFlowDialog", u"Clean Water", None))
        self.combo_flow_type.setItemText(1, QCoreApplication.translate("EditFlowDialog", u"Dirty/Waste Water", None))
        self.combo_flow_type.setItemText(2, QCoreApplication.translate("EditFlowDialog", u"Evaporation Loss", None))
        self.combo_flow_type.setItemText(3, QCoreApplication.translate("EditFlowDialog", u"Recirculation", None))

        self.label_color.setText(QCoreApplication.translate("EditFlowDialog", u"Flow Line Color:", None))
        self.btn_color_picker.setText(QCoreApplication.translate("EditFlowDialog", u"Choose Color", None))
        self.label_color_preview.setStyleSheet(QCoreApplication.translate("EditFlowDialog", u"border: 2px solid #333;", None))
        self.label_color_preview.setText("")
        self.label_excel.setText(QCoreApplication.translate("EditFlowDialog", u"Excel Mapping:", None))
        self.groupBox_excel.setTitle("")
        self.label_sheet.setText(QCoreApplication.translate("EditFlowDialog", u"Sheet Name:", None))
        self.label_column.setText(QCoreApplication.translate("EditFlowDialog", u"Column Name:", None))
        self.btn_auto_map.setText(QCoreApplication.translate("EditFlowDialog", u"Auto-Map (Intelligent Matching)", None))
        self.btn_ok.setText(QCoreApplication.translate("EditFlowDialog", u"OK", None))
        self.btn_cancel.setText(QCoreApplication.translate("EditFlowDialog", u"Cancel", None))
    # retranslateUi

