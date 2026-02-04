# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monthly_parameters_dialog.ui'
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
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTableView, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, monthly_parameters_dialog):
        if not monthly_parameters_dialog.objectName():
            monthly_parameters_dialog.setObjectName(u"monthly_parameters_dialog")
        monthly_parameters_dialog.setMinimumSize(QSize(900, 600))
        self.verticalLayout_main = QVBoxLayout(monthly_parameters_dialog)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.frame_header = QFrame(monthly_parameters_dialog)
        self.frame_header.setObjectName(u"frame_header")
        self.frame_header.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_header = QVBoxLayout(self.frame_header)
        self.verticalLayout_header.setObjectName(u"verticalLayout_header")
        self.label_title = QLabel(self.frame_header)
        self.label_title.setObjectName(u"label_title")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_title.setFont(font)

        self.verticalLayout_header.addWidget(self.label_title)

        self.label_facility = QLabel(self.frame_header)
        self.label_facility.setObjectName(u"label_facility")

        self.verticalLayout_header.addWidget(self.label_facility)


        self.verticalLayout_main.addWidget(self.frame_header)

        self.group_inputs = QGroupBox(monthly_parameters_dialog)
        self.group_inputs.setObjectName(u"group_inputs")
        self.gridLayout_inputs = QGridLayout(self.group_inputs)
        self.gridLayout_inputs.setObjectName(u"gridLayout_inputs")
        self.label_record_status = QLabel(self.group_inputs)
        self.label_record_status.setObjectName(u"label_record_status")
        self.label_record_status.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_inputs.addWidget(self.label_record_status, 2, 0, 1, 4)

        self.label_year = QLabel(self.group_inputs)
        self.label_year.setObjectName(u"label_year")

        self.gridLayout_inputs.addWidget(self.label_year, 0, 0, 1, 1)

        self.spin_year = QSpinBox(self.group_inputs)
        self.spin_year.setObjectName(u"spin_year")
        self.spin_year.setMinimum(2000)
        self.spin_year.setMaximum(2100)
        self.spin_year.setValue(2026)

        self.gridLayout_inputs.addWidget(self.spin_year, 0, 1, 1, 1)

        self.label_month = QLabel(self.group_inputs)
        self.label_month.setObjectName(u"label_month")

        self.gridLayout_inputs.addWidget(self.label_month, 0, 2, 1, 1)

        self.combo_month = QComboBox(self.group_inputs)
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.addItem("")
        self.combo_month.setObjectName(u"combo_month")

        self.gridLayout_inputs.addWidget(self.combo_month, 0, 3, 1, 1)

        self.label_inflows = QLabel(self.group_inputs)
        self.label_inflows.setObjectName(u"label_inflows")

        self.gridLayout_inputs.addWidget(self.label_inflows, 1, 0, 1, 1)

        self.spin_inflows = QDoubleSpinBox(self.group_inputs)
        self.spin_inflows.setObjectName(u"spin_inflows")
        self.spin_inflows.setMinimum(0.000000000000000)
        self.spin_inflows.setMaximum(1000000000.000000000000000)
        self.spin_inflows.setDecimals(2)
        self.spin_inflows.setSingleStep(1000.000000000000000)

        self.gridLayout_inputs.addWidget(self.spin_inflows, 1, 1, 1, 1)

        self.label_outflows = QLabel(self.group_inputs)
        self.label_outflows.setObjectName(u"label_outflows")

        self.gridLayout_inputs.addWidget(self.label_outflows, 1, 2, 1, 1)

        self.spin_outflows = QDoubleSpinBox(self.group_inputs)
        self.spin_outflows.setObjectName(u"spin_outflows")
        self.spin_outflows.setMinimum(0.000000000000000)
        self.spin_outflows.setMaximum(1000000000.000000000000000)
        self.spin_outflows.setDecimals(2)
        self.spin_outflows.setSingleStep(1000.000000000000000)

        self.gridLayout_inputs.addWidget(self.spin_outflows, 1, 3, 1, 1)


        self.verticalLayout_main.addWidget(self.group_inputs)

        self.group_history = QGroupBox(monthly_parameters_dialog)
        self.group_history.setObjectName(u"group_history")
        self.verticalLayout_history = QVBoxLayout(self.group_history)
        self.verticalLayout_history.setObjectName(u"verticalLayout_history")
        self.table_history = QTableView(self.group_history)
        self.table_history.setObjectName(u"table_history")

        self.verticalLayout_history.addWidget(self.table_history)


        self.verticalLayout_main.addWidget(self.group_history)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.spacer_left = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.spacer_left)

        self.btn_save = QPushButton(monthly_parameters_dialog)
        self.btn_save.setObjectName(u"btn_save")

        self.horizontalLayout_buttons.addWidget(self.btn_save)

        self.btn_update = QPushButton(monthly_parameters_dialog)
        self.btn_update.setObjectName(u"btn_update")

        self.horizontalLayout_buttons.addWidget(self.btn_update)

        self.btn_delete = QPushButton(monthly_parameters_dialog)
        self.btn_delete.setObjectName(u"btn_delete")

        self.horizontalLayout_buttons.addWidget(self.btn_delete)

        self.btn_close = QPushButton(monthly_parameters_dialog)
        self.btn_close.setObjectName(u"btn_close")

        self.horizontalLayout_buttons.addWidget(self.btn_close)


        self.verticalLayout_main.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(monthly_parameters_dialog)

        QMetaObject.connectSlotsByName(monthly_parameters_dialog)
    # setupUi

    def retranslateUi(self, monthly_parameters_dialog):
        monthly_parameters_dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Monthly Parameters", None))
        self.label_title.setText(QCoreApplication.translate("Dialog", u"Monthly Parameters", None))
        self.label_facility.setText(QCoreApplication.translate("Dialog", u"Facility: <code>", None))
        self.group_inputs.setTitle(QCoreApplication.translate("Dialog", u"Monthly Totals", None))
        self.label_record_status.setText(QCoreApplication.translate("Dialog", u"Status: Ready", None))
        self.label_year.setText(QCoreApplication.translate("Dialog", u"Year", None))
        self.label_month.setText(QCoreApplication.translate("Dialog", u"Month", None))
        self.combo_month.setItemText(0, QCoreApplication.translate("Dialog", u"January", None))
        self.combo_month.setItemText(1, QCoreApplication.translate("Dialog", u"February", None))
        self.combo_month.setItemText(2, QCoreApplication.translate("Dialog", u"March", None))
        self.combo_month.setItemText(3, QCoreApplication.translate("Dialog", u"April", None))
        self.combo_month.setItemText(4, QCoreApplication.translate("Dialog", u"May", None))
        self.combo_month.setItemText(5, QCoreApplication.translate("Dialog", u"June", None))
        self.combo_month.setItemText(6, QCoreApplication.translate("Dialog", u"July", None))
        self.combo_month.setItemText(7, QCoreApplication.translate("Dialog", u"August", None))
        self.combo_month.setItemText(8, QCoreApplication.translate("Dialog", u"September", None))
        self.combo_month.setItemText(9, QCoreApplication.translate("Dialog", u"October", None))
        self.combo_month.setItemText(10, QCoreApplication.translate("Dialog", u"November", None))
        self.combo_month.setItemText(11, QCoreApplication.translate("Dialog", u"December", None))

        self.label_inflows.setText(QCoreApplication.translate("Dialog", u"Total Inflows (m\u00b3)", None))
        self.label_outflows.setText(QCoreApplication.translate("Dialog", u"Total Outflows (m\u00b3)", None))
        self.group_history.setTitle(QCoreApplication.translate("Dialog", u"History for this Facility", None))
        self.btn_save.setText(QCoreApplication.translate("Dialog", u"Save", None))
        self.btn_update.setText(QCoreApplication.translate("Dialog", u"Update", None))
        self.btn_delete.setText(QCoreApplication.translate("Dialog", u"Delete", None))
        self.btn_close.setText(QCoreApplication.translate("Dialog", u"Close", None))
    # retranslateUi

