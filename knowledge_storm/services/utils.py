from __future__ import annotations

from typing import Any, Dict, Optional
from urllib import parse

try:
    import aiohttp  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    aiohttp = None


class CacheKeyBuilder:
    """Builds cache keys for API requests."""

    def build_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        base_key = url
        if params:
            sorted_params = sorted(params.items())
            param_string = parse.urlencode(sorted_params)
            return f"{base_key}?{param_string}"
        return base_key


class ConnectionManager:
    """Manages a reusable aiohttp session."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _create_session(self) -> "aiohttp.ClientSession":
        if aiohttp is None:
            raise RuntimeError("aiohttp not installed")
        return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

    async def get_session(self) -> "aiohttp.ClientSession":
        if self._session is None:
            self._session = await self._create_session()
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "ConnectionManager":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


class CircuitBreaker:
    """Simple circuit breaker for failing external calls."""

    def __init__(self, failure_threshold: int = 3) -> None:
        self.failure_count = 0
        self.failure_threshold = failure_threshold

    def record_success(self) -> None:
        self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1

    def should_allow_request(self) -> bool:
        return self.failure_count < self.failure_threshold
