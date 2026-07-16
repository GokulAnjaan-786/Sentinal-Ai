"""
Authentication Package
=======================

This package handles all authentication and authorization logic for SentinelAI.

Components:
    - jwt_handler: JWT token creation, validation, and management
    - password_utils: Password hashing with bcrypt and verification
    - dependencies: FastAPI dependency injection for auth checks
    - rbac: Role-Based Access Control permission checking

Security Notes:
    - All passwords are hashed with bcrypt (12 rounds minimum)
    - JWT tokens have configurable expiration (default 30 minutes)
    - Refresh tokens enable silent re-authentication
    - Failed login attempts trigger progressive account lockout
    - Session management tracks concurrent sessions per user
"""

from app.auth.jwt_handler import JWTHandler
from app.auth.password_utils import PasswordManager
from app.auth.dependencies import get_current_user, require_role, require_permission
from app.auth.rbac import RBACManager

__all__ = [
    "JWTHandler",
    "PasswordManager",
    "get_current_user",
    "require_role",
    "require_permission",
    "RBACManager",
]
