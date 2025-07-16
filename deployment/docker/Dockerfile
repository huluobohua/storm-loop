# Multi-stage build for production-grade Python application
# Support configurable Python version
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better cache utilization
COPY deployment/docker/requirements.txt .
COPY setup.py* .
COPY pyproject.toml* .

# Install Python dependencies with pinned versions
# Note: For production, use --require-hashes with pip-compile generated hashes
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash stormuser

# Set work directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (filtered by .dockerignore)
COPY --chown=stormuser:stormuser . .

# Create necessary directories with proper ownership
RUN mkdir -p /app/data /app/logs /app/cache

# Environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STORM_ENV=production \
    STORM_DATA_DIR=/app/data \
    STORM_LOG_DIR=/app/logs \
    STORM_CACHE_DIR=/app/cache

# Switch to non-root user
USER stormuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose Streamlit port
EXPOSE 8501

# Run the application
# Note: CORS is enabled for proper browser functionality when behind proxies/gateways
# XSRF protection remains enabled for security
CMD ["streamlit", "run", "frontend/demo_light/storm_stable.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=true", \
     "--server.enableXsrfProtection=true"]