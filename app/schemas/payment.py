from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentCreate(BaseModel):
    """Payment creation schema."""
    tenant_id: UUID
    amount: float = Field(..., gt=0)
    due_date: date


class PaymentMarkPaid(BaseModel):
    """Mark payment as paid schema."""
    paid_date: Optional[date] = None


class Payment(BaseModel):
    """Payment response schema."""
    id: UUID
    tenant_id: UUID
    tenant_name: Optional[str] = None  # Derived from relationship
    property_id: Optional[UUID] = None  # Derived from tenant
    property_name: Optional[str] = None  # Derived from tenant
    house_no: Optional[str] = None  # Derived from tenant
    amount: float
    due_date: date
    paid_date: Optional[date] = None
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}
