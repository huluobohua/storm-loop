from __future__ import annotations

import difflib
from typing import Any, Dict

from .academic_source_service import SourceQualityScorer


class CitationVerificationSystem:
    """Verify and format citations using simple heuristics."""

    def __init__(self, scorer: SourceQualityScorer | None = None) -> None:
        self.scorer = scorer or SourceQualityScorer()

    def calculate_verification_score(self, claim: str, source_text: str) -> float:
        """Return a similarity score between claim and source text."""
        return difflib.SequenceMatcher(None, claim.lower(), source_text.lower()).ratio()

    def assess_source_quality(self, source: Dict[str, Any]) -> float:
        """Assess quality of an academic source using :class:`SourceQualityScorer`."""
        return self.scorer.score_source(source)

    def verify_citation(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a claim against a source.

        Returns a dictionary with verification status, confidence score and quality metrics.
        """
        text = source.get("content") or " ".join(source.get("snippets", [])) or source.get("title", "")
        score = self.calculate_verification_score(claim, text)
        return {
            "verified": score > 0.8,
            "confidence": score,
            "quality_metrics": self.assess_source_quality(source),
        }

    def format_citation(self, source: Dict[str, Any], style: str = "APA") -> str:
        """Format a citation according to the specified style."""
        authors = source.get("author", "Unknown")
        year = source.get("publication_year") or source.get("year") or "n.d."
        title = source.get("title", "")
        doi = source.get("doi", "")
        style = style.upper()
        if style == "APA":
            return f"{authors} ({year}). {title}. DOI:{doi}"
        if style == "MLA":
            return f"{authors}. \"{title}.\" {year}. DOI:{doi}"
        if style == "CHICAGO":
            return f"{authors}. {title}. ({year}). DOI:{doi}"
        raise ValueError(f"Unsupported citation style: {style}")
