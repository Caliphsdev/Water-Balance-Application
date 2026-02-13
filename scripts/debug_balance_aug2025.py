import sys
import json
from pathlib import Path

# Ensure project src is on sys.path so imports like `services.*` resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from services.calculation.balance_service import get_balance_service

svc = get_balance_service()
res = svc.calculate_for_date(8, 2025, force_recalculate=True)

out = {
    "period": res.period.period_label,
    "inflows_m3": res.inflows.total_m3,
    "outflows_m3": res.outflows.total_m3,
    "storage_opening_m3": res.storage.opening_m3,
    "storage_closing_m3": res.storage.closing_m3,
    "storage_delta_m3": res.storage.delta_m3,
    "balance_error_m3": res.balance_error_m3,
    "error_pct": res.error_pct,
    "inflow_components": res.inflows.components,
    "outflow_components": res.outflows.components,
    "storage_facility_breakdown_count": len(res.storage.facility_breakdown) if res.storage.facility_breakdown else 0,
    "quality_flags": res.quality_flags.as_dict(),
}
print(json.dumps(out, default=str, indent=2))
