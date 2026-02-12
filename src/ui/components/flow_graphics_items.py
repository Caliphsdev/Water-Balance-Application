"""
Flow Diagram Custom Graphics Items (PySide6 QGraphicsItem subclasses).

This module provides custom graphics item classes for rendering and interacting with
flow diagram components:

1. FlowNodeItem: Represents a water source/storage/plant/sink component
   - Draggable (unless locked)
   - 17 anchor points for edge snapping
   - Selection highlighting
   - Double-click to edit
   - Visual styling (fill color, outline, shadow)

2. FlowEdgeItem: Represents a flow line connecting two nodes
   - Orthogonal path (90° segments)
   - Flow type color coding (clean/dirty/evaporation/recirculation)
   - Volume label (draggable repositioning)
   - Selection highlighting
   - Automatic path routing

Data Model:
- Nodes: {id, label, type, shape, fill, outline, locked, x, y, width, height}
- Edges: {from_id, to_id, flow_type, color, volume, excel_mapping, waypoints}

Signals emitted by items:
- node_moved: When node is dragged to new position
- node_selected: When node is clicked
- node_double_clicked: When node is double-clicked (edit)
- edge_selected: When edge is clicked
- edge_double_clicked: When edge is double-clicked (edit volume)

Anchor Points (FlowNodeItem):
- 17 points around node perimeter for edge connection snapping
- Layout: 4 corners + 12 edge midpoints + 1 center
- Automatically calculated from node position/size
"""

from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsPathItem, QGraphicsTextItem,
    QGraphicsEllipseItem, QGraphicsLineItem
)
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, Signal, QObject, QTimer
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainter, QFont, QPainterPath,
    QPainterPathStroker, QTextDocument, QTextBlockFormat
)
from typing import Dict, List, Tuple, Optional
import math
import logging

logger = logging.getLogger(__name__)


