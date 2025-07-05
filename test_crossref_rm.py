import pytest

pytest.importorskip("dspy")
from knowledge_storm.rm import CrossrefRM

class DummyResp:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data


def test_crossref_rm_basic(monkeypatch):
    sample = {
        "message": {
            "items": [
                {"URL": "http://example.com", "title": ["Sample"], "abstract": "A"}
            ]
        }
    }
    def fake_get(url, params=None):
        return DummyResp(sample)
    monkeypatch.setattr("knowledge_storm.rm.requests.get", fake_get)
    rm = CrossrefRM(k=1)
    results = rm.forward("test")
    assert results == [{"url": "http://example.com", "title": "Sample", "description": "A", "snippets": ["A"]}]

