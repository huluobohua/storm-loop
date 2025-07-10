from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from urllib import parse, request

from .cache_service import CacheService
from .utils import CacheKeyBuilder, ConnectionManager, CircuitBreaker

try:
    import aiohttp  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    aiohttp = None

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 5
BASE_YEAR = 2000
RECENCY_WEIGHT = 0.1


class AcademicSourceService:
    """Service for retrieving academic sources from OpenAlex and Crossref."""

    OPENALEX_URL = "https://api.openalex.org/works"
    CROSSREF_URL = "https://api.crossref.org/works"

    def __init__(
        self,
        cache: CacheService | None = None,
        ttl: int = 3600,
        conn_manager: ConnectionManager | None = None,
        key_builder: CacheKeyBuilder | None = None,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self.cache = cache or CacheService(ttl=ttl)
        self.ttl = ttl
        self.conn_manager = conn_manager or ConnectionManager()
        self.key_builder = key_builder or CacheKeyBuilder()
        self.breaker = breaker or CircuitBreaker()

    async def close(self) -> None:
        await self.conn_manager.close()

    async def __aenter__(self) -> "AcademicSourceService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def search_openalex(self, query: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        params = {"search": query, "per-page": limit}
        data = await self._fetch_json(self.OPENALEX_URL, params)
        return data.get("results", [])

    async def get_paper_details(self, paper_id: str) -> Dict[str, Any]:
        return await self._fetch_json(f"{self.OPENALEX_URL}/{paper_id}")

    async def search_crossref(self, query: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        params = {"query": query, "rows": limit}
        data = await self._fetch_json(self.CROSSREF_URL, params)
        return data.get("message", {}).get("items", [])

    async def resolve_doi(self, doi: str) -> Dict[str, Any]:
        data = await self._fetch_json(f"{self.CROSSREF_URL}/{doi}")
        return data.get("message", {})

    async def get_publication_metadata(self, doi: str) -> Dict[str, Any]:
        return await self.resolve_doi(doi)

    async def search_combined(self, query: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        openalex_coro = self.search_openalex(query, limit)
        crossref_coro = self.search_crossref(query, limit)
        openalex, crossref = await asyncio.gather(openalex_coro, crossref_coro)
        return openalex + crossref

    async def warm_cache(
        self, queries: List[str], limit: int = DEFAULT_LIMIT, parallel: int = 5
    ) -> None:
        """Preload results for multiple queries concurrently.

        Parameters
        ----------
        queries:
            List of search strings to cache.
        limit:
            Maximum results per query.
        parallel:
            Maximum number of concurrent fetch operations.
        """

        semaphore = asyncio.Semaphore(parallel)

        async def _fetch(q: str) -> None:
            async with semaphore:
                await self.search_combined(q, limit)

        await asyncio.gather(*(_fetch(q) for q in queries))

    async def _fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cache_key = self.key_builder.build_key(url, params)

        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        if not self.breaker.should_allow_request():
            raise RuntimeError("Circuit breaker open")

        try:
            try:
                session = await self.conn_manager.get_session()
            except RuntimeError:
                session = None

            if session is not None:
                async with session.get(url, params=params, timeout=10) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
            else:
                def _sync() -> Dict[str, Any]:
                    full_url = url
                    if params:
                        full_url += f"?{parse.urlencode(params)}"
                    with request.urlopen(full_url) as resp:
                        return json.load(resp)

                data = await asyncio.to_thread(_sync)

            await self.cache.set(cache_key, data, self.ttl)
            self.breaker.record_success()
            return data
        except Exception:  # pragma: no cover - network errors
            self.breaker.record_failure()
            logger.exception("Failed request to %s", url)
            if not self.breaker.should_allow_request():
                raise
            return {}


class SourceQualityScorer:
    """Simple scoring based on citation count and recency."""

    def score_source(self, metadata: Dict[str, Any]) -> float:
        citations = self._get_citations(metadata)
        year = self._extract_year(metadata)
        score = float(citations)
        if year:
            score += max(0, year - BASE_YEAR) * RECENCY_WEIGHT
        return score

    def _get_citations(self, metadata: Dict[str, Any]) -> int:
        return metadata.get("cited_by_count") or metadata.get("is-referenced-by-count", 0)

    def _extract_year(self, metadata: Dict[str, Any]) -> Optional[int]:
        if "publication_year" in metadata:
            return metadata.get("publication_year")
        if "issued" in metadata and "date-parts" in metadata["issued"]:
            return metadata["issued"]["date-parts"][0][0]
        return None

