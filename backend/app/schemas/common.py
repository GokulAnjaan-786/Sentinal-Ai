"""
Common Schemas
===============

Shared Pydantic schemas used across the SentinelAI API for standardized
request/response patterns, pagination, and error handling.
"""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    Base response schema for all API responses.

    Provides a consistent response envelope with status, message, and data fields.
    This ensures that all API consumers can rely on a predictable response format.
    """
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    message: str = Field(
        default="Operation completed successfully",
        description="Human-readable status message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Server timestamp of the response"
    )

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SuccessResponse(BaseResponse):
    """Success response with optional data payload."""
    data: Optional[Any] = Field(
        default=None,
        description="Response data payload"
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response schema.

    Provides consistent error information including error code,
    message, and optional details for debugging.
    """
    success: bool = Field(
        default=False,
        description="Always False for error responses"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code for programmatic handling"
    )
    details: Optional[Any] = Field(
        default=None,
        description="Additional error details (only in debug mode)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Server timestamp of the error"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response schema for list endpoints.

    Provides consistent pagination metadata alongside the data items.
    All list endpoints in the API return this format.
    """
    success: bool = Field(default=True)
    data: List[T] = Field(
        default_factory=list,
        description="List of items in the current page"
    )
    total: int = Field(
        description="Total number of items across all pages"
    )
    page: int = Field(
        description="Current page number (1-indexed)"
    )
    page_size: int = Field(
        description="Number of items per page"
    )
    total_pages: int = Field(
        description="Total number of pages"
    )
    has_next: bool = Field(
        description="Whether there is a next page"
    )
    has_previous: bool = Field(
        description="Whether there is a previous page"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )


class PaginationParams(BaseModel):
    """
    Query parameters for paginated list endpoints.

    Usage:
        @router.get("/activities")
        async def get_activities(pagination: PaginationParams = Depends()):
            ...
    """
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET value."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get the SQL LIMIT value."""
        return self.page_size


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""
    status: str = Field(description="Service health status")
    version: str = Field(description="Application version")
    database: str = Field(description="Database connectivity status")
    uptime: float = Field(description="Uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
