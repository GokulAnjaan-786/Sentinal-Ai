"""
Alert Routes
=============

API endpoints for security alert management.

Endpoints:
    GET  /           - List alerts (paginated, filterable)
    GET  /{alert_id} - Get alert details
    PUT  /{alert_id} - Update alert status
    GET  /stats      - Get alert statistics
    POST /{alert_id}/acknowledge - Acknowledge an alert
    POST /{alert_id}/resolve - Resolve an alert
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db_session
from app.models.alert import Alert
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.alert import (
    AlertCreate, AlertUpdate, AlertResponse, AlertListResponse
)
from app.schemas.common import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List security alerts with filtering and pagination."""
    query = select(Alert)

    if user_id:
        query = query.where(Alert.user_id == user_id)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if source:
        query = query.where(Alert.source == source)
    if start_date:
        query = query.where(Alert.created_at >= start_date)
    if end_date:
        query = query.where(Alert.created_at <= end_date)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Order by most recent first
    query = query.order_by(Alert.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    alerts = result.scalars().all()

    alert_responses = []
    for alert in alerts:
        alert_responses.append(AlertResponse(
            id=str(alert.id),
            user_id=str(alert.user_id),
            alert_type=alert.alert_type,
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            priority=alert.priority,
            status=alert.status,
            risk_score=alert.risk_score,
            explanation=alert.explanation,
            recommended_action=alert.recommended_action,
            source=alert.source,
            metadata_json=alert.metadata_json,
            acknowledged_by=str(alert.acknowledged_by) if alert.acknowledged_by else None,
            acknowledged_at=alert.acknowledged_at,
            resolved_by=str(alert.resolved_by) if alert.resolved_by else None,
            resolved_at=alert.resolved_at,
            resolution_notes=alert.resolution_notes,
            is_false_positive=alert.is_false_positive,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        ))

    total_pages = (total + page_size - 1) // page_size

    return AlertListResponse(
        data=alert_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get alert statistics for the specified time period."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Total alerts
    total_result = await db.execute(
        select(func.count()).where(Alert.created_at >= cutoff)
    )
    total = total_result.scalar()

    # By severity
    sev_result = await db.execute(
        select(Alert.severity, func.count())
        .where(Alert.created_at >= cutoff)
        .group_by(Alert.severity)
    )
    by_severity = dict(sev_result.all())

    # By status
    status_result = await db.execute(
        select(Alert.status, func.count())
        .where(Alert.created_at >= cutoff)
        .group_by(Alert.status)
    )
    by_status = dict(status_result.all())

    # By type
    type_result = await db.execute(
        select(Alert.alert_type, func.count())
        .where(Alert.created_at >= cutoff)
        .group_by(Alert.alert_type)
    )
    by_type = dict(type_result.all())

    return {
        "total_alerts": total,
        "alerts_by_severity": by_severity,
        "alerts_by_status": by_status,
        "alerts_by_type": by_type,
        "period_days": days,
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get detailed alert information."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse(
        id=str(alert.id),
        user_id=str(alert.user_id),
        alert_type=alert.alert_type,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        priority=alert.priority,
        status=alert.status,
        risk_score=alert.risk_score,
        explanation=alert.explanation,
        recommended_action=alert.recommended_action,
        source=alert.source,
        metadata_json=alert.metadata_json,
        acknowledged_by=str(alert.acknowledged_by) if alert.acknowledged_by else None,
        acknowledged_at=alert.acknowledged_at,
        resolved_by=str(alert.resolved_by) if alert.resolved_by else None,
        resolved_at=alert.resolved_at,
        resolution_notes=alert.resolution_notes,
        is_false_positive=alert.is_false_positive,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.post("/{alert_id}/acknowledge", response_model=BaseResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Acknowledge a security alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()

    return BaseResponse(message="Alert acknowledged")


@router.post("/{alert_id}/resolve", response_model=BaseResponse)
async def resolve_alert(
    alert_id: str,
    resolution_notes: Optional[str] = Query(None),
    is_false_positive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Resolve a security alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "resolved" if not is_false_positive else "false_positive"
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolution_notes
    alert.is_false_positive = is_false_positive

    return BaseResponse(
        message="Alert resolved" if not is_false_positive else "Alert marked as false positive"
    )
