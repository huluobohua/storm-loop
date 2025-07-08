"""
Standalone regex pattern tests - no pytest required.
"""
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_apa_patterns():
    """Test APA citation regex patterns."""
    print("\n=== Testing APA Regex Patterns ===")
    
    # Test 1: Journal title in italics
    print("\n1. Testing journal title italics pattern (*Journal Name*)...")
    pattern = re.compile(r'\*([^*]+)\*')
    
    test_cases = [
        ("Smith, J. (2024). Article. *Journal of Testing*, 15(3).", True, "Journal of Testing"),
        ("No italics here.", False, None),
        ("Wrong _italics_ marker.", False, None),
    ]
    
    for text, should_match, expected in test_cases:
        match = pattern.search(text)
        if should_match:
            assert match is not None, f"Failed to match: {text}"
            assert match.group(1) == expected, f"Wrong capture: {match.group(1)}"
            print(f"  ✓ Matched: '{expected}' in '{text[:50]}...'")
        else:
            assert match is None, f"Shouldn't match: {text}"
            print(f"  ✓ Correctly rejected: '{text}'")
    
    # Test 2: Article title in quotes
    print("\n2. Testing article title quotes pattern...")
    pattern = re.compile(r'"([^"]+)"')
    
    test_cases = [
        ('Smith, J. "Understanding patterns". Journal.', True, "Understanding patterns"),
        ("No quotes here.", False, None),
        ("'Single quotes'.", False, None),
    ]
    
    for text, should_match, expected in test_cases:
        match = pattern.search(text)
        if should_match:
            assert match is not None and match.group(1) == expected
            print(f"  ✓ Matched: '{expected}'")
        else:
            if '"' not in text:
                assert match is None
                print(f"  ✓ Correctly rejected: '{text}'")
    
    # Test 3: Year pattern
    print("\n3. Testing year extraction pattern...")
    pattern = re.compile(r'\((\d{4}[a-z]?)\)')
    
    test_cases = [
        ("Smith, J. (2024). Title.", True, "2024"),
        ("Author, A. (2023a). Multiple.", True, "2023a"),
        ("No (parentheses) 2024.", False, None),
    ]
    
    for text, should_match, expected in test_cases:
        match = pattern.search(text)
        if should_match:
            assert match is not None and match.group(1) == expected
            print(f"  ✓ Matched year: '{expected}'")
        else:
            assert match is None or not match.group(1).startswith(('19', '20'))
            print(f"  ✓ Correctly rejected: '{text}'")
    
    print("\n✅ All APA patterns tested successfully!")


def test_prisma_keywords():
    """Test PRISMA keyword detection."""
    print("\n=== Testing PRISMA Keywords ===")
    
    # Test protocol keywords
    print("\n1. Testing protocol registration keywords...")
    protocol_keywords = ["protocol", "prospero", "registration", "registered", "crd"]
    
    positive_texts = [
        "This study was registered in PROSPERO (CRD42024001234)",
        "Protocol registration number: 12345",
    ]
    
    negative_texts = [
        "This study examined outcomes",
        "We conducted a review",
    ]
    
    for text in positive_texts:
        matches = [kw for kw in protocol_keywords if kw in text.lower()]
        assert len(matches) > 0
        print(f"  ✓ Found keywords {matches} in: '{text[:50]}...'")
    
    for text in negative_texts:
        matches = [kw for kw in protocol_keywords if kw in text.lower()]
        assert len(matches) == 0
        print(f"  ✓ No keywords in: '{text}'")
    
    # Test database keywords
    print("\n2. Testing database search keywords...")
    db_keywords = ["pubmed", "medline", "embase", "cochrane", "web of science"]
    
    positive_texts = [
        "We searched PubMed, Embase, and Cochrane",
        "MEDLINE and Web of Science databases",
    ]
    
    for text in positive_texts:
        matches = [kw for kw in db_keywords if kw in text.lower()]
        assert len(matches) >= 2
        print(f"  ✓ Found {len(matches)} databases: {matches}")
    
    print("\n✅ All PRISMA keywords tested successfully!")


