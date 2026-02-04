"""
Storage Facility Data Model (PYDANTIC VALIDATION).

Defines the structure and validation for storage facility records.
Used for type-safe data validation before saving to SQLite.

Data source: SQLite database (storage_facilities table)
Validation rules: Capacity > 0, name not empty, code unique (enforced at DB level)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StorageFacility(BaseModel):
    """Storage facility record with validation (DATA VALIDATION MODEL).
    
    Represents a single water storage facility (TSF, pond, dam, etc.) with:
    - Identification (code, name, type)
    - Physical properties (capacity, surface area)
    - Current state (volume, status)
    - Timestamps (created, updated)
    
    Why Pydantic: Enforces type safety and validation rules before database writes.
    Prevents invalid data from entering system.
    """
    
    id: Optional[int] = Field(None, description="Database primary key (auto-generated)")
    code: str = Field(..., min_length=1, max_length=50, description="Facility code (e.g., 'NDCD1', 'OLDTSF')")
    name: str = Field(..., min_length=1, max_length=255, description="Facility display name")
    facility_type: str = Field(..., description="Type: TSF, Pond, Dam, Tank, Other")
    capacity_m3: float = Field(..., gt=0, description="Total capacity in cubic meters (must be > 0)")
    surface_area_m2: Optional[float] = Field(None, ge=0, description="Surface area in square meters (for evaporation calculations)")
    current_volume_m3: float = Field(default=0, ge=0, description="Current water volume in cubic meters")
    is_lined: Optional[bool] = Field(None, description="Lined status: True=lined, False=unlined, None=not applicable (for tanks, etc.)")
    status: str = Field(default="active", description="Status: active, inactive, decommissioned")
    notes: Optional[str] = Field(None, description="Additional notes about facility")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when record created")
    updated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when record last updated")
    
    class Config:
        """Pydantic configuration for JSON serialization and documentation."""
        json_schema_extra = {
            "example": {
                "code": "NDCD1",
                "name": "North Decline Decant 1",
                "facility_type": "TSF",
                "capacity_m3": 250000,
                "surface_area_m2": 45000,
                "current_volume_m3": 180000,
                "status": "active",
                "notes": "Main TSF for northern area"
            }
        }
    
    @property
    def volume_percentage(self) -> float:
        """Calculate current volume as percentage of capacity (CONVENIENCE PROPERTY).
        
        Used in UI to show fill level (e.g., "72% full").
        Safe division: returns 0 if capacity is 0 (shouldn't happen with validation).
        
        Returns:
            Percentage 0-100 (or >100 if overfilled - data quality check)
        """
        if self.capacity_m3 <= 0:
            return 0.0
        return (self.current_volume_m3 / self.capacity_m3) * 100
    
    @property
    def is_full(self) -> bool:
        """Check if facility is at or above capacity (BUSINESS LOGIC).
        
        Used to trigger pump transfers or alerts.
        Threshold: >= 95% (allows small overfill margin for measurement error)
        
        Returns:
            True if volume >= 95% of capacity
        """
        return self.volume_percentage >= 95.0
    
    @property
    def is_empty(self) -> bool:
        """Check if facility is nearly empty (BUSINESS LOGIC).
        
        Used to trigger supply alerts.
        Threshold: <= 5% (safety margin)
        
        Returns:
            True if volume <= 5% of capacity
        """
        return self.volume_percentage <= 5.0
    
    def available_capacity_m3(self) -> float:
        """Calculate remaining capacity available for inflow (BUSINESS LOGIC).
        
        Useful for pump transfer calculations.
        
        Returns:
            Remaining capacity in m³ (may be negative if overfilled)
        
        Example:
            if facility.available_capacity_m3() > 50000:
                # Can accept more transfers
        """
        return self.capacity_m3 - self.current_volume_m3
