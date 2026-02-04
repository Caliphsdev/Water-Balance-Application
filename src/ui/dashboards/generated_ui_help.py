# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'help.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1196, 792)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(388, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(40, 40))
        self.label_2.setMaximumSize(QSize(40, 40))
        self.label_2.setMidLineWidth(0)
        self.label_2.setTextFormat(Qt.TextFormat.MarkdownText)
        self.label_2.setPixmap(QPixmap(u":/icons/book.svg"))
        self.label_2.setScaledContents(True)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.label_2, 0, Qt.AlignmentFlag.AlignHCenter)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.label)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalSpacer_2 = QSpacerItem(338, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label_3)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.help_tab = QTabWidget(Form)
        self.help_tab.setObjectName(u"help_tab")
        self.Overview = QWidget()
        self.Overview.setObjectName(u"Overview")
        self.label_4 = QLabel(self.Overview)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(540, 240, 81, 41))
        self.help_tab.addTab(self.Overview, "")
        self.Dashboards = QWidget()
        self.Dashboards.setObjectName(u"Dashboards")
        self.label_5 = QLabel(self.Dashboards)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(260, 200, 111, 51))
        self.help_tab.addTab(self.Dashboards, "")
        self.Calculations = QWidget()
        self.Calculations.setObjectName(u"Calculations")
        self.label_11 = QLabel(self.Calculations)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setGeometry(QRect(338, 185, 121, 111))
        self.help_tab.addTab(self.Calculations, "")
        self.Formulas = QWidget()
        self.Formulas.setObjectName(u"Formulas")
        self.label_10 = QLabel(self.Formulas)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setGeometry(QRect(370, 250, 101, 61))
        self.help_tab.addTab(self.Formulas, "")
        self.WaterSources = QWidget()
        self.WaterSources.setObjectName(u"WaterSources")
        self.label_9 = QLabel(self.WaterSources)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(480, 260, 141, 61))
        self.help_tab.addTab(self.WaterSources, "")
        self.Storage = QWidget()
        self.Storage.setObjectName(u"Storage")
        self.label_8 = QLabel(self.Storage)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(430, 360, 101, 51))
        self.help_tab.addTab(self.Storage, "")
        self.Features = QWidget()
        self.Features.setObjectName(u"Features")
        self.label_7 = QLabel(self.Features)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(540, 280, 101, 61))
        self.help_tab.addTab(self.Features, "")
        self.Troubleshooting = QWidget()
        self.Troubleshooting.setObjectName(u"Troubleshooting")
        self.label_6 = QLabel(self.Troubleshooting)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(570, 240, 151, 51))
        self.help_tab.addTab(self.Troubleshooting, "")

        self.gridLayout.addWidget(self.help_tab, 1, 0, 1, 1)


        self.retranslateUi(Form)

        self.help_tab.setCurrentIndex(7)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Help", None))
        self.label_2.setText("")
        self.label.setText(QCoreApplication.translate("Form", u"Water Balance Application- User Guide & Technical Documentation", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Comprehensive guide to calculations, formulas, and Features", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Overview", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Overview), QCoreApplication.translate("Form", u"Overview", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Dashboards", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Dashboards), QCoreApplication.translate("Form", u"Dashboards", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"Calculations", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Calculations), QCoreApplication.translate("Form", u"Calculations", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"Formulas", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Formulas), QCoreApplication.translate("Form", u"Formulas", None))
        self.label_9.setText(QCoreApplication.translate("Form", u"WaterSources", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.WaterSources), QCoreApplication.translate("Form", u"Water Sources", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"Storage", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Storage), QCoreApplication.translate("Form", u"Storage", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Features", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Features), QCoreApplication.translate("Form", u"Features", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Troubleshooting", None))
        self.help_tab.setTabText(self.help_tab.indexOf(self.Troubleshooting), QCoreApplication.translate("Form", u"Troubleshooting", None))
    # retranslateUi

