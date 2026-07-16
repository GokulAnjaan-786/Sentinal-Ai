<p align="center">
  <img src="docs/images/logo.png" alt="SentinelAI Logo" width="200"/>
</p>

<h1 align="center">SentinelAI</h1>
<p align="center">
  <strong>AI-Powered Privileged Access Misuse & Insider Threat Detection System</strong>
</p>

<p align="center">
  Enterprise-grade cybersecurity platform built for the Banking Cybersecurity Hackathon
</p>

---

## 🎯 Overview

SentinelAI is a real-time insider threat detection system designed specifically for the banking sector. It leverages machine learning, behavioral analytics, and quantum-safe cryptography to detect, analyze, and respond to privileged access misuse and insider threats before they cause damage.

### Key Features

- **ML-Powered Anomaly Detection** — Isolation Forest + Local Outlier Factor algorithms
- **Behavioral Analytics** — Real-time user activity profiling and deviation detection
- **Dynamic Risk Scoring** — 4-component weighted scoring (ML 40%, Rules 30%, Context 20%, Historical 10%)
- **12 Detection Rules** — Pre-configured rules for common insider threat patterns
- **Quantum-Safe Cryptography** — CRYSTALS-Kyber (KEM) + CRYSTALS-Dilithium (Signatures) via OQS or simulation
- **Real-Time Dashboard** — Interactive metrics, charts, and alert management
- **Role-Based Access Control** — 6 predefined roles with granular permissions
- **Full Audit Trail** — Every action is logged with structured metadata

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│        TypeScript · Tailwind CSS · Recharts · Framer Motion│
├─────────────────────────────────────────────────────────────┤
│                       Nginx (Reverse Proxy)                 │
├─────────────────────────────────────────────────────────────┤
│                   Backend (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Auth     │ │ Rule     │ │ Risk     │ │ Quantum-Safe │  │
│  │ Module   │ │ Engine   │ │ Engine   │ │ Crypto       │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ ML       │ │ Alert    │ │ Activity │ │ Dashboard    │  │
│  │ Module   │ │ Engine   │ │ Monitor  │ │ API          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              PostgreSQL · SQLAlchemy (Async)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.10+, Node.js 18+, PostgreSQL 15+

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/sentinel-ai.git
cd sentinel-ai

# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# Seed the database
docker-compose exec backend python scripts/seed_database.py
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create database
createdb sentinel_ai_db

# Seed database
python scripts/seed_database.py

# Start backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## 👤 Default Credentials

| Role              | Username          | Password           |
|-------------------|-------------------|-------------------|
| Super Admin       | `admin`           | `Admin@12345!`    |
| SOC Analyst       | `soc_analyst_1`   | `Analyst@123!`    |
| Security Analyst  | `analyst_2`       | `Analyst@123!`    |

---

## 📊 Dashboard Features

### Real-Time Monitoring
- Active alerts with severity badges
- User risk scores with trend indicators
- Activity volume metrics (last 24 hours)
- System health indicators

### Analytics
- Risk score distribution charts
- Alert type breakdown (pie chart)
- Activity timeline with anomaly highlighting
- User risk rankings

### Alert Management
- View all alerts with filtering (severity, status)
- Investigate alerts with full activity context
- Acknowledge, investigate, resolve, or dismiss alerts
- AI-generated explanations for each alert

---

## 🔒 Security Features

### Authentication
- JWT access tokens (30-minute expiry)
- Refresh tokens (7-day expiry)
- bcrypt password hashing (12 rounds)
- Account lockout after 5 failed attempts

### Authorization (RBAC)
| Role              | Permissions                                         |
|-------------------|----------------------------------------------------|
| Super Admin       | Full system access                                 |
| Security Analyst  | View alerts, investigate, view users               |
| Admin             | Manage users, manage departments                   |
| Viewer            | View-only dashboard access                         |
| Employee          | View own activities only                           |
| Contractor        | View own activities with restrictions              |

### Quantum-Safe Cryptography
- **CRYSTALS-Kyber** — Key Encapsulation Mechanism (ML-KEM)
- **CRYSTALS-Dilithium** — Digital Signature Algorithm (ML-DSA)
- Falls back to simulation mode when OQS library unavailable
- Ready for post-quantum threat landscape

---

## 🧠 ML Pipeline

### Training Data
- Synthetic data generator with 15+ activity types
- User profiles: normal, data_exfiltrator, privilege_abuser, insider_threat, lazy_employee
- Configurable anomaly injection rate

### Feature Engineering (35 features)
- Temporal: login hour, session duration, weekend/afternoon patterns
- Network: unique IPs, locations, device count, new device ratio
- Behavioral: activity count, failure rate, risk score trends
- Data access: DB query volume, export count, file access patterns

### Models
| Model              | Purpose                    | Hyperparameters             |
|--------------------|----------------------------|-----------------------------|
| Isolation Forest   | Unsupervised anomaly detection | n_estimators=200, contamination=0.1 |
| Local Outlier Factor | Density-based anomaly detection | n_neighbors=20, contamination=0.1 |

### Risk Score Formula
```
Total Risk = (ML Score × 0.4) + (Rule Score × 0.3) + (Context Score × 0.2) + (Historical × 0.1)
```

---

## 📁 Project Structure

```
sentinel-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic settings configuration
│   │   │   └── logging_config.py      # Structured logging setup
│   │   ├── database/
│   │   │   └── connection.py          # Async SQLAlchemy engine & session
│   │   ├── models/                    # SQLAlchemy ORM models (12 models)
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── auth/                      # JWT, passwords, RBAC, dependencies
│   │   ├── api/v1/                    # Route handlers (8 endpoint groups)
│   │   ├── ml/
│   │   │   ├── synthetic/             # Synthetic data generation
│   │   │   ├── features/              # Feature engineering
│   │   │   ├── training/              # Model training pipeline
│   │   │   └── inference/             # Real-time inference engine
│   │   ├── rule_engine/               # Detection rule definitions
│   │   ├── risk_engine/               # Dynamic risk scoring
│   │   ├── alert_engine/              # Alert lifecycle management
│   │   ├── activity_monitor/          # Central detection pipeline
│   │   └── quantum_safe/              # Post-quantum cryptography
│   ├── scripts/
│   │   └── seed_database.py           # Database seeding with sample data
│   ├── tests/                         # Unit, integration, ML tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/                     # React page components
│   │   ├── components/                # Reusable UI components
│   │   ├── context/                   # React context providers
│   │   ├── services/                  # API service layer
│   │   └── types/                     # TypeScript type definitions
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   └── nginx.conf                     # Reverse proxy configuration
├── docs/                              # Project documentation
├── docker-compose.yml                 # Multi-service orchestration
└── README.md
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/installation.md) | Step-by-step setup instructions |
| [Architecture Overview](docs/architecture.md) | System design and data flow |
| [API Reference](docs/api-reference.md) | Complete endpoint documentation |
| [Deployment Guide](docs/deployment.md) | Production deployment instructions |
| [ML Pipeline](docs/ml-pipeline.md) | Model training and inference details |

---

## 🧪 Testing

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test modules
pytest tests/unit/test_auth.py -v
pytest tests/unit/test_risk_engine.py -v
pytest tests/ml_tests/test_ml.py -v
```

---

## 🛡️ Detection Rules

| Rule | Description | Severity |
|------|-------------|----------|
| USB Device Usage | Unauthorized USB storage connected | High |
| Database Export | Large-scale data extraction from database | Critical |
| Multiple Failed Logins | Repeated authentication failures | High |
| Privilege Escalation | Attempt to gain unauthorized privileges | Critical |
| Security Tool Disabled | Security controls intentionally disabled | Critical |
| Off-Hours Activity | Suspicious activity during non-business hours | Medium |
| Config Change | Unauthorized system configuration changes | High |
| Account Lockout | Account temporarily locked due to failures | Medium |
| Concurrent Sessions | Multiple active sessions from different locations | High |
| Excessive DB Queries | Abnormally high database query volume | Medium |
| Large File Download | Bulk file downloads exceeding threshold | High |
| After-Hours Login | Login attempts during unusual hours | Medium |

---

## 📄 License

This project was built for the **Banking Cybersecurity Hackathon**. All rights reserved.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

