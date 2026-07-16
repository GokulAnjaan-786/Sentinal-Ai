"""
Threat Routes
==============

API endpoints for threat history management.

Endpoints:
    GET  /         - List threat history
    GET  /{id}     - Get threat details
    POST /         - Record a new threat
    GET  /stats    - Threat statistics
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.connection import get_db_session
from app.models.threat_history import ThreatHistory
from app.models.user import User
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_threats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resolved: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List threat history records."""
    query = select(ThreatHistory).where(ThreatHistory.resolved == resolved)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    query = query.order_by(ThreatHistory.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    threats = result.scalars().all()
    return {
        "data": [
            {
                "id": str(t.id), "user_id": str(t.user_id),
                "threat_type": t.threat_type, "threat_level": t.threat_level,
                "description": t.description, "resolved": t.resolved,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in threats
        ],
        "total": total, "page": page, "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/stats")
async def get_threat_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get threat statistics."""
    total_result = await db.execute(select(func.count()).select_from(ThreatHistory))
    total = total_result.scalar()
    resolved_result = await db.execute(
        select(func.count()).where(ThreatHistory.resolved == True)
    )
    resolved = resolved_result.scalar()
    return {"total_threats": total, "resolved": resolved, "open": total - resolved}
