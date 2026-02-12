"""
About Dashboard Controller (APPLICATION INFO).

Purpose:
- Load about.ui (container for about content)
- Display application version, licensing, and credits
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import ConfigManager, get_resource_path
from ui.dashboards.generated_ui_about import Ui_Form


class AboutPage(QWidget):
    """About Page (APPLICATION INFORMATION)."""

    def __init__(self, parent=None):
        """Initialize About page."""
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._build_about_content()

    def _build_about_content(self) -> None:
        """Replace placeholder labels with a complete About layout."""
        self.ui.label.hide()
        self.ui.label_2.hide()

        frame_layout = self.ui.frame.layout()
        if frame_layout is None:
            frame_layout = QVBoxLayout(self.ui.frame)
        frame_layout.setContentsMargins(20, 16, 20, 16)
        frame_layout.setSpacing(12)

        scroll = QScrollArea(self.ui.frame)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget(scroll)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._build_header_card())
        content_layout.addWidget(self._build_company_address_card())
        content_layout.addWidget(self._build_product_card())
        content_layout.addWidget(self._build_team_cards())
        content_layout.addWidget(self._build_legal_card())
        content_layout.addStretch(1)

        scroll.setWidget(content)
        frame_layout.addWidget(scroll)

    def _build_header_card(self) -> QWidget:
        card = self._new_card("aboutHeaderCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)

        logo_label = QLabel(card)
        logo_label.setFixedSize(110, 110)
        logo_label.setAlignment(Qt.AlignCenter)
        pixmap = self._load_company_logo()
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("TAR")
            logo_label.setObjectName("aboutLogoFallback")
        layout.addWidget(logo_label, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title = QLabel("TransAfrica Resources", card)
        title.setObjectName("aboutCompanyTitle")
        subtitle = QLabel("Water Balance Dashboard", card)
        subtitle.setObjectName("aboutProductTitle")
        desc = QLabel(
            "A professional platform for water balance analysis, monitoring, "
            "and reporting across mining operations.",
            card,
        )
        desc.setWordWrap(True)
        desc.setObjectName("aboutSubtitle")

        config = ConfigManager()
        version = config.get("app.version", "1.0.0")
        year = date.today().year
        meta = QLabel(f"Version {version}  |  Release Year {year}", card)
        meta.setObjectName("aboutMeta")

        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addWidget(desc)
        text_col.addWidget(meta)
        text_col.addStretch(1)
        layout.addLayout(text_col, 1)

        self._apply_about_styles(card)
        return card

    def _build_company_address_card(self) -> QWidget:
        card = self._new_card("aboutAddressCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        heading = QLabel("Company Address", card)
        heading.setObjectName("aboutSectionTitle")
        layout.addWidget(heading)

        columns = QWidget(card)
        grid = QGridLayout(columns)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)

        physical_title = QLabel("Physical Address", columns)
        physical_title.setObjectName("aboutAddressHeading")
        physical_body = QLabel(
            "TRANS AFRICA RESOURCES (PTY) LTD\n"
            "91 Hornbill Avenue\n"
            "Rooihuiskraal\n"
            "Centurion, 0157\n"
            "Pretoria\n"
            "South Africa",
            columns,
        )
        physical_body.setObjectName("aboutBody")
        physical_body.setWordWrap(True)

        postal_title = QLabel("Postal Address", columns)
        postal_title.setObjectName("aboutAddressHeading")
        postal_body = QLabel(
            "Postnet Suite 55\n"
            "Private Bag X3\n"
            "The Reeds, 0061\n"
            "Pretoria\n"
            "South Africa",
            columns,
        )
        postal_body.setObjectName("aboutBody")
        postal_body.setWordWrap(True)

        grid.addWidget(physical_title, 0, 0)
        grid.addWidget(postal_title, 0, 1)
        grid.addWidget(physical_body, 1, 0)
        grid.addWidget(postal_body, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addWidget(columns)

        self._apply_about_styles(card)
        return card

    def _build_product_card(self) -> QWidget:
        card = self._new_card("aboutProductCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        heading = QLabel("About This Product", card)
        heading.setObjectName("aboutSectionTitle")
        body = QLabel(
            "This application supports monthly water accounting by combining "
            "meter data, environmental records, storage tracking, and flow "
            "categorization into one review workflow. It is intended for "
            "operational users, technical reviewers, and management reporting.",
            card,
        )
        body.setWordWrap(True)
        body.setObjectName("aboutBody")

        layout.addWidget(heading)
        layout.addWidget(body)
        self._apply_about_styles(card)
        return card

    def _build_team_cards(self) -> QWidget:
        wrapper = self._new_card("aboutTeamWrap")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(16, 14, 16, 14)
        wrapper_layout.setSpacing(10)

        heading = QLabel("Project Team and Contacts", wrapper)
        heading.setObjectName("aboutSectionTitle")
        wrapper_layout.addWidget(heading)

        grid_host = QWidget(wrapper)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        grid.addWidget(
            self._person_card(
                "Project Lead",
                "Prof Caliphs Zvinowanda",
                "+27 82 355 8130",
                "caliphs@transafreso.com",
            ),
            0,
            0,
        )
        grid.addWidget(
            self._person_card(
                "Administrator",
                "Ms Moloko Florence Morethe",
                "+27 83 870 65 69",
                "mfmorethe@transafreso.com",
            ),
            0,
            1,
        )
        grid.addWidget(
            self._person_card(
                "Developer",
                "Mr Caliphs Zvinowanda (Jnr)",
                "065 235 7607",
                "kali@transafreso.com",
            ),
            0,
            2,
        )

        wrapper_layout.addWidget(grid_host)
        self._apply_about_styles(wrapper)
        return wrapper

    def _build_legal_card(self) -> QWidget:
        card = self._new_card("aboutLegalCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        heading = QLabel("Legal and Copyright", card)
        heading.setObjectName("aboutSectionTitle")
        year = date.today().year
        today = date.today().strftime("%Y-%m-%d")
        legal = QLabel(
            f"Copyright (c) {year} TransAfrica Resources. All rights reserved.\n"
            "Water Balance Dashboard and related materials are proprietary to "
            "TransAfrica Resources and are intended for authorized operational use.\n"
            "Third-party open-source notices are listed in THIRD_PARTY_LICENSES.txt.\n"
            "For support, maintenance, or access requests, contact the project team listed above.\n"
            f"Last updated: {today}",
            card,
        )
        legal.setWordWrap(True)
        legal.setObjectName("aboutBody")

        layout.addWidget(heading)
        layout.addWidget(legal)
        self._apply_about_styles(card)
        return card

    def _person_card(self, role: str, name: str, phone: str, email: str) -> QWidget:
        card = self._new_card("aboutPersonCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        role_lbl = QLabel(role, card)
        role_lbl.setObjectName("aboutRole")
        name_lbl = QLabel(name, card)
        name_lbl.setWordWrap(True)
        name_lbl.setObjectName("aboutName")
        phone_lbl = QLabel(f"Cell: {phone}", card)
        phone_lbl.setObjectName("aboutContact")
        email_lbl = QLabel(f"Email: <a href='mailto:{email}'>{email}</a>", card)
        email_lbl.setObjectName("aboutContact")
        email_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        email_lbl.setOpenExternalLinks(True)

        layout.addWidget(role_lbl)
        layout.addWidget(name_lbl)
        layout.addSpacing(2)
        layout.addWidget(phone_lbl)
        layout.addWidget(email_lbl)
        layout.addStretch(1)
        self._apply_about_styles(card)
        return card

    @staticmethod
    def _new_card(object_name: str) -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        card.setFrameShape(QFrame.StyledPanel)
        return card

    @staticmethod
    def _load_company_logo() -> QPixmap:
        """Load company logo from known resource locations."""
        candidates = [
            get_resource_path("src/ui/resources/icons/Company logo.png"),
            get_resource_path("ui/resources/icons/Company logo.png"),
            Path(__file__).resolve().parents[1] / "resources" / "icons" / "Company logo.png",
        ]
        for path in candidates:
            if path.exists():
                pix = QPixmap(str(path))
                if not pix.isNull():
                    return pix
        return QPixmap()

    @staticmethod
    def _apply_about_styles(widget: QWidget) -> None:
        widget.setStyleSheet(
            """
            QFrame#aboutHeaderCard,
            QFrame#aboutAddressCard,
            QFrame#aboutProductCard,
            QFrame#aboutTeamWrap,
            QFrame#aboutLegalCard {
                background: #f8fbff;
                border: 1px solid #c9d8ea;
                border-radius: 12px;
            }
            QFrame#aboutPersonCard {
                background: #ffffff;
                border: 1px solid #d6e0ed;
                border-radius: 10px;
            }
            QLabel#aboutCompanyTitle {
                font-size: 26px;
                font-weight: 700;
                color: #0b2a53;
            }
            QLabel#aboutProductTitle {
                font-size: 18px;
                font-weight: 600;
                color: #1d4f91;
            }
            QLabel#aboutSubtitle {
                font-size: 14px;
                color: #2f4666;
            }
            QLabel#aboutMeta {
                font-size: 13px;
                font-weight: 600;
                color: #35557d;
            }
            QLabel#aboutSectionTitle {
                font-size: 18px;
                font-weight: 700;
                color: #0f315e;
            }
            QLabel#aboutBody {
                font-size: 14px;
                color: #1c2f4a;
            }
            QLabel#aboutRole {
                font-size: 13px;
                font-weight: 700;
                color: #1d4f91;
            }
            QLabel#aboutAddressHeading {
                font-size: 14px;
                font-weight: 800;
                color: #153e72;
            }
            QLabel#aboutName {
                font-size: 15px;
                font-weight: 600;
                color: #112a4b;
            }
            QLabel#aboutContact {
                font-size: 13px;
                color: #28415f;
            }
            QLabel#aboutContact a {
                color: #1d4f91;
                text-decoration: none;
            }
            QLabel#aboutContact a:hover {
                text-decoration: underline;
            }
            QLabel#aboutLogoFallback {
                background: #dbe8f8;
                border: 1px solid #b7c9df;
                border-radius: 12px;
                font-size: 26px;
                font-weight: 800;
                color: #194a86;
            }
            """
        )
