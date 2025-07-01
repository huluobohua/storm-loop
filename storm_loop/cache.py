"""Caching utilities with metrics and multi-backend support."""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Dict, Optional


class CacheMetrics:
    """Collects metrics for cache operations."""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.errors = 0

    def record_hit(self) -> None:
        self.hits += 1

    def record_miss(self) -> None:
        self.misses += 1

    def record_error(self) -> None:
        self.errors += 1

    def snapshot(self) -> Dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
        }


class CacheBackend(ABC):
    """Abstract backend API used by the cache."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Retrieve a cached value."""

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        """Store a value with a given TTL."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""

    @abstractmethod
    def size(self) -> int:
        """Return approximate cache size."""


class LRUMemoryBackend(CacheBackend):
    """Simple in-memory LRU backend."""

    def __init__(self, capacity: int = 128) -> None:
        self.capacity = capacity
        self._store: "OrderedDict[str, tuple[str, Optional[float]]]" = OrderedDict()

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        value, expires_at = item
        if expires_at and expires_at < time.time():
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    async def set(self, key: str, value: str, ttl: int) -> None:
        expires_at = time.time() + ttl if ttl else None
        if key in self._store:
            self._store.pop(key)
        elif len(self._store) >= self.capacity:
            self._store.popitem(last=False)
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def size(self) -> int:
        return len(self._store)


class RedisBackend(CacheBackend):
    """Redis-based cache backend."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis  # type: ignore

        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    def size(self) -> int:
        return 0


class MetricsBackend(CacheBackend):
    """Wraps another backend to collect metrics."""

    def __init__(self, backend: CacheBackend, metrics: CacheMetrics) -> None:
        self.backend = backend
        self.metrics = metrics

    async def get(self, key: str) -> Optional[str]:
        try:
            value = await self.backend.get(key)
        except Exception:
            self.metrics.record_error()
            value = None
        if value is None:
            self.metrics.record_miss()
        else:
            self.metrics.record_hit()
        return value

    async def set(self, key: str, value: str, ttl: int) -> None:
        try:
            await self.backend.set(key, value, ttl)
        except Exception:
            self.metrics.record_error()

    async def delete(self, key: str) -> None:
        try:
            await self.backend.delete(key)
        except Exception:
            self.metrics.record_error()

    def size(self) -> int:
        return self.backend.size()


class RedisAcademicCache:
    """Multi-level cache with optional Redis backend."""

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600, memory_capacity: int = 128) -> None:
        self.ttl = ttl
        self.metrics = CacheMetrics()
        self.memory_backend = MetricsBackend(LRUMemoryBackend(memory_capacity), self.metrics)
        self.redis_backend: Optional[MetricsBackend]
        try:
            self.redis_backend = MetricsBackend(RedisBackend(redis_url), self.metrics)
        except Exception:
            self.redis_backend = None

    def generate_cache_key(self, source: str, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        filters = filters or {}
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        filter_hash = hashlib.sha256(json.dumps(filters, sort_keys=True).encode("utf-8")).hexdigest()
        return f"academic:{source}:{query_hash}:{filter_hash}"

    async def get_cached_search(self, key: str) -> Optional[Dict[str, Any]]:
        value = await self.memory_backend.get(key)
        if value is not None:
            return json.loads(value)
        if self.redis_backend:
            value = await self.redis_backend.get(key)
            if value is not None:
                await self.memory_backend.set(key, value, self.ttl)
                return json.loads(value)
        return None

    async def cache_search_result(self, key: str, result: Dict[str, Any], ttl: Optional[int] = None) -> None:
        ttl = ttl or self.ttl
        data = json.dumps(result)
        await self.memory_backend.set(key, data, ttl)
        if self.redis_backend:
            await self.redis_backend.set(key, data, ttl)

    async def invalidate(self, key: str) -> None:
        await self.memory_backend.delete(key)
        if self.redis_backend:
            await self.redis_backend.delete(key)

    def memory_usage(self) -> int:
        """Approximate in-memory cache size."""
        return self.memory_backend.size()

    async def warm_cache(self, entries: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> None:
        """Pre-populate the cache with common queries."""
        for key, value in entries.items():
            await self.cache_search_result(key, value, ttl=ttl)


def cache_decorator(cache: RedisAcademicCache, source: str):
    """Decorator to transparently cache async search methods."""

    def wrapper(func):
        async def inner(query: str, *args: Any, **kwargs: Any):
            filters = kwargs.get("filters")
            key = cache.generate_cache_key(source, query, filters)
            cached = await cache.get_cached_search(key)
            if cached is not None:
                return cached
            result = await func(query, *args, **kwargs)
            await cache.cache_search_result(key, result)
            return result

        return inner

    return wrapper
