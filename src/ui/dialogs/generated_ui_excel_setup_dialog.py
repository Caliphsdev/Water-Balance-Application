# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'excel_setup_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ExcelSetupDialog(object):
    def setupUi(self, ExcelSetupDialog):
        if not ExcelSetupDialog.objectName():
            ExcelSetupDialog.setObjectName(u"ExcelSetupDialog")
        ExcelSetupDialog.resize(700, 500)
        ExcelSetupDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(ExcelSetupDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_instruction = QLabel(ExcelSetupDialog)
        self.label_instruction.setObjectName(u"label_instruction")

        self.verticalLayout.addWidget(self.label_instruction)

        self.groupBox_excel_file = QGroupBox(ExcelSetupDialog)
        self.groupBox_excel_file.setObjectName(u"groupBox_excel_file")
        self.formLayout_file = QFormLayout(self.groupBox_excel_file)
        self.formLayout_file.setObjectName(u"formLayout_file")
        self.label_file_path = QLabel(self.groupBox_excel_file)
        self.label_file_path.setObjectName(u"label_file_path")

        self.formLayout_file.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_file_path)

        self.horizontalLayout_path = QHBoxLayout()
        self.horizontalLayout_path.setObjectName(u"horizontalLayout_path")
        self.input_file_path = QLineEdit(self.groupBox_excel_file)
        self.input_file_path.setObjectName(u"input_file_path")
        self.input_file_path.setReadOnly(True)

        self.horizontalLayout_path.addWidget(self.input_file_path)

        self.btn_browse = QPushButton(self.groupBox_excel_file)
        self.btn_browse.setObjectName(u"btn_browse")
        self.btn_browse.setMaximumWidth(100)

        self.horizontalLayout_path.addWidget(self.btn_browse)


        self.formLayout_file.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_path)

        self.label_status = QLabel(self.groupBox_excel_file)
        self.label_status.setObjectName(u"label_status")

        self.formLayout_file.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_status)

        self.value_status = QLabel(self.groupBox_excel_file)
        self.value_status.setObjectName(u"value_status")

        self.formLayout_file.setWidget(1, QFormLayout.ItemRole.FieldRole, self.value_status)


        self.verticalLayout.addWidget(self.groupBox_excel_file)

        self.groupBox_mapping = QGroupBox(ExcelSetupDialog)
        self.groupBox_mapping.setObjectName(u"groupBox_mapping")
        self.verticalLayout_table = QVBoxLayout(self.groupBox_mapping)
        self.verticalLayout_table.setObjectName(u"verticalLayout_table")
        self.table_mapping = QTableWidget(self.groupBox_mapping)
        if (self.table_mapping.columnCount() < 4):
            self.table_mapping.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_mapping.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_mapping.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_mapping.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_mapping.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table_mapping.setObjectName(u"table_mapping")
        self.table_mapping.setColumnCount(4)
        self.table_mapping.setRowCount(0)
        self.table_mapping.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout_table.addWidget(self.table_mapping)

        self.horizontalLayout_mapping_buttons = QHBoxLayout()
        self.horizontalLayout_mapping_buttons.setObjectName(u"horizontalLayout_mapping_buttons")
        self.btn_auto_map_all = QPushButton(self.groupBox_mapping)
        self.btn_auto_map_all.setObjectName(u"btn_auto_map_all")

        self.horizontalLayout_mapping_buttons.addWidget(self.btn_auto_map_all)

        self.btn_clear_mapping = QPushButton(self.groupBox_mapping)
        self.btn_clear_mapping.setObjectName(u"btn_clear_mapping")

        self.horizontalLayout_mapping_buttons.addWidget(self.btn_clear_mapping)

        self.btn_manage_columns = QPushButton(self.groupBox_mapping)
        self.btn_manage_columns.setObjectName(u"btn_manage_columns")

        self.horizontalLayout_mapping_buttons.addWidget(self.btn_manage_columns)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_mapping_buttons.addItem(self.horizontalSpacer)


        self.verticalLayout_table.addLayout(self.horizontalLayout_mapping_buttons)


        self.verticalLayout.addWidget(self.groupBox_mapping)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.horizontalSpacer_buttons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer_buttons)

        self.btn_save = QPushButton(ExcelSetupDialog)
        self.btn_save.setObjectName(u"btn_save")
        self.btn_save.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_save)

        self.btn_cancel = QPushButton(ExcelSetupDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(ExcelSetupDialog)
        self.btn_save.clicked.connect(ExcelSetupDialog.accept)
        self.btn_cancel.clicked.connect(ExcelSetupDialog.reject)

        self.btn_save.setDefault(True)


        QMetaObject.connectSlotsByName(ExcelSetupDialog)
    # setupUi

    def retranslateUi(self, ExcelSetupDialog):
        ExcelSetupDialog.setWindowTitle(QCoreApplication.translate("ExcelSetupDialog", u"Excel Setup - Flow Volume Mapping", None))
        self.label_instruction.setText(QCoreApplication.translate("ExcelSetupDialog", u"Configure Excel file location and map flow lines to Excel columns", None))
        self.label_instruction.setStyleSheet(QCoreApplication.translate("ExcelSetupDialog", u"QLabel { font-weight: bold; font-size: 12px; margin-bottom: 10px; }", None))
        self.groupBox_excel_file.setTitle(QCoreApplication.translate("ExcelSetupDialog", u"Excel File Configuration", None))
        self.label_file_path.setText(QCoreApplication.translate("ExcelSetupDialog", u"Excel File Path:", None))
        self.btn_browse.setText(QCoreApplication.translate("ExcelSetupDialog", u"Browse...", None))
        self.label_status.setText(QCoreApplication.translate("ExcelSetupDialog", u"Status:", None))
        self.value_status.setStyleSheet(QCoreApplication.translate("ExcelSetupDialog", u"QLabel { color: #FF6B6B; }", None))
        self.groupBox_mapping.setTitle(QCoreApplication.translate("ExcelSetupDialog", u"Flow to Excel Column Mapping", None))
        ___qtablewidgetitem = self.table_mapping.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ExcelSetupDialog", u"From \u2192 To", None));
        ___qtablewidgetitem1 = self.table_mapping.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ExcelSetupDialog", u"Excel Sheet", None));
        ___qtablewidgetitem2 = self.table_mapping.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("ExcelSetupDialog", u"Column Name", None));
        ___qtablewidgetitem3 = self.table_mapping.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("ExcelSetupDialog", u"Status", None));
        self.btn_auto_map_all.setText(QCoreApplication.translate("ExcelSetupDialog", u"Auto-Map All Flows", None))
        self.btn_clear_mapping.setText(QCoreApplication.translate("ExcelSetupDialog", u"Clear All", None))
        self.btn_manage_columns.setText(QCoreApplication.translate("ExcelSetupDialog", u"Manage Columns", None))
        self.btn_save.setText(QCoreApplication.translate("ExcelSetupDialog", u"Save", None))
        self.btn_cancel.setText(QCoreApplication.translate("ExcelSetupDialog", u"Cancel", None))
    # retranslateUi

