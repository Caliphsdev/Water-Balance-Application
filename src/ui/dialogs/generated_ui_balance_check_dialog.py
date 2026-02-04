# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'balance_check_dialog.ui'
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
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_BalanceCheckDialog(object):
    def setupUi(self, BalanceCheckDialog):
        if not BalanceCheckDialog.objectName():
            BalanceCheckDialog.setObjectName(u"BalanceCheckDialog")
        BalanceCheckDialog.resize(700, 600)
        BalanceCheckDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(BalanceCheckDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_header = QHBoxLayout()
        self.horizontalLayout_header.setObjectName(u"horizontalLayout_header")
        self.label_area = QLabel(BalanceCheckDialog)
        self.label_area.setObjectName(u"label_area")

        self.horizontalLayout_header.addWidget(self.label_area)

        self.value_area = QLabel(BalanceCheckDialog)
        self.value_area.setObjectName(u"value_area")

        self.horizontalLayout_header.addWidget(self.value_area)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_header.addItem(self.horizontalSpacer)

        self.label_balance_title = QLabel(BalanceCheckDialog)
        self.label_balance_title.setObjectName(u"label_balance_title")

        self.horizontalLayout_header.addWidget(self.label_balance_title)

        self.value_balance = QLabel(BalanceCheckDialog)
        self.value_balance.setObjectName(u"value_balance")

        self.horizontalLayout_header.addWidget(self.value_balance)


        self.verticalLayout.addLayout(self.horizontalLayout_header)

        self.groupBox_categorization = QGroupBox(BalanceCheckDialog)
        self.groupBox_categorization.setObjectName(u"groupBox_categorization")
        self.verticalLayout_table = QVBoxLayout(self.groupBox_categorization)
        self.verticalLayout_table.setObjectName(u"verticalLayout_table")
        self.table_flows = QTableWidget(self.groupBox_categorization)
        if (self.table_flows.columnCount() < 4):
            self.table_flows.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_flows.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_flows.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_flows.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_flows.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table_flows.setObjectName(u"table_flows")
        self.table_flows.setColumnCount(4)
        self.table_flows.setRowCount(0)
        self.table_flows.horizontalHeader().setStretchLastSection(True)

        self.verticalLayout_table.addWidget(self.table_flows)


        self.verticalLayout.addWidget(self.groupBox_categorization)

        self.groupBox_summary = QGroupBox(BalanceCheckDialog)
        self.groupBox_summary.setObjectName(u"groupBox_summary")
        self.formLayout = QFormLayout(self.groupBox_summary)
        self.formLayout.setObjectName(u"formLayout")
        self.label_inflows = QLabel(self.groupBox_summary)
        self.label_inflows.setObjectName(u"label_inflows")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_inflows)

        self.value_inflows = QLabel(self.groupBox_summary)
        self.value_inflows.setObjectName(u"value_inflows")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.value_inflows)

        self.label_outflows = QLabel(self.groupBox_summary)
        self.label_outflows.setObjectName(u"label_outflows")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_outflows)

        self.value_outflows = QLabel(self.groupBox_summary)
        self.value_outflows.setObjectName(u"value_outflows")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.value_outflows)

        self.label_recirculation = QLabel(self.groupBox_summary)
        self.label_recirculation.setObjectName(u"label_recirculation")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_recirculation)

        self.value_recirculation = QLabel(self.groupBox_summary)
        self.value_recirculation.setObjectName(u"value_recirculation")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.value_recirculation)

        self.label_error_pct = QLabel(self.groupBox_summary)
        self.label_error_pct.setObjectName(u"label_error_pct")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_error_pct)

        self.value_error_pct = QLabel(self.groupBox_summary)
        self.value_error_pct.setObjectName(u"value_error_pct")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.value_error_pct)


        self.verticalLayout.addWidget(self.groupBox_summary)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.horizontalSpacer_buttons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer_buttons)

        self.btn_save_categories = QPushButton(BalanceCheckDialog)
        self.btn_save_categories.setObjectName(u"btn_save_categories")
        self.btn_save_categories.setMinimumWidth(150)

        self.horizontalLayout_buttons.addWidget(self.btn_save_categories)

        self.btn_close = QPushButton(BalanceCheckDialog)
        self.btn_close.setObjectName(u"btn_close")
        self.btn_close.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_close)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(BalanceCheckDialog)
        self.btn_close.clicked.connect(BalanceCheckDialog.accept)

        self.btn_close.setDefault(True)


        QMetaObject.connectSlotsByName(BalanceCheckDialog)
    # setupUi

    def retranslateUi(self, BalanceCheckDialog):
        BalanceCheckDialog.setWindowTitle(QCoreApplication.translate("BalanceCheckDialog", u"Water Balance Check", None))
        self.label_area.setText(QCoreApplication.translate("BalanceCheckDialog", u"Area:", None))
        self.label_area.setStyleSheet(QCoreApplication.translate("BalanceCheckDialog", u"QLabel { font-weight: bold; }", None))
        self.value_area.setText(QCoreApplication.translate("BalanceCheckDialog", u"[Area Name]", None))
        self.label_balance_title.setText(QCoreApplication.translate("BalanceCheckDialog", u"Balance Closure:", None))
        self.label_balance_title.setStyleSheet(QCoreApplication.translate("BalanceCheckDialog", u"QLabel { font-weight: bold; }", None))
        self.value_balance.setText(QCoreApplication.translate("BalanceCheckDialog", u"0.0 %", None))
        self.value_balance.setStyleSheet(QCoreApplication.translate("BalanceCheckDialog", u"QLabel { font-size: 14px; font-weight: bold; color: #22AA22; }", None))
        self.groupBox_categorization.setTitle(QCoreApplication.translate("BalanceCheckDialog", u"Flow Categorization", None))
        ___qtablewidgetitem = self.table_flows.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("BalanceCheckDialog", u"From", None));
        ___qtablewidgetitem1 = self.table_flows.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("BalanceCheckDialog", u"To", None));
        ___qtablewidgetitem2 = self.table_flows.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("BalanceCheckDialog", u"Volume (m\u00b3)", None));
        ___qtablewidgetitem3 = self.table_flows.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("BalanceCheckDialog", u"Category", None));
        self.groupBox_summary.setTitle(QCoreApplication.translate("BalanceCheckDialog", u"Balance Summary", None))
        self.label_inflows.setText(QCoreApplication.translate("BalanceCheckDialog", u"Total Inflows:", None))
        self.value_inflows.setText(QCoreApplication.translate("BalanceCheckDialog", u"0 m\u00b3", None))
        self.label_outflows.setText(QCoreApplication.translate("BalanceCheckDialog", u"Total Outflows:", None))
        self.value_outflows.setText(QCoreApplication.translate("BalanceCheckDialog", u"0 m\u00b3", None))
        self.label_recirculation.setText(QCoreApplication.translate("BalanceCheckDialog", u"Recirculation:", None))
        self.value_recirculation.setText(QCoreApplication.translate("BalanceCheckDialog", u"0 m\u00b3", None))
        self.label_error_pct.setText(QCoreApplication.translate("BalanceCheckDialog", u"Closure Error:", None))
        self.value_error_pct.setText(QCoreApplication.translate("BalanceCheckDialog", u"0.0 %", None))
        self.value_error_pct.setStyleSheet(QCoreApplication.translate("BalanceCheckDialog", u"QLabel { color: #22AA22; font-weight: bold; }", None))
        self.btn_save_categories.setText(QCoreApplication.translate("BalanceCheckDialog", u"Save Categories", None))
        self.btn_close.setText(QCoreApplication.translate("BalanceCheckDialog", u"Close", None))
    # retranslateUi

