try:
    from .academic_rm import CrossrefRM  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    CrossrefRM = None  # type: ignore

from .multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule
from ..prisma_assistant import PRISMAScreener

__all__ = ["CrossrefRM", "MultiAgentKnowledgeCurationModule", "PRISMAScreener"]