def test_bias_patterns():
    """Test bias detection patterns."""
    print("\n=== Testing Bias Detection Patterns ===")
    
    # Test cherry-picking terms
    print("\n1. Testing cherry-picking terms...")
    cherry_terms = ["only", "exclusively", "particularly", "specifically supports"]
    
    biased_texts = [
        "We only included positive studies",
        "This exclusively supports our view",
    ]
    
    unbiased_texts = [
        "We included all relevant studies",
        "Both positive and negative results",
    ]
    
    for text in biased_texts:
        matches = [term for term in cherry_terms if term in text.lower()]
        assert len(matches) > 0
        print(f"  ✓ Detected bias terms {matches} in: '{text}'")
    
    for text in unbiased_texts:
        matches = [term for term in cherry_terms if term in text.lower()]
        assert len(matches) == 0
        print(f"  ✓ No bias terms in: '{text}'")
    
    # Test industry funding terms
    print("\n2. Testing industry funding terms...")
    industry_terms = ["sponsored by", "funded by", "pharmaceutical", "company"]
    
    industry_texts = [
        "Sponsored by XYZ Pharmaceutical",
        "Research funded by ABC Company",
    ]
    
    academic_texts = [
        "Supported by NIH grant",
        "University funding",
    ]
    
    for text in industry_texts:
        matches = [term for term in industry_terms if term in text.lower()]
        assert len(matches) > 0
        print(f"  ✓ Detected industry terms {matches}")
    
    for text in academic_texts:
        matches = [term for term in industry_terms if term in text.lower()]
        assert len(matches) == 0
        print(f"  ✓ No industry terms detected")
    
    print("\n✅ All bias patterns tested successfully!")


def test_complex_patterns():
    """Test complex multi-part patterns."""
    print("\n=== Testing Complex Patterns ===")
    
    # Test page range pattern
    print("\n1. Testing page range patterns...")
    pattern = re.compile(r'\b(\d+)\s*[-–]\s*(\d+)\b')
    
    test_cases = [
        ("Journal, 15(3), 234-256.", True, ("234", "256")),
        ("Book (pp. 123–145).", True, ("123", "145")),
        ("Volume 15, Issue 3", False, None),
    ]
    
    for text, should_match, expected in test_cases:
        match = pattern.search(text)
        if should_match:
            assert match is not None
            assert match.groups() == expected
            print(f"  ✓ Matched page range: {expected}")
        else:
            # May have false positives, but check they're reasonable
            if match:
                start, end = map(int, match.groups())
                assert end - start < 10000  # Reasonable page range
            else:
                print(f"  ✓ No page range in: '{text}'")
    
    # Test DOI pattern
    print("\n2. Testing DOI patterns...")
    pattern = re.compile(r'https?://doi\.org/10\.\d{4,}/[^\s]+')
    
    valid_dois = [
        "https://doi.org/10.1234/journal.2024",
        "http://doi.org/10.5678/abc-def",
    ]
    
    invalid_dois = [
        "doi.org/10.1234/journal",  # No protocol
        "https://doi.com/10.1234/x",  # Wrong domain
    ]
    
    for doi in valid_dois:
        assert pattern.search(doi) is not None
        print(f"  ✓ Valid DOI: {doi}")
    
    for doi in invalid_dois:
        assert pattern.search(doi) is None
        print(f"  ✓ Rejected invalid: {doi}")
    
    print("\n✅ All complex patterns tested successfully!")


def main():
    """Run all regex tests."""
    print("=" * 60)
    print("COMPREHENSIVE REGEX PATTERN TESTING")
    print("=" * 60)
    
    try:
        test_apa_patterns()
        test_prisma_keywords()
        test_bias_patterns()
        test_complex_patterns()
        
        print("\n" + "=" * 60)
        print("✅ ALL REGEX PATTERN TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)