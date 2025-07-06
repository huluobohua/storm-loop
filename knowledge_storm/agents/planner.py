from __future__ import annotations

import asyncio
from typing import Any, Dict, TYPE_CHECKING

from .base import Agent

if TYPE_CHECKING:
    from ..services.research_planner import ResearchPlanner


class ResearchPlannerAgent(Agent):
    """Agent that produces research plans for academic topics."""

    def __init__(self, agent_id: str, name: str, planner: "ResearchPlanner", role: str = "Research Planner") -> None:
        super().__init__(agent_id, name, role)
        self.planner = planner

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute research planning task."""
        return await self.planner.plan_research(task)

    async def communicate(self, message: str) -> str:
        """Handle communication with other agents."""
        await asyncio.sleep(0)  # Placeholder: Fulfills async contract
        return f"{self.name} notes: {message}"
