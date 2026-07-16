"""
User Management Routes
=======================

API endpoints for user administration and management.

Endpoints:
    GET  /            - List all users (paginated)
    GET  /{user_id}   - Get user details
    POST /            - Create new user (admin only)
    PUT  /{user_id}   - Update user (admin only)
    DELETE /{user_id} - Deactivate user (admin only)
    GET  /risk-profile/{user_id} - Get user risk profile
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db_session
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.auth.dependencies import get_current_user, require_role
from app.auth.password_utils import PasswordManager
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserSummary, UserListResponse
)
from app.schemas.common import BaseResponse
from app.risk_engine.engine import get_risk_engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List all users with filtering and pagination."""
    query = select(User)

    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    risk_engine = get_risk_engine()
    user_summaries = []
    for user in users:
        risk = risk_engine.get_user_trend(str(user.id))
        user_summaries.append(UserSummary(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role_name=user.role.name if user.role else None,
            department_name=user.department.name if user.department else None,
            is_active=user.is_active,
            risk_level=risk.get("trend", "low"),
            last_login=user.last_login,
        ))

    total_pages = (total + page_size - 1) // page_size

    return UserListResponse(
        data=user_summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get detailed user information."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    risk_engine = get_risk_engine()
    risk = risk_engine.get_user_trend(user_id)

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role_id=str(user.role_id) if user.role_id else None,
        role_name=user.role.name if user.role else None,
        department_id=str(user.department_id) if user.department_id else None,
        department_name=user.department.name if user.department else None,
        employee_id=user.employee_id,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts,
        account_locked=user.account_locked,
        risk_level=risk.get("trend", "low"),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/", response_model=BaseResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role("super_admin", "admin")),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new user account (admin only)."""
    # Check for existing username
    existing = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check for existing email
    existing = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=PasswordManager.hash_password(user_data.password),
        full_name=user_data.full_name,
        role_id=user_data.role_id,
        department_id=user_data.department_id,
        employee_id=user_data.employee_id,
    )
    db.add(new_user)

    logger.info(f"New user created: {user_data.username} by {current_user.username}")

    return BaseResponse(message=f"User {user_data.username} created successfully")


@router.put("/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_role("super_admin", "admin")),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an existing user account (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)

    logger.info(f"User {user_id} updated by {current_user.username}")

    return BaseResponse(message="User updated successfully")


@router.delete("/{user_id}", response_model=BaseResponse)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db_session),
):
    """Deactivate a user account (super admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot deactivate super admin")

    user.is_active = False
    logger.warning(f"User {user.username} deactivated by {current_user.username}")

    return BaseResponse(message=f"User {user.username} deactivated")


@router.get("/risk-profile/{user_id}")
async def get_user_risk_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the risk profile for a specific user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    risk_engine = get_risk_engine()
    trend = risk_engine.get_user_trend(user_id)

    return {
        "user_id": user_id,
        "username": user.username,
        "full_name": user.full_name,
        "current_risk_level": trend.get("trend", "unknown"),
        "risk_history": trend,
    }
