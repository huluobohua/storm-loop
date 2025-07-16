"""
Unit tests for PRISMA draft generation functionality.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from knowledge_storm.modules.prisma.draft_generation import ZeroDraftGenerator
from knowledge_storm.modules.prisma.core import SearchStrategy, ScreeningResult


class TestZeroDraftGenerator:
    """Test suite for ZeroDraftGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_lm_model = MagicMock()
        self.mock_lm_model.generate_async = AsyncMock(return_value="Generated text")
        
        self.draft_generator = ZeroDraftGenerator(self.mock_lm_model)
    
    def create_test_search_strategy(self):
        """Helper method to create test search strategy."""
        return SearchStrategy(
            research_question="What is the effectiveness of intervention X in adults?",
            pico_elements={
                'population': ['adults', 'age 18-65'],
                'intervention': ['intervention X'],
                'comparison': ['placebo', 'standard care'],
                'outcome': ['primary outcome', 'secondary outcome']
            },
            search_queries={
                'pubmed': 'adults AND "intervention X" AND (placebo OR "standard care")',
                'embase': 'adult AND intervention X AND (placebo OR standard care)',
                'cochrane': 'intervention X AND adult'
            },
            inclusion_criteria=['Adults aged 18-65', 'Randomized controlled trials'],
            exclusion_criteria=['Animal studies', 'Case reports', 'Reviews'],
            date_range=(2010, 2023),
            languages=['English']
        )
    
    def create_test_screening_results(self):
        """Helper method to create test screening results."""
        return [
            ScreeningResult(
                decision="include",
                confidence=0.95,
                reason="Well-designed RCT meeting inclusion criteria"
            ),
            ScreeningResult(
                decision="include",
                confidence=0.85,
                reason="Cohort study with relevant outcomes"
            ),
            ScreeningResult(
                decision="exclude",
                confidence=0.90,
                reason="Animal study - does not meet inclusion criteria"
            ),
            ScreeningResult(
                decision="exclude",
                confidence=0.88,
                reason="Case report - inappropriate study design"
            ),
            ScreeningResult(
                decision="maybe",
                confidence=0.65,
                reason="Unclear methodology - requires full text review"
            )
        ]
    
    def test_initialization(self):
        """Test ZeroDraftGenerator initialization."""
        generator = ZeroDraftGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_methods_section')
        assert hasattr(generator, 'generate_results_section')
        assert hasattr(generator, 'generate_discussion_section')
        assert hasattr(generator, 'generate_abstract')
    
    def test_initialization_with_model(self):
        """Test ZeroDraftGenerator initialization with LM model."""
        mock_model = MagicMock()
        generator = ZeroDraftGenerator(mock_model)
        assert generator.lm_model == mock_model
    
    @pytest.mark.asyncio
    async def test_generate_methods_section(self):
        """Test generating methods section."""
        search_strategy = self.create_test_search_strategy()
        
        generator = ZeroDraftGenerator()
        methods_section = await generator.generate_methods_section(search_strategy)
        
        assert isinstance(methods_section, str)
        assert len(methods_section) > 100  # Should be substantial
        
        # Should contain key methodological elements
        methods_lower = methods_section.lower()
        assert "search strategy" in methods_lower
        assert "inclusion criteria" in methods_lower
        assert "exclusion criteria" in methods_lower
        assert "database" in methods_lower
        
        # Should mention specific databases
        assert "pubmed" in methods_lower
        assert "embase" in methods_lower
        assert "cochrane" in methods_lower
        
        # Should mention PICO elements
        assert "population" in methods_lower or "participants" in methods_lower
        assert "intervention" in methods_lower
        assert "outcome" in methods_lower
        
        # Should mention date range
        assert "2010" in methods_section
        assert "2023" in methods_section
    
    @pytest.mark.asyncio
    async def test_generate_results_section(self):
        """Test generating results section."""
        screening_results = self.create_test_screening_results()
        
        generator = ZeroDraftGenerator()
        results_section = await generator.generate_results_section(screening_results)
        
        assert isinstance(results_section, str)
        assert len(results_section) > 100  # Should be substantial
        
        # Should contain key results elements
        results_lower = results_section.lower()
        assert "screening" in results_lower
        assert "included" in results_lower
        assert "excluded" in results_lower
        
        # Should mention specific numbers
        assert "2" in results_section  # 2 included
        assert "2" in results_section  # 2 excluded
        assert "1" in results_section  # 1 maybe
        
        # Should mention screening methodology
        assert "confidence" in results_lower or "automated" in results_lower
        assert "80/20" in results_section or "methodology" in results_lower
    
    @pytest.mark.asyncio
    async def test_generate_discussion_section(self):
        """Test generating discussion section."""
        search_strategy = self.create_test_search_strategy()
        screening_results = self.create_test_screening_results()
        
        generator = ZeroDraftGenerator()
        discussion_section = await generator.generate_discussion_section(
            search_strategy, screening_results
        )
        
        assert isinstance(discussion_section, str)
        assert len(discussion_section) > 100  # Should be substantial
        
        # Should contain key discussion elements
        discussion_lower = discussion_section.lower()
        assert "limitation" in discussion_lower
        assert "strength" in discussion_lower or "findings" in discussion_lower
        assert "future" in discussion_lower or "research" in discussion_lower
        
        # Should reference the methodology
        assert "systematic" in discussion_lower
        assert "screening" in discussion_lower
    
    @pytest.mark.asyncio
    async def test_generate_abstract(self):
        """Test generating abstract."""
        search_strategy = self.create_test_search_strategy()
        screening_results = self.create_test_screening_results()
        
        generator = ZeroDraftGenerator()
        abstract = await generator.generate_abstract(search_strategy, screening_results)
        
        assert isinstance(abstract, str)
        assert len(abstract) > 100  # Should be substantial
        assert len(abstract) < 2000  # But not too long for an abstract
        
        # Should contain key abstract elements
        abstract_lower = abstract.lower()
        assert "objective" in abstract_lower or "background" in abstract_lower
        assert "method" in abstract_lower
        assert "result" in abstract_lower
        assert "conclusion" in abstract_lower
        
        # Should mention the research question
        assert "intervention x" in abstract_lower
        assert "adult" in abstract_lower
    
    @pytest.mark.asyncio
    async def test_generate_methods_section_with_lm_model(self):
        """Test generating methods section with LM model."""
        mock_model = MagicMock()
        mock_model.generate_async = AsyncMock(return_value="AI-generated methods section")
        
        generator = ZeroDraftGenerator(mock_model)
        search_strategy = self.create_test_search_strategy()
        
        methods_section = await generator.generate_methods_section(search_strategy)
        
        # Should use the AI model when available
        mock_model.generate_async.assert_called_once()
        
        # Should return AI-generated content
        assert "AI-generated methods section" in methods_section
    
    @pytest.mark.asyncio
    async def test_generate_results_section_with_lm_model(self):
        """Test generating results section with LM model."""
        mock_model = MagicMock()
        mock_model.generate_async = AsyncMock(return_value="AI-generated results section")
        
        generator = ZeroDraftGenerator(mock_model)
        screening_results = self.create_test_screening_results()
        
        results_section = await generator.generate_results_section(screening_results)
        
        # Should use the AI model when available
        mock_model.generate_async.assert_called_once()
        
        # Should return AI-generated content
        assert "AI-generated results section" in results_section
    
    @pytest.mark.asyncio
    async def test_generate_methods_section_no_model(self):
        """Test generating methods section without LM model."""
        generator = ZeroDraftGenerator()  # No model provided
        search_strategy = self.create_test_search_strategy()
        
        methods_section = await generator.generate_methods_section(search_strategy)
        
        # Should generate template-based content
        assert isinstance(methods_section, str)
        assert len(methods_section) > 100
        
        # Should contain template elements
        methods_lower = methods_section.lower()
        assert "search strategy" in methods_lower
        assert "databases" in methods_lower
        assert "criteria" in methods_lower
    
    @pytest.mark.asyncio
    async def test_generate_results_section_no_model(self):
        """Test generating results section without LM model."""
        generator = ZeroDraftGenerator()  # No model provided
        screening_results = self.create_test_screening_results()
        
        results_section = await generator.generate_results_section(screening_results)
        
        # Should generate template-based content
        assert isinstance(results_section, str)
        assert len(results_section) > 100
        
        # Should contain template elements and statistics
        results_lower = results_section.lower()
        assert "screening" in results_lower
        assert "included" in results_lower
        assert "excluded" in results_lower
        assert "2" in results_section  # Number of included studies
    
    @pytest.mark.asyncio
    async def test_screening_statistics_calculation(self):
        """Test that screening statistics are calculated correctly."""
        screening_results = self.create_test_screening_results()
        
        generator = ZeroDraftGenerator()
        results_section = await generator.generate_results_section(screening_results)
        
        # Should correctly calculate statistics
        assert "2" in results_section  # 2 included
        assert "2" in results_section  # 2 excluded
        assert "1" in results_section  # 1 maybe
        assert "5" in results_section  # 5 total
        
        # Should mention automation rate
        results_lower = results_section.lower()
        assert "automated" in results_lower or "confidence" in results_lower
    
    @pytest.mark.asyncio
    async def test_generate_with_empty_results(self):
        """Test generating sections with empty screening results."""
        empty_results = []
        
        generator = ZeroDraftGenerator()
        results_section = await generator.generate_results_section(empty_results)
        
        # Should handle empty results gracefully
        assert isinstance(results_section, str)
        assert len(results_section) > 50  # Should still generate something
        
        results_lower = results_section.lower()
        assert "no studies" in results_lower or "0" in results_section
    
    @pytest.mark.asyncio
    async def test_generate_with_minimal_search_strategy(self):
        """Test generating methods with minimal search strategy."""
        minimal_strategy = SearchStrategy(
            research_question="Simple question",
            pico_elements={'population': ['adults']},
            search_queries={'pubmed': 'simple query'},
            inclusion_criteria=['Include adults'],
            exclusion_criteria=['Exclude animals']
        )
        
        generator = ZeroDraftGenerator()
        methods_section = await generator.generate_methods_section(minimal_strategy)
        
        # Should handle minimal strategy gracefully
        assert isinstance(methods_section, str)
        assert len(methods_section) > 50
        
        methods_lower = methods_section.lower()
        assert "search strategy" in methods_lower
        assert "adults" in methods_lower
    
    @pytest.mark.asyncio
    async def test_newline_character_usage(self):
        """Test that proper newline characters are used (not chr(10))."""
        search_strategy = self.create_test_search_strategy()
        
        generator = ZeroDraftGenerator()
        methods_section = await generator.generate_methods_section(search_strategy)
        
        # Should use \n not chr(10) for newlines
        assert "\n" in methods_section
        assert chr(10) not in methods_section or methods_section.count(chr(10)) == methods_section.count("\n")


if __name__ == "__main__":
    pytest.main([__file__])