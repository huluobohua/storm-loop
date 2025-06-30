
import asyncio

class AgentCoordinator:
    """
    Manages the interactions between the different agents.
    """

    def __init__(self):
        self.agents = {}

    def register_agent(self, agent):
        """
        Registers a new agent with the coordinator.

        :param agent: The agent to be registered.
        """
        self.agents[agent.agent_id] = agent

    async def distribute_task(self, agent_id, task):
        """
        Distributes a task to a specific agent asynchronously.

        :param agent_id: The ID of the agent to distribute the task to.
        :param task: The task to be distributed.
        """
        if agent_id in self.agents:
            return await self.agents[agent_id].execute_task(task)
        else:
            return "Agent not found"

    async def distribute_tasks_parallel(self, tasks):
        """
        Distributes multiple tasks to agents in parallel.

        :param tasks: A list of (agent_id, task) tuples.
        """
        import asyncio
        results = await asyncio.gather(*[self.distribute_task(agent_id, task) for agent_id, task in tasks])
        return results

    def set_strategy(self, strategy):
        """
        Sets the strategy for the coordinator.

        :param strategy: The strategy to be used.
        """
        # Placeholder for strategy pattern implementation
        print(f"Setting strategy to {strategy}")
