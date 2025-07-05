from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("dspy")

from knowledge_storm.modules.academic_rm import CrossrefRM


def test_crossref_rm_ranking():
    rm = CrossrefRM(k=2)
    items = [
        {"DOI": "1", "title": ["A"], "is-referenced-by-count": 5, "issued": {"date-parts": [[2010]]}},
        {"DOI": "2", "title": ["B"], "is-referenced-by-count": 10, "issued": {"date-parts": [[2020]]}},
    ]
    with patch.object(rm.service, "search_works", new=AsyncMock(return_value=items)):
        results = rm.forward("q")
        assert results[0]["doi"] == "2"
        assert results[1]["doi"] == "1"


def test_crossref_rm_multiple_queries():
    rm = CrossrefRM(k=0)
    with patch.object(
        rm.service,
        "search_works",
        side_effect=[AsyncMock(return_value=[{"DOI": "1"}])(), AsyncMock(return_value=[{"DOI": "2"}])()],
    ) as mock:
        results = rm.forward(["a", "b"])
        assert mock.call_count == 2
        dois = {r["doi"] for r in results}
        assert dois == {"1", "2"}


def test_crossref_rm_exclude_url():
    rm = CrossrefRM(k=5)
    items = [{"DOI": "1", "title": ["T"], "issued": {"date-parts": [[2020]]}}]
    with patch.object(rm.service, "search_works", new=AsyncMock(return_value=items)):
        results = rm.forward("q", exclude_urls=["https://doi.org/1"])
        assert results == []

