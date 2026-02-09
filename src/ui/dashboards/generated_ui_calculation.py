# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'calculation.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTabWidget, QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1208, 838)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 120))
        self.frame.setMaximumSize(QSize(16777215, 120))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(30, 30))
        self.label_4.setMaximumSize(QSize(30, 30))
        self.label_4.setPixmap(QPixmap(u":/icons/Calculations_2.svg"))
        self.label_4.setScaledContents(True)

        self.horizontalLayout_3.addWidget(self.label_4)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_3.addWidget(self.label_5)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_2.addWidget(self.label_6)

        self.label_7 = QLabel(self.frame)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_2.addWidget(self.label_7)

        self.comboBox = QComboBox(self.frame)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")

        self.horizontalLayout_2.addWidget(self.comboBox)

        self.label_8 = QLabel(self.frame)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_2.addWidget(self.label_8)

        self.comboBox_2 = QComboBox(self.frame)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")

        self.horizontalLayout_2.addWidget(self.comboBox_2)

        self.pushButton = QPushButton(self.frame)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QSize(150, 35))
        self.pushButton.setMaximumSize(QSize(150, 35))

        self.horizontalLayout_2.addWidget(self.pushButton)

        self.horizontalSpacer_2 = QSpacerItem(628, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.gridLayout.addWidget(self.frame, 1, 0, 1, 1)

        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.System_Balance_Regulator = QWidget()
        self.System_Balance_Regulator.setObjectName(u"System_Balance_Regulator")
        self.label_9 = QLabel(self.System_Balance_Regulator)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(430, 170, 331, 141))
        self.tabWidget.addTab(self.System_Balance_Regulator, "")
        self.Recycled_Water = QWidget()
        self.Recycled_Water.setObjectName(u"Recycled_Water")
        self.label_10 = QLabel(self.Recycled_Water)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(340, 150, 171, 61))
        self.tabWidget.addTab(self.Recycled_Water, "")
        self.Data_Quality = QWidget()
        self.Data_Quality.setObjectName(u"Data_Quality")
        self.label_11 = QLabel(self.Data_Quality)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(470, 220, 241, 101))
        self.tabWidget.addTab(self.Data_Quality, "")
        self.Inputs_Audit = QWidget()
        self.Inputs_Audit.setObjectName(u"Inputs_Audit")
        self.label_12 = QLabel(self.Inputs_Audit)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setGeometry(QRect(470, 220, 231, 131))
        self.tabWidget.addTab(self.Inputs_Audit, "")
        self.Manual_Inputs = QWidget()
        self.Manual_Inputs.setObjectName(u"Manual_Inputs")
        self.label_13 = QLabel(self.Manual_Inputs)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setGeometry(QRect(460, 210, 241, 141))
        self.tabWidget.addTab(self.Manual_Inputs, "")
        self.Storage_Dams = QWidget()
        self.Storage_Dams.setObjectName(u"Storage_Dams")
        self.label_14 = QLabel(self.Storage_Dams)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setGeometry(QRect(400, 180, 211, 111))
        self.tabWidget.addTab(self.Storage_Dams, "")
        self.Days_of_operation = QWidget()
        self.Days_of_operation.setObjectName(u"Days_of_operation")
        self.label_15 = QLabel(self.Days_of_operation)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setGeometry(QRect(620, 250, 141, 111))
        self.tabWidget.addTab(self.Days_of_operation, "")
        self.Facility_Flows = QWidget()
        self.Facility_Flows.setObjectName(u"Facility_Flows")
        self.label_16 = QLabel(self.Facility_Flows)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setGeometry(QRect(520, 230, 121, 81))
        self.tabWidget.addTab(self.Facility_Flows, "")

        self.gridLayout.addWidget(self.tabWidget, 2, 0, 1, 1)

        self.header_frame = QFrame(Form)
        self.header_frame.setObjectName(u"header_frame")
        self.header_frame.setMinimumSize(QSize(0, 100))
        self.header_frame.setMaximumSize(QSize(16777215, 100))
        self.header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.header_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.header_frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.header_frame)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(30, 30))
        self.label.setMaximumSize(QSize(30, 30))
        self.label.setPixmap(QPixmap(u":/icons/balance_calculations.svg"))
        self.label.setScaledContents(True)

        self.horizontalLayout.addWidget(self.label)

        self.label_2 = QLabel(self.header_frame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_3 = QLabel(self.header_frame)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)


        self.gridLayout.addWidget(self.header_frame, 0, 0, 1, 1)


        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(7)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_4.setText("")
        self.label_5.setText(QCoreApplication.translate("Form", u"Calculations Parameters", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Calculation Month", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Year:", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("Form", u"2010", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("Form", u"2011", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("Form", u"2012", None))
        self.comboBox.setItemText(3, QCoreApplication.translate("Form", u"2013", None))
        self.comboBox.setItemText(4, QCoreApplication.translate("Form", u"2014", None))
        self.comboBox.setItemText(5, QCoreApplication.translate("Form", u"2015", None))
        self.comboBox.setItemText(6, QCoreApplication.translate("Form", u"2016", None))
        self.comboBox.setItemText(7, QCoreApplication.translate("Form", u"2017", None))
        self.comboBox.setItemText(8, QCoreApplication.translate("Form", u"2018", None))
        self.comboBox.setItemText(9, QCoreApplication.translate("Form", u"2019", None))
        self.comboBox.setItemText(10, QCoreApplication.translate("Form", u"2020", None))
        self.comboBox.setItemText(11, QCoreApplication.translate("Form", u"2021", None))
        self.comboBox.setItemText(12, QCoreApplication.translate("Form", u"2022", None))
        self.comboBox.setItemText(13, QCoreApplication.translate("Form", u"2023", None))
        self.comboBox.setItemText(14, QCoreApplication.translate("Form", u"2024", None))
        self.comboBox.setItemText(15, QCoreApplication.translate("Form", u"2025", None))
        self.comboBox.setItemText(16, QCoreApplication.translate("Form", u"2026", None))

        self.label_8.setText(QCoreApplication.translate("Form", u"Month:", None))
        self.comboBox_2.setItemText(0, QCoreApplication.translate("Form", u"Jan", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("Form", u"Feb", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("Form", u"Mar", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("Form", u"Apr", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("Form", u"May", None))
        self.comboBox_2.setItemText(5, QCoreApplication.translate("Form", u"Jun", None))
        self.comboBox_2.setItemText(6, QCoreApplication.translate("Form", u"Jul", None))
        self.comboBox_2.setItemText(7, QCoreApplication.translate("Form", u"Aug", None))
        self.comboBox_2.setItemText(8, QCoreApplication.translate("Form", u"Sep", None))
        self.comboBox_2.setItemText(9, QCoreApplication.translate("Form", u"Oct", None))
        self.comboBox_2.setItemText(10, QCoreApplication.translate("Form", u"Nov", None))
        self.comboBox_2.setItemText(11, QCoreApplication.translate("Form", u"Dec", None))

        self.pushButton.setText(QCoreApplication.translate("Form", u"Calculation Balance", None))
        self.label_9.setText(QCoreApplication.translate("Form", u"System Balance (Regulator)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.System_Balance_Regulator), QCoreApplication.translate("Form", u"Tab 1", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"Recycled Water", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Recycled_Water), QCoreApplication.translate("Form", u"Page", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"Data Quality", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Data_Quality), QCoreApplication.translate("Form", u"Tab 2", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"Inputs Aduits", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Inputs_Audit), QCoreApplication.translate("Form", u"Page", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"Manual Inputs", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Manual_Inputs), QCoreApplication.translate("Form", u"Page", None))
        self.label_14.setText(QCoreApplication.translate("Form", u"Storage & Dams", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Storage_Dams), QCoreApplication.translate("Form", u"Page", None))
        self.label_15.setText(QCoreApplication.translate("Form", u"Days of Operation", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Days_of_operation), QCoreApplication.translate("Form", u"Page", None))
        self.label_16.setText(QCoreApplication.translate("Form", u"Facility flows", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Facility_Flows), QCoreApplication.translate("Form", u"Page", None))
        self.label.setText("")
        self.label_2.setText(QCoreApplication.translate("Form", u"Water Balance Calculations", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Calculate water balance using TRP formulas", None))
    # retranslateUi



