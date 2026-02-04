"""
System Constant Data Model (PYDANTIC VALIDATION).

Represents a configurable calculation constant stored in SQLite.
Used by the Settings UI and calculation services.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SystemConstant(BaseModel):
    """System constant configuration (DATA VALIDATION MODEL).

    Fields:
    - constant_key: Unique identifier used by calculation services
    - constant_value: Numeric value used in formulas
    - unit: Display unit (e.g., '%', 'm³/t')
    - category: Grouping label for UI filtering
    - description: User-facing explanation
    - editable: Flag to prevent editing critical constants
    - min_value/max_value: Optional validation bounds
    - created_at/updated_at: Audit timestamps
    """

    id: Optional[int] = Field(None, description="Database primary key (auto-generated)")
    constant_key: str = Field(..., min_length=1, description="Unique constant identifier")
    constant_value: float = Field(..., description="Numeric constant value")
    unit: Optional[str] = Field(None, description="Unit of measure")
    category: Optional[str] = Field(None, description="Grouping category for UI")
    description: Optional[str] = Field(None, description="Constant description")
    editable: int = Field(default=1, description="Editable flag (1=editable, 0=locked)")
    min_value: Optional[float] = Field(None, description="Minimum allowed value")
    max_value: Optional[float] = Field(None, description="Maximum allowed value")
    created_at: datetime = Field(default_factory=datetime.now, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Updated timestamp")

    class Config:
        """Pydantic configuration for JSON serialization and documentation."""
        json_schema_extra = {
            "example": {
                "constant_key": "tailings_moisture_pct",
                "constant_value": 20.0,
                "unit": "%",
                "category": "Optimization",
                "description": "Tailings retained moisture percent",
                "editable": 1,
                "min_value": 0.0,
                "max_value": 100.0,
            }
        }
