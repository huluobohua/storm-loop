"""
Unit tests for PRISMA core data models.
"""

import pytest
from datetime import datetime
from knowledge_storm.modules.prisma.core import (
    Paper, SearchStrategy, ExtractionTemplate, ScreeningResult
)


class TestPaper:
    """Test suite for Paper data model."""
    
    def test_paper_creation_with_required_fields(self):
        """Test creating a Paper with only required fields."""
        paper = Paper(
            id="paper_123",
            title="Test Paper",
            authors=["Author One", "Author Two"],
            abstract="This is a test abstract.",
            year=2023,
            journal="Test Journal"
        )
        
        assert paper.id == "paper_123"
        assert paper.title == "Test Paper"
        assert paper.authors == ["Author One", "Author Two"]
        assert paper.abstract == "This is a test abstract."
        assert paper.year == 2023
        assert paper.journal == "Test Journal"
        assert paper.doi is None
        assert paper.url is None
        assert paper.keywords == []
        assert paper.study_type is None
        assert paper.sample_size is None
        assert paper.screening_decision is None
        assert paper.exclusion_reason is None
        assert paper.confidence_score == 0.0
    
    def test_paper_creation_with_all_fields(self):
        """Test creating a Paper with all fields."""
        paper = Paper(
            id="paper_456",
            title="Complete Test Paper",
            authors=["Author One", "Author Two"],
            abstract="This is a comprehensive test abstract.",
            year=2023,
            journal="Test Journal",
            doi="10.1234/test.doi",
            url="https://example.com/paper",
            keywords=["diabetes", "insulin"],
            study_type="randomized_controlled_trial",
            sample_size=100,
            screening_decision="include",
            exclusion_reason=None,
            confidence_score=0.95
        )
        
        assert paper.id == "paper_456"
        assert paper.title == "Complete Test Paper"
        assert paper.authors == ["Author One", "Author Two"]
        assert paper.abstract == "This is a comprehensive test abstract."
        assert paper.year == 2023
        assert paper.journal == "Test Journal"
        assert paper.doi == "10.1234/test.doi"
        assert paper.url == "https://example.com/paper"
        assert paper.keywords == ["diabetes", "insulin"]
        assert paper.study_type == "randomized_controlled_trial"
        assert paper.sample_size == 100
        assert paper.screening_decision == "include"
        assert paper.exclusion_reason is None
        assert paper.confidence_score == 0.95


class TestSearchStrategy:
    """Test suite for SearchStrategy data model."""
    
    def test_search_strategy_creation(self):
        """Test creating a SearchStrategy."""
        pico_elements = {
            "population": ["adults", "diabetes"],
            "intervention": ["insulin therapy"],
            "comparison": ["placebo"],
            "outcome": ["blood glucose"]
        }
        search_queries = {
            "pubmed": "diabetes AND insulin",
            "embase": "diabetes AND insulin resistance"
        }
        inclusion_criteria = ["Adults aged 18+", "Diabetes diagnosis"]
        exclusion_criteria = ["Animal studies", "Review articles"]
        
        strategy = SearchStrategy(
            research_question="What is the effect of insulin therapy on diabetes?",
            pico_elements=pico_elements,
            search_queries=search_queries,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria
        )
        
        assert strategy.research_question == "What is the effect of insulin therapy on diabetes?"
        assert strategy.pico_elements == pico_elements
        assert strategy.search_queries == search_queries
        assert strategy.inclusion_criteria == inclusion_criteria
        assert strategy.exclusion_criteria == exclusion_criteria
        assert strategy.date_range is None
        assert strategy.languages == ["English"]
    
    def test_search_strategy_with_date_range(self):
        """Test SearchStrategy with date range."""
        strategy = SearchStrategy(
            research_question="Test question",
            pico_elements={"population": ["adults"]},
            search_queries={"pubmed": "test query"},
            inclusion_criteria=["Test inclusion"],
            exclusion_criteria=["Test exclusion"],
            date_range=(2020, 2023),
            languages=["English", "Spanish"]
        )
        
        assert strategy.date_range == (2020, 2023)
        assert strategy.languages == ["English", "Spanish"]


class TestExtractionTemplate:
    """Test suite for ExtractionTemplate data model."""
    
    def test_extraction_template_creation(self):
        """Test ExtractionTemplate creation."""
        fields = {
            "sample_size": {"type": "int", "description": "Number of participants", "required": True},
            "intervention": {"type": "str", "description": "Treatment intervention", "required": True}
        }
        template = ExtractionTemplate(
            fields=fields,
            study_characteristics=["design", "duration"],
            outcome_measures=["primary_outcome", "secondary_outcome"],
            quality_indicators=["bias_risk", "completeness"]
        )
        
        assert template.fields == fields
        assert template.study_characteristics == ["design", "duration"]
        assert template.outcome_measures == ["primary_outcome", "secondary_outcome"]
        assert template.quality_indicators == ["bias_risk", "completeness"]


class TestScreeningResult:
    """Test suite for ScreeningResult data model."""
    
    def test_screening_result_included(self):
        """Test ScreeningResult for included paper."""
        result = ScreeningResult(
            decision="include",
            confidence=0.95,
            reason="Meets all inclusion criteria"
        )
        
        assert result.decision == "include"
        assert result.confidence == 0.95
        assert result.reason == "Meets all inclusion criteria"
        assert isinstance(result.timestamp, datetime)
    
    def test_screening_result_excluded(self):
        """Test ScreeningResult for excluded paper."""
        result = ScreeningResult(
            decision="exclude",
            confidence=0.85,
            reason="Animal study - violates inclusion criteria"
        )
        
        assert result.decision == "exclude"
        assert result.confidence == 0.85
        assert result.reason == "Animal study - violates inclusion criteria"
    
    def test_screening_result_maybe(self):
        """Test ScreeningResult for maybe decision."""
        result = ScreeningResult(
            decision="maybe",
            confidence=0.65,
            reason="Unclear methodology - needs full text review"
        )
        
        assert result.decision == "maybe"
        assert result.confidence == 0.65
        assert result.reason == "Unclear methodology - needs full text review"
    
    def test_screening_result_with_custom_timestamp(self):
        """Test ScreeningResult with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        result = ScreeningResult(
            decision="include",
            confidence=0.8,
            reason="Test reason",
            timestamp=custom_time
        )
        
        assert result.timestamp == custom_time


if __name__ == "__main__":
    pytest.main([__file__])
