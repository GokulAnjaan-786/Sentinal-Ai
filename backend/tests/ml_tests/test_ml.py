"""
Unit Tests for ML Module
==========================

Tests for synthetic data generation, feature engineering, and model training.
"""

import pytest
import numpy as np
import pandas as pd


class TestSyntheticDataGenerator:
    """Tests for the synthetic data generator."""

    def test_generator_creates_data(self):
        """Test that the generator produces a non-empty DataFrame."""
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        df, users = generator.generate_dataset(days=7)

        assert len(df) > 0
        assert len(users) > 0

    def test_generator_has_required_columns(self):
        """Test that generated data has all required columns."""
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        df, users = generator.generate_dataset(days=7)

        required_columns = [
            "user_id", "activity_type", "created_at",
            "severity", "status", "risk_contribution",
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_generator_user_profiles(self):
        """Test that user profiles have expected fields."""
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        _, users = generator.generate_dataset(days=7)

        for user in users[:5]:
            assert "id" in user
            assert "username" in user
            assert "profile_type" in user
            assert "login_hour_mean" in user

    def test_generator_injects_anomalies(self):
        """Test that some anomalies are present in the data."""
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        df, _ = generator.generate_dataset(days=30)

        assert "is_anomaly" in df.columns
        anomaly_count = df["is_anomaly"].sum()
        assert anomaly_count > 0, "Expected some anomalies in the data"

    def test_generator_reproducible(self):
        """Test that the generator produces same data with same seed."""
        from app.ml.synthetic.generator import SyntheticDataGenerator

        gen1 = SyntheticDataGenerator(seed=42)
        df1, _ = gen1.generate_dataset(days=7)

        gen2 = SyntheticDataGenerator(seed=42)
        df2, _ = gen2.generate_dataset(days=7)

        pd.testing.assert_frame_equal(df1, df2)


class TestFeatureEngineer:
    """Tests for feature engineering."""

    def test_feature_extraction(self):
        """Test that features are extracted correctly from activities."""
        from app.ml.features.engineer import FeatureEngineer
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        df, _ = generator.generate_dataset(days=7)

        engineer = FeatureEngineer()
        features = engineer.extract_features(df)

        assert len(features) > 0
        assert "user_id" in features.columns
        assert "activity_count" in features.columns

    def test_feature_names(self):
        """Test that feature names are consistently defined."""
        from app.ml.features.engineer import FeatureEngineer

        engineer = FeatureEngineer()
        names = engineer.get_feature_names()

        assert len(names) > 0
        assert "login_hour" in names
        assert "activity_count" in names
        assert "risk_contribution_sum" in names

    def test_single_window_features(self):
        """Test feature extraction for a single time window."""
        from app.ml.features.engineer import FeatureEngineer

        engineer = FeatureEngineer()
        activities = [
            {
                "user_id": "test-user",
                "activity_type": "login",
                "created_at": "2024-01-15T09:00:00",
                "status": "success",
                "ip_address": "10.0.1.100",
                "device_id": "dev_0001",
                "location": "New York",
                "severity": "info",
                "risk_contribution": 0.0,
            },
        ]

        features = engineer.extract_single_window_features(activities)
        assert features.shape == (1, len(engineer.get_feature_names()))

    def test_empty_features_handled(self):
        """Test that empty input produces zero features."""
        from app.ml.features.engineer import FeatureEngineer

        engineer = FeatureEngineer()
        features = engineer.extract_single_window_features([])
        assert features.shape == (1, len(engineer.get_feature_names()))
        assert np.all(features == 0)


class TestModelTrainer:
    """Tests for model training pipeline."""

    def test_prepare_training_data(self):
        """Test that training data preparation works."""
        from app.ml.training.trainer import ModelTrainer
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        df, _ = generator.generate_dataset(days=14)

        trainer = ModelTrainer()
        X, y, features_df = trainer.prepare_training_data(df)

        assert len(X) > 0
        assert len(y) > 0
        assert X.shape[0] == len(y)

    def test_train_and_evaluate(self):
        """Test the complete training pipeline."""
        from app.ml.training.trainer import ModelTrainer
        from app.ml.synthetic.generator import SyntheticDataGenerator

        generator = SyntheticDataGenerator(seed=42)
        df, _ = generator.generate_dataset(days=30)

        trainer = ModelTrainer()
        report = trainer.train_and_evaluate(df, test_size=0.2)

        assert "best_model" in report
        assert "best_metrics" in report
        assert report["best_model"] in ["Isolation Forest", "Local Outlier Factor"]
        assert report["dataset_size"] > 0
        assert report["feature_count"] > 0


class TestAnomalyInference:
    """Tests for anomaly inference engine."""

    def test_fallback_prediction(self):
        """Test fallback prediction when models are not loaded."""
        from app.ml.inference.anomaly_detector import AnomalyInference

        inference = AnomalyInference()
        # Don't load models - test fallback
        result = inference.predict([
            {"activity_type": "login", "status": "success", "created_at": "2024-01-15T09:00:00"},
        ])

        assert "anomaly_score" in result
        assert "is_anomaly" in result
        assert "explanation" in result
        assert "rule_based_fallback" in result["model_used"]
