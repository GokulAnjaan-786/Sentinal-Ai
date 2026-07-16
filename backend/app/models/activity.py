"""
Activity Model
===============

Defines the SQLAlchemy ORM model for user activity records in SentinelAI.

Activity monitoring is the core of the insider threat detection system.
Every action a user takes within the banking environment is logged here,
providing the raw data for behavioral analytics and anomaly detection.

Tracked Activity Types:
    - login / logout
    - database_access / database_export
    - file_download / file_upload
    - usb_insertion / usb_removal
    - password_change
    - configuration_change
    - email_send / email_receive
    - admin_command
    - privilege_escalation
    - access_denied

Database Table: activities
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Integer, Text,
    ForeignKey, Index, Float
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Activity(Base):
    """
    Activity record model for user action monitoring.

    This model captures every significant action performed by users in the
    system. The rich activity data feeds the ML-based behavioral analytics
    engine to establish baseline patterns and detect anomalies.

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to the user who performed the activity
        session_id: Foreign key to the session during which this occurred
        activity_type: Category of activity (login, file_download, etc.)
        description: Human-readable description of the activity
        ip_address: IP address of the client performing the activity
        user_agent: Browser/client user agent string
        device_id: Identifier for the device used
        location: Geographic location derived from IP
        resource_accessed: Specific resource targeted by the activity
        resource_type: Type of resource (file, database, api, etc.)
        severity: Activity severity level (info, low, medium, high, critical)
        risk_contribution: How much this activity contributed to risk score
        metadata_json: Additional structured data about the activity
        status: Outcome of the activity (success, failure, denied)
        created_at: When the activity occurred
    """
    __tablename__ = "activities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique activity record identifier"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the user who performed this activity"
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the user session"
    )
    activity_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Category of activity: login, logout, file_download, etc."
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of the activity"
    )
    ip_address = Column(
        INET,
        nullable=True,
        comment="Client IP address at time of activity"
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client user agent string"
    )
    device_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Device identifier used for this activity"
    )
    location = Column(
        String(255),
        nullable=True,
        comment="Geographic location derived from IP geolocation"
    )
    resource_accessed = Column(
        String(500),
        nullable=True,
        comment="Specific resource path or identifier targeted"
    )
    resource_type = Column(
        String(50),
        nullable=True,
        comment="Type of resource: file, database, api, system"
    )
    severity = Column(
        String(20),
        default="info",
        nullable=False,
        comment="Severity level: info, low, medium, high, critical"
    )
    risk_contribution = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Risk score points contributed by this activity"
    )
    metadata_json = Column(
        JSONB,
        nullable=True,
        comment="Additional structured metadata about the activity"
    )
    status = Column(
        String(20),
        default="success",
        nullable=False,
        comment="Activity outcome: success, failure, denied"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Timestamp when the activity occurred"
    )

    __table_args__ = (
        Index("idx_activities_user_type", "user_id", "activity_type"),
        Index("idx_activities_user_created", "user_id", "created_at"),
        Index("idx_activities_type_created", "activity_type", "created_at"),
        Index("idx_activities_severity", "severity"),
        Index("idx_activities_device", "device_id"),
    )

    # Relationships
    user = relationship("User", back_populates="activities", lazy="selectin")
    session = relationship("UserSession", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Activity(id={self.id}, type='{self.activity_type}', "
            f"user_id={self.user_id}, severity='{self.severity}')>"
        )
