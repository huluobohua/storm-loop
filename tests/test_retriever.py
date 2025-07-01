import asyncio

from storm_loop.cache import RedisAcademicCache
from storm_loop.retriever import AcademicRetrieverAgent


def test_retriever_caches_result():
    async def run():
        cache = RedisAcademicCache()
        agent = AcademicRetrieverAgent(cache)

        result1 = await agent.search("quantum physics")
        assert result1.source == "openalex"

        # second call should hit cache
        result2 = await agent.search("quantum physics")
        assert result2.results == result1.results

    asyncio.run(run())
