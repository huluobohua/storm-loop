from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from urllib import parse, request

from .cache_service import CacheService
from .utils import CacheKeyBuilder, ConnectionManager, CircuitBreaker

try:
    import aiohttp  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    aiohttp = None

logger = logging.getLogger(__name__)


class CrossrefService:
    """Service layer for Crossref API interactions."""

    BASE_URL = "https://api.crossref.org/works"
    JOURNAL_URL = "https://api.crossref.org/journals"

    def __init__(
        self,
        cache: CacheService | None = None,
        ttl: int = 86400,
        conn_manager: ConnectionManager | None = None,
        key_builder: CacheKeyBuilder | None = None,
        breaker: CircuitBreaker | None = None,
        rate_limit_interval: float = 3.6,
    ) -> None:
        self.cache = cache or CacheService(ttl=ttl)
        self.ttl = ttl
        self.conn_manager = conn_manager or ConnectionManager()
        self.key_builder = key_builder or CacheKeyBuilder()
        self.breaker = breaker or CircuitBreaker()
        self._rate_limit = rate_limit_interval
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        await self.conn_manager.close()

    async def __aenter__(self) -> "CrossrefService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _wait_rate_limit(self) -> None:
        async with self._lock:
            wait = self._rate_limit - (time.time() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.time()

    async def _fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cache_key = self.key_builder.build_key(url, params)
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        if not self.breaker.should_allow_request():
            raise RuntimeError("Circuit breaker open")
        await self._wait_rate_limit()
        attempt = 0
        while True:
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
                            return json.load(resp)  # type: ignore
                    import json
                    data = await asyncio.to_thread(_sync)
                await self.cache.set(cache_key, data, self.ttl)
                self.breaker.record_success()
                return data
            except asyncio.CancelledError:
                raise
            except Exception as e:  # pragma: no cover - network errors
                self.breaker.record_failure()
                logger.exception("Failed request to %s: %s", url, e)
                attempt += 1
                if attempt >= 3 or not self.breaker.should_allow_request():
                    break
                await asyncio.sleep(2 ** attempt)
        return {}

    async def search_works(self, query: str, limit: int = 5) -> list[Dict[str, Any]]:
        params = {"query": query, "rows": limit}
        data = await self._fetch_json(self.BASE_URL, params)
        return data.get("message", {}).get("items", [])

    async def get_metadata_by_doi(self, doi: str) -> Dict[str, Any]:
        data = await self._fetch_json(f"{self.BASE_URL}/{doi}")
        return data.get("message", {})

    async def validate_citation(self, citation_data: Dict[str, Any]) -> bool:
        doi = citation_data.get("doi")
        if not doi:
            return False
        metadata = await self.get_metadata_by_doi(doi)
        return bool(metadata)

    async def get_journal_metadata(self, issn: str) -> Dict[str, Any]:
        data = await self._fetch_json(f"{self.JOURNAL_URL}/{issn}")
        return data.get("message", {})
