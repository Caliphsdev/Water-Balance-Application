"""
Flow Diagram Graphics Scene (QGraphicsScene subclass).

Purpose:
- Load JSON diagram data (nodes, edges, zones)
- Render zones (background rectangles)
- Render nodes (component boxes with labels)
- Render edges (flow lines with volume labels)
- Handle zooming, panning, and interactivity

This layer handles ALL drawing logic - the controller just loads data into this scene.
"""

import json
from pathlib import Path
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsPolygonItem
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QPointF, QSize

from core.app_logger import logger as app_logger

logger = app_logger.get_dashboard_logger('flow_diagram')


class FlowZoneItem(QGraphicsRectItem):
    """Background zone (colored rectangle with label)."""
    
    def __init__(self, zone_data: dict):
        """Initialize zone.
        
        Args:
            zone_data: Dict with keys: name, x, y, width, height, color
        """
        super().__init__(
            zone_data['x'],
            zone_data['y'],
            zone_data['width'],
            zone_data['height']
        )
        self.zone_data = zone_data
        
        # Style: semi-transparent background
        brush = QBrush(QColor(zone_data['color']))
        self.setBrush(brush)
        
        # Light border
        pen = QPen(QColor("#999"))
        pen.setWidth(1)
        self.setPen(pen)
        
        # Set to back layer (behind nodes and edges)
        self.setZValue(-100)


class FlowNodeItem(QGraphicsRectItem):
    """Component node (source, plant, TSF, etc.)."""
    
    def __init__(self, node_data: dict):
        """Initialize node.
        
        Args:
            node_data: Dict with keys: id, label, type, x, y, width, height, 
                      fill, outline, font_size
        """
        super().__init__(
            node_data['x'],
            node_data['y'],
            node_data['width'],
            node_data['height']
        )
        self.node_data = node_data
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        
        # Fill color
        self.setBrush(QBrush(QColor(node_data['fill'])))
        
        # Border
        pen = QPen(QColor(node_data['outline']))
        pen.setWidth(2)
        self.setPen(pen)
        
        # Add text label (centered)
        text_item = QGraphicsTextItem(node_data['label'], self)
        text_item.setDefaultTextColor(QColor("#000"))
        
        # Font
        font = QFont('Segoe UI', node_data.get('font_size', 8))
        font.setBold(True)
        text_item.setFont(font)
        
        # Center text in box
        text_rect = text_item.boundingRect()
        x_offset = (node_data['width'] - text_rect.width()) / 2
        y_offset = (node_data['height'] - text_rect.height()) / 2
        text_item.setPos(x_offset, y_offset)
    
    def mousePressEvent(self, event):
        """Handle click on node."""
        logger.debug(
            "Clicked node: %s (%s)",
            self.node_data.get('id'),
            self.node_data.get('label'),
        )
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        pen = QPen(QColor("#FF0000"))
        pen.setWidth(3)
        self.setPen(pen)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight on leave."""
        pen = QPen(QColor(self.node_data['outline']))
        pen.setWidth(2)
        self.setPen(pen)


class FlowEdgeItem(QGraphicsLineItem):
    """Flow edge (connection between nodes) with volume label."""
    
    def __init__(self, edge_data: dict):
        """Initialize edge.
        
        Args:
            edge_data: Dict with keys: id, type, segments (polyline points),
                      volume, color, label, flow_type
        """
        super().__init__()
        self.edge_data = edge_data
        self.volume = edge_data.get('volume') or 0  # Default to 0 if None
        self.setZValue(5)
        
        # Handle polyline edges (segments) - draw from first to last point
        segments = edge_data.get('segments', [])
        if segments and len(segments) >= 2:
            # Use first and last point for the line
            start = segments[0]
            end = segments[-1]
            self.setLine(start[0], start[1], end[0], end[1])
        else:
            # Fallback: check for x1, y1, x2, y2 format
            if all(k in edge_data for k in ['x1', 'y1', 'x2', 'y2']):
                self.setLine(
                    edge_data['x1'], 
                    edge_data['y1'],
                    edge_data['x2'], 
                    edge_data['y2']
                )
        
        # Color based on flow type
        flow_type = edge_data.get('flow_type', edge_data.get('type', 'unknown'))
        color_map = {
            'inflow': '#228B22',        # Green
            'outflow': '#FF6347',       # Red
            'recirculation': '#696969', # Gray
            'dirty': '#e74c3c',         # Red/dirty
            'clean': '#228B22',         # Green/clean
            'unknown': '#999999'        # Default gray
        }
        color = edge_data.get('color') or color_map.get(flow_type, '#999999')
        
        # Pen style
        pen = QPen(QColor(color))
        pen.setWidth(2)
        self.setPen(pen)
        
        # Volume label (will be positioned at midpoint)
        self.volume_text = QGraphicsTextItem(self)
        self.update_volume_label()
        
        self.setAcceptHoverEvents(True)
    
    def update_volume_label(self):
        """Update or create volume label at edge midpoint."""
        if self.volume > 0:
            text = f"{self.volume:,.0f} m³"
        else:
            text = "0 m³"
        
        self.volume_text.setPlainText(text)
        
        # Position label at midpoint of line
        line = self.line()
        mid_x = (line.x1() + line.x2()) / 2
        mid_y = (line.y1() + line.y2()) / 2
        
        text_rect = self.volume_text.boundingRect()
        self.volume_text.setPos(
            mid_x - text_rect.width() / 2,
            mid_y - text_rect.height() / 2 - 10
        )
        
        # Style volume text
        font = QFont('Segoe UI', 9)
        font.setBold(True)
        self.volume_text.setFont(font)
        self.volume_text.setDefaultTextColor(QColor(self.edge_data.get('color', '#333')))
    
    def set_volume(self, volume: float):
        """Update edge volume value.
        
        Args:
            volume: Volume in m³ (handles None gracefully)
        """
        self.volume = volume or 0  # Handle None
        self.update_volume_label()
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        pen = QPen(QColor("#FF0000"))
        pen.setWidth(4)
        self.setPen(pen)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight on leave."""
        color = self.edge_data.get('color', '#999999')
        pen = QPen(QColor(color))
        pen.setWidth(2)
        self.setPen(pen)


