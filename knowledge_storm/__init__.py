"""Convenience package imports with optional dependencies."""

try:
    from . import lm  # noqa: F401
    from . import rm  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - handled for optional deps
    lm = None
    rm = None

from . import interface  # noqa: F401
from .storm_config import STORMConfig  # noqa: F401
from .hybrid_engine import EnhancedSTORMEngine  # noqa: F401
from .exceptions import ServiceUnavailableError  # noqa: F401
from .services.research_planner import ResearchPlanner  # noqa: F401
try:
    from .storm_wiki import utils  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    utils = None

__all__ = [
    "lm",
    "rm",
    "interface",
    "utils",
    "STORMConfig",
    "EnhancedSTORMEngine",
    "ServiceUnavailableError",
    "ResearchPlanner",
]
