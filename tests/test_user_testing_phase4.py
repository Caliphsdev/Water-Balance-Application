"""
Phase 4: User Testing - Interactive Testing Script

This script provides an interactive testing environment for validating
the drawing mode functionality with actual diagrams.

Run this to test drawing mode without running a full Qt application.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(Path(__file__).parent))

import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_diagram(area_code='UG2'):
    """Load a test diagram from JSON (USER TESTING)."""
    diagram_path = Path(f'data/diagrams/{area_code}_flow_diagram.json')
    
    if not diagram_path.exists():
        logger.error(f"❌ Diagram not found: {diagram_path}")
        return None
    
    with open(diagram_path) as f:
        diagram_data = json.load(f)
    
    logger.info(f"✅ Loaded diagram: {area_code}")
    logger.info(f"   Nodes: {len(diagram_data['nodes'])}")
    logger.info(f"   Edges: {len(diagram_data['edges'])}")
    
    return diagram_data

def print_diagram_summary(diagram_data):
    """Print a summary of the loaded diagram (TEST REPORT)."""
    print("\n" + "="*70)
    print("DIAGRAM SUMMARY")
    print("="*70)
    
    print(f"\nArea Code: {diagram_data['area_code']}")
    
    print(f"\nNODES ({len(diagram_data['nodes'])}):")
    for node in diagram_data['nodes'][:5]:  # Show first 5
        print(f"  • {node['id']:20s} ({node['label']})")
    if len(diagram_data['nodes']) > 5:
        print(f"  ... and {len(diagram_data['nodes']) - 5} more")
    
    print(f"\nEXISTING EDGES ({len(diagram_data['edges'])}):")
    for edge in diagram_data['edges'][:5]:  # Show first 5
        print(f"  • {edge['from_id']:15s} → {edge['to_id']:15s} ({edge['flow_type']})")
    if len(diagram_data['edges']) > 5:
        print(f"  ... and {len(diagram_data['edges']) - 5} more")
    
    print("\n" + "="*70)

def test_scenario_1_basic_drawing():
    """TEST SCENARIO 1: Basic drawing mode (SMOKE TEST)."""
    logger.info("\n" + "="*70)
    logger.info("TEST SCENARIO 1: Basic Drawing Mode Toggle")
    logger.info("="*70)
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPointF
    
    app = QApplication.instance() or QApplication([])
    
    # Load diagram
    diagram_data = load_test_diagram('UG2')
    if not diagram_data:
        logger.error("Cannot proceed: diagram not loaded")
        return False
    
    # Create page
    page = FlowDiagramPage()
    page.load_diagram('UG2')
    
    print_diagram_summary(page.diagram_data)
    
    # Test 1: Enter drawing mode
    logger.info("\n[Step 1] Entering drawing mode...")
    page._on_draw_clicked()
    assert page.drawing_mode is True, "Drawing mode should be True"
    logger.info("✅ Drawing mode activated")
    logger.info(f"   drawing_mode: {page.drawing_mode}")
    logger.info(f"   cursor: {page.ui.graphicsView.cursor().shape()}")
    
    # Test 2: Exit drawing mode
    logger.info("\n[Step 2] Exiting drawing mode...")
    page._on_draw_clicked()
    assert page.drawing_mode is False, "Drawing mode should be False"
    logger.info("✅ Drawing mode deactivated")
    logger.info(f"   drawing_mode: {page.drawing_mode}")
    logger.info(f"   drawing_from_id: {page.drawing_from_id}")
    logger.info(f"   drawing_segments: {page.drawing_segments}")
    
    return True

def test_scenario_2_waypoint_collection():
    """TEST SCENARIO 2: Waypoint collection during drawing (STATE TEST)."""
    logger.info("\n" + "="*70)
    logger.info("TEST SCENARIO 2: Waypoint Collection")
    logger.info("="*70)
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPointF
    
    app = QApplication.instance() or QApplication([])
    
    page = FlowDiagramPage()
    page.load_diagram('UG2')
    
    # Enter drawing mode
    page._on_draw_clicked()
    
    # Simulate setting drawing state (as would happen on node click)
    source_node = list(page.node_items.values())[0]
    source_anchor = source_node.get_nearest_anchor_point(QPointF(source_node.rect().center()))
    
    page.drawing_from_id = source_node.node_id
    page.drawing_segments = [source_anchor]
    
    logger.info("\n[Step 1] Source node selected")
    logger.info(f"✅ drawing_from_id: {page.drawing_from_id}")
    logger.info(f"   drawing_segments: {len(page.drawing_segments)} waypoint(s)")
    
    # Add waypoints
    logger.info("\n[Step 2] Adding waypoints...")
    for i in range(3):
        waypoint = QPointF(source_anchor.x() + (i+1)*100, source_anchor.y() + (i+1)*50)
        page.drawing_segments.append(waypoint)
        logger.info(f"✅ Waypoint {i+1}: ({waypoint.x():.0f}, {waypoint.y():.0f})")
    
    logger.info(f"\nTotal waypoints: {len(page.drawing_segments)}")
    
    # Test cancellation
    logger.info("\n[Step 3] Cancelling drawing...")
    page._cancel_drawing()
    assert page.drawing_from_id is None, "drawing_from_id should be cleared"
    assert page.drawing_segments == [], "drawing_segments should be cleared"
    logger.info("✅ Drawing cancelled, state reset")
    logger.info(f"   drawing_from_id: {page.drawing_from_id}")
    logger.info(f"   drawing_segments: {page.drawing_segments}")
    
    return True

def test_scenario_3_orthogonal_routing():
    """TEST SCENARIO 3: Orthogonal path routing (ALGORITHM TEST)."""
    logger.info("\n" + "="*70)
    logger.info("TEST SCENARIO 3: Orthogonal Path Routing")
    logger.info("="*70)
    
    from ui.dashboards.flow_diagram_page import FlowDiagramPage
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPointF
    
    app = QApplication.instance() or QApplication([])
    page = FlowDiagramPage()
    
    # Test horizontal-first routing
    logger.info("\n[Test 1] Horizontal-First Routing")
    start = QPointF(0, 0)
    end = QPointF(100, 50)
    path = page._build_orthogonal_path(start, end, angle_start='horizontal')
    
    elements = [path.elementAt(i) for i in range(path.elementCount())]
    logger.info(f"✅ Path created with {len(elements)} points:")
    for i, elem in enumerate(elements):
        logger.info(f"   Point {i}: ({elem.x:.0f}, {elem.y:.0f})")
    
    assert elements[0].x == 0 and elements[0].y == 0, "Start incorrect"
    assert elements[1].x == 100 and elements[1].y == 0, "Corner incorrect"
    assert elements[2].x == 100 and elements[2].y == 50, "End incorrect"
    logger.info("✅ Horizontal-first routing verified")
    
    # Test vertical-first routing
    logger.info("\n[Test 2] Vertical-First Routing")
    path2 = page._build_orthogonal_path(start, end, angle_start='vertical')
    
    elements2 = [path2.elementAt(i) for i in range(path2.elementCount())]
    logger.info(f"✅ Path created with {len(elements2)} points:")
    for i, elem in enumerate(elements2):
        logger.info(f"   Point {i}: ({elem.x:.0f}, {elem.y:.0f})")
    
    assert elements2[0].x == 0 and elements2[0].y == 0, "Start incorrect"
    assert elements2[1].x == 0 and elements2[1].y == 50, "Corner incorrect"
    assert elements2[2].x == 100 and elements2[2].y == 50, "End incorrect"
    logger.info("✅ Vertical-first routing verified")
    
    return True

def print_test_results(results):
    """Print comprehensive test results (TEST REPORT)."""
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    print("\nResults:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*70)
    if passed == total:
        print("🎉 ALL TESTS PASSED - READY FOR PHASE 5!")
    else:
        print(f"⚠️  {total - passed} test(s) failed - review needed")
    print("="*70)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("PHASE 4: USER TESTING - INTERACTIVE VALIDATION")
    print("="*70)
    print("\nThis script validates Phase 4 drawing mode with actual diagrams.")
    print("Tests performed:")
    print("  1. Basic drawing mode toggle")
    print("  2. Waypoint collection and cancellation")
    print("  3. Orthogonal path routing algorithm")
    
    results = {}
    
    try:
        results['Drawing Mode Toggle'] = test_scenario_1_basic_drawing()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        results['Drawing Mode Toggle'] = False
    
    try:
        results['Waypoint Collection'] = test_scenario_2_waypoint_collection()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        results['Waypoint Collection'] = False
    
    try:
        results['Orthogonal Routing'] = test_scenario_3_orthogonal_routing()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        results['Orthogonal Routing'] = False
    
    print_test_results(results)
    
    print("\n📚 Next Steps:")
    print("  1. Review test results above")
    print("  2. Check Docs/PHASE_4_DRAWING_MODE_COMPLETE.md for details")
    print("  3. Run manual tests with actual diagrams (see README)")
    print("  4. Proceed to Phase 5 when satisfied")
    print()
