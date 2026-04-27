from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from enum import Enum


class WaitlistSource(str, Enum):
    """Waitlist entry source."""
    USSD = "ussd"
    ADMIN = "admin"


class WaitlistCreate(BaseModel):
    """Waitlist creation schema."""
    name: str
    phone: str = Field(..., pattern=r'^\+254\d{9}$')
    property_id: UUID
    source: WaitlistSource = WaitlistSource.ADMIN


class WaitlistEntry(BaseModel):
    """Waitlist entry response schema."""
    id: UUID
    name: str
    phone: str
    property_id: UUID
    property_name: Optional[str] = None  # Derived from relationship
    position: int  # Calculated via SQL window function
    source: WaitlistSource
    created_at: datetime

    model_config = {"from_attributes": True}


class WaitlistPromote(BaseModel):
    """Promote waitlist entry to tenant schema."""
    house_no: str
    rent_amount: float = Field(..., gt=0)
    lease_start_date: date
