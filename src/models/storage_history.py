import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from typing import Optional


class StorageHistoryRecord(BaseModel):
    """Storage history record (monthly opening/closing volumes)."""

    id: Optional[int] = Field(default=None)
    facility_code: str
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    opening_volume_m3: float = Field(default=0.0, ge=0)
    closing_volume_m3: float = Field(default=0.0, ge=0)
    data_source: str = Field(default="measured")
    notes: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)

    @property
    def delta_volume_m3(self) -> float:
        """Change in storage for the month."""
        return self.closing_volume_m3 - self.opening_volume_m3
