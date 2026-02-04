"""
Monthly Parameters Data Model (PYDANTIC VALIDATION).

Defines the structure and validation for monthly inflow/outflow totals
per storage facility.

Data source: SQLite database (facility_monthly_parameters table)
Validation rules: Valid year/month, non-negative totals
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MonthlyParameters(BaseModel):
    """Monthly inflow/outflow totals for a facility (DATA VALIDATION MODEL).

    Represents a single monthly record tied to a facility.

    Fields:
    - facility_id: FK to storage_facilities.id (enforces data integrity)
    - year/month: Time period (month 1-12)
    - total_inflows_m3 / total_outflows_m3: Monthly totals
    - created_at/updated_at: Audit timestamps
    """

    id: Optional[int] = Field(None, description="Database primary key (auto-generated)")
    facility_id: int = Field(..., gt=0, description="Storage facility ID (FK to storage_facilities.id)")
    year: int = Field(..., ge=2000, le=2100, description="Calendar year (2000-2100)")
    month: int = Field(..., ge=1, le=12, description="Month number (1=Jan, 12=Dec)")
    total_inflows_m3: float = Field(default=0, ge=0, description="Total inflows in m³ for the month")
    total_outflows_m3: float = Field(default=0, ge=0, description="Total outflows in m³ for the month")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when record created")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when record last updated")

    class Config:
        """Pydantic configuration for JSON serialization and documentation."""
        json_schema_extra = {
            "example": {
                "facility_id": 1,
                "year": 2026,
                "month": 1,
                "total_inflows_m3": 125000.0,
                "total_outflows_m3": 118500.0
            }
        }
