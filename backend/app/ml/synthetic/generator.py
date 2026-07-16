"""
Synthetic Data Generator
==========================

Generates realistic synthetic activity data for ML model training.

In a real deployment, the ML models would be trained on historical
activity data from the production system. For development, testing,
and hackathon demonstrations, this module generates realistic synthetic
data that mimics real banking employee behavior patterns.

The generator creates:
    - Normal activity patterns (99% of data)
    - Anomalous activity patterns (1-5% of data)
    - Multiple user profiles with different behavioral patterns
    - Temporal patterns (work hours, after-hours, weekends)
    - Device and location patterns
    - Activity type distributions

Anomaly Types Simulated:
    - Unusual login times (midnight access)
    - Excessive database queries
    - Large file downloads
    - Multiple failed login attempts
    - USB device usage
    - Privilege escalation attempts
    - Access from unusual locations
"""

import random
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

"""
Configuration for synthetic data generation.
These parameters control the realism and characteristics of the generated data.
"""
USER_PROFILES = {
    "normal_employee": {
        "count": 50,
        "login_hour_mean": 9,
        "login_hour_std": 1.0,
        "logout_hour_mean": 17.5,
        "logout_hour_std": 1.5,
        "session_duration_mean": 360,  # minutes
        "session_duration_std": 120,
        "daily_activities_mean": 15,
        "daily_activities_std": 5,
        "database_queries_mean": 5,
        "database_queries_std": 3,
        "file_downloads_mean": 2,
        "file_downloads_std": 1.5,
        "failed_logins_mean": 0.1,
        "failed_logins_std": 0.3,
        "usb_events_mean": 0.2,
        "usb_events_std": 0.4,
        "anomaly_probability": 0.01,
    },
    "privileged_admin": {
        "count": 10,
        "login_hour_mean": 8.5,
        "login_hour_std": 1.5,
        "logout_hour_mean": 18,
        "logout_hour_std": 2,
        "session_duration_mean": 420,
        "session_duration_std": 150,
        "daily_activities_mean": 30,
        "daily_activities_std": 10,
        "database_queries_mean": 20,
        "database_queries_std": 8,
        "file_downloads_mean": 5,
        "file_downloads_std": 3,
        "failed_logins_mean": 0.05,
        "failed_logins_std": 0.2,
        "usb_events_mean": 0.5,
        "usb_events_std": 0.6,
        "anomaly_probability": 0.02,
    },
    "security_analyst": {
        "count": 8,
        "login_hour_mean": 8,
        "login_hour_std": 2,
        "logout_hour_mean": 19,
        "logout_hour_std": 2.5,
        "session_duration_mean": 480,
        "session_duration_std": 180,
        "daily_activities_mean": 40,
        "daily_activities_std": 15,
        "database_queries_mean": 15,
        "database_queries_std": 5,
        "file_downloads_mean": 8,
        "file_downloads_std": 4,
        "failed_logins_mean": 0.02,
        "failed_logins_std": 0.1,
        "usb_events_mean": 0.3,
        "usb_events_std": 0.5,
        "anomaly_probability": 0.015,
    },
    "contractor": {
        "count": 15,
        "login_hour_mean": 10,
        "login_hour_std": 1.5,
        "logout_hour_mean": 17,
        "logout_hour_std": 1,
        "session_duration_mean": 300,
        "session_duration_std": 90,
        "daily_activities_mean": 10,
        "daily_activities_std": 4,
        "database_queries_mean": 3,
        "database_queries_std": 2,
        "file_downloads_mean": 1,
        "file_downloads_std": 1,
        "failed_logins_mean": 0.3,
        "failed_logins_std": 0.5,
        "usb_events_mean": 0.1,
        "usb_events_std": 0.3,
        "anomaly_probability": 0.04,
    },
}

ACTIVITY_TYPES = [
    "login", "logout", "database_access", "database_export",
    "file_download", "file_upload", "usb_insertion", "usb_removal",
    "password_change", "config_change", "email_send", "email_receive",
    "admin_command", "privilege_escalation", "access_denied",
]

DEVICES = [
    {"type": "desktop", "os": "Windows 11", "browser": "Chrome 120"},
    {"type": "laptop", "os": "Windows 10", "browser": "Edge 119"},
    {"type": "laptop", "os": "macOS 14", "browser": "Safari 17"},
    {"type": "server", "os": "Ubuntu 22.04", "browser": "N/A"},
    {"type": "mobile", "os": "iOS 17", "browser": "Safari Mobile"},
]

