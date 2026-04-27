import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class IssueType(str, enum.Enum):
    """Issue type categories."""
    WATER = "water"
    ELECTRICITY = "electricity"
    OTHER = "other"


class IssueUrgency(str, enum.Enum):
    """Issue urgency levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueStatus(str, enum.Enum):
    """Issue resolution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IssueSource(str, enum.Enum):
    """Issue source."""
    USSD = "ussd"
    ADMIN = "admin"


class Issue(Base):
    """Issue model representing maintenance issues."""
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    type = Column(Enum(IssueType), nullable=False)
    description = Column(Text, nullable=True)
    urgency = Column(Enum(IssueUrgency), nullable=False)
    status = Column(Enum(IssueStatus), nullable=False, default=IssueStatus.PENDING)
    source = Column(Enum(IssueSource), nullable=False, default=IssueSource.ADMIN)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="issues")

    def __repr__(self):
        return f"<Issue(id={self.id}, type={self.type}, urgency={self.urgency}, status={self.status})>"
