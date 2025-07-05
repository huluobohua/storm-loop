from __future__ import annotations

import os
from dataclasses import dataclass


class STORMConfig:
    """Configuration system for STORM modes."""

    VALID_MODES = ("academic", "wikipedia", "hybrid")

    def __init__(self, mode: str | None = None) -> None:
        self.set_mode(mode or os.getenv("STORM_MODE", "hybrid"))

    def set_mode(self, mode: str) -> None:
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self.academic_sources = mode in ("academic", "hybrid")
        self.quality_gates = mode in ("academic", "hybrid")
        self.citation_verification = mode == "academic"
        self.real_time_verification = mode == "academic"

    def switch_mode(self, mode: str) -> None:
        """Switch to a new configuration mode at runtime."""
        self.set_mode(mode)


@dataclass
class Article:
    """Minimal article representation used for the hybrid engine."""

    topic: str
    content: str = ""


class EnhancedSTORMEngine:
    """Simple engine that routes workflows based on :class:`STORMConfig`."""

    def __init__(self, config: STORMConfig) -> None:
        self.config = config
        self.setup_components_based_on_mode()

    def setup_components_based_on_mode(self) -> None:
        """Placeholder for mode-specific initialization."""
        # Real implementation would configure caching, verification, etc.
        pass

    async def academic_workflow(self, topic: str, **kwargs) -> Article:
        """Stub for the academic generation workflow."""
        return Article(topic=topic, content=f"Academic article about {topic}")

    async def original_workflow(self, topic: str, **kwargs) -> Article:
        """Stub for the original STORM workflow."""
        return Article(topic=topic, content=f"Wikipedia style article about {topic}")

    async def generate_article(self, topic: str, **kwargs) -> Article:
        """Unified entry point selecting the workflow based on configuration."""
        if self.config.academic_sources:
            return await self.academic_workflow(topic, **kwargs)
        return await self.original_workflow(topic, **kwargs)
