import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Property(Base):
    """Property model representing rental properties."""
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    total_units = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenants = relationship("Tenant", back_populates="property", cascade="all, delete-orphan")
    waitlist_entries = relationship("WaitlistEntry", back_populates="property", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Property(id={self.id}, name={self.name}, total_units={self.total_units})>"
