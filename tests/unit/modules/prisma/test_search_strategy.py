"""
Unit tests for PRISMA search strategy builder.
"""

import pytest
from knowledge_storm.modules.prisma.search_strategy import SearchStrategyBuilder
from knowledge_storm.modules.prisma.core import SearchStrategy


class TestSearchStrategyBuilder:
    """Test suite for SearchStrategyBuilder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = SearchStrategyBuilder()
    
    def test_initialization(self):
        """Test SearchStrategyBuilder initialization."""
        builder = SearchStrategyBuilder()
        assert builder is not None
        assert hasattr(builder, 'build_search_strategy')
        assert hasattr(builder, 'extract_pico_elements')
        assert hasattr(builder, 'generate_database_queries')
    
    def test_build_search_strategy_diabetes_example(self):
        """Test building search strategy for diabetes research."""
        research_question = "What is the effectiveness of insulin therapy in adults with type 2 diabetes?"
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        assert isinstance(strategy, SearchStrategy)
        assert strategy.research_question == research_question
        assert isinstance(strategy.pico_elements, dict)
        assert isinstance(strategy.search_queries, dict)
        assert isinstance(strategy.inclusion_criteria, list)
        assert isinstance(strategy.exclusion_criteria, list)
        
        # Check PICO elements are populated
        assert 'population' in strategy.pico_elements
        assert 'intervention' in strategy.pico_elements
        assert 'outcome' in strategy.pico_elements
        
        # Check that search queries are generated for multiple databases
        assert len(strategy.search_queries) > 0
        expected_databases = ["pubmed", "embase", "cochrane"]
        for db in expected_databases:
            if db in strategy.search_queries:
                assert isinstance(strategy.search_queries[db], str)
                assert len(strategy.search_queries[db]) > 0
    
    def test_build_search_strategy_cancer_example(self):
        """Test building search strategy for cancer research."""
        research_question = "Does chemotherapy improve survival in elderly patients with lung cancer?"
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        assert isinstance(strategy, SearchStrategy)
        assert strategy.research_question == research_question
        
        # Check that PICO elements are appropriate for cancer research
        pico = strategy.pico_elements
        assert 'population' in pico
        assert 'intervention' in pico
        assert 'outcome' in pico
        
        # Population should include elderly and lung cancer terms
        population_terms = ' '.join(pico['population']).lower()
        assert 'elderly' in population_terms or 'older' in population_terms
        assert 'lung' in population_terms and 'cancer' in population_terms
        
        # Intervention should include chemotherapy
        intervention_terms = ' '.join(pico['intervention']).lower()
        assert 'chemotherapy' in intervention_terms or 'chemo' in intervention_terms
        
        # Outcome should include survival
        outcome_terms = ' '.join(pico['outcome']).lower()
        assert 'survival' in outcome_terms or 'mortality' in outcome_terms
    
    def test_extract_pico_elements_basic(self):
        """Test PICO element extraction."""
        research_question = "Does exercise therapy reduce pain in adults with arthritis?"
        
        pico = SearchStrategyBuilder().extract_pico_elements(research_question)
        
        assert isinstance(pico, dict)
        assert 'population' in pico
        assert 'intervention' in pico
        assert 'outcome' in pico
        
        # Check population
        population_str = ' '.join(pico['population']).lower()
        assert 'adults' in population_str or 'adult' in population_str
        assert 'arthritis' in population_str
        
        # Check intervention
        intervention_str = ' '.join(pico['intervention']).lower()
        assert 'exercise' in intervention_str
        
        # Check outcome
        outcome_str = ' '.join(pico['outcome']).lower()
        assert 'pain' in outcome_str
    
    def test_generate_database_queries_pubmed(self):
        """Test PubMed query generation."""
        pico = {
            'population': ['adults', 'diabetes'],
            'intervention': ['insulin therapy'],
            'outcome': ['blood glucose', 'glycemic control']
        }
        
        queries = SearchStrategyBuilder().generate_database_queries(pico)
        
        assert isinstance(queries, dict)
        assert 'pubmed' in queries
        
        pubmed_query = queries['pubmed'].lower()
        assert 'adults' in pubmed_query or 'adult' in pubmed_query
        assert 'diabetes' in pubmed_query
        assert 'insulin' in pubmed_query
        assert 'blood glucose' in pubmed_query or 'glycemic' in pubmed_query
        
        # Check for proper boolean operators
        assert 'and' in pubmed_query or 'or' in pubmed_query
    
    def test_generate_database_queries_embase(self):
        """Test Embase query generation."""
        pico = {
            'population': ['children', 'asthma'],
            'intervention': ['inhaled corticosteroids'],
            'outcome': ['lung function']
        }
        
        queries = SearchStrategyBuilder().generate_database_queries(pico)
        
        assert isinstance(queries, dict)
        assert 'embase' in queries
        
        embase_query = queries['embase'].lower()
        assert 'children' in embase_query or 'child' in embase_query
        assert 'asthma' in embase_query
        assert 'corticosteroids' in embase_query or 'steroid' in embase_query
        assert 'lung function' in embase_query
    
    def test_generate_database_queries_cochrane(self):
        """Test Cochrane Library query generation."""
        pico = {
            'population': ['pregnant women'],
            'intervention': ['vitamin D supplementation'],
            'outcome': ['birth weight']
        }
        
        queries = SearchStrategyBuilder().generate_database_queries(pico)
        
        assert isinstance(queries, dict)
        assert 'cochrane' in queries
        
        cochrane_query = queries['cochrane'].lower()
        assert 'pregnant' in cochrane_query or 'pregnancy' in cochrane_query
        assert 'vitamin d' in cochrane_query
        assert 'birth weight' in cochrane_query
    
    def test_inclusion_criteria_generation(self):
        """Test that reasonable inclusion criteria are generated."""
        research_question = "What is the effect of meditation on anxiety in adults?"
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        assert len(strategy.inclusion_criteria) > 0
        
        # Convert to lowercase for easier checking
        criteria_str = ' '.join(strategy.inclusion_criteria).lower()
        
        # Should include study types and population criteria
        assert any(keyword in criteria_str for keyword in ['randomized', 'controlled', 'clinical', 'study'])
        assert 'adults' in criteria_str or 'adult' in criteria_str
    
    def test_exclusion_criteria_generation(self):
        """Test that reasonable exclusion criteria are generated."""
        research_question = "Does physical therapy improve mobility in stroke patients?"
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        assert len(strategy.exclusion_criteria) > 0
        
        # Convert to lowercase for easier checking
        criteria_str = ' '.join(strategy.exclusion_criteria).lower()
        
        # Should exclude common irrelevant study types
        assert any(keyword in criteria_str for keyword in ['animal', 'review', 'case report', 'editorial'])
    
    def test_build_search_strategy_with_empty_question(self):
        """Test handling of empty research question."""
        with pytest.raises(ValueError, match="Research question cannot be empty"):
            SearchStrategyBuilder().build_search_strategy("")
    
    def test_build_search_strategy_with_none_question(self):
        """Test handling of None research question."""
        with pytest.raises(ValueError, match="Research question cannot be empty"):
            SearchStrategyBuilder().build_search_strategy(None)
    
    def test_date_range_default(self):
        """Test that default date range is reasonable."""
        research_question = "What is the effect of exercise on depression?"
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        # Should have a date range or be None
        if strategy.date_range is not None:
            start_year, end_year = strategy.date_range
            assert isinstance(start_year, int)
            assert isinstance(end_year, int)
            assert start_year <= end_year
            assert start_year >= 1990  # Reasonable lower bound
            assert end_year <= 2025    # Reasonable upper bound
    
    def test_languages_default(self):
        """Test that default languages are set."""
        research_question = "What is the effect of diet on cardiovascular disease?"
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        assert isinstance(strategy.languages, list)
        assert len(strategy.languages) > 0
        assert "English" in strategy.languages
    
    def test_complex_medical_question(self):
        """Test handling of complex medical research question."""
        research_question = ("What is the comparative effectiveness of minimally invasive "
                           "versus open surgical approaches for treating colorectal cancer "
                           "in elderly patients with comorbidities?")
        
        strategy = SearchStrategyBuilder().build_search_strategy(research_question)
        
        assert isinstance(strategy, SearchStrategy)
        
        # Check that complex terms are captured in PICO
        pico_str = str(strategy.pico_elements).lower()
        assert 'colorectal' in pico_str or 'colon' in pico_str
        assert 'elderly' in pico_str or 'older' in pico_str
        assert 'surgical' in pico_str or 'surgery' in pico_str
        assert 'minimally invasive' in pico_str or 'laparoscopic' in pico_str


if __name__ == "__main__":
    pytest.main([__file__])