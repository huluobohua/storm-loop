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
        assert len(results) == 2
        assert results[0]["doi"] == "2"
        assert results[1]["doi"] == "1"
        # Verify complete structure
        assert "url" in results[0]
        assert "title" in results[0]
        assert "score" in results[0]
        assert results[0]["url"] == "https://doi.org/2"