LOCATIONS = [
    "New York, NY", "San Francisco, CA", "Chicago, IL",
    "London, UK", "Toronto, ON", "Singapore",
    "Frankfurt, DE", "Tokyo, JP", "Mumbai, IN",
]

IP_RANGES = {
    "internal": "10.0.",
    "vpn": "172.16.",
    "external": "203.0.",
}


class SyntheticDataGenerator:
    """
    Generates realistic synthetic activity data for ML model training.

    The generator creates user profiles with consistent behavioral patterns
    and injects anomalies at configurable rates to create training datasets.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize the generator with a random seed for reproducibility.

        Args:
            seed: Random seed for reproducible data generation.
        """
        self.rng = np.random.default_rng(seed)
        random.seed(seed)
        np.random.seed(seed)
        self.users = []
        self.user_profiles = {}

    def _generate_user_profiles(self) -> List[Dict]:
        """
        Generate individual user profiles based on profile type categories.

        Each user gets consistent behavioral parameters that define their
        "normal" activity pattern. This ensures the generated data has
        realistic inter-user variability.

        Returns:
            List of user profile dictionaries.
        """
        users = []
        user_id_counter = 0

        for profile_type, config in USER_PROFILES.items():
            for i in range(config["count"]):
                user_id = str(uuid.uuid4())
                user = {
                    "id": user_id,
                    "username": f"{profile_type}_{i+1:03d}",
                    "full_name": f"User {user_id_counter + 1}",
                    "profile_type": profile_type,
                    "department": self._assign_department(profile_type),
                    "role_name": profile_type,
                    # Behavioral parameters drawn from distribution
                    "login_hour_mean": config["login_hour_mean"] + self.rng.normal(0, 0.3),
                    "login_hour_std": config["login_hour_std"],
                    "logout_hour_mean": config["logout_hour_mean"] + self.rng.normal(0, 0.3),
                    "logout_hour_std": config["logout_hour_std"],
                    "session_duration_mean": config["session_duration_mean"] + self.rng.normal(0, 20),
                    "session_duration_std": config["session_duration_std"],
                    "daily_activities_mean": config["daily_activities_mean"] + self.rng.normal(0, 2),
                    "daily_activities_std": config["daily_activities_std"],
                    "database_queries_mean": config["database_queries_mean"],
                    "database_queries_std": config["database_queries_std"],
                    "file_downloads_mean": config["file_downloads_mean"],
                    "file_downloads_std": config["file_downloads_std"],
                    "failed_logins_mean": config["failed_logins_mean"],
                    "failed_logins_std": config["failed_logins_std"],
                    "usb_events_mean": config["usb_events_mean"],
                    "usb_events_std": config["usb_events_std"],
                    "anomaly_probability": config["anomaly_probability"],
                    "primary_device": random.choice(DEVICES[:3]),  # Regular users have desktop/laptop
                    "primary_location": random.choice(LOCATIONS[:5]),  # Local locations
                    "primary_ip_prefix": IP_RANGES["internal"],
                }
                users.append(user)
                self.user_profiles[user_id] = user
                user_id_counter += 1

        logger.info(f"Generated {len(users)} synthetic user profiles")
        return users

    def _assign_department(self, profile_type: str) -> str:
        """Assign department based on user profile type."""
        department_map = {
            "normal_employee": ["Finance", "HR", "Operations", "Retail Banking", "Corporate Banking"],
            "privileged_admin": ["IT Infrastructure", "IT Operations", "Security Operations"],
            "security_analyst": ["Security Operations", "SOC", "Fraud Prevention"],
            "contractor": ["External IT Services", "Consulting", "Vendor Support"],
        }
        departments = department_map.get(profile_type, ["General"])
        return random.choice(departments)

    def _generate_daily_activities(
        self, user: Dict, date: datetime, is_anomaly: bool = False
    ) -> List[Dict]:
        """
        Generate activities for a single user on a single day.

        Args:
            user: User profile dictionary.
            date: The date to generate activities for.
            is_anomaly: If True, generate anomalous activity patterns.

        Returns:
            List of activity dictionaries.
        """
        activities = []
        day_of_week = date.weekday()

        # Skip weekends with high probability (80% chance of no activity)
        if day_of_week >= 5 and self.rng.random() < 0.8:
            return activities

        # Determine login time
        if is_anomaly:
            # Anomalous: unusual login time
            login_hour = self.rng.choice([0, 1, 2, 3, 4, 22, 23])
            login_minute = self.rng.integers(0, 60)
        else:
            # Normal: around the user's typical login time
            login_hour = int(np.clip(
                self.rng.normal(user["login_hour_mean"], user["login_hour_std"]),
                6, 22
            ))
            login_minute = self.rng.integers(0, 60)

        current_time = date.replace(hour=login_hour, minute=login_minute, second=0, microsecond=0)

        # Generate login activity
        device = user["primary_device"] if not is_anomaly else random.choice(DEVICES)
        ip_prefix = user["primary_ip_prefix"] if not is_anomaly else IP_RANGES["external"]
        ip_address = f"{ip_prefix}{self.rng.integers(1, 255)}.{self.rng.integers(1, 255)}"
        location = user["primary_location"] if not is_anomaly else random.choice(LOCATIONS)

        _key = f"{user['id']}_{device['type']}"
        device_id = f"dev_{hash(_key) % 10000:04d}"

        activities.append({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "activity_type": "login",
            "description": f"User logged in from {location}",
            "ip_address": ip_address,
            "location": location,
            "device_id": device_id,
            "resource_accessed": "system",
            "resource_type": "system",
            "severity": "info",
            "risk_contribution": 0.0,
            "status": "success" if self.rng.random() > 0.02 else "failure",
            "created_at": current_time,
            "is_anomaly": is_anomaly and self.rng.random() < 0.3,
        })

        # Generate failed login attempts (if anomalous)
        if is_anomaly and self.rng.random() < 0.5:
            num_failed = int(self.rng.integers(3, 10))
            for _ in range(num_failed):
                current_time += timedelta(seconds=int(self.rng.integers(5, 60)))
                activities.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "activity_type": "login",
                    "description": "Failed login attempt",
                    "ip_address": f"{IP_RANGES['external']}{self.rng.integers(1, 255)}.{self.rng.integers(1, 255)}",
                    "location": random.choice(LOCATIONS),
                    "device_id": f"dev_unknown_{self.rng.integers(1000, 9999)}",
                    "resource_accessed": "system",
                    "resource_type": "system",
                    "severity": "medium",
                    "risk_contribution": 5.0,
                    "status": "failure",
                    "created_at": current_time,
                    "is_anomaly": True,
                })

        # Determine number of daily activities
        if is_anomaly:
            # Anomalous: much higher activity volume
            num_activities = int(self.rng.normal(
                user["daily_activities_mean"] * 3,
                user["daily_activities_std"]
            ))
        else:
            num_activities = int(max(1, self.rng.normal(
                user["daily_activities_mean"],
                user["daily_activities_std"]
            )))

        # Determine session end time
        logout_hour = int(np.clip(
            self.rng.normal(user["logout_hour_mean"], user["logout_hour_std"]),
            7, 23
        ))
        logout_minute = self.rng.integers(0, 60)
        session_end = date.replace(hour=logout_hour, minute=logout_minute)

        # Generate activities throughout the session
        session_duration = (session_end - current_time).total_seconds() / 60
        if session_duration <= 0:
            session_duration = 60

        for _ in range(num_activities):
            # Random time within the session
            offset_minutes = float(self.rng.uniform(5, max(6, session_duration)))
            current_time += timedelta(minutes=offset_minutes)
            if current_time > session_end:
                break

            # Select activity type with realistic distribution
            activity_type = self._select_activity_type(is_anomaly)
            activity = self._create_activity(
                user, activity_type, current_time, device, device_id,
                ip_address, location, is_anomaly
            )
            activities.append(activity)

        # Generate logout
        activities.append({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "activity_type": "logout",
            "description": "User logged out",
            "ip_address": ip_address,
            "location": location,
            "device_id": device_id,
            "resource_accessed": "system",
            "resource_type": "system",
            "severity": "info",
            "risk_contribution": 0.0,
            "status": "success",
            "created_at": session_end,
            "is_anomaly": False,
        })

        return activities

    def _select_activity_type(self, is_anomaly: bool) -> str:
        """
        Select an activity type based on realistic probability distribution.

        Anomalous sessions have higher probability of sensitive activities
        like database exports, USB usage, and admin commands.
        """
        if is_anomaly:
            # Anomalous: skew towards sensitive activities
            weights = [0.1, 0.05, 0.15, 0.2, 0.1, 0.05, 0.1, 0.05, 0.05, 0.1, 0.02, 0.01, 0.02, 0.02, 0.02]
        else:
            # Normal: most activities are routine access
            weights = [0.25, 0.2, 0.15, 0.02, 0.1, 0.05, 0.02, 0.01, 0.02, 0.05, 0.08, 0.03, 0.01, 0.005, 0.005]

        return self.rng.choice(ACTIVITY_TYPES, p=np.array(weights) / sum(weights))

    def _create_activity(
        self, user: Dict, activity_type: str, timestamp: datetime,
        device: Dict, device_id: str, ip_address: str,
        location: str, is_anomaly: bool
    ) -> Dict:
        """Create a single activity record with appropriate metadata."""
        severity_map = {
            "database_export": "high",
            "privilege_escalation": "critical",
            "admin_command": "medium",
            "config_change": "medium",
            "usb_insertion": "low",
            "access_denied": "medium",
        }

        risk_map = {
            "database_export": 30.0,
            "privilege_escalation": 40.0,
            "admin_command": 15.0,
            "config_change": 15.0,
            "usb_insertion": 10.0,
            "file_download": 5.0,
            "access_denied": 10.0,
        }

        # Calculate risk contribution
        risk_contribution = risk_map.get(activity_type, 0.0)
        if is_anomaly:
            risk_contribution *= 2.0

        # Determine severity
        severity = severity_map.get(activity_type, "info")
        if is_anomaly and severity == "info":
            severity = "low"

        # Build description
        descriptions = {
            "database_access": f"Database query executed via {device['type']}",
            "database_export": f"Database export: {self.rng.integers(100, 10000)} rows",
            "file_download": f"Downloaded file ({self.rng.integers(1, 500)} MB)",
            "file_upload": f"Uploaded file to cloud storage",
            "usb_insertion": "USB device connected",
            "usb_removal": "USB device removed",
            "password_change": "Password changed",
            "config_change": f"Configuration modified: {'firewall' if is_anomaly else 'profile'}",
            "email_send": f"Email sent to {self.rng.integers(1, 5)} recipients",
            "email_receive": "Email received",
            "admin_command": f"Administrative command: {'antivirus_disabled' if is_anomaly else 'service_restart'}",
            "privilege_escalation": "Elevated privileges requested",
            "access_denied": "Access to restricted resource denied",
        }

        return {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "activity_type": activity_type,
            "description": descriptions.get(activity_type, f"{activity_type} performed"),
            "ip_address": ip_address,
            "location": location,
            "device_id": device_id,
            "resource_accessed": activity_type,
            "resource_type": activity_type.split("_")[0] if "_" in activity_type else activity_type,
            "severity": severity,
            "risk_contribution": risk_contribution,
            "status": "success" if activity_type != "access_denied" else "denied",
            "created_at": timestamp,
            "is_anomaly": is_anomaly,
        }

    def generate_dataset(
        self,
        days: int = 90,
        start_date: Optional[datetime] = None,
        anomaly_rate: float = 0.03,
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Generate a complete synthetic activity dataset.

        Args:
            days: Number of days of data to generate.
            start_date: Starting date (defaults to 90 days ago).
            anomaly_rate: Proportion of anomalous days (0.0 to 1.0).

        Returns:
            Tuple of (DataFrame of all activities, List of user profiles).
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=days)

        # Generate user profiles
        users = self._generate_user_profiles()

        all_activities = []
        total_anomaly_days = 0

        logger.info(
            f"Generating {days} days of data for {len(users)} users "
            f"with {anomaly_rate*100:.1f}% anomaly rate"
        )

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)

            for user in users:
                # Decide if this is an anomalous day
                is_anomaly = self.rng.random() < user["anomaly_probability"]
                if is_anomaly:
                    total_anomaly_days += 1

                daily_activities = self._generate_daily_activities(
                    user, current_date, is_anomaly
                )
                all_activities.extend(daily_activities)

        # Create DataFrame
        df = pd.DataFrame(all_activities)

        # Ensure datetime column
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])

        anomaly_count = df["is_anomaly"].sum() if "is_anomaly" in df.columns else 0
        logger.info(
            f"Generated {len(df)} total activities "
            f"({anomaly_count} anomalous, "
            f"{total_anomaly_days} anomaly days)"
        )

        return df, users
