"""
Quality Metrics Tracking Component
Single responsibility for tracking quality metrics
"""

from typing import Dict
import threading


class QualityMetricsTracker:
    """
    Tracks quality metrics during research
    Adheres to Single Responsibility Principle
    """
    
    def __init__(self):
        self._quality_metrics = {}
        self._lock = threading.RLock()
    
    def update_quality_metric(self, metric_name: str, value: float) -> None:
        """Update quality metric"""
        with self._lock:
            self._quality_metrics[metric_name] = value
    
    def get_quality_metrics(self) -> Dict[str, float]:
        """Get quality metrics"""
        with self._lock:
            return self._quality_metrics.copy()