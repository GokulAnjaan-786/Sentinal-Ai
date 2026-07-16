"""
User Model
===========

Defines the SQLAlchemy ORM model for system users in SentinelAI.

The User model is the central entity in the system, representing all types
of users including employees, administrators, security analysts, contractors,
and vendors. Each user is associated with a role for RBAC, a department
for organizational grouping, and has their own activity history and risk profile.

Security Features:
    - Password is stored as a bcrypt hash (never plaintext)
    - Failed login attempts are tracked for brute force detection
    - Account lockout after configurable failed attempts
    - Session tracking for concurrent session management

Database Table: users
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, ForeignKey, Integer,
    Text, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base


class User(Base):
    """
    User model representing all system users.

    This model stores user credentials, profile information, security
    settings, and status flags. Passwords are always stored as bcrypt
    hashes - the application never stores plaintext passwords.

    Attributes:
        id: Primary key (UUID) used throughout the system
        username: Unique login identifier
        email: Unique email address for notifications and password recovery
        hashed_password: bcrypt-hashed password (never store plaintext)
        full_name: User's display name
        role_id: Foreign key to the assigned role (RBAC)
        department_id: Foreign key to the organizational department
        employee_id: Bank employee identifier number
        is_active: Whether the account is currently active
        is_superuser: Whether the user has full system access
        last_login: Timestamp of the most recent successful login
        failed_login_attempts: Counter for consecutive failed logins
        account_locked: Whether the account is locked due to failed attempts
        locked_until: Timestamp when the lockout expires
        password_changed_at: When the password was last changed
        force_password_change: Whether the user must change password on next login
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
    """
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique user identifier"
    )
    username = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique login username"
    )
    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique email address"
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="bcrypt-hashed password (NEVER store plaintext)"
    )
    full_name = Column(
        String(200),
        nullable=False,
        comment="User's full display name"
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the assigned role"
    )
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the organizational department"
    )
    employee_id = Column(
        String(50),
        nullable=True,
        unique=True,
        comment="Bank employee identification number"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account is currently active"
    )
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Superuser flag - bypasses all permission checks"
    )

    # Security tracking fields
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the most recent successful login"
    )
    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of consecutive failed login attempts"
    )
    account_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the account is locked due to security violations"
    )
    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the account lockout expires"
    )
    password_changed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the password was last changed"
    )
    force_password_change = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Force password change on next login"
    )

    # Password reset
    reset_token = Column(
        String(255),
        nullable=True,
        comment="Token for password reset workflow"
    )
    reset_token_expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration timestamp for the reset token"
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last modification timestamp"
    )

    # Database indexes for common query patterns
    __table_args__ = (
        Index("idx_users_active_role", "is_active", "role_id"),
        Index("idx_users_department", "department_id"),
        Index("idx_users_last_login", "last_login"),
        Index("idx_users_account_status", "is_active", "account_locked"),
    )

    # Relationships
    role = relationship("Role", back_populates="users", lazy="selectin")
    department = relationship("Department", back_populates="users", lazy="selectin")
    sessions = relationship(
        "UserSession",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    activities = relationship(
        "Activity",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    alerts = relationship(
        "Alert",
        back_populates="user",
        foreign_keys="Alert.user_id",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    risk_scores = relationship(
        "RiskScore",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    devices = relationship(
        "Device",
        back_populates="user",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.name if self.role else None}')>"

    @property
    def is_locked(self) -> bool:
        """
        Check if the account is currently locked.

        An account is considered locked if the account_locked flag is True
        and the lockout period has not yet expired.

        Returns:
            True if the account is locked, False otherwise.
        """
        if not self.account_locked:
            return False
        if self.locked_until and self.locked_until < datetime.utcnow():
            return False  # Lockout has expired
        return True

    @property
    def risk_level(self) -> str:
        """
        Get the current risk level for this user based on their latest risk score.

        Returns:
            String risk level: 'low', 'medium', 'high', or 'critical'
        """
        if self.risk_scores:
            latest = sorted(self.risk_scores, key=lambda x: x.created_at, reverse=True)[0]
            return latest.risk_level
        return "low"
