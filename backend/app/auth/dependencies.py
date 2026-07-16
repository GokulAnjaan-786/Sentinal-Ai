"""
Authentication Dependencies
=============================

FastAPI dependency functions for authentication and authorization.
These are used with the Depends() mechanism to protect route handlers.

Usage in routes:
    @router.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        return {"user_id": user.id}

    @router.get("/admin-only")
    async def admin_route(user = Depends(require_role("super_admin"))):
        return {"message": "Admin access granted"}
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import JWTHandler
from app.database.connection import get_db_session
from app.models.user import User

logger = logging.getLogger(__name__)

"""
HTTP Bearer security scheme.
This extracts the JWT token from the Authorization header.
The auto_error flag controls whether missing tokens cause errors.
"""
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get the currently authenticated user from the JWT token.

    This is the primary authentication dependency. It:
    1. Extracts the JWT token from the Authorization header
    2. Validates the token signature and expiration
    3. Looks up the user in the database
    4. Verifies the user is active and not locked

    Args:
        credentials: Bearer token from Authorization header.
        db: Database session for user lookup.

    Returns:
        The authenticated User model instance.

    Raises:
        HTTPException 401: If token is missing or invalid.
        HTTPException 403: If user account is locked or inactive.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verify the JWT token
    payload = JWTHandler.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify this is an access token (not a refresh token)
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID and look up the user
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    # Query the user from the database
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Token may be revoked.",
        )

    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked due to too many failed login attempts.",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Optional authentication dependency.

    Same as get_current_user but returns None instead of raising
    an exception when no token is provided. Useful for routes that
    behave differently for authenticated vs anonymous users.

    Args:
        credentials: Optional Bearer token.
        db: Database session.

    Returns:
        User instance if authenticated, None otherwise.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    """
    Create a dependency that requires specific role(s).

    This factory function creates a dependency that checks if the
    authenticated user has one of the specified roles. Use it to
    restrict access to role-specific endpoints.

    Args:
        *allowed_roles: One or more role names that are allowed.

    Returns:
        FastAPI dependency function.

    Usage:
        @router.get("/security-dashboard")
        async def security_dashboard(
            user = Depends(require_role("security_analyst", "super_admin"))
        ):
            ...
    """
    async def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        # Superusers bypass role checks
        if user.is_superuser:
            return user

        # Check if user's role is in the allowed list
        if user.role and user.role.name in allowed_roles:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Required role: "
                f"{' or '.join(allowed_roles)}. "
                f"Your role: {user.role.name if user.role else 'None'}."
            ),
        )

    return role_checker


def require_permission(*required_permissions: str):
    """
    Create a dependency that requires specific permission(s).

    This factory function creates a dependency that checks if the
    authenticated user's role includes all of the specified permissions.
    This provides finer-grained access control than role checking alone.

    Args:
        *required_permissions: Permission names that are all required.

    Returns:
        FastAPI dependency function.

    Usage:
        @router.post("/users")
        async def create_user(
            user = Depends(require_permission("users.create", "users.manage"))
        ):
            ...
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        # Superusers bypass permission checks
        if user.is_superuser:
            return user

        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned. Cannot verify permissions.",
            )

        # Get all permission names for the user's role
        user_permissions = {
            p.name for p in user.role.permissions
        }

        # Check if all required permissions are present
        missing = set(required_permissions) - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Missing required permissions: {', '.join(missing)}"
                ),
            )

        return user

    return permission_checker
