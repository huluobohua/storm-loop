"""
Agent Monitoring Component
Single responsibility for monitoring agent activities
"""

from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
import threading


@dataclass
class AgentActivity:
    """Value object for agent activity data"""
    current_task: str
    task_data: Dict[str, Any]
    last_update: datetime


class AgentMonitor:
    """
    Monitors agent activities and status
    Adheres to Single Responsibility Principle
    """
    
    def __init__(self):
        self._agent_status = {}
        self._agent_activities = {}
        self._lock = threading.RLock()
    
    def register_agent(self, agent_name: str, status: str) -> None:
        """Register agent with initial status"""
        with self._lock:
            self._agent_status[agent_name] = {
                "status": status, 
                "last_update": datetime.now()
            }
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current agent status"""
        with self._lock:
            return self._agent_status.copy()
    
    def update_agent_activity(self, agent_name: str, task: str, task_data: Dict[str, Any]) -> None:
        """Update agent activity"""
        with self._lock:
            self._agent_activities[agent_name] = AgentActivity(
                current_task=task,
                task_data=task_data,
                last_update=datetime.now()
            )
    
    def get_agent_activity(self, agent_name: str) -> Dict[str, Any]:
        """Get agent activity"""
        with self._lock:
            activity = self._agent_activities.get(agent_name)
            if activity:
                return {
                    "current_task": activity.current_task,
                    "task_data": activity.task_data,
                    "last_update": activity.last_update
                }
            return {}