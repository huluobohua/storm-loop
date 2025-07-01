import asyncio
from unittest.mock import AsyncMock, patch

from knowledge_storm.services.academic_source_service import \
    AcademicSourceService
from knowledge_storm.services.cache_service import CacheService
from models.agent import (AcademicResearcherAgent, AcademicRetrieverAgent,
                          CitationVerifierAgent, CriticAgent, WriterAgent)


async def _run(coro):
    return await coro


def test_academic_researcher_agent():
    service = AcademicSourceService()
    agent = AcademicResearcherAgent("a", "Researcher", service=service)

    with patch.object(
        service, "search_openalex", new=AsyncMock(return_value=[{"title": "A"}])
    ), patch.object(
        service, "search_crossref", new=AsyncMock(return_value=[{"title": "B"}])
    ):
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
    with patch.object(
        service, "get_publication_metadata", new=AsyncMock(return_value={"title": "x"})
    ):
        result = asyncio.run(agent.execute_task("10.1234/test"))
        assert result == "DOI verified"


def test_writer_agent_citation_formatting():
    agent = WriterAgent("w", "Writer")
    agent.update_state(
        "references",
        [{"author": "Doe", "publication_year": 2020, "title": "Paper", "doi": "10.1"}],
    )
    text = asyncio.run(agent.execute_task("Topic"))
    assert "Doe" in text


def test_cache_service():
    cache = CacheService(ttl=10)
    asyncio.run(cache.set("k", {"v": 1}))
    result = asyncio.run(cache.get("k"))
    assert result == {"v": 1}


def test_academic_retriever_agent_with_fallback():
    service = AcademicSourceService(cache=CacheService())

    class DummyRM:
        def forward(self, q):
            return [{"title": "F"}]

    agent = AcademicRetrieverAgent(
        "r", "Retriever", service=service, fallback_rm=DummyRM()
    )
    with patch.object(service, "search_combined", new=AsyncMock(return_value=[])):
        results = asyncio.run(agent.execute_task("topic"))
        assert results == [{"title": "F"}]


def test_academic_source_service_caching():
    cache = CacheService()
    service = AcademicSourceService(cache=cache)

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
    mock_resp.json.return_value = {"results": [1]}
    mock_session = MockSession()
    from types import SimpleNamespace

    aiohttp_mock = SimpleNamespace(
        ClientSession=lambda timeout=None: mock_session,
        ClientTimeout=lambda total=None: None,
    )
    with patch(
        "knowledge_storm.services.utils.aiohttp",
        aiohttp_mock,
    ):
        asyncio.run(service.search_openalex("q"))
        asyncio.run(service.search_openalex("q"))
        assert mock_session.get_call_count == 1


def test_citation_verification_system():
    from knowledge_storm.services.citation_verification_system import \
        CitationVerificationSystem

    cvs = CitationVerificationSystem()
    claim = "The cats sit on the mats in the sun."
    source = {
        "text": "The cats sit on the mats in the sun.",
        "author": "Smith",
        "publication_year": 2021,
        "title": "Feline Behavior",
        "doi": "10.1/feline",
    }
    result = cvs.verify_citation(claim, source)
    assert result["verified"] is True
    citation = cvs.format_citation(source, style="APA")
    assert "Smith" in citation
