import json
from typing import Any, Optional

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional
    redis = None


class CacheService:
    """Simple async cache service using Redis if available."""

    def __init__(self, url: str = "redis://localhost:6379/0", ttl: int = 3600) -> None:
        self.ttl = ttl
        self._local_cache: dict[str, Any] = {}
        self.redis: Optional["redis.Redis"] = None
        if redis is not None:
            try:
                self.redis = redis.from_url(url)
            except Exception:
                self.redis = None

    async def get(self, key: str) -> Any:
        if self.redis is not None:
            try:
                value = await self.redis.get(key)
                if value is not None:
                    return json.loads(value)
            except Exception:
                pass
        return self._local_cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.ttl
        if self.redis is not None:
            try:
                await self.redis.set(key, json.dumps(value), ex=ttl)
                return
            except Exception:
                pass
        self._local_cache[key] = value

    async def close(self) -> None:
        if self.redis is not None:
            try:
                await self.redis.close()
            except Exception:
                pass
