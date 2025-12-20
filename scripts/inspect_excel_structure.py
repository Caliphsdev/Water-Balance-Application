"""Inspect Excel workbook sheets and columns (standalone).

Reads the Excel file resolved via config (FlowVolumeLoader) or an optional
override path, and prints sheet names plus their columns. Use this to verify
sheet/column layout without running the app.
"""

import argparse
import sys
from pathlib import Path
from typing import List

import pandas as pd

# Ensure src is on path for config/loader reuse
SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from utils.flow_volume_loader import get_flow_volume_loader


def list_sheet_columns(xlsx_path: Path) -> None:
    """Print sheet names and their columns."""
    xls = pd.ExcelFile(xlsx_path, engine="openpyxl")
    print(f"Excel file: {xlsx_path}")
    print(f"Total sheets: {len(xls.sheet_names)}\n")

    for sheet in xls.sheet_names:
        # Try header=2 for flow sheets, fallback to header=0 for others
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sheet, engine="openpyxl", header=2)
        except Exception:
            df = pd.read_excel(xlsx_path, sheet_name=sheet, engine="openpyxl", header=0)

        columns: List[str] = [c for c in df.columns if pd.notna(c)]
        print(f"Sheet: {sheet}")
        print(f"  Columns ({len(columns)}):")
        for idx, col in enumerate(columns, 1):
            print(f"    {idx:2d}. {col}")
        print()


def resolve_excel_path(override: str | None) -> Path:
    """Resolve the Excel path using override or config via FlowVolumeLoader."""
    if override:
        return Path(override).resolve()
    loader = get_flow_volume_loader()
    return loader.excel_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Excel sheets and columns")
    parser.add_argument("excel_path", nargs="?", help="Optional path to Excel file; defaults to config path")
    args = parser.parse_args()

    xlsx_path = resolve_excel_path(args.excel_path)
    if not xlsx_path.exists():
        print(f"❌ Excel file not found: {xlsx_path}")
        return 1

    list_sheet_columns(xlsx_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
