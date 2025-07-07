import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from knowledge_storm.workflows.academic import AcademicWorkflowRunner
from knowledge_storm.hybrid_engine import Article


async def run_runner(tmp_path, create_output_file=True):
    runner = AsyncMock()
    runner.args = SimpleNamespace(output_dir=str(tmp_path))
    runner.post_run = Mock()
    
    if create_output_file:
        article_dir = tmp_path / "topic"
        article_dir.mkdir()
        (article_dir / "storm_gen_article_polished.txt").write_text("result")
    
    awr = AcademicWorkflowRunner(runner)
    result = await awr.run_academic_workflow("topic")
    runner.run.assert_awaited_once()
    runner.post_run.assert_called_once()
    return result


def test_academic_workflow_runner(tmp_path):
    """Test the academic workflow runner with existing output file."""
    article = asyncio.run(run_runner(tmp_path, create_output_file=True))
    assert isinstance(article, Article)
    assert article.topic == "topic"
    assert article.content == "result"
    assert article.metadata == {"type": "academic"}


def test_academic_workflow_runner_missing_file(tmp_path):
    """Test the academic workflow runner when output file doesn't exist."""
    article = asyncio.run(run_runner(tmp_path, create_output_file=False))
    assert isinstance(article, Article)
    assert article.topic == "topic"
    assert article.content == ""  # Should return empty string when file doesn't exist
    assert article.metadata == {"type": "academic"}


def test_academic_workflow_runner_special_characters(tmp_path):
    """Test the academic workflow runner with special characters in topic."""
    runner = AsyncMock()
    runner.args = SimpleNamespace(output_dir=str(tmp_path))
    runner.post_run = Mock()
    
    # Test topic with special characters
    topic = "Computer Science / Algorithms & Data Structures"
    expected_safe_topic = "Computer_Science_Algorithms_Data_Structures"
    
    article_dir = tmp_path / expected_safe_topic
    article_dir.mkdir()
    (article_dir / "storm_gen_article_polished.txt").write_text("special content")
    
    awr = AcademicWorkflowRunner(runner)
    result = asyncio.run(awr.run_academic_workflow(topic))
    
    assert isinstance(result, Article)
    assert result.topic == topic  # Original topic preserved
    assert result.content == "special content"
    assert result.metadata == {"type": "academic"}
    
    # Verify the path sanitization worked
    assert awr._get_article_path(topic) == str(article_dir / "storm_gen_article_polished.txt")


def test_slugify_function():
    """Test the slugify function for path sanitization."""
    from knowledge_storm.workflows.academic import slugify
    
    # Test basic cases
    assert slugify("simple") == "simple"
    assert slugify("with spaces") == "with_spaces"
    assert slugify("with-hyphens") == "with_hyphens"
    
    # Test special characters
    assert slugify("Computer Science / Algorithms") == "Computer_Science_Algorithms"
    assert slugify("file/with/slashes") == "filewithslashes"
    assert slugify("../../malicious") == "malicious"
    assert slugify("special!@#$%^&*()chars") == "specialchars"
    
    # Test edge cases
    assert slugify("") == "unnamed"
    assert slugify("   ") == "unnamed"
    assert slugify("___") == "unnamed"
    assert slugify("--multiple--separators--") == "multiple_separators"