import asyncio

from storm_loop.cache import RedisAcademicCache


def test_cache_roundtrip():
    async def run():
        cache = RedisAcademicCache()
        key = cache.generate_cache_key("openalex", "example query", {})

        await cache.cache_search_result(key, {"value": 42}, ttl=1)
        result = await cache.get_cached_search(key)
        assert result == {"value": 42}

        await asyncio.sleep(1.1)
        expired = await cache.get_cached_search(key)
        assert expired is None

    asyncio.run(run())


def test_cache_metrics_and_lru():
    async def run():
        cache = RedisAcademicCache(memory_capacity=1)
        key1 = cache.generate_cache_key("openalex", "q1", {})
        await cache.cache_search_result(key1, {"num": 1})

        # hit should increase metrics.hits
        assert await cache.get_cached_search(key1) == {"num": 1}

        key2 = cache.generate_cache_key("openalex", "q2", {})
        # miss increments metrics.misses
        assert await cache.get_cached_search(key2) is None

        metrics = cache.metrics.snapshot()
        assert metrics["hits"] == 1
        assert metrics["misses"] >= 1

        # storing second key should evict the first due to LRU capacity=1
        await cache.cache_search_result(key2, {"num": 2})
        assert await cache.get_cached_search(key1) is None
    asyncio.run(run())
