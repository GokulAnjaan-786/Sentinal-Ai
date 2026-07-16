"""
Machine Learning Package
=========================

AI-powered behavioral analytics engine for SentinelAI.

This package implements the core ML capabilities:
    - Synthetic data generation for training
    - Feature engineering from raw activity data
    - Model training (Isolation Forest, Local Outlier Factor)
    - Real-time anomaly inference
    - Model evaluation and comparison

The ML engine learns normal user behavior patterns and identifies
anomalies that may indicate insider threats, compromised accounts,
or privilege misuse.

Architecture:
    1. Raw activities are processed into feature vectors
    2. Features capture temporal, behavioral, and contextual patterns
    3. Isolation Forest identifies point anomalies (individual events)
    4. LOF detects density-based anomalies (contextual outliers)
    5. Anomaly scores are fed into the Risk Score Engine
"""
