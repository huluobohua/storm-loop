"""
Resource Monitoring Component
Single responsibility for monitoring system resources
"""

from typing import Dict, Any
import threading


class ResourceMonitor:
    """
    Monitors system resources and API usage
    Adheres to Single Responsibility Principle
    """
    
    def __init__(self):
        self._api_usage = {}
        self._memory_usage = 0
        self._processing_times = {}
        self._lock = threading.RLock()
    
    def track_api_usage(self, api_name: str, usage_count: int) -> None:
        """Track API usage"""
        with self._lock:
            self._api_usage[api_name] = usage_count
    
    def get_api_usage(self) -> Dict[str, int]:
        """Get API usage statistics"""
        with self._lock:
            return self._api_usage.copy()
    
    def update_memory_usage(self, usage_mb: int) -> None:
        """Update memory usage"""
        with self._lock:
            self._memory_usage = usage_mb
    
    def get_memory_usage(self) -> int:
        """Get memory usage in MB"""
        with self._lock:
            return self._memory_usage
    
    def track_processing_time(self, phase: str, time_seconds: float) -> None:
        """Track processing time for a phase"""
        with self._lock:
            self._processing_times[phase] = time_seconds
    
    def get_processing_time(self, phase: str) -> float:
        """Get processing time for a phase"""
        with self._lock:
            return self._processing_times.get(phase, 0.0)