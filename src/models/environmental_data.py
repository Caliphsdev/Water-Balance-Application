"""
Environmental Data Model (Pydantic validation).

Stores monthly rainfall and evaporation data for water balance calculations.
Used by EnvironmentalDataService and water balance calculator.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class EnvironmentalData(BaseModel):
    """Monthly environmental data for water balance calculations.
    
    Stores rainfall and evaporation measurements that are used to calculate:
    - Rainfall volume additions to storage facilities
    - Evaporation losses from open water surfaces
    
    Business rules:
    - Data is per (year, month) combination
    - Values must be non-negative (can't have negative rainfall)
    - Extreme values validated to prevent data entry errors
    """
    
    id: Optional[int] = None
    year: int = Field(..., description="Year (e.g., 2025)")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    rainfall_mm: float = Field(..., ge=0, description="Monthly rainfall in mm")
    evaporation_mm: float = Field(..., ge=0, description="Monthly evaporation in mm")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v: int) -> int:
        """Validate year is reasonable (DATA QUALITY CHECK).
        
        Args:
            v: Year value to validate
        
        Returns:
            Validated year
        
        Raises:
            ValueError: If year is unrealistic (< 1900 or > 2100)
        
        Why: Prevents accidental typos (e.g., 202 instead of 2025)
        """
        if v < 1900 or v > 2100:
            raise ValueError(f"Year must be between 1900 and 2100, got {v}")
        return v
    
    @field_validator('rainfall_mm')
    @classmethod
    def validate_rainfall(cls, v: float) -> float:
        """Validate rainfall is within reasonable bounds (DATA INTEGRITY).
        
        Args:
            v: Rainfall value in mm
        
        Returns:
            Validated rainfall
        
        Raises:
            ValueError: If rainfall exceeds 2000mm/month (extreme outlier)
        
        Why: World record monthly rainfall is ~9000mm, but anything > 2000mm
        in mining context is likely a data entry error (missing decimal point).
        """
        if v > 2000:
            raise ValueError(
                f"Rainfall {v}mm exceeds maximum 2000mm/month. "
                "Check if decimal point is missing (e.g., 150.0 not 1500)"
            )
        return v
    
    @field_validator('evaporation_mm')
    @classmethod
    def validate_evaporation(cls, v: float) -> float:
        """Validate evaporation is within reasonable bounds (DATA INTEGRITY).
        
        Args:
            v: Evaporation value in mm
        
        Returns:
            Validated evaporation
        
        Raises:
            ValueError: If evaporation exceeds 500mm/month (extreme outlier)
        
        Why: Typical monthly evaporation is 50-300mm. Values > 500mm
        suggest data entry error or unit confusion (maybe entered in cm).
        """
        if v > 500:
            raise ValueError(
                f"Evaporation {v}mm exceeds maximum 500mm/month. "
                "Typical range is 50-300mm. Check units and decimal point."
            )
        return v
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "year": 2025,
                "month": 1,
                "rainfall_mm": 125.5,
                "evaporation_mm": 180.3
            }
        }
