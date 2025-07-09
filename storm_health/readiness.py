"""
Kubernetes readiness and liveness probes implementation
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import logging
from dataclasses import dataclass
from enum import Enum

from .health_checks import HealthCheckManager, HealthStatus, HealthCheckResult

logger = logging.getLogger(__name__)


class ProbeStatus(Enum):
    """Probe status results"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass
class ProbeResult:
    """Result of a probe check"""
    probe_type: str
    status: ProbeStatus
    message: str = ""
    checks: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.checks is None:
            self.checks = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "probe_type": self.probe_type,
            "status": self.status.value,
            "message": self.message,
            "checks": self.checks,
            "timestamp": self.timestamp.isoformat()
        }


class ReadinessProbe:
    """
    Kubernetes readiness probe - checks if application is ready to serve traffic
    """
    
    def __init__(self, health_manager: HealthCheckManager):
        self.health_manager = health_manager
        self.startup_grace_period = int(os.getenv("READINESS_GRACE_PERIOD", "30"))
        self.startup_time = datetime.now(timezone.utc)
        
        # Critical checks for readiness
        self.critical_checks = [
            "database",
            "redis",
            "api_authentication"
        ]
        
        # Optional checks that can be degraded
        self.optional_checks = [
            "api_openai",
            "api_anthropic",
            "api_google"
        ]
    
    async def check(self) -> ProbeResult:
        """
        Perform readiness check
        Returns success if all critical services are healthy
        """
        # Check if still in startup grace period
        if self._in_grace_period():
            return ProbeResult(
                probe_type="readiness",
                status=ProbeStatus.SUCCESS,
                message="In startup grace period"
            )
        
        try:
            # Run health checks
            results = await self.health_manager.run_all_checks()
            
            # Check critical services
            critical_results = {}
            all_critical_healthy = True
            
            for check_name in self.critical_checks:
                if check_name in results:
                    result = results[check_name]
                    critical_results[check_name] = result.status.value
                    
                    if result.status != HealthStatus.HEALTHY:
                        all_critical_healthy = False
                        logger.warning(
                            f"Critical service unhealthy: {check_name} - {result.message}"
                        )
                else:
                    # Missing critical check
                    critical_results[check_name] = "missing"
                    all_critical_healthy = False
            
            # Check optional services (for logging)
            optional_results = {}
            for check_name in self.optional_checks:
                if check_name in results:
                    result = results[check_name]
                    optional_results[check_name] = result.status.value
                    
                    if result.status != HealthStatus.HEALTHY:
                        logger.info(
                            f"Optional service degraded: {check_name} - {result.message}"
                        )
            
            # Determine overall readiness
            if all_critical_healthy:
                return ProbeResult(
                    probe_type="readiness",
                    status=ProbeStatus.SUCCESS,
                    message="All critical services healthy",
                    checks={
                        "critical": critical_results,
                        "optional": optional_results
                    }
                )
            else:
                return ProbeResult(
                    probe_type="readiness",
                    status=ProbeStatus.FAILURE,
                    message="Critical services unhealthy",
                    checks={
                        "critical": critical_results,
                        "optional": optional_results
                    }
                )
                
        except asyncio.TimeoutError:
            return ProbeResult(
                probe_type="readiness",
                status=ProbeStatus.TIMEOUT,
                message="Health check timeout"
            )
        except Exception as e:
            logger.error(f"Readiness probe error: {e}")
            return ProbeResult(
                probe_type="readiness",
                status=ProbeStatus.FAILURE,
                message=f"Probe error: {str(e)}"
            )
    
    def _in_grace_period(self) -> bool:
        """Check if still within startup grace period"""
        elapsed = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        return elapsed < self.startup_grace_period


