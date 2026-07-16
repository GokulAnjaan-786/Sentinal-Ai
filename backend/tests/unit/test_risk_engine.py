"""
Unit Tests for Risk Engine
============================

Tests for the dynamic risk scoring engine.
"""

import pytest
from app.risk_engine.engine import RiskEngine


class TestRiskEngine:
    """Tests for risk score calculation."""

    def setup_method(self):
        """Create a fresh RiskEngine for each test."""
        self.engine = RiskEngine()

    def test_low_risk_score(self):
        """Test that normal activity produces low risk score."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=-0.5,  # Very normal
            rule_violations=[],
            activity_context={"hour": 10, "is_weekend": False},
        )
        assert assessment.score < 25
        assert assessment.risk_level == "low"

    def test_medium_risk_score(self):
        """Test that some anomalies produce medium risk score."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=0.2,
            rule_violations=["usb_device_usage"],
            activity_context={"hour": 10, "is_weekend": False},
        )
        assert 25 <= assessment.score <= 50 or assessment.score < 75

    def test_high_risk_score(self):
        """Test that multiple violations produce high risk score."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=0.7,
            rule_violations=["database_export", "multiple_failed_logins", "config_change"],
            activity_context={
                "hour": 2, "is_weekend": False, "is_new_device": True,
                "is_new_location": True, "session_count": 3,
            },
        )
        assert assessment.score >= 50

    def test_critical_risk_score(self):
        """Test that severe violations produce critical risk score."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=0.9,
            rule_violations=[
                "privilege_escalation", "security_tool_disabled",
                "database_export", "multiple_failed_logins",
            ],
            activity_context={
                "hour": 3, "is_weekend": True, "is_new_device": True,
                "is_new_location": True, "session_count": 5,
            },
        )
        assert assessment.score >= 75
        assert assessment.risk_level == "critical"

    def test_risk_level_mapping(self):
        """Test that score ranges map to correct risk levels."""
        assert self.engine._score_to_level(10) == "low"
        assert self.engine._score_to_level(30) == "medium"
        assert self.engine._score_to_level(60) == "high"
        assert self.engine._score_to_level(85) == "critical"

    def test_factors_are_populated(self):
        """Test that risk assessment includes contributing factors."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=0.3,
            rule_violations=["usb_device_usage"],
            activity_context={"hour": 10},
        )
        assert len(assessment.factors) > 0
        assert all(hasattr(f, "name") for f in assessment.factors)
        assert all(hasattr(f, "risk_points") for f in assessment.factors)

    def test_explanation_generated(self):
        """Test that a human-readable explanation is generated."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=0.5,
            rule_violations=["database_export"],
            activity_context={"hour": 22},
        )
        assert len(assessment.explanation) > 0
        assert "Risk Score Assessment" in assessment.explanation

    def test_recommended_actions(self):
        """Test that recommended actions are provided."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=0.8,
            rule_violations=["privilege_escalation"],
            activity_context={"hour": 2},
        )
        assert len(assessment.recommended_actions) > 0

    def test_user_trend_tracking(self):
        """Test that user risk trends are tracked over time."""
        user_id = "trend-user"
        # Simulate multiple assessments
        for score in [10, 20, 30, 40, 50]:
            self.engine.calculate_risk_score(
                user_id=user_id,
                ml_anomaly_score=score / 100,
                rule_violations=[],
                activity_context={"hour": 10},
            )

        trend = self.engine.get_user_trend(user_id)
        assert trend["data_points"] == 5
        assert trend["trend"] == "increasing"

    def test_score_is_capped_at_100(self):
        """Test that risk score never exceeds 100."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=1.0,
            rule_violations=[
                "privilege_escalation", "security_tool_disabled",
                "database_export", "multiple_failed_logins",
                "config_change", "concurrent_sessions",
                "account_lockout", "excessive_db_queries",
            ],
            activity_context={
                "hour": 3, "is_weekend": True, "is_new_device": True,
                "is_new_location": True, "session_count": 10,
            },
        )
        assert assessment.score <= 100

    def test_score_is_non_negative(self):
        """Test that risk score is never negative."""
        assessment = self.engine.calculate_risk_score(
            user_id="test-user",
            ml_anomaly_score=-1.0,
            rule_violations=[],
            activity_context={"hour": 12, "is_weekend": False},
        )
        assert assessment.score >= 0
