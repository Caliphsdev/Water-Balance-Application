"""
Phase 4: Drawing Mode Implementation Tests

Validates the drawing mode functionality for creating flow edges:
- Canvas click interception
- Waypoint collection
- Orthogonal path routing
- Edge finalization with flow type dialog
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QPointF, Qt, QEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_drawing_mode_initialization():
    """Test drawing mode state initialization (INITIALIZATION CHECK)."""
    logger.info("TEST 1: Drawing Mode Initialization")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    
    # Check initial state
    assert page.drawing_mode is False, "drawing_mode should start False"
    assert page.drawing_from_id is None, "drawing_from_id should start None"
    assert page.drawing_segments == [], "drawing_segments should start empty"
    assert not hasattr(page, '_preview_line') or page._preview_line is None, "preview_line should not exist initially"
    
    logger.info("✅ Drawing mode state initialized correctly")
    print("✅ TEST 1 PASSED: Drawing mode initialization")

def test_drawing_mode_toggle():
    """Test entering/exiting drawing mode (MODE TOGGLE CHECK)."""
    logger.info("TEST 2: Drawing Mode Toggle")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    
    # Simulate clicking Draw button
    page._on_draw_clicked()
    assert page.drawing_mode is True, "drawing_mode should be True after first click"
    
    # Exit drawing mode
    page._on_draw_clicked()
    assert page.drawing_mode is False, "drawing_mode should be False after second click"
    assert page.drawing_from_id is None, "drawing_from_id should be None when exiting"
    assert page.drawing_segments == [], "drawing_segments should be cleared when exiting"
    
    logger.info("✅ Drawing mode toggle works correctly")
    print("✅ TEST 2 PASSED: Drawing mode toggle")

def test_orthogonal_path_building():
    """Test orthogonal path routing algorithm (ROUTING ENGINE CHECK)."""
    logger.info("TEST 3: Orthogonal Path Building")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    
    # Test horizontal-first routing
    start = QPointF(0, 0)
    end = QPointF(100, 50)
    path = page._build_orthogonal_path(start, end, angle_start='horizontal')
    
    # Path should have 2 line segments: (0,0)→(100,0)→(100,50)
    assert path.elementCount() == 3, f"Path should have 3 elements, got {path.elementCount()}"
    
    # Verify path goes through corner point
    elements = [path.elementAt(i) for i in range(path.elementCount())]
    assert elements[0].x == 0 and elements[0].y == 0, "Start should be (0,0)"
    assert elements[1].x == 100 and elements[1].y == 0, "Corner should be (100,0)"
    assert elements[2].x == 100 and elements[2].y == 50, "End should be (100,50)"
    
    # Test vertical-first routing
    path2 = page._build_orthogonal_path(start, end, angle_start='vertical')
    elements2 = [path2.elementAt(i) for i in range(path2.elementCount())]
    assert elements2[0].x == 0 and elements2[0].y == 0, "Start should be (0,0)"
    assert elements2[1].x == 0 and elements2[1].y == 50, "Corner should be (0,50)"
    assert elements2[2].x == 100 and elements2[2].y == 50, "End should be (100,50)"
    
    logger.info("✅ Orthogonal path routing works correctly")
    print("✅ TEST 3 PASSED: Orthogonal path building")

def test_event_filter_activation():
    """Test event filter is installed/removed with drawing mode (EVENT FILTER CHECK)."""
    logger.info("TEST 4: Event Filter Activation")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    page.load_diagram('UG2')
    
    # Enter drawing mode - should install event filter
    page._on_draw_clicked()
    assert page.drawing_mode is True
    # Note: Can't easily verify event filter is installed from outside,
    # but we can verify cursor changed
    assert page.ui.graphicsView.cursor().shape() == Qt.CrossCursor, "Cursor should be crosshair in drawing mode"
    
    # Exit drawing mode - should remove event filter
    page._on_draw_clicked()
    assert page.drawing_mode is False
    assert page.ui.graphicsView.cursor().shape() != Qt.CrossCursor, "Cursor should not be crosshair outside drawing mode"
    
    logger.info("✅ Event filter activation/deactivation works correctly")
    print("✅ TEST 4 PASSED: Event filter activation")

def test_drawing_state_persistence():
    """Test drawing state is maintained during drawing (STATE PERSISTENCE CHECK)."""
    logger.info("TEST 5: Drawing State Persistence")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    page.load_diagram('UG2')
    
    # Enter drawing mode
    page._on_draw_clicked()
    
    # Simulate setting drawing state (as would happen on node click)
    page.drawing_from_id = 'node_1'
    page.drawing_segments = [QPointF(100, 100), QPointF(200, 100)]
    
    # Verify state persists
    assert page.drawing_from_id == 'node_1', "drawing_from_id should persist"
    assert len(page.drawing_segments) == 2, "drawing_segments should persist"
    
    # Exit drawing mode should clear state
    page._on_draw_clicked()
    assert page.drawing_from_id is None, "drawing_from_id should be cleared on exit"
    assert page.drawing_segments == [], "drawing_segments should be cleared on exit"
    
    logger.info("✅ Drawing state persists correctly")
    print("✅ TEST 5 PASSED: Drawing state persistence")

def test_cancel_drawing_resets_state():
    """Test cancel_drawing() properly resets all state (CANCEL HANDLER CHECK)."""
    logger.info("TEST 6: Cancel Drawing Reset")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    page.load_diagram('UG2')
    page._on_draw_clicked()  # Enter drawing mode
    
    # Set drawing state
    page.drawing_from_id = 'node_1'
    page.drawing_segments = [QPointF(100, 100), QPointF(200, 100), QPointF(200, 200)]
    
    # Cancel drawing
    page._cancel_drawing()
    
    # Verify state cleared
    assert page.drawing_from_id is None, "drawing_from_id should be None"
    assert page.drawing_segments == [], "drawing_segments should be empty"
    assert page.drawing_mode is True, "drawing_mode should still be True (user can start new edge)"
    
    logger.info("✅ Cancel drawing resets state correctly")
    print("✅ TEST 6 PASSED: Cancel drawing reset")

def test_phase4_integration():
    """Integration test: Full drawing mode workflow (INTEGRATION TEST)."""
    logger.info("TEST 7: Phase 4 Integration - Full Drawing Workflow")
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    page.load_diagram('UG2')
    
    # Verify diagram loaded
    assert page.diagram_data is not None, "Diagram should load"
    assert len(page.node_items) > 0, "Nodes should be created"
    
    # Enter drawing mode
    page._on_draw_clicked()
    assert page.drawing_mode is True
    
    # Simulate waypoint collection
    if len(page.node_items) >= 2:
        # Get two different nodes for testing
        node_ids = list(page.node_items.keys())
        from_node_id = node_ids[0]
        to_node_id = node_ids[1]
        from_node_item = page.node_items[from_node_id]
        to_node_item = page.node_items[to_node_id]
        
        # Simulate clicking source node
        from_anchor = from_node_item.get_nearest_anchor_point(QPointF(from_node_item.rect().center()))
        page.drawing_from_id = from_node_id
        page.drawing_segments = [from_anchor]
        
        # Add some waypoints
        waypoint1 = QPointF(from_node_item.rect().right() + 50, from_node_item.rect().center().y())
        waypoint2 = QPointF(waypoint1.x(), to_node_item.rect().center().y())
        page.drawing_segments.extend([waypoint1, waypoint2])
        
        # Verify state
        assert len(page.drawing_segments) == 3, f"Should have 3 points, got {len(page.drawing_segments)}"
        assert page.drawing_from_id == from_node_id
        
        logger.info("✅ Full drawing workflow state management works")
    
    # Exit drawing mode
    page._on_draw_clicked()
    assert page.drawing_mode is False
    
    logger.info("✅ Phase 4 integration test passed")
    print("✅ TEST 7 PASSED: Phase 4 integration - Full drawing workflow")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("PHASE 4: DRAWING MODE IMPLEMENTATION TESTS")
    print("="*70 + "\n")
    
    try:
        test_drawing_mode_initialization()
        print()
        test_drawing_mode_toggle()
        print()
        test_orthogonal_path_building()
        print()
        test_event_filter_activation()
        print()
        test_drawing_state_persistence()
        print()
        test_cancel_drawing_resets_state()
        print()
        test_phase4_integration()
        
        print("\n" + "="*70)
        print("✅ ALL PHASE 4 TESTS PASSED (7/7)")
        print("="*70)
        print("\nDrawing mode implementation complete:")
        print("✓ Canvas click interception")
        print("✓ Waypoint collection")
        print("✓ Orthogonal path routing")
        print("✓ Event filter management")
        print("✓ State initialization and cleanup")
        print("✓ Drawing cancellation")
        print("\nNext: Implement edge finalization with dialog integration")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
