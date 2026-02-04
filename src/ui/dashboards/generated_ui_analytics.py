# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'analytics.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1196, 800)
        Form.setStyleSheet(u"QWidget#Form {\n"
"    background-color: #F5F6F7;\n"
"}\n"
"\n"
"QLabel#label_title{\n"
"	font:16px;\n"
"	font-weight:bold;\n"
"}\n"
"\n"
"QLabel#label_subtitle{\n"
"	color: rgb(102, 102, 102);\n"
"	font: Size 9;\n"
"}")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_title = QLabel(Form)
        self.label_title.setObjectName(u"label_title")
        self.label_title.setMinimumSize(QSize(0, 40))
        self.label_title.setMaximumSize(QSize(16777215, 20))
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout.addWidget(self.label_title)

        self.label_subtitle = QLabel(Form)
        self.label_subtitle.setObjectName(u"label_subtitle")
        self.label_subtitle.setMaximumSize(QSize(16777215, 20))

        self.verticalLayout.addWidget(self.label_subtitle)

        self.frame_datasource_header = QFrame(Form)
        self.frame_datasource_header.setObjectName(u"frame_datasource_header")
        self.frame_datasource_header.setMaximumSize(QSize(16777215, 50))
        self.frame_datasource_header.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_datasource_header.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_header_datasource = QHBoxLayout(self.frame_datasource_header)
        self.horizontalLayout_header_datasource.setObjectName(u"horizontalLayout_header_datasource")
        self.horizontalLayout_header_datasource.setContentsMargins(5, 0, 10, 0)
        self.pushButton = QPushButton(self.frame_datasource_header)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMaximumSize(QSize(200, 40))
        self.pushButton.setStyleSheet(u"QPushButton {\n"
"\n"
"	color: black;\n"
"	border: none;\n"
"	border-radius: 4px;\n"
"	font-weight: bold;\n"
"	padding: 5px 10px;\n"
"}\n"
"QPushButton:hover {\n"
"	background-color: rgb(10, 50, 120);\n"
"}")
        icon = QIcon()
        icon.addFile(u":/icons/folder.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QSize(24, 24))
        self.pushButton.setCheckable(True)

        self.horizontalLayout_header_datasource.addWidget(self.pushButton)

        self.records_loaded_2 = QLabel(self.frame_datasource_header)
        self.records_loaded_2.setObjectName(u"records_loaded_2")

        self.horizontalLayout_header_datasource.addWidget(self.records_loaded_2)

        self.sources_loaded_2 = QLabel(self.frame_datasource_header)
        self.sources_loaded_2.setObjectName(u"sources_loaded_2")

        self.horizontalLayout_header_datasource.addWidget(self.sources_loaded_2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_header_datasource.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.frame_datasource_header)

        self.data_source_frame_uncollapsed = QFrame(Form)
        self.data_source_frame_uncollapsed.setObjectName(u"data_source_frame_uncollapsed")
        self.data_source_frame_uncollapsed.setMaximumSize(QSize(16777215, 120))
        self.data_source_frame_uncollapsed.setFrameShape(QFrame.Shape.StyledPanel)
        self.data_source_frame_uncollapsed.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_frame_content = QVBoxLayout(self.data_source_frame_uncollapsed)
        self.verticalLayout_frame_content.setObjectName(u"verticalLayout_frame_content")
        self.verticalLayout_frame_content.setContentsMargins(10, 5, 10, 5)
        self.excel_filemeter_readings_label = QLabel(self.data_source_frame_uncollapsed)
        self.excel_filemeter_readings_label.setObjectName(u"excel_filemeter_readings_label")

        self.verticalLayout_frame_content.addWidget(self.excel_filemeter_readings_label)

        self.horizontalLayout_file_select = QHBoxLayout()
        self.horizontalLayout_file_select.setObjectName(u"horizontalLayout_file_select")
        self.line_edit_folder_path = QLineEdit(self.data_source_frame_uncollapsed)
        self.line_edit_folder_path.setObjectName(u"line_edit_folder_path")
        self.line_edit_folder_path.setMaximumSize(QSize(16777215, 35))

        self.horizontalLayout_file_select.addWidget(self.line_edit_folder_path)

        self.select_file_button = QPushButton(self.data_source_frame_uncollapsed)
        self.select_file_button.setObjectName(u"select_file_button")
        self.select_file_button.setMinimumSize(QSize(130, 30))
        self.select_file_button.setMaximumSize(QSize(140, 36))
        self.select_file_button.setStyleSheet(u"QPushButton#select_file_button {\n"
"	background-color: rgb(8, 201, 255);\n"
"	color: white;\n"
"	border: none;\n"
"	border-radius: 4px;\n"
"	font-weight: bold;\n"
"	padding: 5px;\n"
"}\n"
"QPushButton#select_file_button:hover {\n"
"	background-color: rgb(0, 175, 230);\n"
"}\n"
"QPushButton#select_file_button:pressed {\n"
"	background-color: rgb(0, 150, 200);\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u":/icons/folder_open.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.select_file_button.setIcon(icon1)
        self.select_file_button.setIconSize(QSize(18, 18))

        self.horizontalLayout_file_select.addWidget(self.select_file_button)


        self.verticalLayout_frame_content.addLayout(self.horizontalLayout_file_select)

        self.auto_loads_label = QLabel(self.data_source_frame_uncollapsed)
        self.auto_loads_label.setObjectName(u"auto_loads_label")

        self.verticalLayout_frame_content.addWidget(self.auto_loads_label)

        self.verticalSpacer_file_section = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_frame_content.addItem(self.verticalSpacer_file_section)


        self.verticalLayout.addWidget(self.data_source_frame_uncollapsed)

        self.frame_3 = QFrame(Form)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setMinimumSize(QSize(0, 45))
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.layoutWidget = QWidget(self.frame_3)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 10, 1181, 28))
        self.horizontalLayout_chart_header_2 = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_chart_header_2.setSpacing(0)
        self.horizontalLayout_chart_header_2.setObjectName(u"horizontalLayout_chart_header_2")
        self.horizontalLayout_chart_header_2.setContentsMargins(0, 0, 0, 0)
        self.chart_options_logo_2 = QPushButton(self.layoutWidget)
        self.chart_options_logo_2.setObjectName(u"chart_options_logo_2")
        self.chart_options_logo_2.setMaximumSize(QSize(120, 35))
        self.chart_options_logo_2.setStyleSheet(u"QPushButton#chart_options_logo_2{\n"
"	border:none;\n"
"	font-weight: bold;\n"
"}")
        icon2 = QIcon()
        icon2.addFile(u":/icons/charts.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.chart_options_logo_2.setIcon(icon2)
        self.chart_options_logo_2.setCheckable(True)

        self.horizontalLayout_chart_header_2.addWidget(self.chart_options_logo_2)

        self.label_5 = QLabel(self.layoutWidget)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_chart_header_2.addWidget(self.label_5)

        self.horizontalSpacer_chart_header_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_chart_header_2.addItem(self.horizontalSpacer_chart_header_2)


        self.verticalLayout.addWidget(self.frame_3)

        self.frame_2 = QFrame(Form)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_chart_options = QVBoxLayout(self.frame_2)
        self.verticalLayout_chart_options.setObjectName(u"verticalLayout_chart_options")
        self.verticalLayout_chart_options.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout_chart_type = QHBoxLayout()
        self.horizontalLayout_chart_type.setObjectName(u"horizontalLayout_chart_type")
        self.label_chart_type = QLabel(self.frame_2)
        self.label_chart_type.setObjectName(u"label_chart_type")

        self.horizontalLayout_chart_type.addWidget(self.label_chart_type)

        self.charts_options = QComboBox(self.frame_2)
        self.charts_options.addItem("")
        self.charts_options.addItem("")
        self.charts_options.addItem("")
        self.charts_options.setObjectName(u"charts_options")
        self.charts_options.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout_chart_type.addWidget(self.charts_options)

        self.water_source_label = QLabel(self.frame_2)
        self.water_source_label.setObjectName(u"water_source_label")

        self.horizontalLayout_chart_type.addWidget(self.water_source_label)

        self.water_source_options = QComboBox(self.frame_2)
        self.water_source_options.addItem("")
        self.water_source_options.setObjectName(u"water_source_options")
        self.water_source_options.setMaximumSize(QSize(180, 16777215))

        self.horizontalLayout_chart_type.addWidget(self.water_source_options)

        self.horizontalSpacer_chart_type = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_chart_type.addItem(self.horizontalSpacer_chart_type)


        self.verticalLayout_chart_options.addLayout(self.horizontalLayout_chart_type)

        self.horizontalLayout_date_range = QHBoxLayout()
        self.horizontalLayout_date_range.setObjectName(u"horizontalLayout_date_range")
        self.date_range_label = QLabel(self.frame_2)
        self.date_range_label.setObjectName(u"date_range_label")

        self.horizontalLayout_date_range.addWidget(self.date_range_label)

        self.label_from = QLabel(self.frame_2)
        self.label_from.setObjectName(u"label_from")

        self.horizontalLayout_date_range.addWidget(self.label_from)

        self.year_from = QComboBox(self.frame_2)
        self.year_from.setObjectName(u"year_from")
        self.year_from.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_date_range.addWidget(self.year_from)

        self.month_label = QLabel(self.frame_2)
        self.month_label.setObjectName(u"month_label")

        self.horizontalLayout_date_range.addWidget(self.month_label)

        self.month_from = QComboBox(self.frame_2)
        self.month_from.setObjectName(u"month_from")
        self.month_from.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_date_range.addWidget(self.month_from)

        self.label_to_year = QLabel(self.frame_2)
        self.label_to_year.setObjectName(u"label_to_year")

        self.horizontalLayout_date_range.addWidget(self.label_to_year)

        self.year_to = QComboBox(self.frame_2)
        self.year_to.setObjectName(u"year_to")
        self.year_to.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_date_range.addWidget(self.year_to)

        self.to_month_label = QLabel(self.frame_2)
        self.to_month_label.setObjectName(u"to_month_label")

        self.horizontalLayout_date_range.addWidget(self.to_month_label)

        self.month_to = QComboBox(self.frame_2)
        self.month_to.setObjectName(u"month_to")
        self.month_to.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_date_range.addWidget(self.month_to)

        self.horizontalSpacer_date_range = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_date_range.addItem(self.horizontalSpacer_date_range)


        self.verticalLayout_chart_options.addLayout(self.horizontalLayout_date_range)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.generate_chart = QPushButton(self.frame_2)
        self.generate_chart.setObjectName(u"generate_chart")
        self.generate_chart.setMinimumSize(QSize(120, 25))
        self.generate_chart.setMaximumSize(QSize(180, 35))
        self.generate_chart.setStyleSheet(u"QPushButton#generate_chart{\n"
"	color:white;\n"
"	background-color:rgb(51, 186, 28);\n"
"	border: none;\n"
"	border-radius: 4px;\n"
"	font-weight: bold;\n"
"}")
        icon3 = QIcon()
        icon3.addFile(u":/icons/chart_white.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.generate_chart.setIcon(icon3)

        self.horizontalLayout_buttons.addWidget(self.generate_chart)

        self.save_chart = QPushButton(self.frame_2)
        self.save_chart.setObjectName(u"save_chart")
        self.save_chart.setMinimumSize(QSize(120, 25))
        self.save_chart.setMaximumSize(QSize(150, 40))
        self.save_chart.setStyleSheet(u"QPushButton#save_chart{\n"
"	color:white;\n"
"	background-color: rgb(42, 150, 232);\n"
"	border: none;\n"
"	border-radius: 4px;\n"
"	font-weight: bold;\n"
"}")
        icon4 = QIcon()
        icon4.addFile(u":/icons/save_white.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.save_chart.setIcon(icon4)

        self.horizontalLayout_buttons.addWidget(self.save_chart)

        self.horizontalSpacer_buttons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer_buttons)


        self.verticalLayout_chart_options.addLayout(self.horizontalLayout_buttons)

        self.verticalSpacer_chart_options = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_chart_options.addItem(self.verticalSpacer_chart_options)


        self.verticalLayout.addWidget(self.frame_2)

        self.chartLayout = QVBoxLayout()
        self.chartLayout.setObjectName(u"chartLayout")
        self.label_chartplaceholder = QLabel(Form)
        self.label_chartplaceholder.setObjectName(u"label_chartplaceholder")
        self.label_chartplaceholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chartLayout.addWidget(self.label_chartplaceholder)


        self.verticalLayout.addLayout(self.chartLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(Form)
        self.pushButton.toggled.connect(self.data_source_frame_uncollapsed.setVisible)
        self.chart_options_logo_2.toggled.connect(self.frame_2.setVisible)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_title.setText(QCoreApplication.translate("Form", u"Analytics & Trends", None))
        self.label_subtitle.setText(QCoreApplication.translate("Form", u"Water source trend analysis abd Visualization", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"\u25b6 DataSource File", None))
        self.records_loaded_2.setText(QCoreApplication.translate("Form", u"238 records", None))
        self.sources_loaded_2.setText(QCoreApplication.translate("Form", u"43 sources loaded", None))
        self.excel_filemeter_readings_label.setText(QCoreApplication.translate("Form", u"Excel file with Meter Readings:", None))
        self.select_file_button.setText(QCoreApplication.translate("Form", u"Select File", None))
        self.auto_loads_label.setStyleSheet(QCoreApplication.translate("Form", u"color: rgb(153, 153, 153); font-size: 9pt;", None))
        self.auto_loads_label.setText(QCoreApplication.translate("Form", u"Auto-loads: columns from row 3, data from row 5 onwards", None))
        self.chart_options_logo_2.setText(QCoreApplication.translate("Form", u"Chart Options", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"(click to collapse)", None))
        self.label_chart_type.setText(QCoreApplication.translate("Form", u"Chart Type:", None))
        self.charts_options.setItemText(0, QCoreApplication.translate("Form", u"Line Chart", None))
        self.charts_options.setItemText(1, QCoreApplication.translate("Form", u"Bar Chart", None))
        self.charts_options.setItemText(2, QCoreApplication.translate("Form", u"Box Plot", None))

        self.water_source_label.setText(QCoreApplication.translate("Form", u"Water Source:", None))
        self.water_source_options.setItemText(0, QCoreApplication.translate("Form", u"Tonnes Milled", None))

        self.date_range_label.setText(QCoreApplication.translate("Form", u"Date Range:", None))
        self.label_from.setText(QCoreApplication.translate("Form", u"From  Year:", None))
        self.month_label.setText(QCoreApplication.translate("Form", u"Month:", None))
        self.label_to_year.setText(QCoreApplication.translate("Form", u"To Year:", None))
        self.to_month_label.setText(QCoreApplication.translate("Form", u"Month:", None))
        self.generate_chart.setText(QCoreApplication.translate("Form", u"Generate Chart", None))
        self.save_chart.setText(QCoreApplication.translate("Form", u"Save Chart", None))
        self.label_chartplaceholder.setStyleSheet(QCoreApplication.translate("Form", u"color: rgb(153, 153, 153); font-size: 12pt;", None))
        self.label_chartplaceholder.setText(QCoreApplication.translate("Form", u"Select Excel file and generate chart to view results", None))
    # retranslateUi

