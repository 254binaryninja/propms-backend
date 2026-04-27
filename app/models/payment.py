import uuid
import enum
from sqlalchemy import Column, Date, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class Payment(Base):
    """Payment model representing rent payments."""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, tenant_id={self.tenant_id}, amount={self.amount}, status={self.status})>"
