"""
Model Training Module
======================

Trains and evaluates anomaly detection models for behavioral analytics.

Supported Models:
    1. Isolation Forest (IF): Efficient tree-based anomaly detection
    2. Local Outlier Factor (LOF): Density-based anomaly detection

Training Pipeline:
    1. Generate synthetic data (or load real data)
    2. Extract features from raw activities
    3. Preprocess features (scaling, imputation)
    4. Train both models with cross-validation
    5. Evaluate and compare performance
    6. Select and save the best model
    7. Generate training report

Model Selection Criteria:
    - Precision: Minimize false positives (alert fatigue)
    - Recall: Detect as many true anomalies as possible
    - F1-Score: Balance precision and recall
    - Training time: Must support periodic retraining
    - Inference latency: Must support real-time scoring
"""

import os
import json
import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Optional, Any
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
    roc_auc_score, average_precision_score
)
from sklearn.pipeline import Pipeline
import warnings

warnings.filterwarnings("ignore")

from app.core.config import settings
from app.ml.features.engineer import FeatureEngineer

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trains and evaluates anomaly detection models.

    Manages the complete ML lifecycle from data preparation through
    model training, evaluation, and serialization.
    """

    def __init__(self):
        """Initialize the model trainer."""
        self.feature_engineer = FeatureEngineer(window_hours=24)
        self.feature_names = self.feature_engineer.get_feature_names()
        self.scaler = RobustScaler()
        self.isolation_forest = None
        self.local_outlier_factor = None
        self.model_metadata = {}

    def prepare_training_data(
        self, activities_df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        Prepare training data from raw activities.

        Args:
            activities_df: Raw activity data from the synthetic generator.

        Returns:
            Tuple of (feature_matrix, labels, features_df).
            - feature_matrix: numpy array of shape (n_samples, n_features)
            - labels: numpy array of binary labels (0=normal, 1=anomaly)
            - features_df: DataFrame with feature names and metadata
        """
        logger.info("Preparing training data from raw activities")

        # Extract features
        features_df = self.feature_engineer.extract_features(activities_df)

        if features_df.empty:
            logger.warning("No features extracted from activities")
            return np.array([]), np.array([]), features_df

        # Separate labels and metadata
        labels = None
        if "is_anomaly" in activities_df.columns:
            # Aggregate labels per user per window
            activities_df = activities_df.copy()
            activities_df["created_at"] = pd.to_datetime(activities_df["created_at"])
            activities_df["window_start"] = activities_df["created_at"].dt.floor("24H")

            label_agg = activities_df.groupby(["user_id", "window_start"])["is_anomaly"].max()
            # Match labels to features
            labels = []
            for _, row in features_df.iterrows():
                key = (row["user_id"], row["window_start"])
                if key in label_agg.index:
                    labels.append(int(label_agg[key]))
                else:
                    labels.append(0)
            labels = np.array(labels)

        # Extract numeric features only
        numeric_cols = [col for col in self.feature_names if col in features_df.columns]
        X = features_df[numeric_cols].values

        # Handle NaN and infinite values
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)

        # If no labels available, create synthetic labels based on heuristics
        if labels is None:
            labels = self._generate_heuristic_labels(X)

        logger.info(
            f"Prepared {X.shape[0]} samples with {X.shape[1]} features. "
            f"Anomaly rate: {labels.mean()*100:.1f}%"
        )

        return X, labels, features_df

    def _generate_heuristic_labels(self, X: np.ndarray) -> np.ndarray:
        """
        Generate heuristic labels when ground truth is not available.

        Uses statistical thresholds on key features to estimate which
        samples are anomalous. This is a fallback - always prefer
        labeled data when available.
        """
        labels = np.zeros(X.shape[0], dtype=int)

        for i in range(X.shape[0]):
            score = 0
            # High activity count
            if X[i, self.feature_names.index("activity_count")] > 60:
                score += 1
            # Many failed logins
            if X[i, self.feature_names.index("failed_login_count")] > 3:
                score += 2
            # Sensitive activities
            if X[i, self.feature_names.index("sensitive_activity_count")] > 5:
                score += 2
            # After hours activity
            if X[i, self.feature_names.index("is_after_hours")] > 0.5:
                score += 1
            # New device/location
            if X[i, self.feature_names.index("new_device_used")] > 0.5:
                score += 1
            if X[i, self.feature_names.index("new_location_used")] > 0.5:
                score += 1

            if score >= 3:
                labels[i] = 1

        return labels

    def train_isolation_forest(
        self, X_train: np.ndarray, contamination: float = 0.05
    ) -> IsolationForest:
        """
        Train an Isolation Forest model.

        Isolation Forest works by randomly selecting features and split
        values to isolate anomalies. Anomalies are isolated in fewer
        splits than normal points, resulting in shorter average path
        lengths in the ensemble of random trees.

        Args:
            X_train: Training feature matrix.
            contamination: Expected proportion of anomalies (0.0 to 0.5).

        Returns:
            Trained Isolation Forest model.
        """
        logger.info(
            f"Training Isolation Forest with {settings.ML_N_ESTIMATORS} estimators "
            f"and contamination={contamination}"
        )

        self.isolation_forest = IsolationForest(
            n_estimators=settings.ML_N_ESTIMATORS,
            contamination=contamination,
            max_features=0.8,  # Use 80% of features per tree
            bootstrap=True,    # Use bootstrapped samples
            random_state=42,
            n_jobs=-1,         # Use all CPU cores
            verbose=0,
        )

        self.isolation_forest.fit(X_train)
        logger.info("Isolation Forest training complete")
        return self.isolation_forest

    def train_local_outlier_factor(
        self, X_train: np.ndarray, contamination: float = 0.05
    ) -> LocalOutlierFactor:
        """
        Train a Local Outlier Factor model.

        LOF compares the local density of a point with the local densities
        of its neighbors. Points with significantly lower density than
        their neighbors are considered outliers.

        Args:
            X_train: Training feature matrix.
            contamination: Expected proportion of anomalies.

        Returns:
            Trained Local Outlier Factor model.
        """
        logger.info(
            f"Training Local Outlier Factor with contamination={contamination}"
        )

        self.local_outlier_factor = LocalOutlierFactor(
            n_neighbors=min(20, len(X_train) - 1),
            contamination=contamination,
            novelty=True,  # Enable prediction on new data
            n_jobs=-1,
        )

        self.local_outlier_factor.fit(X_train)
        logger.info("Local Outlier Factor training complete")
        return self.local_outlier_factor

    def evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_name: str,
    ) -> Dict[str, float]:
        """
        Evaluate a trained model on test data.

        Args:
            model: Trained model with predict method.
            X_test: Test feature matrix.
            y_test: True labels for test data.
            model_name: Name of the model for logging.

        Returns:
            Dictionary of evaluation metrics.
        """
        logger.info(f"Evaluating {model_name}")

        # Get predictions
        y_pred_raw = model.predict(X_test)

        # Convert IF predictions: 1 (normal) -> 0, -1 (anomaly) -> 1
        if model_name == "Isolation Forest":
            y_pred = np.where(y_pred_raw == -1, 1, 0)
        else:
            y_pred = np.where(y_pred_raw == -1, 1, 0)

        # Calculate metrics
        metrics = {
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "accuracy": float((y_pred == y_test).mean()),
            "true_positives": int(((y_pred == 1) & (y_test == 1)).sum()),
            "false_positives": int(((y_pred == 1) & (y_test == 0)).sum()),
            "true_negatives": int(((y_pred == 0) & (y_test == 0)).sum()),
            "false_negatives": int(((y_pred == 0) & (y_test == 1)).sum()),
            "anomaly_detection_rate": float(y_pred.mean()),
        }

        # Try to compute AUC if possible
        try:
            if hasattr(model, "decision_function"):
                scores = model.decision_function(X_test)
                # For IF, lower scores = more anomalous
                if model_name == "Isolation Forest":
                    scores = -scores
                metrics["auc_roc"] = roc_auc_score(y_test, scores)
                metrics["average_precision"] = average_precision_score(y_test, scores)
        except Exception as e:
            logger.warning(f"Could not compute AUC for {model_name}: {str(e)}")
            metrics["auc_roc"] = 0.0
            metrics["average_precision"] = 0.0

        logger.info(
            f"{model_name} - Precision: {metrics['precision']:.3f}, "
            f"Recall: {metrics['recall']:.3f}, "
            f"F1: {metrics['f1']:.3f}"
        )

        return metrics

    def train_and_evaluate(
        self,
        activities_df: pd.DataFrame,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Complete training pipeline: prepare data, train models, evaluate.

        This is the main entry point for the training pipeline.
        It orchestrates the entire process and returns a comprehensive
        training report.

        Args:
            activities_df: Raw activity data.
            test_size: Proportion of data to hold out for testing.

        Returns:
            Dictionary containing training report, metrics, and model info.
        """
        logger.info("=" * 60)
        logger.info("Starting ML Training Pipeline")
        logger.info("=" * 60)

        # Step 1: Prepare data
        X, y, features_df = self.prepare_training_data(activities_df)

        if len(X) == 0:
            logger.error("No training data available")
            return {"error": "No training data available"}

        # Step 2: Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if y.sum() > 10 else None
        )

        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        logger.info(f"Anomaly rate (train): {y_train.mean()*100:.1f}%")
        logger.info(f"Anomaly rate (test): {y_test.mean()*100:.1f}%")

        # Step 3: Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Step 4: Train models
        contamination = max(y_train.mean(), 0.01)
        self.train_isolation_forest(X_train_scaled, contamination)
        self.train_local_outlier_factor(X_train_scaled, contamination)

        # Step 5: Evaluate models
        if_metrics = self.evaluate_model(
            self.isolation_forest, X_test_scaled, y_test, "Isolation Forest"
        )
        lof_metrics = self.evaluate_model(
            self.local_outlier_factor, X_test_scaled, y_test, "Local Outlier Factor"
        )

        # Step 6: Compare and select best model
        if if_metrics["f1"] >= lof_metrics["f1"]:
            best_model_name = "Isolation Forest"
            best_model = self.isolation_forest
            best_metrics = if_metrics
        else:
            best_model_name = "Local Outlier Factor"
            best_model = self.local_outlier_factor
            best_metrics = lof_metrics

        logger.info(f"Best model: {best_model_name} (F1: {best_metrics['f1']:.3f})")

        # Step 7: Build training report
        training_report = {
            "training_timestamp": datetime.utcnow().isoformat(),
            "dataset_size": int(X.shape[0]),
            "feature_count": int(X.shape[1]),
            "feature_names": self.feature_names,
            "anomaly_rate": float(y.mean()),
            "models": {
                "isolation_forest": {
                    "metrics": if_metrics,
                    "hyperparameters": {
                        "n_estimators": settings.ML_N_ESTIMATORS,
                        "contamination": contamination,
                        "max_features": 0.8,
                    },
                },
                "local_outlier_factor": {
                    "metrics": lof_metrics,
                    "hyperparameters": {
                        "n_neighbors": min(20, len(X_train) - 1),
                        "contamination": contamination,
                    },
                },
            },
            "best_model": best_model_name,
            "best_metrics": best_metrics,
            "model_selection_reason": (
                f"Selected {best_model_name} based on F1 score "
                f"({best_metrics['f1']:.3f}). "
                f"This model provides the best balance between "
                f"precision ({best_metrics['precision']:.3f}) and "
                f"recall ({best_metrics['recall']:.3f})."
            ),
        }

        # Step 8: Save models and metadata
        self.save_models(training_report)

        logger.info("=" * 60)
        logger.info("Training Pipeline Complete")
        logger.info(f"Best Model: {best_model_name}")
        logger.info(f"F1 Score: {best_metrics['f1']:.3f}")
        logger.info(f"AUC-ROC: {best_metrics.get('auc_roc', 0):.3f}")
        logger.info("=" * 60)

        return training_report

    def save_models(self, training_report: Dict) -> None:
        """
        Save trained models and metadata to disk.

        Saves:
            - Isolation Forest model (pickle)
            - Local Outlier Factor model (pickle)
            - Feature scaler (pickle)
            - Training report (JSON)

        Args:
            training_report: Complete training report dictionary.
        """
        model_dir = settings.ML_MODEL_PATH
        os.makedirs(model_dir, exist_ok=True)

        # Save models
        if self.isolation_forest:
            with open(os.path.join(model_dir, "isolation_forest.pkl"), "wb") as f:
                pickle.dump(self.isolation_forest, f)
            logger.info("Saved Isolation Forest model")

        if self.local_outlier_factor:
            with open(os.path.join(model_dir, "local_outlier_factor.pkl"), "wb") as f:
                pickle.dump(self.local_outlier_factor, f)
            logger.info("Saved Local Outlier Factor model")

        # Save scaler
        with open(os.path.join(model_dir, "scaler.pkl"), "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("Saved feature scaler")

        # Save training report
        with open(os.path.join(model_dir, "training_report.json"), "w") as f:
            json.dump(training_report, f, indent=2, default=str)
        logger.info("Saved training report")

    def load_models(self) -> bool:
        """
        Load previously trained models from disk.

        Returns:
            True if models loaded successfully, False otherwise.
        """
        model_dir = settings.ML_MODEL_PATH

        try:
            if os.path.exists(os.path.join(model_dir, "isolation_forest.pkl")):
                with open(os.path.join(model_dir, "isolation_forest.pkl"), "rb") as f:
                    self.isolation_forest = pickle.load(f)
                logger.info("Loaded Isolation Forest model")

            if os.path.exists(os.path.join(model_dir, "local_outlier_factor.pkl")):
                with open(os.path.join(model_dir, "local_outlier_factor.pkl"), "rb") as f:
                    self.local_outlier_factor = pickle.load(f)
                logger.info("Loaded Local Outlier Factor model")

            if os.path.exists(os.path.join(model_dir, "scaler.pkl")):
                with open(os.path.join(model_dir, "scaler.pkl"), "rb") as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded feature scaler")

            if os.path.exists(os.path.join(model_dir, "training_report.json")):
                with open(os.path.join(model_dir, "training_report.json"), "r") as f:
                    self.model_metadata = json.load(f)
                logger.info("Loaded training report metadata")

            return self.isolation_forest is not None or self.local_outlier_factor is not None

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
