"""
SentinelAI FastAPI Application Entry Point
============================================

This module creates and configures the FastAPI application instance.
It sets up all middleware, CORS, router mounting, startup/shutdown
events, and exception handlers.

The application follows clean architecture principles with clearly
separated concerns across controllers, services, repositories, and models.

Startup Sequence:
    1. Configure CORS middleware
    2. Add security headers middleware
    3. Add request logging middleware
    4. Mount API routers
    5. On startup: verify database connection, load ML models
    6. On shutdown: close database connections, cleanup resources
"""

import time
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.connection import async_engine

# Import API routers
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.user_routes import router as user_router
from app.api.v1.activity_routes import router as activity_router
from app.api.v1.alert_routes import router as alert_router
from app.api.v1.risk_routes import router as risk_router
from app.api.v1.dashboard_routes import router as dashboard_router
from app.api.v1.threat_routes import router as threat_router
from app.api.v1.quantum_routes import router as quantum_router

# Configure module-level logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the FastAPI application.
    This is the modern approach to managing application lifecycle
    (replaces deprecated @app.on_event decorators).

    Startup:
        - Verifies database connectivity
        - Initializes ML model cache
        - Logs application startup

    Shutdown:
        - Flushes any pending log entries
        - Closes database engine connections
        - Logs application shutdown
    """
    # ========================
    # STARTUP
    # ========================
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.APP_DEBUG}")

    # Verify database connectivity
    try:
        async with async_engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        # In development, log warning and continue
        if settings.APP_ENV == "production":
            raise
        logger.warning("Continuing in development mode without database")

    # Initialize ML model cache directory
    import os
    os.makedirs(settings.ML_MODEL_PATH, exist_ok=True)
    os.makedirs(settings.ML_DATA_PATH, exist_ok=True)
    logger.info("ML directories initialized")

    yield  # Application is running

    # ========================
    # SHUTDOWN
    # ========================
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Dispose of the database engine connection pool
    await async_engine.dispose()
    logger.info("Database connections closed")

    logger.info(f"{settings.APP_NAME} shutdown complete")


def create_application() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.

    This function encapsulates all application setup logic and returns
    a fully configured FastAPI instance. Using a factory pattern allows
    for easier testing with different configurations.

    Returns:
        FastAPI: Fully configured application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-Powered Privileged Access Misuse & Insider Threat Detection System. "
            "Enterprise-grade cybersecurity platform for banking and financial institutions."
        ),
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.APP_DEBUG else None,
        redoc_url="/api/redoc" if settings.APP_DEBUG else None,
        openapi_url="/api/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # ========================
    # CORS MIDDLEWARE
    # ========================
    # Configure Cross-Origin Resource Sharing to allow frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
    )

    # ========================
    # SECURITY HEADERS MIDDLEWARE
    # ========================
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        """
        Add security headers to all HTTP responses.

        These headers protect against common web vulnerabilities:
        - X-Content-Type-Options: Prevents MIME type sniffing
        - X-Frame-Options: Prevents clickjacking
        - X-XSS-Protection: Enables XSS filtering
        - Strict-Transport-Security: Enforces HTTPS
        - Content-Security-Policy: Controls resource loading
        - Cache-Control: Prevents sensitive data caching
        """
        response: Response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"

        # Only add HSTS in production (requires valid HTTPS)
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response

    # ========================
    # REQUEST ID & LOGGING MIDDLEWARE
    # ========================
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """
        Log all incoming requests and responses with timing information.

        Each request is assigned a unique ID for correlation across
        distributed components. Request/response details are logged
        for debugging and audit purposes.
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )

        # Process the request
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Log unhandled exceptions
            logger.error(
                f"Unhandled exception: {str(exc)}",
                extra={"request_id": request_id}
            )
            raise

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Add request ID and timing headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log completed request
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[{response.status_code}] {duration_ms:.2f}ms",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )

        return response

    # ========================
    # EXCEPTION HANDLERS
    # ========================
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent error response format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": str(exc.detail),
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle validation errors with 400 Bad Request."""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(exc),
                "error_code": "VALIDATION_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Catch-all handler for unhandled exceptions.
        Returns generic error to prevent information leakage.
        """
        logger.exception(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An internal server error occurred",
                "error_code": "INTERNAL_SERVER_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    # ========================
    # MOUNT API ROUTERS
    # ========================
    # All API routes are versioned under /api/v1/ for backward compatibility
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(activity_router, prefix="/api/v1/activities", tags=["Activities"])
    app.include_router(alert_router, prefix="/api/v1/alerts", tags=["Alerts"])
    app.include_router(risk_router, prefix="/api/v1/risk", tags=["Risk Scoring"])
    app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
    app.include_router(threat_router, prefix="/api/v1/threats", tags=["Threats"])
    app.include_router(quantum_router, prefix="/api/v1/quantum", tags=["Quantum-Safe Security"])

    # ========================
    # HEALTH CHECK ENDPOINT
    # ========================
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Application health check endpoint.

        Used by load balancers, monitoring systems, and container
        orchestrators to verify application availability.
        """
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with application information."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "AI-Powered Privileged Access Misuse & Insider Threat Detection",
            "docs": "/api/docs" if settings.APP_DEBUG else "Documentation disabled in production",
        }

    return app


# Create the application instance
# This is imported by uvicorn to run the application:
#   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
app = create_application()
