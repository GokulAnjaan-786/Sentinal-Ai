"""
SentinelAI - AI-Powered Privileged Access Misuse & Insider Threat Detection System
====================================================================================

This is the root package for the SentinelAI backend application.
SentinelAI is an enterprise-grade cybersecurity platform designed for banking
and financial institutions to detect insider threats, monitor privileged
access, and provide AI-driven behavioral analytics.

Package Structure:
    - core: Core configuration, settings, and dependency injection
    - api: API route definitions and versioning
    - controllers: Request handlers and response formatting
    - services: Business logic layer
    - repositories: Data access layer
    - models: SQLAlchemy ORM database models
    - schemas: Pydantic request/response schemas
    - middleware: HTTP middleware components
    - auth: Authentication and authorization modules
    - ml: Machine learning models and inference engine
    - rule_engine: Rule-based threat detection engine
    - risk_engine: Dynamic risk score calculation engine
    - alert_engine: Alert generation and notification system
    - quantum_safe: Quantum-proof cryptography module
    - activity_monitor: User activity monitoring and logging
    - logging_config: Structured logging configuration
    - utils: Shared utility functions

Author: SentinelAI Engineering Team
Version: 1.0.0
License: Enterprise
"""

__version__ = "1.0.0"
__title__ = "SentinelAI"
__description__ = "AI-Powered Privileged Access Misuse & Insider Threat Detection System"
