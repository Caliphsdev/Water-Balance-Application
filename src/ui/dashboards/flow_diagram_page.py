"""
Flow Diagram Dashboard Page Controller

This module provides the main PySide6 interface for the Flow Diagram drawing editor.
It orchestrates:
- QGraphicsView/Scene setup for rendering flow diagrams
- Toolbar button connections
- Dialog management (Add/Edit Node, Edit Flow, Balance Check, Excel Setup)
- JSON loading/saving of diagram data
- Excel data integration for flow volumes

Data Sources:
- Flow diagram JSON: data/diagrams/{area_code}_flow_diagram.json
- Flow volumes Excel: timeseries_excel_path (from config)
- Database: Optional connection validation via db_manager

Key Concepts:
- Nodes: Water components (sources, storage, plants) represented as graphical rectangles/ovals
- Edges: Flow lines connecting nodes, color-coded by flow type (clean/dirty/recirculation)
- Anchor Points: 17 snapping points per node for precise edge connections
- Drawing Mode: State machine for drawing orthogonal (90°) flow lines
"""

import sys
import os
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem, QGraphicsTextItem,
    QMessageBox, QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QListWidget, QListWidgetItem, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QSize, QPointF, QEvent
from PySide6.QtGui import (
    QPainter, QColor, QPen, QPainterPath, QTransform, QBrush, QFont,
    QKeySequence, QShortcut, QIcon
)

import json
import logging
import time
from typing import Dict, List, Optional, Tuple
import pandas as pd

from ui.dashboards.generated_ui_flow_diagram import Ui_Form
from ui.dialogs.add_edit_node_dialog import AddEditNodeDialog
from ui.dialogs.edit_flow_dialog import EditFlowDialog
from ui.dialogs.flow_type_selection_dialog import FlowTypeSelectionDialog
from ui.dialogs.balance_check_dialog import BalanceCheckDialog
from ui.dialogs.excel_setup_dialog import ExcelSetupDialog
from ui.dialogs.recirculation_manager_dialog import RecirculationManagerDialog
from ui.components.flow_graphics_items import FlowNodeItem, FlowEdgeItem
from services.excel_manager import get_excel_manager
from services.recirculation_loader import get_recirculation_loader
from core.app_logger import logger as app_logger
from core.config_manager import get_resource_path
from ui.theme import PALETTE

# Flow Diagram dashboard-specific logger (logs/flow_diagram/ folder)
logger = app_logger.get_dashboard_logger('flow_diagram')


