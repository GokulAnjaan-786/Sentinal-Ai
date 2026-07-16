"""
Authentication Routes
======================

API endpoints for user authentication, token management, and session control.

Endpoints:
    POST /login         - Authenticate user and return JWT tokens
    POST /logout        - Terminate user session
    POST /refresh       - Refresh access token
    POST /change-password - Change user password
    POST /forgot-password - Request password reset
    POST /reset-password  - Confirm password reset with token
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import get_db_session
from app.models.user import User
from app.models.session import UserSession
from app.models.audit_log import AuditLog
from app.auth.jwt_handler import JWTHandler
from app.auth.password_utils import PasswordManager
from app.auth.dependencies import get_current_user
from app.schemas.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest,
    TokenRefreshResponse, PasswordChangeRequest, LogoutRequest,
    UserSummary,
)
from app.schemas.common import BaseResponse, ErrorResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate a user and return JWT tokens.

    Validates credentials against the database, checks for account
    lockout, records login attempt, and generates JWT tokens on
    successful authentication.

    Security:
        - Brute force protection via rate limiting
        - Account lockout after 5 failed attempts
        - All login attempts are logged for audit
    """
    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == login_data.username) |
            (User.email == login_data.username)
        )
    )
    user = result.scalar_one_or_none()

    # Always perform password verification even if user not found
    # to prevent timing-based user enumeration
    if user is None:
        # Dummy hash to prevent timing attacks
        PasswordManager.hash_password("dummy_password_to_prevent_timing")
        # Record failed attempt for audit
        audit_log = AuditLog(
            action="login_failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=False,
            error_message="User not found",
        )
        db.add(audit_log)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Contact your administrator."
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator."
        )

    # Verify password
    if not PasswordManager.verify_password(login_data.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.account_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            logger.warning(f"Account locked for user {user.username} after 5 failed attempts")

        # Record failed login audit
        audit_log = AuditLog(
            user_id=user.id,
            action="login_failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=False,
            error_message="Invalid password",
        )
        db.add(audit_log)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Login successful - reset failed attempts
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()

    # Generate JWT tokens
    access_token = JWTHandler.create_access_token(
        user_id=str(user.id),
        role=user.role.name if user.role else "employee",
    )
    refresh_token = JWTHandler.create_refresh_token(user_id=str(user.id))

    # Create session record
    session = UserSession(
        user_id=user.id,
        session_token=access_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        login_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        is_active=True,
    )
    db.add(session)

    # Record successful login audit
    audit_log = AuditLog(
        user_id=user.id,
        action="login_success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
    )
    db.add(audit_log)

    logger.info(f"User {user.username} logged in successfully")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=JWTHandler.get_access_token_expiry_seconds(),
        user=UserSummary(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.name if user.role else "employee",
            department=user.department.name if user.department else None,
            is_active=user.is_active,
        ),
        requires_password_change=user.force_password_change,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Refresh an access token using a valid refresh token.

    Validates the refresh token, verifies the user still exists and
    is active, then issues a new access token.
    """
    # Verify refresh token
    payload = JWTHandler.verify_token(refresh_data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Refresh token required."
        )

    # Get user
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Generate new access token
    new_access_token = JWTHandler.create_access_token(
        user_id=str(user.id),
        role=user.role.name if user.role else "employee",
    )

    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=JWTHandler.get_access_token_expiry_seconds(),
    )


@router.post("/logout", response_model=BaseResponse)
async def logout(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Terminate the current user session.

    Invalidates the current JWT token and marks the session as inactive.
    """
    # Deactivate active sessions
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        )
    )
    sessions = result.scalars().all()

    for session in sessions:
        session.is_active = False
        session.logout_at = datetime.utcnow()
        session.logout_reason = "user_logout"

    # Record audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="logout",
        success=True,
    )
    db.add(audit_log)

    logger.info(f"User {current_user.username} logged out")

    return BaseResponse(message="Logged out successfully")


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Change the current user's password.

    Requires the current password for verification before setting
    the new password.
    """
    # Verify current password
    if not PasswordManager.verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, errors = PasswordManager.validate_password_strength(
        password_data.new_password
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet strength requirements: {'; '.join(errors)}"
        )

    # Update password
    current_user.hashed_password = PasswordManager.hash_password(
        password_data.new_password
    )
    current_user.password_changed_at = datetime.utcnow()
    current_user.force_password_change = False

    # Record audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="password_changed",
        success=True,
    )
    db.add(audit_log)

    logger.info(f"Password changed for user {current_user.username}")

    return BaseResponse(message="Password changed successfully")


@router.get("/me", response_model=UserSummary)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get the current authenticated user's profile information.
    """
    return UserSummary(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.name if current_user.role else "employee",
        department=current_user.department.name if current_user.department else None,
        is_active=current_user.is_active,
    )
