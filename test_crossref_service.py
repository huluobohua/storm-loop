import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from knowledge_storm.services.cache_service import CacheService

from knowledge_storm.services.crossref_service import CrossrefService, CrossrefConfig


async def _run(coro):
    return await coro


def test_get_metadata_by_doi():
    service = CrossrefService()
    with patch.object(service, "_fetch_json", new=AsyncMock(return_value={"message": {"x": 1}})):
        result = asyncio.run(service.get_metadata_by_doi("10.1"))
        assert result == {"x": 1}


def test_validate_citation():
    service = CrossrefService()
    with patch.object(service, "get_metadata_by_doi", new=AsyncMock(return_value={"title": "T"})):
        ok = asyncio.run(service.validate_citation({"doi": "10.1"}))
        assert ok is True


def test_get_journal_metadata():
    service = CrossrefService()
    with patch.object(service, "_fetch_json", new=AsyncMock(return_value={"message": {"journal": "J"}})):
        result = asyncio.run(service.get_journal_metadata("1234"))
        assert result == {"journal": "J"}


def test_crossref_service_caching():
    cache = CacheService()
    service = CrossrefService(CrossrefConfig(cache=cache))

    class MockContext:
        async def __aenter__(self):
            return mock_resp

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class MockSession:
        def __init__(self):
            self.get_call_count = 0

        def get(self, *args, **kwargs):
            self.get_call_count += 1
            return MockContext()

    mock_resp = AsyncMock()
    mock_resp.json.return_value = {"message": {"items": [1]}}
    mock_session = MockSession()
    aiohttp_mock = SimpleNamespace(
        ClientSession=lambda timeout=None: mock_session,
        ClientTimeout=lambda total=None: None,
    )

    with patch("knowledge_storm.services.utils.aiohttp", aiohttp_mock):
        asyncio.run(service.search_works("q"))
        asyncio.run(service.search_works("q"))
        assert mock_session.get_call_count == 1


def test_crossref_service_rate_limit_called():
    service = CrossrefService()
    wait_mock = AsyncMock()

    class DummyResp(str):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    with patch.object(service.rate_limiter, "wait", wait_mock), patch.object(
        service.fetcher.conn_manager, "get_session", AsyncMock(side_effect=RuntimeError())
    ), patch(
        "knowledge_storm.services.crossref_service.request.urlopen",
        lambda *args, **kwargs: DummyResp("{}"),
    ):
        asyncio.run(service.search_works("q"))
        assert wait_mock.await_count == 1


def test_crossref_service_circuit_breaker():
    service = CrossrefService()
    with patch.object(service.breaker, "should_allow_request", return_value=False):
        with pytest.raises(RuntimeError):
            asyncio.run(service.search_works("q"))

