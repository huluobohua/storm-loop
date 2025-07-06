from __future__ import annotations

import logging
from typing import Any, Dict

from .cache_service import CacheService

# Research planning constants
MAX_COMPLEXITY_SCORE = 10
HIGH_COMPLEXITY_THRESHOLD = 5
TIME_MULTIPLIER_HOURS = 2
FALLBACK_COMPLEXITY = 1
FALLBACK_TIME_HOURS = 2

logger = logging.getLogger(__name__)


class ResearchPlanner:
    """Service for planning academic research workflows."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache or CacheService()

    async def analyze_topic_complexity(self, topic: str) -> int:
        """Return complexity score based on word count.

        This is a simple heuristic. Future versions could use an LLM
        to provide a more nuanced assessment of topic difficulty.
        """
        if not topic or not topic.strip():
            return FALLBACK_COMPLEXITY
        return min(len(topic.split()), MAX_COMPLEXITY_SCORE)

    async def generate_research_strategy(self, topic: str, complexity: int) -> Dict[str, Any]:
        """Generate basic research plan for the given topic."""
        base_steps = [
            "scope topic",
            "search literature",
            "analyze findings",
            "draft article",
        ]

        if complexity > HIGH_COMPLEXITY_THRESHOLD:
            base_steps.insert(1, "break into subtopics")

        return {
            "topic": topic,
            "complexity": complexity,
            "steps": base_steps,
            "estimated_time": complexity * TIME_MULTIPLIER_HOURS,
        }


    async def plan_research(self, topic: str) -> Dict[str, Any]:
        """End-to-end planning with caching and error handling."""
        self._validate_topic(topic)
        cache_key = self._make_cache_key(topic)
        plan = await self._get_cached_plan(cache_key)
        if plan is None:
            plan = await self._generate_and_cache_plan(topic, cache_key)
        return plan

    def _validate_topic(self, topic: str) -> None:
        """Validate topic is not empty."""
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")

    def _make_cache_key(self, topic: str) -> str:
        return f"plan:{topic.strip()}"

    async def _get_cached_plan(self, cache_key: str) -> Dict[str, Any] | None:
        """Retrieve plan from cache, returning None on failure."""
        try:
            return await self.cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None

    async def _generate_new_plan(self, topic: str) -> Dict[str, Any]:
        complexity = await self.analyze_topic_complexity(topic)
        return await self.generate_research_strategy(topic, complexity)

    async def _cache_plan(self, cache_key: str, plan: Dict[str, Any]) -> None:
        """Cache the plan, logging failures."""
        try:
            await self.cache.set(cache_key, plan)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def _generate_and_cache_plan(self, topic: str, cache_key: str) -> Dict[str, Any]:
        try:
            plan = await self._generate_new_plan(topic)
            await self._cache_plan(cache_key, plan)
            return plan
        except Exception as e:
            logger.error(f"Research planning failed for {topic}: {e}")
            return self._create_fallback_plan(topic)

    def _create_fallback_plan(self, topic: str) -> Dict[str, Any]:
        """Create minimal fallback plan."""
        return {
            "topic": topic,
            "complexity": FALLBACK_COMPLEXITY,
            "steps": ["search literature", "draft article"],
            "estimated_time": FALLBACK_TIME_HOURS,
            "error": "Planning failed, using fallback",
        }
