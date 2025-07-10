import sys

try:
    from .academic_rm import CrossrefRM, HAS_DSPY
    if 'dspy' in sys.modules and sys.modules.get('dspy') is None:
        CrossrefRM = None  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    CrossrefRM = None  # type: ignore

try:
    from .multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule
except Exception:  # pragma: no cover - optional dependency
    MultiAgentKnowledgeCurationModule = None  # type: ignore

__all__ = ["CrossrefRM", "MultiAgentKnowledgeCurationModule"]
