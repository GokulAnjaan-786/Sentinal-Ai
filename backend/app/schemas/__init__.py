"""
Pydantic Schemas Package
=========================

This package contains all Pydantic schemas used for request validation
and response serialization in the SentinelAI API.

Schemas are organized by domain and serve as the API contract:
    - Auth schemas: Login, registration, token refresh
    - User schemas: User CRUD operations
    - Activity schemas: Activity log queries and responses
    - Alert schemas: Alert management operations
    - Risk schemas: Risk score queries and responses
    - Dashboard schemas: Dashboard aggregated data
    - Common schemas: Shared response types, pagination
"""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    LogoutRequest,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserSummary,
)
from app.schemas.activity import (
    ActivityCreate,
    ActivityResponse,
    ActivityListResponse,
    ActivityFilter,
)
from app.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertListResponse,
    AlertFilter,
    AlertStats,
)
from app.schemas.risk import (
    RiskScoreResponse,
    RiskScoreListResponse,
    RiskScoreFilter,
    RiskAssessment,
)
from app.schemas.dashboard import (
    DashboardSummary,
    ThreatTimeline,
    TopRiskUser,
    RiskDistribution,
)
from app.schemas.common import (
    BaseResponse,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)
