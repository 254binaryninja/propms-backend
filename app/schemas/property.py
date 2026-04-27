from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class PropertyCreate(BaseModel):
    """Property creation schema."""
    name: str
    total_units: int = Field(..., ge=1)


class PropertyUpdate(BaseModel):
    """Property update schema."""
    name: Optional[str] = None
    total_units: Optional[int] = Field(None, ge=1)


class Property(BaseModel):
    """Property response schema with derived fields."""
    id: UUID
    name: str
    total_units: int
    occupied_units: int
    vacant_units: int
    occupancy_rate: float
    monthly_rent_collected: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PropertySummary(BaseModel):
    """Property summary for dashboard."""
    id: UUID
    name: str
    total_units: int
    occupied_units: int
    vacant_units: int
    occupancy_rate: float

    model_config = {"from_attributes": True}
