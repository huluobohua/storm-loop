from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ScreeningResult:
    """Result of screening a single record."""

    decision: str
    confidence: float
    reasons: List[str]


class PRISMAScreener:
    """Simple 80/20 screening assistant.

    This implementation uses keyword patterns to approximate a confidence
    score for inclusion or exclusion. A decision is only returned when the
    score exceeds the threshold (default 0.8). Otherwise the record is
    marked as ``unsure``.
    """

    def __init__(
        self,
        include_patterns: List[str] | None = None,
        exclude_patterns: List[str] | None = None,
        threshold: float = 0.8,
    ) -> None:
        self.include_patterns = include_patterns or [
            "randomized",
            "controlled",
            "trial",
            "study",
            "results",
        ]
        self.exclude_patterns = exclude_patterns or [
            "protocol",
            "editorial",
            "letter",
            "commentary",
            "case report",
        ]
        self.threshold = threshold

    def _score(self, text: str) -> Tuple[float, float]:
        text = text.lower()
        inc_hits = sum(1 for p in self.include_patterns if p in text)
        exc_hits = sum(1 for p in self.exclude_patterns if p in text)
        inc_score = inc_hits / len(self.include_patterns)
        exc_score = exc_hits / len(self.exclude_patterns)
        return inc_score, exc_score

    def screen(self, text: str) -> ScreeningResult:
        """Screen a single text and return the decision."""
        inc, exc = self._score(text)

        if (inc >= self.threshold and inc > exc) or (inc > exc and inc >= 0.5):
            return ScreeningResult(
                "include", inc, [f"include score {inc:.2f} >= {self.threshold}"]
            )

        exc_hits = exc * len(self.exclude_patterns)
        inc_hits = inc * len(self.include_patterns)
        if (
            (exc >= self.threshold and exc > inc)
            or (exc_hits >= 1 and inc_hits <= exc_hits)
        ):
            reason = (
                "strong exclude keyword detected"
                if exc_hits >= 1 and inc_hits <= exc_hits
                else f"exclude score {exc:.2f} >= {self.threshold}"
            )
            return ScreeningResult("exclude", exc, [reason])

        return ScreeningResult("unsure", max(inc, exc), ["scores below threshold"])

    def batch_screen(self, texts: List[str]) -> List[ScreeningResult]:
        """Screen multiple texts at once."""
        return [self.screen(t) for t in texts]
