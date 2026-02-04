# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monitoring_data_dashboard.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_MonitoringDataDashboard(object):
    def setupUi(self, MonitoringDataDashboard):
        if not MonitoringDataDashboard.objectName():
            MonitoringDataDashboard.setObjectName(u"MonitoringDataDashboard")
        MonitoringDataDashboard.resize(1200, 800)
        MonitoringDataDashboard.setStyleSheet(u"\n"
"QWidget {\n"
"    background-color: #F5F6F7;\n"
"}\n"
"\n"
"QTabWidget::pane {\n"
"    border: 1px solid #E0E0E0;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background-color: #E8E8E8;\n"
"    color: #333;\n"
"    padding: 5px 20px;\n"
"    border: 1px solid #D0D0D0;\n"
"    border-bottom: none;\n"
"    margin-right: 2px;\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    background-color: white;\n"
"    color: #0D47A1;\n"
"    border-bottom: 2px solid #0D47A1;\n"
"}\n"
"\n"
"QTabBar::tab:hover {\n"
"    background-color: #F0F0F0;\n"
"}\n"
"\n"
"QPushButton {\n"
"    background-color: #0D47A1;\n"
"    color: white;\n"
"    border: none;\n"
"    border-radius: 4px;\n"
"    padding: 6px 12px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #0052A3;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #003D82;\n"
"}\n"
"\n"
"QPushButton:disabled {\n"
"    background-color: #CCCCCC;\n"
"    color: #666666;\n"
"}\n"
"\n"
"QLabel {\n"
"    color: #333333;\n"
"}\n"
"\n"
"Q"
                        "LineEdit, QTextEdit {\n"
"    background-color: white;\n"
"    border: 1px solid #D0D0D0;\n"
"    border-radius: 3px;\n"
"    padding: 4px;\n"
"    color: #333333;\n"
"}\n"
"\n"
"QLineEdit:focus, QTextEdit:focus {\n"
"    border: 2px solid #0D47A1;\n"
"}\n"
"\n"
"QTreeWidget, QTableWidget {\n"
"    background-color: white;\n"
"    alternate-background-color: #F9F9F9;\n"
"    gridline-color: #E0E0E0;\n"
"    border: 1px solid #D0D0D0;\n"
"}\n"
"\n"
"QTreeWidget::item:selected, QTableWidget::item:selected {\n"
"    background-color: #BBD7FF;\n"
"}\n"
"\n"
"QGroupBox {\n"
"    border: 1px solid #D0D0D0;\n"
"    border-radius: 4px;\n"
"    margin-top: 10px;\n"
"    padding-top: 10px;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    left: 10px;\n"
"    padding: 0 3px 0 3px;\n"
"    color: #333333;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QProgressBar {\n"
"    border: 1px solid #D0D0D0;\n"
"    border-radius: 3px;\n"
"    text-align: center;\n"
"    background-color: #F5F6F7;\n"
"}\n"
""
                        "\n"
"QProgressBar::chunk {\n"
"    background-color: #0D47A1;\n"
"    border-radius: 2px;\n"
"}\n"
"   ")
        self.verticalLayout_main = QVBoxLayout(MonitoringDataDashboard)
        self.verticalLayout_main.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.tabWidget = QTabWidget(MonitoringDataDashboard)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_placeholder = QWidget()
        self.tab_placeholder.setObjectName(u"tab_placeholder")
        self.verticalLayout = QVBoxLayout(self.tab_placeholder)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_loading = QLabel(self.tab_placeholder)
        self.label_loading.setObjectName(u"label_loading")
        self.label_loading.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_loading)

        self.tabWidget.addTab(self.tab_placeholder, "")

        self.verticalLayout_main.addWidget(self.tabWidget)


        self.retranslateUi(MonitoringDataDashboard)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MonitoringDataDashboard)
    # setupUi

    def retranslateUi(self, MonitoringDataDashboard):
        MonitoringDataDashboard.setWindowTitle(QCoreApplication.translate("MonitoringDataDashboard", u"Monitoring Data Dashboard", None))
        self.label_loading.setText(QCoreApplication.translate("MonitoringDataDashboard", u"Loading monitoring data sources...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_placeholder), QCoreApplication.translate("MonitoringDataDashboard", u"Loading...", None))
    # retranslateUi

