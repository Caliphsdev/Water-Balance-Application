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
        MonitoringDataDashboard.setStyleSheet("")
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



