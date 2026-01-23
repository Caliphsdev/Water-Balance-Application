"""Integration-oriented tests for FlowVolumeLoader using a temp workbook.

These tests exercise sheet-aware volume loading without touching existing
mapped components or real Excel assets.
"""

import math
from pathlib import Path
import pandas as pd

from src.utils.flow_volume_loader import FlowVolumeLoader


def _build_workbook(tmp_path):
    """Create a temporary flow diagram workbook with primary and empty sheets."""
    path = tmp_path / "flows.xlsx"
    df_primary = pd.DataFrame(
        {"Year": [2025], "Month": [3], "FlowA": [100.0], "FlowB": [200.0]}
    )
    df_empty = pd.DataFrame({"Year": [2025], "Month": [3], "FlowZ": [math.nan]})
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_primary.to_excel(writer, sheet_name="Flows_UG2 North", index=False)
        df_empty.to_excel(writer, sheet_name="Flows_Old TSF", index=False)
    return path


def test_update_diagram_edges_populates_and_handles_missing_columns(tmp_path):
    """Volumes populate mapped edges and mark empty sheets with a dash label."""
    path = _build_workbook(tmp_path)
    loader = FlowVolumeLoader(excel_path=path)
    loader._resolve_excel_path = lambda override: path if override is None else Path(override)
    area_data = {
        "edges": [
            {
                "from": "A",
                "to": "B",
                "excel_mapping": {
                    "enabled": True,
                    "sheet": "Flows_UG2 North",
                    "column": "FlowA",
                },
            },
            {
                "from": "B",
                "to": "C",
                "excel_mapping": {"enabled": True, "column": "FlowB"},
            },
            {
                "from": "C",
                "to": "D",
                "excel_mapping": {
                    "enabled": True,
                    "sheet": "Flows_Old TSF",
                    "column": "FlowZ",
                },
            },
            {
                "from": "D",
                "to": "E",
                "excel_mapping": {
                    "enabled": True,
                    "sheet": "Flows_UG2 North",
                    "column": "Missing",
                },
            },
        ]
    }

    updated = loader.update_diagram_edges(area_data, area_code="UG2N", year=2025, month=3)
    edges = updated["edges"]

    assert edges[0]["volume"] == 100.0
    assert edges[0]["label"] == "100.00"
    assert edges[1]["volume"] == 200.0
    assert edges[2]["volume"] is None and edges[2].get("label") == "—"
    assert edges[3]["volume"] is None and "label" not in edges[3]


def test_get_flow_volume_respects_enabled_and_sheet(tmp_path):
    """Flow lookups honor enabled flag, explicit sheets, and missing columns."""
    path = _build_workbook(tmp_path)
    loader = FlowVolumeLoader(excel_path=path)
    loader._resolve_excel_path = lambda override: path if override is None else Path(override)

    assert loader.get_flow_volume("UG2N", {"enabled": False, "column": "FlowA"}, 2025, 3) is None
    assert loader.get_flow_volume("UG2N", {"enabled": True, "column": None}, 2025, 3) is None
    assert loader.get_flow_volume("UG2N", {"enabled": True, "column": "FlowA"}, 2025, 3) == 100.0
    assert loader.get_flow_volume(
        "OLDTSF",
        {"enabled": True, "sheet": "Flows_Old TSF", "column": "FlowZ"},
        2025,
        3,
    ) is None
