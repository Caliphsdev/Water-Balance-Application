# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monitoring_data.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QTableView, QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1196, 800)
        Form.setStyleSheet("")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 0, 0, 0)
        self.label_title = QLabel(Form)
        self.label_title.setObjectName(u"label_title")
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout.addWidget(self.label_title)

        self.label_subtitle = QLabel(Form)
        self.label_subtitle.setObjectName(u"label_subtitle")
        self.label_subtitle.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout.addWidget(self.label_subtitle)

        self.label_status = QLabel(Form)
        self.label_status.setObjectName(u"label_status")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout.addWidget(self.label_status)

        self.mainTabWidget = QTabWidget(Form)
        self.mainTabWidget.setObjectName(u"mainTabWidget")
        self.tab_borehole_static = QWidget()
        self.tab_borehole_static.setObjectName(u"tab_borehole_static")
        self.verticalLayout_static = QVBoxLayout(self.tab_borehole_static)
        self.verticalLayout_static.setSpacing(10)
        self.verticalLayout_static.setObjectName(u"verticalLayout_static")
        self.staticSubTabs = QTabWidget(self.tab_borehole_static)
        self.staticSubTabs.setObjectName(u"staticSubTabs")
        self.tab_static_upload = QWidget()
        self.tab_static_upload.setObjectName(u"tab_static_upload")
        self.verticalLayout_static_upload = QVBoxLayout(self.tab_static_upload)
        self.verticalLayout_static_upload.setSpacing(10)
        self.verticalLayout_static_upload.setObjectName(u"verticalLayout_static_upload")
        self.frame_static_folder = QFrame(self.tab_static_upload)
        self.frame_static_folder.setObjectName(u"frame_static_folder")
        self.frame_static_folder.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_static_folder.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_static_folder)
        self.verticalLayout_2.setSpacing(8)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_static_folder = QLabel(self.frame_static_folder)
        self.label_static_folder.setObjectName(u"label_static_folder")

        self.verticalLayout_2.addWidget(self.label_static_folder)

        self.horizontalLayout_static_folder = QHBoxLayout()
        self.horizontalLayout_static_folder.setSpacing(10)
        self.horizontalLayout_static_folder.setObjectName(u"horizontalLayout_static_folder")
        self.static_folder_path = QLineEdit(self.frame_static_folder)
        self.static_folder_path.setObjectName(u"static_folder_path")
        self.static_folder_path.setReadOnly(True)

        self.horizontalLayout_static_folder.addWidget(self.static_folder_path)

        self.pushButton_6 = QPushButton(self.frame_static_folder)
        self.pushButton_6.setObjectName(u"pushButton_6")
        self.pushButton_6.setMinimumSize(QSize(120, 35))
        self.pushButton_6.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_static_folder.addWidget(self.pushButton_6)


        self.verticalLayout_2.addLayout(self.horizontalLayout_static_folder)

        self.label_static_autoload = QLabel(self.frame_static_folder)
        self.label_static_autoload.setObjectName(u"label_static_autoload")

        self.verticalLayout_2.addWidget(self.label_static_autoload)


        self.verticalLayout_static_upload.addWidget(self.frame_static_folder)

        self.tableView_2 = QTableView(self.tab_static_upload)
        self.tableView_2.setObjectName(u"tableView_2")

        self.verticalLayout_static_upload.addWidget(self.tableView_2)

        self.staticSubTabs.addTab(self.tab_static_upload, "")
        self.tab_static_visualize = QWidget()
        self.tab_static_visualize.setObjectName(u"tab_static_visualize")
        self.verticalLayout_static_viz = QVBoxLayout(self.tab_static_visualize)
        self.verticalLayout_static_viz.setSpacing(10)
        self.verticalLayout_static_viz.setObjectName(u"verticalLayout_static_viz")
        self.frame_static_options = QFrame(self.tab_static_visualize)
        self.frame_static_options.setObjectName(u"frame_static_options")
        self.frame_static_options.setMinimumSize(QSize(0, 60))
        self.frame_static_options.setMaximumSize(QSize(16777215, 60))
        self.frame_static_options.setFrameShape(QFrame.Shape.StyledPanel)
        self.horizontalLayout_static_options = QHBoxLayout(self.frame_static_options)
        self.horizontalLayout_static_options.setObjectName(u"horizontalLayout_static_options")
        self.label_static_chart_type = QLabel(self.frame_static_options)
        self.label_static_chart_type.setObjectName(u"label_static_chart_type")

        self.horizontalLayout_static_options.addWidget(self.label_static_chart_type)

        self.static_chart_type = QComboBox(self.frame_static_options)
        self.static_chart_type.addItem("")
        self.static_chart_type.addItem("")
        self.static_chart_type.addItem("")
        self.static_chart_type.setObjectName(u"static_chart_type")

        self.horizontalLayout_static_options.addWidget(self.static_chart_type)

        self.label_static_borehole = QLabel(self.frame_static_options)
        self.label_static_borehole.setObjectName(u"label_static_borehole")

        self.horizontalLayout_static_options.addWidget(self.label_static_borehole)

        self.combo_static_borehole = QComboBox(self.frame_static_options)
        self.combo_static_borehole.setObjectName(u"combo_static_borehole")
        self.combo_static_borehole.setMinimumSize(QSize(120, 0))
        self.combo_static_borehole.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_static_options.addWidget(self.combo_static_borehole)

        self.label_from_year = QLabel(self.frame_static_options)
        self.label_from_year.setObjectName(u"label_from_year")

        self.horizontalLayout_static_options.addWidget(self.label_from_year)

        self.combo_year_from = QComboBox(self.frame_static_options)
        self.combo_year_from.setObjectName(u"combo_year_from")
        self.combo_year_from.setMinimumSize(QSize(70, 0))
        self.combo_year_from.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_static_options.addWidget(self.combo_year_from)

        self.label_from_month = QLabel(self.frame_static_options)
        self.label_from_month.setObjectName(u"label_from_month")

        self.horizontalLayout_static_options.addWidget(self.label_from_month)

        self.combo_month_from = QComboBox(self.frame_static_options)
        self.combo_month_from.setObjectName(u"combo_month_from")
        self.combo_month_from.setMinimumSize(QSize(70, 0))
        self.combo_month_from.setMaximumSize(QSize(90, 16777215))

        self.horizontalLayout_static_options.addWidget(self.combo_month_from)

        self.label_to_year = QLabel(self.frame_static_options)
        self.label_to_year.setObjectName(u"label_to_year")

        self.horizontalLayout_static_options.addWidget(self.label_to_year)

        self.combo_year_to = QComboBox(self.frame_static_options)
        self.combo_year_to.setObjectName(u"combo_year_to")
        self.combo_year_to.setMinimumSize(QSize(70, 0))
        self.combo_year_to.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_static_options.addWidget(self.combo_year_to)

        self.label_to_month = QLabel(self.frame_static_options)
        self.label_to_month.setObjectName(u"label_to_month")

        self.horizontalLayout_static_options.addWidget(self.label_to_month)

        self.combo_month_to = QComboBox(self.frame_static_options)
        self.combo_month_to.setObjectName(u"combo_month_to")
        self.combo_month_to.setMinimumSize(QSize(70, 0))
        self.combo_month_to.setMaximumSize(QSize(90, 16777215))

        self.horizontalLayout_static_options.addWidget(self.combo_month_to)

        self.horizontalSpacer_static = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_static_options.addItem(self.horizontalSpacer_static)

        self.pushButton_4 = QPushButton(self.frame_static_options)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setMinimumSize(QSize(120, 35))
        self.pushButton_4.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_static_options.addWidget(self.pushButton_4)

        self.pushButton_5 = QPushButton(self.frame_static_options)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setMinimumSize(QSize(100, 35))
        self.pushButton_5.setMaximumSize(QSize(100, 35))

        self.horizontalLayout_static_options.addWidget(self.pushButton_5)


        self.verticalLayout_static_viz.addWidget(self.frame_static_options)

        self.static_chart_viewport = QFrame(self.tab_static_visualize)
        self.static_chart_viewport.setObjectName(u"static_chart_viewport")
        self.static_chart_viewport.setFrameShape(QFrame.Shape.StyledPanel)
        self.staticChartLayout = QVBoxLayout(self.static_chart_viewport)
        self.staticChartLayout.setObjectName(u"staticChartLayout")
        self.static_chart_placeholder = QLabel(self.static_chart_viewport)
        self.static_chart_placeholder.setObjectName(u"static_chart_placeholder")
        self.static_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.staticChartLayout.addWidget(self.static_chart_placeholder)


        self.verticalLayout_static_viz.addWidget(self.static_chart_viewport)

        self.staticSubTabs.addTab(self.tab_static_visualize, "")

        self.verticalLayout_static.addWidget(self.staticSubTabs)

        self.mainTabWidget.addTab(self.tab_borehole_static, "")
        self.tab_borehole_monitoring = QWidget()
        self.tab_borehole_monitoring.setObjectName(u"tab_borehole_monitoring")
        self.verticalLayout_monitoring = QVBoxLayout(self.tab_borehole_monitoring)
        self.verticalLayout_monitoring.setSpacing(10)
        self.verticalLayout_monitoring.setObjectName(u"verticalLayout_monitoring")
        self.monitoringSubTabs = QTabWidget(self.tab_borehole_monitoring)
        self.monitoringSubTabs.setObjectName(u"monitoringSubTabs")
        self.tab_monitoring_upload = QWidget()
        self.tab_monitoring_upload.setObjectName(u"tab_monitoring_upload")
        self.verticalLayout_monitoring_upload = QVBoxLayout(self.tab_monitoring_upload)
        self.verticalLayout_monitoring_upload.setSpacing(10)
        self.verticalLayout_monitoring_upload.setObjectName(u"verticalLayout_monitoring_upload")
        self.frame_monitoring_folder = QFrame(self.tab_monitoring_upload)
        self.frame_monitoring_folder.setObjectName(u"frame_monitoring_folder")
        self.frame_monitoring_folder.setMaximumSize(QSize(16777215, 120))
        self.frame_monitoring_folder.setFrameShape(QFrame.Shape.StyledPanel)
        self.verticalLayout_3 = QVBoxLayout(self.frame_monitoring_folder)
        self.verticalLayout_3.setSpacing(8)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_monitoring_folder = QLabel(self.frame_monitoring_folder)
        self.label_monitoring_folder.setObjectName(u"label_monitoring_folder")

        self.verticalLayout_3.addWidget(self.label_monitoring_folder)

        self.horizontalLayout_monitoring_folder = QHBoxLayout()
        self.horizontalLayout_monitoring_folder.setSpacing(10)
        self.horizontalLayout_monitoring_folder.setObjectName(u"horizontalLayout_monitoring_folder")
        self.monitoring_status_label = QLabel(self.frame_monitoring_folder)
        self.monitoring_status_label.setObjectName(u"monitoring_status_label")
        self.monitoring_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_monitoring_folder.addWidget(self.monitoring_status_label)

        self.monitoring_folder_path = QLineEdit(self.frame_monitoring_folder)
        self.monitoring_folder_path.setObjectName(u"monitoring_folder_path")
        self.monitoring_folder_path.setReadOnly(True)

        self.horizontalLayout_monitoring_folder.addWidget(self.monitoring_folder_path)

        self.pushButton_3 = QPushButton(self.frame_monitoring_folder)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setMinimumSize(QSize(120, 35))
        self.pushButton_3.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_monitoring_folder.addWidget(self.pushButton_3)


        self.verticalLayout_3.addLayout(self.horizontalLayout_monitoring_folder)

        self.label_monitoring_autoload = QLabel(self.frame_monitoring_folder)
        self.label_monitoring_autoload.setObjectName(u"label_monitoring_autoload")

        self.verticalLayout_3.addWidget(self.label_monitoring_autoload)


        self.verticalLayout_monitoring_upload.addWidget(self.frame_monitoring_folder)

        self.frame_monitoring_filter = QFrame(self.tab_monitoring_upload)
        self.frame_monitoring_filter.setObjectName(u"frame_monitoring_filter")
        self.frame_monitoring_filter.setFrameShape(QFrame.Shape.StyledPanel)
        self.horizontalLayout_monitoring_filter = QHBoxLayout(self.frame_monitoring_filter)
        self.horizontalLayout_monitoring_filter.setObjectName(u"horizontalLayout_monitoring_filter")
        self.label_monitoring_aquifer = QLabel(self.frame_monitoring_filter)
        self.label_monitoring_aquifer.setObjectName(u"label_monitoring_aquifer")

        self.horizontalLayout_monitoring_filter.addWidget(self.label_monitoring_aquifer)

        self.monitoring_aquifer_filter = QComboBox(self.frame_monitoring_filter)
        self.monitoring_aquifer_filter.addItem("")
        self.monitoring_aquifer_filter.addItem("")
        self.monitoring_aquifer_filter.addItem("")
        self.monitoring_aquifer_filter.setObjectName(u"monitoring_aquifer_filter")

        self.horizontalLayout_monitoring_filter.addWidget(self.monitoring_aquifer_filter)

        self.horizontalSpacer_monitoring_filter = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_monitoring_filter.addItem(self.horizontalSpacer_monitoring_filter)


        self.verticalLayout_monitoring_upload.addWidget(self.frame_monitoring_filter)

        self.tableView = QTableView(self.tab_monitoring_upload)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout_monitoring_upload.addWidget(self.tableView)

        self.monitoringSubTabs.addTab(self.tab_monitoring_upload, "")
        self.tab_monitoring_visualize = QWidget()
        self.tab_monitoring_visualize.setObjectName(u"tab_monitoring_visualize")
        self.verticalLayout_monitoring_viz = QVBoxLayout(self.tab_monitoring_visualize)
        self.verticalLayout_monitoring_viz.setSpacing(10)
        self.verticalLayout_monitoring_viz.setObjectName(u"verticalLayout_monitoring_viz")
        self.frame_monitoring_options = QFrame(self.tab_monitoring_visualize)
        self.frame_monitoring_options.setObjectName(u"frame_monitoring_options")
        self.frame_monitoring_options.setMinimumSize(QSize(0, 60))
        self.frame_monitoring_options.setMaximumSize(QSize(16777215, 60))
        self.frame_monitoring_options.setFrameShape(QFrame.Shape.StyledPanel)
        self.horizontalLayout_monitoring_options = QHBoxLayout(self.frame_monitoring_options)
        self.horizontalLayout_monitoring_options.setObjectName(u"horizontalLayout_monitoring_options")
        self.label_monitoring_chart_type = QLabel(self.frame_monitoring_options)
        self.label_monitoring_chart_type.setObjectName(u"label_monitoring_chart_type")

        self.horizontalLayout_monitoring_options.addWidget(self.label_monitoring_chart_type)

        self.monitoring_chart_type = QComboBox(self.frame_monitoring_options)
        self.monitoring_chart_type.addItem("")
        self.monitoring_chart_type.addItem("")
        self.monitoring_chart_type.setObjectName(u"monitoring_chart_type")
        self.monitoring_chart_type.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_monitoring_options.addWidget(self.monitoring_chart_type)

        self.label = QLabel(self.frame_monitoring_options)
        self.label.setObjectName(u"label")

        self.horizontalLayout_monitoring_options.addWidget(self.label)

        self.comboBox_2 = QComboBox(self.frame_monitoring_options)
        self.comboBox_2.setObjectName(u"comboBox_2")
        self.comboBox_2.setMinimumSize(QSize(130, 0))

        self.horizontalLayout_monitoring_options.addWidget(self.comboBox_2)

        self.horizontalSpacer_monitoring = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_monitoring_options.addItem(self.horizontalSpacer_monitoring)

        self.label_2 = QLabel(self.frame_monitoring_options)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_monitoring_options.addWidget(self.label_2)

        self.comboBox_4 = QComboBox(self.frame_monitoring_options)
        self.comboBox_4.setObjectName(u"comboBox_4")
        self.comboBox_4.setMinimumSize(QSize(90, 0))
        self.comboBox_4.setMaximumSize(QSize(90, 16777215))

        self.horizontalLayout_monitoring_options.addWidget(self.comboBox_4)

        self.label_3 = QLabel(self.frame_monitoring_options)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_monitoring_options.addWidget(self.label_3)

        self.comboBox_3 = QComboBox(self.frame_monitoring_options)
        self.comboBox_3.setObjectName(u"comboBox_3")
        self.comboBox_3.setMinimumSize(QSize(90, 0))
        self.comboBox_3.setMaximumSize(QSize(90, 16777215))

        self.horizontalLayout_monitoring_options.addWidget(self.comboBox_3)

        self.label_monitoring_date_from = QLabel(self.frame_monitoring_options)
        self.label_monitoring_date_from.setObjectName(u"label_monitoring_date_from")

        self.horizontalLayout_monitoring_options.addWidget(self.label_monitoring_date_from)

        self.date_monitoring_from = QDateEdit(self.frame_monitoring_options)
        self.date_monitoring_from.setObjectName(u"date_monitoring_from")
        self.date_monitoring_from.setMinimumSize(QSize(110, 0))
        self.date_monitoring_from.setCalendarPopup(True)

        self.horizontalLayout_monitoring_options.addWidget(self.date_monitoring_from)

        self.label_monitoring_date_to = QLabel(self.frame_monitoring_options)
        self.label_monitoring_date_to.setObjectName(u"label_monitoring_date_to")

        self.horizontalLayout_monitoring_options.addWidget(self.label_monitoring_date_to)

        self.date_monitoring_to = QDateEdit(self.frame_monitoring_options)
        self.date_monitoring_to.setObjectName(u"date_monitoring_to")
        self.date_monitoring_to.setMinimumSize(QSize(110, 0))
        self.date_monitoring_to.setCalendarPopup(True)

        self.horizontalLayout_monitoring_options.addWidget(self.date_monitoring_to)

        self.pushButton_2 = QPushButton(self.frame_monitoring_options)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setMinimumSize(QSize(120, 35))
        self.pushButton_2.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_monitoring_options.addWidget(self.pushButton_2)

        self.pushButton = QPushButton(self.frame_monitoring_options)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QSize(100, 35))
        self.pushButton.setMaximumSize(QSize(100, 35))

        self.horizontalLayout_monitoring_options.addWidget(self.pushButton)


        self.verticalLayout_monitoring_viz.addWidget(self.frame_monitoring_options)

        self.monitoring_chart_viewport = QFrame(self.tab_monitoring_visualize)
        self.monitoring_chart_viewport.setObjectName(u"monitoring_chart_viewport")
        self.monitoring_chart_viewport.setFrameShape(QFrame.Shape.StyledPanel)
        self.monitoringChartLayout = QVBoxLayout(self.monitoring_chart_viewport)
        self.monitoringChartLayout.setObjectName(u"monitoringChartLayout")
        self.monitoring_chart_placeholder = QLabel(self.monitoring_chart_viewport)
        self.monitoring_chart_placeholder.setObjectName(u"monitoring_chart_placeholder")
        self.monitoring_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.monitoringChartLayout.addWidget(self.monitoring_chart_placeholder)


        self.verticalLayout_monitoring_viz.addWidget(self.monitoring_chart_viewport)

        self.monitoringSubTabs.addTab(self.tab_monitoring_visualize, "")

        self.verticalLayout_monitoring.addWidget(self.monitoringSubTabs)

        self.mainTabWidget.addTab(self.tab_borehole_monitoring, "")
        self.tab_pcd_monitoring = QWidget()
        self.tab_pcd_monitoring.setObjectName(u"tab_pcd_monitoring")
        self.verticalLayout_pcd = QVBoxLayout(self.tab_pcd_monitoring)
        self.verticalLayout_pcd.setSpacing(10)
        self.verticalLayout_pcd.setObjectName(u"verticalLayout_pcd")
        self.pcdSubTabs = QTabWidget(self.tab_pcd_monitoring)
        self.pcdSubTabs.setObjectName(u"pcdSubTabs")
        self.tab_pcd_upload = QWidget()
        self.tab_pcd_upload.setObjectName(u"tab_pcd_upload")
        self.verticalLayout_pcd_upload = QVBoxLayout(self.tab_pcd_upload)
        self.verticalLayout_pcd_upload.setSpacing(10)
        self.verticalLayout_pcd_upload.setObjectName(u"verticalLayout_pcd_upload")
        self.frame_pcd_folder = QFrame(self.tab_pcd_upload)
        self.frame_pcd_folder.setObjectName(u"frame_pcd_folder")
        self.frame_pcd_folder.setFrameShape(QFrame.Shape.StyledPanel)
        self.verticalLayout_4 = QVBoxLayout(self.frame_pcd_folder)
        self.verticalLayout_4.setSpacing(8)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_pcd_folder = QLabel(self.frame_pcd_folder)
        self.label_pcd_folder.setObjectName(u"label_pcd_folder")

        self.verticalLayout_4.addWidget(self.label_pcd_folder)

        self.horizontalLayout_pcd_folder = QHBoxLayout()
        self.horizontalLayout_pcd_folder.setSpacing(10)
        self.horizontalLayout_pcd_folder.setObjectName(u"horizontalLayout_pcd_folder")
        self.pcd_folder_path = QLineEdit(self.frame_pcd_folder)
        self.pcd_folder_path.setObjectName(u"pcd_folder_path")
        self.pcd_folder_path.setReadOnly(True)

        self.horizontalLayout_pcd_folder.addWidget(self.pcd_folder_path)

        self.pushButton_7 = QPushButton(self.frame_pcd_folder)
        self.pushButton_7.setObjectName(u"pushButton_7")
        self.pushButton_7.setMinimumSize(QSize(120, 35))
        self.pushButton_7.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_pcd_folder.addWidget(self.pushButton_7)


        self.verticalLayout_4.addLayout(self.horizontalLayout_pcd_folder)

        self.label_pcd_autoload = QLabel(self.frame_pcd_folder)
        self.label_pcd_autoload.setObjectName(u"label_pcd_autoload")

        self.verticalLayout_4.addWidget(self.label_pcd_autoload)


        self.verticalLayout_pcd_upload.addWidget(self.frame_pcd_folder)

        self.frame_pcd_filter = QFrame(self.tab_pcd_upload)
        self.frame_pcd_filter.setObjectName(u"frame_pcd_filter")
        self.frame_pcd_filter.setFrameShape(QFrame.Shape.StyledPanel)
        self.horizontalLayout_pcd_filter = QHBoxLayout(self.frame_pcd_filter)
        self.horizontalLayout_pcd_filter.setObjectName(u"horizontalLayout_pcd_filter")
        self.label_pcd_point = QLabel(self.frame_pcd_filter)
        self.label_pcd_point.setObjectName(u"label_pcd_point")

        self.horizontalLayout_pcd_filter.addWidget(self.label_pcd_point)

        self.pcd_point_filter = QComboBox(self.frame_pcd_filter)
        self.pcd_point_filter.addItem("")
        self.pcd_point_filter.setObjectName(u"pcd_point_filter")
        self.pcd_point_filter.setMinimumSize(QSize(130, 0))
        self.pcd_point_filter.setMaximumSize(QSize(130, 16777215))

        self.horizontalLayout_pcd_filter.addWidget(self.pcd_point_filter)

        self.horizontalSpacer_pcd_filter = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_pcd_filter.addItem(self.horizontalSpacer_pcd_filter)


        self.verticalLayout_pcd_upload.addWidget(self.frame_pcd_filter)

        self.tableView_3 = QTableView(self.tab_pcd_upload)
        self.tableView_3.setObjectName(u"tableView_3")

        self.verticalLayout_pcd_upload.addWidget(self.tableView_3)

        self.pcdSubTabs.addTab(self.tab_pcd_upload, "")
        self.tab_pcd_visualize = QWidget()
        self.tab_pcd_visualize.setObjectName(u"tab_pcd_visualize")
        self.verticalLayout_pcd_viz = QVBoxLayout(self.tab_pcd_visualize)
        self.verticalLayout_pcd_viz.setSpacing(10)
        self.verticalLayout_pcd_viz.setObjectName(u"verticalLayout_pcd_viz")
        self.frame_pcd_options = QFrame(self.tab_pcd_visualize)
        self.frame_pcd_options.setObjectName(u"frame_pcd_options")
        self.frame_pcd_options.setMaximumSize(QSize(16777215, 60))
        self.frame_pcd_options.setFrameShape(QFrame.Shape.StyledPanel)
        self.horizontalLayout_pcd_options = QHBoxLayout(self.frame_pcd_options)
        self.horizontalLayout_pcd_options.setObjectName(u"horizontalLayout_pcd_options")
        self.label_pcd_chart_type = QLabel(self.frame_pcd_options)
        self.label_pcd_chart_type.setObjectName(u"label_pcd_chart_type")

        self.horizontalLayout_pcd_options.addWidget(self.label_pcd_chart_type)

        self.pcd_chart_type = QComboBox(self.frame_pcd_options)
        self.pcd_chart_type.addItem("")
        self.pcd_chart_type.addItem("")
        self.pcd_chart_type.setObjectName(u"pcd_chart_type")
        self.pcd_chart_type.setMinimumSize(QSize(100, 0))
        self.pcd_chart_type.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_pcd_options.addWidget(self.pcd_chart_type)

        self.label_4 = QLabel(self.frame_pcd_options)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_pcd_options.addWidget(self.label_4)

        self.comboBox_5 = QComboBox(self.frame_pcd_options)
        self.comboBox_5.setObjectName(u"comboBox_5")
        self.comboBox_5.setMinimumSize(QSize(130, 0))
        self.comboBox_5.setMaximumSize(QSize(130, 16777215))

        self.horizontalLayout_pcd_options.addWidget(self.comboBox_5)

        self.horizontalSpacer_pcd = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_pcd_options.addItem(self.horizontalSpacer_pcd)

        self.label_5 = QLabel(self.frame_pcd_options)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_pcd_options.addWidget(self.label_5)

        self.comboBox_6 = QComboBox(self.frame_pcd_options)
        self.comboBox_6.setObjectName(u"comboBox_6")
        self.comboBox_6.setMinimumSize(QSize(130, 0))
        self.comboBox_6.setMaximumSize(QSize(130, 16777215))

        self.horizontalLayout_pcd_options.addWidget(self.comboBox_6)

        self.pushButton_8 = QPushButton(self.frame_pcd_options)
        self.pushButton_8.setObjectName(u"pushButton_8")
        self.pushButton_8.setMinimumSize(QSize(120, 35))
        self.pushButton_8.setMaximumSize(QSize(120, 35))

        self.horizontalLayout_pcd_options.addWidget(self.pushButton_8)

        self.pushButton_9 = QPushButton(self.frame_pcd_options)
        self.pushButton_9.setObjectName(u"pushButton_9")
        self.pushButton_9.setMinimumSize(QSize(100, 35))
        self.pushButton_9.setMaximumSize(QSize(100, 35))

        self.horizontalLayout_pcd_options.addWidget(self.pushButton_9)


        self.verticalLayout_pcd_viz.addWidget(self.frame_pcd_options)

        self.pcd_chart_viewport = QFrame(self.tab_pcd_visualize)
        self.pcd_chart_viewport.setObjectName(u"pcd_chart_viewport")
        self.pcd_chart_viewport.setFrameShape(QFrame.Shape.StyledPanel)
        self.pcdChartLayout = QVBoxLayout(self.pcd_chart_viewport)
        self.pcdChartLayout.setObjectName(u"pcdChartLayout")
        self.pcd_chart_placeholder = QLabel(self.pcd_chart_viewport)
        self.pcd_chart_placeholder.setObjectName(u"pcd_chart_placeholder")
        self.pcd_chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pcdChartLayout.addWidget(self.pcd_chart_placeholder)


        self.verticalLayout_pcd_viz.addWidget(self.pcd_chart_viewport)

        self.pcdSubTabs.addTab(self.tab_pcd_visualize, "")

        self.verticalLayout_pcd.addWidget(self.pcdSubTabs)

        self.mainTabWidget.addTab(self.tab_pcd_monitoring, "")

        self.verticalLayout.addWidget(self.mainTabWidget)


        self.retranslateUi(Form)

        self.mainTabWidget.setCurrentIndex(2)
        self.staticSubTabs.setCurrentIndex(1)
        self.monitoringSubTabs.setCurrentIndex(0)
        self.pcdSubTabs.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Monitoring Data Dashboard", None))
        self.label_title.setText(QCoreApplication.translate("Form", u"\U0001f4ca Monitoring Data Dashboard", None))
        self.label_subtitle.setText(QCoreApplication.translate("Form", u"Environmental and operational monitoring data visualization", None))
        self.label_status.setText(QCoreApplication.translate("Form", u"Ready to load monitoring data", None))
        self.label_static_folder.setText(QCoreApplication.translate("Form", u"Folder with static borehole Excel files:", None))
        self.static_folder_path.setPlaceholderText(QCoreApplication.translate("Form", u"Choose a folder to auto-load and preview static Levels data", None))
        self.pushButton_6.setText(QCoreApplication.translate("Form", u"Choose Folder", None))
        self.label_static_autoload.setStyleSheet("")
        self.label_static_autoload.setText(QCoreApplication.translate("Form", u"Auto-loads: date + borehole headers (TRM x)", None))
        self.staticSubTabs.setTabText(self.staticSubTabs.indexOf(self.tab_static_upload), QCoreApplication.translate("Form", u"Upload & Preview", None))
        self.label_static_chart_type.setText(QCoreApplication.translate("Form", u"Chart Type:", None))
        self.static_chart_type.setItemText(0, QCoreApplication.translate("Form", u"Line", None))
        self.static_chart_type.setItemText(1, QCoreApplication.translate("Form", u"Bar", None))
        self.static_chart_type.setItemText(2, QCoreApplication.translate("Form", u"Scatter", None))

        self.label_static_borehole.setText(QCoreApplication.translate("Form", u"Borehole:", None))
        self.label_from_year.setText(QCoreApplication.translate("Form", u"From Year:", None))
        self.label_from_month.setText(QCoreApplication.translate("Form", u"Month:", None))
        self.label_to_year.setText(QCoreApplication.translate("Form", u"To Year:", None))
        self.label_to_month.setText(QCoreApplication.translate("Form", u"Month:", None))
        self.pushButton_4.setText(QCoreApplication.translate("Form", u"Generate Chart", None))
        self.pushButton_5.setText(QCoreApplication.translate("Form", u"Save Chart", None))
        self.static_chart_placeholder.setStyleSheet("")
        self.static_chart_placeholder.setText(QCoreApplication.translate("Form", u"Load files then generate charts", None))
        self.staticSubTabs.setTabText(self.staticSubTabs.indexOf(self.tab_static_visualize), QCoreApplication.translate("Form", u"Visualize", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_borehole_static), QCoreApplication.translate("Form", u"Borehole Static Levels", None))
        self.label_monitoring_folder.setText(QCoreApplication.translate("Form", u"Folder with monitoring borehole Excel files:", None))
        self.monitoring_status_label.setStyleSheet("")
        self.monitoring_status_label.setText("")
        self.monitoring_folder_path.setPlaceholderText(QCoreApplication.translate("Form", u"Choose a folder to auto-load and preview monitoring data", None))
        self.pushButton_3.setText(QCoreApplication.translate("Form", u"Choose Folder", None))
        self.label_monitoring_autoload.setStyleSheet("")
        self.label_monitoring_autoload.setText(QCoreApplication.translate("Form", u"Auto-loads: date + borehole + parameters", None))
        self.label_monitoring_aquifer.setText(QCoreApplication.translate("Form", u"Aquifer:", None))
        self.monitoring_aquifer_filter.setItemText(0, QCoreApplication.translate("Form", u"All", None))
        self.monitoring_aquifer_filter.setItemText(1, QCoreApplication.translate("Form", u"Shallow Aquifer", None))
        self.monitoring_aquifer_filter.setItemText(2, QCoreApplication.translate("Form", u"Deep Aquifer", None))

        self.monitoringSubTabs.setTabText(self.monitoringSubTabs.indexOf(self.tab_monitoring_upload), QCoreApplication.translate("Form", u"Upload & Preview", None))
        self.label_monitoring_chart_type.setText(QCoreApplication.translate("Form", u"Chart Type:", None))
        self.monitoring_chart_type.setItemText(0, QCoreApplication.translate("Form", u"Line", None))
        self.monitoring_chart_type.setItemText(1, QCoreApplication.translate("Form", u"Bar", None))

        self.label.setText(QCoreApplication.translate("Form", u"Parameters:", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Aquifer: ", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"BH:", None))
        self.label_monitoring_date_from.setText(QCoreApplication.translate("Form", u"From:", None))
        self.date_monitoring_from.setDisplayFormat(QCoreApplication.translate("Form", u"yyyy-MM-dd", None))
        self.label_monitoring_date_to.setText(QCoreApplication.translate("Form", u"To:", None))
        self.date_monitoring_to.setDisplayFormat(QCoreApplication.translate("Form", u"yyyy-MM-dd", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"Generate Chart", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"Save Chart", None))
        self.monitoring_chart_placeholder.setStyleSheet("")
        self.monitoring_chart_placeholder.setText(QCoreApplication.translate("Form", u"Load files then generate charts", None))
        self.monitoringSubTabs.setTabText(self.monitoringSubTabs.indexOf(self.tab_monitoring_visualize), QCoreApplication.translate("Form", u"Visualize", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_borehole_monitoring), QCoreApplication.translate("Form", u"Borehole Monitoring", None))
        self.label_pcd_folder.setText(QCoreApplication.translate("Form", u"Folder with PCD monitoring Excel files:", None))
        self.pcd_folder_path.setPlaceholderText(QCoreApplication.translate("Form", u"Choose a folder to auto-load and preview PCD monitoring data", None))
        self.pushButton_7.setText(QCoreApplication.translate("Form", u"Choose Folder", None))
        self.label_pcd_autoload.setStyleSheet("")
        self.label_pcd_autoload.setText(QCoreApplication.translate("Form", u"Auto-loads: date + monitoring point + parameters", None))
        self.label_pcd_point.setText(QCoreApplication.translate("Form", u"Monitoring Point:", None))
        self.pcd_point_filter.setItemText(0, QCoreApplication.translate("Form", u"All", None))

        self.pcdSubTabs.setTabText(self.pcdSubTabs.indexOf(self.tab_pcd_upload), QCoreApplication.translate("Form", u"Upload & Preview", None))
        self.label_pcd_chart_type.setText(QCoreApplication.translate("Form", u"Chart Type:", None))
        self.pcd_chart_type.setItemText(0, QCoreApplication.translate("Form", u"Line", None))
        self.pcd_chart_type.setItemText(1, QCoreApplication.translate("Form", u"Bar", None))

        self.label_4.setText(QCoreApplication.translate("Form", u"Parameter: ", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Point:", None))
        self.pushButton_8.setText(QCoreApplication.translate("Form", u"Generate Chart", None))
        self.pushButton_9.setText(QCoreApplication.translate("Form", u"Save Chart", None))
        self.pcd_chart_placeholder.setStyleSheet("")
        self.pcd_chart_placeholder.setText(QCoreApplication.translate("Form", u"Load files then generate charts", None))
        self.pcdSubTabs.setTabText(self.pcdSubTabs.indexOf(self.tab_pcd_visualize), QCoreApplication.translate("Form", u"Visualize", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_pcd_monitoring), QCoreApplication.translate("Form", u"PCD Monitoring", None))
    # retranslateUi