class LivenessProbe:
    """
    Kubernetes liveness probe - checks if application should be restarted
    """
    
    def __init__(self, health_manager: HealthCheckManager):
        self.health_manager = health_manager
        self.failure_threshold = int(os.getenv("LIVENESS_FAILURE_THRESHOLD", "3"))
        self.consecutive_failures = 0
        self.last_success = datetime.now(timezone.utc)
        
        # Deadlock detection
        self.deadlock_timeout = int(os.getenv("DEADLOCK_TIMEOUT", "300"))  # 5 minutes
        self.last_request_time = datetime.now(timezone.utc)
        
        # Memory threshold
        self.memory_threshold = float(os.getenv("MEMORY_THRESHOLD", "90.0"))
    
    async def check(self) -> ProbeResult:
        """
        Perform liveness check
        Returns failure if application is in unrecoverable state
        """
        try:
            # Check for deadlock
            if self._check_deadlock():
                return ProbeResult(
                    probe_type="liveness",
                    status=ProbeStatus.FAILURE,
                    message="Possible deadlock detected"
                )
            
            # Check memory usage
            memory_check = await self._check_memory()
            if not memory_check["healthy"]:
                self.consecutive_failures += 1
                
                if self.consecutive_failures >= self.failure_threshold:
                    return ProbeResult(
                        probe_type="liveness",
                        status=ProbeStatus.FAILURE,
                        message=f"Memory threshold exceeded: {memory_check['percent']:.1f}%",
                        checks={"memory": memory_check}
                    )
            
            # Check basic application responsiveness
            app_check = await self._check_app_responsiveness()
            if not app_check["healthy"]:
                self.consecutive_failures += 1
                
                if self.consecutive_failures >= self.failure_threshold:
                    return ProbeResult(
                        probe_type="liveness",
                        status=ProbeStatus.FAILURE,
                        message="Application unresponsive",
                        checks={"app": app_check}
                    )
            
            # All checks passed
            self.consecutive_failures = 0
            self.last_success = datetime.now(timezone.utc)
            
            return ProbeResult(
                probe_type="liveness",
                status=ProbeStatus.SUCCESS,
                message="Application is alive",
                checks={
                    "memory": memory_check,
                    "app": app_check,
                    "consecutive_failures": self.consecutive_failures
                }
            )
            
        except Exception as e:
            logger.error(f"Liveness probe error: {e}")
            self.consecutive_failures += 1
            
            if self.consecutive_failures >= self.failure_threshold:
                return ProbeResult(
                    probe_type="liveness",
                    status=ProbeStatus.FAILURE,
                    message=f"Probe error: {str(e)}"
                )
            else:
                return ProbeResult(
                    probe_type="liveness",
                    status=ProbeStatus.SUCCESS,
                    message=f"Probe error but under threshold: {str(e)}"
                )
    
    def _check_deadlock(self) -> bool:
        """Check for potential deadlock"""
        time_since_last_request = (
            datetime.now(timezone.utc) - self.last_request_time
        ).total_seconds()
        
        return time_since_last_request > self.deadlock_timeout
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                "healthy": memory.percent < self.memory_threshold,
                "percent": memory.percent,
                "available_mb": memory.available / (1024 * 1024),
                "total_mb": memory.total / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Memory check error: {e}")
            return {
                "healthy": True,  # Don't fail on check error
                "error": str(e)
            }
    
    async def _check_app_responsiveness(self) -> Dict[str, Any]:
        """Check if application can respond to basic requests"""
        try:
            # Simple computation to verify event loop is responsive
            start_time = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # If sleep took much longer than expected, event loop might be blocked
            responsive = elapsed < 0.5  # 500ms threshold
            
            return {
                "healthy": responsive,
                "response_time_ms": elapsed * 1000
            }
        except Exception as e:
            logger.error(f"App responsiveness check error: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def update_request_time(self):
        """Update last request time for deadlock detection"""
        self.last_request_time = datetime.now(timezone.utc)


class StartupProbe:
    """
    Kubernetes startup probe - allows longer startup time
    """
    
    def __init__(self, health_manager: HealthCheckManager):
        self.health_manager = health_manager
        self.startup_timeout = int(os.getenv("STARTUP_TIMEOUT", "300"))  # 5 minutes
        self.startup_time = datetime.now(timezone.utc)
        self.startup_complete = False
        
        # Services that must be ready for startup
        self.startup_checks = [
            "database",
            "redis"
        ]
    
    async def check(self) -> ProbeResult:
        """
        Perform startup check
        Returns success when application has fully started
        """
        if self.startup_complete:
            return ProbeResult(
                probe_type="startup",
                status=ProbeStatus.SUCCESS,
                message="Startup complete"
            )
        
        # Check if startup timeout exceeded
        elapsed = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        if elapsed > self.startup_timeout:
            return ProbeResult(
                probe_type="startup",
                status=ProbeStatus.FAILURE,
                message=f"Startup timeout exceeded ({self.startup_timeout}s)"
            )
        
        try:
            # Check startup services
            results = {}
            all_ready = True
            
            for check_name in self.startup_checks:
                result = await self.health_manager.run_check(check_name)
                results[check_name] = result.status.value
                
                if result.status != HealthStatus.HEALTHY:
                    all_ready = False
                    logger.info(f"Waiting for {check_name} to be ready: {result.message}")
            
            if all_ready:
                self.startup_complete = True
                logger.info("Startup probe complete - all services ready")
                
                return ProbeResult(
                    probe_type="startup",
                    status=ProbeStatus.SUCCESS,
                    message="All startup services ready",
                    checks=results
                )
            else:
                return ProbeResult(
                    probe_type="startup",
                    status=ProbeStatus.FAILURE,
                    message=f"Waiting for services (elapsed: {elapsed:.0f}s)",
                    checks=results
                )
                
        except Exception as e:
            logger.error(f"Startup probe error: {e}")
            return ProbeResult(
                probe_type="startup",
                status=ProbeStatus.FAILURE,
                message=f"Probe error: {str(e)}"
            )