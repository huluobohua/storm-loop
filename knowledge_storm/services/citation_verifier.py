from __future__ import annotations

import asyncio
import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from .academic_source_service import AcademicSourceService, SourceQualityScorer
from .cache_service import CacheService
from .config import VerificationConfig

logger = logging.getLogger(__name__)



class CitationVerifier:
    """Verify textual claims against academic sources."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache or CacheService()
        self.source_service = AcademicSourceService(cache=self.cache)
        self.scorer = SourceQualityScorer()

    def verify_citation(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.verify_citation_async(claim, source))

    async def verify_citation_async(self, claim: str, source: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = self._build_cache_key(claim, source)
        cached = await self._get_cached_result(cache_key)
        if cached is not None:
            return cached
        return await self._perform_verification(claim, source, cache_key)

    def _build_cache_key(self, claim: str, source: Dict[str, Any]) -> str:
        identifier = source.get("doi") or source.get("url", "")
        return f"{claim}:{identifier}"

    async def _get_cached_result(self, cache_key: str) -> Dict[str, Any] | None:
        return await self.cache.get(cache_key)

    async def _perform_verification(self, claim: str, source: Dict[str, Any], cache_key: str) -> Dict[str, Any]:
        text, metadata = await self._extract_source_content(source)
        result = self._create_verification_result(claim, text, metadata)
        await self.cache.set(cache_key, result)
        return result

    async def _extract_source_content(self, source: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        text = self._get_initial_text(source)
        metadata = source
        if self._needs_doi_fetch(text, source):
            text, metadata = await self._fetch_from_doi(source["doi"])
        return text, metadata

    def _get_initial_text(self, source: Dict[str, Any]) -> str:
        return source.get("text") or source.get("abstract", "")

    def _needs_doi_fetch(self, text: str, source: Dict[str, Any]) -> bool:
        return not text and "doi" in source

    async def _fetch_from_doi(self, doi: str) -> Tuple[str, Dict[str, Any]]:
        metadata = await self._fetch_metadata(doi)
        text = metadata.get("abstract", "")
        return text, metadata

    async def _fetch_metadata(self, doi: str) -> Dict[str, Any]:
        try:
            return await self.source_service.get_publication_metadata(doi)
        except Exception as e:  # pragma: no cover - network errors
            logger.error("Failed to fetch metadata for DOI %s: %s", doi, e)
            return {}

    def _create_verification_result(self, claim: str, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        score = self._calculate_verification_score(claim, text)
        return {
            "verified": self._is_verified(score),
            "confidence": score,
            "quality_metrics": self._assess_source_quality(metadata),
        }

    def _calculate_verification_score(self, claim: str, source_text: str) -> float:
        normalized_claim = self._normalize_text(claim)
        normalized_source = self._normalize_text(source_text)
        return SequenceMatcher(None, normalized_claim, normalized_source).ratio()

    def _normalize_text(self, text: str) -> str:
        return text.lower()

    def _assess_source_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not metadata:
            return {}
        return {"score": self.scorer.score_source(metadata)}

    def _is_verified(self, score: float) -> bool:
        return score > VerificationConfig.VERIFICATION_THRESHOLD


