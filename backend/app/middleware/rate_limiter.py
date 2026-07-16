"""
Rate Limiter Middleware
========================

Implements request rate limiting to protect against:
- Brute force attacks on authentication endpoints
- API abuse and denial-of-service attempts
- Excessive resource consumption by individual clients

The rate limiter uses an in-memory sliding window counter.
In production, this should be replaced with Redis for distributed
rate limiting across multiple application instances.

Rate Limiting Strategy:
    - Default: 100 requests per 60-second window
    - Login endpoints: 5 attempts per 300-second window
    - Per-IP tracking for external clients
    - Per-user tracking for authenticated requests
"""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware for enforcing request rate limits.

    Uses a sliding window algorithm to track request counts per client.
    When a client exceeds the rate limit, subsequent requests receive
    a 429 Too Many Requests response with retry-after information.

    The middleware tracks clients by:
    1. Authenticated user ID (from JWT token)
    2. Client IP address (for unauthenticated requests)

    Attributes:
        default_limit: Maximum requests in the default window
        default_window: Default window duration in seconds
        login_limit: Maximum requests in the login window
        login_window: Login window duration in seconds
        login_paths: URL paths that use the stricter login rate limit
    """

    def __init__(self, app):
        """
        Initialize the rate limiter middleware.

        Args:
            app: The ASGI application to wrap.
        """
        super().__init__(app)
        self.default_limit = settings.RATE_LIMIT_REQUESTS
        self.default_window = settings.RATE_LIMIT_WINDOW_SECONDS
        self.login_limit = settings.LOGIN_RATE_LIMIT_REQUESTS
        self.login_window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS

        """
        In-memory rate limit storage.
        Structure: {client_key: [(timestamp, count), ...]}
        In production, replace with Redis for distributed rate limiting.
        """
        self._request_counts: Dict[str, list] = defaultdict(list)

        """
        Login-specific rate limit storage.
        Uses separate storage to apply stricter limits on auth endpoints.
        """
        self._login_counts: Dict[str, list] = defaultdict(list)

    def _get_client_key(self, request: Request) -> str:
        """
        Generate a unique client identifier for rate limiting.

        Uses the authenticated user ID if available, otherwise falls back
        to the client's IP address. This ensures authenticated users are
        rate-limited by account, while anonymous users are limited by IP.

        Args:
            request: The incoming HTTP request.

        Returns:
            String key uniquely identifying the client.
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        return f"ip:{client_ip}"

    def _is_login_path(self, path: str) -> bool:
        """
        Check if the request path is a login-related endpoint.

        Login endpoints have stricter rate limiting to prevent
        brute force attacks.

        Args:
            path: The request URL path.

        Returns:
            True if the path is a login endpoint.
        """
        login_keywords = ["/login", "/authenticate", "/token"]
        return any(keyword in path.lower() for keyword in login_keywords)

    def _cleanup_old_entries(self, entries: list, window_seconds: int) -> list:
        """
        Remove entries older than the rate limit window.

        Uses the sliding window algorithm to maintain an accurate
        count of requests within the current window period.

        Args:
            entries: List of request timestamps.
            window_seconds: The rate limit window duration.

        Returns:
            Filtered list containing only recent entries.
        """
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [ts for ts in entries if ts > cutoff]

    def _check_rate_limit(
        self, client_key: str, limit: int, window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if the client has exceeded the rate limit.

        Args:
            client_key: Unique client identifier.
            limit: Maximum allowed requests.
            window: Time window in seconds.

        Returns:
            Tuple of (is_limited, remaining, retry_after_seconds).
            - is_limited: True if the rate limit is exceeded
            - remaining: Number of requests remaining in the window
            - retry_after_seconds: Seconds until the oldest request expires
        """
        current_time = time.time()
        entries = self._request_counts.get(client_key, [])

        # Clean up old entries
        entries = self._cleanup_old_entries(entries, window)
        self._request_counts[client_key] = entries

        current_count = len(entries)

        if current_count >= limit:
            # Rate limit exceeded - calculate retry-after time
            oldest_entry = entries[0] if entries else current_time
            retry_after = int(oldest_entry + window - current_time) + 1
            return True, 0, max(retry_after, 1)

        # Record this request
        entries.append(current_time)
        remaining = limit - current_count - 1
        return False, remaining, 0

    async def dispatch(self, request: Request, call_next):
        """
        Process each request through the rate limiter.

        Checks the rate limit before processing the request. If the
        limit is exceeded, returns a 429 response immediately without
        forwarding the request to the application.

        The response includes standard rate limiting headers:
        - X-RateLimit-Limit: Maximum requests allowed
        - X-RateLimit-Remaining: Requests remaining
        - X-RateLimit-Reset: Time when the limit resets
        - Retry-After: Seconds to wait (only on 429 responses)
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/", "/api/docs", "/api/redoc", "/openapi.json"]:
            return await call_next(request)

        client_key = self._get_client_key(request)

        # Determine which rate limit applies
        if self._is_login_path(request.url.path):
            is_limited, remaining, retry_after = self._check_rate_limit(
                f"login:{client_key}", self.login_limit, self.login_window
            )
            limit = self.login_limit
            window = self.login_window
        else:
            is_limited, remaining, retry_after = self._check_rate_limit(
                client_key, self.default_limit, self.default_window
            )
            limit = self.default_limit
            window = self.default_window

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_key}: "
                f"{limit} requests per {window}s"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                }
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response
