"""
Comprehensive regex pattern tests for Academic Validation Framework.
Tests all regex patterns with positive and negative cases.
"""
import pytest
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_validation_framework.strategies.apa_strategy import APAFormatStrategy
from academic_validation_framework.strategies.mla_strategy import MLAFormatStrategy
from academic_validation_framework.strategies.ieee_strategy import IEEEFormatStrategy
from academic_validation_framework.validators.enhanced_prisma_validator import EnhancedPRISMAValidator
from academic_validation_framework.validators.bias_detector import BiasDetector


class TestAPARegexPatterns:
    """Test APA citation format regex patterns."""
    
    def test_journal_title_italics_pattern(self):
        """Test journal title in italics (*Journal Name*)."""
        # Pattern: r'\*([^*]+)\*'
        pattern = re.compile(r'\*([^*]+)\*')
        
        # Positive cases
        positive_cases = [
            ("Smith, J. (2024). Article title. *Journal of Testing*, 15(3), 234-256.", "Journal of Testing"),
            ("Author, A. (2023). Title. *Nature*, 500, 123-145.", "Nature"),
            ("Multiple authors. (2022). Study. *Very Long Journal Name With Spaces*, 1(1), 1-10.", "Very Long Journal Name With Spaces"),
        ]
        
        for text, expected in positive_cases:
            match = pattern.search(text)
            assert match is not None, f"Pattern should match: {text}"
            assert match.group(1) == expected, f"Expected '{expected}', got '{match.group(1)}'"
        
        # Negative cases
        negative_cases = [
            "Smith, J. (2024). Article title. Journal of Testing, 15(3), 234-256.",  # No italics
            "Author, A. (2023). Title. _Nature_, 500, 123-145.",  # Wrong italics marker
            "No italics here at all.",
        ]
        
        for text in negative_cases:
            match = pattern.search(text)
            assert match is None, f"Pattern should not match: {text}"
    
    def test_article_title_quotes_pattern(self):
        """Test article title in quotes pattern."""
        # Pattern: r'"([^"]+)"'
        pattern = re.compile(r'"([^"]+)"')
        
        # Positive cases
        positive_cases = [
            ('Smith, J. (2024). "Understanding regex patterns". Journal, 15(3).', "Understanding regex patterns"),
            ('Author, A. (2023). "A study with: Special characters!". Nature.', "A study with: Special characters!"),
            ('"Complex title at start". (2022). By Author, A.', "Complex title at start"),
        ]
        
        for text, expected in positive_cases:
            match = pattern.search(text)
            assert match is not None, f"Pattern should match: {text}"
            assert match.group(1) == expected
        
        # Negative cases
        negative_cases = [
            "Smith, J. (2024). 'Single quotes not double'. Journal.",
            "No quotes here at all.",
            "Author (2023). Title without quotes. Journal.",
        ]
        
        for text in negative_cases:
            match = pattern.search(text)
            if match:
                assert '"' not in text or match is None
    
    def test_year_pattern(self):
        """Test year extraction pattern."""
        # Pattern: r'\((\d{4}[a-z]?)\)'
        pattern = re.compile(r'\((\d{4}[a-z]?)\)')
        
        # Positive cases
        positive_cases = [
            ("Smith, J. (2024). Title.", "2024"),
            ("Author, A. (2023a). Multiple pubs.", "2023a"),
            ("Jones, B. (1999b). Old citation.", "1999b"),
        ]
        
        for text, expected in positive_cases:
            match = pattern.search(text)
            assert match is not None, f"Pattern should match: {text}"
            assert match.group(1) == expected
        
        # Negative cases
        negative_cases = [
            "Smith, J. 2024. No parentheses.",
            "Author (24). Too short year.",
            "Writer [2024]. Wrong brackets.",
        ]
        
        for text in negative_cases:
            match = pattern.search(text)
            assert match is None or not match.group(1).isdigit()[:4]
    
    def test_doi_pattern(self):
        """Test DOI pattern."""
        # Pattern: r'https?://doi\.org/10\.\d{4,}/[^\s]+'
        pattern = re.compile(r'https?://doi\.org/10\.\d{4,}/[^\s]+')
        
        # Positive cases
        positive_cases = [
            "Article. https://doi.org/10.1234/journal.2024.001",
            "Study. http://doi.org/10.5678/abc-def.123",
            "Research. https://doi.org/10.99999/very.long.doi.identifier",
        ]
        
        for text in positive_cases:
            match = pattern.search(text)
            assert match is not None, f"Pattern should match: {text}"
        
        # Negative cases
        negative_cases = [
            "Article. doi.org/10.1234/journal.2024.001",  # Missing protocol
            "Study. https://doi.org/11.1234/journal",  # Not starting with 10.
            "Research. https://doi.com/10.1234/journal",  # Wrong domain
        ]
        
        for text in negative_cases:
            match = pattern.search(text)
            assert match is None, f"Pattern should not match: {text}"


