"""
Rule Engine Core
=================

Core rule execution engine that evaluates activities against a set of
predefined detection rules. Each rule defines conditions that, when
met, generate security alerts.

Rule Structure:
    Each rule has:
    - name: Unique identifier
    - description: Human-readable explanation
    - severity: Alert severity if triggered
    - conditions: Callable that evaluates the rule
    - cooldown: Minimum minutes between alerts for the same rule/user
    - explanation_template: Template for explainable AI output
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RuleSeverity(Enum):
    """Severity levels for rule-triggered alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleResult:
    """
    Result of evaluating a single rule.

    Attributes:
        rule_name: Name of the triggered rule
        triggered: Whether the rule was triggered
        severity: Severity level if triggered
        explanation: Human-readable explanation
        risk_contribution: Risk score points from this rule
        metadata: Additional context about the trigger
        triggered_at: Timestamp when the rule was triggered
    """
    rule_name: str
    triggered: bool
    severity: str = "info"
    explanation: str = ""
    risk_contribution: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    triggered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Rule:
    """
    Detection rule definition.

    Attributes:
        name: Unique rule identifier
        description: What this rule detects
        severity: Alert severity level
        risk_contribution: Risk score points when triggered
        cooldown_minutes: Minimum minutes between alerts per user
        category: Rule category for grouping
    """
    name: str
    description: str
    severity: RuleSeverity
    risk_contribution: float
    cooldown_minutes: int = 60
    category: str = "general"


