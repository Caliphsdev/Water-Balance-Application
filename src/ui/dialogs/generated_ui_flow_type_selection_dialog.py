# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'flow_type_selection_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_FlowTypeSelectionDialog(object):
    def setupUi(self, FlowTypeSelectionDialog):
        if not FlowTypeSelectionDialog.objectName():
            FlowTypeSelectionDialog.setObjectName(u"FlowTypeSelectionDialog")
        FlowTypeSelectionDialog.resize(400, 250)
        FlowTypeSelectionDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(FlowTypeSelectionDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_instruction = QLabel(FlowTypeSelectionDialog)
        self.label_instruction.setObjectName(u"label_instruction")

        self.verticalLayout.addWidget(self.label_instruction)

        self.verticalLayout_options = QVBoxLayout()
        self.verticalLayout_options.setObjectName(u"verticalLayout_options")
        self.radio_clean = QRadioButton(FlowTypeSelectionDialog)
        self.radio_clean.setObjectName(u"radio_clean")
        self.radio_clean.setChecked(True)

        self.verticalLayout_options.addWidget(self.radio_clean)

        self.radio_dirty = QRadioButton(FlowTypeSelectionDialog)
        self.radio_dirty.setObjectName(u"radio_dirty")

        self.verticalLayout_options.addWidget(self.radio_dirty)

        self.radio_evaporation = QRadioButton(FlowTypeSelectionDialog)
        self.radio_evaporation.setObjectName(u"radio_evaporation")

        self.verticalLayout_options.addWidget(self.radio_evaporation)

        self.radio_recirculation = QRadioButton(FlowTypeSelectionDialog)
        self.radio_recirculation.setObjectName(u"radio_recirculation")

        self.verticalLayout_options.addWidget(self.radio_recirculation)


        self.verticalLayout.addLayout(self.verticalLayout_options)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer)

        self.btn_ok = QPushButton(FlowTypeSelectionDialog)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton(FlowTypeSelectionDialog)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumWidth(100)

        self.horizontalLayout_buttons.addWidget(self.btn_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(FlowTypeSelectionDialog)
        self.btn_ok.clicked.connect(FlowTypeSelectionDialog.accept)
        self.btn_cancel.clicked.connect(FlowTypeSelectionDialog.reject)

        self.btn_ok.setDefault(True)


        QMetaObject.connectSlotsByName(FlowTypeSelectionDialog)
    # setupUi

    def retranslateUi(self, FlowTypeSelectionDialog):
        FlowTypeSelectionDialog.setWindowTitle(QCoreApplication.translate("FlowTypeSelectionDialog", u"Select Flow Type", None))
        self.label_instruction.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"Select the type of water flow for this line:", None))
        self.label_instruction.setStyleSheet(QCoreApplication.translate("FlowTypeSelectionDialog", u"QLabel { font-weight: bold; font-size: 12px; margin-bottom: 10px; }", None))
        self.radio_clean.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"\U0001f535 Clean Water (Blue) - Fresh water source", None))
        self.radio_dirty.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"\U0001f534 Dirty/Waste Water (Red) - Treated effluent", None))
        self.radio_evaporation.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"\u26ab Evaporation Loss (Black) - Water loss to atmosphere", None))
        self.radio_recirculation.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"\U0001f7e3 Recirculation (Purple) - Recycled water back to source", None))
        self.btn_ok.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"OK", None))
        self.btn_cancel.setText(QCoreApplication.translate("FlowTypeSelectionDialog", u"Cancel", None))
    # retranslateUi

