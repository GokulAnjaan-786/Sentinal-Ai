"""
Core Configuration Module
==========================

This module contains the core application settings, environment variable
management, and dependency injection setup for the SentinelAI platform.

Key Classes:
    - Settings: Pydantic-based configuration with environment variable loading
    - DatabaseSettings: PostgreSQL connection configuration
    - SecuritySettings: JWT and encryption configuration
    - MLSettings: Machine learning model configuration
    - QuantumSafeSettings: Post-quantum cryptography configuration

The Settings class uses pydantic-settings to automatically load and validate
configuration from environment variables and .env files. This ensures that
sensitive configuration values are never hardcoded in source code.

Usage:
    from app.core.config import settings
    print(settings.DATABASE_URL)
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Main application configuration class.

    This class loads all configuration values from environment variables.
    Create a .env file in the backend root directory with the required
    variables, or set them in your deployment environment.

    All fields use uppercase names to match standard environment variable
    conventions (e.g., DATABASE_URL maps to the DATABASE_URL env var).
    """

    # ===========================
    # Application Configuration
    # ===========================
    APP_NAME: str = Field(
        default="SentinelAI",
        description="Application name used in logs and headers"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Current application version"
    )
    APP_ENV: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )
    APP_DEBUG: bool = Field(
        default=True,
        description="Enable debug mode with verbose error messages"
    )
    APP_HOST: str = Field(
        default="0.0.0.0",
        description="Host address to bind the application server"
    )
    APP_PORT: int = Field(
        default=8000,
        description="Port number for the application server"
    )
    APP_SECRET_KEY: str = Field(
        default="sentinelai-dev-secret-key-change-in-production-256bit",
        description="Master secret key for cryptographic operations"
    )

    # ===========================
    # CORS Configuration
    # ===========================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins for frontend communication"
    )

    # ===========================
    # Database Configuration
    # ===========================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sentinelai:sentinelai_secret@localhost:5432/sentinelai_db",
        description="Async PostgreSQL connection URL"
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://sentinelai:sentinelai_secret@localhost:5432/sentinelai_db",
        description="Synchronous PostgreSQL connection URL for migrations"
    )
    DB_POOL_SIZE: int = Field(
        default=20,
        description="Number of connections in the database pool"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum number of connections beyond pool_size"
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        description="Timeout in seconds for obtaining a connection from the pool"
    )

    # ===========================
    # Security Configuration
    # ===========================
    JWT_SECRET_KEY: str = Field(
        default="sentinelai-jwt-secret-key-change-in-production",
        description="Secret key used for JWT token signing"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token expiration time in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="JWT refresh token expiration time in days"
    )
    BCRYPT_ROUNDS: int = Field(
        default=12,
        description="Number of bcrypt hashing rounds (higher = more secure but slower)"
    )

    # ===========================
    # Rate Limiting Configuration
    # ===========================
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Maximum number of requests per rate limit window"
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        description="Rate limit window duration in seconds"
    )
    LOGIN_RATE_LIMIT_REQUESTS: int = Field(
        default=5,
        description="Maximum login attempts per rate limit window"
    )
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=300,
        description="Login rate limit window (5 minutes for brute force protection)"
    )

    # ===========================
    # Machine Learning Configuration
    # ===========================
    ML_MODEL_PATH: str = Field(
        default="app/ml/data/models",
        description="Directory path for saved ML models"
    )
    ML_DATA_PATH: str = Field(
        default="app/ml/data",
        description="Directory path for ML training data"
    )
    ML_CONTAMINATION_FACTOR: float = Field(
        default=0.05,
        description="Expected proportion of anomalies in the dataset (5%)"
    )
    ML_N_ESTIMATORS: int = Field(
        default=200,
        description="Number of trees in the Isolation Forest ensemble"
    )
    ML_RETRAIN_INTERVAL_HOURS: int = Field(
        default=24,
        description="Hours between automatic model retraining"
    )

    # ===========================
    # Alert Configuration
    # ===========================
    ALERT_EMAIL_ENABLED: bool = Field(
        default=False,
        description="Enable email alert notifications"
    )
    ALERT_EMAIL_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP server for email alerts"
    )
    ALERT_EMAIL_PORT: int = Field(
        default=587,
        description="SMTP port for email alerts"
    )
    ALERT_EMAIL_USER: str = Field(
        default="",
        description="Email username for sending alerts"
    )
    ALERT_EMAIL_PASSWORD: str = Field(
        default="",
        description="Email password for sending alerts"
    )

    # ===========================
    # Quantum-Safe Security Configuration
    # ===========================
    QPC_KEY_SIZE: int = Field(
        default=256,
        description="Key size for post-quantum cryptographic operations"
    )
    QPC_ENABLED: bool = Field(
        default=True,
        description="Enable quantum-safe cryptography features"
    )
    QPC_KEY_ROTATION_DAYS: int = Field(
        default=30,
        description="Days between quantum-safe key rotations"
    )

    # ===========================
    # Session Configuration
    # ===========================
    SESSION_TIMEOUT_MINUTES: int = Field(
        default=30,
        description="Session timeout for inactive users"
    )
    MAX_CONCURRENT_SESSIONS: int = Field(
        default=3,
        description="Maximum concurrent sessions per user"
    )

    # ===========================
    # Logging Configuration
    # ===========================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format string"
    )
    AUDIT_LOG_ENABLED: bool = Field(
        default=True,
        description="Enable audit logging for compliance"
    )

    class Config:
        """Pydantic model configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings singleton.

    This function uses @lru_cache to ensure the Settings object is only
    instantiated once and reused across the application. This prevents
    redundant file reads and environment variable parsing.

    Returns:
        Settings: The validated application configuration object.

    Note:
        The cache is per-process. In multi-process deployments, each
        process will load its own Settings instance.
    """
    return Settings()


# Global settings instance for easy import across the application
settings = get_settings()
