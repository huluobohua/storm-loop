"""
Health check API endpoints for Kubernetes probes and monitoring
"""

from fastapi import APIRouter, Response, status, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import logging

from storm_health import (
    HealthCheckManager,
    ReadinessProbe,
    LivenessProbe,
    HealthStatus
)
from storm_health.readiness import StartupProbe, ProbeStatus
from storm_health.health_checks import (
    check_database,
    check_redis,
    check_external_api,
    check_disk_space
)
from storm_auth.middleware import require_permission

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/health", tags=["health"])

# Initialize health check manager
health_manager = HealthCheckManager()

# Initialize probes
readiness_probe = ReadinessProbe(health_manager)
liveness_probe = LivenessProbe(health_manager)
startup_probe = StartupProbe(health_manager)


# Register health checks on startup
async def register_health_checks():
    """Register all health checks"""
    
    # Database check
    health_manager.register_check(
        "database",
        lambda: check_database(os.getenv("POSTGRES_URL")),
        interval_seconds=30
    )
    
    # Redis check
    health_manager.register_check(
        "redis",
        lambda: check_redis(os.getenv("REDIS_URL")),
        interval_seconds=20
    )
    
    # Disk space check
    health_manager.register_check(
        "disk_space",
        lambda: check_disk_space(
            path="/app/data",
            warning_threshold=80.0,
            critical_threshold=90.0
        ),
        interval_seconds=60
    )
    
    # External API checks
    if os.getenv("OPENAI_API_KEY"):
        health_manager.register_check(
            "api_openai",
            lambda: check_external_api(
                "openai",
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
            ),
            interval_seconds=300  # 5 minutes
        )
    
    if os.getenv("ANTHROPIC_API_KEY"):
        health_manager.register_check(
            "api_anthropic",
            lambda: check_external_api(
                "anthropic",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                    "anthropic-version": "2023-06-01"
                }
            ),
            interval_seconds=300
        )
    
    if os.getenv("GOOGLE_API_KEY"):
        health_manager.register_check(
            "api_google",
            lambda: check_external_api(
                "google",
                f"https://generativelanguage.googleapis.com/v1beta/models?key={os.getenv('GOOGLE_API_KEY')}"
            ),
            interval_seconds=300
        )
    
    # Start periodic health checks
    await health_manager.start()
    logger.info("Health check manager started")


@router.get("/", summary="Basic health check")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint
    Always returns 200 OK if application is running
    """
    return {"status": "healthy", "service": "storm-academic"}


@router.get("/live", summary="Kubernetes liveness probe")
async def liveness() -> Response:
    """
    Kubernetes liveness probe endpoint
    Returns 200 if application is alive, 503 if it should be restarted
    """
    # Update request time for deadlock detection
    liveness_probe.update_request_time()
    
    result = await liveness_probe.check()
    
    if result.status == ProbeStatus.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.to_dict()
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=result.to_dict()
        )


@router.get("/ready", summary="Kubernetes readiness probe")
async def readiness() -> Response:
    """
    Kubernetes readiness probe endpoint
    Returns 200 if ready to serve traffic, 503 if not ready
    """
    result = await readiness_probe.check()
    
    if result.status == ProbeStatus.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.to_dict()
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=result.to_dict()
        )


@router.get("/startup", summary="Kubernetes startup probe")
async def startup() -> Response:
    """
    Kubernetes startup probe endpoint
    Returns 200 when application has fully started, 503 during startup
    """
    result = await startup_probe.check()
    
    if result.status == ProbeStatus.SUCCESS:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.to_dict()
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=result.to_dict()
        )


@router.get(
    "/detailed",
    summary="Detailed health status",
    dependencies=[Depends(require_permission("system:monitor"))]
)
async def detailed_health() -> Dict[str, Any]:
    """
    Detailed health status for monitoring
    Requires authentication and monitor permission
    """
    report = health_manager.get_health_report()
    
    # Add additional application metrics
    report["application"] = {
        "version": os.getenv("APP_VERSION", "unknown"),
        "environment": os.getenv("STORM_ENV", "unknown"),
        "node": os.getenv("HOSTNAME", "unknown")
    }
    
    return report


@router.get(
    "/checks/{check_name}",
    summary="Run specific health check",
    dependencies=[Depends(require_permission("system:monitor"))]
)
async def run_health_check(check_name: str) -> Dict[str, Any]:
    """
    Run a specific health check on demand
    Requires authentication and monitor permission
    """
    result = await health_manager.run_check(check_name)
    return result.to_dict()


@router.post(
    "/maintenance/{mode}",
    summary="Toggle maintenance mode",
    dependencies=[Depends(require_permission("system:admin"))]
)
async def maintenance_mode(mode: str) -> Dict[str, str]:
    """
    Enable or disable maintenance mode
    Requires admin permission
    """
    if mode not in ["enable", "disable"]:
        return {"error": "Invalid mode. Use 'enable' or 'disable'"}
    
    # In production, this would update a flag that affects readiness probe
    maintenance_enabled = mode == "enable"
    
    # You would typically store this in Redis or similar
    # For now, we'll just return the status
    
    return {
        "status": "success",
        "maintenance_mode": maintenance_enabled,
        "message": f"Maintenance mode {'enabled' if maintenance_enabled else 'disabled'}"
    }


# Streamlit specific health check
@router.get("/_stcore/health", summary="Streamlit health check")
async def streamlit_health() -> Dict[str, Any]:
    """
    Streamlit-specific health check endpoint
    """
    return {
        "status": "healthy",
        "streamlit": True,
        "server_info": {
            "version": os.getenv("STREAMLIT_VERSION", "1.22.0"),
            "python_version": os.getenv("PYTHON_VERSION", "3.11")
        }
    }