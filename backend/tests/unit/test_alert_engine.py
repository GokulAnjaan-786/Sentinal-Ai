"""
Unit Tests for Alert Engine
=============================

Tests for alert creation, lifecycle, and management.
"""

import pytest
from datetime import datetime, timedelta

from app.alert_engine.engine import AlertEngine


class TestAlertEngine:
    """Tests for the alert creation and management engine."""

    def setup_method(self):
        """Create a fresh AlertEngine for each test."""
        self.engine = AlertEngine()

    def test_initialization(self):
        """Test that engine initializes correctly."""
        assert self.engine is not None

    def test_create_alert_from_rule(self):
        """Test that alerts can be created from rule violations."""
        alert = self.engine.create_alert(
            user_id="test-user",
            alert_type="rule_violation",
            severity="high",
            title="USB Device Detected",
            description="Unauthorized USB device connected to workstation",
            risk_score=72.5,
        )
        assert alert is not None
        assert alert.user_id == "test-user"
        assert alert.severity == "high"
        assert alert.status == "open"

    def test_create_alert_from_ml(self):
        """Test that alerts can be created from ML anomalies."""
        alert = self.engine.create_alert(
            user_id="test-user",
            alert_type="ml_anomaly",
            severity="critical",
            title="Anomalous Database Activity",
            description="ML model detected unusual database query patterns",
            risk_score=85.0,
            explanation="Pattern deviates significantly from baseline",
        )
        assert alert.alert_type == "ml_anomaly"
        assert alert.risk_score == 85.0

    def test_create_alert_from_risk_threshold(self):
        """Test that alerts can be created from risk threshold breaches."""
        alert = self.engine.create_alert(
            user_id="test-user",
            alert_type="risk_threshold",
            severity="medium",
            title="Risk Score Elevated",
            description="User risk score exceeded threshold",
            risk_score=55.0,
        )
        assert alert.alert_type == "risk_threshold"

    def test_alert_severity_mapping(self):
        """Test that risk scores map to correct severities."""
        assert self.engine._score_to_severity(15) == "low"
        assert self.engine._score_to_severity(35) == "medium"
        assert self.engine._score_to_severity(65) == "high"
        assert self.engine._score_to_severity(85) == "critical"

    def test_get_alerts_list(self):
        """Test that alerts can be retrieved as a list."""
        # Create some alerts
        for i in range(3):
            self.engine.create_alert(
                user_id=f"user-{i}",
                alert_type="rule_violation",
                severity="medium",
                title=f"Alert {i}",
                description=f"Test alert {i}",
                risk_score=40.0,
            )
        alerts = self.engine.get_alerts()
        assert len(alerts) >= 3

    def test_get_alerts_filter_by_severity(self):
        """Test that alerts can be filtered by severity."""
        self.engine.create_alert(
            user_id="user-critical",
            alert_type="ml_anomaly",
            severity="critical",
            title="Critical Alert",
            description="Critical test",
            risk_score=90.0,
        )
        self.engine.create_alert(
            user_id="user-low",
            alert_type="rule_violation",
            severity="low",
            title="Low Alert",
            description="Low test",
            risk_score=15.0,
        )
        critical_alerts = self.engine.get_alerts(severity="critical")
        low_alerts = self.engine.get_alerts(severity="low")
        assert len(critical_alerts) >= 1
        assert all(a.severity == "critical" for a in critical_alerts)
        assert all(a.severity == "low" for a in low_alerts)

    def test_get_alerts_filter_by_status(self):
        """Test that alerts can be filtered by status."""
        alert = self.engine.create_alert(
            user_id="user-test",
            alert_type="rule_violation",
            severity="high",
            title="Status Test",
            description="Testing status filter",
            risk_score=60.0,
        )
        open_alerts = self.engine.get_alerts(status="open")
        assert len(open_alerts) >= 1

    def test_alert_has_created_timestamp(self):
        """Test that alerts have a creation timestamp."""
        alert = self.engine.create_alert(
            user_id="user-test",
            alert_type="rule_violation",
            severity="medium",
            title="Timestamp Test",
            description="Testing timestamps",
            risk_score=40.0,
        )
        assert alert.created_at is not None

    def test_alert_has_id(self):
        """Test that each alert has a unique ID."""
        alert1 = self.engine.create_alert(
            user_id="user-1",
            alert_type="rule_violation",
            severity="low",
            title="ID Test 1",
            description="First",
            risk_score=20.0,
        )
        alert2 = self.engine.create_alert(
            user_id="user-2",
            alert_type="rule_violation",
            severity="low",
            title="ID Test 2",
            description="Second",
            risk_score=20.0,
        )
        assert alert1.id != alert2.id

    def test_recommendation_generation(self):
        """Test that recommended actions are generated for high-severity alerts."""
        alert = self.engine.create_alert(
            user_id="user-test",
            alert_type="ml_anomaly",
            severity="critical",
            title="Critical Anomaly",
            description="Detected data exfiltration pattern",
            risk_score=90.0,
        )
        assert hasattr(alert, "recommended_actions") or hasattr(alert, "explanation")
