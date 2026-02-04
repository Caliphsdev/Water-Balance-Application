# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'flow_diagram.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGraphicsView,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QWidget)
import ui.resources.resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1153, 819)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.graphicsView = QGraphicsView(Form)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        self.graphicsView.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.gridLayout.addWidget(self.graphicsView, 1, 0, 1, 1)

        self.frame_2 = QFrame(Form)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(0, 80))
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.frame_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalSpacer_4 = QSpacerItem(38, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.total_inflows_label = QLabel(self.frame_2)
        self.total_inflows_label.setObjectName(u"total_inflows_label")
        self.total_inflows_label.setStyleSheet(u"QLabel{\n"
"border: 2px solid black;\n"
"}")

        self.horizontalLayout_5.addWidget(self.total_inflows_label)

        self.total_inflows_value = QLabel(self.frame_2)
        self.total_inflows_value.setObjectName(u"total_inflows_value")

        self.horizontalLayout_5.addWidget(self.total_inflows_value)

        self.unit = QLabel(self.frame_2)
        self.unit.setObjectName(u"unit")

        self.horizontalLayout_5.addWidget(self.unit)


        self.horizontalLayout_9.addLayout(self.horizontalLayout_5)

        self.horizontalSpacer_10 = QSpacerItem(268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_10)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.recirculation_value = QLabel(self.frame_2)
        self.recirculation_value.setObjectName(u"recirculation_value")

        self.horizontalLayout_6.addWidget(self.recirculation_value)

        self.unit_2 = QLabel(self.frame_2)
        self.unit_2.setObjectName(u"unit_2")

        self.horizontalLayout_6.addWidget(self.unit_2)


        self.horizontalLayout_9.addLayout(self.horizontalLayout_6)

        self.horizontalSpacer_9 = QSpacerItem(318, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_9)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.total_outflows_label = QLabel(self.frame_2)
        self.total_outflows_label.setObjectName(u"total_outflows_label")
        self.total_outflows_label.setStyleSheet(u"QLabel{\n"
"border: 2px solid black;\n"
"}")

        self.horizontalLayout_7.addWidget(self.total_outflows_label)

        self.total_outflows_value = QLabel(self.frame_2)
        self.total_outflows_value.setObjectName(u"total_outflows_value")

        self.horizontalLayout_7.addWidget(self.total_outflows_value)

        self.unit_3 = QLabel(self.frame_2)
        self.unit_3.setObjectName(u"unit_3")

        self.horizontalLayout_7.addWidget(self.unit_3)


        self.horizontalLayout_9.addLayout(self.horizontalLayout_7)

        self.horizontalSpacer_6 = QSpacerItem(38, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_6)


        self.gridLayout_3.addLayout(self.horizontalLayout_9, 0, 0, 1, 1)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalSpacer_11 = QSpacerItem(468, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_11)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setSpacing(10)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.balance_check_label = QLabel(self.frame_2)
        self.balance_check_label.setObjectName(u"balance_check_label")

        self.horizontalLayout_8.addWidget(self.balance_check_label)

        self.balance_check_value = QLabel(self.frame_2)
        self.balance_check_value.setObjectName(u"balance_check_value")

        self.horizontalLayout_8.addWidget(self.balance_check_value)

        self.unit_4 = QLabel(self.frame_2)
        self.unit_4.setObjectName(u"unit_4")

        self.horizontalLayout_8.addWidget(self.unit_4)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_8)

        self.horizontalSpacer_12 = QSpacerItem(528, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_12)


        self.gridLayout_3.addLayout(self.horizontalLayout_10, 1, 0, 1, 1)


        self.gridLayout.addWidget(self.frame_2, 3, 0, 1, 1)

        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 0))
        self.frame.setStyleSheet(u"QFrame{\n"
"	background-color: rgb(63, 63, 94);\n"
"	color: rgb(255, 255, 255);\n"
"}")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalSpacer_5 = QSpacerItem(769, 25, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_5, 2, 1, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_7 = QSpacerItem(398, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_7)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(0, 20))
        self.label.setMaximumSize(QSize(16777215, 25))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.label)

        self.horizontalSpacer_8 = QSpacerItem(478, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_8)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 0, 1, 2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(65, -1, -1, -1)
        self.zoom_in_button = QPushButton(self.frame)
        self.zoom_in_button.setObjectName(u"zoom_in_button")

        self.horizontalLayout_3.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton(self.frame)
        self.zoom_out_button.setObjectName(u"zoom_out_button")

        self.horizontalLayout_3.addWidget(self.zoom_out_button)

        self.horizontalSpacer = QSpacerItem(18, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.save_diagram_button = QPushButton(self.frame)
        self.save_diagram_button.setObjectName(u"save_diagram_button")

        self.horizontalLayout_3.addWidget(self.save_diagram_button)


        self.gridLayout_2.addLayout(self.horizontalLayout_3, 2, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(20, 20))
        self.label_3.setMaximumSize(QSize(20, 20))
        self.label_3.setPixmap(QPixmap(u":/icons/flow_line.svg"))
        self.label_3.setScaledContents(True)

        self.horizontalLayout.addWidget(self.label_3)

        self.label_2 = QLabel(self.frame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)

        self.Draw_button = QPushButton(self.frame)
        self.Draw_button.setObjectName(u"Draw_button")

        self.horizontalLayout.addWidget(self.Draw_button)

        self.edit_flows_button = QPushButton(self.frame)
        self.edit_flows_button.setObjectName(u"edit_flows_button")

        self.horizontalLayout.addWidget(self.edit_flows_button)

        self.delete_folws_button = QPushButton(self.frame)
        self.delete_folws_button.setObjectName(u"delete_folws_button")

        self.horizontalLayout.addWidget(self.delete_folws_button)

        self.line = QFrame(self.frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.VLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMinimumSize(QSize(20, 20))
        self.label_4.setMaximumSize(QSize(20, 20))
        self.label_4.setPixmap(QPixmap(u":/icons/nodes.svg"))
        self.label_4.setScaledContents(True)

        self.horizontalLayout.addWidget(self.label_4)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout.addWidget(self.label_5)

        self.Add_button = QPushButton(self.frame)
        self.Add_button.setObjectName(u"Add_button")

        self.horizontalLayout.addWidget(self.Add_button)

        self.edit_nodes_button = QPushButton(self.frame)
        self.edit_nodes_button.setObjectName(u"edit_nodes_button")

        self.horizontalLayout.addWidget(self.edit_nodes_button)

        self.pushButton_6 = QPushButton(self.frame)
        self.pushButton_6.setObjectName(u"pushButton_6")

        self.horizontalLayout.addWidget(self.pushButton_6)

        self.lock_nodes_button = QPushButton(self.frame)
        self.lock_nodes_button.setObjectName(u"lock_nodes_button")

        self.horizontalLayout.addWidget(self.lock_nodes_button)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMinimumSize(QSize(20, 20))
        self.label_6.setMaximumSize(QSize(20, 20))
        self.label_6.setPixmap(QPixmap(u":/icons/excel.svg"))
        self.label_6.setScaledContents(True)

        self.horizontalLayout_4.addWidget(self.label_6)

        self.label_7 = QLabel(self.frame)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_4.addWidget(self.label_7)

        self.label_8 = QLabel(self.frame)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_4.addWidget(self.label_8)

        self.comboBox_filter_year = QComboBox(self.frame)
        self.comboBox_filter_year.setObjectName(u"comboBox_filter_year")

        self.horizontalLayout_4.addWidget(self.comboBox_filter_year)

        self.label_9 = QLabel(self.frame)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_4.addWidget(self.label_9)

        self.comboBox_filter_month = QComboBox(self.frame)
        self.comboBox_filter_month.setObjectName(u"comboBox_filter_month")

        self.horizontalLayout_4.addWidget(self.comboBox_filter_month)

        self.load_excel_button = QPushButton(self.frame)
        self.load_excel_button.setObjectName(u"load_excel_button")

        self.horizontalLayout_4.addWidget(self.load_excel_button)

        self.excel_setup_button = QPushButton(self.frame)
        self.excel_setup_button.setObjectName(u"excel_setup_button")

        self.horizontalLayout_4.addWidget(self.excel_setup_button)

        self.balance_check_button = QPushButton(self.frame)
        self.balance_check_button.setObjectName(u"balance_check_button")

        self.horizontalLayout_4.addWidget(self.balance_check_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.gridLayout_2.addLayout(self.horizontalLayout_4, 3, 0, 1, 2)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Flow Diagram", None))
        self.total_inflows_label.setText(QCoreApplication.translate("Form", u"Inflows Total:", None))
        self.total_inflows_value.setText(QCoreApplication.translate("Form", u"5 157 069", None))
        self.unit.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.recirculation_value.setText(QCoreApplication.translate("Form", u"11 218", None))
        self.unit_2.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.total_outflows_label.setText(QCoreApplication.translate("Form", u"Outflows Total:", None))
        self.total_outflows_value.setText(QCoreApplication.translate("Form", u"5 128 782", None))
        self.unit_3.setText(QCoreApplication.translate("Form", u"m\u00b3", None))
        self.balance_check_label.setText(QCoreApplication.translate("Form", u"Balance Check", None))
        self.balance_check_value.setText(QCoreApplication.translate("Form", u"0", None))
        self.unit_4.setText(QCoreApplication.translate("Form", u"%", None))
        self.label.setText(QCoreApplication.translate("Form", u"Flow Diagram - Manual Flow Line Drawing", None))
        self.zoom_in_button.setText(QCoreApplication.translate("Form", u"Zoom In", None))
        self.zoom_out_button.setText(QCoreApplication.translate("Form", u"Zoom Out", None))
        self.save_diagram_button.setText(QCoreApplication.translate("Form", u"Save Diagram", None))
        self.label_3.setText("")
        self.label_2.setText(QCoreApplication.translate("Form", u"Flows:", None))
        self.Draw_button.setText(QCoreApplication.translate("Form", u"Draw", None))
        self.edit_flows_button.setText(QCoreApplication.translate("Form", u"Edit", None))
        self.delete_folws_button.setText(QCoreApplication.translate("Form", u"Delete", None))
        self.label_4.setText("")
        self.label_5.setText(QCoreApplication.translate("Form", u"Nodes: ", None))
        self.Add_button.setText(QCoreApplication.translate("Form", u"Add", None))
        self.edit_nodes_button.setText(QCoreApplication.translate("Form", u"Edit", None))
        self.pushButton_6.setText(QCoreApplication.translate("Form", u"Delete", None))
        self.lock_nodes_button.setText(QCoreApplication.translate("Form", u"Lock", None))
        self.label_6.setText("")
        self.label_7.setText(QCoreApplication.translate("Form", u"Load Data:", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"Year:", None))
        self.label_9.setText(QCoreApplication.translate("Form", u"Month: ", None))
        self.load_excel_button.setText(QCoreApplication.translate("Form", u"Load Excel", None))
        self.excel_setup_button.setText(QCoreApplication.translate("Form", u"Excel Setup", None))
        self.balance_check_button.setText(QCoreApplication.translate("Form", u"Balance Check", None))
    # retranslateUi

