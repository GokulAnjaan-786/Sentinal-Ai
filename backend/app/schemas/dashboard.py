"""
Dashboard Schemas
==================

Pydantic schemas for the SOC dashboard API responses.
These schemas define the data structures for all dashboard widgets
and visualizations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DashboardSummary(BaseModel):
    """
    Main dashboard summary containing all key metrics.
    This is the primary response for the dashboard overview page.
    """
    total_users: int = Field(description="Total registered users")
    active_users: int = Field(description="Currently active users")
    active_sessions: int = Field(description="Active sessions count")
    total_alerts_today: int = Field(description="Alerts generated today")
    critical_alerts: int = Field(description="Unresolved critical alerts")
    high_alerts: int = Field(description="Unresolved high-severity alerts")
    medium_alerts: int = Field(description="Unresolved medium-severity alerts")
    low_alerts: int = Field(description="Unresolved low-severity alerts")
    total_activities_today: int = Field(description="Activities logged today")
    average_risk_score: float = Field(description="Organization-wide average risk score")
    users_at_risk: int = Field(description="Users with risk score > 50")
    users_critical: int = Field(description="Users with risk score > 75")
    threats_detected_today: int = Field(description="Threats detected today")
    mean_time_to_detect: Optional[float] = Field(
        default=None,
        description="Mean time to detect in minutes"
    )
    system_health: str = Field(description="Overall system health status")
    last_model_training: Optional[datetime] = Field(default=None)


class ThreatTimeline(BaseModel):
    """
    Threat activity timeline for the dashboard chart.
    Shows alert/threat frequency over a configurable time period.
    """
    timestamps: List[str] = Field(description="Time labels (ISO format)")
    critical_counts: List[int] = Field(description="Critical alert counts per interval")
    high_counts: List[int] = Field(description="High alert counts per interval")
    medium_counts: List[int] = Field(description="Medium alert counts per interval")
    low_counts: List[int] = Field(description="Low alert counts per interval")
    total_counts: List[int] = Field(description="Total alert counts per interval")


class TopRiskUser(BaseModel):
    """Summary of a high-risk user for the dashboard widget."""
    user_id: str = Field(description="User UUID")
    username: str = Field(description="Username")
    full_name: str = Field(description="Full display name")
    department: Optional[str] = Field(default=None, description="Department name")
    role: Optional[str] = Field(default=None, description="Role name")
    risk_score: float = Field(description="Current risk score")
    risk_level: str = Field(description="Current risk level")
    alert_count: int = Field(description="Number of active alerts")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity time")
    top_risk_factor: Optional[str] = Field(default=None, description="Primary risk factor")


class RiskDistribution(BaseModel):
    """Risk level distribution for pie/donut chart visualization."""
    low_count: int = Field(description="Users at low risk")
    medium_count: int = Field(description="Users at medium risk")
    high_count: int = Field(description="Users at high risk")
    critical_count: int = Field(description="Users at critical risk")
    total: int = Field(description="Total users")
    percentages: Dict[str, float] = Field(
        description="Percentage breakdown by risk level"
    )


class ActivityByType(BaseModel):
    """Activity type distribution for bar chart visualization."""
    activity_types: List[str] = Field(description="Activity type labels")
    counts: List[int] = Field(description="Count per activity type")
    percentages: Dict[str, float] = Field(description="Percentage per type")


class AlertHeatmap(BaseModel):
    """Alert heatmap data for the dashboard calendar/timeline view."""
    date: str = Field(description="Date (YYYY-MM-DD)")
    hour: int = Field(description="Hour of day (0-23)")
    count: int = Field(description="Number of alerts in this time slot")
    max_severity: str = Field(description="Highest severity in this time slot")


class RecentActivity(BaseModel):
    """Recent activity summary for the dashboard activity feed."""
    id: str = Field(description="Activity UUID")
    username: str = Field(description="User who performed the action")
    activity_type: str = Field(description="Type of activity")
    description: str = Field(description="Activity description")
    severity: str = Field(description="Activity severity")
    ip_address: Optional[str] = Field(default=None)
    created_at: datetime = Field(description="When it occurred")


class SecurityScorecard(BaseModel):
    """Overall security posture scorecard."""
    overall_score: int = Field(description="Overall security score (0-100)")
    access_control_score: int = Field(description="Access control score")
    monitoring_coverage: int = Field(description="Monitoring coverage percentage")
    response_readiness: int = Field(description="Incident response readiness")
    compliance_score: int = Field(description="Regulatory compliance score")
    threat_detection_rate: float = Field(description="Threat detection rate percentage")
    false_positive_rate: float = Field(description="False positive rate percentage")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Security improvement recommendations"
    )


class DepartmentRiskSummary(BaseModel):
    """Risk summary aggregated by department."""
    department_name: str = Field(description="Department name")
    department_code: str = Field(description="Department code")
    user_count: int = Field(description="Number of users in department")
    average_risk_score: float = Field(description="Average risk score")
    max_risk_score: float = Field(description="Highest risk score in department")
    active_alerts: int = Field(description="Active alerts in department")
