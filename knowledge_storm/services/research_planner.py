from __future__ import annotations

import logging
from typing import Any, Dict, List

from .cache_service import CacheService

logger = logging.getLogger(__name__)


class ResearchPlanner:
    """Service for planning academic research workflows."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache or CacheService()

    async def analyze_topic_complexity(self, topic: str) -> int:
        """Return complexity score based on word count."""
        if not topic or not topic.strip():
            return 1
        return min(len(topic.split()), 10)  # Cap at 10

    async def generate_research_strategy(self, topic: str, complexity: int) -> Dict[str, Any]:
        """Generate basic research plan for the given topic."""
        base_steps = [
            "scope topic",
            "search literature",
            "analyze findings",
            "draft article"
        ]

        if complexity > 5:
            base_steps.insert(1, "break into subtopics")

        return {
            "topic": topic,
            "complexity": complexity,
            "steps": base_steps,
            "estimated_time": complexity * 2  # hours
        }


    async def plan_research(self, topic: str) -> Dict[str, Any]:
        """End-to-end planning with caching and error handling."""
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")

        cache_key = f"plan:{topic.strip()}"

        try:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Retrieved cached plan for topic: {topic}")
                return cached
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {topic}: {e}")
            # Continue without cache

        try:
            complexity = await self.analyze_topic_complexity(topic)
            strategy = await self.generate_research_strategy(topic, complexity)

            # Attempt to cache result
            try:
                await self.cache.set(cache_key, strategy)
            except Exception as e:
                logger.warning(f"Cache storage failed for {topic}: {e}")
                # Continue without caching

            return strategy

        except Exception as e:
            logger.error(f"Research planning failed for {topic}: {e}")
            # Return minimal fallback plan
            return {
                "topic": topic,
                "complexity": 1,
                "steps": ["search literature", "draft article"],
                "estimated_time": 2,
                "error": "Planning failed, using fallback"
            }
