import asyncio
import time

from knowledge_storm.agent_coordinator import AgentCoordinator


class DummyAgent:
    """Minimal agent that just sleeps for a bit."""

    def __init__(self, agent_id: str, delay: float = 0.1) -> None:
        self.agent_id = agent_id
        self.delay = delay

    async def execute_task(self, task: float) -> str:
        await asyncio.sleep(self.delay)
        return f"done_{task}"


def test_parallel_task_execution():
    """Demonstrate that tasks are executed concurrently."""

    async def run():
        coordinator = AgentCoordinator()
        for i in range(3):
            coordinator.register_agent(DummyAgent(f"a{i}"))

        assignments = [(f"a{i}", 0.1) for i in range(3)]
        start = time.perf_counter()
        results = await coordinator.distribute_tasks_parallel(assignments)
        duration = time.perf_counter() - start

        assert all(r.startswith("done") for r in results)
        assert duration < 0.2  # each takes 0.1s -> parallel should finish <0.2s

    asyncio.run(run())
