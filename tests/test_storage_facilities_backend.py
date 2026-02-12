"""Backend integration smoke test for storage facilities.

This test verifies that core backend layers can initialize and that
creating/retrieving a facility works without import-time side effects.
"""

from __future__ import annotations

import uuid

from database.schema import DatabaseSchema
from database.db_manager import DatabaseManager
from services.storage_facility_service import StorageFacilityService


def test_storage_facilities_backend_smoke() -> None:
    """Initialize backend stack and round-trip a test facility."""
    schema = DatabaseSchema()
    schema.create_database()

    db = DatabaseManager()
    assert db.table_exists("storage_facilities")

    service = StorageFacilityService()
    summary = service.get_summary()
    assert "total_count" in summary

    code = f"TST{uuid.uuid4().hex[:6].upper()}"
    created = service.add_facility(
        code=code,
        name="Pytest Integration Facility",
        facility_type="TSF",
        capacity_m3=100000,
        surface_area_m2=5000,
        current_volume_m3=50000,
    )
    assert created.code == code
    assert created.status == "active"

    fetched = service.get_facility(code)
    assert fetched is not None
    assert fetched.code == code
