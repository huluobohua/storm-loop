"""
Test cases for Citation Strategy Pattern Implementation
Tests the strategy pattern for citation formatting
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'frontend'))

# Set development environment for testing
os.environ['ENVIRONMENT'] = 'development'

from advanced_interface.citation import (
    CitationFormatterInterface,
    CitationFactory,
    ApaFormatter,
    MlaFormatter,
    ChicagoFormatter
)
from advanced_interface.output_manager import OutputManager


class TestCitationStrategyPattern(unittest.TestCase):
    """Test cases for citation strategy pattern implementation"""
    
    def setUp(self):
        """Set up test dependencies"""
        self.sample_paper = {
            "title": "Machine Learning in Academic Research",
            "authors": ["John Smith", "Jane Doe", "Bob Johnson"],
            "year": 2023,
            "journal": "Journal of Computer Science",
            "volume": "15",
            "issue": "3",
            "pages": "123-145",
            "doi": "10.1000/example.doi"
        }
        self.output_manager = OutputManager()
    
    def test_factory_creates_apa_formatter(self):
        """Test that factory creates APA formatter correctly"""
        formatter = CitationFactory.create_formatter('apa')
        self.assertIsInstance(formatter, ApaFormatter)
        self.assertIsInstance(formatter, CitationFormatterInterface)
        self.assertEqual(formatter.get_style_name(), "APA")
    
    def test_factory_creates_mla_formatter(self):
        """Test that factory creates MLA formatter correctly"""
        formatter = CitationFactory.create_formatter('mla')
        self.assertIsInstance(formatter, MlaFormatter)
        self.assertIsInstance(formatter, CitationFormatterInterface)
        self.assertEqual(formatter.get_style_name(), "MLA")
    
    def test_factory_creates_chicago_formatter(self):
        """Test that factory creates Chicago formatter correctly"""
        formatter = CitationFactory.create_formatter('chicago')
        self.assertIsInstance(formatter, ChicagoFormatter)
        self.assertIsInstance(formatter, CitationFormatterInterface)
        self.assertEqual(formatter.get_style_name(), "Chicago")
    
    def test_factory_case_insensitive(self):
        """Test that factory handles case-insensitive style names"""
        formatter1 = CitationFactory.create_formatter('APA')
        formatter2 = CitationFactory.create_formatter('apa')
        formatter3 = CitationFactory.create_formatter('Apa')
        
        self.assertIsInstance(formatter1, ApaFormatter)
        self.assertIsInstance(formatter2, ApaFormatter)
        self.assertIsInstance(formatter3, ApaFormatter)
    
    def test_factory_raises_error_for_invalid_style(self):
        """Test that factory raises error for unsupported style"""
        with self.assertRaises(ValueError) as context:
            CitationFactory.create_formatter('invalid_style')
        
        self.assertIn("Unsupported citation style", str(context.exception))
    
    def test_factory_get_available_styles(self):
        """Test that factory returns available citation styles"""
        styles = CitationFactory.get_available_styles()
        self.assertIn('apa', styles)
        self.assertIn('mla', styles)
        self.assertIn('chicago', styles)
        self.assertIsInstance(styles, list)
    
    def test_factory_register_new_formatter(self):
        """Test that factory can register new formatter types"""
        # Create mock formatter class
        class MockFormatter(CitationFormatterInterface):
            def format_citation(self, paper_data):
                return f"Mock: {paper_data.get('title', 'Unknown')}"
            
            def get_style_name(self):
                return "Mock"
        
        # Register new formatter
        CitationFactory.register_formatter('mock', MockFormatter)
        
        # Verify registration worked
        self.assertIn('mock', CitationFactory.get_available_styles())
        self.assertTrue(CitationFactory.is_style_supported('mock'))
        
        # Verify formatter creation works
        formatter = CitationFactory.create_formatter('mock')
        self.assertIsInstance(formatter, MockFormatter)
    
    def test_apa_formatter_basic_citation(self):
        """Test APA formatter produces correct basic citation"""
        formatter = ApaFormatter()
        citation = formatter.format_citation(self.sample_paper)
        
        # Should contain key APA elements
        self.assertIn("Smith, J., Doe, J., & Johnson, B.", citation)
        self.assertIn("(2023)", citation)
        self.assertIn("Machine Learning in Academic Research", citation)
        self.assertIn("*Journal of Computer Science*", citation)
        self.assertIn("https://doi.org/10.1000/example.doi", citation)
    
    def test_mla_formatter_basic_citation(self):
        """Test MLA formatter produces correct basic citation"""
        formatter = MlaFormatter()
        citation = formatter.format_citation(self.sample_paper)
        
        # Should contain key MLA elements
        self.assertIn("Smith, John, Jane Doe, and Bob Johnson", citation)
        self.assertIn('"Machine Learning in Academic Research."', citation)
        self.assertIn("*Journal of Computer Science*", citation)
        self.assertIn("2023", citation)
        self.assertIn("doi:10.1000/example.doi", citation)
    
    def test_chicago_formatter_basic_citation(self):
        """Test Chicago formatter produces correct basic citation"""
        formatter = ChicagoFormatter()
        citation = formatter.format_citation(self.sample_paper)
        
        # Should contain key Chicago elements
        self.assertIn("Smith, John, Jane Doe, and Bob Johnson", citation)
        self.assertIn("2023", citation)
        self.assertIn('"Machine Learning in Academic Research."', citation)
        self.assertIn("*Journal of Computer Science*", citation)
        self.assertIn("https://doi.org/10.1000/example.doi", citation)
    
    def test_formatters_handle_missing_data(self):
        """Test that formatters handle missing data gracefully"""
        minimal_paper = {"title": "Test Paper"}
        
        # All formatters should handle minimal data
        apa_citation = ApaFormatter().format_citation(minimal_paper)
        mla_citation = MlaFormatter().format_citation(minimal_paper)
        chicago_citation = ChicagoFormatter().format_citation(minimal_paper)
        
        # All should contain the title
        self.assertIn("Test Paper", apa_citation)
        self.assertIn("Test Paper", mla_citation)
        self.assertIn("Test Paper", chicago_citation)
    
    def test_formatters_validate_required_fields(self):
        """Test that formatters validate required fields"""
        empty_paper = {}
        
        # Should raise ValueError for missing title
        with self.assertRaises(ValueError):
            ApaFormatter().format_citation(empty_paper)
        
        with self.assertRaises(ValueError):
            MlaFormatter().format_citation(empty_paper)
        
        with self.assertRaises(ValueError):
            ChicagoFormatter().format_citation(empty_paper)
    
    def test_output_manager_uses_strategy_pattern(self):
        """Test that OutputManager uses the strategy pattern correctly"""
        # Test different citation styles
        apa_citation = self.output_manager.preview_citation_style('apa', self.sample_paper)
        mla_citation = self.output_manager.preview_citation_style('mla', self.sample_paper)
        chicago_citation = self.output_manager.preview_citation_style('chicago', self.sample_paper)
        
        # Each should be different and contain style-specific elements
        self.assertNotEqual(apa_citation, mla_citation)
        self.assertNotEqual(apa_citation, chicago_citation)
        self.assertNotEqual(mla_citation, chicago_citation)
        
        # APA specific check
        self.assertIn("(2023)", apa_citation)
        
        # MLA specific check
        self.assertIn('"Machine Learning in Academic Research."', mla_citation)
    
    def test_output_manager_get_citation_styles_uses_factory(self):
        """Test that OutputManager gets citation styles from factory"""
        styles = self.output_manager.get_citation_styles()
        factory_styles = CitationFactory.get_available_styles()
        
        self.assertEqual(set(styles), set(factory_styles))
    
    def test_output_manager_handles_invalid_citation_style(self):
        """Test that OutputManager handles invalid citation styles"""
        with self.assertRaises(ValueError) as context:
            self.output_manager.preview_citation_style('invalid', self.sample_paper)
        
        self.assertIn("Citation formatting error", str(context.exception))
    
    def test_author_formatting_edge_cases(self):
        """Test author formatting for various edge cases"""
        # Single author
        single_author_paper = {
            "title": "Solo Work", 
            "authors": ["John Smith"]
        }
        
        apa_single = ApaFormatter().format_citation(single_author_paper)
        self.assertIn("Smith, J.", apa_single)
        
        # Many authors (should trigger et al. rules)
        many_authors_paper = {
            "title": "Collaborative Work",
            "authors": [f"Author {i}" for i in range(1, 25)]  # 24 authors
        }
        
        mla_many = MlaFormatter().format_citation(many_authors_paper)
        self.assertIn("et al.", mla_many)
    
    def test_extensibility_principle(self):
        """Test that the system follows Open/Closed Principle"""
        # Should be able to add new formatter without modifying existing code
        
        class IeeeFormatter(CitationFormatterInterface):
            def format_citation(self, paper_data):
                authors = ", ".join(paper_data.get("authors", ["Unknown"]))
                title = paper_data.get("title", "Unknown")
                year = paper_data.get("year", "Unknown")
                return f'{authors}, "{title}," {year}.'
            
            def get_style_name(self):
                return "IEEE"
        
        # Register new style
        CitationFactory.register_formatter('ieee', IeeeFormatter)
        
        # Should now be available
        self.assertIn('ieee', CitationFactory.get_available_styles())
        
        # Should work with OutputManager
        ieee_citation = self.output_manager.preview_citation_style('ieee', self.sample_paper)
        self.assertIn("Machine Learning in Academic Research", ieee_citation)


if __name__ == "__main__":
    unittest.main()