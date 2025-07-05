from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from urllib import parse, request

from dataclasses import dataclass, field

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


@dataclass
class RateLimiter:
    """Simple async rate limiter."""

    interval: float
    _last: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def wait(self) -> None:
        async with self._lock:
            wait = self.interval - (time.time() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.time()


@dataclass
class CacheManager:
    """Handles cache operations."""

    cache: CacheService
    ttl: int
    key_builder: CacheKeyBuilder

    async def get(self, url: str, params: Optional[Dict[str, Any]]) -> tuple[str, Any]:
        key = self.key_builder.build_key(url, params)
        return key, await self.cache.get(key)

    async def set(self, key: str, data: Dict[str, Any]) -> None:
        await self.cache.set(key, data, self.ttl)


class HttpFetcher:
    """Fetch JSON data using aiohttp when available."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self.conn_manager = conn_manager

    async def fetch(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        session = await self._safe_session()
        if session:
            return await self._fetch_async(session, url, params)
        return await self._fetch_sync(url, params)

    async def _safe_session(self) -> Optional["aiohttp.ClientSession"]:
        try:
            return await self.conn_manager.get_session()
        except RuntimeError:
            return None

    async def _fetch_async(self, session: "aiohttp.ClientSession", url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        async with session.get(url, params=params, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_sync(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        def _sync() -> Dict[str, Any]:
            full_url = url
            if params:
                full_url += f"?{parse.urlencode(params)}"
            with request.urlopen(full_url) as resp:
                return json.load(resp)  # type: ignore

        import json
        return await asyncio.to_thread(_sync)


class CrossrefService:
    """Service layer for Crossref API interactions."""

    BASE_URL = "https://api.crossref.org/works"
    JOURNAL_URL = "https://api.crossref.org/journals"

    def __init__(self, config: CrossrefConfig | None = None) -> None:
        config = config or CrossrefConfig()
        cache = config.cache or CacheService(ttl=config.ttl)
        conn = config.conn_manager or ConnectionManager()
        builder = config.key_builder or CacheKeyBuilder()
        self.breaker = config.breaker or CircuitBreaker()
        self.rate_limiter = RateLimiter(config.rate_limit_interval)
        self.cache_mgr = CacheManager(cache, config.ttl, builder)
        self.fetcher = HttpFetcher(conn)

    async def close(self) -> None:
        await self.fetcher.conn_manager.close()

    async def __aenter__(self) -> "CrossrefService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _record_success(self, key: str, data: Dict[str, Any]) -> None:
        await self.cache_mgr.set(key, data)
        self.breaker.record_success()

    async def _handle_error(self, url: str, error: Exception) -> None:
        self.breaker.record_failure()
        logger.exception("Failed request to %s: %s", url, error)

    async def _attempt_fetch(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return await self.fetcher.fetch(url, params)

    async def _should_retry(self, attempt: int) -> bool:
        return attempt < 3 and self.breaker.should_allow_request()

    async def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        attempt = 0
        while True:
            try:
                return await self._attempt_fetch(url, params)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # pragma: no cover - network errors
                await self._handle_error(url, e)
                attempt += 1
                if not await self._should_retry(attempt):
                    break
                await asyncio.sleep(2 ** attempt)
        return {}

    async def _fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key, cached = await self.cache_mgr.get(url, params)
        if cached is not None:
            return cached
        if not self.breaker.should_allow_request():
            raise RuntimeError("Circuit breaker open")
        await self.rate_limiter.wait()
        data = await self._fetch_with_retry(url, params)
        if data:
            await self._record_success(key, data)
        return data

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
