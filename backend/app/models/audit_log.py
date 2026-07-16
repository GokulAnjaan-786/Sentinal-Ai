"""
Audit Log Model
================

Defines the SQLAlchemy ORM model for audit trail records in SentinelAI.

Audit logs are immutable records of all significant actions within the system.
They serve as:
- Compliance evidence (PCI-DSS, SOX, GDPR)
- Forensic investigation data
- Non-repudiation proof
- System integrity verification

Audit logs are append-only - they can never be modified or deleted through
normal application operations.

Database Table: audit_logs
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from app.database.connection import Base


class AuditLog(Base):
    """
    Immutable audit log record.

    Captures who did what, when, from where, and with what result.
    These records are the foundation of regulatory compliance and
    forensic investigation capabilities.

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to the user who performed the action
        action: The specific action performed
        resource_type: Type of resource affected
        resource_id: Identifier of the affected resource
        old_value: Previous value before the change (for updates)
        new_value: New value after the change (for creates/updates)
        ip_address: Client IP address
        user_agent: Client user agent string
        success: Whether the action completed successfully
        error_message: Error details if the action failed
        metadata_json: Additional audit context
        created_at: When the action occurred
    """
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique audit log identifier"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the user who performed the action"
    )
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Specific action: login, create_user, export_data, etc."
    )
    resource_type = Column(
        String(50),
        nullable=True,
        comment="Type of affected resource: user, alert, config, etc."
    )
    resource_id = Column(
        String(255),
        nullable=True,
        comment="Identifier of the specific resource affected"
    )
    old_value = Column(
        JSONB,
        nullable=True,
        comment="Previous state before the change (for audit trail)"
    )
    new_value = Column(
        JSONB,
        nullable=True,
        comment="New state after the change"
    )
    ip_address = Column(
        INET,
        nullable=True,
        comment="Client IP address at time of action"
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client user agent string"
    )
    success = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the action completed successfully"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error details if the action failed"
    )
    metadata_json = Column(
        JSONB,
        nullable=True,
        comment="Additional structured audit context"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the audited action occurred"
    )

    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_time_action", "created_at", "action"),
    )

    # Relationships
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"resource='{self.resource_type}', success={self.success})>"
        )
