"""
Logging Configuration Package
===============================

Configures structured logging for the SentinelAI platform.

Logging Strategy:
    - Console logging for development (human-readable format)
    - File logging for production (JSON format for log aggregation)
    - Database logging for audit trails (queryable log entries)
    - Separate loggers for different subsystems (auth, ML, rules, etc.)

Log Levels:
    - DEBUG: Detailed debugging information
    - INFO: General operational messages
    - WARNING: Unexpected but recoverable conditions
    - ERROR: Failures that require attention
    - CRITICAL: System-threatening failures
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from app.core.config import settings


class SecurityFilter(logging.Filter):
    """
    Custom logging filter that adds security context to log records.

    Adds fields for user_id, ip_address, and request_id to each
    log record. These fields are populated by the middleware and
    request context.
    """

    def filter(self, record):
        # Add default security context fields if not present
        if not hasattr(record, "user_id"):
            record.user_id = None
        if not hasattr(record, "ip_address"):
            record.ip_address = None
        if not hasattr(record, "request_id"):
            record.request_id = None
        return True


class SecurityFormatter(logging.Formatter):
    """
    Custom log formatter for security-focused log output.

    Produces structured log lines that include:
    - Timestamp (ISO 8601 format)
    - Log level
    - Module name
    - Request ID (for correlating requests)
    - User ID (for tracking user actions)
    - IP address (for network tracking)
    - Message
    """

    def format(self, record):
        timestamp = datetime.utcnow().isoformat()
        parts = [
            f"[{timestamp}]",
            f"[{record.levelname:8s}]",
            f"[{record.name}]",
        ]

        # Add request context if available
        if hasattr(record, "request_id") and record.request_id:
            parts.append(f"[req:{record.request_id[:8]}]")

        if hasattr(record, "user_id") and record.user_id:
            parts.append(f"[user:{record.user_id[:8]}]")

        if hasattr(record, "ip_address") and record.ip_address:
            parts.append(f"[ip:{record.ip_address}]")

        parts.append(record.getMessage())

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            parts.append(f"\n{self.formatException(record.exc_info)}")

        return " ".join(parts)


def setup_logging() -> None:
    """
    Configure the application logging system.

    Sets up multiple log handlers:
    1. Console handler: Human-readable output for development
    2. File handler: Rotating log files for production
    3. Error file handler: Separate file for errors and critical messages

    This function should be called once during application startup,
    before any other module imports that use logging.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers to prevent duplicate logging
    root_logger.handlers.clear()

    # Add security context filter
    security_filter = SecurityFilter()

    # Create formatter
    formatter = SecurityFormatter(settings.LOG_FORMAT)

    # ========================
    # Console Handler
    # ========================
    # Always log to console for container environments (Docker, k8s)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    console_handler.addFilter(security_filter)
    root_logger.addHandler(console_handler)

    # ========================
    # File Handler (Rotating)
    # ========================
    # Create log directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Main application log file (rotates at 10MB, keeps 10 files)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "sentinelai.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(security_filter)
    root_logger.addHandler(file_handler)

    # Error log file (separate file for errors and above)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "sentinelai_errors.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(security_filter)
    root_logger.addHandler(error_handler)

    # ========================
    # Security-specific log file
    # ========================
    # Logs security events separately for SOC analyst review
    security_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "security_events.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=20,  # Keep more security logs
        encoding="utf-8",
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(formatter)
    security_handler.addFilter(security_filter)
    root_logger.addHandler(security_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    logging.info("Logging system initialized")


def get_security_logger(name: str) -> logging.Logger:
    """
    Get a logger configured for security event logging.

    Security loggers automatically include additional context
    and write to the security events log file.

    Args:
        name: Logger name (typically the module name).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(f"sentinelai.security.{name}")
    return logger
