"""
Activity Monitor
=================

Real-time activity monitoring service that processes incoming user actions,
applies rule-based detection, feeds data to the ML engine, and coordinates
with the risk and alert engines.

This is the central coordinator that ties all detection components together:

    Activity -> Rule Engine -> Risk Engine -> Alert Engine -> Dashboard
         |
         +-> ML Engine -> Risk Engine -> Alert Engine -> Dashboard
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.rule_engine.engine import get_rule_engine
from app.risk_engine.engine import get_risk_engine
from app.alert_engine.engine import get_alert_engine
from app.ml.inference.anomaly_detector import get_anomaly_inference

logger = logging.getLogger(__name__)


class ActivityMonitor:
    """
    Central activity monitoring service.

    Processes each incoming activity through the complete detection pipeline:
    1. Record the activity
    2. Run rule engine checks
    3. Run ML anomaly detection
    4. Calculate risk score
    5. Generate alerts if needed
    6. Return comprehensive assessment
    """

    def __init__(self):
        """Initialize the activity monitor and its component engines."""
        self.rule_engine = get_rule_engine()
        self.risk_engine = get_risk_engine()
        self.alert_engine = get_alert_engine()
        self.ml_inference = get_anomaly_inference()
        self._session_contexts: Dict[str, Dict[str, Any]] = {}

    def process_activity(
        self,
        activity: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a single activity through the complete detection pipeline.

        This is the main entry point for real-time activity monitoring.

        Args:
            activity: Activity data dictionary with fields:
                - user_id, activity_type, ip_address, device_id, etc.
            user_context: Optional user context (baseline, session info).

        Returns:
            Complete processing result including:
            - activity_id: The recorded activity identifier
            - alerts: Any generated alerts
            - risk_assessment: Current risk assessment
            - anomaly_result: ML anomaly detection result
            - rule_results: Any triggered rules
        """
        user_id = activity.get("user_id", "unknown")
        activity_type = activity.get("activity_type", "unknown")

        logger.debug(f"Processing activity: {activity_type} for user {user_id}")

        result = {
            "activity_id": activity.get("id"),
            "user_id": user_id,
            "activity_type": activity_type,
            "alerts": [],
            "risk_assessment": None,
            "anomaly_result": None,
            "rule_results": [],
            "processed_at": datetime.utcnow().isoformat(),
        }

        # Update session context
        self._update_session_context(user_id, activity)

        # Get user context for detection
        if user_context is None:
            user_context = self._session_contexts.get(user_id, {})

        # Step 1: Run rule engine
        rule_results = self.rule_engine.evaluate_activity(activity, user_context)
        result["rule_results"] = [
            {
                "rule_name": r.rule_name,
                "triggered": r.triggered,
                "severity": r.severity,
                "explanation": r.explanation,
                "risk_contribution": r.risk_contribution,
            }
            for r in rule_results
        ]

        # Step 2: Create alerts for triggered rules
        for rule_result in rule_results:
            if rule_result.triggered:
                alert = self.alert_engine.create_rule_alert(
                    user_id=user_id,
                    rule_name=rule_result.rule_name,
                    rule_explanation=rule_result.explanation,
                    risk_score=0,  # Will be updated after risk calculation
                    metadata=rule_result.metadata,
                )
                result["alerts"].append(alert)

        # Step 3: Run ML anomaly detection
        activities_in_window = self._get_window_activities(user_id)
        if activities_in_window:
            anomaly_result = self.ml_inference.predict(
                activities_in_window, user_context
            )
            result["anomaly_result"] = anomaly_result

            # Create anomaly alert if needed
            if anomaly_result.get("is_anomaly", False):
                anomaly_alert = self.alert_engine.create_anomaly_alert(
                    user_id=user_id,
                    anomaly_data=anomaly_result,
                )
                result["alerts"].append(anomaly_alert)

        # Step 4: Calculate risk score
        rule_violations = [r.rule_name for r in rule_results if r.triggered]
        ml_score = (
            result["anomaly_result"].get("anomaly_score", 0)
            if result["anomaly_result"]
            else 0
        )

        risk_assessment = self.risk_engine.calculate_risk_score(
            user_id=user_id,
            ml_anomaly_score=ml_score,
            rule_violations=rule_violations,
            activity_context=self._build_context(activity, user_context),
        )
        result["risk_assessment"] = {
            "score": risk_assessment.score,
            "risk_level": risk_assessment.risk_level,
            "explanation": risk_assessment.explanation,
            "recommended_actions": risk_assessment.recommended_actions,
            "factors": [
                {
                    "name": f.name,
                    "description": f.description,
                    "risk_points": f.risk_points,
                }
                for f in risk_assessment.factors
            ],
        }

        # Step 5: Create risk threshold alert if needed
        risk_alert = self.alert_engine.create_risk_alert(
            user_id=user_id,
            risk_assessment={
                "score": risk_assessment.score,
                "risk_level": risk_assessment.risk_level,
                "explanation": risk_assessment.explanation,
                "recommended_actions": risk_assessment.recommended_actions,
                "factors": [
                    {"name": f.name, "risk_points": f.risk_points}
                    for f in risk_assessment.factors
                ],
            },
        )
        if risk_alert:
            result["alerts"].append(risk_alert)

        return result

    def process_batch(
        self,
        activities: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Process a batch of activities."""
        results = []
        for activity in activities:
            result = self.process_activity(activity, user_context)
            results.append(result)
        return results

    def _update_session_context(
        self, user_id: str, activity: Dict[str, Any]
    ) -> None:
        """Update the session context for a user."""
        if user_id not in self._session_contexts:
            self._session_contexts[user_id] = {
                "recent_failed_logins": 0,
                "session_db_queries": 0,
                "session_activities": 0,
                "session_start": datetime.utcnow().isoformat(),
            }

        ctx = self._session_contexts[user_id]
        ctx["session_activities"] += 1

        if activity.get("activity_type") == "login" and activity.get("status") == "failure":
            ctx["recent_failed_logins"] += 1
        elif activity.get("activity_type") == "login" and activity.get("status") == "success":
            ctx["recent_failed_logins"] = 0
            ctx["session_start"] = datetime.utcnow().isoformat()

        if activity.get("activity_type") in ("database_access", "database_export"):
            ctx["session_db_queries"] += 1

    def _get_window_activities(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent activities for the user in the current time window."""
        # In production, this would query the database
        # For now, return a minimal list
        return []

    def _build_context(
        self,
        activity: Dict[str, Any],
        user_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build context dictionary for risk assessment."""
        now = datetime.utcnow()
        context = {
            "hour": now.hour,
            "is_weekend": now.weekday() >= 5,
            "is_new_device": False,
            "is_new_location": False,
            "session_count": 1,
        }

        if user_context:
            context.update({
                "is_new_device": user_context.get("is_new_device", False),
                "is_new_location": user_context.get("is_new_location", False),
                "session_count": user_context.get("session_count", 1),
            })

        return context


# Global instance
_activity_monitor: Optional[ActivityMonitor] = None


def get_activity_monitor() -> ActivityMonitor:
    """Get the global activity monitor singleton."""
    global _activity_monitor
    if _activity_monitor is None:
        _activity_monitor = ActivityMonitor()
    return _activity_monitor
