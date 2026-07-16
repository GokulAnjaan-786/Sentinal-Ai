#!/usr/bin/env python3
"""
SentinelAI ML Training Script
===============================

Trains anomaly detection models on synthetic data.
Run this script to generate trained models for inference.

Usage:
    python scripts/train_models.py
"""

import sys
import os
from pathlib import Path

# Add backend root to path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))


def main():
    print("=" * 60)
    print("  SentinelAI - ML Model Training")
    print("=" * 60)

    try:
        from app.ml.synthetic.generator import SyntheticDataGenerator
        from app.ml.training.trainer import ModelTrainer

        print("\n[1/3] Generating synthetic training data...")
        generator = SyntheticDataGenerator(seed=42)
        df, user_profiles = generator.generate_dataset(days=30)
        print(f"  Generated {len(df)} activity records for {len(user_profiles)} users")

        print("\n[2/3] Training models...")
        trainer = ModelTrainer()
        report = trainer.train_and_evaluate(df, test_size=0.2)

        print("\n[3/3] Training complete!")
        print(f"\nResults:")
        print(f"  Best Model:    {report['best_model']}")
        print(f"  F1-Score:      {report['best_metrics']['f1_score']:.4f}")
        print(f"  Precision:     {report['best_metrics']['precision']:.4f}")
        print(f"  Recall:        {report['best_metrics']['recall']:.4f}")
        print(f"  Dataset Size:  {report['dataset_size']}")
        print(f"  Features:      {report['feature_count']}")
        print(f"\nModels saved to: app/ml/data/models/")

    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
