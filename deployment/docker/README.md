# Docker Configuration for STORM

This directory contains the Docker configuration for the STORM Academic Research Platform.

## Security Features

- **Multi-stage build** for minimal final image size
- **Non-root user** (stormuser) for security
- **No unnecessary packages** in production stage
- **Health checks** built into the container
- **Environment variable support** for configuration

## Building

```bash
# Build the Docker image
docker build -f deployment/docker/Dockerfile -t storm-app:latest .

# Build with specific Python version
docker build -f deployment/docker/Dockerfile --build-arg PYTHON_VERSION=3.11 -t storm-app:latest .
```

## Running

```bash
# Run with environment variables
docker run -p 8501:8501 --env-file .env storm-app:latest

# Run with volume mounts for data persistence
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  storm-app:latest
```

## Environment Variables

Required environment variables:
- `STORM_ENV`: Environment (development/staging/production)
- `STORM_DATA_DIR`: Data directory path
- `STORM_LOG_DIR`: Log directory path
- `STORM_CACHE_DIR`: Cache directory path

## Health Check

The container includes a health check that queries the Streamlit health endpoint:
- Endpoint: `http://localhost:8501/_stcore/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

## Security Considerations

1. The image runs as a non-root user (UID 1000)
2. All Python dependencies are installed in the builder stage
3. Only runtime dependencies are included in the final image
4. The application directories are owned by the non-root user
5. No shell or package managers in the final image (for reduced attack surface)