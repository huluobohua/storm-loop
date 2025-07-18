"""
Progress Tracking Component
Single responsibility for tracking research progress
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import threading


@dataclass
class ProgressInfo:
    """Value object for progress information"""
    completion: float
    status_message: str
    last_update: datetime


class ProgressTracker:
    """
    Tracks progress for research stages
    Adheres to Single Responsibility Principle
    """
    
    def __init__(self):
        self._progress_stages = []
        self._stage_progress = {}
        self._lock = threading.RLock()
    
    def initialize_progress(self, stages: List[str]) -> None:
        """Initialize progress tracking"""
        with self._lock:
            self._progress_stages = stages
            self._stage_progress = {
                stage: ProgressInfo(0.0, "Not started", datetime.now()) 
                for stage in stages
            }
    
    def update_progress(self, stage: str, completion: float, message: str) -> None:
        """Update progress for a stage"""
        with self._lock:
            if stage in self._stage_progress:
                self._stage_progress[stage] = ProgressInfo(
                    completion=completion,
                    status_message=message,
                    last_update=datetime.now()
                )
    
    def get_overall_progress(self) -> Dict[str, Any]:
        """Get overall progress"""
        with self._lock:
            stage_data = {}
            total_completion = 0.0
            completed_stages = 0
            
            for stage, progress in self._stage_progress.items():
                stage_data[stage] = {
                    "completion": progress.completion,
                    "status_message": progress.status_message,
                    "last_update": progress.last_update
                }
                
                if progress.completion >= 1.0:
                    completed_stages += 1
                    total_completion += progress.completion
                elif progress.completion > 0:
                    total_completion += progress.completion
            
            overall_completion = total_completion / len(self._progress_stages) if self._progress_stages else 0
            
            return {
                **stage_data,
                "overall_completion": overall_completion,
                "completed_stages": completed_stages,
                "total_stages": len(self._progress_stages)
            }
    
    def get_estimated_completion_time(self) -> float:
        """Get estimated completion time in seconds"""
        # Simple estimation based on current progress
        progress = self.get_overall_progress()
        if progress["overall_completion"] == 0:
            return 3600  # Default 1 hour
        
        # Calculate based on current progress rate
        elapsed_time = 300  # Assume 5 minutes elapsed for demo
        completion_rate = progress["overall_completion"] / elapsed_time
        remaining_work = 1.0 - progress["overall_completion"]
        
        return remaining_work / completion_rate if completion_rate > 0 else 1800