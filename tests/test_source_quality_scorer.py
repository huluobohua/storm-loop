"""
Tests for source quality scoring system
"""
import pytest
from datetime import datetime

from storm_loop.models.academic_models import AcademicPaper, Author, Journal, SourceType
from storm_loop.services.source_quality_scorer import SourceQualityScorer


class TestSourceQualityScorer:
    """Test SourceQualityScorer functionality"""
    
    @pytest.fixture
    def scorer(self):
        """Fixture for SourceQualityScorer instance"""
        return SourceQualityScorer()
    
    @pytest.fixture
    def high_quality_paper(self):
        """Fixture for a high-quality paper"""
        return AcademicPaper(
            id="high_quality_1",
            title="A Comprehensive Study of Machine Learning Applications in Healthcare",
            doi="10.1038/s41586-021-03819-2",
            authors=[
                Author(display_name="Dr. Jane Smith", affiliation="Harvard Medical School", orcid="0000-0000-0000-0001"),
                Author(display_name="Dr. John Doe", affiliation="MIT", orcid="0000-0000-0000-0002"),
                Author(display_name="Dr. Alice Johnson", affiliation="Stanford University")
            ],
            journal=Journal(
                name="Nature",
                publisher="Springer Nature",
                impact_factor=42.778,
                h_index=150
            ),
            publication_year=2023,
            citation_count=150,
            referenced_works_count=75,
            abstract="This comprehensive study examines the applications of machine learning in healthcare, providing novel insights into diagnostic accuracy improvements and treatment optimization strategies.",
            is_open_access=True,
            source_type=SourceType.JOURNAL_ARTICLE
        )
    
    @pytest.fixture
    def low_quality_paper(self):
        """Fixture for a low-quality paper"""
        return AcademicPaper(
            id="low_quality_1",
            title="Study of things",
            authors=[],
            journal=Journal(
                name="International Journal of Research",
                publisher="Random Publisher"
            ),
            publication_year=1995,
            citation_count=2,
            referenced_works_count=5,
            abstract="Short abstract.",
            is_open_access=False
        )
    
    @pytest.fixture
    def predatory_paper(self):
        """Fixture for a predatory publication"""
        return AcademicPaper(
            id="predatory_1",
            title="Revolutionary Findings in Science",
            journal=Journal(
                name="International Journal of Advanced Research in Science",
                publisher="OMICS Publishing"
            ),
            publication_year=2023,
            citation_count=0
        )
    
    def test_score_high_quality_paper(self, scorer, high_quality_paper):
        """Test scoring of a high-quality paper"""
        metrics = scorer.score_paper(high_quality_paper)
        
        assert metrics.overall_score > 0.7
        assert metrics.citation_score > 0.5
        assert metrics.venue_score > 0.7
        assert metrics.author_score > 0.6
        assert metrics.recency_score > 0.8
        assert metrics.open_access_bonus > 0.0
        assert not metrics.is_predatory
        assert not metrics.is_retracted
    
    def test_score_low_quality_paper(self, scorer, low_quality_paper):
        """Test scoring of a low-quality paper"""
        metrics = scorer.score_paper(low_quality_paper)
        
        assert metrics.overall_score < 0.6
        assert metrics.citation_score < 0.3
        assert metrics.recency_score < 0.3  # Old paper
        assert metrics.author_score < 0.5   # No authors
    
    def test_score_predatory_paper(self, scorer, predatory_paper):
        """Test scoring of a predatory publication"""
        metrics = scorer.score_paper(predatory_paper)
        
        assert metrics.is_predatory
        assert metrics.overall_score < 0.2  # Heavy penalty
    
    def test_citation_score_calculation(self, scorer):
        """Test citation score calculation"""
        # Recent paper with good citations
        paper = AcademicPaper(
            id="test1",
            title="Test",
            publication_year=2023,
            citation_count=50
        )
        score = scorer._calculate_citation_score(paper)
        assert score > 0.3
        
        # Old paper with many citations
        paper = AcademicPaper(
            id="test2",
            title="Test",
            publication_year=2000,
            citation_count=1000
        )
        score = scorer._calculate_citation_score(paper)
        assert score > 0.4
        
        # No citations
        paper = AcademicPaper(
            id="test3",
            title="Test",
            publication_year=2023,
            citation_count=0
        )
        score = scorer._calculate_citation_score(paper)
        assert score == 0.0
    
    def test_recency_score_calculation(self, scorer):
        """Test recency score calculation"""
        current_year = datetime.now().year
        
        # Very recent paper
        paper = AcademicPaper(
            id="test1",
            title="Test",
            publication_year=current_year
        )
        score = scorer._calculate_recency_score(paper)
        assert score > 0.9
        
        # 5-year-old paper
        paper = AcademicPaper(
            id="test2",
            title="Test",
            publication_year=current_year - 5
        )
        score = scorer._calculate_recency_score(paper)
        assert 0.3 < score < 0.7
        
        # Very old paper
        paper = AcademicPaper(
            id="test3",
            title="Test",
            publication_year=current_year - 20
        )
        score = scorer._calculate_recency_score(paper)
        assert score < 0.2
        
        # Future date (suspicious)
        paper = AcademicPaper(
            id="test4",
            title="Test",
            publication_year=current_year + 1
        )
        score = scorer._calculate_recency_score(paper)
        assert score == 0.2
    
    def test_venue_score_calculation(self, scorer):
        """Test venue quality score calculation"""
        # High-quality venue
        paper = AcademicPaper(
            id="test1",
            title="Test",
            journal=Journal(
                name="Nature",
                publisher="Springer Nature",
                impact_factor=42.0,
                h_index=150
            )
        )
        score = scorer._calculate_venue_score(paper)
        assert score > 0.8
        
        # Unknown venue
        paper = AcademicPaper(
            id="test2",
            title="Test",
            journal=None
        )
        score = scorer._calculate_venue_score(paper)
        assert score == 0.3
        
        # Predatory venue
        paper = AcademicPaper(
            id="test3",
            title="Test",
            journal=Journal(
                name="International Journal of Advanced Research",
                publisher="OMICS"
            )
        )
        score = scorer._calculate_venue_score(paper)
        assert score < 0.2
    
    def test_author_score_calculation(self, scorer):
        """Test author reputation score calculation"""
        # Good author profile
        authors = [
            Author(display_name="Dr. A", affiliation="MIT", orcid="0000-0000-0000-0001"),
            Author(display_name="Dr. B", affiliation="Stanford", orcid="0000-0000-0000-0002"),
            Author(display_name="Dr. C", affiliation="Harvard")
        ]
        paper = AcademicPaper(id="test1", title="Test", authors=authors)
        score = scorer._calculate_author_score(paper)
        assert score > 0.7
        
        # No authors
        paper = AcademicPaper(id="test2", title="Test", authors=[])
        score = scorer._calculate_author_score(paper)
        assert score == 0.2
        
        # Too many authors (might indicate less individual contribution)
        authors = [Author(display_name=f"Author {i}") for i in range(50)]
        paper = AcademicPaper(id="test3", title="Test", authors=authors)
        score = scorer._calculate_author_score(paper)
        assert score < 0.5
    
    def test_content_score_calculation(self, scorer):
        """Test content quality score calculation"""
        # High-quality content indicators
        paper = AcademicPaper(
            id="test1",
            title="A Comprehensive Analysis of Deep Learning Architectures for Natural Language Processing: Methodological Innovations and Performance Evaluation",
            abstract="This study presents a comprehensive analysis of various deep learning architectures applied to natural language processing tasks. We evaluate the performance of transformer-based models, recurrent neural networks, and convolutional neural networks across multiple benchmarks. Our findings reveal significant improvements in accuracy and computational efficiency through novel architectural modifications.",
            doi="10.1038/example",
            referenced_works_count=45
        )
        score = scorer._calculate_content_score(paper)
        assert score > 0.7
        
        # Minimal content
        paper = AcademicPaper(
            id="test2",
            title="Study",
            abstract="Short.",
            referenced_works_count=1
        )
        score = scorer._calculate_content_score(paper)
        assert score < 0.6
    
    def test_predatory_detection(self, scorer):
        """Test predatory publication detection"""
        # Known predatory indicators
        assert scorer._is_predatory_venue("international journal of advanced research", "omics")
        assert scorer._is_predatory_venue("waset conference", "waset")
        assert scorer._is_predatory_venue("global journal of research", "hindawi")
        
        # Legitimate venues
        assert not scorer._is_predatory_venue("nature", "springer nature")
        assert not scorer._is_predatory_venue("ieee transactions", "ieee")
    
    def test_retraction_detection(self, scorer):
        """Test retraction detection"""
        # Retracted paper
        paper = AcademicPaper(
            id="test1",
            title="RETRACTED: Study of Machine Learning"
        )
        assert scorer._is_retracted(paper)
        
        # Normal paper
        paper = AcademicPaper(
            id="test2",
            title="Study of Machine Learning"
        )
        assert not scorer._is_retracted(paper)
    
    def test_peer_review_detection(self, scorer):
        """Test peer review status detection"""
        # Journal article (typically peer-reviewed)
        paper = AcademicPaper(
            id="test1",
            title="Test",
            journal=Journal(name="Journal of Machine Learning"),
            source_type=SourceType.JOURNAL_ARTICLE
        )
        assert scorer._has_peer_review(paper) is True
        
        # Preprint (typically not peer-reviewed)
        paper = AcademicPaper(
            id="test2",
            title="Test",
            journal=Journal(name="arXiv"),
            source_type=SourceType.PREPRINT
        )
        assert scorer._has_peer_review(paper) is False
    
    def test_multiple_papers_scoring(self, scorer, high_quality_paper, low_quality_paper):
        """Test scoring multiple papers"""
        papers = [high_quality_paper, low_quality_paper]
        results = scorer.score_multiple_papers(papers)
        
        assert len(results) == 2
        assert high_quality_paper.id in results
        assert low_quality_paper.id in results
        
        # High quality paper should score better
        assert results[high_quality_paper.id].overall_score > results[low_quality_paper.id].overall_score
    
    def test_paper_ranking(self, scorer, high_quality_paper, low_quality_paper):
        """Test paper ranking by quality"""
        papers = [low_quality_paper, high_quality_paper]  # Intentionally wrong order
        ranked_papers = scorer.rank_papers_by_quality(papers)
        
        assert len(ranked_papers) == 2
        # Should be reordered by quality (high quality first)
        assert ranked_papers[0][0].id == high_quality_paper.id
        assert ranked_papers[1][0].id == low_quality_paper.id
    
    def test_quality_threshold_filtering(self, scorer, high_quality_paper, low_quality_paper):
        """Test filtering papers by quality threshold"""
        papers = [high_quality_paper, low_quality_paper]
        
        # High threshold - should only return high quality paper
        filtered = scorer.filter_by_quality_threshold(papers, threshold=0.7)
        assert len(filtered) == 1
        assert filtered[0].id == high_quality_paper.id
        
        # Low threshold - should return both
        filtered = scorer.filter_by_quality_threshold(papers, threshold=0.3)
        assert len(filtered) == 2