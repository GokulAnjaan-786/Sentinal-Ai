"""
Threat History Model
=====================

Defines the SQLAlchemy ORM model for historical threat records in SentinelAI.

Threat history tracks the complete lifecycle of security threats,
from initial detection through investigation to resolution. This data
feeds back into the ML model training pipeline and provides valuable
insights for improving detection accuracy over time.

Database Table: threat_history
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey,
    Index, Float, Integer, Boolean
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base


class ThreatHistory(Base):
    """
    Historical threat record model.

    Each record represents a confirmed or investigated threat incident,
    including all contextual information needed for forensic analysis
    and machine learning model improvement.

    Attributes:
        id: Primary key (UUID)
        alert_id: Foreign key to the originating alert
        user_id: Foreign key to the user involved
        threat_type: Category of the threat
        threat_level: Assessed threat level
        description: Detailed threat description
        indicators_of_compromise: List of IOCs related to this threat
        impact_assessment: Assessment of potential/actual impact
        response_actions: Actions taken in response
        resolved: Whether the threat has been fully addressed
        resolution_summary: Summary of the resolution
        time_to_detect: Time from occurrence to detection (seconds)
        time_to_respond: Time from detection to response (seconds)
        ml_prediction_correct: Whether the ML prediction was accurate
        analyst_confidence: Analyst confidence in the assessment
        created_at: When the threat was first recorded
        resolved_at: When the threat was fully resolved
    """
    __tablename__ = "threat_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique threat history identifier"
    )
    alert_id = Column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the originating alert"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the user associated with this threat"
    )
    threat_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Threat category: data_exfiltration, privilege_abuse, etc."
    )
    threat_level = Column(
        String(20),
        nullable=False,
        comment="Assessed threat level: low, medium, high, critical"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Detailed narrative description of the threat"
    )
    indicators_of_compromise = Column(
        JSONB,
        nullable=True,
        comment="List of IOCs: IPs, file hashes, URLs, etc."
    )
    impact_assessment = Column(
        Text,
        nullable=True,
        comment="Assessment of potential or actual business impact"
    )
    response_actions = Column(
        JSONB,
        nullable=True,
        comment="List of response actions taken"
    )
    resolved = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the threat has been fully addressed"
    )
    resolution_summary = Column(
        Text,
        nullable=True,
        comment="Summary of how the threat was resolved"
    )
    time_to_detect = Column(
        Integer,
        nullable=True,
        comment="Seconds from threat occurrence to detection"
    )
    time_to_respond = Column(
        Integer,
        nullable=True,
        comment="Seconds from detection to first response action"
    )
    ml_prediction_correct = Column(
        Boolean,
        nullable=True,
        comment="Whether the ML model's prediction matched reality"
    )
    analyst_confidence = Column(
        Float,
        nullable=True,
        comment="Analyst confidence level in the assessment (0-1)"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the threat was first recorded"
    )
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the threat was fully resolved"
    )

    __table_args__ = (
        Index("idx_threat_type_level", "threat_type", "threat_level"),
        Index("idx_threat_user_resolved", "user_id", "resolved"),
    )

    # Relationships
    alert = relationship("Alert", lazy="selectin")
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<ThreatHistory(id={self.id}, type='{self.threat_type}', "
            f"level='{self.threat_level}', resolved={self.resolved})>"
        )
