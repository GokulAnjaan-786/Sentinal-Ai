# Architecture Overview

SentinelAI follows a modular, layered architecture designed for scalability, maintainability, and security.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION                              │
│   React SPA · TypeScript · Tailwind CSS · Recharts · Framer Motion │
│   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐ │
│   │Login    │ │Dashboard│ │Alerts    │ │Risk     │ │User       │ │
│   │Page     │ │Page     │ │Page      │ │Analysis │ │Management │ │
│   └─────────┘ └─────────┘ └──────────┘ └─────────┘ └───────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┴────────────────────────────────────────┐
│                       REVERSE PROXY (Nginx)                        │
│         Static file serving · API proxy · Gzip · Security headers  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                       │
│    Authentication · Rate Limiting · Input Validation · Routing      │
├─────────────────────────────────────────────────────────────────────┤
│                         BUSINESS LOGIC                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐│
│  │ Auth         │ │ Alert        │ │ Activity     │ │ Dashboard  ││
│  │ Service      │ │ Engine       │ │ Monitor      │ │ Service    ││
│  │              │ │              │ │              │ │            ││
│  │ JWT · bcrypt │ │ Lifecycle    │ │ Pipeline     │ │ Metrics    ││
│  │ RBAC · Sess. │ │ Templates    │ │ Coordinat.   │ │ Charts     ││
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘│
│         │                │                │                │       │
│  ┌──────┴───────────────┴────────────────┴────────────────┴─────┐  │
│  │                    DETECTION PIPELINE                        │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐  │  │
│  │  │ Rule Engine  │ │ ML Inference │ │ Risk Score Engine   │  │  │
│  │  │              │ │              │ │                     │  │  │
│  │  │ 12 rules     │ │ Isolation    │ │ 4-component         │  │  │
│  │  │ Cooldown     │ │ Forest + LOF │ │ weighted scoring    │  │  │
│  │  │ Pattern      │ │ Feature Eng. │ │ Trend tracking      │  │  │
│  │  │ matching     │ │ Anomaly det. │ │ Explainable AI      │  │  │
│  │  └──────────────┘ └──────────────┘ └─────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────┐ ┌──────────────────────────────────────────────┐ │
│  │ Quantum-Safe │ │ Data Models (SQLAlchemy ORM)                 │ │
│  │ Crypto       │ │ User · Activity · Alert · RiskScore · Audit  │ │
│  │ Kyber+Dilith │ │ Device · Session · Department · Role · Perm  │ │
│  └──────────────┘ └──────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Async I/O
┌────────────────────────────┴────────────────────────────────────────┐
│                      DATA LAYER                                    │
│         PostgreSQL 15 · SQLAlchemy 2.0 (Async) · Alembic          │
│         Connection pooling · Transaction management                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. Detection Pipeline

The `ActivityMonitor` is the central orchestrator that processes every incoming user activity:

```
Activity Received
      │
      ▼
┌─────────────────┐
│ Save to Database │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Rule Engine     │────▶│ Rule Violations  │
│ (12 patterns)   │     │ []               │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       │
┌─────────────────┐              │
│ ML Inference    │              │
│ (IF + LOF)      │              │
└────────┬────────┘              │
         │                       │
         ▼                       ▼
┌────────────────────────────────────┐
│ Risk Score Engine                  │
│ ML(0.4) + Rules(0.3) +            │
│ Context(0.2) + Historical(0.1)    │
└────────────────┬───────────────────┘
                 │
                 ▼
┌─────────────────┐
│ Alert Engine    │
│ Threshold check │
│ Alert creation  │
│ Notification    │
└─────────────────┘
```

### 2. Machine Learning Pipeline

#### Training Phase

```
Synthetic Data Generator
        │
        ▼
┌───────────────────┐
│ 10,000 records    │
│ 15 activity types │
│ 5 user profiles   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Feature Engineer  │
│ 35 features       │
│ Temporal +        │
│ Network +         │
│ Behavioral +      │
│ Data Access       │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Isol.   │ │LOF     │
│Forest  │ │Model   │
└────────┘ └────────┘
    │         │
    └────┬────┘
         │
         ▼
┌───────────────────┐
│ Model Selection   │
│ (best F1-score)   │
└───────────────────┘
```

