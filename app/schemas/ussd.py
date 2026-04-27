from pydantic import BaseModel, Field
from typing import Optional


class USSDRequest(BaseModel):
    """USSD request from Africa's Talking."""
    sessionId: str
    serviceCode: str
    phoneNumber: str = Field(..., pattern=r'^\+254\d{9}$')
    text: str
    networkCode: Optional[str] = None

    model_config = {"populate_by_name": True}
