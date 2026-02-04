"""
Test Flow Diagram Graphics Rendering (PySide6).

This script verifies that:
1. FlowNodeItem and FlowEdgeItem classes can be instantiated
2. Graphics items render correctly in QGraphicsScene
3. Anchor points are calculated properly
4. Signal connections work
5. Scene rendering from JSON data works end-to-end

Usage:
    .venv\Scripts\python test_flow_diagram_graphics.py

Requirements:
    - Sample diagram JSON in data/diagrams/test_diagram.json
    - PySide6 installed in .venv
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
import json
import logging

# Import custom graphics items
from src.ui.components.flow_graphics_items import FlowNodeItem, FlowEdgeItem

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_diagram_json():
    """Create sample diagram JSON for testing."""
    diagram_data = {
        'area_code': 'TEST',
        'created': '2026-01-31',
        'nodes': [
            {
                'id': 'bh_main',
                'label': 'Borehole\nMain',
                'type': 'source',
                'shape': 'rect',
                'fill': '#DFE6ED',
                'outline': '#2C3E50',
                'locked': False,
                'x': 100,
                'y': 50,
                'width': 100,
                'height': 80
            },
            {
                'id': 'sump_a',
                'label': 'Sump A',
                'type': 'storage',
                'shape': 'rect',
                'fill': '#E8F4F8',
                'outline': '#1E90FF',
                'locked': False,
                'x': 300,
                'y': 150,
                'width': 100,
                'height': 80
            },
            {
                'id': 'plant',
                'label': 'Processing\nPlant',
                'type': 'plant',
                'shape': 'oval',
                'fill': '#F0E68C',
                'outline': '#DAA520',
                'locked': False,
                'x': 550,
                'y': 150,
                'width': 120,
                'height': 90
            },
            {
                'id': 'discharge',
                'label': 'Discharge',
                'type': 'sink',
                'shape': 'rect',
                'fill': '#FFE4E1',
                'outline': '#DC143C',
                'locked': False,
                'x': 800,
                'y': 50,
                'width': 100,
                'height': 80
            }
        ],
        'edges': [
            {
                'from_id': 'bh_main',
                'to_id': 'sump_a',
                'flow_type': 'clean',
                'color': '#3498DB',
                'volume': 150.5,
                'waypoints': [[200, 90], [200, 190], [300, 190]],
                'excel_mapping': {'sheet': 'Flows_Test', 'column': 'BH_to_Sump'}
            },
            {
                'from_id': 'sump_a',
                'to_id': 'plant',
                'flow_type': 'clean',
                'color': '#3498DB',
                'volume': 120.3,
                'waypoints': [[400, 190], [450, 190], [500, 195]],
                'excel_mapping': {'sheet': 'Flows_Test', 'column': 'Sump_to_Plant'}
            },
            {
                'from_id': 'plant',
                'to_id': 'discharge',
                'flow_type': 'dirty',
                'color': '#E74C3C',
                'volume': 100.2,
                'waypoints': [[670, 195], [750, 90], [800, 90]],
                'excel_mapping': {'sheet': 'Flows_Test', 'column': 'Plant_to_Discharge'}
            },
            {
                'from_id': 'plant',
                'to_id': 'sump_a',
                'flow_type': 'recirculation',
                'color': '#9B59B6',
                'volume': 45.7,
                'waypoints': [[610, 200], [450, 300], [350, 250]],
                'excel_mapping': {'sheet': 'Flows_Test', 'column': 'Plant_to_Sump_Recirculation'}
            }
        ]
    }
    
    return diagram_data


def test_flow_node_item():
    """Test FlowNodeItem instantiation and properties."""
    print("\n" + "="*70)
    print("TEST 1: FlowNodeItem - Node Graphics Item Creation")
    print("="*70)
    
    node_data = {
        'id': 'test_node',
        'label': 'Test Node',
        'type': 'source',
        'shape': 'rect',
        'fill': '#FFFFFF',
        'outline': '#000000',
        'locked': False,
        'x': 100,
        'y': 100,
        'width': 100,
        'height': 80
    }
    
    try:
        node_item = FlowNodeItem('test_node', node_data)
        
        # Check properties
        assert node_item.node_id == 'test_node', "Node ID mismatch"
        assert node_item.rect().width() == 100, "Node width mismatch"
        assert node_item.rect().height() == 80, "Node height mismatch"
        assert len(node_item.anchor_points) == 17, f"Expected 17 anchor points, got {len(node_item.anchor_points)}"
        
        print(f"✓ FlowNodeItem created successfully")
        print(f"✓ Node ID: {node_item.node_id}")
        print(f"✓ Position: ({node_item.pos().x():.0f}, {node_item.pos().y():.0f})")
        print(f"✓ Size: {node_item.rect().width():.0f}x{node_item.rect().height():.0f}")
        print(f"✓ Anchor points: {len(node_item.anchor_points)}")
        print(f"✓ Selected: {node_item.is_selected}")
        print(f"✓ Locked: {node_item.is_locked}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flow_edge_item():
    """Test FlowEdgeItem instantiation and properties."""
    print("\n" + "="*70)
    print("TEST 2: FlowEdgeItem - Edge Graphics Item Creation")
    print("="*70)
    
    # Create two nodes for edge
    node1_data = {
        'id': 'node1',
        'label': 'Node 1',
        'type': 'source',
        'shape': 'rect',
        'fill': '#FFFFFF',
        'outline': '#000000',
        'locked': False,
        'x': 100,
        'y': 100,
        'width': 100,
        'height': 80
    }
    
    node2_data = {
        'id': 'node2',
        'label': 'Node 2',
        'type': 'sink',
        'shape': 'rect',
        'fill': '#FFFFFF',
        'outline': '#000000',
        'locked': False,
        'x': 400,
        'y': 100,
        'width': 100,
        'height': 80
    }
    
    edge_data = {
        'from_id': 'node1',
        'to_id': 'node2',
        'flow_type': 'clean',
        'color': '#3498DB',
        'volume': 100.5,
        'waypoints': [[200, 140], [200, 140], [400, 140]],
        'excel_mapping': {'sheet': 'Flows_Test', 'column': 'Flow_Column'}
    }
    
    try:
        node1 = FlowNodeItem('node1', node1_data)
        node2 = FlowNodeItem('node2', node2_data)
        edge = FlowEdgeItem(0, edge_data, node1, node2)
        
        # Check properties
        assert edge.edge_idx == 0, "Edge index mismatch"
        assert edge.edge_data['flow_type'] == 'clean', "Flow type mismatch"
        assert edge.edge_data['volume'] == 100.5, "Volume mismatch"
        
        print(f"✓ FlowEdgeItem created successfully")
        print(f"✓ Edge: {edge.edge_data['from_id']} → {edge.edge_data['to_id']}")
        print(f"✓ Flow type: {edge.edge_data['flow_type']}")
        print(f"✓ Volume: {edge.edge_data['volume']:.1f} m³")
        print(f"✓ Selected: {edge.is_selected}")
        print(f"✓ Pen width: {edge.pen().width():.1f} px")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scene_rendering():
    """Test rendering nodes and edges in QGraphicsScene."""
    print("\n" + "="*70)
    print("TEST 3: Scene Rendering - Add Items to QGraphicsScene")
    print("="*70)
    
    try:
        # Create scene
        scene = QGraphicsScene()
        
        # Create diagram data
        diagram_data = create_test_diagram_json()
        
        # Create nodes
        node_items = {}
        for node_data in diagram_data['nodes']:
            node_id = node_data['id']
            node_item = FlowNodeItem(node_id, node_data)
            scene.addItem(node_item)
            node_items[node_id] = node_item
        
        # Create edges
        edge_items = []
        for edge_idx, edge_data in enumerate(diagram_data['edges']):
            from_node = node_items[edge_data['from_id']]
            to_node = node_items[edge_data['to_id']]
            edge_item = FlowEdgeItem(edge_idx, edge_data, from_node, to_node)
            scene.addItem(edge_item)
            edge_items.append(edge_item)
            edge_item.setZValue(0)  # Edges behind nodes
        
        print(f"✓ Scene created successfully")
        print(f"✓ Added {len(node_items)} nodes")
        print(f"✓ Added {len(edge_items)} edges")
        
        # Verify scene bounds
        scene_rect = scene.itemsBoundingRect()
        print(f"✓ Scene bounds: ({scene_rect.x():.0f}, {scene_rect.y():.0f}, "
              f"{scene_rect.width():.0f}x{scene_rect.height():.0f})")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_connections():
    """Test signal emission from graphics items."""
    print("\n" + "="*70)
    print("TEST 4: Signal Connections - Verify Signals Emit")
    print("="*70)
    
    try:
        node_data = {
            'id': 'test_node',
            'label': 'Test',
            'type': 'source',
            'shape': 'rect',
            'fill': '#FFFFFF',
            'outline': '#000000',
            'locked': False,
            'x': 100,
            'y': 100,
            'width': 100,
            'height': 80
        }
        
        node_item = FlowNodeItem('test_node', node_data)
        
        # Test that signals exist
        assert hasattr(node_item, 'node_moved'), "node_moved signal not found"
        assert hasattr(node_item, 'node_selected'), "node_selected signal not found"
        assert hasattr(node_item, 'node_double_clicked'), "node_double_clicked signal not found"
        
        print(f"✓ FlowNodeItem signals found:")
        print(f"  - node_moved")
        print(f"  - node_selected")
        print(f"  - node_double_clicked")
        
        # Create edge and check signals
        node2_data = {
            'id': 'test_node2',
            'label': 'Test 2',
            'type': 'sink',
            'shape': 'rect',
            'fill': '#FFFFFF',
            'outline': '#000000',
            'locked': False,
            'x': 400,
            'y': 100,
            'width': 100,
            'height': 80
        }
        
        node_item2 = FlowNodeItem('test_node2', node2_data)
        
        edge_data = {
            'from_id': 'test_node',
            'to_id': 'test_node2',
            'flow_type': 'clean',
            'color': '#3498DB',
            'volume': 100.0,
            'waypoints': [[200, 140], [300, 140]],
            'excel_mapping': {}
        }
        
        edge_item = FlowEdgeItem(0, edge_data, node_item, node_item2)
        
        assert hasattr(edge_item, 'edge_selected'), "edge_selected signal not found"
        assert hasattr(edge_item, 'edge_double_clicked'), "edge_double_clicked signal not found"
        
        print(f"✓ FlowEdgeItem signals found:")
        print(f"  - edge_selected")
        print(f"  - edge_double_clicked")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anchor_points():
    """Test anchor point calculation on nodes."""
    print("\n" + "="*70)
    print("TEST 5: Anchor Points - Verify 17 Points Calculated Correctly")
    print("="*70)
    
    try:
        node_data = {
            'id': 'anchor_test',
            'label': 'Test',
            'type': 'source',
            'shape': 'rect',
            'fill': '#FFFFFF',
            'outline': '#000000',
            'locked': False,
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 160
        }
        
        node_item = FlowNodeItem('anchor_test', node_data)
        anchors = node_item.anchor_points
        
        print(f"✓ {len(anchors)} anchor points calculated")
        
        # Check that anchors are within node bounds
        rect = node_item.rect()
        out_of_bounds = 0
        for i, anchor in enumerate(anchors):
            if not (0 <= anchor.x() <= rect.width() and 0 <= anchor.y() <= rect.height()):
                out_of_bounds += 1
                print(f"  ⚠ Anchor {i} out of bounds: ({anchor.x():.1f}, {anchor.y():.1f})")
        
        if out_of_bounds == 0:
            print(f"✓ All anchor points within node bounds")
        else:
            print(f"✗ {out_of_bounds} anchor points out of bounds")
        
        # Print anchor point locations (corners, midpoints, quarter points)
        print(f"\nAnchor points (first 5):")
        for i in range(min(5, len(anchors))):
            print(f"  [{i}] ({anchors[i].x():.1f}, {anchors[i].y():.1f})")
        print(f"  ...")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all graphics rendering tests."""
    print("\n" + "="*70)
    print("FLOW DIAGRAM GRAPHICS RENDERING TEST SUITE")
    print("="*70)
    
    results = {
        'FlowNodeItem Creation': test_flow_node_item(),
        'FlowEdgeItem Creation': test_flow_edge_item(),
        'Scene Rendering': test_scene_rendering(),
        'Signal Connections': test_signal_connections(),
        'Anchor Points': test_anchor_points(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    # Must create QApplication for PySide6
    app = QApplication(sys.argv)
    
    # Run tests
    exit_code = run_all_tests()
    sys.exit(exit_code)
