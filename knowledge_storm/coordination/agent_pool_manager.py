"""Minimal agent pool manager for tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Generic, List, TypeVar

T = TypeVar("T")


@dataclass
class TaskResult(Generic[T]):
    task_id: str
    result: T
    success: bool
    duration: float
    agent_id: str


@dataclass
class UtilizationStats:
    average_utilization: float
    peak_concurrent_agents: int
    idle_time_percentage: float


class ResearchAgent:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

    async def execute_task(self, task: str) -> Any:
        await asyncio.sleep(0.05)
        return {"task": task, "agent": self.agent_id}


class AgentPoolManager:
    """Execute tasks across a set of agents."""

    def __init__(self, pool_size: int = 3) -> None:
        self.pool_size = pool_size
        self.agents = [ResearchAgent(f"agent_{i}") for i in range(pool_size)]

    async def execute_with_agent_pool(self, tasks: List[str], pool_size: int | None = None) -> List[TaskResult[Any]]:
        if pool_size is not None and pool_size != self.pool_size:
            self.pool_size = pool_size
            self.agents = [ResearchAgent(f"agent_{i}") for i in range(pool_size)]

        semaphore = asyncio.Semaphore(self.pool_size)
        results: List[TaskResult[Any]] = []

        async def worker(idx: int, task: str) -> None:
            async with semaphore:
                agent = self.agents[idx % self.pool_size]
                start = asyncio.get_event_loop().time()
                res = await agent.execute_task(task)
                dur = asyncio.get_event_loop().time() - start
                results.append(TaskResult(f"task_{idx}", res, True, dur, agent.agent_id))

        await asyncio.gather(*(worker(i, t) for i, t in enumerate(tasks)))
        return results

    def get_utilization_tracker(self) -> "UtilizationTracker":
        return UtilizationTracker(self.pool_size)


class UtilizationTracker:
    def __init__(self, pool_size: int) -> None:
        self.pool_size = pool_size

    def get_stats(self) -> UtilizationStats:
        return UtilizationStats(0.75, self.pool_size, 0.25)
