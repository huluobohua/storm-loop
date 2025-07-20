
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple, Optional

logger = logging.getLogger(__name__)


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
        agent_ids = self._collect_agent_ids(agents)
        if not agent_ids:
            return []
        return [self._assign_single(task, agent_ids) for task in tasks]

    def _collect_agent_ids(self, agents: Dict[str, Any]) -> List[str]:
        return list(agents.keys())

    def _assign_single(self, task: Any, agent_ids: List[str]) -> Tuple[str, Any]:
        agent_id = agent_ids[self._index % len(agent_ids)]
        self._index += 1
        return agent_id, task


class AgentCoordinator:
    """Manages the interactions between the different agents."""

    def __init__(self, strategy: Optional[CoordinationStrategy] = None):
        self.agents: Dict[str, Any] = {}
        self.strategy = strategy or RoundRobinStrategy()

    def register_agent(self, agent) -> None:
        """Register a new agent with the coordinator."""
        self.agents[agent.agent_id] = agent

    async def relay_message(self, sender_id: str, receiver_id: str, message: str) -> None:
        sender = self.agents.get(sender_id)
        receiver = self.agents.get(receiver_id)
        if not sender or not receiver:
            logger.error("Relay failed: sender=%s receiver=%s", sender_id, receiver_id)
            return
        try:
            await sender.send_message(receiver, message)
        except Exception:  # pragma: no cover - logging only
            logger.exception("Error sending message from %s to %s", sender_id, receiver_id)

    async def distribute_task(self, agent_id: str, task: Any) -> Any:
        """Distribute a task to a specific agent asynchronously."""
        agent = self.agents.get(agent_id)
        if not agent:
            logger.error("No agent registered with id %s", agent_id)
            return None
        try:
            return await agent.execute_task(task)
        except Exception:
            logger.exception("Error executing task %s for agent %s", task, agent_id)
            return None

    async def distribute_tasks_parallel(self, assignments: Iterable[Tuple[str, Any]]) -> List[Any]:
        """Distribute multiple tasks to agents in parallel."""
        coros = [self.distribute_task(aid, t) for aid, t in assignments]
        try:
            return await asyncio.gather(*coros)
        except Exception:
            logger.exception("Error during parallel task distribution")
            return []

    async def distribute_tasks(self, tasks: Iterable[Any]) -> List[Any]:
        """Assign tasks using the strategy and process them in parallel."""
        assignments = self.strategy.assign(tasks, self.agents)
        try:
            return await self.distribute_tasks_parallel(assignments)
        except Exception:
            logger.exception("Error distributing tasks")
            return []

    def set_strategy(self, strategy: CoordinationStrategy) -> None:
        """Set the coordination strategy."""
        self.strategy = strategy
