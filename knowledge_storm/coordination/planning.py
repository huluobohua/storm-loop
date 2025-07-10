import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PlanningResult:
    strategy: str
    plan: Dict[str, Any]
    success: bool = True

    def is_valid(self) -> bool:
        return self.success and bool(self.plan)


@dataclass
class ParallelPlanningResult:
    results: List[PlanningResult]
    duration: float

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.success) / len(self.results)

    def get_best_plan(self) -> Optional[PlanningResult]:
        valid = [r for r in self.results if r.is_valid()]
        if not valid:
            return None
        return valid[0]


class ParallelPlanningCoordinator:
    """Run multiple planning strategies concurrently."""

    def __init__(self) -> None:
        self._strategies = [self._systematic, self._exploratory, self._focused]

    async def run_parallel_planning(self, topic: str) -> ParallelPlanningResult:
        start = asyncio.get_event_loop().time()
        tasks = [asyncio.create_task(fn(topic)) for fn in self._strategies]
        results = await asyncio.gather(*tasks)
        duration = asyncio.get_event_loop().time() - start
        return ParallelPlanningResult(results, duration)

    async def _systematic(self, topic: str) -> PlanningResult:
        await asyncio.sleep(0.1)
        return PlanningResult("systematic", {"topic": topic, "type": "sys"})

    async def _exploratory(self, topic: str) -> PlanningResult:
        await asyncio.sleep(0.1)
        return PlanningResult("exploratory", {"topic": topic, "type": "exp"})

    async def _focused(self, topic: str) -> PlanningResult:
        await asyncio.sleep(0.1)
        return PlanningResult("focused", {"topic": topic, "type": "foc"})
