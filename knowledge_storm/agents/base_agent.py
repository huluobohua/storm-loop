"""
Base agent infrastructure for STORM-Academic multi-agent system.

Provides foundational classes and interfaces for specialized agents.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents a specific capability of an agent."""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    confidence_level: float = 1.0  # 0.0 to 1.0


@dataclass 
class AgentMessage:
    """Message for inter-agent communication."""
    sender_id: str
    recipient_id: str
    message_type: str
    content: Any
    timestamp: datetime
    correlation_id: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all agents in the STORM-Academic system.
    
    Provides common functionality and interfaces for specialized agents.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 capabilities: Optional[List[AgentCapability]] = None):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        
        # Agent state
        self.is_active = True
        self.last_activity = datetime.now()
        self.task_history = []
        
        logger.info(f"Initialized agent: {self.name} ({self.agent_id})")
    
    @abstractmethod
    async def execute_task(self, task: Any) -> Dict[str, Any]:
        """Execute a task assigned to this agent."""
        pass
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get list of agent capabilities."""
        return self.capabilities
    
    def can_handle_task(self, task_type: str) -> bool:
        """Check if agent can handle a specific task type."""
        return any(cap.name == task_type for cap in self.capabilities)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'is_active': self.is_active,
            'last_activity': self.last_activity.isoformat(),
            'capabilities_count': len(self.capabilities),
            'tasks_completed': len(self.task_history)
        }
    
    def record_task_completion(self, task_result: Dict[str, Any]):
        """Record completion of a task."""
        self.task_history.append({
            'timestamp': datetime.now(),
            'success': task_result.get('success', False),
            'task_type': task_result.get('task_type', 'unknown')
        })
        self.last_activity = datetime.now()


class AgentRegistry:
    """Registry for managing agents in the system."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.capabilities_index: Dict[str, List[str]] = {}  # capability -> agent_ids
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent in the system."""
        self.agents[agent.agent_id] = agent
        
        # Index capabilities
        for capability in agent.capabilities:
            if capability.name not in self.capabilities_index:
                self.capabilities_index[capability.name] = []
            self.capabilities_index[capability.name].append(agent.agent_id)
        
        logger.info(f"Registered agent: {agent.name} with {len(agent.capabilities)} capabilities")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def find_agents_for_capability(self, capability_name: str) -> List[BaseAgent]:
        """Find all agents that have a specific capability."""
        agent_ids = self.capabilities_index.get(capability_name, [])
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(self.agents.values())
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        active_agents = [agent for agent in self.agents.values() if agent.is_active]
        
        return {
            'total_agents': len(self.agents),
            'active_agents': len(active_agents),
            'total_capabilities': len(self.capabilities_index),
            'agent_summary': [agent.get_status() for agent in active_agents]
        }


# Export main classes
__all__ = [
    'BaseAgent',
    'AgentCapability', 
    'AgentMessage',
    'AgentRegistry'
]