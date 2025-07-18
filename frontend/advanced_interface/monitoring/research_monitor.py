"""
Research Monitor Facade
Orchestrates all monitoring components
"""

from typing import Dict, List, Any
import threading
from .progress_tracker import ProgressTracker
from .agent_monitor import AgentMonitor
from .resource_monitor import ResourceMonitor
from .quality_metrics_tracker import QualityMetricsTracker


class ResearchMonitor:
    """
    Facade for all monitoring components
    Adheres to Facade Pattern and Single Responsibility Principle
    """
    
    def __init__(self):
        self.progress_tracker = ProgressTracker()
        self.agent_monitor = AgentMonitor()
        self.resource_monitor = ResourceMonitor()
        self.quality_tracker = QualityMetricsTracker()
        
        self._paused = False
        self._pause_reason = ""
        self._current_parameters = {}
        self._lock = threading.RLock()
    
    # Delegate to progress tracker
    def initialize_progress(self, stages: List[str]) -> None:
        self.progress_tracker.initialize_progress(stages)
    
    def update_progress(self, stage: str, completion: float, message: str) -> None:
        self.progress_tracker.update_progress(stage, completion, message)
    
    def get_overall_progress(self) -> Dict[str, Any]:
        return self.progress_tracker.get_overall_progress()
    
    def get_estimated_completion_time(self) -> float:
        return self.progress_tracker.get_estimated_completion_time()
    
    # Delegate to agent monitor
    def register_agent(self, agent_name: str, status: str) -> None:
        self.agent_monitor.register_agent(agent_name, status)
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        return self.agent_monitor.get_agent_status()
    
    def update_agent_activity(self, agent_name: str, task: str, task_data: Dict[str, Any]) -> None:
        self.agent_monitor.update_agent_activity(agent_name, task, task_data)
    
    def get_agent_activity(self, agent_name: str) -> Dict[str, Any]:
        return self.agent_monitor.get_agent_activity(agent_name)
    
    # Delegate to resource monitor
    def track_api_usage(self, api_name: str, usage_count: int) -> None:
        self.resource_monitor.track_api_usage(api_name, usage_count)
    
    def get_api_usage(self) -> Dict[str, int]:
        return self.resource_monitor.get_api_usage()
    
    def update_memory_usage(self, usage_mb: int) -> None:
        self.resource_monitor.update_memory_usage(usage_mb)
    
    def get_memory_usage(self) -> int:
        return self.resource_monitor.get_memory_usage()
    
    def track_processing_time(self, phase: str, time_seconds: float) -> None:
        self.resource_monitor.track_processing_time(phase, time_seconds)
    
    def get_processing_time(self, phase: str) -> float:
        return self.resource_monitor.get_processing_time(phase)
    
    # Delegate to quality tracker
    def update_quality_metric(self, metric_name: str, value: float) -> None:
        self.quality_tracker.update_quality_metric(metric_name, value)
    
    def get_quality_metrics(self) -> Dict[str, float]:
        return self.quality_tracker.get_quality_metrics()
    
    # Research control methods
    def pause_research(self, reason: str) -> None:
        with self._lock:
            self._paused = True
            self._pause_reason = reason
    
    def resume_research(self) -> None:
        with self._lock:
            self._paused = False
            self._pause_reason = ""
    
    def is_paused(self) -> bool:
        with self._lock:
            return self._paused
    
    @property
    def pause_reason(self) -> str:
        with self._lock:
            return self._pause_reason
    
    def adjust_research_parameters(self, parameters: Dict[str, Any]) -> None:
        with self._lock:
            self._current_parameters.update(parameters)
    
    def get_current_parameters(self) -> Dict[str, Any]:
        with self._lock:
            return self._current_parameters.copy()