#### Inference Phase

```python
# Real-time anomaly detection for each activity
features = FeatureEngineer.extract_single_window_features([activity])
prediction = inference_engine.predict(features)
# Returns: anomaly_score, is_anomaly, confidence, explanation
```

### 3. Risk Scoring System

The risk score combines four weighted components:

| Component | Weight | Source | Description |
|-----------|--------|--------|-------------|
| ML Score | 40% | Isolation Forest / LOF | Anomaly probability from trained models |
| Rule Score | 30% | Rule Engine | Number and severity of triggered rules |
| Context Score | 20% | Activity Context | Time, location, device, session patterns |
| Historical Score | 10% | User History | Past risk scores for this user |

**Risk Levels:**
- **Low** (0-24): Normal activity, no action required
- **Medium** (25-49): Unusual patterns, monitor closely
- **High** (50-74): Suspicious activity, investigate promptly
- **Critical** (75-100): Likely threat, immediate response required

### 4. Quantum-Safe Cryptography

```
┌────────────────────────────────────────────┐
│          Quantum-Safe Crypto Layer          │
├────────────────────────────────────────────┤
│                                            │
│  Key Encapsulation (Kyber ML-KEM-512)     │
│  ┌──────────────────────────────────┐      │
│  │ generate_keypair()               │      │
│  │ encrypt(plaintext, pub_key)      │      │
│  │ decrypt(ciphertext, priv_key)    │      │
│  └──────────────────────────────────┘      │
│                                            │
│  Digital Signatures (Dilithium ML-DSA-44)  │
│  ┌──────────────────────────────────┐      │
│  │ sign(message, private_key)       │      │
│  │ verify(message, sig, pub_key)    │      │
│  └──────────────────────────────────┘      │
│                                            │
│  Mode: OQS native or Simulation            │
└────────────────────────────────────────────┘
```

---

## Data Flow

### Activity Processing Flow

```
User performs action
        │
        ▼
┌─────────────────┐
│ Frontend sends   │
│ POST /api/v1/    │
│ activities       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Nginx proxies    │
│ to backend:8000  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Auth middleware   │
│ validates JWT    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Activity route   │
│ handler          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ActivityMonitor  │
│ .process()       │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────────┐
    │         │            │              │
    ▼         ▼            ▼              ▼
┌───────┐ ┌───────┐ ┌──────────┐ ┌────────────┐
│ DB    │ │Rules  │ │ML        │ │Risk Score  │
│ Save  │ │Check  │ │Predict   │ │Calculate   │
└───────┘ └───────┘ └──────────┘ └───────┬────┘
                                          │
                                    ┌─────┴─────┐
                                    │           │
                                    ▼           ▼
                              ┌─────────┐ ┌─────────┐
                              │Alert if │ │Update   │
                              │threshold│ │user risk│
                              │exceeded │ │history  │
                              └─────────┘ └─────────┘
```

---

## Security Architecture

### Authentication Flow

```
Login Request
      │
      ▼
┌───────────────────┐
│ Validate username │
│ & password        │
│ (bcrypt verify)   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Check account     │
│ lockout status    │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────────┐
│Success │ │ Lockout or │
│        │ │ Invalid    │
└────┬───┘ └────────────┘
     │
     ▼
┌───────────────────┐
│ Generate tokens   │
│ access + refresh  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Log login event   │
│ to audit trail    │
└───────────────────┘
```

### Authorization Middleware

Every API request passes through:
1. **JWT Verification** — Token is valid and not expired
2. **Role Extraction** — User's role is determined from token
3. **Permission Check** — Role has required permission for endpoint
4. **Rate Limiting** — Request is within rate limits

---

## Scalability Considerations

### Horizontal Scaling
- **Backend**: Stateless FastAPI instances behind load balancer
- **Frontend**: Static assets served from CDN
- **Database**: Read replicas for dashboard queries

### Vertical Scaling
- **ML Models**: GPU acceleration for training, CPU for inference
- **Database**: Connection pooling (10-20 connections per instance)
- **Cache**: Redis for session storage and frequently accessed data

### Performance Targets
- Activity processing: < 100ms per event
- Dashboard refresh: < 500ms
- Alert generation: < 200ms from detection
- ML inference: < 50ms per prediction
