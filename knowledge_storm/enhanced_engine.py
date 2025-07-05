from __future__ import annotations

from typing import Any

from .storm_config import STORMConfig
from .interface import Article


class EnhancedSTORMEngine:
    """Unified entry point for STORM with configurable modes."""

    def __init__(self, config: STORMConfig, runner: Any) -> None:
        self.config = config
        self.runner = runner
        self.setup_components_based_on_mode()

    def setup_components_based_on_mode(self) -> None:
        """Setup components based on the selected mode."""
        # Placeholder for future customization based on mode
        pass

    async def academic_workflow(self, topic: str, **kwargs: Any) -> Article | None:
        await self.runner.run(topic=topic, **kwargs)
        return None

    async def original_workflow(self, topic: str, **kwargs: Any) -> Article | None:
        await self.runner.run(topic=topic, **kwargs)
        return None

    async def generate_article(self, topic: str, **kwargs: Any) -> Article | None:
        if self.config.academic_sources:
            return await self.academic_workflow(topic, **kwargs)
        return await self.original_workflow(topic, **kwargs)
