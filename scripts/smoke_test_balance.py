"""Smoke test for regulator closure and inputs audit.

- Detects latest month from Meter Readings (if available)
- Runs BalanceEngine (REGULATOR mode) with Legacy services
- Prints concise summary of closure and recycled components
- Prints Inputs Audit key indicators
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import sys

# Import shim for src
sys.path.insert(0, str((Path(__file__).parent.parent / 'src').resolve()))

from utils.excel_timeseries import get_default_excel_repo
from utils.balance_engine import BalanceEngine
from utils.balance_services_legacy import LegacyBalanceServices
from utils.inputs_audit import collect_inputs_audit


def main() -> int:
    repo = get_default_excel_repo()
    latest = repo.get_latest_date()
    if latest is None:
        # Fall back to today's month end
        from calendar import monthrange
        today = date.today()
        latest = date(today.year, today.month, monthrange(today.year, today.month)[1])

    # Run engine
    legacy = LegacyBalanceServices()
    engine = BalanceEngine(
        inflows_service=legacy,
        outflows_service=legacy,
        storage_service=legacy,
        mode="REGULATOR",
    )
    result = engine.run(latest)

    # Prepare summary
    summary = {
        "month": latest.strftime("%Y-%m"),
        "fresh_in_m3": round(result.fresh_in.total, 2),
        "outflows_m3": round(result.outflows.total, 2),
        "delta_storage_m3": round(result.storage.delta, 2),
        "error_m3": round(result.error_m3, 2),
        "error_pct": round(result.error_pct, 2),
        "recycled": {k: round(v or 0.0, 2) for k, v in result.recycled.components.items()},
        "flags": result.flags.as_dict(),
    }

    audit = collect_inputs_audit(latest)

    print("=== CLOSURE SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print("\n=== INPUTS AUDIT (condensed) ===")
    condensed = {
        "legacy_path_exists": bool(audit.get("legacy_excel", {}).get("exists")),
        "matched_row_date": audit.get("legacy_excel", {}).get("matched_row_date"),
        "headers_found": {h["name"]: h["value"] for h in audit.get("legacy_excel", {}).get("headers", []) if h.get("found")},
        "extended_path_exists": bool(audit.get("extended_excel", {}).get("exists")),
        "extended_values": audit.get("extended_excel", {}).get("values", {}),
    }
    print(json.dumps(condensed, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
