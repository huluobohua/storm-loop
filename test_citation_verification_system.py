import asyncio
from types import SimpleNamespace

from knowledge_storm.services.citation_service import CitationVerificationSystem
from knowledge_storm.services.cache_service import CacheService

class DummyConvToSection:
    def __init__(self, citation_verifier=None):
        self.citation_verifier = citation_verifier
        self.write_section = lambda **kw: SimpleNamespace(output="# Heading\nText [1]")

    def forward(self, topic, outline, section, collected_info):
        text = self.write_section().output
        if self.citation_verifier:
            self.citation_verifier.verify_section(text, collected_info)
        return SimpleNamespace(section=text)


class StormInformation:
    def __init__(self, uuid, description, snippets, title):
        self.uuid = uuid
        self.description = description
        self.snippets = snippets
        self.title = title


def test_verify_citation_and_caching():
    cache = CacheService()
    system = CitationVerificationSystem(cache=cache)
    claim = "The sky is blue"
    source = {"text": "The sky is blue and clear."}
    result1 = asyncio.run(system.verify_citation_async(claim, source))
    result2 = asyncio.run(system.verify_citation_async(claim, source))
    assert result1 == result2
    assert result1["verified"]
    assert result1["confidence"] > 0.7


def test_conv_to_section_triggers_verification(monkeypatch):
    verifier = CitationVerificationSystem(cache=CacheService())
    called = {}

    def mock_verify(section_text, info_list):
        called["v"] = True
        return []

    verifier.verify_section = mock_verify
    conv = DummyConvToSection(citation_verifier=verifier)
    info = [StormInformation("u", "d", ["Text"], "t")]
    conv.forward("topic", "", "sec", info)
    assert called.get("v")
