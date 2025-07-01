from __future__ import annotations

import asyncio
from difflib import SequenceMatcher
from typing import Any, Dict, List

from .academic_source_service import AcademicSourceService, SourceQualityScorer
from .cache_service import CacheService
import re


class CitationVerificationSystem:
    """Verify citations and format them in various styles."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache or CacheService()
        self.source_service = AcademicSourceService(cache=self.cache)
        self.scorer = SourceQualityScorer()

    def calculate_verification_score(self, claim: str, source_text: str) -> float:
        """Return a similarity ratio between the claim and source text."""
        return SequenceMatcher(None, claim.lower(), source_text.lower()).ratio()

    def assess_source_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not metadata:
            return {}
        return {"score": self.scorer.score_source(metadata)}

    async def verify_citation_async(
        self, claim: str, source: Dict[str, Any]
    ) -> Dict[str, Any]:
        cache_key = f"{claim}:{source.get('doi') or source.get('url', '')}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        text = source.get("text") or source.get("abstract", "")
        metadata = source
        if not text and "doi" in source:
            metadata = await self.source_service.get_publication_metadata(source["doi"])
            text = metadata.get("abstract", "")

        score = self.calculate_verification_score(claim, text)
        result = {
            "verified": score > 0.7,
            "confidence": score,
            "quality_metrics": self.assess_source_quality(metadata),
        }
        await self.cache.set(cache_key, result)
        return result

    def verify_citation(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.verify_citation_async(claim, source))

    def verify_section(
        self, section_text: str, info_list: List[Any]
    ) -> List[Dict[str, Any]]:
        indices = [int(i[1:-1]) for i in re.findall(r"\[\d+\]", section_text)]
        results = []
        for idx in indices:
            if 0 < idx <= len(info_list):
                snippet = info_list[idx - 1].snippets[0] if info_list[idx - 1].snippets else ""
                result = self.verify_citation(snippet, {"text": snippet})
                results.append(result)
        return results

    def format_citation(self, source: Dict[str, Any], style: str = "APA") -> str:
        author = source.get("author", "Anon")
        year = source.get("year") or source.get("publication_year", "n.d.")
        title = source.get("title", "")
        if style.upper() == "MLA":
            return f"{author}. \"{title}.\" ({year})."
        if style.upper() == "CHICAGO":
            return f"{author}. {year}. {title}."
        return f"{author} ({year}). {title}."
