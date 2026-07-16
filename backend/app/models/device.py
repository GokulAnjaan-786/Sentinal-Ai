"""
Device Model
==============

Defines the SQLAlchemy ORM model for user devices in SentinelAI.

Device tracking is essential for:
- Identifying unauthorized device usage
- Detecting new/unknown devices accessing the system
- Tracking device trust levels
- Correlating activities across devices
- Detecting device-based attack patterns

Database Table: devices
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Device(Base):
    """
    Device model for tracking user devices.

    Each device is tracked with a fingerprint, trust level, and association
    to its primary user. New devices trigger alerts when used for privileged
    access or sensitive operations.

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to the device owner
        device_name: Human-readable device name
        device_type: Type of device (desktop, laptop, server, mobile)
        device_fingerprint: Unique device identifier
        operating_system: OS name and version
        browser: Browser name and version
        trust_level: Device trust status (trusted, pending, revoked)
        is_authorized: Whether the device is authorized for access
        first_seen: When the device was first registered
        last_seen: Most recent activity from this device
        risk_score: Device-specific risk score
        metadata_json: Additional device attributes
    """
    __tablename__ = "devices"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique device identifier"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the device owner"
    )
    device_name = Column(
        String(200),
        nullable=True,
        comment="Human-readable device name"
    )
    device_type = Column(
        String(50),
        nullable=False,
        comment="Device type: desktop, laptop, server, mobile, tablet"
    )
    device_fingerprint = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique device fingerprint hash"
    )
    operating_system = Column(
        String(100),
        nullable=True,
        comment="Operating system name and version"
    )
    browser = Column(
        String(100),
        nullable=True,
        comment="Browser name and version"
    )
    trust_level = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="Trust level: trusted, pending, revoked"
    )
    is_authorized = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this device is authorized for system access"
    )
    first_seen = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="When this device was first registered"
    )
    last_seen = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Most recent activity timestamp from this device"
    )
    risk_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Device-specific risk score"
    )
    metadata_json = Column(
        JSONB,
        nullable=True,
        comment="Additional device attributes and metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index("idx_devices_user", "user_id"),
        Index("idx_devices_trust", "trust_level"),
        Index("idx_devices_type", "device_type"),
    )

    # Relationships
    user = relationship("User", back_populates="devices", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Device(id={self.id}, name='{self.device_name}', "
            f"type='{self.device_type}', trust='{self.trust_level}')>"
        )
