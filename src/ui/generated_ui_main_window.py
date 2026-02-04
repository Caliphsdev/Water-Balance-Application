# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 771)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.icon_name = QWidget(self.centralwidget)
        self.icon_name.setObjectName(u"icon_name")
        self.icon_name.setStyleSheet(u"QWidget {\n"
"		background-color: #1E2A38;\n"
"}\n"
"\n"
"QPushButton{\n"
"	color:white;\n"
"	text-align:left;\n"
"	height:30px;\n"
"	border:none;\n"
"	padding-left:5px;\n"
"	border-radius: 10px\n"
"}\n"
"\n"
"QPushButton:checked{\n"
"	background-color: #2980b9;\n"
"	font-weight: bold;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #2980b9;\n"
"    color: white;\n"
"}")
        self.verticalLayout_6 = QVBoxLayout(self.icon_name)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(10, 10, 10, -1)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(15)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 15, 15, -1)
        self.dashboard_2 = QPushButton(self.icon_name)
        self.dashboard_2.setObjectName(u"dashboard_2")
        icon = QIcon()
        icon.addFile(u":/icons/Dashboard_white.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.dashboard_2.setIcon(icon)
        self.dashboard_2.setIconSize(QSize(25, 25))
        self.dashboard_2.setCheckable(True)
        self.dashboard_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.dashboard_2)

        self.analytics_2 = QPushButton(self.icon_name)
        self.analytics_2.setObjectName(u"analytics_2")
        icon1 = QIcon()
        icon1.addFile(u":/icons/Analytics & Trends.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.analytics_2.setIcon(icon1)
        self.analytics_2.setCheckable(True)
        self.analytics_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.analytics_2)

        self.monitoring_data_2 = QPushButton(self.icon_name)
        self.monitoring_data_2.setObjectName(u"monitoring_data_2")
        self.monitoring_data_2.setStyleSheet(u"padding-right:5px\n"
"")
        icon2 = QIcon()
        icon2.addFile(u":/icons/Monitoring Data.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.monitoring_data_2.setIcon(icon2)
        self.monitoring_data_2.setCheckable(True)
        self.monitoring_data_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.monitoring_data_2)

        self.storage_facilites_2 = QPushButton(self.icon_name)
        self.storage_facilites_2.setObjectName(u"storage_facilites_2")
        icon3 = QIcon()
        icon3.addFile(u":/icons/Storage Facilities.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.storage_facilites_2.setIcon(icon3)
        self.storage_facilites_2.setCheckable(True)
        self.storage_facilites_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.storage_facilites_2)

        self.calculations_2 = QPushButton(self.icon_name)
        self.calculations_2.setObjectName(u"calculations_2")
        icon4 = QIcon()
        icon4.addFile(u":/icons/Calculations.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.calculations_2.setIcon(icon4)
        self.calculations_2.setCheckable(True)
        self.calculations_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.calculations_2)

        self.flow_diagram_2 = QPushButton(self.icon_name)
        self.flow_diagram_2.setObjectName(u"flow_diagram_2")
        icon5 = QIcon()
        icon5.addFile(u":/icons/Flow Diagram.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.flow_diagram_2.setIcon(icon5)
        self.flow_diagram_2.setCheckable(True)
        self.flow_diagram_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.flow_diagram_2)

        self.settings_2 = QPushButton(self.icon_name)
        self.settings_2.setObjectName(u"settings_2")
        icon6 = QIcon()
        icon6.addFile(u":/icons/Settings.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.settings_2.setIcon(icon6)
        self.settings_2.setCheckable(True)
        self.settings_2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.settings_2)


        self.verticalLayout_6.addLayout(self.verticalLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 238, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_2)

        self.help_2 = QPushButton(self.icon_name)
        self.help_2.setObjectName(u"help_2")
        icon7 = QIcon()
        icon7.addFile(u":/icons/Help.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.help_2.setIcon(icon7)
        self.help_2.setCheckable(True)
        self.help_2.setAutoExclusive(True)

        self.verticalLayout_6.addWidget(self.help_2)

        self.about_2 = QPushButton(self.icon_name)
        self.about_2.setObjectName(u"about_2")
        icon8 = QIcon()
        icon8.addFile(u":/icons/About.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.about_2.setIcon(icon8)
        self.about_2.setCheckable(True)
        self.about_2.setAutoExclusive(True)

        self.verticalLayout_6.addWidget(self.about_2)

        self.exit_2 = QPushButton(self.icon_name)
        self.exit_2.setObjectName(u"exit_2")
        icon9 = QIcon()
        icon9.addFile(u":/icons/Exit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.exit_2.setIcon(icon9)
        self.exit_2.setCheckable(True)
        self.exit_2.setAutoExclusive(True)

        self.verticalLayout_6.addWidget(self.exit_2)


        self.gridLayout.addWidget(self.icon_name, 1, 1, 1, 1)

        self.main_menu = QWidget(self.centralwidget)
        self.main_menu.setObjectName(u"main_menu")
        self.main_menu.setStyleSheet(u"background-color: #F5F6F7\n"
"")
        self.verticalLayout_5 = QVBoxLayout(self.main_menu)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.Heade_Submain = QWidget(self.main_menu)
        self.Heade_Submain.setObjectName(u"Heade_Submain")
        self.Heade_Submain.setStyleSheet(u"background-color: rgb(245, 246, 247);")
        self.horizontalLayout = QHBoxLayout(self.Heade_Submain)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_4 = QLabel(self.Heade_Submain)
        self.label_4.setObjectName(u"label_4")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label_4.setFont(font)
        self.label_4.setStyleSheet(u"color: rgb(0, 85, 255);")

        self.horizontalLayout.addWidget(self.label_4)

        self.horizontalSpacer = QSpacerItem(684, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.referesh_button = QPushButton(self.Heade_Submain)
        self.referesh_button.setObjectName(u"referesh_button")
        font1 = QFont()
        font1.setBold(True)
        self.referesh_button.setFont(font1)
        self.referesh_button.setStyleSheet(u"background-color:rgb(85, 170, 255);\n"
"color:white;\n"
"")
        icon10 = QIcon()
        icon10.addFile(u":/icons/refresh_icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.referesh_button.setIcon(icon10)

        self.horizontalLayout.addWidget(self.referesh_button)


        self.verticalLayout_5.addWidget(self.Heade_Submain)

        self.stackedWidget = QStackedWidget(self.main_menu)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setStyleSheet(u"background-color:rgb(255, 255, 255);\n"
"")
        self.dashboard = QWidget()
        self.dashboard.setObjectName(u"dashboard")
        self.label = QLabel(self.dashboard)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(460, 170, 241, 61))
        font2 = QFont()
        font2.setPointSize(20)
        font2.setBold(True)
        self.label.setFont(font2)
        self.stackedWidget.addWidget(self.dashboard)
        self.analytics_trends = QWidget()
        self.analytics_trends.setObjectName(u"analytics_trends")
        self.label_5 = QLabel(self.analytics_trends)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(460, 170, 241, 101))
        self.label_5.setFont(font2)
        self.stackedWidget.addWidget(self.analytics_trends)
        self.monitoring_data = QWidget()
        self.monitoring_data.setObjectName(u"monitoring_data")
        self.label_9 = QLabel(self.monitoring_data)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(260, 140, 241, 91))
        self.label_9.setFont(font2)
        self.stackedWidget.addWidget(self.monitoring_data)
        self.storge_facilitites = QWidget()
        self.storge_facilitites.setObjectName(u"storge_facilitites")
        self.label_11 = QLabel(self.storge_facilitites)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(430, 170, 241, 131))
        self.label_11.setFont(font2)
        self.stackedWidget.addWidget(self.storge_facilitites)
        self.calculations = QWidget()
        self.calculations.setObjectName(u"calculations")
        self.label_6 = QLabel(self.calculations)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(360, 180, 211, 161))
        self.label_6.setFont(font2)
        self.stackedWidget.addWidget(self.calculations)
        self.flow_diagram = QWidget()
        self.flow_diagram.setObjectName(u"flow_diagram")
        self.label_7 = QLabel(self.flow_diagram)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(350, 100, 211, 131))
        self.label_7.setFont(font2)
        self.stackedWidget.addWidget(self.flow_diagram)
        self.settings = QWidget()
        self.settings.setObjectName(u"settings")
        self.label_10 = QLabel(self.settings)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(370, 210, 161, 101))
        self.label_10.setFont(font2)
        self.stackedWidget.addWidget(self.settings)
        self.help = QWidget()
        self.help.setObjectName(u"help")
        self.label_8 = QLabel(self.help)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(340, 170, 81, 41))
        self.label_8.setFont(font2)
        self.stackedWidget.addWidget(self.help)
        self.about = QWidget()
        self.about.setObjectName(u"about")
        self.label_3 = QLabel(self.about)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(510, 170, 161, 81))
        self.label_3.setFont(font2)
        self.stackedWidget.addWidget(self.about)

        self.verticalLayout_5.addWidget(self.stackedWidget)


        self.gridLayout.addWidget(self.main_menu, 1, 2, 1, 1)

        self.Header_Main = QWidget(self.centralwidget)
        self.Header_Main.setObjectName(u"Header_Main")
        self.Header_Main.setStyleSheet(u"\n"
"background-color: rgb(13, 71, 161);")
        self.horizontalLayout_2 = QHBoxLayout(self.Header_Main)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_19 = QPushButton(self.Header_Main)
        self.pushButton_19.setObjectName(u"pushButton_19")
        self.pushButton_19.setStyleSheet(u"border:none;")
        icon11 = QIcon()
        icon11.addFile(u":/icons/Burger_icon.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton_19.setIcon(icon11)
        self.pushButton_19.setIconSize(QSize(35, 35))
        self.pushButton_19.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.pushButton_19)

        self.horizontalSpacer_3 = QSpacerItem(479, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.label_2 = QLabel(self.Header_Main)
        self.label_2.setObjectName(u"label_2")
        font3 = QFont()
        font3.setFamilies([u"Segoe UI"])
        font3.setPointSize(16)
        font3.setBold(True)
        self.label_2.setFont(font3)
        self.label_2.setStyleSheet(u"color: rgb(255, 255, 255);")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.horizontalSpacer_2 = QSpacerItem(478, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.notification_container = QWidget(self.Header_Main)
        self.notification_container.setObjectName(u"notification_container")
        self.notification_container.setStyleSheet(u"QToolButton{\n"
"	border:none;\n"
"}\n"
"\n"
"QLabel {\n"
"    background-color: red;\n"
"    color: white;\n"
"    border-radius: 9px;\n"
"    font-size: 10px;\n"
"    font-weight: bold;\n"
"    min-width: 18px;\n"
"    min-height: 18px;\n"
"    max-width: 18px;\n"
"    max-height: 18px;\n"
"    qproperty-alignment: AlignCenter;\n"
"}")
        self.verticalLayout_4 = QVBoxLayout(self.notification_container)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")

        self.horizontalLayout_2.addWidget(self.notification_container)


        self.gridLayout.addWidget(self.Header_Main, 0, 0, 1, 3)

        self.icon_only = QWidget(self.centralwidget)
        self.icon_only.setObjectName(u"icon_only")
        self.icon_only.setStyleSheet(u"QWidget {\n"
"		background-color: #1E2A38;\n"
"}\n"
"\n"
"QPushButton{\n"
"	height:30px;\n"
"	border:none;\n"
"	border-radius:10px;\n"
"}\n"
"\n"
"QPushButton:checked{\n"
"	background-color: #2980b9;\n"
"	font-weight: bold;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #2980b9;\n"
"    color: white;\n"
"}")
        self.verticalLayout_3 = QVBoxLayout(self.icon_only)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(9, 10, 10, -1)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 15, -1, -1)
        self.dashboard_1 = QPushButton(self.icon_only)
        self.dashboard_1.setObjectName(u"dashboard_1")
        self.dashboard_1.setIcon(icon)
        self.dashboard_1.setIconSize(QSize(25, 25))
        self.dashboard_1.setCheckable(True)
        self.dashboard_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.dashboard_1)

        self.analytics_1 = QPushButton(self.icon_only)
        self.analytics_1.setObjectName(u"analytics_1")
        self.analytics_1.setIcon(icon1)
        self.analytics_1.setCheckable(True)
        self.analytics_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.analytics_1)

        self.monitoring_data_1 = QPushButton(self.icon_only)
        self.monitoring_data_1.setObjectName(u"monitoring_data_1")
        self.monitoring_data_1.setIcon(icon2)
        self.monitoring_data_1.setCheckable(True)
        self.monitoring_data_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.monitoring_data_1)

        self.storage_facilities_1 = QPushButton(self.icon_only)
        self.storage_facilities_1.setObjectName(u"storage_facilities_1")
        self.storage_facilities_1.setIcon(icon3)
        self.storage_facilities_1.setCheckable(True)
        self.storage_facilities_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.storage_facilities_1)

        self.calculations_1 = QPushButton(self.icon_only)
        self.calculations_1.setObjectName(u"calculations_1")
        self.calculations_1.setIcon(icon4)
        self.calculations_1.setCheckable(True)
        self.calculations_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.calculations_1)

        self.flow_diagram_1 = QPushButton(self.icon_only)
        self.flow_diagram_1.setObjectName(u"flow_diagram_1")
        self.flow_diagram_1.setIcon(icon5)
        self.flow_diagram_1.setCheckable(True)
        self.flow_diagram_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.flow_diagram_1)

        self.settings_1 = QPushButton(self.icon_only)
        self.settings_1.setObjectName(u"settings_1")
        self.settings_1.setIcon(icon6)
        self.settings_1.setCheckable(True)
        self.settings_1.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.settings_1)


        self.verticalLayout_3.addLayout(self.verticalLayout)

        self.verticalSpacer = QSpacerItem(20, 264, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.help_1 = QPushButton(self.icon_only)
        self.help_1.setObjectName(u"help_1")
        self.help_1.setIcon(icon7)
        self.help_1.setCheckable(True)
        self.help_1.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.help_1)

        self.about_1 = QPushButton(self.icon_only)
        self.about_1.setObjectName(u"about_1")
        self.about_1.setIcon(icon8)
        self.about_1.setCheckable(True)
        self.about_1.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.about_1)

        self.exit_1 = QPushButton(self.icon_only)
        self.exit_1.setObjectName(u"exit_1")
        self.exit_1.setStyleSheet(u"QPushButton:checked{\n"
"	background-color: #2980b9;\n"
"	font-weight: bold;\n"
"}")
        self.exit_1.setIcon(icon9)
        self.exit_1.setCheckable(True)
        self.exit_1.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.exit_1)


        self.gridLayout.addWidget(self.icon_only, 1, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.dashboard_2.toggled.connect(self.dashboard_1.setChecked)
        self.about_2.toggled.connect(self.about_1.setChecked)
        self.monitoring_data_2.toggled.connect(self.monitoring_data_1.setChecked)
        self.analytics_1.toggled.connect(self.analytics_2.setChecked)
        self.storage_facilites_2.toggled.connect(self.storage_facilities_1.setChecked)
        self.settings_2.toggled.connect(self.settings_1.setChecked)
        self.dashboard_1.toggled.connect(self.dashboard_2.setChecked)
        self.help_1.toggled.connect(self.help_2.setChecked)
        self.exit_1.toggled.connect(self.exit_2.setChecked)
        self.help_2.toggled.connect(self.help_1.setChecked)
        self.analytics_2.toggled.connect(self.analytics_1.setChecked)
        self.flow_diagram_1.toggled.connect(self.flow_diagram_2.setChecked)
        self.exit_2.toggled.connect(self.exit_1.setChecked)
        self.settings_1.toggled.connect(self.settings_2.setChecked)
        self.calculations_1.toggled.connect(self.calculations_2.setChecked)
        self.monitoring_data_1.toggled.connect(self.monitoring_data_2.setChecked)
        self.pushButton_19.toggled.connect(self.icon_name.setVisible)
        self.about_1.toggled.connect(self.about_2.setChecked)
        self.storage_facilities_1.toggled.connect(self.storage_facilites_2.setChecked)
        self.pushButton_19.toggled.connect(self.icon_only.setHidden)
        self.flow_diagram_2.toggled.connect(self.flow_diagram_1.setChecked)
        self.calculations_2.toggled.connect(self.calculations_1.setChecked)
        self.exit_1.toggled.connect(MainWindow.close)
        self.exit_2.toggled.connect(MainWindow.close)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Water Balance Dashboard", None))
        self.dashboard_2.setText(QCoreApplication.translate("MainWindow", u"Dashboard", None))
        self.analytics_2.setText(QCoreApplication.translate("MainWindow", u"Analytics & Trends   ", None))
        self.monitoring_data_2.setText(QCoreApplication.translate("MainWindow", u"Monitoring Data  ", None))
        self.storage_facilites_2.setText(QCoreApplication.translate("MainWindow", u"Storage Facilities   ", None))
        self.calculations_2.setText(QCoreApplication.translate("MainWindow", u"Calculations", None))
        self.flow_diagram_2.setText(QCoreApplication.translate("MainWindow", u"Flow Diagram   ", None))
        self.settings_2.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.help_2.setText(QCoreApplication.translate("MainWindow", u"Help", None))
        self.about_2.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.exit_2.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Water Balance Dashboard", None))
        self.referesh_button.setText(QCoreApplication.translate("MainWindow", u"Refresh", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Dashboard Page", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Analytics Trends", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Monitoring Data", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Storage Facilities", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Calculations", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Flow Diagram", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Help", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.pushButton_19.setText("")
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Water Balance System", None))
        self.dashboard_1.setText("")
        self.analytics_1.setText("")
        self.monitoring_data_1.setText("")
        self.storage_facilities_1.setText("")
        self.calculations_1.setText("")
        self.flow_diagram_1.setText("")
        self.settings_1.setText("")
        self.help_1.setText("")
        self.about_1.setText("")
        self.exit_1.setText("")
    # retranslateUi