class FlowDiagramPage(QWidget):
    """
    Flow Diagram Dashboard Page (MAIN UI CONTAINER).
    
    Loads from flow_diagram_main.ui and provides:
    - Graphics view for drawing flow diagrams
    - Toolbar for node/edge/Excel operations
    - Dialog management for editing operations
    - State management for drawing mode
    
    Responsibilities:
    - Connect all toolbar buttons to actions
    - Create and manage QGraphicsScene
    - Handle dialog callbacks
    - Update status bar with operation feedback
    - Coordinate Excel data loading with ExcelManager
    
    Signals:
    - diagram_changed: Emitted when diagram structure changes
    - status_message: Emitted for status bar updates (message, duration_ms)
    """
    
    # Signals
    diagram_changed = Signal()  # Diagram structure changed
    status_message = Signal(str, int)  # Message, duration in ms (0 = permanent)
    balance_data_updated = Signal(dict)  # Balance data changed (inflows, outflows, recirculation, error)
    
    def __init__(self, parent=None):
        """
        Initialize Flow Diagram Page.
        
        Args:
            parent: Parent widget (typically MainWindow)
        """
        super().__init__(parent)
        # Setup UI from .ui file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._apply_toolbar_layout_refresh()
        self._modernize_balance_footer()
        self._apply_balance_compact_mode()
        
        # Create graphics scene for drawing
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.ui.graphicsView.setRenderHint(QPainter.SmoothPixmapTransform)
        # Ensure full viewport redraws to avoid drag trails
        self.ui.graphicsView.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.ui.graphicsView.setCacheMode(QGraphicsView.CacheNone)
        # Enable item interaction and selection
        self.ui.graphicsView.setInteractive(True)
        # Set no drag mode by default (we'll control cursor explicitly)
        self.ui.graphicsView.setDragMode(QGraphicsView.NoDrag)
        # Ensure mouse events reach items (don't consume at view level)
        self.ui.graphicsView.setMouseTracking(True)
        # Ensure key events can be captured by this widget and the view
        self.setFocusPolicy(Qt.StrongFocus)
        self.ui.graphicsView.setFocusPolicy(Qt.StrongFocus)
        self.ui.graphicsView.viewport().setFocusPolicy(Qt.StrongFocus)
        
        # State management
        self.area_code = "UG2N"  # Default area (can be changed)
        self.diagram_path = None
        self.diagram_data = {}
        # Session flag: avoid using persisted stale volumes until user explicitly loads Excel.
        self._excel_data_loaded_for_session = False
        
        # Drawing mode state machine
        self.drawing_mode = False
        self.drawing_from_id = None
        self.drawing_segments = []
        self._preview_items = []  # List of preview graphics items (anchors, lines)
        self._last_mouse_scene_pos = None  # Track last cursor position for instant previews
        self._last_mouse_modifiers = Qt.KeyboardModifier.NoModifier
        self._snap_edge_idx = None  # Index of edge being hovered for snap (None if no snap available)
        self._snap_edge_item = None  # Reference to edge graphics item for highlighting
        
        # Selection state
        self.selected_node_id = None
        self.selected_edge_idx = None
        self.selected_edge_item = None  # Track the actual selected graphics item

        # Global ESC shortcut to exit drawing mode reliably
        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._esc_shortcut.activated.connect(self._on_escape_pressed)
        
        # Populate filter dropdowns (BEFORE connecting signals to avoid unwanted saves)
        self._populate_filter_dropdowns()
        
        # Setup toolbar button connections (AFTER populate/restore to avoid interfering with initialization)
        self._connect_toolbar_buttons()
        
        # Load default diagram (UG2N)
        self.load_diagram("UG2N")
        
        logger.info("Flow Diagram Page initialized")

    def _modernize_balance_footer(self) -> None:
        """Rebuild footer metrics into compact KPI cards + balance badge."""
        if not hasattr(self.ui, "frame_2"):
            return

        footer = self.ui.frame_2
        footer.setObjectName("flow_balance_panel")
        footer.setMinimumHeight(96)

        old_layout = footer.layout()
        if old_layout is None:
            return

        def _clear_layout_tree(layout) -> None:
            """Recursively detach widgets/layouts from a generated layout tree."""
            while layout.count():
                item = layout.takeAt(0)
                child_widget = item.widget()
                child_layout = item.layout()
                if child_widget is not None:
                    child_widget.setVisible(False)
                    child_widget.setParent(footer)
                elif child_layout is not None:
                    _clear_layout_tree(child_layout)

        # Clear generated spacer-heavy layout (including nested sub-layouts).
        _clear_layout_tree(old_layout)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(3)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(6)
        card_layouts = []

        def _build_metric_card(
            title_text: str,
            value_label: QLabel,
            unit_label: QLabel,
            card_name: str,
        ) -> QFrame:
            card = QFrame(footer)
            card.setObjectName(card_name)
            card.setMinimumHeight(42)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 4, 8, 4)
            card_layout.setSpacing(1)
            card_layouts.append(card_layout)

            title = QLabel(title_text, card)
            title.setObjectName("flow_balance_metric_title")
            card_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)

            value_row = QHBoxLayout()
            value_row.setSpacing(4)
            value_label.setParent(card)
            value_label.setVisible(True)
            unit_label.setParent(card)
            unit_label.setVisible(True)
            value_label.setObjectName("flow_balance_metric_value")
            unit_label.setObjectName("flow_balance_metric_unit")
            value_label.setMinimumHeight(20)
            value_label.setMaximumHeight(24)
            value_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_row.addWidget(value_label)
            value_row.addWidget(unit_label)
            value_row.addStretch(1)
            card_layout.addLayout(value_row)
            return card

        inflows_card = _build_metric_card(
            "Inflows Total",
            self.ui.total_inflows_value,
            self.ui.unit,
            "flow_balance_card_inflows",
        )
        recirc_card = _build_metric_card(
            "Recirculation",
            self.ui.recirculation_value,
            self.ui.unit_2,
            "flow_balance_card_recirculation",
        )
        outflows_card = _build_metric_card(
            "Outflows Total",
            self.ui.total_outflows_value,
            self.ui.unit_3,
            "flow_balance_card_outflows",
        )

        cards_row.addWidget(inflows_card, 1)
        cards_row.addWidget(recirc_card, 1)
        cards_row.addWidget(outflows_card, 1)
        main_layout.addLayout(cards_row)

        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.setSpacing(0)
        badge_row.addStretch(1)

        badge = QFrame(footer)
        badge.setObjectName("flow_balance_badge")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(8, 2, 8, 2)
        badge_layout.setSpacing(4)

        self.ui.balance_check_label.setParent(badge)
        self.ui.balance_check_label.setVisible(True)
        self.ui.balance_check_label.setObjectName("flow_balance_badge_label")
        self.ui.balance_check_label.setText("Balance Check")
        self.ui.balance_check_value.setParent(badge)
        self.ui.balance_check_value.setVisible(True)
        self.ui.balance_check_value.setObjectName("flow_balance_badge_value")
        self.ui.unit_4.setParent(badge)
        self.ui.unit_4.setVisible(True)
        self.ui.unit_4.setObjectName("flow_balance_badge_unit")

        badge_layout.addWidget(self.ui.balance_check_label)
        badge_layout.addWidget(self.ui.balance_check_value)
        badge_layout.addWidget(self.ui.unit_4)
        badge_row.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)
        badge_row.addStretch(1)
        main_layout.addLayout(badge_row)

        old_layout.addLayout(main_layout, 0, 0, 1, 1)

        self._balance_cards = [inflows_card, recirc_card, outflows_card]
        self._balance_card_layouts = card_layouts
        self._balance_cards_row = cards_row
        self._balance_main_layout = main_layout
        self._balance_badge_layout = badge_layout
        self._balance_badge_row = badge_row
        self._balance_value_labels = [
            self.ui.total_inflows_value,
            self.ui.recirculation_value,
            self.ui.total_outflows_value,
        ]
        self._balance_badge = badge
        self._apply_balance_compact_mode()

    def _apply_balance_compact_mode(self) -> None:
        """Apply balanced compact sizing, with tighter mode on short windows."""
        if not hasattr(self.ui, "frame_2"):
            return

        is_tight = self.height() < 860
        panel_min_h = 86 if is_tight else 96
        frame_min_h = 174 if is_tight else 182
        card_min_h = 38 if is_tight else 42
        value_min_h = 18 if is_tight else 20
        value_max_h = 22 if is_tight else 24
        main_margins = (8, 3 if is_tight else 4, 8, 3 if is_tight else 4)
        main_spacing = 2 if is_tight else 3
        cards_spacing = 6
        card_margins = (8, 3 if is_tight else 4, 8, 3 if is_tight else 4)
        card_spacing = 1
        badge_margins = (7 if is_tight else 8, 2, 7 if is_tight else 8, 2)
        badge_spacing = 3 if is_tight else 4

        self.ui.frame_2.setMinimumHeight(panel_min_h)
        if hasattr(self.ui, "frame"):
            self.ui.frame.setMinimumHeight(frame_min_h)

        for card in getattr(self, "_balance_cards", []):
            card.setMinimumHeight(card_min_h)

        for value_lbl in getattr(self, "_balance_value_labels", []):
            if value_lbl is not None:
                value_lbl.setMinimumHeight(value_min_h)
                value_lbl.setMaximumHeight(value_max_h)

        cards_row = getattr(self, "_balance_cards_row", None)
        if cards_row is not None:
            cards_row.setSpacing(cards_spacing)

        for card_layout in getattr(self, "_balance_card_layouts", []):
            card_layout.setContentsMargins(*card_margins)
            card_layout.setSpacing(card_spacing)

        main_layout = getattr(self, "_balance_main_layout", None)
        if main_layout is not None:
            main_layout.setContentsMargins(*main_margins)
            main_layout.setSpacing(main_spacing)

        badge_layout = getattr(self, "_balance_badge_layout", None)
        if badge_layout is not None:
            badge_layout.setContentsMargins(*badge_margins)
            badge_layout.setSpacing(badge_spacing)

    def resizeEvent(self, event):
        """Re-apply compact mode based on available vertical space."""
        super().resizeEvent(event)
        self._apply_balance_compact_mode()

    def _apply_toolbar_layout_refresh(self) -> None:
        """Refine header + toolbar grouping for clearer operations UX."""
        # Page margins and section spacing
        if hasattr(self.ui, "gridLayout"):
            self.ui.gridLayout.setContentsMargins(10, 6, 12, 10)
            self.ui.gridLayout.setVerticalSpacing(8)
        if hasattr(self.ui, "frame"):
            self.ui.frame.setMinimumHeight(182)

        # Title row: align with global dashboard title/subtitle pattern.
        if hasattr(self.ui, "horizontalLayout_2") and hasattr(self.ui, "label"):
            title_layout = self.ui.horizontalLayout_2
            # Hide generated label (it has restrictive size hints) and build a fresh header.
            self.ui.label.setVisible(False)

            if not hasattr(self, "_flow_header_wrap"):
                title_label = QLabel("Flow Diagram", self.ui.frame)
                title_label.setObjectName("label_title")
                title_label.setWordWrap(False)
                title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                title_label.setMinimumHeight(28)
                title_label.setMaximumHeight(34)
                title_label.setVisible(True)
                # Enforce title paint metrics to avoid clipping under DPI/style variance.
                title_label.setStyleSheet(
                    "font-size: 18px; font-weight: 700; color: #0b1a2a; padding-top: 0px;"
                )

                subtitle_label = QLabel("Manual flow line drawing", self.ui.frame)
                subtitle_label.setObjectName("label_subtitle")
                subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                subtitle_label.setMinimumHeight(18)
                subtitle_label.setMaximumHeight(20)
                subtitle_label.setVisible(True)

                icon_label = QLabel(self.ui.frame)
                icon_label.setPixmap(QIcon(":/icons/flow_diagram_color.svg").pixmap(22, 22))
                icon_label.setFixedSize(22, 22)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                title_row = QWidget(self.ui.frame)
                title_row.setMinimumHeight(32)
                title_row_layout = QHBoxLayout(title_row)
                title_row_layout.setContentsMargins(0, 0, 0, 0)
                title_row_layout.setSpacing(10)
                title_row_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignVCenter)
                title_row_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignVCenter)
                title_row_layout.addWidget(subtitle_label, 0, Qt.AlignmentFlag.AlignVCenter)
                title_row_layout.addStretch(1)

                header_wrap = QWidget(self.ui.frame)
                header_wrap.setMinimumHeight(34)
                header_wrap.setMaximumHeight(38)
                header_layout = QVBoxLayout(header_wrap)
                header_layout.setContentsMargins(0, 0, 0, 0)
                header_layout.setSpacing(0)
                header_layout.addWidget(title_row)

                self._flow_header_wrap = header_wrap

            while title_layout.count():
                item = title_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)

            title_layout.setContentsMargins(8, 4, 8, 4)
            title_layout.setSpacing(0)
            title_layout.addWidget(self._flow_header_wrap, 0, Qt.AlignmentFlag.AlignLeft)
            title_layout.addStretch(1)

        # Row 1: Flows/Nodes groups
        if hasattr(self.ui, "horizontalLayout"):
            self.ui.horizontalLayout.setContentsMargins(8, 6, 8, 0)
            self.ui.horizontalLayout.setSpacing(8)
        if hasattr(self.ui, "label_2"):
            self.ui.label_2.setText("Flows")
            self.ui.label_2.setObjectName("flow_toolbar_section")
        if hasattr(self.ui, "label_5"):
            self.ui.label_5.setText("Nodes")
            self.ui.label_5.setObjectName("flow_toolbar_section")
        if hasattr(self.ui, "label_3"):
            self.ui.label_3.setVisible(False)
        if hasattr(self.ui, "label_4"):
            self.ui.label_4.setVisible(False)

        # Row 2: View + Save groups
        if hasattr(self.ui, "horizontalLayout_3"):
            row2 = self.ui.horizontalLayout_3
            row2.setContentsMargins(8, 0, 8, 0)
            row2.setSpacing(8)
            for idx in range(row2.count() - 1, -1, -1):
                item = row2.itemAt(idx)
                if item and item.spacerItem():
                    row2.takeAt(idx)
            row2.addStretch(1)

        # Row 3: Data & Validation controls
        if hasattr(self.ui, "horizontalLayout_4"):
            self.ui.horizontalLayout_4.setContentsMargins(8, 4, 8, 4)
            self.ui.horizontalLayout_4.setSpacing(8)
        if hasattr(self.ui, "label_6"):
            self.ui.label_6.setVisible(False)
        if hasattr(self.ui, "label_7"):
            self.ui.label_7.setText("Data & Validation")
            self.ui.label_7.setObjectName("flow_toolbar_section")
        if hasattr(self.ui, "label_8"):
            self.ui.label_8.setText("Year")
        if hasattr(self.ui, "label_9"):
            self.ui.label_9.setText("Month")

        # Button hierarchy and consistency
        if hasattr(self.ui, "load_excel_button"):
            self.ui.load_excel_button.setText("Load Excel")
            self.ui.load_excel_button.setMinimumWidth(112)
            self.ui.load_excel_button.setStyleSheet(
                "background-color:#1f3a5f; color:#ffffff; border:1px solid #1f3a5f; "
                "border-radius:8px; padding:6px 12px; font-weight:700;"
            )
            if hasattr(self.ui, "horizontalLayout_4"):
                self._excel_state_badge = QLabel(self.ui.frame)
                self._excel_state_badge.setObjectName("flow_excel_state_badge")
                self._excel_state_badge.setMinimumWidth(182)
                self.ui.horizontalLayout_4.insertWidget(
                    self.ui.horizontalLayout_4.indexOf(self.ui.excel_setup_button),
                    self._excel_state_badge
                )
        for name in ["excel_setup_button", "balance_check_button", "save_diagram_button"]:
            if hasattr(self.ui, name):
                btn = getattr(self.ui, name)
                btn.setMinimumWidth(112)
                btn.setMinimumHeight(30)
                btn.setMaximumHeight(30)

        # Keep Save Diagram aligned with app-wide Save action pattern.
        if hasattr(self.ui, "save_diagram_button"):
            self.ui.save_diagram_button.setText("Save Diagram")
            self.ui.save_diagram_button.setIcon(QIcon(":/icons/save_icon_black.svg"))
            self.ui.save_diagram_button.setIconSize(QSize(16, 16))
            self.ui.save_diagram_button.setStyleSheet(
                "background-color:#ffffff; color:#1f2f43; border:1px solid #c7d0da; "
                "border-radius:8px; padding:6px 12px; font-weight:600;"
            )
        if hasattr(self.ui, "zoom_in_button"):
            self.ui.zoom_in_button.setMinimumHeight(30)
            self.ui.zoom_in_button.setMaximumHeight(30)
            self.ui.zoom_in_button.setIcon(QIcon(":/icons/zoomin.svg"))
            self.ui.zoom_in_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "zoom_out_button"):
            self.ui.zoom_out_button.setMinimumHeight(30)
            self.ui.zoom_out_button.setMaximumHeight(30)
            self.ui.zoom_out_button.setIcon(QIcon(":/icons/zoom_out.svg"))
            self.ui.zoom_out_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "Draw_button"):
            self.ui.Draw_button.setMinimumHeight(30)
            self.ui.Draw_button.setMaximumHeight(30)
            self.ui.Draw_button.setIcon(QIcon(":/icons/draw_icon.svg"))
            self.ui.Draw_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "Add_button"):
            self.ui.Add_button.setMinimumHeight(30)
            self.ui.Add_button.setMaximumHeight(30)
            self.ui.Add_button.setIcon(QIcon(":/icons/add_icon.svg"))
            self.ui.Add_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "excel_setup_button"):
            self.ui.excel_setup_button.setIcon(QIcon(":/icons/exce_setup.svg"))
            self.ui.excel_setup_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "balance_check_button"):
            self.ui.balance_check_button.setIcon(QIcon(":/icons/balance check.svg"))
            self.ui.balance_check_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "lock_nodes_button"):
            self.ui.lock_nodes_button.setMinimumHeight(30)
            self.ui.lock_nodes_button.setMaximumHeight(30)
            self._refresh_lock_button_state()

        # Delete actions as danger buttons for clearer affordance
        if hasattr(self.ui, "edit_flows_button"):
            self.ui.edit_flows_button.setIcon(QIcon(":/icons/edit.svg"))
            self.ui.edit_flows_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "edit_nodes_button"):
            self.ui.edit_nodes_button.setIcon(QIcon(":/icons/edit.svg"))
            self.ui.edit_nodes_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "delete_folws_button"):
            self.ui.delete_folws_button.setObjectName("dangerButton")
            self.ui.delete_folws_button.setIcon(QIcon(":/icons/delete.svg"))
            self.ui.delete_folws_button.setIconSize(QSize(14, 14))
        if hasattr(self.ui, "pushButton_6"):
            self.ui.pushButton_6.setObjectName("dangerButton")
            self.ui.pushButton_6.setIcon(QIcon(":/icons/delete.svg"))
            self.ui.pushButton_6.setIconSize(QSize(14, 14))

        # Compact filter controls
        if hasattr(self.ui, "comboBox_filter_year"):
            self.ui.comboBox_filter_year.setMinimumWidth(100)
        if hasattr(self.ui, "comboBox_filter_month"):
            self.ui.comboBox_filter_month.setMinimumWidth(128)
        self._refresh_excel_state_badge()

    def _refresh_excel_state_badge(self) -> None:
        """Update inline Excel session state badge near Load Excel button."""
        badge = getattr(self, "_excel_state_badge", None)
        if badge is None:
            return
        if getattr(self, "_excel_data_loaded_for_session", False):
            badge.setText("Excel loaded for session")
            badge.setProperty("state", "ready")
        else:
            badge.setText("No Excel loaded for session")
            badge.setProperty("state", "missing")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        badge.update()

    def _refresh_lock_button_state(self) -> None:
        """Refresh lock/unlock button icon/text from selected node state."""
        if not hasattr(self.ui, "lock_nodes_button"):
            return

        btn = self.ui.lock_nodes_button
        btn.setIconSize(QSize(14, 14))

        selected_node_id = getattr(self, "selected_node_id", None)
        node_items = getattr(self, "node_items", {})
        node_item = node_items.get(selected_node_id) if selected_node_id else None
        is_locked = bool(getattr(node_item, "is_locked", False))

        if is_locked:
            btn.setText("Unlock")
            btn.setIcon(QIcon(":/icons/unlock.svg"))
        else:
            btn.setText("Lock")
            btn.setIcon(QIcon(":/icons/lock.svg"))

    def _get_user_data_dir(self) -> Optional[Path]:
        """Return user data directory (or None in dev mode)."""
        user_dir = os.environ.get('WATERBALANCE_USER_DIR')
        if user_dir:
            return Path(user_dir) / "data"
        return None

    def _resolve_data_file(self, relative_path: Path) -> Path:
        """Resolve a data file path with user-dir preference and bundled fallback."""
        user_data = self._get_user_data_dir()
        if user_data:
            user_path = user_data / relative_path
            if user_path.exists():
                return user_path

        return get_resource_path(str(Path("data") / relative_path))

    def _ensure_user_data_copy(self, relative_path: Path) -> Path:
        """Ensure a writable copy exists in user data; fall back to bundled resource."""
        resource_path = self._resolve_data_file(relative_path)
        user_data = self._get_user_data_dir()

        if user_data:
            user_path = user_data / relative_path
            if not user_path.exists() and resource_path.exists():
                try:
                    user_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(resource_path, user_path)
                except Exception:
                    return resource_path
            return user_path if user_path.exists() else resource_path

        return resource_path

    def _on_escape_pressed(self):
        """
        Handle ESC key press (GLOBAL SHORTCUT).

        This bypasses viewport focus issues by registering a shortcut on the
        page itself, ensuring ESC always exits drawing mode.
        """
        if self.drawing_mode:
            logger.info("Drawing mode disabled by user (ESC shortcut)")
            self._on_draw_clicked()  # Toggle off
    
    def _connect_toolbar_buttons(self):
        """Connect all toolbar buttons to their action methods (SIGNAL/SLOT WIRING).
        
        Connections:
        - Draw button → _on_draw_clicked() [toggle drawing mode]
        - Edit flows → _on_edit_flow_clicked() [open edit dialog]
        - Delete flows → _on_delete_flow_clicked() [remove selected edge]
        - Add node → _on_add_node_clicked() [create new component]
        - Edit node → _on_edit_node_clicked() [modify selected node]
        - Delete node → _on_delete_node_clicked() [remove selected node]
        - Lock node → _on_lock_node_clicked() [toggle position lock]
        - Zoom in/out → scale viewport
        - Load Excel → refresh flow volumes from Excel
        - Excel setup → open column mapping dialog
        - Balance check → open balance validation dialog
        - Save diagram → persist to JSON file
        - Recirculation → open recirculation manager
        - Year/Month filters → save and reload data
        """
        # Flow operations
        self.ui.Draw_button.clicked.connect(self._on_draw_clicked)
        self.ui.edit_flows_button.clicked.connect(self._on_edit_flow_clicked)
        self.ui.delete_folws_button.clicked.connect(self._on_delete_flow_clicked)
        
        # Node operations
        self.ui.Add_button.clicked.connect(self._on_add_node_clicked)
        self.ui.edit_nodes_button.clicked.connect(self._on_edit_node_clicked)
        self.ui.pushButton_6.clicked.connect(self._on_delete_node_clicked)
        self.ui.lock_nodes_button.clicked.connect(self._on_lock_node_clicked)
        
        # View operations
        self.ui.zoom_in_button.clicked.connect(self._on_zoom_in)
        self.ui.zoom_out_button.clicked.connect(self._on_zoom_out)
        
        # Excel operations
        self.ui.load_excel_button.clicked.connect(self._on_load_excel_clicked)
        self.ui.excel_setup_button.clicked.connect(self._on_excel_setup_clicked)
        
        # Utility operations
        self.ui.balance_check_button.clicked.connect(self._on_balance_check_clicked)
        self.ui.save_diagram_button.clicked.connect(self._on_save_diagram_clicked)
        
        # Recirculation management
        if hasattr(self.ui, 'recirculation_button'):
            self.ui.recirculation_button.clicked.connect(self._on_recirculation_clicked)
        
        # Filter dropdown changes - save selected date for persistence
        self.ui.comboBox_filter_year.currentTextChanged.connect(self._save_selected_date)
        self.ui.comboBox_filter_month.currentIndexChanged.connect(self._save_selected_date)
        
        logger.debug("Toolbar buttons connected")
    
    def _populate_filter_dropdowns(self):
        """Populate year and month dropdown filters (INIT HELPER).
        
        Populates:
        - Year dropdown: Current year ± 5 years (for historical analysis)
        - Month dropdown: January-December with 1-12 index values
        
        After populating, restores previously selected date from filter_state.json.
        """
        # Year dropdown
        import datetime
        current_year = datetime.datetime.now().year
        for year in range(current_year - 5, current_year + 3):
            self.ui.comboBox_filter_year.addItem(str(year), year)
        self.ui.comboBox_filter_year.setCurrentText(str(current_year))
        
        # Month dropdown
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for idx, month in enumerate(months, 1):
            self.ui.comboBox_filter_month.addItem(month, idx)
        
        # Restore previously selected date from persistent storage
        self._restore_selected_date()
        
        logger.debug("Filter dropdowns populated")
    
    def _restore_selected_date(self):
        """Restore previously selected year/month from persistent storage (UI STATE RESTORATION).
        
        Reads data/filter_state.json to restore the last selected date.
        If file doesn't exist or is invalid, defaults to current date.
        
        This ensures diagram values AND date selection persist across app restarts.
        
        IMPORTANT: Temporarily blocks signals during restoration to prevent
        triggering _save_selected_date() during initialization.
        """
        try:
            # Temporarily block signals to prevent saving during restoration
            self.ui.comboBox_filter_year.blockSignals(True)
            self.ui.comboBox_filter_month.blockSignals(True)
            
            state_file = self._ensure_user_data_copy(Path("filter_state.json"))
            if Path(state_file).exists():
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                    saved_year = state_data.get("year")
                    saved_month = state_data.get("month")
                    
                    # Restore year if valid
                    if saved_year:
                        year_index = self.ui.comboBox_filter_year.findText(str(saved_year))
                        if year_index >= 0:
                            self.ui.comboBox_filter_year.setCurrentIndex(year_index)
                            logger.debug(f"Restored year: {saved_year}")
                    
                    # Restore month if valid
                    if saved_month and 1 <= saved_month <= 12:
                        self.ui.comboBox_filter_month.setCurrentIndex(saved_month - 1)
                        logger.debug(f"Restored month: {saved_month}")
            else:
                # File doesn't exist - use current date as default
                import datetime
                self.ui.comboBox_filter_year.setCurrentText(str(datetime.datetime.now().year))
                self.ui.comboBox_filter_month.setCurrentIndex(datetime.datetime.now().month - 1)
                logger.debug("No saved filter state - using current date")
        
        except Exception as e:
            logger.warning(f"Error restoring filter state: {e} - using current date")
            import datetime
            self.ui.comboBox_filter_year.setCurrentText(str(datetime.datetime.now().year))
            self.ui.comboBox_filter_month.setCurrentIndex(datetime.datetime.now().month - 1)
        
        finally:
            # Re-enable signals now that restoration is complete
            self.ui.comboBox_filter_year.blockSignals(False)
            self.ui.comboBox_filter_month.blockSignals(False)
    
    def _save_selected_date(self):
        """Save currently selected year/month to persistent storage (UI STATE PERSISTENCE).
        
        Writes to data/filter_state.json so the selected date is restored on next app launch.
        Called whenever user changes the date dropdowns.
        
        This keeps diagram values and date selection in sync.
        """
        try:
            selected_year = self.ui.comboBox_filter_year.currentText()
            selected_month = self.ui.comboBox_filter_month.currentIndex() + 1
            
            state_data = {
                "year": int(selected_year),
                "month": selected_month
            }
            
            data_dir = self._get_user_data_dir() or get_resource_path("data")
            data_dir.mkdir(parents=True, exist_ok=True)
            state_file = data_dir / "filter_state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.debug(f"Saved filter state: {selected_year}/{selected_month}")
        
        except Exception as e:
            logger.warning(f"Error saving filter state: {e}")
    
    def load_diagram(self, area_code: str = "UG2N"):
        """Load flow diagram for specified area from JSON file.
        
        Args:
            area_code: Mining area code (e.g., 'UG2N', 'MERS')
        """
        self.area_code = area_code
        self.diagram_path = self._ensure_user_data_copy(Path("diagrams") / "flow_diagram.json")
        self._excel_data_loaded_for_session = False
        self._refresh_excel_state_badge()
        
        try:
            with open(self.diagram_path, 'r') as f:
                self.diagram_data = json.load(f)

            # Fallback: if user copy is empty or missing zones/nodes, load bundled version
            resource_path = get_resource_path("data/diagrams/flow_diagram.json")
            if resource_path.exists():
                if not self.diagram_data.get('nodes') or not self.diagram_data.get('zone_bg'):
                    with open(resource_path, 'r') as f:
                        self.diagram_data = json.load(f)
                    # Ensure user copy exists for future saves
                    self.diagram_path = self._ensure_user_data_copy(Path("diagrams") / "flow_diagram.json")

            logger.info(f"Loaded diagram for {area_code}")
            self._clear_loaded_volumes_for_session()
            self._render_diagram()
            self._load_and_display_recirculation()
            # Update balance check labels on initial load
            self._update_balance_check_labels()
        except FileNotFoundError:
            logger.error(f"Diagram file not found: {self.diagram_path}")
            self.status_message.emit(f"Error: Diagram file not found for {area_code}", 5000)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in diagram file: {e}")
            self.status_message.emit(f"Error: Invalid diagram file format", 5000)

    def _clear_loaded_volumes_for_session(self) -> None:
        """Clear persisted diagram volumes until Excel is loaded in current session."""
        if not self.diagram_data:
            return

        for edge in self.diagram_data.get('edges', []):
            edge['volume'] = 0.0

        for node in self.diagram_data.get('nodes', []):
            if 'recirculation_volume' in node:
                node['recirculation_volume'] = 0.0
    
    def _render_diagram(self):
        """
        Render current diagram data to graphics scene (SCENE ORCHESTRATOR).
        
        Clears scene and recreates all nodes and edges from diagram_data.
        This is called after loading JSON or after data modifications.
        
        Process:
        1. Clear all existing graphics items from scene
        2. Create FlowNodeItem for each node in diagram_data['nodes']
        3. Create FlowEdgeItem for each edge in diagram_data['edges']
        4. Connect signals (node_moved, node_selected, node_double_clicked, edge_selected, edge_double_clicked)
        5. Set Z-ordering so edges appear behind nodes
        6. Adjust scene rect to fit all items with margin
        
        Data Structures:
        - Nodes: List of {id, label, type, shape, fill, outline, locked, x, y, width, height}
        - Edges: List of {from_id, to_id, flow_type, color, volume, waypoints}
        """
        self.scene.clear()
        self.node_items: Dict[str, FlowNodeItem] = {}  # Track nodes by ID
        self.edge_items: List[FlowEdgeItem] = []         # Track all edges
        self.selected_node_id = None
        self.selected_edge_idx = None
        self.selected_edge_item = None
        
        # Clear drawing state references to prevent accessing deleted Qt objects
        self._snap_edge_item = None
        self._snap_edge_idx = None
        self._preview_items = []  # Clear anchor preview items that were attached to scene
        self._refresh_lock_button_state()
        
        nodes_data = self.diagram_data.get('nodes', [])
        edges_data = self.diagram_data.get('edges', [])
        zones_data = self.diagram_data.get('zone_bg', [])
        
        try:
            # ========== STEP 0: Draw zone background rectangles ==========
            for zone_data in zones_data:
                zone_x = zone_data.get('x', 0)
                zone_y = zone_data.get('y', 0)
                zone_w = zone_data.get('width', 100)
                zone_h = zone_data.get('height', 100)
                zone_name = zone_data.get('name', 'Zone')
                zone_color = zone_data.get('color', '#f0f0f0')
                
                # Create zone background rectangle
                zone_rect = QGraphicsRectItem(zone_x, zone_y, zone_w, zone_h)
                zone_rect.setBrush(QBrush(QColor(zone_color)))
                zone_rect.setPen(QPen(QColor('#cccccc'), 1, Qt.DashLine))
                zone_rect.setZValue(-10)  # Behind everything
                self.scene.addItem(zone_rect)
                
                # Add zone label (larger, bold, centered at top)
                zone_label = QGraphicsTextItem(zone_name)
                label_font = QFont("Arial", 11, QFont.Bold)
                zone_label.setFont(label_font)
                zone_label.setDefaultTextColor(QColor("#333333"))
                zone_label.setPos(zone_x + 10, zone_y + 5)
                zone_label.setZValue(100)  # On top of everything
                self.scene.addItem(zone_label)
                
                logger.debug(f"Created zone background: {zone_name}")
            
            # Add INFLOWS and OUTFLOWS labels at the very top (only once)
            top_y = 5  # Position at top of canvas
            
            # INFLOWS label on the left
            inflows_label = QGraphicsTextItem("INFLOWS")
            inflows_font = QFont("Arial", 14, QFont.Bold)
            inflows_label.setFont(inflows_font)
            inflows_label.setDefaultTextColor(QColor("#0066cc"))
            inflows_label.setPos(50, top_y)
            inflows_label.setZValue(100)
            self.scene.addItem(inflows_label)
            
            # OUTFLOWS label on the right
            outflows_label = QGraphicsTextItem("OUTFLOWS")
            outflows_font = QFont("Arial", 14, QFont.Bold)
            outflows_label.setFont(outflows_font)
            outflows_label.setDefaultTextColor(QColor("#cc0000"))
            # Position on right side - calculate based on diagram width if available
            diagram_width = self.diagram_data.get('width', 1800)
            outflows_label.setPos(diagram_width - 150, top_y)
            outflows_label.setZValue(100)
            self.scene.addItem(outflows_label)
            
            # ========== STEP 1: Create all node graphics items ==========
            for node_data in nodes_data:
                node_id = node_data.get('id')
                if not node_id:
                    logger.warning("Node missing ID, skipping")
                    continue

                # Hide legacy junction nodes (keep as invisible anchors for existing edges)
                node_label = str(node_data.get('label', '')).lower()
                is_junction_node = (
                    str(node_id).lower().startswith('junction')
                    or node_data.get('type') == 'junction'
                    or 'junction' in node_label
                )
                
                # Create FlowNodeItem (QGraphicsRectItem subclass)
                node_item = FlowNodeItem(node_id, node_data)
                
                if is_junction_node:
                    node_item.setOpacity(0.0)
                    node_item.setEnabled(False)
                    self.scene.addItem(node_item)
                    self.node_items[node_id] = node_item
                    logger.debug(f"Rendered junction node as hidden anchor: {node_id}")
                    continue
                
                # Add to scene
                self.scene.addItem(node_item)
                self.node_items[node_id] = node_item
                
                # Connect signals: when node moves, update connected edges
                node_item.node_moved.connect(self._on_node_moved)
                node_item.node_selected.connect(self._on_node_selected)
                node_item.node_double_clicked.connect(self._on_node_double_clicked)
                node_item.node_context_menu.connect(self._on_node_context_menu)
                
                logger.debug(f"Created FlowNodeItem: {node_id}")
            
            # ========== STEP 2: Create all edge graphics items ==========
            for edge_idx, edge_data in enumerate(edges_data):
                # Support both old format ("from"/"to") and new format ("from_id"/"to_id")
                from_id = edge_data.get('from_id') or edge_data.get('from')
                to_id = edge_data.get('to_id') or edge_data.get('to')
                
                if not from_id or not to_id:
                    logger.debug(f"Edge {edge_idx} missing from_id/from or to_id/to, skipping")
                    continue
                
                # Normalize to new format for consistency
                edge_data['from_id'] = from_id
                edge_data['to_id'] = to_id
                
                # Support both old format ("segments") and new format ("waypoints")
                if 'waypoints' not in edge_data and 'segments' in edge_data:
                    edge_data['waypoints'] = edge_data['segments']
                
                is_junction = bool(edge_data.get('is_junction', False))
                junction_pos = edge_data.get('junction_pos')
                from_node = self.node_items.get(from_id)
                to_node = self.node_items.get(to_id) if not is_junction else None
                
                if not from_node or (to_node is None and not (is_junction and junction_pos)):
                    logger.debug(f"Edge {edge_idx}: Missing node {from_id} or {to_id}, skipping")
                    continue
                
                # Create FlowEdgeItem (junction edges use a stored junction_pos instead of a node)
                edge_item = FlowEdgeItem(
                    edge_idx=edge_idx,
                    edge_data=edge_data,
                    from_node=from_node,
                    to_node=to_node
                )
                
                # Add to scene
                self.scene.addItem(edge_item)
                self.edge_items.append(edge_item)
                
                # Set Z-value so edges appear behind nodes
                edge_item.setZValue(0)
                
                # Connect signals
                edge_item.edge_selected.connect(self._on_edge_selected)
                edge_item.edge_double_clicked.connect(self._on_edge_double_clicked)
                
                logger.debug(f"Created FlowEdgeItem: {from_id} -> {to_id}")
            
            # Ensure nodes are in front of edges
            for node_item in self.node_items.values():
                node_item.setZValue(1)
            
            # ========== STEP 3: Adjust scene rect to fit all items ==========
            # Add margin around content
            margin = 50
            scene_rect = self.scene.itemsBoundingRect()
            scene_rect.adjust(-margin, -margin, margin, margin)
            self.scene.setSceneRect(scene_rect)
            
            logger.info(
                f"Rendered diagram: {len(self.node_items)} nodes, "
                f"{len(self.edge_items)} edges"
            )
            
        except Exception as e:
            logger.error(f"Error rendering diagram: {e}", exc_info=True)
            self.status_message.emit(f"Error rendering diagram: {e}", 5000)
    
    def _update_color_legend(self, nodes_data: List[Dict]):
        """
        Create and display color legend as info text (COLOR LEGEND - FLOATING PANEL).
        
        Builds a legend that shows what each outline color means.
        Stored as text in dialog/label instead of scene items to avoid render loops.
        
        Args:
            nodes_data: List of node dictionaries with 'outline' and 'type' fields
        """
        try:
            # Extract unique outline colors
            color_map = {}
            for node_data in nodes_data:
                outline = node_data.get('outline', '#000000')
                if outline not in color_map:
                    color_map[outline] = True
            
            if not color_map:
                return
            
            # Define color descriptions
            color_descriptions = {
                '#2c5d8a': 'Water Source (Borehole)',
                '#1f4d7a': 'Fresh Water Source',
                '#c46f00': 'Storage/TSF',
                '#6d1c12': 'Recirculation Return',
                '#c40000': 'Waste/Discharge',
                '#000000': 'Generic Component',
            }
            
            # Build legend text
            legend_text = "COMPONENT COLORS:\n" + "-" * 30 + "\n"
            for color_hex in sorted(color_map.keys()):
                description = color_descriptions.get(color_hex, 'Unknown')
                legend_text += f"  {description}\n"
            
            # Store legend in status bar or tooltip for later display
            self.legend_text = legend_text
            logger.debug(f"Created color legend with {len(color_map)} unique colors")
            
        except Exception as e:
            logger.error(f"Error creating color legend: {e}", exc_info=True)
    
    def _load_and_display_recirculation(self):
        """Load recirculation data from Excel and update node badges (RECIRCULATION DISPLAY).
        
        After diagram is rendered, this method:
        1. Reads recirculation config from diagram JSON
        2. Loads recirculation volumes from Excel FOR THE SELECTED MONTH/YEAR
        3. Updates node items with recirculation_volume
        4. Triggers badge rendering
        """
        try:
            if not getattr(self, "_excel_data_loaded_for_session", False):
                # Keep recirculation cleared until explicit Excel load in this session.
                for node_item in self.node_items.values():
                    node_item.node_data['recirculation_volume'] = 0.0
                    node_item._setup_recirculation_badge()
                return

            # Get recirculation config from current diagram
            recirc_config = self.diagram_data.get('recirculation', [])
            if not recirc_config:
                logger.debug("No recirculation configuration found in diagram")
                return
            
            logger.info(f"Found {len(recirc_config)} recirculation configs to load")
            
            # Get the selected year/month from filters (for consistent date filtering)
            year = self.ui.comboBox_filter_year.currentData()
            month = self.ui.comboBox_filter_month.currentData()
            
            logger.debug(f"Loading recirculation for {year}/{month}")
            
            # Load recirculation volumes from Excel FOR THE SELECTED MONTH/YEAR
            recirc_loader = get_recirculation_loader()
            recirc_loader.set_config_path(self.diagram_path)
            
            # CRITICAL: Pass month and year to load data for the selected date, not the default
            recirc_volumes = recirc_loader.get_recirculation(self.area_code, month=month, year=year)
            
            if not recirc_volumes:
                # No volumes found - check if configs exist but Excel data is missing
                logger.warning(f"No recirculation volumes found for {self.area_code} in Excel")
                logger.warning(f"Configured components: {[c.get('component_name', 'N/A') for c in recirc_config]}")
                logger.warning(f"Check that Excel sheets and columns are populated with data for {year}/{month}")
                return
            
            # Update node items with recirculation data
            for component_id, volume in recirc_volumes.items():
                if component_id in self.node_items:
                    node_item = self.node_items[component_id]
                    
                    # Update node_data with recirculation volume
                    node_item.node_data['recirculation_volume'] = volume
                    
                    # Refresh the badge (calls _setup_recirculation_badge())
                    node_item._setup_recirculation_badge()
                    
                    logger.debug(f"Updated {component_id} recirculation badge: {volume} m³")
            
            logger.info(f"Loaded {len(recirc_volumes)} recirculation volumes for {self.area_code} ({year}/{month})")
            
        except Exception as e:
            logger.error(f"Error loading recirculation data: {e}")
    
    def _on_node_moved(self, node_id: str, new_pos: QPointF):
        """
        Handle node movement - update connected edges and state.
        
        Called by FlowNodeItem when user drags node to new position.
        Updates edge paths to keep connections accurate.
        
        When a node moves, all edges connected to it (either as source or destination)
        must have their paths recalculated to maintain the connection from the new position.
        
        Args:
            node_id: ID of moved node
            new_pos: New position (scene coordinates)
        """
        logger.debug(f"Node {node_id} moved to ({new_pos.x():.0f}, {new_pos.y():.0f})")
        
        # Update connected edges by calling their _update_path()
        # This ensures the edge stays connected to the node's new position
        for edge_item in self.edge_items:
            edge_data = edge_item.edge_data
            if edge_data.get('from_id') == node_id or edge_data.get('to_id') == node_id:
                # This edge is connected to the moved node - update its path
                edge_item._update_path()
                logger.debug(f"Updated edge path for: {edge_data.get('from_id')} -> {edge_data.get('to_id')}")
        
        # Mark diagram as modified (unsaved)
        self.diagram_changed.emit()
    
    def _on_node_selected(self, node_id: str):
        """
        Handle node selection - highlight and show properties.
        
        Called by FlowNodeItem when user clicks on it.
        
        Args:
            node_id: ID of selected node
        """
        logger.debug(f"Node selected: {node_id}")
        
        # Deselect all other nodes
        for nid, node_item in self.node_items.items():
            if nid != node_id:
                node_item.set_selected(False)
        
        # Select this node
        node_item = self.node_items.get(node_id)
        if node_item:
            node_item.set_selected(True)
            self.selected_node_id = node_id
            self._refresh_lock_button_state()
            self.status_message.emit(f"Selected node: {node_id}", 2000)
    
    def _on_node_double_clicked(self, node_id: str):
        """
        Handle node double-click - open edit dialog.
        
        Called by FlowNodeItem when user double-clicks it.
        
        Args:
            node_id: ID of node to edit
        """
        logger.debug(f"Node double-clicked: {node_id}")
        
        # Find node data
        node_data = None
        for nd in self.diagram_data.get('nodes', []):
            if nd.get('id') == node_id:
                node_data = nd
                break
        
        if not node_data:
            logger.warning(f"Node data not found for {node_id}")
            return
        
        # Open edit dialog
        dialog = AddEditNodeDialog(self, mode="edit", node_id=node_id, node_data=node_data)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_node_data()
            new_id = updated_data.get('id')
            
            # Handle ID change if user changed it
            if new_id and new_id != node_id:
                # Update all edge references
                for edge in self.diagram_data.get('edges', []):
                    if edge.get('from') == node_id or edge.get('from_id') == node_id:
                        edge['from'] = new_id
                        edge['from_id'] = new_id
                    if edge.get('to') == node_id or edge.get('to_id') == node_id:
                        edge['to'] = new_id
                        edge['to_id'] = new_id
                
                # Update node_items dict
                node_item = self.node_items.pop(node_id)
                self.node_items[new_id] = node_item
                node_item.node_id = new_id
                
                logger.info(f"Renamed node {node_id} → {new_id}")

            # Update node data and graphics item
            node_data.update(updated_data)
            node_item = self.node_items[new_id if new_id and new_id != node_id else node_id]
            node_item.apply_node_data(node_data)

            logger.info(f"Updated node {new_id if new_id else node_id}")
            self.diagram_changed.emit()
    
    def _on_node_context_menu(self, node_id: str, scene_pos: QPointF):
        """Handle right-click context menu on node (CONTEXT MENU FOR RECIRCULATION).
        
        Shows options to manage recirculation for storage/dam components.
        
        Args:
            node_id: ID of node that was right-clicked
            scene_pos: Position of click in scene coordinates
        """
        # Find node data to check type
        node_data = None
        for nd in self.diagram_data.get('nodes', []):
            if nd.get('id') == node_id:
                node_data = nd
                break
        
        if not node_data:
            return
        
        node_type = node_data.get('type', '').lower()
        
        # Skip junction nodes (not real components)
        if node_type == 'junction' or node_id.startswith('junction:'):
            logger.debug(f"Context menu skipped for junction node")
            return
        
        # Create context menu
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Recirculation action
        recirc_action = menu.addAction("Manage Recirculation for this Component")
        
        # Show menu at cursor position
        # mapFromScene() already returns QPoint, no need for .toPoint()
        global_pos = self.ui.graphicsView.mapToGlobal(self.ui.graphicsView.mapFromScene(scene_pos))
        action = menu.exec(global_pos)
        
        # Handle selection
        if action == recirc_action:
            self._open_recirculation_manager_for_node(node_id)
    
    def _open_recirculation_manager_for_node(self, node_id: str):
        """Open recirculation manager dialog for specific node (RECIRCULATION UI).
        
        Args:
            node_id: Component ID to manage recirculation for
        """
        try:
            dialog = RecirculationManagerDialog(self.diagram_data, self.diagram_path, self)
            
            if dialog.exec() == QDialog.Accepted:
                # Configuration saved to JSON - reload diagram data from file
                logger.info(f"Recirculation configuration updated for {node_id}")
                
                # Reload diagram data from file to get updated recirculation config
                try:
                    with open(self.diagram_path, 'r') as f:
                        self.diagram_data = json.load(f)
                    logger.debug(f"Reloaded diagram data from {self.diagram_path}")
                except Exception as e:
                    logger.error(f"Error reloading diagram data: {e}")
                
                # Now load and display recirculation with updated config
                self._load_and_display_recirculation()
                self.status_message.emit(f"Recirculation configuration saved for {node_id}", 3000)
            
            logger.debug("Recirculation manager dialog closed")
        except Exception as e:
            logger.error(f"Error opening recirculation manager: {e}")
    
    def _on_edge_selected(self, edge_idx: int):
        """
        Handle edge selection - highlight and show properties.
        
        Called by FlowEdgeItem when user clicks on it.
        
        Args:
            edge_idx: Index in diagram_data['edges'] (data index, not list position)
        """
        logger.info(f"🎯 Edge selected handler called: data index {edge_idx}")
        
        # Deselect all edges first to avoid multiple highlights
        for edge_item in self.edge_items:
            edge_item.set_selected(False)

        # Find the rendered edge item that matches the data index
        edge_item = next(
            (item for item in self.edge_items if item.edge_idx == edge_idx),
            None
        )
        if edge_item is None:
            logger.warning(f"Edge data index {edge_idx} not rendered; selection skipped")
            return

        logger.info(
            "Selected edge item details: "
            f"edge_idx={edge_item.edge_idx}, "
            f"from_id={edge_item.edge_data.get('from_id')}, "
            f"to_id={edge_item.edge_data.get('to_id')}, "
            f"data_obj_id={id(edge_item.edge_data)}"
        )

        try:
            data_index = self.diagram_data.get('edges', []).index(edge_item.edge_data)
            logger.info(f"Edge data object index in diagram_data: {data_index}")
        except ValueError:
            logger.warning("Edge data object not found in diagram_data edges list")

        # Select the edge and update selection state
        edge_item.set_selected(True)
        self.selected_edge_idx = edge_idx
        self.selected_edge_item = edge_item
        self.selected_node_id = None
        for _, node_item in self.node_items.items():
            node_item.set_selected(False)
        self._refresh_lock_button_state()

        edge_data = self.diagram_data.get('edges', [])[edge_idx]
        volume = edge_data.get('volume', 0)
        volume_str = f"{volume:.1f} m³" if volume is not None else "No volume"
        self.status_message.emit(
            f"Selected flow: {edge_data['from_id']} -> {edge_data['to_id']} "
            f"({volume_str})", 2000
        )
    
    def _on_edge_double_clicked(self, edge_idx: int):
        """
        Handle edge double-click - open edit dialog.
        
        Called by FlowEdgeItem when user double-clicks it.
        
        Args:
            edge_idx: Index in diagram_data['edges'] (data index, not list position)
        """
        logger.debug(f"Edge double-clicked: index {edge_idx}")
        
        if 0 <= edge_idx < len(self.diagram_data.get('edges', [])):
            edge_data = self.diagram_data.get('edges', [])[edge_idx]
            
            # Get source and destination node info for display
            from_node_data = None
            to_node_data = None
            for nd in self.diagram_data.get('nodes', []):
                if nd.get('id') == edge_data['from_id']:
                    from_node_data = nd
                if nd.get('id') == edge_data['to_id']:
                    to_node_data = nd
            
            # Open edit dialog
            dialog = EditFlowDialog(self, edge_idx, edge_data, from_node_data, to_node_data)
            if dialog.exec() == QDialog.Accepted:
                updated_data = dialog.get_flow_data()
                
                # Update edge data and graphics item
                edge_data.update(updated_data)
                edge_item = self.edge_items[edge_idx]
                edge_item.edge_data = updated_data
                edge_item._setup_styling()
                
                logger.info(f"Updated edge {edge_idx}")
                self.diagram_changed.emit()

    def _refresh_scene_rect(self) -> None:
        """Refresh scene bounds to fit all items with margin.

        This keeps panning/zooming aligned to the content extents after
        adding, editing, or deleting nodes/edges.
        """
        margin = 50
        scene_rect = self.scene.itemsBoundingRect()
        scene_rect.adjust(-margin, -margin, margin, margin)
        self.scene.setSceneRect(scene_rect)
    
    # ======================== Node Operations ========================
    
    def _on_add_node_clicked(self):
        """Open Add Node dialog."""
        dialog = AddEditNodeDialog(self, mode="add")
        if dialog.exec() == QDialog.Accepted:
            node_data = dialog.get_node_data()
            node_id = node_data.get('id')
            if not node_id:
                QMessageBox.warning(self, "Invalid Data", "Component ID is required")
                return

            # Prevent duplicate IDs to keep diagram data consistent.
            if any(n.get('id') == node_id for n in self.diagram_data.get('nodes', [])):
                QMessageBox.warning(
                    self,
                    "Duplicate Component",
                    f"A component with ID '{node_id}' already exists."
                )
                return

            # Place new node at the center of the current view.
            view_center = self.ui.graphicsView.mapToScene(
                self.ui.graphicsView.viewport().rect().center()
            )
            width = node_data.get('width', FlowNodeItem.DEFAULT_WIDTH)
            height = node_data.get('height', FlowNodeItem.DEFAULT_HEIGHT)
            node_data.update({
                'x': view_center.x() - (width / 2),
                'y': view_center.y() - (height / 2),
                'width': width,
                'height': height,
            })

            # Persist node in diagram data first.
            self.diagram_data.setdefault('nodes', []).append(node_data)

            # Create and wire the graphics item.
            node_item = FlowNodeItem(node_id, node_data)
            self.scene.addItem(node_item)
            self.node_items[node_id] = node_item
            node_item.setZValue(1)

            node_item.node_moved.connect(self._on_node_moved)
            node_item.node_selected.connect(self._on_node_selected)
            node_item.node_double_clicked.connect(self._on_node_double_clicked)

            self._refresh_scene_rect()
            self.diagram_changed.emit()
            self.status_message.emit(f"Component added: {node_id}", 3000)
            logger.info(f"Added node: {node_id}")
    
    def _on_edit_node_clicked(self):
        """Open Edit Node dialog for selected node."""
        if not self.selected_node_id:
            QMessageBox.warning(self, "No Selection", "Please select a component first")
            return

        existing_node = next(
            (n for n in self.diagram_data.get('nodes', []) if n.get('id') == self.selected_node_id),
            None
        )
        if not existing_node:
            QMessageBox.warning(self, "Not Found", "Selected component not found in data")
            return

        dialog = AddEditNodeDialog(
            self,
            mode="edit",
            node_id=self.selected_node_id,
            node_data=existing_node
        )
        if dialog.exec() == QDialog.Accepted:
            updated_fields = dialog.get_node_data()

            # Preserve geometry while updating visual and metadata fields.
            updated_node = existing_node.copy()
            updated_node.update(updated_fields)
            updated_node['x'] = existing_node.get('x', updated_node.get('x', 0))
            updated_node['y'] = existing_node.get('y', updated_node.get('y', 0))
            updated_node['width'] = updated_fields.get(
                'width', existing_node.get('width', FlowNodeItem.DEFAULT_WIDTH)
            )
            updated_node['height'] = updated_fields.get(
                'height', existing_node.get('height', FlowNodeItem.DEFAULT_HEIGHT)
            )

            # Update diagram data list.
            nodes = self.diagram_data.get('nodes', [])
            for idx, node in enumerate(nodes):
                if node.get('id') == self.selected_node_id:
                    nodes[idx] = updated_node
                    break

            # Update graphics item.
            node_item = self.node_items.get(self.selected_node_id)
            if node_item:
                node_item.apply_node_data(updated_node)

            self.diagram_changed.emit()
            self.status_message.emit(f"Component updated: {self.selected_node_id}", 3000)
            logger.info(f"Edited node: {self.selected_node_id}")
    
    def _on_delete_node_clicked(self):
        """Delete selected node."""
        if not self.selected_node_id:
            QMessageBox.warning(self, "No Selection", "Please select a component first")
            return
        
        reply = QMessageBox.question(
            self, "Delete Component",
            f"Delete component '{self.selected_node_id}'? This will also delete all connected flows.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info(f"Deleting node: {self.selected_node_id}")
            node_id = self.selected_node_id

            # Remove connected edges from scene and data.
            edges_to_remove = [
                item for item in list(self.edge_items)
                if item.edge_data.get('from_id') == node_id or item.edge_data.get('to_id') == node_id
            ]
            for item in edges_to_remove:
                self.scene.removeItem(item)
                if item in self.edge_items:
                    self.edge_items.remove(item)

            self.diagram_data['edges'] = [
                e for e in self.diagram_data.get('edges', [])
                if e.get('from_id') != node_id and e.get('to_id') != node_id
            ]

            # Remove node item from scene and data.
            node_item = self.node_items.pop(node_id, None)
            if node_item:
                self.scene.removeItem(node_item)

            self.diagram_data['nodes'] = [
                n for n in self.diagram_data.get('nodes', []) if n.get('id') != node_id
            ]

            # Re-sync edge indices after deletions.
            for item in self.edge_items:
                try:
                    item.edge_idx = self.diagram_data['edges'].index(item.edge_data)
                except ValueError:
                    logger.warning("Edge data missing after node delete; keeping edge_idx")

            self.selected_node_id = None
            self.selected_edge_idx = None
            self.selected_edge_item = None
            self._refresh_lock_button_state()

            self._refresh_scene_rect()
            self.diagram_changed.emit()
            self.status_message.emit(f"Component deleted: {node_id}", 3000)
    
    def _on_lock_node_clicked(self):
        """Toggle lock state for selected node."""
        if not self.selected_node_id:
            QMessageBox.warning(self, "No Selection", "Please select a component first")
            return
        
        # Get the node item from scene
        node_item = self.node_items.get(self.selected_node_id)
        if not node_item:
            logger.warning(f"Node item not found: {self.selected_node_id}")
            return
        
        # Toggle lock state
        new_locked_state = not node_item.is_locked
        node_item.set_locked(new_locked_state)
        
        # Update visual indication (thicker outline when locked)
        current_pen = node_item.pen()
        if new_locked_state:
            current_pen.setWidth(4)  # Thick border when locked
            status = "locked"
        else:
            current_pen.setWidth(2)  # Normal border when unlocked
            status = "unlocked"
        node_item.setPen(current_pen)
        
        # Update diagram data
        for node_data in self.diagram_data.get('nodes', []):
            if node_data.get('id') == self.selected_node_id:
                node_data['locked'] = new_locked_state
                break
        
        logger.info(f"Node {self.selected_node_id} {status}")
        self._refresh_lock_button_state()
        self.status_message.emit(f"Component {status}", 2000)
    
    # ======================== Edge Operations ========================
    
    def _on_draw_clicked(self):
        """
        Toggle drawing mode for creating new flow lines (DRAWING MODE ORCHESTRATOR).
        
        State Machine:
        1. Click source node → drawing_from_id = node_id, show status
        2. Click canvas waypoints → drawing_segments.append((x, y)), update preview
        3. Click destination node → finish_drawing()
        4. Select flow type in dialog (FlowTypeSelectionDialog)
        5. Save edge to JSON, add to scene, emit diagram_changed signal
        
        Drawing mode is enabled/disabled by toggling this state. When enabled:
        - QGraphicsView's mousePressEvent filters clicks
        - mouseMoveEvent renders preview line
        - ESC key cancels drawing
        - Button turns GREEN to indicate active mode
        - Status bar shows clear instructions
        - Cursor changes to CROSSHAIR
        
        When disabled:
        - Preview line removed
        - State variables cleared
        - drawing_from_id = None
        - drawing_segments = [] (waypoints cleared)
        - Button returns to normal color
        - Cursor returns to ARROW
        """
        self.drawing_mode = not self.drawing_mode
        
        if self.drawing_mode:
            # Enter drawing mode
            # GREEN button with clear visual indication
            self.ui.Draw_button.setStyleSheet("")
            self.drawing_from_id = None
            self.drawing_segments = []
            
            # Install custom event filter to intercept mouse clicks
            # Install on the viewport (the actual drawable widget)
            self.ui.graphicsView.viewport().installEventFilter(self)
            # Ensure the page has focus so the ESC shortcut is active
            self.setFocus()
            self.ui.graphicsView.setFocus()
            
            # Disable drag mode and change cursor to crosshair for drawing
            self.ui.graphicsView.setDragMode(QGraphicsView.NoDrag)
            self.ui.graphicsView.viewport().setCursor(Qt.CrossCursor)
            self.ui.graphicsView.setCursor(Qt.CrossCursor)
            
            # Clear status message and show drawing instructions
            self.status_message.emit(
                "🎨 DRAWING MODE ACTIVE: "
                "1) Click source component  "
                "2) Click canvas for turns  "
                "3) Click destination component  "
                "4) Choose flow type  |  ESC to cancel",
                0  # Persistent until mode disabled
            )
            logger.info("Entered drawing mode - waiting for source component click")
            logger.debug(f"Event filter installed on viewport: {self.ui.graphicsView.viewport()}")
        else:
            # Exit drawing mode
            self.ui.Draw_button.setStyleSheet("")  # Reset to default styling
            self.ui.graphicsView.viewport().removeEventFilter(self)
            # Restore normal drag mode and cursor
            self.ui.graphicsView.setDragMode(QGraphicsView.NoDrag)
            self.ui.graphicsView.viewport().setCursor(Qt.ArrowCursor)
            self.ui.graphicsView.setCursor(Qt.ArrowCursor)
            
            # Clear drawing state
            self.drawing_segments = []
            self.drawing_from_id = None
            
            # Remove all preview items (lines, anchor indicators)
            if hasattr(self, '_preview_items') and self._preview_items:
                for item in self._preview_items:
                    self.scene.removeItem(item)
                self._preview_items = []
            
            self.status_message.emit("Drawing mode disabled - click Draw to enable", 3000)
            logger.info("Exited drawing mode")
    
    def eventFilter(self, obj, event):
        """
        Intercept mouse events on QGraphicsView viewport when drawing mode is active (EVENT INTERCEPTOR).
        
        Handles:
        - mousePressEvent: Start edge, add waypoint, or complete edge
        - mouseMoveEvent: Render preview line while dragging
        - keyPressEvent: ESC to cancel drawing
        
        ESC Key Behavior:
        - If drawing_from_id is set: Cancel current edge (reset waypoints, keep drawing mode ON)
        - If drawing_from_id is None: Exit drawing mode entirely (turn off GREEN button)
        
        The preview line shows the orthogonal path from drawing_from_id to cursor.
        
        Args:
            obj: QObject that triggered event (viewport widget)
            event: QEvent with type and data
        
        Returns:
            bool: True if event was handled (consumed), False to pass through
        """
        if not self.drawing_mode:
            return super().eventFilter(obj, event)
        
        # Check if this is the graphicsView viewport
        if obj != self.ui.graphicsView.viewport():
            return super().eventFilter(obj, event)
        
        if event.type() == QEvent.MouseMove:
            # Cache last mouse position for immediate preview after first click
            self._last_mouse_scene_pos = self.ui.graphicsView.mapToScene(event.pos())
            return self._on_canvas_mouse_move(event)
        elif event.type() == QEvent.MouseButtonPress:
            return self._on_canvas_mouse_press(event)
        elif event.type() == QEvent.KeyPress:
            # Diagnostic print to confirm keypress events are captured by viewport filter
            logger.debug("KeyPress captured: key=%s", event.key())
            if event.key() == Qt.Key_Escape:
                # Always exit drawing mode on ESC (user-requested behavior)
                if self.drawing_mode:
                    logger.info("Drawing mode disabled by user (ESC pressed)")
                    logger.debug("ESC detected - exiting drawing mode")
                    self._on_draw_clicked()  # Toggle off
                return True
        
        return super().eventFilter(obj, event)
    
    def _on_canvas_mouse_move(self, event):
        """
        Render preview line while drawing edge (PREVIEW RENDERER).
        
        Shows a solid blue line from last waypoint to cursor position.
        Only displays anchor points for nodes NEAR the cursor (within 100px)
        to avoid visual clutter. Highlights snap points within 15px.
        
        Args:
            event: QMouseEvent with cursor position
        
        Returns:
            bool: True (consume event to prevent default handling)
        """
        if not self.drawing_from_id or not self.drawing_segments:
            # No source selected yet - show snap points on hover for easier start
            scene_pos = self.ui.graphicsView.mapToScene(event.pos())
            self._last_mouse_scene_pos = scene_pos
            self._render_hover_anchors(scene_pos)
            return True
        
        # Map screen to scene coordinates
        scene_pos = self.ui.graphicsView.mapToScene(event.pos())
        # Store last mouse position for instant preview after first node selection
        self._last_mouse_scene_pos = scene_pos
        self._last_mouse_modifiers = event.modifiers()
        
        # Render preview using shared helper (supports instant preview after first click)
        self._render_preview_from_scene_pos(scene_pos)
        return True

    def _render_hover_anchors(self, scene_pos: QPointF):
        """
        Render snap points while hovering before selecting a source node (HOVER GUIDES).

        This gives users visual snapping guidance BEFORE the first click, making
        it easier to choose a clean starting alignment for new flow lines.

        Args:
            scene_pos: Current cursor position in scene coordinates
        """
        # Remove old preview graphics (anchor indicators only)
        # DEFENSIVE: Wrap in try-except to handle deleted Qt objects when scene is cleared
        if hasattr(self, '_preview_items') and self._preview_items:
            for item in self._preview_items:
                try:
                    self.scene.removeItem(item)
                except RuntimeError:
                    # Qt C++ object was deleted (e.g., scene cleared), skip gracefully
                    pass
            self._preview_items = []

        # Only show anchor indicators (no preview path yet)
        self._render_anchor_indicators(scene_pos)

    def _render_preview_from_scene_pos(self, scene_pos: QPointF):
        """
        Render the full preview path from current drawing state to a scene position.

        This helper is used by mouse-move previews AND by the first node click to
        show snapping guidance immediately (without waiting for mouse movement).

        Args:
            scene_pos: Current cursor position in scene coordinates
        """
        if not self.drawing_from_id or not self.drawing_segments:
            return

        # Remove old preview graphics (line + anchor indicators)
        if hasattr(self, '_preview_items') and self._preview_items:
            for item in self._preview_items:
                self.scene.removeItem(item)
            self._preview_items = []
        
        # ===== Draw FULL preview path (ALL segments from source through waypoints to cursor) =====
        path = QPainterPath()
        path.moveTo(self.drawing_segments[0])  # Start at source anchor
        
        # Draw through all waypoints
        for segment in self.drawing_segments[1:]:
            path.lineTo(segment)
        
        # Assisted orthogonal routing:
        # - Hold Shift to force 90° segments
        # - Otherwise allow free movement, snapping only when near H/V
        last_point = self.drawing_segments[-1]
        force_orthogonal = bool(self._last_mouse_modifiers & Qt.KeyboardModifier.ShiftModifier)
        snapped_pos = self._snap_to_orthogonal_assisted(last_point, scene_pos, force_orthogonal)
        
        # Draw final segment to cursor (strictly orthogonal)
        path.lineTo(snapped_pos)
        
        # Create preview line (solid, bright blue, thin)
        preview_line = QGraphicsPathItem(path)
        pen = QPen(QColor("#0066FF"))  # Bright blue
        pen.setWidth(1)  # Thin, elegant line (matches FlowEdgeItem 1px)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        preview_line.setPen(pen)
        preview_line.setZValue(5)  # Above nodes but below anchors
        self.scene.addItem(preview_line)
        self._preview_items.append(preview_line)
        
        # Draw visual guide line showing horizontal/vertical snap
        if abs(snapped_pos.x() - scene_pos.x()) > 1 or abs(snapped_pos.y() - scene_pos.y()) > 1:
            # Cursor is being snapped - show guide line
            guide_path = QPainterPath()
            guide_path.moveTo(last_point)
            guide_path.lineTo(snapped_pos)
            guide_line = QGraphicsPathItem(guide_path)
            guide_pen = QPen(QColor("#FF9800"))  # Orange guide
            guide_pen.setWidth(1)
            guide_pen.setStyle(Qt.DashLine)
            guide_line.setPen(guide_pen)
            guide_line.setZValue(4)
            self.scene.addItem(guide_line)
            self._preview_items.append(guide_line)

        # ===== Anchor point indicators (shared with hover) =====
        self._render_anchor_indicators(scene_pos)

        return

    def _find_snap_edge(self, scene_pos: QPointF, snap_distance: float = 15.0) -> Tuple[Optional[int], Optional[FlowEdgeItem]]:
        """Find edge near cursor position for snapping during drawing (EDGE SNAP DETECTION).
        
        When drawing a flow line, check if cursor is near any existing edge.
        If so, return that edge for potential junction connection.
        
        Args:
            scene_pos: Current cursor position in scene coordinates
            snap_distance: Maximum distance to consider as snap-able (pixels)
        
        Returns:
            Tuple of (edge_idx, edge_item) if snap-able edge found, (None, None) otherwise
        """
        nearest_edge_idx = None
        nearest_edge_item = None
        nearest_distance = snap_distance + 1
        
        # Search through all edges in diagram
        for edge_idx, edge_item in enumerate(self.edge_items):
            # Skip if edge_item is not a FlowEdgeItem or doesn't have edge_data
            if not isinstance(edge_item, FlowEdgeItem) or not hasattr(edge_item, 'edge_data'):
                continue
            
            # Safely get from_id and to_id with defaults to avoid KeyError
            from_id = edge_item.edge_data.get('from_id')
            to_id = edge_item.edge_data.get('to_id')
            
            # Skip edges with missing IDs
            if not from_id or not to_id:
                continue
            
            # Don't snap to edges we're drawing FROM (avoid self-connection)
            if from_id == self.drawing_from_id or to_id == self.drawing_from_id:
                continue
            
            # Calculate distance to this edge
            dist = edge_item.distance_to_point(scene_pos)
            
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_edge_idx = edge_idx
                nearest_edge_item = edge_item
        
        return (nearest_edge_idx, nearest_edge_item)
    
    def _render_anchor_indicators(self, scene_pos: QPointF):
        """
        Render nearby anchor points and snap highlight (ANCHOR GUIDE RENDERER).

        Used for both hover-before-start and active preview rendering to keep
        the snapping UX consistent.

        Args:
            scene_pos: Current cursor position in scene coordinates
        """
        # ===== Check for edge snap first (higher priority than anchor snapping) =====
        edge_snap_distance = 15.0
        snap_edge_idx, snap_edge_item = self._find_snap_edge(scene_pos, edge_snap_distance)
        
        # Update edge highlighting
        if snap_edge_idx is not None and snap_edge_item is not None:
            if self._snap_edge_item != snap_edge_item:
                # Highlight new snap edge
                if self._snap_edge_item is not None:
                    try:
                        self._snap_edge_item.set_highlighted(False)  # Unhighlight old
                    except RuntimeError:
                        # Qt C++ object was deleted (e.g., scene cleared), clear the reference
                        pass
                snap_edge_item.set_highlighted(True)  # Highlight new
                self._snap_edge_item = snap_edge_item
                self._snap_edge_idx = snap_edge_idx
        else:
            # No snap edge
            if self._snap_edge_item is not None:
                try:
                    self._snap_edge_item.set_highlighted(False)  # Unhighlight
                except RuntimeError:
                    # Qt C++ object was deleted (e.g., scene cleared), just clear the reference
                    pass
                self._snap_edge_item = None
                self._snap_edge_idx = None
        
        # ===== Only show anchor points for NEARBY nodes (within 100px) =====
        # This reduces visual clutter dramatically
        snap_distance = 15.0
        search_distance = 100.0  # Only show anchors for nodes within this range
        nearest_anchor = None
        nearest_distance = snap_distance + 1

        for node_id, node_item in self.node_items.items():
            # Get node center in scene coordinates
            node_center = node_item.mapToScene(node_item.rect().center())

            # Calculate distance from cursor to node center
            dx = node_center.x() - scene_pos.x()
            dy = node_center.y() - scene_pos.y()
            dist_to_node = (dx*dx + dy*dy) ** 0.5

            # Only show anchors for nodes within search distance
            if dist_to_node > search_distance:
                continue

            # Get all 17 anchor points for this node
            anchor_points = node_item._calculate_anchor_points()

            for anchor_point in anchor_points:
                # Calculate distance from cursor to anchor (in scene coords)
                anchor_scene = node_item.mapToScene(anchor_point)
                dx = anchor_scene.x() - scene_pos.x()
                dy = anchor_scene.y() - scene_pos.y()
                dist = (dx*dx + dy*dy) ** 0.5

                # Track nearest snap point
                if dist < snap_distance and dist < nearest_distance:
                    nearest_distance = dist
                    nearest_anchor = (anchor_scene, node_id)

                # Draw small circle for anchor point
                # Only draw if within snap range, otherwise skip for cleanliness
                if dist < snap_distance:
                    color = Qt.yellow  # Bright yellow when within snap range
                else:
                    continue  # Don't clutter with gray anchors far away

                # Draw small circle for anchor point
                anchor_marker = QGraphicsRectItem(anchor_scene.x()-3, anchor_scene.y()-3, 6, 6)
                anchor_marker.setBrush(QBrush(color))
                anchor_marker.setPen(QPen(QColor("#333333"), 1))
                anchor_marker.setZValue(10)  # On top of preview line
                self.scene.addItem(anchor_marker)
                self._preview_items.append(anchor_marker)

        # ===== Highlight nearest snap point if within snap distance =====
        if nearest_anchor:
            anchor_point, snap_node_id = nearest_anchor
            # Draw large orange circle around snap point
            snap_indicator = QGraphicsRectItem(anchor_point.x()-8, anchor_point.y()-8, 16, 16)
            snap_indicator.setBrush(QBrush(QColor("#ff9800")))  # Bright orange
            snap_indicator.setPen(QPen(QColor("#d84315"), 2))
            snap_indicator.setZValue(11)  # On top of all
            self.scene.addItem(snap_indicator)
            self._preview_items.append(snap_indicator)
    
    def _offset_parallel_edge_waypoints(self, waypoints: List[dict], parallel_index: int) -> List[dict]:
        """
        Calculate offset waypoints for parallel edges (PARALLEL EDGE ROUTER).
        
        When multiple edges exist between the same two nodes, this function adds
        extra waypoints to route each edge differently so they don't stack/overlap.
        
        Strategy:
        - Parallel edges are offset perpendicular to the direct node-to-node direction
        - Odd-indexed parallels offset right, even-indexed offset left (fan effect)
        - Offset increases with parallel_index to spread edges further apart
        - Offset amount: 40px + (index * 20px) = one edge 40px, next 60px, etc.
        
        Args:
            waypoints (list): Original waypoints [{x, y}, ...] INTERMEDIATE POINTS ONLY
                             (NOT including source/destination anchors - those are calculated in _update_path)
            parallel_index (int): Which parallel this is (0=first, 1=second, etc.)
        
        Returns:
            list: New waypoints with extra offset points added for spreading
        
        Example:
            Original: [{x:100, y:100}]  (just destination anchor)
            If source is at (0, 0), destination at (100, 100):
            Parallel 1 (second edge):
            Returns: [
                {x:40, y:0},      # Offset perpendicular from start
                {x:140, y:100}    # Offset perpendicular to end
            ]
            (creates rectangular detour to the right, spreads the edges)
        """
        if parallel_index == 0:
            return waypoints  # No offset for first edge
        
        if len(waypoints) < 1:
            # No waypoints provided - create a default based on edges that need spacing
            # This shouldn't happen but handle gracefully
            return waypoints
        
        # Extract the destination anchor (last waypoint or junction_pos equivalent)
        # The source anchor will be added by _update_path(), so we need to infer it from context
        # Since we don't have direct access to source/dest nodes here, we'll create offset
        # waypoints based on the provided waypoints list
        
        if len(waypoints) == 1:
            # Single waypoint (destination anchor)
            # We need to create intermediate waypoints that offset the edge
            end = waypoints[0]
            end_pt = QPointF(end['x'], end['y']) if isinstance(end, dict) else QPointF(end[0], end[1])
            
            # Calculate offset distance and direction
            offset_distance = 60 + (parallel_index * 30)  # 60px, 90px, 120px, etc. (LARGER offsets)
            direction_right = (parallel_index % 2 == 1)  # Odd = right, even = left
            
            # For simple case, offset perpendicular direction
            # We'll offset the point horizontally then vertically
            offset_x = offset_distance if direction_right else -offset_distance
            
            # Create offset intermediate waypoint that creates a detour
            offset_waypoint = {
                'x': end_pt.x() + offset_x,
                'y': end_pt.y()
            }
            
            return [offset_waypoint]
        else:
            # Multiple waypoints - offset all of them
            new_waypoints = []
            for wp in waypoints:
                wp_pt = QPointF(wp['x'], wp['y']) if isinstance(wp, dict) else QPointF(wp[0], wp[1])
                
                offset_distance = 60 + (parallel_index * 30)  # LARGER offsets: 60px, 90px, 120px, etc.
                direction_right = (parallel_index % 2 == 1)
                offset_x = offset_distance if direction_right else -offset_distance
                
                offset_wp = {
                    'x': wp_pt.x() + offset_x,
                    'y': wp_pt.y()
                }
                new_waypoints.append(offset_wp)
            
            return new_waypoints

    def _snap_to_orthogonal_strict(self, reference_point, cursor_pos):
        """
        FORCE orthogonal routing - ALWAYS snap to horizontal OR vertical (STRICT MODE).
        
        No diagonal lines allowed - only clean 90° turns for professional flow diagrams.
        Chooses H or V based on which direction has more mouse movement from reference.
        
        Algorithm:
        - If horizontal distance > vertical distance → snap to HORIZONTAL
        - If vertical distance > horizontal distance → snap to VERTICAL
        - Equal distance → prefer horizontal
        
        Args:
            reference_point: QPointF of last waypoint (snap reference)
            cursor_pos: QPointF of current mouse position
        
        Returns:
            QPointF: Snapped position (ALWAYS horizontal OR vertical, never diagonal)
        
        Example:
            last_point = QPointF(100, 200)
            cursor = QPointF(150, 250)  # dx=50, dy=50
            snapped = _snap_to_orthogonal_strict(last_point, cursor)
            # Returns (150, 200) - horizontal (equal distance, prefer H)
        """
        dx = abs(cursor_pos.x() - reference_point.x())
        dy = abs(cursor_pos.y() - reference_point.y())
        
        # Choose direction with MORE movement (prefer horizontal on ties)
        if dx >= dy:
            # Snap to horizontal (keep X from cursor, Y from reference)
            return QPointF(cursor_pos.x(), reference_point.y())
        else:
            # Snap to vertical (keep Y from cursor, X from reference)
            return QPointF(reference_point.x(), cursor_pos.y())

    def _snap_to_orthogonal_assisted(self, reference_point: QPointF, cursor_pos: QPointF, force: bool) -> QPointF:
        """Snap to 90° only when requested or when cursor is nearly aligned (ASSISTED ROUTING).

        This keeps drawing flexible while still helping users make clean right angles.

        Args:
            reference_point: Last waypoint (scene coordinates).
            cursor_pos: Current mouse position (scene coordinates).
            force: If True, always snap to horizontal/vertical (Shift key).

        Returns:
            QPointF: Snapped or original cursor position.
        """
        if force:
            return self._snap_to_orthogonal_strict(reference_point, cursor_pos)

        # Soft snap: only snap if cursor is close to horizontal/vertical alignment.
        tolerance = 12.0
        dx = abs(cursor_pos.x() - reference_point.x())
        dy = abs(cursor_pos.y() - reference_point.y())

        if dx <= tolerance:
            return QPointF(reference_point.x(), cursor_pos.y())
        if dy <= tolerance:
            return QPointF(cursor_pos.x(), reference_point.y())

        return cursor_pos
    
    def _create_junction_and_split_edge(self, edge_idx: int, junction_pos: QPointF) -> str:
        """Create new junction node and split edge into two parts (EDGE SPLITTING FOR JUNCTIONS).
        
        When user connects a flow line to an existing edge, split that edge at the
        connection point by:
        1. Creating a new junction node at click position
        2. Splitting edge A→B into A→Junction and Junction→B
        3. Updating waypoints appropriately
        4. Returning the new junction node ID for the incoming edge connection
        
        Args:
            edge_idx: Index of edge to split in diagram_data['edges']
            junction_pos: Scene coordinate where junction should be placed
        
        Returns:
            str: Node ID of the new junction node
        
        Raises:
            ValueError: If edge_idx invalid or edge not found
        """
        if edge_idx < 0 or edge_idx >= len(self.diagram_data.get('edges', [])):
            raise ValueError(f"Invalid edge index: {edge_idx}")
        
        edge_to_split = self.diagram_data['edges'][edge_idx]
        old_from_id = edge_to_split['from_id']
        old_to_id = edge_to_split['to_id']
        
        # Generate unique junction node ID
        junction_id = f"junction_{len(self.diagram_data.get('nodes', []))}_{int(time.time() * 1000) % 10000}"
        
        # Create junction node at connection point
        junction_node = {
            'id': junction_id,
            'label': 'Junction',
            'type': 'junction',  # Mark as auto-created junction
            'shape': 'oval',
            'fill': '#CCCCCC',  # Light gray
            'outline': '#666666',
            'locked': False,
            'x': junction_pos.x() - 20,  # Center on junction_pos
            'y': junction_pos.y() - 15,
            'width': 40,
            'height': 30
        }
        self.diagram_data['nodes'].append(junction_node)
        
        # Create new junction node item in graphics scene
        junction_item = FlowNodeItem(junction_id, junction_node)
        junction_item.node_moved.connect(self._on_node_moved)
        junction_item.node_selected.connect(self._on_node_selected)
        junction_item.node_double_clicked.connect(self._on_node_double_clicked)
        self.scene.addItem(junction_item)
        self.node_items[junction_id] = junction_item
        
        # Get properties from old edge (split at the junction point)
        old_waypoints = edge_to_split.get('waypoints', [])
        old_flow_type = edge_to_split.get('flow_type', 'clean')
        old_color = edge_to_split.get('color', None)
        old_volume = edge_to_split.get('volume', 0)
        
        # Find where to split waypoints (closest point before junction)
        # For now, just use empty waypoints for both halves (can be improved with more complex logic)
        waypoints_to_junction = []
        waypoints_from_junction = []
        
        # Update original edge: old_from_id → junction_id
        edge_to_split['to_id'] = junction_id
        edge_to_split['waypoints'] = waypoints_to_junction
        
        # Remove old edge graphics
        if edge_idx < len(self.edge_items):
            old_edge_item = self.edge_items[edge_idx]
            self.scene.removeItem(old_edge_item)
        
        # Create new edge graphics for modified original edge
        new_edge_item = FlowEdgeItem(edge_idx, edge_to_split, self.node_items[old_from_id], junction_item)
        new_edge_item.edge_selected.connect(self._on_edge_selected)
        new_edge_item.edge_double_clicked.connect(self._on_edge_double_clicked)
        self.scene.addItem(new_edge_item)
        self.edge_items[edge_idx] = new_edge_item
        
        # Create new edge: junction_id → old_to_id (with half the volume)
        new_edge_data = {
            'from_id': junction_id,
            'to_id': old_to_id,
            'flow_type': old_flow_type,
            'color': old_color,
            'volume': old_volume / 2 if old_volume else 0,  # Split volume
            'waypoints': waypoints_from_junction,
            'excel_mapping': edge_to_split.get('excel_mapping', {})
        }
        self.diagram_data['edges'].append(new_edge_data)
        
        # Create edge graphics for new edge
        new_edge_idx = len(self.diagram_data['edges']) - 1
        new_edge_item2 = FlowEdgeItem(new_edge_idx, new_edge_data, junction_item, self.node_items[old_to_id])
        new_edge_item2.edge_selected.connect(self._on_edge_selected)
        new_edge_item2.edge_double_clicked.connect(self._on_edge_double_clicked)
        self.scene.addItem(new_edge_item2)
        self.edge_items.append(new_edge_item2)
        
        # Update original edge volume to half
        edge_to_split['volume'] = old_volume / 2 if old_volume else 0
        
        logger.info(f"Split edge {old_from_id} -> {old_to_id} at junction {junction_id}")
        self.status_message.emit(f"Junction created: {junction_id}", 2000)
        
        return junction_id
    
    def _on_canvas_mouse_press(self, event):
        """
        Handle canvas clicks during drawing mode (WAYPOINT COLLECTOR).
        
        Click behavior:
        1. First click on source node: drawing_from_id = node_id, add anchor point
        2. Clicks on canvas: Add waypoint, check for destination node
        3. Click on destination node (≠ source): Finalize edge, show flow type dialog
        4. Click on edge during drawing: Create junction and connect to junction
        5. Click on source node again: Cancel and reset
        
        Args:
            event: QMouseEvent with click position
        
        Returns:
            bool: True (consume event to prevent default handling)
        """
        scene_pos = self.ui.graphicsView.mapToScene(event.pos())
        logger.debug(f"Canvas click at scene pos: ({scene_pos.x():.0f}, {scene_pos.y():.0f})")
        self._last_mouse_modifiers = event.modifiers()
        
        # Check if clicked on a node or edge - iterate through items instead of itemAt
        # which can be unreliable with complex transforms
        clicked_item = None
        for item in self.scene.items(scene_pos):
            if isinstance(item, FlowNodeItem):
                clicked_item = item
                break
            elif isinstance(item, FlowEdgeItem) and self.drawing_from_id is not None and len(self.drawing_segments) > 0:
                # Only allow edge clicks if we're in the middle of drawing
                clicked_item = item
                break
        
        logger.debug(f"Item at click position: {type(clicked_item).__name__ if clicked_item else 'None'}")
        
        if isinstance(clicked_item, FlowNodeItem):
            # Clicked on a node
            node_id = clicked_item.node_id
            anchor_point = clicked_item.get_nearest_anchor_point(scene_pos)
            logger.info(f"Clicked on node: {node_id}, anchor at ({anchor_point.x():.0f}, {anchor_point.y():.0f})")
            
            if self.drawing_from_id is None:
                # Start new edge - first click on source node
                self.drawing_from_id = node_id
                self.drawing_segments = [anchor_point]
                self.status_message.emit(
                    f"Source: {node_id} → Click waypoints or edge → destination component",
                    0
                )
                logger.info(f"Drawing started from node: {node_id}")
                # Render snap preview immediately using last mouse position (if available)
                if self._last_mouse_scene_pos is not None:
                    self._render_preview_from_scene_pos(self._last_mouse_scene_pos)
                else:
                    # If mouse hasn't moved yet, draw a short stub to show direction
                    # This gives immediate visual feedback after the first click.
                    stub_pos = QPointF(anchor_point.x() + 20, anchor_point.y())
                    self._render_preview_from_scene_pos(stub_pos)
                return True
            
            elif node_id != self.drawing_from_id:
                # Clicked on destination node (different from source)
                logger.info(f"Destination node clicked: {node_id}")
                self._finish_drawing(node_id, anchor_point)
                return True
            
            else:
                # Clicked on source node again - cancel drawing
                logger.info("User clicked source node again - cancelling drawing")
                self._cancel_drawing()
                return True
        
        elif isinstance(clicked_item, FlowEdgeItem) and self.drawing_from_id is not None:
            # Clicked on an edge - snap to it and connect without splitting the existing flow
            edge_idx = clicked_item.edge_idx
            
            # Get the exact snap point on the edge
            snap_point = clicked_item.get_point_on_path(scene_pos)
            if snap_point is None:
                logger.warning(f"Could not get snap point on edge {edge_idx}")
                return True
            
            # Create a virtual junction connection (metadata only, no junction node)
            junction_id = f"junction:{int(snap_point.x())}:{int(snap_point.y())}"
            self._finish_drawing(junction_id, snap_point, is_junction=True, junction_pos=snap_point)
            return True
        
        else:
            # Clicked on canvas (not on a node or edge)
            if self.drawing_from_id:
                # A source node is already selected - add waypoint (STRICT ORTHOGONAL)
                # Shift forces 90° alignment, otherwise allow free movement with soft snap
                last_point = self.drawing_segments[-1]
                force_orthogonal = bool(self._last_mouse_modifiers & Qt.KeyboardModifier.ShiftModifier)
                waypoint = self._snap_to_orthogonal_assisted(last_point, scene_pos, force_orthogonal)
                self.drawing_segments.append(waypoint)
                logger.debug(f"Waypoint added: ({waypoint.x():.0f}, {waypoint.y():.0f}), total: {len(self.drawing_segments)}")
                self.status_message.emit(
                    f"Waypoint added ({len(self.drawing_segments)} total) → Click destination or edge",
                    5000  # Auto-clear after 5 seconds
                )
                return True
            else:
                # No source selected yet - ignore canvas clicks
                logger.debug("Canvas click before source node selected - ignoring")
                return True
    
    def _build_orthogonal_path(self, start_point, end_point, angle_start='horizontal'):
        """
        Build orthogonal (90° angle only) path between two points (ROUTING ENGINE).
        
        Creates a path using only horizontal and vertical segments. The path
        alternates between horizontal and vertical moves.
        
        Routing algorithm:
        1. If angle_start='horizontal': Move X first, then Y
        2. If angle_start='vertical': Move Y first, then X
        3. Result: L-shaped path with single waypoint at corner
        
        This ensures clean, grid-aligned flow lines that are easy to read
        and visually consistent.
        
        Args:
            start_point: QPointF where path starts
            end_point: QPointF where path ends
            angle_start: 'horizontal' (X first) or 'vertical' (Y first)
        
        Returns:
            QPainterPath: Orthogonal path from start to end
        
        Example:
            start = QPointF(0, 0)
            end = QPointF(100, 50)
            path = build_orthogonal_path(start, end, 'horizontal')
            # Creates path: (0,0) → (100,0) → (100,50)
        """
        path = QPainterPath()
        path.moveTo(start_point)
        
        if angle_start == 'horizontal':
            # Move horizontally first, then vertically
            corner = QPointF(end_point.x(), start_point.y())
        else:
            # Move vertically first, then horizontally
            corner = QPointF(start_point.x(), end_point.y())
        
        path.lineTo(corner)
        path.lineTo(end_point)
        
        return path
    
    def _finalize_edge(self, to_node_id, to_anchor_point):
        """
        Complete edge drawing and show flow type dialog (EDGE FINALIZER).
        
        Steps:
        1. Show FlowTypeSelectionDialog to user
        2. If accepted: Create edge_data dict with all waypoints
        3. Add edge to diagram_data['edges']
        4. Create FlowEdgeItem and add to scene
        5. Connect signals for selection/editing
        6. Clear drawing state
        7. Emit diagram_changed signal for persistence
        
        Args:
            to_node_id: Destination node ID
            to_anchor_point: QPointF of destination anchor (snapped)
        
        Side effects:
            - Modifies diagram_data['edges']
            - Adds item to scene
            - Emits diagram_changed signal
            - Resets drawing_from_id, drawing_segments
        """
        from ui.dialogs.flow_type_selection_dialog import FlowTypeSelectionDialog
        
        # Show flow type selection dialog
        dialog = FlowTypeSelectionDialog(self)
        if dialog.exec() != QDialog.Accepted:
            logger.info("Flow type dialog cancelled - edge not created")
            return
        
        flow_type = dialog.get_selected_flow_type()
        logger.info(f"Edge created: {self.drawing_from_id} -> {to_node_id}, type: {flow_type}")
        
        # Build waypoints list: start anchor + all canvas waypoints + end anchor
        waypoints = [
            {'x': p.x(), 'y': p.y()} if isinstance(p, QPointF) 
            else p 
            for p in self.drawing_segments
        ] + [{'x': to_anchor_point.x(), 'y': to_anchor_point.y()}]
        
        # Count parallel edges (multiple edges between same two nodes) to add offset
        # This prevents edges from stacking on top of each other visually
        parallel_edge_count = 0
        for edge in self.diagram_data['edges']:
            if (edge.get('from_id') == self.drawing_from_id and edge.get('to_id') == to_node_id):
                parallel_edge_count += 1
        
        # If this is a parallel edge (not the first), add offset waypoints to route it differently
        # Offset alternates: right, left, right, left, etc. to fan out the edges
        if parallel_edge_count > 0:
            waypoints = self._offset_parallel_edge_waypoints(waypoints, parallel_edge_count)
        
        # Create edge_data dict
        edge_data = {
            'from_id': self.drawing_from_id,
            'to_id': to_node_id,
            'flow_type': flow_type,
            'volume': 0.0,  # Will be populated by Excel loader
            'waypoints': waypoints,
            'label_offset': 0.5  # 50% along path
        }
        
        # Add to diagram JSON data
        self.diagram_data['edges'].append(edge_data)
        edge_idx = len(self.diagram_data['edges']) - 1
        
        # Create FlowEdgeItem and add to scene
        from ui.components.flow_graphics_items import FlowEdgeItem
        
        from_node = self.node_items[self.drawing_from_id]
        to_node = self.node_items[to_node_id]
        
        edge_item = FlowEdgeItem(
            edge_idx=edge_idx,
            edge_data=edge_data,
            from_node=from_node,
            to_node=to_node
        )
        edge_item.edge_selected.connect(self._on_edge_selected)
        edge_item.edge_double_clicked.connect(self._on_edge_double_clicked)
        
        self.scene.addItem(edge_item)
        self.edge_items.append(edge_item)
        
        # Reset drawing state
        self.drawing_from_id = None
        self.drawing_segments = []
        
        # Remove all preview items (lines, anchor indicators)
        if hasattr(self, '_preview_items') and self._preview_items:
            for item in self._preview_items:
                self.scene.removeItem(item)
            self._preview_items = []
        
        self.status_message.emit(f"Flow created: {self.drawing_from_id} → {to_node_id}", 5000)
        self.diagram_changed.emit()
    
    def _finish_drawing(
        self,
        to_node_id: str,
        to_anchor_point: QPointF,
        is_junction: bool = False,
        junction_pos: Optional[QPointF] = None
    ):
        """
        Finalize edge drawing and save to diagram (EDGE FINALIZER).
        
        Called when user clicks on destination node or edge. Opens flow type selection dialog,
        then adds completed edge to diagram_data and renders it on scene.
        
        Steps:
        1. Validate: to_node_id != drawing_from_id (no self-loops, junctions excluded)
        2. Get source node data
        3. Open EditFlowDialog to get flow_type and volume
        4. Create edge object with waypoints
        5. Add to diagram_data['edges']
        6. Create FlowEdgeItem and add to scene
        7. Clear drawing state
        8. Emit diagram_changed signal
        
        Args:
            to_node_id: ID of destination node or virtual junction ID
            to_anchor_point: Anchor point on destination (scene coords)
            is_junction: True when destination is a flowline junction point
            junction_pos: Scene coordinate of the junction (required when is_junction=True)
        
        Returns:
            None
        """
        is_junction = bool(is_junction)
        if is_junction and junction_pos is None:
            logger.error("Junction connection missing junction_pos")
            self.status_message.emit("Error: junction point missing", 3000)
            self._cancel_drawing()
            return

        # Validate: not a self-loop (junctions are metadata, so skip validation)
        if not is_junction and to_node_id == self.drawing_from_id:
            logger.warning(f"Ignoring self-loop attempt: {to_node_id} -> {to_node_id}")
            QMessageBox.warning(self, "Invalid Flow", "Cannot connect a component to itself")
            self._cancel_drawing()
            return
        
        # Get source node anchor point
        source_node_item = self.node_items.get(self.drawing_from_id)
        if not source_node_item:
            logger.error(f"Source node not found: {self.drawing_from_id}")
            self._cancel_drawing()
            return
        
        source_anchor = self.drawing_segments[0]  # First point in segments list
        
        # Combine all waypoints: intermediate waypoints ONLY (without source and destination anchors)
        # The source and destination anchors are calculated by _update_path() based on nodes
        # Waypoints should be intermediate clicks on the canvas (if any)
        # drawing_segments[0] = source anchor (not included)
        # drawing_segments[1:] = intermediate waypoints (these should be included)
        waypoints_raw = self.drawing_segments[1:] if len(self.drawing_segments) > 1 else []
        
        # Convert waypoints to serializable format [x, y] for JSON storage
        waypoints = []
        for wp in waypoints_raw:
            if hasattr(wp, 'x') and hasattr(wp, 'y'):
                waypoints.append([wp.x(), wp.y()])
            elif isinstance(wp, (list, tuple)) and len(wp) == 2:
                waypoints.append(list(wp))
        
        # Open flow properties dialog
        from_node_data = None
        to_node_data = None
        for nd in self.diagram_data.get('nodes', []):
            if nd.get('id') == self.drawing_from_id:
                from_node_data = nd
            if not is_junction and nd.get('id') == to_node_id:
                to_node_data = nd

        if is_junction:
            to_node_data = {
                'id': to_node_id,
                'label': 'Junction'
            }
        
        from ui.dialogs.edit_flow_dialog import EditFlowDialog
        dialog = EditFlowDialog(
            self,
            edge_idx=None,  # New edge
            edge_data={
                'from_id': self.drawing_from_id,
                'to_id': to_node_id,
                'flow_type': 'transfer',  # Default
                'color': '#0066CC',       # Default blue
                'volume': 0,              # Default
                'waypoints': waypoints    # Collected during drawing
            },
            from_node_data=from_node_data,
            to_node_data=to_node_data,
            is_new_edge=True
        )
        
        if dialog.exec() == QDialog.Accepted:
            edge_data = dialog.get_flow_data()
            
            # Add edge to diagram data
            self.diagram_data['edges'].append(edge_data)
            edge_idx = len(self.diagram_data['edges']) - 1
            
            if is_junction and junction_pos is not None:
                edge_data['is_junction'] = True
                edge_data['junction_pos'] = {
                    'x': junction_pos.x(),
                    'y': junction_pos.y()
                }

            # Get node items for rendering
            from_node_item = self.node_items.get(self.drawing_from_id)
            to_node_item = self.node_items.get(to_node_id) if not is_junction else None
            
            if from_node_item and (to_node_item or is_junction):
                # Create graphics item for edge with proper node references
                edge_item = FlowEdgeItem(
                    edge_idx=edge_idx,
                    edge_data=edge_data,
                    from_node=from_node_item,
                    to_node=to_node_item
                )
                self.scene.addItem(edge_item)
                self.edge_items.append(edge_item)
                
                # Set Z-value so edges appear behind nodes
                edge_item.setZValue(0)
                # Ensure nodes are in front
                for node_item in self.node_items.values():
                    node_item.setZValue(1)
                
                # Connect signals
                edge_item.edge_selected.connect(self._on_edge_selected)
                edge_item.edge_double_clicked.connect(self._on_edge_double_clicked)
                
                logger.info(
                    f"[OK] Created edge: {self.drawing_from_id} -> {to_node_id}, "
                    f"waypoints={len(waypoints)}, type={edge_data.get('flow_type')}"
                )
                self.status_message.emit(
                    f"[OK] Flow created: {self.drawing_from_id} -> {to_node_id} | Click Draw again to draw more flows",
                    5000
                )
                self.diagram_changed.emit()
            else:
                logger.error(f"Missing node items: from_node={bool(from_node_item)}, to_node={bool(to_node_item)}")
                self.status_message.emit("Error creating flow line", 3000)
        else:
            # User cancelled flow dialog - discard edge
            logger.info("Flow creation cancelled by user")
            self.status_message.emit("Flow cancelled", 2000)
        
        # Clear drawing state
        self._cancel_drawing()
    
    def _cancel_drawing(self):
        """
        Cancel current edge drawing operation (DRAWING CANCELLER).
        
        Resets all drawing state:
        - drawing_from_id = None
        - drawing_segments = []
        - Removes all preview items (lines, anchor indicators) from scene
        - Shows status message
        - Keeps drawing_mode=True (user can start new edge)
        
        Called when:
        - User presses ESC
        - User clicks source node again
        - Edge finalization cancelled
        """
        self.drawing_from_id = None
        self.drawing_segments = []
        
        # Remove all preview items (lines, anchor indicators)
        if hasattr(self, '_preview_items') and self._preview_items:
            for item in self._preview_items:
                self.scene.removeItem(item)
            self._preview_items = []
        
        self.status_message.emit(
            "Drawing cancelled - click source component to start new flow",
            3000
        )
        logger.info("Drawing cancelled and reset")
    
    def _build_orthogonal_path(self, start_point: QPointF, end_point: QPointF, 
                               angle_start: str = 'horizontal') -> QPainterPath:
        """
        Build orthogonal (90° angles) path between two points (PATH BUILDER).
        
        Creates a path with only horizontal and vertical segments (no diagonals).
        Useful for flow diagrams where connections should follow grid directions.
        
        Routing rules:
        1. If angle_start='horizontal': First segment is horizontal, then vertical
        2. If angle_start='vertical': First segment is vertical, then horizontal
        3. Returns QPainterPath with moveTo(start) → lineTo(intermediate) → lineTo(end)
        
        Example:
        - Start (100, 100), End (300, 200), angle_start='horizontal'
        - Path: (100,100) → (300,100) → (300,200)
        
        Args:
            start_point: Starting point (scene coordinates, QPointF)
            end_point: Ending point (scene coordinates, QPointF)
            angle_start: 'horizontal' or 'vertical' for first segment direction
        
        Returns:
            QPainterPath with orthogonal routing
        """
        path = QPainterPath()
        path.moveTo(start_point)
        
        if angle_start == 'horizontal':
            # First horizontal, then vertical
            intermediate = QPointF(end_point.x(), start_point.y())
        else:
            # First vertical, then horizontal
            intermediate = QPointF(start_point.x(), end_point.y())
        
        path.lineTo(intermediate)
        path.lineTo(end_point)
        
        return path
    
    def _on_edit_flow_clicked(self):
        """Open Edit Flow dialog for selected edge."""
        if self.selected_edge_idx is None:
            QMessageBox.warning(self, "No Selection", "Please select a flow line first")
            return

        if not (0 <= self.selected_edge_idx < len(self.diagram_data.get('edges', []))):
            QMessageBox.warning(self, "Not Found", "Selected flow line not found in data")
            return

        edge_data = self.diagram_data.get('edges', [])[self.selected_edge_idx]

        from_node_data = None
        to_node_data = None
        for nd in self.diagram_data.get('nodes', []):
            if nd.get('id') == edge_data.get('from_id'):
                from_node_data = nd
            if nd.get('id') == edge_data.get('to_id'):
                to_node_data = nd

        dialog = EditFlowDialog(self, self.selected_edge_idx, edge_data, from_node_data, to_node_data)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_flow_data()
            edge_data.update(updated_data)

            edge_item = self.selected_edge_item
            if edge_item is None:
                edge_item = next(
                    (item for item in self.edge_items if item.edge_idx == self.selected_edge_idx),
                    None
                )

            if edge_item:
                edge_item.edge_data = edge_data
                edge_item._setup_styling()
                edge_item._setup_volume_label()
                edge_item._update_path()

            self.diagram_changed.emit()
            self.status_message.emit("Flow updated", 2000)
            logger.info(f"Updated flow: {self.selected_edge_idx}")
    
    def _on_delete_flow_clicked(self):
        """Delete selected flow line."""
        if self.selected_edge_idx is None or self.selected_edge_item is None:
            # Fallback: attempt to read selection directly from the scene
            # This covers cases where the edge item is selected but handler state
            # did not update (e.g., missed signal or focus changes).
            selected_items = self.scene.selectedItems()
            logger.info(f"Scene selected items count: {len(selected_items)}")
            selected_edge_item = next(
                (item for item in selected_items if isinstance(item, FlowEdgeItem)),
                None
            )
            if selected_edge_item is not None:
                self.selected_edge_item = selected_edge_item
                self.selected_edge_idx = selected_edge_item.edge_idx
            else:
                QMessageBox.warning(self, "No Selection", "Please select a flow line first")
                return
        
        reply = QMessageBox.question(
            self, "Delete Flow Line",
            "Delete this flow line?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                data_idx = self.selected_edge_idx
                edge_item = self.selected_edge_item
                logger.info(
                    "Delete requested for edge: "
                    f"data_idx={data_idx}, "
                    f"edge_idx={edge_item.edge_idx}, "
                    f"from_id={edge_item.edge_data.get('from_id')}, "
                    f"to_id={edge_item.edge_data.get('to_id')}, "
                    f"data_obj_id={id(edge_item.edge_data)}"
                )

                # Build a match key to remove all duplicate edges between same nodes
                from_id = edge_item.edge_data.get('from_id')
                to_id = edge_item.edge_data.get('to_id')
                waypoints = edge_item.edge_data.get('waypoints', [])
                match_key = (from_id, to_id, tuple(map(tuple, waypoints)))
                logger.info(f"Deleting rendered edge(s): {from_id} -> {to_id}")

                # Remove all matching graphics items (handles duplicate overlays)
                items_to_remove = [
                    item for item in self.edge_items
                    if (
                        item.edge_data.get('from_id'),
                        item.edge_data.get('to_id'),
                        tuple(map(tuple, item.edge_data.get('waypoints', [])))
                    ) == match_key
                ]
                for item in items_to_remove:
                    self.scene.removeItem(item)
                    if item in self.edge_items:
                        self.edge_items.remove(item)

                # Remove matching edges from diagram data (handles duplicates)
                edges_data = self.diagram_data.get('edges', [])
                removed_edges = []
                remaining_edges = []
                for edge in edges_data:
                    edge_key = (
                        edge.get('from_id') or edge.get('from'),
                        edge.get('to_id') or edge.get('to'),
                        tuple(map(tuple, edge.get('waypoints', [])))
                    )
                    if edge_key == match_key:
                        removed_edges.append(edge)
                    else:
                        remaining_edges.append(edge)
                self.diagram_data['edges'] = remaining_edges
                for removed in removed_edges:
                    logger.debug(
                        f"Removed edge from data: {removed.get('from_id') or removed.get('from')} → "
                        f"{removed.get('to_id') or removed.get('to')}"
                    )

                # Re-sync edge data indices after deletion
                for item in self.edge_items:
                    try:
                        item.edge_idx = self.diagram_data['edges'].index(item.edge_data)
                    except ValueError:
                        # Fallback: keep current index if data object is missing
                        logger.warning("Edge data object missing after delete; keeping edge_idx")

                # Clear selection
                self.selected_edge_idx = None
                self.selected_edge_item = None

                # Force a repaint so removed items disappear immediately
                self.scene.update()

                # Emit diagram changed signal
                self.diagram_changed.emit()
                self.status_message.emit("[OK] Flow line deleted successfully", 2000)
                logger.info(
                    f"Edge deletion complete. Remaining edges: {len(self.edge_items)}"
                )

            except Exception as e:
                logger.error(f"Error deleting edge: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to delete flow line: {e}")
    
    # ======================== View Operations ========================
    
    def _on_zoom_in(self):
        """Zoom in graphics view by 10%."""
        self.ui.graphicsView.scale(1.1, 1.1)
        logger.debug("Zoomed in")
    
    def _on_zoom_out(self):
        """Zoom out graphics view by 10%."""
        self.ui.graphicsView.scale(0.9, 0.9)
        logger.debug("Zoomed out")
    
    # ======================== Excel Operations ========================
    
    def _on_load_excel_clicked(self):
        """
        Load flow volumes from Excel for selected month/year.
        
        Retrieves:
        - Year from comboBox_filter_year
        - Month from comboBox_filter_month
        
        Updates all edges with volume data from Excel via ExcelManager.
        Then re-renders edges with updated volume labels.
        """
        year = int(self.ui.comboBox_filter_year.currentData())
        month = int(self.ui.comboBox_filter_month.currentData())
        
        logger.info(f"Loading Excel volumes for {month}/{year}")
        self.status_message.emit(f"Loading Excel data for {month}/{year}...", 0)

        excel_manager = get_excel_manager()
        edges = self.diagram_data.get('edges', [])

        updated_count = 0
        missing_count = 0
        for edge in edges:
            excel_mapping = edge.get('excel_mapping', {})
            column_name = excel_mapping.get('column')
            if not column_name:
                missing_count += 1
                continue

            sheet_name = excel_mapping.get('sheet') or excel_manager.resolve_flow_sheet_name(self.area_code)
            volume = excel_manager.get_flow_volume(sheet_name, column_name, year, month)

            if volume is None:
                missing_count += 1
                continue

            edge['volume'] = volume
            updated_count += 1

        # Re-render to update labels with new volumes
        self._render_diagram()

        self.status_message.emit(
            f"Loaded {updated_count} flow volumes ({missing_count} unmapped)",
            3000
        )
    
    def _on_excel_setup_clicked(self):
        """Open Excel Setup dialog for configuring column mappings."""
        dialog = ExcelSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            logger.info("Excel setup complete")
            self.status_message.emit("Excel setup saved", 3000)
    
    # ======================== Utility Operations ========================
    
    def _update_balance_check_labels(self):
        """Calculate water balance and update footer labels (AUTO-BALANCE UPDATE).
        
        Reads flow categorizations from saved JSON file and calculates:
        - Total Inflows (m³)
        - Total Outflows (m³)
        - Balance Error (%)
        
        Updates the labels at the bottom of the flow diagram automatically.
        
        Called after:
        - Load Excel (auto-update when volumes change)
        - Balance Check dialog closes (if categories were saved)
        """
        try:
            # If Excel has not been loaded in this session, keep balance footer cleared.
            if not getattr(self, "_excel_data_loaded_for_session", False):
                self.ui.total_inflows_value.setText("0")
                self.ui.recirculation_value.setText("0")
                self.ui.total_outflows_value.setText("0")
                self.ui.balance_check_value.setText("0.0")
                self.ui.balance_check_value.setStyleSheet("color:#5b6775; font-weight:700;")
                if hasattr(self, "_balance_badge"):
                    self._balance_badge.setStyleSheet(
                        "background-color:#eef3f8; border:1px solid #c7d0da; border-radius:14px;"
                    )
                return

            # Load saved flow categorizations from JSON
            categories_file = self._ensure_user_data_copy(Path("balance_check_flow_categories.json"))
            flow_categories = {}
            
            try:
                with open(categories_file, 'r') as f:
                    categories_data = json.load(f)
                    flow_categories = categories_data.get(self.area_code, {})
            except FileNotFoundError:
                # No categories saved yet - default all to "Ignore"
                flow_categories = {}
            
            # Calculate totals from categorized flows
            inflows = 0.0
            outflows = 0.0
            recirculation = 0.0
            
            # Process regular flow edges
            edges = self.diagram_data.get('edges', [])
            for row, edge in enumerate(edges):
                # Get saved category for this edge (using legacy key format)
                category = flow_categories.get(str(row), "Ignore")
                
                # Get volume from edge
                volume_str = edge.get('volume', '0')
                try:
                    volume = float(str(volume_str).replace(',', ''))
                except (ValueError, AttributeError):
                    volume = 0.0
                
                # Accumulate by category
                if category == "Inflow":
                    inflows += volume
                elif category == "Outflow":
                    outflows += volume
                elif category == "Recirculation":
                    recirculation += volume
            
            # Process recirculation entries (self-loops with recirculation volumes)
            recirculation_entries = self.diagram_data.get('recirculation', [])
            node_lookup = {node.get('id'): node for node in self.diagram_data.get('nodes', [])}
            
            for recirc_entry in recirculation_entries:
                component_id = recirc_entry.get('component_id', '')
                flow_key = f"recirc::{component_id}"
                
                # Get saved category (defaults to "Recirculation")
                category = flow_categories.get(flow_key, "Recirculation")
                
                # Get recirculation volume from node data
                node_data = node_lookup.get(component_id, {})
                volume = node_data.get('recirculation_volume', 0.0)
                
                try:
                    volume = float(volume) if volume else 0.0
                except (ValueError, AttributeError):
                    volume = 0.0
                
                # Accumulate by category
                if category == "Inflow":
                    inflows += volume
                elif category == "Outflow":
                    outflows += volume
                elif category == "Recirculation":
                    recirculation += volume
            
            # Calculate balance error
            balance_numerator = inflows - outflows - recirculation
            balance_error_pct = (abs(balance_numerator) / inflows * 100) if inflows > 0 else 0
            
            # Update footer labels (units are in separate labels)
            self.ui.total_inflows_value.setText(f"{inflows:,.0f}")
            self.ui.recirculation_value.setText(f"{recirculation:,.0f}")
            self.ui.total_outflows_value.setText(f"{outflows:,.0f}")
            self.ui.balance_check_value.setText(f"{balance_error_pct:.1f}")
            
            # Color code balance error
            if balance_error_pct < 5:
                self.ui.balance_check_value.setStyleSheet(
                    "color:#2e7d32; font-weight:700;"
                )
                if hasattr(self, "_balance_badge"):
                    self._balance_badge.setStyleSheet(
                        "background-color:#e7f4ea; border:1px solid #bfe2c6; border-radius:14px;"
                    )
            elif balance_error_pct < 10:
                self.ui.balance_check_value.setStyleSheet(
                    "color:#b26a00; font-weight:700;"
                )
                if hasattr(self, "_balance_badge"):
                    self._balance_badge.setStyleSheet(
                        "background-color:#fff4e5; border:1px solid #f0d29d; border-radius:14px;"
                    )
            else:
                self.ui.balance_check_value.setStyleSheet(
                    "color:#b3261e; font-weight:700;"
                )
                if hasattr(self, "_balance_badge"):
                    self._balance_badge.setStyleSheet(
                        "background-color:#fdeceb; border:1px solid #f3c5c1; border-radius:14px;"
                    )
            
            logger.debug(f"Balance check labels updated: Inflows={inflows:.0f}, Recirculation={recirculation:.0f}, Outflows={outflows:.0f}, Error={balance_error_pct:.1f}%")
            
            # Get current month/year from combo boxes
            current_month = self.ui.comboBox_filter_month.currentIndex() + 1
            current_year = int(self.ui.comboBox_filter_year.currentText()) if self.ui.comboBox_filter_year.currentText() else datetime.datetime.now().year
            
            # Emit signal to notify dashboard of balance update
            self.balance_data_updated.emit({
                'total_inflows': inflows,
                'total_outflows': outflows,
                'recirculation': recirculation,
                'balance_error': balance_error_pct,
                'month': current_month,
                'year': current_year
            })
            
        except Exception as e:
            logger.error(f"Error updating balance check labels: {e}", exc_info=True)
    
    def get_balance_summary(self) -> dict:
        """Get current balance data summary (PUBLIC API FOR DASHBOARD).
        
        Returns dict with keys: total_inflows, total_outflows, recirculation, balance_error, month, year
        Used by main dashboard to display balance status cards.
        """
        try:
            if not getattr(self, "_excel_data_loaded_for_session", False):
                return {
                    'total_inflows': 0.0,
                    'total_outflows': 0.0,
                    'recirculation': 0.0,
                    'balance_error': 0.0,
                    'month': self.ui.comboBox_filter_month.currentIndex() + 1,
                    'year': int(self.ui.comboBox_filter_year.currentText()) if self.ui.comboBox_filter_year.currentText() else datetime.datetime.now().year
                }

            # Load saved flow categorizations from JSON
            categories_file = self._ensure_user_data_copy(Path("balance_check_flow_categories.json"))
            flow_categories = {}
            
            try:
                with open(categories_file, 'r') as f:
                    categories_data = json.load(f)
                    flow_categories = categories_data.get(self.area_code, {})
            except FileNotFoundError:
                flow_categories = {}
            
            # Calculate totals
            inflows = 0.0
            outflows = 0.0
            recirculation = 0.0
            
            # Process regular flow edges
            edges = self.diagram_data.get('edges', [])
            for row, edge in enumerate(edges):
                category = flow_categories.get(str(row), "Ignore")
                volume_str = edge.get('volume', '0')
                try:
                    volume = float(str(volume_str).replace(',', ''))
                except (ValueError, AttributeError):
                    volume = 0.0
                
                if category == "Inflow":
                    inflows += volume
                elif category == "Outflow":
                    outflows += volume
                elif category == "Recirculation":
                    recirculation += volume
            
            # Process recirculation entries
            recirculation_entries = self.diagram_data.get('recirculation', [])
            node_lookup = {node.get('id'): node for node in self.diagram_data.get('nodes', [])}
            
            for recirc_entry in recirculation_entries:
                component_id = recirc_entry.get('component_id', '')
                flow_key = f"recirc::{component_id}"
                category = flow_categories.get(flow_key, "Recirculation")
                
                node_data = node_lookup.get(component_id, {})
                volume = node_data.get('recirculation_volume', 0.0)
                try:
                    volume = float(volume) if volume else 0.0
                except (ValueError, AttributeError):
                    volume = 0.0
                
                if category == "Inflow":
                    inflows += volume
                elif category == "Outflow":
                    outflows += volume
                elif category == "Recirculation":
                    recirculation += volume
            
            # Calculate balance error
            balance_numerator = inflows - outflows - recirculation
            balance_error_pct = (abs(balance_numerator) / inflows * 100) if inflows > 0 else 0
            
            # Get current month/year from combo boxes
            current_month = self.ui.comboBox_filter_month.currentIndex() + 1
            current_year = int(self.ui.comboBox_filter_year.currentText()) if self.ui.comboBox_filter_year.currentText() else datetime.datetime.now().year
            
            return {
                'total_inflows': inflows,
                'total_outflows': outflows,
                'recirculation': recirculation,
                'balance_error': balance_error_pct,
                'month': current_month,
                'year': current_year
            }
        except Exception as e:
            logger.error(f"Error getting balance summary: {e}", exc_info=True)
            return {
                'total_inflows': 0.0,
                'total_outflows': 0.0,
                'recirculation': 0.0,
                'balance_error': 0.0
            }
    
    def _on_balance_check_clicked(self):
        """Open Balance Check dialog (DATA VALIDATION UI).
        
        Opens modal dialog showing:
        - Water balance calculations
        - Inflows vs outflows comparison
        - Closure error percentage
        - Flow categorization (inflow/outflow/recirculation/ignore)
        """
        logger.info("Balance Check button clicked")
        
        try:
            # Open Balance Check dialog with area_code for context
            dialog = BalanceCheckDialog(self, area_code=self.area_code)
            dialog.exec()
            
            # After dialog closes, update the footer labels in case categories changed
            self._update_balance_check_labels()
            
            logger.info("Balance Check dialog closed")
            
        except Exception as e:
            logger.error(f"Error opening Balance Check: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while opening Balance Check:\n{e}"
            )

    def _on_recirculation_clicked(self):
        """Open Recirculation Manager dialog to configure recirculation mapping (RECIRCULATION MANAGEMENT UI)."""
        try:
            dialog = RecirculationManagerDialog(self.diagram_data, self.diagram_path, self)
            
            if dialog.exec() == QDialog.Accepted:
                # Configuration saved to JSON
                # Reload diagram to apply new recirculation settings
                logger.info("Recirculation configuration updated, reloading diagram...")
                self._load_and_display_recirculation()
                self.status_message.emit("Recirculation configuration saved", 3000)
            
            logger.debug("Recirculation manager dialog closed")
        except Exception as e:
            logger.error(f"Error opening recirculation manager: {e}")
    
    def _on_save_diagram_clicked(self):
        """Save current diagram to JSON file (PERSISTENCE LAYER)."""
        try:
            # CRITICAL: Update node positions from graphics items before saving
            for node_id, node_item in self.node_items.items():
                # Find the node data in diagram_data
                for node_data in self.diagram_data.get('nodes', []):
                    if node_data.get('id') == node_id:
                        # Update position from graphics item
                        pos = node_item.pos()
                        node_data['x'] = pos.x()
                        node_data['y'] = pos.y()
                        # Update locked state
                        node_data['locked'] = node_item.is_locked
                        # Save recirculation badge angle if it exists
                        badge_angle = node_item.get_badge_position()
                        if badge_angle is not None:
                            node_data['badge_angle'] = badge_angle
                        break
            
            # Ensure edges have waypoints in serializable format (list of [x, y])
            for edge in self.diagram_data.get('edges', []):
                # Normalize key names for backward compatibility
                if edge.get('from_id') and not edge.get('from'):
                    edge['from'] = edge['from_id']
                if edge.get('to_id') and not edge.get('to'):
                    edge['to'] = edge['to_id']

                waypoints = edge.get('waypoints', [])
                # Convert QPointF to [x, y] if needed
                serializable_waypoints = []
                for wp in waypoints:
                    if hasattr(wp, 'x') and hasattr(wp, 'y'):
                        # QPointF object - convert to list
                        serializable_waypoints.append([wp.x(), wp.y()])
                    elif isinstance(wp, (list, tuple)) and len(wp) == 2:
                        # Already a list/tuple - keep as is
                        serializable_waypoints.append(list(wp))
                    else:
                        logger.warning(f"Invalid waypoint format: {wp}")
                edge['waypoints'] = serializable_waypoints
                # Keep legacy segments in sync for older JSON consumers
                if 'segments' not in edge:
                    edge['segments'] = serializable_waypoints
            
            # Save to JSON
            with open(self.diagram_path, 'w') as f:
                json.dump(self.diagram_data, f, indent=2)
            
            logger.info(f"[OK] Saved diagram to {self.diagram_path} (nodes: {len(self.diagram_data.get('nodes', []))}, edges: {len(self.diagram_data.get('edges', []))})")
            
            # Show success message to user
            QMessageBox.information(
                self,
                "Diagram Saved",
                f"[OK] Diagram saved successfully!\n\n"
                f"File: {Path(self.diagram_path).name}\n"
                f"Nodes: {len(self.diagram_data.get('nodes', []))}\n"
                f"Flows: {len(self.diagram_data.get('edges', []))}"
            )
            self.status_message.emit("[OK] Diagram saved successfully", 3000)
        except Exception as e:
            logger.error(f"Error saving diagram: {e}", exc_info=True)
            self.status_message.emit(f"Error saving diagram: {e}", 5000)
    
    def _on_load_excel_clicked(self):
        """Load flow volumes from Excel file (USER ACTION).
        
        Checks if Excel file is configured before loading.
        Shows helpful pop-up if not configured, directing user to Excel Setup.
        """
        logger.info("Load Excel button clicked")
        
        try:
            # Get Excel manager singleton
            excel_mgr = get_excel_manager()
            
            # Check if Excel file is configured using the correct method
            excel_path = excel_mgr.get_flow_diagram_path()
            if not excel_path or not excel_path.exists():
                QMessageBox.warning(
                    self,
                    "Excel File Not Configured",
                    "Please configure the Excel file path first.\n\n"
                    "Click 'Excel Setup' button to browse and select your Excel file."
                )
                return
            
            # Load flow volumes from Excel and update diagram
            year = self.ui.comboBox_filter_year.currentData()
            month = self.ui.comboBox_filter_month.currentData()
            
            if not year or not month:
                QMessageBox.warning(
                    self,
                    "Select Date",
                    "Please select a Year and Month from the filters first."
                )
                return
            
            # Load data for each mapped flow
            updated_count = 0
            errors = []
            
            for edge in self.diagram_data.get('edges', []):
                excel_mapping = edge.get('excel_mapping', {})
                if not excel_mapping or not excel_mapping.get('sheet') or not excel_mapping.get('column'):
                    continue  # Skip unmapped flows
                
                sheet_name = excel_mapping['sheet']
                column_name = excel_mapping['column']
                
                try:
                    # Load sheet data
                    df = excel_mgr.load_flow_sheet(sheet_name)
                    if df.empty:
                        continue
                    
                    # Filter by year and month
                    df_filtered = df[(df['Year'] == year) & (df['Month'] == month)]
                    
                    if df_filtered.empty:
                        errors.append(f"No data for {year}/{month} in sheet '{sheet_name}'")
                        continue
                    
                    # Get volume value
                    if column_name in df_filtered.columns:
                        volume_value = df_filtered[column_name].iloc[0]
                        if pd.notna(volume_value):
                            edge['volume'] = float(volume_value)
                            updated_count += 1
                        else:
                            errors.append(f"Empty value for '{column_name}' in {year}/{month}")
                    else:
                        errors.append(f"Column '{column_name}' not found in sheet '{sheet_name}'")
                
                except Exception as e:
                    errors.append(f"Error loading '{column_name}': {str(e)}")
            
            # Re-render diagram to show updated volumes
            if updated_count > 0:
                self._excel_data_loaded_for_session = True
                self._refresh_excel_state_badge()
                # CRITICAL ORDER: First re-render diagram (creates node_items),
                # THEN load recirculation data into those newly created nodes
                self._render_diagram()
                # Now load recirculation data for the selected month/year
                self._load_and_display_recirculation()
            else:
                self._excel_data_loaded_for_session = False
                self._refresh_excel_state_badge()
                # Even if no flows updated, still refresh diagram and recirculation
                self._render_diagram()
                self._load_and_display_recirculation()
            
            # AUTO-UPDATE BALANCE CHECK: Calculate and update footer labels
            # This automatically shows balance metrics without opening the dialog
            self._update_balance_check_labels()
            
            # Show results in a structured dialog (cleaner than plain messagebox text).
            self._show_load_excel_results_dialog(
                updated_count=updated_count,
                year=year,
                month=month,
                warnings=errors,
            )
            logger.info(f"Loaded Excel data: {updated_count} flows updated, {len(errors)} errors")
            
        except Exception as e:
            logger.error(f"Error loading Excel: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while loading Excel:\n{e}"
            )

    def _show_load_excel_results_dialog(
        self,
        updated_count: int,
        year: int,
        month: int,
        warnings: list[str],
    ) -> None:
        """Show structured Load Excel results dialog with compact warning list."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Excel Results")
        dialog.setModal(True)
        dialog.setMinimumWidth(560)
        dialog.setMinimumHeight(300)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        title = QLabel("Load Excel Summary", dialog)
        title.setStyleSheet("font-size:16px; font-weight:700; color:#0f172a;")
        root.addWidget(title)

        subtitle = QLabel(
            f"Updated <b>{updated_count}</b> flow volume(s) for <b>{year}/{month:02d}</b>.",
            dialog
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size:12px; color:#334155;")
        root.addWidget(subtitle)

        if warnings:
            warn_title = QLabel(f"Warnings ({len(warnings)})", dialog)
            warn_title.setStyleSheet("font-size:12px; font-weight:700; color:#92400e;")
            root.addWidget(warn_title)

            warn_list = QListWidget(dialog)
            warn_list.setObjectName("flow_load_excel_warnings")
            warn_list.setMinimumHeight(160)
            for msg in warnings:
                item = QListWidgetItem(msg)
                warn_list.addItem(item)
            root.addWidget(warn_list)
        else:
            ok_note = QLabel("No warnings. All mapped rows loaded successfully.", dialog)
            ok_note.setStyleSheet("font-size:12px; color:#166534;")
            root.addWidget(ok_note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        root.addWidget(buttons)

        dialog.exec()
    
    def _on_excel_setup_clicked(self):
        """Open Excel Setup dialog (CONFIGURATION UI).
        
        Opens modal dialog where user can:
        - Browse and select Excel file
        - Map flow columns to diagram edges
        - Auto-create missing columns
        - Preview and edit Excel data
        """
        logger.info("Excel Setup button clicked")
        
        try:
            # Open Excel Setup dialog
            dialog = ExcelSetupDialog(self)
            dialog.exec()
            
            logger.info("Excel Setup dialog closed")
            
        except Exception as e:
            logger.error(f"Error opening Excel Setup: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while opening Excel Setup:\n{e}"
            )


