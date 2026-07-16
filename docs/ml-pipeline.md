# ML Pipeline Documentation

This document covers the machine learning pipeline used in SentinelAI for insider threat detection.

---

## Overview

The ML pipeline processes user activity data, extracts behavioral features, and uses unsupervised anomaly detection to identify potential insider threats.

---

## Pipeline Architecture

```
Raw Activities → Feature Engineering → Model Inference → Anomaly Score → Risk Engine
     │                  │                    │                │              │
     ▼                  ▼                    ▼                ▼              ▼
 ┌────────┐     ┌────────────┐      ┌──────────────┐   ┌──────────┐  ┌──────────┐
 │PostgreSQL│   │35 features │      │IF + LOF      │   │Score +   │  │Risk      │
 │Activities│   │per window  │      │Ensemble      │   │Confidence│  │Component │
 └────────┘     └────────────┘      └──────────────┘   └──────────┘  └──────────┘
```

---

## Feature Engineering

### Feature Categories (35 total)

#### Temporal Features (8)
| Feature | Description |
|---------|-------------|
| `login_hour` | Hour of day (0-23) |
| `login_is_weekend` | Whether login was on weekend |
| `login_is_after_hours` | Whether login was outside business hours (8am-6pm) |
| `login_is_late_night` | Whether login was between midnight and 6am |
| `session_duration_minutes` | Length of user session |
| `avg_time_between_actions` | Mean seconds between consecutive actions |
| `std_time_between_actions` | Standard deviation of time gaps |
| `actions_per_hour` | Activity rate per hour |

#### Network Features (7)
| Feature | Description |
|---------|-------------|
| `unique_ip_addresses` | Number of distinct IPs used |
| `unique_locations` | Number of distinct geographic locations |
| `unique_devices` | Number of distinct devices used |
| `new_device_ratio` | Ratio of unknown/new devices |
| `new_location_ratio` | Ratio of new geographic locations |
| `remote_access_count` | Number of remote access events |
| `ip_entropy` | Shannon entropy of IP distribution |

#### Behavioral Features (10)
| Feature | Description |
|---------|-------------|
| `activity_count` | Total number of activities in window |
| `failed_activity_ratio` | Ratio of failed to total activities |
| `unique_activity_types` | Number of distinct activity types |
| `risk_contribution_sum` | Cumulative risk contribution |
| `risk_contribution_mean` | Average risk contribution |
| `risk_contribution_max` | Maximum risk contribution |
| `risk_contribution_std` | Std deviation of risk contribution |
| `concurrent_sessions` | Number of simultaneous sessions |
| `weekend_activity_ratio` | Ratio of weekend to total activities |
| `off_hours_activity_ratio` | Ratio of off-hours to total activities |

#### Data Access Features (10)
| Feature | Description |
|---------|-------------|
| `db_query_count` | Number of database queries |
| `db_export_count` | Number of data exports |
| `file_access_count` | Number of file accesses |
| `large_download_count` | Number of large file downloads |
| `privilege_escalation_count` | Attempts to escalate privileges |
| `config_change_count` | System configuration changes |
| `usb_device_count` | USB device connections |
| `email_forward_count` | Email forwarding events |
| `db_query_volume` | Total rows queried |
| `sensitive_data_access` | Access to classified data |

---

## Training Pipeline

### Synthetic Data Generation

The generator creates realistic activity data with controllable anomaly injection:

```python
from app.ml.synthetic.generator import SyntheticDataGenerator

generator = SyntheticDataGenerator(seed=42)
activities_df, user_profiles = generator.generate_dataset(
    days=30,           # 30 days of data
    num_users=100,     # 100 synthetic users
    anomaly_rate=0.1,  # 10% anomaly injection
)
```

**User Profiles:**
| Profile | Anomaly Rate | Behavior |
|---------|-------------|----------|
| `normal` | 0.02 | Standard business hours, normal access |
| `data_exfiltrator` | 0.15 | After-hours, large exports, new locations |
| `privilege_abuser` | 0.12 | Privilege escalation, config changes |
| `insider_threat` | 0.20 | Multiple suspicious patterns |
| `lazy_employee` | 0.05 | Low activity, missed sessions |

### Model Training

```python
from app.ml.training.trainer import ModelTrainer

trainer = ModelTrainer()
report = trainer.train_and_evaluate(
    activities_df,
    test_size=0.2,
)
```

**Output artifacts:**
- `app/ml/data/models/isolation_forest.pkl` — Trained Isolation Forest model
- `app/ml/data/models/lof_model.pkl` — Trained Local Outlier Factor model
- `app/ml/data/models/feature_scaler.pkl` — StandardScaler fitted on training data
- `app/ml/data/models/feature_names.json` — Ordered list of feature names

### Model Selection

The trainer evaluates both models and selects the best based on F1-score on the test set:

```json
{
  "best_model": "Isolation Forest",
  "best_metrics": {
    "accuracy": 0.92,
    "precision": 0.85,
    "recall": 0.78,
    "f1_score": 0.81
  },
  "all_models": {
    "Isolation Forest": { "f1_score": 0.81 },
    "Local Outlier Factor": { "f1_score": 0.76 }
  },
  "dataset_size": 5000,
  "feature_count": 35
}
```

---

## Inference Pipeline

### Real-Time Inference

```python
from app.ml.inference.anomaly_detector import AnomalyInference

detector = AnomalyInference()
detector.load_models()

result = detector.predict(features_array)
# Returns:
# {
#   "anomaly_score": 0.73,
#   "is_anomaly": True,
#   "confidence": 0.87,
#   "model_used": "Isolation Forest",
#   "explanation": "Anomaly detected with 87% confidence..."
# }
```

### Fallback Mode

When models are not loaded (e.g., first startup), a rule-based fallback is used:

```python
# Rule-based fallback checks:
# - Off-hours activity (>22:00 or <06:00)
# - High-risk activity types (USB, export, privilege escalation)
# - High risk_contribution values (>0.5)
# Returns anomaly_score between 0.0 and 1.0
```

---

## Model Hyperparameters

### Isolation Forest
```python
IsolationForest(
    n_estimators=200,      # Number of trees
    max_samples='auto',    # Samples per tree
    contamination=0.1,     # Expected anomaly ratio
    max_features=1.0,      # Features per tree
    bootstrap=False,       # No bootstrap sampling
    random_state=42,       # Reproducibility
    n_jobs=-1              # All CPU cores
)
```

### Local Outlier Factor
```python
LocalOutlierFactor(
    n_neighbors=20,        # Neighbors for density estimation
    algorithm='auto',      # Best algorithm for data
    metric='minkowski',    # Distance metric
    p=2,                   # Euclidean distance
    contamination=0.1,     # Expected anomaly ratio
    novelty=False,         # Training mode (not novelty detection)
    n_jobs=-1              # All CPU cores
)
```

---

## Performance Benchmarks

| Metric | Isolation Forest | Local Outlier Factor |
|--------|-----------------|---------------------|
| Training Time (5K samples) | 1.2s | 0.8s |
| Inference Time (1 sample) | <1ms | <1ms |
| Memory Usage | ~15 MB | ~12 MB |
| F1-Score | 0.81 | 0.76 |

---

## Retraining Schedule

For production, retrain models weekly with new labeled data:

```bash
# Automated retraining (cron job)
0 3 * * 0 cd /opt/sentinel-ai/backend && python scripts/train_models.py
```

### Monitoring Model Drift

Track these metrics over time:
- Anomaly detection rate (should remain ~10-15%)
- False positive rate (should remain <5%)
- Feature distribution shift (compare current vs training data)
