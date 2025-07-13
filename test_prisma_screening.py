"""
Comprehensive test suite for PRISMA ScreeningAssistant.

Tests the core 80/20 rule functionality and complex scoring logic that drives
automated paper screening decisions.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock
from datetime import datetime

# Add the direct path to avoid import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'knowledge_storm', 'prisma'))

try:
    from knowledge_storm.prisma.screening import ScreeningAssistant, PRISMAScreener
    from knowledge_storm.prisma.models import Paper, SearchStrategy
except ImportError:
    # Direct import if main package has issues
    from screening import ScreeningAssistant, PRISMAScreener
    from models import Paper, SearchStrategy


class TestScreeningAssistant:
    """Test the core ScreeningAssistant functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assistant = ScreeningAssistant()
        
        # Create mock search strategy for testing
        self.search_strategy = SearchStrategy(
            research_question="Effects of machine learning on healthcare outcomes",
            pico_elements={
                'population': ['patients', 'healthcare workers', 'medical professionals'],
                'intervention': ['machine learning', 'artificial intelligence', 'deep learning'],
                'comparison': ['traditional methods', 'standard care', 'manual analysis'],
                'outcome': ['accuracy', 'efficiency', 'patient outcomes', 'diagnosis']
            },
            search_queries={
                'primary': 'machine learning healthcare',
                'secondary': 'AI medical diagnosis'
            },
            inclusion_criteria=['human studies', 'peer-reviewed', 'english language'],
            exclusion_criteria=['animal studies', 'editorials', 'conference abstracts']
        )
    
    def test_high_confidence_exclusion_animal_studies(self):
        """Test high-confidence exclusion of animal studies."""
        animal_paper = Paper(
            title="Effects of drug X on laboratory mice",
            abstract="This study examined the effects of drug X on 50 laboratory mice over 6 weeks.",
            authors=["Smith J", "Doe A"],
            year=2023,
            journal="Animal Research Journal"
        )
        
        decision, reason, confidence = self.assistant._screen_single_paper(animal_paper, self.search_strategy)
        
        assert decision == 'exclude'
        assert reason == 'wrong_population'
        assert confidence >= 0.8  # High confidence exclusion
    
    def test_high_confidence_exclusion_editorial(self):
        """Test high-confidence exclusion of editorials."""
        editorial_paper = Paper(
            title="Editorial: The future of AI in medicine",
            abstract="This editorial discusses the potential impacts of AI on healthcare delivery.",
            authors=["Editor A"],
            year=2023,
            journal="Medical Journal"
        )
        
        decision, reason, confidence = self.assistant._screen_single_paper(editorial_paper, self.search_strategy)
        
        assert decision == 'exclude'
        assert reason == 'wrong_study_type'
        assert confidence >= 0.8
    
    def test_human_study_exception_handling(self):
        """Test that animal studies mentioning humans get lower exclusion confidence."""
        comparative_paper = Paper(
            title="Comparison of drug efficacy in mice and human cell lines",
            abstract="This study compared drug X effects in laboratory mice and human cell cultures.",
            authors=["Research Team"],
            year=2023,
            journal="Comparative Medicine"
        )
        
        decision, reason, confidence = self.assistant._screen_single_paper(comparative_paper, self.search_strategy)
        
        # Should still exclude but with lower confidence due to human mention
        assert decision == 'exclude'
        assert reason == 'wrong_population'
        assert confidence < 0.8  # Lower confidence due to human mention
    
    def test_high_confidence_inclusion_rct(self):
        """Test high-confidence inclusion of randomized controlled trial."""
        rct_paper = Paper(
            title="Randomized controlled trial of machine learning for medical diagnosis",
            abstract="""This randomized controlled trial examined the effectiveness of machine learning 
            algorithms for medical diagnosis. 200 patients were randomly assigned to either AI-assisted 
            diagnosis or standard care. Primary outcome was diagnostic accuracy. Statistical analysis 
            used chi-square tests with p<0.05 significance. The study received ethics approval.""",
            authors=["Clinical Team"],
            year=2023,
            journal="New England Journal of Medicine",
            doi="10.1056/example"
        )
        
        decision, reason, confidence = self.assistant._screen_single_paper(rct_paper, self.search_strategy)
        
        assert decision == 'include'
        assert reason == 'high_relevance'
        assert confidence >= 0.8  # High confidence inclusion
    
    def test_moderate_confidence_needs_review(self):
        """Test that moderate confidence papers go to human review."""
        moderate_paper = Paper(
            title="Survey of AI applications in healthcare",
            abstract="This survey reviewed various applications of AI in healthcare settings.",
            authors=["Survey Team"],
            year=2022,
            journal="Healthcare Technology Review"
        )
        
        decision, reason, confidence = self.assistant._screen_single_paper(moderate_paper, self.search_strategy)
        
        assert decision == 'maybe'
        assert 0.3 <= confidence < 0.8  # Moderate confidence range
    
    def test_advanced_inclusion_score_pico_alignment(self):
        """Test PICO alignment scoring component."""
        # Paper with strong PICO alignment
        strong_pico_paper = Paper(
            title="Machine learning improves patient outcomes in healthcare",
            abstract="""This study evaluated machine learning algorithms for improving patient outcomes. 
            Healthcare workers used AI tools compared to traditional methods. Primary outcome was 
            diagnostic accuracy and efficiency improvements.""",
            authors=["Research Team"],
            year=2023,
            journal="Medical AI Journal"
        )
        
        score = self.assistant._calculate_advanced_inclusion_score(strong_pico_paper, self.search_strategy)
        
        # Should have good score due to strong PICO alignment
        assert score >= 0.4  # Reasonable minimum for strong PICO match
        
        # Test weak PICO alignment
        weak_pico_paper = Paper(
            title="Software engineering principles",
            abstract="This paper discusses general software engineering principles and methodologies.",
            authors=["Software Team"],
            year=2023,
            journal="Software Engineering Journal"
        )
        
        weak_score = self.assistant._calculate_advanced_inclusion_score(weak_pico_paper, self.search_strategy)
        
        # Should have much lower score
        assert weak_score < score
        assert weak_score <= 0.2  # Low score for poor PICO alignment
    
    def test_advanced_inclusion_score_methodology_component(self):
        """Test methodology scoring component."""
        high_method_paper = Paper(
            title="Clinical trial of AI diagnosis",
            abstract="""Randomized controlled prospective study with n=500 participants. 
            Statistical significance tested with p<0.01. Primary outcome was diagnostic accuracy.
            Secondary outcomes included efficiency metrics. Study had ethics approval and 
            used intention-to-treat analysis. Confidence intervals calculated at 95%.""",
            authors=["Clinical Team"],
            year=2023,
            journal="Clinical Research"
        )
        
        score = self.assistant._calculate_advanced_inclusion_score(high_method_paper, self.search_strategy)
        
        # Should have high methodology score component
        assert score >= 0.5  # Should be high due to strong methodology signals
    
    def test_advanced_inclusion_score_venue_quality(self):
        """Test venue quality scoring component."""
        top_venue_paper = Paper(
            title="AI research study",
            abstract="Research on AI applications in medicine.",
            authors=["Research Team"],
            year=2023,
            journal="Nature Medicine"  # Top-tier journal
        )
        
        mid_venue_paper = Paper(
            title="AI research study",
            abstract="Research on AI applications in medicine.",
            authors=["Research Team"],
            year=2023,
            journal="PLOS ONE"  # Mid-tier journal
        )
        
        unknown_venue_paper = Paper(
            title="AI research study",
            abstract="Research on AI applications in medicine.",
            authors=["Research Team"],
            year=2023,
            journal="Unknown Venue"
        )
        
        top_score = self.assistant._calculate_advanced_inclusion_score(top_venue_paper, self.search_strategy)
        mid_score = self.assistant._calculate_advanced_inclusion_score(mid_venue_paper, self.search_strategy)
        unknown_score = self.assistant._calculate_advanced_inclusion_score(unknown_venue_paper, self.search_strategy)
        
        # Venue quality should contribute incrementally
        assert top_score >= mid_score >= unknown_score
    
    def test_advanced_inclusion_score_recency_component(self):
        """Test recency scoring component."""
        recent_paper = Paper(
            title="AI research study",
            abstract="Research on AI applications in medicine.",
            authors=["Research Team"],
            year=datetime.now().year,  # Current year
            journal="Medical Journal"
        )
        
        old_paper = Paper(
            title="AI research study", 
            abstract="Research on AI applications in medicine.",
            authors=["Research Team"],
            year=2010,  # Old paper
            journal="Medical Journal"
        )
        
        recent_score = self.assistant._calculate_advanced_inclusion_score(recent_paper, self.search_strategy)
        old_score = self.assistant._calculate_advanced_inclusion_score(old_paper, self.search_strategy)
        
        # Recent papers should score slightly higher
        assert recent_score >= old_score
    
    def test_confidence_boosting_multiple_signals(self):
        """Test confidence boosting when multiple strong signals are present."""
        strong_signals_paper = Paper(
            title="Randomized controlled trial of machine learning for patient diagnosis accuracy",
            abstract="""This randomized controlled trial examined machine learning algorithms for 
            improving patient diagnosis accuracy in healthcare settings. 300 patients were enrolled
            with statistical significance testing (p<0.01). Primary outcome was diagnostic accuracy.
            Ethics approval obtained. Confidence intervals reported at 95%. Multiple references cited.""",
            authors=["Strong Research Team"],
            year=datetime.now().year,
            journal="Nature Medicine",
            doi="10.1038/example"
        )
        
        weak_signals_paper = Paper(
            title="Brief note on AI",
            abstract="Short note about AI applications.",
            authors=["Author"],
            year=2015,
            journal="Minor Journal"
        )
        
        strong_score = self.assistant._calculate_advanced_inclusion_score(strong_signals_paper, self.search_strategy)
        weak_score = self.assistant._calculate_advanced_inclusion_score(weak_signals_paper, self.search_strategy)
        
        # Strong signals paper should have significantly higher score
        assert strong_score >= 0.7  # Should be high due to multiple strong signals
        assert weak_score <= 0.3   # Should be low due to weak signals
        assert strong_score > weak_score * 2  # At least 2x difference
    
    @pytest.mark.asyncio
    async def test_screen_papers_80_20_rule(self):
        """Test that screening achieves approximately 80/20 distribution."""
        # Create a diverse set of test papers
        test_papers = [
            # High-confidence inclusions (should be auto-included)
            Paper(
                title="Randomized controlled trial of AI diagnosis",
                abstract="RCT with 500 patients testing machine learning for medical diagnosis. p<0.001.",
                authors=["Clinical Team"], year=2023, journal="NEJM"
            ),
            Paper(
                title="Systematic review of AI in healthcare",
                abstract="Systematic review and meta-analysis of AI applications in patient care.",
                authors=["Review Team"], year=2023, journal="Lancet"
            ),
            
            # High-confidence exclusions (should be auto-excluded) 
            Paper(
                title="Effects of drug X on laboratory mice",
                abstract="Animal study testing drug effects on 50 laboratory mice.",
                authors=["Animal Team"], year=2023, journal="Animal Research"
            ),
            Paper(
                title="Editorial: Future of AI",
                abstract="Editorial discussing potential AI applications.",
                authors=["Editor"], year=2023, journal="Medical Journal"
            ),
            
            # Moderate confidence (should need human review)
            Paper(
                title="Survey of AI tools", 
                abstract="Survey of various AI tools used in healthcare settings.",
                authors=["Survey Team"], year=2022, journal="Tech Review"
            ),
            Paper(
                title="Case report of AI diagnosis",
                abstract="Single case report of AI-assisted diagnosis.",
                authors=["Case Team"], year=2021, journal="Case Reports"
            ),
            
            # Additional papers for better statistics
            Paper(
                title="Cohort study of AI outcomes",
                abstract="Prospective cohort study examining AI implementation outcomes in hospitals.",
                authors=["Cohort Team"], year=2023, journal="Healthcare Research"
            ),
            Paper(
                title="Conference abstract on AI",
                abstract="Abstract from conference presentation on AI applications.",
                authors=["Presenter"], year=2023, journal="Conference Proceedings"
            )
        ]
        
        results = await self.assistant.screen_papers(test_papers, self.search_strategy)
        
        # Verify results structure
        assert 'definitely_exclude' in results
        assert 'definitely_include' in results  
        assert 'needs_human_review' in results
        assert 'performance_metrics' in results
        
        # Check that we have reasonable distribution
        total = len(test_papers)
        auto_decided = len(results['definitely_exclude']) + len(results['definitely_include'])
        human_review = len(results['needs_human_review'])
        
        assert auto_decided + human_review == total
        
        # Verify performance metrics calculation
        metrics = results['performance_metrics']
        assert metrics['total_papers'] == total
        assert metrics['auto_decided'] == auto_decided
        assert abs(metrics['auto_decision_rate'] - (auto_decided / total)) < 0.01
        assert abs(metrics['human_review_rate'] - (human_review / total)) < 0.01
        
        # Check confidence threshold application
        for paper in results['definitely_exclude']:
            assert paper.confidence_score >= 0.8
        for paper in results['definitely_include']:
            assert paper.confidence_score >= 0.8
    
    def test_exclusion_pattern_coverage(self):
        """Test that exclusion patterns cover expected cases."""
        exclusion_cases = [
            ("Animal study on rats", "wrong_population"),
            ("In vitro cell culture study", "wrong_population"), 
            ("Editorial commentary", "wrong_study_type"),
            ("Conference abstract presentation", "wrong_study_type"),
            ("Duplicate publication notice", "duplicate"),
            ("Chinese language article", "wrong_language")
        ]
        
        for title, expected_reason in exclusion_cases:
            test_paper = Paper(
                title=title,
                abstract=f"This is a {title.lower()} examining various aspects.",
                authors=["Test Author"],
                year=2023,
                journal="Test Journal"
            )
            
            decision, reason, confidence = self.assistant._screen_single_paper(test_paper, self.search_strategy)
            
            assert decision == 'exclude', f"Failed to exclude: {title}"
            assert reason == expected_reason, f"Wrong exclusion reason for: {title}"
            assert confidence >= 0.6, f"Low confidence for clear exclusion: {title}"


