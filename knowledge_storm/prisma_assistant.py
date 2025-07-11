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

    Keyword patterns are counted to derive inclusion and exclusion scores.
    A record is included or excluded when the corresponding score meets or
    exceeds ``threshold`` (default ``0.8``) **and** is greater than the
    opposite score. If exclusion keywords outnumber inclusion keywords, the
    record is excluded even when scores fall below the threshold. Any other
    case results in an ``unsure`` decision.
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

    def _hits(self, text: str) -> Tuple[int, int]:
        text = text.lower()
        inc_hits = sum(1 for p in self.include_patterns if p in text)
        exc_hits = sum(1 for p in self.exclude_patterns if p in text)
        return inc_hits, exc_hits

    @staticmethod
    def _score(hits: int, total: int) -> float:
        return hits / total if total else 0.0

    def screen(self, text: str) -> ScreeningResult:
        """Screen a single text and return the decision."""
        inc_hits, exc_hits = self._hits(text)
        inc_score = self._score(inc_hits, len(self.include_patterns))
        exc_score = self._score(exc_hits, len(self.exclude_patterns))

        if inc_score >= self.threshold and inc_score > exc_score:
            return ScreeningResult(
                "include",
                inc_score,
                [f"include score {inc_score:.2f} >= {self.threshold}"]
            )

        if exc_score >= self.threshold and exc_score > inc_score:
            return ScreeningResult(
                "exclude",
                exc_score,
                [f"exclude score {exc_score:.2f} >= {self.threshold}"]
            )

        if exc_hits >= 1 and inc_hits <= exc_hits:
            return ScreeningResult(
                "exclude",
                exc_score,
                [f"{exc_hits} exclude hits >= {inc_hits} include hits"]
            )

        return ScreeningResult(
            "unsure",
            max(inc_score, exc_score),
            ["scores below threshold or conflicting"]
        )

    def batch_screen(self, texts: List[str]) -> List[ScreeningResult]:
        """Screen multiple texts at once."""
        return [self.screen(t) for t in texts]
