# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1244, 757)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QSize(0, 120))
        self.frame.setMaximumSize(QSize(16777215, 120))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(40, 40))
        self.label_3.setMaximumSize(QSize(40, 40))
        self.label_3.setPixmap(QPixmap(u":/icons/settings_2.svg"))
        self.label_3.setScaledContents(True)

        self.horizontalLayout.addWidget(self.label_3)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.label)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.Settings = QTabWidget(Form)
        self.Settings.setObjectName(u"Settings")
        self.Constants = QWidget()
        self.Constants.setObjectName(u"Constants")
        self.frame_2 = QFrame(self.Constants)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setGeometry(QRect(9, 9, 1144, 50))
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout = QFormLayout(self.frame_2)
        self.formLayout.setObjectName(u"formLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.category_label = QLabel(self.frame_2)
        self.category_label.setObjectName(u"category_label")

        self.horizontalLayout_2.addWidget(self.category_label)

        self.comboBox_filter_constants = QComboBox(self.frame_2)
        self.comboBox_filter_constants.setObjectName(u"comboBox_filter_constants")

        self.horizontalLayout_2.addWidget(self.comboBox_filter_constants)

        self.search_label = QLabel(self.frame_2)
        self.search_label.setObjectName(u"search_label")

        self.horizontalLayout_2.addWidget(self.search_label)

        self.lineEdit_searchbox = QLineEdit(self.frame_2)
        self.lineEdit_searchbox.setObjectName(u"lineEdit_searchbox")

        self.horizontalLayout_2.addWidget(self.lineEdit_searchbox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.export_button = QPushButton(self.frame_2)
        self.export_button.setObjectName(u"export_button")

        self.horizontalLayout_2.addWidget(self.export_button)

        self.history_button = QPushButton(self.frame_2)
        self.history_button.setObjectName(u"history_button")

        self.horizontalLayout_2.addWidget(self.history_button)


        self.formLayout.setLayout(0, QFormLayout.ItemRole.LabelRole, self.horizontalLayout_2)

        self.horizontalSpacer_2 = QSpacerItem(558, 25, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.formLayout.setItem(0, QFormLayout.ItemRole.FieldRole, self.horizontalSpacer_2)

        self.frame_3 = QFrame(self.Constants)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setGeometry(QRect(10, 60, 1141, 481))
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.label_8 = QLabel(self.frame_3)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(20, 20, 101, 16))
        self.tableWidget_constant_table = QTableWidget(self.frame_3)
        if (self.tableWidget_constant_table.columnCount() < 5):
            self.tableWidget_constant_table.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget_constant_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_constant_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_constant_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_constant_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_constant_table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.tableWidget_constant_table.setObjectName(u"tableWidget_constant_table")
        self.tableWidget_constant_table.setGeometry(QRect(10, 40, 1111, 431))
        self.tableWidget_constant_table.horizontalHeader().setCascadingSectionResizes(False)
        self.frame_4 = QFrame(self.Constants)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setGeometry(QRect(10, 550, 1141, 50))
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout_2 = QFormLayout(self.frame_4)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_9 = QLabel(self.frame_4)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_3.addWidget(self.label_9)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)

        self.selected_constant = QLabel(self.frame_4)
        self.selected_constant.setObjectName(u"selected_constant")

        self.horizontalLayout_3.addWidget(self.selected_constant)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)

        self.label_10 = QLabel(self.frame_4)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_3.addWidget(self.label_10)

        self.lineEdit_value = QLineEdit(self.frame_4)
        self.lineEdit_value.setObjectName(u"lineEdit_value")

        self.horizontalLayout_3.addWidget(self.lineEdit_value)

        self.horizontalSpacer_3 = QSpacerItem(28, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.save_button = QPushButton(self.frame_4)
        self.save_button.setObjectName(u"save_button")

        self.horizontalLayout_3.addWidget(self.save_button)

        self.details_button = QPushButton(self.frame_4)
        self.details_button.setObjectName(u"details_button")

        self.horizontalLayout_3.addWidget(self.details_button)

        self.add_button = QPushButton(self.frame_4)
        self.add_button.setObjectName(u"add_button")

        self.horizontalLayout_3.addWidget(self.add_button)

        self.delete_button = QPushButton(self.frame_4)
        self.delete_button.setObjectName(u"delete_button")

        self.horizontalLayout_3.addWidget(self.delete_button)


        self.formLayout_2.setLayout(0, QFormLayout.ItemRole.LabelRole, self.horizontalLayout_3)

        self.horizontalSpacer_4 = QSpacerItem(349, 25, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.formLayout_2.setItem(0, QFormLayout.ItemRole.FieldRole, self.horizontalSpacer_4)

        self.Settings.addTab(self.Constants, "")
        self.Environmental = QWidget()
        self.Environmental.setObjectName(u"Environmental")
        self.verticalLayout_5 = QVBoxLayout(self.Environmental)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_5 = QFrame(self.Environmental)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setMinimumSize(QSize(0, 100))
        self.frame_5.setMaximumSize(QSize(16777215, 120))
        self.frame_5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_32 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_32.setObjectName(u"horizontalLayout_32")
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.horizontalLayout_31 = QHBoxLayout()
        self.horizontalLayout_31.setObjectName(u"horizontalLayout_31")
        self.icon_label_historical_data = QLabel(self.frame_5)
        self.icon_label_historical_data.setObjectName(u"icon_label_historical_data")
        self.icon_label_historical_data.setMinimumSize(QSize(20, 20))
        self.icon_label_historical_data.setMaximumSize(QSize(30, 30))
        self.icon_label_historical_data.setPixmap(QPixmap(u":/icons/archives_history.svg"))
        self.icon_label_historical_data.setScaledContents(True)

        self.horizontalLayout_31.addWidget(self.icon_label_historical_data)

        self.historical_data_label = QLabel(self.frame_5)
        self.historical_data_label.setObjectName(u"historical_data_label")

        self.horizontalLayout_31.addWidget(self.historical_data_label)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_31.addItem(self.horizontalSpacer_15)


        self.verticalLayout_11.addLayout(self.horizontalLayout_31)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.select_year_label = QLabel(self.frame_5)
        self.select_year_label.setObjectName(u"select_year_label")

        self.horizontalLayout_30.addWidget(self.select_year_label)

        self.comboBox_year_filter = QComboBox(self.frame_5)
        self.comboBox_year_filter.setObjectName(u"comboBox_year_filter")

        self.horizontalLayout_30.addWidget(self.comboBox_year_filter)

        self.horizontalSpacer_13 = QSpacerItem(28, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_13)

        self.save_button_environment = QPushButton(self.frame_5)
        self.save_button_environment.setObjectName(u"save_button_environment")

        self.horizontalLayout_30.addWidget(self.save_button_environment)

        self.load_button_environment = QPushButton(self.frame_5)
        self.load_button_environment.setObjectName(u"load_button_environment")

        self.horizontalLayout_30.addWidget(self.load_button_environment)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_16)


        self.verticalLayout_11.addLayout(self.horizontalLayout_30)


        self.horizontalLayout_32.addLayout(self.verticalLayout_11)

        self.horizontalSpacer_14 = QSpacerItem(838, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_32.addItem(self.horizontalSpacer_14)


        self.verticalLayout_5.addWidget(self.frame_5)

        self.frame_6 = QFrame(self.Environmental)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setMinimumSize(QSize(0, 50))
        self.frame_6.setMaximumSize(QSize(16777215, 60))
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout_3 = QFormLayout(self.frame_6)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.rainfall_icon = QLabel(self.frame_6)
        self.rainfall_icon.setObjectName(u"rainfall_icon")
        self.rainfall_icon.setMinimumSize(QSize(20, 20))
        self.rainfall_icon.setMaximumSize(QSize(30, 30))
        self.rainfall_icon.setPixmap(QPixmap(u":/icons/rainfall_2.svg"))
        self.rainfall_icon.setScaledContents(True)

        self.horizontalLayout_34.addWidget(self.rainfall_icon)

        self.rainfall_label = QLabel(self.frame_6)
        self.rainfall_label.setObjectName(u"rainfall_label")

        self.horizontalLayout_34.addWidget(self.rainfall_label)


        self.formLayout_3.setLayout(0, QFormLayout.ItemRole.LabelRole, self.horizontalLayout_34)


        self.verticalLayout_5.addWidget(self.frame_6)

        self.Rainfall = QFrame(self.Environmental)
        self.Rainfall.setObjectName(u"Rainfall")
        self.Rainfall.setFrameShape(QFrame.Shape.StyledPanel)
        self.Rainfall.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_16 = QHBoxLayout(self.Rainfall)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.january_rainfall_label = QLabel(self.Rainfall)
        self.january_rainfall_label.setObjectName(u"january_rainfall_label")

        self.horizontalLayout_4.addWidget(self.january_rainfall_label)

        self.lineEdit_january_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_january_rainfall.setObjectName(u"lineEdit_january_rainfall")

        self.horizontalLayout_4.addWidget(self.lineEdit_january_rainfall)

        self.unit_15 = QLabel(self.Rainfall)
        self.unit_15.setObjectName(u"unit_15")

        self.horizontalLayout_4.addWidget(self.unit_15)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.may_label_rainfall = QLabel(self.Rainfall)
        self.may_label_rainfall.setObjectName(u"may_label_rainfall")

        self.horizontalLayout_8.addWidget(self.may_label_rainfall)

        self.lineEdit_may_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_may_rainfall.setObjectName(u"lineEdit_may_rainfall")

        self.horizontalLayout_8.addWidget(self.lineEdit_may_rainfall)

        self.unit_14 = QLabel(self.Rainfall)
        self.unit_14.setObjectName(u"unit_14")

        self.horizontalLayout_8.addWidget(self.unit_14)


        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_sep_rainfall = QLabel(self.Rainfall)
        self.label_sep_rainfall.setObjectName(u"label_sep_rainfall")

        self.horizontalLayout_12.addWidget(self.label_sep_rainfall)

        self.lineEdit_sep_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_sep_rainfall.setObjectName(u"lineEdit_sep_rainfall")

        self.horizontalLayout_12.addWidget(self.lineEdit_sep_rainfall)

        self.unit_13 = QLabel(self.Rainfall)
        self.unit_13.setObjectName(u"unit_13")

        self.horizontalLayout_12.addWidget(self.unit_13)


        self.verticalLayout_2.addLayout(self.horizontalLayout_12)


        self.horizontalLayout_16.addLayout(self.verticalLayout_2)

        self.horizontalSpacer_7 = QSpacerItem(125, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_7)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.february_rainfall_label = QLabel(self.Rainfall)
        self.february_rainfall_label.setObjectName(u"february_rainfall_label")

        self.horizontalLayout_5.addWidget(self.february_rainfall_label)

        self.lineEdit_february_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_february_rainfall.setObjectName(u"lineEdit_february_rainfall")

        self.horizontalLayout_5.addWidget(self.lineEdit_february_rainfall)

        self.unit_18 = QLabel(self.Rainfall)
        self.unit_18.setObjectName(u"unit_18")

        self.horizontalLayout_5.addWidget(self.unit_18)


        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.jun_rainfall_label = QLabel(self.Rainfall)
        self.jun_rainfall_label.setObjectName(u"jun_rainfall_label")

        self.horizontalLayout_9.addWidget(self.jun_rainfall_label)

        self.lineEdit_jun_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_jun_rainfall.setObjectName(u"lineEdit_jun_rainfall")

        self.horizontalLayout_9.addWidget(self.lineEdit_jun_rainfall)

        self.unit_17 = QLabel(self.Rainfall)
        self.unit_17.setObjectName(u"unit_17")

        self.horizontalLayout_9.addWidget(self.unit_17)


        self.verticalLayout_3.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_oct_rainfall = QLabel(self.Rainfall)
        self.label_oct_rainfall.setObjectName(u"label_oct_rainfall")

        self.horizontalLayout_13.addWidget(self.label_oct_rainfall)

        self.lineEdit_oct_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_oct_rainfall.setObjectName(u"lineEdit_oct_rainfall")

        self.horizontalLayout_13.addWidget(self.lineEdit_oct_rainfall)

        self.unit_16 = QLabel(self.Rainfall)
        self.unit_16.setObjectName(u"unit_16")

        self.horizontalLayout_13.addWidget(self.unit_16)


        self.verticalLayout_3.addLayout(self.horizontalLayout_13)


        self.horizontalLayout_16.addLayout(self.verticalLayout_3)

        self.horizontalSpacer_8 = QSpacerItem(125, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_8)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.march_label_rainfall = QLabel(self.Rainfall)
        self.march_label_rainfall.setObjectName(u"march_label_rainfall")

        self.horizontalLayout_6.addWidget(self.march_label_rainfall)

        self.lineEdit_march_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_march_rainfall.setObjectName(u"lineEdit_march_rainfall")

        self.horizontalLayout_6.addWidget(self.lineEdit_march_rainfall)

        self.unit_21 = QLabel(self.Rainfall)
        self.unit_21.setObjectName(u"unit_21")

        self.horizontalLayout_6.addWidget(self.unit_21)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.july_rainfall_label = QLabel(self.Rainfall)
        self.july_rainfall_label.setObjectName(u"july_rainfall_label")

        self.horizontalLayout_10.addWidget(self.july_rainfall_label)

        self.lineEdit_july_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_july_rainfall.setObjectName(u"lineEdit_july_rainfall")

        self.horizontalLayout_10.addWidget(self.lineEdit_july_rainfall)

        self.unit_20 = QLabel(self.Rainfall)
        self.unit_20.setObjectName(u"unit_20")

        self.horizontalLayout_10.addWidget(self.unit_20)


        self.verticalLayout_4.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_nov_rainfall = QLabel(self.Rainfall)
        self.label_nov_rainfall.setObjectName(u"label_nov_rainfall")

        self.horizontalLayout_14.addWidget(self.label_nov_rainfall)

        self.lineEdit_nov_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_nov_rainfall.setObjectName(u"lineEdit_nov_rainfall")

        self.horizontalLayout_14.addWidget(self.lineEdit_nov_rainfall)

        self.unit_19 = QLabel(self.Rainfall)
        self.unit_19.setObjectName(u"unit_19")

        self.horizontalLayout_14.addWidget(self.unit_19)


        self.verticalLayout_4.addLayout(self.horizontalLayout_14)


        self.horizontalLayout_16.addLayout(self.verticalLayout_4)

        self.horizontalSpacer_9 = QSpacerItem(125, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_9)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.april_rainfall_label = QLabel(self.Rainfall)
        self.april_rainfall_label.setObjectName(u"april_rainfall_label")

        self.horizontalLayout_7.addWidget(self.april_rainfall_label)

        self.lineEdit_april_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_april_rainfall.setObjectName(u"lineEdit_april_rainfall")

        self.horizontalLayout_7.addWidget(self.lineEdit_april_rainfall)

        self.unit_24 = QLabel(self.Rainfall)
        self.unit_24.setObjectName(u"unit_24")

        self.horizontalLayout_7.addWidget(self.unit_24)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_august_label = QLabel(self.Rainfall)
        self.label_august_label.setObjectName(u"label_august_label")

        self.horizontalLayout_11.addWidget(self.label_august_label)

        self.lineEdit_august_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_august_rainfall.setObjectName(u"lineEdit_august_rainfall")

        self.horizontalLayout_11.addWidget(self.lineEdit_august_rainfall)

        self.unit_23 = QLabel(self.Rainfall)
        self.unit_23.setObjectName(u"unit_23")

        self.horizontalLayout_11.addWidget(self.unit_23)


        self.verticalLayout_6.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_dec_rainfall = QLabel(self.Rainfall)
        self.label_dec_rainfall.setObjectName(u"label_dec_rainfall")

        self.horizontalLayout_15.addWidget(self.label_dec_rainfall)

        self.lineEdit_dec_rainfall = QLineEdit(self.Rainfall)
        self.lineEdit_dec_rainfall.setObjectName(u"lineEdit_dec_rainfall")

        self.horizontalLayout_15.addWidget(self.lineEdit_dec_rainfall)

        self.unit_22 = QLabel(self.Rainfall)
        self.unit_22.setObjectName(u"unit_22")

        self.horizontalLayout_15.addWidget(self.unit_22)


        self.verticalLayout_6.addLayout(self.horizontalLayout_15)


        self.horizontalLayout_16.addLayout(self.verticalLayout_6)


        self.verticalLayout_5.addWidget(self.Rainfall)

        self.frame_7 = QFrame(self.Environmental)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setMinimumSize(QSize(0, 30))
        self.frame_7.setMaximumSize(QSize(16777215, 60))
        self.frame_7.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout_4 = QFormLayout(self.frame_7)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.horizontalLayout_35 = QHBoxLayout()
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.label_63 = QLabel(self.frame_7)
        self.label_63.setObjectName(u"label_63")
        self.label_63.setMinimumSize(QSize(20, 20))
        self.label_63.setMaximumSize(QSize(30, 30))
        self.label_63.setPixmap(QPixmap(u":/icons/sunny_2.svg"))
        self.label_63.setScaledContents(True)

        self.horizontalLayout_35.addWidget(self.label_63)

        self.label_64 = QLabel(self.frame_7)
        self.label_64.setObjectName(u"label_64")

        self.horizontalLayout_35.addWidget(self.label_64)


        self.formLayout_4.setLayout(0, QFormLayout.ItemRole.LabelRole, self.horizontalLayout_35)


        self.verticalLayout_5.addWidget(self.frame_7)

        self.Evaporation = QFrame(self.Environmental)
        self.Evaporation.setObjectName(u"Evaporation")
        self.Evaporation.setMinimumSize(QSize(0, 151))
        self.Evaporation.setFrameShape(QFrame.Shape.StyledPanel)
        self.Evaporation.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_33 = QHBoxLayout(self.Evaporation)
        self.horizontalLayout_33.setObjectName(u"horizontalLayout_33")
        self.Rainfall_2 = QFrame(self.Evaporation)
        self.Rainfall_2.setObjectName(u"Rainfall_2")
        self.Rainfall_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.Rainfall_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_17 = QHBoxLayout(self.Rainfall_2)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.label_jan_evaporation = QLabel(self.Rainfall_2)
        self.label_jan_evaporation.setObjectName(u"label_jan_evaporation")

        self.horizontalLayout_18.addWidget(self.label_jan_evaporation)

        self.lineEdit_jan_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_jan_evaporation.setObjectName(u"lineEdit_jan_evaporation")

        self.horizontalLayout_18.addWidget(self.lineEdit_jan_evaporation)

        self.unit_12 = QLabel(self.Rainfall_2)
        self.unit_12.setObjectName(u"unit_12")

        self.horizontalLayout_18.addWidget(self.unit_12)


        self.verticalLayout_7.addLayout(self.horizontalLayout_18)

        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.label_may_evaporation = QLabel(self.Rainfall_2)
        self.label_may_evaporation.setObjectName(u"label_may_evaporation")

        self.horizontalLayout_19.addWidget(self.label_may_evaporation)

        self.lineEdit_may_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_may_evaporation.setObjectName(u"lineEdit_may_evaporation")

        self.horizontalLayout_19.addWidget(self.lineEdit_may_evaporation)

        self.unit = QLabel(self.Rainfall_2)
        self.unit.setObjectName(u"unit")

        self.horizontalLayout_19.addWidget(self.unit)


        self.verticalLayout_7.addLayout(self.horizontalLayout_19)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.label_sep_evaporation = QLabel(self.Rainfall_2)
        self.label_sep_evaporation.setObjectName(u"label_sep_evaporation")

        self.horizontalLayout_20.addWidget(self.label_sep_evaporation)

        self.lineEdit_sep_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_sep_evaporation.setObjectName(u"lineEdit_sep_evaporation")

        self.horizontalLayout_20.addWidget(self.lineEdit_sep_evaporation)

        self.unit_11 = QLabel(self.Rainfall_2)
        self.unit_11.setObjectName(u"unit_11")

        self.horizontalLayout_20.addWidget(self.unit_11)


        self.verticalLayout_7.addLayout(self.horizontalLayout_20)


        self.horizontalLayout_17.addLayout(self.verticalLayout_7)

        self.horizontalSpacer_10 = QSpacerItem(109, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_10)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.feb_evaporation_label = QLabel(self.Rainfall_2)
        self.feb_evaporation_label.setObjectName(u"feb_evaporation_label")

        self.horizontalLayout_21.addWidget(self.feb_evaporation_label)

        self.lineEdit_feb_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_feb_evaporation.setObjectName(u"lineEdit_feb_evaporation")

        self.horizontalLayout_21.addWidget(self.lineEdit_feb_evaporation)

        self.unit_10 = QLabel(self.Rainfall_2)
        self.unit_10.setObjectName(u"unit_10")

        self.horizontalLayout_21.addWidget(self.unit_10)


        self.verticalLayout_8.addLayout(self.horizontalLayout_21)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.label_jun_evaporation = QLabel(self.Rainfall_2)
        self.label_jun_evaporation.setObjectName(u"label_jun_evaporation")

        self.horizontalLayout_22.addWidget(self.label_jun_evaporation)

        self.lineEdit_jun_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_jun_evaporation.setObjectName(u"lineEdit_jun_evaporation")

        self.horizontalLayout_22.addWidget(self.lineEdit_jun_evaporation)

        self.unit_9 = QLabel(self.Rainfall_2)
        self.unit_9.setObjectName(u"unit_9")

        self.horizontalLayout_22.addWidget(self.unit_9)


        self.verticalLayout_8.addLayout(self.horizontalLayout_22)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.label_oct_evaporation = QLabel(self.Rainfall_2)
        self.label_oct_evaporation.setObjectName(u"label_oct_evaporation")

        self.horizontalLayout_23.addWidget(self.label_oct_evaporation)

        self.lineEdit_oct_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_oct_evaporation.setObjectName(u"lineEdit_oct_evaporation")

        self.horizontalLayout_23.addWidget(self.lineEdit_oct_evaporation)

        self.unit_8 = QLabel(self.Rainfall_2)
        self.unit_8.setObjectName(u"unit_8")

        self.horizontalLayout_23.addWidget(self.unit_8)


        self.verticalLayout_8.addLayout(self.horizontalLayout_23)


        self.horizontalLayout_17.addLayout(self.verticalLayout_8)

        self.horizontalSpacer_11 = QSpacerItem(109, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_11)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.march_evaporation_label = QLabel(self.Rainfall_2)
        self.march_evaporation_label.setObjectName(u"march_evaporation_label")

        self.horizontalLayout_24.addWidget(self.march_evaporation_label)

        self.lineEdit_march_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_march_evaporation.setObjectName(u"lineEdit_march_evaporation")

        self.horizontalLayout_24.addWidget(self.lineEdit_march_evaporation)

        self.unit_7 = QLabel(self.Rainfall_2)
        self.unit_7.setObjectName(u"unit_7")

        self.horizontalLayout_24.addWidget(self.unit_7)


        self.verticalLayout_9.addLayout(self.horizontalLayout_24)

        self.horizontalLayout_25 = QHBoxLayout()
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.label_jul_evaporation = QLabel(self.Rainfall_2)
        self.label_jul_evaporation.setObjectName(u"label_jul_evaporation")

        self.horizontalLayout_25.addWidget(self.label_jul_evaporation)

        self.lineEdit_jul_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_jul_evaporation.setObjectName(u"lineEdit_jul_evaporation")

        self.horizontalLayout_25.addWidget(self.lineEdit_jul_evaporation)

        self.unit_6 = QLabel(self.Rainfall_2)
        self.unit_6.setObjectName(u"unit_6")

        self.horizontalLayout_25.addWidget(self.unit_6)


        self.verticalLayout_9.addLayout(self.horizontalLayout_25)

        self.horizontalLayout_26 = QHBoxLayout()
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.label_nov_evaporation = QLabel(self.Rainfall_2)
        self.label_nov_evaporation.setObjectName(u"label_nov_evaporation")

        self.horizontalLayout_26.addWidget(self.label_nov_evaporation)

        self.lineEdit_nov_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_nov_evaporation.setObjectName(u"lineEdit_nov_evaporation")

        self.horizontalLayout_26.addWidget(self.lineEdit_nov_evaporation)

        self.unit_5 = QLabel(self.Rainfall_2)
        self.unit_5.setObjectName(u"unit_5")

        self.horizontalLayout_26.addWidget(self.unit_5)


        self.verticalLayout_9.addLayout(self.horizontalLayout_26)


        self.horizontalLayout_17.addLayout(self.verticalLayout_9)

        self.horizontalSpacer_12 = QSpacerItem(109, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_12)

        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.label_apri_evaporation = QLabel(self.Rainfall_2)
        self.label_apri_evaporation.setObjectName(u"label_apri_evaporation")

        self.horizontalLayout_27.addWidget(self.label_apri_evaporation)

        self.lineEdit_april_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_april_evaporation.setObjectName(u"lineEdit_april_evaporation")

        self.horizontalLayout_27.addWidget(self.lineEdit_april_evaporation)

        self.unit_4 = QLabel(self.Rainfall_2)
        self.unit_4.setObjectName(u"unit_4")

        self.horizontalLayout_27.addWidget(self.unit_4)


        self.verticalLayout_10.addLayout(self.horizontalLayout_27)

        self.horizontalLayout_28 = QHBoxLayout()
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.label_augevaporation = QLabel(self.Rainfall_2)
        self.label_augevaporation.setObjectName(u"label_augevaporation")

        self.horizontalLayout_28.addWidget(self.label_augevaporation)

        self.lineEdit_augevaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_augevaporation.setObjectName(u"lineEdit_augevaporation")

        self.horizontalLayout_28.addWidget(self.lineEdit_augevaporation)

        self.unit_3 = QLabel(self.Rainfall_2)
        self.unit_3.setObjectName(u"unit_3")

        self.horizontalLayout_28.addWidget(self.unit_3)


        self.verticalLayout_10.addLayout(self.horizontalLayout_28)

        self.horizontalLayout_29 = QHBoxLayout()
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.label_dec_evaporation = QLabel(self.Rainfall_2)
        self.label_dec_evaporation.setObjectName(u"label_dec_evaporation")

        self.horizontalLayout_29.addWidget(self.label_dec_evaporation)

        self.lineEdit_dec_evaporation = QLineEdit(self.Rainfall_2)
        self.lineEdit_dec_evaporation.setObjectName(u"lineEdit_dec_evaporation")

        self.horizontalLayout_29.addWidget(self.lineEdit_dec_evaporation)

        self.unit_2 = QLabel(self.Rainfall_2)
        self.unit_2.setObjectName(u"unit_2")

        self.horizontalLayout_29.addWidget(self.unit_2)


        self.verticalLayout_10.addLayout(self.horizontalLayout_29)


        self.horizontalLayout_17.addLayout(self.verticalLayout_10)


        self.horizontalLayout_33.addWidget(self.Rainfall_2)


        self.verticalLayout_5.addWidget(self.Evaporation)

        self.Settings.addTab(self.Environmental, "")

        self.gridLayout.addWidget(self.Settings, 1, 0, 1, 1)


        self.retranslateUi(Form)

        self.Settings.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Settings", None))
        self.label_3.setText("")
        self.label.setText(QCoreApplication.translate("Form", u"Settings & Configuration", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Manage Application settings, constants, backups, and system configuration", None))
        self.category_label.setText(QCoreApplication.translate("Form", u"Category:", None))
        self.search_label.setText(QCoreApplication.translate("Form", u"Search:", None))
        self.export_button.setText(QCoreApplication.translate("Form", u"Export", None))
        self.history_button.setText(QCoreApplication.translate("Form", u"History", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"System Constants", None))
        ___qtablewidgetitem = self.tableWidget_constant_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Form", u"Category", None));
        ___qtablewidgetitem1 = self.tableWidget_constant_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Form", u"Constant key", None));
        ___qtablewidgetitem2 = self.tableWidget_constant_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("Form", u"Value", None));
        ___qtablewidgetitem3 = self.tableWidget_constant_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("Form", u"Unit", None));
        ___qtablewidgetitem4 = self.tableWidget_constant_table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("Form", u"Used In/ Formula", None));
        self.label_9.setText(QCoreApplication.translate("Form", u"Quick Edit:", None))
        self.selected_constant.setText(QCoreApplication.translate("Form", u"constant", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"value:", None))
        self.save_button.setText(QCoreApplication.translate("Form", u"Save", None))
        self.details_button.setText(QCoreApplication.translate("Form", u"Details", None))
        self.add_button.setText(QCoreApplication.translate("Form", u"Add", None))
        self.delete_button.setText(QCoreApplication.translate("Form", u"Delete", None))
        self.Settings.setTabText(self.Settings.indexOf(self.Constants), QCoreApplication.translate("Form", u"Constants", None))
        self.icon_label_historical_data.setText("")
        self.historical_data_label.setText(QCoreApplication.translate("Form", u"Historical Data", None))
        self.select_year_label.setText(QCoreApplication.translate("Form", u"Select Year:", None))
        self.save_button_environment.setText(QCoreApplication.translate("Form", u"Save", None))
        self.load_button_environment.setText(QCoreApplication.translate("Form", u"Load", None))
        self.rainfall_icon.setText("")
        self.rainfall_label.setText(QCoreApplication.translate("Form", u"Regional Rainfall (mm/month)", None))
        self.january_rainfall_label.setText(QCoreApplication.translate("Form", u"Jan: ", None))
        self.unit_15.setText(QCoreApplication.translate("Form", u"mm", None))
        self.may_label_rainfall.setText(QCoreApplication.translate("Form", u"May:", None))
        self.unit_14.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_sep_rainfall.setText(QCoreApplication.translate("Form", u"Sep:", None))
        self.unit_13.setText(QCoreApplication.translate("Form", u"mm", None))
        self.february_rainfall_label.setText(QCoreApplication.translate("Form", u"Feb", None))
        self.unit_18.setText(QCoreApplication.translate("Form", u"mm", None))
        self.jun_rainfall_label.setText(QCoreApplication.translate("Form", u"Jun:", None))
        self.unit_17.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_oct_rainfall.setText(QCoreApplication.translate("Form", u"Oct:", None))
        self.unit_16.setText(QCoreApplication.translate("Form", u"mm", None))
        self.march_label_rainfall.setText(QCoreApplication.translate("Form", u"Mar", None))
        self.unit_21.setText(QCoreApplication.translate("Form", u"mm", None))
        self.july_rainfall_label.setText(QCoreApplication.translate("Form", u"Jul:", None))
        self.unit_20.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_nov_rainfall.setText(QCoreApplication.translate("Form", u"Nov:", None))
        self.unit_19.setText(QCoreApplication.translate("Form", u"mm", None))
        self.april_rainfall_label.setText(QCoreApplication.translate("Form", u"Apr", None))
        self.unit_24.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_august_label.setText(QCoreApplication.translate("Form", u"Aug:", None))
        self.unit_23.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_dec_rainfall.setText(QCoreApplication.translate("Form", u"Dec:", None))
        self.unit_22.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_63.setText("")
        self.label_64.setText(QCoreApplication.translate("Form", u"Regional Evaporation  (mm/month)", None))
        self.label_jan_evaporation.setText(QCoreApplication.translate("Form", u"Jan: ", None))
        self.unit_12.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_may_evaporation.setText(QCoreApplication.translate("Form", u"May:", None))
        self.unit.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_sep_evaporation.setText(QCoreApplication.translate("Form", u"Sep:", None))
        self.unit_11.setText(QCoreApplication.translate("Form", u"mm", None))
        self.feb_evaporation_label.setText(QCoreApplication.translate("Form", u"Feb", None))
        self.unit_10.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_jun_evaporation.setText(QCoreApplication.translate("Form", u"Jun:", None))
        self.unit_9.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_oct_evaporation.setText(QCoreApplication.translate("Form", u"Oct:", None))
        self.unit_8.setText(QCoreApplication.translate("Form", u"mm", None))
        self.march_evaporation_label.setText(QCoreApplication.translate("Form", u"Mar", None))
        self.unit_7.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_jul_evaporation.setText(QCoreApplication.translate("Form", u"Jul:", None))
        self.unit_6.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_nov_evaporation.setText(QCoreApplication.translate("Form", u"Nov:", None))
        self.unit_5.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_apri_evaporation.setText(QCoreApplication.translate("Form", u"Apr", None))
        self.unit_4.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_augevaporation.setText(QCoreApplication.translate("Form", u"Aug:", None))
        self.unit_3.setText(QCoreApplication.translate("Form", u"mm", None))
        self.label_dec_evaporation.setText(QCoreApplication.translate("Form", u"Dec:", None))
        self.unit_2.setText(QCoreApplication.translate("Form", u"mm", None))
        self.Settings.setTabText(self.Settings.indexOf(self.Environmental), QCoreApplication.translate("Form", u"Environmental", None))
    # retranslateUi



