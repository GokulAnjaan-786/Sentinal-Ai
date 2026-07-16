"""
Authentication Schemas
=======================

Pydantic schemas for authentication-related API operations including
login, token management, password changes, and session management.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
import re


class LoginRequest(BaseModel):
    """
    User login request schema.

    Validates the login credentials before processing authentication.
    The username field accepts either a username or email address.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Username or email address"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password"
    )
    remember_me: bool = Field(
        default=False,
        description="Extend session duration if True"
    )


class LoginResponse(BaseModel):
    """
    Successful login response schema.

    Contains the JWT tokens, user information, and session details
    needed by the frontend to complete the authentication flow.
    """
    access_token: str = Field(
        description="JWT access token for API authorization"
    )
    refresh_token: str = Field(
        description="JWT refresh token for obtaining new access tokens"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        description="Access token expiration time in seconds"
    )
    user: "UserSummary" = Field(
        description="Summary of the authenticated user's profile"
    )
    requires_password_change: bool = Field(
        default=False,
        description="Whether the user must change their password"
    )


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(
        ...,
        description="Valid refresh token"
    )


class TokenRefreshResponse(BaseModel):
    """Token refresh response with new access token."""
    access_token: str = Field(description="New JWT access token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(description="New token expiration in seconds")


class PasswordChangeRequest(BaseModel):
    """Password change request for authenticated users."""
    current_password: str = Field(
        ...,
        min_length=1,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Confirm new password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce password strength requirements.

        Passwords must contain at least:
        - One uppercase letter
        - One lowercase letter
        - One digit
        - One special character
        """
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Verify that the confirmation password matches the new password."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request (initiated via email)."""
    email: str = Field(
        ...,
        description="Email address associated with the account"
    )


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation (completes the reset flow)."""
    token: str = Field(
        ...,
        description="Password reset token from email"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Confirm new password"
    )


class LogoutRequest(BaseModel):
    """Logout request schema."""
    session_id: Optional[str] = Field(
        default=None,
        description="Specific session ID to terminate (null for all sessions)"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for logout"
    )


class UserSummary(BaseModel):
    """
    Minimal user information returned in authentication responses.
    Contains only the fields needed by the frontend for display and authorization.
    """
    id: str = Field(description="User UUID")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    full_name: str = Field(description="Full display name")
    role: str = Field(description="Role name")
    department: Optional[str] = Field(default=None, description="Department name")
    is_active: bool = Field(description="Whether the account is active")

    class Config:
        from_attributes = True


# Rebuild forward references for circular schema dependencies
LoginResponse.model_rebuild()
