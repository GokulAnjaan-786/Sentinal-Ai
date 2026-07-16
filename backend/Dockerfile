# ==========================================
# SentinelAI Backend Dockerfile
# ==========================================
# Multi-stage build for optimized production image
#
# Stage 1: Build dependencies
# Stage 2: Production image with minimal footprint

# ---- Stage 1: Builder ----
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching optimization)
COPY backend/requirements.txt .

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --retries 5 --timeout 120 --upgrade pip && \
    pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt


# ---- Stage 2: Production ----
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    APP_DEBUG=false

# Create non-root user for security
RUN groupadd -r sentinelai && useradd -r -g sentinelai -d /app -s /sbin/nologin sentinelai

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p logs app/ml/data/models app/ml/data

# Set ownership
RUN chown -R sentinelai:sentinelai /app

# Switch to non-root user
USER sentinelai

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the application port
EXPOSE 8000

# Run the application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
