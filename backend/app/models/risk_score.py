"""
Risk Score Model
=================

Defines the SQLAlchemy ORM model for user risk scores in SentinelAI.

Risk scores are dynamically calculated by the Risk Engine based on:
- Behavioral anomalies detected by the ML engine
- Rule violations from the rule engine
- User context (role, department, access level)
- Historical risk trends
- Current threat landscape

Risk Score Ranges:
    0-25:   LOW     - Normal activity, no concerns
    26-50:  MEDIUM  - Minor anomalies, monitor closely
    51-75:  HIGH    - Significant risk, investigation warranted
    76-100: CRITICAL - Immediate action required

Database Table: risk_scores
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Float, Text,
    ForeignKey, Index, Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base


class RiskScore(Base):
    """
    Risk score model tracking user risk over time.

    Every time the risk engine evaluates a user, a new risk score record
    is created. This provides a complete audit trail of risk assessments
    and enables trend analysis.

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to the evaluated user
        session_id: Foreign key to the session being evaluated
        score: Numerical risk score (0-100)
        risk_level: Categorical risk level (low, medium, high, critical)
        factors: List of factors that contributed to the score
        explanation: Human-readable explanation of the score
        model_version: Version of the scoring model used
        ml_anomaly_score: Raw anomaly score from the ML engine
        rule_violations: Count of rule violations
        context_json: Additional context about the scoring environment
        calculated_at: When the score was calculated
    """
    __tablename__ = "risk_scores"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique risk score identifier"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the user being evaluated"
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to the session being evaluated"
    )
    score = Column(
        Float,
        nullable=False,
        comment="Numerical risk score from 0 (safe) to 100 (critical)"
    )
    risk_level = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Categorical risk level: low, medium, high, critical"
    )
    factors = Column(
        JSONB,
        nullable=True,
        comment="List of contributing factors with their individual weights"
    )
    explanation = Column(
        Text,
        nullable=True,
        comment="Human-readable explanation of why this score was given"
    )
    model_version = Column(
        String(50),
        nullable=True,
        comment="Version of the ML model used for this assessment"
    )
    ml_anomaly_score = Column(
        Float,
        nullable=True,
        comment="Raw anomaly score from the ML engine (-1 to 1)"
    )
    rule_violations = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of rule violations contributing to this score"
    )
    context_json = Column(
        JSONB,
        nullable=True,
        comment="Additional scoring context (time of day, location, etc.)"
    )
    calculated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When this risk score was calculated"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index("idx_risk_user_time", "user_id", "calculated_at"),
        Index("idx_risk_level_time", "risk_level", "calculated_at"),
        Index("idx_risk_user_level", "user_id", "risk_level"),
    )

    # Relationships
    user = relationship("User", back_populates="risk_scores", lazy="selectin")
    session = relationship("UserSession", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<RiskScore(id={self.id}, user_id={self.user_id}, "
            f"score={self.score}, level='{self.risk_level}')>"
        )
