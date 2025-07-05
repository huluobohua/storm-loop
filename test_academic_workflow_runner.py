import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from knowledge_storm.workflows.academic import AcademicWorkflowRunner
from knowledge_storm.hybrid_engine import Article


async def run_runner(tmp_path):
    runner = AsyncMock()
    runner.args = SimpleNamespace(output_dir=str(tmp_path))
    runner.post_run = Mock()
    article_dir = tmp_path / "topic"
    article_dir.mkdir()
    (article_dir / "storm_gen_article_polished.txt").write_text("result")
    awr = AcademicWorkflowRunner(runner)
    result = await awr.run_academic_workflow("topic")
    runner.run.assert_awaited_once()
    runner.post_run.assert_called_once()
    return result


def test_academic_workflow_runner(tmp_path):
    article = asyncio.run(run_runner(tmp_path))
    assert isinstance(article, Article)
    assert article.topic == "topic"
    assert article.content == "result"
