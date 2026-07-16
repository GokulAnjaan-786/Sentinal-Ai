"""
Activity Routes
================

API endpoints for activity monitoring and logging.

Endpoints:
    GET  /           - List activities (paginated, filterable)
    POST /           - Record a new activity
    GET  /stats      - Get activity statistics
    GET  /user/{id}  - Get activities for a specific user
    POST /detect     - Process activity through detection pipeline
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db_session
from app.models.activity import Activity
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.activity import (
    ActivityCreate, ActivityResponse, ActivityListResponse, ActivityFilter
)
from app.schemas.common import BaseResponse
from app.activity_monitor.monitor import get_activity_monitor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=ActivityListResponse)
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    activity_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List activities with filtering and pagination."""
    query = select(Activity)

    if user_id:
        query = query.where(Activity.user_id == user_id)
    if activity_type:
        query = query.where(Activity.activity_type == activity_type)
    if severity:
        query = query.where(Activity.severity == severity)
    if status:
        query = query.where(Activity.status == status)
    if start_date:
        query = query.where(Activity.created_at >= start_date)
    if end_date:
        query = query.where(Activity.created_at <= end_date)
    if search:
        query = query.where(Activity.description.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Order by most recent first
    query = query.order_by(Activity.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    activities = result.scalars().all()

    activity_responses = []
    for act in activities:
        activity_responses.append(ActivityResponse(
            id=str(act.id),
            user_id=str(act.user_id),
            session_id=str(act.session_id) if act.session_id else None,
            activity_type=act.activity_type,
            description=act.description,
            ip_address=str(act.ip_address) if act.ip_address else None,
            location=act.location,
            device_id=act.device_id,
            resource_accessed=act.resource_accessed,
            resource_type=act.resource_type,
            severity=act.severity,
            risk_contribution=act.risk_contribution,
            status=act.status,
            metadata_json=act.metadata_json,
            created_at=act.created_at,
        ))

    total_pages = (total + page_size - 1) // page_size

    return ActivityListResponse(
        data=activity_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=BaseResponse)
async def record_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Record a new activity."""
    import uuid
    activity = Activity(
        user_id=activity_data.user_id,
        activity_type=activity_data.activity_type,
        description=activity_data.description,
        ip_address=activity_data.ip_address,
        user_agent=activity_data.user_agent,
        device_id=activity_data.device_id,
        location=activity_data.location,
        resource_accessed=activity_data.resource_accessed,
        resource_type=activity_data.resource_type,
        status=activity_data.status,
        metadata_json=activity_data.metadata_json,
    )
    db.add(activity)

    return BaseResponse(message="Activity recorded successfully")


@router.post("/detect")
async def detect_threats(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Process an activity through the complete threat detection pipeline.

    This endpoint:
    1. Records the activity
    2. Runs rule engine checks
    3. Runs ML anomaly detection
    4. Calculates risk score
    5. Generates alerts if needed
    6. Returns comprehensive results
    """
    monitor = get_activity_monitor()

    activity_dict = {
        "id": str(__import__("uuid").uuid4()),
        "user_id": activity_data.user_id,
        "activity_type": activity_data.activity_type,
        "description": activity_data.description,
        "ip_address": activity_data.ip_address,
        "device_id": activity_data.device_id,
        "location": activity_data.location,
        "resource_accessed": activity_data.resource_accessed,
        "resource_type": activity_data.resource_type,
        "status": activity_data.status,
        "created_at": datetime.utcnow().isoformat(),
    }

    result = monitor.process_activity(activity_dict)

    return {
        "success": True,
        "message": "Threat detection completed",
        "data": result,
    }


@router.get("/stats")
async def get_activity_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get activity statistics for the specified time period."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Total activities
    total_result = await db.execute(
        select(func.count()).where(Activity.created_at >= cutoff)
    )
    total = total_result.scalar()

    # Activities by type
    type_result = await db.execute(
        select(Activity.activity_type, func.count())
        .where(Activity.created_at >= cutoff)
        .group_by(Activity.activity_type)
    )
    by_type = dict(type_result.all())

    # Activities by severity
    sev_result = await db.execute(
        select(Activity.severity, func.count())
        .where(Activity.created_at >= cutoff)
        .group_by(Activity.severity)
    )
    by_severity = dict(sev_result.all())

    return {
        "total_activities": total,
        "activities_by_type": by_type,
        "activities_by_severity": by_severity,
        "period_days": days,
    }
