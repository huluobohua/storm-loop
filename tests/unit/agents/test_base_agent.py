"""
Unit tests for BaseAgent infrastructure.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from knowledge_storm.agents.base_agent import (
    BaseAgent, 
    AgentCapability, 
    AgentMessage, 
    AgentRegistry
)


class TestAgentCapability:
    """Test suite for AgentCapability dataclass."""
    
    def test_agent_capability_creation(self):
        """Test creating AgentCapability with all fields."""
        capability = AgentCapability(
            name="test_capability",
            description="Test capability description",
            input_types=["str", "dict"],
            output_types=["dict"],
            confidence_level=0.95
        )
        
        assert capability.name == "test_capability"
        assert capability.description == "Test capability description"
        assert capability.input_types == ["str", "dict"]
        assert capability.output_types == ["dict"]
        assert capability.confidence_level == 0.95
    
    def test_agent_capability_default_confidence(self):
        """Test AgentCapability default confidence level."""
        capability = AgentCapability(
            name="test_capability",
            description="Test capability description",
            input_types=["str"],
            output_types=["dict"]
        )
        
        assert capability.confidence_level == 1.0


class TestAgentMessage:
    """Test suite for AgentMessage dataclass."""
    
    def test_agent_message_creation(self):
        """Test creating AgentMessage with all fields."""
        timestamp = datetime.now()
        
        message = AgentMessage(
            sender_id="sender_123",
            recipient_id="recipient_456",
            message_type="task_request",
            content={"task": "process_data"},
            timestamp=timestamp,
            correlation_id="corr_789"
        )
        
        assert message.sender_id == "sender_123"
        assert message.recipient_id == "recipient_456"
        assert message.message_type == "task_request"
        assert message.content == {"task": "process_data"}
        assert message.timestamp == timestamp
        assert message.correlation_id == "corr_789"
    
    def test_agent_message_optional_correlation_id(self):
        """Test AgentMessage without correlation_id."""
        timestamp = datetime.now()
        
        message = AgentMessage(
            sender_id="sender_123",
            recipient_id="recipient_456",
            message_type="task_request",
            content={"task": "process_data"},
            timestamp=timestamp
        )
        
        assert message.correlation_id is None


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def __init__(self, agent_id: str, name: str, description: str, capabilities=None):
        super().__init__(agent_id, name, description, capabilities)
        self.executed_tasks = []
    
    async def execute_task(self, task):
        """Execute a task (test implementation)."""
        self.executed_tasks.append(task)
        result = {
            'success': True,
            'task_type': task.get('type', 'unknown'),
            'result': f"Processed task: {task}"
        }
        self.record_task_completion(result)
        return result


class TestBaseAgent:
    """Test suite for BaseAgent class."""
    
    def test_base_agent_initialization(self):
        """Test BaseAgent initialization."""
        capabilities = [
            AgentCapability("test_cap", "Test capability", ["str"], ["dict"])
        ]
        
        agent = ConcreteAgent(
            agent_id="test_agent_123",
            name="Test Agent",
            description="A test agent",
            capabilities=capabilities
        )
        
        assert agent.agent_id == "test_agent_123"
        assert agent.name == "Test Agent"
        assert agent.description == "A test agent"
        assert agent.capabilities == capabilities
        assert agent.is_active is True
        assert isinstance(agent.last_activity, datetime)
        assert agent.task_history == []
    
    def test_base_agent_initialization_without_capabilities(self):
        """Test BaseAgent initialization without capabilities."""
        agent = ConcreteAgent(
            agent_id="test_agent_123",
            name="Test Agent",
            description="A test agent"
        )
        
        assert agent.capabilities == []
    
    def test_get_capabilities(self):
        """Test getting agent capabilities."""
        capability1 = AgentCapability("cap1", "Capability 1", ["str"], ["dict"])
        capability2 = AgentCapability("cap2", "Capability 2", ["dict"], ["str"])
        
        agent = ConcreteAgent(
            agent_id="test_agent",
            name="Test Agent",
            description="Test",
            capabilities=[capability1, capability2]
        )
        
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 2
        assert capability1 in capabilities
        assert capability2 in capabilities
    
    def test_can_handle_task(self):
        """Test checking if agent can handle specific task types."""
        capability = AgentCapability("data_processing", "Process data", ["dict"], ["dict"])
        
        agent = ConcreteAgent(
            agent_id="test_agent",
            name="Test Agent",
            description="Test",
            capabilities=[capability]
        )
        
        assert agent.can_handle_task("data_processing") is True
        assert agent.can_handle_task("unknown_task") is False
    
    def test_get_status(self):
        """Test getting agent status."""
        capability = AgentCapability("test_cap", "Test capability", ["str"], ["dict"])
        
        agent = ConcreteAgent(
            agent_id="test_agent_123",
            name="Test Agent",
            description="Test",
            capabilities=[capability]
        )
        
        status = agent.get_status()
        
        assert status['agent_id'] == "test_agent_123"
        assert status['name'] == "Test Agent"
        assert status['is_active'] is True
        assert 'last_activity' in status
        assert status['capabilities_count'] == 1
        assert status['tasks_completed'] == 0
    
    @pytest.mark.asyncio
    async def test_execute_task_and_record_completion(self):
        """Test executing task and recording completion."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            name="Test Agent",
            description="Test"
        )
        
        task = {"type": "test_task", "data": "test_data"}
        
        # Execute task
        result = await agent.execute_task(task)
        
        # Check result
        assert result['success'] is True
        assert result['task_type'] == "test_task"
        assert "Processed task:" in result['result']
        
        # Check task was recorded
        assert len(agent.task_history) == 1
        assert agent.task_history[0]['success'] is True
        assert agent.task_history[0]['task_type'] == "test_task"
        assert isinstance(agent.task_history[0]['timestamp'], datetime)
        
        # Check status reflects completion
        status = agent.get_status()
        assert status['tasks_completed'] == 1
    
    def test_record_task_completion_manual(self):
        """Test manually recording task completion."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            name="Test Agent",
            description="Test"
        )
        
        task_result = {
            'success': True,
            'task_type': 'manual_task'
        }
        
        original_activity = agent.last_activity
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        agent.record_task_completion(task_result)
        
        # Check task was recorded
        assert len(agent.task_history) == 1
        assert agent.task_history[0]['success'] is True
        assert agent.task_history[0]['task_type'] == 'manual_task'
        assert agent.last_activity > original_activity
    
    def test_record_task_completion_with_failure(self):
        """Test recording failed task completion."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            name="Test Agent",
            description="Test"
        )
        
        task_result = {
            'success': False,
            'task_type': 'failed_task'
        }
        
        agent.record_task_completion(task_result)
        
        # Check task was recorded
        assert len(agent.task_history) == 1
        assert agent.task_history[0]['success'] is False
        assert agent.task_history[0]['task_type'] == 'failed_task'


