from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from services.calculation.days_of_operation_service import (
    DaysOfOperationService,
    FacilityRunway,
)


class _DummyConstants:
    runway_gross_floor_pct = 0.25


class _DummyDb:
    pass


def _make_balance_result(outflows_m3: float, recycled_m3: float):
    outflows = SimpleNamespace(
        total_m3=outflows_m3,
        evaporation_m3=0.0,
        seepage_m3=0.0,
    )
    recycled = SimpleNamespace(total_m3=recycled_m3, components={})
    return SimpleNamespace(outflows=outflows, recycled=recycled)


def _make_service(monkeypatch, current_volume=50000.0, capacity=100000.0):
    from services.calculation import days_of_operation_service as dos_module

    monkeypatch.setattr(dos_module, "get_constants", lambda: _DummyConstants())
    service = DaysOfOperationService(db_manager=_DummyDb())

    monkeypatch.setattr(
        service,
        "_get_facilities_data",
        lambda: [
            {
                "code": "F1",
                "name": "Facility 1",
                "capacity_m3": capacity,
                "current_volume_m3": current_volume,
                "surface_area_m2": 1000.0,
            }
        ],
    )

    def _fake_facility_runway(facility, month, year, consumption_rates, projection_months):
        return FacilityRunway(
            facility_code=facility["code"],
            facility_name=facility["name"],
            current_volume_m3=facility["current_volume_m3"],
            capacity_m3=facility["capacity_m3"],
            net_daily_consumption_m3=0.0,
            days_remaining_conservative=120,
        )

    monkeypatch.setattr(service, "_calculate_facility_runway", _fake_facility_runway)
    return service


def test_hybrid_method_uses_net_when_net_above_floor(monkeypatch):
    service = _make_service(monkeypatch)
    result = service.calculate_runway(
        month=1,
        year=2025,
        balance_result=_make_balance_result(outflows_m3=30000.0, recycled_m3=10000.0),
    )

    assert result.runway_demand_method == "net"
    assert result.runway_daily_demand_m3 == result.net_fresh_daily_demand_m3
    assert result.combined_days_remaining is not None
    assert result.combined_days_remaining > 0


def test_hybrid_method_uses_floor_when_recycled_exceeds_outflow(monkeypatch):
    service = _make_service(monkeypatch)
    result = service.calculate_runway(
        month=1,
        year=2025,
        balance_result=_make_balance_result(outflows_m3=30000.0, recycled_m3=32000.0),
    )

    assert result.runway_demand_method == "floor"
    assert result.net_fresh_daily_demand_m3 == 0.0
    assert result.gross_floor_daily_m3 > 0.0
    assert result.runway_daily_demand_m3 == result.gross_floor_daily_m3
    assert result.combined_days_remaining is not None
    assert result.combined_days_remaining > 0


def test_zero_outflows_results_in_na_days(monkeypatch):
    service = _make_service(monkeypatch)
    result = service.calculate_runway(
        month=1,
        year=2025,
        balance_result=_make_balance_result(outflows_m3=0.0, recycled_m3=5000.0),
    )

    assert result.runway_demand_method == "zero"
    assert result.runway_daily_demand_m3 == 0.0
    assert result.combined_days_remaining is None


def test_zero_usable_storage_gives_zero_days_when_demand_positive(monkeypatch):
    service = _make_service(monkeypatch, current_volume=10000.0, capacity=100000.0)
    result = service.calculate_runway(
        month=1,
        year=2025,
        balance_result=_make_balance_result(outflows_m3=30000.0, recycled_m3=0.0),
    )

    assert result.runway_daily_demand_m3 > 0.0
    assert result.combined_days_remaining == 0


def test_month_length_changes_daily_demand(monkeypatch):
    service = _make_service(monkeypatch)
    jan_result = service.calculate_runway(
        month=1,
        year=2025,
        balance_result=_make_balance_result(outflows_m3=31000.0, recycled_m3=0.0),
    )
    feb_result = service.calculate_runway(
        month=2,
        year=2025,
        balance_result=_make_balance_result(outflows_m3=31000.0, recycled_m3=0.0),
    )

    assert jan_result.runway_demand_method == "net"
    assert feb_result.runway_demand_method == "net"
    assert jan_result.runway_daily_demand_m3 != feb_result.runway_daily_demand_m3
    assert feb_result.runway_daily_demand_m3 > jan_result.runway_daily_demand_m3
