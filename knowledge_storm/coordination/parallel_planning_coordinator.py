"""Simple parallel planning coordinator used for testing."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PlanningResult:
    """Result of a single planning strategy."""

    strategy: str
    plan: Dict[str, Any]
    duration: float
    success: bool

    def is_valid(self) -> bool:
        return self.success and bool(self.plan)


@dataclass
class ParallelPlanningResult:
    """Container for multiple planning results."""

    results: List[PlanningResult]
    total_duration: float
    success_rate: float

    def get_best_plan(self) -> Optional[PlanningResult]:
        valid = [r for r in self.results if r.is_valid()]
        if not valid:
            return None
        return max(valid, key=lambda r: len(r.plan))


class ParallelPlanningCoordinator:
    """Runs several planning strategies concurrently."""

    def __init__(self) -> None:
        self._strategies = [
            self._systematic_plan,
            self._exploratory_plan,
            self._focused_plan,
        ]

    async def run_parallel_planning(self, topic: str) -> ParallelPlanningResult:
        start = asyncio.get_event_loop().time()
        tasks = [s(topic) for s in self._strategies]
        raw = await asyncio.gather(*tasks)
        duration = asyncio.get_event_loop().time() - start
        success = [r for r in raw if r.success]
        rate = len(success) / len(raw) if raw else 0.0
        return ParallelPlanningResult(raw, duration, rate)

    async def _systematic_plan(self, topic: str) -> PlanningResult:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.05)
        plan = {"approach": "systematic", "topic": topic}
        dur = asyncio.get_event_loop().time() - start
        return PlanningResult("systematic", plan, dur, True)

    async def _exploratory_plan(self, topic: str) -> PlanningResult:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.05)
        plan = {"approach": "exploratory", "topic": topic}
        dur = asyncio.get_event_loop().time() - start
        return PlanningResult("exploratory", plan, dur, True)

    async def _focused_plan(self, topic: str) -> PlanningResult:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.05)
        plan = {"approach": "focused", "topic": topic}
        dur = asyncio.get_event_loop().time() - start
        return PlanningResult("focused", plan, dur, True)
