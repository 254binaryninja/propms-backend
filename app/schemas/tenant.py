from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


class TenantStatus(str, Enum):
    """Tenant lifecycle status."""
    ACTIVE = "active"
    NOTICE_GIVEN = "notice_given"
    VACATED = "vacated"


class TenantCreate(BaseModel):
    """Tenant creation schema."""
    name: str
    phone: str = Field(..., pattern=r'^\+254\d{9}$')  # E.164 format for Kenya
    house_no: str
    property_id: UUID
    rent_amount: float = Field(..., gt=0)
    lease_start_date: date


class TenantUpdate(BaseModel):
    """Tenant update schema."""
    name: Optional[str] = None
    phone: Optional[str] = Field(None, pattern=r'^\+254\d{9}$')
    house_no: Optional[str] = None
    rent_amount: Optional[float] = Field(None, gt=0)
    status: Optional[TenantStatus] = None


class Tenant(BaseModel):
    """Tenant response schema."""
    id: UUID
    name: str
    phone: str
    house_no: str
    property_id: UUID
    property_name: Optional[str] = None  # Derived from relationship
    rent_amount: float
    lease_start_date: date
    status: TenantStatus
    vacated_at: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantDetail(Tenant):
    """Tenant detail with related data."""
    recent_payments: List["Payment"] = []
    open_issues: List["Issue"] = []


class TenantVacate(BaseModel):
    """Tenant vacate request schema."""
    vacated_at: Optional[date] = None
    note: Optional[str] = None


# Forward references for nested models
from app.schemas.payment import Payment  # noqa: E402
from app.schemas.issue import Issue  # noqa: E402

TenantDetail.model_rebuild()
