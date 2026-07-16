"""
Feature Engineering Module
============================

Transforms raw activity data into numerical feature vectors suitable
for machine learning model training and inference.

Feature Categories:
    1. Temporal Features: Login hour, session duration, activity timing
    2. Volume Features: Activity counts, query counts, download sizes
    3. Behavioral Features: Activity type distribution, uniqueness
    4. Contextual Features: Device changes, location changes, IP patterns
    5. Risk Features: Failed logins, access denials, sensitive operations

The feature engineering pipeline converts raw activity logs into a
fixed-size feature vector per user per time window. This vector
captures the behavioral fingerprint of the user for that period.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering pipeline for behavioral analytics.

    Transforms raw activity data into numerical features that capture
    user behavior patterns for anomaly detection.
    """

    # Activity types that carry security significance
    SENSITIVE_ACTIVITIES = {
        "database_export", "privilege_escalation", "admin_command",
        "config_change", "usb_insertion",
    }

    # Normal working hours for the banking environment
    WORK_START_HOUR = 7
    WORK_END_HOUR = 20

    def __init__(self, window_hours: int = 24):
        """
        Initialize the feature engineer.

        Args:
            window_hours: Time window in hours for feature aggregation.
                         Default is 24 hours (daily feature vectors).
        """
        self.window_hours = window_hours
        self.feature_names = []
        self._compute_feature_names()

    def _compute_feature_names(self) -> None:
        """
        Compute the list of feature names for the feature vector.
        These names are used for model interpretability and debugging.
        """
        self.feature_names = [
            # Temporal features (7)
            "login_hour",
            "logout_hour",
            "session_duration_minutes",
            "is_weekend",
            "is_after_hours",
            "activity_count",
            "unique_activity_types",

            # Volume features (8)
            "database_query_count",
            "database_export_count",
            "file_download_count",
            "file_upload_count",
            "email_count",
            "admin_command_count",
            "total_data_access",

            # Security features (7)
            "failed_login_count",
            "access_denied_count",
            "sensitive_activity_count",
            "usb_event_count",
            "password_change_count",
            "privilege_escalation_count",
            "config_change_count",

            # Behavioral features (6)
            "activity_diversity",
            "unique_ips",
            "unique_devices",
            "unique_locations",
            "new_device_used",
            "new_location_used",

            # Risk features (4)
            "after_hours_ratio",
            "sensitive_ratio",
            "error_ratio",
            "risk_contribution_sum",

            # Derived features (3)
            "hour_sin",
            "hour_cos",
            "activity_intensity",
        ]

    def extract_features(self, activities: pd.DataFrame) -> pd.DataFrame:
        """
        Extract feature vectors from raw activity data.

        Groups activities by user and time window, then computes
        feature vectors for each (user, window) combination.

        Args:
            activities: DataFrame with columns [user_id, activity_type,
                       created_at, status, ip_address, device_id, location,
                       severity, risk_contribution].

        Returns:
            DataFrame with one row per (user, window) and columns for each feature.
        """
        if activities.empty:
            logger.warning("Empty activities DataFrame provided")
            return pd.DataFrame(columns=self.feature_names + ["user_id", "window_start"])

        # Ensure datetime column
        activities = activities.copy()
        activities["created_at"] = pd.to_datetime(activities["created_at"])

        # Create time windows
        activities["window_start"] = activities["created_at"].dt.floor(f"{self.window_hours}H")

        # Get baseline data for new device/location detection
        baseline = self._compute_baseline(activities)

        # Group by user and time window
        feature_records = []

        for (user_id, window_start), group in activities.groupby(["user_id", "window_start"]):
            features = self._compute_window_features(group, baseline)
            features["user_id"] = user_id
            features["window_start"] = window_start
            feature_records.append(features)

        df = pd.DataFrame(feature_records)
        logger.info(f"Extracted {len(df)} feature vectors from {len(activities)} activities")
        return df

    def _compute_baseline(self, activities: pd.DataFrame) -> Dict:
        """
        Compute baseline statistics for each user.

        The baseline is used to detect deviations from normal behavior,
        such as new devices or unusual locations.

        Args:
            activities: Full activity history DataFrame.

        Returns:
            Dictionary mapping user_id to their baseline statistics.
        """
        baseline = {}
        for user_id, user_activities in activities.groupby("user_id"):
            baseline[user_id] = {
                "known_devices": set(user_activities["device_id"].dropna().unique()),
                "known_locations": set(user_activities["location"].dropna().unique()),
                "known_ips": set(user_activities["ip_address"].dropna().unique()),
                "typical_hour_mean": user_activities["created_at"].dt.hour.mean(),
            }
        return baseline

    def _compute_window_features(
        self, group: pd.DataFrame, baseline: Dict
    ) -> Dict[str, float]:
        """
        Compute features for a single (user, window) group of activities.

        Args:
            group: DataFrame slice for one user and time window.
            baseline: Baseline statistics for all users.

        Returns:
            Dictionary of feature name to feature value.
        """
        user_id = group["user_id"].iloc[0]
        user_baseline = baseline.get(user_id, {})

        features = {}

        # ===== Temporal Features =====
        hours = group["created_at"].dt.hour
        features["login_hour"] = hours.min()
        features["logout_hour"] = hours.max()

        # Session duration estimate
        if len(group) > 1:
            time_span = (group["created_at"].max() - group["created_at"].min()).total_seconds() / 60
        else:
            time_span = 0
        features["session_duration_minutes"] = time_span

        features["is_weekend"] = float(group["created_at"].dt.dayofweek.iloc[0] >= 5)
        features["is_after_hours"] = float(
            (hours < self.WORK_START_HOUR).any() or (hours > self.WORK_END_HOUR).any()
        )
        features["activity_count"] = len(group)
        features["unique_activity_types"] = group["activity_type"].nunique()

        # ===== Volume Features =====
        activity_counts = group["activity_type"].value_counts()
        features["database_query_count"] = activity_counts.get("database_access", 0)
        features["database_export_count"] = activity_counts.get("database_export", 0)
        features["file_download_count"] = activity_counts.get("file_download", 0)
        features["file_upload_count"] = activity_counts.get("file_upload", 0)
        features["email_count"] = (
            activity_counts.get("email_send", 0) +
            activity_counts.get("email_receive", 0)
        )
        features["admin_command_count"] = activity_counts.get("admin_command", 0)
        features["total_data_access"] = (
            features["database_query_count"] +
            features["database_export_count"] +
            features["file_download_count"] +
            features["file_upload_count"]
        )

        # ===== Security Features =====
        features["failed_login_count"] = int(
            (group["activity_type"] == "login") & (group["status"] == "failure")
        )
        features["access_denied_count"] = int(
            (group["activity_type"] == "access_denied")
        )
        features["sensitive_activity_count"] = int(
            group["activity_type"].isin(self.SENSITIVE_ACTIVITIES).sum()
        )
        features["usb_event_count"] = int(
            group["activity_type"].isin(["usb_insertion", "usb_removal"]).sum()
        )
        features["password_change_count"] = int(
            (group["activity_type"] == "password_change").sum()
        )
        features["privilege_escalation_count"] = int(
            (group["activity_type"] == "privilege_escalation").sum()
        )
        features["config_change_count"] = int(
            (group["activity_type"] == "config_change").sum()
        )

        # ===== Behavioral Features =====
        features["activity_diversity"] = (
            len(activity_counts) / len(ACTIVITY_TYPES) if ACTIVITY_TYPES else 0
        )
        features["unique_ips"] = group["ip_address"].nunique()
        features["unique_devices"] = group["device_id"].nunique()
        features["unique_locations"] = group["location"].nunique()

        # Check for new devices and locations
        known_devices = user_baseline.get("known_devices", set())
        known_locations = user_baseline.get("known_locations", set())
        current_devices = set(group["device_id"].dropna().unique())
        current_locations = set(group["location"].dropna().unique())

        features["new_device_used"] = float(
            len(current_devices - known_devices) > 0
        )
        features["new_location_used"] = float(
            len(current_locations - known_locations) > 0
        )

        # ===== Risk Features =====
        total = max(len(group), 1)
        features["after_hours_ratio"] = features["is_after_hours"]
        features["sensitive_ratio"] = features["sensitive_activity_count"] / total
        features["error_ratio"] = (
            features["failed_login_count"] + features["access_denied_count"]
        ) / total
        features["risk_contribution_sum"] = group["risk_contribution"].sum()

        # ===== Derived Features =====
        avg_hour = hours.mean() if len(hours) > 0 else 12
        features["hour_sin"] = np.sin(2 * np.pi * avg_hour / 24)
        features["hour_cos"] = np.cos(2 * np.pi * avg_hour / 24)
        features["activity_intensity"] = features["activity_count"] / max(time_span / 60, 1)

        return features

    def get_feature_names(self) -> List[str]:
        """Get the list of feature names for the feature vector."""
        return self.feature_names.copy()

    def extract_single_window_features(
        self,
        activities: List[Dict],
        user_baseline: Optional[Dict] = None,
    ) -> np.ndarray:
        """
        Extract features from a single time window for real-time inference.

        This is used during live monitoring to compute features for
        the current activity window and feed them to the ML models.

        Args:
            activities: List of activity dictionaries in the current window.
            user_baseline: Optional baseline for the user.

        Returns:
            numpy array of shape (1, n_features) ready for model input.
        """
        if not activities:
            return np.zeros((1, len(self.feature_names)))

        df = pd.DataFrame(activities)
        df["created_at"] = pd.to_datetime(df["created_at"])

        baseline = {activities[0].get("user_id", "unknown"): user_baseline} if user_baseline else {}
        features = self._compute_window_features(df, baseline)

        # Return as numpy array in the correct feature order
        feature_vector = np.array([features.get(name, 0.0) for name in self.feature_names])
        return feature_vector.reshape(1, -1)


# Global activity types reference (used in feature_diversity calculation)
ACTIVITY_TYPES = [
    "login", "logout", "database_access", "database_export",
    "file_download", "file_upload", "usb_insertion", "usb_removal",
    "password_change", "config_change", "email_send", "email_receive",
    "admin_command", "privilege_escalation", "access_denied",
]