class FlowNodeItem(QGraphicsRectItem, QObject):
    """
    Custom graphics item representing a water component node (FLOW NODE).
    
    A node is a rectangular or oval component that appears on the flow diagram
    (e.g., borehole, sump, plant, storage tank). Nodes can be:
    - Dragged to new positions (unless locked)
    - Selected and highlighted with dashed border
    - Double-clicked to edit properties
    - Connected by edges through 17 anchor points
    
    Attributes:
        node_id (str): Unique identifier (e.g., 'bh_ndgwa')
        node_data (dict): Full node definition {id, label, type, shape, fill, outline, locked, x, y, ...}
        anchor_points (list): 17 QPointF positions around perimeter for edge snapping
        is_selected (bool): Current selection state
        is_locked (bool): Whether node can be dragged
        parent_scene: Reference to QGraphicsScene
        
    Visual Styling:
        - Fill color: RGB from node_data['fill']
        - Outline: 2px solid from node_data['outline']
        - Shadow: 4px offset (when selected)
        - Label: Centered, multi-line text with line-height adjustment
        
    Signals:
        node_moved(node_id, new_pos): Emitted when node is dragged
        node_selected(node_id): Emitted when node is clicked
        node_double_clicked(node_id): Emitted when node is double-clicked (edit)
    """
    
    # Signals (must be defined at class level for QObject signal support)
    node_moved = Signal(str, QPointF)  # (node_id, new_position)
    node_selected = Signal(str)         # (node_id,)
    node_double_clicked = Signal(str)   # (node_id,) - user wants to edit
    node_context_menu = Signal(str, QPointF)  # (node_id, screen_position) - right-click menu
    
    # Node sizing constants (in pixels)
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 80
    MIN_WIDTH = 60
    MIN_HEIGHT = 50
    MAX_WIDTH = 200
    MAX_HEIGHT = 150
    
    # Selection and visual styling
    SELECTION_PEN_WIDTH = 2
    SELECTION_DASH_PATTERN = [5, 5]  # 5px dash, 5px gap
    NORMAL_PEN_WIDTH = 1.5
    SHADOW_OFFSET = 4
    
    # Anchor points around perimeter for edge connection snapping
    # Total: 17 points (4 corners + 4 side midpoints + 4 quarter points per side + 1 center)
    NUM_ANCHOR_POINTS = 17
    
    def __init__(self, node_id: str, node_data: Dict, parent=None):
        """
        Initialize flow node graphics item.
        
        Args:
            node_id (str): Unique node identifier (e.g., 'bh_ndgwa')
            node_data (dict): Node definition dictionary with keys:
                - id: Unique identifier
                - label: Display text (may contain \\n for multi-line)
                - type: 'source', 'storage', 'plant', 'sink', or 'none'
                - shape: 'rect' or 'oval'
                - fill: RGB color string (e.g., '#DFE6ED')
                - outline: RGB color string (e.g., '#2C3E50')
                - locked: bool - whether node can be dragged
                - x, y: Position on canvas (pixels)
                - width, height: Size (pixels)
            parent: Parent QGraphicsItem
        """
        QGraphicsRectItem.__init__(self, parent)
        QObject.__init__(self)
        
        self.node_id = node_id
        self.node_data = node_data
        self.is_selected = False
        self.is_locked = node_data.get('locked', False)
        self.anchor_points: List[QPointF] = []
        
        # Initialize geometry from node_data
        x = node_data.get('x', 0.0)
        y = node_data.get('y', 0.0)
        width = node_data.get('width', self.DEFAULT_WIDTH)
        height = node_data.get('height', self.DEFAULT_HEIGHT)
        
        # Set rect (QGraphicsRectItem position/size)
        self.setRect(0, 0, width, height)
        self.setPos(x, y)
        
        # Setup visual styling
        self._setup_styling()
        
        # Setup label text
        self._setup_label()
        
        # Setup recirculation badge (if applicable)
        self._setup_recirculation_badge()
        
        # Calculate anchor points for edge connection
        self._calculate_anchor_points()
        
        # Enable interactions
        self.setAcceptHoverEvents(True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        if not self.is_locked:
            self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        
        logger.debug(f"Created FlowNodeItem: {node_id} at ({x}, {y}) size {width}x{height}")
    
    def _setup_styling(self):
        """Configure pen and brush colors based on node data."""
        # Fill color (background)
        fill_color = QColor(self.node_data.get('fill', '#FFFFFF'))
        self.setBrush(QBrush(fill_color))
        
        # Outline color and width
        outline_color = QColor(self.node_data.get('outline', '#000000'))
        outline_pen = QPen(outline_color)
        outline_pen.setWidth(self.NORMAL_PEN_WIDTH)
        self.setPen(outline_pen)
    
    def _setup_label(self):
        """Create and position label text item as child of this node."""
        # Label text may contain newlines for multi-line display
        label_text = self.node_data.get('label', self.node_id)
        
        # Create text item
        if not hasattr(self, "label_item"):
            self.label_item = QGraphicsTextItem(self)
        self.label_item.setPlainText(label_text)
        self.label_item.setDefaultTextColor(self._get_contrasting_label_color())
        
        # Configure text appearance
        font_size = int(self.node_data.get('font_size', 9))
        font_weight = self.node_data.get('font_weight', 'normal')
        font = QFont("Arial", font_size)
        font.setBold(str(font_weight).lower() == 'bold')
        self.label_item.setFont(font)
        
        # Set text alignment to center using QTextBlockFormat
        text_doc = self.label_item.document()
        text_doc.setTextWidth(self.rect().width() - 8)  # 4px padding on each side
        
        # Apply center alignment to all text blocks
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursor = self.label_item.textCursor()
        cursor.select(cursor.SelectionType.Document)  # Select all text
        cursor.setBlockFormat(block_format)
        cursor.clearSelection()  # Remove selection highlight
        cursor.movePosition(cursor.MoveOperation.Start)  # Move to start
        self.label_item.setTextCursor(cursor)
        
        # Position label to center of node (accounting for text height)
        rect = self.rect()
        text_height = text_doc.size().height()
        text_x = 0  # Let text item handle horizontal alignment via block format
        text_y = (rect.height() - text_height) / 2  # Center vertically
        
        self.label_item.setPos(text_x, text_y)

    def _get_contrasting_label_color(self) -> QColor:
        """Return black/white label color with best contrast against node fill."""
        fill_color = QColor(self.node_data.get('fill', '#FFFFFF'))
        if not fill_color.isValid():
            return QColor("#0b1a2a")

        def _to_linear(channel: float) -> float:
            c = channel / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r = _to_linear(fill_color.red())
        g = _to_linear(fill_color.green())
        b = _to_linear(fill_color.blue())
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # WCAG contrast against white/black.
        contrast_white = (1.0 + 0.05) / (luminance + 0.05)
        contrast_black = (luminance + 0.05) / 0.05
        return QColor("#FFFFFF") if contrast_white >= contrast_black else QColor("#0b1a2a")

    def _setup_recirculation_badge(self):
        """Create rectangular draggable recirculation badge on component edge.
        
        Creates a small rectangular badge with dashed border that:
        - Sits on the edge of the component (not overlapping)
        - Is semi-transparent (30% opacity)
        - Can be dragged around the component perimeter
        - Constraint keeps it on the edge
        - Position is saved in diagram JSON
        
        Loads saved position from node_data['badge_angle'] if available (default 0° = top).
        """
        recirculation_vol = self.node_data.get('recirculation_volume', 0)
        
        if recirculation_vol is None or recirculation_vol == 0:
            if hasattr(self, 'recirculation_badge'):
                if self.recirculation_badge.scene():
                    self.scene().removeItem(self.recirculation_badge)
                delattr(self, 'recirculation_badge')
            return
        
        # Format volume preserving sign - show full number without abbreviation
        if recirculation_vol < 0:
            badge_text = f"↻ {recirculation_vol:.1f}"
        else:
            badge_text = f"↻ {recirculation_vol:.1f}"
        
        # Create circular badge as separate graphics item (not child of node)
        if not hasattr(self, 'recirculation_badge'):
            self.recirculation_badge = CircularRecirculationBadge(badge_text, parent_node=self)
            
            # Load saved badge position if available (default 0° = top of component)
            saved_angle = self.node_data.get('badge_angle', 0)
            self.recirculation_badge.angle = saved_angle
        
        self.recirculation_badge.setText(badge_text)
        self.recirculation_badge.update_position(self)
        
        # Add to scene if not already there
        if self.recirculation_badge.scene() is None and self.scene():
            self.scene().addItem(self.recirculation_badge)

    def get_badge_position(self) -> float | None:
        """Return current recirculation badge angle for JSON persistence.

        Returns:
            float | None: Badge angle in degrees if badge exists; otherwise None.
        """
        if hasattr(self, 'recirculation_badge'):
            return self.recirculation_badge.get_badge_position()

        return None

    def apply_node_data(self, node_data: Dict) -> None:
        """Apply updated node data and refresh visuals (EDIT REFRESH).

        Args:
            node_data: Updated node definition dict containing visual fields.
        """
        self.node_data = node_data

        # Update geometry
        width = node_data.get('width', self.DEFAULT_WIDTH)
        height = node_data.get('height', self.DEFAULT_HEIGHT)
        x = node_data.get('x', self.x())
        y = node_data.get('y', self.y())
        self.setRect(0, 0, width, height)
        self.setPos(x, y)

        # Update visual styling and label
        self._setup_styling()
        self._setup_label()
        self._setup_recirculation_badge()

        # Update lock state and anchor points
        self.set_locked(node_data.get('locked', False))
        self._calculate_anchor_points()
    
    def _calculate_anchor_points(self):
        """
        Calculate 17 anchor points around node perimeter for edge snapping.
        
        Layout (for rectangular node):
        - 4 corner points (top-left, top-right, bottom-right, bottom-left)
        - 4 side midpoints (top-center, right-center, bottom-center, left-center)
        - 8 quarter points (halfway between corner and midpoint on each side)
        - 1 center point
        
        Total: 4 + 4 + 8 + 1 = 17 points
        
        These points are used by FlowEdgeItem to snap new edge connections
        to the nearest available anchor point on the node.
        
        Returns:
            list[QPointF]: List of 17 anchor points in item coordinates
        """
        self.anchor_points = []
        rect = self.rect()
        
        # Get node center
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        # 4 corners
        corners = [
            QPointF(0, 0),                          # Top-left
            QPointF(rect.width(), 0),               # Top-right
            QPointF(rect.width(), rect.height()),   # Bottom-right
            QPointF(0, rect.height())                # Bottom-left
        ]
        self.anchor_points.extend(corners)
        
        # 4 side midpoints
        midpoints = [
            QPointF(center_x, 0),                   # Top-center
            QPointF(rect.width(), center_y),        # Right-center
            QPointF(center_x, rect.height()),       # Bottom-center
            QPointF(0, center_y)                    # Left-center
        ]
        self.anchor_points.extend(midpoints)
        
        # 8 quarter points (between corners and midpoints)
        quarter_points = [
            # Top edge
            QPointF(center_x / 2, 0),               # Top-left quarter
            QPointF(center_x * 1.5, 0),             # Top-right quarter
            # Right edge
            QPointF(rect.width(), center_y / 2),    # Right-top quarter
            QPointF(rect.width(), center_y * 1.5),  # Right-bottom quarter
            # Bottom edge
            QPointF(center_x * 1.5, rect.height()), # Bottom-right quarter
            QPointF(center_x / 2, rect.height()),   # Bottom-left quarter
            # Left edge
            QPointF(0, center_y * 1.5),             # Left-bottom quarter
            QPointF(0, center_y / 2)                # Left-top quarter
        ]
        self.anchor_points.extend(quarter_points)
        
        # 1 center point
        self.anchor_points.append(QPointF(center_x, center_y))
        
        logger.debug(f"Calculated {len(self.anchor_points)} anchor points for node {self.node_id}")
        return self.anchor_points
    
    def get_nearest_anchor_point(self, point: QPointF, exclude_anchor_idx: int = -1) -> QPointF:
        """
        Find nearest anchor point to given point (ANCHOR SNAPPING).
        
        Used by FlowEdgeItem when finalizing edge connection to snap
        edge endpoint to nearest anchor point on this node.
        
        For parallel edges (multiple edges between same nodes), can exclude
        one anchor point to force edges to use different anchors.
        
        Args:
            point (QPointF): Target point (in scene coordinates)
            exclude_anchor_idx (int): Anchor index to skip (-1 = no exclusion)
            
        Returns:
            QPointF: Nearest anchor point (in scene coordinates)
        """
        # Convert scene point to item coordinates
        item_point = self.mapFromScene(point)
        
        min_distance = float('inf')
        nearest_anchor = self.anchor_points[0]
        
        for idx, anchor in enumerate(self.anchor_points):
            # Skip excluded anchor for parallel edge spreading
            if idx == exclude_anchor_idx:
                continue
                
            distance = (anchor - item_point).manhattanLength()
            if distance < min_distance:
                min_distance = distance
                nearest_anchor = anchor
        
        # Convert back to scene coordinates
        return self.mapToScene(nearest_anchor)
    
    def mouseMoveEvent(self, event):
        """
        Handle node dragging (if not locked).
        
        Called when user drags node to new position. Emits node_moved signal
        to allow FlowDiagramPage to update edge waypoints as node moves.
        
        Locking is controlled by is_locked attribute and ItemIsMovable flag.
        """
        if not self.is_locked:
            super().mouseMoveEvent(event)
            # Emit signal with new position (in scene coordinates)
            self.node_moved.emit(self.node_id, self.pos())
    
    def mousePressEvent(self, event):
        """
        Handle node selection and context menu (RIGHT-CLICK HANDLER).
        
        Called when user clicks on node. Handles:
        - Left-click: Emits node_selected signal
        - Right-click: Emits node_context_menu signal for context menu
        """
        # Right-click → Show context menu
        if event.button() == Qt.MouseButton.RightButton:
            screen_pos = self.mapToScene(event.pos())
            self.node_context_menu.emit(self.node_id, screen_pos)
        else:
            # Left-click → Select node
            super().mousePressEvent(event)
            self.node_selected.emit(self.node_id)
    
    def mouseDoubleClickEvent(self, event):
        """
        Handle node double-click for editing.
        
        Called when user double-clicks node. Emits node_double_clicked signal
        which prompts FlowDiagramPage to open edit dialog.
        """
        super().mouseDoubleClickEvent(event)
        self.node_double_clicked.emit(self.node_id)
    
    def set_selected(self, selected: bool):
        """
        Set selection state and update visual highlighting.
        
        Args:
            selected (bool): True to highlight, False to unhighlight
        """
        self.is_selected = selected
        
        if selected:
            # Selection style: dashed outline with shadow effect
            outline_color = QColor(self.node_data.get('outline', '#000000'))
            select_pen = QPen(outline_color)
            select_pen.setWidth(self.SELECTION_PEN_WIDTH)
            select_pen.setDashPattern(self.SELECTION_DASH_PATTERN)
            self.setPen(select_pen)
            
            # Add shadow effect (in production, could use QGraphicsDropShadowEffect)
            # For now, just visual feedback via pen style
            self.setZValue(10)  # Bring to front
        else:
            # Normal style
            self._setup_styling()
            self.setZValue(0)
    
    def set_locked(self, locked: bool):
        """
        Set lock state and update movability.
        
        Args:
            locked (bool): True to prevent dragging, False to allow
        """
        self.is_locked = locked
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not locked)
        self.node_data['locked'] = locked
    
    def paint(self, painter: QPainter, option, widget=None):
        """
        Paint node item on graphics scene.
        
        Renders rectangle/oval background, outline, and any visual effects
        (shadow, glow, etc.)
        """
        # Paint shadow if selected (simple offset shape)
        if self.is_selected:
            rect = self.rect()
            shadow_rect = rect.translated(self.SHADOW_OFFSET, self.SHADOW_OFFSET)
            shadow_pen = QPen(QColor(100, 100, 100, 100))
            shadow_pen.setWidth(1)
            painter.setPen(shadow_pen)
            self._draw_shape(painter, shadow_rect, use_brush=False)

        # Draw the main shape using current pen/brush
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        self._draw_shape(painter, self.rect(), use_brush=True)

    def _draw_shape(self, painter: QPainter, rect, use_brush: bool = True) -> None:
        """Draw shape based on node_data['shape'].

        Args:
            painter: QPainter to draw with.
            rect: QRectF of the node bounds.
            use_brush: Whether to fill with brush or outline only.
        """
        shape = self.node_data.get('shape', 'rect')

        if not use_brush:
            painter.setBrush(Qt.NoBrush)

        if shape == 'oval':
            painter.drawEllipse(rect)
            return

        if shape == 'trapezoid':
            top_inset = rect.width() * 0.15
            points = [
                QPointF(rect.left() + top_inset, rect.top()),
                QPointF(rect.right() - top_inset, rect.top()),
                QPointF(rect.right(), rect.bottom()),
                QPointF(rect.left(), rect.bottom()),
            ]
            painter.drawPolygon(points)
            return

        if shape == 'hexagon':
            dx = rect.width() * 0.2
            points = [
                QPointF(rect.left() + dx, rect.top()),
                QPointF(rect.right() - dx, rect.top()),
                QPointF(rect.right(), rect.center().y()),
                QPointF(rect.right() - dx, rect.bottom()),
                QPointF(rect.left() + dx, rect.bottom()),
                QPointF(rect.left(), rect.center().y()),
            ]
            painter.drawPolygon(points)
            return

        if shape == 'office':
            notch_width = rect.width() * 0.25
            notch_height = rect.height() * 0.25
            points = [
                QPointF(rect.left(), rect.top()),
                QPointF(rect.right() - notch_width, rect.top()),
                QPointF(rect.right() - notch_width, rect.top() + notch_height),
                QPointF(rect.right(), rect.top() + notch_height),
                QPointF(rect.right(), rect.bottom()),
                QPointF(rect.left(), rect.bottom()),
            ]
            painter.drawPolygon(points)
            return

        # Default: rectangle
        painter.drawRect(rect)
    
    def __repr__(self) -> str:
        return f"FlowNodeItem(id={self.node_id}, pos=({self.pos().x():.0f},{self.pos().y():.0f}))"


