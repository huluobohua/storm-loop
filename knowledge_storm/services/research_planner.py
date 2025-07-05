from __future__ import annotations

import logging
from typing import Any, Dict, List

from .cache_service import CacheService

logger = logging.getLogger(__name__)


class ResearchPlanner:
    """Simple service for planning academic research workflows."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache or CacheService()

    async def analyze_topic_complexity(self, topic: str) -> int:
        """Return a naive complexity score based on word count."""
        return len(topic.split())

    async def generate_research_strategy(self, topic: str, complexity: int) -> Dict[str, Any]:
        """Generate a very basic research plan for the given topic."""
        steps = [
            "scope topic",
            "search literature",
            "analyze findings",
            "draft article",
        ]
        return {"topic": topic, "complexity": complexity, "steps": steps}

    async def optimize_multi_perspective_plan(self, perspectives: List[str]) -> List[str]:
        """Return a deduplicated and sorted list of perspectives."""
        return sorted(set(perspectives))

    async def plan_research(self, topic: str) -> Dict[str, Any]:
        """End-to-end planning with caching."""
        cache_key = f"plan:{topic}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        complexity = await self.analyze_topic_complexity(topic)
        strategy = await self.generate_research_strategy(topic, complexity)
        await self.cache.set(cache_key, strategy)
        return strategy
