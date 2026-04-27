from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum


class IssueType(str, Enum):
    """Issue type categories."""
    WATER = "water"
    ELECTRICITY = "electricity"
    OTHER = "other"


class IssueUrgency(str, Enum):
    """Issue urgency levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueStatus(str, Enum):
    """Issue resolution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IssueSource(str, Enum):
    """Issue source."""
    USSD = "ussd"
    ADMIN = "admin"


class IssueCreate(BaseModel):
    """Issue creation schema."""
    tenant_id: UUID
    type: IssueType
    description: Optional[str] = None
    urgency: IssueUrgency
    source: IssueSource = IssueSource.ADMIN


class IssueStatusUpdate(BaseModel):
    """Issue status update schema."""
    status: IssueStatus
    urgency: Optional[IssueUrgency] = None


class Issue(BaseModel):
    """Issue response schema."""
    id: UUID
    tenant_id: UUID
    tenant_name: Optional[str] = None  # Derived from relationship
    house_no: Optional[str] = None  # Derived from tenant
    property_id: Optional[UUID] = None  # Derived from tenant
    property_name: Optional[str] = None  # Derived from tenant
    type: IssueType
    description: Optional[str] = None
    urgency: IssueUrgency
    status: IssueStatus
    source: IssueSource
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
