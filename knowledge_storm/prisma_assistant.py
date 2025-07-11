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

    The screener counts inclusion and exclusion keyword hits for a text. Scores
    are calculated as the fraction of patterns matched. If either score exceeds
    ``threshold`` (default ``0.8``) and is greater than the opposing score the
    record is automatically included or excluded. Otherwise the decision is
    ``unsure``.
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

    def _count_hits(self, text: str) -> Tuple[int, int]:
        text = text.lower()
        inc_hits = sum(1 for p in self.include_patterns if p in text)
        exc_hits = sum(1 for p in self.exclude_patterns if p in text)
        return inc_hits, exc_hits

    def _calc_scores(self, inc_hits: int, exc_hits: int) -> Tuple[float, float]:
        inc_score = inc_hits / len(self.include_patterns)
        exc_score = exc_hits / len(self.exclude_patterns)
        return inc_score, exc_score

    def _decide(self, inc_score: float, exc_score: float) -> ScreeningResult:
        if inc_score >= self.threshold and inc_score > exc_score:
            return ScreeningResult(
                "include",
                inc_score,
                [f"include score {inc_score:.2f} > {exc_score:.2f}"],
            )
        if exc_score >= self.threshold and exc_score > inc_score:
            return ScreeningResult(
                "exclude",
                exc_score,
                [f"exclude score {exc_score:.2f} > {inc_score:.2f}"],
            )
        return ScreeningResult(
            "unsure",
            max(inc_score, exc_score),
            ["scores below threshold or conflict"],
        )

    def screen(self, text: str) -> ScreeningResult:
        """Screen a single text and return the decision."""
        hits = self._count_hits(text)
        scores = self._calc_scores(*hits)
        return self._decide(*scores)

    def batch_screen(self, texts: List[str]) -> List[ScreeningResult]:
        """Screen multiple texts at once."""
        return [self.screen(t) for t in texts]