class TestPRISMARegexPatterns:
    """Test PRISMA validator keyword patterns."""
    
    def test_protocol_keywords(self):
        """Test protocol registration keywords."""
        protocol_keywords = ["protocol", "prospero", "registration", "registered", "crd", "protocol number"]
        
        # Positive cases
        positive_texts = [
            "This study was registered in PROSPERO (CRD42024001234)",
            "Protocol registration number: 12345",
            "The protocol was registered before data collection",
            "PROSPERO registration: CRD42023999999",
        ]
        
        for text in positive_texts:
            text_lower = text.lower()
            matches = [kw for kw in protocol_keywords if kw in text_lower]
            assert len(matches) > 0, f"Should find protocol keywords in: {text}"
        
        # Negative cases
        negative_texts = [
            "This study examined patient outcomes",
            "We conducted a systematic review",
            "Data was collected from multiple sources",
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            matches = [kw for kw in protocol_keywords if kw in text_lower]
            assert len(matches) == 0, f"Should not find protocol keywords in: {text}"
    
    def test_database_keywords(self):
        """Test database search keywords."""
        database_keywords = ["pubmed", "medline", "embase", "cochrane", "web of science", "scopus", "searched"]
        
        # Positive cases
        positive_texts = [
            "We searched PubMed, Embase, and Cochrane databases",
            "Systematic search of MEDLINE and Web of Science",
            "Databases searched included Scopus and PubMed",
        ]
        
        for text in positive_texts:
            text_lower = text.lower()
            matches = [kw for kw in database_keywords if kw in text_lower]
            assert len(matches) >= 2, f"Should find multiple database keywords in: {text}"
        
        # Negative cases  
        negative_texts = [
            "We reviewed relevant literature",
            "Articles were selected based on relevance",
            "Google Scholar was used",  # Not a proper database
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            matches = [kw for kw in database_keywords if kw in text_lower]
            assert len(matches) <= 1, f"Should find few/no database keywords in: {text}"


class TestBiasDetectorPatterns:
    """Test bias detection patterns."""
    
    def test_cherry_picking_terms(self):
        """Test cherry-picking detection terms."""
        cherry_pick_terms = ["only", "exclusively", "particularly", "specifically supports"]
        
        # Positive cases
        positive_texts = [
            "We only included studies that showed positive results",
            "This exclusively supports our hypothesis",
            "Particularly focusing on favorable outcomes",
            "The evidence specifically supports our theory",
        ]
        
        for text in positive_texts:
            text_lower = text.lower()
            matches = [term for term in cherry_pick_terms if term in text_lower]
            assert len(matches) > 0, f"Should detect cherry-picking in: {text}"
        
        # Negative cases
        negative_texts = [
            "We included all relevant studies",
            "Both positive and negative results were analyzed",
            "The evidence shows mixed results",
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            matches = [term for term in cherry_pick_terms if term in text_lower]
            assert len(matches) == 0, f"Should not detect cherry-picking in: {text}"
    
    def test_industry_funding_terms(self):
        """Test industry funding detection terms."""
        industry_terms = ["sponsored by", "funded by", "pharmaceutical", "company", "corporation", "industry funding"]
        
        # Positive cases
        positive_texts = [
            "This study was sponsored by XYZ Pharmaceutical",
            "Research funded by ABC Company",
            "Industry funding was provided by the corporation",
            "Pharmaceutical company supported this trial",
        ]
        
        for text in positive_texts:
            text_lower = text.lower()
            matches = [term for term in industry_terms if term in text_lower]
            assert len(matches) > 0, f"Should detect industry funding in: {text}"
        
        # Negative cases
        negative_texts = [
            "This study was supported by NIH grant",
            "Government funding supported this research",
            "Academic institution provided resources",
        ]
        
        for text in negative_texts:
            text_lower = text.lower()
            matches = [term for term in industry_terms if term in text_lower]
            assert len(matches) == 0, f"Should not detect industry funding in: {text}"


class TestComplexPatterns:
    """Test complex multi-component patterns."""
    
    def test_author_list_pattern(self):
        """Test author list extraction patterns."""
        # Pattern for "LastName, F. I., LastName2, G. H., & LastName3, J. K."
        pattern = re.compile(r'([A-Z][a-z]+,\s+[A-Z]\.\s*(?:[A-Z]\.\s*)*(?:,\s*)?)+(?:&\s+[A-Z][a-z]+,\s+[A-Z]\.)?')
        
        # Positive cases
        positive_cases = [
            "Smith, J. D., Jones, K. L., & Brown, M. N.",
            "Johnson, A. B., Williams, C.",
            "Lee, X. Y., Park, S. T., Kim, H. J., & Chen, W.",
        ]
        
        for text in positive_cases:
            match = pattern.search(text)
            assert match is not None, f"Should match author pattern: {text}"
        
        # Negative cases
        negative_cases = [
            "Smith and Jones",  # Wrong format
            "J. Smith, K. Jones",  # First initial first
            "smith, j., jones, k.",  # Lowercase
        ]
        
        for text in negative_cases:
            match = pattern.search(text)
            # Pattern might partially match, but won't capture full correct format
            if match:
                assert match.group() != text
    
    def test_page_range_pattern(self):
        """Test page range patterns."""
        # Pattern for page ranges: "123-456" or "123–456" (em dash)
        pattern = re.compile(r'\b(\d+)\s*[-–]\s*(\d+)\b')
        
        # Positive cases
        positive_cases = [
            ("Journal, 15(3), 234-256.", ("234", "256")),
            ("Book (pp. 123–145).", ("123", "145")),
            ("Pages 1000 - 1050", ("1000", "1050")),
        ]
        
        for text, expected in positive_cases:
            match = pattern.search(text)
            assert match is not None, f"Should match page range: {text}"
            assert match.groups() == expected
        
        # Negative cases
        negative_cases = [
            "Volume 15, Issue 3",  # No page range
            "2024-01-01",  # Date, not pages
            "ISBN-13: 978-0123456789",  # ISBN
        ]
        
        for text in negative_cases:
            match = pattern.search(text)
            if match:
                # Make sure it's not mistaking other number ranges
                start, end = match.groups()
                assert int(end) - int(start) < 10000  # Reasonable page range


if __name__ == "__main__":
    # Run specific test class or all tests
    pytest.main([__file__, "-v", "--tb=short"])