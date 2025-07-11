try:
    from .academic_rm import CrossrefRM  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    CrossrefRM = None  # type: ignore

from .multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule

try:
    from ..prisma_assistant import PRISMAScreener  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PRISMAScreener = None  # type: ignore

__all__ = ["CrossrefRM", "MultiAgentKnowledgeCurationModule", "PRISMAScreener"]