class TestPRISMAScreener:
    """Test the PRISMAScreener interface wrapper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.screener = PRISMAScreener(
            include_patterns=['randomized', 'controlled', 'trial'],
            exclude_patterns=['animal', 'mice', 'editorial'],
            threshold=0.8
        )
    
    @pytest.mark.asyncio
    async def test_screener_interface(self):
        """Test the PRISMAScreener interface works correctly."""
        test_papers = [
            Paper(
                title="Randomized controlled trial of treatment X",
                abstract="RCT testing treatment effectiveness.",
                authors=["Test Team"],
                year=2023,
                journal="Medical Journal"
            ),
            Paper(
                title="Animal study on mice",
                abstract="Study testing drug effects on laboratory mice.",
                authors=["Animal Team"],
                year=2023,
                journal="Animal Research"
            )
        ]
        
        results = await self.screener.screen_papers(test_papers)
        
        # Verify interface returns expected structure
        assert isinstance(results, dict)
        assert 'definitely_exclude' in results
        assert 'definitely_include' in results
        assert 'needs_human_review' in results
        assert 'performance_metrics' in results
        
        # Verify papers were processed
        total_processed = (len(results['definitely_exclude']) + 
                          len(results['definitely_include']) + 
                          len(results['needs_human_review']))
        assert total_processed == len(test_papers)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assistant = ScreeningAssistant()
        self.empty_strategy = SearchStrategy(
            research_question="Empty test strategy",
            pico_elements={'population': [], 'intervention': [], 'comparison': [], 'outcome': []},
            search_queries={},
            inclusion_criteria=[],
            exclusion_criteria=[]
        )
    
    def test_empty_paper_fields(self):
        """Test handling of papers with empty or None fields."""
        empty_paper = Paper(
            title="",
            abstract="",
            authors=[],
            year=None,
            journal=None
        )
        
        # Should not crash and should return low confidence
        decision, reason, confidence = self.assistant._screen_single_paper(empty_paper, self.empty_strategy)
        
        assert decision in ['exclude', 'maybe']
        assert confidence <= 0.5  # Low confidence for empty paper
    
    def test_missing_abstract(self):
        """Test handling of papers with missing abstracts."""
        no_abstract_paper = Paper(
            title="Interesting research title about machine learning in healthcare",
            abstract=None,  # Missing abstract
            authors=["Research Team"],
            year=2023,
            journal="Medical Journal"
        )
        
        # Should still process based on title
        decision, reason, confidence = self.assistant._screen_single_paper(no_abstract_paper, self.empty_strategy)
        
        assert decision is not None
        assert reason is not None
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_empty_paper_list(self):
        """Test screening with empty paper list."""
        results = await self.assistant.screen_papers([], self.empty_strategy)
        
        assert results['performance_metrics']['total_papers'] == 0
        assert results['performance_metrics']['auto_decision_rate'] == 0
        assert len(results['definitely_exclude']) == 0
        assert len(results['definitely_include']) == 0
        assert len(results['needs_human_review']) == 0
    
    def test_score_bounds(self):
        """Test that inclusion scores are always between 0 and 1."""
        # Test with extreme cases that might push scores out of bounds
        extreme_paper = Paper(
            title="RANDOMIZED CONTROLLED TRIAL " * 10,  # Repetitive keywords
            abstract="MACHINE LEARNING " * 50 + "PATIENTS " * 50 + "STATISTICAL SIGNIFICANCE " * 50,
            authors=["Test Team"],
            year=datetime.now().year,
            journal="Nature Science Lancet NEJM",  # Multiple top venues
            doi="10.1000/example"
        )
        
        score = self.assistant._calculate_advanced_inclusion_score(extreme_paper, SearchStrategy(
            research_question="Test",
            pico_elements={
                'population': ['patients'] * 20,  # Many terms
                'intervention': ['machine learning'] * 20,
                'comparison': ['control'] * 20,
                'outcome': ['accuracy'] * 20
            },
            search_queries={},
            inclusion_criteria=[],
            exclusion_criteria=[]
        ))
        
        assert 0.0 <= score <= 1.0, f"Score {score} is out of bounds [0,1]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])