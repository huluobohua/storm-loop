# Import available modules
from .academic_rm import CrossrefRM

# MultiAgentKnowledgeCurationModule has dspy dependency issues
# Will be re-enabled when dspy dependencies are resolved
try:
    from .multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule
    _MULTI_AGENT_AVAILABLE = True
except ImportError:
    _MULTI_AGENT_AVAILABLE = False

# Export available modules
if _MULTI_AGENT_AVAILABLE:
    __all__ = ["CrossrefRM", "MultiAgentKnowledgeCurationModule"]
else:
    __all__ = ["CrossrefRM"]
