from pydantic import BaseModel, EmailStr
from uuid import UUID


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminUser(BaseModel):
    """Admin user response schema."""
    id: UUID
    email: str
    name: str

    model_config = {"from_attributes": True}
