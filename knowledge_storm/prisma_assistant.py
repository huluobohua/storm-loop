"""Lightweight 80/20 screening assistant for systematic reviews."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass
class ScreeningResult:
    """Decision outcome for a single record."""

    decision: str
    confidence: float
    reasons: List[str]


class PRISMAScreener:
    """Keyword based helper to approximate PRISMA 80/20 screening."""

    def __init__(
        self,
        include_patterns: Sequence[str] | None = None,
        exclude_patterns: Sequence[str] | None = None,
        threshold: float = 0.8,
    ) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.include_patterns = list(include_patterns) if include_patterns is not None else [
            "randomized",
            "controlled",
            "trial",
            "study",
            "results",
        ]
        self.exclude_patterns = list(exclude_patterns) if exclude_patterns is not None else [
            "protocol",
            "editorial",
            "letter",
            "commentary",
            "case report",
        ]
        self.threshold = threshold

    def _count_hits(self, text: str) -> Tuple[int, int]:
        text = text.lower()
        inc = sum(1 for p in self.include_patterns if p in text)
        exc = sum(1 for p in self.exclude_patterns if p in text)
        return inc, exc

    def _scores(self, inc_hits: int, exc_hits: int) -> Tuple[float, float]:
        inc_score = (
            inc_hits / len(self.include_patterns)
            if self.include_patterns
            else 0.0
        )
        exc_score = (
            exc_hits / len(self.exclude_patterns)
            if self.exclude_patterns
            else 0.0
        )
        return inc_score, exc_score

    def _should_include(self, inc: float, exc: float) -> bool:
        return inc >= self.threshold and inc > exc

    def _should_exclude(self, inc: float, exc: float) -> bool:
        return exc >= self.threshold and exc > inc

    def _include_result(self, score: float) -> ScreeningResult:
        return ScreeningResult(
            "include",
            score,
            [f"include score {score:.2f} >= {self.threshold}"]
        )

    def _exclude_result(self, score: float) -> ScreeningResult:
        return ScreeningResult(
            "exclude",
            score,
            [f"exclude score {score:.2f} >= {self.threshold}"]
        )

    def _conflict_result(
        self,
        inc_hits: int,
        exc_hits: int,
        inc_score: float,
        exc_score: float,
    ) -> ScreeningResult:
        if exc_hits > inc_hits:
            return ScreeningResult(
                "exclude",
                exc_score,
                ["more exclude keywords"]
            )
        if inc_hits > exc_hits:
            return ScreeningResult(
                "include",
                inc_score,
                ["more include keywords"]
            )
        return ScreeningResult(
            "unsure",
            max(inc_score, exc_score),
            ["scores below threshold or tie"],
        )

    def screen(self, text: str) -> ScreeningResult:
        """Screen a single record for inclusion or exclusion."""
        inc_hits, exc_hits = self._count_hits(text)
        inc_score, exc_score = self._scores(inc_hits, exc_hits)
        if self._should_include(inc_score, exc_score):
            return self._include_result(inc_score)
        if self._should_exclude(inc_score, exc_score):
            return self._exclude_result(exc_score)
        return self._conflict_result(inc_hits, exc_hits, inc_score, exc_score)

    def batch_screen(self, texts: List[str]) -> List[ScreeningResult]:
        return [self.screen(t) for t in texts]

