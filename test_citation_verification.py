import asyncio
from unittest.mock import AsyncMock, patch

from knowledge_storm.services.citation_verification import CitationVerificationSystem
from knowledge_storm.services.academic_source_service import AcademicSourceService


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def test_verify_citation():
    service = AcademicSourceService()
    cvs = CitationVerificationSystem(service=service)
    metadata = {
        "title": "Verification of claims",
        "abstract": "This paper studies citation verification methods.",
        "publication_year": 2021,
        "cited_by_count": 5,
    }
    with patch.object(service, "get_publication_metadata", new=AsyncMock(return_value=metadata)):
        result = _run(cvs.verify_citation("verification methods", {"doi": "10.1"}))
        assert result["verified"]
        assert result["quality_metrics"]["score"] >= 5


def test_format_citation_styles():
    cvs = CitationVerificationSystem()
    source = {
        "author": "Doe",
        "title": "Research",
        "publication_year": 2020,
        "doi": "10.1",
    }
    assert "Doe" in cvs.format_citation(source, style="APA")
    assert "Doe" in cvs.format_citation(source, style="MLA")
    assert "Doe" in cvs.format_citation(source, style="Chicago")

