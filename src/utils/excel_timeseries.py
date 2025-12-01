from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd


@dataclass
class ExcelTimeSeriesConfig:
    file_path: Path
    sheet_name: str = "Meter Readings"
    header_row: int = 3  # 1-based index where column names live
    first_data_row: int = 5  # 1-based index where data starts
    date_column: str = "A"  # Excel-style column for dates


class ExcelTimeSeriesRepository:
    """Lightweight reader for the Meter Readings sheet.

    This class is intentionally minimal for now: it loads the target sheet
    into a DataFrame and lets callers ask for monthly values by column
    header name (row 3 in your workbook) and exact date (column A).
    """

    def __init__(self, config: ExcelTimeSeriesConfig) -> None:
        self.config = config
        self._df: Optional[pd.DataFrame] = None
        # Cache: (date, header_name) -> value
        self._value_cache: Dict[tuple[date, str], float] = {}

    def _load(self) -> None:
        if self._df is not None:
            return
        if not self.config.file_path.exists():
            raise FileNotFoundError(f"Excel time series file not found: {self.config.file_path}")

        # Read the sheet with header at row 3 (1-based -> header=2)
        df = pd.read_excel(
            self.config.file_path,
            sheet_name=self.config.sheet_name,
            header=self.config.header_row - 1,
            engine="openpyxl",
        )
        # Normalize the date column from column A; pandas will give it a
        # generated name if the header is blank. We assume it's the first
        # column.
        first_col_name = df.columns[0]
        df = df.rename(columns={first_col_name: "Date"})
        # Drop any rows before first_data_row (1-based)
        # header_row is already consumed by pandas, so we need to skip
        # (first_data_row - header_row - 1) additional rows.
        extra_skip = max(0, self.config.first_data_row - self.config.header_row - 1)
        if extra_skip > 0:
            df = df.iloc[extra_skip:].reset_index(drop=True)
        # Ensure Date is datetime.date and add helper Year/Month columns
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        df["Year"] = df["Date"].apply(lambda d: d.year if pd.notna(d) else None)
        df["Month"] = df["Date"].apply(lambda d: d.month if pd.notna(d) else None)
        self._df = df

    def get_monthly_value(self, calculation_date: date, header_name: str) -> float:
        """Return the value for a given header and month date.

        Assumes one row per month; matches on exact date in column A.
        Returns 0.0 when no row or cell is found.
        """
        key = (calculation_date, header_name)
        if key in self._value_cache:
            return self._value_cache[key]

        self._load()
        assert self._df is not None

        val, _ = self._lookup_row(calculation_date, header_name)
        self._value_cache[key] = val
        return val

    def debug_get_row(self, calculation_date: date) -> pd.DataFrame:
        """Return the raw DataFrame row(s) matching the given date.

        This is for debugging so you can inspect exactly which
        Excel row is being matched (or not matched).
        Uses exact Date equality; for month-level matching, rely on
        the Year/Month columns.
        """
        self._load()
        assert self._df is not None
        return self._df[self._df["Date"] == calculation_date]

    def _lookup_row(self, calculation_date: date, header_name: str) -> tuple[float, Optional[date]]:
        """Internal helper: find the value and the actual row date used."""
        assert self._df is not None
        df = self._df

        # Match on year+month only because the day-of-month in the
        # Excel sheet can vary (e.g., 30th, 31st, mid-month). We
        # assume at most one data row per month.
        y = calculation_date.year
        m = calculation_date.month
        rows = df[(df["Year"] == y) & (df["Month"] == m)]
        if rows.empty:
            return 0.0, None

        row = rows.iloc[0]
        if header_name not in rows.columns:
            return 0.0, row["Date"]

        raw = row[header_name]
        try:
            val = float(raw) if pd.notna(raw) else 0.0
        except (TypeError, ValueError):
            val = 0.0
        return val, row["Date"]
    
    def get_latest_date(self) -> Optional[date]:
        """Return the most recent date available in the Excel data.
        
        Returns None if no data exists.
        """
        self._load()
        assert self._df is not None
        
        if self._df.empty or self._df["Date"].isna().all():
            return None
        
        # Get the maximum date that's not NaT/NaN
        valid_dates = self._df["Date"].dropna()
        if valid_dates.empty:
            return None
        
        return valid_dates.max()


# Convenience factory for the app to use

def get_default_excel_repo() -> ExcelTimeSeriesRepository:
    from utils.config_manager import config
    from utils.app_logger import logger
    base_dir = Path(__file__).resolve().parents[2]
    # Get path from config or use default
    excel_path = config.get('data_sources.legacy_excel_path', 'data/New Water Balance  20250930 Oct.xlsx')
    file_path = base_dir / excel_path if not Path(excel_path).is_absolute() else Path(excel_path)
    
    # Warn if file doesn't exist but don't crash
    if not file_path.exists():
        logger.warning(f"TRP Water Balance Excel file not found: {file_path}. Historical data will not be available.")
    
    cfg = ExcelTimeSeriesConfig(file_path=file_path)
    return ExcelTimeSeriesRepository(cfg)
