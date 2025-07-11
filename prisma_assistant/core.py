"""Core integration with the PRISMA screening system."""

import sys
from pathlib import Path

# Add the parent directory to the path to import knowledge_storm
sys.path.append(str(Path(__file__).parent.parent))

try:
    from knowledge_storm.prisma_assistant import PRISMAScreener, ScreeningResult
except ImportError:  # pragma: no cover - optional dependency
    # Fallback for development/testing
    PRISMAScreener = None
    ScreeningResult = None

__all__ = ["PRISMAScreener", "ScreeningResult", "get_screener"]


def get_screener(
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    threshold: float = 0.8,
) -> "PRISMAScreener":
    """Get a configured PRISMA screener instance."""
    if PRISMAScreener is None:
        raise ImportError(
            "PRISMA screener not available. "
            "Make sure knowledge_storm.prisma_assistant is installed."
        )

    return PRISMAScreener(
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        threshold=threshold,
    )
