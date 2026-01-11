"""
Inputs Audit Utility

Collects a concise audit of input data available for a given month from
configured Excel sources. This helps users see what's found vs missing
without changing calculation behavior.

Sources inspected:
- Legacy Excel (Meter Readings): checks for row by month and key headers
  like "Tonnes Milled" and "RWD".
- Template/Extended Excel (if configured): checks sheet presence and
  a few representative values for the month (rainfall, evaporation,
  storage rows, discharge total).

Note: This audit is read-only and does not persist overrides. It is
intended for transparency and troubleshooting. Persistence/override
handling can be added later.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Import shim for src package
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.excel_timeseries import get_default_excel_repo
from utils.excel_timeseries_extended import get_extended_excel_repo
from utils.config_manager import config


@dataclass
class HeaderCheck:
    name: str
    found: bool
    value: Optional[float]


def _audit_legacy_excel(calc_date: date) -> Dict[str, Any]:
    """
    Audit the legacy Meter Readings workbook for the target month.

    Returns a dict with file path, existence, matched row date and
    a list of header checks for key fields.
    """
    result: Dict[str, Any] = {
        "path": None,
        "exists": False,
        "matched_row_date": None,
        "headers": [],
    }

    # Resolve configured path
    try:
        legacy_path = config.get('data_sources.legacy_excel_path', 'data/New Water Balance  20250930 Oct.xlsx')
    except Exception:
        legacy_path = 'data/New Water Balance  20250930 Oct.xlsx'
    legacy_path = Path(legacy_path)
    if not legacy_path.is_absolute():
        legacy_path = Path(__file__).resolve().parents[2] / legacy_path
    result["path"] = str(legacy_path)
    result["exists"] = legacy_path.exists()

    try:
        repo = get_default_excel_repo()
        # Match on year+month (ignore day-of-month) to find the sheet row date
        matched_row_date = repo.get_matched_row_date(calc_date)
        result["matched_row_date"] = str(matched_row_date) if matched_row_date else None

        # Key headers we actively try to read in the app today
        headers_to_check = [
            # Production/ore
            "Tonnes Milled",
            # Recycled inflows
            "RWD",
            "Main decline dewatering",
            "North decline dewatering",
            "Merensky dewatering",
            # Boreholes and sources (sums)
            "Plant BH sum",
            "MDGWA sum",
            "NDGWA sum",
            "MERGWA sum",
            # Rivers
            "Groot Dwars",
            "Klein Dwars",
            # Concentrate production (PGM + Chromite)
            "PGM Concentrate Wet tons dispatched",
            "PGM Concentrate Moisture",
            "Chromite Concentrate Wet tons dispatched",
            "Chromite Concentrate Moisture",
        ]

        checks: List[HeaderCheck] = []
        
        # Ensure DF is loaded so we can inspect available columns for group sums
        try:
            _ = repo.get_matched_row_date(calc_date)
        except Exception:
            pass

        # Helper: resolve alias headers (calculator uses these)
        header_aliases: Dict[str, List[str]] = {
            # Rivers are named differently in Excel vs UI label
            "Groot Dwars": ["Groot Dwars River", "Groot Dwars"],
            "Klein Dwars": ["Klein Dwars River", "Klein Dwars"],
            # Concentrate moisture columns may have trailing spaces
            "PGM Concentrate Moisture": ["PGM Concentrate Moisture", "PGM Concentrate Moisture "],
            "Chromite Concentrate Moisture": ["Chromite Concentrate Moisture", "Chromite Concentrate Moisture "],
            # Plant borehole (observed leading space in header)
            "Plant BH sum": ["Plant Borehole Water Use", " Plant Borehole Water Use"],
        }

        # Normalized header matching (case-insensitive, trimmed, collapsed spaces)
        def _normalize(s: str) -> str:
            return " ".join((s or "").strip().split()).lower()

        def _find_actual_header(repo_obj, variants: List[str]) -> Optional[str]:
            df = getattr(repo_obj, "_df", None)
            if df is None or df.empty:
                return None
            # Build normalized map of existing columns
            norm_map = { _normalize(col): col for col in df.columns if isinstance(col, str) }
            for v in variants:
                nv = _normalize(v)
                if nv in norm_map:
                    return norm_map[nv]
            # Try contains matching for robustness (e.g., minor typos)
            for v in variants:
                nv = _normalize(v)
                for k, orig in norm_map.items():
                    if nv == k or nv in k:
                        return orig
            return None

        # Helper: compute sum across a group of numbered columns (e.g., MDGWA 1..6)
        def sum_group(prefix: str) -> tuple[bool, float]:
            df = getattr(repo, "_df", None)
            if df is None or df.empty:
                return False, 0.0
            cols = [c for c in df.columns if isinstance(c, str) and c.strip().upper().startswith(prefix.upper())]
            # Handle quirky trailing space such as "MDGWA 2 "
            cols = [c for c in cols if any(ch.isdigit() for ch in c)]
            if not cols:
                return False, 0.0
            total = 0.0
            for c in cols:
                try:
                    total += float(repo.get_monthly_value(calc_date, c) or 0.0)
                except Exception:
                    pass
            return True, total

        for h in headers_to_check:
            try:
                # Group sums
                if h == "MDGWA sum":
                    present, val = sum_group("MDGWA")
                    checks.append(HeaderCheck(name=h, found=present, value=float(val)))
                    continue
                if h == "NDGWA sum":
                    present, val = sum_group("NDGWA")
                    checks.append(HeaderCheck(name=h, found=present, value=float(val)))
                    continue
                if h == "MERGWA sum":
                    present, val = sum_group("MERGWA")
                    checks.append(HeaderCheck(name=h, found=present, value=float(val)))
                    continue
                if h == "Plant BH sum":
                    # Prefer explicit Meter Readings header first
                    aliases = header_aliases.get("Plant BH sum", [])
                    actual = _find_actual_header(repo, aliases)
                    if actual:
                        try:
                            val = float(repo.get_monthly_value(calc_date, actual))
                        except Exception:
                            val = None
                        checks.append(HeaderCheck(name=h, found=True, value=val))
                        continue
                    # Fallback: sum group across Plant BH numbered columns
                    present, val = sum_group("Plant BH")
                    checks.append(HeaderCheck(name=h, found=present, value=float(val)))
                    continue

                # Aliased headers
                if h in header_aliases:
                    aliases = header_aliases[h]
                    actual = _find_actual_header(repo, aliases)
                    present = actual is not None
                    val = None
                    if present:
                        try:
                            val = float(repo.get_monthly_value(calc_date, actual))
                        except Exception:
                            val = None
                    checks.append(HeaderCheck(name=h, found=present, value=val))
                    continue

                # Default: direct header lookup
                val = repo.get_monthly_value(calc_date, h)
                present = False
                try:
                    present = repo.has_header(h)
                except Exception:
                    present = (val is not None)
                checks.append(HeaderCheck(name=h, found=bool(present), value=float(val)))
            except Exception:
                checks.append(HeaderCheck(name=h, found=False, value=None))
        result["headers"] = [asdict(c) for c in checks]
    except Exception:
        # Repo may fail to load; leave defaults
        pass

    return result


def _audit_extended_excel(calc_date: date) -> Dict[str, Any]:
    """
    Audit the template/extended Excel workbook if configured.

    Returns a dict with file path (if discernible), sheet presence, and
    a few month-level values when available.
    """
    details: Dict[str, Any] = {
        "path": None,
        "exists": False,
        "sheets": {},
        "values": {},
    }

    # Derive configured path
    try:
        template_path = config.get('data_sources.template_excel_path', 'templates/Water_Balance_TimeSeries_Template.xlsx')
    except Exception:
        template_path = 'templates/Water_Balance_TimeSeries_Template.xlsx'
    path = Path(template_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    details["path"] = str(path)
    details["exists"] = path.exists()

    try:
        repo = get_extended_excel_repo()
        # Probe a few representative month values; functions are safe if sheet missing
        try:
            rainfall = repo.get_rainfall(calc_date)
        except Exception:
            rainfall = None
        try:
            evap = repo.get_custom_evaporation(calc_date)
        except Exception:
            evap = None
        try:
            total_discharge = float(repo.get_total_discharge(calc_date))
        except Exception:
            total_discharge = None
        # Production sheet (optional)
        try:
            conc_t = repo.get_concentrate_produced(calc_date)
        except Exception:
            conc_t = None
        try:
            conc_moist_pct = repo.get_concentrate_moisture(calc_date)
        except Exception:
            conc_moist_pct = None
        try:
            tails_moist_pct = repo.get_tailings_moisture(calc_date)
        except Exception:
            tails_moist_pct = None

        details["values"] = {
            "rainfall_mm": rainfall,
            "evaporation_mm": evap,
            "total_discharge_m3": total_discharge,
            "concentrate_t": conc_t,
            "concentrate_moisture_pct": conc_moist_pct,
            "tailings_moisture_pct": tails_moist_pct,
        }

        # Infer sheet presence by whether DataFrame attributes look populated
        # We cannot access the internal DFs directly; instead, call getters and
        # infer availability from non-None/None returns on the same month.
        details["sheets"] = {
            "Environmental": (rainfall is not None) or (evap is not None),
            "Discharge": total_discharge is not None,
            "Production": (conc_t is not None) or (conc_moist_pct is not None) or (tails_moist_pct is not None),
            # Storage and others require row-level checks; we mark unknown if file missing
        }
    except Exception:
        # Extended repo may not be configured; leave defaults
        pass

    return details


def collect_inputs_audit(calc_date: date) -> Dict[str, Any]:
    """Collect audit details for the specified month across inputs.

    Parameters:
    - calc_date: last day (or any day) of the target month

    Returns: nested dict summarizing legacy and extended Excel availability.
    """
    return {
        "month": calc_date.strftime("%Y-%m"),
        "legacy_excel": _audit_legacy_excel(calc_date),
        "extended_excel": _audit_extended_excel(calc_date),
    }
