try:
    from .academic_rm import CrossrefRM
except Exception:  # pragma: no cover - optional dependency on dspy
    CrossrefRM = None  # type: ignore

from .multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule

__all__ = ["MultiAgentKnowledgeCurationModule"]
if CrossrefRM is not None:
    __all__.insert(0, "CrossrefRM")
