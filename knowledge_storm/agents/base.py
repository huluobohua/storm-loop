
from abc import ABC, abstractmethod

class Agent(ABC):
    """
    Base class for all agents in the multi-agent system.
    """

    def __init__(self, agent_id, name, role):
        """
        Initializes the Agent.

        :param agent_id: The unique identifier for the agent.
        :param name: The name of the agent.
        :param role: The role of the agent in the system.
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role

    @abstractmethod
    async def execute_task(self, task):
        """
        Executes a given task asynchronously.

        :param task: The task to be executed.
        """
        pass

    @abstractmethod
    async def communicate(self, message):
        """
        Communicates with other agents asynchronously.

        :param message: The message to be sent.
        """
        pass

    def __repr__(self):
        return f"Agent(agent_id={self.agent_id}, name={self.name}, role={self.role})"
