from __future__ import annotations

import difflib
from typing import Any, Dict

from .academic_source_service import SourceQualityScorer


class CitationVerificationSystem:
    """Verify claims against academic sources and format citations."""

    def __init__(
        self, scorer: SourceQualityScorer | None = None, threshold: float = 0.8
    ) -> None:
        self.scorer = scorer or SourceQualityScorer()
        self.threshold = threshold

    def calculate_verification_score(self, claim: str, source_text: str) -> float:
        """Return a similarity score between claim and source text."""
        return difflib.SequenceMatcher(None, claim.lower(), source_text.lower()).ratio()

    def assess_source_quality(self, source: Dict[str, Any]) -> float:
        """Assess source quality using :class:`SourceQualityScorer`."""
        return self.scorer.score_source(source)

    def verify_citation(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a claim against a source dictionary."""
        source_text = source.get("text", "")
        score = self.calculate_verification_score(claim, source_text)
        return {
            "verified": score > self.threshold,
            "confidence": score,
            "quality_metrics": self.assess_source_quality(source),
        }

    def format_citation(self, source: Dict[str, Any], style: str = "APA") -> str:
        """Format citation metadata using the specified style."""
        authors = source.get("author", "Unknown")
        year = source.get("publication_year") or "n.d."
        title = source.get("title", "")
        doi = source.get("doi", "")
        style = style.lower()

        if style == "mla":
            return f'{authors}. "{title}." ({year}), DOI:{doi}'
        if style == "chicago":
            return f"{authors}. {title}. {year}. DOI:{doi}"
        return f"{authors} ({year}). {title}. DOI:{doi}"
