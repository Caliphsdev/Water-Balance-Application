"""Optional Excel structure inspection test.

This test is intentionally non-blocking for CI/release readiness because it
depends on a local .xls file outside the repository.
"""

from __future__ import annotations

from pathlib import Path

import pytest


FILE_PATH = Path(
    "C:/Users/Caliphs Zvinowanda/OneDrive/Desktop/Monitoring Borehole/Boreholes Q3 2021.xls"
)


@pytest.mark.skipif(not FILE_PATH.exists(), reason="Local .xls sample file not available")
def test_excel_structure_sample_file_loads() -> None:
    """Ensure the local sample .xls can be opened when present."""
    pd = pytest.importorskip("pandas")
    pytest.importorskip("xlrd")

    df = pd.read_excel(FILE_PATH, header=None)
    assert len(df) > 0
    assert len(df.columns) > 0
