import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from knowledge_storm.services.crossref_service import CrossrefService


def test_get_metadata_by_doi():
    from knowledge_storm.services.cache_service import CacheService
    with patch.object(CacheService, "__init__", lambda self, **kwargs: None), \
         patch.object(CacheService, "get", new=AsyncMock(return_value=None)), \
         patch.object(CacheService, "set", new=AsyncMock(return_value=None)):
        service = CrossrefService()
        with patch.object(service, "_fetch_json", new=AsyncMock(return_value={"message": {"x": 1}})):
            result = asyncio.run(service.get_metadata_by_doi("10.1"))
            assert result == {"x": 1}


@pytest.mark.asyncio
async def test_validate_citation():
    from knowledge_storm.services.cache_service import CacheService
    with patch.object(CacheService, "__init__", lambda self, **kwargs: None), \
         patch.object(CacheService, "get", new=AsyncMock(return_value=None)), \
         patch.object(CacheService, "set", new=AsyncMock(return_value=None)):
        service = CrossrefService()
        with patch.object(service, "get_metadata_by_doi", new=AsyncMock(return_value={"title": "T"})):
            ok = await service.validate_citation({"doi": "10.1"})
            assert ok is True


@pytest.mark.asyncio
async def test_get_journal_metadata():
    from knowledge_storm.services.cache_service import CacheService
    with patch.object(CacheService, "__init__", lambda self, **kwargs: None), \
         patch.object(CacheService, "get", new=AsyncMock(return_value=None)), \
         patch.object(CacheService, "set", new=AsyncMock(return_value=None)):
        service = CrossrefService()
        with patch.object(service, "_fetch_json", new=AsyncMock(return_value={"message": {"journal": "J"}})):
            result = await service.get_journal_metadata("1234")
            assert result == {"journal": "J"}
