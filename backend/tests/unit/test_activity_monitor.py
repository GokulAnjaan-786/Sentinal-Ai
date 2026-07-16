"""
Unit Tests for Activity Monitor
=================================

Tests for the central activity detection pipeline.
"""

import pytest
from datetime import datetime

from app.activity_monitor.monitor import ActivityMonitor


class TestActivityMonitor:
    """Tests for the activity monitoring pipeline."""

    def setup_method(self):
        """Create a fresh ActivityMonitor for each test."""
        self.monitor = ActivityMonitor()

    def test_initialization(self):
        """Test that monitor initializes correctly."""
        assert self.monitor is not None

    def test_process_normal_activity(self):
        """Test processing a normal, non-anomalous activity."""
        activity = {
            "user_id": "test-user-001",
            "activity_type": "login",
            "created_at": "2024-01-15T09:00:00",
            "status": "success",
            "ip_address": "10.0.1.100",
            "device_id": "dev_0001",
            "location": "New York",
            "severity": "info",
            "risk_contribution": 0.0,
        }
        result = self.monitor.process(activity)
        assert result is not None
        assert "violations" in result
        assert "risk_score" in result or "risk_assessment" in result

    def test_process_anomalous_activity(self):
        """Test processing a known anomalous activity."""
        activity = {
            "user_id": "suspicious-user-001",
            "activity_type": "database_export",
            "created_at": "2024-01-15T02:30:00",
            "status": "success",
            "ip_address": "192.168.1.200",
            "device_id": "dev_unknown",
            "location": "Unknown Location",
            "severity": "critical",
            "risk_contribution": 0.95,
        }
        result = self.monitor.process(activity)
        assert result is not None
        assert "violations" in result
        assert len(result["violations"]) > 0

    def test_process_returns_violations_list(self):
        """Test that processing returns a violations list."""
        activity = {
            "user_id": "test-user",
            "activity_type": "usb_device",
            "created_at": "2024-01-15T09:00:00",
            "status": "success",
            "ip_address": "10.0.1.100",
            "device_id": "dev_0001",
            "location": "New York",
            "severity": "warning",
            "risk_contribution": 0.5,
        }
        result = self.monitor.process(activity)
        assert isinstance(result["violations"], list)

    def test_process_multiple_activities_sequentially(self):
        """Test that processing multiple activities maintains state."""
        activities = [
            {
                "user_id": "test-user",
                "activity_type": "login",
                "created_at": "2024-01-15T09:00:00",
                "status": "success",
                "ip_address": "10.0.1.100",
                "device_id": "dev_0001",
                "location": "New York",
                "severity": "info",
                "risk_contribution": 0.0,
            },
            {
                "user_id": "test-user",
                "activity_type": "usb_device",
                "created_at": "2024-01-15T09:15:00",
                "status": "success",
                "ip_address": "10.0.1.100",
                "device_id": "dev_0001",
                "location": "New York",
                "severity": "warning",
                "risk_contribution": 0.6,
            },
        ]
        for activity in activities:
            result = self.monitor.process(activity)
            assert result is not None

    def test_process_handles_empty_activity_fields(self):
        """Test that processing handles activities with minimal fields."""
        activity = {
            "user_id": "test-user",
            "activity_type": "file_access",
            "created_at": "2024-01-15T09:00:00",
            "status": "success",
        }
        result = self.monitor.process(activity)
        assert result is not None