class FlowEdgeItem(QGraphicsPathItem, QObject):
    """
    Custom graphics item representing a flow line connecting two nodes (FLOW EDGE).
    
    An edge is a directed flow line connecting a source node to a destination node.
    Edges can be:
    - Orthogonal paths (90° segments only, no diagonal lines)
    - Colored by flow type (clean=blue, dirty=red, evaporation=black, recirculation=purple)
    - Labeled with volume values
    - Selected and highlighted with thicker outline
    - Double-clicked to edit properties
    
    Attributes:
        edge_idx (int): Index in parent diagram's edges list
        edge_data (dict): Edge definition {from_id, to_id, flow_type, color, volume, waypoints}
        from_node (FlowNodeItem): Source node reference
        to_node (FlowNodeItem | None): Destination node reference (None for junction endpoints)
        is_selected (bool): Current selection state
        volume_label (QGraphicsTextItem): Volume label item
        waypoints (list): List of QPointF waypoints along edge path
        
    Visual Styling:
        - Stroke color: 2.5px solid, colored by flow_type
        - Arrow head: Filled triangle at destination
        - Label: Volume value displayed near midpoint (draggable)
        - Dashed style: For recirculation flows (loop back)
        
    Signals:
        edge_selected(edge_idx): Emitted when edge is clicked
        edge_double_clicked(edge_idx): Emitted when edge is double-clicked (edit)
        
    Flow Type Colors:
        - clean: #3498DB (blue)
        - dirty: #E74C3C (red)
        - evaporation: #2C3E50 (dark gray/black)
        - recirculation: #9B59B6 (purple)
    """
    
    # Signals
    edge_selected = Signal(int)         # (edge_idx,)
    edge_double_clicked = Signal(int)   # (edge_idx,) - user wants to edit
    
    # Visual styling constants
    NORMAL_PEN_WIDTH = 1.75
    SELECTED_PEN_WIDTH = 2.45
    ARROW_SIZE = 7
    LABEL_FONT_SIZE = 8
    RECIRCULATION_DASH = [8, 4]  # 8px dash, 4px gap (for loop flows)
    
    # Flow type color mapping
    FLOW_TYPE_COLORS = {
        'clean': '#3498DB',        # Blue
        'dirty': '#E74C3C',         # Red
        'evaporation': '#2C3E50',   # Dark gray/black
        'recirculation': '#9B59B6'  # Purple
    }
    
    def __init__(self, edge_idx: int, edge_data: Dict, 
                 from_node: 'FlowNodeItem', to_node: Optional['FlowNodeItem'], parent=None):
        """
        Initialize flow edge graphics item.
        
        Args:
            edge_idx (int): Index of edge in parent diagram's edges list
            edge_data (dict): Edge definition dictionary with keys:
                - from_id: Source node ID
                - to_id: Destination node ID or virtual junction ID
                - flow_type: 'clean', 'dirty', 'evaporation', or 'recirculation'
                - color: RGB color string (override default type color)
                - volume: Float volume in m³
                - waypoints: List of [x, y] waypoints along path
                - excel_mapping: {sheet, column} for Excel configuration
                - is_junction: True when the edge terminates on a flowline junction
                - junction_pos: {x, y} destination point when is_junction=True
            from_node (FlowNodeItem): Source node graphics item
            to_node (FlowNodeItem | None): Destination node graphics item (None for junction endpoints)
            parent: Parent QGraphicsItem
        """
        QGraphicsPathItem.__init__(self, parent)
        QObject.__init__(self)
        
        self.edge_idx = edge_idx
        self.edge_data = edge_data
        self.from_node = from_node
        self.to_node = to_node
        self.is_selected = False
        self.waypoints = []
        self._last_segment: Optional[Tuple[QPointF, QPointF]] = None
        
        # Setup visual styling (pen color/width)
        self._setup_styling()
        
        # Create volume label text item
        self._setup_volume_label()
        
        # Draw edge path from source to destination through waypoints
        self._update_path()
        
        # Enable interactions
        self.setAcceptHoverEvents(True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        
        logger.debug(f"Created FlowEdgeItem: {edge_data['from_id']} -> {edge_data['to_id']}")
    
    def _setup_styling(self):
        """Configure pen color based on flow type."""
        # Get flow type color (use override color if provided, else default)
        flow_type = self.edge_data.get('flow_type', 'clean')
        
        # If edge_data has explicit color, use it; else use flow_type default
        if 'color' in self.edge_data and self.edge_data['color']:
            color_str = self.edge_data['color']
        else:
            color_str = self.FLOW_TYPE_COLORS.get(flow_type, self.FLOW_TYPE_COLORS['clean'])
        
        edge_color = QColor(color_str)
        
        # Create pen with appropriate style
        pen = QPen(edge_color)
        pen.setWidth(self.NORMAL_PEN_WIDTH)
        # Square caps reduce visible gaps between line and arrow head.
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # Recirculation flows (loop back) use dashed style
        if flow_type == 'recirculation':
            pen.setDashPattern(self.RECIRCULATION_DASH)
        
        self.setPen(pen)
    
    def _setup_volume_label(self):
        """
        Create volume label text item positioned at edge midpoint (LABEL VISIBILITY SETUP).
        
        Label styling:
        - Bold Arial font at 10px
        - Semi-transparent white background for readability
        - Z-value 10 (above edges and nodes)
        - Positioned at edge path midpoint with perpendicular offset
        """
        volume = self.edge_data.get('volume')
        # Handle None or missing volume values
        if volume is None:
            volume_text = "Flow"
        else:
            try:
                volume_text = f"{float(volume):.1f} m³"
            except (ValueError, TypeError):
                volume_text = "Flow"
        
        self.volume_label = QGraphicsTextItem(volume_text, self)
        
        # Font styling
        font = QFont("Arial", self.LABEL_FONT_SIZE)
        font.setBold(True)
        self.volume_label.setFont(font)
        
        # Text color - dark blue for contrast
        self.volume_label.setDefaultTextColor(QColor("#0D47A1"))
        
        # Background for readability (semi-transparent white)
        self.volume_label.setHtml(
            f'<div style="background-color: rgba(255, 255, 255, 0.85); '
            f'padding: 2px 4px; border-radius: 3px;">{volume_text}</div>'
        )
        
        # Z-value: Above everything (edges=0, nodes=1, anchors=5, labels=10)
        self.volume_label.setZValue(10)
        
        # Ensure label is visible
        self.volume_label.setVisible(True)
    
    def _update_path(self):
        """
        Update edge path based on source/dest nodes and waypoints (EDGE PATH CALCULATOR).
        
        Creates orthogonal path from source anchor point through waypoints to
        destination anchor point. This is called when:
        - Edge is first created
        - Source node moves
        - Destination node moves
        - Waypoints are modified
        
        Waypoint Format:
        - Waypoints stored in edge_data['waypoints'] are INTERMEDIATE waypoints only
        - They do NOT include source or destination anchor points
        - Source and destination anchors are calculated dynamically based on nodes
        
        Path Construction:
        1. Calculate source anchor (snap to source node boundary)
        2. Add intermediate waypoints
        3. Calculate destination anchor (snap to destination node boundary)
        """
        # Get waypoints from edge data (intermediate points only, no source/dest)
        waypoints = self.edge_data.get('waypoints', [])
        
        # Determine direction for snapping based on first/last waypoint
        if waypoints and len(waypoints) > 0:
            # First waypoint exists - use it as direction hint for source snap
            first_waypoint = QPointF(waypoints[0][0], waypoints[0][1]) if isinstance(waypoints[0], (list, tuple)) else waypoints[0]
            # Last waypoint exists - use it as direction hint for dest snap
            last_waypoint = QPointF(waypoints[-1][0], waypoints[-1][1]) if isinstance(waypoints[-1], (list, tuple)) else waypoints[-1]
        else:
            # No waypoints - snap based on direct node-to-node direction
            first_waypoint = None
            last_waypoint = None
        
        # Resolve junction destination (metadata-only endpoint)
        junction_pos = None
        if self.to_node is None:
            jpos = self.edge_data.get('junction_pos')
            if isinstance(jpos, dict) and 'x' in jpos and 'y' in jpos:
                junction_pos = QPointF(jpos['x'], jpos['y'])
            elif isinstance(jpos, (list, tuple)) and len(jpos) == 2:
                junction_pos = QPointF(jpos[0], jpos[1])
            if junction_pos is None:
                # Junction endpoint missing; skip path update to avoid bad geometry
                return
        
        # Get snap point on source node (based on direction toward first waypoint or destination)
        if first_waypoint:
            source_direction_point = first_waypoint
        else:
            # No waypoints - snap toward destination node or junction point
            if junction_pos is not None:
                source_direction_point = junction_pos
            else:
                source_direction_point = self.to_node.mapToScene(self.to_node.rect().center())
        
        from_anchor = self.from_node.get_nearest_anchor_point(source_direction_point)
        
        # Get snap point on destination node (based on direction from last waypoint or source)
        if last_waypoint:
            dest_direction_point = last_waypoint
        else:
            # No waypoints - snap from source node direction
            dest_direction_point = self.from_node.mapToScene(self.from_node.rect().center())
        
        if junction_pos is not None:
            to_anchor = junction_pos
        else:
            to_anchor = self.to_node.get_nearest_anchor_point(dest_direction_point)
        
        # Build path: source anchor → waypoints → destination anchor
        path = QPainterPath()
        path.moveTo(from_anchor)

        # Build a full point list (source → waypoints → destination).
        # We honor the user's drawn waypoints to keep drawing flexible and predictable.
        routed_points: List[QPointF] = [from_anchor]
        for wp in waypoints:
            if isinstance(wp, dict) and 'x' in wp and 'y' in wp:
                wp_point = QPointF(wp['x'], wp['y'])
            else:
                wp_point = QPointF(wp[0], wp[1]) if isinstance(wp, (list, tuple)) else wp
            routed_points.append(wp_point)
        routed_points.append(to_anchor)

        # Draw through each point directly (no forced orthogonal conversion).
        for idx in range(1, len(routed_points)):
            path.lineTo(routed_points[idx])

        # Cache the final non-zero segment for arrow orientation.
        self._last_segment = None
        for idx in range(len(routed_points) - 1, 0, -1):
            candidate_end = routed_points[idx]
            candidate_start = routed_points[idx - 1]
            if (candidate_end - candidate_start).manhattanLength() > 0.1:
                self._last_segment = (candidate_start, candidate_end)
                break
        
        self.setPath(path)
        
        # Update volume label position to edge midpoint (CRITICAL FOR LABEL VISIBILITY)
        if hasattr(self, 'volume_label') and self.volume_label:
            self._update_label_position(from_anchor, to_anchor)

    def _append_orthogonal_segment(self, path: QPainterPath, start: QPointF, end: QPointF) -> None:
        """Append a 90° path segment between two points (ORTHOGONAL ROUTER).

        If the points are aligned horizontally or vertically, draws a single line.
        If both X and Y differ, inserts a corner so the path remains orthogonal.

        Args:
            path: QPainterPath being built for the edge.
            start: Segment start point (scene coordinates).
            end: Segment end point (scene coordinates).
        """
        # Aligned segments are drawn directly.
        if start.x() == end.x() or start.y() == end.y():
            path.lineTo(end)
            return

        # Insert an orthogonal corner to avoid diagonal lines.
        # Choose direction based on larger delta to minimize sharp backtracking.
        dx = abs(end.x() - start.x())
        dy = abs(end.y() - start.y())
        if dx >= dy:
            corner = QPointF(end.x(), start.y())  # Horizontal first, then vertical
        else:
            corner = QPointF(start.x(), end.y())  # Vertical first, then horizontal

        path.lineTo(corner)
        path.lineTo(end)
    
    def distance_to_point(self, point: QPointF) -> float:
        """Calculate perpendicular distance from point to edge path (HIT DETECTION FOR SNAPPING).
        
        Used during drawing mode to detect when cursor is near an existing edge,
        enabling snap feedback and connection to edge for junction creation.
        
        Args:
            point: Point in scene coordinates
        
        Returns:
            float: Minimum distance from point to any part of edge path.
                   If path is empty, returns infinity.
        """
        path = self.path()
        if path.isEmpty():
            return float('inf')
        
        # Get all elements in path and find closest point
        min_distance = float('inf')
        
        # Sample points along the path and measure distance
        # This is more reliable than using path.elementAt() directly
        length = path.length()
        if length <= 0:
            return float('inf')
        
        # Sample every ~5 pixels along the path
        sample_points = max(2, int(length / 5))
        for i in range(sample_points + 1):
            t = i / sample_points if sample_points > 0 else 0
            path_point = path.pointAtPercent(t)
            dx = point.x() - path_point.x()
            dy = point.y() - path_point.y()
            dist = (dx*dx + dy*dy) ** 0.5
            min_distance = min(min_distance, dist)
        
        return min_distance
    
    def get_point_on_path(self, point: QPointF) -> Optional[QPointF]:
        """Get the closest point on edge path to a given point (JUNCTION PLACEMENT).
        
        Used to determine where a new junction node should be placed when
        connecting to an existing edge.
        
        Args:
            point: Point in scene coordinates
        
        Returns:
            QPointF: Closest point on path, or None if path is empty
        """
        path = self.path()
        if path.isEmpty():
            return None
        
        length = path.length()
        if length <= 0:
            return None
        
        # Find the percent along path that is closest to the point
        min_distance = float('inf')
        best_percent = 0.0
        
        sample_points = max(2, int(length / 5))
        for i in range(sample_points + 1):
            t = i / sample_points if sample_points > 0 else 0
            path_point = path.pointAtPercent(t)
            dx = point.x() - path_point.x()
            dy = point.y() - path_point.y()
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < min_distance:
                min_distance = dist
                best_percent = t
        
        return path.pointAtPercent(best_percent)
    
    def set_highlighted(self, highlighted: bool):
        """Set visual highlight state for snap feedback (SNAP INDICATOR).
        
        When cursor is near an edge and user can connect to it,
        highlight the edge in bright green to show it's snap-able.
        
        Args:
            highlighted: True to show as snap-able, False for normal
        """
        if highlighted:
            # Bright green with thicker pen
            highlight_color = QColor("#00FF00")  # Bright green
            pen = QPen(highlight_color)
            pen.setWidth(self.NORMAL_PEN_WIDTH + 1)  # Slightly thicker
            pen.setCapStyle(Qt.PenCapStyle.SquareCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            flow_type = self.edge_data.get('flow_type', 'clean')
            if flow_type == 'recirculation':
                pen.setDashPattern(self.RECIRCULATION_DASH)
            self.setPen(pen)
            self.setZValue(100)  # Bring to front
        else:
            # Return to normal styling
            self._setup_styling()
            self.setZValue(0)
    
    def shape(self):
        """
        Return clickable shape for edge selection (MOUSE INTERACTION ENHANCER).
        
        Creates a wider path around the actual edge to make it easier to click.
        Without this, the 1px edge would be very difficult to select with the mouse.
        
        Returns:
            QPainterPath: Path with 10px stroke width for easier selection
        """
        path = self.path()
        stroker = QPainterPathStroker()
        stroker.setWidth(10)  # 10px clickable area around the edge
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(path)
    
    def paint(self, painter: QPainter, option, widget=None):
        """
        Paint edge and arrow head (ARROW RENDERER).
        
        Renders:
        1. Base edge path (line with color and width)
        2. Arrow head at destination with flow direction indicator
        
        Arrow properties:
        - Size: 10x10 pixel triangle
        - Position: At destination node
        - Direction: Points toward destination node
        - Color: Same as edge line
        
        Args:
            painter: QPainter for rendering
            option: QStyleOptionGraphicsItem
            widget: Optional widget pointer
        """
        # Draw the edge line itself
        super().paint(painter, option, widget)
        
        # Draw arrow head at destination
        self._draw_arrow_head(painter)
    
    def _draw_arrow_head(self, painter: QPainter):
        """
        Draw arrow head triangle at destination node (ARROW HEAD RENDERER).
        
        Arrow is a filled triangle pointing along the edge direction toward
        the destination node. This provides visual flow direction indication.
        
        Args:
            painter: QPainter for rendering
        """
        path = self.path()

        # Compute direction from the cached final segment so the arrow
        # always points toward the destination component after snapping.
        if path.length() <= 0:
            return

        if self._last_segment:
            prev_point, dest_point = self._last_segment
        else:
            # Fallback: Extract path elements to find the last two distinct points.
            elements = [path.elementAt(i) for i in range(path.elementCount())]
            if len(elements) < 2:
                return

            dest_point = QPointF(elements[-1].x, elements[-1].y)

            # Walk backward to find a point different from the destination.
            prev_point = None
            for elem in reversed(elements[:-1]):
                candidate = QPointF(elem.x, elem.y)
                if (candidate - dest_point).manhattanLength() > 0.1:
                    prev_point = candidate
                    break

            if prev_point is None:
                return

        dx = dest_point.x() - prev_point.x()
        dy = dest_point.y() - prev_point.y()
        length = (dx**2 + dy**2) ** 0.5
        if length == 0:
            return

        # Normalize direction for arrow geometry.
        dx /= length
        dy /= length
        
        # Arrow head parameters (slightly overlapped to avoid visible gaps)
        arrow_len = self.ARROW_SIZE
        arrow_width = self.ARROW_SIZE * 0.5
        
        # Calculate arrow points (triangle)
        # Tip slightly beyond line end so arrow overlaps the line cap.
        overlap = self.NORMAL_PEN_WIDTH * 0.6
        tip = QPointF(dest_point.x() + dx * overlap, dest_point.y() + dy * overlap)
        
        # Back-left point (perpendicular to direction)
        back_x = dest_point.x() - dx * arrow_len
        back_y = dest_point.y() - dy * arrow_len
        left_x = back_x - dy * arrow_width
        left_y = back_y + dx * arrow_width
        
        # Back-right point
        right_x = back_x + dy * arrow_width
        right_y = back_y - dx * arrow_width
        
        # Create triangle path
        arrow_path = QPainterPath()
        arrow_path.moveTo(tip)
        arrow_path.lineTo(left_x, left_y)
        arrow_path.lineTo(right_x, right_y)
        arrow_path.closeSubpath()
        
        # Draw filled triangle with same color as edge
        current_pen = painter.pen()
        arrow_color = current_pen.color()
        
        # Save painter state
        painter.save()
        painter.setPen(current_pen)
        painter.setBrush(QBrush(arrow_color))
        painter.drawPath(arrow_path)
        painter.restore()
    
    def _update_label_position(self, from_pos: QPointF, to_pos: QPointF):
        """
        Position volume label at midpoint of edge path (LABEL POSITIONER).
        
        Places the volume label at the approximate middle of the edge line,
        slightly offset perpendicular to avoid overlapping the line itself.
        
        Args:
            from_pos (QPointF): Start point of edge (scene coordinates)
            to_pos (QPointF): End point of edge (scene coordinates)
        """
        # Get the actual path for more accurate midpoint calculation
        path = self.path()
        path_length = path.length()
        
        # Get point at 50% along the path (true midpoint)
        if path_length > 0:
            mid_point = path.pointAtPercent(0.5)
        else:
            # Fallback to simple midpoint
            mid_point = QPointF(
                (from_pos.x() + to_pos.x()) / 2,
                (from_pos.y() + to_pos.y()) / 2
            )
        
        # Center label directly at midpoint (no perpendicular offset)
        # Offset slightly to avoid overlapping the line itself
        label_bounds = self.volume_label.boundingRect()
        label_x = mid_point.x() - label_bounds.width() / 2
        label_y = mid_point.y() - label_bounds.height() / 2
        
        self.volume_label.setPos(label_x, label_y)
    
    def mousePressEvent(self, event):
        """
        Handle edge selection when user clicks on it.
        
        Emits edge_selected signal to allow FlowDiagramPage to highlight
        connected nodes and show edge properties.
        """
        logger.debug(f"FlowEdgeItem mousePressEvent: edge_idx={self.edge_idx}")
        # Ensure the graphics item is marked as selected (QGraphicsScene selection)
        # This enables scene.selectedItems() fallback in the delete handler.
        self.setSelected(True)
        self.edge_selected.emit(self.edge_idx)
        super().mousePressEvent(event)
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """
        Handle edge double-click for editing properties.
        
        Emits edge_double_clicked signal which prompts FlowDiagramPage
        to open edit flow dialog.
        """
        super().mouseDoubleClickEvent(event)
        self.edge_double_clicked.emit(self.edge_idx)
    
    def set_selected(self, selected: bool):
        """
        Set selection state and update visual highlighting.
        
        Args:
            selected (bool): True to highlight with thicker stroke, False to unhighlight
        """
        self.is_selected = selected
        
        if selected:
            # Selection style: thicker pen
            current_pen = self.pen()
            current_pen.setWidth(self.SELECTED_PEN_WIDTH)
            self.setPen(current_pen)
            self.setZValue(5)  # Bring forward
        else:
            # Normal style: restore original pen width
            current_pen = self.pen()
            current_pen.setWidth(self.NORMAL_PEN_WIDTH)
            self.setPen(current_pen)
            self.setZValue(0)
    
    def update_volume(self, volume: float):
        """
        Update edge volume label with new value.
        
        Called when volume is changed via dialog or Excel import.
        
        Args:
            volume (float): New volume in m³
        """
        self.edge_data['volume'] = volume
        volume_text = f"{volume:.1f} m³"
        self.volume_label.setPlainText(volume_text)
        logger.debug(f"Updated edge volume to {volume} m³")
    
    def __repr__(self) -> str:
        return (f"FlowEdgeItem({self.edge_data['from_id']} → "
                f"{self.edge_data['to_id']}, volume={self.edge_data.get('volume', 0):.1f})")


class CircularRecirculationBadge(QGraphicsRectItem):
    """Rectangular draggable recirculation badge that sits on component edge (DRAGGABLE BADGE).
    
    Features:
    - Rectangular shape with thin dashed border
    - Semi-transparent (30% opacity)
    - Sits on the edge of the parent component
    - Draggable around the perimeter (constrained to edge)
    - Position saved in diagram JSON
    - Shows recirculation volume with sign (negative = return flow)
    """
    
    BADGE_HEIGHT = 20  # Height (FIXED - never changes)
    BADGE_PADDING = 16  # Horizontal padding for text (8px each side)
    OPACITY = 0.3  # 30% transparent
    
    def __init__(self, text: str, parent_node: 'FlowNodeItem'):
        """Initialize circular badge.
        
        Args:
            text: Badge text (e.g., "↻ -26.0")
            parent_node: Reference to FlowNodeItem this badge belongs to
        """
        super().__init__()
        
        self.parent_node = parent_node
        self.badge_text = text
        self.angle = 0  # Position on edge perimeter (0 = top, 90 = right, 180 = bottom, 270 = left)
        
        # Setup text label first to measure width
        self.text_item = QGraphicsTextItem()
        self.text_item.setPlainText(text)
        font = QFont("Arial", 6)  # Small font to fit longer numbers
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("#5B0E7E"))
        
        # Calculate dynamic width based on text
        text_rect = self.text_item.boundingRect()
        self.badge_width = text_rect.width() + self.BADGE_PADDING
        
        # Setup rectangular shape (centered at origin) with dynamic width
        self.setRect(-self.badge_width / 2, -self.BADGE_HEIGHT / 2, self.badge_width, self.BADGE_HEIGHT)
        
        # Setup styling: thin dashed border, semi-transparent fill
        badge_fill = QColor("#E8D5F2")  # Light purple
        badge_fill.setAlpha(int(255 * self.OPACITY))
        self.setBrush(QBrush(badge_fill))
        
        badge_pen = QPen(QColor("#9C27B0"))  # Dark purple
        badge_pen.setWidth(1)  # Thin border
        badge_pen.setDashPattern([3, 2])  # Dashed pattern
        self.setPen(badge_pen)
        
        # Add text as child and center it
        self.text_item.setParentItem(self)
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
        
        # Enable interactions
        self.setAcceptHoverEvents(True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, False)  # Disable default movement
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # Position on edge
        self.update_position(parent_node)
        
        # Dragging state
        self.is_dragging = False
        self.drag_start_pos = None
    
    def setText(self, text: str):
        """Update badge text and resize badge to fit."""
        self.badge_text = text
        self.text_item.setPlainText(text)
        
        # Recalculate width based on new text
        text_rect = self.text_item.boundingRect()
        self.badge_width = text_rect.width() + self.BADGE_PADDING
        
        # Update rectangle size
        self.setRect(-self.badge_width / 2, -self.BADGE_HEIGHT / 2, self.badge_width, self.BADGE_HEIGHT)
        
        # Re-center text
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
    
    def update_position(self, parent_node: 'FlowNodeItem'):
        """Position badge on parent node's edge at current angle."""
        rect = parent_node.rect()
        
        # Calculate position on perimeter based on angle
        # angle in degrees: 0=top, 90=right, 180=bottom, 270=left
        angle_rad = math.radians(self.angle)
        
        # Node center
        cx = rect.width() / 2
        cy = rect.height() / 2
        
        # Semi-axes for ellipse (component is oval/ellipse shaped)
        a = rect.width() / 2  # Horizontal semi-axis
        b = rect.height() / 2  # Vertical semi-axis
        
        # Point on ellipse perimeter at this angle
        # Ellipse equation: x = a*cos(t), y = b*sin(t)
        ellipse_x = a * math.cos(angle_rad)
        ellipse_y = b * math.sin(angle_rad)
        
        # Calculate distance from center to this point on ellipse
        ellipse_radius = math.sqrt(ellipse_x**2 + ellipse_y**2)
        
        # Position badge so it touches the edge (no gap) - use max dimension for rectangle
        offset_distance = ellipse_radius + max(self.badge_width, self.BADGE_HEIGHT) / 2 - 2  # -2px overlap for visual contact
        
        # Calculate final position
        px = cx + offset_distance * math.cos(angle_rad)
        py = cy + offset_distance * math.sin(angle_rad)
        
        # Position badge relative to parent node
        global_pos = parent_node.mapToScene(QPointF(px, py))
        self.setPos(global_pos)
    
    def mousePressEvent(self, event):
        """Start dragging badge around edge."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.scenePos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            event.ignore()
    
    def mouseMoveEvent(self, event):
        """Drag badge around parent node's edge (constrained movement)."""
        if not self.is_dragging:
            event.ignore()
            return
        
        # Get parent node position and size
        parent_pos = self.parent_node.pos()
        parent_rect = self.parent_node.rect()
        
        # Current mouse position in scene coordinates
        mouse_scene_pos = event.scenePos()
        
        # Calculate angle from parent node center to mouse
        parent_center = parent_pos + QPointF(parent_rect.width() / 2, parent_rect.height() / 2)
        delta = mouse_scene_pos - parent_center
        
        # Calculate angle (in degrees)
        angle_rad = math.atan2(delta.y(), delta.x())
        self.angle = math.degrees(angle_rad)
        
        # Reposition on edge
        self.update_position(self.parent_node)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """Stop dragging and save position."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            logger.debug(f"Recirculation badge moved to angle {self.angle:.1f}°")
            event.accept()
        else:
            event.ignore()
    
    def get_badge_position(self) -> float:
        """Return current angle for saving in diagram JSON."""
        return self.angle
