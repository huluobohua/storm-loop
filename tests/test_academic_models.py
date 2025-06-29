"""
Tests for academic data models
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from storm_loop.models.academic_models import (
    Author, Journal, Concept, AcademicPaper, SearchQuery, 
    SearchResult, QualityMetrics, SourceType
)


class TestAuthor:
    """Test Author model"""
    
    def test_author_creation(self):
        """Test basic author creation"""
        author = Author(
            display_name="John Doe",
            given_name="John",
            family_name="Doe",
            orcid="0000-0000-0000-0000",
            affiliation="University of Example"
        )
        
        assert author.display_name == "John Doe"
        assert author.given_name == "John"
        assert author.family_name == "Doe"
        assert author.orcid == "https://orcid.org/0000-0000-0000-0000"
        assert author.affiliation == "University of Example"
    
    def test_author_orcid_validation(self):
        """Test ORCID URL validation"""
        # Test without https prefix
        author = Author(display_name="Test", orcid="0000-0000-0000-0000")
        assert author.orcid == "https://orcid.org/0000-0000-0000-0000"
        
        # Test with https prefix
        author = Author(display_name="Test", orcid="https://orcid.org/0000-0000-0000-0001")
        assert author.orcid == "https://orcid.org/0000-0000-0000-0001"


class TestJournal:
    """Test Journal model"""
    
    def test_journal_creation(self):
        """Test journal creation with all fields"""
        journal = Journal(
            name="Nature",
            issn="0028-0836",
            publisher="Springer Nature",
            impact_factor=42.778,
            h_index=150
        )
        
        assert journal.name == "Nature"
        assert journal.issn == "0028-0836"
        assert journal.publisher == "Springer Nature"
        assert journal.impact_factor == 42.778
        assert journal.h_index == 150


class TestAcademicPaper:
    """Test AcademicPaper model"""
    
    def test_paper_creation_minimal(self):
        """Test paper creation with minimal required fields"""
        paper = AcademicPaper(
            id="test_paper_1",
            title="Test Paper Title"
        )
        
        assert paper.id == "test_paper_1"
        assert paper.title == "Test Paper Title"
        assert paper.authors == []
        assert paper.concepts == []
        assert paper.keywords == []
        assert paper.external_urls == []
    
    def test_paper_creation_full(self, sample_academic_paper):
        """Test paper creation with all fields"""
        paper_data = sample_academic_paper.copy()
        
        authors = [Author(display_name=author["display_name"]) for author in paper_data["authors"]]
        journal = Journal(name=paper_data["journal"])
        concepts = [Concept(id=f"concept_{i}", display_name=concept["display_name"]) 
                   for i, concept in enumerate(paper_data["concepts"])]
        
        paper = AcademicPaper(
            id=paper_data["id"],
            title=paper_data["title"],
            doi=paper_data["doi"],
            authors=authors,
            journal=journal,
            concepts=concepts,
            publication_year=paper_data["publication_year"],
            citation_count=paper_data["citation_count"],
            abstract=paper_data["abstract"]
        )
        
        assert paper.id == paper_data["id"]
        assert paper.title == paper_data["title"]
        assert paper.doi == paper_data["doi"]
        assert len(paper.authors) == len(paper_data["authors"])
        assert paper.journal.name == paper_data["journal"]
        assert len(paper.concepts) == len(paper_data["concepts"])
        assert paper.publication_year == paper_data["publication_year"]
        assert paper.citation_count == paper_data["citation_count"]
    
    def test_paper_publication_year_validation(self):
        """Test publication year validation"""
        # Valid year
        paper = AcademicPaper(id="test", title="Test", publication_year=2023)
        assert paper.publication_year == 2023
        
        # Invalid year (too old)
        with pytest.raises(ValidationError):
            AcademicPaper(id="test", title="Test", publication_year=1200)
        
        # Invalid year (too future)
        with pytest.raises(ValidationError):
            AcademicPaper(id="test", title="Test", publication_year=2030)
    
    def test_paper_citation_count_validation(self):
        """Test citation count validation"""
        # Valid count
        paper = AcademicPaper(id="test", title="Test", citation_count=100)
        assert paper.citation_count == 100
        
        # Invalid count (negative)
        with pytest.raises(ValidationError):
            AcademicPaper(id="test", title="Test", citation_count=-1)
    
    def test_paper_quality_score_validation(self):
        """Test quality score validation"""
        # Valid score
        paper = AcademicPaper(id="test", title="Test", quality_score=0.85)
        assert paper.quality_score == 0.85
        
        # Invalid score (too high)
        with pytest.raises(ValidationError):
            AcademicPaper(id="test", title="Test", quality_score=1.5)
        
        # Invalid score (negative)
        with pytest.raises(ValidationError):
            AcademicPaper(id="test", title="Test", quality_score=-0.1)


class TestSearchQuery:
    """Test SearchQuery model"""
    
    def test_search_query_creation(self):
        """Test search query creation"""
        query = SearchQuery(
            query="machine learning",
            limit=20,
            offset=10,
            filters={"publication_year": [2020, 2023]},
            sort_by="relevance"
        )
        
        assert query.query == "machine learning"
        assert query.limit == 20
        assert query.offset == 10
        assert query.filters == {"publication_year": [2020, 2023]}
        assert query.sort_by == "relevance"
    
    def test_search_query_validation(self):
        """Test search query validation"""
        # Valid limit
        query = SearchQuery(query="test", limit=100)
        assert query.limit == 100
        
        # Invalid limit (too high)
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=500)
        
        # Invalid limit (too low)
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=0)
        
        # Invalid offset
        with pytest.raises(ValidationError):
            SearchQuery(query="test", offset=-1)


class TestQualityMetrics:
    """Test QualityMetrics model"""
    
    def test_quality_metrics_creation(self):
        """Test quality metrics creation"""
        metrics = QualityMetrics(
            citation_score=0.8,
            recency_score=0.6,
            venue_score=0.9,
            author_score=0.7,
            content_score=0.5,
            open_access_bonus=0.1,
            is_predatory=False
        )
        
        assert metrics.citation_score == 0.8
        assert metrics.recency_score == 0.6
        assert metrics.venue_score == 0.9
        assert metrics.author_score == 0.7
        assert metrics.content_score == 0.5
        assert metrics.open_access_bonus == 0.1
        assert metrics.is_predatory is False
    
    def test_overall_score_calculation(self):
        """Test overall score calculation"""
        metrics = QualityMetrics(
            citation_score=0.8,
            recency_score=0.6,
            venue_score=0.9,
            author_score=0.7,
            content_score=0.5,
            open_access_bonus=0.1,
            is_predatory=False,
            is_retracted=False
        )
        
        overall_score = metrics.calculate_overall_score()
        
        # Check that score is calculated and within valid range
        assert 0.0 <= overall_score <= 1.0
        assert metrics.overall_score == overall_score
        
        # Verify it's a weighted combination
        expected = (0.8 * 0.3 + 0.9 * 0.25 + 0.6 * 0.2 + 0.7 * 0.15 + 0.5 * 0.1) + (0.1 * 0.05)
        assert abs(overall_score - expected) < 0.01
    
    def test_predatory_penalty(self):
        """Test predatory publication penalty"""
        metrics = QualityMetrics(
            citation_score=0.8,
            venue_score=0.9,
            is_predatory=True
        )
        
        overall_score = metrics.calculate_overall_score()
        
        # Should be heavily penalized
        assert overall_score < 0.2
    
    def test_retraction_penalty(self):
        """Test retracted paper penalty"""
        metrics = QualityMetrics(
            citation_score=0.8,
            venue_score=0.9,
            is_retracted=True
        )
        
        overall_score = metrics.calculate_overall_score()
        
        # Should be zero for retracted papers
        assert overall_score == 0.0


class TestSearchResult:
    """Test SearchResult model"""
    
    def test_search_result_creation(self):
        """Test search result creation"""
        query = SearchQuery(query="test", limit=10)
        papers = [
            AcademicPaper(id="paper1", title="Paper 1"),
            AcademicPaper(id="paper2", title="Paper 2")
        ]
        
        result = SearchResult(
            query=query,
            papers=papers,
            total_count=2,
            search_time_ms=150.5,
            source="test_source"
        )
        
        assert result.query == query
        assert len(result.papers) == 2
        assert result.total_count == 2
        assert result.search_time_ms == 150.5
        assert result.source == "test_source"