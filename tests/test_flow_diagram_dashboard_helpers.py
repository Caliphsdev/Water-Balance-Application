"""Helper-level tests for flow diagram dashboard logic.

These tests avoid UI rendering and mapped component mutations while
covering filtering and area detection helpers that back the flow diagram
dashboard.
"""

from types import SimpleNamespace

from src.ui.flow_diagram_dashboard import (
    DetailedNetworkFlowDiagram,
    FlowDiagramBalanceCheckDialog,
)


def test_get_filtered_edges_respects_mapping_and_area_filter():
    """Ensure mapped, area-matching edges are returned for categorization."""
    edges = [
        {"id": "edge1", "excel_mapping": "colA", "area": "UG2N"},
        {
            "id": "edge2",
            "excel_mapping": {
                "enabled": True,
                "column": "colB",
                "sheet": "Flows_UG2S",
            },
            "area": "UG2S",
        },
        {"id": "edge3", "excel_mapping": {}},
        {"id": "edge4", "excel_mapping": {"enabled": False, "column": "colD"}},
        {
            "id": "edge5",
            "excel_mapping": {
                "enabled": True,
                "column": None,
                "sheet": "Flows_UG2N",
            },
        },
    ]
    diagram = SimpleNamespace(area_data={"edges": edges}, area_code="UG2N")
    dialog = FlowDiagramBalanceCheckDialog(parent=None, flow_diagram=diagram)
    dialog.area_filter_var = SimpleNamespace(
        get=lambda: "UG2N", set=lambda value: None
    )

    filtered = dialog._get_filtered_edges()

    assert [edge[1]["id"] for edge in filtered] == ["edge1"]


def test_collect_edge_areas_uses_sheet_fallback():
    """Area collection includes explicit areas and mapping sheet fallbacks."""
    edges = [
        {"id": "edge1", "excel_mapping": "colA", "area": "UG2N"},
        {
            "id": "edge2",
            "excel_mapping": {
                "enabled": True,
                "column": "colB",
                "sheet": "Flows_UG2S",
            },
        },
        {"id": "edge3", "excel_mapping": "colC", "area": "UG2S"},
    ]
    diagram = SimpleNamespace(area_data={"edges": edges})
    dialog = FlowDiagramBalanceCheckDialog(parent=None, flow_diagram=diagram)

    areas = dialog._collect_edge_areas()

    assert areas == ["Flows_UG2S", "UG2N", "UG2S"]


def test_get_area_code_from_title_matches_known_areas():
    """Area code inference maps known titles and falls back to UG2N."""
    diagram = DetailedNetworkFlowDiagram.__new__(DetailedNetworkFlowDiagram)
    diagram.area_data = {"title": "Merensky Plant Flow Diagram"}

    assert diagram._get_area_code_from_title() == "MERPLANT"

    diagram.area_data = {"title": "Unmapped Custom Area"}

    assert diagram._get_area_code_from_title() == "UG2N"
