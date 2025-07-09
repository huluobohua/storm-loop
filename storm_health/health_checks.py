"""
Comprehensive health check system for production monitoring
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import psutil
import aiohttp
import asyncpg
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class HealthCheckManager:
    """
    Manages all health checks for the application
    """
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.check_intervals: Dict[str, int] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Metrics
        self.health_check_duration = Histogram(
            'storm_health_check_duration_seconds',
            'Duration of health checks',
            ['check_name']
        )
        self.health_check_status = Gauge(
            'storm_health_check_status',
            'Current health check status (1=healthy, 0.5=degraded, 0=unhealthy)',
            ['check_name']
        )
        self.health_check_total = Counter(
            'storm_health_check_total',
            'Total number of health checks',
            ['check_name', 'status']
        )
    
    def register_check(
        self,
        name: str,
        check_func: Callable,
        interval_seconds: int = 30
    ):
        """Register a health check"""
        self.checks[name] = check_func
        self.check_intervals[name] = interval_seconds
        logger.info(f"Registered health check: {name} (interval: {interval_seconds}s)")
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a single health check"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Check '{name}' not registered"
            )
        
        start_time = time.time()
        try:
            result = await self.checks[name]()
            duration_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            self.health_check_duration.labels(check_name=name).observe(duration_ms / 1000)
            self.health_check_total.labels(check_name=name, status=result.status.value).inc()
            
            status_value = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.DEGRADED: 0.5,
                HealthStatus.UNHEALTHY: 0.0,
                HealthStatus.UNKNOWN: 0.0
            }[result.status]
            self.health_check_status.labels(check_name=name).set(status_value)
            
            result.duration_ms = duration_ms
            self.last_results[name] = result
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {str(e)}")
            
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=duration_ms
            )
            
            self.health_check_duration.labels(check_name=name).observe(duration_ms / 1000)
            self.health_check_total.labels(check_name=name, status="unhealthy").inc()
            self.health_check_status.labels(check_name=name).set(0.0)
            
            self.last_results[name] = result
            return result
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        results = await asyncio.gather(
            *[self.run_check(name) for name in self.checks.keys()],
            return_exceptions=True
        )
        
        return {
            name: result if isinstance(result, HealthCheckResult) else HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(result)}"
            )
            for name, result in zip(self.checks.keys(), results)
        }
    
    async def _periodic_check(self, name: str):
        """Run a health check periodically"""
        interval = self.check_intervals[name]
        while self._running:
            try:
                await self.run_check(name)
            except Exception as e:
                logger.error(f"Error in periodic check '{name}': {e}")
            
            await asyncio.sleep(interval)
    
    async def start(self):
        """Start periodic health checks"""
        self._running = True
        self._tasks = [
            asyncio.create_task(self._periodic_check(name))
            for name in self.checks.keys()
        ]
        logger.info("Started health check manager")
    
    async def stop(self):
        """Stop periodic health checks"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Stopped health check manager")
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.last_results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self.last_results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        overall_status = self.get_overall_status()
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                name: result.to_dict()
                for name, result in self.last_results.items()
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        }


# Predefined health checks

async def check_database(
    connection_string: str,
    timeout: float = 5.0
) -> HealthCheckResult:
    """Check PostgreSQL database health"""
    try:
        conn = await asyncpg.connect(connection_string, timeout=timeout)
        
        # Check basic connectivity
        result = await conn.fetchval("SELECT 1")
        if result != 1:
            raise Exception("Unexpected query result")
        
        # Check database size
        db_size = await conn.fetchval("""
            SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb
        """)
        
        # Check connection count
        conn_count = await conn.fetchval("""
            SELECT count(*) FROM pg_stat_activity
        """)
        
        await conn.close()
        
        return HealthCheckResult(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database is responsive",
            metadata={
                "size_mb": db_size,
                "connections": conn_count
            }
        )
        
    except asyncio.TimeoutError:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message="Database connection timeout"
        )
    except Exception as e:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {str(e)}"
        )


async def check_redis(
    redis_url: str,
    timeout: float = 5.0
) -> HealthCheckResult:
    """Check Redis health"""
    try:
        client = redis.from_url(redis_url, socket_connect_timeout=timeout)
        
        # Check basic connectivity
        await client.ping()
        
        # Get memory info
        info = await client.info("memory")
        used_memory_mb = info.get("used_memory", 0) / 1024 / 1024
        max_memory_mb = info.get("maxmemory", 0) / 1024 / 1024
        
        # Check keyspace
        keyspace_info = await client.info("keyspace")
        total_keys = sum(
            int(db_info.split(",")[0].split("=")[1])
            for db_info in keyspace_info.values()
            if isinstance(db_info, str) and "keys=" in db_info
        )
        
        await client.close()
        
        # Determine status based on memory usage
        if max_memory_mb > 0:
            memory_percent = (used_memory_mb / max_memory_mb) * 100
            if memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Redis memory usage critical: {memory_percent:.1f}%"
            elif memory_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Redis memory usage high: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis is healthy"
        else:
            status = HealthStatus.HEALTHY
            message = "Redis is healthy"
        
        return HealthCheckResult(
            name="redis",
            status=status,
            message=message,
            metadata={
                "used_memory_mb": used_memory_mb,
                "max_memory_mb": max_memory_mb,
                "total_keys": total_keys
            }
        )
        
    except Exception as e:
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis error: {str(e)}"
        )


async def check_external_api(
    api_name: str,
    test_endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0
) -> HealthCheckResult:
    """Check external API availability"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                test_endpoint,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                if response.status == 200:
                    return HealthCheckResult(
                        name=f"api_{api_name}",
                        status=HealthStatus.HEALTHY,
                        message=f"{api_name} API is accessible",
                        metadata={
                            "status_code": response.status,
                            "response_time_ms": response.headers.get("X-Response-Time", "unknown")
                        }
                    )
                else:
                    return HealthCheckResult(
                        name=f"api_{api_name}",
                        status=HealthStatus.DEGRADED,
                        message=f"{api_name} API returned status {response.status}",
                        metadata={"status_code": response.status}
                    )
                    
    except asyncio.TimeoutError:
        return HealthCheckResult(
            name=f"api_{api_name}",
            status=HealthStatus.UNHEALTHY,
            message=f"{api_name} API timeout"
        )
    except Exception as e:
        return HealthCheckResult(
            name=f"api_{api_name}",
            status=HealthStatus.UNHEALTHY,
            message=f"{api_name} API error: {str(e)}"
        )


async def check_disk_space(
    path: str = "/",
    warning_threshold: float = 80.0,
    critical_threshold: float = 90.0
) -> HealthCheckResult:
    """Check disk space availability"""
    try:
        usage = psutil.disk_usage(path)
        percent_used = usage.percent
        
        if percent_used >= critical_threshold:
            status = HealthStatus.UNHEALTHY
            message = f"Disk space critical: {percent_used:.1f}% used"
        elif percent_used >= warning_threshold:
            status = HealthStatus.DEGRADED
            message = f"Disk space warning: {percent_used:.1f}% used"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk space healthy: {percent_used:.1f}% used"
        
        return HealthCheckResult(
            name="disk_space",
            status=status,
            message=message,
            metadata={
                "path": path,
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "percent_used": percent_used
            }
        )
        
    except Exception as e:
        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.UNHEALTHY,
            message=f"Disk check error: {str(e)}"
        )