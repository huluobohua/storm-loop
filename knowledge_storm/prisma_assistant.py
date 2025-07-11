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

    DEFAULT_INCLUDE = ["randomized", "controlled", "trial", "study", "results"]
    DEFAULT_EXCLUDE = ["protocol", "editorial", "letter", "commentary", "case report"]

    def __init__(
        self,
        include_patterns: Sequence[str] | None = None,
        exclude_patterns: Sequence[str] | None = None,
        threshold: float = 0.8,
    ) -> None:
        self._validate_threshold(threshold)
        self.include_patterns = (
            list(include_patterns)
            if include_patterns is not None
            else self.DEFAULT_INCLUDE[:]
        )
        self.exclude_patterns = (
            list(exclude_patterns)
            if exclude_patterns is not None
            else self.DEFAULT_EXCLUDE[:]
        )
        self.threshold = threshold

    def _validate_threshold(self, threshold: float) -> None:
        """Validate threshold is between 0 and 1."""
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")

    def _count_hits(self, text: str) -> Tuple[int, int]:
        text = text.lower()
        inc = sum(1 for p in self.include_patterns if p in text)
        exc = sum(1 for p in self.exclude_patterns if p in text)
        return inc, exc

    def _calculate_score(self, hits: int, patterns: List[str]) -> float:
        """Calculate normalized score for pattern hits."""
        return hits / len(patterns) if patterns else 0.0

    def _scores(self, inc_hits: int, exc_hits: int) -> Tuple[float, float]:
        """Return inclusion and exclusion scores."""
        inc_score = self._calculate_score(inc_hits, self.include_patterns)
        exc_score = self._calculate_score(exc_hits, self.exclude_patterns)
        return inc_score, exc_score

    def _is_clear_decision(self, score: float, opposite_score: float) -> bool:
        """Check if score passes threshold and exceeds the opposite score."""
        return score >= self.threshold and score > opposite_score


    def _should_include(self, inc: float, exc: float) -> bool:
        return self._is_clear_decision(inc, exc)

    def _should_exclude(self, inc: float, exc: float) -> bool:
        return self._is_clear_decision(exc, inc)

    def _clear_decision_result(self, decision: str, score: float) -> ScreeningResult:
        return ScreeningResult(
            decision,
            score,
            [f"{decision} score {score:.2f} >= {self.threshold}"]
        )

    def _include_result(self, score: float) -> ScreeningResult:
        return self._clear_decision_result("include", score)

    def _exclude_result(self, score: float) -> ScreeningResult:
        return self._clear_decision_result("exclude", score)

    def _conflict_result(
        self,
        inc_hits: int,
        exc_hits: int,
        inc_score: float,
        exc_score: float,
    ) -> ScreeningResult:
        if inc_hits > exc_hits:
            return self._conflict_winner("include", inc_score)
        if exc_hits > inc_hits:
            return self._conflict_winner("exclude", exc_score)
        return self._conflict_tie(inc_score, exc_score)

    def _conflict_winner(self, decision: str, score: float) -> ScreeningResult:
        return ScreeningResult(decision, score, [f"more {decision} keywords"])

    def _conflict_tie(self, inc_score: float, exc_score: float) -> ScreeningResult:
        return ScreeningResult(
            "unsure", max(inc_score, exc_score), ["scores below threshold or tie"]
        )

    def screen(self, text: str) -> ScreeningResult:
        """Screen a single text record for inclusion or exclusion."""
        inc_hits, exc_hits = self._count_hits(text)
        inc_score, exc_score = self._scores(inc_hits, exc_hits)
        if self._should_include(inc_score, exc_score):
            return self._include_result(inc_score)
        if self._should_exclude(inc_score, exc_score):
            return self._exclude_result(exc_score)
        return self._conflict_result(inc_hits, exc_hits, inc_score, exc_score)

    def batch_screen(self, texts: List[str]) -> List[ScreeningResult]:
        """Screen multiple text records."""
        return [self.screen(t) for t in texts]

