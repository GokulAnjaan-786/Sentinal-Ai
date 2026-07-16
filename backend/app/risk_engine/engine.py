"""
Risk Score Engine
==================

Dynamic risk scoring engine that calculates real-time risk scores
for users based on multiple risk factors.

Risk Score Components:
    1. ML Anomaly Score (40% weight): Output from behavioral analytics
    2. Rule Violation Score (30% weight): Triggered rule penalties
    3. Context Score (20% weight): Device, location, time context
    4. Historical Score (10% weight): User's historical risk trend

Risk Score Ranges:
    0-25:   LOW     - Normal activity, routine monitoring
    26-50:  MEDIUM  - Minor anomalies, increased monitoring
    51-75:  HIGH    - Significant risk, investigation recommended
    76-100: CRITICAL - Immediate action required
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """
    A single contributing factor to a risk score.

    Attributes:
        name: Factor identifier
        description: Human-readable description
        weight: How much this factor contributes to the score
        value: Raw value of this factor
        normalized_value: Value normalized to 0-1 range
        risk_points: Actual risk points contributed
    """
    name: str
    description: str
    weight: float
    value: float
    normalized_value: float
    risk_points: float


@dataclass
class RiskAssessment:
    """
    Complete risk assessment for a user at a point in time.

    Attributes:
        user_id: User being assessed
        score: Final risk score (0-100)
        risk_level: Categorical risk level
        factors: List of contributing risk factors
        explanation: Human-readable explanation
        recommended_actions: Suggested response actions
        ml_anomaly_score: Raw ML anomaly score
        rule_violations_count: Number of triggered rules
        calculated_at: Assessment timestamp
    """
    user_id: str
    score: float
    risk_level: str
    factors: List[RiskFactor]
    explanation: str
    recommended_actions: List[str]
    ml_anomaly_score: float = 0.0
    rule_violations_count: int = 0
    calculated_at: datetime = field(default_factory=datetime.utcnow)


class RiskEngine:
    """
    Dynamic risk scoring engine.

    Combines signals from multiple sources (ML models, rule engine,
    user context, and historical data) to produce a comprehensive
    risk score for each user.
    """

    # Component weights (must sum to 1.0)
    WEIGHTS = {
        "ml_anomaly": 0.40,
        "rule_violations": 0.30,
        "context": 0.20,
        "historical": 0.10,
    }

    # Risk level thresholds
    THRESHOLDS = {
        "low": (0, 25),
        "medium": (26, 50),
        "high": (51, 75),
        "critical": (76, 100),
    }

    # Rule violation point mappings
    RULE_PENALTIES = {
        "midnight_login": 15,
        "multiple_failed_logins": 25,
        "usb_device_usage": 10,
        "database_export": 30,
        "privilege_escalation": 40,
        "large_file_download": 20,
        "security_tool_disabled": 40,
        "unusual_location": 15,
        "excessive_db_queries": 20,
        "account_lockout": 30,
        "config_change": 15,
        "concurrent_sessions": 25,
    }

    def __init__(self):
        """Initialize the risk engine."""
        self.user_history: Dict[str, List[float]] = {}

    def calculate_risk_score(
        self,
        user_id: str,
        ml_anomaly_score: float = 0.0,
        rule_violations: List[str] = None,
        activity_context: Dict[str, Any] = None,
        historical_score: Optional[float] = None,
    ) -> RiskAssessment:
        """
        Calculate the comprehensive risk score for a user.

        This is the main entry point for risk assessment. It combines
        all available signals into a single risk score.

        Args:
            user_id: UUID of the user to assess.
            ml_anomaly_score: Anomaly score from ML engine (-1 to 1).
            rule_violations: List of triggered rule names.
            activity_context: Current activity context data.
            historical_score: Previous risk score for trend analysis.

        Returns:
            Complete RiskAssessment with score, level, factors, and explanation.
        """
        factors = []
        rule_violations = rule_violations or []
        activity_context = activity_context or {}

        # === Component 1: ML Anomaly Score ===
        ml_factor = self._compute_ml_factor(ml_anomaly_score)
        factors.append(ml_factor)

        # === Component 2: Rule Violations ===
        rule_factor = self._compute_rule_factor(rule_violations)
        factors.append(rule_factor)

        # === Component 3: Context Score ===
        context_factor = self._compute_context_factor(activity_context)
        factors.append(context_factor)

        # === Component 4: Historical Score ===
        historical_factor = self._compute_historical_factor(
            user_id, historical_score
        )
        factors.append(historical_factor)

        # Calculate weighted final score
        final_score = sum(f.risk_points for f in factors)
        final_score = float(np.clip(final_score, 0, 100))

        # Determine risk level
        risk_level = self._score_to_level(final_score)

        # Generate explanation
        explanation = self._generate_explanation(
            final_score, risk_level, factors, rule_violations
        )

        # Generate recommended actions
        actions = self._recommend_actions(risk_level, rule_violations, factors)

        # Update user history
        if user_id not in self.user_history:
            self.user_history[user_id] = []
        self.user_history[user_id].append(final_score)
        # Keep only last 100 scores
        self.user_history[user_id] = self.user_history[user_id][-100:]

        assessment = RiskAssessment(
            user_id=user_id,
            score=round(final_score, 2),
            risk_level=risk_level,
            factors=factors,
            explanation=explanation,
            recommended_actions=actions,
            ml_anomaly_score=ml_anomaly_score,
            rule_violations_count=len(rule_violations),
        )

        logger.info(
            f"Risk assessment for {user_id}: score={final_score:.1f}, "
            f"level={risk_level}, rules_triggered={len(rule_violations)}"
        )

        return assessment

    def _compute_ml_factor(self, ml_score: float) -> RiskFactor:
        """
        Convert ML anomaly score to risk points.

        The ML score ranges from -1 (very normal) to 1 (very anomalous).
        We map this to 0-40 risk points (the ML component's max contribution).
        """
        # Normalize from [-1, 1] to [0, 1]
        normalized = (ml_score + 1) / 2
        risk_points = normalized * 40.0 * self.WEIGHTS["ml_anomaly"] / 0.40

        description = (
            f"ML anomaly score: {ml_score:.3f}. "
        )
        if ml_score > 0.5:
            description += "Strong anomalous pattern detected by behavioral analytics."
        elif ml_score > 0.0:
            description += "Mild behavioral deviation detected."
        else:
            description += "Behavioral patterns appear normal."

        return RiskFactor(
            name="ml_anomaly",
            description=description,
            weight=self.WEIGHTS["ml_anomaly"],
            value=ml_score,
            normalized_value=normalized,
            risk_points=risk_points,
        )

    def _compute_rule_factor(self, rule_violations: List[str]) -> RiskFactor:
        """
        Calculate risk points from rule violations.

        Each rule contributes a specific number of risk points based
        on its severity. The total is capped at 30 points.
        """
        total_penalty = sum(
            self.RULE_PENALTIES.get(rule, 10) for rule in rule_violations
        )
        # Cap at 30 and normalize to the rule component's max contribution
        capped_penalty = min(total_penalty, 30)
        normalized = capped_penalty / 30.0
        risk_points = normalized * 30.0

        description = f"{len(rule_violations)} rule(s) violated"
        if rule_violations:
            description += f": {', '.join(rule_violations[:5])}"
            if len(rule_violations) > 5:
                description += f" (and {len(rule_violations) - 5} more)"

        return RiskFactor(
            name="rule_violations",
            description=description,
            weight=self.WEIGHTS["rule_violations"],
            value=float(len(rule_violations)),
            normalized_value=normalized,
            risk_points=risk_points,
        )

    def _compute_context_factor(self, context: Dict[str, Any]) -> RiskFactor:
        """
        Calculate risk points from contextual signals.

        Context includes:
        - Time of day (after-hours = higher risk)
        - Device trust (new device = higher risk)
        - Location (unusual location = higher risk)
        - Session behavior (unusual patterns = higher risk)
        """
        context_score = 0.0

        # After-hours check
        hour = context.get("hour", 12)
        if hour < 6 or hour > 22:
            context_score += 8.0
        elif hour < 7 or hour > 20:
            context_score += 3.0

        # New device
        if context.get("is_new_device", False):
            context_score += 7.0

        # New location
        if context.get("is_new_location", False):
            context_score += 6.0

        # Weekend
        if context.get("is_weekend", False):
            context_score += 3.0

        # Multiple concurrent sessions
        if context.get("session_count", 1) > 2:
            context_score += 5.0

        # Cap at 20
        context_score = min(context_score, 20.0)
        normalized = context_score / 20.0
        risk_points = context_score

        descriptions = []
        if hour < 6 or hour > 22:
            descriptions.append("after-hours access")
        if context.get("is_new_device", False):
            descriptions.append("new device")
        if context.get("is_new_location", False):
            descriptions.append("unusual location")
        if context.get("is_weekend", False):
            descriptions.append("weekend access")
        if context.get("session_count", 1) > 2:
            descriptions.append("multiple sessions")

        description = (
            f"Context signals: {', '.join(descriptions) if descriptions else 'all normal'}"
        )

        return RiskFactor(
            name="context",
            description=description,
            weight=self.WEIGHTS["context"],
            value=context_score,
            normalized_value=normalized,
            risk_points=risk_points,
        )

    def _compute_historical_factor(
        self, user_id: str, historical_score: Optional[float]
    ) -> RiskFactor:
        """
        Calculate risk points from historical trend.

        If the user has been trending upward in risk, this component
        adds additional risk points to account for persistent risk.
        """
        history = self.user_history.get(user_id, [])

        if historical_score is not None:
            # Use provided historical score
            trend_score = historical_score * 0.1  # Max 10 points
        elif len(history) >= 3:
            # Calculate trend from recent history
            recent = history[-10:]
            if len(recent) >= 2:
                trend = np.polyfit(range(len(recent)), recent, 1)[0]
                # Positive trend = increasing risk
                trend_score = max(0, trend * 2)
                trend_score = min(trend_score, 10.0)
            else:
                trend_score = recent[-1] * 0.1
        else:
            trend_score = 0.0

        normalized = trend_score / 10.0

        if trend_score > 5:
            description = "Risk trend is increasing over recent sessions."
        elif trend_score > 2:
            description = "Risk trend shows slight elevation."
        else:
            description = "Risk trend is stable or decreasing."

        return RiskFactor(
            name="historical_trend",
            description=description,
            weight=self.WEIGHTS["historical"],
            value=trend_score,
            normalized_value=normalized,
            risk_points=trend_score,
        )

    def _score_to_level(self, score: float) -> str:
        """Convert numerical score to categorical risk level."""
        for level, (low, high) in self.THRESHOLDS.items():
            if low <= score <= high:
                return level
        return "critical" if score > 100 else "low"

    def _generate_explanation(
        self,
        score: float,
        level: str,
        factors: List[RiskFactor],
        rule_violations: List[str],
    ) -> str:
        """Generate a comprehensive human-readable explanation."""
        parts = [
            f"Risk Score Assessment: {score:.1f}/100 ({level.upper()} risk level).",
            "",
            "Contributing Factors:",
        ]

        for factor in sorted(factors, key=lambda f: f.risk_points, reverse=True):
            parts.append(
                f"  - {factor.name}: {factor.description} "
                f"(+{factor.risk_points:.1f} points)"
            )

        if rule_violations:
            parts.append("")
            parts.append(
                f"Rule Violations: {len(rule_violations)} policy rule(s) triggered."
            )

        return " ".join(parts)

    def _recommend_actions(
        self,
        level: str,
        rule_violations: List[str],
        factors: List[RiskFactor],
    ) -> List[str]:
        """Generate recommended response actions based on risk assessment."""
        actions = []

        if level == "critical":
            actions.append("IMMEDIATE: Review user's current session and recent activities")
            actions.append("Consider suspending the user's active sessions")
            actions.append("Notify the SOC team lead and CISO")
            actions.append("Initiate incident response protocol")

        elif level == "high":
            actions.append("Priority: Investigate user's recent activities within 4 hours")
            actions.append("Review access logs for the past 24 hours")
            actions.append("Consider additional monitoring of the user's account")

        elif level == "medium":
            actions.append("Review user activity during next shift")
            actions.append("Verify recent access patterns against business justification")

        else:
            actions.append("Continue standard monitoring")

        # Rule-specific actions
        if "database_export" in rule_violations:
            actions.append("Review database export scope and authorization")
        if "privilege_escalation" in rule_violations:
            actions.append("Verify privilege escalation request was authorized")
        if "usb_device_usage" in rule_violations:
            actions.append("Verify USB device usage is authorized per data handling policy")
        if "security_tool_disabled" in rule_violations:
            actions.append("URGENT: Investigate security tool modification immediately")

        return actions

    def get_user_trend(self, user_id: str) -> Dict[str, Any]:
        """
        Get the risk score trend for a user.

        Args:
            user_id: User to get trend for.

        Returns:
            Dictionary with trend data.
        """
        history = self.user_history.get(user_id, [])
        if not history:
            return {"scores": [], "trend": "no_data"}

        scores = history[-30:]  # Last 30 scores
        if len(scores) >= 2:
            trend_slope = np.polyfit(range(len(scores)), scores, 1)[0]
            if trend_slope > 0.5:
                trend = "increasing"
            elif trend_slope < -0.5:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "scores": scores,
            "average": float(np.mean(scores)),
            "max": float(max(scores)),
            "min": float(min(scores)),
            "current": scores[-1],
            "trend": trend,
            "data_points": len(scores),
        }


# Global risk engine instance
_risk_engine: Optional[RiskEngine] = None


def get_risk_engine() -> RiskEngine:
    """Get the global risk engine singleton."""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
