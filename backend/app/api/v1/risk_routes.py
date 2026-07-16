"""
Risk Routes
=============

API endpoints for risk score management and analysis.

Endpoints:
    GET  /                    - List risk scores (paginated)
    GET  /user/{user_id}      - Get risk scores for a user
    POST /assess/{user_id}    - Trigger risk assessment
    GET  /trend/{user_id}     - Get risk score trend
    GET  /top-risk            - Get top risk users
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.connection import get_db_session
from app.models.risk_score import RiskScore
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.risk import RiskScoreResponse, RiskScoreListResponse
from app.risk_engine.engine import get_risk_engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=RiskScoreListResponse)
async def list_risk_scores(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List risk scores with filtering and pagination."""
    query = select(RiskScore)
    if risk_level:
        query = query.where(RiskScore.risk_level == risk_level)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(RiskScore.calculated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    scores = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return RiskScoreListResponse(
        data=[RiskScoreResponse(
            id=str(s.id), user_id=str(s.user_id), score=s.score,
            risk_level=s.risk_level, factors=s.factors,
            explanation=s.explanation, rule_violations=s.rule_violations,
            calculated_at=s.calculated_at,
        ) for s in scores],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.post("/assess/{user_id}")
async def assess_risk(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Trigger a real-time risk assessment for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    risk_engine = get_risk_engine()
    assessment = risk_engine.calculate_risk_score(
        user_id=user_id, ml_anomaly_score=0.0, rule_violations=[],
        activity_context={"hour": datetime.utcnow().hour, "is_weekend": datetime.utcnow().weekday() >= 5},
    )

    return {
        "user_id": user_id,
        "username": user.username,
        "score": assessment.score,
        "risk_level": assessment.risk_level,
        "explanation": assessment.explanation,
        "recommended_actions": assessment.recommended_actions,
        "factors": [{"name": f.name, "description": f.description, "risk_points": f.risk_points} for f in assessment.factors],
    }


@router.get("/trend/{user_id}")
async def get_risk_trend(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get risk score trend for a user."""
    risk_engine = get_risk_engine()
    return risk_engine.get_user_trend(user_id)


@router.get("/top-risk")
async def get_top_risk_users(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get users with the highest risk scores."""
    risk_engine = get_risk_engine()
    result = await db.execute(select(User).where(User.is_active == True).limit(100))
    users = result.scalars().all()

    user_risks = []
    for user in users:
        trend = risk_engine.get_user_trend(str(user.id))
        current_score = trend.get("current", 0)
        user_risks.append({
            "user_id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "risk_score": current_score,
            "risk_level": risk_engine._score_to_level(current_score),
            "department": user.department.name if user.department else None,
        })

    user_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    return {"top_risk_users": user_risks[:limit]}
