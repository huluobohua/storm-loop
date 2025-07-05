from __future__ import annotations

import asyncio
from typing import Any, Dict

from .base import Agent


class ResearchPlannerAgent(Agent):
    """Agent that produces research plans for academic topics."""

    def __init__(self, agent_id: str, name: str, role: str = "Research Planner") -> None:
        super().__init__(agent_id, name, role)
        # Import here to avoid circular dependency
        from ..services.research_planner import ResearchPlanner
        self.planner = ResearchPlanner()

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute research planning task."""
        return await self.planner.plan_research(task)

    async def communicate(self, message: str) -> str:
        """Handle communication with other agents."""
        await asyncio.sleep(0)
        return f"{self.name} notes: {message}"
