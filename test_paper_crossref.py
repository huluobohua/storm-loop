from knowledge_storm.models.paper import Paper


def test_from_crossref_response():
    data = {
        "message": {
            "DOI": "10.1234/example",
            "title": ["Sample Paper"],
            "author": [{"given": "Jane", "family": "Doe"}],
            "container-title": ["Journal"],
            "issued": {"date-parts": [[2021]]},
        }
    }
    paper = Paper.from_crossref_response(data)
    assert paper.doi == "10.1234/example"
    assert paper.title == "Sample Paper"
    assert paper.authors == ["Jane Doe"]
    assert paper.journal == "Journal"
    assert paper.year == 2021