class TestAgentRegistry:
    """Test suite for AgentRegistry class."""
    
    def test_agent_registry_initialization(self):
        """Test AgentRegistry initialization."""
        registry = AgentRegistry()
        
        assert isinstance(registry.agents, dict)
        assert len(registry.agents) == 0
        assert isinstance(registry.capabilities_index, dict)
        assert len(registry.capabilities_index) == 0
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        
        capability = AgentCapability("test_cap", "Test capability", ["str"], ["dict"])
        agent = ConcreteAgent(
            agent_id="test_agent_123",
            name="Test Agent",
            description="Test",
            capabilities=[capability]
        )
        
        registry.register_agent(agent)
        
        # Check agent is registered
        assert "test_agent_123" in registry.agents
        assert registry.agents["test_agent_123"] == agent
        
        # Check capability is indexed
        assert "test_cap" in registry.capabilities_index
        assert "test_agent_123" in registry.capabilities_index["test_cap"]
    
    def test_register_multiple_agents_same_capability(self):
        """Test registering multiple agents with same capability."""
        registry = AgentRegistry()
        
        capability = AgentCapability("shared_cap", "Shared capability", ["str"], ["dict"])
        
        agent1 = ConcreteAgent("agent1", "Agent 1", "Test", [capability])
        agent2 = ConcreteAgent("agent2", "Agent 2", "Test", [capability])
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # Check both agents are indexed under the same capability
        assert len(registry.capabilities_index["shared_cap"]) == 2
        assert "agent1" in registry.capabilities_index["shared_cap"]
        assert "agent2" in registry.capabilities_index["shared_cap"]
    
    def test_get_agent(self):
        """Test getting agent by ID."""
        registry = AgentRegistry()
        
        agent = ConcreteAgent("test_agent", "Test Agent", "Test")
        registry.register_agent(agent)
        
        # Test getting existing agent
        retrieved_agent = registry.get_agent("test_agent")
        assert retrieved_agent == agent
        
        # Test getting non-existent agent
        non_existent = registry.get_agent("non_existent")
        assert non_existent is None
    
    def test_find_agents_for_capability(self):
        """Test finding agents by capability."""
        registry = AgentRegistry()
        
        capability1 = AgentCapability("cap1", "Capability 1", ["str"], ["dict"])
        capability2 = AgentCapability("cap2", "Capability 2", ["dict"], ["str"])
        
        agent1 = ConcreteAgent("agent1", "Agent 1", "Test", [capability1])
        agent2 = ConcreteAgent("agent2", "Agent 2", "Test", [capability2])
        agent3 = ConcreteAgent("agent3", "Agent 3", "Test", [capability1, capability2])
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        registry.register_agent(agent3)
        
        # Test finding agents with capability1
        agents_with_cap1 = registry.find_agents_for_capability("cap1")
        assert len(agents_with_cap1) == 2
        assert agent1 in agents_with_cap1
        assert agent3 in agents_with_cap1
        
        # Test finding agents with capability2
        agents_with_cap2 = registry.find_agents_for_capability("cap2")
        assert len(agents_with_cap2) == 2
        assert agent2 in agents_with_cap2
        assert agent3 in agents_with_cap2
        
        # Test finding agents with non-existent capability
        agents_with_unknown = registry.find_agents_for_capability("unknown_cap")
        assert len(agents_with_unknown) == 0
    
    def test_get_all_agents(self):
        """Test getting all registered agents."""
        registry = AgentRegistry()
        
        agent1 = ConcreteAgent("agent1", "Agent 1", "Test")
        agent2 = ConcreteAgent("agent2", "Agent 2", "Test")
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        all_agents = registry.get_all_agents()
        assert len(all_agents) == 2
        assert agent1 in all_agents
        assert agent2 in all_agents
    
    def test_get_system_status(self):
        """Test getting system status."""
        registry = AgentRegistry()
        
        capability = AgentCapability("test_cap", "Test capability", ["str"], ["dict"])
        
        agent1 = ConcreteAgent("agent1", "Agent 1", "Test", [capability])
        agent2 = ConcreteAgent("agent2", "Agent 2", "Test", [capability])
        
        # Make one agent inactive
        agent2.is_active = False
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        status = registry.get_system_status()
        
        assert status['total_agents'] == 2
        assert status['active_agents'] == 1  # Only agent1 is active
        assert status['total_capabilities'] == 1
        assert len(status['agent_summary']) == 1  # Only active agents in summary
        assert status['agent_summary'][0]['agent_id'] == 'agent1'
    
    def test_registry_with_agent_removal(self):
        """Test behavior when agent is removed from registry."""
        registry = AgentRegistry()
        
        capability = AgentCapability("test_cap", "Test capability", ["str"], ["dict"])
        agent = ConcreteAgent("agent1", "Agent 1", "Test", [capability])
        
        registry.register_agent(agent)
        
        # Manually remove agent (simulating agent going offline)
        del registry.agents["agent1"]
        
        # find_agents_for_capability should handle missing agents gracefully
        agents = registry.find_agents_for_capability("test_cap")
        assert len(agents) == 0
    
    def test_agent_registry_integration(self):
        """Test full integration of agent registry functionality."""
        registry = AgentRegistry()
        
        # Create agents with different capabilities
        text_processing = AgentCapability("text_processing", "Process text", ["str"], ["dict"])
        data_analysis = AgentCapability("data_analysis", "Analyze data", ["dict"], ["dict"])
        
        agent1 = ConcreteAgent("text_agent", "Text Agent", "Processes text", [text_processing])
        agent2 = ConcreteAgent("data_agent", "Data Agent", "Analyzes data", [data_analysis])
        agent3 = ConcreteAgent("hybrid_agent", "Hybrid Agent", "Multi-capable", [text_processing, data_analysis])
        
        # Register all agents
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        registry.register_agent(agent3)
        
        # Test finding specialized agents
        text_agents = registry.find_agents_for_capability("text_processing")
        data_agents = registry.find_agents_for_capability("data_analysis")
        
        assert len(text_agents) == 2  # agent1 and agent3
        assert len(data_agents) == 2  # agent2 and agent3
        
        # Test system status
        status = registry.get_system_status()
        assert status['total_agents'] == 3
        assert status['active_agents'] == 3
        assert status['total_capabilities'] == 2
        
        # Test agent capabilities
        assert agent1.can_handle_task("text_processing") is True
        assert agent1.can_handle_task("data_analysis") is False
        assert agent3.can_handle_task("text_processing") is True
        assert agent3.can_handle_task("data_analysis") is True


if __name__ == "__main__":
    pytest.main([__file__])