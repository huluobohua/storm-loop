from __future__ import annotations

from typing import Protocol, Any
from dataclasses import dataclass
import logging

from .storm_config import STORMConfig
from .exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


class WorkflowRunner(Protocol):
    async def run_academic_workflow(self, topic: str, **kwargs) -> Article:
        ...

    async def run_original_workflow(self, topic: str, **kwargs) -> Article:
        ...


@dataclass(frozen=True)
class Article:
    topic: str
    content: str = ""
    metadata: dict[str, Any] | None = None


class WorkflowSelector:
    def __init__(self, config: STORMConfig):
        self._config = config

    def should_use_academic_workflow(self) -> bool:
        return self._config.academic_sources

    def should_use_quality_gates(self) -> bool:
        return self._config.quality_gates

    def should_verify_citations(self) -> bool:
        return self._config.citation_verification


class EnhancedSTORMEngine:
    def __init__(self, config: STORMConfig,
                 workflow_runner: WorkflowRunner | None = None) -> None:
        self._config = config
        self._workflow_selector = WorkflowSelector(config)
        self._workflow_runner = workflow_runner or DefaultWorkflowRunner()
        self._setup_components()

    def _setup_components(self) -> None:
        # Placeholder - would initialize caching, verification, etc.
        pass

    async def generate_article(self, topic: str, **kwargs) -> Article:
        if self._workflow_selector.should_use_academic_workflow():
            return await self._generate_academic_article(topic, **kwargs)
        return await self._generate_standard_article(topic, **kwargs)

    async def _generate_academic_article(self, topic: str, **kwargs) -> Article:
        try:
            article = await self._workflow_runner.run_academic_workflow(topic, **kwargs)
        except (ConnectionError, TimeoutError, ServiceUnavailableError) as e:
            logger.warning(
                f"Academic workflow failed: {e}, falling back to standard"
            )
            return await self._generate_standard_article(topic, **kwargs)
        if self._workflow_selector.should_verify_citations():
            return await self._verify_and_enhance(article)
        return article

    async def _generate_standard_article(self, topic: str, **kwargs) -> Article:
        return await self._workflow_runner.run_original_workflow(topic, **kwargs)

    async def _verify_and_enhance(self, article: Article) -> Article:
        # Placeholder for citation verification
        return article


class DefaultWorkflowRunner:
    async def run_academic_workflow(self, topic: str, **kwargs) -> Article:
        return Article(
            topic=topic,
            content=f"Academic article about {topic}",
            metadata={"type": "academic", "verified": True},
        )

    async def run_original_workflow(self, topic: str, **kwargs) -> Article:
        return Article(
            topic=topic,
            content=f"Wikipedia style article about {topic}",
            metadata={"type": "wikipedia"},
        )

