# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'storage_facilities.ui'
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
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QTableView,
    QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1251, 793)
        Form.setStyleSheet(u"")
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(6)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_5 = QFrame(Form)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton = QPushButton(self.frame_5)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setStyleSheet(u"QPushButton{\n"
"border:none;\n"
"}")
        icon = QIcon()
        icon.addFile(u":/icons/search.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.pushButton)

        self.lineedit_search = QLineEdit(self.frame_5)
        self.lineedit_search.setObjectName(u"lineedit_search")

        self.horizontalLayout_2.addWidget(self.lineedit_search)

        self.label = QLabel(self.frame_5)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.comboBox_type_storage = QComboBox(self.frame_5)
        self.comboBox_type_storage.addItem("")
        self.comboBox_type_storage.addItem("")
        self.comboBox_type_storage.addItem("")
        self.comboBox_type_storage.addItem("")
        self.comboBox_type_storage.addItem("")
        self.comboBox_type_storage.setObjectName(u"comboBox_type_storage")

        self.horizontalLayout_2.addWidget(self.comboBox_type_storage)

        self.label_2 = QLabel(self.frame_5)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.comboBox_status_storage = QComboBox(self.frame_5)
        self.comboBox_status_storage.addItem("")
        self.comboBox_status_storage.addItem("")
        self.comboBox_status_storage.addItem("")
        self.comboBox_status_storage.setObjectName(u"comboBox_status_storage")

        self.horizontalLayout_2.addWidget(self.comboBox_status_storage)

        self.horizontalSpacer = QSpacerItem(267, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.add_facility_button = QPushButton(self.frame_5)
        self.add_facility_button.setObjectName(u"add_facility_button")
        self.add_facility_button.setMinimumSize(QSize(80, 35))
        self.add_facility_button.setMaximumSize(QSize(80, 35))

        self.horizontalLayout_2.addWidget(self.add_facility_button)

        self.edit_facility_button = QPushButton(self.frame_5)
        self.edit_facility_button.setObjectName(u"edit_facility_button")
        self.edit_facility_button.setMinimumSize(QSize(80, 35))
        self.edit_facility_button.setMaximumSize(QSize(80, 35))

        self.horizontalLayout_2.addWidget(self.edit_facility_button)

        self.delete_facility_button = QPushButton(self.frame_5)
        self.delete_facility_button.setObjectName(u"delete_facility_button")
        self.delete_facility_button.setMinimumSize(QSize(80, 35))
        self.delete_facility_button.setMaximumSize(QSize(80, 35))

        self.horizontalLayout_2.addWidget(self.delete_facility_button)

        self.monthly_parameter_button = QPushButton(self.frame_5)
        self.monthly_parameter_button.setObjectName(u"monthly_parameter_button")
        self.monthly_parameter_button.setMinimumSize(QSize(120, 35))
        self.monthly_parameter_button.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_2.addWidget(self.monthly_parameter_button)


        self.gridLayout.addWidget(self.frame_5, 3, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame_2 = QFrame(Form)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(250, 140))
        self.frame_2.setMaximumSize(QSize(300, 140))
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.icon_total_capacity = QLabel(self.frame_2)
        self.icon_total_capacity.setObjectName(u"icon_total_capacity")
        self.icon_total_capacity.setMinimumSize(QSize(30, 30))
        self.icon_total_capacity.setMaximumSize(QSize(30, 30))
        self.icon_total_capacity.setPixmap(QPixmap(u":/icons/total_capacity.svg"))
        self.icon_total_capacity.setScaledContents(True)

        self.verticalLayout_4.addWidget(self.icon_total_capacity, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title_total_capacity = QLabel(self.frame_2)
        self.title_total_capacity.setObjectName(u"title_total_capacity")
        self.title_total_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.title_total_capacity)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_7)

        self.value_total_capacity = QLabel(self.frame_2)
        self.value_total_capacity.setObjectName(u"value_total_capacity")
        self.value_total_capacity.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_6.addWidget(self.value_total_capacity)

        self.total_capacity_volume_unit = QLabel(self.frame_2)
        self.total_capacity_volume_unit.setObjectName(u"total_capacity_volume_unit")

        self.horizontalLayout_6.addWidget(self.total_capacity_volume_unit)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_8)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)


        self.horizontalLayout.addWidget(self.frame_2)

        self.frame_3 = QFrame(Form)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setMinimumSize(QSize(250, 140))
        self.frame_3.setMaximumSize(QSize(300, 140))
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.icon_current_volume = QLabel(self.frame_3)
        self.icon_current_volume.setObjectName(u"icon_current_volume")
        self.icon_current_volume.setMinimumSize(QSize(30, 30))
        self.icon_current_volume.setMaximumSize(QSize(30, 30))
        self.icon_current_volume.setPixmap(QPixmap(u":/icons/current_storage.svg"))
        self.icon_current_volume.setScaledContents(True)

        self.verticalLayout.addWidget(self.icon_current_volume, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title_current_volume = QLabel(self.frame_3)
        self.title_current_volume.setObjectName(u"title_current_volume")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_current_volume.sizePolicy().hasHeightForWidth())
        self.title_current_volume.setSizePolicy(sizePolicy)
        self.title_current_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_current_volume.setMargin(0)

        self.verticalLayout.addWidget(self.title_current_volume)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.value_current_volume = QLabel(self.frame_3)
        self.value_current_volume.setObjectName(u"value_current_volume")
        self.value_current_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_4.addWidget(self.value_current_volume)

        self.current_volume_unit = QLabel(self.frame_3)
        self.current_volume_unit.setObjectName(u"current_volume_unit")

        self.horizontalLayout_4.addWidget(self.current_volume_unit)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.horizontalLayout.addWidget(self.frame_3)

        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(250, 140))
        self.frame.setMaximumSize(QSize(300, 140))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.icon_average_utilization = QLabel(self.frame)
        self.icon_average_utilization.setObjectName(u"icon_average_utilization")
        self.icon_average_utilization.setMinimumSize(QSize(30, 30))
        self.icon_average_utilization.setMaximumSize(QSize(30, 30))
        self.icon_average_utilization.setPixmap(QPixmap(u":/icons/utilization.svg"))
        self.icon_average_utilization.setScaledContents(True)
        self.icon_average_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.icon_average_utilization, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title_average_utilization = QLabel(self.frame)
        self.title_average_utilization.setObjectName(u"title_average_utilization")
        self.title_average_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.title_average_utilization)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

        self.value_average_utilization = QLabel(self.frame)
        self.value_average_utilization.setObjectName(u"value_average_utilization")
        self.value_average_utilization.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_5.addWidget(self.value_average_utilization)

        self.avg_utilization_unit = QLabel(self.frame)
        self.avg_utilization_unit.setObjectName(u"avg_utilization_unit")

        self.horizontalLayout_5.addWidget(self.avg_utilization_unit)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_6)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)


        self.horizontalLayout.addWidget(self.frame)

        self.frame_4 = QFrame(Form)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setMinimumSize(QSize(250, 140))
        self.frame_4.setMaximumSize(QSize(300, 140))
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.icon_active_facilities = QLabel(self.frame_4)
        self.icon_active_facilities.setObjectName(u"icon_active_facilities")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(30)
        sizePolicy1.setHeightForWidth(self.icon_active_facilities.sizePolicy().hasHeightForWidth())
        self.icon_active_facilities.setSizePolicy(sizePolicy1)
        self.icon_active_facilities.setMinimumSize(QSize(30, 30))
        self.icon_active_facilities.setMaximumSize(QSize(30, 30))
        self.icon_active_facilities.setPixmap(QPixmap(u":/icons/active.svg"))
        self.icon_active_facilities.setScaledContents(True)

        self.verticalLayout_3.addWidget(self.icon_active_facilities, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title_active_facilities = QLabel(self.frame_4)
        self.title_active_facilities.setObjectName(u"title_active_facilities")
        self.title_active_facilities.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.title_active_facilities)

        self.value_active_facilities = QLabel(self.frame_4)
        self.value_active_facilities.setObjectName(u"value_active_facilities")
        self.value_active_facilities.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.value_active_facilities)


        self.horizontalLayout.addWidget(self.frame_4)


        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)

        self.frame_6 = QFrame(Form)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setStyleSheet(u"QFrame{\n"
"	background-color: rgb(62, 62, 93);\n"
"	color:white;\n"
"}")
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.frame_6)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(20, 20))
        self.label_3.setMaximumSize(QSize(20, 20))
        self.label_3.setPixmap(QPixmap(u":/icons/Storage Facilities_2.svg"))
        self.label_3.setScaledContents(True)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.label_4 = QLabel(self.frame_6)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setStyleSheet(u"QLabel{\n"
"font-weight: bold;\n"
"font: 12px;\n"
"}")

        self.horizontalLayout_3.addWidget(self.label_4)

        self.horizontalSpacer_2 = QSpacerItem(608, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.label_5 = QLabel(self.frame_6)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setStyleSheet(u"QLabel{\n"
"font:10px;\n"
"}")
        self.label_5.setScaledContents(False)
        self.label_5.setWordWrap(False)

        self.horizontalLayout_3.addWidget(self.label_5)


        self.gridLayout.addWidget(self.frame_6, 4, 0, 1, 1)

        self.tableView = QTableView(Form)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setMinimumSize(QSize(20, 20))

        self.gridLayout.addWidget(self.tableView, 5, 0, 1, 1)

        self.label_7 = QLabel(Form)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setStyleSheet(u"QLabel{\n"
"font-weight:bold;\n"
"font:28px;\n"
"}")

        self.gridLayout.addWidget(self.label_7, 0, 0, 1, 1)

        self.label_6 = QLabel(Form)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        self.pushButton.setText("")
        self.label.setText(QCoreApplication.translate("Form", u"Type:", None))
        self.comboBox_type_storage.setItemText(0, QCoreApplication.translate("Form", u"All", None))
        self.comboBox_type_storage.setItemText(1, QCoreApplication.translate("Form", u"Resevoir", None))
        self.comboBox_type_storage.setItemText(2, QCoreApplication.translate("Form", u"TSF", None))
        self.comboBox_type_storage.setItemText(3, QCoreApplication.translate("Form", u"Dam", None))
        self.comboBox_type_storage.setItemText(4, QCoreApplication.translate("Form", u"PCD", None))

        self.label_2.setText(QCoreApplication.translate("Form", u"Status:", None))
        self.comboBox_status_storage.setItemText(0, QCoreApplication.translate("Form", u"All", None))
        self.comboBox_status_storage.setItemText(1, QCoreApplication.translate("Form", u"Active", None))
        self.comboBox_status_storage.setItemText(2, QCoreApplication.translate("Form", u"Inactive", None))

        self.add_facility_button.setText(QCoreApplication.translate("Form", u"Add Facility", None))
        self.edit_facility_button.setText(QCoreApplication.translate("Form", u"Edit", None))
        self.delete_facility_button.setText(QCoreApplication.translate("Form", u"Delete", None))
        self.monthly_parameter_button.setText(QCoreApplication.translate("Form", u"Monthly Params", None))
        self.icon_total_capacity.setText("")
        self.title_total_capacity.setText(QCoreApplication.translate("Form", u"Total Capacity", None))
        self.value_total_capacity.setText(QCoreApplication.translate("Form", u"15,205.000", None))
        self.total_capacity_volume_unit.setText(QCoreApplication.translate("Form", u" m\u00b3", None))
        self.icon_current_volume.setText("")
        self.title_current_volume.setText(QCoreApplication.translate("Form", u"Current Volume", None))
        self.value_current_volume.setText(QCoreApplication.translate("Form", u"832,628 ", None))
        self.current_volume_unit.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.icon_average_utilization.setText("")
        self.title_average_utilization.setText(QCoreApplication.translate("Form", u"Avg Utilization", None))
        self.value_average_utilization.setText(QCoreApplication.translate("Form", u"27.4 ", None))
        self.avg_utilization_unit.setText(QCoreApplication.translate("Form", u"%", None))
        self.icon_active_facilities.setText("")
        self.title_active_facilities.setText(QCoreApplication.translate("Form", u"Active Facilities", None))
        self.value_active_facilities.setText(QCoreApplication.translate("Form", u"10", None))
        self.label_3.setText("")
        self.label_4.setText(QCoreApplication.translate("Form", u"Storage Facilities Overview", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Utilization = current volume / capacity. End of month volume rolls into the next month per facility. Volumes moves via\n"
"automatic pump tranfers (when level >= pump start level or manual inter-facility transfers.)", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Storage Facilities", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Monitoring and manage water storage infrastructure", None))
        pass
    # retranslateUi