class FlowDiagramScene(QGraphicsScene):
    """Graphics scene that renders flow diagram from JSON.
    
    Loads JSON structure containing zones, nodes, and edges.
    Renders them as interactive graphics items with proper styling.
    
    Usage:
        scene = FlowDiagramScene(diagram_json_dict)
        view.setScene(scene)
    """
    
    def __init__(self, diagram_data: dict):
        """Initialize graphics scene with diagram data.
        
        Args:
            diagram_data: Dict loaded from JSON file with keys:
                - area_code: Area identifier (e.g., 'UG2N')
                - title: Diagram title
                - width: Scene width
                - height: Scene height
                - zone_bg: List of zone dicts
                - nodes: List of node dicts
                - edges: List of edge dicts
        """
        super().__init__()
        
        self.diagram_data = diagram_data
        self.nodes = {}       # {node_id: FlowNodeItem}
        self.edges = {}       # {edge_id: FlowEdgeItem}
        self.zones = []       # [FlowZoneItem, ...]
        
        # Set scene dimensions
        width = diagram_data.get('width', 1800)
        height = diagram_data.get('height', 3470)
        self.setSceneRect(0, 0, width, height)
        
        # Render layers (in order: back to front)
        self._draw_zones()      # Background with titles
        # self._draw_edges()      # Connections - DISABLED until backend ready
        # self._draw_nodes()      # Components - DISABLED until backend ready
        self._draw_section_labels()  # INFLOWS and OUTFLOWS labels
    
    def _draw_zones(self):
        """Draw background zone rectangles (LAYER 1 - BACK).
        
        Zones are colored background areas that group components logically.
        Each zone gets a title label at the top.
        """
        for zone_data in self.diagram_data.get('zone_bg', []):
            zone_item = FlowZoneItem(zone_data)
            self.addItem(zone_item)
            self.zones.append(zone_item)
            
            # Add zone title label
            title_text = QGraphicsTextItem(zone_data['name'])
            title_font = QFont('Segoe UI', 14, QFont.Bold)
            title_text.setFont(title_font)
            title_text.setDefaultTextColor(QColor('#333333'))
            
            # Position title at top-left of zone with padding
            title_text.setPos(
                zone_data['x'] + 10,
                zone_data['y'] + 5
            )
            title_text.setZValue(1)  # Above zone background
            self.addItem(title_text)
    
    def _draw_nodes(self):
        """Draw component nodes (LAYER 3 - FRONT).
        
        Nodes represent system components (boreholes, plants, TSF, etc).
        """
        for node_data in self.diagram_data.get('nodes', []):
            node_item = FlowNodeItem(node_data)
            self.addItem(node_item)
            self.nodes[node_data['id']] = node_item
    
    def _draw_edges(self):
        """Draw flow edges/connections (LAYER 2 - MIDDLE).
        
        Edges represent water flow paths between nodes with volume labels.
        Edges may or may not have explicit 'id'; use edge index as fallback.
        """
        for idx, edge_data in enumerate(self.diagram_data.get('edges', [])):
            edge_item = FlowEdgeItem(edge_data)
            self.addItem(edge_item)
            # Use explicit id if available, otherwise use from->to tuple or index
            edge_id = edge_data.get('id') or f"{edge_data.get('from', 'unknown')}_{edge_data.get('to', 'unknown')}_{idx}"
            self.edges[edge_id] = edge_item
    
    def _draw_section_labels(self):
        """Draw INFLOWS and OUTFLOWS section labels.
        
        Labels are positioned on left (INFLOWS) and right (OUTFLOWS) sides.
        """
        # Get diagram bounds
        width = self.diagram_data.get('width', 1800)
        height = self.diagram_data.get('height', 3470)
        
        # INFLOWS label (top-left, above first zone)
        inflows_label = QGraphicsTextItem('INFLOWS')
        inflows_font = QFont('Segoe UI', 16, QFont.Bold)
        inflows_label.setFont(inflows_font)
        inflows_label.setDefaultTextColor(QColor('#0D47A1'))  # Blue
        inflows_label.setPos(60, 10)
        inflows_label.setZValue(100)  # Top layer
        self.addItem(inflows_label)
        
        # OUTFLOWS label (top-right, above first zone)
        outflows_label = QGraphicsTextItem('OUTFLOWS')
        outflows_font = QFont('Segoe UI', 16, QFont.Bold)
        outflows_label.setFont(outflows_font)
        outflows_label.setDefaultTextColor(QColor('#D32F2F'))  # Red
        
        # Position on right side
        label_width = outflows_label.boundingRect().width()
        outflows_label.setPos(width - label_width - 60, 10)
        outflows_label.setZValue(100)  # Top layer
        self.addItem(outflows_label)
    
    def update_edge_volume(self, edge_id: str, volume: float):
        """Update volume label on specific edge.
        
        Called when Excel data changes to refresh displayed volumes.
        
        Args:
            edge_id: Edge identifier
            volume: New volume in m³
        """
        if edge_id in self.edges:
            self.edges[edge_id].set_volume(volume)
    
    def update_all_volumes(self, volumes_dict: dict):
        """Update volumes for multiple edges at once.
        
        Args:
            volumes_dict: {edge_id: volume_m3, ...}
        """
        for edge_id, volume in volumes_dict.items():
            self.update_edge_volume(edge_id, volume)
    
    def get_node_info(self, node_id: str) -> dict:
        """Get node data by ID.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Node data dict or None if not found
        """
        for node_data in self.diagram_data.get('nodes', []):
            if node_data['id'] == node_id:
                return node_data
        return None
    
    def get_edge_info(self, edge_id: str) -> dict:
        """Get edge data by ID.
        
        Args:
            edge_id: Edge identifier
            
        Returns:
            Edge data dict or None if not found
        """
        for edge_data in self.diagram_data.get('edges', []):
            if edge_data['id'] == edge_id:
                return edge_data
        return None
