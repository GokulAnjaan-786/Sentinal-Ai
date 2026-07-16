"""
Session Model
==============

Defines the SQLAlchemy ORM model for user sessions in SentinelAI.

Session tracking is critical for:
- Detecting concurrent session abuse
- Enforcing session timeout policies
- Identifying session hijacking attempts
- Correlating activities to specific sessions
- Managing forced logout for compromised accounts

Database Table: user_sessions
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.database.connection import Base


class UserSession(Base):
    """
    User session tracking model.

    Each login creates a new session record. Sessions track the client's
    IP address, user agent, and login/logout timestamps. This data is
    essential for detecting anomalous access patterns such as:

    - Logins from unusual locations
    - Multiple concurrent sessions from different IPs
    - Sessions active during non-working hours
    - Geographic impossibility (impossible travel detection)

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to the user who owns this session
        session_token: Unique session identifier
        ip_address: Client IP address at login time
        user_agent: Browser/client user agent string
        device_fingerprint: Derived device identifier
        login_at: Session creation timestamp
        logout_at: Session termination timestamp (NULL if active)
        expires_at: Absolute session expiration time
        is_active: Whether this session is currently active
        last_activity: Timestamp of last recorded activity in this session
        logout_reason: Why the session ended (timeout, logout, forced, etc.)
    """
    __tablename__ = "user_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique session identifier"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the session owner"
    )
    session_token = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        comment="JWT session token"
    )
    ip_address = Column(
        INET,
        nullable=True,
        comment="Client IP address at session creation"
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="Full user agent string from the client"
    )
    device_fingerprint = Column(
        String(255),
        nullable=True,
        comment="Derived device identifier for tracking"
    )
    login_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the session was created"
    )
    logout_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the session was terminated (NULL if active)"
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Absolute session expiration time"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this session is currently active"
    )
    last_activity = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp of last recorded activity in this session"
    )
    logout_reason = Column(
        String(50),
        nullable=True,
        comment="Reason for session termination: timeout, logout, forced, security"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index("idx_sessions_user_active", "user_id", "is_active"),
        Index("idx_sessions_ip", "ip_address"),
        Index("idx_sessions_last_activity", "last_activity"),
    )

    # Relationships
    user = relationship("User", back_populates="sessions", lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    @property
    def duration_minutes(self) -> float:
        """
        Calculate the session duration in minutes.

        Returns:
            Session duration in minutes, or current duration if still active.
        """
        end_time = self.logout_at or datetime.utcnow()
        delta = end_time - self.login_at
        return delta.total_seconds() / 60.0
