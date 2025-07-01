import asyncio
import hashlib
import json
from typing import Any, Dict, Optional


class RedisAcademicCache:
    """Simple Redis-based cache with in-memory fallback."""

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600) -> None:
        self.ttl = ttl
        try:
            import redis.asyncio as redis  # type: ignore
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self.enabled = True
        except Exception:
            # Fallback to in-memory dictionary if redis is unavailable
            self._store: Dict[str, str] = {}
            self.enabled = False

    def generate_cache_key(self, source: str, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        filters = filters or {}
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        filter_hash = hashlib.sha256(json.dumps(filters, sort_keys=True).encode("utf-8")).hexdigest()
        return f"academic:{source}:{query_hash}:{filter_hash}"

    async def get_cached_search(self, key: str) -> Optional[Dict[str, Any]]:
        if self.enabled:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        # memory fallback
        value = self._store.get(key)
        return json.loads(value) if value else None

    async def cache_search_result(self, key: str, result: Dict[str, Any], ttl: Optional[int] = None) -> None:
        ttl = ttl or self.ttl
        data = json.dumps(result)
        if self.enabled:
            await self._redis.set(key, data, ex=ttl)
        else:
            self._store[key] = data
            # naive in-memory TTL handling
            asyncio.get_event_loop().call_later(ttl, lambda: self._store.pop(key, None))

    async def invalidate(self, key: str) -> None:
        if self.enabled:
            await self._redis.delete(key)
        else:
            self._store.pop(key, None)
