import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from knowledge_storm import STORMConfig, EnhancedSTORMEngine


class TestPerformance:
    def test_concurrent_article_generation(self):
        config = STORMConfig("hybrid")
        engine = EnhancedSTORMEngine(config)

        async def run():
            start = time.perf_counter()
            tasks = [engine.generate_article(f"topic_{i}") for i in range(10)]
            results = await asyncio.gather(*tasks)
            end = time.perf_counter()
            return results, end - start

        results, duration = asyncio.run(run())

        assert len(results) == 10
        assert all(article.topic.startswith("topic_") for article in results)
        assert duration < 1.0

    def test_thread_safe_mode_switching(self):
        config = STORMConfig("hybrid")

        def switch_mode_repeatedly():
            for _ in range(100):
                config.switch_mode("academic")
                config.switch_mode("wikipedia")
                config.switch_mode("hybrid")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(switch_mode_repeatedly) for _ in range(5)]
            for future in futures:
                future.result()

        assert config.mode in ["academic", "wikipedia", "hybrid"]


