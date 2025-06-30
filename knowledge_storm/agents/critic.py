
from knowledge_storm.agents.base import Agent

class CriticAgent(Agent):
    """
    An agent specialized in providing critical evaluation and review.
    """

    def __init__(self, agent_id, name, role="Critic"):
        super().__init__(agent_id, name, role)

    async def execute_task(self, task):
        """
        Executes a critique task asynchronously.
        """
        print(f"{self.name} is executing task: {task}")
        # Placeholder for actual critique logic
        return f"Critique of {task}"

    async def communicate(self, message):
        """
        Communicates with other agents asynchronously.
        """
        print(f"{self.name} is communicating: {message}")
