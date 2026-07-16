"""
Activity Schemas
=================

Pydantic schemas for activity monitoring API operations including
activity creation, querying, filtering, and response serialization.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ActivityCreate(BaseModel):
    """
    Schema for creating a new activity record.
    Used by the activity monitoring service to log user actions.
    """
    user_id: str = Field(description="UUID of the user performing the activity")
    session_id: Optional[str] = Field(default=None, description="UUID of the session")
    activity_type: str = Field(
        ...,
        description="Activity category: login, file_download, database_access, etc."
    )
    description: Optional[str] = Field(default=None, description="Activity description")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    device_id: Optional[str] = Field(default=None, description="Device identifier")
    location: Optional[str] = Field(default=None, description="Geographic location")
    resource_accessed: Optional[str] = Field(default=None, description="Target resource")
    resource_type: Optional[str] = Field(default=None, description="Type of resource")
    status: str = Field(default="success", description="Outcome: success, failure, denied")
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional activity metadata"
    )


class ActivityResponse(BaseModel):
    """
    Activity record response schema.
    Returns full activity details for API consumers.
    """
    id: str = Field(description="Activity UUID")
    user_id: str = Field(description="User UUID")
    username: Optional[str] = Field(default=None, description="Username")
    session_id: Optional[str] = Field(default=None, description="Session UUID")
    activity_type: str = Field(description="Activity category")
    description: Optional[str] = Field(default=None, description="Description")
    ip_address: Optional[str] = Field(default=None, description="Client IP")
    location: Optional[str] = Field(default=None, description="Geographic location")
    device_id: Optional[str] = Field(default=None, description="Device identifier")
    resource_accessed: Optional[str] = Field(default=None, description="Resource targeted")
    resource_type: Optional[str] = Field(default=None, description="Resource type")
    severity: str = Field(description="Severity level")
    risk_contribution: float = Field(description="Risk score points contributed")
    status: str = Field(description="Activity outcome")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None)
    created_at: datetime = Field(description="When the activity occurred")

    class Config:
        from_attributes = True


class ActivityFilter(BaseModel):
    """
    Filter parameters for activity queries.
    All fields are optional - only provided filters are applied.
    """
    user_id: Optional[str] = Field(default=None, description="Filter by user UUID")
    activity_type: Optional[str] = Field(
        default=None,
        description="Filter by activity type"
    )
    severity: Optional[str] = Field(default=None, description="Filter by severity")
    status: Optional[str] = Field(default=None, description="Filter by status")
    ip_address: Optional[str] = Field(default=None, description="Filter by IP address")
    device_id: Optional[str] = Field(default=None, description="Filter by device")
    start_date: Optional[datetime] = Field(
        default=None,
        description="Start of date range"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="End of date range"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search term for description matching"
    )


class ActivityListResponse(BaseModel):
    """Paginated activity list response."""
    success: bool = Field(default=True)
    data: List[ActivityResponse] = Field(default_factory=list)
    total: int = Field(description="Total activity count")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total pages")


class ActivityStats(BaseModel):
    """Activity statistics summary for dashboard display."""
    total_activities: int = Field(description="Total activities in period")
    activities_by_type: Dict[str, int] = Field(
        description="Activity counts grouped by type"
    )
    activities_by_severity: Dict[str, int] = Field(
        description="Activity counts grouped by severity"
    )
    unique_users: int = Field(description="Number of unique active users")
    peak_hour: int = Field(description="Hour with most activity")
    average_daily: float = Field(description="Average daily activity count")
