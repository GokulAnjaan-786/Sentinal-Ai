"""
Database Models Package
========================

This package contains all SQLAlchemy ORM models for the SentinelAI platform.
Each model maps to a specific database table and defines the schema, relationships,
and constraints for that table.

Models are imported here for convenient access throughout the application:
    from app.models import User, Role, Activity, Alert, RiskScore

All models inherit from app.database.connection.Base which provides
consistent metadata configuration and naming conventions.
"""

from app.models.user import User
from app.models.role import Role, Permission, RolePermission
from app.models.session import UserSession
from app.models.activity import Activity
from app.models.alert import Alert
from app.models.risk_score import RiskScore
from app.models.device import Device
from app.models.department import Department
from app.models.audit_log import AuditLog
from app.models.threat_history import ThreatHistory
from app.models.log_entry import LogEntry

__all__ = [
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserSession",
    "Activity",
    "Alert",
    "RiskScore",
    "Device",
    "Department",
    "AuditLog",
    "ThreatHistory",
    "LogEntry",
]
