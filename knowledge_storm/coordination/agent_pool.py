import asyncio
from dataclasses import dataclass
from typing import Any, List


@dataclass
class TaskResult:
    task: str
    success: bool
    duration: float


class AgentPoolManager:
    """Execute tasks concurrently with a fixed pool size."""

    def __init__(self, pool_size: int = 3) -> None:
        self.pool_size = pool_size

    async def execute_with_agent_pool(self, tasks: List[str], pool_size: int | None = None) -> List[TaskResult]:
        if pool_size is not None:
            self.pool_size = pool_size
        semaphore = asyncio.Semaphore(self.pool_size)
        results: List[TaskResult] = []

        async def worker(task: str) -> None:
            async with semaphore:
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(0.05)
                duration = asyncio.get_event_loop().time() - start
                results.append(TaskResult(task, True, duration))

        await asyncio.gather(*(worker(t) for t in tasks))
        return results
