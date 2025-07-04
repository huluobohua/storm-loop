import asyncio
from unittest.mock import AsyncMock, patch

from knowledge_storm.services.crossref_service import CrossrefService


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
