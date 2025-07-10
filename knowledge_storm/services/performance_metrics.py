"""
Performance monitoring and metrics for STORM academic research workloads.
Addresses Issue #65: Performance Optimization and Scalability for Academic Research Loads.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from contextlib import asynccontextmanager


@dataclass
class WarmCacheMetrics:
    """Metrics collected during warm_cache operations."""
    
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_duration_seconds: float = 0.0
    average_query_duration_seconds: float = 0.0
    max_concurrent_queries: int = 0
    parallel_setting: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_queries == 0:
            return 0.0
        return (self.successful_queries / self.total_queries) * 100.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        return 100.0 - self.success_rate


class PerformanceMonitor:
    """Monitor and collect performance metrics for academic research operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._metrics_history: list[WarmCacheMetrics] = []
        self._current_concurrent_queries = 0
        self._max_concurrent_queries = 0
    
    @asynccontextmanager
    async def track_warm_cache(self, total_queries: int, parallel: int):
        """Context manager to track warm_cache operation metrics."""
        
        metrics = WarmCacheMetrics(
            total_queries=total_queries,
            parallel_setting=parallel
        )
        
        start_time = time.time()
        self._current_concurrent_queries = 0
        self._max_concurrent_queries = 0
        
        try:
            yield metrics
        finally:
            end_time = time.time()
            metrics.total_duration_seconds = end_time - start_time
            metrics.max_concurrent_queries = self._max_concurrent_queries
            
            if metrics.successful_queries > 0:
                metrics.average_query_duration_seconds = (
                    metrics.total_duration_seconds / metrics.successful_queries
                )
            
            self._metrics_history.append(metrics)
            self._log_metrics(metrics)
    
    @asynccontextmanager
    async def track_query(self, metrics: WarmCacheMetrics):
        """Context manager to track individual query execution."""
        
        self._current_concurrent_queries += 1
        self._max_concurrent_queries = max(
            self._max_concurrent_queries, 
            self._current_concurrent_queries
        )
        
        try:
            yield
            metrics.successful_queries += 1
        except Exception as e:
            metrics.failed_queries += 1
            self.logger.debug(f"Query failed with error: {e}")
            raise
        finally:
            self._current_concurrent_queries -= 1
    
    def _log_metrics(self, metrics: WarmCacheMetrics):
        """Log performance metrics in structured format."""
        
        self.logger.info(
            "Warm cache operation completed",
            extra={
                "operation": "warm_cache",
                "total_queries": metrics.total_queries,
                "successful_queries": metrics.successful_queries,
                "failed_queries": metrics.failed_queries,
                "success_rate_percent": metrics.success_rate,
                "total_duration_seconds": metrics.total_duration_seconds,
                "average_query_duration_seconds": metrics.average_query_duration_seconds,
                "max_concurrent_queries": metrics.max_concurrent_queries,
                "parallel_setting": metrics.parallel_setting,
                "queries_per_second": (
                    metrics.successful_queries / metrics.total_duration_seconds
                    if metrics.total_duration_seconds > 0 else 0
                )
            }
        )
        
        # Alert on high failure rate
        if metrics.failure_rate > 20.0:
            self.logger.warning(
                f"High failure rate detected: {metrics.failure_rate:.1f}% "
                f"({metrics.failed_queries}/{metrics.total_queries} queries failed)"
            )
        
        # Alert on poor performance
        if metrics.total_duration_seconds > 300:  # 5 minutes
            self.logger.warning(
                f"Slow warm_cache operation: {metrics.total_duration_seconds:.1f}s "
                f"for {metrics.total_queries} queries"
            )
    
    def get_recent_metrics(self, limit: int = 10) -> list[WarmCacheMetrics]:
        """Get the most recent performance metrics."""
        return self._metrics_history[-limit:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all recorded operations."""
        
        if not self._metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = self._metrics_history[-10:]  # Last 10 operations
        
        return {
            "total_operations": len(self._metrics_history),
            "recent_operations": len(recent_metrics),
            "average_success_rate": sum(m.success_rate for m in recent_metrics) / len(recent_metrics),
            "average_duration": sum(m.total_duration_seconds for m in recent_metrics) / len(recent_metrics),
            "total_queries_processed": sum(m.total_queries for m in self._metrics_history),
            "total_successful_queries": sum(m.successful_queries for m in self._metrics_history),
            "total_failed_queries": sum(m.failed_queries for m in self._metrics_history),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience functions for external use
async def track_warm_cache_operation(total_queries: int, parallel: int):
    """Track a warm cache operation and return context manager."""
    return performance_monitor.track_warm_cache(total_queries, parallel)


async def track_individual_query(metrics: WarmCacheMetrics):
    """Track an individual query execution."""
    return performance_monitor.track_query(metrics)


def get_performance_summary() -> Dict[str, Any]:
    """Get current performance summary."""
    return performance_monitor.get_performance_summary()