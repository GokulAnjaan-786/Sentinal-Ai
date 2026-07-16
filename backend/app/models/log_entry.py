"""
Log Entry Model
================

Defines the SQLAlchemy ORM model for structured log entries in SentinelAI.

Log entries provide a queryable, structured log store that complements
the standard file-based logging. While file logs are used for debugging
and operational monitoring, log entries in the database are used for:

- Real-time log search and filtering in the SOC dashboard
- Log correlation across users and time periods
- Long-term log retention for compliance
- Log-based threat detection patterns

Database Table: log_entries
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from app.database.connection import Base


class LogEntry(Base):
    """
    Structured log entry model for database-stored logs.

    Attributes:
        id: Primary key (UUID)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger: Logger name that generated this entry
        message: Log message text
        source: Component that generated the log
        user_id: Foreign key to the associated user (if any)
        ip_address: Client IP address (if applicable)
        module: Application module name
        function: Function name that generated the log
        line_number: Source code line number
        exception_info: Exception traceback if this is an error log
        metadata_json: Additional structured log data
        created_at: When the log entry was created
    """
    __tablename__ = "log_entries"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique log entry identifier"
    )
    level = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    logger = Column(
        String(200),
        nullable=False,
        comment="Logger name that generated this entry"
    )
    message = Column(
        Text,
        nullable=False,
        comment="Log message text"
    )
    source = Column(
        String(100),
        nullable=True,
        comment="Component that generated the log (auth, ml_engine, etc.)"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the associated user"
    )
    ip_address = Column(
        INET,
        nullable=True,
        comment="Client IP address"
    )
    module = Column(
        String(100),
        nullable=True,
        comment="Application module name"
    )
    function = Column(
        String(200),
        nullable=True,
        comment="Function name that generated the log"
    )
    line_number = Column(
        String(20),
        nullable=True,
        comment="Source code line number"
    )
    exception_info = Column(
        Text,
        nullable=True,
        comment="Exception traceback for error logs"
    )
    metadata_json = Column(
        JSONB,
        nullable=True,
        comment="Additional structured log data"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the log entry was created"
    )

    __table_args__ = (
        Index("idx_logs_level_time", "level", "created_at"),
        Index("idx_logs_source_time", "source", "created_at"),
        Index("idx_logs_user_time", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<LogEntry(id={self.id}, level='{self.level}', "
            f"source='{self.source}', message='{self.message[:50]}')>"
        )
