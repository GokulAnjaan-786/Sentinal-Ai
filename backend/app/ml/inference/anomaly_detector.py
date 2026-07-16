"""
ML Inference Module
====================

Provides real-time anomaly inference using trained ML models.

This module is used by the activity monitoring service to score
incoming activities in real-time. It loads the trained models and
feature engineering pipeline to generate anomaly scores and explanations.

Inference Pipeline:
    1. Receive new activity data
    2. Extract features using the feature engineer
    3. Scale features using the saved scaler
    4. Score with Isolation Forest and/or LOF
    5. Combine scores and generate explanation
    6. Return anomaly score and explanation
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.core.config import settings
from app.ml.features.engineer import FeatureEngineer

logger = logging.getLogger(__name__)


class AnomalyInference:
    """
    Real-time anomaly inference engine.

    Loads trained models and provides prediction capabilities
    for incoming activity data.
    """

    def __init__(self):
        """Initialize the inference engine."""
        self.isolation_forest = None
        self.local_outlier_factor = None
        self.scaler = None
        self.feature_engineer = FeatureEngineer(window_hours=24)
        self.feature_names = self.feature_engineer.get_feature_names()
        self.is_loaded = False
        self.model_version = "1.0.0"

    def load_models(self) -> bool:
        """
        Load trained models from disk for inference.

        Returns:
            True if models loaded successfully, False otherwise.
        """
        import os
        import pickle
        import json

        model_dir = settings.ML_MODEL_PATH

        try:
            # Load Isolation Forest
            if_path = os.path.join(model_dir, "isolation_forest.pkl")
            if os.path.exists(if_path):
                with open(if_path, "rb") as f:
                    self.isolation_forest = pickle.load(f)
                logger.info("Loaded Isolation Forest for inference")

            # Load Local Outlier Factor
            lof_path = os.path.join(model_dir, "local_outlier_factor.pkl")
            if os.path.exists(lof_path):
                with open(lof_path, "rb") as f:
                    self.local_outlier_factor = pickle.load(f)
                logger.info("Loaded Local Outlier Factor for inference")

            # Load scaler
            scaler_path = os.path.join(model_dir, "scaler.pkl")
            if os.path.exists(scaler_path):
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded feature scaler")

            # Load metadata
            report_path = os.path.join(model_dir, "training_report.json")
            if os.path.exists(report_path):
                with open(report_path, "r") as f:
                    metadata = json.load(f)
                self.model_version = metadata.get("training_timestamp", "unknown")

            self.is_loaded = (
                self.isolation_forest is not None or
                self.local_outlier_factor is not None
            )

            if self.is_loaded:
                logger.info(f"Inference engine ready (model version: {self.model_version})")
            else:
                logger.warning("No trained models found for inference")

            return self.is_loaded

        except Exception as e:
            logger.error(f"Error loading models for inference: {str(e)}")
            return False

    def predict(
        self, activities: List[Dict], user_baseline: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Generate anomaly prediction for a set of activities.

        This is the main inference method used by the activity monitoring
        service to score incoming activity batches.

        Args:
            activities: List of activity dictionaries in the current window.
            user_baseline: Optional baseline data for the user.

        Returns:
            Dictionary containing:
                - anomaly_score: Float from -1 (normal) to 1 (anomalous)
                - is_anomaly: Boolean flag
                - risk_level: Categorical risk level
                - explanation: Human-readable explanation
                - contributing_features: List of features driving the score
                - model_used: Name of the model that produced the prediction
        """
        if not self.is_loaded:
            return self._fallback_prediction(activities)

        try:
            # Extract features
            X = self.feature_engineer.extract_single_window_features(
                activities, user_baseline
            )

            if X.size == 0:
                return self._fallback_prediction(activities)

            # Scale features
            if self.scaler is not None:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X

            # Get predictions from available models
            scores = {}
            predictions = {}

            if self.isolation_forest is not None:
                raw_score = self.isolation_forest.decision_function(X_scaled)[0]
                raw_pred = self.isolation_forest.predict(X_scaled)[0]
                # Normalize: lower decision_function score = more anomalous
                scores["isolation_forest"] = -raw_score
                predictions["isolation_forest"] = raw_pred == -1

            if self.local_outlier_factor is not None:
                raw_score = self.local_outlier_factor.decision_function(X_scaled)[0]
                raw_pred = self.local_outlier_factor.predict(X_scaled)[0]
                scores["local_outlier_factor"] = -raw_score
                predictions["local_outlier_factor"] = raw_pred == -1

            # Combine scores (ensemble approach)
            if scores:
                combined_score = np.mean(list(scores.values()))
                is_anomaly = any(predictions.values())
                model_used = "+".join(scores.keys())
            else:
                return self._fallback_prediction(activities)

            # Normalize score to [-1, 1] range
            combined_score = float(np.clip(combined_score, -1, 1))

            # Determine risk level from score
            risk_level = self._score_to_risk_level(combined_score)

            # Generate explanation
            explanation = self._generate_explanation(
                X[0], combined_score, is_anomaly, activities
            )

            # Identify contributing features
            contributing_features = self._identify_contributing_features(X[0])

            return {
                "anomaly_score": combined_score,
                "is_anomaly": is_anomaly,
                "risk_level": risk_level,
                "explanation": explanation,
                "contributing_features": contributing_features,
                "model_used": model_used,
                "model_version": self.model_version,
                "confidence": abs(combined_score),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            return self._fallback_prediction(activities)

    def _score_to_risk_level(self, score: float) -> str:
        """
        Convert a numerical anomaly score to a categorical risk level.

        Args:
            score: Anomaly score from -1 (normal) to 1 (anomalous).

        Returns:
            Risk level string: low, medium, high, or critical.
        """
        # Normalize score from [-1, 1] to [0, 1]
        normalized = (score + 1) / 2

        if normalized < 0.3:
            return "low"
        elif normalized < 0.5:
            return "medium"
        elif normalized < 0.7:
            return "high"
        else:
            return "critical"

    def _generate_explanation(
        self,
        features: np.ndarray,
        score: float,
        is_anomaly: bool,
        activities: List[Dict],
    ) -> str:
        """
        Generate a human-readable explanation of the anomaly score.

        This implements Explainable AI (XAI) by translating the numerical
        score and feature values into natural language that SOC analysts
        can understand and act upon.

        Args:
            features: Feature vector for the current window.
            score: Combined anomaly score.
            is_anomaly: Whether the sample is flagged as anomalous.
            activities: Original activity data.

        Returns:
            Human-readable explanation string.
        """
        explanations = []

        if is_anomaly:
            explanations.append(
                f"Anomalous behavior detected (anomaly score: {score:.3f})."
            )
        else:
            explanations.append(
                f"Behavior appears normal (anomaly score: {score:.3f})."
            )

        # Analyze specific feature values
        feature_dict = dict(zip(self.feature_names, features))

        # After-hours activity
        if feature_dict.get("is_after_hours", 0) > 0.5:
            explanations.append(
                "Activity was detected outside normal working hours."
            )

        # Failed logins
        failed = feature_dict.get("failed_login_count", 0)
        if failed > 3:
            explanations.append(
                f"Multiple failed login attempts detected ({int(failed)}). "
                "This may indicate a brute force attack or compromised credentials."
            )

        # Sensitive activities
        sensitive = feature_dict.get("sensitive_activity_count", 0)
        if sensitive > 3:
            explanations.append(
                f"Unusually high number of sensitive operations ({int(sensitive)}). "
                "This includes database exports, admin commands, or privilege changes."
            )

        # Device/location changes
        if feature_dict.get("new_device_used", 0) > 0.5:
            explanations.append(
                "Activity from a new or unrecognized device was detected."
            )
        if feature_dict.get("new_location_used", 0) > 0.5:
            explanations.append(
                "Activity from an unusual geographic location was detected."
            )

        # High activity volume
        activity_count = feature_dict.get("activity_count", 0)
        if activity_count > 80:
            explanations.append(
                f"Abnormally high activity volume ({int(activity_count)} actions). "
                "This is significantly above the user's normal baseline."
            )

        # Database export
        db_exports = feature_dict.get("database_export_count", 0)
        if db_exports > 0:
            explanations.append(
                f"Database export operation(s) detected ({int(db_exports)}). "
                "Large data exports may indicate data exfiltration."
            )

        # USB usage
        usb = feature_dict.get("usb_event_count", 0)
        if usb > 1:
            explanations.append(
                f"USB device activity detected ({int(usb)} events). "
                "USB devices can be used for unauthorized data transfer."
            )

        # Risk contribution
        risk_sum = feature_dict.get("risk_contribution_sum", 0)
        if risk_sum > 50:
            explanations.append(
                f"High cumulative risk contribution ({risk_sum:.1f}). "
                "Multiple risk factors are present in this session."
            )

        return " ".join(explanations)

    def _identify_contributing_features(
        self, features: np.ndarray, top_n: int = 5
    ) -> List[Dict[str, any]]:
        """
        Identify the top features contributing to the anomaly score.

        Uses a simple feature importance analysis based on the feature
        values relative to typical ranges.

        Args:
            features: Feature vector for the current sample.
            top_n: Number of top contributing features to return.

        Returns:
            List of dictionaries with feature name, value, and contribution.
        """
        feature_dict = dict(zip(self.feature_names, features))

        # Features that indicate risk when high
        risk_features = [
            "failed_login_count", "sensitive_activity_count", "access_denied_count",
            "database_export_count", "admin_command_count", "privilege_escalation_count",
            "usb_event_count", "config_change_count", "unique_ips", "unique_devices",
            "unique_locations", "new_device_used", "new_location_used",
            "after_hours_ratio", "error_ratio", "risk_contribution_sum",
            "activity_count", "is_after_hours",
        ]

        contributions = []
        for fname in risk_features:
            if fname in feature_dict:
                value = float(feature_dict[fname])
                # Simple contribution: value normalized by a reasonable threshold
                if fname.endswith("_count"):
                    threshold = 10.0
                elif fname.endswith("_ratio") or fname in ("new_device_used", "new_location_used", "is_after_hours"):
                    threshold = 1.0
                else:
                    threshold = 50.0

                contribution = min(value / threshold, 1.0) if threshold > 0 else 0
                if contribution > 0.1:  # Only include meaningful contributions
                    contributions.append({
                        "feature": fname,
                        "value": value,
                        "contribution": round(contribution, 3),
                        "description": self._feature_description(fname, value),
                    })

        # Sort by contribution and return top N
        contributions.sort(key=lambda x: x["contribution"], reverse=True)
        return contributions[:top_n]

    def _feature_description(self, feature_name: str, value: float) -> str:
        """Generate a human-readable description for a feature."""
        descriptions = {
            "failed_login_count": f"{int(value)} failed login attempts",
            "sensitive_activity_count": f"{int(value)} sensitive operations performed",
            "access_denied_count": f"{int(value)} access denied events",
            "database_export_count": f"{int(value)} database export operations",
            "admin_command_count": f"{int(value)} administrative commands executed",
            "privilege_escalation_count": f"{int(value)} privilege escalation attempts",
            "usb_event_count": f"{int(value)} USB device events",
            "config_change_count": f"{int(value)} configuration changes",
            "unique_ips": f"Accessed from {int(value)} different IP addresses",
            "unique_devices": f"Used {int(value)} different devices",
            "unique_locations": f"Connected from {int(value)} different locations",
            "new_device_used": "New/unrecognized device used" if value > 0.5 else "Known device",
            "new_location_used": "Unusual location detected" if value > 0.5 else "Normal location",
            "after_hours_ratio": "After-hours activity detected" if value > 0.5 else "Normal hours",
            "error_ratio": f"Error rate: {value*100:.0f}%",
            "risk_contribution_sum": f"Cumulative risk: {value:.1f}",
            "activity_count": f"{int(value)} total activities",
            "is_after_hours": "Activity outside business hours" if value > 0.5 else "",
        }
        return descriptions.get(feature_name, f"{feature_name}: {value:.2f}")

    def _fallback_prediction(self, activities: List[Dict]) -> Dict[str, any]:
        """
        Fallback prediction when ML models are not available.

        Uses simple rule-based scoring when the ML models have not
        been trained or loaded. This ensures the system always provides
        some level of threat detection.
        """
        score = 0.0
        explanations = ["ML models not available. Using rule-based fallback scoring."]

        for activity in activities:
            atype = activity.get("activity_type", "")
            status = activity.get("status", "success")

            if atype == "failed_login" or status == "failure":
                score += 0.1
                explanations.append("Failed login attempt detected.")
            if atype in ("database_export", "privilege_escalation"):
                score += 0.2
                explanations.append(f"Sensitive activity: {atype}")
            if atype == "usb_insertion":
                score += 0.05
            if atype == "admin_command":
                score += 0.1

        score = min(score, 1.0)

        return {
            "anomaly_score": score,
            "is_anomaly": score > 0.3,
            "risk_level": self._score_to_risk_level(score),
            "explanation": " ".join(explanations),
            "contributing_features": [],
            "model_used": "rule_based_fallback",
            "model_version": "fallback",
            "confidence": 0.5,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global inference instance
_anomaly_inference: Optional[AnomalyInference] = None


def get_anomaly_inference() -> AnomalyInference:
    """
    Get the global anomaly inference singleton.

    Returns:
        AnomalyInference instance (creates if needed).
    """
    global _anomaly_inference
    if _anomaly_inference is None:
        _anomaly_inference = AnomalyInference()
        _anomaly_inference.load_models()
    return _anomaly_inference
