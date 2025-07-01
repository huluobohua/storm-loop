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
        normalized_claim = self._normalize_text(claim)
        normalized_source = self._normalize_text(source_text)
        return SequenceMatcher(None, normalized_claim, normalized_source).ratio()

    def _normalize_text(self, text: str) -> str:
        return text.lower()

    def assess_source_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not metadata:
            return self._empty_quality_result()
        return self._create_quality_result(metadata)

    def _empty_quality_result(self) -> Dict[str, Any]:
        return {}

    def _create_quality_result(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": self.scorer.score_source(metadata)}

    async def verify_citation_async(
        self, claim: str, source: Dict[str, Any]
    ) -> Dict[str, Any]:
        cache_key = self._build_cache_key(claim, source)
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        return await self._perform_verification(claim, source, cache_key)

    def _build_cache_key(self, claim: str, source: Dict[str, Any]) -> str:
        identifier = source.get("doi") or source.get("url", "")
        return f"{claim}:{identifier}"

    async def _perform_verification(
        self, claim: str, source: Dict[str, Any], cache_key: str
    ) -> Dict[str, Any]:
        text, metadata = await self._extract_source_content(source)
        result = self._create_verification_result(claim, text, metadata)
        await self.cache.set(cache_key, result)
        return result

    async def _extract_source_content(
        self, source: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        text = self._get_initial_text(source)
        metadata = source
        if not text and "doi" in source:
            metadata = await self._fetch_metadata(source["doi"])
            text = metadata.get("abstract", "")
        return text, metadata

    def _get_initial_text(self, source: Dict[str, Any]) -> str:
        return source.get("text") or source.get("abstract", "")

    async def _fetch_metadata(self, doi: str) -> Dict[str, Any]:
        return await self.source_service.get_publication_metadata(doi)

    def _create_verification_result(
        self, claim: str, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        score = self.calculate_verification_score(claim, text)
        quality = self.assess_source_quality(metadata)
        return {
            "verified": self._is_verified(score),
            "confidence": score,
            "quality_metrics": quality,
        }

    def _is_verified(self, score: float) -> bool:
        return score > 0.7

    def verify_citation(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.verify_citation_async(claim, source))

    def verify_section(
        self, section_text: str, info_list: List[Any]
    ) -> List[Dict[str, Any]]:
        indices = self._extract_citation_indices(section_text)
        return self._verify_citations_by_indices(indices, info_list)

    def _extract_citation_indices(self, section_text: str) -> List[int]:
        return [int(i[1:-1]) for i in re.findall(r"\[\d+\]", section_text)]

    def _verify_citations_by_indices(
        self, indices: List[int], info_list: List[Any]
    ) -> List[Dict[str, Any]]:
        results = []
        for idx in indices:
            result = self._verify_single_citation(idx, info_list)
            if result:
                results.append(result)
        return results

    def _verify_single_citation(
        self, idx: int, info_list: List[Any]
    ) -> Dict[str, Any] | None:
        if not (0 < idx <= len(info_list)):
            return None
        snippet = self._get_snippet_text(info_list[idx - 1])
        return self.verify_citation(snippet, {"text": snippet})

    def _get_snippet_text(self, info_item: Any) -> str:
        return info_item.snippets[0] if info_item.snippets else ""

    def format_citation(self, source: Dict[str, Any], style: str = "APA") -> str:
        citation_data = self._extract_citation_data(source)
        return self._format_by_style(citation_data, style.upper())

    def _extract_citation_data(self, source: Dict[str, Any]) -> Dict[str, str]:
        return {
            "author": source.get("author", "Anon"),
            "year": self._get_publication_year(source),
            "title": source.get("title", ""),
        }

    def _get_publication_year(self, source: Dict[str, Any]) -> str:
        return str(source.get("year") or source.get("publication_year", "n.d."))

    def _format_by_style(self, data: Dict[str, str], style: str) -> str:
        if style == "MLA":
            return self._format_mla(data)
        if style == "CHICAGO":
            return self._format_chicago(data)
        return self._format_apa(data)

    def _format_mla(self, data: Dict[str, str]) -> str:
        return f"{data['author']}. \"{data['title']}.\" ({data['year']})."

    def _format_chicago(self, data: Dict[str, str]) -> str:
        return f"{data['author']}. {data['year']}. {data['title']}."

    def _format_apa(self, data: Dict[str, str]) -> str:
        return f"{data['author']} ({data['year']}). {data['title']}."
