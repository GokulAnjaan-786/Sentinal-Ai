"""
User Schemas
==============

Pydantic schemas for user management API operations including
creation, updates, retrieval, and listing of users.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    """
    Schema for creating a new user account.
    Used by admin endpoints to onboard new users.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique login username"
    )
    email: str = Field(
        ...,
        description="Unique email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Initial password"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Full display name"
    )
    role_id: Optional[str] = Field(
        default=None,
        description="UUID of the role to assign"
    )
    department_id: Optional[str] = Field(
        default=None,
        description="UUID of the department"
    )
    employee_id: Optional[str] = Field(
        default=None,
        description="Bank employee identification number"
    )


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user account.
    All fields are optional - only provided fields will be updated.
    """
    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=200
    )
    email: Optional[str] = Field(default=None)
    role_id: Optional[str] = Field(default=None)
    department_id: Optional[str] = Field(default=None)
    employee_id: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class UserResponse(BaseModel):
    """
    Full user information response schema.
    Used when returning detailed user information to authorized users.
    """
    id: str = Field(description="User UUID")
    username: str = Field(description="Login username")
    email: str = Field(description="Email address")
    full_name: str = Field(description="Full display name")
    role_id: Optional[str] = Field(default=None, description="Role UUID")
    role_name: Optional[str] = Field(default=None, description="Role name")
    department_id: Optional[str] = Field(default=None, description="Department UUID")
    department_name: Optional[str] = Field(default=None, description="Department name")
    employee_id: Optional[str] = Field(default=None, description="Employee ID")
    is_active: bool = Field(description="Account active status")
    is_superuser: bool = Field(description="Superuser status")
    last_login: Optional[datetime] = Field(default=None, description="Last login time")
    failed_login_attempts: int = Field(description="Failed login attempt count")
    account_locked: bool = Field(description="Account locked status")
    risk_level: str = Field(description="Current risk level")
    created_at: datetime = Field(description="Account creation time")
    updated_at: datetime = Field(description="Last update time")

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """
    Minimal user information for list views and dashboards.
    Contains only essential fields for performance.
    """
    id: str = Field(description="User UUID")
    username: str = Field(description="Login username")
    full_name: str = Field(description="Full display name")
    role_name: Optional[str] = Field(default=None, description="Role name")
    department_name: Optional[str] = Field(default=None, description="Department name")
    is_active: bool = Field(description="Account active status")
    risk_level: Optional[str] = Field(default="low", description="Current risk level")
    last_login: Optional[datetime] = Field(default=None, description="Last login time")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""
    success: bool = Field(default=True)
    data: List[UserSummary] = Field(default_factory=list)
    total: int = Field(description="Total user count")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total pages")
