"""
Middleware Package
===================

This package contains all HTTP middleware components for the SentinelAI API.

Middleware runs in the order it is added. The processing pipeline is:
    1. Security Headers Middleware - Adds protective HTTP headers
    2. Request Logging Middleware - Logs all requests with timing
    3. Rate Limiting Middleware - Enforces request rate limits
    4. Authentication Middleware - Validates JWT tokens (route-specific)
"""

from app.middleware.rate_limiter import RateLimiterMiddleware

__all__ = ["RateLimiterMiddleware"]
