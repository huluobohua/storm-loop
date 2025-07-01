import asyncio
from unittest.mock import AsyncMock, patch

from models.agent import (
    AcademicResearcherAgent,
    CriticAgent,
    CitationVerifierAgent,
    WriterAgent,
)
from knowledge_storm.services.academic_source_service import AcademicSourceService


async def _run(coro):
    return await coro


def test_academic_researcher_agent():
    service = AcademicSourceService()
    agent = AcademicResearcherAgent("a", "Researcher", service=service)

    with patch.object(service, "search_openalex", new=AsyncMock(return_value=[{"title": "A"}])), patch.object(service, "search_crossref", new=AsyncMock(return_value=[{"title": "B"}])):
        results = asyncio.run(agent.execute_task("test"))
        assert len(results) == 2
        assert results[0]["score"] >= 0


def test_critic_agent_scoring():
    agent = CriticAgent("c", "Critic")
    result = asyncio.run(agent.execute_task("some text"))
    assert "Quality score" in result


def test_citation_verifier_agent():
    service = AcademicSourceService()
    agent = CitationVerifierAgent("v", "Verifier", service=service)
    with patch.object(service, "get_publication_metadata", new=AsyncMock(return_value={"title": "x"})):
        result = asyncio.run(agent.execute_task("10.1234/test"))
        assert result == "DOI verified"


def test_writer_agent_citation_formatting():
    agent = WriterAgent("w", "Writer")
    agent.update_state("references", [{"author": "Doe", "publication_year": 2020, "title": "Paper", "doi": "10.1"}])
    text = asyncio.run(agent.execute_task("Topic"))
    assert "Doe" in text
