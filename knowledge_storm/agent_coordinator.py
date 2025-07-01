
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple


class CoordinationStrategy(ABC):
    """Base strategy class for assigning tasks to agents."""

    @abstractmethod
    def assign(self, tasks: Iterable[Any], agents: Dict[str, Any]) -> List[Tuple[str, Any]]:
        pass


class RoundRobinStrategy(CoordinationStrategy):
    """Simple round robin strategy for task distribution."""

    def __init__(self):
        self._index = 0

    def assign(self, tasks: Iterable[Any], agents: Dict[str, Any]) -> List[Tuple[str, Any]]:
        agent_ids = list(agents.keys())
        assigned = []
        for task in tasks:
            if not agent_ids:
                break
            agent_id = agent_ids[self._index % len(agent_ids)]
            self._index += 1
            assigned.append((agent_id, task))
        return assigned


class AgentCoordinator:
    """Manages the interactions between the different agents."""

    def __init__(self, strategy: CoordinationStrategy | None = None):
        self.agents: Dict[str, Any] = {}
        self.strategy = strategy or RoundRobinStrategy()

    def register_agent(self, agent) -> None:
        """Register a new agent with the coordinator."""
        self.agents[agent.agent_id] = agent

    async def relay_message(self, sender_id: str, receiver_id: str, message: str) -> None:
        sender = self.agents.get(sender_id)
        receiver = self.agents.get(receiver_id)
        if sender and receiver:
            await sender.send_message(receiver, message)

    async def distribute_task(self, agent_id: str, task: Any) -> Any:
        """Distribute a task to a specific agent asynchronously."""
        agent = self.agents.get(agent_id)
        if agent:
            return await agent.execute_task(task)
        return None

    async def distribute_tasks_parallel(self, assignments: Iterable[Tuple[str, Any]]) -> List[Any]:
        """Distribute multiple tasks to agents in parallel."""
        coros = [self.distribute_task(aid, t) for aid, t in assignments]
        return await asyncio.gather(*coros)

    async def distribute_tasks(self, tasks: Iterable[Any]) -> List[Any]:
        """Assign tasks using the strategy and process them in parallel."""
        assignments = self.strategy.assign(tasks, self.agents)
        return await self.distribute_tasks_parallel(assignments)

    def set_strategy(self, strategy: CoordinationStrategy) -> None:
        """Set the coordination strategy."""
        self.strategy = strategy
