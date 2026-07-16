"""
Pytest Configuration and Shared Fixtures
==========================================

Provides reusable test fixtures for the SentinelAI test suite.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Ensure backend is on the path for imports
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_user_data():
    """Return a sample user dictionary for tests."""
    return {
        "user_id": "test-user-001",
        "username": "testanalyst",
        "role": "security_analyst",
        "department": "Security Operations Center",
    }


@pytest.fixture
def sample_activities():
    """Return a list of sample activity records."""
    return [
        {
            "user_id": "test-user-001",
            "activity_type": "login",
            "created_at": "2024-01-15T09:00:00Z",
            "status": "success",
            "ip_address": "10.0.1.100",
            "device_id": "dev_0001",
            "location": "New York",
            "severity": "info",
            "risk_contribution": 0.0,
        },
        {
            "user_id": "test-user-001",
            "activity_type": "file_access",
            "created_at": "2024-01-15T09:15:00Z",
            "status": "success",
            "ip_address": "10.0.1.100",
            "device_id": "dev_0001",
            "location": "New York",
            "severity": "info",
            "risk_contribution": 0.1,
        },
        {
            "user_id": "test-user-001",
            "activity_type": "database_query",
            "created_at": "2024-01-15T09:30:00Z",
            "status": "success",
            "ip_address": "10.0.1.100",
            "device_id": "dev_0001",
            "location": "New York",
            "severity": "warning",
            "risk_contribution": 0.4,
        },
        {
            "user_id": "test-user-001",
            "activity_type": "usb_device",
            "created_at": "2024-01-15T09:45:00Z",
            "status": "success",
            "ip_address": "10.0.1.100",
            "device_id": "dev_0001",
            "location": "New York",
            "severity": "critical",
            "risk_contribution": 0.9,
        },
    ]


@pytest.fixture
def sample_anomalous_activities():
    """Return a list of anomalous activity records."""
    return [
        {
            "user_id": "suspicious-user-002",
            "activity_type": "database_export",
            "created_at": "2024-01-15T02:30:00Z",
            "status": "success",
            "ip_address": "192.168.1.200",
            "device_id": "dev_unknown",
            "location": "Unknown Location",
            "severity": "critical",
            "risk_contribution": 0.95,
        },
        {
            "user_id": "suspicious-user-002",
            "activity_type": "privilege_escalation",
            "created_at": "2024-01-15T02:35:00Z",
            "status": "success",
            "ip_address": "192.168.1.200",
            "device_id": "dev_unknown",
            "location": "Unknown Location",
            "severity": "critical",
            "risk_contribution": 1.0,
        },
        {
            "user_id": "suspicious-user-002",
            "activity_type": "security_tool_disabled",
            "created_at": "2024-01-15T02:40:00Z",
            "status": "success",
            "ip_address": "192.168.1.200",
            "device_id": "dev_unknown",
            "location": "Unknown Location",
            "severity": "critical",
            "risk_contribution": 1.0,
        },
    ]


@pytest.fixture
def sample_risk_context():
    """Return a sample risk context dictionary."""
    return {
        "hour": 14,
        "is_weekend": False,
        "is_holiday": False,
        "is_new_device": False,
        "is_new_location": False,
        "session_count": 1,
        "time_since_last_activity_hours": 0.5,
        "concurrent_sessions": 1,
    }


@pytest.fixture
def sample_risk_context_suspicious():
    """Return a sample suspicious risk context dictionary."""
    return {
        "hour": 2,
        "is_weekend": True,
        "is_holiday": False,
        "is_new_device": True,
        "is_new_location": True,
        "session_count": 3,
        "time_since_last_activity_hours": 0.1,
        "concurrent_sessions": 2,
    }
