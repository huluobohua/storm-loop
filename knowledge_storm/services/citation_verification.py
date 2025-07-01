from __future__ import annotations

import asyncio
import re
from typing import Any, Dict

from .academic_source_service import AcademicSourceService, SourceQualityScorer

DEFAULT_THRESHOLD = 0.8


class CitationVerificationSystem:
    """Verify and format citations from academic sources."""

    def __init__(
        self,
        service: AcademicSourceService | None = None,
        scorer: SourceQualityScorer | None = None,
        default_style: str = "APA",
        verification_threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.service = service or AcademicSourceService()
        self.scorer = scorer or SourceQualityScorer()
        self.default_style = default_style
        self.threshold = verification_threshold

    def calculate_verification_score(self, claim: str, metadata: Dict[str, Any]) -> float:
        """Very naive similarity based on word overlap."""
        text = (metadata.get("title", "") + " " + metadata.get("abstract", "")).lower()
        words = re.findall(r"\w+", claim.lower())
        if not words:
            return 0.0
        matches = sum(1 for w in words if w in text)
        return matches / len(words)

    def assess_source_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        score = self.scorer.score_source(metadata)
        citations = self.scorer._get_citations(metadata)
        year = metadata.get("publication_year") or None
        return {"score": score, "citations": citations, "year": year}

    async def verify_citation(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        metadata = source
        if "doi" in source:
            try:
                metadata = await self.service.get_publication_metadata(source["doi"])
            except Exception:  # pragma: no cover - network failures
                metadata = source
        score = self.calculate_verification_score(claim, metadata)
        return {
            "verified": score > self.threshold,
            "confidence": score,
            "quality_metrics": self.assess_source_quality(metadata),
        }

    def format_citation(self, source: Dict[str, Any], style: str | None = None) -> str:
        style = (style or self.default_style).lower()
        authors = source.get("author", "Unknown")
        year = source.get("publication_year") or "n.d."
        title = source.get("title", "")
        doi = source.get("doi", "")
        if style == "apa":
            return f"{authors} ({year}). {title}. DOI:{doi}"
        if style == "mla":
            return f"{authors}. \"{title}.\" {year}. DOI:{doi}."
        if style == "chicago":
            return f"{authors}. {title}. ({year}). DOI:{doi}."
        raise ValueError("Unsupported citation style")

