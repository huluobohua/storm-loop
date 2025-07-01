from knowledge_storm.services.citation_verification import CitationVerificationSystem


def test_verify_and_format():
    cvs = CitationVerificationSystem()
    claim = "AI beats humans at chess"
    source = {
        "content": "Recent studies show AI beats humans at chess with ease.",
        "cited_by_count": 10,
        "publication_year": 2024,
        "author": "Doe",
        "title": "AI Chess",
        "doi": "10.1/xyz",
    }
    result = cvs.verify_citation(claim, source)
    assert 0 <= result["confidence"] <= 1
    apa = cvs.format_citation(source, "APA")
    mla = cvs.format_citation(source, "MLA")
    chicago = cvs.format_citation(source, "Chicago")
    assert "Doe" in apa and "Doe" in mla and "Doe" in chicago
