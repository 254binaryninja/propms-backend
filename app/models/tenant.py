import uuid
import enum
from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class TenantStatus(str, enum.Enum):
    """Tenant lifecycle status."""
    ACTIVE = "active"
    NOTICE_GIVEN = "notice_given"
    VACATED = "vacated"


class Tenant(Base):
    """Tenant model representing renters."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, index=True)  # E.164 format
    house_no = Column(String, nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    rent_amount = Column(Numeric(10, 2), nullable=False)
    lease_start_date = Column(Date, nullable=False)
    status = Column(Enum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE)
    vacated_at = Column(Date, nullable=True)
    ussd_pin = Column(String, nullable=False)  # Hashed 4-digit PIN
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    property = relationship("Property", back_populates="tenants")
    payments = relationship("Payment", back_populates="tenant", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, phone={self.phone}, house_no={self.house_no})>"
