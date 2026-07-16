"""
Department Model
=================

Defines the SQLAlchemy ORM model for organizational departments within the bank.

Departments are used to:
- Organize users by business unit (e.g., IT, Security, Finance, HR)
- Apply department-level access policies
- Generate department-specific threat reports
- Correlate insider threat patterns across organizational boundaries

Database Table: departments
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Department(Base):
    """
    Department model representing organizational units within the bank.

    Attributes:
        id: Primary key (UUID)
        name: Unique department name
        code: Short department code for reports
        description: Detailed department description
        is_active: Whether the department is currently active
        created_at: Timestamp when the department was created
        updated_at: Timestamp of last modification
    """
    __tablename__ = "departments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique department identifier"
    )
    name = Column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
        comment="Full department name"
    )
    code = Column(
        String(20),
        nullable=False,
        unique=True,
        comment="Short department code (e.g., IT, SEC, FIN)"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the department"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this department is currently active"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when this department record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp of last update to this record"
    )

    # Relationships
    # One department can have many users
    users = relationship("User", back_populates="department", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"
