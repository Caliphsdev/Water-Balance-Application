# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1400, 900)  # Initial size, but window is resizable
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 10, 10, 10)
        self.verticalLayout.setSpacing(18)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(15)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.card_water_sources = QFrame(Form)
        self.card_water_sources.setObjectName(u"card_water_sources")
        self.card_water_sources.setMinimumSize(QSize(180, 180))
        self.card_water_sources.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_water_sources.setStyleSheet("")
        self.card_water_sources.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_water_sources.setFrameShadow(QFrame.Shadow.Raised)
        self.widget = QWidget(self.card_water_sources)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 5, 0, 0)
        self.icon_water_sources = QLabel(self.widget)
        self.icon_water_sources.setObjectName(u"icon_water_sources")
        self.icon_water_sources.setMinimumSize(QSize(40, 40))
        self.icon_water_sources.setMaximumSize(QSize(40, 40))
        self.icon_water_sources.setPixmap(QPixmap(u":/icons/water_source.svg"))
        self.icon_water_sources.setScaledContents(True)
        self.icon_water_sources.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.icon_water_sources, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_water_sources = QLabel(self.widget)
        self.value_water_sources.setObjectName(u"value_water_sources")
        self.value_water_sources.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.value_water_sources)

        self.unit_water_sources = QLabel(self.widget)
        self.unit_water_sources.setObjectName(u"unit_water_sources")
        self.unit_water_sources.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.unit_water_sources)

        self.title_water_sources = QLabel(self.widget)
        self.title_water_sources.setObjectName(u"title_water_sources")
        self.title_water_sources.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.title_water_sources)


        self.horizontalLayout.addWidget(self.card_water_sources)

        self.card_storage_facilities = QFrame(Form)
        self.card_storage_facilities.setObjectName(u"card_storage_facilities")
        self.card_storage_facilities.setMinimumSize(QSize(180, 180))
        self.card_storage_facilities.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_storage_facilities.setStyleSheet("")
        self.card_storage_facilities.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_storage_facilities.setFrameShadow(QFrame.Shadow.Raised)
        self.widget1 = QWidget(self.card_storage_facilities)
        self.widget1.setObjectName(u"widget1")
        self.widget1.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_3 = QVBoxLayout(self.widget1)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 5, 0, 0)
        self.icon_storage_facilities = QLabel(self.widget1)
        self.icon_storage_facilities.setObjectName(u"icon_storage_facilities")
        self.icon_storage_facilities.setMinimumSize(QSize(40, 40))
        self.icon_storage_facilities.setMaximumSize(QSize(40, 40))
        self.icon_storage_facilities.setPixmap(QPixmap(u":/icons/Storage Facilities_dashboard.svg"))
        self.icon_storage_facilities.setScaledContents(True)
        self.icon_storage_facilities.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.icon_storage_facilities, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_storage_facilities = QLabel(self.widget1)
        self.value_storage_facilities.setObjectName(u"value_storage_facilities")
        self.value_storage_facilities.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.value_storage_facilities)

        self.unit_storage_facilities = QLabel(self.widget1)
        self.unit_storage_facilities.setObjectName(u"unit_storage_facilities")
        self.unit_storage_facilities.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.unit_storage_facilities)

        self.title_storage_facilities = QLabel(self.widget1)
        self.title_storage_facilities.setObjectName(u"title_storage_facilities")
        self.title_storage_facilities.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.title_storage_facilities)


        self.horizontalLayout.addWidget(self.card_storage_facilities)

        self.card_total_capacity = QFrame(Form)
        self.card_total_capacity.setObjectName(u"card_total_capacity")
        self.card_total_capacity.setMinimumSize(QSize(180, 180))
        self.card_total_capacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_total_capacity.setStyleSheet("")
        self.card_total_capacity.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_total_capacity.setFrameShadow(QFrame.Shadow.Raised)
        self.widget2 = QWidget(self.card_total_capacity)
        self.widget2.setObjectName(u"widget2")
        self.widget2.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_4 = QVBoxLayout(self.widget2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 5, 0, 0)
        self.icon_total_capacity = QLabel(self.widget2)
        self.icon_total_capacity.setObjectName(u"icon_total_capacity")
        self.icon_total_capacity.setMinimumSize(QSize(40, 40))
        self.icon_total_capacity.setMaximumSize(QSize(40, 40))
        self.icon_total_capacity.setPixmap(QPixmap(u":/icons/total_capacity.svg"))
        self.icon_total_capacity.setScaledContents(True)
        self.icon_total_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.icon_total_capacity, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_total_capacity = QLabel(self.widget2)
        self.value_total_capacity.setObjectName(u"value_total_capacity")
        self.value_total_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.value_total_capacity)

        self.unit_total_capacity = QLabel(self.widget2)
        self.unit_total_capacity.setObjectName(u"unit_total_capacity")
        self.unit_total_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.unit_total_capacity)

        self.title_total_capacity = QLabel(self.widget2)
        self.title_total_capacity.setObjectName(u"title_total_capacity")
        self.title_total_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.title_total_capacity)


        self.horizontalLayout.addWidget(self.card_total_capacity)

        self.card_current_volume = QFrame(Form)
        self.card_current_volume.setObjectName(u"card_current_volume")
        self.card_current_volume.setMinimumSize(QSize(180, 180))
        self.card_current_volume.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_current_volume.setStyleSheet("")
        self.card_current_volume.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_current_volume.setFrameShadow(QFrame.Shadow.Raised)
        self.widget3 = QWidget(self.card_current_volume)
        self.widget3.setObjectName(u"widget3")
        self.widget3.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_5 = QVBoxLayout(self.widget3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 5, 0, 0)
        self.icon_current_volume = QLabel(self.widget3)
        self.icon_current_volume.setObjectName(u"icon_current_volume")
        self.icon_current_volume.setMinimumSize(QSize(40, 40))
        self.icon_current_volume.setMaximumSize(QSize(40, 40))
        self.icon_current_volume.setPixmap(QPixmap(u":/icons/current_storage.svg"))
        self.icon_current_volume.setScaledContents(True)
        self.icon_current_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.icon_current_volume, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_current_volume = QLabel(self.widget3)
        self.value_current_volume.setObjectName(u"value_current_volume")
        self.value_current_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.value_current_volume)

        self.unit_current_volume = QLabel(self.widget3)
        self.unit_current_volume.setObjectName(u"unit_current_volume")
        self.unit_current_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.unit_current_volume)

        self.title_current_volume = QLabel(self.widget3)
        self.title_current_volume.setObjectName(u"title_current_volume")
        self.title_current_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.title_current_volume)


        self.horizontalLayout.addWidget(self.card_current_volume)

        self.card_utilization = QFrame(Form)
        self.card_utilization.setObjectName(u"card_utilization")
        self.card_utilization.setMinimumSize(QSize(180, 180))
        self.card_utilization.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_utilization.setStyleSheet("")
        self.card_utilization.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_utilization.setFrameShadow(QFrame.Shadow.Raised)
        self.widget4 = QWidget(self.card_utilization)
        self.widget4.setObjectName(u"widget4")
        self.widget4.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_6 = QVBoxLayout(self.widget4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 5, 0, 0)
        self.icon_utilization = QLabel(self.widget4)
        self.icon_utilization.setObjectName(u"icon_utilization")
        self.icon_utilization.setMinimumSize(QSize(40, 40))
        self.icon_utilization.setMaximumSize(QSize(40, 40))
        self.icon_utilization.setPixmap(QPixmap(u":/icons/utilization.svg"))
        self.icon_utilization.setScaledContents(True)
        self.icon_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_6.addWidget(self.icon_utilization, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_utilization = QLabel(self.widget4)
        self.value_utilization.setObjectName(u"value_utilization")
        self.value_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_6.addWidget(self.value_utilization)

        self.unit_utilization = QLabel(self.widget4)
        self.unit_utilization.setObjectName(u"unit_utilization")
        self.unit_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_6.addWidget(self.unit_utilization)

        self.title_utilization = QLabel(self.widget4)
        self.title_utilization.setObjectName(u"title_utilization")
        self.title_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_6.addWidget(self.title_utilization)


        self.horizontalLayout.addWidget(self.card_utilization)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.label_environmental_kpis = QLabel(Form)
        self.label_environmental_kpis.setObjectName(u"label_environmental_kpis")
        self.label_environmental_kpis.setStyleSheet("")

        self.verticalLayout.addWidget(self.label_environmental_kpis)

        self.layout_environmental_row = QHBoxLayout()
        self.layout_environmental_row.setSpacing(20)
        self.layout_environmental_row.setObjectName(u"layout_environmental_row")
        self.card_evapouration = QFrame(Form)
        self.card_evapouration.setObjectName(u"card_evapouration")
        self.card_evapouration.setMinimumSize(QSize(280, 180))
        self.card_evapouration.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_evapouration.setStyleSheet("")
        self.card_evapouration.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_evapouration.setFrameShadow(QFrame.Shadow.Raised)
        self.widget5 = QWidget(self.card_evapouration)
        self.widget5.setObjectName(u"widget5")
        self.widget5.setGeometry(QRect(10, 10, 531, 161))
        self.verticalLayout_7 = QVBoxLayout(self.widget5)
        self.verticalLayout_7.setSpacing(5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.icon_rainfall = QLabel(self.widget5)
        self.icon_rainfall.setObjectName(u"icon_rainfall")
        self.icon_rainfall.setMinimumSize(QSize(50, 50))
        self.icon_rainfall.setMaximumSize(QSize(50, 50))
        self.icon_rainfall.setPixmap(QPixmap(u":/icons/Rainfall.svg"))
        self.icon_rainfall.setScaledContents(True)
        self.icon_rainfall.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.icon_rainfall, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_rainfall = QLabel(self.widget5)
        self.value_rainfall.setObjectName(u"value_rainfall")
        self.value_rainfall.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.value_rainfall)

        self.unit_rainfall = QLabel(self.widget5)
        self.unit_rainfall.setObjectName(u"unit_rainfall")
        self.unit_rainfall.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.unit_rainfall)

        self.title_rainfall = QLabel(self.widget5)
        self.title_rainfall.setObjectName(u"title_rainfall")
        self.title_rainfall.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_7.addWidget(self.title_rainfall)


        self.layout_environmental_row.addWidget(self.card_evapouration, 1)

        self.card_rainfall = QFrame(Form)
        self.card_rainfall.setObjectName(u"card_rainfall")
        self.card_rainfall.setMinimumSize(QSize(280, 180))
        self.card_rainfall.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_rainfall.setStyleSheet("")
        self.card_rainfall.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_rainfall.setFrameShadow(QFrame.Shadow.Raised)
        self.widget6 = QWidget(self.card_rainfall)
        self.widget6.setObjectName(u"widget6")
        self.widget6.setGeometry(QRect(10, 10, 531, 161))
        self.verticalLayout_8 = QVBoxLayout(self.widget6)
        self.verticalLayout_8.setSpacing(6)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 5, 0, 0)
        self.icon_evaporation = QLabel(self.widget6)
        self.icon_evaporation.setObjectName(u"icon_evaporation")
        self.icon_evaporation.setMinimumSize(QSize(50, 50))
        self.icon_evaporation.setMaximumSize(QSize(50, 50))
        self.icon_evaporation.setPixmap(QPixmap(u":/icons/Sunny.svg"))
        self.icon_evaporation.setScaledContents(True)
        self.icon_evaporation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_8.addWidget(self.icon_evaporation, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_evaporation = QLabel(self.widget6)
        self.value_evaporation.setObjectName(u"value_evaporation")
        self.value_evaporation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_8.addWidget(self.value_evaporation)

        self.unit_evaporation = QLabel(self.widget6)
        self.unit_evaporation.setObjectName(u"unit_evaporation")
        self.unit_evaporation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_8.addWidget(self.unit_evaporation)

        self.title_evaporation = QLabel(self.widget6)
        self.title_evaporation.setObjectName(u"title_evaporation")
        self.title_evaporation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_8.addWidget(self.title_evaporation)


        self.layout_environmental_row.addWidget(self.card_rainfall, 1)


        self.verticalLayout.addLayout(self.layout_environmental_row)

        self.label_balance_status = QLabel(Form)
        self.label_balance_status.setObjectName(u"label_balance_status")
        self.label_balance_status.setStyleSheet("")

        self.verticalLayout.addWidget(self.label_balance_status)

        self.layout_balance_row = QHBoxLayout()
        self.layout_balance_row.setSpacing(15)
        self.layout_balance_row.setObjectName(u"layout_balance_row")
        self.card_total_inflows = QFrame(Form)
        self.card_total_inflows.setObjectName(u"card_total_inflows")
        self.card_total_inflows.setMinimumSize(QSize(180, 180))
        self.card_total_inflows.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_total_inflows.setStyleSheet("")
        self.card_total_inflows.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_total_inflows.setFrameShadow(QFrame.Shadow.Raised)
        self.widget7 = QWidget(self.card_total_inflows)
        self.widget7.setObjectName(u"widget7")
        self.widget7.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_9 = QVBoxLayout(self.widget7)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 5, 0, 0)
        self.icon_total_inflows = QLabel(self.widget7)
        self.icon_total_inflows.setObjectName(u"icon_total_inflows")
        self.icon_total_inflows.setMinimumSize(QSize(30, 30))
        self.icon_total_inflows.setMaximumSize(QSize(30, 30))
        self.icon_total_inflows.setPixmap(QPixmap(u":/icons/water_drop.svg"))
        self.icon_total_inflows.setScaledContents(True)
        self.icon_total_inflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_9.addWidget(self.icon_total_inflows, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_total_inflows = QLabel(self.widget7)
        self.value_total_inflows.setObjectName(u"value_total_inflows")
        self.value_total_inflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_9.addWidget(self.value_total_inflows)

        self.unit_total_inflows = QLabel(self.widget7)
        self.unit_total_inflows.setObjectName(u"unit_total_inflows")
        self.unit_total_inflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_9.addWidget(self.unit_total_inflows)

        self.title_total_inflows = QLabel(self.widget7)
        self.title_total_inflows.setObjectName(u"title_total_inflows")
        self.title_total_inflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_9.addWidget(self.title_total_inflows)


        self.layout_balance_row.addWidget(self.card_total_inflows)

        self.card_total_outflows = QFrame(Form)
        self.card_total_outflows.setObjectName(u"card_total_outflows")
        self.card_total_outflows.setMinimumSize(QSize(180, 180))
        self.card_total_outflows.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_total_outflows.setStyleSheet("")
        self.card_total_outflows.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_total_outflows.setFrameShadow(QFrame.Shadow.Raised)
        self.widget8 = QWidget(self.card_total_outflows)
        self.widget8.setObjectName(u"widget8")
        self.widget8.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_10 = QVBoxLayout(self.widget8)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 5, 0, 0)
        self.icon_total_outflows = QLabel(self.widget8)
        self.icon_total_outflows.setObjectName(u"icon_total_outflows")
        self.icon_total_outflows.setMinimumSize(QSize(30, 30))
        self.icon_total_outflows.setMaximumSize(QSize(30, 30))
        self.icon_total_outflows.setPixmap(QPixmap(u":/icons/water_drop_red.svg"))
        self.icon_total_outflows.setScaledContents(True)
        self.icon_total_outflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_10.addWidget(self.icon_total_outflows, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_total_outflows = QLabel(self.widget8)
        self.value_total_outflows.setObjectName(u"value_total_outflows")
        self.value_total_outflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_10.addWidget(self.value_total_outflows)

        self.unit_total_outflows = QLabel(self.widget8)
        self.unit_total_outflows.setObjectName(u"unit_total_outflows")
        self.unit_total_outflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_10.addWidget(self.unit_total_outflows)

        self.title_total_outflows = QLabel(self.widget8)
        self.title_total_outflows.setObjectName(u"title_total_outflows")
        self.title_total_outflows.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_10.addWidget(self.title_total_outflows)


        self.layout_balance_row.addWidget(self.card_total_outflows)

        self.card_recirculation = QFrame(Form)
        self.card_recirculation.setObjectName(u"card_recirculation")
        self.card_recirculation.setMinimumSize(QSize(180, 180))
        self.card_recirculation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_recirculation.setStyleSheet("")
        self.card_recirculation.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_recirculation.setFrameShadow(QFrame.Shadow.Raised)
        self.widget9 = QWidget(self.card_recirculation)
        self.widget9.setObjectName(u"widget9")
        self.widget9.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_11 = QVBoxLayout(self.widget9)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 5, 0, 0)
        self.icon_recirculation = QLabel(self.widget9)
        self.icon_recirculation.setObjectName(u"icon_recirculation")
        self.icon_recirculation.setMinimumSize(QSize(30, 30))
        self.icon_recirculation.setMaximumSize(QSize(30, 30))
        self.icon_recirculation.setPixmap(QPixmap(u":/icons/water_recycle.svg"))
        self.icon_recirculation.setScaledContents(True)
        self.icon_recirculation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_11.addWidget(self.icon_recirculation, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_recirculation = QLabel(self.widget9)
        self.value_recirculation.setObjectName(u"value_recirculation")
        self.value_recirculation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_11.addWidget(self.value_recirculation)

        self.unit_recirculation = QLabel(self.widget9)
        self.unit_recirculation.setObjectName(u"unit_recirculation")
        self.unit_recirculation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_11.addWidget(self.unit_recirculation)

        self.title_recirculation = QLabel(self.widget9)
        self.title_recirculation.setObjectName(u"title_recirculation")
        self.title_recirculation.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_11.addWidget(self.title_recirculation)


        self.layout_balance_row.addWidget(self.card_recirculation)

        self.card_balance_error = QFrame(Form)
        self.card_balance_error.setObjectName(u"card_balance_error")
        self.card_balance_error.setMinimumSize(QSize(180, 180))
        self.card_balance_error.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_balance_error.setStyleSheet("")
        self.card_balance_error.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_balance_error.setFrameShadow(QFrame.Shadow.Raised)
        self.widget10 = QWidget(self.card_balance_error)
        self.widget10.setObjectName(u"widget10")
        self.widget10.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_12 = QVBoxLayout(self.widget10)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 5, 0, 0)
        self.icon_balance_error = QLabel(self.widget10)
        self.icon_balance_error.setObjectName(u"icon_balance_error")
        self.icon_balance_error.setMinimumSize(QSize(30, 30))
        self.icon_balance_error.setMaximumSize(QSize(30, 30))
        self.icon_balance_error.setPixmap(QPixmap(u":/icons/balance error.svg"))
        self.icon_balance_error.setScaledContents(True)
        self.icon_balance_error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_12.addWidget(self.icon_balance_error, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_balance_error = QLabel(self.widget10)
        self.value_balance_error.setObjectName(u"value_balance_error")
        self.value_balance_error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_12.addWidget(self.value_balance_error)

        self.unit_balance_error = QLabel(self.widget10)
        self.unit_balance_error.setObjectName(u"unit_balance_error")
        self.unit_balance_error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_12.addWidget(self.unit_balance_error)

        self.title_balance_error = QLabel(self.widget10)
        self.title_balance_error.setObjectName(u"title_balance_error")
        self.title_balance_error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_12.addWidget(self.title_balance_error)


        self.layout_balance_row.addWidget(self.card_balance_error)

        self.card_status = QFrame(Form)
        self.card_status.setObjectName(u"card_status")
        self.card_status.setMinimumSize(QSize(180, 180))
        self.card_status.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_status.setStyleSheet("")
        self.card_status.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_status.setFrameShadow(QFrame.Shadow.Raised)
        self.widget11 = QWidget(self.card_status)
        self.widget11.setObjectName(u"widget11")
        self.widget11.setGeometry(QRect(10, 10, 181, 161))
        self.verticalLayout_13 = QVBoxLayout(self.widget11)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 5, 0, 0)
        self.icon_status = QLabel(self.widget11)
        self.icon_status.setObjectName(u"icon_status")
        self.icon_status.setMinimumSize(QSize(30, 30))
        self.icon_status.setMaximumSize(QSize(30, 30))
        self.icon_status.setPixmap(QPixmap(u":/icons/excellent.svg"))
        self.icon_status.setScaledContents(True)
        self.icon_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_13.addWidget(self.icon_status, 0, Qt.AlignmentFlag.AlignHCenter)

        self.value_status = QLabel(self.widget11)
        self.value_status.setObjectName(u"value_status")
        self.value_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_13.addWidget(self.value_status)

        self.unit_status = QLabel(self.widget11)
        self.unit_status.setObjectName(u"unit_status")
        self.unit_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_13.addWidget(self.unit_status)

        self.title_status = QLabel(self.widget11)
        self.title_status.setObjectName(u"title_status")
        self.title_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_13.addWidget(self.title_status)


        self.layout_balance_row.addWidget(self.card_status)


        self.verticalLayout.addLayout(self.layout_balance_row)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.icon_water_sources.setText("")
        self.value_water_sources.setText(QCoreApplication.translate("Form", u"87", None))
        self.unit_water_sources.setText(QCoreApplication.translate("Form", u"Active", None))
        self.title_water_sources.setText(QCoreApplication.translate("Form", u"Water Sources", None))
        self.icon_storage_facilities.setText("")
        self.value_storage_facilities.setText(QCoreApplication.translate("Form", u"10", None))
        self.unit_storage_facilities.setText(QCoreApplication.translate("Form", u"dams", None))
        self.title_storage_facilities.setText(QCoreApplication.translate("Form", u"Storage Facilities", None))
        self.icon_total_capacity.setText("")
        self.value_total_capacity.setText(QCoreApplication.translate("Form", u"15.21", None))
        self.unit_total_capacity.setText(QCoreApplication.translate("Form", u"Mm\u00b3", None))
        self.title_total_capacity.setText(QCoreApplication.translate("Form", u"Total Capacity", None))
        self.icon_current_volume.setText("")
        self.value_current_volume.setText(QCoreApplication.translate("Form", u"0.83", None))
        self.unit_current_volume.setText(QCoreApplication.translate("Form", u"Mm\u00b3", None))
        self.title_current_volume.setText(QCoreApplication.translate("Form", u"Current Volume", None))
        self.icon_utilization.setText("")
        self.value_utilization.setText(QCoreApplication.translate("Form", u"5.5 %", None))
        self.unit_utilization.setText(QCoreApplication.translate("Form", u"%", None))
        self.title_utilization.setText(QCoreApplication.translate("Form", u"Utilization", None))
        self.label_environmental_kpis.setText(QCoreApplication.translate("Form", u"Environmental KPIs", None))
        self.icon_rainfall.setText("")
        self.value_rainfall.setText(QCoreApplication.translate("Form", u"75", None))
        self.unit_rainfall.setText(QCoreApplication.translate("Form", u"mm", None))
        self.title_rainfall.setText(QCoreApplication.translate("Form", u"RainFall", None))
        self.icon_evaporation.setText("")
        self.value_evaporation.setText(QCoreApplication.translate("Form", u"150", None))
        self.unit_evaporation.setText(QCoreApplication.translate("Form", u"mm", None))
        self.title_evaporation.setText(QCoreApplication.translate("Form", u"Evapouration", None))
        self.label_balance_status.setText(QCoreApplication.translate("Form", u"Balance Status | December 2025 | ", None))
        self.icon_total_inflows.setText("")
        self.value_total_inflows.setText(QCoreApplication.translate("Form", u"0", None))
        self.unit_total_inflows.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.title_total_inflows.setText(QCoreApplication.translate("Form", u"total Inflows", None))
        self.icon_total_outflows.setText("")
        self.value_total_outflows.setText(QCoreApplication.translate("Form", u"0", None))
        self.unit_total_outflows.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.title_total_outflows.setText(QCoreApplication.translate("Form", u"Total Outflows", None))
        self.icon_recirculation.setText("")
        self.value_recirculation.setText(QCoreApplication.translate("Form", u"0", None))
        self.unit_recirculation.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.title_recirculation.setText(QCoreApplication.translate("Form", u"Recirculation", None))
        self.icon_balance_error.setText("")
        self.value_balance_error.setText(QCoreApplication.translate("Form", u"0", None))
        self.unit_balance_error.setText(QCoreApplication.translate("Form", u"%", None))
        self.title_balance_error.setText(QCoreApplication.translate("Form", u"Balance Error", None))
        self.icon_status.setText("")
        self.value_status.setText(QCoreApplication.translate("Form", u"Excellent", None))
        self.unit_status.setText(QCoreApplication.translate("Form", u"Results", None))
        self.title_status.setText(QCoreApplication.translate("Form", u"Status", None))
    # retranslateUi



