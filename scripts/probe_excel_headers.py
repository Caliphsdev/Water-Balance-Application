"""
Probe Excel header detection across all Flows_* sheets and print results.

Usage:
  .venv\Scripts\python scripts\probe_excel_headers.py

This script resets the FlowVolumeLoader, lists all sheets, filters Flows_*,
then invokes list_sheet_columns() for each and prints counts plus a preview.
"""
import sys
from pathlib import Path

# Import shim for src/
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.flow_volume_loader import get_flow_volume_loader, reset_flow_volume_loader
from utils.app_logger import logger


def main() -> None:
    reset_flow_volume_loader()
    loader = get_flow_volume_loader()

    sheets = loader.list_sheets()
    flows_sheets = [s for s in sheets if s.startswith('Flows_')]

    if not flows_sheets:
        logger.error('❌ No Flows_* sheets found in workbook')
        print('No Flows_* sheets found in workbook')
        return

    print(f"Found {len(flows_sheets)} Flows_* sheets: {', '.join(flows_sheets)}")
    total_cols = 0
    for sheet in sorted(flows_sheets):
        cols = loader.list_sheet_columns(sheet)
        total_cols += len(cols)
        preview = ', '.join(cols[:10]) if cols else '(none)'
        logger.info(f"📄 Columns for '{sheet}': {len(cols)} found")
        print(f"{sheet}: {len(cols)} columns")
        print(f"  Preview: {preview}")

    print(f"Total detected columns across Flows_*: {total_cols}")


if __name__ == '__main__':
    main()
