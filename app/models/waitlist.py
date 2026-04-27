import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class WaitlistSource(str, enum.Enum):
    """Waitlist entry source."""
    USSD = "ussd"
    ADMIN = "admin"


class WaitlistEntry(Base):
    """WaitlistEntry model representing prospect queue."""
    __tablename__ = "waitlist_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    source = Column(Enum(WaitlistSource), nullable=False, default=WaitlistSource.ADMIN)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    property = relationship("Property", back_populates="waitlist_entries")

    def __repr__(self):
        return f"<WaitlistEntry(id={self.id}, name={self.name}, phone={self.phone})>"