class RuleEngine:
    """
    Rule-based threat detection engine.

    Maintains a collection of detection rules and evaluates them
    against incoming activity data. Tracks rule cooldowns to prevent
    alert fatigue from repeated triggers.
    """

    def __init__(self):
        """Initialize the rule engine with all detection rules."""
        self.rules: Dict[str, Rule] = {}
        self.cooldown_tracker: Dict[str, datetime] = {}
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register all default detection rules."""

        # Rule 1: Midnight Login
        self.register_rule(Rule(
            name="midnight_login",
            description="User logged in between midnight and 5 AM",
            severity=RuleSeverity.MEDIUM,
            risk_contribution=15.0,
            cooldown_minutes=120,
            category="temporal",
        ))

        # Rule 2: Multiple Failed Logins
        self.register_rule(Rule(
            name="multiple_failed_logins",
            description="More than 5 failed login attempts in a short period",
            severity=RuleSeverity.HIGH,
            risk_contribution=25.0,
            cooldown_minutes=30,
            category="security",
        ))

        # Rule 3: USB Device Usage
        self.register_rule(Rule(
            name="usb_device_usage",
            description="USB device connected or removed",
            severity=RuleSeverity.LOW,
            risk_contribution=10.0,
            cooldown_minutes=60,
            category="data_loss",
        ))

        # Rule 4: Database Export
        self.register_rule(Rule(
            name="database_export",
            description="Database export or bulk data extraction detected",
            severity=RuleSeverity.HIGH,
            risk_contribution=30.0,
            cooldown_minutes=60,
            category="data_loss",
        ))

        # Rule 5: Privilege Escalation
        self.register_rule(Rule(
            name="privilege_escalation",
            description="Attempt to escalate privileges or access restricted resources",
            severity=RuleSeverity.CRITICAL,
            risk_contribution=40.0,
            cooldown_minutes=15,
            category="privilege",
        ))

        # Rule 6: Large File Download
        self.register_rule(Rule(
            name="large_file_download",
            description="Download of file larger than 100MB detected",
            severity=RuleSeverity.MEDIUM,
            risk_contribution=20.0,
            cooldown_minutes=60,
            category="data_loss",
        ))

        # Rule 7: Antivirus/System Security Disabled
        self.register_rule(Rule(
            name="security_tool_disabled",
            description="Security tool or antivirus disabled by user",
            severity=RuleSeverity.CRITICAL,
            risk_contribution=40.0,
            cooldown_minutes=15,
            category="security",
        ))

        # Rule 8: Unusual Location Login
        self.register_rule(Rule(
            name="unusual_location",
            description="Login from unusual geographic location",
            severity=RuleSeverity.MEDIUM,
            risk_contribution=15.0,
            cooldown_minutes=120,
            category="temporal",
        ))

        # Rule 9: Excessive Database Queries
        self.register_rule(Rule(
            name="excessive_db_queries",
            description="More than 50 database queries in a single session",
            severity=RuleSeverity.MEDIUM,
            risk_contribution=20.0,
            cooldown_minutes=60,
            category="volume",
        ))

        # Rule 10: Account Lockout
        self.register_rule(Rule(
            name="account_lockout",
            description="Account locked due to too many failed attempts",
            severity=RuleSeverity.HIGH,
            risk_contribution=30.0,
            cooldown_minutes=30,
            category="security",
        ))

        # Rule 11: Configuration Change
        self.register_rule(Rule(
            name="config_change",
            description="System configuration change detected",
            severity=RuleSeverity.MEDIUM,
            risk_contribution=15.0,
            cooldown_minutes=60,
            category="compliance",
        ))

        # Rule 12: Concurrent Sessions from Different Locations
        self.register_rule(Rule(
            name="concurrent_sessions",
            description="Active sessions from geographically distant locations",
            severity=RuleSeverity.HIGH,
            risk_contribution=25.0,
            cooldown_minutes=30,
            category="security",
        ))

        logger.info(f"Registered {len(self.rules)} detection rules")

    def register_rule(self, rule: Rule) -> None:
        """Register a new detection rule."""
        self.rules[rule.name] = rule

    def _check_cooldown(self, rule_name: str, user_id: str) -> bool:
        """
        Check if a rule is in cooldown for a specific user.

        Args:
            rule_name: Name of the rule to check.
            user_id: User to check the cooldown for.

        Returns:
            True if the rule is in cooldown (should NOT trigger), False otherwise.
        """
        cooldown_key = f"{rule_name}:{user_id}"
        last_triggered = self.cooldown_tracker.get(cooldown_key)

        if last_triggered is None:
            return False

        rule = self.rules.get(rule_name)
        if rule is None:
            return False

        cooldown_end = last_triggered + timedelta(minutes=rule.cooldown_minutes)
        return datetime.utcnow() < cooldown_end

    def _set_cooldown(self, rule_name: str, user_id: str) -> None:
        """Set the cooldown timestamp for a rule/user combination."""
        cooldown_key = f"{rule_name}:{user_id}"
        self.cooldown_tracker[cooldown_key] = datetime.utcnow()

    def evaluate_activity(
        self, activity: Dict[str, Any], user_context: Dict[str, Any]
    ) -> List[RuleResult]:
        """
        Evaluate a single activity against all registered rules.

        Args:
            activity: Activity data dictionary.
            user_context: User context (baseline, session info, etc.).

        Returns:
            List of RuleResult for any triggered rules.
        """
        results = []

        for rule_name, rule in self.rules.items():
            # Check cooldown
            user_id = activity.get("user_id", "unknown")
            if self._check_cooldown(rule_name, user_id):
                continue

            # Evaluate the rule
            triggered, explanation, metadata = self._evaluate_rule(
                rule, activity, user_context
            )

            if triggered:
                # Set cooldown
                self._set_cooldown(rule_name, user_id)

                result = RuleResult(
                    rule_name=rule_name,
                    triggered=True,
                    severity=rule.severity.value,
                    explanation=explanation,
                    risk_contribution=rule.risk_contribution,
                    metadata=metadata,
                )
                results.append(result)

                logger.warning(
                    f"Rule triggered: {rule_name} for user {user_id} "
                    f"(severity: {rule.severity.value})"
                )

        return results

    def _evaluate_rule(
        self,
        rule: Rule,
        activity: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        Evaluate a single rule against an activity.

        Returns:
            Tuple of (triggered, explanation, metadata).
        """
        activity_type = activity.get("activity_type", "")
        timestamp = activity.get("created_at", datetime.utcnow())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        metadata = {
            "rule_name": rule.name,
            "activity_type": activity_type,
            "activity_id": activity.get("id"),
        }

        if rule.name == "midnight_login":
            if activity_type == "login":
                hour = timestamp.hour if isinstance(timestamp, datetime) else 0
                if 0 <= hour < 5:
                    return (
                        True,
                        f"Login detected at {timestamp.strftime('%H:%M')} which is "
                        f"outside normal business hours. This could indicate "
                        f"unauthorized access or compromised credentials.",
                        metadata
                    )

        elif rule.name == "multiple_failed_logins":
            if activity_type == "login" and activity.get("status") == "failure":
                failed_count = user_context.get("recent_failed_logins", 0) + 1
                if failed_count >= 5:
                    return (
                        True,
                        f"Detected {failed_count} consecutive failed login attempts. "
                        f"This pattern is consistent with a brute force attack "
                        f"or credential stuffing attempt.",
                        {**metadata, "failed_count": failed_count}
                    )

        elif rule.name == "usb_device_usage":
            if activity_type in ("usb_insertion", "usb_removal"):
                return (
                    True,
                    f"USB device {activity_type.replace('usb_', '')} detected. "
                    f"USB devices can be used for unauthorized data exfiltration "
                    f"or malware introduction.",
                    {**metadata, "usb_action": activity_type}
                )

        elif rule.name == "database_export":
            if activity_type == "database_export":
                return (
                    True,
                    "Database export operation detected. Bulk data extraction "
                    "may indicate data theft or policy violation. Review the "
                    "export scope and business justification.",
                    {**metadata, "export_details": activity.get("description", "")}
                )

        elif rule.name == "privilege_escalation":
            if activity_type == "privilege_escalation":
                return (
                    True,
                    "Privilege escalation attempt detected. A user is attempting "
                    "to gain access beyond their authorized permissions. This is "
                    "a critical security event requiring immediate investigation.",
                    metadata
                )

        elif rule.name == "large_file_download":
            if activity_type == "file_download":
                # Parse file size from metadata if available
                meta = activity.get("metadata_json", {})
                file_size_mb = meta.get("file_size_mb", 0)
                if file_size_mb > 100:
                    return (
                        True,
                        f"Large file download detected ({file_size_mb} MB). "
                        f"Unusually large downloads may indicate data exfiltration.",
                        {**metadata, "file_size_mb": file_size_mb}
                    )

        elif rule.name == "security_tool_disabled":
            if activity_type == "admin_command":
                desc = activity.get("description", "").lower()
                if "antivirus" in desc or "disable" in desc or "firewall" in desc:
                    return (
                        True,
                        "Security tool modification detected. Disabling or "
                        "modifying security controls is a critical policy "
                        "violation that may indicate an active threat.",
                        metadata
                    )

        elif rule.name == "excessive_db_queries":
            if activity_type == "database_access":
                db_count = user_context.get("session_db_queries", 0) + 1
                if db_count > 50:
                    return (
                        True,
                        f"Excessive database queries detected ({db_count} in session). "
                        f"This volume is significantly above normal and may indicate "
                        f"data harvesting or unauthorized bulk access.",
                        {**metadata, "query_count": db_count}
                    )

        elif rule.name == "config_change":
            if activity_type == "config_change":
                return (
                    True,
                    "System configuration change detected. Unauthorized "
                    "configuration modifications can create security "
                    "vulnerabilities or disable protective controls.",
                    {**metadata, "change_details": activity.get("description", "")}
                )

        return False, "", metadata

    def evaluate_batch(
        self,
        activities: List[Dict[str, Any]],
        user_context: Dict[str, Any],
    ) -> List[RuleResult]:
        """
        Evaluate a batch of activities against all rules.

        Args:
            activities: List of activity data dictionaries.
            user_context: User context information.

        Returns:
            List of all triggered RuleResults.
        """
        all_results = []
        for activity in activities:
            results = self.evaluate_activity(activity, user_context)
            all_results.extend(results)
        return all_results

    def get_rule_summary(self) -> Dict[str, Any]:
        """Get a summary of all registered rules."""
        return {
            "total_rules": len(self.rules),
            "rules_by_category": {},
            "rules_by_severity": {},
        }


# Global rule engine instance
_rule_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """Get the global rule engine singleton."""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
