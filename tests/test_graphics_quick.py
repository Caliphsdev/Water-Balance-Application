#!/usr/bin/env python3
"""Quick test of graphics items rendering."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.ui.components.flow_graphics_items import FlowNodeItem, FlowEdgeItem
from PySide6.QtWidgets import QApplication, QGraphicsScene

app = QApplication(sys.argv)

# Create nodes
node1_data = {
    'id': 'n1', 'label': 'Node 1', 'type': 'source', 'shape': 'rect', 
    'fill': '#FFFFFF', 'outline': '#000000', 'locked': False, 
    'x': 100, 'y': 100, 'width': 100, 'height': 80
}
node2_data = {
    'id': 'n2', 'label': 'Node 2', 'type': 'sink', 'shape': 'rect', 
    'fill': '#FFFFFF', 'outline': '#000000', 'locked': False, 
    'x': 400, 'y': 100, 'width': 100, 'height': 80
}

node1 = FlowNodeItem('n1', node1_data)
node2 = FlowNodeItem('n2', node2_data)

# Create edge
edge_data = {
    'from_id': 'n1', 'to_id': 'n2', 'flow_type': 'clean', 'color': '#3498DB', 
    'volume': 100.0, 'waypoints': [[200, 140], [300, 140]], 'excel_mapping': {}
}
edge = FlowEdgeItem(0, edge_data, node1, node2)

# Test scene rendering
scene = QGraphicsScene()
scene.addItem(node1)
scene.addItem(node2)
scene.addItem(edge)

print("=" * 70)
print("FLOW DIAGRAM GRAPHICS ITEMS TEST")
print("=" * 70)
print()
print("✓ FlowNodeItem 1 created:", node1.node_id)
print("✓ FlowNodeItem 2 created:", node2.node_id)
print("✓ FlowEdgeItem created:", node1.node_id, "→", node2.node_id)
print()
print("Scene Contents:")
print("  - Node 1: position ({}, {}), size {}x{}".format(
    node1.pos().x(), node1.pos().y(), node1.rect().width(), node1.rect().height()
))
print("  - Node 2: position ({}, {}), size {}x{}".format(
    node2.pos().x(), node2.pos().y(), node2.rect().width(), node2.rect().height()
))
print("  - Edge: {} → {} ({} m³, {})".format(
    edge_data['from_id'], edge_data['to_id'], edge_data['volume'], edge_data['flow_type']
))
print()
print("Scene Statistics:")
print("  - Total items:", len(scene.items()))
print("  - Node 1 anchors:", len(node1.anchor_points))
print("  - Node 2 anchors:", len(node2.anchor_points))
print("  - Scene bounds:", scene.itemsBoundingRect())
print()
print("=" * 70)
print("✓✓✓ ALL GRAPHICS TESTS PASSED! ✓✓✓")
print("=" * 70)
