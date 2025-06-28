"""
Pytest configuration and fixtures for STORM-Loop tests
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import MagicMock
from storm_loop.config import STORMLoopConfig, OperationMode


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Create a test configuration"""
    return STORMLoopConfig(
        mode=OperationMode.HYBRID,
        redis_host="localhost",
        redis_port=6379,
        redis_db=1,  # Use different DB for tests
        database_url="sqlite:///test_storm_loop.db",
        log_level="DEBUG",
        enable_monitoring=False,
        max_concurrent_requests=5,
        request_timeout=10,
        cache_ttl=300,
    )


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    return mock_redis


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_academic_paper():
    """Sample academic paper metadata for testing"""
    return {
        "id": "https://openalex.org/W2741809807",
        "title": "Attention Is All You Need",
        "authors": [
            {"display_name": "Ashish Vaswani"},
            {"display_name": "Noam Shazeer"},
            {"display_name": "Niki Parmar"},
        ],
        "publication_year": 2017,
        "journal": "Advances in Neural Information Processing Systems",
        "doi": "https://doi.org/10.48550/arXiv.1706.03762",
        "citation_count": 50000,
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        "concepts": [
            {"display_name": "Artificial Intelligence"},
            {"display_name": "Machine Learning"},
            {"display_name": "Natural Language Processing"},
        ]
    }


@pytest.fixture
def sample_crossref_metadata():
    """Sample Crossref metadata for testing"""
    return {
        "DOI": "10.48550/arXiv.1706.03762",
        "URL": "http://dx.doi.org/10.48550/arXiv.1706.03762",
        "title": ["Attention Is All You Need"],
        "author": [
            {"given": "Ashish", "family": "Vaswani"},
            {"given": "Noam", "family": "Shazeer"},
        ],
        "published-print": {"date-parts": [[2017]]},
        "container-title": ["Advances in Neural Information Processing Systems"],
        "is-referenced-by-count": 50000,
    }