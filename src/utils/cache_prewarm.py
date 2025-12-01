"""Cache pre-warm utilities.

Provides functions to pre-warm the persistent cache for facility-month
storage results to speed up cold starts.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Tuple

import pandas as pd

from utils.app_logger import logger


def _latest_month_from_repo(repo) -> Optional[date]:
    """Determine the latest month present across known Excel sheets.

    Returns first day of that month as date or None if no dates found.
    """
    try:
        repo._load()  # ensure dataframes loaded
    except Exception:
        pass
    candidates = []
    for df in [
        getattr(repo, "_storage_df", None),
        getattr(repo, "_environmental_df", None),
        getattr(repo, "_production_df", None),
        getattr(repo, "_consumption_df", None),
        getattr(repo, "_seepage_df", None),
        getattr(repo, "_discharge_df", None),
    ]:
        if df is not None and getattr(df, "empty", True) is False and 'Date' in df.columns:
            try:
                dates = pd.to_datetime(df['Date'], errors='coerce').dropna()
                if not dates.empty:
                    candidates.append(dates.max())
            except Exception:
                continue
    if not candidates:
        return None
    latest_ts = max(candidates)
    return date(latest_ts.year, latest_ts.month, 1)


def prewarm_latest_month(db_manager, repo) -> Tuple[int, int, Optional[date]]:
    """Pre-warm the cache for the latest month across all active facilities.

    Returns tuple (ok_count, total_facilities, latest_month_date).
    """
    latest = _latest_month_from_repo(repo)
    facilities = db_manager.get_storage_facilities(active_only=True)
    total = len(facilities)
    if not latest or total == 0:
        return (0, total, latest)

    logger.info(f"Pre-warming cache for {total} facilities, month {latest:%Y-%m}…")
    ok = 0
    for f in facilities:
        code = f.get('facility_code')
        cap = f.get('total_capacity') or 0.0
        area = f.get('surface_area') or 0.0
        try:
            _ = repo.get_storage_data(code, latest, cap, area, db_manager=db_manager)
            ok += 1
        except Exception as e:
            logger.warning(f"Pre-warm failed for {code}: {e}")
    logger.info(f"Pre-warm complete: {ok}/{total} cached for {latest:%Y-%m}")
    return (ok, total, latest)
