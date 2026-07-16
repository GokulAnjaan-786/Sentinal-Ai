"""
Risk Score Schemas
===================

Pydantic schemas for risk score API operations including
risk assessment queries, risk history, and risk analysis responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RiskScoreResponse(BaseModel):
    """
    Risk score response schema.
    Returns the risk assessment details for a user.
    """
    id: str = Field(description="Risk score UUID")
    user_id: str = Field(description="User UUID")
    username: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    score: float = Field(description="Numerical risk score (0-100)")
    risk_level: str = Field(description="Categorical risk level")
    factors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Contributing risk factors"
    )
    explanation: Optional[str] = Field(default=None, description="Human-readable explanation")
    model_version: Optional[str] = Field(default=None)
    ml_anomaly_score: Optional[float] = Field(default=None)
    rule_violations: int = Field(default=0)
    context_json: Optional[Dict[str, Any]] = Field(default=None)
    calculated_at: datetime = Field(description="Assessment timestamp")

    class Config:
        from_attributes = True


class RiskScoreFilter(BaseModel):
    """Filter parameters for risk score queries."""
    user_id: Optional[str] = Field(default=None)
    risk_level: Optional[str] = Field(default=None, description="Filter by risk level")
    min_score: Optional[float] = Field(default=None, description="Minimum risk score")
    max_score: Optional[float] = Field(default=None, description="Maximum risk score")
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)


class RiskScoreListResponse(BaseModel):
    """Paginated risk score list response."""
    success: bool = Field(default=True)
    data: List[RiskScoreResponse] = Field(default_factory=list)
    total: int = Field(description="Total risk score records")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total pages")


class RiskAssessment(BaseModel):
    """
    Real-time risk assessment request and response.
    Used to trigger and return an immediate risk evaluation.
    """
    user_id: str = Field(description="User to assess")
    score: float = Field(description="Calculated risk score (0-100)")
    risk_level: str = Field(description="Categorical risk level")
    contributing_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of factors that contributed to the score"
    )
    explanation: str = Field(description="Human-readable explanation")
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended response actions"
    )
    ml_anomaly_score: Optional[float] = Field(default=None)
    rule_violations_count: int = Field(default=0)
    assessment_timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class RiskTrend(BaseModel):
    """Risk trend data for chart visualization."""
    timestamps: List[datetime] = Field(description="Time points")
    scores: List[float] = Field(description="Risk scores at each time point")
    levels: List[str] = Field(description="Risk levels at each time point")


class UserRiskProfile(BaseModel):
    """Complete risk profile for a user."""
    user_id: str = Field(description="User UUID")
    username: str = Field(description="Username")
    current_score: float = Field(description="Current risk score")
    current_level: str = Field(description="Current risk level")
    average_score_7d: float = Field(description="7-day average risk score")
    average_score_30d: float = Field(description="30-day average risk score")
    peak_score_30d: float = Field(description="30-day peak risk score")
    score_trend: str = Field(description="Score trend: increasing, stable, decreasing")
    total_alerts: int = Field(description="Total alerts for this user")
    active_alerts: int = Field(description="Currently active alerts")
    risk_trend: Optional[RiskTrend] = Field(default=None)
    top_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most common risk contributing factors"
    )
