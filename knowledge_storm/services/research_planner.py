from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from .academic_source_service import DEFAULT_LIMIT
from .cache_service import CacheService
from ..storm_config import STORMConfig


class ResearchPlanner:
    """Simple research planning utility."""

    def __init__(self, cache: CacheService | None = None, config: STORMConfig | None = None) -> None:
        self.cache = cache or CacheService()
        self.config = config or STORMConfig()

    async def analyze_topic_complexity(self, topic: str) -> int:
        """Return a naive complexity score based on unique words."""
        words = set(topic.lower().split())
        return len(words)

    async def generate_research_strategy(self, topic: str, complexity: int) -> List[str]:
        """Generate a basic research strategy for a topic."""
        strategy = [
            f"Define scope for '{topic}'.",
            "Search OpenAlex and Crossref for recent papers.",
        ]
        if self.config.academic_sources:
            strategy.append("Prioritize peer-reviewed sources.")
        if complexity > 5:
            strategy.append("Break topic into subtopics and research separately.")
        return strategy

    async def optimize_multi_perspective_plan(self, perspectives: List[str]) -> List[str]:
        """Deduplicate and sort perspectives."""
        return sorted(set(perspectives))

    async def get_plan(self, topic: str) -> Dict[str, Any]:
        """Return a cached research plan for the topic."""
        key = f"plan:{hashlib.md5(topic.encode()).hexdigest()}"
        cached = await self.cache.get(key)
        if cached:
            return cached
        complexity = await self.analyze_topic_complexity(topic)
        strategy = await self.generate_research_strategy(topic, complexity)
        plan = {"topic": topic, "complexity": complexity, "strategy": strategy}
        await self.cache.set(key, plan)
        return plan
