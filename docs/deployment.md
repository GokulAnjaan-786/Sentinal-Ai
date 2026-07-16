# Deployment Guide

This guide covers deploying SentinelAI to production environments.

---

## Docker Compose Deployment (Single Server)

### Prerequisites
- Linux server with Docker and Docker Compose installed
- Minimum 4 GB RAM, 2 CPU cores
- Ports 80, 3000, 5432 available

### Steps

1. **Clone and configure**
```bash
git clone https://github.com/your-org/sentinel-ai.git
cd sentinel-ai
cp backend/.env.example backend/.env
```

2. **Edit environment variables**
```bash
nano backend/.env
```

Set these for production:
```env
DATABASE_URL=postgresql+asyncpg://sentinel:STRONG_PASSWORD@postgres:5432/sentinel_ai_db
JWT_SECRET_KEY=<generate with: openssl rand -hex 64>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=WARNING
RATE_LIMIT_PER_MINUTE=60
QPC_ENABLED=true
QPC_SIMULATION_MODE=false
```

3. **Start services**
```bash
docker-compose -f docker-compose.yml up -d --build
```

4. **Initialize database**
```bash
docker-compose exec backend python scripts/seed_database.py
```

5. **Train ML models** (optional, uses synthetic data)
```bash
docker-compose exec backend python scripts/train_models.py
```

### Production docker-compose.yml Modifications

```yaml
services:
  postgres:
    restart: always
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Use strong password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 2G

  backend:
    restart: always
    environment:
      - LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          memory: 1G

  frontend:
    restart: always
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  postgres_data:
    driver: local
```

---

## Nginx Reverse Proxy (Production)

Replace the default nginx.conf with production settings:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## SSL/TLS Setup with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d your-domain.com -d api.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Database Backup

### Automated Backup Script

Create `/opt/scripts/backup-sentinel-db.sh`:

```bash
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/sentinel"
DB_CONTAINER="sentinel-postgres"
DB_NAME="sentinel_ai_db"
DB_USER="sentinel"

mkdir -p $BACKUP_DIR

# Dump database
docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/sentinel_$TIMESTAMP.sql.gz"

# Remove backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: sentinel_$TIMESTAMP.sql.gz"
```

```bash
# Make executable
chmod +x /opt/scripts/backup-sentinel-db.sh

# Schedule with cron (daily at 2 AM)
echo "0 2 * * * /opt/scripts/backup-sentinel-db.sh" | crontab -
```

### Manual Backup/Restore

```bash
# Backup
docker exec sentinel-postgres pg_dump -U sentinel sentinel_ai_db > backup.sql

# Restore
docker exec -i sentinel-postgres psql -U sentinel sentinel_ai_db < backup.sql
```

---

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

### Docker Health Checks

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sentinel -d sentinel_ai_db"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Log Monitoring

```bash
# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail 100 backend
```

### Resource Monitoring

```bash
# Docker stats
docker stats

# Specific container
docker stats sentinel-backend
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

### PostgreSQL Scaling

```yaml
# For read replicas
services:
  postgres:
    # Primary database
  postgres-replica:
    image: postgres:15
    environment:
      POSTGRES_PRIMARY_HOST: postgres
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_REPLICATION_USER: replication
    volumes:
      - replica_data:/var/lib/postgresql/data
```

---

## Security Hardening

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw deny 5432/tcp  # Database not exposed externally
ufw enable
```

### Docker Security

```bash
# Run containers as non-root (already configured in Dockerfiles)
# Scan images for vulnerabilities
docker scan sentinel-ai-backend
docker scan sentinel-ai-frontend
```

### Environment Security

- Never commit `.env` files to version control
- Use Docker secrets for sensitive values in production
- Rotate JWT secrets periodically
- Use strong database passwords (20+ characters)

---

## Troubleshooting Production

### Common Issues

**Database connection pool exhaustion:**
```yaml
# Increase pool size in config
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**Memory issues:**
```bash
# Check container memory usage
docker stats --format "table {{.Name}}\t{{.MemUsage}}"

# Increase memory limit
docker-compose up -d --scale backend=1 --build
# Modify deploy.resources.limits.memory in docker-compose.yml
```

**Slow ML inference:**
```bash
# Check if models are loaded
curl http://localhost:8000/health | jq '.ml_models_loaded'

# Retrain models
docker-compose exec backend python scripts/train_models.py
```

**High CPU from logging:**
```bash
# Reduce log level
# Edit backend/.env
LOG_LEVEL=WARNING  # Instead of DEBUG
```
