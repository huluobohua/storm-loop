import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from knowledge_storm import STORMConfig, EnhancedSTORMEngine
from knowledge_storm.hybrid_engine import Article


class TestIntegration:
    def test_end_to_end_academic_workflow(self):
        config = STORMConfig("academic")
        mock_runner = AsyncMock()
        mock_runner.run_academic_workflow.return_value = Article(
            topic="quantum computing",
            content="Detailed academic content...",
            metadata={"citations": 15, "peer_reviewed": True},
        )

        engine = EnhancedSTORMEngine(config, mock_runner)

        async def run():
            return await engine.generate_article("quantum computing")

        result = asyncio.run(run())

        assert result.topic == "quantum computing"
        assert "academic" in result.content.lower()
        mock_runner.run_academic_workflow.assert_called_once()

    def test_fallback_on_academic_workflow_failure(self):
        config = STORMConfig("academic")
        mock_runner = AsyncMock()
        mock_runner.run_academic_workflow.side_effect = Exception("Academic service down")
        mock_runner.run_original_workflow.return_value = Article(
            topic="quantum computing",
            content="Basic article content...",
        )

        engine = EnhancedSTORMEngine(config, mock_runner)

        async def run():
            with patch.object(engine, '_generate_standard_article') as fallback_mock:
                fallback_mock.return_value = Article(topic="quantum computing", content="fallback")
                result = await engine.generate_article("quantum computing")
                assert result.content == "fallback"
                fallback_mock.assert_called_once()

        asyncio.run(run())


