"""
Alert Engine
=============

Generates, manages, and dispatches security alerts.

The Alert Engine is responsible for:
1. Creating alerts from rule violations and ML anomalies
2. Enriching alerts with contextual information
3. Generating explainable AI output for each alert
4. Storing alerts in the database for SOC analyst review
5. Dispatching notifications (email, dashboard, etc.)
6. Managing alert lifecycle (acknowledgment, resolution)

Alert Priority Matrix:
    CRITICAL: Immediate SOC notification, possible automated response
    HIGH:     Alert within 15 minutes, assigned to analyst
    MEDIUM:   Alert within 1 hour, queued for review
    LOW:      Alert within 24 hours, informational
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AlertData:
    """Data structure for a new alert."""
    user_id: str
    alert_type: str
    title: str
    description: str
    severity: str
    priority: str
    risk_score: float
    explanation: str
    recommended_action: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertEngine:
    """
    Alert generation and management engine.

    Processes signals from the rule engine and ML engine to create
    actionable alerts for SOC analysts.
    """

    def __init__(self):
        """Initialize the alert engine."""
        self.alert_templates = self._load_alert_templates()

    def _load_alert_templates(self) -> Dict[str, Dict[str, str]]:
        """Load alert templates for consistent alert formatting."""
        return {
            "midnight_login": {
                "title": "Unusual Login Time Detected",
                "description": "User logged in during non-business hours",
            },
            "multiple_failed_logins": {
                "title": "Multiple Failed Login Attempts",
                "description": "Excessive failed login attempts detected",
            },
            "usb_device_usage": {
                "title": "USB Device Activity Detected",
                "description": "USB device connected or removed",
            },
            "database_export": {
                "title": "Database Export Detected",
                "description": "Bulk data extraction from database",
            },
            "privilege_escalation": {
                "title": "Privilege Escalation Attempt",
                "description": "Unauthorized attempt to escalate privileges",
            },
            "large_file_download": {
                "title": "Large File Download",
                "description": "Unusually large file download detected",
            },
            "security_tool_disabled": {
                "title": "Security Tool Tampering",
                "description": "Security controls modified or disabled",
            },
            "anomaly_detected": {
                "title": "Behavioral Anomaly Detected",
                "description": "AI detected unusual behavioral pattern",
            },
            "risk_threshold": {
                "title": "Risk Score Threshold Exceeded",
                "description": "User risk score exceeded critical threshold",
            },
            "concurrent_sessions": {
                "title": "Suspicious Concurrent Sessions",
                "description": "Sessions active from geographically distant locations",
            },
            "excessive_db_queries": {
                "title": "Excessive Database Activity",
                "description": "Unusually high number of database queries",
            },
            "config_change": {
                "title": "Configuration Change Detected",
                "description": "System configuration modification detected",
            },
            "unusual_location": {
                "title": "Unusual Access Location",
                "description": "Login from unexpected geographic location",
            },
            "account_lockout": {
                "title": "Account Locked",
                "description": "Account locked due to security policy violation",
            },
        }

    def create_alert(self, alert_data: AlertData) -> Dict[str, Any]:
        """
        Process and create a new security alert.

        Enriches the alert with contextual information and generates
        the explainable AI output.

        Args:
            alert_data: Raw alert data from detection engines.

        Returns:
            Enriched alert dictionary ready for storage and display.
        """
        # Get template for this alert type
        template = self.alert_templates.get(
            alert_data.alert_type,
            {"title": alert_data.title, "description": alert_data.description}
        )

        # Create enriched alert
        alert = {
            "user_id": alert_data.user_id,
            "alert_type": alert_data.alert_type,
            "title": alert_data.title or template["title"],
            "description": alert_data.description or template["description"],
            "severity": alert_data.severity,
            "priority": alert_data.priority or self._calculate_priority(
                alert_data.severity, alert_data.risk_score
            ),
            "status": "generated",
            "risk_score": alert_data.risk_score,
            "explanation": alert_data.explanation,
            "recommended_action": alert_data.recommended_action,
            "source": alert_data.source,
            "metadata_json": alert_data.metadata,
            "is_false_positive": False,
            "created_at": datetime.utcnow(),
        }

        # Log the alert generation
        logger.warning(
            f"ALERT GENERATED: [{alert['severity'].upper()}] "
            f"{alert['title']} for user {alert_data.user_id} "
            f"(source: {alert_data.source}, risk: {alert_data.risk_score:.1f})"
        )

        return alert

    def create_rule_alert(
        self,
        user_id: str,
        rule_name: str,
        rule_explanation: str,
        risk_score: float,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Create an alert from a rule engine trigger.

        This is a convenience method that wraps the rule violation
        information into an AlertData and creates the alert.

        Args:
            user_id: User who triggered the rule.
            rule_name: Name of the triggered rule.
            rule_explanation: Explanation from the rule engine.
            risk_score: Current risk score.
            metadata: Additional rule-specific metadata.

        Returns:
            Created alert dictionary.
        """
        template = self.alert_templates.get(rule_name, {})

        # Determine severity based on rule
        severity_map = {
            "privilege_escalation": "critical",
            "security_tool_disabled": "critical",
            "database_export": "high",
            "multiple_failed_logins": "high",
            "account_lockout": "high",
            "concurrent_sessions": "high",
            "midnight_login": "medium",
            "usb_device_usage": "low",
            "large_file_download": "medium",
            "config_change": "medium",
            "unusual_location": "medium",
            "excessive_db_queries": "medium",
        }
        severity = severity_map.get(rule_name, "medium")

        alert_data = AlertData(
            user_id=user_id,
            alert_type=rule_name,
            title=template.get("title", f"Rule Violation: {rule_name}"),
            description=template.get("description", rule_explanation),
            severity=severity,
            priority="",
            risk_score=risk_score,
            explanation=rule_explanation,
            recommended_action=self._get_rule_action(rule_name),
            source="rule_engine",
            metadata=metadata or {},
        )

        return self.create_alert(alert_data)

    def create_anomaly_alert(
        self,
        user_id: str,
        anomaly_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create an alert from ML anomaly detection.

        Args:
            user_id: User with anomalous behavior.
            anomaly_data: Output from the ML inference engine.

        Returns:
            Created alert dictionary.
        """
        risk_level = anomaly_data.get("risk_level", "medium")
        score = anomaly_data.get("anomaly_score", 0)

        alert_data = AlertData(
            user_id=user_id,
            alert_type="anomaly_detected",
            title="Behavioral Anomaly Detected",
            description=(
                f"AI behavioral analytics detected unusual activity patterns. "
                f"Anomaly score: {score:.3f}"
            ),
            severity=risk_level,
            priority="",
            risk_score=score * 100,
            explanation=anomaly_data.get("explanation", "Anomaly detected by ML model"),
            recommended_action="Review the user's recent activity and compare with baseline behavior",
            source="ml_engine",
            metadata={
                "model_used": anomaly_data.get("model_used", "unknown"),
                "model_version": anomaly_data.get("model_version", "unknown"),
                "confidence": anomaly_data.get("confidence", 0),
                "contributing_features": anomaly_data.get("contributing_features", []),
            },
        )

        return self.create_alert(alert_data)

    def create_risk_alert(
        self,
        user_id: str,
        risk_assessment: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Create an alert when risk score exceeds threshold.

        Only creates an alert if the risk level is HIGH or CRITICAL.

        Args:
            user_id: User whose risk score exceeded threshold.
            risk_assessment: Risk assessment data.

        Returns:
            Created alert dictionary, or None if risk level is below threshold.
        """
        level = risk_assessment.get("risk_level", "low")

        # Only alert for high and critical risk levels
        if level not in ("high", "critical"):
            return None

        alert_data = AlertData(
            user_id=user_id,
            alert_type="risk_threshold",
            title=f"Risk Score: {level.upper()} ({risk_assessment.get('score', 0):.1f}/100)",
            description=(
                f"User risk score has reached {level.upper} level. "
                f"Immediate attention recommended."
            ),
            severity=level,
            priority="high" if level == "critical" else "medium",
            risk_score=risk_assessment.get("score", 0),
            explanation=risk_assessment.get("explanation", ""),
            recommended_action="\n".join(
                risk_assessment.get("recommended_actions", [])[:3]
            ),
            source="risk_engine",
            metadata={
                "risk_factors": [
                    {"name": f.get("name", ""), "points": f.get("risk_points", 0)}
                    for f in risk_assessment.get("factors", [])
                ]
            },
        )

        return self.create_alert(alert_data)

    def _calculate_priority(self, severity: str, risk_score: float) -> str:
        """Calculate alert priority from severity and risk score."""
        if severity == "critical" or risk_score >= 80:
            return "critical"
        elif severity == "high" or risk_score >= 60:
            return "high"
        elif severity == "medium" or risk_score >= 40:
            return "medium"
        return "low"

    def _get_rule_action(self, rule_name: str) -> str:
        """Get recommended action for a specific rule violation."""
        actions = {
            "midnight_login": "Verify if after-hours access was authorized",
            "multiple_failed_logins": "Check for brute force attack indicators",
            "usb_device_usage": "Verify USB usage is authorized per policy",
            "database_export": "Review export scope and business justification",
            "privilege_escalation": "Investigate immediately - verify authorization",
            "large_file_download": "Review file content and download authorization",
            "security_tool_disabled": "URGENT: Investigate security tool modification",
            "concurrent_sessions": "Check for session hijacking or shared credentials",
            "excessive_db_queries": "Review query patterns for data harvesting",
            "config_change": "Verify change was authorized and documented",
            "unusual_location": "Verify user identity and location legitimacy",
            "account_lockout": "Investigate failed login attempts for attack patterns",
        }
        return actions.get(rule_name, "Review the triggered event and take appropriate action")

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get aggregate alert statistics."""
        return {
            "total_rules": len(self.alert_templates),
            "alert_types": list(self.alert_templates.keys()),
        }


# Global alert engine instance
_alert_engine: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    """Get the global alert engine singleton."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine
