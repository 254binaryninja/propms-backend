from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from enum import Enum


class MassSMSRequest(BaseModel):
    """Mass SMS request schema."""
    property_id: Optional[UUID] = None
    message: str = Field(..., max_length=160)


class SingleSMSRequest(BaseModel):
    """Single SMS request schema."""
    tenant_id: UUID
    message: str = Field(..., max_length=160)


class SMSStatus(str, Enum):
    """SMS delivery status."""
    QUEUED = "queued"
    FAILED = "failed"


class SMSResponse(BaseModel):
    """SMS response schema."""
    recipients: int
    at_message_id: str
    status: SMSStatus
