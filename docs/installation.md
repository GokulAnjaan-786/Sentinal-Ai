# Installation Guide

This guide covers setting up SentinelAI for development and production use.

## Prerequisites

### Docker Installation (Recommended)
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- 4 GB RAM minimum, 8 GB recommended

### Manual Installation
- Python 3.10 or later
- Node.js 18 or later
- PostgreSQL 15 or later
- Git

---

## Docker Setup (Recommended)

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/sentinel-ai.git
cd sentinel-ai

# Create environment configuration
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your settings:

```env
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel_ai_db
JWT_SECRET_KEY=your-secure-random-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Verify all services are running
docker-compose ps
```

You should see:
- `sentinel-postgres` — PostgreSQL database
- `sentinel-backend` — FastAPI backend
- `sentinel-frontend` — React frontend served by nginx

### 3. Initialize the Database

```bash
# Run the database seeder
docker-compose exec backend python scripts/seed_database.py
```

This creates:
- Default roles (super_admin, security_analyst, admin, viewer, employee, contractor)
- Default departments (Security Operations, IT Operations, Engineering, etc.)
- Sample users with demo credentials
- 500 synthetic activity records for testing

### 4. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React dashboard |
| Backend API | http://localhost:8000 | REST API endpoints |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| API Documentation (ReDoc) | http://localhost:8000/redoc | ReDoc format |

### Default Login Credentials

```
Admin Login:
  Username: admin
  Password: Admin@12345!

SOC Analyst Login:
  Username: soc_analyst_1
  Password: Analyst@123!
```

---

## Manual Development Setup

### 1. Database Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE USER sentinel WITH PASSWORD 'sentinel';
CREATE DATABASE sentinel_ai_db OWNER sentinel;
GRANT ALL PRIVILEGES ON DATABASE sentinel_ai_db TO sentinel;
\q
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Seed the database
python scripts/seed_database.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend runs on http://localhost:5173 by default.

---

## Environment Variables

### Backend Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel_ai_db` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | (must be set) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `ML_MODEL_PATH` | Path to trained ML models | `app/ml/data/models` |
| `ML_CONTAMINATION_RATE` | Expected anomaly ratio | `0.1` |
| `RISK_ML_WEIGHT` | Weight for ML in risk scoring | `0.4` |
| `RISK_RULES_WEIGHT` | Weight for rules in risk scoring | `0.3` |
| `RISK_CONTEXT_WEIGHT` | Weight for context in risk scoring | `0.2` |
| `RISK_HISTORICAL_WEIGHT` | Weight for history in risk scoring | `0.1` |
| `QPC_ENABLED` | Enable quantum-safe crypto | `false` |
| `QPC_SIMULATION_MODE` | Use simulated QPC | `true` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Frontend Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |

---

## Training ML Models

To train models on synthetic data:

```bash
cd backend
source venv/bin/activate

# Run the training script
python scripts/train_models.py
```

This generates:
- `app/ml/data/models/isolation_forest.pkl` — Trained IF model
- `app/ml/data/models/lof_model.pkl` — Trained LOF model
- `app/ml/data/models/feature_scaler.pkl` — Feature scaler
- `app/ml/data/models/feature_names.json` — Feature name mappings

---

## Verifying Installation

### Health Check

```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs are accessible
curl http://localhost:8000/docs

# Check database connection
docker-compose exec postgres psql -U sentinel -d sentinel_ai_db -c "\dt"
```

### Running Tests

```bash
cd backend

# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## Troubleshooting

### Common Issues

**Port conflict on 5432 (PostgreSQL):**
```bash
# Check if port is in use
netstat -ano | findstr :5432  # Windows
lsof -i :5432                  # Linux/Mac

# Stop local PostgreSQL if running
sudo systemctl stop postgresql
```

**Docker build fails:**
```bash
# Clean Docker cache and rebuild
docker-compose down --rmi all
docker-compose build --no-cache
docker-compose up -d
```

**Module import errors:**
```bash
# Ensure you're in the backend directory with venv active
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Database connection refused:**
```bash
# Verify PostgreSQL container is running
docker-compose logs postgres

# Check environment variables
docker-compose exec backend env | grep DATABASE
```
