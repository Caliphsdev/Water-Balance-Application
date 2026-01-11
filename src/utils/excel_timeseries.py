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
        
        # Check if file exists - silently return empty DataFrame
        if not self.config.file_path.exists():
            # Don't warn on startup - only when actually trying to access data
            # User can check file status in Settings > Data Sources
            self._df = pd.DataFrame()
            return

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

    def get_matched_row_date(self, calculation_date: date) -> Optional[date]:
        """Return the actual Date in the sheet that matches the given month.

        Matches by year and month (ignoring day) and returns the first row's
        Date if present; otherwise returns None. This is useful for UI audit
        displays where the UI uses end-of-month dates that may not match the
        sheet's exact day-of-month.
        """
        self._load()
        assert self._df is not None
        y, m = calculation_date.year, calculation_date.month
        rows = self._df[(self._df["Year"] == y) & (self._df["Month"] == m)]
        if rows.empty:
            return None
        try:
            return rows.iloc[0]["Date"]
        except Exception:
            return None

    def has_header(self, header_name: str) -> bool:
        """Return True if the provided header exists in the sheet columns."""
        self._load()
        assert self._df is not None
        return header_name in list(self._df.columns)

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
        
        Returns None if no data exists or file is not available.
        """
        self._load()
        
        # Handle case where Excel file doesn't exist (empty DataFrame)
        if self._df is None or self._df.empty:
            return None
        
        if "Date" not in self._df.columns or self._df["Date"].isna().all():
            return None
        
        # Get the maximum date that's not NaT/NaN
        valid_dates = self._df["Date"].dropna()
        if valid_dates.empty:
            return None
        
        return valid_dates.max()


# Convenience factory for the app to use

def get_default_excel_repo() -> ExcelTimeSeriesRepository:
    """Get default Excel repository (lazy-loaded, no warnings on init)"""
    from utils.config_manager import config
    base_dir = Path(__file__).resolve().parents[2]
    # Get path from config or use default
    excel_path = config.get('data_sources.legacy_excel_path', 'data/New Water Balance  20250930 Oct.xlsx')
    file_path = base_dir / excel_path if not Path(excel_path).is_absolute() else Path(excel_path)
    
    # Don't warn on init - file will be checked when actually loaded
    cfg = ExcelTimeSeriesConfig(file_path=file_path)
    return ExcelTimeSeriesRepository(cfg)
