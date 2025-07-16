"""
Unit tests for PRISMA screening functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from knowledge_storm.modules.prisma.screening import ScreeningAssistant
from knowledge_storm.modules.prisma.core import Paper, SearchStrategy, ScreeningResult


class TestScreeningAssistant:
    """Test suite for ScreeningAssistant."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_citation_verifier = MagicMock()
        self.mock_citation_verifier.verify_citation_async = AsyncMock(
            return_value={'verified': True, 'confidence': 0.8}
        )
        
        self.screening_assistant = ScreeningAssistant(
            citation_verifier=self.mock_citation_verifier
        )
    
    def create_test_paper(self, paper_id="test_paper_1", title="Test Paper", 
                         abstract="Test abstract", study_type=None):
        """Helper method to create test papers."""
        return Paper(
            id=paper_id,
            title=title,
            abstract=abstract,
            authors=["Test Author"],
            year=2023,
            journal="Test Journal",
            study_type=study_type
        )
    
    def create_test_search_strategy(self):
        """Helper method to create test search strategy."""
        return SearchStrategy(
            research_question="Test research question",
            pico_elements={
                'population': ['adults'],
                'intervention': ['test intervention'],
                'outcome': ['test outcome']
            },
            search_queries={'pubmed': 'test query'},
            inclusion_criteria=['Adults only', 'Randomized controlled trials'],
            exclusion_criteria=['Animal studies', 'Case reports']
        )
    
    @pytest.mark.asyncio
    async def test_screen_papers_basic(self):
        """Test basic paper screening functionality."""
        papers = [
            self.create_test_paper("paper_1", "RCT of intervention X", "Randomized controlled trial of intervention X in adults"),
            self.create_test_paper("paper_2", "Animal study of drug Y", "Study of drug Y in laboratory mice"),
            self.create_test_paper("paper_3", "Case report of patient Z", "Single case report of patient Z")
        ]
        
        search_strategy = self.create_test_search_strategy()
        
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert isinstance(results, list)
        assert len(results) == 3
        
        for result in results:
            assert isinstance(result, ScreeningResult)
            assert result.decision in ['include', 'exclude', 'maybe']
            assert 0.0 <= result.confidence <= 1.0
            assert isinstance(result.reason, str)
    
    @pytest.mark.asyncio
    async def test_screen_papers_rct_inclusion(self):
        """Test that RCTs are typically included."""
        papers = [
            self.create_test_paper(
                "rct_paper",
                "Randomized controlled trial of intervention X in adults",
                "This randomized controlled trial evaluated the effectiveness of intervention X in 200 adult participants",
                study_type="randomized_controlled_trial"
            )
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        result = results[0]
        
        # RCT should typically be included with high confidence
        assert result.decision == "include"
        assert result.confidence >= 0.7
        assert "randomized" in result.reason.lower() or "rct" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_screen_papers_animal_study_exclusion(self):
        """Test that animal studies are excluded."""
        papers = [
            self.create_test_paper(
                "animal_paper",
                "Effects of drug X in laboratory mice",
                "This study evaluated the effects of drug X in 50 laboratory mice over 12 weeks"
            )
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        result = results[0]
        
        # Animal study should be excluded with high confidence
        assert result.decision == "exclude"
        assert result.confidence >= 0.8
        assert "animal" in result.reason.lower() or "mice" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_screen_papers_case_report_exclusion(self):
        """Test that case reports are excluded."""
        papers = [
            self.create_test_paper(
                "case_report",
                "Case report: Unusual presentation of disease Y",
                "We report a case of a 45-year-old patient with unusual presentation of disease Y"
            )
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        result = results[0]
        
        # Case report should be excluded
        assert result.decision == "exclude"
        assert result.confidence >= 0.7
        assert "case report" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_screen_papers_review_exclusion(self):
        """Test that systematic reviews are excluded."""
        papers = [
            self.create_test_paper(
                "review_paper",
                "Systematic review of interventions for condition Z",
                "This systematic review and meta-analysis examined interventions for condition Z"
            )
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        result = results[0]
        
        # Review should be excluded
        assert result.decision == "exclude"
        assert result.confidence >= 0.7
        assert "review" in result.reason.lower() or "meta-analysis" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_screen_papers_mixed_decisions(self):
        """Test screening with mixed inclusion/exclusion decisions."""
        papers = [
            self.create_test_paper("good_rct", "RCT of therapy X", "Randomized controlled trial of therapy X in adults"),
            self.create_test_paper("animal_study", "Drug test in rats", "Testing drug effects in laboratory rats"),
            self.create_test_paper("unclear_study", "Study of intervention Y", "Unclear study design examining intervention Y")
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 3
        
        # Should have mixture of decisions
        decisions = [r.decision for r in results]
        assert "include" in decisions
        assert "exclude" in decisions
        # May or may not have "maybe" depending on the unclear study
    
    @pytest.mark.asyncio
    async def test_screen_papers_with_verify_integration(self):
        """Test screening with VERIFY integration."""
        papers = [
            self.create_test_paper("test_paper", "Test study", "Test abstract")
        ]
        
        search_strategy = self.create_test_search_strategy()
        
        # Mock citation verifier
        mock_verifier = MagicMock()
        mock_verifier.verify_citation_async = AsyncMock(
            return_value={'verified': True, 'confidence': 0.9}
        )
        
        screening_assistant = ScreeningAssistant(citation_verifier=mock_verifier)
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        # Verify that the citation verifier was called
        mock_verifier.verify_citation_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_screen_papers_empty_list(self):
        """Test screening with empty papers list."""
        papers = []
        search_strategy = self.create_test_search_strategy()
        
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_screen_papers_confidence_scoring(self):
        """Test that confidence scores are reasonable."""
        papers = [
            self.create_test_paper("clear_include", "Randomized controlled trial of X", "Well-designed RCT"),
            self.create_test_paper("clear_exclude", "Animal study of Y", "Study in laboratory mice"),
            self.create_test_paper("unclear", "Study of Z", "Unclear methodology")
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 3
        
        # Clear decisions should have higher confidence
        for result in results:
            if "randomized" in result.reason.lower() or "animal" in result.reason.lower():
                assert result.confidence >= 0.7
            assert 0.0 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_screen_papers_80_20_methodology(self):
        """Test that the 80/20 methodology is applied correctly."""
        # Create papers that should trigger different confidence levels
        papers = [
            self.create_test_paper("high_conf_include", "Randomized controlled trial", "RCT in adults"),
            self.create_test_paper("high_conf_exclude", "Animal study", "Study in mice"),
            self.create_test_paper("medium_conf", "Observational study", "Cohort study design"),
            self.create_test_paper("low_conf", "Unclear study", "Methodology not clearly described")
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 4
        
        # Check that we have a range of confidence scores
        confidences = [r.confidence for r in results]
        assert max(confidences) >= 0.8  # Some high confidence decisions
        assert min(confidences) <= 0.7  # Some lower confidence decisions
    
    @pytest.mark.asyncio
    async def test_screen_papers_reasoning_quality(self):
        """Test that screening reasoning is informative."""
        papers = [
            self.create_test_paper("test_paper", "Test study", "Test abstract")
        ]
        
        search_strategy = self.create_test_search_strategy()
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        result = results[0]
        
        # Reasoning should be non-empty and informative
        assert len(result.reason) > 10
        assert not result.reason.startswith("No reason")
        assert not result.reason.startswith("Unknown")


class TestScreeningFallback:
    """Test suite for screening fallback functionality."""
    
    @pytest.mark.asyncio
    async def test_screening_without_verify(self):
        """Test screening works without VERIFY integration."""
        papers = [
            Paper(
                id="test_paper",
                title="Test Paper",
                abstract="Test abstract",
                authors=["Test Author"],
                year=2023,
                journal="Test Journal"
            )
        ]
        
        search_strategy = SearchStrategy(
            research_question="Test question",
            pico_elements={'population': ['adults']},
            search_queries={'pubmed': 'test'},
            inclusion_criteria=['Test'],
            exclusion_criteria=['Test']
        )
        
        # No citation verifier provided
        screening_assistant = ScreeningAssistant()
        results = await screening_assistant.screen_papers(papers, search_strategy)
        
        assert len(results) == 1
        assert isinstance(results[0], ScreeningResult)


if __name__ == "__main__":
    pytest.main([__file__])