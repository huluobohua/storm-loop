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
