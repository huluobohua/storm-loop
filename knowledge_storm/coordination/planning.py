from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Any, List, Dict, Optional

@dataclass
class PlanningResult:
    strategy: str
    plan: Dict[str, Any]
    duration: float
    success: bool

    def is_valid(self) -> bool:
        return self.success and bool(self.plan)

@dataclass
class ParallelPlanningResult:
    results: List[PlanningResult]
    total_duration: float
    success_rate: float

    def get_best_plan(self) -> Optional[PlanningResult]:
        valid = [r for r in self.results if r.is_valid()]
        if not valid:
            return None
        return max(valid, key=lambda r: len(r.plan))

class ParallelPlanningCoordinator:
    async def run_parallel_planning(self, topic: str) -> ParallelPlanningResult:
        async def make_plan(name: str) -> PlanningResult:
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)
            plan = {"topic": topic, "strategy": name}
            dur = asyncio.get_event_loop().time() - start
            return PlanningResult(name, plan, dur, True)

        start = asyncio.get_event_loop().time()
        tasks = [make_plan(s) for s in ["systematic", "exploratory", "focused"]]
        results = await asyncio.gather(*tasks)
        duration = asyncio.get_event_loop().time() - start
        success_rate = len([r for r in results if r.success]) / len(results)
        return ParallelPlanningResult(results, duration, success_rate)
