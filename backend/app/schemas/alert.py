"""
Alert Schemas
==============

Pydantic schemas for alert management API operations including
alert creation, updates, querying, filtering, and response serialization.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AlertCreate(BaseModel):
    """
    Schema for creating a new security alert.
    Used by the alert engine to generate new alerts.
    """
    user_id: str = Field(description="UUID of the user who triggered the alert")
    alert_type: str = Field(
        ...,
        description="Alert category: anomaly, rule_violation, risk_threshold"
    )
    title: str = Field(
        ...,
        max_length=255,
        description="Short alert title"
    )
    description: Optional[str] = Field(default=None, description="Detailed description")
    severity: str = Field(
        ...,
        description="Severity level: low, medium, high, critical"
    )
    priority: str = Field(default="medium", description="Response priority")
    risk_score: Optional[float] = Field(
        default=None,
        description="Risk score at time of alert"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Explainable AI output"
    )
    recommended_action: Optional[str] = Field(
        default=None,
        description="Suggested remediation steps"
    )
    source: str = Field(
        description="Detection source: rule_engine, ml_engine, risk_engine"
    )
    metadata_json: Optional[Dict[str, Any]] = Field(default=None)


class AlertUpdate(BaseModel):
    """
    Schema for updating an existing alert.
    Used by SOC analysts during alert investigation.
    """
    status: Optional[str] = Field(
        default=None,
        description="New status: acknowledged, investigating, resolved, false_positive"
    )
    acknowledged_by: Optional[str] = Field(
        default=None,
        description="UUID of the analyst acknowledging the alert"
    )
    resolved_by: Optional[str] = Field(
        default=None,
        description="UUID of the user resolving the alert"
    )
    resolution_notes: Optional[str] = Field(
        default=None,
        description="Notes about the resolution"
    )
    is_false_positive: Optional[bool] = Field(
        default=None,
        description="Mark as false positive"
    )


class AlertResponse(BaseModel):
    """
    Full alert information response schema.
    Contains all alert details including explanations and resolution info.
    """
    id: str = Field(description="Alert UUID")
    user_id: str = Field(description="User UUID")
    username: Optional[str] = Field(default=None, description="Username")
    alert_type: str = Field(description="Alert category")
    title: str = Field(description="Alert title")
    description: Optional[str] = Field(default=None, description="Description")
    severity: str = Field(description="Severity level")
    priority: str = Field(description="Response priority")
    status: str = Field(description="Lifecycle status")
    risk_score: Optional[float] = Field(default=None, description="Risk score")
    explanation: Optional[str] = Field(default=None, description="AI explanation")
    recommended_action: Optional[str] = Field(default=None, description="Recommended action")
    source: str = Field(description="Detection source")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None)
    acknowledged_by: Optional[str] = Field(default=None)
    acknowledged_at: Optional[datetime] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None)
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)
    is_false_positive: bool = Field(default=False)
    created_at: datetime = Field(description="Alert generation time")
    updated_at: datetime = Field(description="Last update time")

    class Config:
        from_attributes = True


class AlertFilter(BaseModel):
    """Filter parameters for alert queries."""
    user_id: Optional[str] = Field(default=None, description="Filter by user")
    alert_type: Optional[str] = Field(default=None, description="Filter by type")
    severity: Optional[str] = Field(default=None, description="Filter by severity")
    priority: Optional[str] = Field(default=None, description="Filter by priority")
    status: Optional[str] = Field(default=None, description="Filter by status")
    source: Optional[str] = Field(default=None, description="Filter by source")
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    search: Optional[str] = Field(default=None, description="Search in title/description")


class AlertListResponse(BaseModel):
    """Paginated alert list response."""
    success: bool = Field(default=True)
    data: List[AlertResponse] = Field(default_factory=list)
    total: int = Field(description="Total alert count")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total pages")


class AlertStats(BaseModel):
    """Alert statistics for dashboard display."""
    total_alerts: int = Field(description="Total alerts in period")
    alerts_by_severity: Dict[str, int] = Field(description="Counts by severity")
    alerts_by_status: Dict[str, int] = Field(description="Counts by status")
    alerts_by_type: Dict[str, int] = Field(description="Counts by alert type")
    mean_time_to_acknowledge: Optional[float] = Field(
        default=None,
        description="Average minutes to acknowledge"
    )
    mean_time_to_resolve: Optional[float] = Field(
        default=None,
        description="Average minutes to resolve"
    )
    false_positive_rate: float = Field(description="Percentage of false positives")
