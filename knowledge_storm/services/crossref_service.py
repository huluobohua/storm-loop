from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from urllib import parse, request

from dataclasses import dataclass

from .cache_service import CacheService
from .utils import CacheKeyBuilder, ConnectionManager, CircuitBreaker

try:
    import aiohttp  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    aiohttp = None

logger = logging.getLogger(__name__)


@dataclass
class CrossrefConfig:
    """Configuration for ``CrossrefService``."""

    ttl: int = 86400
    rate_limit_interval: float = 3.6
    cache: CacheService | None = None
    conn_manager: ConnectionManager | None = None
    key_builder: CacheKeyBuilder | None = None
    breaker: CircuitBreaker | None = None


class RateLimiter:
    """Asynchronous rate limiter."""

    def __init__(self, interval: float = 3.6) -> None:
        self.interval = interval
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            wait = self.interval - (time.time() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.time()


class HttpFetcher:
    """Fetch JSON from a URL using aiohttp with sync fallback."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self.conn_manager = conn_manager

    async def safe_session(self) -> Optional["aiohttp.ClientSession"]:
        try:
            return await self.conn_manager.get_session()
        except RuntimeError:
            return None

    async def fetch_async(
        self, session: "aiohttp.ClientSession", url: str, params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        async with session.get(url, params=params, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def fetch_sync(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        def _sync() -> Dict[str, Any]:
            full_url = url
            if params:
                full_url += f"?{parse.urlencode(params)}"
            with request.urlopen(full_url) as resp:
                return json.load(resp)  # type: ignore

        import json
        return await asyncio.to_thread(_sync)

    async def attempt_fetch(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        session = await self.safe_session()
        if session:
            return await self.fetch_async(session, url, params)
        return await self.fetch_sync(url, params)

    async def try_fetch(self, url: str, params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        try:
            return await self.attempt_fetch(url, params)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # pragma: no cover - network errors
            logger.exception("Failed request to %s: %s", url, e)
        return None

    async def fetch_with_retry(
        self, url: str, params: Optional[Dict[str, Any]], breaker: CircuitBreaker
    ) -> Dict[str, Any]:
        for attempt in range(3):
            result = await self.try_fetch(url, params)
            if result is not None:
                breaker.record_success()
                return result
            if attempt >= 2 or not breaker.should_allow_request():
                break
            await asyncio.sleep(2 ** attempt)
        breaker.record_failure()
        return {}


class CrossrefService:
    """Service layer for Crossref API interactions."""

    BASE_URL = "https://api.crossref.org/works"
    JOURNAL_URL = "https://api.crossref.org/journals"

    def __init__(
        self,
        config: CrossrefConfig | None = None,
        fetcher: HttpFetcher | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        config = config or CrossrefConfig()
        self.cache = config.cache or CacheService(ttl=config.ttl)
        self.ttl = config.ttl
        self.conn_manager = config.conn_manager or ConnectionManager()
        self.key_builder = config.key_builder or CacheKeyBuilder()
        self.breaker = config.breaker or CircuitBreaker()
        self.fetcher = fetcher or HttpFetcher(self.conn_manager)
        self.limiter = limiter or RateLimiter(config.rate_limit_interval)

    async def close(self) -> None:
        await self.conn_manager.close()

    async def __aenter__(self) -> "CrossrefService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _get_cached(self, url: str, params: Optional[Dict[str, Any]]) -> tuple[str, Any]:
        key = self.key_builder.build_key(url, params)
        return key, await self.cache.get(key)

    async def _record_success(self, key: str, data: Dict[str, Any]) -> None:
        await self.cache.set(key, data, self.ttl)
        self.breaker.record_success()

    async def _ensure_can_call(self) -> None:
        if not self.breaker.should_allow_request():
            raise RuntimeError("Circuit breaker open")
        await self.limiter.wait()

    async def _retrieve_data(self, key: str, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        data = await self.fetcher.fetch_with_retry(url, params, self.breaker)
        if data:
            await self._record_success(key, data)
        return data

    async def _fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key, cached = await self._get_cached(url, params)
        if cached is not None:
            return cached
        await self._ensure_can_call()
        return await self._retrieve_data(key, url, params)

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
