import pytest
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


def test_from_crossref_response_invalid_input():
    """Test that non-dict input raises TypeError."""
    with pytest.raises(TypeError, match="crossref_data must be a dictionary"):
        Paper.from_crossref_response("not a dict")
    
    with pytest.raises(TypeError, match="crossref_data must be a dictionary"):
        Paper.from_crossref_response(None)


def test_from_crossref_response_missing_fields():
    """Test handling of missing or null fields."""
    data = {"message": {}}
    paper = Paper.from_crossref_response(data)
    assert paper.doi is None
    assert paper.title == ""
    assert paper.authors is None
    assert paper.journal is None
    assert paper.year is None


def test_from_crossref_response_empty_authors():
    """Test handling of empty author list."""
    data = {
        "message": {
            "DOI": "10.1234/example",
            "title": ["Sample Paper"],
            "author": [],
        }
    }
    paper = Paper.from_crossref_response(data)
    assert paper.authors is None


def test_from_crossref_response_title_formats():
    """Test different title formats (string vs list)."""
    # String title
    data = {"message": {"title": "String Title"}}
    paper = Paper.from_crossref_response(data)
    assert paper.title == "String Title"
    
    # Empty list title
    data = {"message": {"title": []}}
    paper = Paper.from_crossref_response(data)
    assert paper.title == ""


def test_from_crossref_response_invalid_date():
    """Test handling of invalid date formats."""
    # Invalid date structure
    data = {"message": {"issued": {"invalid": "format"}}}
    paper = Paper.from_crossref_response(data)
    assert paper.year is None
    
    # Empty date parts
    data = {"message": {"issued": {"date-parts": [[]]}}}
    paper = Paper.from_crossref_response(data)
    assert paper.year is None


def test_from_crossref_response_no_message_wrapper():
    """Test response without 'message' wrapper."""
    data = {
        "DOI": "10.1234/example",
        "title": ["Direct Paper"],
        "author": [{"given": "John", "family": "Smith"}],
    }
    paper = Paper.from_crossref_response(data)
    assert paper.doi == "10.1234/example"
    assert paper.title == "Direct Paper"
    assert paper.authors == ["John Smith"]
