import asyncio
from dataclasses import dataclass
from typing import Any, List

@dataclass
class TaskResult:
    task_id: str
    result: Any
    success: bool
    duration: float

class _Worker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.busy = False

    async def run(self, task: str) -> Any:
        self.busy = True
        await asyncio.sleep(0.1)
        self.busy = False
        return {"done": task}

class AgentPoolManager:
    def __init__(self, pool_size: int = 3):
        self.pool = [_Worker(i) for i in range(pool_size)]

    async def execute_with_agent_pool(self, tasks: List[str], pool_size: int | None = None) -> List[TaskResult]:
        if pool_size and pool_size != len(self.pool):
            self.pool = [_Worker(i) for i in range(pool_size)]

        async def run_task(tid: int, task: str) -> TaskResult:
            worker = self.pool[tid % len(self.pool)]
            start = asyncio.get_event_loop().time()
            result = await worker.run(task)
            dur = asyncio.get_event_loop().time() - start
            return TaskResult(task, result, True, dur)

        jobs = [run_task(i, t) for i, t in enumerate(tasks)]
        return await asyncio.gather(*jobs)
